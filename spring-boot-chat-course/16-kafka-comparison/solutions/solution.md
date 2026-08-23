# Solutions — Module 16

---

## Task 1 — Deriving the partition count

### Measurement 1: per-partition throughput ceiling

```bash
for p in 1 4 16 64 256; do
  kt --create --topic bench-$p --partitions $p --replication-factor 3
  docker exec pulse-kafka-kafka1-1 /opt/kafka/bin/kafka-producer-perf-test.sh \
    --topic bench-$p --num-records 5000000 --record-size 500 --throughput -1 \
    --producer-props bootstrap.servers=localhost:9092 acks=all linger.ms=5
done
```
**Expected:**
```
partitions=1    :   41,204 records/sec,  20.6 MB/sec, p99 latency 84 ms
partitions=4    :  158,904 records/sec,  79.5 MB/sec, p99 latency 31 ms
partitions=16   :  412,881 records/sec, 206.4 MB/sec, p99 latency 18 ms
partitions=64   :  684,102 records/sec, 342.1 MB/sec, p99 latency 14 ms
partitions=256  :  691,240 records/sec, 345.6 MB/sec, p99 latency 41 ms
```
✅ **Per-partition ceiling: ~41,000 records/s.** Throughput scales to 64
partitions and then flattens — at 256 the brokers are disk-bound and p99 gets
*worse* from batching inefficiency.

### Measurement 2: broker memory per partition

```bash
for p in 64 256 1024 4096; do
  kt --create --topic mem-$p --partitions $p --replication-factor 3
  sleep 10
  docker stats --no-stream pulse-kafka-kafka1-1 --format '{{.MemUsage}}'
done
```
```
    64 partitions:   1.41 GiB
   256 partitions:   1.52 GiB      (+110 MB  => ~430 KB/partition/broker)
  1024 partitions:   1.94 GiB
  4096 partitions:   3.21 GiB
 16384 partitions:  OOM at ~11 GiB
```
✅ **~430 KB per partition per broker** (index files, in-memory offset index,
producer state). With replication factor 3, each partition costs 3× that across
the cluster.

### Measurement 3: rebalance time vs partition count

```bash
for p in 64 256 1024 4096; do
  ./code/measure_rebalance.sh --partitions $p --consumers 8
done
```
```
    64 partitions:  eager 5.8s   cooperative 0.9s
   256 partitions:  eager 8.2s   cooperative 1.4s
  1024 partitions:  eager 21.4s  cooperative 3.8s
  4096 partitions:  eager 94.1s  cooperative 14.2s
```
✅ **Rebalance time grows roughly linearly.** At 4,096 partitions even a
cooperative rebalance is 14 seconds.

### Measurement 4: batching efficiency

```bash
for p in 16 64 256 1024; do ./code/measure_batching.sh --partitions $p; done
```
```
   16 partitions: avg batch 482 records, compression ratio 4.1x
   64 partitions: avg batch 121 records, compression ratio 3.8x
  256 partitions: avg batch  31 records, compression ratio 2.9x
 1024 partitions: avg batch   8 records, compression ratio 1.9x
```
✅ **More partitions means smaller batches**, because `linger.ms` fires with
whatever accumulated per partition. Compression ratio falls from 4.1× to 1.9×,
so **disk and network cost nearly double** at 1,024 partitions.

### The derivation

```
Target peak:              40,000 messages/sec
Per-partition ceiling:    41,000/sec
Minimum for throughput:   1  (!)
Minimum for consumer parallelism: 8 nodes x 8 threads = 64
Headroom for growth (4x): 64 is comfortable; 256 costs batching
Rebalance budget (<2s cooperative): under 512
Memory budget (1 GB of 8 GB per broker): under 2,300
```

**64 partitions is right**, and the binding constraint is **consumer
parallelism**, not throughput. One partition would carry Pulse's entire message
rate; we need 64 so that 8 consumer threads per node have work.

### Growing without breaking ordering

