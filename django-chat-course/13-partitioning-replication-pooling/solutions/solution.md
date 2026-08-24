# Solutions — Module 13

Reference answers with the reasoning, the rejected alternatives, and the numbers.
Reference machine: 8-core / 16 GB, Ubuntu 24.04, Python 3.12, Django 5.1,
Postgres 16 primary + replica and PgBouncer 1.23 from
`infra/compose.replica.yml`.

---

## Task 1 — Restoring the guarantees partitioning weakened

### 1a. Idempotency is now per-partition. Reproduce it.

```python
# tests/test_partition_dedup.py
@pytest.mark.django_db(transaction=True)
def test_retry_across_a_month_boundary_double_inserts():
    room = "room.boundary"
    cid = "01JQ8Z4K7M8YQ2VBXR3N5TDGWH"

    insert(room, cid, created_at="2026-09-30 23:59:58+00")   # -> messages_2026_09
    insert(room, cid, created_at="2026-10-01 00:00:04+00")   # -> messages_2026_10

    rows = Message.objects.filter(room_id=room, client_id=cid)
    assert rows.count() == 1, f"idempotency broken: {rows.count()} rows"
```
**Expected — the test fails, which is the point:**
```
AssertionError: idempotency broken: 2 rows
```

Both inserts succeeded. `ON CONFLICT (room_id, client_id, created_at) DO NOTHING`
found no conflict, because the second row is in a different partition with a
different `created_at`. The recipient renders the message twice.

**Frequency:** roughly `retries/s × the retry window × 12` per year. At Pulse's
measured retry rate that is about **4 duplicated messages a year** — real, and
essentially impossible to reproduce from a bug report.

### The fix, and the three rejections

**Rejected — a non-partitioned `message_dedup` table** with `UNIQUE (room_id,
client_id)`. It works and it costs a second insert on the hot path (**+0.6 ms**,
measured) plus a table that grows at 864M rows/day and therefore needs *its own*
retention story — which is the problem this whole module exists to solve, moved
one table to the left.

**Rejected — partition by `(room_id, client_id)` hash instead of time.** Restores
global idempotency and destroys the retention story, which was the entire reason
to partition. Trading the win for the consolation prize.

**Rejected — a wider partition (yearly).** Turns a 1-month window into a 12-month
one and turns the retention granularity from "drop a month" into "drop a year,"
which for a 90-day retention policy is useless.

**Chosen — a Redis dedup key in front, with the index as the backstop.** Module 10
already built it; here it stops being an optimization and becomes the actual
guarantee.

```python
async def is_duplicate(room_key: str, client_id: str) -> bool:
    fresh = await redis.set(f"dedup:{{{room_key}}}:{client_id}", "1",
                            nx=True, ex=DEDUP_TTL_S)
    return not fresh
```

The interesting decision is `DEDUP_TTL_S`, because **the TTL is a memory budget**:

| TTL | Keys held at 10k msg/s | Redis memory (~72 B/key) |
|-----|------------------------|--------------------------|
| 24 h | 864,000,000 | **62 GB** — not happening |
| 1 h | 36,000,000 | 2.6 GB |
| **10 min** | **6,000,000** | **432 MB** |
| 1 min | 600,000 | 43 MB |

```bash
python code/dedup_memory.py --ttl 600 --rate 10000
```
```
keys at steady state : 6,014,208
MEMORY USAGE total   : 431.8 MB
p99 SET NX EX        : 0.11 ms
```

**Ten minutes, 432 MB.** And then the load-bearing consequence: the client's retry
policy must be **strictly inside** the window.

```js
// pulse-room.js — bounded retry, and the bound is a system invariant
const MAX_RETRY_AGE_MS = 300_000;        // 5 minutes, half the dedup window
if (Date.now() - bubble.firstAttemptAt > MAX_RETRY_AGE_MS) {
  bubble.state = "failed";               // surface it; do NOT retry silently
  return;
}
```

