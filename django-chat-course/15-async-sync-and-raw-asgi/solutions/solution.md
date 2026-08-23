# Solutions — Module 15

Reference machine throughout: **8-core / 16 GB, Ubuntu 24.04, Python 3.12,
Django 5.1 / Channels 4.1, Uvicorn 0.30 + uvloop, `RedisChannelLayer`**. Every
number is the median of three runs; spreads are given where they matter.

The lab's baseline, which everything below is measured against:

| | Sync consumer | Async consumer | Raw ASGI |
|---|---------------|----------------|----------|
| p50 / p99 fan-out | 14 / 180 ms | **11 / 138 ms** | 7 / 94 ms |
| RSS per connection | ~120 KB | **~45 KB** | ~28 KB |
| Connections per worker | ~15,000 | **~40,000** | ~62,000 |
| Node fan-out knee | — | **≈150,000 out msg/s** | ≈210,000 |

---

## Task 1 — Where the 17 KB goes, and how much of it you can get back

### Measuring, not guessing

The trick is to measure the *delta* across a connection, not a total. Take a
`tracemalloc` snapshot with N connections open, another with N + 5,000, and
diff — that attributes bytes to the lines that allocated them.

`code/measure_conn.py`:

```python
import asyncio, gc, tracemalloc, resource, sys
from pympler import asizeof

def rss_kb():
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss

async def profile(open_n, extra_n):
    tracemalloc.start(25)
    await open_connections(open_n)            # your ws client harness
    gc.collect()
    base_rss, base_snap = rss_kb(), tracemalloc.take_snapshot()

    await open_connections(extra_n)
    gc.collect()
    rss, snap = rss_kb(), tracemalloc.take_snapshot()

    print(f"RSS delta: {(rss - base_rss) * 1024 / extra_n:,.0f} bytes/conn")
    for stat in snap.compare_to(base_snap, "lineno")[:15]:
        print(f"  {stat.size_diff / extra_n:8,.0f} B/conn  {stat}")

    # And the objects themselves, deep-sized:
    from chat.consumers import ChatConsumer
    one = next(c for c in gc.get_objects() if isinstance(c, ChatConsumer))
    print("consumer instance :", asizeof.asizeof(one))
    print("  scope           :", asizeof.asizeof(one.scope))
    print("  scope['headers']:", asizeof.asizeof(one.scope.get("headers")))
    print("  scope['user']   :", asizeof.asizeof(one.scope.get("user")))
```

```bash
python code/measure_conn.py 20000 5000
```

**Expected — the 17 KB, attributed:**

```
RSS delta: 45,312 bytes/conn

component                                                 bytes/conn   cumulative
-------------------------------------------------------  ----------  ----------
raw-ASGI floor (socket, transport, protocol, one Task)        28,100      28,100
Channels dispatch machinery                                    5,140      33,240
  await_many_dispatch: TWO extra asyncio Tasks per conn
  (one draining the socket, one draining channel_receive)
ASGI scope dict                                                4,220      37,460
  headers (list of ~14 (bytes, bytes) tuples)  2,180
  cookies/session/user/url_route/subprotocols  2,040
consumer instance __dict__ + attributes                        2,610      40,070
channel-layer bookkeeping                                      3,380      43,450
  channel_name str, per-channel asyncio.Queue object,
  membership entries in THREE group dicts (Module 21
  added `membership.{uid}` and `jti.{jti}` alongside `room.{id}`)
AuthMiddlewareStack: cached User + SessionStore                1,860      45,310
```

✅ **17.2 KB of Channels, in five buckets.** Note the two that surprise people:
Channels allocates **two extra asyncio Tasks per connection** for its dispatch
loop, and Module 21's security work silently **tripled** the group-membership
bookkeeping.

### The reductions, and what each one costs

```python
class ChatConsumer(AsyncJsonWebsocketConsumer):
    # 1. __slots__ on the consumer.
    __slots__ = ("room", "user_id", "seq", "_tasks")

    async def connect(self):
        await self.accept()
        # 2. Drop the scope you will never read again. Headers were needed by
        #    the middleware during the handshake and by nobody afterwards.
        self.scope.pop("headers", None)
        self.scope.pop("cookies", None)
        self.scope.pop("subprotocols", None)
        # 3. Keep the id, not the object. A Django User carries a SessionStore,
        #    a backend reference, and every field of the row.
        self.user_id = self.scope["user"].id
        self.scope["user"] = None
```

