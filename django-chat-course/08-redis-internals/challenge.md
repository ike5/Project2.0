# Challenge 08 — Make Redis Tell You Where It Hurts

Solutions in [`solutions/`](./solutions/). Try first.

The lab showed you the instruments. These tasks turn them into three artefacts
you will still be using in Module 22: a latency budget, a growth audit that runs
itself, and a CI gate that stops Module 18's migration from becoming a rewrite.

## Tasks

1. **Build a Redis latency budget for Pulse, in round trips.**
   Establish your machine's floor with `redis-cli --intrinsic-latency 60`, then
   measure round-trip latency under three loads (idle, the Module 06 baseline,
   and the 8-worker knee). For each, separate the three contributions: the
   kernel's scheduling floor, Redis's own `usec_per_call`, and everything else
   (syscalls, network, queueing on the single thread).

   Then answer the design question: given a p99 fan-out budget of **200 ms** and
   the Module 07 measurement that the channel layer alone consumes 181 ms of it,
   **how many sequential Redis round trips can a single chat message afford?**
   Budget at the tail, not the mean, and say why.

   Finally, audit Pulse's send path against your answer. Count the round trips
   it issues today, and identify the one place where the count scales with room
   size rather than being constant — that is the one that will break first.

2. **Find every unbounded key, and stop looking manually.**
   Audit the running system with `redis-cli --bigkeys`, `--memkeys` and a TTL
   scan. For each key pattern, answer: **what bounds its growth?** If nothing
   does, it is a leak, not a design.

   Fix at least two. At least one of your fixes must remove a dependence on a
   graceful cleanup event — a `disconnect()`, a `finally:` block, anything that
   does not run when a process is `SIGKILL`ed — because those are leaks by
   construction.

   Then reproduce the fragmentation trap: drive `mem_fragmentation_ratio` above
   1.5, show `used_memory` falling while RSS does not, explain why the OS cannot
   reclaim it, and measure what `activedefrag yes` costs in Redis CPU and chat
   p99 while it runs.

   Finally, turn `redis_doctor.py --only keys` into something that fails a
   build: a scheduled check that emits a metric and an alert when any pattern
   exceeds its documented budget.

3. **Build the hash-tag CI gate, then prove it works.**
   The lab claimed four characters of hash tag today save Module 18's
   migration. Make that claim enforceable.

   Write a check that extracts every Redis key literal from the Pulse codebase,
   groups the keys used together in each `pipeline()` block and each Lua call
   site, and asserts that every group shares a slot via `CLUSTER KEYSLOT`. It
   must run on a standalone Redis — you do not have a cluster yet, and that is
   the point.

   Then plant a realistic mistake (tag a key by something other than the entity
   its operation groups on — a random ticket value is a good choice, since it is
   what Module 21 will actually do) and show the gate catching it.

   Then be honest about the gate's limits: name two `CROSSSLOT` failures it
   cannot catch, and say what would catch those instead.

4. **Optimise a real hot path, and justify pipeline versus Lua.**
   Find a place in Pulse issuing N sequential Redis calls where N scales with
   room size. Bulk presence lookup for a room's members is the obvious
   candidate; per-recipient unread increments is the other.

   Convert it two ways — once with a pipeline, once with a Lua script — and
   measure p50/p99 for all three versions at a room size of **500**, plus
   Redis's `usec_per_call` and CPU for each.

   Then explain when Lua beats a pipeline and when it loses. There is a real
   answer involving atomicity, reply size, and interruptibility, and one of the
   three is the reason **not** to use Lua for the case you just optimised.

5. **Stretch — client-side caching with RESP3 tracking.**
   Use `CLIENT TRACKING` to keep a local cache of room metadata that Redis
   invalidates for you, over the push type you saw in Part A. Measure the
   reduction in Redis operations per second and the local memory it costs.

   Then find the failure mode: what happens to a client whose invalidation push
   is lost, and how would you bound the resulting staleness? Identify at least
   one field in Pulse's room metadata that must **never** be client-cached, and
   say what kind of bug caching it would produce.

## Success criteria

- [ ] A latency budget separates kernel floor, Redis, and everything else at
      three load levels, with a maximum round-trip count derived from the 200 ms
      p99 budget and the one round trip that scales with room size identified
- [ ] Every key pattern has a documented growth bound; two leaks are fixed, at
      least one by removing a dependence on graceful cleanup
- [ ] Fragmentation above 1.5 is reproduced and explained, with `activedefrag`'s
      CPU and p99 cost measured
- [ ] An automated key-budget check emits a metric and an alert
- [ ] A hash-tag gate runs against a standalone Redis, catches a planted
      mistake, and its two blind spots are named
- [ ] A hot path is measured in three versions at room size 500, with the
      pipeline-versus-Lua tradeoff stated and the reason Lua loses this case
      named explicitly
- [ ] Stretch: client-side caching works with a measured op reduction, the
      lost-invalidation failure mode is bounded, and one never-cache field is
      identified with the bug class it would cause