> **Write this pair down together.** "Server dedup window = 10 minutes" and
> "client retry bound = 5 minutes" are one decision with two halves, and a change
> to either without the other reopens the hole. It belongs in the protocol file's
> operational notes, not in a comment in `dedup.py`.

Cost of the fix: **0.11 ms per send and 432 MB of Redis.** The per-partition
unique index stays as the backstop for the case Redis restarts, and the honest
statement is: *idempotency is guaranteed for 10 minutes by Redis and for one
partition-month by Postgres, and the client never retries past 5 minutes.*

### 1b. `seq` uniqueness across partitions

```python
@pytest.mark.django_db(transaction=True)
def test_seq_collides_across_partitions_after_a_redis_restart(monkeypatch):
    monkeypatch.setenv("PULSE_SKIP_HWM", "1")        # disable Module 10 recovery
    send(room="room.collide", body="a", created_at="2026-09-15")   # seq 1
    redis.delete("room:{room.collide}:seq")
    send(room="room.collide", body="b", created_at="2026-10-15")   # seq 1 again
    assert Message.objects.filter(room_id="room.collide", seq=1).count() == 1
```
**Expected:**
```
AssertionError: assert 2 == 1
```

Two rows with `seq = 1` in one room. Before partitioning the primary key rejected
this. Now nothing does, and the effect on clients is severe: `to_seq` is wrong,
gap detection is wrong, and resume returns two rows for one cursor position.

**The fix has two halves, and the second is the one people skip.**

**Half 1 — make high-water-mark recovery fail-closed.** Module 10's recovery is
currently best-effort: if the `max(seq)` query raises, the allocator carries on
from whatever Redis says. Invert it.

```python
async def _ensure_recovered(self, room_id: str) -> None:
    if room_id in self._recovered:
        return
    try:
        await self.recover_high_water_mark(room_id)
    except Exception:
        # FAIL CLOSED. Refusing to send is a visible outage for one room.
        # Allocating from 1 is silent, permanent corruption of every client's
        # cursor in that room. Always choose the loud failure.
        raise SequencerUnavailable(room_id)
    self._recovered.add(room_id)
```

Cost of the recovery query itself, now that the table is partitioned:

```bash
pg -c "EXPLAIN (ANALYZE) SELECT max(seq) FROM messages WHERE room_id='room.42';"
```
```
 Aggregate (actual time=0.402..0.403 rows=1 loops=1)
   ->  Merge Append  (5 partitions)
 Execution Time: 0.421 ms
```
**0.42 ms, once per room per worker process per Redis lifetime.** No optimization
needed; do not be tempted to add a `created_at` hint here, because an idle room's
last message may be months old and the hint would silently return a stale maximum
— which is the bug you are fixing.

**Half 2 — checkpoint the counters, so recovery has a floor that does not depend
on the message table.**

```python
@shared_task(name="chat.checkpoint_sequences")
def checkpoint_sequences() -> int:
    """Every 10 s, persist the Redis counter for every ACTIVE room."""
    rooms = registry.active_rooms()               # bounded by real concurrency
    values = [(r, int(redis.get(seq_key(r)) or 0)) for r in rooms]
    with connection.cursor() as cur:
        cur.executemany(
            """INSERT INTO chat_roomsequence (room_id, last_seq)
               SELECT id, %s FROM chat_room WHERE slug = %s
               ON CONFLICT (room_id) DO UPDATE
                 SET last_seq = GREATEST(chat_roomsequence.last_seq, EXCLUDED.last_seq)""",
            [(v, r.removeprefix("room.")) for r, v in values])
    return len(values)
```

```bash
python code/checkpoint_bench.py --rooms 1000
```
```
1,000 active rooms, one executemany per tick: 4.1 ms per tick, 0.4 writes/s/room
```