| Change | Saved | What it costs |
|--------|-------|---------------|
| `__slots__` on the consumer | **0.6 KB** | No dynamic attributes; some third-party consumer mixins stop working. Cheap and safe here. |
| Pop `headers`/`cookies`/`subprotocols` from `scope` after `connect()` | **3.9 KB** | Anything later that wants a header (a debug view, a per-connection User-Agent metric) must capture it explicitly at connect time. Do that once, deliberately. |
| Store `user_id: int`, drop `scope["user"]` | **1.7 KB** | Every place that used `self.scope["user"].is_staff` needs a query or a cached claim. Module 21's JWT claims already carry what we need, so this was free for us — it would not be for an app relying on `AuthMiddlewareStack`. |
| Drop `AuthMiddlewareStack` entirely (Module 21 uses ticket + first-frame JWT, so the session was dead weight) | **1.9 KB** | `scope["user"]` no longer exists at all. This is a real architectural commitment, not a tweak — but we already made it in Module 21 for *security* reasons, and the memory is a second dividend. |
| Collapse three groups to one: keep `room.{id}`, replace `membership.{uid}` and `jti.{jti}` with the **reconciliation loop** from Module 21's challenge | **2.2 KB** | Revocation stops being a push and becomes poll-based, so the worst-case window a revoked user stays connected grows from ~5 ms to the reconciliation interval (we chose 10 s). A genuine security-for-memory trade — and one you should make consciously or not at all. |
| Encode the fan-out payload **once** per `group_send` instead of per recipient (`AsyncWebsocketConsumer.send(text_data=…)` with a pre-serialized string) | 0.3 KB, **and ~11% CPU** | The consumer no longer speaks JSON, so every handler does its own encode/decode. Memory was the excuse; the CPU is the reason. |

```bash
python code/measure_conn.py 20000 5000     # after all six
```
**Expected:**
```
RSS delta: 33,140 bytes/conn
```

### The result, and the part that will not move

```
async Channels, as shipped     45.3 KB/conn     ~40,000 conns/worker
after six reductions           33.1 KB/conn     ~54,000 conns/worker   (+35%)
raw ASGI (websockets)          28.1 KB/conn     ~62,000 conns/worker
```

✅ **We closed 12.2 of the 17.2 KB — 71% of the gap — and got 35% more
connections per worker.**

The remaining **5.0 KB is Channels' dispatch machinery: two asyncio Tasks per
connection.** You cannot delete it without deleting Channels, because it is
exactly the mechanism that lets a `group_send` from another worker arrive at
*this* socket — that is, it is what you are paying Channels for. Raw ASGI is
cheaper because it doesn't have a channel layer; when you rebuild one (the lab's
~300 lines), you rebuild something structurally similar and get the memory back
only by making it worse.

> **The honest framing for a design review:** "Channels costs 5 KB/connection of
> irreducible dispatch overhead and 12 KB of defaults we can turn off. We turned
> them off, and the remaining 5 KB buys us groups, routing, lifecycle, and
> middleware. At our connection counts (Task 3) that costs us nothing we need."

---

## Task 2 — Sizing the `database_sync_to_async` threadpool from data

### Proving it's a bounded resource

```python
# chat/metrics.py — you cannot size what you cannot see
from prometheus_client import Gauge
import asyncio

POOL_ACTIVE = Gauge("chat_db_threadpool_active", "threads executing ORM work")
POOL_QUEUED = Gauge("chat_db_threadpool_queued", "coroutines awaiting a thread")

def sample_executor(loop):
    ex = loop._default_executor
    POOL_ACTIVE.set(len(ex._threads) - ex._work_queue.qsize())
    POOL_QUEUED.set(ex._work_queue.qsize())
```

Saturate it — 20,000 connections, a message every 2 s, every message doing one
real `Message.objects.create()`:

```bash
k6 run -e WS_PATH="/ws/async" -e ROOMS=100 -e SEND_EVERY=2000 \
       --vus 20000 --duration 3m ../../06-load-testing-harness/code/pulse-load.js
```
**Expected (default pool = `min(32, cpu+4)` = 12):**
```
✗ fanout_latency_ms.: p(50)=310ms  p(95)=2,940ms  p(99)=7,180ms
  chat_db_threadpool_active: 12 / 12   (SATURATED for 174 of 180 seconds)
  chat_db_threadpool_queued: 2,890
  worker CPU: 41%          <-- IDLE, while p99 is 7 seconds
```

✅ **The signature of a bounded resource with no admission control: p99 in
seconds while CPU sits at 41%.** Nothing is *working* hard; things are *waiting*.

### Finding the optimum

`ASGI_THREADS` / `AsyncToSync` executor sizes, same workload:

| Pool size | Throughput (msg/s persisted) | p50 | p99 | Worker CPU | Threads RSS |
|-----------|------------------------------|-----|-----|------------|-------------|
| 8 | 1,180 | 480 ms | 9,900 ms | 34% | 6 MB |
| **12 (default)** | 1,740 | 310 ms | 7,180 ms | 41% | 9 MB |
| 24 | 3,390 | 96 ms | 810 ms | 62% | 18 MB |
| **32** | **4,210** | **41 ms** | **196 ms** | **78%** | **24 MB** |
| 48 | 4,240 | 44 ms | 268 ms | 88% | 36 MB |
| 64 | 4,050 | 61 ms | 512 ms | 94% | 48 MB |
| 96 | 3,510 | 104 ms | 1,340 ms | 97% | 72 MB |
| 192 | 2,690 | 190 ms | 3,900 ms | 99% | 144 MB |

✅ **Throughput peaks at 32 threads (4× cores) and *falls* beyond it.** 192
threads is worse than 12.

### Why more threads gets *worse* — the part that isn't obvious

A `Message.objects.create()` is not pure I/O. Roughly:

```
  build the SQL + parameter adaptation      ~0.9 ms   Python bytecode  → GIL-BOUND
  socket round trip to Postgres             ~1.4 ms   GIL released     → parallel
  parse the result, instantiate the model    ~0.7 ms  Python bytecode  → GIL-BOUND
```

About **53% of the call holds the GIL.** Amdahl applies directly: with a 53%
serial fraction, no number of threads gets you past ~1.9× — and every thread past
that adds GIL handoff and context switching, which is pure loss. That's the
32→192 collapse.

Compare Module 01's stretch, where the "query" was `time.sleep(0.05)` — a call
that releases the GIL for its entire duration. There, 64 threads gave a clean
5.3× and would have kept scaling. **The difference between the two experiments is
the whole reason this measurement had to be done with the real ORM.**

### The two-part answer Pulse ships

Sizing alone is half the fix. Add admission control, because the pool must be
allowed to *reject*:

```python
# chat/db.py
import asyncio
from channels.db import database_sync_to_async

DB_ADMISSION = asyncio.Semaphore(32)          # == the pool size (Module 01, Task 5)

async def db(fn, /, *args, timeout=0.5, **kwargs):
    try:
        await asyncio.wait_for(DB_ADMISSION.acquire(), timeout=timeout)
    except TimeoutError:
        raise Overloaded("db_admission")       # -> {"type":"error","code":"busy"}
    try:
        return await database_sync_to_async(fn)(*args, **kwargs)
    finally:
        DB_ADMISSION.release()
```

**Expected, 32 threads + `Semaphore(32)` + a 500 ms admission timeout, at 1.5×
the offered load that produced the 7,180 ms p99:**
```
  fanout p50 44 ms  p99 231 ms
  rejected (code "busy"): 3.1% of sends
  chat_db_threadpool_queued: max 34
```
✅ **A 3.1% fast, honest rejection beats a 100% seven-second stall.** The client
(Module 17) already retries from its outbox with jitter, so those 3.1% are
delayed by ~1 s, not lost.

> **Why 32 and not "as many as it takes":** the number came from a measurement on
> *this* query mix. Change the mix — add a `select_related` that returns 50 rows,
> or a `bulk_create` — and the GIL-bound fraction changes and so does the
> optimum. Re-measure when the workload changes; do not treat 32 as a constant.

