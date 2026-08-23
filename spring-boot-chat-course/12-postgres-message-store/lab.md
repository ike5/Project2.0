# Lab 12 — Build a Store That Survives Ten Billion Rows

**You'll:** build the schema, benchmark three ID schemes at 50 million rows,
prove the index-order rule with `EXPLAIN`, measure OFFSET versus keyset at depth,
and compare JPA against `JdbcClient` at full write rate.

⏱️ ~100 min. Work in `spring-boot-chat-course/apps/pulse`.

```bash
docker compose -f ../../infra/compose.dev.yml up -d
alias pg='docker exec -i pulse-postgres psql -U pulse -d pulse'
```

> **Low-memory path:** use 5,000,000 rows instead of 50,000,000 throughout.
> Every ratio below holds; only the absolute times shrink.

---

## Part A — The schema

`src/main/resources/db/migration/V4__message_store.sql`:

```sql
-- Rebuild messages with the full production shape.
DROP TABLE IF EXISTS messages CASCADE;

CREATE TABLE messages (
    id         bigint      NOT NULL,          -- Snowflake: time-sortable, coordination-free
    room_id    text        NOT NULL,
    seq        bigint      NOT NULL,          -- per-room, the client's resume cursor
    sender     text        NOT NULL,
    client_id  text        NOT NULL,          -- idempotency key
    body       text        NOT NULL,
    reply_to   bigint,
    created_at timestamptz NOT NULL DEFAULT now(),
    edited_at  timestamptz,
    deleted_at timestamptz,

    -- (room_id, seq) as PK: the resume query is a primary-key range scan,
    -- and it enforces per-room sequence uniqueness for free.
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
```

Note there is **no index on `created_at`** and none on `sender`. Neither serves a
hot-path query, so neither exists. Module 13 adds partitioning *on* `created_at`,
which gives you time-range pruning without an index.

```bash
./mvnw spring-boot:run
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

---

## Part B — Benchmark the three ID schemes

`code/id_bench.sql`:

```sql
-- Three tables, identical except for the ID type.
CREATE TABLE bench_snowflake (id bigint PRIMARY KEY, room_id text, body text);
CREATE TABLE bench_uuidv7    (id uuid   PRIMARY KEY, room_id text, body text);
CREATE TABLE bench_uuidv4    (id uuid   PRIMARY KEY, room_id text, body text);

-- UUIDv7: 48-bit unix-ms prefix, then random. Postgres 18 has uuidv7();
-- this works on 16+.
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

Now insert 50 million rows into each, in batches, measuring as you go:

`code/id_bench.sh`:
```bash
#!/usr/bin/env bash
set -euo pipefail
ROWS=${1:-50000000}
BATCH=500000

bench() {
  local table="$1" idexpr="$2"
  local start=$(date +%s.%N)
  local wal_start=$(docker exec pulse-postgres psql -U pulse -d pulse -tAc \
      "SELECT pg_current_wal_lsn() - '0/0'::pg_lsn")

  for ((i=0; i<ROWS; i+=BATCH)); do
    docker exec -i pulse-postgres psql -U pulse -d pulse -q -c "
      INSERT INTO $table (id, room_id, body)
      SELECT $idexpr, 'room.' || (random()*1000)::int, repeat('x', 120)
      FROM generate_series(1, $BATCH);" > /dev/null
  done

  local end=$(date +%s.%N)
  local wal_end=$(docker exec pulse-postgres psql -U pulse -d pulse -tAc \
      "SELECT pg_current_wal_lsn() - '0/0'::pg_lsn")
  local secs=$(echo "$end - $start" | bc)

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

See exactly why:

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
— and every insert dirties a random page, which is where the 891 bytes of WAL
per row comes from (a full-page write, because the page wasn't already dirty in
this checkpoint cycle).

The extra tree level on UUIDv4 (4 vs 3) means every lookup costs an extra page
read too.

Record it:
```markdown
## Module 12 — ID schemes (50M rows)

| Scheme    | Inserts/s | Index  | WAL/row | Leaf density | Fragmentation |
|-----------|-----------|--------|---------|--------------|---------------|
| Snowflake |    41,219 | 1.1 GB |   220 B |        90%   |          0%   |
| UUIDv7    |    38,904 | 2.1 GB |   261 B |        88%   |        0.3%   |
| UUIDv4    |     6,118 | 3.8 GB |   891 B |        60%   |         49%   |
```

---

## Part C — Prove the index-order rule

Load 50 million realistic messages:

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

Now the right index:

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

✅ **54 buffers, 0.118 ms.** Note: no `Sort` node — the index is already in
`id DESC` order, so `ORDER BY` is free. And no `Rows Removed by Filter`.

Now build the wrong index and force it:

```bash
pg -c "CREATE INDEX idx_wrong ON messages (id, room_id);"
pg -c "
SET enable_indexscan = on;
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

