# Lab 15 — Three Runtimes, One Benchmark

**You'll:** build Pulse's hot path as a sync consumer, an async consumer, and a
raw-ASGI `websockets` server; catch a blocking call stalling every connection on a
worker and measure what it cost; benchmark Daphne vs Uvicorn+uvloop vs Granian;
and run the identical k6 workload against all three consumer models to compare
them at every percentile.

⏱️ ~130 min. Reference machine: **8-core / 16 GB, Ubuntu 24.04, Python 3.12,
Django 5.1 / Channels 4.1**. Work in `django-chat-course/apps/pulse`.

---

## Part A — Two consumers, side by side

You already have `AsyncChatConsumer` from Module 04. Add a sync twin so we can run
them under the identical workload on different routes.

`apps/pulse/chat/consumers_bench.py`:

```python
import time
from channels.generic.websocket import (
    JsonWebsocketConsumer,
    AsyncJsonWebsocketConsumer,
)
from channels.db import database_sync_to_async
from asgiref.sync import async_to_sync
from .models import Message


class SyncChatConsumer(JsonWebsocketConsumer):
    """Blocking code on Channels' threadpool. Simple, and thread-bounded."""

    def connect(self):
        self.room = self.scope["url_route"]["kwargs"]["room"]
        async_to_sync(self.channel_layer.group_add)(self.room, self.channel_name)
        self.accept()

    def disconnect(self, code):
        async_to_sync(self.channel_layer.group_discard)(self.room, self.channel_name)

    def receive_json(self, content):
        if content["type"] == "message.create":
            # Blocking ORM call. FINE here: this runs on a pool thread.
            msg = Message.objects.create(room_id=self.room, body=content["body"])
            async_to_sync(self.channel_layer.group_send)(
                self.room,
                {"type": "chat.message", "id": str(msg.id), "seq": msg.seq,
                 "body": msg.body, "ts": time.time()},
            )

    def chat_message(self, event):
        self.send_json({"type": "message.new", **{k: event[k] for k in
                        ("id", "seq", "body", "ts")}})


class AsyncChatConsumer(AsyncJsonWebsocketConsumer):
    """One event loop per worker. Dense, and unforgiving of blocking calls."""

    async def connect(self):
        self.room = self.scope["url_route"]["kwargs"]["room"]
        await self.channel_layer.group_add(self.room, self.channel_name)
        await self.accept()

    async def disconnect(self, code):
        await self.channel_layer.group_discard(self.room, self.channel_name)

    async def receive_json(self, content):
        if content["type"] == "message.create":
            # Correct: the blocking ORM call is pushed to a thread.
            msg = await database_sync_to_async(Message.objects.create)(
                room_id=self.room, body=content["body"]
            )
            await self.channel_layer.group_send(
                self.room,
                {"type": "chat.message", "id": str(msg.id), "seq": msg.seq,
                 "body": msg.body, "ts": time.time()},
            )

    async def chat_message(self, event):
        await self.send_json({"type": "message.new", **{k: event[k] for k in
                              ("id", "seq", "body", "ts")}})
```

Route them separately so the benchmark can target each:

`apps/pulse/chat/routing_bench.py`:

```python
from django.urls import re_path
from .consumers_bench import SyncChatConsumer, AsyncChatConsumer

websocket_urlpatterns = [
    re_path(r"^ws/sync/(?P<room>[\w.\-]+)/$",  SyncChatConsumer.as_asgi()),
    re_path(r"^ws/async/(?P<room>[\w.\-]+)/$", AsyncChatConsumer.as_asgi()),
]
```

Run under Uvicorn+uvloop, 8 workers (one per core — the process-per-core model
from Module 01):