**And the alternative that beats all of it where it applies:** Django's native
async ORM (`acreate`, `aexists`, `async for`) skips the threadpool entirely for
simple queries. Where we could use it, we did — the pool exists for the calls
that can't (transactions with `select_for_update`, third-party sync libraries,
signals).

---

## Task 3 — The crossover surface

### Three variables, two degrees of freedom

The challenge names three variables. The first insight is that **only two of them
are independent**:

```
outbound_rate = inbound_rate × (room_size − 1)
```

Room size is not an axis — it is the *multiplier* that converts message rate into
fan-out work. So the surface is two-dimensional:

- **Axis D (density):** connections per node. Memory-bound.
- **Axis F (fan-out):** outbound messages/second per node. CPU-bound.

```
 conns/node
  400k ┤ GO / RUST EDGE
       │ (Python cannot hold this many per box at ANY consumer model)
  320k ┼───────────────────────────────────────────────
       │ RAW ASGI                     │  RAW ASGI or an
  200k ┤ (density is binding;         │  edge tier — you
       │  28 KB vs 45 KB is real      │  are binding on
       │  money at this scale)        │  BOTH axes
  120k ┼──────────────────────────────┼────────────────
       │                              │
       │ ASYNC CHANNELS               │  ASYNC CHANNELS
   40k ┤ ← Pulse at 3× (60k)          │  + MORE NODES
       │ ● Pulse today (20k)          │  (the knee is per node;
       │                              │   nodes are cheap, a second
   10k ┤ SYNC CONSUMERS               │   codebase is not)
       │ (an internal tool, an        │
       │  admin live-tail)            │
     0 └──────────────┬───────────────┴────────────────→ out msg/s per node
                   100k              150k            300k
                (safe point)        (knee)
```

### Where Pulse sits

| | Today | At 3× |
|---|-------|-------|
| Connections/node | 20,000 | 60,000 |
| Density limit (8 workers × 40,000) | 320,000 | 320,000 |
| **Density utilization** | **6%** | **19%** |
| Inbound | 333 msg/s | 1,000 msg/s |
| Room size | 200 | 200 |
| Outbound | 66,267/s | 198,800/s |
| Knee | 150,000/s | 150,000/s |
| **Fan-out utilization** | **44%** | **133% — past the knee** |

✅ **Pulse is fan-out-bound and nowhere near density-bound, at both scales.**

That single fact decides the module:

- **Raw ASGI's advantage is 1.5× density** — on the axis where we're using 6% of
  what we have. It buys us *nothing we need*. Its 30% latency advantage is real
  but does not change what we can serve.
- **At 3× we are 33% past the knee**, and the fix on that axis is a second node:
  Module 07 measured horizontal scaling at **1.9×**, so two nodes = 285,000
  out msg/s, comfortably above 198,800 with the safe-operating-point margin
  intact. **A second container is cheaper than a second codebase**, and the ~300
  lines of raw ASGI would have to be maintained forever by a team that is
  currently one person deep on it.

### The two independent thresholds that move the answer

**Threshold D (density):** `connections_per_node > 0.7 × (usable_RAM ÷ KB_per_conn)`.
At 16 GB and 45 KB that's ~250,000/node; after Task 1's reductions, ~340,000.
Crossing it means paying for machines you're using at 6% on the other axis, and
raw ASGI's 28 KB (or a Go edge's ~4 KB) starts buying real hardware. **Pulse
crosses this at roughly 12× today's connection count with today's message rate.**

**Threshold F (fan-out):** `out_msg_s_per_node > 0.65 × knee`, *and* adding nodes
has stopped being the cheap answer — because of cost, of a room-affinity
constraint that pins a room to a node, or of Redis becoming the bottleneck before
the app tier does. **Pulse crosses the first half at ~1.5× and handles it with
nodes; the second half is not in sight.**

They are independent because they are bound by different physical resources
(bytes vs cycles) and are moved by different product changes: **more users**
moves D, **bigger rooms or chattier users** moves F. A product decision to
support 5,000-member broadcast rooms multiplies F by 25 and leaves D untouched —
which is why Module 10 switches large rooms to fan-out-on-read rather than buying
a faster runtime.

