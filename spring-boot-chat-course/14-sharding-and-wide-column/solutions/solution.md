# Solutions — Module 14

---

## Task 1 — Break the migration

### Killing a node during phase 1 (dual write)

```bash
curl -X POST localhost:8080/api/admin/shards/1288/migrate -d '{"to": 3}'
sleep 2
kill -9 $(pgrep -f 'PULSE_NODE_ID=node-b')
```

**Expected:**
```
shard1: 184,291 rows
shard3: 184,102 rows        <-- 189 rows missing
```

✅ **189 messages written to the old shard only.** node-b was killed after
writing to `from` but before writing to `to`, for messages in flight — and after
restart it reloaded the map and dual-wrote correctly, so the *gap* is invisible.
The backfill in phase 2 would catch most of it, but messages written *during*
phase 2, in the already-copied range, are missed.

**Worse:** if the node had been killed *before* it reloaded the assignment map,
it would have single-written to `from` for as long as it stayed up — potentially
minutes.

### Killing a node during phase 3 (cutover)

```bash
kill -9 $(pgrep -f 'PULSE_NODE_ID=node-c') # during the 184ms drain
```
**Expected:**
```
node-c restarts, loads assignment: shard 1288 -> physical 3
shard1: 184,291   shard3: 184,291        <-- consistent
```
✅ **Phase 3 is safe**, because the assignment change is a single atomic commit
in the coordination database. A node either sees the old value or the new one.

### The fix: fence on assignment version

The real hazard in phase 1 is a node operating on a **stale map**. Make that
impossible to do silently:

```sql
ALTER TABLE shard_assignment ADD COLUMN version bigint NOT NULL DEFAULT 1;
CREATE TABLE shard_assignment_version (
    id int PRIMARY KEY DEFAULT 1,
    version bigint NOT NULL,
    updated_at timestamptz NOT NULL DEFAULT now()
);
```

```java
@Component
public class ShardAssignmentWatcher {

    private volatile long localVersion;

    /** Poll frequently; this is one tiny query. */
    @Scheduled(fixedRate = 500)
    public void refresh() {
        long remote = coordinationJdbc.sql("SELECT version FROM shard_assignment_version")
                                      .query(Long.class).single();
        if (remote != localVersion) {
            router.reassign(loadAssignment());
            localVersion = remote;
            log.info("shard assignment updated to version {}", remote);
        }
        lastRefreshOk = System.nanoTime();
    }

    /**
     * FENCING: if we haven't confirmed our map is current recently, we must not
     * write. A node with a stale map writing to the wrong shard is silent,
     * permanent data divergence -- far worse than a rejected send.
     */
    public void assertFresh() {
        if (System.nanoTime() - lastRefreshOk > Duration.ofSeconds(5).toNanos()) {
            staleMapRejections.increment();
            throw new ServiceUnavailableException("shard map may be stale", 1000);
        }
    }
}
```

And the migrator waits for **every** node to acknowledge before dual-writing:

```java
private void awaitAllNodesAcknowledge(long targetVersion) {
    Instant deadline = Instant.now().plusSeconds(30);
    while (Instant.now().isBefore(deadline)) {
        var behind = coordinationJdbc.sql("""
                SELECT node_id FROM node_heartbeats
                WHERE last_seen > now() - interval '30 seconds'
                  AND assignment_version < :v
                """).param("v", targetVersion).query(String.class).list();

        if (behind.isEmpty()) return;
        log.info("waiting for nodes to pick up assignment v{}: {}", targetVersion, behind);
        sleepQuietly(500);
    }
    throw new MigrationAbortedException("nodes did not acknowledge in time");
}
```

Plus a **reconciliation pass** at the end of phase 2, which catches the 189-row
case:

```java
private long reconcile(int logicalShard, int from, int to) {
    // Anything in `from` that isn't in `to`. Cheap because both are indexed
    // on (room_id, seq).
    var missing = fromShard.sql("""
            SELECT m.* FROM messages m
            WHERE m.room_id = ANY(:rooms)
              AND NOT EXISTS (SELECT 1 FROM dblink_to_target(m.room_id, m.seq))
            """).query(MessageRow.class).list();
    missing.forEach(this::copyToTarget);
    return missing.size();
}
```

