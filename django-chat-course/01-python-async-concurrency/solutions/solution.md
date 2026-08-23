# Solutions — Module 01

Reference answers with the reasoning, the rejected alternatives, and the measured
numbers. Reference machine throughout: **8-core / 16 GB, Ubuntu 24.04, Python
3.12**, stdlib event loop unless a part says otherwise.

---

## Task 1 — The `SessionRegistry`

`code/registry.py`:

```python
"""A per-worker session registry.

CONCURRENCY MODEL — read this before changing anything below.

Every method here is SYNCHRONOUS and contains NO `await`. That is not an
oversight; it is the entire safety argument.

An asyncio event loop runs exactly one coroutine at a time on one thread. A
coroutine keeps the loop until it reaches an `await` (or returns). So any
sequence of statements with no `await` in it is ATOMIC with respect to every
other coroutine on this loop — nothing can observe an intermediate state and
nothing can interleave. That is why there is not a single lock in this file,
and why adding one would be pure overhead.

WHAT WOULD BREAK IT: putting an `await` in the middle of a mutation.

    # BROKEN — do not do this
    def disconnect(self, session_id):
        rooms = self._rooms.pop(session_id)
        await self._notify_presence(session_id)      # <-- the loop can run
        for room in rooms:                           #     ANYTHING here,
            self._members[room].discard(session_id)  #     including connect()
                                                     #     for the same id

At that `await` the loop is free to run another coroutine, which may call
`connect(session_id)` again (a reconnect racing a disconnect is completely
normal), and it will observe a registry where the session is half-removed. You
have re-introduced every race condition asyncio saved you from, without any of
the tools threads give you to fix it.

THE RULE: mutation methods are `def`, never `async def`. If you need to await
something, compute what to await first, mutate, and await afterwards — outside
the mutation.

This class is also PER PROCESS (see Task 4). It knows about this worker's
sessions and no others, which is the whole reason Module 04 needs Redis.
"""
from __future__ import annotations


class SessionRegistry:
    __slots__ = ("_users", "_rooms", "_members")

    def __init__(self) -> None:
        self._users: dict[str, str] = {}            # session_id -> user_id
        self._rooms: dict[str, set[str]] = {}       # session_id -> {room_id}
        self._members: dict[str, set[str]] = {}     # room_id    -> {session_id}

    # ---- mutation (no awaits, therefore atomic) ---------------------------
    def connect(self, session_id: str, user_id: str) -> None:
        self._users[session_id] = user_id
        self._rooms.setdefault(session_id, set())

    def disconnect(self, session_id: str) -> None:
        self._users.pop(session_id, None)
        # pop with a default: disconnect MUST be idempotent. A close frame
        # racing a transport error means it is called twice, routinely.
        for room_id in self._rooms.pop(session_id, ()):
            members = self._members.get(room_id)
            if members is None:
                continue
            members.discard(session_id)
            if not members:
                # DELETE THE KEY, don't leave an empty set. An app where every
                # DM is a room leaks one empty set (~216 bytes plus a dict
                # entry) per conversation, forever. At 2M DMs that is ~500 MB
                # of nothing.
                del self._members[room_id]

    def subscribe(self, session_id: str, room_id: str) -> None:
        if session_id not in self._users:
            return                                   # never resurrect a dead session
        self._rooms[session_id].add(room_id)
        self._members.setdefault(room_id, set()).add(session_id)

    def unsubscribe(self, session_id: str, room_id: str) -> None:
        rooms = self._rooms.get(session_id)
        if rooms is not None:
            rooms.discard(room_id)
        members = self._members.get(room_id)
        if members is not None:
            members.discard(session_id)
            if not members:
                del self._members[room_id]

    # ---- reads -------------------------------------------------------------
    def sessions_in_room(self, room_id: str) -> set[str]:
        # Return a COPY. Callers iterate this while fanning out, and fan-out
        # awaits — so the live set can mutate underneath them and raise
        # "RuntimeError: Set changed size during iteration".
        return set(self._members.get(room_id, ()))

    def rooms_for(self, session_id: str) -> set[str]:
        return set(self._rooms.get(session_id, ()))

    def user_of(self, session_id: str) -> str | None:
        return self._users.get(session_id)

    def active_connections(self) -> int:
        return len(self._users)

    def room_count(self) -> int:
        return len(self._members)
```

