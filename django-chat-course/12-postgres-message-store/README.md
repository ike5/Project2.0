# Module 12 — The Message Store

**Goal:** Design a message table that still works at ten billion rows — ID
scheme, index strategy, pagination, and the write-amplification decision that
determines everything downstream. And decide, with numbers, where the Django ORM
earns its keep and where it is pure overhead on the hot path.

⏱️ ~5 hours · **Prerequisites:** Modules 00–11.

> This is the Django/Python twin of
> [`spring-boot-chat-course/12-postgres-message-store`](../../spring-boot-chat-course/12-postgres-message-store/).
> The database is the same Postgres, so the ID/index/pagination numbers are
> **identical** — Postgres does not care what language talks to it. What changes
> is the application layer: Flyway becomes `migrations.RunSQL`, JPA-vs-`JdbcClient`
> becomes **Django ORM vs raw `connection.cursor()`**, and the Python runtime tax
> you have measured since Module 01 shows up one more time in the write path.

---

## Problem 4, finally

Module 00 named four problems of chat: a **connection-state** problem, a
**fan-out** problem, a **delivery-semantics** problem, and a
**write-amplification** problem. Phases 1–2 spent themselves on the first three.
This module is the fourth.

**Write amplification** is the question of how many rows one typed sentence
becomes.

```
Fan-out on READ:    1 message = 1 row.       Reads assemble each user's view.
Fan-out on WRITE:   1 message = N rows,      Writes do the work, one row per
                    one per recipient inbox.  recipient's inbox.
```

A 1,000-member room with fan-out-on-write is **1,000 inserts for one sentence**.
At 100 messages/second across busy rooms that is 100,000 writes/second — a
completely different database from the one you started with, and one you reach by
accident if you model "each user has an inbox" literally.

Pulse uses **fan-out on read**. It stores each message exactly once and derives
every user's view from `(room_id, seq)` plus their `last_read_seq` (the read
cursor from [Module 10](../10-ordering-and-delivery-semantics/)). The storage
cost is one row per message, forever; the read cost is one indexed range scan per
scrollback page. That is the whole trade, and it is the right one for chat —
until a room gets big enough that the calculus flips, which is
[Module 14](../14-sharding-and-wide-column/).

Everything in this module follows from "one row per message, and reads must be
cheap at any depth."

---

## ID design decides your future

The message ID is the single most consequential column in the schema. It is the
scrollback cursor, the sort key, the physical order rows land in the index, and —
in [Module 14](../14-sharding-and-wide-column/) — the thing that has to keep
working when messages live on eight independent databases. Choose it once; you
live with it for the life of the product.

| Scheme | Bits | Time-sortable | Coordination | Index locality |
|--------|------|---------------|--------------|----------------|
| `bigserial` | 64 | Yes | **A central sequence** | Excellent |
| UUIDv4 | 128 | No | None | **Terrible** |
| UUIDv7 | 128 | Yes | None | Good |
| **Snowflake** | 64 | Yes | Worker ID only | Excellent |

### Why UUIDv4 is a performance bug, not a style choice

A B-tree index stores keys in sorted order. **Sequential** inserts always append
to the rightmost leaf page — which is already in cache, and fills to ~90% before
Postgres allocates a new page. **Random** inserts land on random pages:

```
Sequential (Snowflake/UUIDv7):        Random (UUIDv4):
  [aaa|aab|aac|___]  <- append here     [a__|_m_|__z]  <- insert lands anywhere
       one hot page                      every page is dirtied
       ~100% fill                        ~50–70% fill after splits
       cache-resident                    random I/O across the whole index
```

Measured on a 50M-row table (you reproduce this in Lab Part B; reference machine
**8-core / 16 GB, Postgres 16, Python 3.12**):

| | Snowflake | UUIDv7 | UUIDv4 |
|---|-----------|--------|--------|
| Insert rate | 41,200/s | 38,900/s | **6,100/s** |
| Index size | 1.1 GB | 2.1 GB | **3.8 GB** |
| WAL per insert | 220 B | 260 B | **890 B** |

