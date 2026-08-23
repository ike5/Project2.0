# Module 14 — Sharding & Wide-Column

**Goal:** Scale writes past one machine — and understand why the chat companies
you've heard of ultimately left relational databases for wide-column stores.

⏱️ ~6 hours · **Prerequisites:** Modules 00–13.

---

## Everything you should try before sharding

Sharding is a one-way door. It removes cross-shard joins, cross-shard
transactions, and global ordering, and it makes every future schema change an
orchestrated migration across N databases. Exhaust the alternatives first:

| Option | Buys you | Try before sharding? |
|--------|----------|---------------------|
| **Retention** (Module 13) | Most "we need to shard" is "we need to delete." 74 TB → 18 TB. | ✅ **always first** |
| **Read replicas** | Read scaling. Does nothing for writes. | ✅ |
| **A bigger machine** | A 96-core / 1.5 TB RAM / NVMe box handles far more than people assume. | ✅ genuinely |
| **Tiering to object storage** | 66% cost, no data loss. | ✅ |
| **Sharding** | Write scaling past one machine. | Last |

The honest threshold: **shard when a single well-tuned primary cannot absorb
your write rate, and you have already deleted everything you can.** For Pulse,
Module 12 measured 41k inserts/s on a laptop; a real server does several hundred
thousand. Most products never reach it.

---

## Shard by room, not by user

```
shard = consistent_hash(room_id) mod N
```

This is the single most consequential decision, and it follows from the query
pattern:

| Shard key | "last 50 messages in this room" | "all my rooms' unread counts" |
|-----------|--------------------------------|-------------------------------|
| **`room_id`** | ✅ **one shard** | scatter-gather over ~20 rooms |
| `user_id` | ❌ **scatter-gather over every member** | ✅ one shard |

Chat's dominant, latency-critical query is scrollback. Sharding by room keeps it
on one node. The unread-count query is scatter-gather — but it's cheap (two
integers per room, Module 10) and cacheable.

**Sharding by user would require storing a copy of each message per recipient**,
which is fan-out on write, which is Module 12's rejected design.

---

## What you lose, precisely

