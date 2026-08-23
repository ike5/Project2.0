# Lab 04 — A Real Chat Server, and the Wall Behind It

**You'll:** wire `asgi.py` into a `ProtocolTypeRouter`; build `RoomConsumer`
with join, fan-out, presence, heartbeat and a `4401` rejection path; persist
messages without blocking the event loop (and watch what happens when you do);
serve a browser client; measure the real per-connection memory cost against the
pinned **≈45 KB**; fill a channel's mailbox until `ChannelFull` fires; take a
baseline fan-out latency measurement — and then start a **second worker process**
and watch two users in the same room become permanently invisible to each other,
with clean logs, no errors, and no metric that shows it.

⏱️ ~120 min. Work in `django-chat-course/apps/pulse` — the project from
[Module 02](../02-django-fast-track/).

```bash
cd django-chat-course/apps/pulse
source ../../.venv/bin/activate
set -a; source env.dev; set +a
docker compose -p pulse-dev -f ../../infra/compose.dev.yml up -d
pip install --quiet "channels==4.1.*"
```

Reference machine for every number: **8-core / 16 GB, Ubuntu 24.04, Python
3.12, Django 5.1, Channels 4.1, Uvicorn + uvloop**.

---

## Part A — Make `asgi.py` speak WebSocket

Right now `pulse/asgi.py` is `get_asgi_application()` — an ASGI app that handles
`scope["type"] == "http"` and nothing else. Module 02's Uvicorn log said as much
(`ASGI 'lifespan' protocol appears unsupported`). Time to compose.

Add Channels to `INSTALLED_APPS` and configure the layer. In `pulse/settings.py`:

```python
INSTALLED_APPS = [
    "channels",                    # must be present for Channels' checks + commands
    "django.contrib.admin",
    # ... unchanged ...
    "rest_framework",
    "chat",
]

# Module 07 replaces this with channels_redis.core.RedisChannelLayer.
# Read the BACKEND string out loud: "in memory". Of WHICH process?
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer",
        "CONFIG": {
            # Per-channel mailbox depth. The default is 100; we lower it so
            # Part G's slow-consumer failure happens in seconds, not minutes.
            "capacity": env("CHANNEL_CAPACITY", "100", cast=int),
            "expiry": 60,
        },
    }
}
```

`chat/routing.py`:

```python
from django.urls import re_path

from chat import consumers

websocket_urlpatterns = [
    re_path(r"^ws/room/(?P<slug>[\w.-]+)/$", consumers.RoomConsumer.as_asgi()),
]
```

`pulse/asgi.py` — replace the whole file:

```python
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pulse.settings")

# get_asgi_application() must be called BEFORE importing anything that touches
# models, or you get AppRegistryNotReady. This import order is not style; it is
# the single most common Channels startup error.
from django.core.asgi import get_asgi_application          # noqa: E402

django_asgi_app = get_asgi_application()

from channels.auth import AuthMiddlewareStack              # noqa: E402
from channels.routing import ProtocolTypeRouter, URLRouter  # noqa: E402
from channels.security.websocket import AllowedHostsOriginValidator  # noqa: E402

from chat.middleware import DevUserMiddleware              # noqa: E402
from chat.routing import websocket_urlpatterns             # noqa: E402

application = ProtocolTypeRouter({
    # HTTP: everything from Module 02 — DRF, admin, health — unchanged.
    "http": django_asgi_app,

    # WebSocket: a completely separate middleware onion. Django's MIDDLEWARE
    # list does not run here (Module 02, Part I).
    "websocket": AllowedHostsOriginValidator(       # CSWSH defence. Outside. Always.
        DevUserMiddleware(                          # dev-only ?as=<user>; see below
            AuthMiddlewareStack(                    # session cookie -> scope["user"]
                URLRouter(websocket_urlpatterns)
            )
        )
    ),
})
```

Append the dev auth shim to `chat/middleware.py`. **Read the docstring; it is a
deliberate hole**, and closing it is Module 21's job:

```python
from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from django.conf import settings


class DevUserMiddleware:
    """DEVELOPMENT ONLY: authenticate a socket with ?as=<username>.

    A browser's `new WebSocket(url)` cannot set an Authorization header, so
    real auth needs a cookie or a ticket in the query string. Cookies are
    awkward from `websocat`, so this shim lets the lab drive the server from a
    terminal. It is an authentication bypass and it refuses to run outside
    DEBUG. Module 21 replaces it with single-use, signed, Redis-backed tickets
    and then attacks the version that came before.
    """

    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        if settings.DEBUG and scope["type"] == "websocket":
            qs = parse_qs(scope.get("query_string", b"").decode())
            if "as" in qs:
                scope = dict(scope, user=await self._user(qs["as"][0]))
        return await self.inner(scope, receive, send)

    @database_sync_to_async
    def _user(self, username):
        from django.contrib.auth import get_user_model
        return get_user_model().objects.filter(username=username).first()
```