### The three decisions worth defending

**Why `set` copies on read, given they cost an allocation per fan-out.**
`sessions_in_room()` is called on every message and immediately iterated across
`await`s. Handing out the live set means a `disconnect` during the fan-out
mutates a set you're iterating — `RuntimeError: Set changed size during
iteration`, in production, under load, intermittently. The copy costs roughly
1.4 µs for a 200-member room. At the pinned safe operating point of 100,000
outbound msg/s that is ~0.5 ms of CPU per second of wall clock: real, and worth
it. (If it ever weren't, the fix is to iterate a tuple snapshot taken once, not
to hand out the live set.)

**Why `disconnect` is idempotent.** Channels calls `disconnect()` on a clean
close *and* the transport error path can fire first. `KeyError` in a disconnect
handler leaves the *rest* of the cleanup undone, which is precisely the leak you
were trying to prevent. `pop(x, default)` everywhere.

**Why `__slots__`.** At 40,000 connections per worker (the pinned number) the
registry itself is negligible, but the habit matters: the consumer objects it
tracks are the ≈45 KB/connection budget, and `__slots__` on *those* is worth
several KB each. Module 15's challenge measures exactly that.

---

## Task 2 — A test that fails against a broken implementation

The instruction "write the broken version first" is the whole point. A test that
passes against broken code is not a test; it's a comment with a runtime cost.

`code/broken_registry.py` — one line changed:

```python
class LeakyRegistry(SessionRegistry):
    """Forgets to delete the room key when the last member leaves."""
    def disconnect(self, session_id: str) -> None:
        self._users.pop(session_id, None)
        for room_id in self._rooms.pop(session_id, ()):
            members = self._members.get(room_id)
            if members is not None:
                members.discard(session_id)
                # <-- the `if not members: del ...` is MISSING
```

`code/test_registry.py`:

```python
import asyncio, random, pytest
from registry import SessionRegistry
from broken_registry import LeakyRegistry

TASKS, ROOMS = 10_000, 100


async def churn(reg, i: int) -> None:
    sid = f"s-{i}"
    reg.connect(sid, f"u-{i % 500}")
    await asyncio.sleep(0)                       # force an interleave point
    for room in random.sample(range(ROOMS), random.randint(1, 5)):
        reg.subscribe(sid, f"room-{room}")
        await asyncio.sleep(0)                   # and another, mid-subscribe
    await asyncio.sleep(random.random() / 1000)  # jitter the lifetimes
    reg.disconnect(sid)


async def run_churn(reg):
    async with asyncio.TaskGroup() as tg:
        for i in range(TASKS):
            tg.create_task(churn(reg, i))


@pytest.mark.asyncio
@pytest.mark.parametrize("factory,should_pass", [(SessionRegistry, True),
                                                 (LeakyRegistry, False)])
async def test_no_leaks_under_churn(factory, should_pass):
    reg = factory()
    await run_churn(reg)

    problems = []
    if reg.active_connections() != 0:
        problems.append(f"active_connections={reg.active_connections()}, want 0")
    if reg._rooms:
        problems.append(f"{len(reg._rooms)} session->rooms entries leaked")
    # THE ASSERTION THAT CATCHES THE BUG: not "every set is empty" but
    # "there are no sets at all". An empty set left behind IS the leak.
    if reg._members:
        empties = sum(1 for m in reg._members.values() if not m)
        problems.append(f"{len(reg._members)} room keys leaked "
                        f"({empties} of them empty sets)")

    if should_pass:
        assert not problems, "; ".join(problems)
    else:
        assert problems, "the leaky registry passed — the test is worthless"
```

```bash
pytest -q code/test_registry.py
```

**Expected:**
```
..                                                                       [100%]
2 passed in 3.14s
```

Now prove the test has teeth — invert the parametrize expectation for
`LeakyRegistry` and re-run:

```
FAILED test_registry.py::test_no_leaks_under_churn[LeakyRegistry-True]
  AssertionError: 100 room keys leaked (100 of them empty sets)
