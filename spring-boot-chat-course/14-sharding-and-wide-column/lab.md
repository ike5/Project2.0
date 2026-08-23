# Lab 14 — Shard It, Then Model It in ScyllaDB

**You'll:** build logical sharding with a routing layer, move a shard while
traffic flows, measure scatter-gather, then model the same chat data in ScyllaDB
and benchmark both.

⏱️ ~110 min.

> **Low-memory path:** run 2 Postgres shards instead of 4, and a single-node
> Scylla with `--smp 1 --memory 1G`. Every conclusion holds.

---

## Part A — Logical shards

`infra/compose.shards.yml`:

```yaml
name: pulse-shards

x-shard: &shard
  image: postgres:16-alpine
  environment:
    POSTGRES_USER: pulse
    POSTGRES_PASSWORD: pulse
    POSTGRES_DB: pulse
  healthcheck:
    test: ["CMD-SHELL", "pg_isready -U pulse"]
    interval: 5s
    retries: 10
  command:
    - postgres
    - -c
    - max_connections=100
    - -c
    - log_min_duration_statement=200

services:
  shard0: { <<: *shard, ports: ["5440:5432"] }
  shard1: { <<: *shard, ports: ["5441:5432"] }
  shard2: { <<: *shard, ports: ["5442:5432"] }
  shard3: { <<: *shard, ports: ["5443:5432"] }
```

```bash
docker compose -f infra/compose.shards.yml up -d --wait
```

### The routing layer

`src/main/java/com/pulse/shard/ShardRouter.java`:

```java
package com.pulse.shard;

import org.springframework.jdbc.core.simple.JdbcClient;
import org.springframework.stereotype.Component;

import java.nio.charset.StandardCharsets;
import java.util.*;
import java.util.zip.CRC32;

@Component
public class ShardRouter {

    /**
     * 4096 LOGICAL shards, mapped onto however many PHYSICAL databases exist.
     * This number is chosen once and never changes -- it is the one thing a
     * reshard must not touch.
     */
    public static final int LOGICAL_SHARDS = 4096;

    private final List<JdbcClient> physical;
    /** logicalShard -> index into `physical`. The only thing a reshard mutates. */
    private volatile int[] assignment;

    public ShardRouter(List<JdbcClient> physical, ShardAssignmentStore store) {
        this.physical = physical;
        this.assignment = store.load(LOGICAL_SHARDS, physical.size());
    }

    /** CRC32, not String.hashCode(): stable across JVM versions and languages. */
    public static int logicalShardFor(String roomId) {
        var crc = new CRC32();
        crc.update(roomId.getBytes(StandardCharsets.UTF_8));
        return (int) (crc.getValue() % LOGICAL_SHARDS);
    }

    public JdbcClient forRoom(String roomId) {
        return physical.get(assignment[logicalShardFor(roomId)]);
    }

    public int physicalShardFor(String roomId) {
        return assignment[logicalShardFor(roomId)];
    }

    /** Every physical shard, for scatter-gather queries. */
    public List<JdbcClient> all() { return physical; }

    void reassign(int[] next) { this.assignment = next; }   // atomic reference swap
}
```

> ⚠️ **Never use `String.hashCode()` as a shard function.** It's stable within a
> JVM but is not a contract across languages, and a change would silently
> relocate every room. Use CRC32, MurmurHash, or xxHash — something specified.

The assignment table lives in a coordination database (or etcd):

```sql
CREATE TABLE shard_assignment (
    logical_shard int PRIMARY KEY,
    physical_shard int NOT NULL,
    state text NOT NULL DEFAULT 'active',      -- active | migrating | draining
    migrating_to int,
    updated_at timestamptz NOT NULL DEFAULT now()
);

INSERT INTO shard_assignment (logical_shard, physical_shard)
SELECT g, g % 4 FROM generate_series(0, 4095) g;
```

Wire it into the repository:

```java
public SendResult send(String roomId, String sender, MessageCreate create) {
    JdbcClient shard = router.forRoom(roomId);         // <-- the only change
    // ... identical SQL, executed against the right database ...
}
```

Check the distribution:
```bash
curl -s localhost:8080/api/debug/shard-distribution | jq
```
**Expected:**
```json
{ "shard0": 251, "shard1": 249, "shard2": 252, "shard3": 248 }
```
✅ 1,000 rooms spread within 1.6% of even. CRC32 distributes well.

---

## Part B — Move a shard, live

The operation people fear. Do it with traffic running.

`src/main/java/com/pulse/shard/ShardMigrator.java`:

```java
/**
 * Four phases. The only one with a write pause is phase 3, and it is bounded to
 * the time it takes to copy the tail (typically tens of milliseconds).
 */
public void migrate(int logicalShard, int fromPhysical, int toPhysical) {

    // PHASE 1 -- DUAL WRITE. New writes go to both. Reads still go to `from`.
    setState(logicalShard, "migrating", toPhysical);
    log.info("phase 1: dual-writing shard {} -> {}", logicalShard, toPhysical);
    awaitAllNodesAcknowledge(logicalShard);        // every app node reloaded the map

    // PHASE 2 -- BACKFILL. Copy historical rows in batches while traffic flows.
    long copied = backfill(logicalShard, fromPhysical, toPhysical);
    log.info("phase 2: backfilled {} rows", copied);

    // PHASE 3 -- CATCH UP AND CUT OVER. Briefly reject writes for this shard,
    // copy the tail, flip the map. This is the only pause.
    setState(logicalShard, "draining", toPhysical);
    long tail = backfill(logicalShard, fromPhysical, toPhysical);   // usually tiny
    verifyRowCountsMatch(logicalShard, fromPhysical, toPhysical);
    commitAssignment(logicalShard, toPhysical);
    setState(logicalShard, "active", null);
    log.info("phase 3: cut over ({} tail rows)", tail);

    // PHASE 4 -- CLEAN UP. Only after a soak period, so rollback stays possible.
    scheduleCleanup(logicalShard, fromPhysical, Duration.ofHours(24));
}
```

Run it under load:

```bash
k6 run -e ROOMS=1000 --vus 5000 --duration 5m code/pulse-load.js &
sleep 60
curl -X POST localhost:8080/api/admin/shards/1288/migrate -d '{"to": 3}'
```

**Expected:**
```
phase 1: dual-writing shard 1288 -> 3
phase 2: backfilled 184,291 rows in 41,204 ms
phase 3: cut over (312 tail rows) in 184 ms
```

And in k6:
```
fanout_latency_ms: p(99)=214   (baseline 192)
ws_errors: 0.02%
sequence_gaps: 0
```

✅ **184 ms of write pause for one logical shard (1/4096 of traffic), zero
message loss.** The 0.02% errors are sends rejected during the 184 ms drain,
which clients retried with the same `clientId`.

Verify:
```bash
docker exec pulse-shards-shard1-1 psql -U pulse -d pulse -tAc \
  "SELECT count(*) FROM messages WHERE room_id = ANY(:rooms)"
docker exec pulse-shards-shard3-1 psql -U pulse -d pulse -tAc \
  "SELECT count(*) FROM messages WHERE room_id = ANY(:rooms)"
```
**Expected — identical:**
```
184603
184603
```

Now grow 4 → 8 databases:
```bash
docker compose -f infra/compose.shards.yml --profile grow up -d
curl -X POST localhost:8080/api/admin/shards/rebalance -d '{"physicalShards": 8}'
```
**Expected:**
```
rebalancing: moving 2048 of 4096 logical shards
estimated rows to copy: 41,204,881
[progress] 512/2048 shards migrated (25%)
...
rebalance complete in 38m 12s; 0 messages lost
```

✅ **Exactly half the logical shards moved** — `1/n` where n went 4→8. With naive
`hash mod N` it would have been ~87%.

