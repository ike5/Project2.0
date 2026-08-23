# Cheatsheet — Postgres at Chat Scale (Django edition)

---

## Message ID design

| Scheme | Bits | Time-sortable | Coordination | Index locality | Notes |
|--------|------|---------------|--------------|----------------|-------|
| `BigAutoField` (bigserial) | 64 | Yes | **Central sequence** | Excellent | Django's default. The sequence is a single point of contention and blocks sharding |
| UUIDv4 (`uuid4`) | 128 | No | None | **Terrible** | Random inserts → page splits, bloat, cold cache. Avoid for high-write tables |
| UUIDv7 | 128 | Yes | None | Good | Standards-track, `uuid6`/native support. 2× the bytes of a Snowflake |
| Snowflake | 64 | Yes | Worker ID only | Excellent | 41-bit ms + 10-bit worker + 12-bit seq. What Discord/Twitter use |

```
Snowflake layout (64 bits):
 ┌─┬──────────────────────────────────┬──────────┬────────────┐
 │0│      timestamp ms (41 bits)      │worker(10)│  seq (12)  │
 └─┴──────────────────────────────────┴──────────┴────────────┘
   sign      ~69 years from epoch      1024 nodes  4096/ms/node
```

The ID **is** the timestamp and **is** the pagination cursor. Storing a separate
`created_at` for ordering is redundant (keep it for humans).

> In Django, generate the ID in Python (a Snowflake helper or `uuid7()`) and set
> it as the PK explicitly — do **not** lean on `BigAutoField`, whose central
> sequence is exactly what sharding (Module 14) can't have.

```python
class Message(models.Model):
    id = models.BigIntegerField(primary_key=True)          # Snowflake, set in code
    room = models.ForeignKey(Room, on_delete=models.CASCADE, db_index=False)
    sender_id = models.BigIntegerField()
    client_id = models.UUIDField()                          # idempotency key
    body = models.TextField()
    created_at = models.DateTimeField()
    class Meta:
        indexes = [models.Index(fields=["room", "-id"])]    # scrollback
        constraints = [models.UniqueConstraint(
            fields=["room", "client_id"], name="uq_room_cid")]  # dedup
```

---

## Core schema shape (the DDL under the ORM)

```sql
CREATE TABLE chat_message (
    id          bigint      NOT NULL,          -- Snowflake
    room_id     bigint      NOT NULL,
    sender_id   bigint      NOT NULL,
    client_id   uuid        NOT NULL,          -- idempotency key
    body        text        NOT NULL,
    created_at  timestamptz NOT NULL DEFAULT now(),
    edited_at   timestamptz,
    deleted_at  timestamptz
) PARTITION BY RANGE (created_at);

-- The scrollback query index. Order matters: equality col first, range col second.
CREATE INDEX ON chat_message (room_id, id DESC);

-- Idempotency. Unique per room + client id.
CREATE UNIQUE INDEX ON chat_message (room_id, client_id);
```

> **Index column order rule:** for `WHERE room_id = ? AND id < ? ORDER BY id
> DESC`, the index must be `(room_id, id)`. `(id, room_id)` cannot serve it.

Django can't emit `PARTITION BY` from a model, so the partitioned parent and its
children are created in a `RunSQL` migration (below), and the model is managed
against it.

---

## Keyset pagination (never OFFSET)

```python
# FIRST page
qs = (Message.objects
      .filter(room_id=7)
      .order_by("-id")[:50])

# NEXT page — cursor is the last id you saw
qs = (Message.objects
      .filter(room_id=7, id__lt=cursor)
      .order_by("-id")[:50])
```

The SQL those produce:
```sql
SELECT id, sender_id, body, created_at FROM chat_message
WHERE room_id = 7 AND id < 1735689600123456789
ORDER BY id DESC LIMIT 50;
```

Why not Django's `Paginator` / `OFFSET`:
```sql
EXPLAIN ANALYZE SELECT * FROM chat_message WHERE room_id=7 ORDER BY id DESC LIMIT 50 OFFSET 100000;
--  ... rows=50 ... but it READ AND DISCARDED 100,000 rows first.
```
`OFFSET n` is O(n). Keyset is O(log n + limit), forever, at any depth. `Paginator`
also fires a `COUNT(*)` — another full scan. Neither belongs on a hot scrollback.

---

