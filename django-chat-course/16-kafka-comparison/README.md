# Module 16 — The Same Fan-Out on Kafka

**Goal:** Run Pulse's fan-out on Kafka in KRaft mode, measure it against the
Redis Streams design from [Module 09](../09-redis-streams-delivery/), and be able
to defend the choice — including the case where Kafka is obviously right and this
course's answer is wrong.

⏱️ ~5 hours · **Prerequisites:** Modules 00–15.

> The Django/Python twin of
> [`spring-boot-chat-course/16-kafka-comparison`](../../spring-boot-chat-course/16-kafka-comparison/).
> Kafka is Kafka, so the broker-side conclusions match. Two things do not: the
> **client** (Python has three Kafka libraries and they disagree with each other
> about something load-bearing), and the **fan-out topology**, because Module 09
> established that Pulse's unit of consumption is a **worker process**, not a
> machine — and 24 consumer groups behave very differently from 3.

---

## Kafka's model, and why it is not Redis Streams

Both are append-only logs with consumer groups and offsets. The similarity ends
faster than people expect.

```
Kafka:                              Redis Streams:
  topic                               one key per room
    ├── partition 0  [msgs...]          room:{7}:stream    [msgs...]
    ├── partition 1  [msgs...]          room:{42}:stream   [msgs...]
    └── partition 2  [msgs...]          room:{general}:... [msgs...]
    ordering WITHIN a partition       ordering within the stream
```

| | Redis Streams | Kafka |
|---|--------------|-------|
| Unit of parallelism | **one key per room**, create freely | **partitions, fixed per topic** |
| Ordering guarantee | per stream (= per room) | **per partition** (= per ~15,000 rooms) |
| Consumer state | the **PEL**, per entry, server-side | **one offset per partition**, per group |
| Recovering a dead consumer | `XAUTOCLAIM` | rebalance, or static membership |
| Durability | memory (+ optional AOF) | **disk, replicated, `acks=all`** |
| Retention | `MAXLEN ~`/`MINID`, minutes | **hours or days, per topic** |
| Rebalance | does not exist | **a stop-the-world event you must engineer around** |
| Cost of "one log per entity" | ~nothing (a key) | **real** — files, memory, controller metadata |

That last row is the crux for chat, and it is where the module starts.

---

## The partition-count problem

Module 09 gave every room its own stream — `room:{7}:stream`. A million rooms is
a million keys, which in Redis costs approximately nothing.

**Kafka cannot do this.** A partition is a directory of segment files on every
replica, plus memory in each broker, plus metadata in the controller. Practical
ceilings:

| Partitions per cluster | Reality |
|-----------------------|---------|
| ~4,000 | comfortable |
| ~20,000 | fine on KRaft, needs tuning |
| ~200,000 | possible on KRaft, painful |
| 1,000,000 | **no** |

So rooms must be **hashed onto a fixed number of partitions**:

```python
producer.send("chat-messages", key=room.key.encode(), value=payload)
#                              ^^^^^^^^^^^^^^^^^^^^^
#                              partition = hash(key) % num_partitions
```

You have seen this exact pattern twice already, and it is worth naming:

| System | Buckets | Bucket → machine |
|--------|---------|-----------------|
| Pulse shards (Module 14) | 4,096 logical shards | `shard_assignment` table |
| Redis Cluster (Module 18) | 16,384 slots | the cluster's slot map |
| **Kafka** | **`num_partitions`** | the partition leader map |

> **Hash to a fixed, large-ish number of buckets. Map buckets to machines. Move
> buckets, never rehash.** Three systems, one idea. The difference is the bucket
> count: 4,096 and 16,384 are large enough that "one bucket per entity" was never
> the plan, but they are also cheap. **Kafka's buckets are expensive**, so the
> count is small, so many rooms share one.

Consequences, all of which matter:

- **Ordering is preserved per room** (same key → same partition). ✅ Exactly the
  guarantee Module 10 needs, and Kafka gives it cleanly.
- **Rooms share partitions.** At 64 partitions and a million rooms, ~15,625 rooms
  share a log. A slow consumer on that partition delays every one of them:
  **head-of-line blocking at the room level**, which per-room streams did not have.
- **You cannot replay one room** without reading its whole partition and
  filtering. Redis replayed one room with one `XRANGE`.
