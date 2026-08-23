# Module 16 — The Same Workload on Kafka

**Goal:** Run Pulse's fan-out on Kafka, measure it against Redis Streams, and be
able to defend the choice — including the case where Kafka is obviously right and
this course's answer is wrong.

⏱️ ~5 hours · **Prerequisites:** Modules 00–15.

---

## Kafka's model, and why it isn't Redis Streams

Both are append-only logs with consumer groups. The similarity ends quickly.

```
Kafka:                              Redis Streams:
  topic                               one key
    ├── partition 0  [msgs...]          [msgs...]
    ├── partition 1  [msgs...]        (one log per key; you create many keys)
    └── partition 2  [msgs...]
    ordering WITHIN a partition       ordering within the stream
```

| | Redis Streams | Kafka |
|---|--------------|-------|
| Unit of parallelism | one key per room (create freely) | **partitions, fixed per topic** |
| Ordering | per stream | **per partition** |
| Consumer state | PEL, per entry, server-side | **one offset per partition** |
| Durability | memory (+ optional AOF) | **disk, replicated** |
| Retention | trim by count/time | **time or size, per topic** |
| Rebalance | none | **stop-the-world reassignment** |
| Cost of a "topic" | ~nothing (a key) | **real** — files, memory, controller metadata |

That last row is the crux for chat.

---

## The partition-count problem

Redis Streams gave every room its own stream — `room:{7}:stream`. Creating a
million rooms creates a million keys, which costs approximately nothing.

**Kafka cannot do this.** A partition is a set of files on every replica, plus
memory in the broker and metadata in the controller. Practical limits:

| Partitions per cluster | Reality |
|-----------------------|---------|
| ~4,000 | comfortable |
| ~20,000 | fine on KRaft, needs tuning |
| ~200,000 | possible on KRaft, painful |
| 1,000,000 | **no** |

So you cannot give each room a partition. You must **hash rooms onto a fixed
number of partitions**:

```java
new ProducerRecord<>("chat-messages", roomId, payload)
//                                    ^^^^^^ key -> partition = hash(key) % numPartitions
```

Consequences, all of which matter:

- **Ordering is preserved per room** (same key → same partition). ✅ This is the
  guarantee you need, and Kafka gives it cleanly.
- **Rooms share partitions.** A hot room's traffic is interleaved with 5,000
  other rooms' in the same log. A slow consumer on that partition delays
  everyone in it — **head-of-line blocking at the room level**.
- **You cannot replay one room** without scanning its whole partition and
  filtering.
- **Partition count is nearly immutable.** Increasing it **changes the
  key→partition mapping**, so a room's history is split across two partitions and
  ordering breaks across the boundary. Kafka lets you add partitions; it does not
  let you do so safely for keyed ordering.

---

## Fan-out shape

Module 09 chose **one consumer group per node**, so every node receives every
entry. On Kafka that means:

```
topic chat-messages (64 partitions)
   ├── group "node-a"  -> node-a consumes all 64
   ├── group "node-b"  -> node-b consumes all 64
   └── group "node-c"  -> node-c consumes all 64
```

Every node reads the **entire topic**. At 8 nodes that's 8× the read bandwidth —
the same amplification Module 09 measured for Streams, with the same shape.

Kafka handles this better than Redis for one specific reason: **it's on disk, and
the page cache serves sequential reads extremely well.** Eight consumers reading
the same recent offsets hit the same pages. Redis paid CPU on one thread per
read; Kafka pays page-cache hits and `sendfile`.

**This is Kafka's genuine architectural advantage for high-fan-out**, and the lab
measures it.

---

## Rebalances: the operational cost people underestimate

When a consumer joins, leaves, or is deemed dead, the group **rebalances**:
partitions are revoked from everyone and reassigned. Under the default eager
protocol, **consumption stops entirely** for the duration.

