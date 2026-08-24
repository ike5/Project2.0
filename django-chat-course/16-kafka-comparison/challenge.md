# Challenge 16 — Kafka or Not, With Evidence

Solutions in [`solutions/`](./solutions/). Try first.

## Tasks

1. **Justify the partition count, or overturn 64.**
   Measure sustained throughput per partition, retention size per partition at
   Pulse's 10k msg/s, rebalance duration as a function of partition count, and
   the per-partition memory cost on a broker.

   Then pick a number for Pulse and defend it. "64 is what the lab used" is not
   an answer. State what would make you change it, and what you would have to
   migrate if you were wrong.

2. **Break per-room ordering three ways, then prove each fix.**
   Kafka guarantees order *within a partition*. Find three distinct ways a room's
   messages end up out of order despite that guarantee — at least one must
   involve the producer, and at least one must involve adding partitions.

   For each: reproduce it, show the client-visible symptom in terms of the
   protocol's `seq` and gap detection, and fix it.

3. **Find the real crossover on your machine.**
   Part D measured Redis saturating at ~48 worker processes and Kafka flat to
   128. Reproduce it, then express the crossover as a formula in terms of
   messages/second, worker processes and fan-out ratio — not as a single number.

   Then answer: at what point does Pulse cross it, given the growth rate you would
   have to assume? Show the assumption.

4. **Make Kafka the durable record and delete the outbox.**
   Module 13's transactional outbox exists to close the dual-write hole. If Kafka
   is `acks=all` durable, the outbox is redundant — *if* you can make the
   Postgres write and the Kafka write consistent.

   Design and implement it. Then find the failure mode you did not eliminate, and
   say honestly whether the trade is worth it.

5. **Add a second consumer, and measure what it costs both backends.**
   Add a moderation consumer that reads every message, scores it, and writes to a
   separate table. Add it on Kafka (a new consumer group) and on Redis Streams (a
   new consumer group per room).

   Measure: implementation effort, added backbone load, impact on delivery p99,
   and how far back the new consumer can replay on its first run.

6. **Instrument lag properly, and alert on it.**
   Consumer lag is the metric of this module. Build the alert: what threshold,
   over what window, and why? A lag of 10,000 at 400k msg/s is 25 ms of backlog
   and completely fine; a lag of 200 on a quiet room may be an hour.

   Write an alert that is right in both cases. (Hint: lag alone is the wrong
   unit.)

7. **Stretch — run both backends at once and cut over live.**
   Dual-publish to Redis Streams and Kafka, consume from one, and cut over under
   load with zero loss and zero duplicates *observed by a client*. Then cut back.

   Write the runbook first, including how you know the new backend is caught up
   before you switch, and what your rollback trigger is.

## Success criteria

- [ ] Partition count chosen from four measurements, with a stated revisit
      condition and the migration cost of being wrong
- [ ] Three distinct per-room ordering breakages reproduced, each with its
      client-visible `seq` symptom and its fix
- [ ] The Redis/Kafka crossover expressed as a formula, validated against your
      own measurements, with Pulse located on it
- [ ] The outbox deleted in favour of Kafka durability, with the remaining
      failure mode named and the trade judged
- [ ] A second consumer added to both backends, with four dimensions measured
- [ ] A lag alert that is correct for both a busy and a quiet room, with the unit
      justified
- [ ] Stretch: a live dual-publish cutover and rollback, from a runbook written
      first, with zero client-observed loss or duplication
