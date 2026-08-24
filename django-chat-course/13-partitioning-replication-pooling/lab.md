# Lab 13 — Partition It, Replicate It, Pool It, and Stop Losing Writes

**You'll:** convert `messages` to a time-partitioned table without a table
rewrite, measure retention at **41 minutes versus 12 milliseconds**, pay the read
tax and then claw it back with a Snowflake-derived time hint, break partition
maintenance on purpose at midnight, stand up a streaming replica and reproduce
read-your-own-writes, write the Django router and the `contextvar` sticky window,
exhaust `max_connections` and fix it with PgBouncer, hit all three of Django's
transaction-pooling failures, and finally build the outbox and kill a worker
between persist and publish to prove nothing is lost.

⏱️ ~120 min. Work in `apps/pulse`.

```bash
docker compose -p pulse-dev  -f ../../infra/compose.dev.yml down
docker compose -p pulse-repl -f ../../infra/compose.replica.yml up -d --wait
alias pg='docker exec -i pulse-pg-primary psql -U pulse -d pulse'
alias pgr='docker exec -i pulse-pg-replica psql -U pulse -d pulse'
```

> **Low-memory path:** load 5,000,000 rows instead of 50,000,000 everywhere below.
> Every ratio holds; only the absolute times shrink.

You are starting from Module 12's store: table `messages`, `PRIMARY KEY
(room_id, seq)`, `UNIQUE (room_id, client_id)`, three indexes, a `managed = False`
model, 50 million rows and a projection of **74 TB/year**.

---

## Part A — Partition without a rewrite

The naive conversion is `CREATE TABLE messages_new (...) PARTITION BY RANGE
(created_at)` followed by `INSERT INTO messages_new SELECT * FROM messages`. On 50
million rows that is a 14-minute copy and a full-table exclusive lock. There is a
better way, and it is the one you would use in production.

`chat/migrations/0005_partition_messages.py`:

```python
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [("chat", "0004_message_store")]     # Module 12's RunSQL

    operations = [
        migrations.RunSQL(
            sql=r"""
            -- 1. Rename the existing table out of the way. It becomes the first
            --    partition, keeping its data, its heap and its indexes.
            ALTER TABLE messages RENAME TO messages_legacy;

            -- 2. A CHECK constraint that exactly matches the partition bound we
            --    are about to attach it with. This is the trick: with a matching
            --    VALID constraint already present, ATTACH PARTITION SKIPS THE
            --    FULL SCAN it would otherwise do to prove no row is out of range.
            --    Adding the constraint itself is one scan; without it, ATTACH is
            --    a second scan under ACCESS EXCLUSIVE.
            ALTER TABLE messages_legacy
                ADD CONSTRAINT messages_legacy_range
                CHECK (created_at >= '2000-01-01' AND created_at < '2026-09-01')
                NOT VALID;
            ALTER TABLE messages_legacy VALIDATE CONSTRAINT messages_legacy_range;

            -- 3. The new parent. Note what changed from Module 12:
            --      PRIMARY KEY (room_id, seq)      -> (room_id, seq, created_at)
            --      UNIQUE (room_id, client_id)     -> (room_id, client_id, created_at)
            --    Postgres REQUIRES the partition key in every unique index on a
            --    partitioned table. Both guarantees are now enforced WITHIN A
            --    PARTITION only. Write that down; see the note below.
            CREATE TABLE messages (
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
                PRIMARY KEY (room_id, seq, created_at)
            ) PARTITION BY RANGE (created_at);

            CREATE UNIQUE INDEX idx_messages_dedup
                ON messages (room_id, client_id, created_at);
            CREATE INDEX idx_messages_scrollback
                ON messages (room_id, id DESC) WHERE deleted_at IS NULL;
            CREATE INDEX idx_messages_thread
                ON messages (reply_to, id) WHERE reply_to IS NOT NULL;

            -- 4. Attach the old table as the historical partition. Because the
            --    CHECK constraint is present and VALID, this is metadata-only.
            ALTER TABLE messages ATTACH PARTITION messages_legacy
                FOR VALUES FROM ('2000-01-01') TO ('2026-09-01');

            COMMENT ON TABLE messages IS
              'Partitioned by created_at, monthly. Retention is DROP TABLE.
               NOTE: uniqueness on (room_id, seq) and (room_id, client_id) is
               enforced PER PARTITION only. See Module 13 README.';
            """,
            reverse_sql=r"""
            ALTER TABLE messages DETACH PARTITION messages_legacy;
            DROP TABLE messages;
            ALTER TABLE messages_legacy RENAME TO messages;
            ALTER TABLE messages DROP CONSTRAINT messages_legacy_range;
            """,
        ),
    ]
```

```bash
time python manage.py migrate chat
```
**Expected:**
```
  Applying chat.0005_partition_messages... OK

real    1m41.208s
```

✅ **101 seconds for 50 million rows**, almost all of it the one `VALIDATE
CONSTRAINT` scan. Compare with the copy approach:

```bash
pg -c "\timing on" -c "CREATE TABLE t AS SELECT * FROM messages_legacy;" -c "DROP TABLE t;"
```
```
Time: 841204.118 ms (14:01.204)
```

✅ **8.3× faster, and no exclusive lock on the live table** except for the
metadata-only `ATTACH`. Verify:

```bash
pg -c "\d+ messages" | head -20
```
**Expected:**
```
                        Partitioned table "public.messages"
   Column   |           Type           | Nullable |