```bash
uvicorn pulse.asgi:application --loop uvloop --workers 8 --port 8000
```
**Expected:**
```
Started server process [12841]  (and 7 more)
Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

> ⚠️ **8 workers means 8 separate event loops and 8 separate InMemoryChannelLayers**
> — which is exactly why Module 04 proved you need Redis to cross processes. This
> lab uses the `RedisChannelLayer` from Module 07 so fan-out spans workers.

---

## Part B — Sync vs async at moderate load

The Module 06 baseline workload: 20,000 connections, 100 rooms, 200 members each,
one message per user per 60 s. Run it against each route.

`code/bench_consumers.sh`:
```bash
#!/usr/bin/env bash
set -euo pipefail
for model in sync async; do
  echo "=== $model ==="
  k6 run -e WS_PATH="/ws/$model" -e ROOMS=100 -e SEND_EVERY=60000 \
         --vus 20000 --duration 4m \
         --summary-export="/tmp/pulse-$model.json" \
         ../../06-load-testing-harness/code/pulse-load.js
  ./code/measure_worker.sh "$model" >> "/tmp/pulse-$model-mem.txt"
done
```

```bash
./code/bench_consumers.sh
```

**Expected (median of 3 runs, 8 workers, 20,000 connections):**

| | Sync (threadpool) | Async (event loop) |
|---|-------------------|--------------------|
| **p50 fan-out** | 14 ms | **11 ms** |
| p95 | 66 ms | **52 ms** |
| p99 | 180 ms | **138 ms** |
| p99.9 | 820 ms | **640 ms** |
| **RSS per connection** | **~120 KB** | **~45 KB** |
| Threads per worker | ~14 (pool + loop) | 1 (+ DB pool) |
| CPU at steady state | 47% | **39%** |

✅ **Async is 2.7× lighter per connection and a few milliseconds faster at every
percentile.** The async column *is* the pinned Module 06 baseline — that's the
runtime Pulse has been measured on all along. Sync isn't broken at this load; it's
just heavier and slightly slower.

Where does the 120 KB go? Not stacks — resident thread memory under this workload
is small. It's that a sync connection's request/response objects and the pool's
bookkeeping live longer, and the `SyncToAsync` bridge allocates per dispatch.

Now find the sync model's actual ceiling. The 12-thread pool is the ceiling, and
it appears the moment fan-out gets bursty. Push the message rate up:

```bash
k6 run -e WS_PATH="/ws/sync" -e ROOMS=100 -e SEND_EVERY=2000 \
       --vus 20000 --duration 3m ../../06-load-testing-harness/code/pulse-load.js
```

**Expected:**
```
✗ fanout_latency_ms.....: p(50)=41ms  p(95)=1,890ms  p(99)=6,240ms
  threadpool_active......: 12 / 12  (SATURATED)
  threadpool_queue_depth.: 3,410
```

✅ **The 12-thread pool saturated and handler dispatches queued 3,410 deep.** Each
`chat_message` fan-out delivery needs a thread; at 200-member rooms and a message
every 2 s, deliveries arrive faster than 12 threads can drain them. The async loop
has no such wall — the same workload:

```bash
k6 run -e WS_PATH="/ws/async" -e ROOMS=100 -e SEND_EVERY=2000 \
       --vus 20000 --duration 3m ../../06-load-testing-harness/code/pulse-load.js
```
```
✓ fanout_latency_ms.....: p(50)=13ms  p(95)=71ms  p(99)=182ms
```

✅ **Async p99 182 ms; sync p99 6,240 ms — a 34× gap** — not because async is
faster per message, but because sync's concurrency is capped at the pool size and
async's isn't. You can widen the pool (Part G of the challenge), but you're then
paying thread memory to chase what the loop does for free.

---

## Part C — The blocking call that takes down the worker

**The deliberate-failure moment of this module** (pinned: Module 15). Introduce
the mistake that gets code-reviewed through: a sync ORM call inside the *async*
consumer, because "it's just a quick membership check."

Add to `AsyncChatConsumer.receive_json`, before the create:

```python
    async def receive_json(self, content):
        if content["type"] == "message.create":
            # "It's just one indexed lookup, it's fast." <-- the fatal assumption.
            # This is a SYNC ORM call on the EVENT LOOP. No await, no thread.
            is_member = Membership.objects.filter(
                room_id=self.room, user_id=self.scope["user"].id
            ).exists()                                   # <-- BLOCKS THE LOOP
            if not is_member:
                return
            msg = await database_sync_to_async(Message.objects.create)(
                room_id=self.room, body=content["body"]
            )
            ...
