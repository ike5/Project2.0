# Module 13 — Partitioning, Replication & Pooling

**Goal:** Make 74 TB/year manageable on one machine — instant retention, read
scaling, connection multiplexing — and finally close the dual-write hole with a
transactional outbox.

⏱️ ~5 hours · **Prerequisites:** Modules 00–12.

---

## Partitioning: retention becomes free

Module 12 projected 204 GB/day. The naive retention job:

```sql
DELETE FROM messages WHERE created_at < now() - interval '90 days';
```

At 864 million rows/day that statement:
- Runs for **hours**, holding a transaction open the whole time.
- Generates **~200 GB of WAL**, which ships to every replica and every backup.
- Leaves 864 million **dead tuples** for autovacuum, which then competes with
  your live traffic for I/O.
- **Doesn't return the disk space** — the table stays the same size until a
  `VACUUM FULL` (which takes an exclusive lock) or `pg_repack`.

With declarative partitioning:

```sql
DROP TABLE messages_2025_08;
```

**Instant. Near-zero WAL. Space returned immediately. No vacuum debt.**

That single difference is the reason to partition. Query performance is a bonus.

```sql
CREATE TABLE messages (...) PARTITION BY RANGE (created_at);

CREATE TABLE messages_2026_08 PARTITION OF messages
    FOR VALUES FROM ('2026-08-01') TO ('2026-09-01');
```

### Partition on time, index on room

The instinct is to partition by `room_id` — that's the shard key, after all.
Resist it:

| Partition key | Partitions | Retention | Pruning on scrollback | Verdict |
|---------------|-----------|-----------|----------------------|---------|
| `created_at` (monthly) | ~12–36 | ✅ `DROP TABLE` | ✅ when a time range is given | **Yes** |
| `room_id` (hash, 64) | 64 | ❌ `DELETE` per partition | ✅ always | No retention story |
| `room_id` (list, one per room) | **thousands** | ✅ per room | ✅ | Planning-time explosion |

Postgres considers every partition at plan time. A few dozen is free; a few
thousand adds milliseconds to **every** query. Time partitioning gives you a
bounded, predictable count.

**Room-level sharding is a different mechanism at a different layer** — Module 14.

### The pruning caveat that catches everyone

```sql
-- PRUNES: created_at is in the predicate
SELECT * FROM messages WHERE room_id='7' AND created_at > '2026-08-01' ORDER BY seq DESC LIMIT 50;

-- DOES NOT PRUNE: no created_at predicate, so every partition is scanned
SELECT * FROM messages WHERE room_id='7' AND seq < 48213 ORDER BY seq DESC LIMIT 50;
```

Your scrollback query pages by `seq`, not by time — so it **doesn't prune**, and
partitioning makes it *slower* (N index scans instead of one).

Two fixes, and you want both:
1. **Add a time hint** derived from the Snowflake ID, which contains a timestamp.
   `WHERE created_at > timestamp_of(cursor) - interval '1 day'`.
2. **Keep partitions few.** 12 monthly partitions costs 12 index scans of a few
   pages each — measurable but small. 500 daily partitions does not.

> This is the module's central honest admission: **partitioning is not free for
> reads.** You adopt it for retention and pay a small read tax, then claw the tax
> back with a time hint.

---

## Replication and the read-your-writes problem

```sql
-- on the primary
SELECT client_addr, state, replay_lag FROM pg_stat_replication;
-- on the replica
SELECT now() - pg_last_xact_replay_timestamp() AS lag;
```

Read replicas scale reads. They introduce exactly one class of bug:

```
t=0    alice sends a message; it commits on the primary
t=1    alice's client loads history — from a replica that is 200ms behind
t=2    her own message is missing
```

Four fixes, in order of preference for chat:

| Fix | Cost |
|-----|------|
| **Echo optimistically; never read back** | Free — and Pulse already does it (Module 05) |
| Route that user's reads to the primary for N seconds after a write | Simple; a "sticky window" per user |
| Capture the write's LSN, have the read wait for `pg_last_wal_replay_lsn() >= lsn` | Precise; more plumbing |
| `synchronous_commit = remote_apply` | Correct everywhere; costs write latency on every write |

**Chat has a fourth option the others don't: the sender already has the
message.** Optimistic rendering plus a `clientId` match means the sender never
needs to read their own write back. The bug mostly disappears by construction.

Where it *doesn't* disappear: a second device. Alice sends from her phone and
opens her laptop 100 ms later. Then you need the sticky window.