------------+--------------------------+----------+
 id         | bigint                   | not null |
 ...
Partition key: RANGE (created_at)
Indexes:
    "messages_pkey" PRIMARY KEY, btree (room_id, seq, created_at)
    "idx_messages_dedup" UNIQUE, btree (room_id, client_id, created_at)
    "idx_messages_scrollback" btree (room_id, id DESC) WHERE deleted_at IS NULL
    "idx_messages_thread" btree (reply_to, id) WHERE reply_to IS NOT NULL
Partitions: messages_legacy FOR VALUES FROM ('2000-01-01') TO ('2026-09-01')
```

> ⚠️ **Two guarantees just changed meaning, with no application code edited.**
>
> `UNIQUE (room_id, client_id, created_at)` enforces idempotency **within a
> partition**. A retry that crosses a month boundary inserts a second row.
> Module 10 predicted this; now it is true. Bound your client's retry policy far
> inside the partition width, and keep the Redis `SET NX EX 86400` dedup key in
> front (Module 10 Part I) — Redis does not care about month boundaries.
>
> `PRIMARY KEY (room_id, seq, created_at)` no longer prevents a duplicate `seq`
> across partitions. Module 10's Redis high-water-mark recovery just went from
> "belt and braces" to **load-bearing**. Say so in the runbook.

Now create the forward partitions:

```bash
python manage.py shell -c "from chat.partitions import create_ahead; print(create_ahead(3))"
pg -c "SELECT relname FROM pg_class c JOIN pg_inherits i ON i.inhrelid=c.oid
       JOIN pg_class p ON p.oid=i.inhparent WHERE p.relname='messages' ORDER BY 1;"
```
**Expected:**
```
['messages_2026_09', 'messages_2026_10', 'messages_2026_11', 'messages_2026_12']
      relname
--------------------
 messages_2026_09
 messages_2026_10
 messages_2026_11
 messages_2026_12
 messages_legacy
```

And confirm routing works:

```bash
pg -c "INSERT INTO messages (id, room_id, seq, sender, client_id, body)
       VALUES (99999999, 'room.1', 99999999, 'alice', 'c-part-1', 'routed');"
pg -c "SELECT tableoid::regclass, count(*) FROM messages
       WHERE room_id='room.1' GROUP BY 1;"
```
**Expected:**
```
     tableoid     | count
------------------+-------
 messages_2026_09 |     1
 messages_legacy  | 50000
```

✅ The insert landed in the current month's partition without the application
knowing partitions exist.

---

## Part B — Retention: 41 minutes versus 12 milliseconds

The headline measurement of the module. First the old way, on the legacy
partition:

```bash
pg -c "SELECT pg_size_pretty(pg_total_relation_size('messages_legacy'));"
pg -c "SELECT pg_current_wal_lsn();"
```
```
 11 GB
 0/8A41F2C8
```

```bash
time pg -c "DELETE FROM messages_legacy WHERE created_at < '2026-06-01';"
pg -c "SELECT pg_current_wal_lsn();"
pg -c "SELECT pg_size_pretty(pg_total_relation_size('messages_legacy'));"
pg -c "SELECT n_dead_tup, last_autovacuum FROM pg_stat_user_tables
       WHERE relname='messages_legacy';"
```
**Expected:**
```
DELETE 18240104

real    41m12.408s

 pg_current_wal_lsn
--------------------
 0/1D8A41F2C8            <-- 8.2 GB of WAL for a delete
 11 GB                   <-- SAME SIZE. Nothing was returned.
 n_dead_tup | last_autovacuum
------------+-----------------
   18240104 |
```

✅ **41 minutes, 8.2 GB of WAL, zero disk reclaimed, and 18 million dead tuples**
now queued for autovacuum, which will compete with your live traffic for I/O for
the rest of the day. And that is 18 million rows — Pulse produces 864 million a
*day*.

Reclaiming the space needs an exclusive lock and a second copy on disk:

```bash
time pg -c "VACUUM FULL messages_legacy;"
pg -c "SELECT pg_size_pretty(pg_total_relation_size('messages_legacy'));"
```
```
real    12m8.402s
 6841 MB
```

Now the partitioned way. Restore, then:

```bash
time python manage.py shell -c "
from chat.partitions import drop_expired
print(drop_expired(retain_days=90))"
```
**Expected:**
```
['messages_2026_05']

real    0m0.014s
```

```bash
pg -c "SELECT pg_current_wal_lsn();"
pg -c "SELECT pg_size_pretty(pg_database_size('pulse'));"
```
```
 0/1D8A420148         <-- 640 bytes of WAL
 6841 MB              <-- 4.1 GB returned, immediately
```

The scoreboard:

| | `DELETE` + `VACUUM FULL` | `DETACH` + `DROP TABLE` |
|---|---|---|
| Wall time | 53 min 20 s | **0.014 s** |
| WAL generated | 8.2 GB | **640 B** |
| Disk returned | after 12 more minutes, under an exclusive lock | **immediately** |
| Dead tuples left | 18,240,104 | **0** |
| Blocks live traffic | yes, for the whole `VACUUM FULL` | no |

✅ **229,000× faster, 13 million times less WAL.** That single row is the entire
argument for partitioning. Everything else in this section is a detail.

Record it:
```markdown
## Module 13 — Retention

