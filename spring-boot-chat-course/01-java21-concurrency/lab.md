# Lab 01 — Feel the Difference

**You'll:** create a million virtual threads, measure the cost of each thread
model, catch a pinned carrier thread red-handed, watch `synchronized` collapse
throughput, and build the unbounded-concurrency trap on purpose.

⏱️ ~75 min. Everything is a single-file `java` program — no build tool needed.
Work in `spring-boot-chat-course/01-java21-concurrency/code/`.

```bash
cd spring-boot-chat-course/01-java21-concurrency/code
ulimit -n 100000          # you'll need it in Part D
```

---

## Part A — A million threads

Create `MillionThreads.java`:

```java
import java.time.Duration;
import java.time.Instant;
import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicLong;

public class MillionThreads {
    public static void main(String[] args) throws Exception {
        String kind = args.length > 0 ? args[0] : "virtual";
        int n = args.length > 1 ? Integer.parseInt(args[1]) : 1_000_000;

        var done = new AtomicLong();
        var latch = new CountDownLatch(n);
        Instant start = Instant.now();

        ThreadFactory factory = kind.equals("virtual")
                ? Thread.ofVirtual().factory()
                : Thread.ofPlatform().factory();

        try (var executor = Executors.newThreadPerTaskExecutor(factory)) {
            for (int i = 0; i < n; i++) {
                executor.submit(() -> {
                    try {
                        Thread.sleep(Duration.ofSeconds(1));   // pretend I/O
                        done.incrementAndGet();
                    } catch (InterruptedException ignored) {
                    } finally {
                        latch.countDown();
                    }
                });
            }
            System.out.printf("submitted %,d %s threads in %d ms%n",
                    n, kind, Duration.between(start, Instant.now()).toMillis());
            latch.await();
        }

        System.out.printf("completed %,d in %d ms  |  peak RSS %,d KB%n",
                done.get(), Duration.between(start, Instant.now()).toMillis(), rss());
    }

    static long rss() throws Exception {
        var status = java.nio.file.Path.of("/proc/self/status");
        if (!java.nio.file.Files.exists(status)) return -1;          // macOS
        for (String line : java.nio.file.Files.readAllLines(status))
            if (line.startsWith("VmHWM:")) return Long.parseLong(line.replaceAll("\\D+", ""));
        return -1;
    }
}
```

Run the virtual version first:

```bash
java MillionThreads.java virtual 1000000
```

**Expected** (reference machine: 8-core / 16 GB):
```
submitted 1,000,000 virtual threads in 1834 ms
completed 1,000,000 in 3211 ms  |  peak RSS 1,204,880 KB
```

One million concurrent threads, each sleeping a full second, finished in a
little over three seconds using ~1.2 GB. **They all slept simultaneously** — if
they'd been serialized it would have taken 11 days.

Now the platform version. Start small:

```bash
java MillionThreads.java platform 10000
```

**Expected:**
```
submitted 10,000 platform threads in 892 ms
completed 10,000 in 1993 ms  |  peak RSS 812,336 KB
```

10,000 platform threads use **more memory than a million virtual ones**.

Now try to break it:

```bash
java MillionThreads.java platform 1000000
```

**Expected** — a crash, somewhere between 10k and 80k threads depending on your
`ulimit -u`, `threads-max`, and `vm.max_map_count`:
```
[0.834s][warning][os,thread] Failed to start thread "Unnamed thread" - pthread_create failed (EAGAIN)
Exception in thread "main" java.lang.OutOfMemoryError: unable to create native thread: possibly out of memory or process/resource limits reached
```

✅ **That exception is the lesson.** Record the thread count where it died in
`results.md`. On the reference machine it was **~32,000**.

Check what actually stopped you:
```bash
ulimit -u                          # max user processes (threads count!)
cat /proc/sys/kernel/threads-max
cat /proc/sys/vm/max_map_count     # each thread stack needs a mapping
```

---

## Part B — Where is a virtual thread actually running?

Create `Mounting.java`:

```java
public class Mounting {
    public static void main(String[] args) throws Exception {
        Runnable task = () -> {
            Thread t = Thread.currentThread();
            System.out.printf("%-22s virtual=%-5s carrier-info=%s%n",
                    t.getName().isEmpty() ? "(unnamed)" : t.getName(),
                    t.isVirtual(), t);
            try { Thread.sleep(50); } catch (InterruptedException ignored) {}
            System.out.printf("   after sleep, now on: %s%n", Thread.currentThread());
        };

        System.out.println("--- platform ---");
        Thread p = Thread.ofPlatform().name("plat-1").start(task);
        p.join();

        System.out.println("--- virtual ---");
        for (int i = 0; i < 4; i++) Thread.ofVirtual().name("v-" + i).start(task).join();
    }
}
```