Now the consumer. `chat/consumers.py` — start with the smallest thing that is
actually a chat server:

```python
import time

from channels.generic.websocket import AsyncJsonWebsocketConsumer


class RoomConsumer(AsyncJsonWebsocketConsumer):

    async def connect(self):
        self.slug  = self.scope["url_route"]["kwargs"]["slug"]
        self.group = f"room.{self.slug}"
        self.user  = self.scope.get("user")

        if self.user is None or self.user.is_anonymous:
            # Reject BEFORE accept(): the client's onerror fires, not onopen.
            await self.close(code=4401)
            return

        await self.channel_layer.group_add(self.group, self.channel_name)

        # Only echo a subprotocol the client actually offered. Answering with
        # one it did not offer is a protocol violation and browsers hang up.
        offered = self.scope.get("subprotocols", [])
        await self.accept("pulse.v1" if "pulse.v1" in offered else None)

        await self.send_json({
            "type": "hello",
            "room": self.group,
            "you":  self.user.username,
            "channel": self.channel_name,
        })

    async def receive_json(self, content, **kwargs):
        if content.get("type") == "message.create":
            await self.channel_layer.group_send(self.group, {
                "type":   "chat.message",              # -> chat_message()
                "sender": self.user.username,
                "body":   content.get("body", ""),
                "ts":     int(time.time() * 1000),
            })

    async def chat_message(self, event):
        await self.send_json({
            "type":   "message.new",
            "sender": event["sender"],
            "body":   event["body"],
            "ts":     event["ts"],
        })

    async def disconnect(self, code):
        if hasattr(self, "group"):
            await self.channel_layer.group_discard(self.group, self.channel_name)
```

Run it — **one worker for now**:

```bash
uvicorn pulse.asgi:application --host 127.0.0.1 --port 8000 --loop uvloop
```

**Expected:**
```
INFO:     Started server process [52104]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

✅ The `lifespan` warning from Module 02 is gone. `ProtocolTypeRouter` answers
the lifespan scope (by declining it cleanly) where bare Django did not.

Prove the rejection path first, because auth failures should be boring:

```bash
websocat -v "ws://localhost:8000/ws/room/general/"
```

**Expected — closed with your application code, before any data:**
```
[INFO  websocat::ws_client_peer] Connected to ws://localhost:8000/ws/room/general/
[INFO  websocat] Connection finished: (2, 4401)
```

> Codes `4000–4999` are reserved for applications. Using `4401` (echoing HTTP
> 401) instead of a generic `1008` means your client can branch on it: `4401`
> means "get a new credential and retry", where `1006` means "the network died,
> just reconnect". A client that cannot tell those apart reconnect-storms your
> auth service during an outage.

Now with the dev identity:

```bash
websocat -v "ws://localhost:8000/ws/room/general/?as=u0"
```

**Expected:**
```
[INFO  websocat::ws_client_peer] Connected to ws://localhost:8000/ws/room/general/?as=u0
{"type": "hello", "room": "room.general", "you": "u0", "channel": "specific.a3f1c9e2!QK7pZm"}
```

✅ Note `channel`: `specific.<worker-id>!<connection-id>`. The part before `!`
identifies **this worker process's** receive channel. Remember it — in Part H it
becomes the evidence.

---

## Part B — Groups: two people in a room

Open two terminals:

```bash
# terminal 1
websocat "ws://localhost:8000/ws/room/general/?as=u0"
# terminal 2
websocat "ws://localhost:8000/ws/room/general/?as=u1"
```

In terminal 1, type (one line, then Enter):

```json
{"type":"message.create","body":"hello from u0"}
```

**Expected — in *both* terminals:**
```
{"type": "message.new", "sender": "u0", "body": "hello from u0", "ts": 1735689600123}
```

✅ Including the sender's own terminal. That is deliberate: **the sender is a
member of the group, so it gets its own message back**, which is what lets a
client reconcile its optimistic bubble instead of guessing (Module 05, Part D).

Now a third client in a *different* room:

```bash
websocat "ws://localhost:8000/ws/room/random/?as=u2"
```

Send from `u0` again. **Expected:** `u2` sees nothing. Two dict keys,
`"room.general"` and `"room.random"`, in the same process's channel layer, and
`group_send` only walks one of them.

Look at what actually happened, in the layer:

```bash
curl -s localhost:8000/api/layer-debug/ 2>/dev/null || echo "not built yet"
```

Build it — this endpoint is how you will *see* Part H:

```python
# chat/views.py
from channels.layers import get_channel_layer