## Declarative partitioning by time (via RunSQL migration)

```python
# migrations/00xx_partition_messages.py
from django.db import migrations

class Migration(migrations.Migration):
    operations = [
        migrations.RunSQL(
            sql="""
              CREATE TABLE chat_message_2026_08 PARTITION OF chat_message
                  FOR VALUES FROM ('2026-08-01') TO ('2026-09-01');
              CREATE TABLE chat_message_default PARTITION OF chat_message DEFAULT;
            """,
            reverse_sql="""
              DROP TABLE chat_message_2026_08;
              DROP TABLE chat_message_default;
            """,
        ),
    ]
```

```sql
-- confirm routing
SELECT tableoid::regclass, count(*) FROM chat_message GROUP BY 1;

-- confirm PRUNING (the read win)
EXPLAIN (ANALYZE, BUFFERS)
SELECT * FROM chat_message
WHERE room_id=7 AND created_at >= '2026-08-01' ORDER BY id DESC LIMIT 50;
-- look for:  Partitions removed: 11
```

**Retention becomes free:**
```sql
DROP TABLE chat_message_2025_08;             -- instant, ~no WAL
-- vs
DELETE FROM chat_message WHERE created_at < '2025-09-01';   -- hours, GBs of WAL,
                                                            -- then a vacuum problem
```

Settings that matter:
```sql
SET enable_partition_pruning = on;        -- default on
SET plan_cache_mode = force_custom_plan;  -- generic plans can defeat pruning on
                                          -- parameterized queries (and Django
                                          -- server-side-prepares by default)
```

> **Partition on `created_at`, index on `(room_id, id)`.** Partitioning by
> `room_id` instead sounds appealing but gives you thousands of partitions, a
> planning-time explosion, and no retention story.

Automate partition creation with `pg_partman` or a nightly Celery task — a missing
future partition means inserts land in `DEFAULT` (or fail, if you skipped it).
This is the **74 TB/year @ 10k msg/s** projection from Module 12 made survivable.

---

## Replication + read replicas via a Django DB router

Configure two connections, then let a router send reads to the replica:

```python
# settings.py
DATABASES = {
    "default": {  # primary — all writes
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "pulse", "HOST": "pg-primary", "USER": "pulse", ...
    },
    "replica": {  # read replica
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "pulse", "HOST": "pg-replica", "USER": "pulse", ...
        "TEST": {"MIRROR": "default"},
    },
}
DATABASE_ROUTERS = ["pulse.routers.ReplicaRouter"]
```

```python
# routers.py
class ReplicaRouter:
    def db_for_read(self, model, **hints):
        return "replica"
    def db_for_write(self, model, **hints):
        return "default"
    def allow_relation(self, a, b, **hints):
        return True
```

Inspect lag:
```sql
-- On the primary
SELECT client_addr, state, sent_lsn, write_lsn, flush_lsn, replay_lsn,
       write_lag, flush_lag, replay_lag
FROM pg_stat_replication;

-- On the replica
SELECT pg_is_in_recovery();                                 -- t
SELECT now() - pg_last_xact_replay_timestamp() AS lag_time;
```

| `synchronous_commit` | Meaning | Loss on primary crash |
|----------------------|---------|-----------------------|
| `off` | Don't even wait for local WAL flush | Up to `wal_writer_delay` |
| `local` | Local WAL flushed | None locally, replica may lag |
| `remote_write` | Replica received it | Loss if replica OS crashes |
| `on` (default) | Replica flushed to disk | None |
| `remote_apply` | Replica *applied* it — reads are consistent | None; slowest |

**Read-your-writes with a replica router** — the "I sent a message then couldn't
see it" bug. Options, in order of preference for chat:

1. **Echo optimistically** — the sender already has the message; don't read it
   back at all. Best answer for chat specifically.
2. Route that user's reads to `default` for N seconds after a write. Crude,
   effective. In Django: use `.using("default")` on that request's reads.
3. Capture the write's LSN and have the read wait for
   `pg_last_wal_replay_lsn() >= :lsn`. Precise, more plumbing.
4. `synchronous_commit = remote_apply` for the writes that need it. Costs write
   latency on every such write.

---

## Connection pooling / PgBouncer with psycopg