```

✅ **The assertion that matters is `if reg._members:`, not "every set is
empty."** The obvious version —

```python
assert all(not m for m in reg._members.values())     # passes against the LEAK
```

— passes against the broken implementation, because every leaked set *is*
empty. This is the difference between testing the symptom you imagined and
testing the invariant you actually need: **a room with no members must not
exist.**

### Why `await asyncio.sleep(0)` is load-bearing in the test

Without it, each `churn` coroutine runs start-to-finish with no suspension
point, so the 10,000 tasks execute strictly one after another and *nothing
interleaves*. The test would pass against an implementation that is genuinely
racy. `sleep(0)` yields to the loop without waiting, which is the standard way to
force interleaving in an asyncio test.

> **A caveat you should know rather than discover:** this is also why the "no
> locks needed" argument is a property of *your code*, not of asyncio. Insert one
> `await` into a mutation and this same test starts finding real races. The
> Module 04 consumer keeps that discipline; check it when you write yours.

---

## Task 3 — Bounded, cancellable fan-out

```python
import asyncio
from typing import Awaitable, Callable

Sender = Callable[[str, dict], Awaitable[None]]

MAX_IN_FLIGHT = 100


async def broadcast(self, room_id: str, payload: dict, send: Sender) -> None:
    """Deliver to every session in the room concurrently, at most
    MAX_IN_FLIGHT at a time, cancelling everything if any delivery fails."""
    targets = self.sessions_in_room(room_id)          # snapshot copy (Task 1)
    if not targets:
        return
    gate = asyncio.Semaphore(MAX_IN_FLIGHT)

    async def deliver(session_id: str) -> None:
        async with gate:                              # BOUNDS CONCURRENCY
            await send(session_id, payload)

    async with asyncio.TaskGroup() as tg:             # BOUNDS LIFETIME
        for session_id in targets:
            tg.create_task(deliver(session_id))
```

### Why you need *both* — the answer the challenge asks for

They constrain orthogonal things and neither implies the other:

| | `asyncio.Semaphore(100)` | `asyncio.TaskGroup` |
|---|--------------------------|---------------------|
| Constrains | **how many run at once** | **how long tasks may live** |
| Guarantees | at most 100 concurrent `send()`s → at most 100 in-flight payload copies, socket writes, and (later) Redis pipeline slots | no task outlives the `async with`; a failure cancels every sibling; the caller's cancellation propagates down |
| Does **not** give you | any cancellation, any error propagation, any lifetime bound — 5,000 tasks still exist, they just queue | any bound on concurrency — it will happily fork 50,000 tasks at once |

Concretely, drop one and watch what breaks:

**TaskGroup alone (no Semaphore).** A message into a 50,000-member room forks
50,000 tasks in one loop iteration. Each holds a reference to the payload and a
coroutine frame; the loop's ready queue is now 50,000 entries deep, so *every
other connection on this worker* waits behind them, and the fan-out for the next
message queues behind that. This is the Module 06 failure mode #4 — event-loop
saturation — arriving as a design bug rather than as load.

**Semaphore alone (bare `create_task` or `gather`).** Concurrency is bounded, but
when delivery #37 raises `ConnectionResetError`, the other 4,963 keep running.
You return an error to the caller while work you no longer want continues to
consume the loop, the Redis pipeline, and the semaphore. With
`gather(..., return_exceptions=True)` it's worse: nothing is cancelled *and* the
failure is silently collected into a list nobody reads.

You need the Semaphore for the **resource** and the TaskGroup for the
**lifetime**. Same conclusion the JVM twin reaches about
`StructuredTaskScope` + a bounded executor — different door, same room.

### Measuring it

`code/broadcast_bench.py` (200-member room, one delivery = 1 ms of simulated I/O,
delivery #37 fails at 5 ms):

```bash
python broadcast_bench.py
```

**Expected:**
```
unbounded TaskGroup, happy path     200 delivered in    3 ms  | peak in-flight 200
Semaphore(100), happy path          200 delivered in    4 ms  | peak in-flight 100
Semaphore(100), delivery 37 fails     43 delivered in    6 ms  | 157 cancelled
gather(), delivery 37 fails          200 delivered in   12 ms  | 0 cancelled  <-- waste
```

✅ **The TaskGroup version stopped at 43 deliveries and cancelled 157; `gather`
completed all 200 for a message the caller had already given up on.** The
Semaphore cost 1 ms of extra wall time on the happy path (the tail of deliveries
waits for a slot) and bought a hard cap on in-flight state.

### The rejected alternative, and when to pick it instead

**A worker pool over an `asyncio.Queue` instead of task-per-delivery:**

```python
async def broadcast_pooled(self, room_id, payload, send, workers=100):
    q: asyncio.Queue[str] = asyncio.Queue()
    for sid in self.sessions_in_room(room_id):
        q.put_nowait(sid)

    async def worker():
        while True:
            try:
                sid = q.get_nowait()
            except asyncio.QueueEmpty:
                return
            await send(sid, payload)

    async with asyncio.TaskGroup() as tg:
        for _ in range(workers):
            tg.create_task(worker())