```
node-c's pod is restarted
  → group coordinator triggers rebalance
  → ALL consumers revoke ALL partitions
  → reassignment
  → consumers resume
  → 2-10 seconds of no consumption, cluster-wide
```

For a chat backbone, that's 2–10 seconds where no messages are delivered on any
node. During a rolling deploy of 8 nodes, that's 8 rebalances.

Mitigations, and you need all three:

```properties
partition.assignment.strategy=org.apache.kafka.clients.consumer.CooperativeStickyAssignor
group.instance.id=node-a                  # static membership: no rebalance on restart
session.timeout.ms=45000
max.poll.interval.ms=300000
```

- **Cooperative rebalancing** revokes only the partitions that must move, so most
  consumers keep working.
- **Static membership** (`group.instance.id`) means a restarting consumer
  reclaims its own partitions without a rebalance at all, as long as it returns
  within `session.timeout.ms`.

With both, a rolling restart causes **zero** rebalances. Without them it causes
eight. The lab measures both.

---

## Delivery semantics

Same shape as Module 09, different mechanics:

```java
// AT-MOST-ONCE: commit before processing
consumer.commitSync();
process(records);

// AT-LEAST-ONCE: commit after processing   <-- what chat wants
process(records);
consumer.commitSync();
```

Kafka's **exactly-once semantics** (`transactional.id`, `isolation.level=read_committed`)
makes the offset commit and the output write atomic **within Kafka**. That's real
and useful for stream processing (read topic A, write topic B).

It does **not** help Pulse, because our output is a WebSocket write and a Postgres
row — neither of which participates in a Kafka transaction. Cross-system, you are
back to at-least-once plus idempotent processing, which is what Module 05 built.

> Same conclusion as Module 09, reached by a different route: **exactly-once is a
> property of your consumer, not a feature you buy.**

---

## Durability

This is where Kafka is unambiguously stronger.

```properties
acks=all
min.insync.replicas=2
replication.factor=3
```

A message acknowledged with `acks=all` is on disk on at least 2 of 3 brokers.
Redis Streams with AOF `everysec` can lose a second; with persistence off
(Module 08's choice for the fan-out instance) it loses everything on restart.

Module 09 measured that: **57 of 200 messages lost when Redis was killed and
restarted.** Kafka loses zero.

Pulse closed that gap with the outbox (Module 13) — Postgres is the durable
record and the relay republishes. **Kafka would let you delete that machinery.**
That's a genuine simplification and it belongs in the comparison.

---

## When Kafka is obviously right

Be honest about this, because it's often:

| Signal | Why Kafka |
|--------|-----------|
| **You need replay from arbitrary points** — reprocessing, backfills, new consumers reading history | 7-day (or infinite) retention on disk; Redis Streams' trim window is minutes |
| **Multiple independent consumers** — search indexing, analytics, moderation, ML | Add a consumer group; it gets the full history, no impact on others |
| **Cross-team event backbone** | It's the industry default; other teams already consume from it |
| **Durability is a compliance requirement** | Replicated, on disk, auditable |
| **Very high sustained throughput** | Sequential disk + `sendfile` beats in-memory when the working set exceeds RAM |
| **You already run it** | The marginal cost is near zero |

That last row decides more real architectures than any benchmark.

## When Redis Streams is right

| Signal | Why Redis |
|--------|-----------|
| **You already run Redis** for other state | No second stateful system |
| **A stream per entity** (per room, per user) | Millions of keys are free; millions of partitions are impossible |
| **Latency matters more than durability** | In-memory, microsecond appends |
| **Replay window is minutes, not days** | Trim is the point, not a limitation |
| **Small team** | Redis's operational surface is a fraction of Kafka's |

---

## What's next

The lab runs Pulse's fan-out on Kafka in KRaft mode, measures it against Redis
Streams on latency, throughput, durability and resource cost, triggers rebalances
and measures the outage, then fixes them with cooperative and static membership.

See you in [`lab.md`](./lab.md).