Postgres forks a **process per connection** (~5–10 MB each). Now multiply by your
**worker processes**: 8 Uvicorn workers × a pool each × 3 app instances is a lot
of Postgres backends. This is worse than the JVM (one process, one pool) — the
process-per-core model multiplies your connection count, so PgBouncer matters
*sooner*.

```ini
[databases]
pulse = host=pg-primary port=5432 dbname=pulse

[pgbouncer]
pool_mode = transaction
max_client_conn = 10000
default_pool_size = 25
reserve_pool_size = 5
server_idle_timeout = 60
```

| Mode | Server conn held for | Breaks |
|------|---------------------|--------|
| `session` | The whole client session | Nothing; barely helps |
| `transaction` | One transaction | Session state: `SET`, advisory locks, `LISTEN/NOTIFY`, **server-side prepared statements**, temp tables, cursors outside a txn |
| `statement` | One statement | Multi-statement transactions entirely |

**Transaction mode is the one you want** — but psycopg (Django's Postgres driver)
uses **server-side prepared statements by default**, and in transaction pooling
those land on random backends and blow up with *"prepared statement already
exists"* / *"does not exist"*. Fixes:

```python
# settings.py — psycopg 3, disable server-side prepares under PgBouncer txn mode
DATABASES["default"]["OPTIONS"] = {
    "prepare_threshold": None,            # psycopg3: never use server-side prepares
    # older psycopg2 path uses a different knob; Module 13 covers both
}
DATABASES["default"]["CONN_MAX_AGE"] = 0  # let PgBouncer own pooling, not Django
DATABASES["default"]["DISABLE_SERVER_SIDE_CURSORS"] = True   # required for txn pooling
```

> `CONN_MAX_AGE=0` + PgBouncer looks wasteful but is correct: Django's persistent
> connections and PgBouncer's pool fight each other. Pick one pooler — under load,
> pick PgBouncer.

Rough sizing: `pool_size ≈ (core_count × 2) + effective_spindle_count`. For a
16-core box that's ~34, not 500. More connections past that point makes throughput
*worse*.

```sql
SELECT state, count(*) FROM pg_stat_activity GROUP BY 1;
```
```bash
psql -p 6432 pgbouncer -c "SHOW POOLS;"     # cl_waiting > 0 sustained = pool too small
psql -p 6432 pgbouncer -c "SHOW STATS;"
```

---

## The transactional outbox (relayed by Celery)

The dual-write problem: persist the message, then publish to Redis. Crash in
between and the two disagree — forever.

```sql
CREATE TABLE outbox (
    id           bigserial PRIMARY KEY,
    aggregate_id bigint      NOT NULL,
    payload      jsonb       NOT NULL,
    created_at   timestamptz NOT NULL DEFAULT now(),
    published_at timestamptz
);
CREATE INDEX ON outbox (id) WHERE published_at IS NULL;   -- partial: only the backlog
```

Write both rows in one transaction:
```python
from django.db import transaction

@database_sync_to_async
def persist(room_id, body, client_id):
    with transaction.atomic():
        msg = Message.objects.create(room_id=room_id, body=body, client_id=client_id, ...)
        Outbox.objects.create(aggregate_id=room_id, payload={"id": msg.id, ...})
    return msg                                  # atomic: both rows, or neither
```

Celery relay loop, safe with multiple relay workers:
```python
@shared_task
def relay_outbox():
    with transaction.atomic():
        rows = (Outbox.objects
                .select_for_update(skip_locked=True)      # ← the important part
                .filter(published_at__isnull=True)
                .order_by("id")[:100])
        ids = []
        for row in rows:
            xadd_to_redis(row.payload)                     # publish
            ids.append(row.id)
        Outbox.objects.filter(id__in=ids).update(published_at=timezone.now())
```

`select_for_update(skip_locked=True)` (`FOR UPDATE SKIP LOCKED`) lets N relay
workers work the same table without blocking or double-publishing. Delivery is
**at-least-once** (you can publish then crash before the UPDATE), which is why
consumers dedup on `client_id`.

**Outbox vs CDC (Debezium/logical decoding):**

| | Outbox | CDC |
|---|--------|-----|
| Latency | Poll interval (or `LISTEN/NOTIFY` to go instant) | Near-real-time |
| Payload | Exactly what you chose to publish | Raw row changes; shape them downstream |
| Extra infra | A Celery beat task | Connect cluster, replication slots |
| Failure mode | Backlog grows in a table you can see | **A stalled slot pins WAL and fills the disk** |

---

## EXPLAIN, read correctly

```sql
EXPLAIN (ANALYZE, BUFFERS, VERBOSE, FORMAT TEXT) <query>;
```

| What you see | What it means |
|--------------|---------------|
| `Seq Scan` on a big table | Missing/unusable index — or the planner thinks the scan is cheaper (check `rows=` estimate vs `actual rows=`) |
| Estimate off by >10× | Stale stats. `ANALYZE chat_message;` or raise `default_statistics_target` |
| `Rows Removed by Filter: 90000` | The index got you to the neighbourhood, not the row. Add the filter column to the index |
| `Heap Fetches: 50000` on an Index Only Scan | Visibility map is stale → `VACUUM` |
| `Buffers: shared read=...` large | Cold cache / working set exceeds `shared_buffers` |
| `Partitions removed: 0` when you expected pruning | Predicate isn't on the partition key, or a generic plan is in use |
| `Sort Method: external merge Disk: 40MB` | `work_mem` too small for this query |

> See it in Django with `print(qs.explain(analyze=True, buffers=True))` — it runs
> the same `EXPLAIN` on the query the ORM built. Use it to catch the ORM quietly
> emitting an `OFFSET` or a `COUNT`.

---

## Sharding via a Django DB router

```
shard_id = consistent_hash(room_id) → one of N physical databases
```

```python
# settings.py: DATABASES = {"shard0": {...}, "shard1": {...}, ...}
class ShardRouter:
    def _shard_for(self, room_id):
        return f"shard{consistent_hash(room_id) % N}"
    def db_for_read(self, model, **hints):
        inst = hints.get("instance")
        return self._shard_for(inst.room_id) if inst else None
    def db_for_write(self, model, **hints):
        inst = hints.get("instance")
        return self._shard_for(inst.room_id) if inst else None
```

**Route by `room_id`, not `user_id`.** Chat's dominant query is "the last 50
messages in this room"; sharding by room keeps that query on one node. Sharding by
user makes every room read a scatter-gather.

What you lose:
- Cross-shard `JOIN` and cross-shard transactions. Gone. Denormalize or two round
  trips. (Django won't join across databases anyway — it'll error.)
- Global `ORDER BY`. Merge in the app.
- `BigAutoField`. You need coordination-free IDs — this is *why* Snowflake exists.

**Resharding** is the hard part. Use consistent hashing (or many more logical
shards than physical nodes — 4096 logical → 8 physical, move logical shards
around) so adding a node remaps `1/n` of keys instead of all of them.

Alternatives before you shard, in order of preference:
1. Partition + drop old data. Most "we need to shard" is "we need retention."
2. Read replicas. Solves read scaling, does nothing for writes.
3. Bigger box. Genuinely: a 96-core machine with NVMe goes further than you think.
4. Then shard.

---

## Chat query patterns and their indexes

| Query | Index |
|-------|-------|
| Scrollback: last N in a room | `(room_id, id DESC)` |
| Jump to a point in history | `(room_id, id DESC)` — same one, keyset from a cursor |
| Idempotent insert | `UNIQUE (room_id, client_id)` |
| Unread count since a marker | `(room_id, id)` + a per-user `last_read_id` — **count in Redis, not SQL** |
| A user's rooms | `(user_id, room_id)` on membership |
| Search | Not Postgres FTS at scale — Elasticsearch/OpenSearch. `tsvector` + GIN is fine up to a few million rows |

---

## Vacuum, at write volume

Chat is insert-heavy and update-light, the *easy* case — but:

```sql
SELECT relname, n_live_tup, n_dead_tup, last_autovacuum, last_autoanalyze
FROM pg_stat_user_tables ORDER BY n_dead_tup DESC LIMIT 10;

-- transaction ID wraparound risk — check this before it checks you
SELECT datname, age(datfrozenxid) FROM pg_database ORDER BY 2 DESC;
```

Insert-only partitions still need `VACUUM` to set the visibility map (for
index-only scans) and to freeze tuples. Postgres 13+ autovacuums insert-only
tables via `autovacuum_vacuum_insert_threshold` — confirm it's not disabled. For
high-write tables:
```
autovacuum_vacuum_cost_limit = 2000     # default 200 is far too timid
autovacuum_naptime = 15s
```
