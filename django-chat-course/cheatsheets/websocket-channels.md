# Cheatsheet — WebSocket & Django Channels

---

## The WebSocket handshake

**Client request:**
```http
GET /ws/room/42/ HTTP/1.1
Host: chat.example.com
Upgrade: websocket
Connection: Upgrade
Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==
Sec-WebSocket-Version: 13
Origin: https://chat.example.com
Sec-WebSocket-Protocol: pulse.v1, ticket.<short-lived-ticket>
```

**Server response:**
```http
HTTP/1.1 101 Switching Protocols
Upgrade: websocket
Connection: Upgrade
Sec-WebSocket-Accept: s3pPLMBiTxaQ9kYGzzhZRbK+xOo=
Sec-WebSocket-Protocol: pulse.v1
```

`Sec-WebSocket-Accept` = `base64(sha1(key + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"))`.
The GUID is a constant from the RFC. It proves the server understood the
handshake — it is **not** authentication.

> **`Origin` is your only browser-side defense.** CORS does not apply to
> WebSocket. Validate it in Channels with `AllowedHostsOriginValidator` (or a
> custom middleware) or you have a CSWSH hole. Module 21 exploits it, then blocks
> it.

> **Browsers can't set headers on `new WebSocket()`** and won't reliably send
> cookies cross-origin. That's why auth rides in the URL as a short-lived
> **ticket** (or in `Sec-WebSocket-Protocol`), which the JS API *can* set.

---

## Frame layout (RFC 6455)

```
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-------+-+-------------+-------------------------------+
|F|R|R|R| opcode|M| Payload len |    Extended payload length    |
|I|S|S|S|  (4)  |A|     (7)     |             (16/64)           |
|N|V|V|V|       |S|             |   (if payload len==126/127)   |
| |1|2|3|       |K|             |                               |
+-+-+-+-+-------+-+-------------+ - - - - - - - - - - - - - - - +
|     Extended payload length continued, if payload len == 127  |
+ - - - - - - - - - - - - - - - +-------------------------------+
|                               |Masking-key, if MASK set to 1  |
+-------------------------------+-------------------------------+
|    Masking-key (continued)    |          Payload Data         |
+-------------------------------- - - - - - - - - - - - - - - - +
```

| Opcode | Meaning |
|--------|---------|
| `0x0` | Continuation (of a fragmented message) |
| `0x1` | Text (UTF-8) |
| `0x2` | Binary |
| `0x8` | Close |
| `0x9` | Ping |
| `0xA` | Pong |

**Payload length encoding:**

| 7-bit value | Actual length |
|-------------|---------------|
| 0–125 | that value |
| 126 | next **2** bytes, big-endian |
| 127 | next **8** bytes, big-endian (high bit must be 0) |

**Masking:** client→server frames MUST set `MASK=1` and XOR the payload:
`unmasked[i] = masked[i] ^ key[i % 4]`. Server→client frames MUST NOT be masked.

**Minimum frame sizes:** a server→client text frame costs **2 bytes** of overhead;
a client→server one costs **6** (2 + 4-byte mask). At 100k connections × 1
heartbeat/30 s that overhead is real but small — your JSON payload dominates.

> Channels/Daphne/Uvicorn parse and produce these frames for you. You almost never
> touch bytes — the ASGI server hands your consumer a decoded `text`/`bytes`
> payload. Module 03 has you decode one by hand once so the abstraction is never
> magic.

### Close codes worth knowing

| Code | Meaning |
|------|---------|
| 1000 | Normal closure |
| 1001 | Going away (server shutting down / page navigating) |
| 1006 | **Abnormal** — no close frame was received. You never send this; it's what a client library reports when the TCP connection just died. The most common code you'll see in production. |
| 1009 | Message too big |
| 1011 | Internal server error |
| 4000–4999 | Application-defined. Use these for "token expired", "kicked", "rate limited". `await self.close(code=4001)` from a consumer. |

---

## The ASGI scope

Every connection carries a `scope` dict, created once and alive for the whole
connection. In a consumer it's `self.scope`.

```python
scope = {
    "type": "websocket",
    "path": "/ws/room/42/",
    "headers": [(b"origin", b"https://..."), ...],   # list of byte tuples
    "query_string": b"ticket=abc",
    "client": ("203.0.113.7", 54834),
    "subprotocols": ["pulse.v1"],
    "url_route": {"kwargs": {"room": "42"}},           # added by URLRouter
    "user": <User>,                                     # added by AuthMiddleware
    "session": <Session>,                               # added by SessionMiddleware
}
```

- `scope["user"]` exists **only** if an auth middleware ran (see routing below).
  Before that it's absent — reading it raises `KeyError`.
- `scope["url_route"]["kwargs"]` is how you get `room` out of the URL — the analog
  of a view's path kwargs.