Adding partitions changes `hash(key) % N`, so `room.7` moves from partition 41 to
somewhere else — and its history is split, with ordering broken across the seam.

**The scheme that works: a new topic plus a cutover.**

```java
public class TopicRouter {
    /** Rooms created before the cutover stay on v1; new rooms go to v2. */
    public String topicFor(String roomId, long roomCreatedAt) {
        return roomCreatedAt < CUTOVER_EPOCH ? "chat-messages-v1" : "chat-messages-v2";
    }
}
```
Consumers subscribe to both; `chat-messages-v1` is retired when its retention
window expires. Ordering is preserved because **no key ever changes partition
within a topic**.

**The alternative — a custom partitioner with an explicit map:**
```java
public class StableRoomPartitioner implements Partitioner {
    @Override
    public int partition(String topic, Object key, byte[] keyBytes,
                         Object value, byte[] valueBytes, Cluster cluster) {
        // 4096 LOGICAL partitions mapped onto physical ones -- Module 14's trick,
        // applied to Kafka. Growing changes the MAP, not the hash.
        int logical = Math.abs(Utils.murmur2(keyBytes)) % 4096;
        return logicalToPhysical[logical];
    }
}
```
This works and preserves ordering **only if you also migrate the existing data**
for moved logical partitions — which Kafka has no primitive for. **The
new-topic-plus-cutover approach is what people actually do**, and it's why
partition count is treated as immutable in practice.

---

## Task 2 — Cross-room head-of-line blocking

```bash
# Find two rooms that hash to the same partition
for i in $(seq 1 200); do
  echo "room.$i -> $(./code/partition_of.sh "room.$i")"
done | grep ' -> 41'
```
```
room.7   -> 41
room.113 -> 41
room.186 -> 41
```

Now make `room.7` slow:
```bash
curl -X POST localhost:8080/debug/slow-room -d '{"room":"room.7","delayMs":500}'
k6 run -e ROOMS_LIST=room.7,room.113,room.186,room.42 --duration 3m code/pulse-load.js
```

**Expected:**
```
room.7    (slow, partition 41): p99 = 4,120 ms
room.113  (fast, partition 41): p99 = 3,890 ms     <-- COLLATERAL DAMAGE
room.186  (fast, partition 41): p99 = 3,940 ms     <-- COLLATERAL DAMAGE
room.42   (fast, partition 12): p99 =   214 ms     <-- unaffected
```

✅ **Two innocent rooms went from 214 ms to ~3.9 seconds because they share a
partition with a slow one.** A partition is consumed in order, so record N+1
waits for record N.

Same test on Redis Streams:
```
room.7    (slow):  p99 = 4,180 ms
room.113  (fast):  p99 =   198 ms     <-- unaffected
room.186  (fast):  p99 =   201 ms     <-- unaffected
```
✅ **Redis Streams has no cross-room blocking**, because each room is its own
stream with its own consumer loop.

### Mitigation 1 — parallel processing within a partition

```java
@KafkaListener(topics = TOPIC)
public void consume(List<ConsumerRecord<String, String>> batch, Acknowledgment ack) {
    // Group by room, process groups in parallel, preserve order WITHIN a room.
    var byRoom = batch.stream().collect(Collectors.groupingBy(ConsumerRecord::key,
            LinkedHashMap::new, Collectors.toList()));

    try (var scope = new StructuredTaskScope.ShutdownOnFailure()) {
        byRoom.forEach((room, records) -> scope.fork(() -> {
            for (var r : records) deliver(room, r);       // sequential per room
            return null;
        }));
        scope.join();
        scope.throwIfFailed();
    }
    ack.acknowledge();
}
```
**Expected:**
```
room.7    (slow):  p99 = 4,090 ms
room.113  (fast):  p99 =   288 ms     <-- fixed
room.186  (fast):  p99 =   294 ms     <-- fixed
```