Record it:
```markdown
## Module 14 — Sharding

- 4096 logical shards over 4 physical; distribution within 1.6% of even
- Live shard migration: 184ms write pause for 1/4096 of traffic, 0 lost
- Rebalance 4 -> 8 databases: 2048/4096 logical shards moved (exactly 1/n)
  vs ~87% with naive hash-mod-N
```

---

## Part C — The cost of scatter-gather

Some queries can no longer touch one shard.

```java
/** "All my rooms' unread counts" — the user's rooms span many shards. */
public Map<String, Long> unreadAcrossRooms(String userId) {
    var rooms = membership.roomsOf(userId);                   // ~20 rooms

    // Group by physical shard so each database is queried ONCE, not per room.
    var byShard = rooms.stream()
            .collect(Collectors.groupingBy(router::physicalShardFor));

    try (var scope = new StructuredTaskScope.ShutdownOnFailure()) {
        var futures = byShard.entrySet().stream()
                .map(e -> scope.fork(() -> queryShard(e.getKey(), e.getValue(), userId)))
                .toList();
        scope.join();
        scope.throwIfFailed();
        return futures.stream().map(Subtask::get)
                      .flatMap(m -> m.entrySet().stream())
                      .collect(Collectors.toMap(Map.Entry::getKey, Map.Entry::getValue));
    }
}
```

**Expected:**

| Query | Unsharded | Sharded (4) | Sharded (16) |
|-------|-----------|-------------|--------------|
| Scrollback (1 room) | 0.16 ms | **0.16 ms** | **0.16 ms** |
| Send | 0.9 ms | **0.9 ms** | **0.9 ms** |
| Unread across 20 rooms | 1.2 ms | **3.4 ms** | **8.1 ms** |
| Global message count | 41 ms | **184 ms** | **710 ms** |
| Search across all rooms | 4,100 ms | **4,300 ms** (parallel) | 4,400 ms |

✅ **The hot paths are unaffected** — that's the payoff of sharding by room.
Scatter-gather queries degrade with shard count, as expected.

Note the p99 shape:
```
unread across 20 rooms, 4 shards:  p50=3.4ms  p99=41ms
```
**p99 is 12× p50** because a scatter-gather is as slow as its *slowest* shard.
With 4 shards you're sampling the p99 of each — the more shards you touch, the
more likely you hit a slow one. This is why fan-out reads need
`StructuredTaskScope` with a **timeout**, and a partial-result path:

```java
try (var scope = new StructuredTaskScope.ShutdownOnFailure()) {
    // ... fork ...
    scope.joinUntil(Instant.now().plusMillis(200));      // bounded
}
catch (TimeoutException e) {
    partialResults.increment();
    return whateverCompleted(futures);      // a partial badge count beats a spinner
}
```

---

## Part D — Model it in ScyllaDB

```yaml
  scylla:
    image: scylladb/scylla:6.0
    command: --smp 2 --memory 2G --overprovisioned 1 --developer-mode 1
    ports: [ "9042:9042" ]
    healthcheck:
      test: ["CMD-SHELL", "cqlsh -e 'describe cluster' || exit 1"]
      interval: 10s
      retries: 20
```

```bash
docker compose -f infra/compose.scylla.yml up -d --wait
alias cql='docker exec -i pulse-scylla cqlsh'
```

### The schema

```sql
CREATE KEYSPACE pulse WITH replication =
  {'class': 'NetworkTopologyStrategy', 'replication_factor': 1};

USE pulse;

CREATE TABLE messages (
    room_id    text,
    bucket     int,          -- time bucket: THE hot-partition fix
    seq        bigint,
    id         bigint,
    sender     text,
    client_id  text,
    body       text,
    created_at timestamp,
    PRIMARY KEY ((room_id, bucket), seq)
) WITH CLUSTERING ORDER BY (seq DESC)          -- physically sorted newest-first
  AND compaction = {
      'class': 'TimeWindowCompactionStrategy',  -- built for append-only time series
      'compaction_window_unit': 'DAYS',
      'compaction_window_size': 1
  }
  AND default_time_to_live = 7776000;           -- 90 days, enforced by the DB
```

