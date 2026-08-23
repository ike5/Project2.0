# Lab 12 — Build a Store That Survives Ten Billion Rows

**You'll:** build the schema with a `RunSQL` migration, benchmark three ID
schemes at 50 million rows, prove the index-order rule with `EXPLAIN`, measure
`OFFSET` versus keyset at depth, pit the Django ORM against raw `cursor` /
`bulk_create` / `COPY` at full write rate, and end with the capacity projection
that drives the rest of Phase 3.

⏱️ ~100 min. Work in `apps/pulse` (the Django project you have grown since
Module 04).

```bash
docker compose -f ../../infra/compose.dev.yml up -d
alias pg='docker exec -i pulse-postgres psql -U pulse -d pulse'
```

> **Low-memory path:** use `5_000_000` rows instead of `50_000_000` throughout.
> Every ratio below holds; only the absolute times shrink.

> **Why so much raw SQL in a Django lab?** Because the schema decisions here —
> partial indexes, `ON CONFLICT`, the exact index column order — are things the
> ORM either can't express or hides from you, and at ten billion rows you must
> see the DDL you are actually running. You will drive most of it through
> `migrations.RunSQL`, which is the idiomatic Django way to ship SQL the ORM
> can't generate. Modules 13 and 14 lean on `RunSQL` even harder.

---

## Part A — The schema, as a migration

Django's `RunSQL` operation lets a migration carry hand-written SQL, forwards and
backwards. Create `chat/migrations/0004_message_store.py`:

```python
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [("chat", "0003_sequences")]   # whatever Module 10 left

    operations = [
        migrations.RunSQL(
            sql=r"""
            -- Rebuild messages with the full production shape.
            DROP TABLE IF EXISTS messages CASCADE;

            CREATE TABLE messages (
                id         bigint      NOT NULL,   -- Snowflake: sortable, coordination-free
                room_id    text        NOT NULL,
                seq        bigint      NOT NULL,   -- per-room, the client's resume cursor
                sender     text        NOT NULL,
                client_id  text        NOT NULL,   -- idempotency key (Module 05)
                body       text        NOT NULL,
                reply_to   bigint,
                created_at timestamptz NOT NULL DEFAULT now(),
                edited_at  timestamptz,
                deleted_at timestamptz,

                -- (room_id, seq) as PK: the resume query is a primary-key range
                -- scan, and it enforces per-room sequence uniqueness for free.
                PRIMARY KEY (room_id, seq)
            );

            -- 1. Scrollback. Equality column FIRST, range/sort column second.
            --    Partial: deleted messages are never scrolled to, so don't index them.
            CREATE INDEX idx_messages_scrollback
                ON messages (room_id, id DESC)
                WHERE deleted_at IS NULL;

            -- 2. Idempotency. THE guarantee behind Module 05's retry safety.
            CREATE UNIQUE INDEX idx_messages_dedup
                ON messages (room_id, client_id);

            -- 3. Threads. Partial, because most messages are not replies.
            CREATE INDEX idx_messages_thread
                ON messages (reply_to, id)
                WHERE reply_to IS NOT NULL;

            COMMENT ON TABLE messages IS
              'One row per message (fan-out on read). Per-user views derive from
               (room_id, seq) plus read_cursors.last_read_seq.';
            """,
            reverse_sql="DROP TABLE IF EXISTS messages CASCADE;",
        ),
    ]
```

The matching Django model is `managed = False` — the migration owns the DDL, and
the model exists only so the ORM can *read* the table where the object graph is
worth it (never on the write hot path). `chat/models.py`:

```python
class Message(models.Model):
    id = models.BigIntegerField(primary_key=True)   # Snowflake, assigned in code
    room_id = models.TextField()
    seq = models.BigIntegerField()
    sender = models.TextField()
    client_id = models.TextField()
    body = models.TextField()
    reply_to = models.BigIntegerField(null=True)
    created_at = models.DateTimeField()
    edited_at = models.DateTimeField(null=True)
    deleted_at = models.DateTimeField(null=True)

    class Meta:
        db_table = "messages"
        managed = False        # the RunSQL migration owns this table
```

> **Why `managed = False`?** The real primary key is the composite
> `(room_id, seq)`, and Django 5.1's ORM cannot express a composite primary key
> (that lands in 5.2 as `CompositePrimaryKey`). Rather than fight it, we let SQL
> own the table and tell Django not to manage or migrate it. The ORM still reads
> it fine — `Message.objects.filter(room_id=...)` works — it just treats `id` as
> the pk for its own bookkeeping. This is a normal, honest pattern for tables
> whose shape outgrows the ORM.

