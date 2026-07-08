# Lab 11 — Concurrency Hands-On

**You'll:** build a thread-safe `Counter`, an `ExecutorService` worker,
and a `CompletableFuture` pipeline. ⏱️ ~50 min.

---

## Part A — Set up

```bash
mkdir -p ~/dev/oop11 && cd ~/dev/oop11
mkdir -p src/com/example/scheduler
```

## Part B — A thread-safe `Counter`

`src/com/example/scheduler/Counter.java`:
```java
package com.example.scheduler;

import java.util.concurrent.atomic.AtomicLong;

public final class Counter {
    private final AtomicLong count = new AtomicLong();
    public long increment() { return count.incrementAndGet(); }
    public long current()   { return count.get(); }
}
```

## Part C — A worker pool

`src/com/example/scheduler/WorkerPool.java`:
```java
package com.example.scheduler;

import java.util.List;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;

public final class WorkerPool implements AutoCloseable {
    private final ExecutorService pool;

    public WorkerPool(int n) { this.pool = Executors.newFixedThreadPool(n); }

    public <T> CompletableFuture<T> submit(java.util.concurrent.Callable<T> task) {
        return CompletableFuture.supplyAsync(() -> {
            try { return task.call(); }
            catch (Exception e) { throw new RuntimeException(e); }
        }, pool);
    }

    public void shutdown() throws InterruptedException {
        pool.shutdown();
        if (!pool.awaitTermination(5, TimeUnit.SECONDS)) pool.shutdownNow();
    }

    @Override public void close() throws Exception { shutdown(); }
}
```

## Part D — Driver

`src/com/example/scheduler/Main.java`:
```java
package com.example.scheduler;

import java.util.List;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.atomic.AtomicLong;

public class Main {
    public static void main(String[] args) throws Exception {
        // 1. Thread-safe counter, hammered by 4 threads.
        var counter = new Counter();
        try (var pool = new WorkerPool(4)) {
            var futures = new java.util.ArrayList<CompletableFuture<Void>>();
            for (int t = 0; t < 4; t++) {
                futures.add(pool.submit(() -> {
                    for (int i = 0; i < 1000; i++) counter.increment();
                    return null;
                }));
            }
            CompletableFuture.allOf(futures.toArray(CompletableFuture[]::new)).get();
            System.out.println("counter = " + counter.current() + "  (expected 4000)");

            // 2. CompletableFuture pipeline.
            CompletableFuture<String> result = CompletableFuture
                    .supplyAsync(() -> "user:42", pool)
                    .thenApply(s -> "fetched " + s)
                    .thenApply(s -> s.toUpperCase())
                    .exceptionally(ex -> "fallback: " + ex.getClass().getSimpleName());
            System.out.println("pipeline = " + result.get());
        }
    }
}
```

Compile + run:
```bash
javac -d out $(find src -name '*.java')
java -cp out com.example.scheduler.Main
```

Expected:
```
counter = 4000  (expected 4000)
pipeline = FETCHED USER:42
```

## Part E — Show the wrong way

Add a `BrokenCounter` (uses a plain `long` field) and confirm the
race:
```java
public static final class BrokenCounter {
    private long count = 0;          // not volatile, not atomic
    public void increment() { count++; }
    public long current() { return count; }
}
```

Run it in the same driver. The result will be *less than 4000* because
the increments are interleaved and lost. That's the bug `AtomicLong`
solves.

## Part F — Recovery with `handle`

Add a `CompletableFuture` step that uses `handle` to map both
success and failure:
```java
CompletableFuture<Integer> f = CompletableFuture
        .supplyAsync(() -> { throw new IllegalStateException("nope"); })
        .handle((r, ex) -> ex == null ? r : -1);
System.out.println("recovered: " + f.get());
```

Expected: `recovered: -1`.

## What you learned

- `ExecutorService` is the right way to run work concurrently.
- `CompletableFuture` chains async work, transforms, and recovers from
  errors without `try`/`catch` everywhere.
- `AtomicLong` is the right answer for counters; `volatile` alone is
  not enough.
- Shutting down the executor is non-optional; `try (...)` makes it
  automatic.
- Immutability is the easiest safety — reach for it first.

➡️ **[challenge.md](./challenge.md)** then [Module 12](../12-io-nio/).