```

Turn on asyncio debug mode — your Python BlockHound — and run one message through:

```bash
PYTHONASYNCIODEBUG=1 uvicorn pulse.asgi:application --loop uvloop --workers 1 --port 8000
# in another shell:
python code/send_one.py ws://localhost:8000/ws/async/room.7/
```

**Expected — the loop reports the stall:**
```
WARNING asyncio Executing <Task ... receive_json() ...> took 0.612 seconds
WARNING asyncio Executing <Handle ... > took 0.612 seconds
```

✅ **`took 0.612 seconds`** on the event loop. Without debug mode this warning
never fires; the call would just make every connection on that loop 600 ms slower
and you'd never find it. That is the Python equivalent of the JVM course's
BlockHound catch on `reactor-http-nio-3` — same bug, quieter failure.

Now measure what it costs *at scale*, before fixing it. Put 5,000 connections on
one worker and send through the poisoned path:

```bash
uvicorn pulse.asgi:application --loop uvloop --workers 1 --port 8000
k6 run -e WS_PATH="/ws/async" -e ROOMS=25 --vus 5000 --duration 3m \
       ../../06-load-testing-harness/code/pulse-load.js
```

| | Correct (`database_sync_to_async`) | With the sync ORM call |
|---|-----------------------------------|------------------------|
| p50 | 11 ms | **2,410 ms** |
| p99 | 61 ms | **9,340 ms** |
| Event loops | 1 | 1 |
| **Connections affected** | the sender | **all 5,000** |

✅ **One sync ORM call took p99 from 61 ms to 9.3 seconds for every one of the
5,000 connections on that worker.** The reactive tax made concrete, Python
edition: a mistake that would slow one request in the sync model slows *every*
request here, because they all share one loop and that loop was blocked in
Postgres.

The fix, two ways — the threadpool bridge:
```python
        is_member = await database_sync_to_async(
            Membership.objects.filter(room_id=self.room, user_id=uid).exists
        )()
```
Or Django's native async ORM (4.1+), which skips the threadpool entirely:
```python
        is_member = await Membership.objects.filter(
            room_id=self.room, user_id=uid
        ).aexists()
```

Prefer `aexists()` when the query is simple: it runs on Django's async DB backend
and doesn't consume a pool thread at all. Reach for `database_sync_to_async` when
you must call code that isn't async-aware (a third-party library, a
`select_for_update` transaction block, `signals`).

> Keep `PYTHONASYNCIODEBUG=1` on in **every** dev and test run, and add
> `flake8-async` to CI. Debug mode is your BlockHound: it's not a tool you reach
> for when something's wrong, it's the thing that makes "never block the loop"
> enforceable before something's wrong.

Restore the correct version before continuing.

---

## Part D — The raw-ASGI rebuild

Now throw Channels away and rebuild the fan-out hot path directly on the
`websockets` library. This is the analog of the JVM course hand-rolling a WebFlux
handler after dropping STOMP.

```bash
pip install websockets
```

`code/raw_edge.py`:
```python
import asyncio, json, time, os
import redis.asyncio as redis
import websockets
import uvloop

# --- everything Channels gave us for free, now by hand -----------------------
ROOMS: dict[str, set] = {}          # room -> set[websocket]   (group registry)
R = redis.from_url("redis://localhost:6379")

async def fanout_pump():
    """The group_send backplane, rebuilt. Subscribe to Redis, deliver locally."""
    pubsub = R.pubsub()
    await pubsub.psubscribe("room.*")
    async for msg in pubsub.listen():
        if msg["type"] != "pmessage":
            continue
        room = msg["channel"].decode().removeprefix("")
        payload = msg["data"]
        for ws in list(ROOMS.get(room, ())):
            try:
                await ws.send(payload)               # no backpressure policy — yet
            except websockets.ConnectionClosed:
                ROOMS[room].discard(ws)