✅ **4 ms every 10 seconds for 1,000 active rooms.** Note the scoping: *active*
rooms, from the `LocalRegistry`, not all rooms. Checkpointing 100,000 idle rooms
would be 10,000 writes/s to maintain counters nobody is using.

`recover_high_water_mark` then takes `GREATEST(max(seq) from messages, last_seq
from chat_roomsequence)` — the checkpoint covers the window where messages exist
in the stream but not yet in the store, which the message table alone cannot see.

---

## Task 2 — Lag-aware routing

### The failure the naive router produces

A paused replica does not error. It answers, with data frozen at the moment it
stopped replaying:

```bash
docker pause pulse-pg-replica
python code/stale_read_probe.py --seconds 60
docker unpause pulse-pg-replica
```
**Expected:**
```
reads served by replica : 4,812
reads that were STALE   : 4,812 (100%)
worst staleness         : 58.4 s
errors raised           : 0
```

✅ **Not one error, and every read wrong.** This is the failure mode to fear from
replicas — not that they break, but that they confidently answer with the past.

### The probe

```python
class ReplicaHealth:
    """One lag sample every 2 s per worker. 8 workers = 4 queries/s, which is
    noise — and measuring locally is right, because it measures the connection
    THIS worker would actually use."""

    def __init__(self):
        self.lag_s = 0.0
        self.healthy = True
        self._consecutive_ok = 0

    async def run(self):
        while True:
            try:
                self.lag_s = await asyncio.wait_for(self._sample(), timeout=1.0)
                self._update(ok=True)
            except (asyncio.TimeoutError, OperationalError):
                # A paused or partitioned replica times out. Treat the ABSENCE
                # of an answer as maximum lag, never as "probably fine".
                self.lag_s = float("inf")
                self._update(ok=False)
            await asyncio.sleep(2.0)

    @database_sync_to_async
    def _sample(self) -> float:
        with connections["replica"].cursor() as cur:
            cur.execute("""
                SELECT CASE WHEN pg_is_in_recovery()
                       THEN extract(epoch FROM now() - pg_last_xact_replay_timestamp())
                       ELSE 0 END""")
            return float(cur.fetchone()[0] or 0.0)

    def _update(self, ok: bool):
        if not ok or self.lag_s > EJECT_LAG_S:
            self.healthy = False
            self._consecutive_ok = 0
            return
        # HYSTERESIS: 15 consecutive good samples (30 s) before coming back.
        # Without it a replica that is oscillating around the threshold flaps in
        # and out of rotation, and the flapping is worse than either state.
        self._consecutive_ok += 1
        if self._consecutive_ok >= 15 and self.lag_s < REJOIN_LAG_S:
            self.healthy = True
```

### The policy, and the numbers behind each threshold

```python
EJECT_LAG_S  = 5.0     # above this, the replica serves nothing
REJOIN_LAG_S = 2.0     # below this for 30 s, it comes back


def db_for_read(self, model, **hints):
    if model._meta.model_name in PRIMARY_ONLY:
        return "default"
    if not health.healthy:
        _routed.labels(target="primary_ejected").inc()
        return "default"
    # Shrink the sticky window when the replica is genuinely close. At 4 ms of
    # lag a 5-second window sends 20% of reads to the primary for no reason.
    window = max(0.5, min(STICKY_WINDOW_S, health.lag_s * 4))
    if (time.monotonic() - _wrote_at.get()) < window:
        return "default"
    return "replica"
```

| Threshold | Value | Justification |
|-----------|-------|---------------|
| `EJECT_LAG_S` | 5.0 s | Above the measured p99.9 of **4.2 s** during batch writes, so a normal write burst does not eject the replica; below the point where a second device opened after a send finds the message missing, which is the actual user complaint. |
| `REJOIN_LAG_S` + 30 s | 2.0 s | Comfortably below eject, so returning requires genuine recovery, not a lucky sample. |
| Sticky = `lag × 4` | — | 4× the *current* lag covers the tail without covering the whole distribution. At 4 ms of lag the window is the 0.5 s floor; at 1 s of lag it is 4 s. |
| Probe timeout | 1.0 s | A probe that blocks is a probe that lies. Absence of an answer must count as infinite lag. |