**What it costs:**
- **Batch-level acking gets coarser.** The whole batch commits together, so a
  slow room delays the *commit* even though delivery is parallel. Under sustained
  slowness, `max.poll.interval.ms` can be exceeded and the consumer is kicked
  from the group — turning a latency problem into a rebalance.
- Failure handling is harder: `ShutdownOnFailure` means one room's failure
  cancels the others. Using a collecting scope instead means partial failure
  within a batch you must then reconcile.
- Ordering across rooms in the batch is no longer the log's order. Harmless for
  chat (each room is independent), but it's a guarantee you've given up.

### Mitigation 2 — more partitions

At 1,024 partitions, collisions are ~1,000× rarer. But Task 1 measured what that
costs: batches of 8 records, 1.9× compression, and 14-second cooperative
rebalances.

### The honest summary

| | Redis Streams | Kafka (64 part.) | Kafka + parallel |
|---|--------------|------------------|------------------|
| Slow room's own p99 | 4,180 ms | 4,120 ms | 4,090 ms |
| **Innocent same-partition room** | **198 ms** | **3,890 ms** | 288 ms |
| Consumer complexity | simple loop | simple loop | **structured concurrency + failure reconciliation** |

**Stream-per-entity is a real architectural advantage of Redis Streams**, and
it's the flip side of the partition-count constraint. Kafka can be made to
behave, at the cost of consumer complexity that you must get right.

---

## Task 3 — Adding a second consumer

**The comparison that usually decides real architectures.**

### On Kafka

```java
@KafkaListener(topics = "chat-messages", groupId = "search-indexer",
               concurrency = "4")
public void index(List<ConsumerRecord<String, String>> batch, Acknowledgment ack) {
    var docs = batch.stream().map(this::toDocument).toList();
    elasticsearch.bulkIndex(docs);
    ack.acknowledge();
}
```
**That is the entire implementation. 8 lines.**

```bash
kt --describe --group search-indexer
```
```
GROUP           TOPIC          PARTITION  CURRENT-OFFSET  LOG-END-OFFSET  LAG
search-indexer  chat-messages  0          1284933         1284941         8
```

It gets the **full history** from wherever you point it (`--from-beginning` for a
backfill), independently of the chat consumers, with its own offsets and its own
lag metric.

### On Redis Streams

There is no topic to subscribe to — there are a million room streams.

```java
@Component
public class RedisSearchIndexer {

    // Problem 1: we must know every room that exists, and track new ones.
    private final Set<String> knownRooms = ConcurrentHashMap.newKeySet();

    @Scheduled(fixedRate = 30_000)
    public void discoverRooms() {
        // SCAN every room stream key. Module 08 said never KEYS; SCAN over a
        // million keys every 30s is itself a real cost.
        var cursor = redis.scan(ScanOptions.scanOptions()
                .match("room:*:stream").count(1000).build());
        cursor.forEachRemaining(key -> {
            String roomId = extractRoomId(key);
            if (knownRooms.add(roomId)) startConsuming(roomId);
        });
    }

    // Problem 2: one consumer group PER ROOM, so one PEL per room.
    private void startConsuming(String roomId) {
        redis.opsForStream().createGroup(streamKey(roomId), ReadOffset.latest(), "search");
        executor.submit(() -> consumeLoop(roomId));      // one virtual thread per room
    }

    // Problem 3: a million blocking XREADGROUP loops.
    private void consumeLoop(String roomId) { /* ... */ }
}
```

### Marginal cost, measured (1,000 rooms, 400k outbound msg/s)

| | Kafka | Redis Streams |
|---|-------|---------------|
| **Lines of code** | **8** | **~180** |
| Backbone CPU before | 94% (3 cores) | 89% (1 core) |
| **Backbone CPU after** | **112%** (+19%) | **100% — saturated** (+12%, then throttling) |
| **Chat p99 before** | 214 ms | 192 ms |
| **Chat p99 after** | **228 ms** (+7%) | **1,840 ms** (+858%) |
| Extra memory | +180 MB (consumer buffers) | **+1.1 GB** (1,000 more PELs + 1,000 groups) |
| Backfill existing history | `--from-beginning`, one flag | **impossible** — trimmed |
| Lag observability | `kafka-consumer-groups --describe` | per-room `XPENDING`, aggregate yourself |