- DELETE 18.2M rows: 41m12s, 8.2 GB WAL, 0 bytes reclaimed, 18.2M dead tuples
- VACUUM FULL to reclaim: +12m08s under ACCESS EXCLUSIVE
- DETACH CONCURRENTLY + DROP TABLE: 0.014s, 640 B WAL, 4.1 GB returned instantly
```

---

## Part C — Pay the read tax, then claw it back

Partitioning is **not free for reads**, and this is the module's honest
admission. Module 12 measured the scrollback query at 0.118 ms. Re-measure it now:

```bash
pg -c "EXPLAIN (ANALYZE, BUFFERS)
SELECT id, sender, body, seq FROM messages
WHERE room_id = 'room.42' AND id < 7241938472948572160 AND deleted_at IS NULL
ORDER BY id DESC LIMIT 50;"
```
**Expected:**
```
 Limit  (cost=2.34..91.04 rows=50 width=118) (actual time=0.084..0.891 rows=50 loops=1)
   ->  Merge Append  (cost=2.34..66412.08 rows=37402 width=118)
         Sort Key: messages.id DESC
         ->  Index Scan using messages_legacy_scrollback on messages_legacy
         ->  Index Scan using messages_2026_09_scrollback on messages_2026_09
         ->  Index Scan using messages_2026_10_scrollback on messages_2026_10
         ->  Index Scan using messages_2026_11_scrollback on messages_2026_11
         ->  Index Scan using messages_2026_12_scrollback on messages_2026_12
         Buffers: shared hit=284
 Execution Time: 0.912 ms
```

✅ **0.118 ms → 0.912 ms, a 7.7× regression.** No partition was pruned, because
the query has no `created_at` predicate — it pages by the Snowflake `id`, exactly
as Module 12 designed it to. Five index scans and a `Merge Append` where there was
one index scan.

### The fix: the cursor already contains a timestamp

Module 12's `code/snowflake.py` puts 41 bits of milliseconds-since-epoch in the
high bits of every id. So the cursor *is* a time, and you can hand that to the
planner for free:

```python
# chat/snowflake.py — already there from Module 12
PULSE_EPOCH_MS = 1704067200000        # 2024-01-01T00:00:00Z


def timestamp_of(snowflake_id: int) -> int:
    """Epoch milliseconds encoded in a Snowflake id."""
    return (snowflake_id >> 22) + PULSE_EPOCH_MS
```

```python
# chat/history.py
def scrollback(room_key: str, cursor_id: int, limit: int = 50):
    # One day of slack absorbs clock skew between workers and the fact that a
    # message's created_at is set by Postgres, not by the id generator.
    floor_ms = timestamp_of(cursor_id) - 86_400_000
    with connection.cursor() as cur:
        cur.execute(
            """
            SELECT id, sender, body, seq FROM messages
             WHERE room_id = %s
               AND id < %s
               AND created_at > to_timestamp(%s / 1000.0)   -- the hint
               AND deleted_at IS NULL
             ORDER BY id DESC LIMIT %s
            """,
            [room_key, cursor_id, floor_ms, limit])
        return cur.fetchall()
```

```bash
pg -c "EXPLAIN (ANALYZE, BUFFERS)
SELECT id, sender, body, seq FROM messages
WHERE room_id = 'room.42' AND id < 7241938472948572160
  AND created_at > '2026-09-14' AND deleted_at IS NULL
ORDER BY id DESC LIMIT 50;"
```
**Expected:**
```
 Limit  (cost=0.56..38.94 rows=50 width=118) (actual time=0.042..0.109 rows=50 loops=1)
   ->  Index Scan using messages_2026_09_scrollback on messages_2026_09
         Index Cond: ((room_id = 'room.42'::text) AND (id < 7241938472948572160))
         Buffers: shared hit=56
 Planning Time: 0.284 ms
 Execution Time: 0.134 ms
```

✅ **0.134 ms — back within 14% of the unpartitioned baseline**, one index scan,
no `Merge Append`, and the other four partitions were pruned at plan time.

| Query | Execution | Partitions scanned |
|-------|-----------|--------------------|
| Module 12, unpartitioned | 0.118 ms | — |
| Partitioned, no time hint | 0.912 ms | 5 |
| **Partitioned + Snowflake time hint** | **0.134 ms** | **1** |

Now watch the planning cost grow with the partition count, so you know why "12
monthly" and not "365 daily":

```bash
python code/partition_scale.py --counts 12 36 120 365 1000
```
**Expected:**
```
partitions=  12   planning=0.28ms  execution=0.13ms
partitions=  36   planning=0.61ms  execution=0.14ms
partitions= 120   planning=1.94ms  execution=0.14ms
partitions= 365   planning=5.81ms  execution=0.15ms
partitions=1000   planning=16.4ms  execution=0.15ms
```

✅ **Planning time is linear in the partition count and it is paid by every query
in the system**, including single-row lookups that touch one partition. At 1,000
partitions you have added 16 ms to every query to save nothing.

> **`plan_cache_mode`.** Postgres may reuse a *generic* plan for a parameterized
> query after five executions, and a generic plan cannot prune on a parameter it
> has not seen. Symptom: your query is fast five times and then slow forever.
> ```sql
> SET plan_cache_mode = force_custom_plan;
> ```
> Django, with `prepare_threshold` at its psycopg 3 default of 5, walks straight
> into this. It is the second reason to think about that setting, and Part F is
> the first.

---

## Part D — Break maintenance on purpose

Set the clock forward to a month boundary with no future partition:

```bash
pg -c "DROP TABLE messages_2026_10, messages_2026_11, messages_2026_12;"
pg -c "INSERT INTO messages (id, room_id, seq, sender, client_id, body, created_at)
       VALUES (1, 'room.1', 500000, 'alice', 'c-future', 'hello october',
               '2026-10-01 00:00:01+00');"
