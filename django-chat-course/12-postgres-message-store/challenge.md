# Challenge 12 — Make the Store Defensible

Solutions in [`solutions/`](./solutions/). Try first.

## Tasks

1. **Justify every index, and delete one.**
   For each of the three indexes, name the exact query it serves, measure the
   query with and without it, and measure the `executemany` batch-500 insert-rate
   cost of having it.

   Then find an index you can delete, or a fourth you can prove is needed. Your
   answer must include the insert-rate delta. (Hint: look hard at the primary key
   and what `seq` orders relative to `id`.)

2. **Handle edits and deletes properly.**
   Implement message edit and delete. Then answer, with measurements:
   - Does an edit break a client's cached copy? How does the client learn?
   - Does a soft-delete row still cost you on the scrollback path? Prove it, and
     show the dead-tuple count the `UPDATE` created.
   - What does GDPR erasure require that soft delete doesn't give you?

   Implement whichever of hard delete or crypto-shredding you can defend.

3. **Measure the real cost of `TOAST`.**
   Insert messages of 100 B, 1 KB, 2 KB and 10 KB. For each, measure storage,
   insert rate, and the cost of a scrollback query that selects `body` versus one
   that doesn't.

   Find the size at which TOAST kicks in on your instance, and explain why a
   list/preview view should never `SELECT body` — and what to store instead.

4. **Build the read path with correct caching.**
   Add a Redis cache for the most recent N messages per room (Module 08's capped
   `LIST`). Then answer:
   - What invalidates it? (New messages, edits, deletes — and why each is treated
     differently.)
   - What happens on a cache miss during a Postgres failover?
   - How do you prevent a cache stampede when a popular room's cache expires?

   Measure the hit rate and the p99 improvement.

5. **Prove the write path degrades gracefully.**
   Saturate Postgres (`pgbench` alongside, or shrink the connection pool). Show
   what the chat send path does when the database can't keep up — the naive result
   is a 30-second p99 with *zero* errors, which is worse than failing.

   Then make it degrade the way you want: bounded admission, a clear error to the
   client, and a metric — rather than an unbounded queue. Note *why* the retry is
   safe (Module 05's idempotency).

6. **Stretch — model 74 TB/year and cost it.**
   Produce a capacity and cost model for one year at 10,000 messages/second.
   Include storage, IOPS, backup size and **restore time** (the number that should
   alarm you).

   Then produce three alternatives (retention, compression, tiering to object
   storage) with their cost and their user-visible consequence. Recommend one and
   sequence the rollout.

## Success criteria

- [ ] Every index has a named query, a measured benefit, and a measured
      insert-rate cost; one is added or removed with justification
- [ ] Edit and delete work; the client-invalidation path is demonstrated; the
      soft-delete read cost and dead-tuple cost are measured; a GDPR-capable
      erasure exists
- [ ] TOAST threshold found empirically, with select-body vs not measured
- [ ] A read cache exists with a measured hit rate, correct invalidation, and
      stampede protection
- [ ] The write path degrades with bounded admission, a client error and a metric
      — demonstrated under saturation
- [ ] Stretch: a costed one-year model with three alternatives, a recommendation,
      and a rollout sequence
