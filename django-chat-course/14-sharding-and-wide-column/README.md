# Module 14 — Sharding & Wide-Column

**Goal:** Push writes past one Postgres — with a Django DB router, not a
hand-rolled hack — and then ask the harder question: is a relational database
the right *shape* for chat at all?

⏱️ ~6 hours · **Prerequisites:** Modules 00–13.

> The Django/Python twin of
> [`spring-boot-chat-course/14-sharding-and-wide-column`](../../spring-boot-chat-course/14-sharding-and-wide-column/).
> Postgres and ScyllaDB do not care what language talks to them, so the storage
> conclusions are the same. What changes is **who does the routing** — Django's
> `DATABASE_ROUTERS` hook instead of a hand-written `ShardRouter` bean — and one
> Python-specific wall you will hit hard in Part C: a single interpreter cannot
> drive four shards, because scatter-gather is concurrency and the GIL is still
> the GIL.

---

## Everything you should try before sharding

Sharding is a one-way door. It removes cross-shard joins, cross-shard
transactions and global ordering, and it turns every future schema change into an
orchestrated migration across N databases. Exhaust the alternatives first:

| Option | Buys you | Try before sharding? |
|--------|----------|---------------------|
| **Retention** ([Module 13](../13-partitioning-replication-pooling/)) | Most "we need to shard" is "we need to delete." 74 TB/year → 18.4 TB live. | ✅ **always first** |
| **Read replicas** (Module 13) | Read scaling. Does **nothing** for writes. | ✅ |
| **A bigger machine** | A 96-core / 1.5 TB / NVMe box absorbs far more than people assume. | ✅ genuinely |
| **Tiering cold months to object storage** | ~60% of the storage bill, no data loss. | ✅ |
| **Sharding** | Write scaling past one machine. | Last |

Do the arithmetic before the architecture. [Module 12](../12-postgres-message-store/)
projected Pulse at **204 GB/day, 864 million rows/day, 74 TB/year** at the 10k
msg/s target. Module 13's 90-day retention cuts the *live* set to:

```
204 GB/day × 90 days  =  18.4 TB      (77.8 billion rows)
```

That is one commodity NVMe array. Split four ways it is **4.6 TB and 19.4 billion
rows per shard** — comfortably indexed, still one `pg_dump` you could actually
restore.

The honest threshold: **shard when a single well-tuned primary cannot absorb your
write rate, and you have already deleted everything you can.** Module 12 measured
**41,200 inserts/s** on a laptop through raw `connection.cursor()`; a real server
does several hundred thousand. Most products never get there.

---

## Shard by room, not by user

```
physical_shard = assignment[ crc32(room.key) mod 4096 ]
```

This is the single most consequential decision in the module, and it falls out of
the query pattern rather than out of taste:

| Shard key | "last 50 messages in this room" | "all my rooms' unread counts" |
|-----------|--------------------------------|-------------------------------|
| **`room_id`** | ✅ **one shard** | scatter-gather over ~20 rooms |
| `user_id` | ❌ **scatter-gather over every member** | ✅ one shard |

Chat's dominant, latency-critical query is scrollback, and Module 12 built the
whole store around it: `PRIMARY KEY (room_id, seq)`, `INDEX (room_id, id DESC)`.
Sharding by room keeps that query on exactly one node and exactly one index scan.

The unread-count query becomes scatter-gather — but Module 10 made it two
integers per room (`room.last_seq − user.last_read_seq`), it is cacheable, and it
is not on the path a human is watching a cursor blink on.

**Sharding by user would require storing a copy of each message per recipient** —
fan-out on write, one row per member. That is precisely the design
[Module 12](../12-postgres-message-store/) rejected in its first section. Sharding
by user is not a routing choice; it is a data-model choice, made accidentally.

### Room identity, restated because sharding depends on it

Since [Module 05](../05-protocol-and-domain-design/) the identity has been fixed:

```python
class Room(models.Model):
    slug = models.SlugField(unique=True)      # "general", "7"

    @property
    def key(self) -> str:
        return f"room.{self.slug}"            # "room.general", "room.7"
```

