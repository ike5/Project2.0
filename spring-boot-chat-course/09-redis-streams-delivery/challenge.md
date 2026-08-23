# Challenge 09 — Make the Guarantee Real

Solutions in [`solutions/`](./solutions/). Try first.

## Tasks

1. **Detect and quarantine a poison message.**
   An entry that always throws during delivery stays in the PEL forever, gets
   reclaimed every 30 seconds, and burns CPU indefinitely. Its delivery count
   climbs.

   Implement a dead-letter policy: after N delivery attempts, move the entry to a
   `room:{id}:dlq` stream, ack the original, and emit a metric. Prove it works by
   publishing a message that always fails. Then answer: what should N be, and how
   did you decide?

2. **Size the replay window from data, not intuition.**
   `MAXLEN ~ 10000` was a guess. Determine the right value by measuring:
   - the distribution of client disconnect durations in your load test,
   - the message rate per room at p50 and p99,
   - the memory cost per entry.

   Then implement a `MINID`-based policy with a defensible time window, and show
   the memory difference for a quiet room and a busy one.

3. **Handle the trimmed-but-unacked case.**
   Trim a stream while entries are still pending. Show what `XPENDING` and
   `XAUTOCLAIM` report for entries that no longer exist. Then make your consumer
   handle it correctly — the PEL must not grow forever.

   (Hint: `XAUTOCLAIM`'s third return element is not decoration.)

4. **Measure the ack-ordering tradeoff empirically.**
   Implement both orderings — ack-before-process and ack-after-process — behind a
   config flag. For each, kill the consumer mid-batch 20 times and count:
   - messages lost,
   - messages duplicated,
   - messages correct.

   Present the results as a table and state which you'd ship for chat messages,
   and which for read receipts.

5. **Find the consumer-group scaling limit.**
   Every node adds a consumer group per room, and every group has its own PEL.
   Measure Redis memory and CPU as you go from 1 to 8 nodes with 500 active
   rooms.

   Extrapolate: at what node count does per-group PEL overhead become the
   dominant Redis memory cost? Propose an architecture that avoids it.

6. **Stretch — compare against Pub/Sub with an application-level replay buffer.**
   Implement an alternative: keep Pub/Sub for delivery, but maintain a capped
   `LIST` of recent messages per room, and have reconnecting nodes fetch the
   delta with `LRANGE`.

   Measure latency, memory, CPU and loss against the Streams implementation. This
   is a real design that ships in production systems — make the honest case for
   and against it.

## Success criteria

- [ ] Poison messages are dead-lettered after a justified N, with a metric
- [ ] The replay window is sized from measured disconnect durations and message
      rates, implemented with `MINID`
- [ ] Trimmed-but-pending entries are handled and the PEL provably doesn't grow
- [ ] Both ack orderings measured over 20 kills each, with a per-message-type
      recommendation
- [ ] Per-group PEL overhead measured from 1 to 8 nodes with an extrapolated
      limit and a proposed alternative
- [ ] Stretch: the Pub/Sub + LIST design is implemented and compared on four
      dimensions, with an honest verdict
