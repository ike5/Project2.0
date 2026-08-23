# Module 01 — Java 21 Concurrency for Real-Time

**Goal:** Understand *why* a JVM can now hold a million concurrent connections
when five years ago it choked at thirty thousand — deeply enough that you can
predict which of your own code will scale and which will silently ruin it.

⏱️ ~4 hours · **Prerequisites:** Module 00. You should already understand
concurrency in *some* language (goroutines, asyncio, the Node event loop, Go
channels). This module maps what you know onto the JVM and then shows you the
parts that don't map.

---

## The problem this module exists to solve

Here is the entire crisis of server-side concurrency in one code block:

```java
// The most natural way to write a server. Also, historically, the reason
// your server dies at 5,000 users.
while (true) {
    Socket client = serverSocket.accept();
    new Thread(() -> handle(client)).start();   // <-- one OS thread per user
}
```

`handle(client)` spends 99.99% of its life blocked, waiting for the human on the
other end to type something. During that wait it holds:

- an OS thread (a kernel scheduling entity),
- a stack (1 MB of reserved address space; ~70 KB actually touched),
- a slot in the kernel's run queue bookkeeping.

Ten thousand idle users cost ten thousand OS threads. At ~32,000 threads a
typical Linux JVM simply refuses to create more.

Every solution to this problem — Node's event loop, Go's goroutines, Python's
asyncio, Netty, and now Java's virtual threads — is an answer to the same
question:

> **How do we stop paying for an OS thread while we wait?**

There are exactly two families of answer, and this course builds on both so you
can compare them directly (Module 15).

---

## Answer A — Don't block. Ever. (The event loop)

Node, Netty, and WebFlux take this path. One thread runs a loop:

```
loop forever:
    ready = epoll_wait(all_my_sockets)     ← ONE syscall, thousands of sockets
    for each socket in ready:
        run its callback (must not block!)
```

**The win:** one thread, tens of thousands of connections. Memory per connection
is just the socket buffer plus your own state.

**The cost:** the word *must* in "must not block." Every I/O call in your entire
stack has to be non-blocking, or one slow database driver stalls every connection
that thread owns. This is why the reactive ecosystem needs its own driver for
everything — R2DBC instead of JDBC, Lettuce instead of Jedis. Step outside it
once and you've built a very complicated slow server.

And the code inverts. This:
```java
var user = findUser(id);
var rooms = findRooms(user);
return render(user, rooms);
```
becomes this:
```java
return findUser(id)
    .flatMap(user -> findRooms(user)
        .map(rooms -> render(user, rooms)));
```
A stack trace from inside that tells you almost nothing about how you got there.

---

## Answer B — Block, but make blocking cheap (Virtual threads)

Java 21's answer (JEP 444). Keep the natural code. Change what a thread *is*.

A **virtual thread** is not an OS thread. It's an object on the heap holding a
continuation — a stack that the JVM can copy off and back on at will. The JVM
runs virtual threads on a small pool of real OS threads called **carrier
threads** (a `ForkJoinPool`, sized to your core count by default).

The magic is one rule:

> When a virtual thread performs a blocking I/O operation, the JVM **unmounts**
> it from its carrier — copies its stack to the heap, and frees the carrier to
> run someone else. When the I/O completes, it's mounted again and resumes on
> the next line.

```
     Virtual threads (millions, on the heap)
     ┌──┐┌──┐┌──┐┌──┐┌──┐┌──┐┌──┐┌──┐┌──┐┌──┐┌──┐┌──┐
     │v1││v2││v3││v4││v5││v6││v7││v8││v9││..││..││vN│
     └┬─┘└──┘└┬─┘└──┘└──┘└┬─┘└──┘└──┘└──┘└──┘└──┘└──┘
      │mounted│           │
   ┌──▼───┐┌──▼───┐┌──────┐┌──────┐
   │ CT-1 ││ CT-2 ││ CT-3 ││ CT-4 │   Carrier threads (= your core count)
   └──────┘└──────┘└──────┘└──────┘
        ↑ real OS threads. Only these cost kernel resources.
```

