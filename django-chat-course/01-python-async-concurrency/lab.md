# Lab 01 — Feel the Difference

**You'll:** create a million asyncio Tasks and watch OS threads die at ~32k;
prove every coroutine shares one thread; freeze an entire event loop with one
`time.sleep` and measure the stall; race uvloop against the stdlib loop; build
the unbounded-concurrency trap around a bounded resource and fix it with a
Semaphore; and cancel a fan-out sibling with a TaskGroup.

⏱️ ~80 min. Everything is a single Python file — no Django yet. Work in
`django-chat-course/01-python-async-concurrency/code/` with the course venv
active.

```bash
cd django-chat-course/01-python-async-concurrency/code
source ../../.venv/bin/activate
ulimit -n 100000          # you'll need it in Part D
```

Every reference number below is from the reference machine (**8-core / 16 GB,
Ubuntu 24.04, Python 3.12**). Yours will differ; the *ratios* are the lesson.

---

## Part A — A million Tasks, and the thread wall

Create `million.py`:

```python
import asyncio, resource, sys, threading, time

def rss_kb():
    r = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return r // 1024 if sys.platform == "darwin" else r    # macOS reports bytes

# ---------- asyncio Tasks ----------
async def task_worker(barrier):
    await barrier.wait()
    await asyncio.sleep(1)               # pretend I/O — SUSPENDS, frees the loop

async def run_tasks(n):
    barrier = asyncio.Barrier(n + 1)
    t0 = time.perf_counter()
    tasks = [asyncio.create_task(task_worker(barrier)) for _ in range(n)]
    print(f"submitted {n:,} tasks in {(time.perf_counter()-t0)*1000:.0f} ms")
    await barrier.wait()                 # release them all at once
    await asyncio.gather(*tasks)
    print(f"completed {n:,} tasks in {(time.perf_counter()-t0)*1000:.0f} ms  "
          f"|  peak RSS {rss_kb():,} KB")

# ---------- OS threads ----------
def thread_worker(barrier):
    barrier.wait()
    time.sleep(1)                        # BLOCKS a whole OS thread

def run_threads(n):
    barrier = threading.Barrier(n + 1)
    t0 = time.perf_counter()
    threads = []
    try:
        for _ in range(n):
            t = threading.Thread(target=thread_worker, args=(barrier,))
            t.start()
            threads.append(t)
    except RuntimeError as e:
        print(f"FAILED at {len(threads):,} threads: {e}")
        return
    print(f"submitted {n:,} threads in {(time.perf_counter()-t0)*1000:.0f} ms")
    barrier.wait()
    for t in threads:
        t.join()
    print(f"completed {n:,} threads in {(time.perf_counter()-t0)*1000:.0f} ms  "
          f"|  peak RSS {rss_kb():,} KB")

if __name__ == "__main__":
    kind = sys.argv[1] if len(sys.argv) > 1 else "tasks"
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 1_000_000
    if kind == "tasks":
        asyncio.run(run_tasks(n))
    else:
        run_threads(n)
```

Run the Task version first:

```bash
python million.py tasks 1000000
```

**Expected:**
```
submitted 1,000,000 tasks in 1,642 ms
completed 1,000,000 tasks in 2,905 ms  |  peak RSS 1,438,720 KB
```

One million concurrent Tasks, each sleeping a full second, finished in ~3 seconds
using ~1.4 GB. **They all slept simultaneously** — if they'd been serialized it
would have taken 11 days. All on **one thread**.

Now OS threads. Start small:

```bash
python million.py threads 10000
```

**Expected:**
```
submitted 10,000 threads in 3,681 ms
completed 10,000 threads in 4,712 ms  |  peak RSS 803,144 KB
```

10,000 OS threads use **more than half the memory of a million Tasks**, and took
70× longer just to *create* — each `start()` is a `clone()` syscall fighting the
GIL on the way up.

Now try to break it:

```bash
python million.py threads 1000000
```

**Expected** — a crash somewhere between 10k and 80k threads depending on your
`ulimit -u`, `threads-max`, and `vm.max_map_count`:
```
FAILED at 32,001 threads: can't start new thread
```

✅ **That exception is the lesson.** `RuntimeError: can't start new thread` is
`pthread_create` returning `EAGAIN`. Record the count in `results.md`. On the
reference machine it was **~32,000** — the same wall the JVM course's platform
threads hit, and the reason neither runtime lets you do thread-per-connection at
chat scale. The difference: the JVM's escape hatch is virtual threads; Python's
is the event loop you just used to hold a million Tasks.

