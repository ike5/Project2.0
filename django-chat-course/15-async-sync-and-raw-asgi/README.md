# Module 15 — Async, Sync & Raw ASGI

**Goal:** Build the same chat hot path three ways — sync (threadpool) consumers,
async consumers, and a hand-rolled raw-ASGI server — benchmark them head to head,
watch a single blocking call take down every connection on a worker, and be able
to say *with numbers* which runtime you'd choose and why.

⏱️ ~6 hours · **Prerequisites:** Modules 00–14.

---

## The question this module answers

Module 01 named the Python concurrency story, and it is not the JVM's. There are
**no virtual threads**. Python gives you exactly two ways to hold ten thousand
connections on one box:

- **Async** — one event loop per worker process, thousands of connections as
  cheap `asyncio` Tasks, *never block the loop*. This is what Pulse has run on for
  fourteen modules (`AsyncJsonWebsocketConsumer`).
- **Sync + a threadpool** — write blocking code, and let Channels dispatch each
  handler onto a pool of OS threads (`JsonWebsocketConsumer`). Concurrency is
  bounded by the pool.

This is the Python twin of the JVM course's
[`15-webflux-reactive-rebuild`](../../spring-boot-chat-course/15-webflux-reactive-rebuild/),
which pits virtual threads against a WebFlux event loop. The *shape* of that
tradeoff — an event loop is denser but blocking it is catastrophic, threads are
simpler but heavier — is identical here. The **numbers shift**, because Python's
per-connection object overhead and per-message encode/decode cost are higher, and
because there is no virtual-thread middle ground to close the gap.

And there is a third contestant the JVM course doesn't have in quite this form:
**raw ASGI**. Channels gives you groups, auth, routing, and a consumer lifecycle
for free. You can throw all of that away and write the WebSocket loop directly
against the ASGI protocol (via Starlette, or the `websockets` library). It is
faster and denser — and it costs you *hundreds of lines* to rebuild what Channels
handed you. That is the same "you lose the framework's messaging layer" cost the
JVM course pays when it drops STOMP for a hand-rolled WebFlux handler.

Three runtimes, one benchmark. Let's find the gaps.

---

## Sync consumers: blocking code on a threadpool

A `JsonWebsocketConsumer` (sync) looks like the code you'd write without thinking
about the event loop:

```python
from channels.generic.websocket import JsonWebsocketConsumer
from asgiref.sync import async_to_sync

class SyncChatConsumer(JsonWebsocketConsumer):
    def connect(self):
        self.room = self.scope["url_route"]["kwargs"]["room"]
        async_to_sync(self.channel_layer.group_add)(self.room, self.channel_name)
        self.accept()

    def receive_json(self, content):
        # This is a BLOCKING call. It is FINE here — we're on a threadpool thread,
        # not the event loop. That is the entire point of a sync consumer.
        msg = Message.objects.create(room_id=self.room, body=content["body"])
        async_to_sync(self.channel_layer.group_send)(
            self.room, {"type": "chat.message", "id": msg.id, "body": msg.body}
        )

    def chat_message(self, event):
        self.send_json({"type": "message.new", "id": event["id"], "body": event["body"]})
```

Here is what actually happens under the hood, and it is the whole story:

```
   Uvicorn event loop (1 thread)
        │  ws frame arrives for connection #7431
        ▼
   Channels' AsgiHandler  ──dispatch──►  ThreadPoolExecutor
                                            ├─ thread 1  running receive_json(#7431)  ← BLOCKS on the ORM, fine
                                            ├─ thread 2  running chat_message(#0002)
                                            ├─ ...
                                            └─ thread N  (N is bounded)
```

Every handler call — `connect`, `receive_json`, and *every* `chat_message`
fan-out delivery — is shipped to a thread via `asgiref`'s `SyncToAsync`. The
event loop itself never blocks, so one slow handler doesn't stall the others. But
the pool is **bounded**, and that bound is your concurrency ceiling.

> **Term — `SyncToAsync` / `AsyncToSync`:** `asgiref`'s bridges between the two
> worlds. `SyncToAsync` runs a blocking function on a thread and `await`s it from
> the loop; `AsyncToSync` runs a coroutine to completion from inside a thread.
> Channels' entire sync-consumer machinery is built on the first one. Module 01
> introduced them; this module measures what they cost.

The default `asgiref` threadpool is sized at `min(32, os.cpu_count() + 4)` — on
our 8-core reference box, **12 threads**. Twelve concurrent handler executions per
worker. That number is going to matter enormously in Part C of the lab.