```bash
java Mounting.java
```

**Expected** (carrier worker numbers will vary):
```
--- platform ---
plat-1                 virtual=false carrier-info=Thread[#31,plat-1,5,main]
   after sleep, now on: Thread[#31,plat-1,5,main]
--- virtual ---
v-0                    virtual=true  carrier-info=VirtualThread[#33,v-0]/runnable@ForkJoinPool-1-worker-1
   after sleep, now on: VirtualThread[#33,v-0]/runnable@ForkJoinPool-1-worker-2
v-1                    virtual=true  carrier-info=VirtualThread[#35,v-1]/runnable@ForkJoinPool-1-worker-1
   after sleep, now on: VirtualThread[#35,v-1]/runnable@ForkJoinPool-1-worker-3
```

✅ Look carefully at `v-0`: it started on `worker-1` and resumed on `worker-2`.
**It changed carrier threads across a `sleep()`.** That is the unmount/remount
cycle, visible.

This is also why `ThreadLocal` keyed to a carrier would be nonsense, and why any
library caching state "per thread" needs re-examining under virtual threads.

---

## Part C — Catch a pinned thread

This is the failure mode that silently destroys virtual-thread performance.

Create `Pinning.java`:

```java
import java.time.Duration;
import java.time.Instant;
import java.util.concurrent.*;
import java.util.concurrent.locks.ReentrantLock;

public class Pinning {
    static final Object monitor = new Object();
    static final ReentrantLock lock = new ReentrantLock();

    public static void main(String[] args) throws Exception {
        int n = 200;
        System.out.println("carriers = " + Runtime.getRuntime().availableProcessors());
        run("synchronized (PINS)", n, Pinning::withSynchronized);
        run("ReentrantLock      ", n, Pinning::withLock);
    }

    static void withSynchronized() {
        synchronized (monitor) { sleep(100); }
    }

    static void withLock() {
        lock.lock();
        try { sleep(100); } finally { lock.unlock(); }
    }

    static void run(String label, int n, Runnable body) throws Exception {
        var latch = new CountDownLatch(n);
        Instant start = Instant.now();
        try (var ex = Executors.newVirtualThreadPerTaskExecutor()) {
            for (int i = 0; i < n; i++)
                ex.submit(() -> { try { body.run(); } finally { latch.countDown(); } });
            latch.await();
        }
        System.out.printf("%s  %d tasks x 100ms  ->  %,d ms total%n",
                label, n, Duration.between(start, Instant.now()).toMillis());
    }

    static void sleep(long ms) {
        try { Thread.sleep(ms); } catch (InterruptedException ignored) {}
    }
}
```

Both versions hold an exclusive lock for 100 ms, so both *should* take
`200 × 100ms = 20 s` of serialized lock time. Run it:

```bash
java Pinning.java
```

**Expected:**
```
carriers = 8
synchronized (PINS)  200 tasks x 100ms  ->  20,143 ms total
ReentrantLock        200 tasks x 100ms  ->  20,096 ms total
```

Nearly identical — because with mutual exclusion the lock, not the carrier, is
the bottleneck. **Now make the sleep happen *outside* the critical section**,
which is what real code does when it holds a lock while calling a database.
Change `withSynchronized` and `withLock` so only a trivial operation is guarded
but the *blocking* call sits inside:

```java
    static void withSynchronized() {
        synchronized (monitor) { sleep(100); }        // blocking INSIDE the monitor
    }
```

...and add a third variant that blocks with no lock at all:

```java
    static void withNothing() { sleep(100); }
```
```java
        run("no lock at all    ", n, Pinning::withNothing);
```

Re-run:

**Expected:**
```
carriers = 8
synchronized (PINS)  200 tasks x 100ms  ->  20,143 ms total
ReentrantLock        200 tasks x 100ms  ->  20,096 ms total
no lock at all       200 tasks x 100ms  ->     213 ms total
```

✅ **213 ms vs 20 seconds — a 94× difference.** Without a lock, all 200 virtual
threads unmount during `sleep` and run concurrently. That's the model working.

Now prove the pinning specifically. Add `jdk.tracePinnedThreads`:

```bash
java -Djdk.tracePinnedThreads=full Pinning.java 2>&1 | head -20
```

**Expected** — the JVM names the exact frame that pinned the carrier:
```
Thread[#34,ForkJoinPool-1-worker-1,5,CarrierThreads]
    java.base/java.lang.VirtualThread$VThreadContinuation.onPinned(VirtualThread.java:183)
    java.base/java.lang.VirtualThread.parkOnCarrierThread(VirtualThread.java:691)
    java.base/java.lang.VirtualThread.park(VirtualThread.java:635)
    java.base/java.lang.Thread.sleep(Thread.java:507)
    Pinning.sleep(Pinning.java:41)
    Pinning.withSynchronized(Pinning.java:16) <== monitors:1
```