```bash
python manage.py migrate chat
pg -c "\d messages"
```
**Expected:**
```
                            Table "public.messages"
   Column   |           Type           | Nullable |      Default
------------+--------------------------+----------+-------------------
 id         | bigint                   | not null |
 room_id    | text                     | not null |
 seq        | bigint                   | not null |
 ...
Indexes:
    "messages_pkey" PRIMARY KEY, btree (room_id, seq)
    "idx_messages_dedup" UNIQUE, btree (room_id, client_id)
    "idx_messages_scrollback" btree (room_id, id DESC) WHERE deleted_at IS NULL
    "idx_messages_thread" btree (reply_to, id) WHERE reply_to IS NOT NULL
```

Note there is **no index on `created_at`** and none on `sender`. Neither serves a
hot-path query, so neither exists. Module 13 partitions *on* `created_at`, which
gives you time-range pruning without paying for an index.

---

## Part B — Benchmark the three ID schemes

This is a pure-database benchmark — the ID's cost is in the B-tree, not in
Python — so we drive it straight from `psql`. `code/id_bench.sql`:

```sql
-- Three tables, identical except for the ID type.
CREATE TABLE bench_snowflake (id bigint PRIMARY KEY, room_id text, body text);
CREATE TABLE bench_uuidv7    (id uuid   PRIMARY KEY, room_id text, body text);
CREATE TABLE bench_uuidv4    (id uuid   PRIMARY KEY, room_id text, body text);

-- UUIDv7: 48-bit unix-ms prefix, then random. Postgres 18 ships uuidv7();
-- this shim works on 16+.
CREATE OR REPLACE FUNCTION uuid_v7() RETURNS uuid AS $$
  SELECT encode(
    set_bit(set_bit(
      overlay('\x00000000000000000000000000000000'::bytea
              PLACING substring(int8send((extract(epoch from clock_timestamp())*1000)::bigint)
                                from 3 for 6)
              FROM 1 FOR 6)
      || gen_random_bytes(10),
    52, 1), 53, 1), 'hex')::uuid;
$$ LANGUAGE sql VOLATILE;
```

```bash
pg -f code/id_bench.sql
```

Now insert 50 million rows into each, in batches, measuring rate, index size, and
WAL as you go. `code/id_bench.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail
ROWS=${1:-50000000}
BATCH=500000

bench() {
  local table="$1" idexpr="$2"
  local start; start=$(date +%s.%N)
  local wal_start; wal_start=$(docker exec pulse-postgres psql -U pulse -d pulse -tAc \
      "SELECT pg_current_wal_lsn() - '0/0'::pg_lsn")

  for ((i=0; i<ROWS; i+=BATCH)); do
    docker exec -i pulse-postgres psql -U pulse -d pulse -q -c "
      INSERT INTO $table (id, room_id, body)
      SELECT $idexpr, 'room.' || (random()*1000)::int, repeat('x', 120)
      FROM generate_series(1, $BATCH);" > /dev/null
  done

  local end; end=$(date +%s.%N)
  local wal_end; wal_end=$(docker exec pulse-postgres psql -U pulse -d pulse -tAc \
      "SELECT pg_current_wal_lsn() - '0/0'::pg_lsn")
  local secs; secs=$(echo "$end - $start" | bc)

  printf "%-18s %8.0f rows/s  index=%-8s table=%-8s wal/row=%dB\n" \
    "$table" "$(echo "$ROWS / $secs" | bc -l)" \
    "$(docker exec pulse-postgres psql -U pulse -d pulse -tAc \
        "SELECT pg_size_pretty(pg_relation_size('${table}_pkey'))")" \
    "$(docker exec pulse-postgres psql -U pulse -d pulse -tAc \
        "SELECT pg_size_pretty(pg_relation_size('$table'))")" \
    "$(( (wal_end - wal_start) / ROWS ))"
}

bench bench_snowflake "(extract(epoch from clock_timestamp())*1000)::bigint << 22 | (row_number() over ())::bigint"
bench bench_uuidv7    "uuid_v7()"
bench bench_uuidv4    "gen_random_uuid()"
```

```bash
chmod +x code/id_bench.sh
./code/id_bench.sh 50000000
```