---

## Task 4 — The debugging tax, measured

Three identical bugs, injected into the sync and async consumers, located by the
same engineer, alternating order to control for learning. Median of three
injections each.

| Bug | Sync consumer | Async, no tooling | Async + `PYTHONASYNCIODEBUG` | Caught by `flake8-async` in CI |
|-----|---------------|-------------------|------------------------------|-------------------------------|
| **A.** Blocking call (un-wrapped `Membership.objects.filter().exists()`) | 6 min | **74 min** | **4 min** | ✅ **0 min — never merged** |
| **B.** Connection leak (`registry.discard` missing from `disconnect`) | 22 min | 31 min | 29 min | ❌ not this kind of bug |
| **C.** Off-by-one in the resume cursor (`from_seq` inclusive vs exclusive) | 12 min | 13 min | 13 min | ❌ not this kind of bug |

**The multipliers: 12.3× for bug A, 1.4× for bug B, 1.1× for bug C.**

### Why only bug A is taxed, and taxed so brutally

The other two are *local* bugs: the symptom appears in the code that caused it,
so the stack trace, the logs, and the test all point at the right file. Async
adds a modest constant (bug B's 1.4× is `await`-flavoured confusion in the
teardown path, not a category change).

Bug A is **non-local**. The blocking call in *your* `receive_json` produces its
symptom in *other people's* connections — 5,000 of them, none of which executed
the buggy line. So:

- The stack trace of a victim shows a perfectly innocent `send_json`. It is a
  witness, not a suspect.
- The metrics say "everything on worker 3 is slow," which is true and useless.
- The bug is invisible at dev volumes: one connection, one query, 12 ms, fine.
- It only reproduces under concurrency, so the bisect loop is a 3-minute load
  test per candidate commit.

That's the 74 minutes. And the fix is **9 characters** (`await` +
`database_sync_to_async(...)`), which is the part that makes people angry.

### What actually collapses it

`PYTHONASYNCIODEBUG=1` takes 74 minutes to 4 because it converts a non-local
symptom into a local one:

```
WARNING asyncio Executing <Task ... receive_json() at chat/consumers.py:41>
        took 0.612 seconds
```

**The file and the line number.** That is the entire 18× improvement — it is not
a smarter debugger, it is the runtime telling you where the loop went.

And `flake8-async` in CI takes 4 minutes to 0, because the bug never lands:

```
chat/consumers.py:41:9: ASYNC101 blocking sync call in async function
```

### The recommendation, stated as a cost

> The async debugging tax on Pulse is **not a general 12× slowdown**. It is a
> 12× penalty on exactly one bug class — blocking the loop — and **that penalty
> is almost entirely eliminated by two zero-cost tools.** Both must be on by
> default (dev, test, and CI) rather than reached for during an incident,
> because the entire problem is that you don't know to reach for anything: the
> symptom points somewhere else. Budget one afternoon to wire them up, and one
> line in the code-review checklist. Then the honest cost of async is bug B's
> 1.4×, which is noise.

The JVM twin reaches the same conclusion about BlockHound and WebFlux. The
difference is that Python's version costs nothing to run in CI and its warning
names the line, which — measured — is worth more than a smarter tool that nobody
turns on.

---

## Task 5 — Request context through an async consumer, with `contextvars`

### Why `threading.local` is dangerous here (and not merely wrong)

In a sync consumer, one request owns one thread, so `threading.local` works. In
an **async** consumer, one thread runs thousands of interleaved connections. A
value stored there survives across `await` points into *whichever connection runs
next* — so the trace id, tenant id, or user id you stored for alice is read back
by bob's coroutine. **This is not a lost log line; it's a cross-user data leak
into your logs, your traces, and (if you use it for authorization caching) your
authorization decisions.**

`contextvars.ContextVar` is the async-correct equivalent: each Task gets its own
copy of the context, so values do not bleed sideways.

### The wiring

