# Lab 13 — Partition, Replicate, Pool, and Close the Hole

**You'll:** partition the message table and measure both sides of the trade, set
up replication and reproduce read-your-writes, insert PgBouncer, and build the
outbox — then `kill -9` between persist and publish and prove nothing is lost.

⏱️ ~110 min.

```bash
alias pg='docker exec -i pulse-postgres psql -U pulse -d pulse'
```

---

## Part A — Partition the table

`src/main/resources/db/migration/V5__partitioning.sql`:

```sql
-- Postgres can't convert a table to partitioned in place; build and swap.
CREATE TABLE messages_new (
    id         bigint      NOT NULL,
    room_id    text        NOT NULL,
    seq        bigint      NOT NULL,
    sender     text        NOT NULL,
    client_id  text        NOT NULL,
    body       text        NOT NULL,
    reply_to   bigint,
    created_at timestamptz NOT NULL DEFAULT now(),
    edited_at  timestamptz,
    deleted_at timestamptz,
    -- The partition key MUST be in every unique constraint. This is the single
    -- biggest constraint partitioning imposes, and it changes your PK.
    PRIMARY KEY (room_id, seq, created_at)
) PARTITION BY RANGE (created_at);

CREATE UNIQUE INDEX idx_messages_dedup_new
    ON messages_new (room_id, client_id, created_at);

CREATE INDEX idx_messages_thread_new
    ON messages_new (reply_to, id) WHERE reply_to IS NOT NULL;

-- A default partition catches rows outside every range. Without it, an insert
-- for an unprovisioned month FAILS. With it, they land somewhere findable.
CREATE TABLE messages_default PARTITION OF messages_new DEFAULT;
```

`code/create_partitions.sql` — generate a year:

```sql
DO $$
DECLARE
    start_month date := date_trunc('month', now())::date - interval '6 months';
    m date;
BEGIN
    FOR i IN 0..17 LOOP
        m := (start_month + (i || ' months')::interval)::date;
        EXECUTE format(
            'CREATE TABLE IF NOT EXISTS messages_%s PARTITION OF messages_new
             FOR VALUES FROM (%L) TO (%L)',
            to_char(m, 'YYYY_MM'), m, (m + interval '1 month')::date);
    END LOOP;
END $$;
```

```bash
pg -f code/create_partitions.sql
pg -c "SELECT count(*) FROM pg_inherits WHERE inhparent = 'messages_new'::regclass;"
```
**Expected:**
```
 count
-------
    19
```
(18 monthly + the default.)

Migrate the data:
```bash
pg -c "INSERT INTO messages_new SELECT * FROM messages;"
pg -c "BEGIN;
       ALTER TABLE messages RENAME TO messages_old;
       ALTER TABLE messages_new RENAME TO messages;
       COMMIT;"
pg -c "ANALYZE messages;"
```

Confirm routing:
```bash
pg -c "SELECT tableoid::regclass AS partition, count(*)
       FROM messages GROUP BY 1 ORDER BY 1 LIMIT 5;"
```
**Expected:**
```
     partition      |  count
--------------------+---------
 messages_2026_03   | 2814022
 messages_2026_04   | 2903118
 messages_2026_05   | 2811904
 ...
```

✅ Rows landed in child tables by `created_at`, automatically.

> **Note the PK changed** from `(room_id, seq)` to `(room_id, seq, created_at)`.
> Postgres requires the partition key in every unique index, because it can only
> enforce uniqueness within a partition. **This weakens your guarantee**: the same
> `(room_id, seq)` could exist in two different months. In practice `seq` is
> monotonic so it can't happen — but it's now enforced by your code, not by the
> database. Write that down; it's the kind of thing that bites in year three.

---

## Part B — Measure both sides of the trade

### The retention win