✅ `<== monitors:1` is the smoking gun: this frame holds a monitor, so the
virtual thread could not unmount.

> **Put this flag in your dev profile.** In Module 04 you'll add it to the Pulse
> app's run configuration, and in Module 06 a single `synchronized` block will
> cost you a benchmark.

**JDK 24+ note:** JEP 491 removes `synchronized` pinning, so on 24+ the
`synchronized` variant performs like the lock variant. Java 21 is LTS and what
this course targets, so the rule stands — and native-frame pinning persists on
every version.

---

## Part D — Sockets, not sleeps

`Thread.sleep` is a fine proxy, but let's prove it with real I/O. Create
`SocketHolder.java`:

```java
import java.io.*;
import java.net.*;
import java.util.concurrent.*;

public class SocketHolder {
    public static void main(String[] args) throws Exception {
        String kind = args[0];              // virtual | platform
        int n = Integer.parseInt(args[1]);

        var server = new ServerSocket(9200, 65535);
        Thread.ofPlatform().daemon().start(() -> {
            var held = new java.util.ArrayList<Socket>();
            try { while (true) held.add(server.accept()); } catch (IOException ignored) {}
        });

        ThreadFactory f = kind.equals("virtual")
                ? Thread.ofVirtual().factory() : Thread.ofPlatform().factory();
        var ready = new CountDownLatch(n);
        var release = new CountDownLatch(1);

        for (int i = 0; i < n; i++) {
            f.newThread(() -> {
                try (var s = new Socket("127.0.0.1", 9200)) {
                    ready.countDown();
                    release.await();                       // hold the socket open
                } catch (Exception ignored) { ready.countDown(); }
            }).start();
        }

        ready.await();
        System.gc(); Thread.sleep(500);
        var mb = java.lang.management.ManagementFactory.getMemoryMXBean();
        long heap = mb.getHeapMemoryUsage().getUsed();
        System.out.printf("%s: %,d sockets held | heap %,d KB | %.1f KB/conn | threads %d%n",
                kind, n, heap / 1024, heap / 1024.0 / n,
                java.lang.management.ManagementFactory.getThreadMXBean().getThreadCount());
        release.countDown();
    }
}
```

```bash
java SocketHolder.java virtual 20000
java SocketHolder.java platform 20000
```

**Expected:**
```
virtual: 20,000 sockets held | heap 47,208 KB | 2.4 KB/conn | threads 14
platform: (crashes, or)
platform: 20,000 sockets held | heap 38,112 KB | 1.9 KB/conn | threads 20014
```

✅ Note the last column. The virtual run holds 20,000 connections with **14 OS
threads**. The platform run needs 20,014 — if it survives at all.

> If the platform run fails with `pthread_create failed`, that's the expected
> outcome and the reason this course exists. Record the number.

---

## Part E — Build the unbounded-concurrency trap

This is the mistake you'll make in production if nobody shows it to you first.

Create `Unbounded.java`:

```java
import java.time.*;
import java.util.concurrent.*;

public class Unbounded {
    // Pretend this is a Hikari pool of 20 database connections.
    static final Semaphore dbPool = new Semaphore(20);

    static void queryDatabase() throws InterruptedException {
        dbPool.acquire();
        try { Thread.sleep(50); }            // a 50ms query
        finally { dbPool.release(); }
    }

    public static void main(String[] args) throws Exception {
        int requests = 5000;

        // ---- old world: a bounded pool of 200 platform threads ----
        time("bounded 200-thread pool", requests,
             Executors.newFixedThreadPool(200));

        // ---- new world: a virtual thread per request ----
        time("virtual thread per task", requests,
             Executors.newVirtualThreadPerTaskExecutor());
    }

    static void time(String label, int requests, ExecutorService ex) throws Exception {
        var latencies = new java.util.concurrent.ConcurrentLinkedQueue<Long>();
        Instant start = Instant.now();
        var latch = new CountDownLatch(requests);
        for (int i = 0; i < requests; i++) {
            ex.submit(() -> {
                long t0 = System.nanoTime();
                try { queryDatabase(); } catch (InterruptedException ignored) {}
                latencies.add((System.nanoTime() - t0) / 1_000_000);
                latch.countDown();
            });
        }
        latch.await();
        ex.close();
        var sorted = latencies.stream().sorted().toList();
        System.out.printf("%-26s total %,5d ms | p50 %,4d ms | p99 %,5d ms%n",
                label, Duration.between(start, Instant.now()).toMillis(),
                sorted.get(sorted.size() / 2), sorted.get((int) (sorted.size() * 0.99)));
    }
}
```