**6.7× slower inserts and 3.5× the index**, purely from key ordering. The 890
bytes of WAL per random insert is a **full-page write**: the page UUIDv4 dirtied
was not already dirty in this checkpoint cycle, so Postgres logs the whole 8 KB
page for crash safety. Sequential inserts keep hitting the same hot page, so they
amortize that cost to near zero.

This is not a micro-optimization you can defer. At 10,000 messages/second the
difference between 6,100/s and 41,200/s is the difference between one Postgres
box and seven.

### Why UUIDv4 is *especially* a trap in Django

Django makes UUIDv4 a one-liner:

```python
import uuid
id = models.UUIDField(primary_key=True, default=uuid.uuid4)   # <- the trap
```

It reads as the modern, distributed-friendly, "no central sequence" choice. It is
the single most common way a Django team writes a table that falls over at scale,
because the cost is invisible until the table is large and the index no longer
fits in cache. The fix is `uuid.uuid7()` (Python 3.14+; a five-line shim before
that) or a Snowflake — both time-ordered, both keeping your inserts sequential.

### Why not `bigserial`

It is excellent — sequential, compact, cache-friendly — until you shard
([Module 14](../14-sharding-and-wide-column/)). A central sequence is a
coordination point that cannot span independent databases, and the moment you
split messages across two Postgres instances their `bigserial` counters both
start at 1 and your IDs collide.

Snowflake's worker-ID bits exist precisely to make ID generation
**coordination-free**: each process stamps its own worker ID into the ID, so two
processes never collide without ever talking to each other.

```
Snowflake (64 bits):
  ┌────────────────────────────┬───────────┬──────────────┐
  │  41-bit millisecond time   │ 10-bit    │  12-bit       │
  │  (since a custom epoch)    │ worker id │  per-ms seq   │
  └────────────────────────────┴───────────┴──────────────┘
   time-sortable ───────────────┘   coordination-free ┘
```

You pay for a future you may not have; the cost is about ten lines of Python and
it is the difference between sharding being a migration and being impossible.
This is why Module 12's ID decision is *made for Module 14* — write that link
down, because it is the clearest example in the course of an early decision
buying a late option.

---

## Index design

The dominant query in all of chat is scrollback — "give me the last 50 messages
in this room, older than what I already have":

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

**The rule: equality columns first, then the range/sort column.** Postgres can
seek straight to `room_id = 7` and then walk the index backwards — and because
the index is already in `id DESC` order for that room, the `ORDER BY` is *free*
(no `Sort` node in the plan).

Get the order backwards and `EXPLAIN` shows the tell:

```
Rows Removed by Filter: 4982104
```

The index found the right `id` range across *all* rooms, then read and discarded
five million rows from other rooms to find 50 from yours. In Lab Part C you
measure this at **0.118 ms vs 184 ms — 1,560× slower**.

### The other two indexes

```sql
-- Idempotency (Module 05). Without this, a retried send creates a duplicate.
CREATE UNIQUE INDEX ON messages (room_id, client_id);

-- Resume (Module 10). seq, not id — the client's resume cursor is a seq.
CREATE INDEX ON messages (room_id, seq);
```

In the production schema the resume index is the **primary key** itself —
`PRIMARY KEY (room_id, seq)` — which enforces per-room sequence uniqueness for
free *and* makes resume a primary-key range scan. That is one fewer index to
maintain, and the challenge asks you to prove the scrollback index is then
redundant too.

**Three indexes is the budget.** Every index is written on every insert; at
40,000 inserts/second a fourth index that serves a query you run monthly costs
you continuously. The discipline: **an index must serve a query in the hot path,
or it should not exist.** There is deliberately no index on `created_at` (Module
13 partitions on it, which gives time-range pruning without an index) and none on
`sender` (moderation runs a few times a day and can afford a slow plan on a
replica).

---

## Keyset pagination, always