`Room.key` is simultaneously the **channel-layer group name**, the `room` field in
every protocol envelope, and the **`room_id` column** in `chat_message`. One
string, three jobs — which is why it is also the shard key. Hash the composed key
(`room.7`), never the bare slug, or the shard router and the store disagree about
what a room is.

---

## What you lose, precisely

| Capability | Status after sharding |
|------------|----------------------|
| Cross-shard `JOIN` | **Gone.** Denormalize, or two round trips. |
| Cross-shard transaction | **Gone.** (2PC exists; its failure modes are worse than the problem.) |
| Global `ORDER BY` | Merge in the application. |
| `BigAutoField` / `bigserial` | **Gone.** This is *why* Module 12 chose Snowflake. |
| Global unique constraints | Unique **within a shard** only. |
| `COUNT(*)` across everything | Scatter-gather, or a maintained counter. |
| Django FKs from `Message` to `Room` | **Gone** — Django refuses cross-database relations. |
| Schema migrations | N databases, orchestrated, with a version-skew window. |

Two of those rows were decided for you, three modules ago, and it is worth saying
out loud how much that bought:

- **Snowflake IDs (Module 12).** A central sequence cannot span independent
  databases. Had `messages.id` been a `BigAutoField`, sharding would now mean
  rewriting every ID in the system, plus every client cursor that references one.
  Ten lines of `code/snowflake.py` bought this entire module.
- **`managed = False` and a plain `room_id text` column (Module 12).** Because
  `Message` was never given a `ForeignKey` to `Room`, there is no cross-database
  relation to break. If you had written `room = models.ForeignKey(Room)`, sharding
  would now require dropping it — a migration on a table with 19 billion rows.