def layer_debug(request):
    """Introspect THIS worker's channel layer. There is no other kind."""
    layer = get_channel_layer()
    groups = getattr(layer, "groups", {})
    return JsonResponse({
        "pid":    os.getpid(),
        "backend": type(layer).__module__ + "." + type(layer).__qualname__,
        "groups": {g: sorted(chans) for g, chans in groups.items()},
    })
```
```python
    path("api/layer-debug/", views.layer_debug),
```

```bash
curl -s localhost:8000/api/layer-debug/ | python -m json.tool
```

**Expected:**
```json
{
    "pid": 52104,
    "backend": "channels.layers.InMemoryChannelLayer",
    "groups": {
        "room.general": ["specific.a3f1c9e2!QK7pZm", "specific.a3f1c9e2!Lw9xRt"],
        "room.random":  ["specific.a3f1c9e2!Bn4vHy"]
    }
}
```

✅ **There it is: the entire "distributed" system, printed as a dict.** Two
groups, three channels, one pid. Note every channel name shares the prefix
`specific.a3f1c9e2` — that prefix is this worker's identity, and every channel in
this dict belongs to it. Keep this endpoint; Part H is one `curl` away.

---

## Part C — Persist messages without freezing the server

Chat that forgets is not chat. Add persistence — and do it wrong first, on
purpose, because you need to recognize the symptom.

```python
# chat/consumers.py  — the WRONG version
    async def receive_json(self, content, **kwargs):
        if content.get("type") == "message.create":
            room = Room.objects.get(slug=self.slug)                 # ✗ sync ORM
            Message.objects.create(room=room, sender=self.user,
                                   body=content.get("body", ""))    # ✗ sync ORM
            ...
```

```bash
# restart uvicorn, then from a websocat client:
{"type":"message.create","body":"does this work"}
```

**Expected — in the server log:**
```
ERROR    Exception inside application: You cannot call this from an async
         context - use a thread or sync_to_async.
django.core.exceptions.SynchronousOnlyOperation: You cannot call this from an
async context - use a thread or sync_to_async.
```

✅ Same exception as Module 02's async view, same reason, much higher stakes: in
a view it would have stalled a request; in a consumer it stalls **every socket
this worker holds**.

Now the right version:

```python
# chat/consumers.py — final
import time

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer

from chat.models import Membership, Message, Room


class RoomConsumer(AsyncJsonWebsocketConsumer):

    # ---------------------------------------------------------------- db
    @database_sync_to_async
    def _load_room_if_member(self, slug, user_id):
        """One query. Returns None if the room doesn't exist or you're not in it.

        Authorization at CONNECT time, which is necessary and not sufficient —
        see challenge.md task 2 and Module 21.
        """
        return (Room.objects
                .filter(slug=slug, membership__user_id=user_id)
                .first())

    @database_sync_to_async
    def _save(self, room_id, user_id, body):
        m = Message.objects.create(room_id=room_id, sender_id=user_id, body=body)
        return m.id, int(m.created_at.timestamp() * 1000)

    # ------------------------------------------------------------ lifecycle
    async def connect(self):
        self.slug  = self.scope["url_route"]["kwargs"]["slug"]
        self.group = f"room.{self.slug}"
        self.user  = self.scope.get("user")

        if self.user is None or self.user.is_anonymous:
            await self.close(code=4401)
            return

        self.room = await self._load_room_if_member(self.slug, self.user.id)
        if self.room is None:
            await self.close(code=4403)            # authenticated, not authorized
            return

        await self.channel_layer.group_add(self.group, self.channel_name)
        offered = self.scope.get("subprotocols", [])
        await self.accept("pulse.v1" if "pulse.v1" in offered else None)

        ONLINE[self.group].add(self.user.username)
        await self.send_json({"type": "hello", "room": self.group,
                              "you": self.user.username, "pid": os.getpid(),
                              "channel": self.channel_name,
                              "online": sorted(ONLINE[self.group])})
        await self.channel_layer.group_send(self.group, {
            "type": "presence.update", "user": self.user.username, "state": "join",
            "online": sorted(ONLINE[self.group])})

    async def receive_json(self, content, **kwargs):
        mtype = content.get("type")

        if mtype == "ping":
            # Application heartbeat. Rides in a DATA frame, so proxies that
            # strip WebSocket control frames cannot break it (Module 03, Part E).
            await self.send_json({"type": "pong", "ts": content.get("ts"),
                                  "server_ts": int(time.time() * 1000)})

        elif mtype == "message.create":
            body = (content.get("body") or "").strip()
            if not body:
                await self.send_json({"type": "error", "code": "empty_body"})
                return
            msg_id, ts = await self._save(self.room.id, self.user.id, body)
            await self.channel_layer.group_send(self.group, {
                "type": "chat.message", "id": msg_id,
                "sender": self.user.username, "body": body, "ts": ts})

    # ------------------------------------------------- channel-layer handlers
    async def chat_message(self, event):
        await self.send_json({"type": "message.new", "id": event["id"],
                              "sender": event["sender"], "body": event["body"],
                              "ts": event["ts"]})

    async def presence_update(self, event):
        await self.send_json({"type": "presence.update", "user": event["user"],
                              "state": event["state"], "online": event["online"]})

    async def disconnect(self, code):
        if not hasattr(self, "group"):
            return
        ONLINE[self.group].discard(getattr(self.user, "username", None))
        await self.channel_layer.group_discard(self.group, self.channel_name)
        await self.channel_layer.group_send(self.group, {
            "type": "presence.update", "user": self.user.username, "state": "leave",
            "online": sorted(ONLINE[self.group])})