```bash
java Unbounded.java
```

**Expected:**
```
bounded 200-thread pool     total 12,631 ms | p50   50 ms | p99   109 ms
virtual thread per task     total 12,584 ms | p50 6,241 ms | p99 12,402 ms
```

✅ **Read that carefully.** Total throughput is *identical* — both are gated by
the 20-connection pool, so both take ~12.6 s. But:

- Bounded pool: p99 = **109 ms**. Requests queue *before* they start, in the
  executor's queue.
- Virtual threads: p99 = **12.4 seconds**. All 5,000 requests start immediately
  and then all wait on the semaphore.

The work is the same; the **queueing moved**, and it moved somewhere that
destroys latency and holds 5,000 requests' worth of memory. Nothing crashed,
nothing logged an error, and your dashboard shows 4% CPU.

Now fix it — add an explicit admission limit *before* accepting work:

```java
    static final Semaphore admission = new Semaphore(200);
    // in the virtual-thread submit:
    admission.acquire();
    try { queryDatabase(); } finally { admission.release(); }
```

**Expected after the fix:**
```
virtual thread + admission  total 12,602 ms | p50   52 ms | p99   118 ms
```

✅ Same throughput, latency restored. **This is the single most important
practical lesson about virtual threads**, and it's why Module 06's challenge
asks you to find Pulse's unbounded queue.

---

## Part F — Structured concurrency

Create `Fanout.java` (uses a preview API):

```java
import java.util.concurrent.StructuredTaskScope;
import java.util.concurrent.StructuredTaskScope.Subtask;

public class Fanout {
    record RoomView(String room, java.util.List<String> members, int unread) {}

    public static void main(String[] args) throws Exception {
        System.out.println(load("general", false));
        try { System.out.println(load("general", true)); }
        catch (Exception e) { System.out.println("failed fast: " + e.getCause().getMessage()); }
    }

    static RoomView load(String roomId, boolean breakIt) throws Exception {
        try (var scope = new StructuredTaskScope.ShutdownOnFailure()) {
            Subtask<String> room = scope.fork(() -> { sleep(100); return roomId; });
            Subtask<java.util.List<String>> members = scope.fork(() -> {
                sleep(150);
                if (breakIt) throw new IllegalStateException("member service down");
                return java.util.List.of("alice", "bob");
            });
            Subtask<Integer> unread = scope.fork(() -> { sleep(2000); return 7; });

            scope.join();
            scope.throwIfFailed();
            return new RoomView(room.get(), members.get(), unread.get());
        }
    }

    static void sleep(long ms) {
        try { Thread.sleep(ms); } catch (InterruptedException e) { throw new RuntimeException(e); }
    }
}
```

```bash
java --enable-preview --source 21 Fanout.java
```

**Expected:**
```
Note: Fanout.java uses preview features of Java SE 21.
RoomView[room=general, members=[alice, bob], unread=7]
failed fast: member service down
```

✅ Time the second call — it returns in ~150 ms, not 2,000 ms. When `members`
failed at 150 ms, the scope **cancelled the still-running `unread` subtask**.
With a raw `ExecutorService` that 2-second call would have run to completion,
burning a connection nobody was waiting for.

---

## What you measured

Record all of these in `results.md`:

| Measurement | Reference | Yours |
|-------------|-----------|-------|
| Virtual threads created before failure | 1,000,000 ✅ (~1.2 GB) | |
| Platform threads created before failure | ~32,000 ❌ OOM | |
| RSS: 10k platform vs 1M virtual | 812 MB vs 1.2 GB | |
| `synchronized` + block vs no lock | 20,143 ms vs 213 ms (94×) | |
| OS threads holding 20k sockets (virtual) | 14 | |
| p99 with/without admission control | 12,402 ms vs 118 ms | |

---

## What you learned

- A virtual thread is a **heap object with a continuation**, mounted onto a
  carrier only while running. Blocking I/O unmounts it; that's the whole trick.
- **Pinning** (`synchronized`, native frames) breaks the trick and returns you to
  the platform ceiling. `-Djdk.tracePinnedThreads=full` finds it.
- **Concurrency became free; resources did not.** Thread pools used to be
  accidental rate limiters. You now need `Semaphore`s deliberately.
- Structured concurrency makes fan-out cancellable and leak-free.

Now do [`challenge.md`](./challenge.md).

Then: [Module 02 — Spring Boot Fast-Track](../02-spring-fast-track/).
