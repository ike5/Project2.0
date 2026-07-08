# Module 11 — Concurrency Essentials

**Goal:** use the modern concurrency tools — **`ExecutorService`** for
thread pools, **`CompletableFuture`** for composable async, and
**immutability** as the default for safety. Understand the `volatile` and
`AtomicXxx` cases, but reach for them rarely.

⏱️ ~3 h · 🎯 Prereq: Module 10.

---

## 1. Why concurrency is hard

A `HashMap` is fast and simple in a single thread. In two threads, with
no synchronisation, you get **lost updates**, **corrupted structures**,
and `NullPointerException`s in the middle of a `put`. The issue is
"interleaving": any sequence of operations can be cut in half by the
runtime, leaving the other thread to see a half-done result.

Three techniques to deal with this:
1. **Don't share state.** Pass immutable values between threads.
2. **Use higher-level concurrent types.** `ConcurrentHashMap`,
   `AtomicInteger`, `BlockingQueue`.
3. **Synchronise when you must.** `synchronized` blocks, `ReentrantLock`,
   `volatile`.

The order above is your preference order. Start with (1), reach for (3)
only as a last resort.

## 2. Immutability is the easiest safety

A truly immutable object can be shared between threads without any
synchronisation. No locks, no races, no memory-visibility surprises.

```java
public record Money(long cents, Currency currency) { /* final fields, no mutators */ }
Money m1 = new Money(100, USD);
Money m2 = m1.add(new Money(50, USD));    // returns a new Money
// m1 is still cents=100; m2 is cents=150
```

**Rule of thumb:** make every value object a record, every collection
immutable (`List.of`, `Map.of`, or `List.copyOf`), and you'll rarely
need a lock.

## 3. The legacy: `Thread` and `Runnable`

The lowest-level API:
```java
Thread t = new Thread(() -> doWork());
t.start();
t.join();   // wait for it
```

**Don't do this in application code.** Creating raw threads is wasteful
(each thread costs ~1 MB of stack), and there's no built-in way to limit
how many you create. Use a thread pool.

## 4. `ExecutorService` — the right primitive

```java
try (var pool = Executors.newFixedThreadPool(4)) {
    Future<String> f = pool.submit(() -> slowCall());
    String result = f.get(5, TimeUnit.SECONDS);
}
```

`ExecutorService` accepts `Runnable` (fire-and-forget) and `Callable<T>`
(can return a value and throw checked exceptions). The pool manages
thread lifecycle, queueing, and graceful shutdown.

Common factories:
- `Executors.newFixedThreadPool(n)` — n threads, unbounded queue.
- `Executors.newCachedThreadPool()` — grow as needed, shrink on idle.
- `Executors.newSingleThreadExecutor()` — one thread, serialised tasks.
- `Executors.newScheduledThreadPool(n)` — supports `schedule`, periodic.

Always **shutdown** the pool, or `try (...)` will do it for you (calls
`shutdown()` and `awaitTermination(1, TimeUnit.SECONDS)`).

## 5. `Future<T>` — the older async model

```java
Future<String> f = pool.submit(() -> slowCall());
String result = f.get();                   // blocks
String result = f.get(5, TimeUnit.SECONDS); // bounded wait
boolean done = f.isDone();
f.cancel(true);                             // may interrupt
```

`Future` is fine but limited: you can't compose Futures, can't recover
from errors cleanly, and `f.get()` is a blocking call that's easy to
forget.

## 6. `CompletableFuture<T>` — the modern async model

`CompletableFuture` is a `Future` you can *chain*. It supports
non-blocking callbacks, composition, and recovery.

```java
CompletableFuture
    .supplyAsync(() -> fetchUser(id), pool)
    .thenApply(user -> user.address())
    .thenApply(addr -> addr.country())
    .thenAccept(country -> System.out.println(country))
    .exceptionally(ex -> { log.error(ex); return null; });
```

### Source operations
```java
CompletableFuture.supplyAsync(supplier);          // runs on ForkJoinPool.commonPool
CompletableFuture.runAsync(runnable);
CompletableFuture.completedFuture(value);          // already done
```

### Transformation (return a new CompletableFuture)
```java
.thenApply(fn)                // T -> U
.thenCompose(fn)              // T -> CompletableFuture<U>  (chained async)
.thenCombine(other, bifn)     // (T, U) -> V
```

### Consumption (no return)
```java
.thenAccept(consumer)
.thenRun(runnable)
```

### Recovery
```java
.exceptionally(fn)            // T -> U on error
.handle((result, ex) -> ...)  // (T, Throwable) -> U always
```

### Composition
```java
.allOf(cf1, cf2, cf3).thenRun(() -> done());
.anyOf(cf1, cf2, cf3).thenAccept(winner -> ...);
```

## 7. `thenCompose` vs. `thenApply`

`thenApply` is for synchronous transforms; `thenCompose` is for "I
already have a `CompletableFuture<U>`, give me the result."

```java
CompletableFuture<Integer> id = ...;
CompletableFuture<User> user   = id.thenApply(this::findById);                 // ❌ but this is sync
CompletableFuture<User> user   = id.thenCompose(id_ -> findByIdAsync(id_));    // ✓ chains async
```

## 8. `volatile` and `AtomicXxx` — the low-level tools