**Expected after the fix:**
```bash
kill -9 $(pgrep -f 'PULSE_NODE_ID=node-b')      # during phase 1
```
```
phase 1: dual-writing shard 1288 -> 3
  waiting for nodes to pick up assignment v42: [node-b]
  (node-b restarts, picks it up)
phase 2: backfilled 184,291 rows
phase 2b: reconciled 189 rows           <-- caught
phase 3: cut over (12 tail rows)
verify: shard1=184,492  shard3=184,492   MATCH
```

✅ Zero divergence. And a node that can't reach coordination **rejects writes**
rather than guessing — the fencing principle from Module 11, applied where it
actually matters.

---

## Task 2 — The scatter-gather ceiling

| Shards touched | p50 | p99 | p99.9 |
|----------------|-----|-----|-------|
| 1 | 1.2 ms | 4 ms | 9 ms |
| 4 | 3.4 ms | 41 ms | 118 ms |
| 16 | 8.1 ms | 94 ms | 310 ms |
| 64 | 14.2 ms | 189 ms | 890 ms |
| 256 | 22.8 ms | **412 ms** | 2,100 ms |

### The model

A scatter-gather completes when the **slowest** shard replies. If each shard's
latency is independent with CDF `F(t)`, the maximum over `n` shards has CDF
`F(t)^n`. So the p99 of the whole is the **p(0.99^(1/n))** of a single shard:

```
n=4:    need each shard's p99.75   -> 41 ms
n=16:   need each shard's p99.94   -> 94 ms
n=64:   need each shard's p99.984  -> 189 ms
n=256:  need each shard's p99.996  -> 412 ms
```

Fitted: **p99 ≈ 4 ms × n^0.53** — roughly `sqrt(n)`, because Postgres's latency
distribution has a long tail.

**The consequence:** you are sampling deeper and deeper into every shard's tail.
At 256 shards, one shard having a 400 ms hiccup once in 10,000 queries makes
*your* p99 400 ms.

### The constant-time alternative

Stop scattering. **Maintain the answer.**

```java
/**
 * Unread counts live in Redis, keyed by user. One HGETALL, one shard, constant
 * time regardless of how many database shards exist.
 */
public Map<String, Long> unreadAcrossRooms(String userId) {
    var counts = redis.<String, String>opsForHash().entries("unread:{" + userId + "}");
    if (!counts.isEmpty()) { cacheHits.increment(); return parse(counts); }

    // Cold: rebuild by scatter-gather ONCE, then cache.
    var rebuilt = scatterGather(userId);
    redis.opsForHash().putAll("unread:{" + userId + "}", stringify(rebuilt));
    redis.expire("unread:{" + userId + "}", Duration.ofHours(24));
    return rebuilt;
}

/** Maintained incrementally on the write path — a pipelined HINCRBY (Module 08). */
public void onNewMessage(String roomId, Set<String> members, String sender) {
    redis.executePipelined((RedisCallback<Object>) c -> {
        for (String member : members) {
            if (member.equals(sender)) continue;
            c.hashCommands().hIncrBy(("unread:{" + member + "}").getBytes(),
                                     roomId.getBytes(), 1);
        }
        return null;
    });
}
```

| | Scatter-gather (256 shards) | Maintained in Redis |
|---|----------------------------|---------------------|
| p50 | 22.8 ms | **0.2 ms** |
| p99 | 412 ms | **1.1 ms** |
| Scales with shard count | ❌ `sqrt(n)` | ✅ **constant** |
| Postgres load | 256 queries/request | **0** |

### What it costs

1. **Write amplification on the write path.** One message becomes N `HINCRBY`s.
   Pipelined it's one round trip, but it's O(room size) of Redis work — the same
   fan-out-on-write shape Module 12 rejected for storage, accepted here because
   the payload is 8 bytes rather than 500.
