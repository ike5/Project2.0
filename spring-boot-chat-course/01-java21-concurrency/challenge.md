# Challenge 01 — Build a Connection Registry That Doesn't Lie

Solutions in [`solutions/`](./solutions/). Try first.

In Module 04 you'll need a component that tracks every connected session — which
user, which rooms, which node. It's mutated from thousands of virtual threads and
read on every single fan-out. Getting it wrong costs you correctness *and*
throughput. Build it now, before Spring is in the way.

## Tasks

1. **Implement `SessionRegistry`.**
   ```java
   public interface SessionRegistry {
       void connect(String sessionId, String userId);
       void disconnect(String sessionId);
       void subscribe(String sessionId, String roomId);
       Set<String> sessionsInRoom(String roomId);
       int activeConnections();
       Set<String> roomsFor(String sessionId);
   }
   ```
   Requirements:
   - Thread-safe under concurrent connect/disconnect/subscribe.
   - `disconnect` must remove the session from **every** room it joined — no
     leaks. A registry that grows forever is the #1 chat memory bug.
   - `activeConnections()` must be **exact**, not an estimate. (`ConcurrentHashMap.size()`
     is not exact under concurrent modification — use something else.)
   - No `synchronized` anywhere. Prove it with `-Djdk.tracePinnedThreads=full`.

2. **Write a concurrency test that actually fails a broken implementation.**
   Spawn 10,000 virtual threads that randomly connect, subscribe to 1–5 of 100
   rooms, and disconnect. After they all finish, assert:
   - `activeConnections() == 0`
   - every room's subscriber set is empty
   - no room key leaked with an empty set left behind

   Deliberately write a *broken* version first (use `HashMap`, or
   `containsKey`-then-`put`) and confirm your test catches it. A test that passes
   against broken code is not a test.

3. **Benchmark it.**
   Measure throughput (ops/sec) for a read-heavy workload — 95% `sessionsInRoom`,
   5% mutations — at 1, 8, and 64 concurrent virtual threads. Then swap
   `CopyOnWriteArraySet` for `ConcurrentHashMap.newKeySet()` as the per-room
   subscriber collection and re-measure.

   Explain the result. Which is faster for a 5-member room? For a 5,000-member
   room? Why does the answer flip?

4. **Add bounded fan-out.**
   Add `void broadcast(String roomId, String message, Consumer<String> sink)`
   that delivers to every session in the room, in parallel, but with **at most
   100 deliveries in flight at once** — and which cancels all remaining
   deliveries if any single one throws.

   Use `StructuredTaskScope` or a `Semaphore`; justify which and why.

5. **Stretch — measure the ThreadLocal tax.**
   Add a `ThreadLocal<byte[1024]>` that each operation touches (simulating an
   MDC logging context or a per-request buffer). Measure heap usage at 100,000
   concurrent virtual threads with and without it.

   Then reimplement with `ScopedValue` (preview) and compare. Explain, in two
   sentences, why `ThreadLocal` costs so much more under virtual threads than it
   did under a 200-thread pool.

## Success criteria

- [ ] `SessionRegistry` is thread-safe with zero `synchronized` blocks
- [ ] `disconnect` provably leaks nothing — rooms *and* room keys are cleaned up
- [ ] `activeConnections()` is exact under concurrent load
- [ ] The concurrency test fails against a deliberately broken implementation
- [ ] Throughput is measured for both subscriber-set types, with the crossover
      explained
- [ ] `broadcast` bounds in-flight deliveries and cancels siblings on failure
- [ ] `-Djdk.tracePinnedThreads=full` reports no pinning during the benchmark
- [ ] Stretch: the `ThreadLocal` vs `ScopedValue` heap difference is measured