**Expected:**
```
bench_snowflake      41219 rows/s  index=1071 MB table=7891 MB wal/row=220B
bench_uuidv7         38904 rows/s  index=2104 MB table=9112 MB wal/row=261B
bench_uuidv4          6118 rows/s  index=3822 MB table=9384 MB wal/row=891B
```

✅ **UUIDv4 is 6.7× slower with a 3.6× larger index.**

See exactly *why* with `pgstatindex`:

```bash
pg -c "
CREATE EXTENSION IF NOT EXISTS pgstattuple;
SELECT 'snowflake' AS scheme, * FROM pgstatindex('bench_snowflake_pkey')
UNION ALL SELECT 'uuidv7', * FROM pgstatindex('bench_uuidv7_pkey')
UNION ALL SELECT 'uuidv4', * FROM pgstatindex('bench_uuidv4_pkey');" \
  | cut -c1-120
```
**Expected:**
```
  scheme   | version | tree_level | index_size | ... | avg_leaf_density | leaf_fragmentation
-----------+---------+------------+------------+-----+------------------+--------------------
 snowflake |       4 |          3 | 1123287040 | ... |            89.94 |               0.00
 uuidv7    |       4 |          3 | 2206203904 | ... |            88.12 |               0.31
 uuidv4    |       4 |          4 | 4008706048 | ... |            60.18 |              48.72
```

✅ **`avg_leaf_density` 90% vs 60%, `leaf_fragmentation` 0% vs 49%.**

Sequential keys always append to the rightmost page, which fills to ~90% before
splitting. Random keys split pages in the middle, leaving both halves half-empty
— and every insert dirties a random page, which is where the 891 bytes of WAL per
row come from (a full-page write). The extra tree level on UUIDv4 (4 vs 3) means
every lookup costs an extra page read too, forever.

Record it in your running results file:
```markdown
## Module 12 — ID schemes (50M rows)

| Scheme    | Inserts/s | Index  | WAL/row | Leaf density | Fragmentation |
|-----------|-----------|--------|---------|--------------|---------------|
| Snowflake |    41,219 | 1.1 GB |   220 B |        90%   |          0%   |
| UUIDv7    |    38,904 | 2.1 GB |   261 B |        88%   |        0.3%   |
| UUIDv4    |     6,118 | 3.8 GB |   891 B |        60%   |         49%   |
```

> **The Python Snowflake** you use in the real send path is in
> [`code/snowflake.py`](./code/snowflake.py) — 41 bits of ms since a custom
> epoch, 10 bits of worker id (from an env var per process), 12 bits of per-ms
> sequence. Ten lines that make Module 14's sharding possible.

---

## Part C — Prove the index-order rule

Load 50 million realistic messages (Snowflake IDs, `seq` monotonic per room):

```bash
pg -c "
INSERT INTO messages (id, room_id, seq, sender, client_id, body)
SELECT
  (1704067200000 + g)::bigint << 22 | (g % 4096),
  'room.' || (g % 1000),
  (g / 1000) + 1,
  'user.' || (g % 5000),
  'c-' || g,
  repeat('m', 80)
FROM generate_series(1, 50000000) g;
ANALYZE messages;"
```

The right index (`room_id` first):

```bash
pg -c "EXPLAIN (ANALYZE, BUFFERS)
SELECT id, sender, body, seq FROM messages
WHERE room_id = 'room.42' AND id < 7241938472948572160 AND deleted_at IS NULL
ORDER BY id DESC LIMIT 50;"
```
**Expected:**
```
 Limit  (cost=0.56..38.21 rows=50 width=118) (actual time=0.041..0.089 rows=50 loops=1)
   Buffers: shared hit=54
   ->  Index Scan using idx_messages_scrollback on messages
         (cost=0.56..37642.11 rows=49982 width=118) (actual time=0.039..0.081 rows=50 loops=1)
         Index Cond: ((room_id = 'room.42'::text) AND (id < 7241938472948572160::bigint))
         Buffers: shared hit=54
 Planning Time: 0.184 ms
 Execution Time: 0.118 ms
```

✅ **54 buffers, 0.118 ms.** No `Sort` node — the index is already in `id DESC`
order, so `ORDER BY` is free. No `Rows Removed by Filter`.

Now build the *wrong* index and force it:

```bash
pg -c "CREATE INDEX idx_wrong ON messages (id, room_id);"
pg -c "
BEGIN;
DROP INDEX idx_messages_scrollback;
EXPLAIN (ANALYZE, BUFFERS)
SELECT id, sender, body, seq FROM messages
WHERE room_id = 'room.42' AND id < 7241938472948572160 AND deleted_at IS NULL
ORDER BY id DESC LIMIT 50;
ROLLBACK;"
```
**Expected:**
```
 Limit  (cost=0.56..1284.02 rows=50 width=118) (actual time=0.048..184.221 rows=50 loops=1)
   Buffers: shared hit=48213 read=1204
   ->  Index Scan Backward using idx_wrong on messages
         Index Cond: (id < 7241938472948572160::bigint)
         Filter: ((deleted_at IS NULL) AND (room_id = 'room.42'::text))
         Rows Removed by Filter: 49950
         Buffers: shared hit=48213 read=1204
 Execution Time: 184.302 ms
```

✅ **`Rows Removed by Filter: 49,950`** and **184 ms instead of 0.118 ms —
1,560× slower.** The index got to the right `id` range, then read and discarded
49,950 rows from *other* rooms to find 50 from `room.42`. That is the rule made
concrete: **equality first, then range.**

```bash
pg -c "DROP INDEX idx_wrong;"
```

> **In Django ORM terms:** the query above is
> `Message.objects.filter(room_id="room.42", id__lt=cursor, deleted_at__isnull=True).order_by("-id")[:50]`.
> The ORM generates exactly this SQL — but *only your index definition* decides
> whether it is 0.118 ms or 184 ms. The ORM will happily emit a fast query that
> runs slowly against the wrong index, with no warning. `EXPLAIN` is not
> optional.

---

## Part D — OFFSET versus keyset, at depth

`code/pagination_bench.sh`:
```bash
#!/usr/bin/env bash
for page in 1 100 1000 10000 100000; do
  offset=$(( (page - 1) * 50 ))
  o=$(docker exec -i pulse-postgres psql -U pulse -d pulse -tAc "
    EXPLAIN (ANALYZE, FORMAT JSON)
    SELECT id FROM messages WHERE room_id='room.42' AND deleted_at IS NULL
    ORDER BY id DESC LIMIT 50 OFFSET $offset;" | jq -r '.[0]."Execution Time"')

  cursor=$(docker exec -i pulse-postgres psql -U pulse -d pulse -tAc "
    SELECT id FROM messages WHERE room_id='room.42' AND deleted_at IS NULL
    ORDER BY id DESC LIMIT 1 OFFSET $offset;")

  k=$(docker exec -i pulse-postgres psql -U pulse -d pulse -tAc "
    EXPLAIN (ANALYZE, FORMAT JSON)
    SELECT id FROM messages WHERE room_id='room.42' AND id < $cursor AND deleted_at IS NULL
    ORDER BY id DESC LIMIT 50;" | jq -r '.[0]."Execution Time"')

  printf "page %-7s OFFSET %8.2f ms   keyset %6.2f ms\n" "$page" "$o" "$k"
done
```

```bash
chmod +x code/pagination_bench.sh && ./code/pagination_bench.sh
```

**Expected:**
```
page 1       OFFSET     0.89 ms   keyset   0.82 ms
page 100     OFFSET     4.12 ms   keyset   0.81 ms
page 1000    OFFSET    31.40 ms   keyset   0.83 ms
page 10000   OFFSET   284.19 ms   keyset   0.80 ms
page 100000  OFFSET  2841.02 ms   keyset   0.79 ms
```

✅ **Keyset is flat. OFFSET is linear.** At page 100,000 it is **3,596× slower.**

See it in the plan:
```bash
pg -c "EXPLAIN (ANALYZE) SELECT id FROM messages
WHERE room_id='room.42' AND deleted_at IS NULL ORDER BY id DESC LIMIT 50 OFFSET 100000;"
```
```
 Limit  (actual time=2839.102..2841.021 rows=50 loops=1)
   ->  Index Scan Backward using idx_messages_scrollback on messages
         (actual time=0.038..2836.882 rows=100050 loops=1)
```
**`rows=100050`** — it produced 100,050 rows to return 50.

### The DRF trap

Django's default DRF pagination is `OFFSET`-backed:

```python
# settings.py — the innocent-looking default that degrades with depth
REST_FRAMEWORK = {"DEFAULT_PAGINATION_CLASS":
                  "rest_framework.pagination.PageNumberPagination"}
```