✅ **`Rows Removed by Filter: 49,950`** and **184 ms instead of 0.118 ms — 1,560×
slower.** The index got it to the right ID range, then it had to read and discard
49,950 rows from other rooms to find 50 from room.42.

That's the rule made concrete: **equality first, then range.**

```bash
pg -c "DROP INDEX idx_wrong;"
```

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

✅ **Keyset is flat. OFFSET is linear.** At page 100,000 it's **3,596× slower**.

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
**`rows=100050`** — it read 100,050 rows to return 50.

### The correctness bug

```bash
pg -c "
BEGIN;
SELECT id FROM messages WHERE room_id='room.99' ORDER BY id DESC LIMIT 3 OFFSET 0;
INSERT INTO messages (id, room_id, seq, sender, client_id, body)
VALUES (9999999999999999, 'room.99', 999999, 'x', 'c-x', 'new arrival');
SELECT id FROM messages WHERE room_id='room.99' ORDER BY id DESC LIMIT 3 OFFSET 3;
COMMIT;"
```
**Expected — the third row of page 1 reappears as the first row of page 2:**
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

✅ A new row shifted everything by one, so `OFFSET 3` now points at a row the
user already saw. Keyset cannot do this — the cursor **names a row**, not a
position.

---

## Part E — JPA versus JdbcClient

`src/test/java/com/pulse/store/WriteBench.java`:

```java
@SpringBootTest
class WriteBench {

    @Autowired MessageJpaRepository jpa;
    @Autowired JdbcClient jdbc;
    @Autowired EntityManager em;

    private static final int N = 200_000;

    @Test
    void jpaInserts() {
        long t0 = System.nanoTime();
        for (int i = 0; i < N; i++) {
            jpa.save(new MessageEntity(id(i), "room.1", i, "alice", "c-jpa-" + i, "body"));
            if (i % 50 == 0) { em.flush(); em.clear(); }   // or the heap dies
        }
        report("JPA (batch 50)", t0);
    }

    @Test
    void jdbcClientInserts() {
        long t0 = System.nanoTime();
        for (int i = 0; i < N; i++) {
            jdbc.sql("""
                    INSERT INTO messages (id, room_id, seq, sender, client_id, body)
                    VALUES (?,?,?,?,?,?)""")
                .params(id(i), "room.1", (long) i, "alice", "c-jdbc-" + i, "body")
                .update();
        }
        report("JdbcClient (single)", t0);
    }

    @Test
    void jdbcBatched() {
        long t0 = System.nanoTime();
        jdbc.getJdbcTemplate().batchUpdate(
            "INSERT INTO messages (id, room_id, seq, sender, client_id, body) VALUES (?,?,?,?,?,?)",
            IntStream.range(0, N).boxed().toList(), 500,
            (ps, i) -> { ps.setLong(1, id(i)); ps.setString(2, "room.1");
                         ps.setLong(3, i); ps.setString(4, "alice");
                         ps.setString(5, "c-batch-" + i); ps.setString(6, "body"); });
        report("JdbcClient (batch 500)", t0);
    }

    @Test
    void copyIn() throws Exception {                 // the nuclear option
        long t0 = System.nanoTime();
        var conn = dataSource.getConnection().unwrap(PGConnection.class);
        var copy = new CopyManager((BaseConnection) conn);
        var sb = new StringBuilder();
        for (int i = 0; i < N; i++)
            sb.append(id(i)).append('\t').append("room.1").append('\t').append(i)
              .append('\t').append("alice").append('\t').append("c-copy-").append(i)
              .append('\t').append("body").append('\n');
        copy.copyIn("COPY messages (id, room_id, seq, sender, client_id, body) FROM STDIN",
                    new StringReader(sb.toString()));
        report("COPY", t0);
    }
}
```

Enable JDBC batching in `application.yml`:
```yaml
spring:
  datasource:
    url: jdbc:postgresql://localhost:5432/pulse?reWriteBatchedInserts=true
  jpa:
    properties:
      hibernate.jdbc.batch_size: 50
      hibernate.order_inserts: true
```

```bash
./mvnw test -Dtest=WriteBench
```

**Expected:**
```
JPA (batch 50)              200,000 rows in 23,812 ms   =    8,400 rows/s
JdbcClient (single)         200,000 rows in  4,854 ms   =   41,203 rows/s
JdbcClient (batch 500)      200,000 rows in    891 ms   =  224,467 rows/s
COPY                        200,000 rows in    204 ms   =  980,392 rows/s
```

✅ **JdbcClient is 4.9× faster than JPA; batching is another 5.4×.**