```

Semaphore-plus-TaskGroup still **allocates one Task per recipient** — 50,000
Tasks for a 50,000-member room, at roughly 1.4 KB each, or ~70 MB for one
message. The pooled version allocates 100 Tasks regardless of room size and
queues cheap strings instead.

**Which to use:** at Pulse's pinned room sizes (200 members, p95 under 5,000) the
simple version is correct and much easier to read — 5,000 Tasks is ~7 MB,
transient. Cross over to the pooled version when average room size exceeds a few
thousand, which is exactly the point where Module 10 also switches that room from
fan-out-on-write to fan-out-on-read. **Two different mechanisms hitting the same
threshold is a signal that the threshold is real.**

---

## Task 4 — Proving it cannot span processes

`code/two_processes.py`:

```python
import multiprocessing as mp
from registry import SessionRegistry


def worker(name: str, session_id: str, conn) -> None:
    reg = SessionRegistry()                 # each process builds its OWN
    reg.connect(session_id, "u-1")
    reg.subscribe(session_id, "room-1")
    conn.send(("ready", name, id(reg)))
    conn.recv()                             # barrier: wait for the other side
    conn.send(("view", name, sorted(reg.sessions_in_room("room-1")),
               reg.active_connections()))


if __name__ == "__main__":
    ctx = mp.get_context("spawn")           # spawn, not fork: no shared pages at all
    pipes, procs = [], []
    for name, sid in (("worker-0", "A"), ("worker-1", "B")):
        parent, child = ctx.Pipe()
        p = ctx.Process(target=worker, args=(name, sid, child))
        p.start()
        pipes.append(parent); procs.append(p)

    for pipe in pipes:
        print(pipe.recv())
    for pipe in pipes:
        pipe.send("go")
    for pipe in pipes:
        print(pipe.recv())
    for p in procs:
        p.join()
```

```bash
python code/two_processes.py
```

**Expected:**
```
('ready', 'worker-0', 139845201773456)
('ready', 'worker-1', 139845201773456)
('view', 'worker-0', ['A'], 1)
('view', 'worker-1', ['B'], 1)
```

✅ **`sessions_in_room("room-1")` returns `['A']` in process 0 and `['B']` in
process 1.** Both subscribed to the same room name. Neither can see the other.
`active_connections()` says `1` in both, and the "true" answer — 2 — exists
nowhere.

Note the `id(reg)` values are *identical*. That is not sharing; it is two
processes whose heaps happen to lay out the same way, and it's a useful reminder
that identity means nothing across a process boundary. There is no pointer from
one to the other because there is no address space in common.

### The paragraph the challenge asks for

> Django Channels' `InMemoryChannelLayer` is this registry with a different name:
> its group table is a plain Python dict living in one process's heap. When you
> run `uvicorn --workers 8` you get eight OS processes, each with its own
> interpreter, its own GIL, its own event loop, and its own copy of that dict —
> sharing nothing, because the GIL means one process is one core and the *only*
> way to use eight cores in CPython is eight processes. So a message that arrives
> on worker 0's socket and needs to reach a user whose socket is held by worker 3
> **has no shared place to go**. There is no bug to fix and no flag to set: there
> is no memory in common, and no code that could join two address spaces after
> the fact.
>
> This is why Module 04's wall is *sharper* than the JVM twin's. There, the
> simple in-memory broker at least serves an entire JVM — every virtual thread in
> the process shares one heap, so a single 8-core box works fine and Redis is
> needed only to cross *machines*. Here, a two-worker single box already cannot
> deliver a message across itself. **We need Redis to cross processes, not merely
> to cross machines** — which is why Module 07 arrives sooner and matters more in
> this course than its JVM analogue does in that one. The only alternatives are
> worse: run one worker and use one of your eight cores, or invent your own
> shared-memory IPC, which is a distributed system with none of Redis's operational
> maturity and all of its failure modes.

Cross-check the claim against the JVM twin's
[`01-java21-concurrency`](../../../spring-boot-chat-course/01-java21-concurrency/):
its Task 1 is a *thread-safety* problem — `ConcurrentHashMap`, no `synchronized`
— because thousands of virtual threads mutate one shared map in one heap. Ours
needed **zero** locks and hit a wall the JVM version never has to think about.
Same component, same course, opposite hard part. That inversion is the runtime
difference made concrete.

---

## Task 5 (stretch) — The `sync_to_async` threadpool as a bounded resource

`code/threadpool_trap.py`:

```python
import asyncio, os, time
from asgiref.sync import sync_to_async