```python
# chat/context.py
import contextvars, logging, uuid

trace_id: contextvars.ContextVar[str] = contextvars.ContextVar("trace_id", default="-")
user_id:  contextvars.ContextVar[str] = contextvars.ContextVar("user_id",  default="-")


class ContextFilter(logging.Filter):
    def filter(self, record):
        record.trace_id = trace_id.get()
        record.user_id = user_id.get()
        return True
```

Register `ContextFilter` on the console handler in `LOGGING` and add
`[%(trace_id)s u=%(user_id)s]` to the format string. Then set the vars **per
frame**:

```python
# chat/consumers.py
from chat.context import trace_id, user_id

class ChatConsumer(AsyncJsonWebsocketConsumer):
    async def receive_json(self, content):
        # Set PER FRAME, not per connection: a socket lives 8 hours and carries
        # thousands of logically separate operations.
        token_t = trace_id.set(content.get("traceId") or uuid.uuid4().hex[:16])
        token_u = user_id.set(str(self.user_id))
        try:
            await self._dispatch(content)
        finally:
            trace_id.reset(token_t)          # reset, don't set("-") — nesting
            user_id.reset(token_u)

    async def chat_message(self, event):
        # Fan-out from ANOTHER user's frame. Carry their trace id across the
        # channel layer, or the delivery half of the trace is orphaned.
        token = trace_id.set(event.get("traceId", "-"))
        try:
            await self.send_json(event["data"])
        finally:
            trace_id.reset(token)
```

> **The channel layer does not carry context.** `group_send` serializes a dict to
> Redis; `contextvars` are process memory. If you want an end-to-end trace across
> the fan-out (Module 20 does), the trace id must travel **inside the envelope**.
> Same reason Module 05 versions the envelope: anything that must survive a hop
> has to be *in* the message.

### Breaking it the way it actually breaks

```python
# THE BUG. This looks completely reasonable.
class ChatConsumer(AsyncJsonWebsocketConsumer):
    async def _dispatch(self, content):
        ...
        asyncio.create_task(self._persist_async(content))     # fire and forget
```

`asyncio.create_task` **copies the current context at creation time**. Two
distinct failures follow, and the second is the dangerous one:

**Failure 1 — the orphan.** A task created in `connect()` (a presence heartbeat,
say) is created *before* any frame set `trace_id`, so it logs `[-]` forever. Mildly
annoying; easy to spot.

**Failure 2 — the sticky context.** A *shared* background pump created lazily by
whichever connection happened to be first:

```python
_pump = None

async def ensure_pump(self):
    global _pump
    if _pump is None:
        _pump = asyncio.create_task(fanout_pump())   # <-- captures THIS user's context
```

The pump now carries **alice's trace id and user id for the lifetime of the
worker**, and stamps them onto every log line for every fan-out to every user.
You have built a log-correlation system that confidently attributes 40,000
users' activity to alice. Nothing errors. Nothing is slow. The dashboards look
great and are wrong.

**Reproduce it:**
```bash
python code/context_break.py
```
```
[a1b2c3d4 u=alice] chat.consumer received frame from alice
[a1b2c3d4 u=alice] chat.pump    delivering to bob        <-- WRONG USER
[e5f6a7b8 u=bob  ] chat.consumer received frame from bob
[a1b2c3d4 u=alice] chat.pump    delivering to carol      <-- STILL alice
```

**The fixes, in order of preference:**

1. **Create long-lived tasks at startup, in a clean context** — in
   `lifespan.startup` or an `AppConfig.ready()`, where no request context exists.
   This is the real fix: shared machinery should never be born inside a request.
2. **Explicitly run in a fresh context** when you must create it lazily:
   ```python
   import contextvars
   _pump = contextvars.Context().run(asyncio.ensure_future, fanout_pump())
   ```
3. **Pass the trace id as an argument** to per-frame tasks, and set it inside the
   task, rather than relying on inheritance.

⚠️ **Also note `loop.run_in_executor` does *not* propagate context into the
thread** — you must `contextvars.copy_context().run(fn)` yourself. `asgiref`'s
`sync_to_async`/`async_to_sync` *do* propagate it, which is why
`database_sync_to_async` keeps your trace id and a hand-rolled `run_in_executor`
silently loses it. That asymmetry has cost people entire afternoons.

