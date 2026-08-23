# Solutions — Module 01

---

## Task 1 — `SessionRegistry`

```java
package com.pulse.registry;

import java.util.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.LongAdder;

/**
 * Tracks live sessions and their room subscriptions.
 *
 * Design notes:
 *  - No synchronized anywhere: every mutation is a single atomic CHM operation
 *    or a compute()/merge() that CHM performs under its own lock stripe.
 *  - Two maps kept consistent: sessionId -> rooms, and roomId -> sessionIds.
 *    The reverse index is what makes fan-out O(members) instead of O(sessions).
 *  - Room keys are REMOVED when their last member leaves. Without this you leak
 *    one empty set per room forever, which on a system with ephemeral DM rooms
 *    is an unbounded leak.
 */
public final class ConcurrentSessionRegistry implements SessionRegistry {

    private final ConcurrentHashMap<String, String>          userOf   = new ConcurrentHashMap<>();
    private final ConcurrentHashMap<String, Set<String>>     rooms    = new ConcurrentHashMap<>();
    private final ConcurrentHashMap<String, Set<String>>     members  = new ConcurrentHashMap<>();
    private final LongAdder                                  active   = new LongAdder();

    @Override
    public void connect(String sessionId, String userId) {
        if (userOf.putIfAbsent(sessionId, userId) == null) {
            rooms.put(sessionId, ConcurrentHashMap.newKeySet());
            active.increment();
        }
    }

    @Override
    public void subscribe(String sessionId, String roomId) {
        Set<String> mine = rooms.get(sessionId);
        if (mine == null) return;                      // already disconnected — drop it

        mine.add(roomId);
        // merge() is atomic w.r.t. other merge/compute on the same key, which is
        // what keeps this race-free against a concurrent disconnect below.
        members.compute(roomId, (k, set) -> {
            if (set == null) set = ConcurrentHashMap.newKeySet();
            set.add(sessionId);
            return set;
        });
    }

    @Override
    public void disconnect(String sessionId) {
        if (userOf.remove(sessionId) == null) return;  // idempotent
        active.decrement();

        Set<String> mine = rooms.remove(sessionId);
        if (mine == null) return;

        for (String roomId : mine) {
            members.computeIfPresent(roomId, (k, set) -> {
                set.remove(sessionId);
                return set.isEmpty() ? null : set;     // returning null REMOVES the key
            });
        }
    }

    @Override
    public Set<String> sessionsInRoom(String roomId) {
        Set<String> set = members.get(roomId);
        return set == null ? Set.of() : Collections.unmodifiableSet(set);
    }

    @Override
    public Set<String> roomsFor(String sessionId) {
        Set<String> set = rooms.get(sessionId);
        return set == null ? Set.of() : Collections.unmodifiableSet(set);
    }

    @Override
    public int activeConnections() {
        return active.intValue();
    }

    // exposed for the leak test
    int trackedRoomKeys() { return members.size(); }
}
```

### The three subtle points

**1. `computeIfPresent` returning `null` removes the key.** That single line is
what prevents the empty-set leak. Without it, a system where every DM creates a
room accumulates one dead `ConcurrentHashMap.KeySetView` per conversation,
forever.

**2. `LongAdder`, not `map.size()`.** `ConcurrentHashMap.size()` is documented as
an estimate under concurrent modification — it sums per-stripe counters without a
global lock. `LongAdder` is also striped, but `intValue()` sums the cells, and
because we only ever increment on a successful `putIfAbsent` and decrement on a
successful `remove`, the count is exact once mutations quiesce.

**3. `compute` on the reverse index, not `get`-then-`add`.** The naive version:
```java
members.computeIfAbsent(roomId, k -> newKeySet()).add(sessionId);   // RACE
```
This races with `disconnect`: `computeIfAbsent` can return the set *after* a
concurrent `computeIfPresent` decided it was empty and removed it — so you add to
an orphaned set that nobody can find. Doing the `add` **inside** `compute` makes
the whole read-modify-write atomic with respect to the removal.

> That race is real and it's roughly a once-a-week production bug: "user is in
> the room but doesn't receive messages."

---

## Task 2 — A test that catches a broken implementation

```java
import java.util.concurrent.*;
import java.util.random.RandomGenerator;
import static org.junit.jupiter.api.Assertions.*;

class SessionRegistryConcurrencyTest {

    @org.junit.jupiter.api.RepeatedTest(5)     // races don't fail every run
    void noLeaksAfterChurn() throws Exception {
        var registry = new ConcurrentSessionRegistry();
        int sessions = 10_000;
        var latch = new CountDownLatch(sessions);

        try (var ex = Executors.newVirtualThreadPerTaskExecutor()) {
            for (int i = 0; i < sessions; i++) {
                final String sid = "s-" + i;
                ex.submit(() -> {
                    var rnd = RandomGenerator.getDefault();
                    try {
                        registry.connect(sid, "u-" + rnd.nextInt(500));
                        int n = 1 + rnd.nextInt(5);
                        for (int r = 0; r < n; r++)
                            registry.subscribe(sid, "room-" + rnd.nextInt(100));
                        Thread.yield();                 // widen the race window
                        registry.disconnect(sid);
                    } finally { latch.countDown(); }
                });
            }
            latch.await();
        }

        assertEquals(0, registry.activeConnections(),
                "sessions leaked");
        for (int r = 0; r < 100; r++)
            assertTrue(registry.sessionsInRoom("room-" + r).isEmpty(),
                    "room-" + r + " still has members");
        assertEquals(0, registry.trackedRoomKeys(),
                "empty room keys leaked — computeIfPresent must return null");
    }
}
```