Three things to notice:

**1. `((room_id, bucket), seq)`** — the composite partition key. `bucket` is
`floor(epochDay / 7)`, so a room's data spreads across weekly partitions. Without
it, `#general` is one partition on one node, forever growing — Discord's exact
problem.

**2. `CLUSTERING ORDER BY (seq DESC)`** — rows are stored on disk in the order
you read them. "Last 50 messages" is a sequential byte read, not an index seek.

**3. `default_time_to_live`** — retention is a table property. No partition
management, no `DROP TABLE` job, no cron. The database expires rows itself.

Second table for the idempotency lookup — because **Cassandra has no secondary
key you can query efficiently**, you write the same fact twice:

```sql
CREATE TABLE messages_by_client_id (
    room_id   text,
    client_id text,
    seq       bigint,
    id        bigint,
    PRIMARY KEY ((room_id, client_id))
) WITH default_time_to_live = 300;    -- only needs the dedup window
```

> **This is the wide-column tax made concrete:** one table per query pattern, and
> your application maintains consistency between them. Postgres gave you a
> second index; Cassandra gives you a second table and a second write.

```bash
cql -f code/scylla_schema.cql
cql -e "DESCRIBE TABLE pulse.messages;"
```

### The Java client

```xml
<dependency>
  <groupId>com.scylladb</groupId>
  <artifactId>java-driver-core</artifactId>
  <version>4.18.0.0</version>
</dependency>
```

```java
@Repository
public class ScyllaMessageRepository {

    private static final int BUCKET_DAYS = 7;

    private final CqlSession session;
    private final PreparedStatement insert, insertDedup, scrollback, dedupLookup;

    public ScyllaMessageRepository(CqlSession session) {
        this.session = session;
        this.insert = session.prepare("""
                INSERT INTO messages (room_id, bucket, seq, id, sender, client_id, body, created_at)
                VALUES (?,?,?,?,?,?,?,?)
                """);
        this.insertDedup = session.prepare("""
                INSERT INTO messages_by_client_id (room_id, client_id, seq, id)
                VALUES (?,?,?,?) IF NOT EXISTS
                """);                                    // LWT: Paxos, and slow
        this.scrollback = session.prepare("""
                SELECT seq, id, sender, body, created_at
                FROM messages WHERE room_id = ? AND bucket = ? AND seq < ?
                LIMIT ?
                """);
        this.dedupLookup = session.prepare(
                "SELECT seq, id FROM messages_by_client_id WHERE room_id = ? AND client_id = ?");
    }

    static int bucketOf(Instant t) {
        return (int) (t.getEpochSecond() / 86400 / BUCKET_DAYS);
    }

    public void append(String roomId, long seq, long id, String sender,
                       String clientId, String body) {
        Instant now = Instant.now();
        int bucket = bucketOf(now);
        // Two writes, unbatched: a LOGGED batch across partitions costs a
        // coordinator-side batchlog write and is slower than two independent ones.
        session.execute(insert.bind(roomId, bucket, seq, id, sender, clientId, body, now));
        session.execute(insertDedup.bind(roomId, clientId, seq, id));
    }

    public List<MessageNew> scrollback(String roomId, long cursorSeq, int limit) {
        var out = new ArrayList<MessageNew>(limit);
        int bucket = bucketOf(Instant.now());

        // Walk backwards across buckets until we have enough. This is the code
        // the bucket key costs you -- Postgres had one range scan.
        while (out.size() < limit && bucket > bucketOf(Instant.now()) - 52) {
            var rows = session.execute(scrollback.bind(
                    roomId, bucket, cursorSeq, limit - out.size()));
            rows.forEach(r -> out.add(toMessage(r)));
            bucket--;
        }
        return out;
    }
}
```

---

## Part E — Benchmark them head to head