### The resource cost

Each pool thread carries an OS thread stack. Python defaults to an 8 MB *virtual*
stack reservation per thread; resident memory is far less (a few hundred KB
under this workload), but it is not free, and it is not the ~45 KB an idle async
connection costs. More importantly, **a connection actively being served holds a
thread for the duration of its handler**, and there are only twelve of them.

---

## Async consumers: one loop, thousands of Tasks

The `AsyncJsonWebsocketConsumer` you've used since Module 04:

```python
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async

class AsyncChatConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.room = self.scope["url_route"]["kwargs"]["room"]
        await self.channel_layer.group_add(self.room, self.channel_name)
        await self.accept()

    async def receive_json(self, content):
        # The ORM is SYNC. Calling it directly here blocks the event loop and
        # every connection on this worker. We MUST push it to a thread:
        msg = await database_sync_to_async(Message.objects.create)(
            room_id=self.room, body=content["body"]
        )
        await self.channel_layer.group_send(
            self.room, {"type": "chat.message", "id": msg.id, "body": msg.body}
        )

    async def chat_message(self, event):
        await self.send_json({"type": "message.new", "id": event["id"], "body": event["body"]})
```

The difference that decides everything: `connect`, `receive_json`, and
`chat_message` run **as coroutines on the single event loop**. There is no pool.
Ten thousand connections are ten thousand `asyncio` Tasks, each ~45 KB of Python
objects. The loop hops between them at every `await`.

Which means the cardinal sin has teeth. In a sync consumer, `Message.objects.create()`
runs on a thread and blocks only that thread. In an async consumer, the same call
runs **on the event loop**, and while it waits for Postgres it stalls *every other
connection that worker holds*. That is not a metaphor — Part C measures p99 going
from 61 ms to over nine seconds from one accidental sync call, for all 5,000
connections on the worker. The Python analog of the JVM course's "8 ms JDBC call
in a cache loader made p99 8.9 s for everyone."