```

Add the presence registry at module level, with the warning attached:

```python
import os
from collections import defaultdict

# Per-PROCESS presence. Every problem the channel layer has, plus one more:
# a worker killed with SIGKILL never runs disconnect(), so this set is both
# incomplete (other workers' users are missing) and stale (its own users
# never leave). Module 11 rebuilds it as TTL keys in Redis — state that
# expires on its own is state that heals when a process dies badly.
ONLINE: dict[str, set[str]] = defaultdict(set)
```

Restart and test the whole flow:

```bash
websocat "ws://localhost:8000/ws/room/general/?as=u0"
```
```json
{"type":"message.create","body":"persisted?"}
{"type":"ping","ts":1735689600000}
```

**Expected:**
```
{"type": "hello", "room": "room.general", "you": "u0", "pid": 52104, "channel": "specific.a3f1c9e2!QK7pZm", "online": ["u0"]}
{"type": "presence.update", "user": "u0", "state": "join", "online": ["u0"]}
{"type": "message.new", "id": 501, "sender": "u0", "body": "persisted?", "ts": 1735689600241}
{"type": "pong", "ts": 1735689600000, "server_ts": 1735689600389}
```

```bash
curl -s "localhost:8000/api/rooms/general/history/?limit=1" | python -m json.tool
```
**Expected:** the message you just sent, from Postgres.

Try a room you are not a member of:

```bash
websocat -v "ws://localhost:8000/ws/room/random/?as=u0" 2>&1 | tail -1
```
**Expected:** `Connection finished: (2, 4403)` — `u0` is a member of `general`
only. Two codes, two meanings: `4401` "who are you", `4403` "not for you".

### Now feel the cardinal sin

Temporarily make `_save` block the loop instead of hopping to the threadpool:

```python
    # DELIBERATELY WRONG — for one measurement only
    async def _save(self, room_id, user_id, body):        # note: async, no decorator
        time.sleep(0.25)                                   # stands in for a slow query
        return 0, int(time.time() * 1000)
```

Open one client that pings every second and one that sends messages:

```bash
# terminal 1 — the victim: an idle user who just wants heartbeats
websocat "ws://localhost:8000/ws/room/general/?as=u1" &
while true; do echo '{"type":"ping","ts":'$(date +%s%3N)'}'; sleep 1; done \
  | websocat "ws://localhost:8000/ws/room/general/?as=u1" \
  | python -c "