Identical workload: 1,000 rooms, 50M existing messages, measured over 10 minutes.

```bash
./code/store_bench.sh postgres-single
./code/store_bench.sh postgres-sharded-4
./code/store_bench.sh scylla-1node
./code/store_bench.sh scylla-3node
```

**Expected:**

| | PG single | PG sharded ×4 | Scylla 1 node | Scylla 3 nodes |
|---|-----------|---------------|---------------|----------------|
| **Inserts/s** | 41,200 | **158,400** | **112,000** | **321,000** |
| Scrollback p50 | 0.16 ms | 0.16 ms | **0.11 ms** | 0.12 ms |
| Scrollback p99 | 1.4 ms | 1.4 ms | **0.9 ms** | 1.1 ms |
| Scrollback **p99.9** | 8 ms | 8 ms | **41 ms** | 38 ms |
| Idempotency check p50 | 0.08 ms | 0.08 ms | **2.1 ms** (LWT) | 4.8 ms (LWT) |
| Storage, 50M messages | 11 GB | 11 GB | **6.2 GB** | 18.6 GB (RF=3) |
| Retention | `DROP TABLE`, 41 ms | 41 ms × 4 | **automatic (TTL)** | automatic |
| Adding a node | migrate shards, 38 min | 38 min | **`nodetool` + rebalance** | minutes |
| Cross-room query | ✅ SQL | ⚠️ scatter-gather | ❌ **impossible** | ❌ |
| Transactions | ✅ | ⚠️ per-shard | ❌ | ❌ |

### Reading the results

**Scylla wins on raw write throughput** (2.7× single Postgres, 2× sharded) and on
**storage** (6.2 GB vs 11 GB — LSM sstables compress better than a heap plus
B-trees).

**Scylla wins on median read latency** — 0.11 ms vs 0.16 ms. Sequential reads of
sorted bytes beat an index seek plus heap fetches.

**Scylla loses badly on p99.9** (41 ms vs 8 ms) — that's compaction. Investigate:
```bash
docker exec pulse-scylla nodetool compactionstats
docker exec pulse-scylla nodetool tablestats pulse.messages | grep -E 'SSTable count|Compacted'
```
```
pending tasks: 3
SSTable count: 14
```
A read touching 14 sstables does 14 bloom-filter checks and up to 14 disk reads.
Postgres's B-tree is always 3–4 levels.

**Scylla loses catastrophically on the idempotency check** — 2.1 ms vs 0.08 ms,
**26× worse**, because `IF NOT EXISTS` is a lightweight transaction requiring a
**Paxos round trip** (four network round trips at `QUORUM`). At 3 nodes it's 4.8
ms.

> **This is the most important number in the lab.** Module 05's idempotency —
> the thing that makes the entire delivery chain work — is nearly free in
> Postgres and expensive in Cassandra. A design that assumed cheap conditional
> writes has to be rethought.

The workaround: drop the LWT and accept that duplicates are possible, deduping in
the *application* with a Redis `SET NX` instead:

| Approach | p50 | Correct? |
|----------|-----|----------|
| Scylla LWT (`IF NOT EXISTS`) | 2.1 ms | ✅ |
| Scylla plain insert + Redis `SET NX` dedup | **0.19 ms** | ✅ (bounded by the Redis TTL) |
| Scylla plain insert, no dedup | 0.09 ms | ❌ duplicates |

✅ 11× better, and correct — but note what happened: **you moved the guarantee
out of the database and into Redis**, which means it's now bounded by a TTL and
lost on a Redis restart. In Postgres it was a unique index that is true forever.

---

## Part F — Make a hot partition, then fix it

```bash
k6 run -e ROOMS=1 -e SEND_EVERY=100 --vus 5000 --duration 5m code/pulse-load.js
```

With `PRIMARY KEY ((room_id), seq)` — no bucket:

```bash
docker exec pulse-scylla nodetool tablehistograms pulse.messages
docker exec pulse-scylla nodetool toppartitions pulse messages 10000
```
**Expected:**
```
Partition Size (bytes)
  Max: 4,294,967,296        <-- 4 GB in ONE partition

TOP WRITES
  Partition    Count
  room.0       2,841,993     <-- 100% of writes to one node
```
```
scrollback p99: 4,102 ms
node-1 CPU: 100%    node-2 CPU: 3%    node-3 CPU: 3%
```

✅ **One partition, one node, 100% CPU while two nodes idle.** No amount of
adding nodes helps — the partition key determines placement, and there is one
key.

With the bucket (`((room_id, bucket), seq)`):
```
Partition Size (bytes)
  Max: 84,213,760           <-- 84 MB, weekly buckets

scrollback p99: 1.1 ms
node-1 CPU: 34%   node-2 CPU: 31%   node-3 CPU: 33%
```

✅ **3,700× better p99 and even CPU**, because 52 weekly buckets hash to
different nodes.

> **The rule:** in a wide-column store, the partition key is your *only* load
> balancing mechanism. A key with low cardinality or a skewed distribution
> cannot be fixed by adding hardware. Design the key for the *hottest* thing you
> will ever store, not the average.

---

## Part G — The decision

Record it:
```markdown
## Module 14 — Sharding vs wide-column

| | PG single | PG x4 | Scylla 1 | Scylla 3 |
|---|-----------|-------|----------|----------|
| Inserts/s          |  41,200 | 158,400 | 112,000 | 321,000 |
| Scrollback p50     | 0.16 ms | 0.16 ms | 0.11 ms | 0.12 ms |
| Scrollback p99.9   |    8 ms |    8 ms |   41 ms |   38 ms |
| Idempotency p50    | 0.08 ms | 0.08 ms |  2.1 ms |  4.8 ms |
| Storage (50M)      |   11 GB |   11 GB |  6.2 GB | 18.6 GB |

- Hot partition without a bucket key: p99 4,102ms, 1 of 3 nodes at 100% CPU
- With weekly buckets: p99 1.1ms, even CPU  (3,700x)
- Live shard migration: 184ms pause for 1/4096 of traffic
- Rebalance 4->8: exactly 1/n logical shards moved
```

**The recommendation stands: sharded Postgres.**

Not because Scylla is worse — it wins on write throughput, median read latency
and storage. Because:

1. **Pulse's write rate doesn't need it.** 158k inserts/s sharded is well above
   target. Buying 321k costs the rest of this list.
2. **The idempotency check is 26× more expensive**, and it is load-bearing for
   the entire delivery guarantee. The workaround moves a permanent database
   invariant into a TTL-bounded cache.
3. **Transactions.** The outbox (Module 13) requires writing the message and the
   outbox row atomically. Cassandra cannot. You would rebuild that guarantee out
   of weaker primitives.
4. **Every future query must be designed now.** A new feature needing a new
   access pattern is a new table plus a backfill, not a new index.
5. **p99.9 is 5× worse** from compaction — and chat latency is judged at the tail.

**When to revisit:** if write rate exceeds ~500k/s sustained, if storage cost
becomes the dominant line item, or if you acquire a team that operates Cassandra
already. Discord's move was correct *for Discord* — and they made it after
outgrowing exactly the design in this course.

---

## What you built

- Logical sharding (4096 → N) with a stable CRC32 hash and a swappable
  assignment map.
- **A live shard migration** with a 184 ms write pause and zero loss.
- A 4→8 rebalance moving exactly `1/n`, versus ~87% for naive modulo.
- Scatter-gather with structured concurrency, bounded timeouts and partial
  results.
- The same chat data in ScyllaDB, with the bucket key that prevents hot
  partitions, benchmarked head to head.
- **A defensible decision**, with the numbers that support it and the conditions
  that would change it.

Now do [`challenge.md`](./challenge.md).

Then: [Module 15 — Rebuilding the Hot Path in WebFlux](../15-webflux-reactive-rebuild/).