2. **A second source of truth that can drift.** The authoritative answer is
   `room.last_seq − user.last_read_seq` (Module 10). The Redis counter is a
   maintained *copy*. Missed increments (a crashed node mid-pipeline) mean a
   badge that's wrong.
3. **The drift needs a repair path.** Rebuild from the cursors periodically, and
   always on cache miss:
   ```java
   @Scheduled(cron = "0 0 4 * * *")
   public void rebuildAllUnreadCounts() { /* from read_cursors, per shard */ }
   ```
4. **Memory.** 1M users × 20 rooms × ~30 bytes ≈ **600 MB** — and watch Module
   08's listpack threshold: a user in 129+ rooms costs 4× more.

> **The general pattern:** a scatter-gather you run constantly should be a
> maintained aggregate. The cost is denormalization and a repair job — the
> classic trade, and the reason "derived data must be rebuildable" is a rule.

---

## Task 3 — Cross-shard schema migration

### The runbook

```markdown
# Runbook: add `messages.attachment_id` across 4 shards

## Preconditions
- [ ] All app nodes on build >= 4.12 (which tolerates the column being absent)
- [ ] Outbox backlog < 100
- [ ] No shard migration in progress
- [ ] Replica lag < 500ms on all shards

## Phase 1 — Expand (additive only, safe on any shard)
For each shard, in order, with 60s between:
    ALTER TABLE messages ADD COLUMN attachment_id bigint;   -- NULLable, no default
Verify: SELECT count(*) FROM information_schema.columns
        WHERE table_name='messages' AND column_name='attachment_id';  -- expect 1

NOTE: no DEFAULT, no NOT NULL. In PG11+ a constant default is metadata-only,
but a VOLATILE default rewrites the whole table -- minutes of ACCESS EXCLUSIVE
lock on a 50M-row table. Never risk it; add the column nullable, backfill,
then constrain.

## Phase 2 — Deploy readers (build 4.13: reads the column if present, tolerates NULL)
Rolling deploy, maxUnavailable=1. Verify error rate unchanged for 10 minutes.

## Phase 3 — Deploy writers (build 4.14: writes the column)
Rolling deploy. Some nodes are 4.13 and some 4.14 during this window -- both
must work, which is why 4.13 tolerates NULL.

## Phase 4 — Backfill (optional, batched)
For each shard: UPDATE ... WHERE attachment_id IS NULL AND id BETWEEN ? AND ?
in 10,000-row batches with a 100ms pause. Monitor replica lag; abort above 1s.

## Phase 5 — Contract (a LATER release, never the same one)
    ALTER TABLE messages ALTER COLUMN attachment_id SET NOT NULL;   -- if required

## Rollback
Phases 1-4 are all reversible by deploying the previous build. Phase 1's column
can stay -- an unused nullable column costs ~0.
```

### The version-skew matrix

The window where correctness actually lives:

| App build | Shard has column | Behaviour |
|-----------|-----------------|-----------|
| 4.12 (old) | no | ✅ baseline |
| 4.12 (old) | **yes** | ✅ ignores it — **this is why `SELECT *` is banned** |
| 4.13 (reader) | no | ✅ treats as NULL |
| 4.13 (reader) | yes | ✅ reads it |
| 4.14 (writer) | **no** | ❌ **`ERROR: column "attachment_id" does not exist`** |
| 4.14 (writer) | yes | ✅ |

**Row 5 is why phase 1 must complete on every shard before phase 3 starts.**

```java
// This is what makes row 2 safe. SELECT * breaks the moment the shape changes.
jdbc.sql("SELECT id, room_id, seq, sender, body FROM messages WHERE ...")
```

### Execute it

```bash
k6 run -e ROOMS=1000 --vus 5000 --duration 20m code/pulse-load.js &
./code/migrate_schema.sh add-attachment-id
```
**Expected:**
```
phase 1: shard0 ALTER ok (12ms)   shard1 ok (9ms)   shard2 ok (11ms)   shard3 ok (10ms)
phase 2: rolling deploy 4.13 ... 4/4 nodes, error rate 0.00%
phase 3: rolling deploy 4.14 ... 4/4 nodes, error rate 0.00%
phase 4: backfilled 50,204,881 rows in 41m (max replica lag 312ms)
```
```
k6: ws_errors 0.00%, sequence_gaps 0
```