- **Per-room `seq`, not a global one (Module 10).** Module 10 defended per-room
  ordering on latency grounds ("global ordering converts one sick room into a sick
  system"). Sharding is the second, structural reason: a global counter makes
  rooms dependent, and shards exist because they are not.

> The clearest example in this course of an early decision buying a late option.
> Write it down; it is the shape of the answer to "why did you do it that way?"
> in every architecture review you will ever sit in.

---

## Resharding is the hard part

Naive `crc32(room.key) mod N` remaps almost everything when N changes. Measured
over 200,000 room keys (you reproduce this in Lab Part A — it is arithmetic, not
a benchmark, so your numbers will match exactly):

| Growth | Rooms that move with naive `mod N` | Theoretical minimum |
|--------|-----------------------------------|--------------------|
| 4 → 5 | **79.8%** | 20.0% |
| 4 → 6 | **66.6%** | 33.3% |
| 4 → 7 | **85.8%** | 42.9% |
| 4 → 8 | 50.0% | 50.0% |

Look at the last row. **Doubling is the one case where naive modulo is optimal** —
which is exactly why a team that has only ever doubled has never discovered they
have a problem, and then goes 8 → 12 during an incident and moves two thirds of
their data.

Two standard fixes:

**Consistent hashing** — place nodes on a ring; a key belongs to the next node
clockwise. Adding a node remaps only `1/n` of keys. Correct, and slightly fiddly
(you need virtual nodes to get an even distribution).

**Logical shards (simpler, and what Pulse uses)** — hash to a large fixed number
of *logical* shards, then map logical → physical through a table:

```
room.key ──crc32──▶ 4096 logical shards ──lookup──▶ 4 physical databases
                                                     (1024 logical each)
```

```
                 logical shard 0..4095
    ┌──────────┬──────────┬──────────┬──────────┐
    │  0-1023  │1024-2047 │2048-3071 │3072-4095 │
    └────┬─────┴────┬─────┴────┬─────┴────┬─────┘
       shard0     shard1     shard2     shard3
```

Growing to 6 databases means **moving 1,364 of 4,096 logical shards — 33.3%, the
theoretical minimum**, against 66.6% for naive modulo. The hash function never
changes; only a small mapping table does.

This is how Vitess, Citus and Redis Cluster all work — and you have already met
the third one. Redis Cluster hashes keys to **16,384 slots** and maps slots to
nodes; Module 09's stream key `room:{7}:stream` uses the hash tag `{7}` so every
key for room 7 lands in one slot (**slot 1716** — CRC16 of `7`, mod 16384; verify
it yourself with `redis-cli CLUSTER KEYSLOT 'room:{7}:stream'` in Module 18).
Module 16 will show you the same idea a third time as Kafka partitions. Three
systems, one pattern:

> **Hash to a fixed, large-ish number of buckets. Map buckets to machines. Move
> buckets, never rehash.**

**Pick your logical shard count once and make it large.** Changing it later is
precisely the migration you adopted logical shards to avoid.

---

## Django DB routers, extended

Module 13 established the mechanism. Do not abandon it now:

```python
# pulse/settings/shards.py
DATABASE_ROUTERS = [
    "pulse.routers.ShardRouter",     # <- FIRST: messages
    "pulse.routers.ReplicaRouter",   # <- Module 13: everything else
]
```

**Order matters, and it is the first thing people get wrong.** Django consults
routers in list order and takes the first non-`None` answer. `ShardRouter` must
answer for `Message` and return `None` for everything else, so `ReplicaRouter`
still splits reads and writes for rooms, memberships and the outbox. A router that
returns a string for models it does not own silently steals them.

### Not everything shards

```
default   ← rooms, users, memberships, outbox, shard_assignment   (+ its replica)
shard0..3 ← chat_message, and only chat_message
```

The `default` database is the **directory**: small, joinable, transactional, and
the thing the outbox relay (Module 13) still needs an atomic commit against. The
sharded tier holds one insert-only table. Keeping that boundary sharp is what
makes the rest of the system continue to work.

### The trap Django sets for you

```python
def db_for_read(self, model, **hints): ...
```

Look at the signature. **The router receives the model and some hints — never the
query.** It cannot see `WHERE room_id = 'room.7'`, because at the moment Django
picks a database the `WHERE` clause has not been compiled yet. `hints` carries
`instance` on writes (so `db_for_write` can read `instance.room_id`) and carries
essentially nothing on reads.

This is the same shape of problem Module 13 hit with read-your-own-writes, and it
has the same answer: **put the fact where the router can see it, in a
`contextvars.ContextVar`.**

```python
with room_scope(room.key):                        # sets the ContextVar
    rows = Message.objects.filter(room_id=room.key, id__lt=cursor)[:50]
```

`ContextVar`, not `threading.local()` — for the two reasons Module 13's
`code/routers.py` spells out: asyncio runs thousands of coroutines on one thread,
and `database_sync_to_async` copies the *context* into its threadpool worker but
does not copy thread-locals. Both reasons apply here unchanged.

And the router's real job becomes **a tripwire**: if a `Message` query reaches it
with no room in scope, that is a bug that would otherwise silently read the wrong
shard and return an empty page. Raise.

```python
raise ShardRoutingError(
    "Message query with no room in scope — wrap it in room_scope()"
)
```

Loud in development beats "why is scrollback empty for 25% of rooms" in
production.

### Migrations across N databases

`migrate` runs against one database at a time. `allow_migrate` decides what is
allowed to land where, and getting it wrong leaves `django_migrations` claiming
success on a table that does not exist:

```bash
python manage.py migrate --database=default
for s in shard0 shard1 shard2 shard3; do
    python manage.py migrate --database=$s
done
```

`allow_migrate` must return `True` for the message table **only** on shard
aliases, `True` for everything else **only** on `default`, and `False` for
`replica` (Module 13's rule, still in force). The lab writes all three branches
and then breaks each one on purpose.

---

## The cost of scatter-gather, and the Python-specific wall

Some queries can no longer touch one shard. "All my rooms' unread counts" spans
~20 rooms, which after hashing spans up to 4 shards.

The obvious fix is to query the shards concurrently. In Python, "concurrently"
needs a hard look:

| Approach | Concurrency | What it costs |
|----------|-------------|---------------|
| Sequential `for shard in shards: query(shard)` | none | latency = Σ shards |
| `asyncio.gather` of `database_sync_to_async` calls | threadpool | **burns N of your ~12 threadpool slots**, and the ORM is still sync |
| `asyncio.gather` of raw **psycopg 3 async** connections | true asyncio | no ORM; you write the SQL |
| A process pool | true parallelism | a process hop per query — absurd for a 3 ms query |

The second row is the trap, and it is the Module 01 lesson arriving for the fourth
time. `database_sync_to_async` dispatches onto a bounded threadpool of
`min(32, cpu_count + 4)` threads — **12 on the reference machine**. A
scatter-gather over 4 shards consumes 4 of those 12 for its duration. Sixteen
shards consumes more than the pool has, so the "concurrent" fan-out silently
serializes — *and* every other database call on that worker process queues behind
it, including the ones on the hot send path.

> **A scatter-gather that starves the threadpool does not slow down one query. It
> slows down every query on that worker process.** Concurrency is free; resources
> are not. Module 01 said it, Module 15 measures it on the event loop, and here it
> is at the database.

Pulse's answer is the third row: the scatter-gather path uses **raw `psycopg`
async connections** (`psycopg.AsyncConnection`), outside the ORM, with a bounded
`asyncio.Semaphore` and a **hard deadline**. The ORM keeps the single-shard hot
path, where it never fans out. The lab measures all three.

### The p99 arithmetic nobody does

A scatter-gather is as slow as its **slowest** shard. If each shard's latency is
independent, then for a fan-out over `k` shards:

```
P(gather ≤ t)  =  P(shard ≤ t) ^ k
```

Invert it: the gather's **q-quantile** is each shard's **q^(1/k)-quantile**.

| Shards `k` | The gather's p99 is each shard's… |
|-----------|-----------------------------------|
| 1 | p99 |
| 4 | p99.75 |
| 8 | p99.87 |
| 16 | **p99.94** |
| 64 | **p99.984** |

`0.99^(1/16) = 0.99937`. That is not a metaphor — it is why fan-out reads need a
**deadline and a partial-result path**, not a faster database. At 16 shards you
are sampling the far tail of every shard on every request, and the far tail is
where autovacuum, a checkpoint and a cold page live.

A partial badge count beats a spinner. Decide that *before* you shard, not during
the incident.

---

## The alternative: wide-column

At some point the question stops being "how do we shard Postgres?" and becomes
"is a relational database the right shape for this at all?"

### The chat access pattern

```
99% of reads:  "the last N messages in partition X, in order"
99% of writes: "append to partition X"
Almost never:  a join, an aggregate, or an ad-hoc query
```

That is **exactly** what a wide-column store is built for.

```
Cassandra / ScyllaDB data model:

  PRIMARY KEY ((room_id, bucket), seq)
               └───────┬───────┘  └┬┘
              partition key    clustering key
                     │              │
            selects a node    orders rows WITHIN the partition, on disk
```

- The partition key routes to a node — **no lookup table, no coordinator, no
  `shard_assignment` table, no `contextvars` tripwire.** Everything Part A of the
  lab builds by hand, Scylla does structurally.
- Clustering keys keep rows **physically sorted on disk** in exactly the order you
  read them. "Last 50 messages" is a sequential read of adjacent bytes, not an
  index seek followed by 50 heap fetches.

### Why LSM beats B-tree for this workload

| | Postgres (B-tree + heap) | Cassandra/Scylla (LSM) |
|---|-------------------------|------------------------|
| Write | Find the page, modify, WAL, flush later | **Append to a memtable; flush sorted files** |
| Write amplification | Full-page writes, N index updates | Low at write time; deferred to compaction |
| Read (point) | O(log n), one seek | memtable + N sstables + bloom filters |
| Read (**range in a partition**) | Index scan, then heap fetches | **Sequential read of sorted bytes** |
| Adding nodes | You build Part A of this lab | Built in |

The trade is explicit: LSM defers work from write time to **compaction** time. For
an append-heavy, range-read workload — chat — that is the right side of the trade.
It is also why Scylla's p99.9 is worse than Postgres's: compaction is the deferred
bill, and it comes due while you are serving reads.

### What it costs you

| | Postgres | Cassandra / Scylla |
|---|---------|-------------------|
| Joins | ✅ | ❌ none, ever |
| Transactions | ✅ full ACID | ❌ single-partition LWT only, and slow |
| Ad-hoc queries | ✅ | ❌ **you must know every query before you design the schema** |
| Secondary indexes | ✅ good | ⚠️ exist; generally a trap at scale |
| Consistency | strong | tunable (`ONE` / `QUORUM` / `ALL`) |
| Operational complexity | moderate | **high** — compaction, repair, tombstones, GC grace |
| `COUNT(*)` | ✅ | ❌ times out |
| Django integration | first-class ORM, migrations, admin | **none** — `django-cassandra-engine` exists and you should not use it |

That last row deserves its own paragraph, because it is the Django-specific cost.
Cassandra has no Django ORM backend worth running: `django-cassandra-engine` maps a
relational ORM onto a non-relational store, which means it lets you write queries
CQL cannot serve and then fails at runtime. The honest integration is the
**DataStax Python driver directly**, in a repository module, with hand-written
prepared statements — which is exactly what Module 12 already concluded for the
message hot path on Postgres. You lose migrations, the admin, and `makemigrations`
telling you the schema drifted.

**"You must know every query before you design the schema"** is the real cost. In
Cassandra you build one table *per query pattern* and write the same data to each.
A new product feature that needs a new access pattern is a new table and a
backfill, not a new index.

### Tombstones: the classic footgun

A delete in an LSM store writes a **tombstone**, not a removal. Until compaction
runs (after `gc_grace_seconds`, default 10 days), reads must scan tombstones to
know what to skip.

```
SELECT * FROM messages WHERE room_id='room.7' AND bucket=2955 LIMIT 50;
  → reads 50 live rows... and 400,000 tombstones
  → ReadTimeout
```

Queue-like patterns — write, read, delete — are pathological in Cassandra for
exactly this reason. Chat is naturally append-only, which is why it fits. But
note what that implies for Pulse: Module 12's **soft delete** (`deleted_at`, and a
partial index that skips deleted rows) is not a stylistic choice in a wide-column
store, it is mandatory. A hard delete of moderated messages would build a
tombstone field in front of your busiest partitions.

### Why Discord actually moved

Discord published their migration from Cassandra to **ScyllaDB** — a C++
reimplementation of Cassandra with a shard-per-core architecture and no JVM. The
reasons are instructive because none of them are "the data model was wrong":

- **GC pauses.** Cassandra's JVM produced multi-second p99s. Scylla has no GC.
- **Compaction could not keep up** on their hottest partitions, so reads scanned
  ever more sstables.
- **Hot partitions.** One enormous channel maps to one partition on one node.

That last one is the lesson that transfers, and it is the one you can reproduce on
a laptop: **the partition key is your only load-balancing mechanism, and a single
hot key cannot be split by any amount of adding nodes.** Which is why the bucket
goes into the key:

```
PRIMARY KEY ((room_id, bucket), seq)
```

where `bucket` is a time window. A busy room's data spreads across many
partitions; reads target the buckets they need.

> **Shard-per-core, and why you should recognize it.** Scylla runs one thread per
> core, each owning a slice of the data, sharing nothing. That is the same shape
> as Pulse's own deployment model — one Uvicorn worker process per core, no shared
> state, Redis to cross the boundary. Module 01's GIL story and Scylla's
> architecture are the same answer to the same problem, reached from opposite
> directions.

---

## The honest recommendation for Pulse

**Stay on Postgres, sharded by room, with logical shards.**

1. Partitioning plus retention (Module 13) removes most of the pressure: 74 TB/year
   becomes 18.4 TB live.
2. Postgres does several hundred thousand inserts/second on real hardware — above
   Pulse's target with room to spare, and Part E shows sharded Postgres and
   single-node Scylla within 30% of each other on the write path anyway.
3. You keep transactions (the Module 13 outbox **requires** them), joins, ad-hoc
   queries, `makemigrations`, the admin, and an operational model your team knows.
4. The idempotency check — the thing Module 05, 09 and 10 all rest on — is nearly
   free in Postgres and expensive in Cassandra. Part E measures it, and it is the
   most important number in the module.
5. Cassandra/Scylla is right at a scale where you have people who operate it.
   **Adopting it early buys a ceiling you do not need at the cost of flexibility
   you do.**

The lab builds both so you can compare them with numbers rather than opinions.

---

## What's next

The lab implements logical sharding as a Django DB router, migrates a live shard
under load, hits the threadpool wall with scatter-gather and then fixes it, models
the same data in ScyllaDB, manufactures a hot partition and repairs it with a
bucket key, and benchmarks the two stores head to head.

See you in [`lab.md`](./lab.md).