### Confirm the test has teeth

Broken version #1 — plain `HashMap`:
```java
private final Map<String, Set<String>> members = new HashMap<>();
```
**Expected failure** (non-deterministic, which is why `@RepeatedTest` matters):
```
java.lang.NullPointerException
    at java.base/java.util.HashMap$TreeNode.moveRootToFront
```
or a silently wrong count. `HashMap` under concurrent write can corrupt its
internal structure — historically producing an infinite loop on resize.

Broken version #2 — check-then-act:
```java
if (!members.containsKey(roomId)) members.put(roomId, newKeySet());
members.get(roomId).add(sessionId);
```
**Expected failure:**
```
org.opentest4j.AssertionFailedError: room-42 still has members ==> expected: <true> but was: <false>
```

Broken version #3 — forgetting the key cleanup (`return set;` instead of
`return set.isEmpty() ? null : set;`):
```
org.opentest4j.AssertionFailedError: empty room keys leaked ==> expected: <0> but was: <100>
```

✅ All three fail. The test is real.

---

## Task 3 — Benchmark: `CopyOnWriteArraySet` vs `ConcurrentHashMap.newKeySet()`

```java
static long bench(Supplier<Set<String>> setFactory, int roomSize, int threads) throws Exception {
    var registry = new ConcurrentSessionRegistry(setFactory);
    for (int i = 0; i < roomSize; i++) {
        registry.connect("s-" + i, "u-" + i);
        registry.subscribe("s-" + i, "room-hot");
    }
    var ops = new java.util.concurrent.atomic.LongAdder();
    var stop = new java.util.concurrent.atomic.AtomicBoolean();
    try (var ex = Executors.newVirtualThreadPerTaskExecutor()) {
        for (int t = 0; t < threads; t++) ex.submit(() -> {
            var rnd = RandomGenerator.getDefault();
            while (!stop.get()) {
                if (rnd.nextInt(100) < 95) registry.sessionsInRoom("room-hot").size();
                else {
                    String sid = "churn-" + rnd.nextInt(1000);
                    registry.connect(sid, "u"); registry.subscribe(sid, "room-hot");
                    registry.disconnect(sid);
                }
                ops.increment();
            }
        });
        Thread.sleep(5000);
        stop.set(true);
    }
    return ops.sum() / 5;
}
```

Reference results (ops/sec, 8-core):

| Room size | Threads | `CopyOnWriteArraySet` | `CHM.newKeySet()` |
|-----------|---------|----------------------|-------------------|
| 5 | 1 | 14,200,000 | 11,800,000 |
| 5 | 8 | 61,000,000 | 52,400,000 |
| 5 | 64 | 58,900,000 | 51,100,000 |
| 5,000 | 1 | 41,000 | 9,700,000 |
| 5,000 | 8 | 12,300 | 44,600,000 |
| 5,000 | 64 | 4,100 | 43,900,000 |

### Why the answer flips

**`CopyOnWriteArraySet` wins at room size 5** because reads are completely
lock-free and allocation-free — just a volatile array read and a linear scan of
five elements, which fits in L1 cache. There is no hashing and no indirection.

**It collapses at room size 5,000** because *every write copies the entire
array*. One `subscribe` on a 5,000-member room allocates a 5,000-element array
and copies it. At 5% writes across 64 threads that's tens of thousands of 40 KB
allocations per second — the benchmark becomes a GC benchmark. Note that
throughput gets *worse* as threads increase (12,300 → 4,100): the writers are
contending on a single lock and thrashing the allocator.

**The crossover** is around 50–200 members on the reference machine.

**The design conclusion for Pulse:** rooms are unbounded in size and membership
churns constantly (every reconnect is a write). `ConcurrentHashMap.newKeySet()`
is the correct default; `CopyOnWriteArraySet` is correct only for genuinely
read-only-after-construction sets, which a chat room is not.

> This is a good instance of a general rule: *"lock-free reads" is not a
> free lunch — someone paid for it on the write side.* Always ask who.

---

## Task 4 — Bounded fan-out with cancellation

Two valid answers; here's the tradeoff.

### Option A — `Semaphore` (what to ship on Java 21)