```
**Expected:**
```
ERROR:  no partition of relation "messages" found for row
DETAIL:  Partition key of the failing row contains (created_at) = (2026-10-01 00:00:01+00).
```

✅ **Every send in the system fails at midnight on the 1st.** Loud, immediate,
attributable — which is exactly what you want, and is why Pulse has no `DEFAULT`
partition.

Now try the alternative, so you understand what you rejected:

```bash
pg -c "CREATE TABLE messages_default PARTITION OF messages DEFAULT;"
pg -c "INSERT INTO messages (id, room_id, seq, sender, client_id, body, created_at)
       VALUES (1, 'room.1', 500000, 'alice', 'c-future', 'hello october',
               '2026-10-01 00:00:01+00');"
pg -c "SELECT tableoid::regclass, count(*) FROM messages
       WHERE client_id='c-future' GROUP BY 1;"
```
```
INSERT 0 1
     tableoid      | count
-------------------+-------
 messages_default  |     1
```

No error. Now a month of traffic lands there, and your maintenance task tries to
create October's partition:

```bash
pg -c "INSERT INTO messages (id, room_id, seq, sender, client_id, body, created_at)
       SELECT g, 'room.1', 600000+g, 'a', 'c-d-'||g, 'x',
              '2026-10-01'::timestamptz + (g || ' seconds')::interval
       FROM generate_series(1, 2000000) g;"
time pg -c "CREATE TABLE messages_2026_10 PARTITION OF messages
            FOR VALUES FROM ('2026-10-01') TO ('2026-11-01');"
```
**Expected:**
```
ERROR:  updated partition constraint for default partition "messages_default"
        would be violated by some row
```
or, once you move the rows out first, the version that hurts:
```
real    3m41.208s        <-- ACCESS EXCLUSIVE on the parent, the whole time
```

✅ **A routine maintenance task became a 3-minute total outage**, because
Postgres must scan the entire default partition to prove no row belongs in the new
range, and it holds `ACCESS EXCLUSIVE` on the parent while it does.

```bash
pg -c "DROP TABLE messages_default;"
python manage.py shell -c "from chat.partitions import create_ahead; print(create_ahead(3))"
```

### Alert on the invariant, never on the job

Copy [`code/partitions.py`](./code/partitions.py) to `chat/partitions.py` and
schedule it:

```python
# settings.py
CELERY_BEAT_SCHEDULE = {
    "maintain-partitions": {
        "task": "chat.maintain_partitions",
        "schedule": crontab(hour=3, minute=17),
    },
}
```

```bash
celery -A pulse beat -l info &
celery -A pulse worker -l info &
python manage.py shell -c "
from chat.partitions import maintain_partitions; print(maintain_partitions())"
curl -s localhost:8000/metrics | grep pulse_partitions
```
**Expected:**
```
{'created': [], 'dropped': ['messages_2026_05'], 'partitions': 5, 'months_ahead': 3}
pulse_partitions_total 5.0
pulse_partitions_months_ahead 3.0
pulse_partition_oldest_age_days 92.0
```

Now delete the beat schedule and watch the *metric* catch it, which the task's own
logs never could:

```promql
pulse_partitions_months_ahead < 2   for 6h    -> warn
pulse_partitions_months_ahead < 1   for 1h    -> page
```

> **A task that stops running emits nothing.** No error, no metric, no log line —
> you cannot alert on the absence of something you never see. You *can* alert on
> the state it was supposed to maintain, and that alert also fires when the task
> ran and did the wrong thing. **Alert on the invariant, not on the job.** This is
> the single most portable lesson in this module and Module 20 uses it repeatedly.

---

## Part E — The replica, and reading your own writes

The replica is already up. Confirm the streaming actually took:

```bash
pg -c "SELECT client_addr, state, sync_state,
              pg_wal_lsn_diff(sent_lsn, replay_lsn) AS bytes_behind, replay_lag
       FROM pg_stat_replication;"
pgr -c "SELECT pg_is_in_recovery(), now() - pg_last_xact_replay_timestamp() AS lag;"
```
**Expected:**
```
 client_addr | state     | sync_state | bytes_behind |   replay_lag
-------------+-----------+------------+--------------+-----------------
 172.19.0.3  | streaming | async      |            0 | 00:00:00.004
 pg_is_in_recovery |      lag
-------------------+-----------------
 t                 | 00:00:00.006
```

✅ 4 ms behind at idle. Now put it under load and watch it move:

```bash
python code/replica_lag.py --duration 120 &
python manage.py shell < code/write_bench.py     # Module 12's 224k/s executemany
wait
```
**Expected:**
```
lag p50   :    8 ms
lag p95   :  112 ms
lag p99   :  340 ms
lag p99.9 : 4,214 ms      <-- during the 500-row outbox batch commits
lag max   : 6,802 ms
```

✅ **p99.9 of 4.2 seconds** during a batch write. A replica's lag is not a
constant, it is a function of your write pattern — and batching, which Module 12
adopted for throughput, is precisely what makes the tail bad.

### Reproduce the bug

```bash
python code/ryow_probe.py --iterations 2000 --delay-ms 50
```
```python
# code/ryow_probe.py (core)
for i in range(N):
    msg_id = write_message(room, f"c-ryow-{i}")          # -> default (primary)
    time.sleep(delay_ms / 1000)
    found = Message.objects.using("replica").filter(id=msg_id).exists()
    misses += 0 if found else 1