### Measured

```bash
docker pause pulse-pg-replica
python code/stale_read_probe.py --seconds 60 --lag-aware
docker unpause pulse-pg-replica
```
**Expected:**
```
replica ejected after       : 2.4 s
reads that were STALE       : 84   (all inside the 2.4 s detection window)
reads after ejection        : 0 stale, 100% served by primary
replica rejoined after      : 31.8 s post-unpause
```

✅ **From 4,812 stale reads to 84**, and the remaining 84 are bounded by the probe
interval — which is a knob, not a bug. Halve it to 1 s and you halve the exposure
for 8 queries/s.

And the other side of the policy, with a healthy replica:

```bash
python code/ryow_probe.py --iterations 5000 --delay-ms 50 --lag-aware
```
```
misses                   : 0 / 5000
reads served by replica  : 4,712 (94.2%)   [was 80.4% with the fixed 5 s window]
reads served by primary  :   288 (5.8%)
```

✅ **The replica now absorbs 94% instead of 80%** because the sticky window shrank
to match reality, and the miss count is still zero.

> **The capacity requirement that falls out of this.** Ejecting the replica sends
> 100% of reads to the primary. Measured, the primary's p99 goes 31 ms → 44 ms —
> survivable *because the primary was sized to survive it*. **Never size a primary
> assuming the replica exists.** A replica is a latency and headroom improvement;
> the moment it is a capacity requirement, its failure is your outage.

---

## Task 3 — Size the pool from the curve

### Derive it

```bash
python code/pool_curve.py --workload pulse --max 200 --duration 30
```
**Expected:**
```
conns   tps      p50     p99     pg CPU
   4    24,102   0.9ms   2.1ms    38%
   8    41,204   1.0ms   1.4ms    71%
  16    58,102   1.1ms   1.9ms    94%
  20    61,102   1.1ms   2.2ms    98%
  24    61,408   1.3ms   2.6ms   100%      <-- knee
  32    60,884   1.7ms   3.8ms   100%
  48    59,214   2.6ms   6.1ms   100%
  96    54,882   5.4ms  18.4ms   100%
 200    41,902  13.1ms  84.2ms   100%
```

The knee is at **24**, which matches `(8 cores × 2) + 8` — but notice that
throughput is already within 0.5% at **20** and p99 is 15% better there. The rule
of thumb gets you to the right neighbourhood; the curve tells you which side of
the knee to sit on, and the answer is always **just below**.

```ini
default_pool_size = 20
reserve_pool_size = 5
reserve_pool_timeout = 3
```

> **Size the pool per (database, user) pair, and remember PgBouncer does too.**
> `default_pool_size = 20` with both `pulse` and `pulse_ro` aliases means up to 40
> server connections, not 20. Two aliases, one Postgres, and a pool sizing that
> quietly doubled.

### Too small

```bash
sed -i 's/default_pool_size = 20/default_pool_size = 4/' ../../infra/pgbouncer.ini
psql "postgresql://pulse:pulse@localhost:6432/pgbouncer" -c "RELOAD;"
python code/pool_curve.py --workload pulse --fixed-clients 288 --duration 30
psql "postgresql://pulse:pulse@localhost:6432/pgbouncer" -c "SHOW POOLS;"
pg -c "SELECT count(*), state FROM pg_stat_activity WHERE datname='pulse' GROUP BY 2;"
```
**Expected:**
```
app-side p99: 512 ms
 database | cl_active | cl_waiting | sv_active | maxwait | maxwait_us
----------+-----------+------------+-----------+---------+------------
 pulse    |         4 |        284 |       4   |       0 |     498204
 count | state
-------+--------
     4 | active
```