- **Partition count is effectively immutable.** Kafka lets you *add* partitions;
  it does not let you do so safely for keyed ordering, because adding them
  **changes the key→partition mapping**, so a room's history is split across two
  partitions and ordering breaks across the boundary. There is no equivalent of
  Module 14's logical-shard indirection.

### Sizing 64, honestly

Partition count governs producer parallelism and per-partition throughput, and it
caps consumer parallelism **within a group**. Pulse's fan-out topology (below)
gives every worker process its own group, so partition count does not cap consumer
scaling at all — it caps producer batching and per-partition write rate.

64 is comfortable for three brokers. The challenge makes you justify it against
throughput per partition, retention size and rebalance duration rather than by
reciting a rule of thumb.

---

## Fan-out shape — and the Python twist, again

Module 09 chose **one consumer group per worker process**, so that every worker
receives every entry. Not per node: per *process*. Module 01's reason, restated
one final time — one async worker process pins one core, you run one per core, and
the `InMemoryChannelLayer` does not span them.

On Kafka that gives you **Topology A**:

```
topic chat-messages (64 partitions)
   ├── group "node-a-0" ─▶ node-a worker 0 consumes all 64
   ├── group "node-a-1" ─▶ node-a worker 1 consumes all 64
   │   ...
   └── group "node-c-7" ─▶ node-c worker 7 consumes all 64

3 nodes × 8 workers = 24 groups × 64 partitions = 1,536 partition assignments
```

Every worker reads the **entire topic**. At 24 worker processes that is 24× the
read bandwidth — the same amplification Module 09 measured for Streams, with the
same shape, because it is the same design.

**Kafka handles this dramatically better than Redis, for one specific reason:**
the data is on disk and the **page cache serves sequential reads extremely well**.
Twenty-four consumers reading the same recent offsets hit the same pages, and
Kafka serves them with `sendfile` — no user-space copy, no per-read CPU on a
single thread. Redis paid CPU on **one** thread for every read; Module 09's read
amplification is what saturates it.

This is Kafka's genuine architectural advantage for high fan-out, and Part D of
the lab measures exactly where the two curves cross.

There is a second, quieter consequence of Topology A that people miss: **a group
with exactly one member never rebalances.** There is nothing to reassign. Twenty
-four single-member groups make Kafka's most notorious operational problem
disappear — at the cost of 24× the read bandwidth and 24× the `__consumer_offsets`
traffic.

**Topology B** is the alternative, and the lab builds both:

```
topic chat-messages (64 partitions)
   └── group "pulse-fanout" ─▶ 24 consumers share 64 partitions (2-3 each)

   each consumer then re-fans-out over the CHANNEL LAYER to the workers
   that actually hold the sockets for those rooms
```

1× read amplification, an extra hop, sticky room→worker affinity you now have to
maintain — **and rebalances, on every deploy.** Which is the next section.

---

## Rebalances: the operational cost people underestimate

When a consumer joins, leaves, or is deemed dead, the group **rebalances**:
partitions are revoked and reassigned. Under the default eager protocol,
**consumption stops entirely** for the duration.

```
node-c is restarted
  → group coordinator triggers a rebalance
  → ALL consumers revoke ALL partitions
  → reassignment
  → consumers resume
  → 2–10 seconds of no consumption, cluster-wide
```

For a chat backbone that is seconds during which no message is delivered on any
node. A rolling deploy of 3 nodes × 8 workers is **24 rebalances** if you are
naive about it.

Three mitigations, and in Topology B you need all three:

```python
consumer = AIOKafkaConsumer(
    "chat-messages",
    group_id="pulse-fanout",
    group_instance_id=f"{HOSTNAME}-{os.environ['PULSE_WORKER_ID']}",   # static
    partition_assignment_strategy=[CooperativeStickyAssignor],
    session_timeout_ms=45_000,
    max_poll_interval_ms=300_000,
    enable_auto_commit=False,
)
```

- **Cooperative rebalancing** revokes only the partitions that must move, so most
  consumers keep working through it.
- **Static membership** (`group.instance.id`) lets a restarting consumer reclaim
  *its own* partitions with no rebalance at all, provided it returns within
  `session.timeout.ms`.