Check what actually stopped you:
```bash
ulimit -u                          # max user processes (threads count against this)
cat /proc/sys/kernel/threads-max
cat /proc/sys/vm/max_map_count     # each thread's stack needs a memory mapping
```

---

## Part B — Where is a coroutine actually running?

The JVM course shows a virtual thread hopping between carrier threads across a
`sleep`. Python's story is simpler and stranger: **every coroutine runs on the
same one thread.** Prove it. Create `oneloop.py`:

```python
import asyncio, threading

async def worker(name):
    tid = threading.get_ident()
    print(f"{name:>6}  start   thread={tid}")
    await asyncio.sleep(0.05)                    # suspend + resume
    print(f"{name:>6}  resume  thread={threading.get_ident()}  (same? "
          f"{threading.get_ident() == tid})")

async def main():
    print(f"main thread = {threading.get_ident()}")
    async with asyncio.TaskGroup() as tg:
        for i in range(4):
            tg.create_task(worker(f"c{i}"))

asyncio.run(main())
```

```bash
python oneloop.py
```

**Expected** (the thread id is identical everywhere):
```
main thread = 140423156819776
    c0  start   thread=140423156819776
    c1  start   thread=140423156819776
    c2  start   thread=140423156819776
    c3  start   thread=140423156819776
    c0  resume  thread=140423156819776  (same? True)
    c1  resume  thread=140423156819776  (same? True)
    c2  resume  thread=140423156819776  (same? True)
    c3  resume  thread=140423156819776  (same? True)
```

✅ Two things to read here. **First**, all four coroutines *started* before any
*resumed* — they interleave at `await` points, which is cooperative scheduling
made visible. **Second**, every line reports the *same* thread id, before and
after the suspend. There is no carrier-thread hop like the JVM course showed,
because there is no pool of carriers — there is one loop on one thread. This is
exactly why blocking that one thread (next part) is fatal, and why CPU work here
uses one core.

---

## Part C — Freeze the event loop (the whole ballgame)

This is the failure mode that silently destroys an async server. It's the Python
analog of the JVM course's pinned-carrier demo — except worse, because there's no
carrier pool to absorb it. Create `blocking.py`:

```python
import asyncio, time

async def good_worker(i, results):
    t0 = time.perf_counter()
    await asyncio.sleep(0.1)                     # cooperative: frees the loop
    results.append(time.perf_counter() - t0)

async def bad_worker(i, results):
    t0 = time.perf_counter()
    time.sleep(0.1)                              # BLOCKING: freezes the loop
    results.append(time.perf_counter() - t0)

async def run(label, worker, n):
    results = []
    t0 = time.perf_counter()
    async with asyncio.TaskGroup() as tg:
        for i in range(n):
            tg.create_task(worker(i, results))
    wall = (time.perf_counter() - t0) * 1000
    p99 = sorted(results)[int(n * 0.99)] * 1000
    print(f"{label:<28} {n} tasks x 100ms  ->  wall {wall:>8,.0f} ms | "
          f"per-task p99 {p99:>8,.0f} ms")

async def main():
    n = 200
    await run("await asyncio.sleep(0.1)", good_worker, n)
    await run("time.sleep(0.1)  [BLOCKS]", bad_worker, n)

asyncio.run(main())
```

Both versions do "200 tasks, each taking 100 ms." One awaits; one blocks. Run it:

```bash
python blocking.py
```

**Expected:**
```
await asyncio.sleep(0.1)      200 tasks x 100ms  ->  wall      108 ms | per-task p99      104 ms
time.sleep(0.1)  [BLOCKS]     200 tasks x 100ms  ->  wall   20,041 ms | per-task p99   20,038 ms
```

✅ **108 ms vs 20 seconds — a 185× difference for the same 100 ms of "work."**

Read *why* each number is what it is:

- **`asyncio.sleep`**: all 200 tasks reach their `await` almost instantly, the
  loop parks all of them, and 100 ms later they all wake. Total wall ≈ 100 ms.
  The model working.
- **`time.sleep`**: the *first* task calls `time.sleep(0.1)` and the one loop
  thread is stuck inside it — **no other task can run**. They execute strictly
  one after another: 200 × 100 ms = 20 s. And notice the *per-task p99* is also
  20 s: the last task didn't just finish late, it *waited* the entire time,
  frozen, exactly as a real connection would.

