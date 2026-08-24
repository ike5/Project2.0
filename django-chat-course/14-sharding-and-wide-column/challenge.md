# Challenge 14 — Defend the Choice

Solutions in [`solutions/`](./solutions/). Try first.

## Tasks

1. **Break the migration on purpose, in both dangerous phases.**
   Kill an app node during phase 1 (dual write) and again during phase 3 (drain
   and cutover). For each, determine whether data was **lost**, **duplicated**,
   or **split across shards** — and prove which, with a query.

   Then make the migration safe against both. Your answer must say how a worker
   *process* that missed the assignment change is detected and fenced, and why
   counting nodes is not sufficient.

2. **Shrink, not grow.**
   The lab's `plan_rebalance` refuses to shrink. Implement 6 → 4 and explain why
   it is harder than 4 → 6: what can you not do in parallel, what has to drain
   first, and what happens if a room is written to during the final merge?

   Measure the total pause and compare it with the growth case.

3. **Find the scatter-gather ceiling, then eliminate it.**
   Measure unread-count p99 at 4, 16, 64 and 256 shards. Show that your measured
   p99 matches the `p(99^(1/k))` prediction from the lab, or explain the
   discrepancy.

   Then implement a design whose p99 is **constant** regardless of shard count,
   and state precisely what it costs in staleness and in write amplification.

4. **Make a cross-shard schema migration work under load.**
   Add a `thread_id bigint` column to `messages` across all shards while the
   system serves traffic. Handle the version-skew window where some shards have
   it, some do not, and some of the 24 worker processes know about it and some
   do not.

   Write the runbook first. Then execute it and prove zero errors.

5. **Fix Scylla's idempotency problem properly.**
   The lab moved dedup to Redis, which bounds a permanent guarantee by a TTL and
   loses it on a restart (Part E measured three duplicates). Design an
   alternative that keeps the guarantee **durable** without a Paxos round trip
   on the hot path.

   *Hint: what if `client_id` were part of the clustering key? What would that
   cost you on the read path, and what would it do to the bucket walk?*

6. **Measure compaction's real cost.**
   Drive Scylla until compaction falls behind. Track sstable count, read
   amplification and p99 over time. Then compare `TimeWindowCompactionStrategy`
   against `SizeTieredCompactionStrategy` and `LeveledCompactionStrategy` for the
   chat workload and justify the lab's choice with numbers — or overturn it.

7. **Stretch — write the ADR, then attack it.**
   Produce a one-page architecture decision record recommending sharded Postgres
   or ScyllaDB for Pulse. Include the decision, the measured evidence, the
   consequences you accept, and **three specific, falsifiable conditions** that
   would trigger a revisit.

   Then have someone — or your own strongest reasoning — attack it, and revise.
   An ADR nobody has argued with is a diary entry.

## Success criteria

- [ ] Node failure characterized in both migration phases, then made safe, with
      per-worker-process fencing and a stated reason why per-node is not enough
- [ ] 6 → 4 shrink implemented, its extra hazard named, and its pause measured
      against the growth case
- [ ] Scatter-gather p99 measured at four shard counts and checked against the
      `p(99^(1/k))` model, with a constant-time alternative implemented and costed
- [ ] A cross-shard `ALTER TABLE` executes under load with zero errors, from a
      runbook written before the execution
- [ ] A durable Scylla idempotency design that avoids LWT on the hot path, with
      its read-path cost stated in milliseconds
- [ ] Three compaction strategies measured on the chat workload, with a justified
      choice
- [ ] Stretch: an ADR with three falsifiable revisit conditions that survives an
      adversarial review