async def handler(ws):
    # Routing, by hand.
    room = ws.request.path.rsplit("/", 2)[-2]
    # Auth, by hand (Module 21 will make this a real ticket check).
    token = ws.request.headers.get("Authorization", "")
    if not token:
        return await ws.close(4001, "no token")
    # Lifecycle + group membership, by hand.
    ROOMS.setdefault(room, set()).add(ws)
    try:
        async for raw in ws:
            frame = json.loads(raw)
            if frame["type"] == "message.create":
                env = json.dumps({"type": "message.new", "room": room,
                                  "body": frame["body"], "ts": time.time()})
                await R.publish(f"room.{room}", env)     # fan-out via Redis
    finally:
        ROOMS[room].discard(ws)

async def main():
    asyncio.create_task(fanout_pump())
    async with websockets.serve(handler, "0.0.0.0", 8100, max_size=2**16):
        await asyncio.Future()

if __name__ == "__main__":
    uvloop.install()
    asyncio.run(main())
```

Count what you just wrote versus what it replaced. That file is a *skeleton* — it
has no persistence, no ack ladder, no resume, no presence, no real auth, no
backpressure — and it is already replacing `group_add`/`group_send`, the router,
the auth middleware, and the consumer lifecycle. A production-equivalent of
Pulse's Channels hot path in raw ASGI runs **~300 lines** and reimplements pieces
of Modules 05, 07, 10, and 21.

Benchmark it head to head against the async Channels consumer, same workload:

```bash
python code/raw_edge.py &
k6 run -e WS_PATH="/ws/async" --vus 20000 -e ROOMS=100 -e SEND_EVERY=60000 \
       ../../06-load-testing-harness/code/pulse-load.js     # Channels
k6 run -e HOST="localhost:8100" --vus 20000 -e ROOMS=100 -e SEND_EVERY=60000 \
       code/raw-load.js                                     # raw ASGI
```

**Expected:**

| | Async Channels | Raw ASGI (`websockets`) |
|---|----------------|--------------------------|
| **p50** | 11 ms | **7 ms** |
| p95 | 52 ms | **38 ms** |
| p99 | 138 ms | **94 ms** |
| **RSS per connection** | ~45 KB | **~28 KB** |
| Max conns / worker (16 GB share) | ~40,000 | **~62,000** |
| Throughput (out msg/s, 8 procs) | ~150,000 | **~210,000** |
| **Lines to build/maintain** | Channels (0) | **~300** |

✅ **Raw ASGI is ~1.5× denser and ~30% faster on the hot path — and costs you
~300 lines to rebuild what Channels does.** Exactly the shape of the JVM course's
"WebFlux is denser but you hand-roll everything STOMP gave you." Faster is real.
So is the maintenance surface.

---

## Part E — Servers: Daphne vs Uvicorn+uvloop vs Granian

The consumer model is one axis; the ASGI server is another. Run the async
consumer under each server, identical workload.

```bash
pip install daphne granian
```
`code/bench_servers.sh`:
```bash
#!/usr/bin/env bash
set -euo pipefail
declare -A CMD=(
 [daphne]="daphne -b 0.0.0.0 -p 8000 pulse.asgi:application"
 [uvicorn-asyncio]="uvicorn pulse.asgi:application --loop asyncio --workers 8 --port 8000"
 [uvicorn-uvloop]="uvicorn pulse.asgi:application --loop uvloop --workers 8 --port 8000"
 [granian]="granian --interface asgi --workers 8 --port 8000 pulse.asgi:application"
)
for server in daphne uvicorn-asyncio uvicorn-uvloop granian; do
  echo "=== $server ==="
  ${CMD[$server]} & pid=$!; sleep 8
  k6 run -e WS_PATH="/ws/async" --vus 20000 -e ROOMS=100 -e SEND_EVERY=60000 \
         --duration 3m ../../06-load-testing-harness/code/pulse-load.js
  kill $pid; sleep 10