```
**Expected:**
```
delay=  0ms : 412 / 2000 reads missed their own write (20.6%)
delay= 50ms : 361 / 2000 (18.1%)
delay=200ms :  94 / 2000  (4.7%)
delay=  1s  :   3 / 2000  (0.2%)
delay=  5s  :   0 / 2000  (0.0%)
```

✅ **18% of reads 50 ms after a write do not see it.** That is not an edge case;
that is a fifth of your users seeing their own message vanish.

### The router

Copy [`code/routers.py`](./code/routers.py) to `pulse/routers.py`:

```python
# settings.py
DATABASES = {
    "default": {"ENGINE": "django.db.backends.postgresql", "NAME": "pulse",
                "USER": "pulse", "PASSWORD": "pulse",
                "HOST": "localhost", "PORT": 5432},
    "replica": {"ENGINE": "django.db.backends.postgresql", "NAME": "pulse",
                "USER": "pulse", "PASSWORD": "pulse",
                "HOST": "localhost", "PORT": 5433,
                # TRAP 2. Without MIRROR, Django creates a separate EMPTY test
                # database for `replica` and every write-then-read test fails
                # with a result that looks like a router bug.
                "TEST": {"MIRROR": "default"}},
}
DATABASE_ROUTERS = ["pulse.routers.ReplicaRouter"]
```

Prove trap 1 first — comment out `allow_migrate` and run:

```bash
python manage.py migrate
```
**Expected:**
```
django.db.utils.InternalError: cannot execute CREATE TABLE in a read-only transaction
```
and, worse, check what got written before it failed:

```bash
pg -c "SELECT app, name FROM django_migrations ORDER BY id DESC LIMIT 1;"
```
```
 chat | 0006_outbox
```

✅ **The primary now believes a migration ran that did not finish.** Restore
`allow_migrate` returning `db == "default"`.

### The sticky window, and why it must be a ContextVar

```bash
python code/ryow_probe.py --iterations 2000 --delay-ms 50 --router
```
**Expected:**
```
delay= 50ms : 0 / 2000 reads missed their own write (0.0%)
reads served by replica        : 1,608 (80.4%)
reads served by primary_sticky :   392 (19.6%)
```

✅ **Zero misses, and the replica still absorbs 80% of reads.** The sticky window
costs you exactly the reads that were going to be wrong.

Now demonstrate why `threading.local()` is not a substitute. Swap the ContextVar
for a thread-local and run the async path:

```bash
PULSE_STICKY_IMPL=threadlocal python code/ryow_async_probe.py --concurrency 64
```
**Expected:**
```
misses                       : 0 / 2000
reads WRONGLY sent to primary : 1,904 / 2000  (95.2%)
```

✅ Zero misses — because **every** read went to the primary. asyncio runs
thousands of coroutines on one thread, so one user's thread-local write marker
applies to everyone; the "sticky window" degenerates into "always use the
primary," and your replica does nothing.

```bash
PULSE_STICKY_IMPL=contextvar python code/ryow_async_probe.py --concurrency 64
```
```
misses                       : 0 / 2000
reads WRONGLY sent to primary :  76 / 2000  (3.8%)
```

✅ ContextVars are per-coroutine, and asgiref copies the context across
`database_sync_to_async`'s threadpool hop — so the marker set in the consumer is
visible inside the ORM call, which a thread-local set on the event-loop thread
would not be.

### Two replica failure modes worth meeting now

**1. Query cancelled by recovery conflict.**

```bash
pgr -c "SELECT count(*) FROM messages WHERE body LIKE '%needle%';" &
sleep 2
pg -c "DELETE FROM messages_2026_09 WHERE seq < 1000; VACUUM messages_2026_09;"
wait
```
**Expected:**
```
ERROR:  canceling statement due to conflict with recovery
DETAIL:  User query might have needed to see row versions that must be removed.
```

The replica must choose between replaying WAL (which removes rows your query
needs) and staying behind. `max_standby_streaming_delay=30s` buys the query 30
seconds; `hot_standby_feedback=on` makes the primary stop vacuuming rows the
replica is reading — **and therefore lets a long replica query bloat your
primary.** Pick deliberately. Pulse leaves feedback off, because a bloated primary
is a worse outcome than a cancelled analytics query.

**2. The replication slot versus `wal_keep_size`.**

```bash
docker stop pulse-pg-replica
python manage.py shell < code/write_bench.py     # generate ~2 GB of WAL
pg -c "SELECT slot_name, active, pg_size_pretty(
         pg_wal_lsn_diff(pg_current_wal_lsn(), restart_lsn)) AS retained
       FROM pg_replication_slots;"
pg -c "SELECT pg_size_pretty(sum(size)) FROM pg_ls_waldir();"
```
**Expected:**
```
   slot_name     | active | retained
-----------------+--------+----------
 pulse_replica_1 | f      | 2114 MB
 pg_size_pretty
----------------
 2246 MB
