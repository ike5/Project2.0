# Challenge 14 — Defend the Choice

Solutions in [`solutions/`](./solutions/). Try first.

## Tasks

1. **Break the migration on purpose.**
   Kill an app node during phase 1 (dual write) and again during phase 3
   (cutover). For each, determine whether data was lost, duplicated, or split
   across shards.

   Then make the migration safe against both. Your answer must include how a
   node that missed the assignment change is detected and fenced.

2. **Find the scatter-gather ceiling.**
   Measure unread-count latency at 4, 16, 64 and 256 shards. Model the p99 as a
   function of shard count and per-shard p99.

   Then implement a design that keeps it constant regardless of shard count, and
   say what it costs.

3. **Make schema migration work across shards.**
   Add a column to `messages` across all shards while the system serves traffic.
   Handle the version-skew window where some shards have it and some don't, and
   some app nodes know about it and some don't.

   Write the runbook. Then execute it and prove zero errors.

4. **Fix Scylla's idempotency problem properly.**
   The lab moved dedup to Redis, which bounds the guarantee by a TTL. Design an
   alternative that keeps the guarantee durable without a Paxos round trip on the
   hot path.

   (Hint: what if the client ID *were* the clustering key? What would that cost?)

5. **Measure compaction's real cost.**
   Drive Scylla until compaction falls behind. Measure sstable count, read
   amplification and p99 over time. Then compare `TimeWindowCompactionStrategy`
   against `SizeTieredCompactionStrategy` and `LeveledCompactionStrategy` for the
   chat workload, and justify the choice with numbers.

6. **Stretch — write the ADR.**
   Produce a one-page architecture decision record recommending sharded Postgres
   or ScyllaDB for Pulse. Include: the decision, the measured evidence, the
   consequences you accept, and the three specific conditions that would trigger
   a revisit.

   Then have someone (or your own strongest reasoning) attack it, and revise.

## Success criteria

- [ ] Node failure during both migration phases is characterized, then made safe,
      with a fencing mechanism for stale assignment maps
- [ ] Scatter-gather p99 modelled against shard count, with a constant-time
      alternative implemented and costed
- [ ] A cross-shard schema migration executes under load with zero errors and a
      written runbook
- [ ] A durable Scylla idempotency design exists that avoids LWT on the hot path,
      with its cost stated
- [ ] Three compaction strategies measured on the chat workload with a justified
      choice
- [ ] Stretch: an ADR that survives an adversarial review
