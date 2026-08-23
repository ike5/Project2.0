# Solutions — Module 13

---

## Task 1 — Partition management

### The failure, first

```bash
pg -c "DROP TABLE messages_default;"
pg -c "SELECT max(to_date(right(relname, 7), 'YYYY_MM'))
       FROM pg_class WHERE relname LIKE 'messages_2%';"
```
```
 2026-09-01
```
Now insert past it:
```bash
pg -c "INSERT INTO messages (id, room_id, seq, sender, client_id, body, created_at)
       VALUES (1, 'room.x', 1, 'alice', 'c-future', 'hello', '2026-11-15');"
```
**Expected:**
```
ERROR:  no partition of relation "messages" found for row
DETAIL:  Partition key of the failing row contains (created_at) = (2026-11-15 00:00:00+00).
```

✅ **Every insert fails.** Not degraded — *stopped*. Chat is completely down, at
midnight on the first of a month, with an error that mentions nothing about
partitions being unprovisioned.

With the DEFAULT partition restored, inserts succeed but pile into
`messages_default`, which grows unbounded and cannot be dropped for retention.
**Better, but still a slow-motion outage.**

### Automation

```sql
CREATE EXTENSION IF NOT EXISTS pg_partman SCHEMA partman;

SELECT partman.create_parent(
    p_parent_table    => 'public.messages',
    p_control         => 'created_at',
    p_interval        => '1 month',
    p_premake         => 6,                    -- always 6 months ahead
    p_default_table   => true
);

UPDATE partman.part_config
   SET retention           = '3 months',
       retention_keep_table = false,           -- actually DROP, don't detach
       infinite_time_partitions = true
 WHERE parent_table = 'public.messages';
```
```sql
-- pg_cron, or an external scheduler
SELECT cron.schedule('partman-maintenance', '0 3 * * *',
                     $$CALL partman.run_maintenance_proc()$$);
```

Or, without extensions:
```java
@Scheduled(cron = "0 0 3 * * *")
public void maintainPartitions() {
    for (int i = 0; i <= 6; i++) {
        var month = YearMonth.now().plusMonths(i);
        jdbc.sql("""
                CREATE TABLE IF NOT EXISTS %s PARTITION OF messages
                FOR VALUES FROM ('%s') TO ('%s')
                """.formatted(partitionName(month),
                              month.atDay(1), month.plusMonths(1).atDay(1)))
            .update();
    }
    var cutoff = YearMonth.now().minusMonths(3);
    jdbc.sql("DROP TABLE IF EXISTS " + partitionName(cutoff)).update();
}
```

### The predictive alert — the part that matters

```java
@Scheduled(fixedRate = 3_600_000)
public void checkPartitionRunway() {
    LocalDate furthest = jdbc.sql("""
            SELECT max(to_date(right(c.relname, 7), 'YYYY_MM'))
            FROM pg_inherits i JOIN pg_class c ON c.oid = i.inhrelid
            WHERE i.inhparent = 'messages'::regclass AND c.relname ~ '_[0-9]{4}_[0-9]{2}$'
            """).query(LocalDate.class).single();

    long daysOfRunway = ChronoUnit.DAYS.between(LocalDate.now(), furthest);
    registry.gauge("db.partition.runway.days", daysOfRunway);

    if (daysOfRunway < 30) log.error("PARTITION RUNWAY {} DAYS", daysOfRunway);
}
```
```yaml
- alert: PartitionRunwayLow
  expr: db_partition_runway_days < 45
  for: 1h
  annotations:
    summary: "Only {{ $value }} days of message partitions remain"
    runbook: "Run partman.run_maintenance_proc() or check the maintenance job"
```

✅ **45 days of warning.** Also alert on `messages_default` being non-empty —
rows landing there means the runway check failed and you're in the slow-motion
version:

```yaml
- alert: MessagesInDefaultPartition
  expr: pg_stat_user_tables_n_live_tup{relname="messages_default"} > 0
  for: 5m
```

> A monitoring rule that fires *after* the outage is not monitoring. Every
> resource that can be exhausted needs a **runway metric**, not just a
> utilization metric.

---

## Task 2 — Horizontal relay safety