Where JPA's time goes:
```bash
./mvnw test -Dtest=WriteBench#jpaInserts -Dspring.jpa.properties.hibernate.generate_statistics=true
```
```
Session Metrics {
    412831 nanoseconds spent acquiring 1 JDBC connections;
    18294012841 nanoseconds spent preparing 4000 JDBC statements;
    3812004821 nanoseconds spent performing 200000 L2C puts;
    1284993021 nanoseconds spent executing 4000 flushes (flushing 200000 entities);
}
```

**1.28 seconds of dirty checking** on entities that were just created and never
modified, plus second-level-cache puts for data nobody will read from cache.

### Which to use where

| Path | Choice | Rate |
|------|--------|------|
| Single message send | **JdbcClient single** | 41k/s — far above the 10k/s target |
| Outbox relay (Module 13) | **JdbcClient batch 500** | 224k/s |
| Bulk import / backfill | **COPY** | 980k/s |
| Room / user / membership CRUD | **JPA** | rate is irrelevant; the graph earns it |

> The single-insert path stays unbatched deliberately: batching means *waiting*
> for a batch to fill, which adds latency to the send path. 41k/s is 4× the
> target, so we spend the headroom on latency instead of throughput. That's a
> choice, and it's the right one for interactive traffic.

---

## Part F — Watch a query cross the slow-query line

Module 00 set `log_min_duration_statement=200`. Cash that in.

```bash
pg -c "SELECT count(*) FROM messages WHERE body LIKE '%needle%';"
docker compose -f ../../infra/compose.dev.yml logs postgres | tail -3
```
**Expected:**
```
LOG:  duration: 41821.402 ms  statement: SELECT count(*) FROM messages WHERE body LIKE '%needle%';
```

**41 seconds.** A leading-wildcard `LIKE` cannot use a B-tree index — it's a
sequential scan over 50 million rows.

This is why Module 12 has **no full-text search**. The options:

```bash
# Option 1: tsvector + GIN. Works to a few million rows.
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

2,270× faster. But measure what it cost:
```bash
pg -c "SELECT pg_size_pretty(pg_relation_size('idx_messages_fts'));"
```
```
 4218 MB
```

✅ **A 4.2 GB index and a write-time tokenization cost on every insert.** Measure
the insert rate again with it in place:

```
JdbcClient (batch 500) with FTS index:  91,204 rows/s   (was 224,467)
```

**59% slower writes** to serve a query nobody runs in the hot path.

> **The decision for Pulse: no FTS in Postgres.** Search goes to Elasticsearch or
> OpenSearch, fed from the outbox (Module 13). The write path stays fast, and
> search gets a system designed for it. Below ~5 million messages, `tsvector` +
> GIN is genuinely fine and saves you a whole component — know which side of that
> line you're on.

```bash
pg -c "DROP INDEX idx_messages_fts; ALTER TABLE messages DROP COLUMN body_tsv;"
```

---

## Part G — Size it

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

**236 bytes per row** for an 80-byte message body. The overhead:

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

Project it:

```
10,000 messages/sec x 86,400 = 864M rows/day
864,000,000 x 236 bytes      = 204 GB/day
                              = 74 TB/year
```

✅ **74 TB per year, on one table, on one machine.** That number is why Module 13
partitions (so you can drop old data instantly) and Module 14 shards (so it isn't
one machine).

Record it:
```markdown
## Module 12 — Message store

- Index order: (room_id, id) 0.118ms vs (id, room_id) 184ms  (1,560x)
- Keyset vs OFFSET at page 100,000: 0.79ms vs 2,841ms  (3,596x)
- OFFSET also duplicates rows when data is inserted mid-pagination
- Write rates: JPA 8.4k/s | JdbcClient 41k/s | batch-500 224k/s | COPY 980k/s
- FTS GIN index: 4.2GB and -59% write throughput  -> search goes elsewhere
- 236 bytes/row -> 204 GB/day at 10k msg/s -> 74 TB/year
```

---

## What you built

- A three-index schema where every index serves a hot-path query, with partial
  indexes for soft-delete and threads.
- **Measured** proof that UUIDv4 costs 6.7× write throughput and 3.6× index size
  — with `pgstatindex` showing exactly why (60% leaf density, 49% fragmentation).
- `EXPLAIN` proof of the equality-then-range index rule: 1,560× difference.
- Keyset pagination that is flat at any depth, and the OFFSET duplication bug.
- A write-path benchmark justifying `JdbcClient` for messages and JPA for
  everything else.
- A capacity projection: **74 TB/year**, which is the problem Modules 13 and 14
  exist to solve.

Now do [`challenge.md`](./challenge.md).

Then: [Module 13 — Partitioning, Replication & Pooling](../13-partitioning-replication-pooling/).