```

✅ **The primary is retaining 2.1 GB of WAL for a replica that is switched off,
and it will keep doing so until the disk is full.** That is the slot's whole
purpose and its whole danger, and it is the same tradeoff as outbox-versus-CDC in
the README — which is why the README picks the outbox.

Set a bound and re-run:

```bash
pg -c "ALTER SYSTEM SET max_slot_wal_keep_size = '1GB'; SELECT pg_reload_conf();"
python manage.py shell < code/write_bench.py
pg -c "SELECT slot_name, active, wal_status, safe_wal_size FROM pg_replication_slots;"
```
```
   slot_name     | active | wal_status | safe_wal_size
-----------------+--------+------------+---------------
 pulse_replica_1 | f      | lost       |
```

✅ `wal_status = lost` — the slot has been invalidated, the disk is safe, and the
replica now needs a **rebuild** rather than a catch-up. Those are the only two
options and you must choose one before it happens, not during.

```bash
docker start pulse-pg-replica
```

---

## Part F — Exhaust the connections, then pool them

Show the arithmetic first:

```bash
pg -c "SHOW max_connections;"
python - <<'PY'
workers = 8; nodes = 3
import os
threads = min(32, (os.cpu_count() or 8) + 4)     # asgiref's default threadpool
print(f"{nodes} nodes x {workers} workers x {threads} threads = "
      f"{nodes * workers * threads} potential backends")
PY
```
**Expected:**
```
 max_connections
-----------------
 200
3 nodes x 8 workers x 12 threads = 288 potential backends
```

Now actually do it:

```bash
python code/connection_storm.py --processes 24 --threads 12
```
**Expected:**
```
opened 200 connections
psycopg.OperationalError: connection failed: FATAL:  sorry, too many clients already
opened: 200   failed: 88   p99 query latency at 200 conns: 84ms
postgres RSS total: 2.1 GB
```

✅ **88 failed connections, 2.1 GB of Postgres process memory, and p99 already at
84 ms** — because past roughly `(cores × 2)` active connections throughput goes
*down*, not up.

Prove that claim directly:

```bash
python code/pool_curve.py --max 200
```
**Expected:**
```
conns   tps      p99
   8   41,204   1.4ms
  16   58,102   1.9ms
  24   61,408   2.6ms      <-- the knee, ~(8 cores x 2) + 8
  48   59,214   6.1ms
  96   54,882  18.4ms
 200   41,902  84.2ms
```

✅ **Peak throughput at 24 connections; 200 connections is 32% *slower* and 60×
worse at p99.** Your database wants dozens of connections. Your application wants
hundreds. PgBouncer's job is to make those compatible.

### Write the config

Create `infra/pgbouncer.ini` (compare with
[`code/pgbouncer.ini`](./code/pgbouncer.ini) when you are done) and
`infra/userlist.txt`:

```
"pulse" "pulse"
```

> PgBouncer 1.21+ can hold plain passwords in `userlist.txt` and still speak
> `scram-sha-256` to Postgres — it computes the verifier itself. Storing the
> plaintext is fine on a laptop and is not fine in production; there, use
> `auth_query` so PgBouncer reads the verifier from `pg_shadow` and no password
> is written to disk at all.

```bash
docker compose -p pulse-repl -f ../../infra/compose.replica.yml --profile pool up -d --wait
psql "postgresql://pulse:pulse@localhost:6432/pgbouncer" -c "SHOW POOLS;"
```
**Expected:**
```
 database  | user  | cl_active | cl_waiting | sv_active | sv_idle | pool_mode
-----------+-------+-----------+------------+-----------+---------+-----------
 pgbouncer | pulse |         1 |          0 |         0 |       0 | statement
 pulse     | pulse |         0 |          0 |         0 |       0 | transaction
```

Point Django at it and re-run the storm:

```python
DATABASES["default"]["HOST"] = "localhost"
DATABASES["default"]["PORT"] = 6432
DATABASES["default"]["CONN_MAX_AGE"] = 0
```

```bash
python code/connection_storm.py --processes 24 --threads 12
psql "postgresql://pulse:pulse@localhost:6432/pgbouncer" -c "SHOW POOLS;" | head -4
pg -c "SELECT count(*) FROM pg_stat_activity WHERE datname='pulse';"
```
**Expected:**
```
opened: 288   failed: 0   p99 query latency: 31ms
 database | user  | cl_active | cl_waiting | sv_active | sv_idle | pool_mode
----------+-------+-----------+------------+-----------+---------+-----------
 pulse    | pulse |       288 |          0 |        22 |       3 | transaction
 count
-------
    25
```

✅ **288 client connections multiplexed onto 25 Postgres backends**, zero
failures, and **p99 improved from 84 ms to 31 ms** because the database is now
running near its throughput peak instead of far past it.

| | Direct | Via PgBouncer |
|---|---|---|
| Connections accepted | 200 of 288 | **288 of 288** |
| Postgres backends | 200 | **25** |
| Postgres RSS | 2.1 GB | **0.3 GB** |
| p99 query latency | 84 ms | **31 ms** |

And the cost of `CONN_MAX_AGE = 0`, which looks wasteful and is not:

```bash
python code/connect_cost.py
```
```
connect to postgres directly : 3.14 ms  (fork a backend, auth, set up)
connect to pgbouncer         : 0.31 ms  (a socket it already had)
```
✅ **10× cheaper**, which is what makes "let PgBouncer own the pooling" affordable.

### The three things Django breaks in transaction mode

**1. Server-side prepared statements.** Run a warm workload:

```bash
python code/prepared_break.py --iterations 200
```
**Expected:**
```
iteration 1..5   ok
iteration 6      psycopg.errors.InvalidSqlStatementName:
                 prepared statement "_pg3_0" does not exist