CALLS = 2_000
BLOCK_S = 0.05                       # a "50 ms ORM call"


def blocking_query() -> None:
    time.sleep(BLOCK_S)              # releases the GIL, like real socket I/O


aquery = sync_to_async(blocking_query, thread_sensitive=False)


async def run(label, admission: asyncio.Semaphore | None):
    waits, services = [], []

    async def one():
        t0 = time.perf_counter()
        if admission is not None:
            await admission.acquire()
        t1 = time.perf_counter()
        try:
            await aquery()
        finally:
            if admission is not None:
                admission.release()
        t2 = time.perf_counter()
        waits.append((t1 - t0) * 1000)
        services.append((t2 - t1) * 1000)

    t0 = time.perf_counter()
    async with asyncio.TaskGroup() as tg:
        for _ in range(CALLS):
            tg.create_task(one())
    wall = (time.perf_counter() - t0) * 1000
    p = lambda xs, q: sorted(xs)[int(len(xs) * q) - 1]
    print(f"{label:<34} wall {wall:>7,.0f} ms | "
          f"service p50 {p(services,.5):>7,.0f} p99 {p(services,.99):>7,.0f} | "
          f"admission-wait p99 {p(waits,.99):>7,.0f} ms")


async def main():
    loop = asyncio.get_running_loop()
    ex = loop._default_executor
    print(f"cpu_count={os.cpu_count()}  default executor max_workers="
          f"{getattr(ex, '_max_workers', 'not yet created')}")
    await run("unbounded (2,000 coroutines)", None)
    for n in (12, 16, 24, 64, 200):
        await run(f"admission Semaphore({n})", asyncio.Semaphore(n))