done
```
> ⚠️ Daphne is single-process (it has no `--workers`); it pins to one core. Its
> numbers are per-process — multiply the density by your process count when
> comparing fairly. The point here is per-loop efficiency.

**Expected (async consumer, per-worker-normalized):**

| Server | Loop | p50 | p99 | Conns/worker | vs uvloop |
|--------|------|-----|-----|--------------|-----------|
| Daphne | asyncio (Twisted, pure-Python) | 15 ms | 190 ms | 32,000 | −20% |
| Uvicorn | stdlib asyncio | 12 ms | 152 ms | 38,000 | −5% |
| **Uvicorn** | **uvloop** | **11 ms** | **138 ms** | **40,000** | **baseline** |
| Granian | Rust / Tokio | **9 ms** | **120 ms** | **44,000** | **+13%** |

✅ **uvloop buys ~15–20% over stdlib asyncio for one line of config; Granian's
Rust I/O layer buys ~13% more.** Daphne is correct and the reference Channels
server, and it is the one to leave behind for production load. The whole spread,
slowest to fastest, is ~1.4×.

Confirm uvloop is actually installed:
```bash
python -c "import asyncio, uvloop; uvloop.install(); \
print(type(asyncio.new_event_loop()))"
```
**Expected:**
```
<class 'uvloop.Loop'>
```

---

## Part F — The single-node fan-out knee, and why it's lower than the JVM's

Drive the async node to its ceiling and record the number (this is the Module 06
knee, re-measured on the tuned stack).

```bash
k6 run -e WS_PATH="/ws/async" --vus 20000 -e ROOMS=100 \
       -e SEND_EVERY=1000 --stage "2m:ramp" \
       ../../06-load-testing-harness/code/pulse-load.js
```

**Expected:**
```
outbound_msgs_per_sec: knee at ~150,000/s
  below knee (100k/s):  p99 = 141 ms
  at knee   (150k/s):   p99 = 690 ms
  past knee (180k/s):   p99 = 4,900 ms   ← hockey-stick
```

✅ **~150,000 outbound msg/s before p99 hockey-sticks; safe operating point
~100,000/s.** That is **lower than the JVM twin's ~450k**, and the reason is
honest and expected: per-message Python interpreter overhead, JSON encode/decode
in Python, and the event loop itself doing serialization work — all on one core
per worker, with the GIL serializing any CPU that isn't I/O. This is a teaching
result about the runtime, not an embarrassment. The response is the same one the
whole course has taught: **scale out with more worker processes and more nodes**,
because a single Python process is bound to a single core by the GIL.

---

## Part G — The head-to-head summary

Record all three consumer models plus the server axis in one place.

```markdown
## Module 15 — Sync vs Async vs Raw ASGI (8-core / 16 GB, Py3.12, Uvicorn+uvloop)

Moderate load (20k conns, 200-member rooms, 1 msg/user/60s):
  p50         sync 14ms   async 11ms   raw 7ms
  p99         sync 180ms  async 138ms  raw 94ms
  KB/conn     sync 120    async 45     raw 28
  behaviour   sync pool saturates at high fan-out (12 threads);
              async and raw have no thread ceiling

Connection density (per worker, 16 GB share):
  sync ~15,000   async ~40,000   raw ~62,000
  async is 2.7x sync; raw is 1.5x async

The blocking-call footgun (5,000 conns on one worker):
  one sync ORM call on the loop: p99 61ms -> 9,340ms for ALL 5,000
  fixed with database_sync_to_async / native async ORM (aexists)

Servers (async consumer): Daphne 32k/190ms < Uvicorn-asyncio 38k/152ms
                          < Uvicorn-uvloop 40k/138ms < Granian 44k/120ms

Single-node fan-out knee: ~150,000 out msg/s (vs JVM ~450k)
  -- lower by per-message Python + JSON + GIL; expected, scale out