✅ Zero errors. The `ALTER` was 10 ms per shard because it's metadata-only.

**Now do it wrong**, to see why the rules exist:
```sql
ALTER TABLE messages ADD COLUMN attachment_id bigint NOT NULL DEFAULT nextval('some_seq');
```
```
(blocks for 4m 12s holding ACCESS EXCLUSIVE)
k6: ws_errors 41.20%
```
✅ A **volatile** default forces a full table rewrite under an exclusive lock.
Four minutes of total outage per shard. (A *constant* default is metadata-only in
PG 11+; the distinction is the whole thing.)

---

## Task 4 — Durable idempotency in Scylla without LWT

The insight: **make the client ID part of the primary key**, so uniqueness is
enforced by the data model rather than by a conditional write.

```sql
CREATE TABLE messages_by_client (
    room_id   text,
    bucket    int,
    client_id text,
    seq       bigint,
    id        bigint,
    sender    text,
    body      text,
    created_at timestamp,
    PRIMARY KEY ((room_id, bucket), client_id)
) WITH default_time_to_live = 604800;      -- 7 days
```

An `INSERT` with the same `(room_id, bucket, client_id)` is an **upsert** — it
overwrites rather than duplicating. No Paxos, no read-before-write.

```java
public SendResult send(String roomId, String clientId, String body, String sender) {
    int bucket = bucketOf(Instant.now());

    // 1. Cheap read: has this client_id already been written? Single partition,
    //    no coordination. ~0.1ms.
    var existing = session.execute(lookupByClient.bind(roomId, bucket, clientId));
    var row = existing.one();
    if (row != null) return new SendResult(toMessage(row), true);

    // 2. Allocate seq from Redis (already coordination-free, Module 10)
    long seq = sequences.next(roomId);
    long id = ids.nextId();

    // 3. Two plain inserts, no LWT.
    session.execute(insertByClient.bind(roomId, bucket, clientId, seq, id, sender, body, now));
    session.execute(insertBySeq.bind(roomId, bucket, seq, id, sender, clientId, body, now));

    return new SendResult(message, false);
}
```

**Measured:**

| Approach | p50 | p99 | Durable? | Duplicates possible? |
|----------|-----|-----|----------|---------------------|
| LWT `IF NOT EXISTS` | 2.1 ms | 18 ms | ✅ | never |
| Redis `SET NX` | 0.19 ms | 1.2 ms | ⚠️ TTL-bounded | after Redis restart |
| **Read-then-insert on a client_id PK** | **0.31 ms** | **2.1 ms** | ✅ **7 days** | ⚠️ **narrow race** |

### What it costs

**1. A narrow race remains.** Two concurrent retries can both read "not present"
and both insert. Because `client_id` is the primary key, the second **overwrites**
the first rather than duplicating — so `messages_by_client` stays correct. But
they allocated **two different `seq` values**, so `messages_by_seq` has two rows
for one logical message.

The mitigation is to make the seq deterministic from the client ID within the
bucket... which requires coordination... which is what you were avoiding. So:
**accept the race, dedup on read**:

```java
// Reader deduplicates by client_id, keeping the lowest seq.
var seen = new HashSet<String>();
rows.stream().filter(r -> seen.add(r.getString("client_id"))).toList();
```
Measured race rate at 64 concurrent retries of the same `clientId`: **0.4%**.

**2. Double storage.** Every message is written twice (2× write volume, 2×
storage). Measured: 6.2 GB → **11.4 GB**, which erases Scylla's storage advantage
over Postgres entirely.

**3. The dedup window is a TTL** (7 days), where Postgres's unique index is
forever. Better than Redis's 5 minutes, still not permanent.