Now make it visceral — add a "heartbeat" coroutine that's supposed to print every
100 ms, and watch it starve. Append to `blocking.py` and run this variant:

```python
async def heartbeat(stop):
    n = 0
    while not stop.is_set():
        print(f"  heartbeat {n}")
        n += 1
        await asyncio.sleep(0.1)

async def main2():
    stop = asyncio.Event()
    hb = asyncio.create_task(heartbeat(stop))
    await asyncio.sleep(0.25)
    print(">>> one coroutine is about to time.sleep(2) — watch the heartbeat")
    time.sleep(2)                                # blocks the loop for 2 whole seconds
    print(">>> unblocked")
    stop.set()
    await hb

# swap asyncio.run(main()) for:
asyncio.run(main2())
```

**Expected:**
```
  heartbeat 0
  heartbeat 1
  heartbeat 2
>>> one coroutine is about to time.sleep(2) — watch the heartbeat
>>> unblocked
  heartbeat 3
```

✅ The heartbeat printed 0,1,2, then went **silent for two full seconds**, then
resumed. In Pulse, that heartbeat is your presence ping, your WebSocket keepalive,
and every other user's message delivery. One synchronous call froze all of it.
**This is why `Message.objects.create()` in an async consumer is the cardinal
sin, and why `database_sync_to_async` exists.** Module 15 reproduces this with a
real ORM call and measures p99 going from ~60 ms to seconds.

> **The rule for this course:** in any `async def` a connection touches, never
> call a blocking function directly. Wrap ORM calls in `database_sync_to_async`,
> other blocking work in `sync_to_async`, and CPU-heavy work goes to a process
> (Celery) — never inline on the loop.

---

## Part D — Sockets, not sleeps

`asyncio.sleep` is a fine proxy, but let's prove the cost with real held
connections and count the threads. Create `sockets.py`:

```python
import asyncio, resource, sys, threading

def rss_kb():
    r = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return r // 1024 if sys.platform == "darwin" else r

held_server = []

async def server_handle(reader, writer):
    held_server.append((reader, writer))

async def main(n):
    server = await asyncio.start_server(server_handle, "127.0.0.1", 9200)
    async def serve():
        async with server:
            await server.serve_forever()
    asyncio.create_task(serve())
    await asyncio.sleep(0.2)

    conns = []
    for _ in range(n):
        r, w = await asyncio.open_connection("127.0.0.1", 9200)
        conns.append((r, w))

    await asyncio.sleep(0.5)
    print(f"held {n:,} connections (both ends, one process) | "
          f"RSS {rss_kb():,} KB | {rss_kb()*1024/(n*2):.0f} bytes/socket | "
          f"OS threads {threading.active_count()}")

asyncio.run(main(int(sys.argv[1]) if len(sys.argv) > 1 else 20000))
```

```bash
python sockets.py 20000
```

**Expected:**
```
held 20,000 connections (both ends, one process) | RSS 331,400 KB | 8,477 bytes/socket | OS threads 1
```

✅ Note the **last column: 1 OS thread** holding 40,000 socket endpoints (20k
client + 20k server, both in this one process). The JVM course's equivalent held
20,000 sockets on **14** carrier threads and its platform version needed 20,014;
asyncio needs exactly **one**. That is the event loop's whole value proposition,
measured. ~8.5 KB/socket here is the bare asyncio floor (Module 00's Task 5
number); Module 06 adds Django Channels' consumer + group + codec overhead and
you'll land near the pinned ~45 KB/connection.

> If you want the server and client in *separate* processes (more realistic),
> run the `idle_server.py`/`idle_client.py` pair from Module 00's solution — same
> lesson, cleaner memory attribution.

---

## Part E — uvloop vs the stdlib loop

The default loop is pure-Python over `epoll`. **uvloop** is libuv (the C loop
behind Node) with a Python skin. Measure the gap on a task-switch-heavy workload.
Create `loops.py`:

```python
import asyncio, sys, time

async def ping_pong(rounds):
    # a coroutine that suspends and resumes `rounds` times — pure loop overhead
    for _ in range(rounds):
        await asyncio.sleep(0)          # yield to the loop and come right back

async def bench(concurrency, rounds):
    t0 = time.perf_counter()
    async with asyncio.TaskGroup() as tg:
        for _ in range(concurrency):
            tg.create_task(ping_pong(rounds))
    dt = time.perf_counter() - t0
    switches = concurrency * rounds
    print(f"  {switches:,} task-switches in {dt*1000:,.0f} ms "
          f"= {switches/dt/1e6:.2f}M switches/s")

def main():
    which = sys.argv[1] if len(sys.argv) > 1 else "stdlib"
    if which == "uvloop":
        import uvloop
        uvloop.install()
        print("event loop: uvloop (libuv)")
    else:
        print("event loop: stdlib selector loop")
    asyncio.run(bench(concurrency=1000, rounds=1000))

main()
```

```bash
python loops.py stdlib
python loops.py uvloop
```

**Expected:**
```
event loop: stdlib selector loop
  1,000,000 task-switches in 1,982 ms = 0.50M switches/s

event loop: uvloop (libuv)
  1,000,000 task-switches in 712 ms = 1.40M switches/s
```

✅ **~2.8× faster** on raw loop throughput, one line of code, zero semantic
change. This is why `uvicorn[standard]` ships uvloop and enables it by default,
and why the course's reference numbers assume it. Record your ratio.

**The honest ceiling:** uvloop speeds up the *loop* — scheduling, socket
readiness, the C machinery between your coroutines. It does **not** speed up your
Python callback code. Add a `sum(range(10_000))` inside `ping_pong` and re-run:
the gap collapses, because now you're GIL-bound in interpreted Python, not loop-
bound. A faster loop can't fix CPU work — that's what worker processes are for.

---

## Part F — Build the unbounded-concurrency trap

This is the mistake you'll make in production if nobody shows it to you first —
and it's the same trap the JVM course builds, arriving through asyncio instead of
virtual threads. Create `unbounded.py`:

```python
import asyncio, time

# Pretend this is a Postgres pool of 20 connections.
db_pool = asyncio.Semaphore(20)

async def query_database():
    async with db_pool:
        await asyncio.sleep(0.05)       # a 50ms query

async def run(label, requests, admission=None):
    latencies = []
    async def one():
        t0 = time.perf_counter()
        if admission:
            async with admission:
                await query_database()
        else:
            await query_database()
        latencies.append((time.perf_counter() - t0) * 1000)

    t0 = time.perf_counter()
    async with asyncio.TaskGroup() as tg:
        for _ in range(requests):
            tg.create_task(one())
    wall = (time.perf_counter() - t0) * 1000
    s = sorted(latencies)
    p50, p99 = s[len(s)//2], s[int(len(s)*0.99)]
    print(f"{label:<32} total {wall:>7,.0f} ms | p50 {p50:>7,.0f} ms | p99 {p99:>8,.0f} ms")

async def main():
    reqs = 5000
    await run("unbounded (5000 coroutines)", reqs)
    await run("with admission Semaphore(200)", reqs, admission=asyncio.Semaphore(200))

asyncio.run(main())
```

```bash
python unbounded.py
```

**Expected:**
```
unbounded (5000 coroutines)      total  12,594 ms | p50   6,231 ms | p99   12,470 ms
with admission Semaphore(200)    total  12,612 ms | p50      52 ms | p99      118 ms
```

✅ **Read that carefully.** Total throughput is *identical* — both are gated by
the 20-connection pool, so both take ~12.6 s. But:

- **Unbounded**: p99 = **12.5 seconds**. All 5,000 coroutines are created
  instantly and *all* pile onto the `db_pool` semaphore at once. Each one's
  measured latency includes the entire queue ahead of it.
- **With admission control**: p99 = **118 ms**. Only 200 coroutines are ever
  in flight; the other 4,800 wait *before* they start timing, in the admission
  semaphore, and each individual request sees a short, honest latency.

The work is the same; the **queueing moved**, and in the unbounded case it moved
somewhere that destroys latency and holds 5,000 requests' worth of state.
Nothing crashed, nothing logged an error, and your CPU sat near idle. This is
**"concurrency is free but resources are not"** — asyncio gave you 5,000 free
coroutines, but the database is still 20 connections, and bounding the gap
between them is now *your* job, deliberately, with a Semaphore.

> This is why Module 06's challenge asks you to find Pulse's unbounded fan-out,
> and why Module 15 wraps every scarce resource — the DB pool, the
> `sync_to_async` threadpool, the Redis pipeline — in an explicit limit.