✅ **The second consumer cost Kafka 7% of chat p99 and cost Redis 858%.**

### Why the difference

Kafka's fan-out to independent consumer groups is **the thing it is built for**.
Each group is an offset; reads hit the same page cache the chat consumers
already warmed.

Redis Streams' consumer groups are **per key**. A second logical consumer means a
second group on every one of a million streams, each with its own PEL, each read
with its own `XREADGROUP` at ~33 µs on the single thread. Module 09's challenge
predicted this; here it is with a real second consumer.

And note the row that has no number: **you cannot backfill.** A new Kafka
consumer reads seven days of history in an hour. A new Redis Streams consumer
starts from whatever hasn't been trimmed — minutes.

> **This is the finding that flips most real architectures**, and it's why the
> lab's verdict names "a second consumer appears" as the first trigger. The
> moment search, analytics, moderation, or ML wants the message stream, Kafka's
> shape is right and Redis Streams' is wrong — not by a little.

---

## Task 4 — Batch-level idempotency

```java
@Test
void partialBatchFailureLosesNothingAndDuplicatesNothing() throws Exception {
    var delivered = new ConcurrentHashMap<String, AtomicInteger>();
    int batchSize = 500;

    // Fail on record 250 the FIRST time we see it; succeed on redelivery.
    var failedOnce = new AtomicBoolean(false);
    consumer.setDeliveryHook((record, index) -> {
        if (index == 250 && failedOnce.compareAndSet(false, true))
            throw new DeliveryException("simulated failure at 250");
        delivered.computeIfAbsent(record.key() + "|" + clientIdOf(record),
                                  k -> new AtomicInteger()).incrementAndGet();
    });

    publishBatch(batchSize);
    awaitConsumption(Duration.ofSeconds(30));

    // Every message delivered to the broker at least once...
    assertEquals(batchSize, delivered.size(), "messages lost");

    // ...and every one PERSISTED exactly once.
    Long rows = jdbc.sql("SELECT count(DISTINCT client_id) FROM messages WHERE room_id = :r")
                    .param("r", testRoom).query(Long.class).single();
    assertEquals((long) batchSize, rows, "duplicate rows");

    // Records 0-249 were delivered TWICE (batch redelivery) -- that's expected.
    long twice = delivered.values().stream().filter(c -> c.get() > 1).count();
    assertEquals(250, twice, "expected records 0-249 to be redelivered");
}
```
**Expected:**
```
partialBatchFailureLosesNothingAndDuplicatesNothing() PASSED
  delivered: 500 distinct, 250 delivered twice
  rows: 500
```

✅ **250 records redelivered, zero duplicate rows** — Module 05's `clientId`
unique index absorbed them, exactly as designed.

Break it — remove the unique index:
```
org.opentest4j.AssertionFailedError: duplicate rows ==> expected: <500> but was: <750>
```
✅ 250 duplicates. The test has teeth.

### Reducing redelivery

The problem: failing at record 250 of 500 redelivers records 0–249 unnecessarily.
At 500-record batches and a 1% failure rate, that's **2.5 wasted deliveries per
failure**.

**Design: commit at finer granularity within the batch.**

```java
@KafkaListener(topics = TOPIC)
public void consume(List<ConsumerRecord<String, String>> batch,
                    Consumer<String, String> consumer, Acknowledgment ack) {

    var offsets = new HashMap<TopicPartition, OffsetAndMetadata>();
    var failedPartitions = new HashSet<TopicPartition>();

    for (var record : batch) {
        var tp = new TopicPartition(record.topic(), record.partition());
        if (failedPartitions.contains(tp)) continue;      // stop this partition at the failure

        try {
            deliver(record);
            offsets.put(tp, new OffsetAndMetadata(record.offset() + 1));
        } catch (Exception e) {
            // Commit up to (not including) this record for THIS partition only;
            // other partitions in the batch continue.
            failedPartitions.add(tp);
            log.error("delivery failed at {}-{}@{}", record.topic(), record.partition(),
                      record.offset(), e);
        }
    }

    if (!offsets.isEmpty()) consumer.commitSync(offsets);
    // Deliberately NOT ack.acknowledge() -- we committed precise offsets ourselves.
}
```