```sql
-- O(offset). At page 2,000 this reads and discards 100,000 rows.
SELECT * FROM messages WHERE room_id=7 ORDER BY id DESC LIMIT 50 OFFSET 100000;

-- O(log n + limit). Identical cost at page 1 and page 2,000,000.
SELECT * FROM messages WHERE room_id=7 AND id < :cursor ORDER BY id DESC LIMIT 50;
```

`OFFSET` does not skip rows cheaply — Postgres must *produce* every row up to the
offset and throw it away. Measured (Lab Part D):

| Page | OFFSET | Keyset |
|------|--------|--------|
| 1 | 0.9 ms | 0.8 ms |
| 100 | 4.1 ms | 0.8 ms |
| 10,000 | 284 ms | 0.8 ms |
| 100,000 | **2,840 ms** | **0.8 ms** |

Django makes this trap even easier to fall into than raw SQL, because
`Paginator` and DRF's default `PageNumberPagination` are **`OFFSET`/`LIMIT`
underneath**:

```python
Message.objects.filter(room_id=room)[100000:100050]   # -> OFFSET 100000 LIMIT 50
```

Every "page N" API you have ever built with `PageNumberPagination` degrades
linearly with depth. The fix is DRF's **`CursorPagination`** (keyset, and it is
built in) or a hand-rolled `WHERE id < :cursor` — which is exactly the
`resume-from-cursor` your protocol already speaks (Module 10).

`OFFSET` also has a **correctness** bug people miss: if rows are inserted while a
user paginates, `OFFSET 50` now points at a *different* row, and they see a
duplicate — or silently skip one. A cursor is stable because it names a **row**,
not a **position**. You reproduce this in Lab Part D.

---

## Django ORM or raw SQL?

Both, deliberately split — the Python analog of the JVM twin's "JPA or JdbcClient?"

| Data | Access | Why |
|------|--------|-----|
| Rooms, users, memberships | **Django ORM** | Rich relationships, low write rate, migrations, admin — the model layer earns its cost |
| **Messages** | **raw `connection.cursor()`** | 40,000 inserts/sec; model instantiation, field descriptors, signals, and `save()`'s machinery are pure overhead for insert-only data |

At the message rate, the Django ORM costs you, per row:

- A full model instance: every field is a descriptor, `__init__` runs Python for
  each column, and the object lives on the heap until it is garbage-collected.
- `save()`'s pre-save/post-save **signals** dispatch, `update_fields` diffing, and
  a per-call trip through the SQL compiler.
