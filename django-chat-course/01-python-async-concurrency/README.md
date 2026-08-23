# Module 01 — Python Async & Concurrency for Real-Time

**Goal:** Understand *why* a single Python process can hold tens of thousands of
concurrent connections on one core — and *why* it then hits a wall the JVM
doesn't, so you can predict which of your own code will scale and which will
silently stall every connection on the worker.

⏱️ ~4 hours · **Prerequisites:** Module 00. You should be comfortable in Python
and understand concurrency in *some* form (threads, Node's event loop,
goroutines, asyncio at a beginner level). This module builds the exact mental
model the rest of the course stands on.

> **This is the Python twin of the JVM course's
> [`01-java21-concurrency`](../../spring-boot-chat-course/01-java21-concurrency/).**
> Same problem — hold a huge number of mostly-idle connections without paying for
> an OS thread each. The JVM's answer is **virtual threads**: keep writing
> blocking code, make threads cheap. Python's answer is the **event loop plus a
> process-per-core worker model**: stop writing blocking code, and scale CPU by
> running more processes. Read both modules. Where they converge and where they
> diverge *is* the lesson.

---

## The problem this module exists to solve

Here is the entire crisis of server-side concurrency, in Python:

```python
# The most natural way to write a server. Also, historically, the reason
# your Python server dies at a few thousand users.
while True:
    client, addr = server_socket.accept()
    threading.Thread(target=handle, args=(client,)).start()   # one OS thread per user
```

`handle(client)` spends 99.99% of its life blocked, waiting for the human on the
other end to type. During that wait it holds:

- an OS thread (a kernel scheduling entity),
- a stack (megabytes of reserved address space),
- a slot in the kernel's run-queue bookkeeping,
- and — this is the Python-specific tax — it contends for the **GIL** every time
  it wakes up.

You measured the wall in Module 00's challenge: ~32,000 threads and the process
dies with `can't start new thread`, while a *million* asyncio Tasks fit in
1.4 GB. Ten thousand idle users cannot each own an OS thread. Every modern answer
to this — Node's event loop, Go's goroutines, Java's virtual threads, Python's
asyncio — answers the same question:

> **How do we stop paying for an OS thread while we wait?**

There are two families of answer. The JVM course builds on both (threads-that-
are-cheap and event-loops) so it can compare them in Module 15. **Python only has
one of them**, and understanding *why* is half this module.

---

## The event loop, concretely

Python's answer is the event loop. One thread runs this, forever:

```
loop forever:
    ready = epoll_wait(all_my_sockets)      ← ONE syscall, thousands of sockets
    for each socket in ready:
        resume the coroutine waiting on it  ← runs until its next `await`
```

A **coroutine** is a function defined with `async def`. Calling it doesn't run
it — it returns a coroutine object, a resumable computation. `await` is the point
where the coroutine says *"I'm about to wait for I/O; suspend me and go run
someone else."* The event loop parks that coroutine, remembers which socket it's
waiting on, and moves on. When `epoll` reports the socket is ready, the loop
resumes the coroutine on the next line after its `await`.

```python
async def handle(reader, writer):
    data = await reader.read(100)     # SUSPENDS here — the one thread goes elsewhere
    writer.write(data)                # resumes here when bytes arrive
    await writer.drain()              # SUSPENDS again if the send buffer is full
```

A **Task** is a coroutine the loop is actively driving — `asyncio.create_task()`
wraps a coroutine in a Task and schedules it. A million Tasks is a million heap
objects the one loop cycles through; it is *not* a million threads. That's the
whole trick, and it's why Module 00 fit a million of them in 1.4 GB.

```
     Coroutines / Tasks (tens of thousands, on the heap)
     ┌──┐┌──┐┌──┐┌──┐┌──┐┌──┐┌──┐┌──┐┌──┐┌──┐┌──┐┌──┐
     │c1││c2││c3││c4││c5││c6││c7││c8││c9││..││..││cN│
     └┬─┘└──┘└┬─┘└──┘└──┘└┬─┘└──┘└──┘└──┘└──┘└──┘└──┘
      │       │await       │
   ┌──▼───────▼────────────▼──────────────────────┐
   │              ONE event loop                    │
   │         (one OS thread, one core)              │
   └────────────────────┬──────────────────────────┘
                        │ epoll_wait
                   ┌────▼────┐
                   │ kernel  │  thousands of sockets, one syscall
                   └─────────┘
```

**The win:** one thread, tens of thousands of connections, ~45 KB of heap per
connection (Module 06 measures it), no thread-per-user ceiling.

**The cost — and it is the entire ballgame:** every `await` is cooperative. The
loop only regains control *when a coroutine reaches an `await`*. If a coroutine
does something that takes 200 ms **without awaiting** — a synchronous database
call, a big JSON parse, a `time.sleep`, a tight CPU loop — the one thread is
stuck in it, and **every other connection on that loop is frozen** until it
returns. Not slowed. Frozen. This is the single most important operational fact
in the course, and the lab makes it happen to you.