- **A long `max.poll.interval.ms`**, because a consumer that takes too long
  between polls is declared dead — and "too long" includes a slow database write,
  which is exactly what your fan-out does.

> **`group.instance.id` must be unique per worker PROCESS, and stable across
> restarts.** `f"{HOSTNAME}-{PULSE_WORKER_ID}"` — the same `PULSE_WORKER_ID` env
> var Module 12's Snowflake generator uses for its worker-id bits and Module 14's
> fleet fencing uses for its identity. One identity per process, reused rather
> than reinvented, three modules apart. If you derive it from a PID or a UUID it
> changes on restart and static membership does nothing.

With cooperative + static, a rolling restart causes **zero** rebalances. Without
them it causes 24. Part E measures both.

---

## Python has three Kafka clients and they disagree

This is the module's Django/Python-specific content, and one of the disagreements
is a correctness bug.

| Library | Under the hood | Async? | Notes |
|---------|---------------|--------|-------|
| **`confluent-kafka`** | **librdkafka (C)** | ❌ blocking | Fastest by a wide margin. Its `poll()` blocks, which in an async consumer is Module 15's cardinal sin. |
| **`aiokafka`** | pure Python | ✅ native asyncio | Idiomatic in a Channels consumer. Pays per-message Python decode cost. |
| `kafka-python` | pure Python | ❌ | Effectively unmaintained; do not start here. |

The tension is real and it has no free answer:

- `confluent-kafka` is 2–4× faster and **blocks the event loop**. Running its poll
  loop in a thread reintroduces the bounded-threadpool problem from Module 14's
  scatter-gather; running it in a separate process means an extra IPC hop to reach
  the sockets.
- `aiokafka` never blocks the loop and is slower per message, in a fan-out path
  where per-message cost is exactly what Module 06 identified as Python's ceiling
  (the ~150k out msg/s knee versus the JVM's ~450k).

Pulse uses **`aiokafka` for the consumer** (it lives inside the event loop that
owns the sockets) and **`confluent-kafka` for the producer** driven from a
dedicated thread with a queue (the producer is fire-and-forget and batches, so one
thread hop per batch is amortized). Part B measures both ways round.

### The partitioner bug

**`confluent-kafka` and `aiokafka` do not partition the same way by default.**

| Client | Default partitioner |
|--------|--------------------|
| Java producer | `murmur2` (the `DefaultPartitioner`) |
| **`aiokafka`** | murmur2 — Java-compatible |
| **`confluent-kafka` / librdkafka** | **`consistent_random`** — CRC32-based |

Two producers, same room key, **different partitions**. And since Kafka's ordering
guarantee is *per partition*, a room whose messages are produced by both clients
has **no ordering guarantee at all** — the one thing you adopted Kafka for.

The fix is one line, and it must be in your config from the first commit:

```python
Producer({"bootstrap.servers": ..., "partitioner": "murmur2_random"})
```

Part B has you produce the same key with both clients and read back the partition
each landed on. The lesson generalizes past Kafka: **when a hash function is part
of a wire contract, pin it explicitly.** Module 14 said the same thing about
`zlib.crc32` versus Python's randomized `hash()`.

---

## Delivery semantics — the same three, different mechanics

Module 10's table is the vocabulary; nothing here changes it.

```python
# AT-MOST-ONCE: commit before processing
await consumer.commit()
await process(batch)

# AT-LEAST-ONCE: commit after processing        <-- what chat wants
await process(batch)
await consumer.commit()
```

Kafka's **exactly-once semantics** (`transactional.id`,
`isolation.level=read_committed`) makes the offset commit and the output write
atomic **within Kafka**. That is real and useful for stream processing: read topic
A, write topic B, commit both or neither.

It does **not** help Pulse, because Pulse's output is a WebSocket frame and a
Postgres row, and neither participates in a Kafka transaction. Cross-system you
are back to at-least-once plus idempotent processing — which is what Module 05's
`client_id` and Module 12's `UNIQUE (room_id, client_id)` already give you.

> Same conclusion as Module 09, reached by a different route: **exactly-once is a
> property of your consumer, not a feature you buy.** Kafka's version is the same
> trick with better machinery, and the machinery stops at Kafka's boundary.

### Consumer lag is the metric Redis never gave you