**4. Correctness now lives in application code.** In Postgres a duplicate is
*impossible* — the database rejects it. Here it's improbable and repaired on
read. That's a real downgrade in the strength of the guarantee, and it's the kind
of thing that's fine until the one time it isn't.

> **This exercise is the argument of the module in miniature.** Every Cassandra
> workaround is individually reasonable, and together they reconstruct — in
> application code, with weaker guarantees — something the relational database
> gave you as a one-line constraint.

---

## Task 5 — Compaction strategies

```bash
docker exec pulse-scylla nodetool compactionstats
docker exec pulse-scylla nodetool tablestats pulse.messages
```

Driven to 200M messages over 2 hours at 100k writes/s:

| | STCS (size-tiered) | LCS (leveled) | **TWCS (time-window)** |
|---|-------------------|---------------|------------------------|
| SSTables per read | 4–**31** | 2–3 | 1–**2** |
| Read p50 | 0.31 ms | **0.14 ms** | **0.11 ms** |
| Read p99.9 | 184 ms | 41 ms | **38 ms** |
| Write amplification | **2.1×** | 11.4× | **1.9×** |
| Space amplification | 2.0× (transient) | **1.1×** | **1.05×** |
| Compaction CPU | 18% | **61%** | **11%** |
| Disk after TTL expiry (90 days) | **+38% bloat** | +4% | **+0.2%** |
| Peak disk during compaction | **2× dataset** | 1.1× | 1.05× |

### Reading it

**STCS** merges similar-sized sstables. On an append-heavy workload it lets
sstable count grow (31 at peak), so a read checks 31 bloom filters and may do 31
disk seeks — hence the 184 ms p99.9. It also needs **2× the dataset in free
disk** to compact the largest tier, and expired TTL rows linger because they're
scattered across tiers with live data.

**LCS** keeps sstables in non-overlapping levels, so a read touches 2–3. Excellent
reads — at **11.4× write amplification and 61% CPU**, because every write is
eventually rewritten through every level. For a write-heavy workload that's the
wrong side of the trade.

**TWCS** groups sstables by time window and only compacts *within* a window. For
append-only time-series data this is nearly ideal:
- New data goes to the current window; old windows are never rewritten (1.9×
  write amplification, close to the theoretical floor).
- A read for recent messages touches 1–2 sstables.
- **TTL expiry drops entire sstables**, because everything in a window expires
  together. That's the +0.2% versus STCS's +38%.

```bash
docker exec pulse-scylla nodetool tablestats pulse.messages | grep -E 'SSTable count|Space used'
```
```
SSTable count: 2
Space used (live): 6.21 GB
Space used (total): 6.22 GB
```

### The choice: TWCS

Justified by workload shape, not preference:

1. **Chat is append-only.** No updates, and deletes are soft. TWCS's assumption —
   that data written together expires together — holds exactly.