| Capability | Status after sharding |
|------------|----------------------|
| Cross-shard `JOIN` | **Gone.** Denormalize, or two round trips. |
| Cross-shard transaction | **Gone.** (2PC exists; it's slow and its failure modes are worse than the problem.) |
| Global `ORDER BY` | Merge in the application. |
| `bigserial` | **Gone.** This is *why* Snowflake exists (Module 12). |
| Global unique constraints | Only unique within a shard. |
| `COUNT(*)` across everything | Scatter-gather, or a maintained counter. |
| Schema migrations | N databases, orchestrated, with a version skew window. |

Note the third and fourth rows: **Module 12's ID decision was made for this
module.** A central sequence cannot span independent databases. Had we used
`bigserial`, sharding would now require rewriting every ID in the system.

---

## Resharding is the hard part

Naive `hash(room_id) mod N` remaps **almost everything** when N changes:

```
N=4 → N=5:  ~80% of rooms move
```

Two standard fixes:

**Consistent hashing** — place nodes on a ring; a key belongs to the next node
clockwise. Adding a node remaps only `1/n` of keys.

**Logical shards (simpler, and what Pulse uses)** — hash to a large fixed number
of *logical* shards, then map logical → physical:

```
room_id ──hash──▶ 4096 logical shards ──lookup──▶ 8 physical databases
                                                   (512 logical each)
```

Growing to 16 databases means **moving 256 logical shards**, not rehashing
anything. The hash function never changes; only a small mapping table does.

```
                 logical shard 0..4095
    ┌─────┬─────┬─────┬─────┬─────┬─────┬─────┬─────┐
    │ 0-  │512- │1024-│1536-│2048-│2560-│3072-│3584-│
    │ 511 │1023 │1535 │2047 │2559 │3071 │3583 │4095 │
    └──┬──┴──┬──┴──┬──┴──┬──┴──┬──┴──┬──┴──┬──┴──┬──┘
       db0   db1   db2   db3   db4   db5   db6   db7
```

This is how Vitess, Citus, and Redis Cluster (16,384 slots) all work. **Pick your
logical shard count once and make it large**; changing it later is the migration
you were trying to avoid.

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

  PRIMARY KEY ((room_id), bucket, seq)
               └─────┬───┘  └────┬───┘
          partition key    clustering keys
                │                │
       selects a node     orders rows WITHIN the partition
```

- The partition key routes to a node — no lookup table, no coordinator.
- Clustering keys keep rows **physically sorted on disk** in exactly the order
  you read them.
- "Last 50 messages" is a sequential read of adjacent bytes. Not an index seek —
  a disk-order scan.

### Why LSM beats B-tree for this workload

| | Postgres (B-tree + heap) | Cassandra/Scylla (LSM) |
|---|-------------------------|------------------------|
| Write | Find the page, modify, WAL, eventually flush | **Append to a memtable; flush sorted files** |
| Write amplification | Full-page writes, index updates | Low on write; deferred to compaction |
| Read (point) | O(log n), one seek | Check memtable + N sstables + bloom filters |
| Read (**range in a partition**) | Index scan then heap fetches | **Sequential read of sorted bytes** |
| Adding nodes | Manual sharding | Built in |

The trade is explicit: LSM defers work from write time to **compaction** time.
For an append-heavy, range-read workload — chat — that's the right side of the
trade.

### What it costs you

| | Postgres | Cassandra |
|---|---------|-----------|
| Joins | ✅ | ❌ none, ever |
| Transactions | ✅ full ACID | ❌ single-partition LWT only, and slow |
| Ad-hoc queries | ✅ | ❌ **you must know every query before you design the schema** |
| Secondary indexes | ✅ good | ⚠️ exist, generally a trap at scale |
| Consistency | strong | tunable (`ONE`/`QUORUM`/`ALL`) |
| Operational complexity | moderate | **high** — compaction, repair, tombstones, GC grace |
| `COUNT(*)` | ✅ | ❌ times out |

**"You must know every query before you design the schema"** is the real cost. In
Cassandra you build one table *per query pattern* and write the same data to each.
A new product feature that needs a new access pattern means a new table and a
backfill.

### Tombstones: the classic footgun

A delete in an LSM store writes a **tombstone**, not a removal. Until compaction
runs (after `gc_grace_seconds`, default 10 days), reads must scan tombstones to
know what to skip.

```
SELECT * FROM messages WHERE room_id = 'x' LIMIT 50;
  → reads 50 live rows... and 400,000 tombstones
  → ReadTimeoutException
```

Queue-like patterns (write, read, delete) are pathological in Cassandra for
exactly this reason. Chat is naturally append-only, which is why it fits.

### Why Discord actually moved

Discord published their migration from Cassandra to **ScyllaDB** (a C++
reimplementation of Cassandra with a shard-per-core architecture and no JVM). The
reasons are instructive because none of them are "the data model was wrong":

- **GC pauses.** Cassandra's JVM produced multi-second p99s. Scylla has no GC.
- **Compaction couldn't keep up** on their hottest partitions, so reads scanned
  ever more sstables.
- **Hot partitions.** One enormous channel maps to one partition on one node.

That last one is the lesson that transfers: **partition key choice is your only
load-balancing mechanism, and a single hot key cannot be split by any amount of
adding nodes.** Which is why the bucket goes in the key:

```
PRIMARY KEY ((room_id, bucket), seq)
```
where `bucket` is a time window. A busy room's data spreads across many
partitions, and reads target the buckets they need.

---

## The honest recommendation for Pulse

**Stay on Postgres, sharded by room, with logical shards.**

Reasoning:
1. Partitioning plus retention (Module 13) removes most of the pressure.
2. Postgres does several hundred thousand inserts/second on real hardware —
   above Pulse's target with room to spare.
3. You keep transactions (the outbox depends on them), joins, ad-hoc queries, and
   an operational model your team already knows.
4. Cassandra/Scylla is the right answer at a scale where you have a dedicated
   team for it. **Adopting it early buys a ceiling you don't need at the cost of
   flexibility you do.**

The lab builds both so you can compare them with numbers rather than opinions.

---

## What's next

The lab implements logical sharding with a routing layer, moves a shard live,
measures scatter-gather cost, then models the same data in ScyllaDB and
benchmarks both.

See you in [`lab.md`](./lab.md).