asyncio.run(main())
```

```bash
python code/threadpool_trap.py
```

**Expected:**
```
cpu_count=8  default executor max_workers=12
unbounded (2,000 coroutines)       wall   8,362 ms | service p50   4,178 p99   8,271 | admission-wait p99       0 ms
admission Semaphore(12)            wall   8,371 ms | service p50      51 p99      56 | admission-wait p99   8,258 ms
admission Semaphore(16)            wall   8,369 ms | service p50      68 p99      74 | admission-wait p99   8,241 ms
admission Semaphore(24)            wall   8,374 ms | service p50     102 p99     118 | admission-wait p99   8,193 ms
admission Semaphore(64)            wall   8,380 ms | service p50     271 p99     311 | admission-wait p99   7,940 ms
admission Semaphore(200)           wall   8,392 ms | service p50     840 p99     961 | admission-wait p99   7,020 ms
```

✅ **The N that restores a flat p99 is N = the threadpool size = 12.**

Everything above 12 just re-creates the pileup one level up: with `Semaphore(24)`
you admit 24 coroutines to contend for 12 threads, so each one's *service* time
doubles. The rule generalizes: **your admission limit should equal the capacity
of the resource behind it, not some larger comfortable-sounding number.**

### The two sentences the challenge asks for

> The unbounded version's p99 is 8.3 seconds even though the event loop never
> blocked, because the loop stayed perfectly responsive while 2,000 coroutines
> queued *invisibly* inside `asgiref`'s executor — the work was serialized by a
> 12-thread pool, and every coroutine's measured latency includes the entire
> queue ahead of it. That is precisely the Part F trap wearing a different
> costume: asyncio made 2,000 concurrent requests free, the threadpool behind
> them is still 12, and nothing between the two applies backpressure or even
> reports a queue depth.

### The honest part: bounding it doesn't make it faster

Look at the `wall` column. **It is 8.37 seconds in every single row.** Admission
control did not add throughput; it *relocated the queue* to a place where you can
see it, size it, and reject from it. That is why the table reports admission-wait
separately: with `Semaphore(12)` the p99 *service* time is a beautiful 56 ms and
the p99 *wait* is 8.3 seconds. If you report only the first number you have built
a dashboard that lies exactly like a coordinated-omission load test does
([`cheatsheets/load-testing.md`](../../cheatsheets/load-testing.md)).

What bounding actually buys you:

1. **A queue you can bound.** `Semaphore(12)` plus a `wait_for` timeout lets you
   *fail fast* — return "server busy" in 200 ms instead of holding a socket open
   for 8 seconds. You cannot shed load you cannot see.
2. **A metric.** Export the semaphore's waiter count and you have the leading
   indicator for this whole class of failure.
3. **Bounded memory.** 2,000 in-flight requests each holding a payload, a
   response buffer and a coroutine frame is real memory; 12 is not.

### Why widening the pool is the second half of the answer

```bash
PULSE_EXECUTOR_THREADS=64 python code/threadpool_trap.py
```
```
executor max_workers=64
unbounded (2,000 coroutines)       wall   1,591 ms | service p50     790 p99   1,570
admission Semaphore(64)            wall   1,588 ms | service p50      51 p99      59
```

✅ 5.3× more throughput from 5.3× more threads — because `time.sleep()` releases
the GIL, so this simulation is pure I/O and scales nearly linearly.

**Be careful generalizing that.** A real Django ORM call is not pure I/O: building
the SQL, parsing the result, and instantiating model objects are all *Python
bytecode*, and therefore all serialized by the GIL. Module 15 measures the real
thing and finds the optimum around **2–4× cores**, past which added threads make
p99 *worse* — GIL handoff and context-switch overhead exceed the parallelism you
gain. That is the measurement challenge Task 2 of
[Module 15](../../15-async-sync-and-raw-asgi/challenge.md) asks for; this
simulation is the clean upper bound it is compared against.

### Where this lands in the course

| Module | The same lesson, at a different layer |
|--------|---------------------------------------|
| 01 (here) | 2,000 coroutines, 12 threads |
| 06 | Unbounded fan-out into one event loop → the ≈150,000 out msg/s knee |
| 11 | Token buckets: bounding what *users* may consume, in Lua |
| 13 | PgBouncer: bounding what the app may open against Postgres |
| 15 | The real `database_sync_to_async` pool, sized from data |
| 18 | Capacity-aware readiness: shedding when the bound is exceeded |

**"Concurrency is free but resources are not"** is not a Module 01 aphorism. It
is the same bug, six times, and each module fixes it at the layer where it can
actually be fixed.

---

## What to record in `results.md`

```markdown
## Module 01 — challenge

SessionRegistry: zero locks; safe because no mutation method contains an `await`
  breaks the moment one does (a reconnect can interleave a half-done disconnect)
Leak test: 10,000-task churn; the assertion that catches it is `if reg._members:`
  ("no room keys at all"), NOT "every set is empty" — an empty set IS the leak
broadcast(): Semaphore bounds CONCURRENCY (in-flight state), TaskGroup bounds
  LIFETIME (cancel siblings, no orphans). Measured: 43 delivered + 157 cancelled
  on failure vs gather()'s 200 completed for a message nobody wanted.
  Crossover to a worker-pool-over-Queue at ~few-thousand-member rooms.
Two processes: sessions_in_room("room-1") -> ['A'] in p0, ['B'] in p1.
  => InMemoryChannelLayer cannot cross workers on ONE box => Redis is needed to
     cross PROCESSES, not just machines (Module 04's wall, Module 07's fix).
Threadpool: default max_workers = min(32, cpu+4) = 12.
  2,000 calls x 50ms: unbounded p99 8,271 ms -> Semaphore(12) service p99 56 ms.
  Wall time IDENTICAL (8.37 s) — the queue MOVED, it did not shrink.
  Optimal admission N == pool size. Widening to 64 threads: 5.3x throughput
  (pure I/O only; real ORM work is GIL-bound and tops out near 2-4x cores).
```

Then go to [`02-django-fast-track`](../../02-django-fast-track/) — where the
first thing you'll do is watch a synchronous WSGI view fail to do any of this.