```java
@Test
void threeRelaysNeverDoublePublish() throws Exception {
    var published = new ConcurrentHashMap<Long, String>();
    int messages = 10_000;

    for (int i = 0; i < messages; i++) insertOutboxRow(i);

    var relays = IntStream.range(0, 3)
            .mapToObj(n -> new OutboxRelay("relay-" + n, id -> {
                String prior = published.putIfAbsent(id, "relay-" + n);
                if (prior != null) fail("row " + id + " published by " + prior + " AND relay-" + n);
            }))
            .toList();

    try (var ex = Executors.newVirtualThreadPerTaskExecutor()) {
        relays.forEach(r -> ex.submit(r::runUntilDrained));
    }

    assertEquals(messages, published.size());
    assertEquals(0L, unpublishedCount());
}
```
**Expected:**
```
threeRelaysNeverDoublePublish() PASSED   (10,000 rows, 0 duplicates)
```

Now break it — remove `SKIP LOCKED`:
```sql
SELECT * FROM outbox WHERE published_at IS NULL ORDER BY id LIMIT 100 FOR UPDATE;
```
**Expected:**
```
threeRelaysNeverDoublePublish() PASSED   (but takes 8x longer)
```
✅ Still correct — `FOR UPDATE` **blocks** rather than duplicating — but relays 2
and 3 sit waiting on relay 1's locks the whole time. You get correctness with
zero parallelism.

Remove `FOR UPDATE` entirely:
```
org.opentest4j.AssertionFailedError: row 4821 published by relay-0 AND relay-2
```
✅ Duplicates immediately.

### Throughput scaling

| Relays | Rows/s | Speedup | Postgres CPU | `lock_waits` |
|--------|--------|---------|-------------|--------------|
| 1 | 18,400 | 1.0× | 12% | 0 |
| 2 | 34,100 | 1.85× | 24% | 4 |
| 4 | 51,200 | **2.78×** | 51% | 812 |
| 8 | 52,900 | **2.87×** | 88% | 9,140 |

**Scaling stops at ~4 relays.** Why:

1. **`ORDER BY id` forces every relay to start scanning at the same place.**
   Relay 2 must walk over the 100 rows relay 1 just locked before it finds
   unlocked ones. At 8 relays, relay 8 skips 700 locked rows on every pass —
   `SKIP LOCKED` isn't free, it's a per-row lock probe.
2. `pg_stat_activity` confirms it:
   ```sql
   SELECT wait_event_type, wait_event, count(*) FROM pg_stat_activity
   WHERE query LIKE '%outbox%' GROUP BY 1,2;
   ```
   ```
    wait_event_type | wait_event | count
   -----------------+------------+-------
    Lock            | tuple      |     6
   ```

**The fix — partition the work, don't contend for it** (the same lesson as
Module 11's sweeper):

```sql
ALTER TABLE outbox ADD COLUMN shard smallint
    GENERATED ALWAYS AS (abs(hashtext(aggregate_id)) % 16) STORED;
CREATE INDEX ON outbox (shard, id) WHERE published_at IS NULL;
```
```java
// Each relay owns a disjoint set of shards. No contention at all.
var myShards = shardsFor(relayIndex, relayCount);   // e.g. [0,4,8,12]
jdbc.sql("""
        SELECT ... FROM outbox
        WHERE published_at IS NULL AND shard = ANY(:shards)
        ORDER BY id LIMIT :limit
        FOR UPDATE SKIP LOCKED
        """)
```

| Relays | `SKIP LOCKED` only | Sharded |
|--------|--------------------|---------|
| 1 | 18,400/s | 18,200/s |
| 4 | 51,200/s | **71,400/s** |
| 8 | 52,900/s | **139,800/s** |
| 16 | 51,100/s | **241,000/s** |

✅ **Near-linear to 16 relays.** Sharding by `aggregate_id` also preserves
per-room ordering, which `SKIP LOCKED` alone does *not* guarantee — a subtle
correctness improvement, not just speed.

---

## Task 3 — Poisoned outbox rows

```sql
ALTER TABLE outbox ADD COLUMN next_attempt_at timestamptz NOT NULL DEFAULT now();
DROP INDEX idx_outbox_unpublished;
CREATE INDEX idx_outbox_ready ON outbox (shard, next_attempt_at, id)
    WHERE published_at IS NULL;
```

```java
var batch = jdbc.sql("""
        SELECT id, aggregate_id, event_type, payload::text AS payload, attempts
        FROM outbox
        WHERE published_at IS NULL
          AND shard = ANY(:shards)
          AND next_attempt_at <= now()          -- <-- backed-off rows are invisible
        ORDER BY id LIMIT :limit
        FOR UPDATE SKIP LOCKED
        """).params(...).query(OutboxRow.class).list();
```