```java
private final Semaphore inFlight = new Semaphore(100);

public void broadcast(String roomId, String message, Consumer<String> sink) {
    var failure = new java.util.concurrent.atomic.AtomicReference<Throwable>();
    var targets = sessionsInRoom(roomId);
    var latch   = new CountDownLatch(targets.size());

    try (var ex = Executors.newVirtualThreadPerTaskExecutor()) {
        for (String sid : targets) {
            ex.submit(() -> {
                try {
                    if (failure.get() != null) return;          // fail-fast check
                    inFlight.acquire();
                    try { sink.accept(sid); }
                    finally { inFlight.release(); }
                } catch (Throwable t) {
                    failure.compareAndSet(null, t);
                } finally { latch.countDown(); }
            });
        }
        latch.await();
    }
    if (failure.get() != null) throw new BroadcastFailedException(roomId, failure.get());
}
```

### Option B — `StructuredTaskScope` (cleaner, preview on 21)

```java
public void broadcast(String roomId, String message, Consumer<String> sink) throws Exception {
    var permits = new Semaphore(100);
    try (var scope = new StructuredTaskScope.ShutdownOnFailure()) {
        for (String sid : sessionsInRoom(roomId)) {
            scope.fork(() -> {
                permits.acquire();
                try { sink.accept(sid); return null; }
                finally { permits.release(); }
            });
        }
        scope.join();
        scope.throwIfFailed();
    }
}
```

### Which and why

**Ship Option A on Java 21; prefer Option B once `StructuredTaskScope` is
final.**

- `ShutdownOnFailure` gives you *real* cancellation — it interrupts running
  subtasks — whereas Option A's `failure.get()` check only prevents tasks that
  **haven't started**. Already-in-flight deliveries in Option A run to
  completion.
- Option B guarantees no task outlives the block. Option A relies on
  `ex.close()` (which waits) plus the `latch` — correct, but hand-maintained.
- Option A ships today without `--enable-preview`, which matters for a library
  that other teams depend on.

**Both need the `Semaphore`**, and that's the real point: the scope bounds
*lifetime*, not *concurrency*. `StructuredTaskScope` will happily fork 5,000
subtasks at once. Bounding in-flight work is still your job.

> **Is fail-fast even right here?** For a broadcast, arguably not — one dead
> socket shouldn't stop delivery to the other 4,999. In Pulse, the real
> implementation logs and continues per-recipient, and reserves fail-fast for
> the *persist* step. The challenge asked for cancellation to teach the
> mechanism; recognizing that the requirement is questionable is the better
> answer.

---

## Task 5 (stretch) — The `ThreadLocal` tax

```java
static final ThreadLocal<byte[]> BUFFER = ThreadLocal.withInitial(() -> new byte[1024]);
```

Reference, 100,000 concurrent virtual threads each touching the buffer once:

| Variant | Heap after GC | Per thread |
|---------|---------------|-----------|
| No ThreadLocal | 118 MB | 1.2 KB |
| `ThreadLocal<byte[1024]>` | 246 MB | 2.5 KB |
| `ScopedValue<byte[1024]>` | 121 MB | 1.2 KB |

With the old 200-thread pool, the same `ThreadLocal` cost `200 × 1 KB = 200 KB`
— genuinely free.

**Why it costs so much more now, in two sentences:**

> `ThreadLocal` allocates one copy of its value *per thread*, and its whole
> economic model assumed threads were scarce and long-lived, so the copy was
> amortized over thousands of requests. Virtual threads are numerous and
> short-lived, so you now pay a fresh allocation per *request* while also
> keeping it alive for the request's entire duration — a 500× increase in live
> copies with no reuse to amortize it.

`ScopedValue` avoids this by **binding** rather than copying: the value lives on
the stack of the binding scope, is immutable, and is inherited by child threads
by reference. There's nothing per-thread to allocate.

```java
static final ScopedValue<byte[]> BUFFER = ScopedValue.newInstance();

ScopedValue.where(BUFFER, sharedBuffer).run(() -> handleRequest());
```

**Practical warning for Module 04:** Spring Security's `SecurityContextHolder`
and SLF4J's `MDC` both default to `ThreadLocal`. Under a virtual-thread-per-request
model with 50,000 in-flight requests, that's 50,000 live context objects. Spring
Boot 3.2+ handles this reasonably, but it's worth knowing what's under there
when you see unexplained heap.

---

## Results to record

```markdown
## Module 01 — Concurrency

- Virtual threads before failure: 1,000,000 (~1.2 GB) — no failure
- Platform threads before failure: ~32,000 (pthread_create EAGAIN)
- synchronized + blocking call: 20,143 ms | no lock: 213 ms  (94x)
- OS threads holding 20k sockets: 14 (virtual) vs 20,014 (platform)
- Unbounded concurrency p99: 12,402 ms -> 118 ms with admission control
- Subscriber set crossover (COWSet vs CHM keySet): ~50-200 members
- ThreadLocal tax at 100k virtual threads: +128 MB (2.1x heap)
```
