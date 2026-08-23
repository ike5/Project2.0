# Module 04 — Channels Chat on a Single Node

**Goal:** Build a working chat server on Django Channels — and understand
exactly what the `InMemoryChannelLayer` is doing in your process's heap, because
the moment you start a second worker it stops working, and *that* is the reason
Phase 2 exists.

⏱️ ~5 hours · **Prerequisites:** Modules 00–03. You need the `apps/pulse`
project from [Module 02](../02-django-fast-track/) and the WebSocket wire
knowledge from [Module 03](../03-realtime-transports/).

> **This is the Python twin of the JVM course's
> [`04-stomp-chat-single-node`](../../spring-boot-chat-course/04-stomp-chat-single-node/).**
> Same job — first working chat server, then find its wall. The JVM twin's wall
> is that Spring's simple broker is a `ConcurrentHashMap` in one JVM's heap, so
> two *instances* can't see each other. **Python's wall is one level sharper:**
> the in-memory channel layer is a dict in one *process's* heap, and the GIL
> means a single machine needs one process per core. So two workers on **the same
> box** already can't see each other. You reach for Redis sooner, and for a more
> fundamental reason, than a JVM shop does.

---

## No STOMP. You design the protocol.

The JVM twin adopts STOMP at this point — a small spec that already answers
"how do I subscribe," "how do I address a subset of connections," "how do I ack."
Django Channels does not ship a subprotocol, and the community has not converged
on one. You get `AsyncJsonWebsocketConsumer`, which is "JSON in, JSON out," and
the rest is yours.

That is a real cost — you will re-derive subscriptions, acks, error frames and
heartbeats, and you will get one of them wrong the first time. It is also, for
this course, an advantage: **the wire protocol stops being a black box.** Module
05 designs it properly, on purpose, with the failure modes named. In this module
you use the smallest envelope that works so that the *transport* is what you are
studying.

```json
{"type": "message.create", "body": "hello"}          ← client → server
{"type": "message.new", "sender": "alice", "body": "hello", "ts": 1735689600123}
```

Two fields up, four down. Module 05 turns this into something you could ship.

---

## Channels in one page

Channels is not a WebSocket library. It is a **composition layer for ASGI
applications** plus **one distributed primitive**. Three ideas, and then you know
the whole thing.

### 1. A consumer is an ASGI application

```python
class RoomConsumer(AsyncJsonWebsocketConsumer): ...

RoomConsumer.as_asgi()        # -> an ASGI callable, like a view's .as_view()
```

`as_asgi()` returns `async def app(scope, receive, send)`. When a connection
arrives, Channels instantiates **one consumer object per connection** and drives
it with the ASGI event stream. That object lives for the whole connection, which
is why instance attributes (`self.room`, `self.user`) are the right place for
per-connection state — and why 50,000 connections means 50,000 live Python
objects, which is where most of the pinned **≈45 KB per idle connection** goes.

### 2. Routing is a tree of ASGI apps

```python
application = ProtocolTypeRouter({
    "http":      django_asgi_app,             # Django views + DRF from Module 02
    "websocket": AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter(websocket_urlpatterns)  # -> RoomConsumer.as_asgi()
        )
    ),
})
```

Every one of those is an ASGI app wrapping another ASGI app. `ProtocolTypeRouter`
dispatches on `scope["type"]`; `URLRouter` dispatches on `scope["path"]`;
`AuthMiddlewareStack` adds `scope["user"]` and passes through. **This is the
entire architecture of a Channels project**, and it composes exactly like
Django's `MIDDLEWARE` list — except that it is a separate onion that Django's
`MIDDLEWARE` never touches (Module 02, Part I).

### 3. The channel layer is the only thing that crosses a boundary

A **channel** is a named mailbox — one per connection, auto-generated
(`specific.a1b2c3!d4e5f6`). A **group** is a named set of channels. The
**channel layer** is the object that knows which channels are in which groups and
can deliver an event to all of them.

```python
await self.channel_layer.group_add("room.7", self.channel_name)      # subscribe
await self.channel_layer.group_send("room.7", {"type": "chat.message", ...})
await self.channel_layer.group_discard("room.7", self.channel_name)  # unsubscribe
```

Everything else in Channels is local to your process. **The channel layer is the
only piece with a story about crossing processes or machines** — and the
in-memory one has no such story, which is this module's punchline.

### The event-type → method-name contract

```python
await self.channel_layer.group_send(group, {"type": "chat.message", "data": {...}})
```
dispatches to a method named `chat_message` on every consumer in the group.
Dots and hyphens become underscores. If the method does not exist, Channels
raises `ValueError: No handler for message type chat.message`.