The discipline that prevents it is `database_sync_to_async` (and, since Django
4.1, the ORM's native `acreate`/`aget`/`async for`). Both move the blocking work
off the loop — the first onto Channels' bounded threadpool, the second onto
Django's async ORM path. **The threadpool is the same bounded resource the sync
model lives in.** You have not escaped it; you have made your use of it explicit
and rare. This is the Module 01 lesson stated exactly: *concurrency is free,
resources are not.*

> **Why there's no Python BlockHound.** The JVM course installs BlockHound to
> throw a runtime error the instant anything blocks an event-loop thread. Python
> has no direct equivalent that ships in the runtime, but `asyncio`'s debug mode
> (`PYTHONASYNCIODEBUG=1` or `loop.set_debug(True)`) logs any callback that runs
> longer than 100 ms, which catches the same class of bug. The lab turns it on and
> catches a real one. There are third-party libraries (`blockbuster`, `flake8-async`)
> that get closer to BlockHound's guarantee; treat the linter as mandatory and
> debug mode as your BlockHound.

---

## Raw ASGI: throw away the framework

Channels is a framework on top of the ASGI spec. The spec itself is small: your
app is a coroutine that receives a `scope`, a `receive` callable, and a `send`
callable, and loops.

```python
async def app(scope, receive, send):
    assert scope["type"] == "websocket"
    await send({"type": "websocket.accept"})
    while True:
        event = await receive()
        if event["type"] == "websocket.disconnect":
            break
        if event["type"] == "websocket.receive":
            await send({"type": "websocket.send", "text": event["text"]})
```

That is a complete echo server in eleven lines, no Channels, no Django. It is
also **faster and leaner** than a Channels consumer, because there is no consumer
class instantiation, no channel-name bookkeeping, no dispatch indirection, and no
group-layer subscription per connection.

But look at everything the eleven lines *don't* do, all of which Channels gave
you for free:

| Channels gives you | Raw ASGI: you write it |
|--------------------|------------------------|
| **Groups / fan-out** (`group_add`, `group_send` over Redis) | your own room→connections registry + a Redis Pub/Sub or Streams loop |
| **Routing** (`URLRouter`, path kwargs) | your own path parsing |
| **Auth** (`AuthMiddlewareStack`, sessions, the ticket flow) | your own token check and user lookup |
| **The consumer lifecycle** (connect/receive/disconnect, JSON coding) | your own state machine and `try/finally` |
| **Backpressure & flow control** on `send` | your own bounded outbound queue |
| **Reconnect/resume protocol wiring** | all of Module 10, by hand |

The lab rebuilds Pulse's fan-out hot path on raw ASGI with the `websockets`
library and measures it. The result is the same shape as the JVM course dropping
STOMP: **~2× the raw throughput on the hot path, and ~300 lines to reimplement
the parts of Channels you were actually using.** That is a real cost and it
belongs in the comparison, not a footnote.

---

## Servers: Daphne vs Uvicorn+uvloop vs Granian

The ASGI *server* is a separate choice from the *consumer* model, and it moves the
numbers more than people expect.

- **Daphne** — the reference Channels server, written in pure-Python Twisted. It
  is correct and battle-tested and it is the **slowest** of the three, because its
  event loop and protocol parsing are Python.
- **Uvicorn** — a fast ASGI server that can run on the stdlib `asyncio` loop or on
  **uvloop**, a Cython wrapper over libuv (the same event loop that powers
  Node.js). uvloop is a drop-in replacement that is measurably faster at the
  syscall-heavy work of shuffling frames.
- **Granian** — a newer server whose HTTP/WebSocket layer is written in **Rust**
  (on Tokio) with a thin Python ASGI bridge. It pushes more of the per-frame work
  out of Python entirely.

> **Term — uvloop:** a replacement `asyncio` event-loop policy built on libuv.
> `asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())` and everything else is
> unchanged. It is the single cheapest performance win in the async Python stack,
> and it is why the course's reference machine specifies "Uvicorn + uvloop."

The lab benchmarks all three under the identical async workload. The ranking is
stable — Daphne < Uvicorn(asyncio) < Uvicorn(uvloop) < Granian — and the spread
from slowest to fastest is roughly **1.4× on p99 and connection density**. uvloop
alone buys ~15–20% over stdlib asyncio for free.

---

## Should you even use Django for the socket edge?

The honest, uncomfortable question. Python holds ~40,000 connections per worker
and fans out ~150,000 messages/second across 8 workers before the knee (Module
06). A dedicated socket edge written in **Go** (goroutines, no GIL) or **Rust**
(Tokio) holds *hundreds of thousands* of connections per node and fans out
millions of messages/second, because it has no per-message Python interpreter
overhead and no GIL serializing CPU work.

The pattern this leads to is the **edge tier**: a thin, dumb WebSocket terminator
in Go or Rust that does nothing but hold connections and shuffle frames to and
from Redis, with all business logic — auth, persistence, the protocol, presence —
staying in Django, reached over the same Redis backbone Pulse already runs.

```
  browsers ──ws──► [ Go/Rust edge: hold sockets, no logic ] ──Redis──► [ Django: everything else ]
                     250k–1M conns/node                                  ORM, auth, protocol, admin
```

It is a real architecture and large chat systems use it. It is also a second
language, a second deployment, a second on-call surface, and a network hop
between "connection accepted" and "message persisted." The lab's verdict names
the exact condition under which it becomes worth it — and it is *not* Pulse's
current scale.

---

## What to expect from the benchmark

Async should win over sync on:
- **Connections per worker** — no per-connection thread, ~45 KB vs ~120 KB.
- **Concurrency under fan-out** — a 12-thread pool is a hard ceiling; the loop
  isn't.

Sync should win on:
- **Nothing at moderate scale, honestly** — but it wins on *simplicity*: no
  `async def`, no `await`, no "did I block the loop?" anxiety, and the entire
  blocking ecosystem (any library, any driver) just works.

Raw ASGI should win over both on **raw hot-path throughput and density**, and lose
on **everything Channels does that you'd have to rebuild.**

**The interesting questions are the sizes of the gaps** — and whether the sync
model's ceiling is one you'd ever actually hit. That's what the lab finds out.

---

## Where this leaves the decision

An honest framing, because there's noise here too:

- Async did **not** make sync consumers useless. For a low-connection-count
  service (an internal tool, an admin console's live tail), a sync consumer is
  simpler, safe from the blocking-the-loop footgun by construction, and fast
  enough.
- Async is **not** free. The blocking-call footgun is real, `database_sync_to_async`
  is a bounded resource you can exhaust, and the whole team must internalize "never
  block the loop" forever.
- Raw ASGI and a Go/Rust edge are **real options with real costs**, not
  cargo-culted micro-optimizations — and the condition that flips the decision is
  measurable, not a matter of taste.

The lab builds all three, catches a real blocking call and measures what it cost,
benchmarks the servers, and ends with a decision that has numbers behind it and
the conditions that would reverse it.

See you in [`lab.md`](./lab.md).