`Thread.sleep(1000)` inside a virtual thread doesn't sleep an OS thread. Reading
from a socket doesn't block one. The blocking-looking code is *actually*
non-blocking underneath — the JVM did the callback transformation for you, in
the runtime, where a debugger can still see through it.

**This is why the course's primary build uses virtual threads:** you get the
event loop's efficiency with the imperative code's debuggability.

---

## The catch: pinning

The unmount trick doesn't always work. When a virtual thread **cannot** unmount,
it's **pinned** — it holds its carrier hostage while it blocks, and you're back
to the platform-thread ceiling with extra steps.

Two causes:

1. **Inside a `synchronized` block.** The JVM's monitor implementation ties the
   lock to the carrier thread. *(Fixed in JDK 24 by JEP 491; on Java 21 it is
   very real, and Java 21 is what this course targets.)*
2. **Inside a native frame** — a JNI call, or certain filesystem operations.

```java
// PINS the carrier for the whole DB call.
synchronized (this) {
    var row = jdbc.query(...);      // carrier blocked, nobody else can use it
}

// Does NOT pin — ReentrantLock is virtual-thread-aware.
lock.lock();
try {
    var row = jdbc.query(...);      // carrier released during the blocking call
} finally {
    lock.unlock();
}
```

> **The rule for this course:** in any code path a virtual thread might touch,
> use `ReentrantLock`, not `synchronized`. You'll detect violations with
> `-Djdk.tracePinnedThreads=full` in the lab, and it is *not* a hypothetical —
> a synchronized block in a hot chat path costs you an order of magnitude.

### The other catch: thread-locals and pooling

Virtual threads are **cheap and disposable**. Two consequences:

- **Never pool them.** `Executors.newVirtualThreadPerTaskExecutor()` creates one
  per task, on purpose. Pooling a virtual thread is like pooling a `String`.
- **`ThreadLocal` gets expensive** when you have a million threads instead of
  200. Anything that stashes per-thread state — some MDC logging setups,
  security contexts, connection caches — quietly multiplies. Java 21 offers
  `ScopedValue` (preview) as the successor; the lab measures the cost.

---

## What virtual threads do *not* fix

This is the part that separates people who read the release notes from people
who've run this in production.

| Problem | Do virtual threads help? |
|---------|-------------------------|
| Many connections mostly idle | ✅ **Yes.** This is exactly the case. |
| CPU-bound work | ❌ No. You still have N cores. A million threads doing math is a million threads fighting over 8 cores. |
| A limited downstream resource | ❌ **No — and this is the dangerous one.** |
| Memory per connection | ⚠️ Partly. The thread is cheap; your session state isn't. |

### The unbounded-concurrency trap

Old code was accidentally protected. A 200-thread pool meant at most 200
simultaneous database calls — the pool *was* your rate limiter. Replace it with
virtual threads and:

```java
// Every request now gets its own thread. 10,000 concurrent requests =
// 10,000 threads all trying to borrow from a 20-connection Hikari pool.
var executor = Executors.newVirtualThreadPerTaskExecutor();
```

Nothing crashes. Instead, 9,980 virtual threads queue on the connection pool,
each holding its request state, and your p99 goes to eight seconds while CPU
sits at 4%. **The bottleneck moved, it didn't disappear**, and it moved somewhere
with no backpressure signal.

The fix is to make the limit explicit — a `Semaphore` around the scarce resource:

```java
private final Semaphore dbPermits = new Semaphore(50);

public Message save(Message m) throws InterruptedException {
    dbPermits.acquire();
    try { return repository.save(m); }
    finally { dbPermits.release(); }
}
```

> **The principle:** with virtual threads, *concurrency is free but resources
> are not*. You must now limit resources deliberately, because the thread pool
> is no longer doing it for you by accident. Module 06 makes this failure happen
> to you on purpose.

---

## Structured concurrency

Chat fan-out is naturally parallel: "load the room, load the members, load my
unread count, then render." Done with raw threads, that's leak-prone — if one
fails, do the others get cancelled? If the caller gives up, does anything stop?

`StructuredTaskScope` (preview in 21) makes a group of subtasks a single unit
with a lifetime:

```java
try (var scope = new StructuredTaskScope.ShutdownOnFailure()) {
    Subtask<Room>       room    = scope.fork(() -> roomService.find(roomId));
    Subtask<List<User>> members = scope.fork(() -> memberService.list(roomId));
    Subtask<Integer>    unread  = scope.fork(() -> unreadService.count(userId, roomId));

    scope.join();              // wait for all
    scope.throwIfFailed();     // if ANY failed, the others were cancelled

    return new RoomView(room.get(), members.get(), unread.get());
}   // scope closes: nothing can outlive this block. Guaranteed.
```

Three guarantees you'd otherwise hand-roll: no subtask outlives the block, a
failure cancels its siblings, and the caller's cancellation propagates down.

*(Preview API in 21 — needs `--enable-preview`. The lab shows both this and the
plain-`ExecutorService` equivalent you'd ship today.)*

---

## The Java Memory Model, in the amount you need

You will keep a map of connected sessions, mutated from many threads. Two facts
prevent 90% of the bugs:

**1. Without synchronization, there is no guarantee another thread ever sees
your write.** Not "sees it late" — *ever*. The JIT can hoist a field read out of
a loop entirely.

```java
private boolean running = true;              // BROKEN: may loop forever
private volatile boolean running = true;     // correct: establishes happens-before
```

**2. Compound operations on thread-safe collections are still races.**

```java
// RACE — two threads can both see null and both create a room
if (!rooms.containsKey(id)) rooms.put(id, new Room(id));

// ATOMIC — computeIfAbsent does the whole thing under one lock stripe
rooms.computeIfAbsent(id, Room::new);
```

The collections you'll actually use:

| Type | Use for |
|------|---------|
| `ConcurrentHashMap` | Session registry, room→subscribers. `computeIfAbsent`, `merge`, `compute` are your atomics. |
| `CopyOnWriteArrayList` | Small, read-mostly lists (subscribers of a tiny room). **Never** for a big or write-heavy list — every write copies the array. |
| `LongAdder` | High-contention counters (messages sent). Much better than `AtomicLong` under contention. |
| `ConcurrentLinkedQueue` | Unbounded MPSC queues. Note: **unbounded** — see the OOM discussion above. |
| `ArrayBlockingQueue` | Bounded. When you want backpressure instead of an OOM. |

> ⚠️ `ConcurrentHashMap.size()` is an estimate under concurrent modification.
> Don't build logic on it; use a `LongAdder` if you need an exact count.

---

## Decision guide

| Situation | Choice |
|-----------|--------|
| Handling many blocking I/O-bound requests | **Virtual threads** |
| CPU-bound parallel computation | **`ForkJoinPool` / parallel streams** — a fixed pool sized to cores |
| Existing reactive stack, non-blocking drivers throughout | **Stay reactive** (Module 15) |
| Absolute maximum connections per gigabyte | **Event loop / Netty** — measurably better, at a real cost in complexity |
| Fan-out where a failure should cancel siblings | **`StructuredTaskScope`** |
| Protecting a scarce downstream resource | **`Semaphore`** — always, now that pools no longer do it for you |

---

## Why not just use Kotlin coroutines / Go / Node?

Fair question; here's the honest comparison.

- **Go goroutines** are the closest analogue and predate virtual threads by a
  decade. Same model (M:N scheduling, cheap stacks, blocking-style code). Go's
  runtime is more mature at it. Java's advantage is the ecosystem you're
  presumably already in, plus JFR/JMX-grade observability.
- **Kotlin coroutines** are compile-time transformed, not runtime-scheduled.
  Cheaper still, but they colour your functions (`suspend`) and you must use
  suspend-aware libraries — same constraint as reactive, nicer syntax.
- **Node** gives you one event loop per process. Excellent for I/O fan-out,
  awkward for CPU work, and you scale by running more processes.

Virtual threads' distinct claim: **existing blocking libraries get faster
without being rewritten**. JDBC, `InputStream`, `synchronized`-free legacy code
— it all just unmounts now. No other option on this list can say that.

---

## What's next

The lab makes all of this concrete: you'll create a million virtual threads,
watch a `synchronized` block destroy your throughput, catch a pinned thread in
the act, and build the unbounded-concurrency trap so you recognize it later.

See you in [`lab.md`](./lab.md).