`?page=2000` becomes `... LIMIT 50 OFFSET 100000` — the 2,841 ms query above. The
fix is one line, and it is keyset under the hood:

```python
class MessageCursorPagination(CursorPagination):
    page_size = 50
    ordering = "-id"           # must match the index; keyset needs a stable sort
```

DRF's `CursorPagination` emits `WHERE id < :cursor ORDER BY id DESC LIMIT 50` and
returns an opaque `next` cursor — the same resume-from-cursor your WebSocket
protocol already speaks (Module 10). Use it for every list endpoint that can go
deep.

### The correctness bug

`OFFSET` is not just slow at depth — it is *wrong* when rows arrive mid-scroll:

```bash
pg -c "
BEGIN;
SELECT id FROM messages WHERE room_id='room.99' ORDER BY id DESC LIMIT 3 OFFSET 0;
INSERT INTO messages (id, room_id, seq, sender, client_id, body)
VALUES (9999999999999999, 'room.99', 999999, 'x', 'c-x', 'new arrival');
SELECT id FROM messages WHERE room_id='room.99' ORDER BY id DESC LIMIT 3 OFFSET 3;
COMMIT;"
```
**Expected — the last row of page 1 reappears as the first row of page 2:**
```
        id
------------------
 7241938472948575
 7241938472948574
 7241938472948573      <-- last row of page 1
...
        id
------------------
 7241938472948573      <-- SAME ROW, duplicated
 7241938472948572
 7241938472948571
```

✅ A new row shifted everything by one, so `OFFSET 3` now points at a row the user
already saw. In chat, where new messages arrive *constantly*, this is not an edge
case — it is the normal case. Keyset cannot do this: the cursor **names a row**,
not a position.

---

## Part E — Django ORM versus raw SQL, at write rate

Now the runtime *does* matter. `code/write_bench.py` (run with
`python manage.py shell < code/write_bench.py`, or as a management command):

```python
import time, os
from itertools import count
from django.db import connection, reset_queries
from chat.models import Message
from chat.snowflake import Snowflake
from psycopg import sql

N = 200_000
ids = Snowflake(worker_id=int(os.getenv("PULSE_WORKER_ID", "1")))


def report(label, t0, n=N):
    dt = time.perf_counter() - t0
    print(f"{label:<34} {n:>8,} rows in {dt*1000:>8,.0f} ms = {n/dt:>10,.0f} rows/s")


def orm_create():
    t0 = time.perf_counter()
    for i in range(N):
        Message.objects.create(
            id=ids.next_id(), room_id="room.1", seq=i, sender="alice",
            client_id=f"c-orm-{i}", body="body")
    report("ORM Message.objects.create()", t0)


def raw_single():
    t0 = time.perf_counter()
    with connection.cursor() as cur:
        for i in range(N):
            cur.execute(
                """INSERT INTO messages (id, room_id, seq, sender, client_id, body)
                   VALUES (%s,%s,%s,%s,%s,%s)
                   ON CONFLICT (room_id, client_id) DO NOTHING""",
                [ids.next_id(), "room.1", i, "alice", f"c-raw-{i}", "body"])
    report("raw cursor.execute (single)", t0)


def orm_bulk_create():
    t0 = time.perf_counter()
    objs = (Message(id=ids.next_id(), room_id="room.1", seq=i, sender="alice",
                    client_id=f"c-bulk-{i}", body="body") for i in range(N))
    Message.objects.bulk_create(objs, batch_size=500)
    report("ORM bulk_create(batch_size=500)", t0)


def raw_execute_values():
    from psycopg.extras import execute_values  # psycopg2 name; psycopg3: use executemany
    t0 = time.perf_counter()
    rows = [(ids.next_id(), "room.1", i, "alice", f"c-ev-{i}", "body") for i in range(N)]
    with connection.cursor() as cur:
        cur.executemany(
            """INSERT INTO messages (id, room_id, seq, sender, client_id, body)
               VALUES (%s,%s,%s,%s,%s,%s)""", rows)
    report("raw executemany (batch 500)", t0)


def copy_in():                                  # the nuclear option
    t0 = time.perf_counter()
    with connection.cursor() as cur:
        with cur.copy("COPY messages (id, room_id, seq, sender, client_id, body) "
                      "FROM STDIN") as cp:
            for i in range(N):
                cp.write_row([ids.next_id(), "room.1", i, "alice", f"c-copy-{i}", "body"])
    report("COPY (cursor.copy)", t0)


for fn in (orm_create, raw_single, orm_bulk_create, raw_execute_values, copy_in):
    with connection.cursor() as c:
        c.execute("TRUNCATE messages")
    fn()
```