`volatile` guarantees that reads/writes of a field are *visible* across
threads. It does **not** make compound operations atomic:

```java
private volatile int count;          // every thread sees the latest value
// NOT atomic: count++;
```

For atomic compound operations, use `AtomicInteger`:
```java
private final AtomicInteger count = new AtomicInteger();
count.incrementAndGet();             // atomic
count.compareAndSet(expected, new);  // CAS
```

`AtomicReference<T>` gives you a CAS on object references — useful for
"set the field if it's still the old value" patterns.

## 9. `synchronized` and `ReentrantLock` — when you really need a lock

Use `synchronized` for the simplest cases:
```java
public synchronized void increment() { count++; }
```

`ReentrantLock` is the more flexible alternative:
```java
private final ReentrantLock lock = new ReentrantLock();
public void increment() {
    lock.lock();
    try { count++; } finally { lock.unlock(); }
}
```
Use it when you need `tryLock`, timed waits, or interruptible locks.

**Always** use `try { ... } finally { lock.unlock(); }` to release on
exception.

## 10. Thread-local data

`ThreadLocal<T>` gives each thread its own copy of a value:
```java
private static final ThreadLocal<SimpleDateFormat> FMT =
        ThreadLocal.withInitial(() -> new SimpleDateFormat("yyyy-MM-dd"));
```

`SimpleDateFormat` is famously *not* thread-safe; `ThreadLocal` gives
each thread its own instance. (Prefer `DateTimeFormatter` from `java.time`
— it's thread-safe and immutable.)

## 11. `ConcurrentHashMap` — the right answer for a shared map

`ConcurrentHashMap` is a thread-safe, high-concurrency replacement for
`HashMap`. It allows concurrent reads and writes, and its iterators are
*weakly consistent* (no `ConcurrentModificationException`, but no
guarantee on what you see during concurrent writes).

```java
ConcurrentMap<String, Long> wordCounts = new ConcurrentHashMap<>();
// atomic increment:
wordCounts.merge(word, 1L, Long::sum);
```

For most use cases, `ConcurrentHashMap.computeIfAbsent` is the right
answer for "create and add."

## 12. `BlockingQueue` — producer / consumer

A `BlockingQueue` is a thread-safe queue that *blocks* on empty/pop and
full/push. The classic work-queue pattern:

```java
BlockingQueue<Task> queue = new ArrayBlockingQueue<>(100);

new Thread(() -> {
    while (running) queue.put(produce());
}).start();

new Thread(() -> {
    while (running) process(queue.take());
}).start();
```

`put` blocks when the queue is full; `take` blocks when empty. Use
`offer` and `poll` for non-blocking variants.

## 13. The `ExecutorService` patterns

**One-off async work:**
```java
CompletableFuture.supplyAsync(() -> fetchUser(id));
```

**A pool of work:**
```java
try (var pool = Executors.newFixedThreadPool(4)) {
    var futures = ids.stream()
        .map(id -> pool.submit(() -> fetchUser(id)))
        .toList();
    List<User> users = futures.stream().map(Future::get).toList();
}
```

**Better, with `CompletableFuture`:**
```java
try (var pool = Executors.newFixedThreadPool(4)) {
    CompletableFuture<List<User>> all = ids.stream()
        .map(id -> CompletableFuture.supplyAsync(() -> fetchUser(id), pool))
        .collect(CompletableFuture::allOf)
        .thenApply(v -> ids.stream().map(this::fetchUserSync).toList());   // simplified
}
```

## 14. Common concurrency bugs

- **Race on a non-thread-safe collection** — `ConcurrentModificationException`
  or silent corruption. Use the `Concurrent*` collections or
  `Collections.synchronizedList`.
- **Lost update** — `count++` from two threads increments only once. Use
  `AtomicInteger` or `synchronized`.
- **Visibility** — a thread reads a stale value of a non-`volatile` field.
  `volatile`, `synchronized`, or `AtomicXxx`.
- **Deadlock** — two threads each holding a lock the other needs. Avoid
  nested locks; use a single lock or `tryLock` with a timeout.
- **Forgetting to shut down an executor** — the JVM won't exit.

## 15. A worked example — a `Counter` that's thread-safe

```java
public final class Counter {
    private final AtomicLong count = new AtomicLong();
    public long increment() { return count.incrementAndGet(); }
    public long current()   { return count.get(); }
}
```

Two lines of work, no `synchronized`, fully thread-safe. The right
answer for almost every counter.

---

## Do the lab

Build a small `Counter`, an `ExecutorService` worker, and a
`CompletableFuture` pipeline. 👉 **[lab.md](./lab.md)**

Then: 👉 **[challenge.md](./challenge.md)**

## Key terms

thread · `Runnable` / `Callable<T>` · `Future<T>` · `ExecutorService` ·
`Executors.newFixedThreadPool` · `CompletableFuture` · `thenApply` /
`thenCompose` / `thenCombine` · `exceptionally` · `volatile` · `AtomicLong` /
`AtomicReference` · `synchronized` · `ReentrantLock` · `ThreadLocal` ·
`ConcurrentHashMap` · `BlockingQueue` · `submit` · `shutdown`

**Next →** [Module 12: I/O, NIO.2 & Serialization](../12-io-nio/)