✅ **p99 of 512 ms while Postgres is at 12% CPU with four connections.** The
database looks *idle*. Every instinct says "the database is fine, it must be the
app," and every instinct is wrong.

### Too large

```bash
sed -i 's/default_pool_size = 4/default_pool_size = 200/' ../../infra/pgbouncer.ini
psql "postgresql://pulse:pulse@localhost:6432/pgbouncer" -c "RELOAD;"
python code/pool_curve.py --workload pulse --fixed-clients 288 --duration 30
psql "postgresql://pulse:pulse@localhost:6432/pgbouncer" -c "SHOW POOLS;"
```
**Expected:**
```
app-side p99: 84 ms
 database | cl_active | cl_waiting | sv_active | maxwait | maxwait_us
----------+-----------+------------+-----------+---------+------------
 pulse    |       288 |          0 |     196   |       0 |          0
```

### The query that tells them apart

Both feel identical to a user: sends are slow. The distinguishing signal is
**where the wait is**:

```sql
-- On the PgBouncer admin console
SHOW POOLS;
```

| Signal | Pool too small | Pool too large |
|--------|----------------|----------------|
| `cl_waiting` | **284** (sustained) | 0 |
| `maxwait_us` | **498,204** | 0 |
| `sv_active` | 4 (= pool size) | 196 |
| Postgres CPU | 12% | 100% |
| `pg_stat_activity` rows | 4 | 200 |
| Where the time goes | **queueing at PgBouncer** | **contending inside Postgres** |

```promql
# One alert, both directions.
pgbouncer_pools_client_maxwait_seconds > 0.1              -> pool too small
pg_stat_activity_count{state="active"} > 2 * pg_cpu_cores -> pool too large
```

> `maxwait_us > 0` **sustained** is the single most useful PgBouncer number.
> Momentary spikes are normal; a non-zero `maxwait` for minutes means clients are
> queueing in front of a pool that is smaller than your concurrency, and no amount
> of database tuning will help.

Restore `default_pool_size = 20`.

---

## Task 4 — `LISTEN`/`NOTIFY` versus the poll

### The implementation

The notify comes from a trigger, not from application code, so it cannot be
forgotten in a code path someone adds later:

```sql
CREATE OR REPLACE FUNCTION outbox_notify() RETURNS trigger AS $$
BEGIN
  -- No payload. A payload tempts you to publish from it and skip the query,
  -- which loses the SKIP LOCKED coordination. It is also capped at 8000 bytes.
  -- NOTIFY with an identical payload is deduplicated within a transaction,
  -- which is exactly the coalescing we want for a 500-row batch insert.
  PERFORM pg_notify('outbox', '');
  RETURN NULL;
END; $$ LANGUAGE plpgsql;

CREATE TRIGGER outbox_notify_trg
  AFTER INSERT ON outbox
  FOR EACH STATEMENT EXECUTE FUNCTION outbox_notify();
```

The listener needs a **direct, non-pooled connection to the primary** — lab Part F
proved `LISTEN` does not survive transaction pooling:

```python
DATABASES["primary_direct"] = {
    **DATABASES["default"],
    "HOST": "localhost", "PORT": 5432,     # NOT 6432
    "CONN_MAX_AGE": None,                  # this one connection is held forever
}
```

```python
async def listen_forever(wake: asyncio.Event):
    conn = await psycopg.AsyncConnection.connect(DSN_DIRECT, autocommit=True)
    await conn.execute("LISTEN outbox")
    async for _notify in conn.notifies():
        wake.set()          # a FLAG, not a queue — coalescing is free


async def relay_loop():
    wake = asyncio.Event()
    asyncio.create_task(listen_forever(wake))
    while True:
        # The notification is an ACCELERATOR. The 1-second timeout is the FLOOR,
        # and the floor is not optional — see "after an hour down" below.
        with contextlib.suppress(asyncio.TimeoutError):
            await asyncio.wait_for(wake.wait(), timeout=1.0)
        wake.clear()
        await relay_once()
```