```bash
python manage.py shell < code/write_bench.py
```

**Expected:**
```
ORM Message.objects.create()      200,000 rows in 25,641 ms =      7,800 rows/s
raw cursor.execute (single)       200,000 rows in  4,854 ms =     41,203 rows/s
ORM bulk_create(batch_size=500)   200,000 rows in  1,190 ms =    168,067 rows/s
raw executemany (batch 500)       200,000 rows in    893 ms =    223,964 rows/s
COPY (cursor.copy)                200,000 rows in    204 ms =    980,392 rows/s
```

✅ **Raw single is 5.3× faster than the ORM's `create()`; batching is another
5.4×.**

Where the ORM's time goes — turn on query timing and watch:

```python
from django.test.utils import CaptureQueriesContext
from django.db import connection
with CaptureQueriesContext(connection) as ctx:
    Message.objects.create(id=ids.next_id(), room_id="room.1", seq=0,
                           sender="alice", client_id="c-x", body="body")
print(len(ctx.captured_queries), "queries; sql:", ctx.captured_queries[0]["sql"][:80])
```
```
1 queries; sql: INSERT INTO "messages" ("id", "room_id", "seq", "sender", "client_id"...
```

One query — so the cost is *not* extra round trips. It is the Python around the
query: building a `Message` instance (ten field descriptors), running `save()`'s
`pre_save`/`post_save` signal dispatch, the `update_fields` bookkeeping, and a
trip through the SQL compiler *per row*. `bulk_create` skips signals and the
per-row compile, which is why it is 21× faster than `create()` while still
building model instances. `executemany` and `COPY` skip the instances entirely.

> The ORM's `create()` (7,800/s) is a touch slower than the JVM twin's JPA
> (8,400/s). Same lesson, and the same **runtime tax** you measured in Module 06:
> Python's per-operation overhead is higher. It does not change *what* you do —
> it makes doing it correctly matter slightly more.

### Which to use where

| Path | Choice | Rate |
|------|--------|------|
| Single message send | **raw `cursor.execute` + `ON CONFLICT RETURNING`** | 41k/s — 4× the 10k/s target |
| Outbox relay (Module 13) | **`executemany` batch 500** | 224k/s |
| Bulk import / backfill | **`COPY`** | 980k/s |
| Room / user / membership CRUD | **Django ORM** | rate is irrelevant; the graph earns it |

The single-send path stays **unbatched deliberately**: batching means *waiting*
for a batch to fill, which adds latency to an interactive send. 41k/s is 4× the
target, so we spend the headroom on latency, not throughput. That is a choice, and
it is the right one for a human waiting on their own message to appear.

---

## Part F — Watch a query cross the slow-query line

Module 00 set `log_min_duration_statement=200`. Cash it in with the search query
people reach for first:

```bash
pg -c "SELECT count(*) FROM messages WHERE body LIKE '%needle%';"
docker compose -f ../../infra/compose.dev.yml logs postgres | tail -3
```
**Expected:**
```
LOG:  duration: 41821.402 ms  statement: SELECT count(*) FROM messages WHERE body LIKE '%needle%';
```

**41 seconds.** A leading-wildcard `LIKE` cannot use a B-tree — it is a sequential
scan over 50 million rows. This is why Module 12 has **no full-text search**.

The `tsvector` + GIN option, and what it costs:

```bash
pg -c "
ALTER TABLE messages ADD COLUMN body_tsv tsvector
  GENERATED ALWAYS AS (to_tsvector('english', body)) STORED;
CREATE INDEX idx_messages_fts ON messages USING GIN (body_tsv);"

pg -c "EXPLAIN (ANALYZE) SELECT id FROM messages
WHERE body_tsv @@ to_tsquery('english', 'needle') LIMIT 20;"
```
**Expected:**
```
 Limit  (actual time=18.204..18.291 rows=20 loops=1)
   ->  Bitmap Heap Scan on messages (actual time=18.201..18.284 rows=20 loops=1)
         ->  Bitmap Index Scan on idx_messages_fts (actual time=14.102..14.102 rows=1841 loops=1)
 Execution Time: 18.402 ms
```

