# Module 12 — The Message Store

**Goal:** Design a message table that still works at ten billion rows — ID
scheme, index strategy, pagination, and the write-amplification decision that
determines everything downstream.

⏱️ ~5 hours · **Prerequisites:** Modules 00–11.

---

## Problem 4, finally

Module 00 named four problems. This is the fourth: **write amplification**.

```
Fan-out on READ:    1 message = 1 row.       Reads assemble the view.
Fan-out on WRITE:   1 message = N rows,      Writes do the work.
                    one per recipient inbox.
```

A 1,000-member room with fan-out-on-write is **1,000 inserts for one typed
sentence**. At 100 messages/second that's 100,000 writes/second — a completely
different database than the one you started with.

Pulse uses **fan-out on read**, stores each message once, and derives every
user's view from `(room_id, seq)` plus their `last_read_seq` (Module 10). The
storage cost is one row per message, forever, and the read cost is one indexed
range scan.

Module 14 revisits this, because above a certain room size the calculus flips.

---

## ID design decides your future

| Scheme | Bits | Time-sortable | Coordination | Index locality |
|--------|------|---------------|--------------|----------------|
| `bigserial` | 64 | Yes | **A central sequence** | Excellent |
| UUIDv4 | 128 | No | None | **Terrible** |
| UUIDv7 | 128 | Yes | None | Good |
| **Snowflake** | 64 | Yes | Worker ID only | Excellent |

### Why UUIDv4 is a performance bug, not a style choice

B-tree indexes store keys in sorted order. Sequential inserts always append to
the rightmost leaf page — which is in cache, and fills completely before a new
page is allocated.

Random inserts land on **random pages**:

```
Sequential (Snowflake/UUIDv7):        Random (UUIDv4):
  [aaa|aab|aac|___]  <- append here     [a__|_m_|__z]  <- insert lands anywhere
       one hot page                      every page is dirtied
       ~100% fill                        ~50-70% fill after splits
       cache-resident                    random I/O across the whole index
```

Measured on a 50M-row messages table (Lab Part B):

| | Snowflake | UUIDv7 | UUIDv4 |
|---|-----------|--------|--------|
| Insert rate | 41,200/s | 38,900/s | **6,100/s** |
| Index size | 1.1 GB | 2.1 GB | **3.8 GB** |
| WAL per insert | 220 B | 260 B | **890 B** |

**6.7× slower inserts and 3.5× the index**, purely from key ordering.

### Why not `bigserial`

It's excellent — until you shard (Module 14). A central sequence is a
coordination point that cannot span independent databases, and the moment you
split messages across two Postgres instances your IDs collide.

Snowflake's worker-ID bits exist precisely to make ID generation
**coordination-free**. You pay for a future you may not have; the cost is ten
lines of code and it's the difference between sharding being a migration and
being impossible.

---

## Index design

The dominant query is scrollback:

```sql
SELECT * FROM messages
WHERE room_id = 7 AND id < :cursor
ORDER BY id DESC
LIMIT 50;
```

The index must be **`(room_id, id DESC)`**, in that order.

```
(room_id, id)                     (id, room_id)
  room 7 ──▶ [id: 900, 899, ...]    id 900 ──▶ [room 7]
  room 8 ──▶ [id: 950, 949, ...]    id 899 ──▶ [room 3]
  ✅ one contiguous range scan       ❌ scan everything, filter by room
```

**The rule:** equality columns first, then the range/sort column. Postgres can
seek to `room_id = 7` and then walk backwards — the `ORDER BY` is free.

Get it backwards and `EXPLAIN` shows:
```
Rows Removed by Filter: 4982104
```

### The other two indexes

```sql
-- Idempotency (Module 05). Without this, retries create duplicates.
CREATE UNIQUE INDEX ON messages (room_id, client_id);

-- Resume (Module 10). seq, not id — the client's cursor is a seq.
CREATE INDEX ON messages (room_id, seq);
```

**Three indexes is the budget.** Every index is written on every insert; at
40,000 inserts/second, a fourth index you query monthly costs you continuously.
The discipline is: **an index must serve a query in the hot path, or it should
not exist.**

---

## Keyset pagination, always

```sql
-- O(offset). At page 2000 this reads and discards 100,000 rows.
SELECT * FROM messages WHERE room_id=7 ORDER BY id DESC LIMIT 50 OFFSET 100000;

-- O(log n + limit). Identical cost at page 1 and page 2,000,000.
SELECT * FROM messages WHERE room_id=7 AND id < :cursor ORDER BY id DESC LIMIT 50;
```

Measured (Lab Part C):

| Page | OFFSET | Keyset |
|------|--------|--------|
| 1 | 0.9 ms | 0.8 ms |
| 100 | 4.1 ms | 0.8 ms |
| 10,000 | 284 ms | 0.8 ms |
| 100,000 | **2,840 ms** | **0.8 ms** |

`OFFSET` also has a **correctness** bug people miss: if rows are inserted while a
user paginates, `OFFSET 50` now points at a different row and they see a
duplicate — or skip one. A cursor is stable because it names a row, not a
position.

---

## JPA or JDBC?

Both, deliberately split:

| Data | Access | Why |
|------|--------|-----|
| Rooms, users, memberships | **JPA** | Rich relationships, low write rate, the object graph earns its cost |
| **Messages** | **`JdbcClient`** | 40,000 inserts/sec; dirty checking, the persistence context, and entity hydration are pure overhead |

At the message rate, JPA costs you:
- A persistence-context entry per entity (heap that lives until flush).
- Dirty checking on flush — a field-by-field comparison you don't need for
  insert-only data.
- No natural fit for `INSERT ... ON CONFLICT ... RETURNING`, which is the single
  statement that makes idempotency work.

Measured (Lab Part D): **JPA 8,400 inserts/s vs JdbcClient 41,200/s.**

> "Always use the ORM" and "never use the ORM" are both positions held by people
> who haven't profiled. Use it where the object graph earns it.

---

## Storing the body

| Type | When |
|------|------|
| `text` | Default. Postgres `text` and `varchar(n)` are identical in storage; `varchar(n)` only adds a check constraint. |
| `jsonb` | If messages carry rich structured content (attachments, blocks, formatting). Indexable with GIN, but ~15% larger and slower to write. |
| `bytea` | Encrypted payloads (Module 21). |

**TOAST** matters here: Postgres moves values over ~2 KB out of the main heap
into a side table, compressed. So a table of mostly-short messages stays dense
and fast, and the occasional 10 KB message doesn't bloat every page. You get this
for free — but it means a query selecting `body` on long messages does an extra
fetch. `SELECT id, sender, seq` for a list view avoids it entirely.

---

## Soft delete, and its cost

```sql
deleted_at timestamptz
```

Every read must then filter:
```sql
WHERE room_id = 7 AND deleted_at IS NULL
```

Which either widens your index or forces a filter after the index scan. The fix
is a **partial index**:

```sql
CREATE INDEX ON messages (room_id, id DESC) WHERE deleted_at IS NULL;
```

Smaller (deleted rows aren't indexed), and the planner uses it automatically when
the predicate matches. Partial indexes are one of Postgres's genuinely
underused features.

But be clear about what soft delete costs: **deleted messages still occupy
storage, still get vacuumed, and still appear in backups.** For GDPR erasure you
need real deletion, which Module 13's partitioning makes cheap.

---

## What's next

The lab builds the schema, benchmarks the three ID schemes head to head, proves
the index-order rule with `EXPLAIN`, measures OFFSET versus keyset at depth, and
compares JPA against `JdbcClient` at 40,000 inserts/second.

See you in [`lab.md`](./lab.md).