```java
private void handleFailure(OutboxRow row, Exception e) {
    int attempts = row.attempts() + 1;

    if (attempts >= MAX_ATTEMPTS) {                       // 8
        jdbc.sql("""
                INSERT INTO outbox_dlq (id, aggregate_id, event_type, payload,
                                        attempts, error, failed_at)
                SELECT id, aggregate_id, event_type, payload, :attempts, :err, now()
                FROM outbox WHERE id = :id
                """).params(...).update();
        jdbc.sql("DELETE FROM outbox WHERE id = :id").param("id", row.id()).update();
        deadLettered.increment();
        log.error("OUTBOX DEAD LETTER id={} room={} after {} attempts",
                  row.id(), row.aggregateId(), attempts, e);
        return;
    }

    // Exponential backoff with jitter: 100ms, 200ms, 400ms ... capped at 5 min.
    long delayMs = Math.min(300_000, (long) (100 * Math.pow(2, attempts)));
    long jittered = ThreadLocalRandom.current().nextLong(delayMs / 2, delayMs);

    jdbc.sql("""
            UPDATE outbox
               SET attempts = :attempts,
                   next_attempt_at = now() + make_interval(secs => :delay)
             WHERE id = :id
            """).params(...).update();
}
```

### Prove a poison row costs nothing

```bash
pg -c "INSERT INTO outbox (aggregate_id, event_type, payload)
       VALUES ('room.nonexistent', 'message.new', '{\"malformed\": true}'::jsonb);"
```

| | Without backoff | With backoff |
|---|----------------|--------------|
| Retries in 10 minutes | **12,000** (every 50 ms) | **8** |
| Relay CPU spent on it | 4.1% | **0.003%** |
| Log lines | 12,000 | 8 |
| Time to dead-letter | never | **~3 minutes** |
| Effect on healthy throughput | −4% | **0%** |

```bash
curl -s localhost:8080/actuator/metrics/outbox.dead.lettered | jq '.measurements[0].value'
pg -c "SELECT id, aggregate_id, attempts, left(error, 60) FROM outbox_dlq;"
```
```
1
 id | aggregate_id      | attempts |                    error
----+-------------------+----------+----------------------------------------------
 42 | room.nonexistent  |        8 | com.fasterxml.jackson.databind.exc.Mismatched
```

✅ **1,500× fewer retries and zero impact on healthy throughput.**

Now the systemic case — 100,000 poison rows from a bad deploy:
```
Without backoff: relay does 2,400,000 futile attempts/minute, throughput -94%
With backoff:    relay drains all 100,000 to DLQ in ~4 minutes, healthy
                 throughput unaffected throughout
```

> The backoff isn't primarily about the one bad row — it's about the *class*
> failure, where a deploy poisons everything at once. Without backoff that's an
> outage; with it, it's a full DLQ and an alert.

---

## Task 4 — Replica lag drivers

Isolate each variable:

| Scenario | Write rate | Replica reads | Long query | `replay_lag` |
|----------|-----------|---------------|-----------|-------------|
| Baseline | 1k/s | 0 | no | **0.8 ms** |
| High writes | 40k/s | 0 | no | **41 ms** |
| High writes + replica reads | 40k/s | 8k/s | no | **214 ms** |
| High writes + long query | 40k/s | 0 | **5 min analytics query** | **312,000 ms (5.2 min)** |
| + `hot_standby_feedback=on` | 40k/s | 0 | 5 min query | 41 ms, but **primary bloat** |

### What actually drives lag

**1. Write volume (moderate effect).** WAL replay on the replica is
single-threaded. At 40k inserts/s, replay is CPU-bound on one core. Fix:
`wal_compression=on` (measured: 41 ms → 28 ms, at 6% primary CPU).

**2. Replica read load (significant).** Reads compete with the replay process for
I/O and buffers. 8k reads/s took lag from 41 ms to 214 ms.

**3. Long-running queries on the replica (catastrophic).** This is the one people
don't expect:

```sql
SHOW max_standby_streaming_delay;    -- default 30s
```

When replay needs to remove a row a running query might still need, the replica
must choose:
- **Pause replay** (lag grows) until `max_standby_streaming_delay` elapses, then
- **Cancel the query**: `ERROR: canceling statement due to conflict with recovery`

A 5-minute analytics query created **5.2 minutes** of lag. `hot_standby_feedback=on`
fixes the lag by telling the primary not to vacuum those rows — which means
**the primary bloats instead**. You've moved the problem, and on a
high-write table you've moved it somewhere worse.

**The verdict: don't run analytics on the replica that serves your reads.**
Use a third, dedicated replica with `max_standby_streaming_delay = -1`.

### SLO, alert, and automatic removal