2,270× faster — but measure the cost:
```bash
pg -c "SELECT pg_size_pretty(pg_relation_size('idx_messages_fts'));"
```
```
 4218 MB
```

✅ **A 4.2 GB index and a write-time tokenization cost on every insert.** Re-run
the batch write benchmark with it in place:
```
raw executemany (batch 500) with FTS index:  91,204 rows/s   (was 223,964)
```

**59% slower writes** to serve a query nobody runs in the hot path.

> **The decision for Pulse: no FTS in Postgres.** Search goes to
> Elasticsearch/OpenSearch, fed from the outbox (Module 13). The write path stays
> fast; search gets a system designed for it. Below ~5 million messages,
> `tsvector` + GIN is genuinely fine and saves you a whole component — know which
> side of that line you are on. Django's `SearchVectorField` +
> `GinIndex` express exactly this schema if you choose it.

```bash
pg -c "DROP INDEX idx_messages_fts; ALTER TABLE messages DROP COLUMN body_tsv;"
```

---

## Part G — Size it, and meet the 74 TB number

```bash
pg -c "
SELECT
  pg_size_pretty(pg_total_relation_size('messages'))  AS total,
  pg_size_pretty(pg_relation_size('messages'))        AS heap,
  pg_size_pretty(pg_indexes_size('messages'))         AS indexes,
  count(*)                                            AS rows,
  pg_total_relation_size('messages') / count(*)       AS bytes_per_row
FROM messages;"
```
**Expected:**
```
  total   |  heap   | indexes  |   rows   | bytes_per_row
----------+---------+----------+----------+---------------
 11 GB    | 7891 MB | 3204 MB  | 50000000 |           236
```

**236 bytes per row** for an 80-byte body. Where it goes:

| Component | Bytes |
|-----------|-------|
| Tuple header (`HeapTupleHeader`) | 23 |
| Null bitmap + alignment padding | 8 |
| `id`, `seq`, `reply_to` (3 × bigint) | 24 |
| `room_id`, `sender`, `client_id` (varlena) | ~40 |
| `body` | 84 |
| Timestamps (3 × 8) | 24 |
| Item pointer in the page | 4 |
| **Indexes** (3 of them) | **~64** |

Project it at Pulse's target rate:

```
10,000 messages/sec x 86,400 = 864M rows/day
864,000,000 x 236 bytes      = 204 GB/day
                              = 74 TB/year
```

✅ **74 TB per year, on one table, on one machine.** That number is the whole
reason [Module 13](../13-partitioning-replication-pooling/) partitions (so you
can drop old data instantly instead of a multi-hour `DELETE`) and
[Module 14](../14-sharding-and-wide-column/) shards (so it is not one machine).
Keep this figure; the next two modules cash it in and the capstone's cost model
starts from it.

Record it:
```markdown
## Module 12 — Message store

- Index order: (room_id, id) 0.118ms vs (id, room_id) 184ms  (1,560x)
- Keyset vs OFFSET at page 100,000: 0.79ms vs 2,841ms  (3,596x)
- OFFSET also duplicates rows when data is inserted mid-pagination
- Write rates: ORM create 7.8k/s | raw single 41k/s | bulk_create 168k/s
               | executemany 224k/s | COPY 980k/s
- FTS GIN index: 4.2GB and -59% write throughput  -> search goes elsewhere
- 236 bytes/row -> 204 GB/day at 10k msg/s -> 74 TB/year
```

---

## What you built

- A three-index schema, shipped as a `RunSQL` migration, where every index serves
  a hot-path query — with partial indexes for soft-delete and threads, and a
  `managed = False` model that reads the table without fighting the composite PK.
- **Measured** proof that UUIDv4 costs 6.7× write throughput and 3.6× index size,
  with `pgstatindex` showing exactly why (60% leaf density, 49% fragmentation).
- `EXPLAIN` proof of the equality-then-range rule: 1,560× difference.
- Keyset pagination that is flat at any depth, the DRF `CursorPagination` that
  ships it, and the `OFFSET` duplication bug.
- A write-path benchmark that justifies raw `cursor` for the message hot path and
  the ORM for everything else — and shows the Python runtime tax one more time.
- The capacity projection — **74 TB/year** — that Modules 13 and 14 exist to
  solve.

Now do [`challenge.md`](./challenge.md).

Then: [Module 13 — Partitioning, Replication & Pooling](../13-partitioning-replication-pooling/).