### The CI test that catches it

```python
# tests/test_context.py
import asyncio, logging, pytest
from chat.context import trace_id, ContextFilter

@pytest.mark.asyncio
async def test_shared_task_does_not_inherit_a_request_context(caplog):
    caplog.handler.addFilter(ContextFilter())
    log = logging.getLogger("chat.pump")
    started = asyncio.Event()

    async def pump():
        started.set()
        await asyncio.sleep(0.01)
        log.info("delivering")

    token = trace_id.set("alice-trace")           # simulate being inside a frame
    task = asyncio.create_task(pump())            # the bug, verbatim
    trace_id.reset(token)
    await started.wait(); await task

    leaked = [r for r in caplog.records if getattr(r, "trace_id", "-") != "-"]
    assert not leaked, (
        f"a long-lived task inherited a request context: "
        f"{[r.trace_id for r in leaked]}. Create shared tasks at startup, or "
        f"with contextvars.Context().run(...)."
    )

```

Write the **mirror test too** — a per-frame task that *does* inherit
`bob-trace` — otherwise the first test can be "fixed" by never setting a trace
id anywhere and both pass.

**Expected against the buggy code:**
```
FAILED tests/test_context.py::test_shared_task_does_not_inherit_a_request_context
  AssertionError: a long-lived task inherited a request context: ['alice-trace']
```

✅ **Two assertions, not one.** The negative test alone can be "fixed" by never
propagating context anywhere; the positive test locks in the behaviour you
actually want. Same discipline as Module 01's leak test: assert the invariant,
and prove the assertion has teeth.

---

## Task 6 (stretch) — The hybrid, and whether it earns its complexity

### The architecture

Module 06 proved the bottleneck is fan-out, not the connection layer. So: put
the sockets and the fan-out on a raw-ASGI edge, keep Channels as the brain.

```
                    ┌──────────────────────────────────┐
   client ─ws──────▶│  edge (websockets + uvloop)      │  N processes
                    │  • ticket check (Redis GETDEL)   │
                    │  • room set per socket           │
                    │  • Redis Streams consumer -> send│  ← THE HOT PATH ONLY
                    └───────┬──────────────────▲───────┘
                    control │ (XADD)           │ (XREADGROUP)
                            ▼                  │
                    ┌───────────────────────────────────┐
                    │  Redis (Streams + state)          │
                    └───────┬──────────────────▲────────┘
                            ▼                  │
                    ┌──────────────────────────┴───────┐
                    │  Channels workers                │  M processes
                    │  • subscribe/authz, resume, ack  │
                    │  • persist + outbox, presence    │
                    │  • DRF history API, admin        │
                    └──────────────────────────────────┘
```

The edge is a **dumb pipe with a routing table**. It never touches the ORM, never
implements resume or acks — it forwards those frames to Channels over a Redis
Stream and relays whatever comes back. Auth stays in Django: the edge validates
the same single-use ticket Module 21 already mints, so there is one auth
implementation, not two.

### Measured, all three past the knee (20,000 conns, 100 rooms, ramping)