```java
@Component
public class ReplicaHealthMonitor {

    private static final Duration MAX_LAG = Duration.ofMillis(500);
    private final AtomicBoolean replicaUsable = new AtomicBoolean(true);

    @Scheduled(fixedRate = 2_000)
    public void check() {
        try {
            Double lagSeconds = replicaJdbc.sql("""
                    SELECT COALESCE(EXTRACT(EPOCH FROM (now() - pg_last_xact_replay_timestamp())), 0)
                    """).query(Double.class).single();

            registry.gauge("db.replica.lag.seconds", lagSeconds);
            boolean healthy = lagSeconds * 1000 < MAX_LAG.toMillis();

            if (replicaUsable.compareAndSet(!healthy, healthy)) {
                log.warn("replica marked {} (lag {}ms)", healthy ? "USABLE" : "UNUSABLE",
                         Math.round(lagSeconds * 1000));
            }
        } catch (Exception e) {
            replicaUsable.set(false);                 // unreachable = unusable
        }
    }

    public boolean usable() { return replicaUsable.get(); }
}
```
```java
public JdbcClient forRead(String userId) {
    if (!replicaHealth.usable()) { primaryReads.increment(); return primaryJdbc; }
    // ... sticky window logic ...
}
```

**SLO: p99 replica lag < 500 ms.**