⚠️ **Keep this vocabulary distinct from your wire `type`.** They are different
namespaces with different audiences: `chat.message` is internal plumbing between
your consumers; `message.new` is a contract with a client you cannot redeploy.
Conflating them means an internal refactor becomes a protocol break. Pulse names
internal events `chat.*` and wire types `message.*` / `presence.*` / `typing.*`.

---

## The consumer lifecycle

```
   websocket.connect          ┌──────────────────────────────────┐
  ─────────────────────────▶  │  connect(self)                   │
                              │    • read scope (user, url args) │
                              │    • authorize                   │
                              │    • group_add(...)              │
                              │    • await self.accept()   ─── 101 Switching Protocols
                              └───────────────┬──────────────────┘
                                              │
   websocket.receive          ┌───────────────▼──────────────────┐
  ─────────────────────────▶  │  receive_json(self, content)     │  once per client frame
                              └───────────────┬──────────────────┘
                                              │ group_send
   channel layer              ┌───────────────▼──────────────────┐
  ─────────────────────────▶  │  chat_message(self, event)       │  once per delivery
                              │    • await self.send_json(...)   │
                              └───────────────┬──────────────────┘
                                              │
   websocket.disconnect       ┌───────────────▼──────────────────┐
  ─────────────────────────▶  │  disconnect(self, code)          │
                              │    • group_discard(...)  ALWAYS  │
                              └──────────────────────────────────┘
```

Four rules that cost people an afternoon each:

1. **Reject before `accept()`, not after.** If you `accept()` and then `close()`,
   the browser saw a successful handshake and your client's `onopen` fired. If
   you never call `accept()`, Channels sends a rejection and the client's
   `onerror` fires — which is what "unauthorized" should look like.
2. **You cannot `send_json` before `accept()`.** It raises.
3. **`disconnect()` runs on every close, clean or not** — including a `1006`
   abnormal close where the TCP connection just vanished. `group_discard` there
   or the group accumulates dead channel names.
4. **`connect()` blocks the handshake.** A slow database query in `connect()`
   delays the 101 response, and under a reconnect storm (Module 18) that is
   exactly when you have 20,000 clients doing it at once.

---

## The `InMemoryChannelLayer`, decompiled

```python
CHANNEL_LAYERS = {"default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}}
```

Strip the abstraction away and it is approximately this:

```python
class InMemoryChannelLayer:
    def __init__(self, capacity=100, group_expiry=86400):
        self.channels: dict[str, asyncio.Queue] = {}          # channel -> mailbox
        self.groups:   dict[str, dict[str, float]] = {}       # group -> {channel: added_at}
        self.capacity = capacity

    async def group_add(self, group, channel):
        self.groups.setdefault(group, {})[channel] = time.time()

    async def group_send(self, group, message):
        for channel in list(self.groups.get(group, {})):
            queue = self.channels.setdefault(channel, asyncio.Queue(self.capacity))
            try:
                queue.put_nowait((time.time() + 60, deepcopy(message)))
            except asyncio.QueueFull:
                raise ChannelFull(channel)
```

**Two dicts and a set of `asyncio.Queue`s, in one process's heap.** That is the
whole thing. Which tells you everything about its limits:

| Property | Consequence |
|----------|-------------|
| Plain Python dicts | Restart = every subscription gone |
| **Per-process** | **Worker A knows nothing about worker B's subscribers** |
| No persistence | A message published while a client reconnects is gone |
| No acks | `group_send` returns after `put_nowait`, not after delivery |
| `capacity=100` per channel | A slow consumer's mailbox fills and `group_send` **raises `ChannelFull`** |
| `deepcopy` per recipient | Fan-out to 200 members copies the dict 200 times, on your one core |

> **This is not a criticism.** The in-memory layer is fast, dependency-free, and
> completely correct for one process. Knowing precisely what it does is what lets
> you decide when you have outgrown it — which is the skill this whole course
> teaches. Note also that the last two rows are not fixed by Redis: `ChannelFull`
> and per-recipient serialization cost exist in `RedisChannelLayer` too, and
> Module 06 measures them.

---

## The wall: two workers on one box cannot see each other

This is the module's centrepiece, and it is worth being extremely precise about
why it happens, because "just add Redis" without understanding it leaves you
unable to debug the next thing.

Python has a **Global Interpreter Lock**: one thread per process executes Python
bytecode at a time. An `asyncio` event loop gives you cheap concurrency for
*I/O* — Module 01 held a million Tasks on one thread — but **all of it runs on
one core**. To use eight cores you run **eight worker processes**:

```bash
uvicorn pulse.asgi:application --workers 8 --loop uvloop
```

Eight processes. Eight interpreters. Eight event loops. **Eight completely
separate heaps.** And the channel layer is a dict in a heap.

```
                       one 8-core machine, uvicorn --workers 2
   ┌─────────────────────────────────┐   ┌─────────────────────────────────┐
   │  worker pid 51001               │   │  worker pid 51002               │
   │                                 │   │                                 │
   │  alice ──▶ RoomConsumer         │   │  bob ──▶ RoomConsumer           │
   │                                 │   │                                 │
   │  InMemoryChannelLayer           │   │  InMemoryChannelLayer           │
   │    groups = {                   │   │    groups = {                   │
   │      "room.7": {"...alice..."}  │   │      "room.7": {"...bob..."}    │
   │    }                            │   │    }                            │
   └─────────────────────────────────┘   └─────────────────────────────────┘
              │                                        │
              │  group_send("room.7", ...)             │  never hears about it
              ▼                                        ▼
        delivered to alice                         nothing. no error.
```

Alice types. Her consumer calls `group_send("room.7", …)`. Worker 51001's layer
looks up `"room.7"` in **its own dict**, finds one channel (alice's), and
delivers. Worker 51002's dict has a `"room.7"` key too, containing bob — but
nothing in the universe connects the two dictionaries. There is no shared memory
between OS processes, so there is no code that *could* join them.

**And nothing errors.** `group_send` returns successfully. Your logs are clean.
Your metrics show messages delivered. Bob simply never receives anything, and the
first report you get is "chat doesn't work for some people, sometimes" — which is
the worst bug report in software.

### Why this is sharper than the JVM twin's wall

| | JVM twin (Module 04) | This course (Module 04) |
|---|---|---|
| The shared registry | `ConcurrentHashMap` in the JVM heap | `dict` in the process heap |
| Threads sharing it | All of them — virtual threads share a heap | One event loop; other workers share nothing |
| To use all 8 cores | One JVM. Nothing changes. | **Eight processes. The registry fragments.** |
| First thing that breaks it | Deploying a **second instance** | Adding a **second worker on the same box** |
| So Redis is needed… | When you scale horizontally | **To use your second CPU core** |

On the JVM you can run one process, use all eight cores, and postpone the
distributed problem until you need a second machine. In Python you cannot. **The
GIL turns a scaling decision into a day-one architecture decision**, and that is
the single most important structural difference between these two courses.

The escape hatches, and why none of them work:

- **`--workers 1`.** Correct, and it caps your entire node at one core. Module 06
  measures exactly what that ceiling is: **≈150,000 outbound messages/second**
  before p99 hockey-sticks, versus the JVM twin's ≈450,000 across eight cores.
- **Threads instead of processes.** The GIL serializes Python bytecode, so eight
  threads doing JSON serialization get you roughly one core's throughput plus
  contention. This is not a Channels limitation; it is CPython.
- **Sticky routing by room.** Hash the room to a worker so every member of
  `room.7` lands on the same process. It genuinely works, and it is genuinely
  what some systems do — until a user is in twelve rooms and needs twelve
  sockets, or one room gets hot and one worker melts while seven idle. You have
  swapped a fan-out problem for a placement problem. (Module 14 revisits this
  shape as sharding, where it earns its keep.)
- **Shared memory / `multiprocessing.Manager`.** Now you have written a channel
  layer: serialization, liveness, cleanup, backpressure. Badly, and only for one
  machine. Redis is that, done, and it also crosses machines.

The honest conclusion, which Module 07 spends five hours earning: **for a
multi-core Python chat server, a cross-process channel layer is not an
optimization. It is a requirement.**

---

## Presence, and why the in-memory version lies

A room's member list feels like it should live next to the group. It cannot:

```python
ONLINE: dict[str, set[str]] = defaultdict(set)     # room -> {username}
```

That dict has every problem the channel layer has, plus one more: it is
**derived state that outlives its source**. A worker killed by `SIGKILL` never
runs `disconnect()`, so its users stay "online" forever in the surviving
workers' — no, wait, in *its own* dict, which just died. Both failure directions
happen, and neither self-heals.

The lab builds the naive version anyway, because seeing presence disagree
between two browser tabs on two workers is more convincing than a paragraph.
[`11-presence-and-rate-limiting`](../11-presence-and-rate-limiting/) rebuilds it
correctly as **TTL heartbeat keys in Redis**, where "online" means "wrote a key
in the last 30 seconds" — state that expires on its own is state that heals when
a process dies badly.

---

## Sync consumers exist, and they are a trap here

Channels ships `JsonWebsocketConsumer` (sync) alongside
`AsyncJsonWebsocketConsumer`. The sync one runs your handlers in a **thread**,
which means you can call the Django ORM directly — no `database_sync_to_async`,
no `SynchronousOnlyOperation`.

It is a real option with a real cost: one thread per connection, which is the
model Module 01 broke at ~32,000 threads and Module 02 measured queueing at 12
threads. [`15-async-sync-and-raw-asgi`](../15-async-sync-and-raw-asgi/)
benchmarks both properly and finds async consumers hold **2–3× more connections**
than sync ones.

**Pulse is async from here to Module 22**, which means the cardinal sin is
always in reach:

```python
async def receive_json(self, content):
    msg = Message.objects.create(...)          # ✗ blocks the loop. Every socket
                                               #   on this worker freezes.
    msg = await database_sync_to_async(...)()  # ✓ threadpool hop, loop stays free
    msg = await Message.objects.acreate(...)   # ✓ async ORM (still a threadpool
                                               #   underneath — Module 15 measures it)
```

Module 01 measured what a blocking call does to an event loop: 200 tasks × 100 ms
took **20 seconds instead of 108 ms**, and every task's individual latency was
20 seconds. In a consumer, "every task" is "every connected user."

---

## Backpressure, and the slow consumer

One phone on a bad train connection can hurt your worker. The mechanism:

1. Your consumer calls `await self.send_json(...)`.
2. The ASGI server calls `transport.write(...)`, which buffers if the socket's
   send window is full.
3. The client is not reading. The buffer grows. `write()` never applies
   backpressure to *you*, because ASGI's `send()` returns as soon as the frame
   is queued.
4. The channel layer's per-channel `capacity=100` fills, and the *next*
   `group_send` raises `ChannelFull` — **for the whole group send**, not just
   the slow member.

That last point is the surprising one and the lab makes you see it: on the
in-memory layer, one stuck consumer can make `group_send` raise for everyone.
The mitigations are the same shape as the JVM twin's `setSendBufferSizeLimit`:
bound the queue, and **disconnect the slow client rather than degrade the room**.
Choosing to lose one bad connection instead of your worker is correct behaviour,
not a bug.

---

## Authenticating the socket, briefly

`MIDDLEWARE` does not run for WebSocket scopes (Module 02, Part I). Channels has
its own stack:

```python
"websocket": AllowedHostsOriginValidator(     # CSWSH defense. Outside, always.
    AuthMiddlewareStack(                      # session cookie -> scope["user"]
        URLRouter(websocket_urlpatterns)))
```

- `AllowedHostsOriginValidator` compares the `Origin` header to `ALLOWED_HOSTS`.
  **CORS does not apply to WebSocket**; without this, any website your logged-in
  user visits can open an authenticated socket to your server.
  [`21-security-and-abuse-at-scale`](../21-security-and-abuse-at-scale/) performs
  that attack against your own server and then blocks it.
- `AuthMiddlewareStack` reads the session cookie and sets `scope["user"]`. It
  works same-origin, which is enough for this module. It hits the database
  *during the handshake*, which is a cost Module 21 removes by moving to a
  ticket the server can validate without a query.

For now: session auth, origin validation on, and a `4401` close code for
anonymous connections.

---

## Heartbeats

Module 03 watched an nginx `proxy_read_timeout` kill an idle WebSocket after
exactly 20 seconds with no error anywhere. The portable fix is not proxy config —
you do not control the NAT gateway in your customer's office — it is traffic.

Pulse sends an application-level heartbeat every **10 seconds**, inside a normal
data frame:

```json
{"type": "ping", "ts": 1735689600123}      → {"type": "pong", "ts": 1735689600124}
```

Uvicorn's `--ws-ping-interval` sends WebSocket *control* frames, which is
cheaper and which some corporate proxies strip. Doing both costs 2 bytes and
removes an entire class of "my sockets drop every 60 seconds" bug reports. The
`ts` echo also gives you a free per-connection RTT measurement, which Module 06
uses to separate "the server is slow" from "this user's network is slow."

---

## What's next

The lab wires `asgi.py` into a `ProtocolTypeRouter`, builds `RoomConsumer` with
join/leave/presence/heartbeat, persists messages with
`database_sync_to_async`, serves a browser client, measures the per-connection
memory cost against the pinned **≈45 KB**, fills a channel's mailbox until
`ChannelFull` fires — and then starts a second worker and watches two users in
the same room become invisible to each other, with clean logs and no errors.

See you in [`lab.md`](./lab.md).