---

## Part G — Structured concurrency with TaskGroup

The direct analog of the JVM course's `StructuredTaskScope`. Create `fanout.py`:

```python
import asyncio, time

async def get_room(room_id):
    await asyncio.sleep(0.1)
    return room_id

async def list_members(room_id, break_it):
    await asyncio.sleep(0.15)
    if break_it:
        raise RuntimeError("member service down")
    return ["alice", "bob"]

async def count_unread(user_id, room_id):
    await asyncio.sleep(2.0)            # the slow one
    return 7

async def load_room_view(room_id, break_it):
    t0 = time.perf_counter()
    try:
        async with asyncio.TaskGroup() as tg:
            room    = tg.create_task(get_room(room_id))
            members = tg.create_task(list_members(room_id, break_it))
            unread  = tg.create_task(count_unread("u1", room_id))
        dt = (time.perf_counter() - t0) * 1000
        return f"OK in {dt:.0f} ms: room={room.result()} "\
               f"members={members.result()} unread={unread.result()}"
    except* RuntimeError as eg:
        dt = (time.perf_counter() - t0) * 1000
        return f"failed fast in {dt:.0f} ms: {eg.exceptions[0]}"

async def main():
    print(await load_room_view("general", break_it=False))
    print(await load_room_view("general", break_it=True))

asyncio.run(main())
```

```bash
python fanout.py
```

**Expected:**
```
OK in 2,003 ms: room=general members=['alice', 'bob'] unread=7
failed fast in 151 ms: member service down
```

✅ Two things. **The happy path takes ~2 s** — the length of the *slowest*
subtask, because all three ran concurrently (not 0.1 + 0.15 + 2.0 = 2.25 s
serially). **The failure path returns in ~150 ms**, not 2 s: when `list_members`
raised at 150 ms, the TaskGroup **cancelled the still-running `count_unread`
task** before its 2-second sleep finished. With a bare `asyncio.gather(*tasks)`
that 2-second call would have run to completion, burning work nobody was waiting
for.

Note the `except*` syntax — TaskGroup raises an `ExceptionGroup`, because in
general more than one sibling can fail. And note what TaskGroup does *not* do: it
happily forks all three tasks at once. If those were 5,000 fan-out deliveries,
bounding how many run concurrently is still your `Semaphore`'s job (Part F) — the
group bounds *lifetime*, not *concurrency*. That distinction is the challenge.

---

## What you measured

Record all of these in `results.md`:

| Measurement | Reference | Yours |
|-------------|-----------|-------|
| asyncio Tasks before failure | 1,000,000 ✅ (~1.4 GB) | |
| OS threads before failure | ~32,000 ❌ (`can't start new thread`) | |
| RSS: 10k threads vs 1M tasks | 803 MB vs 1.4 GB | |
| `time.sleep` vs `asyncio.sleep` (200×100ms) | 20,041 ms vs 108 ms (185×) | |
| OS threads holding 20k conns (asyncio) | 1 | |
| uvloop vs stdlib task-switch throughput | 1.40M/s vs 0.50M/s (2.8×) | |
| Unbounded vs admission-controlled p99 | 12,470 ms vs 118 ms | |
| TaskGroup fail-fast cancellation | 151 ms vs 2,000 ms | |

---

## What you learned

- A coroutine is a **resumable computation**; a Task is one the loop is driving.
  Tens of thousands of them run on **one thread**, one core, cooperatively —
  that's how one process holds a chat room's worth of connections.
- **Blocking the loop is the whole ballgame.** One synchronous call freezes every
  connection on the worker. `database_sync_to_async` / `sync_to_async` move
  blocking work to a threadpool; CPU work goes to processes.
- **The GIL means one core per process**, so you scale CPU with **one worker per
  core** — and (foreshadowing Module 04) those workers share no memory, so the
  in-memory channel layer can't even reach across them.
- **Concurrency became free; resources did not.** asyncio will over-subscribe any
  bounded downstream. You now need `asyncio.Semaphore`s deliberately.
- **uvloop** is a free 2–4× on the loop (not on your Python code).
- **`asyncio.TaskGroup`** makes fan-out cancellable and leak-free.

Now do [`challenge.md`](./challenge.md).

Then: [Module 02 — Django Fast-Track](../02-django-fast-track/).