```

✅ **It works five times and then fails**, because psycopg 3 promotes the query at
`prepare_threshold = 5` and the sixth execution lands on a different backend. Only
under load. Never in development.

Two fixes, both measured:

```bash
PULSE_PREPARE=none  python code/prepared_break.py --iterations 200 --bench
PULSE_PREPARE=bouncer python code/prepared_break.py --iterations 200 --bench
```
```
prepare_threshold=None                      : 0 errors, keyset query 0.86 ms
max_prepared_statements=200 (pgbouncer 1.21+): 0 errors, keyset query 0.79 ms
```

✅ **Disabling prepares costs 9%** (you parse and plan every time).
`max_prepared_statements` recovers it by having PgBouncer track and re-prepare per
server connection. Prefer the second and document the first as the fallback:

```bash
psql "postgresql://pulse:pulse@localhost:6432/pgbouncer" -c "SHOW VERSION;"
```
```
 PgBouncer 1.23.1
```

**2. Server-side cursors.**

```bash
python manage.py shell -c "
from chat.models import Message
for m in Message.objects.filter(room_id='room.1').iterator(chunk_size=1000):
    pass"
```
**Expected:**
```
psycopg.errors.InvalidCursorName: cursor "_django_curs_140234_1" does not exist
```

```python
DATABASES["default"]["DISABLE_SERVER_SIDE_CURSORS"] = True
```

✅ Fixed — and note that Django now buffers the whole result client-side, so this
setting is a *design constraint*, not just a compatibility flag. If you needed
`.iterator()` because the result set is huge, you still need to fix that; you just
need to fix it with keyset pagination (Module 12) instead of a cursor.

**3. `LISTEN`/`NOTIFY`** — which you will want in Part G:

```bash
python code/listen_probe.py --host localhost --port 6432
```
```
LISTEN sent. Waiting 10s for NOTIFY... received 0 notifications.
```
```bash
python code/listen_probe.py --host localhost --port 5432
```
```
LISTEN sent. Waiting 10s for NOTIFY... received 41 notifications.
```

✅ `LISTEN` is session state. In transaction mode your listener's connection is
returned to the pool the moment the transaction ends and the `NOTIFY` goes to
whoever holds that backend next. **A listener needs a direct connection to the
primary, bypassing the pooler.** Remember this for Part G.

---

## Part G — The outbox, and the crash that used to lose a message

### Reproduce the loss first

```bash
export PULSE_CRASH_AFTER_PERSIST=1     # die between the insert and the XADD
python manage.py sendmsg room.60 "this message will vanish" || true
pg -c "SELECT seq, body FROM messages WHERE room_id='room.60' ORDER BY seq DESC LIMIT 1;"
docker exec -i pulse-redis redis-cli XLEN 'room:{room.60}:stream'
```
**Expected:**
```
Killed
 seq |          body
-----+--------------------------
 412 | this message will vanish
(integer) 411
```

✅ **The row is in Postgres and the entry is not in the stream.** Now check what
the connected clients see:

```bash
python code/connected_client.py --room room.60 --seconds 5
```
```
received seqs: [409, 410, 411]
gap detected : no        <-- seq 412 was never announced, so there is nothing to detect
```

✅ **A connected client has no gap to detect**, because `seq` 412 was allocated and
used — the sequence is contiguous from its point of view up to 411, and 412 simply
never arrives. Module 10's resume would find it if the client asked, but a client
that never disconnects never asks. **This is the only loss mode in Pulse invisible
to every mechanism you have built**, and it is exactly what the outbox is for.

### Build it

`chat/migrations/0006_outbox.py`:

```python
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("chat", "0005_partition_messages")]

    operations = [
        migrations.CreateModel(
            name="Outbox",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("room_id", models.TextField()),
                ("payload", models.JSONField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("published_at", models.DateTimeField(blank=True, null=True)),
            ],
            options={"db_table": "outbox"},
        ),
        migrations.AddIndex(
            model_name="outbox",
            # PARTIAL — it covers only the BACKLOG, normally a handful of rows,
            # instead of every message ever sent. At 864M rows/day a full index
            # would be larger than the messages primary key.
            index=models.Index(
                fields=["id"], name="idx_outbox_unpublished",
                condition=models.Q(published_at__isnull=True)),
        ),
    ]
```

Copy [`code/outbox.py`](./code/outbox.py) to `chat/outbox.py` and change the send
path to write both rows in one transaction, XADD, then mark published:

```python
outbox_id = await database_sync_to_async(persist_with_outbox)(
    room_key=room.key, envelope=envelope, sender_id=user.id)
seq, entry_id = await allocator.send(room.key, envelope)     # the fast path
await database_sync_to_async(mark_published)(outbox_id)      # best effort
```

Schedule the relay:

```python
CELERY_BEAT_SCHEDULE["relay-outbox"] = {"task": "chat.relay_outbox", "schedule": 1.0}
```

### Prove it

```bash
celery -A pulse worker -l info & celery -A pulse beat -l info &
export PULSE_CRASH_AFTER_PERSIST=1
python manage.py sendmsg room.61 "this one survives" || true
sleep 3
docker exec -i pulse-redis redis-cli XRANGE 'room:{room.61}:stream' - + COUNT 1
curl -s localhost:8000/metrics | grep pulse_outbox
```
**Expected:**
```
Killed
1) 1) "1735689612345-0"
   2) 1) "payload"
      2) "{\"v\":1,\"type\":\"message.new\",...,\"body\":\"this one survives\"}"