> **"Blocking the event loop is the whole ballgame."** On the JVM, a blocking
> call inside a virtual thread just unmounts and someone else runs. In Python
> asyncio there is no unmount — a blocking call *is* the loop, so it stalls
> everyone. This is why Django's synchronous ORM is dangerous inside an async
> consumer, and it's the through-line from here to Module 15.

---

## Answer A vs Answer B — and why Python only gets A

The JVM course frames two answers. Restated for Python:

- **Answer A — Don't block, ever (the event loop).** Node, asyncio, and (in this
  course) Django Channels take this path. One thread, non-blocking I/O, cheap
  concurrency — at the cost that every I/O call in the hot path must be
  non-blocking, or you stall the loop. This is asyncio.
- **Answer B — Block, but make blocking cheap (green/virtual threads).** Go's
  goroutines and Java 21's virtual threads. Keep the natural blocking code; the
  runtime unmounts the thread during I/O.

**Python has no Answer B.** There is no virtual thread, no goroutine, no runtime
that unmounts a blocked Python call. (`gevent`/`eventlet` monkey-patch the
stdlib to fake it and are their own bag of sharp edges; asyncio is where the
ecosystem, and Django Channels, actually is.) So Python's realtime story is
**Answer A for I/O concurrency, plus processes for CPU** — which brings us to the
GIL.

---

## The GIL, and why there are no virtual threads

The **Global Interpreter Lock** is a single mutex inside CPython that guarantees
only **one thread executes Python bytecode at a time**, per interpreter. It's not
a bug; it's what keeps reference-counting memory management fast and correct
without locking every object. But it has one enormous consequence:

> **One Python process gets you one core's worth of CPU for Python code.** Ten
> threads doing arithmetic don't run in parallel — they take turns holding the
> GIL. Threads help only when they're *blocked on I/O* (the GIL is released
> during blocking syscalls), and asyncio does that far more efficiently anyway.

So the two things you cannot do in Python that you can on the JVM:

1. **You cannot make CPU-bound work parallel with threads.** N threads doing
   JSON encoding of N fan-out messages don't use N cores; they use one, serially,
   plus lock-handoff overhead. The JVM's virtual threads *also* don't fix CPU-
   bound work (its Module 01 says so too), but the JVM at least runs its carrier
   threads truly in parallel across cores for the CPU it does have. CPython gives
   you exactly one core per process.

2. **You cannot have virtual threads.** A virtual thread's whole premise is that
   many of them run their (blocking) code across a pool of real threads,
   preempted and rescheduled by the runtime. The GIL makes "many threads running
   Python in parallel" impossible, so that model has nothing to stand on.

### The consequence: one worker process per core

If one process = one core, then to use an 8-core box you run **8 worker
processes**, each with its own interpreter, its own GIL, its own event loop:

```bash
uvicorn pulse.asgi:application --workers 8      # 8 processes, one per core
```

```
     8-core box
   ┌──────────┐┌──────────┐┌──────────┐┌──────────┐
   │ worker 0 ││ worker 1 ││ worker 2 ││ worker 3 │   ... 8 total
   │ loop 0   ││ loop 1   ││ loop 2   ││ loop 3   │
   │ GIL 0    ││ GIL 1    ││ GIL 2    ││ GIL 3    │
   └──────────┘└──────────┘└──────────┘└──────────┘
        │           │            │           │
   each holds its own connections. They share NOTHING in memory.
```

This is the **process-per-core model**, and it has a consequence that is *sharper*
than anything in the JVM course:

> **The `InMemoryChannelLayer` cannot even span worker processes on one machine.**
> Django Channels' in-memory channel layer stores its groups and queues in
> ordinary Python dicts — in *one process's* heap. Worker 0 and worker 1 are
> separate OS processes with separate memory. A message that arrives on worker
> 0's connection and needs to reach a user connected to worker 1 **has no shared
> place to go**. On the JVM, an in-process broker at least serves the whole JVM;
> here, a two-worker single box already can't deliver across itself.

The JVM course's Module 04 wall is "the simple broker can't span JVMs." **Ours is
"the in-memory layer can't span *processes*"** — so you need Redis to cross
*processes*, not merely *machines*, and you need it sooner and more
fundamentally. Module 04 makes this failure happen to you; Module 07 fixes it
with the Redis channel layer. Remember this when you get there — it starts here.

---

## Sync vs async, and the cardinal sin

Django is, at its heart, a **synchronous** framework. The ORM, most of the
middleware, most third-party apps — synchronous. Django Channels lets you write
**async** consumers on top of it. The friction between those two worlds is where
90% of realtime Django bugs live.