2. **Reads are recency-biased.** 98.7% of reads touch messages under 30 days old
   (Module 12's measurement), which live in one or two recent windows.
3. **TTL expiry is the retention mechanism**, and TWCS drops whole sstables
   rather than rewriting to remove expired rows.

Configuration that matters:
```sql
compaction = {
    'class': 'TimeWindowCompactionStrategy',
    'compaction_window_unit': 'DAYS',
    'compaction_window_size': 1,
    'unchecked_tombstone_compaction': 'true'
}
```

⚠️ **The TWCS footgun:** any write with an out-of-order timestamp (a backfill, a
clock skew, a `USING TIMESTAMP`) lands in the wrong window and **prevents that
window from ever being dropped**. Measured: backfilling 1M old messages left a
90-day-old sstable pinned indefinitely. Never backfill into a TWCS table without
`USING TIMESTAMP` matching the original write time — and even then, prefer a
separate table.

---

## Task 6 (stretch) — The ADR

> ## ADR-014: Message storage — sharded PostgreSQL
>
> **Status:** Accepted · **Date:** 2026-08 · **Supersedes:** ADR-009
>
> ### Decision
> Store messages in PostgreSQL 16, sharded by `room_id` across 4096 logical
> shards mapped onto N physical databases, with monthly time partitioning within
> each shard.
>
> ### Evidence
> Measured on identical workloads (1,000 rooms, 50M messages, 10 min):
>
> | | PG ×4 | Scylla ×3 |
> |---|-------|-----------|
> | Inserts/s | 158,400 | **321,000** |
> | Scrollback p50 | 0.16 ms | **0.12 ms** |
> | Scrollback p99.9 | **8 ms** | 38 ms |
> | Idempotency check p50 | **0.08 ms** | 4.8 ms (LWT) |
> | Storage, 50M | 11 GB | 18.6 GB (RF=3) |
>
> Target write rate is 10,000/s sustained, 40,000/s peak — **4× headroom on the
> sharded Postgres configuration.**
>
> ### Consequences we accept
> - Cross-shard queries are scatter-gather; p99 grows as ~`sqrt(shards)`. Unread
>   counts are therefore a maintained Redis aggregate with a nightly rebuild.
> - Schema changes are an orchestrated 5-phase expand/contract across N
>   databases, with a documented runbook and a tolerated version-skew window.
> - Adding capacity means a live shard migration (measured: 184 ms write pause
>   per logical shard, zero loss) rather than `nodetool`.
> - We forgo ~2× the write ceiling and ~40% storage efficiency.
>
> ### Consequences we gain
> - **Transactions**, which the outbox (ADR-013) requires and Cassandra cannot
>   provide. Rebuilding that guarantee on weaker primitives was estimated at 6
>   engineer-weeks with a permanently weaker result.
> - **Ad-hoc queries.** Moderation, analytics and incident investigation do not
>   require a schema designed in advance.
> - **A unique index for idempotency** — permanent, database-enforced, 26×
>   cheaper than the LWT equivalent.
> - An operational model the team already runs in production.
>
> ### Revisit if
> 1. Sustained write rate exceeds **300,000/s** (75% of measured sharded
>    capacity), or physical shard count exceeds 32 — at which point migration
>    orchestration cost dominates.
> 2. Storage cost exceeds **$40k/month** after tiering (ADR-012), where Scylla's
>    40% advantage becomes material.
> 3. We hire or build a team that operates Cassandra/Scylla in production for
>    another workload, removing the operational-familiarity argument.

### The adversarial review, and the revision

**Attack 1:** *"You measured Scylla on 3 nodes and Postgres on 4 shards. That's
not like-for-like — you compared 3 machines to 4."*

**Valid.** Normalized per node: Postgres 39,600 inserts/s/node, Scylla 107,000 —
**Scylla is 2.7× more efficient per machine.** The ADR's throughput comparison
understates Scylla. *Revised:* the evidence table now reports per-node figures,
and the revisit threshold in (1) is restated in nodes, not raw rate.

**Attack 2:** *"The 4.8 ms LWT number is a strawman — you'd never use LWT in
production. Task 4 got it to 0.31 ms."*

**Partly valid.** Task 4's design is 15× faster than LWT. But it introduces a
0.4% duplicate rate requiring read-time dedup, doubles storage (erasing the
storage advantage entirely), and bounds the guarantee to a 7-day TTL. *Revised:*
the ADR now cites 0.31 ms with those three consequences named, rather than the
LWT figure — and the conclusion is unchanged, because the objection is about
*speed* while the decision rests on *guarantee strength*.

**Attack 3:** *"'The team already knows Postgres' is organizational inertia
dressed as engineering."*

**Partly valid, and worth being honest about.** Operational familiarity is a real
input — a database your on-call cannot debug at 3 a.m. has worse *effective*
availability regardless of its benchmarks. But it should not be load-bearing.
*Revised:* familiarity is demoted to a supporting consideration, and revisit
condition (3) now names it explicitly as the thing that would change. **The
decision stands on transactions, idempotency cost, and 4× headroom — all three of
which hold with the familiarity argument removed.**

> **What this exercise teaches:** an ADR that survives review is one where you can
> delete the weakest argument and the conclusion is unchanged. If removing one
> bullet collapses the decision, that bullet was doing too much work — and you
> should go and measure it properly.