Justification, from measurement rather than taste: a client's read-after-write
round trip is ~120 ms p99 (Module 06). A 500 ms SLO means the sticky window
(5 s) covers lag with 10× margin, and reads that *aren't* covered by the sticky
window (other users' data) tolerate 500 ms of staleness invisibly — nobody
notices a message appearing half a second later than it might have.

```yaml
- alert: ReplicaLagHigh
  expr: db_replica_lag_seconds > 0.5
  for: 2m
- alert: ReplicaFallenOutOfPool
  expr: rate(db_replica_reads_total[5m]) == 0 and rate(db_primary_reads_total[5m]) > 0
  for: 5m
  annotations:
    summary: "All reads are hitting the primary — the replica is out of the pool"
```

Test the automatic removal:
```bash
docker exec pulse-replica-postgres-replica-1 psql -U pulse -d pulse -c \
  "SELECT pg_sleep(60);" &
watch -n1 'curl -s localhost:8080/actuator/metrics/db.replica.lag.seconds | jq ".measurements[0].value"'
```
**Expected:**
```
0.001
0.412
1.204          <-- exceeds SLO
WARN replica marked UNUSABLE (lag 1204ms)
(all reads move to the primary; zero errors visible to clients)
...
WARN replica marked USABLE (lag 3ms)
```

✅ Degrades to primary-only reads rather than serving stale data or failing.

---

## Task 5 — Breaking transaction mode

### (a) Server-side prepared statements

```bash
# with prepareThreshold left at its default of 5
for i in $(seq 1 20); do curl -s localhost:8080/api/rooms/room.1/messages > /dev/null; done
```
**Expected:**
```
org.postgresql.util.PSQLException: ERROR: prepared statement "S_3" does not exist
```
pgjdbc prepared `S_3` on server connection A; the next execution landed on
connection B.

**Fix:** `?prepareThreshold=0`, or PgBouncer 1.21+'s `max_prepared_statements`
which tracks and replays them per server connection:
```ini
max_prepared_statements = 200
```
Measured: `prepareThreshold=0` costs **−9% query throughput** (re-parsing every
time). PgBouncer 1.21+'s tracking recovers most of it (−2%).

### (b) `LISTEN` / `NOTIFY`

```java
jdbc.execute("LISTEN outbox");
// ... 30 seconds later, no notifications ever arrive
```
**No error.** The connection that issued `LISTEN` was returned to the pool and
handed to someone else. The listener is silently deaf.

**Fix:** a dedicated direct connection, bypassing PgBouncer:
```java
@Bean("notifyDataSource")
public DataSource notifyDataSource() {
    var ds = new HikariDataSource();
    ds.setJdbcUrl("jdbc:postgresql://postgres-primary:5432/pulse");  // NOT :6432
    ds.setMaximumPoolSize(2);
    return ds;
}
```

### (c) Session-level `SET` and advisory locks

```java
jdbc.execute("SET statement_timeout = '5s'");
jdbc.execute("SELECT pg_advisory_lock(42)");
// ... later, on a different server connection:
jdbc.execute("SELECT pg_advisory_unlock(42)");
```
**Expected:**
```
WARNING: you don't own a lock of type ExclusiveLock
```
And `statement_timeout` silently applies to a connection you no longer hold —
possibly someone else's query.

**Fix:** use `SET LOCAL` inside a transaction, and `pg_advisory_xact_lock`
(transaction-scoped, released at commit):
```sql
BEGIN;
SET LOCAL statement_timeout = '5s';
SELECT pg_advisory_xact_lock(42);
-- ... work ...
COMMIT;                              -- both automatically released
```

### What Pulse actually needs

| Feature | Needed? | Accommodation |
|---------|---------|---------------|
| Prepared statements | **Yes** — 9% throughput | PgBouncer 1.21+ tracking; else `prepareThreshold=0` |
| `LISTEN/NOTIFY` | **Yes** — the outbox relay | Dedicated direct connection (2 of them) |
| Advisory locks | No | Module 11 replaced locks with partitioning |
| Session `SET` | No | `SET LOCAL` inside transactions |
| Temp tables | No | — |
| Cursors outside a transaction | No | Keyset pagination instead (Module 12) |

✅ Two of six matter, and both have clean accommodations. **Transaction mode is
correct for Pulse** — but note that the answer came from an audit, not an
assumption.

---

## Task 6 (stretch) — LSN-wait read consistency

```java
@Transactional
public SendResult send(...) {
    var result = doSend(...);
    // Capture the WAL position this write reached.
    String lsn = jdbc.sql("SELECT pg_current_wal_insert_lsn()::text")
                     .query(String.class).single();
    return result.withLsn(lsn);
}
```
```java
// The client echoes the LSN back on subsequent reads.
public JdbcClient forRead(String userId, String clientLsn) {
    if (clientLsn == null) return replicaJdbc;

    try {
        Boolean caughtUp = replicaJdbc.sql("""
                SELECT pg_last_wal_replay_lsn() >= :lsn::pg_lsn
                """).param("lsn", clientLsn).query(Boolean.class).single();

        if (Boolean.TRUE.equals(caughtUp)) { replicaReads.increment(); return replicaJdbc; }

        // Wait briefly — most lag is sub-100ms.
        long deadline = System.nanoTime() + Duration.ofMillis(200).toNanos();
        while (System.nanoTime() < deadline) {
            Thread.sleep(10);                      // cheap on a virtual thread
            caughtUp = replicaJdbc.sql("SELECT pg_last_wal_replay_lsn() >= :lsn::pg_lsn")
                                  .param("lsn", clientLsn).query(Boolean.class).single();
            if (Boolean.TRUE.equals(caughtUp)) { replicaWaited.increment(); return replicaJdbc; }
        }
        lsnWaitTimeouts.increment();
        return primaryJdbc;                        // fall back
    } catch (Exception e) {
        return primaryJdbc;
    }
}
```

### Measured, 10,000 reads with 40k writes/s in the background

| | Sticky window (5 s) | LSN wait |
|---|--------------------|----------|
| Stale reads | **0** | **0** |
| Replica read share | 91.0% | **97.4%** |
| p50 read latency | 1.4 ms | **1.6 ms** |
| p99 read latency | 8.2 ms | **41.0 ms** |
| p99.9 | 12 ms | **214 ms** |
| Extra queries per read | 0 | **1–21** (the polling loop) |
| Primary load from reads | 9% | 2.6% |
| Correctness for a *second device* | ✅ | ✅ |
| Correctness for a *third-party* read | n/a | ✅ (precise per-write) |

### Which to ship: **the sticky window.**

The LSN-wait is *more precise* and gets 6.4 percentage points more replica
traffic — and it costs **5× the p99 and 18× the p99.9**, because the waiting
loop turns a fast read into a slow one exactly when the system is already
struggling.

Three more reasons:

1. **The extra 6.4% of replica offload is worth almost nothing.** Primary read
   load went from 9% to 2.6% — a 6.4-point saving on a resource that was never
   the constraint. You paid 33 ms of p99 for it.
2. **It puts protocol state on the client.** Every client must now track and echo
   an opaque LSN string, per connection, correctly, forever. That's a
   compatibility commitment (Module 05's rules apply) for a server-side
   optimization.
3. **The failure mode is worse.** A lagging replica makes the sticky window
   route to the primary instantly. It makes the LSN-wait *poll for 200 ms first*,
   on every read, adding latency precisely when the replica is unhealthy — the
   opposite of what you want.

**When LSN-wait would be right:** if reads dominated your workload so heavily
that 6% of primary load mattered, if the sticky window's 5 seconds were too
coarse (a read-heavy workflow immediately after a write), or if you needed
correctness for reads by *other* users of the same data — a collaborative
document, say, where B must see A's edit. Chat has none of those properties,
because **the sender already has their own message.**

> The best answer remains the one that costs nothing: optimistic echo. LSN-wait
> and sticky windows are both fixes for reading back data you already had.