- Scope is **not** where you keep mutable per-connection state; use instance
  attributes on the consumer (`self.room_group`, `self.seq`) for that.

---

## Consumer lifecycle

```python
from channels.generic.websocket import AsyncJsonWebsocketConsumer

class RoomConsumer(AsyncJsonWebsocketConsumer):

    async def connect(self):
        self.room = self.scope["url_route"]["kwargs"]["room"]
        self.group = f"room.{self.room}"
        user = self.scope["user"]
        if user.is_anonymous:
            await self.close(code=4401)               # reject BEFORE accept
            return
        await self.channel_layer.group_add(self.group, self.channel_name)
        await self.accept(subprotocol="pulse.v1")     # completes the 101 handshake

    async def receive_json(self, content):            # one inbound client message
        # content is already-parsed JSON — your envelope from Module 05
        await self.channel_layer.group_send(self.group, {
            "type": "chat.message",                   # -> calls chat_message()
            "payload": content,
        })

    async def chat_message(self, event):              # channel-layer -> this socket
        await self.send_json(event["payload"])

    async def disconnect(self, code):
        await self.channel_layer.group_discard(self.group, self.channel_name)
```

**The order that bites everyone:**

1. `connect()` runs. You decide to accept or reject.
2. **If you never call `await self.accept()`, the client gets a rejected
   handshake** — Channels sends `close`. Reject unauthenticated sockets *before*
   `accept()`, not after.
3. Only after `accept()` can you `send_json`. Sending before accept is an error.
4. `receive_json(content)` runs once per inbound client message.
5. `disconnect(code)` runs once, on any close (clean or 1006). **Always
   `group_discard` here** or the group leaks a dead channel name.

### The method-name → event-type contract

`group_send({"type": "chat.message", ...})` dispatches to a method named
`chat_message` (dots and dashes become underscores). If the method doesn't exist,
Channels raises. This string is your internal event vocabulary — keep it distinct
from your *wire* message `type` (the client-facing envelope).

| Method | When it runs |
|--------|--------------|
| `connect()` | On the `websocket.connect` event (handshake) |
| `receive()` / `receive_json(content)` | Each inbound client frame |
| `disconnect(code)` | On close, from either side |
| `<event_type>(event)` | When something is `group_send`/`send`-ed to this channel |

---

## The channel-layer API

`self.channel_layer` (or `get_channel_layer()` from outside a consumer) is the
whole cross-process/cross-machine surface:

```python
# groups
await layer.group_add(group, channel)        # subscribe a channel
await layer.group_discard(group, channel)    # unsubscribe
await layer.group_send(group, event)         # fan-out to every channel in group

# point-to-point
await layer.send(channel_name, event)        # to one specific channel
name = await layer.new_channel()             # a fresh single-use channel name

# from SYNC code (a Celery task, a signal, a mgmt command)
from asgiref.sync import async_to_sync
async_to_sync(layer.group_send)(group, event)
```

- Every event dict **must** have a `"type"` key that maps to a handler method.
- `group_send` is **fire-and-forget** on the default Redis (Pub/Sub) layer — it
  returns after publishing, not after delivery. That's the at-most-once property
  you measure in Module 07.
- Group membership on the Redis layer expires (`group_expiry`, default 86400s). A
  consumer that never `group_discard`s but crashes will eventually age out — but
  don't rely on it; discard in `disconnect`.

---

## Touching the database from an async consumer

The Django ORM is **synchronous**. Calling it directly inside an `async def`
handler blocks the event loop and stalls **every connection this worker holds** —
the cardinal sin of the course (measured in Module 15: p99 60 ms → seconds).

```python
from channels.db import database_sync_to_async

# WRONG — blocks the loop; every socket on this worker freezes
def bad(self):
    msg = Message.objects.create(room_id=self.room, body=body)   # sync, in async

# RIGHT — offload the sync ORM call to the threadpool
@database_sync_to_async
def _save(self, body):
    return Message.objects.create(room_id=self.room, body=body)

async def receive_json(self, content):
    msg = await self._save(content["body"])                      # awaited, non-blocking
```

Two things to keep straight:

- `database_sync_to_async` is `sync_to_async` pre-wired to close stale DB
  connections — use it for ORM work specifically.
- Django 4.1+ also has **native async queries** (`await Message.objects.acreate(...)`,
  `async for m in qs`). They avoid the threadpool but not every ORM feature is
  async yet. Module 15 benchmarks both paths.

> The threadpool is a **bounded resource**. Concurrency is free until the pool is
> full, then it's a queue. "Concurrency is free, resources are not" (Module 01)
> lives right here.

Calling async from sync goes the other way — `async_to_sync(...)` — and must
**not** be called from a thread that already has a running event loop (it raises).
This is why a Celery task uses `async_to_sync(layer.group_send)(...)` cleanly (no
loop running) but calling it from inside a consumer is an error.