### Measured on all four axes

| | 1 s poll | `LISTEN` only | **Both (shipped)** |
|---|---|---|---|
| Publish latency after a crash, p50 | 1,510 ms | **41 ms** | **44 ms** |
| Publish latency after a crash, p99 | 2,940 ms | **118 ms** | **121 ms** |
| Idle cost (4 relay workers) | 4 queries/s | **0** | 4 queries/s |
| After the relay was down 1 h | drains 3,600 rows in **8 s** | **never drains** | drains in 8 s |
| 50,000 rows arriving at once | steady, 100 s | **50,000 wakeups**, 41 s + CPU spike | **1 wakeup**, 100 s |

✅ **34× lower publish latency after a crash**, and two failures that make
`LISTEN`-only unusable:

1. **`LISTEN` is not durable.** Notifications delivered while your listener was
   disconnected are gone. A relay that has been down for an hour has an hour of
   backlog and no notification to tell it so — it sits idle forever with a
   growing table. The poll is not a redundancy; it is the correctness floor.
2. **`FOR EACH ROW` would produce a notification storm.** `FOR EACH STATEMENT`
   plus an `Event` flag collapses 50,000 notifications into one wakeup, because a
   flag has no queue to fill.

### Recommendation

**Ship both.** The notification is an accelerator; the 1-second poll is the floor.
The combination costs the same 4 queries/s as the poll alone, and it is
*correct* under every failure that breaks `LISTEN` alone.

> **The condition that reverses this:** if you cannot give the listener a direct
> connection to the primary, `LISTEN` is unavailable and the poll is the whole
> answer. That is not hypothetical — several managed Postgres products expose only
> a pooler endpoint, and some poolers in transaction mode drop `LISTEN` exactly
> the way PgBouncer does. Before you build the accelerator, check that you can
> reach the primary directly; if you cannot, spend the effort on shrinking
> `LOOKBACK_MS` instead.
>
> **And the simpler condition:** if your publish-latency budget after a crash is
> above two seconds, do not add a component. The poll alone meets it, and a
> listener is a long-lived connection, a reconnect loop, and a failure mode.

---

## Task 5 — Failover, and the RPO you did not know you had

### The runbook

```bash
# 1. Confirm the replica is caught up ENOUGH to promote. There is no "caught up"
#    on an async replica — there is only "how much am I about to lose".
pgr -c "SELECT pg_last_wal_receive_lsn(), pg_last_wal_replay_lsn();"

# 2. Fence the old primary. Skipping this is how you get two primaries and a
#    split brain that is worse than the outage.
docker stop pulse-pg-primary

# 3. Promote.
pgr -c "SELECT pg_promote(wait => true, wait_seconds => 60);"
pgr -c "SELECT pg_is_in_recovery();"        -- expect f

# 4. Repoint the application.
export PULSE_DB_HOST=localhost PULSE_DB_PORT=5433
psql "postgresql://pulse:pulse@localhost:6432/pgbouncer" -c "RELOAD;"
kill -HUP $(pgrep -f 'uvicorn pulse.asgi')

# 5. Rebuild the old primary as a replica of the new one. pg_rewind if the
#    timelines diverged, pg_basebackup if you want to be certain.
```

### Measured under load, as shipped

```bash
python code/failover_drill.py --rate 200 --duration 120
```
**Expected:**
```
messages accepted by the old primary : 12,418
messages present on the new primary  : 12,377
RPO : 41 messages   (0.34 s of writes)
RTO : 12.1 s        (promote 1.8 s + config reload 0.9 s + reconnect 9.4 s)
```

### The specific thing in this module's design that makes RPO non-zero

`compose.replica.yml` sets `synchronous_commit = on`. That looks like it means
"wait for the replica," and it does not:

```bash
pg -c "SHOW synchronous_standby_names;"
```
```
 synchronous_standby_names
---------------------------

```