import sys, json, time
for line in sys.stdin:
    e = json.loads(line)
    if e['type'] == 'pong':
        print(f\"rtt {int(time.time()*1000) - e['ts']} ms\")
"
```
```bash
# terminal 2 — the offender: 20 messages as fast as possible
python - <<'EOF'
import asyncio, json, websockets
async def main():
    async with websockets.connect("ws://localhost:8000/ws/room/general/?as=u0") as ws:
        for i in range(20):
            await ws.send(json.dumps({"type": "message.create", "body": f"m{i}"}))
        await asyncio.sleep(1)
asyncio.run(main())
EOF
```

**Expected — the innocent client's heartbeat RTT during the burst:**
```
rtt 1 ms
rtt 2 ms
rtt 1 ms
rtt 2,731 ms          <-- 20 x 0.25s of blocking, serialized on the one loop
rtt 2,248 ms
rtt 1 ms
```

✅ **`u1` did nothing wrong and its latency went to 2.7 seconds.** One
connection's blocking call froze the entire worker, exactly as Module 01's
`time.sleep` starved the heartbeat coroutine (108 ms → 20,041 ms). This is why
`database_sync_to_async` exists and why Module 15 spends a whole module putting
a number on it. **Restore the `@database_sync_to_async` version before
continuing.**

---

## Part D — A browser client

Terminal clients prove the protocol; a browser proves the handshake, the origin
check, and presence. Create `chat/templates/chat/room.html`:

```html
<!doctype html>
<meta charset="utf-8">
<title>Pulse</title>
<style>
  body { font: 14px/1.5 system-ui; margin: 2rem; max-width: 42rem; }
  #log { border: 1px solid #ccc; height: 20rem; overflow-y: auto; padding: .5rem; }
  .sys { color: #888; } .me { font-weight: 600; }
</style>
<h3>#<span id="room"></span> — <span id="who"></span> <small id="pid"></small></h3>
<div id="log"></div>
<input id="msg" style="width: 80%" placeholder="say something" autofocus>
<p class="sys">online: <span id="online"></span></p>
<script>
const slug = location.pathname.split("/").filter(Boolean).pop();
const who  = new URLSearchParams(location.search).get("as") || "u0";
document.getElementById("room").textContent = slug;
document.getElementById("who").textContent  = who;

const proto = location.protocol === "https:" ? "wss" : "ws";
const ws = new WebSocket(`${proto}://${location.host}/ws/room/${slug}/?as=${who}`,
                         ["pulse.v1"]);          // offer the subprotocol

const log = (html, cls="") => {
  const d = document.createElement("div");
  d.className = cls; d.innerHTML = html;
  document.getElementById("log").append(d);
  d.scrollIntoView();
};

ws.onopen  = () => log("connected (subprotocol: " + (ws.protocol || "none") + ")", "sys");
ws.onerror = () => log("handshake failed — check the close code in DevTools", "sys");
ws.onclose = (e) => log(`closed: code=${e.code} reason=${e.reason || "-"}`, "sys");

ws.onmessage = (e) => {
  const m = JSON.parse(e.data);
  switch (m.type) {
    case "hello":
      document.getElementById("pid").textContent = "worker pid " + m.pid;
      document.getElementById("online").textContent = m.online.join(", ");
      break;
    case "message.new":
      log(`<b>${m.sender}</b>: ${m.body}`, m.sender === who ? "me" : "");
      break;
    case "presence.update":
      document.getElementById("online").textContent = m.online.join(", ");
      log(`${m.user} ${m.state}ed`, "sys");
      break;
    case "pong": break;
    default:  break;     // forward compatibility: ignore unknown types (Module 05)
  }
};

document.getElementById("msg").addEventListener("keydown", (e) => {
  if (e.key === "Enter" && e.target.value.trim()) {
    ws.send(JSON.stringify({type: "message.create", body: e.target.value}));
    e.target.value = "";
  }
});
setInterval(() => ws.readyState === 1 &&
  ws.send(JSON.stringify({type: "ping", ts: Date.now()})), 10000);
</script>
```

Serve it:

```python
# chat/views.py
from django.shortcuts import render
def room_page(request, slug):
    return render(request, "chat/room.html", {"slug": slug})
```
```python
    path("room/<slug:slug>/", views.room_page),
```
Add `"DIRS": [BASE_DIR / "chat" / "templates"]` if your `TEMPLATES` setting does
not already have `APP_DIRS: True` (it does by default).

Open two browser tabs:
`http://localhost:8000/room/general/?as=u0` and `...?as=u1`.

**Expected:** each tab shows `connected (subprotocol: pulse.v1)`, both show
`online: u0, u1`, messages appear in both instantly, and closing one tab makes
the other log `u1 leaved` and update the online list.

✅ **The subprotocol echoed back as `pulse.v1`** because the browser offered it
in `Sec-WebSocket-Protocol` and the consumer accepted only what was offered.
Change the array in `new WebSocket(...)` to `["pulse.v2"]` and reload:
`ws.protocol` is empty and everything still works — which is the protocol
negotiation hook Module 05 uses for versioning.

---

## Part E — What a connection actually costs

The course pins **≈45 KB of application memory per idle WebSocket connection**.
Verify it. Create `code/wsprobe.py` (the full listing is in
[`code/wsprobe.py`](./code/wsprobe.py)) and use its `hold` mode:

```bash
# restart uvicorn cleanly first, one worker
uvicorn pulse.asgi:application --port 8000 --loop uvloop &
sleep 3
PID=$(pgrep -f 'uvicorn pulse.asgi' | head -1)
grep VmRSS /proc/$PID/status
```

**Expected — the baseline: Django + DRF + Channels loaded, zero connections:**
```
VmRSS:	   96412 kB
```

```bash
python code/wsprobe.py hold --n 5000 --room general --user u0 &
sleep 25
grep VmRSS /proc/$PID/status
curl -s localhost:8000/api/layer-debug/ | python -c "
import sys,json; d=json.load(sys.stdin)
print('channels in room.general:', len(d['groups']['room.general']))"
```

**Expected:**
```
VmRSS:	  326008 kB
channels in room.general: 5000
```

Do the arithmetic:

```
(326008 - 96412) KB / 5000 connections  =  45.9 KB per connection
```

✅ **45.9 KB, against a pinned ≈45 KB.** Where it goes, roughly:

| Component | ≈ bytes |
|-----------|--------|
| `RoomConsumer` instance + its `__dict__` (`self.room`, `self.user`, …) | 6,000 |
| The asyncio Task driving it, plus its frames | 4,500 |
| `websockets` protocol object + per-connection buffers | 12,000 |
| ASGI `scope` dict (headers as a list of byte tuples!) | 8,000 |
| Channel-layer bookkeeping: `groups` entry + an `asyncio.Queue` | 5,500 |
| Python object headers, dict overallocation, allocator slack | 9,900 |

Note what is *not* on that list: **a thread stack.** Module 01's OS-thread
experiment died at ~32,000 threads at roughly 8 MB of virtual address space
each; here 5,000 connections live on one thread. And note that `scope` is
expensive — every request header, retained for the whole connection lifetime.
Module 06's challenge trims it.

At 45.9 KB, the pinned **≈40,000 connections per worker process** costs
~1.8 GB of RSS, which is the right order for a worker given a share of 16 GB.
Eight workers ⇒ ~200k connections per node *by memory* — but CPU-bound fan-out
binds first, which Module 06 measures.

Stop the probe (`kill %1`) and confirm the layer drains:

```bash
curl -s localhost:8000/api/layer-debug/ | python -c "
import sys,json; print(len(json.load(sys.stdin)['groups'].get('room.general', [])))"
```
**Expected:** `0` — `disconnect()` ran and `group_discard` cleaned up. If you
ever see a number that never returns to zero, you have a `group_discard` leak,
and on the Redis layer (Module 07) it silently ages out after `group_expiry`
seconds instead of erroring, which is worse.

---

## Part F — Baseline fan-out latency

One sender, 200 receivers in one room, 10 messages/second, 60 seconds. This is a
sighting shot; Module 06 does it properly with an open-model generator.

```bash
python code/wsprobe.py fanout --room general --receivers 200 --rate 10 --seconds 60
```

**Expected:**
```
receivers=200  sent=600  received=120,000  (amplification 200x)
end-to-end latency (sender send() -> receiver recv()):
  p50    1.8 ms
  p95    3.9 ms
  p99    5.4 ms
  p99.9 11.2 ms
server worker CPU: 34% of one core
```

✅ Two things to take from this. First, **amplification is the number that
matters**: 600 inbound messages became 120,000 outbound. Module 06 states the
rule as `inbound × room_size = outbound`, and it is why "can it handle 1,000
messages a second" is an unanswerable question.

Second, **34% of one core** — for 200 receivers at 10 msg/s. Not 34% of the
machine. One core, because one worker. Scale that linearly and you reach 100% at
about 5,900 outbound msg/s from this unoptimized code path; Module 06 tunes it
and finds the real knee at **≈150,000 outbound msg/s**, with a safe operating
point around **100,000**.

Where does the CPU go? `deepcopy` of the event dict per recipient, a JSON encode
per recipient, and a socket write per recipient — 200 of each, on the loop, for
one inbound message.

---

## Part G — A slow consumer takes down the room

Connect a client that completes the handshake and then **never reads its
socket**:

```bash
python code/wsprobe.py deadbeat --room general --user u1 &
sleep 2
python code/wsprobe.py blast --room general --user u0 --n 2000
```

**Expected — after a few hundred messages, in the Uvicorn log:**
```
ERROR    Exception inside application: specific.a3f1c9e2!Lw9xRt
channels.exceptions.ChannelFull: specific.a3f1c9e2!Lw9xRt
  File ".../channels/layers.py", line 235, in group_send
    raise ChannelFull(channel)
```

And on a *third*, perfectly healthy client in the same room:

```bash
websocat "ws://localhost:8000/ws/room/general/?as=u2"
```
**Expected:** messages stop arriving for it too, mid-stream.

✅ **Read that carefully: one client that stopped reading broke fan-out for the
whole room.** The chain is:

```
deadbeat stops reading
   → its TCP receive window closes
   → the server's transport write buffer hits its high-water mark
   → the consumer's send_json() stops returning promptly
   → the consumer stops draining its channel-layer queue
   → the queue reaches capacity=100
   → the NEXT group_send raises ChannelFull  ← for the entire group
```

The fix is the same shape as the JVM twin's `setSendBufferSizeLimit`: **choose
to lose the bad connection rather than the room.**

```python
# chat/consumers.py
from channels.exceptions import ChannelFull
from prometheus_client import Counter          # pip install prometheus-client

SLOW_CONSUMER_DROPS = Counter("chat_slow_consumer_drops_total",
                              "connections closed for not draining their mailbox")


async def _fanout(self, event):
    try:
        await self.channel_layer.group_send(self.group, event)
    except ChannelFull as e:
        # On the in-memory layer the exception names the wedged channel.
        SLOW_CONSUMER_DROPS.inc()
        await self.channel_layer.send(str(e), {"type": "chat.overflow"})
        raise


async def chat_overflow(self, event):
    await self.close(code=4008)          # "you are too slow"; the client reconnects
```

Re-run the blast with the fix in place.

**Expected:** the deadbeat is closed with `4008`, `u2` keeps receiving, and the
room is healthy within ~200 ms.

> **Is disconnecting the user hostile?** No — it is the only option that
> preserves the other 199 people, and the client's reconnect path (Module 05's
> `resume`, Module 17's backoff) means the user sees a two-second blip rather
> than a broken room. The alternative, an unbounded per-connection buffer, means
> one phone in a tunnel grows your worker's RSS until the OOM killer picks a
> process. **A visible, attributable failure beats invisible degradation** — the
> same argument `infra/compose.dev.yml` makes for Redis's `noeviction`.

---

## Part H — The wall

Everything above worked. Now use your second CPU core.

```bash
kill %1 2>/dev/null
uvicorn pulse.asgi:application --host 127.0.0.1 --port 8000 --loop uvloop --workers 2
```

**Expected:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started parent process [53001]
INFO:     Started server process [53002]
INFO:     Started server process [53003]
```

Two worker pids. Now connect two users to **the same room** and check which
worker each landed on:

```bash
# terminal 1
websocat "ws://localhost:8000/ws/room/general/?as=u0"
# terminal 2
websocat "ws://localhost:8000/ws/room/general/?as=u1"
```

**Expected — look at the `pid` field:**
```
terminal 1: {"type": "hello", "room": "room.general", "you": "u0", "pid": 53002, "channel": "specific.7c1a09bb!QK7pZm", "online": ["u0"]}
terminal 2: {"type": "hello", "room": "room.general", "you": "u1", "pid": 53003, "channel": "specific.e4f7233d!Lw9xRt", "online": ["u1"]}
```

> If both show the same pid, close one and reconnect — the kernel balances
> `SO_REUSEPORT` accepts and you need one on each. Two or three tries is normal.

Two things are already wrong and you can see both in that output:

- **The `online` lists disagree.** `u0` sees `["u0"]`, `u1` sees `["u1"]`. Each
  worker's `ONLINE` dict knows only its own connections.
- **The channel prefixes differ** — `specific.7c1a09bb` vs `specific.e4f7233d`.
  Those are two different processes' channel-layer identities.

Now send from terminal 1:

```json
{"type":"message.create","body":"can you hear me"}
```

**Expected:**
```
terminal 1: {"type": "message.new", "id": 502, "sender": "u0", "body": "can you hear me", "ts": ...}
terminal 2: (nothing. ever.)
```

✅ **This is the wall.** Now collect the evidence, because "it doesn't work" is
not an engineering finding.

**Evidence 1 — the message was persisted.** It is not a database problem:

```bash
curl -s "localhost:8000/api/rooms/general/history/?limit=1" | python -m json.tool
```
**Expected:** `"body": "can you hear me"`. The write worked. Only the *delivery*
failed.

**Evidence 2 — no error, anywhere.** Check the Uvicorn log.
**Expected:** nothing. `group_send` returned successfully. There is no exception
to catch, no log line to alert on, and no metric that would show this. **A
counter of "messages fanned out" would read 1 on worker 53002 and be correct.**

**Evidence 3 — two channel layers, each half-right.** Hit the debug endpoint
repeatedly until you have seen both workers answer:

```bash
for i in $(seq 1 8); do curl -s localhost:8000/api/layer-debug/; echo; done \
  | python -c "
import sys, json
seen = {}
for line in sys.stdin:
    d = json.loads(line)
    seen[d['pid']] = d['groups']
for pid, groups in sorted(seen.items()):
    print(pid, json.dumps(groups))
"
```

**Expected:**
```
53002 {"room.general": ["specific.7c1a09bb!QK7pZm"]}
53003 {"room.general": ["specific.e4f7233d!Lw9xRt"]}
```

✅ **Two dictionaries. The same key. One entry each. Nothing joins them.**

`group_send("room.general", …)` on worker 53002 iterates 53002's dict, finds one
channel, delivers to it, and returns. Worker 53003's dict is in a different
process's address space. There is no shared memory between OS processes, so
there is no code that *could* walk both — and Channels does not pretend
otherwise: the backend is called `InMemoryChannelLayer`, and the memory in
question is one process's.

### Prove the ceiling you are choosing between

```bash
# A. correctness, one core
kill %1; uvicorn pulse.asgi:application --port 8000 --loop uvloop --workers 1 &
sleep 3
python code/wsprobe.py crosstalk --room general --pairs 50
```
**Expected:**
```
50/50 message pairs delivered across connections  (100.0%)
```

```bash
# B. two cores, broken
kill %1; uvicorn pulse.asgi:application --port 8000 --loop uvloop --workers 2 &
sleep 3
python code/wsprobe.py crosstalk --room general --pairs 50
```
**Expected:**
```
26/50 message pairs delivered across connections  (52.0%)
```

✅ **52%, not 0%** — and *that* is the cruelest part. With two workers, half the
pairs happen to land on the same process and work perfectly. The bug is
**intermittent, user-specific, and unreproducible on your laptop** where you run
one worker. Run it with `--workers 4`:

```bash
kill %1; uvicorn pulse.asgi:application --port 8000 --loop uvloop --workers 4 &
sleep 3
python code/wsprobe.py crosstalk --room general --pairs 50
```
**Expected:**
```
13/50 message pairs delivered across connections  (26.0%)
```

Roughly `1/workers`. Add cores, deliver less. **In Python, scaling up a single
box makes chat worse until the channel layer crosses processes.**

### What you cannot do about it

| Attempt | Why it fails |
|---------|--------------|
| `--workers 1` | Correct. Caps the node at one core: ≈150,000 outbound msg/s (Module 06). |
| Threads instead of processes | The GIL serializes Python bytecode. Eight threads ≈ one core of JSON encoding, plus contention. |
| Route each room to a fixed worker | Works — until a user is in twelve rooms, or one room gets hot. You traded fan-out for placement. (Module 14 revisits this as sharding, where it earns its keep.) |
| `multiprocessing.Manager` / shared memory | You have now written a channel layer: serialization, liveness, cleanup, backpressure — badly, and only for one machine. |
| A second machine | Strictly worse. Same problem, plus a network. |

**Redis is the answer, and it is needed to use your second CPU core, not your
second server.** That is the sentence that separates this course from its JVM
twin, where one JVM uses eight cores and the same wall only appears when you
deploy a second instance.

[`07-scale-out-redis-channel-layer`](../07-scale-out-redis-channel-layer/) swaps
one settings dict for `channels_redis.core.RedisChannelLayer`, re-runs
`crosstalk` at 100%, measures the cost (**≈+4 ms p50**), and then pauses Redis
under load and counts what the Pub/Sub layer loses (**≈15%**).

Leave the server on `--workers 1` for Modules 05 and 06.

---

## What you measured

Record these in `apps/pulse/results-04.md`:

| Measurement | Reference | Yours |
|-------------|-----------|-------|
| Anonymous connect | closed `4401` before accept | |
| Non-member connect | closed `4403` | |
| Baseline worker RSS (0 connections) | 96,412 kB | |
| RSS at 5,000 connections | 326,008 kB | |
| **Per-connection cost** | **45.9 KB** | |
| Fan-out: 200 receivers, 10 msg/s | p50 1.8 / p99 5.4 ms, 34% of one core | |
| Amplification, 200-member room | 200× | |
| Blocking `_save` (250 ms) | innocent client RTT 1 ms → 2,731 ms | |
| Slow consumer | `ChannelFull` at ~100 queued, room-wide | |
| Cross-worker delivery, `--workers 1` | **50/50 (100%)** | |
| Cross-worker delivery, `--workers 2` | **26/50 (52%)** | |
| Cross-worker delivery, `--workers 4` | **13/50 (26%)** | |

---

## What you built

```
apps/pulse/chat/
├── consumers.py        ← RoomConsumer: auth, groups, persistence, presence, heartbeat
├── routing.py          ← ws/room/<slug>/
├── middleware.py       ← DevUserMiddleware (a deliberate hole; Module 21 closes it)
├── templates/chat/room.html   ← a browser client that reconciles presence
└── views.py            ← + layer_debug, room_page
apps/pulse/pulse/asgi.py       ← ProtocolTypeRouter(http | websocket)
```

And you established the facts Phase 2 exists to fix:

- **A consumer is an ASGI app, one object per connection**, costing a measured
  **45.9 KB** — no thread stack, which is why 5,000 fit where 5,000 threads
  would not.
- **The channel layer is the only distributed primitive**, and the in-memory one
  is two dicts in one process's heap. You printed them.
- **Blocking the loop in a consumer punishes everyone else**: an innocent
  client's heartbeat went from 1 ms to 2.7 seconds because a *different*
  connection made a synchronous call.
- **One slow consumer can wedge a whole room** via `ChannelFull`, and the
  correct response is to disconnect it.
- **Two worker processes cannot see each other.** 100% → 52% → 26% delivery as
  you add cores, with no errors, no logs, and no metric that shows it. In
  Python, the channel layer must cross *processes* before it ever needs to
  cross *machines*.

Now do [`challenge.md`](./challenge.md).

Then: [Module 05 — Protocol & Domain Design](../05-protocol-and-domain-design/),
which replaces this module's two-field envelope with one you could actually
ship — client-generated ids, sequence numbers, acks, and versioning — before
[Module 06](../06-load-testing-harness/) breaks the single node on purpose and
records the number.