```bash
kafka-consumer-groups.sh --bootstrap-server localhost:9092 \
  --describe --group node-a-0
```
```
TOPIC          PARTITION  CURRENT-OFFSET  LOG-END-OFFSET  LAG
chat-messages  0          8412991         8413004         13
chat-messages  1          8409877         8412340         2463      <-- !!
```

`LAG` is "how many messages behind is this consumer, right now, on this
partition." It is the single best health signal a log-based fan-out has, it is one
command, and **Redis Streams has no equivalent.** `XPENDING` tells you what is
un-acked, not how far behind you are; you can compute lag from `XINFO GROUPS`'s
`entries-read` against `XLEN`, but it is per-key, so at a million rooms it is a
million round trips.

This is a genuine, unglamorous, day-two advantage for Kafka and it belongs in the
comparison.

---

## Durability: where Kafka is unambiguously stronger

```
acks=all
min.insync.replicas=2
replication.factor=3
```

A message acknowledged with `acks=all` is on disk on at least 2 of 3 brokers.
Redis Streams with AOF `everysec` can lose a second; with persistence off — which
is what Module 08 chose for the fan-out instance, deliberately — a restart loses
everything.

Module 09 measured that: **57 of 200 messages lost when Redis was killed and
restarted.** Kafka loses zero.

Pulse closed that gap with the **transactional outbox** (Module 13): Postgres is
the durable record and the Celery relay republishes anything the stream never
acknowledged. That machinery is a table, a relay task, a pruning job, and
`SKIP LOCked` semantics you had to reason about. **Kafka would let you delete it.**

That is a genuine simplification and it must be in the comparison. It is also not
free: you would be trading a Postgres table you already run for a three-broker
cluster you do not.

### ISR, and the failure mode you should rehearse

`min.insync.replicas=2` means: if fewer than 2 replicas are in-sync, **the
producer's write is rejected** rather than accepted-and-maybe-lost.

```
NOT_ENOUGH_REPLICAS: Messages are rejected since there are fewer in-sync
replicas than required.
```

That is the correct behaviour and it will page you. Kill two of three brokers and
Pulse **stops accepting messages** — which is Module 10's "prefer a clear failure
over a silent loss," expressed as a broker config. Part F does it.

The subtle part: `acks=all` means "all **in-sync** replicas", not "all replicas."
With `min.insync.replicas=1` and two replicas lagging, `acks=all` acknowledges a
write that exists on **one** disk. `acks=all` alone is not durability; `acks=all`
**plus** `min.insync.replicas ≥ 2` is.

---

## When Kafka is obviously right

Be honest about this, because it is often:

| Signal | Why Kafka |
|--------|-----------|
| **Replay from arbitrary points** — reprocessing, backfills, a new consumer reading history | Days of retention on disk; Redis Streams' trim window is minutes |
| **Multiple independent consumers** — search indexing, analytics, moderation, ML | Add a consumer group; it gets the full history with no impact on the others |
| **A cross-team event backbone** | It is the industry default; other teams already consume from it |
| **Durability is a compliance requirement** | Replicated, on disk, auditable, with a retention policy you can point at |
| **Very high sustained throughput** | Sequential disk + page cache + `sendfile` beats in-memory once the working set exceeds RAM |
| **You already run it** | The marginal cost is near zero |

That last row decides more real architectures than any benchmark in this course.

## When Redis Streams is right

| Signal | Why Redis |
|--------|-----------|
| **You already run Redis** for other state | No second stateful system to operate, monitor and upgrade |
| **A log per entity** (per room, per user) | A million keys is free; a million partitions is impossible |
| **Latency matters more than durability** | In-memory, microsecond appends |
| **The replay window is minutes, not days** | Trimming is the point, not a limitation |
| **A small team** | Redis's operational surface is a fraction of Kafka's |

Pulse hits five of five. That is the answer, and Part G writes it down with the
numbers behind it.

---

## What's next

The lab stands up Kafka in KRaft mode, produces Pulse's envelopes onto it with
both Python clients (and catches them disagreeing), runs both fan-out topologies,
measures latency, throughput and resource cost against Redis Streams, sweeps the
node count until Redis saturates and Kafka does not, triggers rebalances and then
eliminates them, and kills brokers until writes are correctly refused.

See you in [`lab.md`](./lab.md).