The cardinal sin is calling **synchronous, blocking code directly inside an async
coroutine**:

```python
class ChatConsumer(AsyncJsonWebsocketConsumer):
    async def receive_json(self, content):
        # DISASTER: Message.objects.create() is a synchronous, blocking DB call.
        # It blocks THIS event loop — every connection on this worker freezes
        # for the duration of the query.
        Message.objects.create(room_id=content["room"], body=content["body"])
```

That single line takes a worker holding 5,000 connections and stalls all 5,000
of them for the length of the query. Under load, the query gets slower (the pool
saturates), which stalls them longer, which is how a 20 ms query becomes a
multi-second p99 *for every connection on the worker* (Module 15 measures exactly
this — the Python analog of the JVM's "blocking call on the event loop" result).

### The bridges: `sync_to_async`, `async_to_sync`, `database_sync_to_async`

The fix is to move blocking work **off the event loop, onto a threadpool**:

```python
from channels.db import database_sync_to_async

class ChatConsumer(AsyncJsonWebsocketConsumer):
    async def receive_json(self, content):
        await self.save_message(content)          # awaits; loop stays free

    @database_sync_to_async
    def save_message(self, content):
        return Message.objects.create(            # runs in a threadpool thread
            room_id=content["room"], body=content["body"])
```

- **`sync_to_async(fn)`** — runs a synchronous function in a threadpool thread and
  gives you an awaitable, so the loop can keep serving other connections while it
  runs. The blocking call still blocks — but it blocks a *threadpool thread*, not
  the event loop.
- **`database_sync_to_async(fn)`** — `sync_to_async` specialized for the Django
  ORM: it also manages the per-thread database connection correctly (the ORM
  keeps connections in thread-locals). **Always use this for ORM calls in a
  consumer**, never plain `sync_to_async`.
- **`async_to_sync(coro)`** — the reverse: call an async function from
  synchronous code (e.g. sending to a channel group from a Celery task or a DRF
  view). Used constantly from Module 07 on.

### "Concurrency is free but resources are not"

Moving blocking calls to a threadpool feels like it makes the problem vanish. It
doesn't — it *relocates* it, and here is the exact same lesson the JVM course
teaches about virtual threads, arriving from a different door:

`sync_to_async`'s default executor is a **bounded thread pool**. In older
asyncio it defaulted to `min(32, cpu_count + 4)` threads. So if 5,000 connections
all hit the ORM at once, 5,000 coroutines line up for ~40 threads. The event loop
stays responsive (good — connections still get heartbeats), but the *database
work* queues invisibly, and your p99 climbs while CPU sits idle. **The bottleneck
moved to a place with no backpressure signal.**

> **The principle, identical to the JVM course's:** *concurrency became free;
> resources did not.* asyncio will happily create 50,000 coroutines contending
> for a 20-connection Postgres pool or a 40-thread executor. You must bound the
> scarce resource **deliberately** — with an `asyncio.Semaphore` — because the
> old thread-pool-as-accidental-rate-limiter is gone. The lab builds this trap
> and fixes it with a Semaphore, exactly as the JVM course does.

Django's **async ORM (4.1+)** is the other half of the story: `await
Message.objects.acreate(...)`, `async for msg in queryset`. Native async query
methods (the `a`-prefixed ones) don't need `database_sync_to_async` — but under
the hood they *still* run the actual database I/O in a threadpool, because
psycopg's calls are synchronous, so the same bounded-resource lesson applies.
Module 15 pulls this apart in full.

---

## uvloop — a faster loop for free

`asyncio`'s default event loop is pure Python over `epoll` (the
`_UnixSelectorEventLoop` you saw in Module 00). **uvloop** replaces it with a
Cython wrapper around **libuv** — the same C event loop that powers Node.js. It's
a drop-in:

```python
import uvloop
uvloop.install()          # or: asyncio.run(main(), loop_factory=uvloop.new_event_loop)
```

The win is 2–4× on raw loop throughput (task switches, socket reads/writes)
because the hot path is C, not interpreted Python. It changes no semantics —
your coroutines behave identically — so there's rarely a reason not to use it in
production. Uvicorn enables it automatically when installed
(`uvicorn[standard]`). The lab measures the difference so the "2–4×" is your
number, not a slogan. Note the ceiling: uvloop speeds up the *loop*, not your
Python callbacks — if you're CPU-bound in your own handler code, a faster loop
doesn't help, because you're not loop-bound, you're GIL-bound.

---

## Structured concurrency — `asyncio.TaskGroup`

Chat fan-out is naturally parallel: "load the room, load the members, load my
unread count, then render." Done with bare `create_task`, that's leak-prone — if
one fails, do the others get cancelled? If the caller gives up, does anything
stop? Python 3.11+ answers with **`asyncio.TaskGroup`**, the direct analog of the
JVM's `StructuredTaskScope`:

```python
async def load_room_view(room_id, user_id):
    async with asyncio.TaskGroup() as tg:
        room    = tg.create_task(get_room(room_id))
        members = tg.create_task(list_members(room_id))
        unread  = tg.create_task(count_unread(user_id, room_id))
    # We only get here when ALL succeed. If ANY raised, the others were
    # cancelled and the exception (grouped) propagates out of the `async with`.
    return RoomView(room.result(), members.result(), unread.result())
```

Three guarantees you'd otherwise hand-roll: no task outlives the block, a failure
cancels its siblings, and the caller's cancellation propagates down. It replaces
the old, footgun-ridden `asyncio.gather(..., return_exceptions=...)` for anything
where a failure should tear down the group. The lab shows a fan-out that fails
fast and cancels a still-running sibling — and, like the JVM course, notes that
bounding *how many* tasks run at once is still your `Semaphore`'s job, not the
group's.

---

## What async does *not* fix

The part that separates people who read the asyncio docs from people who've run
it under load.

| Problem | Does asyncio help? |
|---------|-------------------|
| Many connections mostly idle (I/O-bound) | ✅ **Yes.** This is exactly the case it's built for. |
| CPU-bound work | ❌ No. One core per process. A fan-out that's JSON-encode-bound is GIL-bound; add worker processes, not tasks. |
| A blocking call in the hot path | ❌ **No — it's catastrophic.** It stalls every connection on the loop. This is the danger the JVM's unmount hides and asyncio does not. |
| A limited downstream resource | ❌ **No — and it's the dangerous one.** 50k coroutines, 20 DB connections; queueing with no backpressure. Bound it with a Semaphore. |
| Memory per connection | ⚠️ Partly. The Task is cheap; your consumer state and buffers aren't (~45 KB, Module 06). |

---

## Decision guide

| Situation | Choice |
|-----------|--------|
| Handling many I/O-bound connections | **async consumers on the event loop** (Channels, Module 04) |
| A synchronous ORM call inside a consumer | **`database_sync_to_async`** — never call it raw |
| CPU-bound parallel work (encode, compress, hash a lot) | **More worker processes**, or offload to Celery; threads won't parallelize it |
| Using all cores | **One worker process per core** (`--workers N`) |
| Fan-out where a failure should cancel siblings | **`asyncio.TaskGroup`** |
| Protecting a scarce downstream (DB pool, threadpool, an API) | **`asyncio.Semaphore`** — always, now that the thread pool no longer rate-limits for you |
| Squeezing more loop throughput | **uvloop** (free; doesn't help CPU-bound code) |

---

## Why not gevent / threads / Go / Node?

Fair question; the honest comparison, since this course is about defending
choices.

- **gevent / eventlet** monkey-patch the stdlib so blocking calls yield to a
  greenlet scheduler — Python's closest thing to Answer B. It works, and older
  Django-Channels deployments used it, but the patching is global and fragile:
  one C extension that doesn't cooperate blocks everything, and debugging the
  patched stack is miserable. The ecosystem (and Channels 4) moved to asyncio.
  Use asyncio.
- **Plain threads** hit the GIL for CPU and the ~32k thread wall for I/O
  concurrency (Module 00). Fine for a handful of background jobs, wrong for
  holding connections.
- **Go** is the strongest alternative for this exact workload: goroutines are
  Answer B *and* there's no GIL, so you get cheap concurrency **and** true
  multi-core in one process. If your only requirement were "maximum sockets per
  dollar at the edge," Go (or Rust) would likely win — and Module 15's benchmark
  is honest about it, comparing Django's numbers to what a raw Go/Rust edge would
  do. We use Python because the *other* four problems (the ORM, migrations,
  Redis, the admin, DRF, the team that already knows Django) are where this
  course spends its time, and Django owns those.
- **Node** is one event loop per process — architecturally *identical* to a single
  Python worker, minus the GIL debate (Node has always been one-core-per-process
  and scales with `cluster`, exactly like our process-per-core model). If you
  know Node's event loop, you already understand asyncio; the shapes are the same.

Python's honest distinct claim here isn't raw speed — Go beats it. It's that
asyncio gives you an event loop that a huge, mature, batteries-included web
framework already sits on, so you get realtime *and* Django's ORM/admin/DRF in
one stack. Module 15 quantifies exactly what you pay for that convenience.

---

## What's next

The lab makes all of this concrete: you'll create a million asyncio Tasks and
watch OS threads die at 32k; freeze an entire event loop with one `time.sleep`
and measure the stall; race uvloop against the stdlib loop; and build the
unbounded-concurrency trap around a bounded resource so you recognize it in
Module 06 and 15.

See you in [`lab.md`](./lab.md).