| Offered load (out msg/s) | Async Channels p99 | Raw ASGI p99 | **Hybrid p99** |
|--------------------------|--------------------|--------------|----------------|
| 100,000 (safe point) | 141 ms | 96 ms | **112 ms** |
| 150,000 (Channels' knee) | 690 ms | 180 ms | **248 ms** |
| 200,000 | **4,900 ms** | 410 ms | **690 ms** |
| 260,000 | timeouts | 1,980 ms | **2,410 ms** |

| | Async Channels | Raw ASGI | Hybrid |
|---|----------------|----------|--------|
| KB per connection | 45 (33 after Task 1) | 28 | **31** (edge) + Channels workers holding no sockets |
| Node knee (out msg/s) | 150,000 | 210,000 | **195,000** |
| Lines you own | 0 | ~300 | **~180** (edge; Channels keeps the rest) |
| Process fleets to operate | 1 | 1 | **2** |
| Where a socket's state lives | one place | one place | **two places** |

✅ **The hybrid gets ~87% of raw ASGI's throughput for ~60% of the code**, and it
keeps auth, resume, acks, presence, persistence, the admin and DRF exactly where
they are. That's a real result and it is the best-shaped of the three
compromises.

### The verdict: not yet, and here's the trigger

**No — Pulse should not build this today**, for the reason Task 3 established:
we are at **44% of the fan-out knee** and 6% of the density limit. The hybrid
optimizes an axis we are not binding on, and it costs:

- **Two fleets to deploy, drain and observe.** Module 18's graceful drain now has
  to be implemented twice — and the edge's version is harder, because it holds
  the sockets but doesn't own the session state.
- **A distributed seam through the middle of one connection.** Resume, ack, and
  delivery-time authz (Module 21) now span two processes. Every one of those was
  hard when it lived in one place.
- **A second on-call surface.** "Is the edge or the brain unhealthy?" is a new
  question at 3 a.m., and the answer is often "neither, the Stream between them
  is backed up."

**The condition that flips it:** when Threshold F is binding *and* adding nodes
has stopped working — concretely, when we are past ~5× today's fan-out (≈330,000
out msg/s), which means 3+ nodes on the 1.9×-per-node scaling curve, **and** a
room-affinity or cost constraint prevents just running more of them. At that
point the hybrid saves roughly 30% of the app fleet, and 30% of eight nodes is
worth a second codebase in a way that 30% of one node never is.

**And the condition that skips it entirely:** if we ever cross Threshold D
(density) — 250,000+ connections per node — neither Channels nor the hybrid is
the answer, because Python's floor is ~28 KB/connection at *best* and a Go or
Rust edge is ~4 KB. At that point you are not choosing a consumer model, you are
choosing a language for one tier, and the honest answer from the lab's verdict
section applies.

> **The generalizable lesson:** the hybrid is the *right shape* of compromise —
> keep the framework where it earns its keep, hand-roll only the measured hot
> path — and it is still wrong for us, because we measured which axis binds. An
> optimization aimed at the axis you aren't on is complexity with no upside, no
> matter how elegant its architecture diagram is. **Task 3 is the reason this
> answer is defensible; without the surface, "the hybrid sounds good" is just
> taste.**

---

## Record it

```markdown
## Module 15 — challenge

1. 45.3 -> 33.1 KB/conn (71% of the gap to raw ASGI's 28.1), +35% conns/worker.
   Irreducible 5.0 KB = Channels' two dispatch Tasks per connection — that IS
   the channel layer. Costs paid: no headers in scope, no scope["user"], no
   AuthMiddlewareStack, revocation push -> 10s reconciliation poll.
2. db threadpool optimum = 32 (4x cores), NOT more: ~53% of an ORM call is
   GIL-bound, so 192 threads is worse than 12. Pair it with Semaphore(32) +
   500ms admission timeout: 3.1% fast rejects beat a 7.2s p99.
3. Three variables, TWO degrees of freedom (room size is the multiplier).
   Pulse: 6% of density, 44% of the fan-out knee -> fan-out-bound, both today
   and at 3x. Raw ASGI's 1.5x density buys nothing we need; a 2nd node does
   (1.9x, Module 07). Thresholds: D = conns/node > 0.7 x RAM/KB-per-conn;
   F = out msg/s > 0.65 x knee AND nodes stopped being the cheap answer.
4. Debugging tax is NOT general: 12.3x on the blocking-call bug, 1.4x and 1.1x
   on the other two. PYTHONASYNCIODEBUG collapses 74 min -> 4 min because it
   makes a NON-LOCAL symptom local; flake8-async takes it to 0.
5. contextvars per FRAME (not per connection); trace id must ride INSIDE the
   envelope to cross the channel layer. The real bug: a shared task created
   lazily inside a request inherits that user's context forever. Two tests.
6. Hybrid = 87% of raw's throughput for 60% of the code, and still NO for
   Pulse — it optimizes the axis we aren't binding on. Trigger: ~5x fan-out
   AND nodes no longer cheap. Above 250k conns/node it's a Go/Rust edge, not
   a consumer model.
```

Then: [`16-kafka-comparison`](../../16-kafka-comparison/) — where the same
fan-out gets a completely different set of tradeoffs.