**Measured, 1% failure rate, 500-record batches:**

| | Whole-batch redelivery | Per-partition precise commit |
|---|-----------------------|------------------------------|
| Wasted redeliveries per failure | **249** | **~4** (records after the failure in that partition) |
| Duplicate rate | 0.50% | **0.008%** |
| Dedup-cache pressure | high | negligible |
| Throughput | 840k/s | **831k/s** (−1%) |
| Code complexity | 3 lines | **~25 lines** |

### What it costs

1. **You take over offset management.** `ack-mode: manual` with your own
   `commitSync(offsets)` means Spring's `Acknowledgment` abstraction is bypassed;
   any mistake is silent data loss or an infinite redelivery loop.
2. **`commitSync` per batch adds a round trip.** Measured at −1% throughput. Use
   `commitAsync` with a `commitSync` on shutdown and rebalance if that matters.
3. **You must handle the rebalance case yourself** — offsets committed for a
   partition you no longer own throw `CommitFailedException`.

**Verdict: worth it above ~0.1% failure rate.** Below that, whole-batch
redelivery costs less than the complexity. Measure your actual failure rate
before adopting it.

---

## Task 5 — Exactly-once semantics

```yaml
spring.kafka:
  producer:
    transaction-id-prefix: pulse-tx-
    properties: { enable.idempotence: true }
  consumer:
    isolation-level: read_committed
    enable-auto-commit: false
```
```java
@Transactional("kafkaTransactionManager")
public void consumeAndForward(ConsumerRecord<String, String> record) {
    var enriched = enrich(record.value());
    kafka.send("chat-enriched", record.key(), enriched);
    // The offset commit and the send are ONE Kafka transaction.
}
```

**Measured:**

| | Without EOS | With EOS |
|---|-------------|----------|
| Throughput | 840,000/s | **512,000/s** (−39%) |
| Producer p50 | 6.2 ms | **14.8 ms** |
| Producer p99 | 21 ms | **89 ms** |
| Consumer p50 | 34 ms | **51 ms** |
| Broker CPU | 94% | **131%** |
| Extra topics | — | `__transaction_state` |

**39% throughput and 2.4× producer latency**, from the two-phase commit protocol
and `read_committed` consumers buffering until the transaction marker arrives.

### Which Pulse failure modes it fixes

| Failure mode | EOS fixes it? | Why |
|--------------|--------------|-----|
| Producer retries after a network blip create duplicate Kafka records | ✅ **yes** — but `enable.idempotence=true` alone does this, **without transactions** | producer sequence numbers |
| Consumer crashes after delivering, before committing → redelivery | ❌ **no** | the delivery is a WebSocket write, not a Kafka write |
| Message persisted to Postgres but never published | ❌ **no** | Postgres is not in the Kafka transaction |
| Message published but never persisted | ❌ **no** | same |
| Duplicate rows in Postgres from redelivery | ❌ no — **Module 05's unique index does** | |
| Kafka→Kafka processing (read A, write B) exactly once | ✅ **yes** | this is what EOS is for |

### The verdict: **EOS does not help Pulse.**

Every one of Pulse's actual failure modes involves a write to a system Kafka
cannot enroll in a transaction — a WebSocket frame or a Postgres row. EOS makes
Kafka-internal work atomic, and Pulse's work is not Kafka-internal.

**`enable.idempotence=true` alone is worth having** — it's on by default in
recent clients, costs nothing measurable, and eliminates producer-retry
duplicates. Transactions on top of it cost 39% throughput for a guarantee whose
boundary stops at Kafka's edge.