pulse_outbox_relayed_total 1.0
pulse_outbox_backlog 0.0
pulse_outbox_oldest_age_seconds 0.0
```

✅ **The relay published the message the crashed worker never did**, 2.1 seconds
later. Run the connected-client probe again:

```bash
python code/connected_client.py --room room.61 --seconds 5
```
```
received seqs: [409, 410, 411, 412]
```

✅ Nothing lost.

### Prove the relay is safe with several workers

```bash
for i in 1 2 3 4; do celery -A pulse worker -n relay$i -Q celery -l warning & done
python code/outbox_flood.py --rows 50000
sleep 20
pg -c "SELECT count(*) FROM outbox WHERE published_at IS NULL;"
docker exec -i pulse-redis redis-cli XLEN 'room:{room.62}:stream'
```
**Expected:**
```
 count
-------
     0
(integer) 50000
```

✅ **50,000 rows, four relay workers, zero duplicates and zero left behind** —
`select_for_update(skip_locked=True)`. Take `skip_locked` out and re-run:

```bash
PULSE_NO_SKIP_LOCKED=1 python code/outbox_flood.py --rows 50000
```
```
relay throughput: 41,208/s -> 9,140/s   (4.5x slower)
lock waits:       0 -> 14,204
```

✅ Without `SKIP LOCKED` the four workers **queue behind each other** and you have
paid for four processes to get one process's throughput.

### And the cost

```bash
python code/send_bench.py --mode stream-only --mode outbox-only --mode both
```
**Expected:**
```
stream-only (Module 10)                : p50 1.8 ms   31,904 sends/s
outbox-only (relay publishes)          : p50 9.4 ms   11,208 sends/s
both (stream fast path + outbox audit) : p50 3.7 ms   24,104 sends/s
```

✅ **Pulse ships "both": +1.9 ms and −24% throughput to close a loss mode nothing
else can see.** `outbox-only` is 5.2× the latency because it moves a Redis round
trip onto a Postgres commit — write that comparison down, because "just use the
outbox" is advice you will receive and it costs more than the person giving it
thinks.

Finally, the `remote_apply` premium on the outbox write specifically:

```bash
python code/send_bench.py --mode both --sync-commit on
python code/send_bench.py --mode both --sync-commit remote_apply
```
```
synchronous_commit=on           : p50 3.7 ms
synchronous_commit=remote_apply : p50 5.8 ms   (+2.1 ms)
```

✅ **+2.1 ms** to guarantee that a promoted replica has every outbox row — i.e. that
a failover cannot silently drop messages that were accepted. Cheap, and Module 18
cashes it in during the Patroni failover drill.

Record it:
```markdown
## Module 13 — Replication, pooling, outbox

- Replica lag under batch writes: p50 8ms, p99 340ms, p99.9 4.2s
- Read-your-own-writes: 18.1% of reads 50ms after a write missed it; 0% with the
  ContextVar sticky window, and the replica still served 80.4% of reads
- Connections: 288 direct -> 200 accepted, 2.1GB RSS, p99 84ms
              288 via PgBouncer -> 25 backends, 0.3GB RSS, p99 31ms
- Postgres throughput peaks at 24 connections; 200 is 32% slower
- prepare_threshold=None costs 9%; pgbouncer max_prepared_statements recovers it
- Outbox: crash between persist and XADD loses a message a connected client
  cannot even detect; the relay recovers it in 2.1s
- Send path: stream-only 1.8ms | outbox-only 9.4ms | both 3.7ms
```

---

## What you built

- A time-partitioned `messages` table, converted **without a rewrite** by
  attaching the old table with a pre-validated `CHECK` constraint — 101 seconds
  instead of 14 minutes.
- The measurement that justifies the whole exercise: retention at **0.014 s and
  640 B of WAL** instead of **53 minutes and 8.2 GB**.
- The read tax paid (0.118 → 0.912 ms) and clawed back (**0.134 ms**) with a time
  hint derived from the Snowflake ID Module 12 chose.
- The default-partition trap sprung deliberately, and a maintenance task that
  **alerts on the invariant rather than on the job**.
- A streaming replica, its lag measured honestly (**p99.9 of 4.2 s**), and a
  Django router whose sticky window is a **ContextVar** — with the measurement
  showing why `threading.local()` sends 95% of reads to the wrong database.
- Both replica failure modes met in person: recovery conflicts and a slot
  retaining 2.1 GB of WAL for a switched-off replica.
- `max_connections` exhausted and then multiplexed **288 → 25**, with p99 improving
  because fewer connections is faster.
- All three of Django's transaction-pooling breakages reproduced and fixed:
  prepared statements, server-side cursors, and `LISTEN`/`NOTIFY`.
- A transactional outbox that recovers the **one loss mode a connected client
  cannot detect**, relayed by Celery with `SKIP LOCKED`, costing +1.9 ms.

Now do [`challenge.md`](./challenge.md).

Then: [Module 14 — Sharding & Wide-Column](../14-sharding-and-wide-column/).
