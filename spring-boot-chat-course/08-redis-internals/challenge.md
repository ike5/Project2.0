# Challenge 08 — Make Redis Tell You Where It Hurts

Solutions in [`solutions/`](./solutions/). Try first.

## Tasks

1. **Build a Redis latency budget for Pulse.**
   Establish your machine's floor with `redis-cli --intrinsic-latency 60`, then
   measure actual round-trip latency under three loads (idle, 50k ops/s, 200k
   ops/s). Report:
   - the intrinsic floor,
   - Redis's contribution at each load,
   - the network's contribution.

   Then state the maximum number of sequential Redis round trips a single chat
   message can afford, if the p99 fan-out budget is 200 ms.

2. **Find every unbounded key in Pulse.**
   Audit your running system with `--bigkeys`, `--memkeys` and a TTL scan. For
   each key pattern, answer: what bounds its growth? If nothing does, it's a leak.

   Fix at least two. Then write a startup assertion or a scheduled check that
   fails loudly if any key pattern exceeds a configured size.

3. **Quantify the `noeviction` decision.**
   Set `maxmemory` deliberately low and drive Pulse until Redis is full. Compare
   `noeviction` against `allkeys-lru`:
   - What error does the application see under each?
   - How many messages are lost under each?
   - How long until you *notice* under each?

   Report the time-to-detection difference and argue which you'd ship.

4. **Optimize a real hot path with pipelining.**
   Find a place in Pulse doing N sequential Redis calls (presence checks for a
   room's members is a good candidate). Convert it to a pipeline or a Lua script.
   Measure p99 before and after at a room size of 500.

   Then explain when a Lua script beats a pipeline and vice versa — there's a
   real answer involving atomicity and reply size.

5. **Reproduce the fragmentation trap.**
   Create a workload that drives `mem_fragmentation_ratio` above 1.5 (hint: write
   many keys of varied sizes, then delete most of them). Show `used_memory`
   dropping while RSS doesn't.

   Then fix it with `activedefrag` and measure the CPU cost of the defragmenter
   while it runs. Explain why the OS doesn't just reclaim the memory.

6. **Stretch — implement client-side caching with RESP3 tracking.**
   Use `CLIENT TRACKING` to have Redis invalidate a local cache of room metadata.
   Measure the reduction in Redis ops/sec and the added complexity.

   Then identify the failure mode: what happens to a client whose invalidation
   push is lost, and how would you bound the resulting staleness?

## Success criteria

- [ ] A latency budget exists with intrinsic floor, Redis, and network separated,
      and a maximum round-trip count derived from the p99 budget
- [ ] Every key pattern in Pulse has a documented growth bound; two leaks fixed;
      an automated check exists
- [ ] `noeviction` vs `allkeys-lru` compared on error visibility, message loss,
      and time-to-detection
- [ ] A hot path is pipelined or scripted with before/after p99 at room size 500,
      and the Lua-vs-pipeline tradeoff is stated
- [ ] Fragmentation above 1.5 is reproduced and fixed, with defrag CPU measured
      and the underlying cause explained
- [ ] Stretch: client-side caching works, with ops reduction measured and the
      lost-invalidation failure mode bounded