```bash
# Unpartitioned (the old table)
pg -c "\timing on
       DELETE FROM messages_old WHERE created_at < '2026-04-01';"
```
**Expected:**
```
DELETE 5717140
Time: 184291.402 ms  (3 min 4 s)
```
```bash
pg -c "SELECT pg_size_pretty(pg_relation_size('messages_old'));"
pg -c "SELECT n_dead_tup FROM pg_stat_user_tables WHERE relname='messages_old';"
```
```
 7891 MB          <-- unchanged, space NOT returned
 5717140          <-- dead tuples for autovacuum to chew through
```

Measure the WAL:
```bash
pg -c "SELECT pg_size_pretty(pg_current_wal_lsn() - :'start_lsn'::pg_lsn);"
```
```
 1284 MB
```

Now the partitioned version:
```bash
pg -c "\timing on
       DROP TABLE messages_2026_03, messages_2026_04;"
```
**Expected:**
```
DROP TABLE
Time: 41.204 ms
```
```bash
pg -c "SELECT pg_size_pretty(pg_total_relation_size('messages'));"
```
```
 6104 MB          <-- space returned IMMEDIATELY
```

| | `DELETE` | `DROP TABLE` |
|---|---------|-------------|
| Time | **184,291 ms** | **41 ms** |
| WAL generated | 1,284 MB | **~8 KB** |
| Dead tuples | 5,717,140 | **0** |
| Space returned | **none** | **immediately** |
| Blocks other queries | yes, heavily | brief `ACCESS EXCLUSIVE` only |

✅ **4,500× faster and 160,000× less WAL.** That's the whole argument.

### The read tax

Scrollback with **no** time predicate:
```bash
pg -c "EXPLAIN (ANALYZE, BUFFERS)
SELECT id, sender, body FROM messages
WHERE room_id='room.42' AND seq < 48213 AND deleted_at IS NULL
ORDER BY seq DESC LIMIT 50;"
```
**Expected:**
```
 Limit  (actual time=1.204..2.891 rows=50 loops=1)
   ->  Merge Append  (actual time=1.202..2.884 rows=50 loops=1)
         Sort Key: messages.seq DESC
         ->  Index Scan Backward using messages_2026_05_pkey  (actual rows=50)
         ->  Index Scan Backward using messages_2026_06_pkey  (actual rows=50)
         ->  Index Scan Backward using messages_2026_07_pkey  (actual rows=50)
         ...  (16 partitions)
         Buffers: shared hit=1284
 Execution Time: 2.941 ms
```

✅ **2.94 ms versus 0.121 ms unpartitioned — 24× slower.** No pruning happened:
without a `created_at` predicate, Postgres must scan **every** partition and merge.

Now add the time hint derived from the Snowflake cursor:
```bash
pg -c "EXPLAIN (ANALYZE, BUFFERS)
SELECT id, sender, body FROM messages
WHERE room_id='room.42' AND seq < 48213 AND deleted_at IS NULL
  AND created_at > '2026-07-15'::timestamptz
ORDER BY seq DESC LIMIT 50;"
```
**Expected:**
```
 Limit  (actual time=0.048..0.139 rows=50 loops=1)
   ->  Merge Append  (actual time=0.046..0.132 rows=50 loops=1)
         ->  Index Scan Backward using messages_2026_07_pkey  (actual rows=50)
         ->  Index Scan Backward using messages_2026_08_pkey  (actual rows=0)
         Buffers: shared hit=62
 Execution Time: 0.164 ms
```
```
Partitions removed: 16
```

✅ **0.164 ms — back to within 36% of unpartitioned**, and 16 partitions pruned.

Implement the hint from the Snowflake timestamp:

```java
public List<MessageNew> scrollback(String roomId, long cursorSeq, long cursorId, int limit) {
    // The Snowflake ID contains its creation time. Look back one day from it to
    // absorb clock skew and out-of-order inserts near a partition boundary.
    Instant hint = Instant.ofEpochMilli(SnowflakeIdGenerator.timestampOf(cursorId))
                          .minus(Duration.ofDays(1));

    return jdbc.sql("""
            SELECT id, client_id, seq, room_id, sender, body,
                   extract(epoch from created_at)*1000 AS ts, reply_to
            FROM messages
            WHERE room_id = :room AND seq < :seq AND deleted_at IS NULL
              AND created_at > :hint
            ORDER BY seq DESC LIMIT :limit
            """)
            .param("room", roomId).param("seq", cursorSeq)
            .param("hint", Timestamp.from(hint)).param("limit", limit)
            .query(MessageNew.class).list();
}
```

> ⚠️ **The hint must be a lower bound, never exact.** If a page straddles a
> partition boundary and your hint is too tight, you silently return fewer rows
> and the client sees a gap. One day of slack costs one extra partition scan and
> removes the entire class of bug.

Record it:
```markdown
## Module 13 — Partitioning

- DELETE 5.7M rows:  184,291 ms, 1,284 MB WAL, 5.7M dead tuples, no space returned
- DROP TABLE:             41 ms,     ~8 KB WAL,    0 dead tuples, space returned
  => 4,500x faster, 160,000x less WAL
- Scrollback read tax: 0.121ms -> 2.94ms without a time hint (24x)
                                -> 0.164ms with one (16 partitions pruned)
```

---

## Part C — Streaming replication

`infra/compose.replica.yml`:

```yaml
name: pulse-replica

services:
  postgres-primary:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: pulse
      POSTGRES_PASSWORD: pulse
      POSTGRES_DB: pulse
    ports: [ "5432:5432" ]
    command:
      - postgres
      - -c
      - wal_level=replica
      - -c
      - max_wal_senders=10
      - -c
      - max_replication_slots=10
      - -c
      - hot_standby=on
      - -c
      - synchronous_commit=on
      - -c
      - log_min_duration_statement=200
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U pulse"]
      interval: 5s
      retries: 10

  postgres-replica:
    image: postgres:16-alpine
    depends_on:
      postgres-primary: { condition: service_healthy }
    ports: [ "5433:5432" ]
    environment:
      PGPASSWORD: pulse
    user: postgres
    command:
      - bash
      - -c
      - |
        if [ ! -s /var/lib/postgresql/data/PG_VERSION ]; then
          pg_basebackup -h postgres-primary -U pulse -D /var/lib/postgresql/data \
                        -Fp -Xs -R -S replica1 -C -P
        fi
        exec postgres -c hot_standby=on -c hot_standby_feedback=on
```

```bash
docker compose -f infra/compose.replica.yml up -d
sleep 20
docker exec pulse-replica-postgres-primary-1 psql -U pulse -d pulse -c \
  "SELECT client_addr, state, sync_state, replay_lag FROM pg_stat_replication;"
```
**Expected:**
```
 client_addr | state     | sync_state |   replay_lag
-------------+-----------+------------+-----------------
 172.20.0.3  | streaming | async      | 00:00:00.000841
```

```bash
docker exec pulse-replica-postgres-replica-1 psql -U pulse -d pulse -c \
  "SELECT pg_is_in_recovery();"
```
```
 t
```

### Reproduce read-your-writes

```bash
# Induce lag: hammer the primary while reading the replica
pgbench -h localhost -p 5432 -U pulse -c 30 -T 60 pulse &

for i in $(seq 1 20); do
  ID=$(pg -tAc "INSERT INTO messages (id, room_id, seq, sender, client_id, body)
                VALUES ($((RANDOM * 100000 + i)), 'room.rw', $i, 'alice', 'c-rw-$i', 'hi')
                RETURNING id;")
  FOUND=$(docker exec pulse-replica-postgres-replica-1 psql -U pulse -d pulse -tAc \
          "SELECT count(*) FROM messages WHERE id = $ID;")
  echo "write $i -> replica sees: $FOUND"
done
```
**Expected:**
```
write 1 -> replica sees: 0
write 2 -> replica sees: 0
write 3 -> replica sees: 1
write 4 -> replica sees: 0
...
```

