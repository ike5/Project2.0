# Challenge 16 — Justify the Numbers

Solutions in [`solutions/`](./solutions/). Try first.

## Tasks

1. **Choose the partition count from data.**
   64 was asserted, not derived. Determine the right number by measuring:
   per-partition throughput ceiling, broker memory per partition, rebalance time
   versus partition count, and producer batching efficiency.

   Then explain what breaks if you need to change it later, and design a scheme
   that lets you grow without breaking per-room ordering.

2. **Demonstrate the head-of-line blocking Kafka introduces.**
   Rooms share partitions. Show that one slow room delays unrelated rooms in the
   same partition, which Redis Streams (one stream per room) cannot do.

   Measure the impact, then mitigate it. State what the mitigation costs.

3. **Add a second consumer, both ways.**
   Add a search indexer that consumes every message. Implement it on Kafka and on
   Redis Streams.

   Measure the marginal cost of the second consumer on each: backbone CPU,
   latency impact on chat, and lines of code. This is the comparison that
   usually decides real architectures.

4. **Make batch-level idempotency correct.**
   Kafka commits one offset per partition, so a failure means the whole batch
   redelivers. Prove your consumer handles a partial-batch failure correctly —
   write a test that fails on record 250 of 500 and asserts no duplicates and no
   losses.

   Then implement a design that reduces redelivery, and state its cost.

5. **Measure exactly-once semantics, and say whether it helps.**
   Enable Kafka transactions (`transactional.id`, `read_committed`). Measure the
   throughput and latency cost.

   Then determine, concretely, which of Pulse's failure modes it fixes — and
   which it does not. Be specific about the Postgres and WebSocket writes.

6. **Stretch — run both backbones simultaneously.**
   Dual-write to Redis Streams and Kafka, consuming from Redis for delivery and
   Kafka for durability and secondary consumers.

   Measure the combined cost. Then argue whether this is a sensible architecture
   or an expensive way to avoid a decision.

## Success criteria

- [ ] Partition count derived from four measurements, with a growth scheme that
      preserves per-room ordering
- [ ] Cross-room head-of-line blocking demonstrated, measured, and mitigated with
      a stated cost
- [ ] A second consumer added to both backbones, with marginal cost measured on
      three dimensions
- [ ] A partial-batch failure test proves no duplicates and no losses; a
      redelivery-reducing design is implemented and costed
- [ ] Kafka EOS measured, with a specific account of which Pulse failure modes it
      does and does not fix
- [ ] Stretch: dual-backbone measured, with a defended verdict