- No natural fit for `INSERT ... ON CONFLICT ... RETURNING`, which is the single
  statement that makes idempotency atomic. `get_or_create` needs two round trips
  and a race window; the ORM's `ON CONFLICT` support (`bulk_create(...,
  update_conflicts=...)`) is batch-only and awkward for a single returning insert.

Measured (Lab Part E, reference machine above):

| Path | Rate | Note |
|------|------|------|
| `Message.objects.create()` (ORM, one row) | **7,800/s** | model build + `save()` + signals per row |
| raw `cursor.execute` (one row, `ON CONFLICT RETURNING`) | **41,200/s** | the hot send path |
| `bulk_create(batch_size=500)` | **168,000/s** | still builds N model instances |
| raw `execute_values` (batch 500) | **224,000/s** | no model instances at all |
| `COPY` (`cursor.copy`) | **980,000/s** | backfill / bulk import only |

**Raw single insert is 5.3× the ORM's `create()`; batching is another 5.4×.**

Notice that Django's `create()` (7,800/s) is *slightly slower* than the JVM
twin's JPA (8,400/s). That is not a mistake — it is the **runtime tax** you have
watched since Module 01 showing up again: Python builds heavier objects per unit
of work and its per-call overhead is higher. The shape of the lesson is identical
across both courses; the numbers shift down a little on Python, exactly as they
did for the single-node fan-out knee in Module 06.

> "Always use the ORM" and "never use the ORM" are both positions held by people
> who have not profiled. Use the ORM where the object graph earns it — rooms,
> memberships, the admin. Drop to `cursor` on the one path that runs 40,000 times
> a second. `database_sync_to_async` (Module 15) wraps either one to keep it off
> the event loop; the choice of ORM-vs-raw is orthogonal to async-vs-sync.

---

## Storing the body

| Type | When |
|------|------|
| `TextField` (`text`) | Default. In Postgres, `text` and `varchar(n)` are **identical** in storage; `varchar(n)` only adds a length check constraint. Don't cargo-cult a max length. |
| `JSONField` (`jsonb`) | Rich structured content (attachments, blocks, formatting). GIN-indexable, but ~15% larger and slower to write. |
| `BinaryField` (`bytea`) | Encrypted payloads (Module 21). |

**TOAST** — *The Oversized-Attribute Storage Technique* — matters here. When a
row's variable-length data would push the row past ~2 KB, Postgres moves the big
values out of the main heap into a side "TOAST" table, compressed, leaving a
pointer behind. So a table of mostly-short messages stays **dense and fast**, and
the occasional 10 KB message does not bloat every page around it. You get this for
free — but it means a query that selects `body` on long messages pays an extra
random fetch into the TOAST table. `SELECT id, sender, seq` for a list view
avoids it entirely; the challenge measures this at **69× slower** with 5 KB
bodies.

---

## Soft delete, and its cost

```python
deleted_at = models.DateTimeField(null=True)
```

Every read must then filter:

```sql
WHERE room_id = 7 AND deleted_at IS NULL
```

which either widens your index or forces a filter after the index scan. The fix
is a **partial index** — one that only indexes the rows you actually query:

```sql
CREATE INDEX ON messages (room_id, id DESC) WHERE deleted_at IS NULL;
```

It is smaller (deleted rows are not indexed at all), and the planner uses it
automatically whenever the query's predicate implies the index's `WHERE`. Django
expresses this natively with a `condition` on the index:

```python
class Meta:
    indexes = [
        models.Index(
            fields=["room_id", "-id"],
            condition=models.Q(deleted_at__isnull=True),
            name="idx_messages_scrollback",
        ),
    ]
```

Partial indexes are one of Postgres's genuinely underused features, and Django
has supported them since 2.2 — most teams just never reach for them.

But be clear about what soft delete *costs*: a soft delete is an `UPDATE`, and
under Postgres MVCC an `UPDATE` writes a **new** row version and marks the old one
dead. Soft-deleting a million messages writes a million new tuples and leaves a
million for autovacuum. And **deleted messages still occupy storage, still get
vacuumed, still appear in backups, and are still one `SELECT` (minus the filter)
away for any operator.** For GDPR erasure you need *real* deletion or
crypto-shredding — which the challenge builds, and which
[Module 13](../13-partitioning-replication-pooling/)'s partitioning makes cheap
at the table level.

---

## Why not full-text search in Postgres?

Because the honest answer is "it works until it doesn't, and the hot path pays for
it forever." A leading-wildcard `LIKE '%needle%'` cannot use a B-tree at all — it
is a sequential scan over every row (**41 seconds** on 50M rows, Lab Part F). A
`tsvector` + GIN index fixes the query (2,270× faster) but costs a **4.2 GB
index** and a **59% write-throughput hit** from tokenizing every message on
insert. For Pulse the decision is: **no FTS in Postgres.** Search goes to a system
built for it (Elasticsearch/OpenSearch), fed asynchronously from the outbox
(Module 13), and the write path stays fast. Below ~5 million messages, `tsvector`
+ GIN is genuinely fine and saves you a component — know which side of that line
you are on.

---

## What's next

The lab builds the schema with `migrations.RunSQL`, benchmarks the three ID
schemes head to head at 50 million rows, proves the equality-then-range index rule
with `EXPLAIN`, measures `OFFSET` versus keyset at depth (and reproduces the
duplication bug), pits the Django ORM against raw `cursor` / `bulk_create` /
`COPY` at full write rate, finds the TOAST threshold, and ends with the
projection that drives the next two modules: **74 TB/year.**

See you in [`lab.md`](./lab.md).