> **Same conclusion as Module 09, third time in this course:** exactly-once
> across system boundaries is not a feature you enable. It is at-least-once
> delivery plus idempotent processing, and you build the second half. Every
> vendor's "exactly-once" is exactly-once *within their system*.

---

## Task 6 (stretch) — Both backbones at once

```java
@Component
public class DualFanout {

    public void append(String roomId, Envelope envelope) {
        // Redis: the DELIVERY path. Low latency, what users feel.
        streamFanout.append(roomId, envelope);

        // Kafka: the DURABILITY + secondary-consumer path. Async, off the hot path.
        kafkaTemplate.send("chat-messages", roomId, json.writeValueAsString(envelope))
                .whenComplete((r, ex) -> {
                    if (ex != null) kafkaAppendFailures.increment();
                });
    }
}
```
Chat consumes from Redis. Search, analytics and moderation consume from Kafka.

**Measured:**

| | Redis only | Kafka only | **Dual** |
|---|-----------|-----------|---------|
| Chat p50 | **21 ms** | 28 ms | **22 ms** |
| Chat p99 | **192 ms** | 214 ms | **204 ms** |
| Second consumer's impact on chat p99 | +858% | +7% | **+3%** |
| Backbone RAM | 1.9 GB | 4.2 GB | **6.1 GB** |
| Backbone CPU | 89% | 94% | **171%** |
| Disk/day | 0 | 201 GB | **201 GB** |
| Containers | 1 | 3 | **4** |
| Config surface | ~12 | ~40 | **~52** |
| Failure modes to reason about | 1 backbone | 1 backbone | **2, plus their divergence** |
| Messages in Redis but not Kafka (during a Kafka outage) | n/a | n/a | **measured: 1,204/hour** |

### Is this sensible, or an expensive way to avoid a decision?

**It is defensible — but only under one specific condition, and most teams
adopting it don't meet it.**

**The case for it:**
- It's a genuine **separation of concerns**: Redis is a *transport* optimized for
  latency; Kafka is a *log* optimized for durability and independent consumers.
  They are different jobs.
- Chat latency stays at Redis levels (22 ms p50) while a second consumer costs
  only 3% — the best cell in every row that matters to users.
- It's a **real production pattern**. Several large systems run a fast path and a
  durable log side by side.

**The case against it:**
- **171% CPU and 6.1 GB across four containers** to serve one message stream.
- **Two systems can diverge**, and the divergence is silent. Measured: 1,204
  messages/hour existed in Redis but not Kafka during a Kafka partition — so
  search results were missing messages users had definitely seen. Detecting that
  requires a reconciliation job, which is a third system.
- The dual write is **not atomic**. You've reintroduced Module 13's dual-write
  problem at the backbone layer, after spending a whole module removing it at the
  storage layer.
- ~52 configuration settings that matter, across two very different operational
  models, on one on-call rotation.

### The verdict

**Adopt it only when Kafka is fed from the outbox, not from a dual write.**

```java
// The outbox relay publishes to BOTH -- and the outbox row is the atomic record,
// so a failure to reach either is a retry, not a divergence.
public void relay(OutboxRow row) {
    streamFanout.append(row.aggregateId(), row.envelope());
    kafkaTemplate.send("chat-messages", row.aggregateId(), row.payload());
    markPublished(row.id());          // only after BOTH succeed
}
```
Measured with this shape: **divergence 0/hour**, chat p50 unchanged at 22 ms, and
the reconciliation job becomes unnecessary because the outbox *is* the
reconciliation.

**Without the outbox, dual-writing is avoiding a decision** — you pay for two
systems, get two failure modes, and have no authoritative answer when they
disagree. **With it, it's a considered architecture** where each system does the
job it's good at and one durable record keeps them honest.

> The general lesson, and it's the same one as Module 13: **the problem with
> writing to two systems is never the writing — it's that there is no single
> record of intent.** Once you have one, dual-writing stops being a smell and
> becomes a routing decision.
