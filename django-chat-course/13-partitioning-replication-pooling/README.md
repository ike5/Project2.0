# Module 13 — Partitioning, Replication & Pooling

**Goal:** Make Module 12's **74 TB/year** survivable on one machine — instant
retention, read scaling, connection multiplexing — and close the dual-write hole
that has been open since Module 07 with a transactional outbox.

⏱️ ~5 hours · **Prerequisites:** Modules 00–12.

---

## Partitioning: retention becomes free

Module 12 projected **204 GB/day** and **864 million rows/day** at Pulse's 10k
msg/s target. The naive 90-day retention job:

```sql
DELETE FROM messages WHERE created_at < now() - interval '90 days';
```

At that volume, that one statement:

- Runs for **hours**, holding a transaction open the entire time — which also
  pins every replica's `xmin` and blocks vacuum on the whole database.
- Generates roughly **200 GB of WAL**, which ships to every replica and every
  backup.
- Leaves 864 million **dead tuples** for autovacuum, which then competes with
  your live traffic for I/O for days.
- **Does not return the disk space.** The table stays the same size until a
  `VACUUM FULL` (which takes an `ACCESS EXCLUSIVE` lock and needs a second copy
  of the table on disk) or `pg_repack`.

With declarative partitioning:

```sql
DROP TABLE messages_2026_05;
```

**Instant. Near-zero WAL. Space returned immediately. No vacuum debt.** The lab
measures the pair at **41 minutes versus 12 milliseconds**.

That single difference is the reason to partition. Query performance is a bonus,
and — as you will see — sometimes a negative one.

```sql
CREATE TABLE messages (...) PARTITION BY RANGE (created_at);

CREATE TABLE messages_2026_08 PARTITION OF messages
    FOR VALUES FROM ('2026-08-01') TO ('2026-09-01');
```

### Partition on time, index on room

The instinct is to partition by `room_id` — it is the shard key, after all. Resist
it:

| Partition key | Partitions | Retention story | Prunes scrollback? | Verdict |
|---------------|-----------|-----------------|--------------------|---------|
| `created_at`, monthly | 12–36 | ✅ `DROP TABLE` | only with a time predicate | **Yes** |
| `created_at`, daily | 90–365 | ✅ | ✅ | Planning cost adds up |
| `room_id`, hash × 64 | 64 | ❌ `DELETE` per partition | ✅ always | No retention story |
| `room_id`, list, one per room | **thousands** | ✅ per room | ✅ | Planning-time explosion |

Postgres considers every partition at plan time. A few dozen costs microseconds; a
few thousand adds milliseconds to **every query in the system**, including the ones
that touch one row. Time partitioning gives you a bounded, predictable count.

**Sharding by room is a different mechanism at a different layer** — Module 14 —
and the two compose fine. Partition within a shard.

### Two things partitioning takes away

**1. The scrollback query stops pruning.** This is the module's central honest
admission.

```sql
-- PRUNES: created_at is in the predicate
SELECT * FROM messages
 WHERE room_id='room.7' AND created_at > '2026-08-01'
 ORDER BY id DESC LIMIT 50;

-- DOES NOT PRUNE: every partition is scanned
SELECT * FROM messages
 WHERE room_id='room.7' AND id < 7241938472948572160
 ORDER BY id DESC LIMIT 50;
```

Module 12's scrollback pages by the Snowflake `id`, and Module 10's resume pages by
`seq`. Neither mentions `created_at`, so neither prunes — and partitioning makes
both *slower*, because one index scan becomes N index scans plus a merge.

Two fixes, and you want both:

- **Derive a time hint from the cursor.** A Snowflake ID *contains* its timestamp
  (Module 12's `code/snowflake.py`), so `WHERE created_at > timestamp_of(cursor) -
  interval '1 day'` costs nothing and prunes to one or two partitions.
- **Keep the partition count small.** 12 monthly partitions is 12 tiny index scans;
  500 daily partitions is not.

The lab measures the tax and then claws it back: **0.118 ms → 0.9 ms → 0.13 ms.**

**2. Your uniqueness guarantees change meaning.** Postgres requires the partition
key to be part of every unique index on a partitioned table. So Module 12's

```sql
PRIMARY KEY (room_id, seq)
UNIQUE INDEX (room_id, client_id)     -- the idempotency guarantee
```

become

```sql
PRIMARY KEY (room_id, seq, created_at)
UNIQUE INDEX (room_id, client_id, created_at)
```

and both are now enforced **within a partition only**. Concretely:

- A `seq` collision across a month boundary is no longer prevented by the
  database. Module 10's Redis high-water-mark recovery is now the *only* thing
  keeping sequence numbers unique, which promotes it from "belt and braces" to
  "load-bearing."
- The idempotency window becomes **one month**. A retry that crosses midnight on
  the last day of the month inserts a duplicate. Module 10 predicted this; here it
  actually happens.

Neither is a reason not to partition. Both are reasons to **write down what
changed**, because a guarantee that silently weakens with no code change is
exactly the kind of thing that surfaces in a postmortem as "we thought the
database was enforcing that."

### Maintenance is the part people skip

A partitioned table needs tomorrow's partition to exist before tomorrow. If it
does not, inserts either fail outright —

```
ERROR:  no partition of relation "messages" found for row
DETAIL:  Partition key of the failing row contains (created_at) = (2026-09-01 00:00:01+00).
```

— or, if you created a `DEFAULT` partition, they land there silently and quietly
undo everything partitioning was for. The default partition is worse than useless
once it has rows in it: attaching a new partition that overlaps it requires
scanning the entire default to prove no row belongs in the new range, taking an
`ACCESS EXCLUSIVE` lock while it does.

> **Pulse's choice: no `DEFAULT` partition, plus a Celery beat task that keeps
> three months ahead and drops anything past retention.** A failed insert at
> 00:00:01 is a page. A silent default partition is a bad quarter. `pg_partman` is
> the excellent alternative if you would rather run an extension than a task, and
> Module 13's lab shows both.

---

## Replication, and the one bug it introduces

```sql
-- on the primary
SELECT client_addr, state, sent_lsn, replay_lsn, replay_lag FROM pg_stat_replication;
-- on the replica
SELECT pg_is_in_recovery(), now() - pg_last_xact_replay_timestamp() AS lag;
```

Read replicas scale reads. They introduce exactly one class of bug, and it is
famous:

```
t=0     alice sends a message; it commits on the primary
t=1     alice's client loads room history — from a replica 200 ms behind
t=2     her own message is missing
```

Four fixes, in order of preference **for chat specifically**:

| Fix | Cost |
|-----|------|
| **Echo optimistically; never read your own write back** | Free — and Pulse already does it (Module 05's `client_id` reconciliation) |
| Route that user's reads to the primary for N seconds after a write | Simple; a per-user "sticky window" |
| Capture the write's LSN; make the read wait for `pg_last_wal_replay_lsn() >= lsn` | Precise; real plumbing |
| `synchronous_commit = remote_apply` | Correct everywhere; costs write latency on **every** write |

Chat has an advantage the others do not: **the sender already has the message.**
Optimistic rendering plus `client_id` matching means the sender never needs to read
their own write back, and the bug mostly disappears by construction.

Where it does *not* disappear: **a second device.** Alice sends from her phone and
opens her laptop 100 ms later. That is the case the sticky window exists for, and
the lab measures how often it actually fires (**18% of reads issued within 100 ms
of a write**, on the reference machine under load).

### `synchronous_commit`, precisely

| Setting | Waits for | Loss on primary crash |
|---------|-----------|-----------------------|
| `off` | nothing | up to `wal_writer_delay` |
| `local` | local WAL flush | none locally; the replica may lag |
| `remote_write` | the replica received it | loss if the replica's OS crashes |
| `on` (default) | the replica flushed it to disk | none |
| `remote_apply` | the replica **applied** it — reads are consistent | none; slowest |

Pulse uses `on` for messages and **`remote_apply` for the outbox write
specifically**, because an outbox row that exists on the primary but not on a
promoted replica is a message that will never be published — a silent, permanent
loss with no error anywhere. The lab measures the premium: **+2.1 ms per outbox
write**, on writes that are already batched.

### Django DB routers are the idiomatic mechanism

Do not hand-roll routing. Django has a first-class hook:

```python
class ReplicaRouter:
    def db_for_read(self, model, **hints): ...
    def db_for_write(self, model, **hints): ...
    def allow_relation(self, obj1, obj2, **hints): ...
    def allow_migrate(self, db, app_label, **hints): ...
```

Three Django-specific traps the lab walks into on purpose:

1. **`allow_migrate` must return `False` for the replica**, or `migrate` will try
   to run DDL against a read-only standby and fail halfway through — after having
   already written to `django_migrations` on the primary.
2. **`TEST: {"MIRROR": "default"}`** on the replica entry, or every test that
   writes then reads fails, because the test database for `replica` is a separate,
   empty database.
3. **The router has no request context**, and in an async consumer there is no
   request at all. `db_for_read` cannot know "this user wrote 40 ms ago" unless you
   put it somewhere the router can see. The answer is a `contextvar` — which
   propagates correctly across `await` **and** across `database_sync_to_async`'s
   threadpool hop, where `threading.local()` does not. That distinction is worth
   the whole section it gets in the lab.

---

## Connection pooling, and why Python needs it sooner

Postgres forks a **process per connection**, roughly 5–10 MB each. This is not a
tunable; it is the architecture.

Now do the Python arithmetic, which is worse than the JVM's:

```
3 app nodes × 8 Uvicorn workers            = 24 processes
each with a database_sync_to_async pool of
  min(32, cpu_count + 4) = 12 threads      = 288 potential backends
                                             against max_connections = 200
```

On the JVM twin, one node is **one process with one pool** — 3 nodes × 20
connections = 60. The process-per-core model multiplies your connection count by
your core count, so **PgBouncer matters sooner and more in Python than on the
JVM.** This is the same structural fact that made Redis necessary in Module 04 and
made read amplification worse in Module 09, arriving a third time.

And more connections is not merely wasteful — past roughly `(cores × 2) +
effective_spindles` *active* connections, throughput **decreases**. On a 16-core
box that is about 34, not 288.

```ini
[pgbouncer]
pool_mode = transaction
max_client_conn = 10000
default_pool_size = 25
```

| Mode | Server connection held for | Breaks |
|------|---------------------------|--------|
| `session` | the whole client session | nothing — and barely helps |
| **`transaction`** | one transaction | `SET`, advisory locks, `LISTEN`/`NOTIFY`, **server-side prepared statements**, temp tables, cursors outside a transaction |
| `statement` | one statement | multi-statement transactions entirely |

### The three Django settings that break under transaction pooling

Transaction mode is what you want, and Django will fight you on it in three
specific places.

**1. `prepare_threshold` — psycopg 3 prepares statements by default.** After the
5th execution of the same query, psycopg promotes it to a server-side prepared
statement. Under transaction pooling that statement was prepared on server
connection A and is later executed on server connection B:

```
psycopg.errors.InvalidSqlStatementName: prepared statement "_pg3_0" does not exist
```

An error that appears **only under load**, only after warm-up, and never in
development — the worst possible shape.

```python
DATABASES["default"]["OPTIONS"] = {"prepare_threshold": None}   # never prepare
```

Cost: the lab measures **+9%** on the keyset query (0.79 ms → 0.86 ms) — you are
paying for parse and plan on every execution. The better fix, if your PgBouncer is
1.21 or newer, is `max_prepared_statements = 200`, which makes PgBouncer track
prepared statements per pooled server connection and recreate them as needed. That
recovers the 9% and is measured too.

**2. `DISABLE_SERVER_SIDE_CURSORS` — `QuerySet.iterator()` is a landmine.** Django
implements `.iterator()` with a server-side cursor (`DECLARE … CURSOR`), which is
session state. In transaction mode, the `FETCH` lands on a different backend:

```
psycopg.errors.InvalidCursorName: cursor "_django_curs_140234_1" does not exist
```

```python
DATABASES["default"]["DISABLE_SERVER_SIDE_CURSORS"] = True
```

Django then buffers the whole result client-side, which is fine for the queries you
should be running and a memory bomb for the ones you should not — so this setting
is also a design constraint, not just a compatibility flag.

**3. `CONN_MAX_AGE` — two poolers fighting.** Django's persistent connections and
PgBouncer's pool are both pools. Pick one.

```python
DATABASES["default"]["CONN_MAX_AGE"] = 0      # let PgBouncer own it
```

`CONN_MAX_AGE = 0` looks wasteful — a TCP connect and an auth handshake per
request — but connecting to PgBouncer costs **0.31 ms** against **3.14 ms** for a
real Postgres backend fork, because PgBouncer is a single process handing you a
socket it already had. The lab measures both, and the ratio is the argument.

> If you are **not** running a pooler, the answer flips completely:
> `CONN_MAX_AGE = 60` with `CONN_HEALTH_CHECKS = True` (Django 4.1+) is right, and
> the health check exists because a persistent connection that a firewall silently
> killed produces `InterfaceError` on the next query. Know which world you are in.

---

## The transactional outbox

This closes a hole that has been open since Module 07 and that Module 09's summary
table explicitly deferred to here.

**The dual-write problem:**

```python
await persist(message)                   # commits
await fanout.append(room_key, envelope)  # <-- the process dies here
```

The message is durable and **will never be delivered**. No retry helps: the
coroutine that knew is gone. Module 10's resume does not help either — resume reads
the database, so a client that asks "what did I miss?" gets it, but a client that
was *connected the whole time* never receives it and has **no gap to detect**,
because the `seq` was allocated and used. This is the one loss mode that is
invisible to every mechanism you have built.

**The outbox makes the two writes atomic:**

```sql
BEGIN;
  INSERT INTO messages (...);
  INSERT INTO outbox (payload) VALUES (...);
COMMIT;                                    -- both, or neither
```

Then a **Celery** relay publishes:

```python
@shared_task
def relay_outbox():
    with transaction.atomic():
        rows = (Outbox.objects
                .select_for_update(skip_locked=True)     # <-- the important part
                .filter(published_at__isnull=True)
                .order_by("id")[:500])
        ...
```

`FOR UPDATE SKIP LOCKED` lets N relay workers work the same table concurrently
without blocking each other or double-publishing. Delivery is still
**at-least-once** — the relay can publish and then crash before the `UPDATE` —
which is exactly why consumers dedup on `client_id`. The whole chain now holds:

```
persist ──atomic──▶ outbox ──at-least-once──▶ Redis Stream
                                                 │ at-least-once
                                                 ▼
                                        consumer ──idempotent──▶ delivery
```

### The cost, stated honestly

The outbox is not free, and Module 10 made the send path fast on purpose:

| Send path | Latency to `message.ack` | Sends/s per room |
|-----------|--------------------------|------------------|
| Module 10: Lua `INCR`+`XADD`, persist later | 1.8 ms | 31,904 |
| Outbox: `INSERT` + `INSERT` in one transaction, relay publishes | **9.4 ms** | 11,208 |

**5.2× the latency**, because you moved a Redis round trip onto a Postgres commit.
Pulse's answer is **both**: publish to the stream *and* write the outbox row, and
let the relay publish only rows the stream never acknowledged. The stream stays the
fast path; the outbox becomes the audit that catches the crash window. That
compromise costs one extra insert on the write path (+1.9 ms) and is the design the
lab builds.

### Outbox versus CDC

| | Outbox | CDC (Debezium / logical decoding) |
|---|--------|----------------------------------|
| Latency | poll interval (or instant with `LISTEN`/`NOTIFY`) | near-real-time |
| Payload | exactly what you chose to publish | raw row changes; you shape them downstream |
| Extra infrastructure | a Celery beat task | a Connect cluster and a replication slot |
| **Failure mode** | a backlog grows in a table you can `SELECT count(*)` from | **a stalled slot pins WAL and fills the disk** |

That last row decides it for Pulse. An outbox backlog is a number on a dashboard
and a task you can scale out. A stalled replication slot is a 3 a.m. disk-full
page, and it is the most common way people take down a Postgres they were using
CDC on. You have already seen the mechanism in this module: `wal_keep_size` versus
a replication slot is the *same* tradeoff, and the lab makes you experience both
sides of it.

---

## What's next

The lab converts `messages` to a partitioned table with a `RunSQL` migration and
measures both the 205,000× retention win and the read tax, automates partition
maintenance and then breaks it on purpose, stands up a streaming replica and
induces read-your-own-writes failures, writes the DB router and the contextvar
sticky window, exhausts `max_connections` and fixes it with PgBouncer, reproduces
all three prepared-statement and cursor failures, and builds the outbox — then
kills the process between persist and publish to prove nothing is lost.

See you in [`lab.md`](./lab.md).