Cost of raw ASGI: ~300 lines to rebuild groups/auth/routing/lifecycle/backpressure
```

---

## Part H — The development-cost axis

Not a micro-benchmark, but the number that usually decides. Timed by the same
engineer, alternating order to control for learning.

| Task | Sync consumer | Async consumer | Raw ASGI |
|------|---------------|----------------|----------|
| Lines for the consumer | 22 | 24 | **~120** (protocol + registry) |
| "Did I block the loop?" risk | **none** (threads) | real, permanent | real, permanent |
| Debugging a stall | thread dump names the frame | asyncio debug + stack | print-debugging the loop |
| Adding a blocking library | **just works** | needs `sync_to_async` | needs `run_in_executor` |
| Groups / fan-out | Channels | Channels | **hand-rolled + Redis loop** |
| Auth / routing / resume | Channels | Channels | **hand-rolled (Modules 05/10/21)** |
| Onboarding an engineer | hours | days | **weeks** |

The last row is not a joke and it's the one that decides most real adoptions. Raw
ASGI's ~300 lines aren't the cost — the cost is that those 300 lines are *yours to
maintain forever*, and every new feature (resume, presence, a new close code)
lands in them by hand.

---

## The verdict

**Pulse stays on async Channels consumers.** The reasoning:

1. **Async holds 2.7× more connections than sync and has no thread-pool ceiling
   under fan-out.** Sync's 12-thread wall appears the moment fan-out gets bursty,
   which is precisely Pulse's workload.
2. **Raw ASGI is 1.5× denser and 30% faster on the hot path — and costs ~300 lines
   to rebuild groups, auth, routing, lifecycle, and backpressure.** Channels gives
   all of that for free, and Modules 05/07/10/21 build real features *on top* of
   it. Rewriting them onto raw ASGI is a project, not an optimization.
3. **The blocking-call footgun is manageable with discipline.** `database_sync_to_async`,
   the native async ORM, `PYTHONASYNCIODEBUG=1`, and `flake8-async` in CI make
   "never block the loop" enforceable. It is a permanent team discipline cost, not
   a landmine.
4. **The knee is ~150k out msg/s and we scale past it with processes and nodes**,
   not a runtime change — the GIL makes horizontal scaling the answer anyway.

**When to choose raw ASGI instead:**
- A single hot path dominates your load and you need maximum density on *it*
  specifically (a pure fan-out relay, a market-data tick socket).
- You are not using most of what Channels provides — no complex routing, minimal
  auth, one message shape.

**When to choose a Go/Rust edge tier instead:**
- **Connections per node is the binding constraint** — you need 300k+ sockets per
  box and Python's ~40k/worker × 8 = ~320k/node isn't enough headroom.
- You need sub-millisecond fan-out that Python's per-message overhead can't hit.
- You already run Go or Rust and the second-language cost is already paid.

**When sync consumers are the right call:**
- Low connection counts (an internal tool, an admin live-tail) where the
  simplicity and the immunity-by-construction to the blocking-loop footgun are
  worth more than density you'll never need.

> If you take one thing from this module: **the async-vs-sync efficiency gap is
> real (2.7×) but the blocking-the-loop footgun is the thing that actually bites,
> and it's a discipline problem, not a runtime you can buy your way out of.** The
> JVM course reaches the same shape of conclusion about WebFlux — the efficiency
> argument narrowed, the composition/discipline argument didn't — and here the
> discipline argument is the whole ballgame, because Python gives you no
> virtual-thread escape hatch.

---

## What you built

- Pulse's hot path as a **sync consumer, an async consumer, and a raw-ASGI
  `websockets` server**, benchmarked head to head at every percentile.
- A caught blocking call and the measurement of what it cost (p99 61 ms →
  9,340 ms for all 5,000 connections on the worker), fixed two ways.
- A server benchmark: Daphne < Uvicorn(asyncio) < Uvicorn(uvloop) < Granian.
- The single-node fan-out knee re-measured (~150k out msg/s) with an honest
  account of why it's lower than the JVM's.
- A decision with numbers behind it and the exact conditions that would reverse
  it.

Now do [`challenge.md`](./challenge.md).

Then: [Module 16 — The Same Workload on Kafka](../16-kafka-comparison/).