✅ **Alice's own message is missing from her history load, intermittently.** This
is the bug, and it only appears under write load — which is why it reaches
production.

Measure the window:
```bash
docker exec pulse-replica-postgres-replica-1 psql -U pulse -d pulse -tAc \
  "SELECT now() - pg_last_xact_replay_timestamp();"
```
```
 00:00:00.412881
```
**412 ms of lag** under load. Plenty of time for a client to round-trip.

### The fixes, measured

```java
@Component
public class ReadRouter {

    /** userId -> when their sticky-to-primary window expires. */
    private final Cache<String, Long> recentWriters = Caffeine.newBuilder()
            .expireAfterWrite(Duration.ofSeconds(10)).build();

    public JdbcClient forRead(String userId) {
        Long until = recentWriters.getIfPresent(userId);
        if (until != null && System.currentTimeMillis() < until) {
            primaryReads.increment();
            return primaryJdbc;              // sticky window
        }
        replicaReads.increment();
        return replicaJdbc;
    }

    public void recordWrite(String userId) {
        recentWriters.put(userId, System.currentTimeMillis() + 5_000);
    }
}
```

| Approach | Stale reads (10,000 trials) | Replica read share | Write latency |
|----------|----------------------------|--------------------|---------------|
| Naive (always replica) | **1,847 (18.5%)** | 100% | 1.2 ms |
| Sticky 5 s window | **0** | **91%** | 1.2 ms |
| LSN wait | 0 | 96% | 1.2 ms + wait |
| `synchronous_commit=remote_apply` | 0 | 100% | **8.4 ms** (7×) |
| **Optimistic echo (Pulse's default)** | **0** | 100% | 1.2 ms |

✅ **The sticky window keeps 91% of reads on the replica and eliminates stale
reads**, at the cost of one cache lookup. `remote_apply` works too, but a 7×
write-latency penalty on every write to fix a read bug is a bad trade.

**And the best answer remains "don't read it back"** — Pulse's optimistic
rendering (Module 05) means the sender already has the message. The sticky
window exists for the *second device* case only.

---

## Part D — PgBouncer

`infra/pgbouncer.ini`:
```ini
[databases]
pulse = host=postgres-primary port=5432 dbname=pulse

[pgbouncer]
listen_addr = 0.0.0.0
listen_port = 6432
auth_type = scram-sha-256
auth_file = /etc/pgbouncer/userlist.txt
pool_mode = transaction
max_client_conn = 10000
default_pool_size = 25
reserve_pool_size = 5
reserve_pool_timeout = 3
server_idle_timeout = 60
stats_period = 30
admin_users = pulse
```

```yaml
  pgbouncer:
    image: edoburu/pgbouncer:latest
    ports: [ "6432:6432" ]
    volumes:
      - ./pgbouncer.ini:/etc/pgbouncer/pgbouncer.ini:ro
      - ./userlist.txt:/etc/pgbouncer/userlist.txt:ro
    depends_on:
      postgres-primary: { condition: service_healthy }
```

```yaml
spring:
  datasource:
    url: jdbc:postgresql://localhost:6432/pulse?prepareThreshold=0
    hikari:
      maximum-pool-size: 20
```

> **`prepareThreshold=0` is mandatory in transaction mode.** Without it pgjdbc
> prepares on one server connection and executes on another:
> ```
> ERROR: prepared statement "S_1" does not exist
> ```
> — an error that appears only under concurrency, which is the worst kind to
> debug.

Measure the multiplexing:

```bash
# 20 app instances x 20 connections, direct
for i in $(seq 1 20); do SERVER_PORT=$((9000+i)) ./mvnw spring-boot:run & done
pg -c "SELECT count(*), state FROM pg_stat_activity WHERE datname='pulse' GROUP BY state;"
```
**Expected — direct:**
```
 count |  state
-------+---------
   400 | idle
     6 | active
```
**400 backend processes, 6 doing work.** ~4 GB of RAM to be idle.

Through PgBouncer:
```bash
psql -h localhost -p 6432 -U pulse pgbouncer -c "SHOW POOLS;"
```
**Expected:**
```
 database | user  | cl_active | cl_waiting | sv_active | sv_idle | sv_used
----------+-------+-----------+------------+-----------+---------+---------
 pulse    | pulse |       400 |          0 |         6 |      19 |       0
```

✅ **400 client connections onto 25 server connections.**

| | Direct | PgBouncer |
|---|--------|-----------|
| Postgres backends | 400 | **25** |
| Postgres RSS | 3.9 GB | **412 MB** |
| p50 query | 1.2 ms | 1.4 ms |
| p99 query | 41 ms | **8 ms** |
| Max app instances before `too many connections` | 5 | **500** |

Note **p99 improved** — fewer backends means less context switching and less
lock contention inside Postgres. Multiplexing is not just a capacity fix.

Watch for saturation:
```bash
watch -n1 "psql -h localhost -p 6432 -U pulse pgbouncer -c 'SHOW POOLS;'"
```
**`cl_waiting > 0` sustained** means your pool is too small or your transactions
are too long. It's the PgBouncer equivalent of `hikaricp_connections_pending`.

---

## Part E — The transactional outbox

**The module's most important piece.**

`src/main/resources/db/migration/V6__outbox.sql`:

```sql
CREATE TABLE outbox (
    id           bigserial   PRIMARY KEY,
    aggregate_id text        NOT NULL,          -- roomId
    event_type   text        NOT NULL,
    payload      jsonb       NOT NULL,
    created_at   timestamptz NOT NULL DEFAULT now(),
    published_at timestamptz,
    attempts     int         NOT NULL DEFAULT 0
);

-- PARTIAL index: only the unpublished backlog is indexed. Once a row is
-- published it leaves the index entirely, so the index stays tiny regardless
-- of how many millions of rows the table has accumulated.
CREATE INDEX idx_outbox_unpublished ON outbox (id) WHERE published_at IS NULL;
```

### Atomic write

```java
@Transactional
public SendResult send(String roomId, String sender, MessageCreate create) {
    var dedupHit = dedup.getIfPresent(roomId + "|" + create.clientId());
    if (dedupHit != null) return new SendResult(dedupHit, true);

    long id = ids.nextId();
    long seq = sequences.next(roomId);

    var inserted = jdbc.sql("""
            INSERT INTO messages (id, room_id, seq, sender, client_id, body, reply_to)
            VALUES (:id,:room,:seq,:sender,:cid,:body,:reply)
            ON CONFLICT (room_id, client_id, created_at) DO NOTHING
            RETURNING id, client_id, seq, room_id, sender, body,
                      extract(epoch from created_at)*1000 AS ts, reply_to
            """)
            .params(...).query(MessageNew.class).optional();

    if (inserted.isEmpty()) {
        sequences.recordGap(roomId, seq);
        return new SendResult(findByClientId(roomId, create.clientId()).orElseThrow(), true);
    }

    // SAME TRANSACTION. This is the entire point.
    jdbc.sql("""
            INSERT INTO outbox (aggregate_id, event_type, payload)
            VALUES (:room, 'message.new', :payload::jsonb)
            """)
            .param("room", roomId)
            .param("payload", json.writeValueAsString(inserted.get()))
            .update();

    dedup.put(roomId + "|" + create.clientId(), inserted.get());
    return new SendResult(inserted.get(), false);
}
```

**No `streamFanout.append()` in the send path any more.** The relay does it.

### The relay

```java
@Component
public class OutboxRelay {

    private static final int BATCH = 100;

    @Scheduled(fixedDelay = 50)
    @Transactional
    public void relay() {
        var batch = jdbc.sql("""
                SELECT id, aggregate_id, event_type, payload::text AS payload
                FROM outbox
                WHERE published_at IS NULL
                ORDER BY id
                LIMIT :limit
                FOR UPDATE SKIP LOCKED
                """)                          -- <-- lets N relays run concurrently
                .param("limit", BATCH)
                .query(OutboxRow.class).list();

        if (batch.isEmpty()) return;

        var publishedIds = new ArrayList<Long>(batch.size());
        for (OutboxRow row : batch) {
            try {
                streamFanout.append(row.aggregateId(),
                        json.readValue(row.payload(), Envelope.class));
                publishedIds.add(row.id());
            } catch (Exception e) {
                // Leave it unpublished; the next pass retries. Do NOT abort the
                // whole batch for one bad row.
                jdbc.sql("UPDATE outbox SET attempts = attempts + 1 WHERE id = :id")
                    .param("id", row.id()).update();
                relayFailures.increment();
            }
        }

        if (!publishedIds.isEmpty()) {
            jdbc.sql("UPDATE outbox SET published_at = now() WHERE id = ANY(:ids)")
                .param("ids", publishedIds.toArray(Long[]::new)).update();
            relayPublished.increment(publishedIds.size());
        }
    }

    /** Backlog depth: the number that tells you the relay is falling behind. */
    @Scheduled(fixedRate = 10_000)
    public void reportBacklog() {
        Long depth = jdbc.sql("SELECT count(*) FROM outbox WHERE published_at IS NULL")
                         .query(Long.class).single();
        registry.gauge("outbox.backlog", depth);
    }

    /** Published rows are dead weight; drop them in bulk. */
    @Scheduled(cron = "0 */10 * * * *")
    public void prune() {
        jdbc.sql("DELETE FROM outbox WHERE published_at < now() - interval '1 hour'")
            .update();
    }
}
```

---

## Part F — Prove the hole is closed

**Before the outbox**, kill the process between persist and publish:

```java
@Value("${pulse.debug.crash-after-persist:false}")
private boolean crashAfterPersist;
// in send(), after the insert commits:
if (crashAfterPersist) Runtime.getRuntime().halt(1);     // no shutdown hooks
```

```bash
PULSE_DEBUG_CRASH_AFTER_PERSIST=true ./mvnw spring-boot:run &
./code/publish.sh room.60 "will this survive?"
sleep 5
pg -c "SELECT seq, body FROM messages WHERE room_id='room.60';"
docker exec pulse-redis redis-cli XLEN 'room:{60}:stream'
```
**Expected (no outbox):**
```
 seq |        body
-----+---------------------
   1 | will this survive?
(integer) 0
```

✅ **Persisted, never published.** No subscriber will ever receive it. A client
that was connected the whole time has no gap to detect (the `seq` was used) and
will never see it.

**After the outbox**, same test:
```bash
pg -c "SELECT seq, body FROM messages WHERE room_id='room.61';"
pg -c "SELECT id, published_at FROM outbox WHERE aggregate_id='room.61';"
```
**Immediately after the crash:**
```
 seq |        body
-----+---------------------
   1 | will this survive?

 id | published_at
----+--------------
 42 |              <-- NULL: unpublished, and the relay will find it
```

Restart, and:
```bash
./mvnw spring-boot:run &
sleep 3
docker exec pulse-redis redis-cli XLEN 'room:{61}:stream'
pg -c "SELECT id, published_at FROM outbox WHERE aggregate_id='room.61';"
```
**Expected:**
```
(integer) 1
 id | published_at
----+-------------------------------
 42 | 2026-08-23 14:41:02.884+00
```

✅ **Recovered automatically.** The relay found the unpublished row and published
it. The message was late, not lost.

Now the relay-crash case (publish then crash before the `UPDATE`):
```bash
PULSE_DEBUG_CRASH_AFTER_PUBLISH=true ./mvnw spring-boot:run &
./code/publish.sh room.62 "duplicate incoming"
# restart
docker exec pulse-redis redis-cli XLEN 'room:{62}:stream'
pg -c "SELECT count(*) FROM messages WHERE room_id='room.62';"
```
**Expected:**
```
(integer) 2       <-- published TWICE
 1                <-- stored ONCE
```

✅ **At-least-once at the relay, absorbed by the consumer's idempotency.** The
duplicate stream entry deserializes to the same `clientId`, the insert is a
no-op, and the broadcast is suppressed. The full chain holds.

Measure the cost:
```bash
k6 run -e ROOMS=100 -e SEND_EVERY=60000 ../../06-load-testing-harness/code/pulse-load.js
```

| | Direct append (Module 09) | Outbox relay |
|---|--------------------------|--------------|
| p50 fan-out | 21 ms | **73 ms** |
| p99 | 192 ms | **310 ms** |
| Send-path latency (client's ack) | 18 ms | **11 ms** (one less network hop!) |
| Messages persisted-not-published on crash | **1 per crash** | **0** |
| Extra Postgres writes | — | +1 insert, +1 update per message |
| Outbox backlog at steady state | — | 3–40 rows |

✅ **+52 ms p50 fan-out for zero lost messages.** And note the *send* path got
*faster* — the client's ack no longer waits for the Redis append.

Tune the relay interval:

| `fixedDelay` | p50 fan-out | Postgres queries/s | Backlog |
|--------------|-------------|--------------------|---------|
| 500 ms | 271 ms | 2 | 160 |
| 50 ms | **73 ms** | 20 | 40 |
| 10 ms | 38 ms | 100 | 8 |
| `LISTEN/NOTIFY` (event-driven) | **26 ms** | 0 polls | 1–3 |

The `LISTEN/NOTIFY` version removes polling entirely:
```sql
CREATE FUNCTION notify_outbox() RETURNS trigger AS $$
BEGIN PERFORM pg_notify('outbox', ''); RETURN NULL; END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER outbox_notify AFTER INSERT ON outbox
FOR EACH STATEMENT EXECUTE FUNCTION notify_outbox();
```
> ⚠️ `LISTEN/NOTIFY` **does not work through PgBouncer in transaction mode** —
> the listening connection is returned to the pool. Give the relay a direct
> connection to Postgres, bypassing PgBouncer. That's a real deployment
> constraint and a good example of transaction pooling's cost.

Record it:
```markdown
## Module 13 — Replication, pooling, outbox

- Read-your-writes: 18.5% stale reads naive -> 0% with a 5s sticky window
  (91% of reads still served by the replica)
- PgBouncer: 400 backends -> 25; Postgres RSS 3.9GB -> 412MB; p99 41ms -> 8ms
- Outbox: +52ms p50 fan-out, -7ms send-path latency, 0 messages lost on crash
- Relay crash publishes twice; absorbed by clientId idempotency
- LISTEN/NOTIFY relay: 26ms p50, no polling — but needs a direct connection
```

---

## What you built

- Time partitioning: **4,500× faster retention**, plus the read tax measured and
  clawed back with a Snowflake-derived time hint.
- Streaming replication with **reproduced** read-your-writes failures and a
  sticky-window fix that keeps 91% of reads on the replica.
- PgBouncer: 400 connections onto 25, with p99 *improving*.
- **A transactional outbox that closes the dual-write hole**, proven by killing
  the process at both dangerous points.

The delivery chain is now complete end to end:
```
persist ─atomic─ outbox ─at-least-once─ stream ─at-least-once─ consumer ─idempotent─ client
```

Now do [`challenge.md`](./challenge.md).

Then: [Module 14 — Sharding & Wide-Column](../14-sharding-and-wide-column/).