---

## Routing

```python
# asgi.py
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator
from django.core.asgi import get_asgi_application
from django.urls import re_path
from chat.consumers import RoomConsumer

websocket_urlpatterns = [
    re_path(r"^ws/room/(?P<room>\w+)/$", RoomConsumer.as_asgi()),
]

application = ProtocolTypeRouter({
    "http": get_asgi_application(),                    # normal Django views + DRF
    "websocket": AllowedHostsOriginValidator(          # origin check (CSWSH defense)
        AuthMiddlewareStack(                           # populates scope["user"]
            URLRouter(websocket_urlpatterns)
        )
    ),
})
```

- Middleware order matters: `AllowedHostsOriginValidator` **outside**
  `AuthMiddlewareStack` so a bad origin is rejected before you touch the session.
- `AuthMiddlewareStack` adds `scope["user"]` from the Django session cookie. For
  token/ticket auth you write your own middleware that puts the user on the scope
  (Module 21).
- `.as_asgi()` turns the consumer class into an ASGI application, the socket
  analog of `.as_view()`.

---

## ASGI servers: Daphne vs Uvicorn+uvloop vs Granian

| | Daphne | Uvicorn + uvloop | Granian |
|---|--------|------------------|---------|
| Language | Pure Python | Python + Cython + libuv | Rust |
| From | The Channels project | Encode | Independent |
| Speed | Baseline | ~2–4× Daphne on socket load | Fastest in Module 15's runs |
| Workers | `--workers` (procs) | `--workers N` (one proc per core) | `--workers` + optional threads |
| Maturity for Channels | Reference; most battle-tested | Standard production choice | Newer; benchmarked, not yet default |
| Use when | Learning, simplest setup | Production ASGI (this course's default) | You've measured and want the last 20% |

```bash
# dev — one process, auto-reload
daphne -b 0.0.0.0 -p 8000 pulse.asgi:application

# production — one worker process PER CORE (the GIL tax; see Module 01)
uvicorn pulse.asgi:application --host 0.0.0.0 --port 8000 \
        --workers 8 --loop uvloop --ws websockets
```

> **`runserver` is not on this list.** Django's dev server is WSGI-first and
> single-threaded; it cannot hold many concurrent sockets. Use an ASGI server even
> in development.

---

## The sync-in-async footgun (know it cold)

Every one of these blocks the event loop and stalls the whole worker:

| Blocking call | Async-safe replacement |
|---------------|------------------------|
| `Model.objects.get(...)` / `.create()` | `database_sync_to_async(...)` or `await Model.objects.aget(...)` |
| `requests.get(url)` | `await httpx.AsyncClient().get(url)` |
| `time.sleep(1)` | `await asyncio.sleep(1)` |
| `redis.Redis().get(k)` (sync client) | `await redis.asyncio.Redis().get(k)` |
| a CPU-bound loop (JSON of a huge payload, hashing) | `await loop.run_in_executor(pool, fn)` — or move it off the hot path |
| `open(f).read()` on a big file | `await sync_to_async(...)`, or aiofiles |

The tell in production: **p50 stays fine, p99 explodes, and it gets worse with
connection count** — because one blocked coroutine holds up everyone sharing that
worker's loop. Diagnosing it is Module 15; the debug-mode warning to enable is
`PYTHONASYNCIODEBUG=1`, which logs any callback that runs longer than 100 ms.

---

## Manual poking

```bash
# raw connect (authenticated via a ticket query param)
websocat "ws://localhost:8000/ws/room/42/?ticket=$TICKET"

# send a JSON envelope by hand once connected (type it, press enter)
{"type":"send","cid":"c-1","body":"hello"}

# see the handshake only
curl -i -N -H "Connection: Upgrade" -H "Upgrade: websocket" \
     -H "Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==" \
     -H "Sec-WebSocket-Version: 13" \
     http://localhost:8000/ws/room/42/
```
**Expected:** `HTTP/1.1 101 Switching Protocols` (or a `403`/close if the origin
or ticket is rejected — which is the point of Module 21).

Alternatives: `wscat -c ws://localhost:8000/ws/room/42/` (npm), or the browser
console: `new WebSocket("ws://localhost:8000/ws/room/42/")`.

---

## Transport decision table

| Need | Use |
|------|-----|
| Server → client only, HTTP-friendly, auto-reconnect with resume | **SSE** (`Last-Event-ID`) |
| Bidirectional, low latency, high message rate | **WebSocket** (Channels) |
| Bidirectional but must cross a hostile proxy | WebSocket + a long-poll fallback |
| Many independent streams, mobile network churn | **WebTransport** (HTTP/3) — watch, don't bet yet |
| Occasional updates, tiny scale, no infra | **Polling** — genuinely fine, stop apologizing for it |