### `synchronous_commit`, precisely

| Setting | Waits for | Loss on primary crash |
|---------|-----------|----------------------|
| `off` | nothing | up to `wal_writer_delay` |
| `local` | local WAL flush | none locally; replica may lag |
| `remote_write` | replica received | loss if the replica's OS crashes |
| `on` (default) | replica flushed to disk | none |
| `remote_apply` | replica **applied** | none; reads are consistent |

Pulse uses `on` for messages and **`remote_apply` for the outbox write
specifically** — because an outbox row that exists on the primary but not on a
promoted replica means a message that will never be published.

---

## Connection pooling

Postgres forks a **process per connection** (~5–10 MB each). This is not a
tunable; it's the architecture.

```
20 app instances x 20 connections = 400 connections = ~4 GB of postgres processes
                                                       and heavy context switching
```

Throughput actually **decreases** past roughly `(cores × 2) + spindles` active
connections. On a 16-core box that's ~34, not 400.

**PgBouncer** multiplexes many client connections onto few server ones:

```ini
pool_mode = transaction
max_client_conn = 10000
default_pool_size = 25
```

| Mode | Server connection held for | Breaks |
|------|---------------------------|--------|
| `session` | the whole client session | nothing; barely helps |
| **`transaction`** | one transaction | `SET`, advisory locks, `LISTEN/NOTIFY`, server-side prepared statements, cursors outside a transaction, temp tables |
| `statement` | one statement | multi-statement transactions entirely |

Transaction mode is what you want, and the prepared-statement issue is real:

```properties
spring.datasource.url=jdbc:postgresql://pgbouncer:6432/pulse?prepareThreshold=0
```

Without that, pgjdbc prepares a statement on one server connection and executes
it on another, and you get `prepared statement "S_1" does not exist` — an error
that appears only under load, which is the worst kind.

---

## The transactional outbox

This is the module's most important piece, and it closes a hole that has been
open since Module 07.

**The dual-write problem:**

```java
repository.insert(message);        // commits
streamFanout.append(envelope);     // <-- crash here
```

The message is durable and **will never be delivered**. No retry helps: the
process that knew is gone. Module 10's resume doesn't help either — resume reads
the *database*, so a client asking "what did I miss" gets the message... but only
if it asks. A client that was connected the whole time simply never receives it
and has no gap to detect, because the `seq` was allocated and used.

**The outbox makes the two writes atomic:**

```sql
BEGIN;
  INSERT INTO messages (...);
  INSERT INTO outbox (payload) VALUES (...);
COMMIT;                             -- both, or neither
```

Then a separate relay publishes:

```sql
BEGIN;
SELECT * FROM outbox WHERE published_at IS NULL
ORDER BY id LIMIT 100
FOR UPDATE SKIP LOCKED;             -- <-- the important part
-- XADD to Redis
UPDATE outbox SET published_at = now() WHERE id = ANY(:ids);
COMMIT;
```

`FOR UPDATE SKIP LOCKED` lets N relay instances work the same table concurrently
without blocking each other or double-publishing.

**Delivery is still at-least-once** — the relay can publish and then crash before
the `UPDATE` — which is exactly why consumers dedup on `client_id`. The whole
chain now holds:

```
persist ──atomic──▶ outbox ──at-least-once──▶ Redis Stream
                                                  │ at-least-once
                                                  ▼
                                           consumer ──idempotent──▶ delivery
```

### Outbox versus CDC

| | Outbox | CDC (Debezium / logical decoding) |
|---|--------|----------------------------------|
| Latency | polling interval (or instant with `LISTEN/NOTIFY`) | near-real-time |
| Payload | exactly what you chose to publish | raw row changes; you shape them downstream |
| Extra infrastructure | none | Connect cluster, replication slots |
| **Failure mode** | backlog grows in a table you can query | **a stalled slot pins WAL and fills the disk** |

That last row decides it for Pulse. An outbox backlog is a number on a dashboard.
A stalled replication slot is a 3 a.m. disk-full page, and it's the most common
way people take down a Postgres they were using CDC on.

---

## What's next

The lab partitions the table and measures both the retention win and the read
tax, sets up streaming replication and induces read-your-writes failures,
inserts PgBouncer and measures the multiplexing win, and builds the outbox — then
kills the process between persist and publish to prove nothing is lost.

See you in [`lab.md`](./lab.md).