**Empty.** `synchronous_commit = on` only waits for a *synchronous* standby, and
with no `synchronous_standby_names` there is none — so `on` degrades to "flush
locally," which is `local`. The replica is asynchronous, the 41 lost messages are
the WAL that had not shipped yet, and 0.34 s of loss matches the measured p99
replay lag exactly.

**This is the trap worth remembering:** `synchronous_commit` and
`synchronous_standby_names` are two settings that only mean anything together, and
the one with the reassuring name is the one that does nothing on its own.

### The fix, and the availability trap inside it

```sql
ALTER SYSTEM SET synchronous_standby_names = 'ANY 1 (pulse_replica_1)';
SELECT pg_reload_conf();
```

```bash
python code/failover_drill.py --rate 200 --duration 120
```
```
RPO : 0 messages
RTO : 11.8 s
write p50 : 3.7 ms -> 6.1 ms
```

✅ **RPO zero.** And now stop the replica:

```bash
docker stop pulse-pg-replica
python manage.py sendmsg room.1 "hello"
```
```
(hangs forever)
```

✅ **Every write blocks indefinitely**, because there is one synchronous standby
and it is gone. You traded a 41-message RPO for a total outage, which is a bad
trade made by many people who read only the first half of this section.

Three ways out, in order:

1. **Two standbys, `ANY 1 (r1, r2)`.** Either one satisfies the quorum, so one
   failure is survivable. This is what Module 18's Patroni cluster is for, and it
   is the real answer.
2. **Per-transaction synchrony.** Pay the premium only where it matters:

   ```python
   with transaction.atomic():
       with connection.cursor() as cur:
           cur.execute("SET LOCAL synchronous_commit = 'remote_apply'")
           # messages + outbox insert
   ```

   ```
   global synchronous_commit=local, outbox txn remote_apply:
     ordinary write p50 : 3.7 ms  (unchanged)
     outbox   write p50 : 5.8 ms  (+2.1 ms)
   ```

   ✅ **+2.1 ms on the transaction that must not be lost, and nothing on anything
   else** — which is exactly what the README promised and why `SET LOCAL` exists.
   It does not fix the availability trap; it shrinks the blast radius to the
   transactions that opted in.
3. **`synchronous_commit = local` and document the RPO.** Perfectly respectable
   with the number written down. "RPO ≈ 0.34 s of writes, ≈ 41 messages at peak"
   is a fact a product owner can make a decision about. "We use synchronous
   replication" when `synchronous_standby_names` is empty is not.

### What I would ship, and why

**`synchronous_commit = local` globally, `SET LOCAL synchronous_commit =
'remote_apply'` on the message + outbox transaction, and only once there are two
standbys (Module 18).** Until the second standby exists, run fully async and
publish the RPO number.

The reasoning: the outbox transaction is the one whose loss is invisible — a lost
outbox row is a message nobody can detect is missing, which is the failure this
entire module exists to prevent. Ordinary reads, presence writes and read cursors
can all lose 340 ms of history without anyone noticing or caring. Pay for
durability precisely where undetectable loss is possible, and nowhere else.

### Improving RTO

Of the 12.1 s, **9.4 s is the application reconnecting** — not the database.

```bash
python code/failover_drill.py --rate 200 --duration 120 --preconfigured
```
```
RTO : 4.1 s   (promote 1.8 s + reload 0.9 s + reconnect 1.4 s)
```

✅ **3× better** just by having both DSNs configured up front and flipping an
alias rather than reconnecting from cold with a fresh DNS lookup and a cold pool.

The rest of the gap is a human running the runbook, and no amount of preparation
fixes that. **Module 18 replaces the human**: Patroni watches, promotes and
updates HAProxy automatically, and the drill there measures **8.4 s end to end
with nobody awake**. Write your manual RTO down first, though — it is the number
the automation has to beat, and "we automated failover" without a before-number is
a claim, not a result.
