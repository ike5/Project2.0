# Lab 03 — Speak the Protocols by Hand

**You'll:** perform a WebSocket handshake with `curl`, decode raw frames byte by
byte with a Python script, build all four transports in the Pulse project — a
polling view, an async long-poll view, an async SSE view with `Last-Event-ID`
resume, and a raw WebSocket via Channels — prove WSGI can't hold them open,
measure real bytes-on-the-wire, and watch an nginx timeout silently kill a
connection.

⏱️ ~100 min. Work in `django-chat-course/apps/pulse`.

> **Setup for this lab.** You need a minimal ASGI Django project. If you did
> Module 02 you already have `apps/pulse` with `pulse/asgi.py` and a `chat` app;
> if not, the scaffold below is enough to run everything here. From
> `apps/pulse`:
>
> ```bash
> python -m venv .venv && source .venv/bin/activate
> pip install "django==5.1.*" "channels==4.1.*" "uvicorn[standard]==0.30.*" \
>             "daphne==4.1.*" "gunicorn==22.*"
> django-admin startproject pulse . 2>/dev/null || true
> python manage.py startapp chat 2>/dev/null || true
> ```
>
> `uvicorn[standard]` pulls in **uvloop** and the **websockets** library — the
> two pieces that make async I/O and WebSocket framing fast. We compare uvloop to
> the stdlib loop in Module 01; here we just use it.

Add the transport demo app to `INSTALLED_APPS` and to the ASGI application as you
go — each Part says exactly what to wire.

---

## Part A — The handshake, by hand

You don't have a `/ws` endpoint yet — that's Part C — so first add a bare
Channels echo consumer so this lab has something to talk to.

`chat/consumers.py`:

```python
from channels.generic.websocket import AsyncWebsocketConsumer

class EchoConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        await self.send(text_data=f"welcome {self.channel_name[-8:]}")

    async def receive(self, text_data=None, bytes_data=None):
        await self.send(text_data=f"echo: {text_data}")
```

`pulse/asgi.py`:

```python
import os
from django.core.asgi import get_asgi_application
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pulse.settings")
django_asgi = get_asgi_application()            # HTTP path (views) go here

from channels.routing import ProtocolTypeRouter, URLRouter
from django.urls import path
from chat.consumers import EchoConsumer

application = ProtocolTypeRouter({
    "http": django_asgi,
    "websocket": URLRouter([
        path("ws-raw", EchoConsumer.as_asgi()),
    ]),
})
```

> `setAllowedOrigins("*")` has no analog here yet — Channels does **not** check
> `Origin` by default, which is itself a Cross-Site WebSocket Hijacking hole.
> [`21-security-and-abuse-at-scale`](../21-security-and-abuse-at-scale/) adds
> `AllowedHostsOriginValidator`. For this lab, wide-open is fine and deliberate.

Run it under Uvicorn (ASGI — **not** `runserver` for the socket parts):

```bash
uvicorn pulse.asgi:application --host 0.0.0.0 --port 8000
```

Now do the handshake by hand:

```bash
curl -i -N \
  -H "Connection: Upgrade" \
  -H "Upgrade: websocket" \
  -H "Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==" \
  -H "Sec-WebSocket-Version: 13" \
  http://localhost:8000/ws-raw
```

**Expected:**
```
HTTP/1.1 101 Switching Protocols
Upgrade: websocket
Connection: Upgrade
Sec-WebSocket-Accept: s3pPLMBiTxaQ9kYGzzhZRbK+xOo=
```

✅ Verify that `Sec-WebSocket-Accept` yourself — this is the whole handshake
proof, and computing it once makes it permanently unmysterious:

```bash
printf 'dGhlIHNhbXBsZSBub25jZQ==258EAFA5-E914-47DA-95CA-C5AB0DC85B11' \
  | openssl dgst -binary -sha1 | base64
```
**Expected:**
```
s3pPLMBiTxaQ9kYGzzhZRbK+xOo=
```

Identical. The `websockets` library inside Uvicorn computed exactly this. Now
break it — change one character of the key and watch the accept value change
completely:

```bash
printf 'XGhlIHNhbXBsZSBub25jZQ==258EAFA5-E914-47DA-95CA-C5AB0DC85B11' \
  | openssl dgst -binary -sha1 | base64
```
**Expected:** a totally different string. A browser receiving that (when it sent
the original key) would abort the connection — the accept value is how it knows
it's talking to a real WebSocket server and not a confused cache.

---

## Part B — Decode raw frames

Capture the actual bytes. In one terminal:

```bash
websocat -v ws://localhost:8000/ws-raw
```
Type `hi` and press Enter.

**Expected:**
```
[INFO  websocat::ws_client_peer] Connected to ws://localhost:8000/ws-raw
welcome b3a91c2f
hi
echo: hi
```

Now see the bytes on the wire with `tcpdump` (or Wireshark if you prefer a GUI):

```bash
sudo tcpdump -i lo -s0 -X 'tcp port 8000' -c 40 2>/dev/null | grep -A3 -B1 'echo'
```

**Expected** (excerpt — the server→client frame for `echo: hi`):
```
0x0030:  8108 6563 686f 3a20 6869
         │ │  └──────────────────┴── payload: "echo: hi"  (8 bytes)
         │ └── 0x08 = MASK 0, length 8
         └── 0x81 = FIN 1, opcode 0x1 (text)
```

Decode it yourself with the script. It's in `code/decode_frame.py` (create it
from the listing below if it isn't there):

```python
#!/usr/bin/env python3
"""Decode a WebSocket frame given as hex. Usage: decode_frame.py 8108656368..."""
import sys

OPCODES = {0x0: "continuation", 0x1: "text", 0x2: "binary",
           0x8: "close", 0x9: "ping", 0xA: "pong"}

data = bytes.fromhex("".join(sys.argv[1:]).replace(" ", ""))
b0, b1 = data[0], data[1]

fin    = (b0 & 0b10000000) >> 7
rsv    = (b0 & 0b01110000) >> 4
opcode =  b0 & 0b00001111
masked = (b1 & 0b10000000) >> 7
length =  b1 & 0b01111111

i = 2
if length == 126:
    length = int.from_bytes(data[2:4], "big"); i = 4
elif length == 127:
    length = int.from_bytes(data[2:10], "big"); i = 10

key = b""
if masked:
    key = data[i:i+4]; i += 4

payload = data[i:i+length]
if masked:
    payload = bytes(b ^ key[j % 4] for j, b in enumerate(payload))

print(f"FIN      : {fin}")
print(f"RSV      : {rsv:03b}   (nonzero means an extension like permessage-deflate)")
print(f"opcode   : 0x{opcode:x} ({OPCODES.get(opcode, '?')})")
print(f"MASK     : {masked}" + (f"  key={key.hex()}" if masked else ""))
print(f"length   : {length}")
print(f"overhead : {i} bytes for {length} bytes of payload")
print(f"payload  : {payload!r}")
```

```bash
chmod +x code/decode_frame.py
./code/decode_frame.py 8108 6563 686f 3a20 6869
```

**Expected:**
```
FIN      : 1
RSV      : 000   (nonzero means an extension like permessage-deflate)
opcode   : 0x1 (text)
MASK     : 0
length   : 8
overhead : 2 bytes for 8 bytes of payload
payload  : b'echo: hi'
```

Now a **masked client frame** — this is what your `hi` looked like going *up*:

```bash
./code/decode_frame.py 8182 37fa 213d 5f93
```

**Expected:**
```
FIN      : 1
opcode   : 0x1 (text)
MASK     : 1  key=37fa213d
length   : 2
overhead : 6 bytes for 2 bytes of payload
payload  : b'hi'
```

✅ **6 bytes of overhead to send 2 bytes.** Note the asymmetry: server→client
costs 2 bytes of overhead, client→server costs 6 (the extra 4 are the mask key).
For chat that's the right way round — **fan-out is the direction that scales**,
and it's the cheap one. This asymmetry is exactly why Pulse's server→client path
can hit ~150,000 messages/second on one node
([`06-load-testing-harness`](../06-load-testing-harness/)) while the client→server
path never has to.

Try the length encodings:
```bash
./code/decode_frame.py 817e 0100 $(python3 -c "print('41'*256)")   # len 126 -> 16-bit
```
**Expected:**
```
length   : 256
overhead : 4 bytes for 256 bytes of payload
```

The `0x7e` (126) in the length field is a *sentinel* meaning "read the next 2
bytes as the real length"; `0x7f` (127) means "read the next 8 bytes." The
challenge asks you to explain why this beats always using 64 bits.

---

## Part C — Build all four transports

Add one Django app exposing the same "give me messages" capability four ways, so
you can measure them against each other. The first three are plain HTTP views;
the fourth is the Channels consumer from Part A, upgraded.

Because three of the four **hold a connection open**, they must be `async def`
and run under ASGI. We'll prove that in Part C-bis.

`chat/transport.py` — a tiny in-process message log and the three HTTP transports:

```python
import asyncio, json, time
from django.http import JsonResponse, StreamingHttpResponse, HttpResponse

# --- shared in-process state (single worker only; that's the point of Module 04) ---
_LOG = []                                  # list[dict(id, body, ts)]
_SEQ = 0
_WAITERS: set[asyncio.Queue] = set()       # long-poll + SSE subscribers

def _publish(body: str) -> dict:
    global _SEQ
    _SEQ += 1
    msg = {"id": _SEQ, "body": body.strip(), "ts": int(time.time() * 1000)}
    _LOG.append(msg)
    for q in list(_WAITERS):               # wake everyone waiting
        q.put_nowait(msg)
    return msg

async def publish(request):
    """POST a body to inject a message: curl -X POST .../publish -d 'hello'"""
    body = (request.body or b"").decode()
    return JsonResponse(_publish(body))

# ---- 1. POLLING (works on WSGI too — holds nothing open) ----
def poll(request):
    since = int(request.GET.get("since", 0))
    return JsonResponse([m for m in _LOG if m["id"] > since], safe=False)

# ---- 2. LONG POLLING (async: parks a coroutine, not a thread) ----
async def longpoll(request):
    since = int(request.GET.get("since", 0))
    newer = [m for m in _LOG if m["id"] > since]
    if newer:
        return JsonResponse(newer, safe=False)         # data already there

    q: asyncio.Queue = asyncio.Queue()
    _WAITERS.add(q)
    try:
        msg = await asyncio.wait_for(q.get(), timeout=30)   # the whole trick
        return JsonResponse([msg], safe=False)
    except asyncio.TimeoutError:
        return JsonResponse([], safe=False)                 # long-poll timeout
    finally:
        _WAITERS.discard(q)                                 # never leak the queue

# ---- 3. SSE (async generator + StreamingHttpResponse, with Last-Event-ID) ----
async def sse(request):
    last_id = int(request.headers.get("Last-Event-ID", request.GET.get("lastId", 0)))

    async def event_stream():
        # Replay anything missed FIRST — this is the resume cursor, built in.
        for m in list(_LOG):
            if m["id"] > last_id:
                yield _sse_event(m)

        q: asyncio.Queue = asyncio.Queue()
        _WAITERS.add(q)
        try:
            while True:
                try:
                    m = await asyncio.wait_for(q.get(), timeout=15)
                    yield _sse_event(m)
                except asyncio.TimeoutError:
                    yield ": ping\n\n"                  # keep-alive comment
        finally:
            _WAITERS.discard(q)

    resp = StreamingHttpResponse(event_stream(),
                                 content_type="text/event-stream")
    resp["Cache-Control"] = "no-cache"
    resp["X-Accel-Buffering"] = "no"       # tell nginx: DO NOT buffer this
    return resp

def _sse_event(m: dict) -> str:
    return (f"id: {m['id']}\n"
            f"event: message\n"
            f"data: {json.dumps(m)}\n\n")
```

Wire the HTTP routes. `pulse/urls.py`:

```python
from django.urls import path
from chat import transport

urlpatterns = [
    path("transport/publish",  transport.publish),
    path("transport/poll",     transport.poll),
    path("transport/longpoll", transport.longpoll),
    path("transport/sse",      transport.sse),
]
```

And upgrade the Part A consumer so `/ws-raw` also receives published messages —
add a shared broadcast. `chat/consumers.py`:

```python
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from chat import transport

class EchoConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        await self.send(text_data=f"welcome {self.channel_name[-8:]}")
        self._q = asyncio.Queue()
        transport._WAITERS.add(self._q)
        self._task = asyncio.create_task(self._pump())

    async def _pump(self):
        while True:
            m = await self._q.get()
            await self.send(text_data=m["body"])

    async def receive(self, text_data=None, bytes_data=None):
        await self.send(text_data=f"echo: {text_data}")

    async def disconnect(self, code):
        transport._WAITERS.discard(self._q)
        self._task.cancel()
```

> This shared `_WAITERS` set is a deliberately crude in-process pub/sub — it lives
> in one Python process and dies with it. That limitation is not a bug to fix
> here; it *is* Module 04's entire lesson, arriving early. Notice it.

Restart Uvicorn and try each:

```bash
# polling
curl -s "localhost:8000/transport/poll?since=0" | jq
curl -s -X POST localhost:8000/transport/publish -d 'first'
curl -s "localhost:8000/transport/poll?since=0" | jq
```

**Expected:**
```json
[]
{"id":1,"body":"first","ts":1735689600123}
[{"id":1,"body":"first","ts":1735689600123}]
```

```bash
# long polling — this BLOCKS until you publish from another terminal
curl -s "localhost:8000/transport/longpoll?since=1" &
sleep 1
curl -s -X POST localhost:8000/transport/publish -d 'second'
wait
```

**Expected** — the long poll returns the instant you publish, not on a timer:
```json
[{"id":2,"body":"second","ts":1735689612456}]
```

```bash
# SSE — leave this running
curl -N -H 'Accept: text/event-stream' localhost:8000/transport/sse
```
In another terminal:
```bash
curl -s -X POST localhost:8000/transport/publish -d 'third'
```

**Expected in the SSE terminal:**
```
id: 3
event: message
data: {"id": 3, "body": "third", "ts": 1735689620789}

```
…and, if you wait 15 seconds with no traffic, a keep-alive:
```
: ping

```

✅ Now test **resume**. Kill the `curl -N` with Ctrl-C, publish two more
messages, then reconnect with a `Last-Event-ID`:

```bash
curl -s -X POST localhost:8000/transport/publish -d 'fourth'
curl -s -X POST localhost:8000/transport/publish -d 'fifth'
curl -N -H 'Accept: text/event-stream' -H 'Last-Event-ID: 3' localhost:8000/transport/sse
```

**Expected — both missed messages replay immediately:**
```
id: 4
event: message
data: {"id": 4, "body": "fourth", "ts": ...}

id: 5
event: message
data: {"id": 5, "body": "fifth", "ts": ...}

```

✅ **That is a resume cursor, and it took one `if m["id"] > last_id` because the
protocol provides it.** WebSocket gives you nothing equivalent — you build it
yourself in [`10-ordering-and-delivery-semantics`](../10-ordering-and-delivery-semantics/).
Note this now; it's a genuine point in SSE's favour, and the reason SSE stays
Pulse's documented fallback.

---

## Part C-bis — Prove WSGI can't hold these open

The README claimed WSGI dies on held-open connections. Don't take it on faith.

Run the *same* code under gunicorn's sync WSGI worker model. Long-poll and SSE
are `async def` views, so first prove the smaller claim: a **sync** long poll
holds a worker thread. Add a deliberately sync, blocking version:

```python
# chat/transport.py  (temporary, for the demo)
import time as _t
def longpoll_sync(request):
    since = int(request.GET.get("since", 0))
    for _ in range(300):                 # poll the log for up to 30s
        newer = [m for m in _LOG if m["id"] > since]
        if newer:
            return JsonResponse(newer, safe=False)
        _t.sleep(0.1)                    # BLOCKS this worker thread
    return JsonResponse([], safe=False)
```
```bash
# 2 sync workers on purpose
gunicorn pulse.wsgi:application --workers 2 --bind 0.0.0.0:8001
```
Open three simultaneous long polls:
```bash
for i in 1 2 3; do curl -s "localhost:8001/transport/longpoll_sync?since=999" & done
# now try a normal request:
time curl -s "localhost:8001/transport/poll?since=0"
```

**Expected:** the `poll` request **hangs** until one of the three long polls
times out, because both gunicorn workers are parked inside `time.sleep`. Two
held connections took the whole server down.

Now the same three long polls against **Uvicorn** (async view, one process):

```bash
uvicorn pulse.asgi:application --port 8000       # already running
for i in 1 2 3; do curl -s "localhost:8000/transport/longpoll?since=999" & done
time curl -s "localhost:8000/transport/poll?since=0"
```

**Expected:** `poll` returns **instantly**. Three parked coroutines cost nothing;
the event loop serves the fourth request without blinking.

✅ **This is the Module 01 lesson as a two-line experiment.** "Concurrency is
free, resources are not" — under WSGI a held connection consumes a *thread* (a
scarce resource); under async it consumes a *coroutine* (nearly free). Remove
`longpoll_sync` before moving on.

---

## Part D — Measure the bytes

`code/measure_transports.sh` (create it from this listing):

```bash
#!/usr/bin/env bash
# Measure bytes-on-the-wire per delivered message for each transport.
set -euo pipefail
IFACE=lo
PORT=8000

measure() {
  local label="$1"; shift
  sudo timeout 22 tcpdump -i "$IFACE" -q -n "tcp port $PORT" -w /tmp/cap.pcap 2>/dev/null &
  local tcpd=$!
  sleep 1
  "$@" >/dev/null 2>&1 &
  local client=$!
  for i in $(seq 1 10); do
    sleep 1
    curl -s -X POST "localhost:$PORT/transport/publish" -d "msg-$i" >/dev/null
  done
  sleep 2
  kill "$client" 2>/dev/null || true
  wait "$tcpd" 2>/dev/null || true
  local total; total=$(stat -c%s /tmp/cap.pcap)
  printf "%-14s capture_bytes=%-8s per_msg=%s\n" "$label" "$total" "$((total / 10))"
}

poll_client() { while true; do curl -s "localhost:$PORT/transport/poll?since=0" >/dev/null; sleep 1; done; }
sse_client()  { curl -sN -H 'Accept: text/event-stream' "localhost:$PORT/transport/sse"; }
ws_client()   { websocat -n "ws://localhost:$PORT/ws-raw"; }

measure "polling(1s)" poll_client
measure "sse"         sse_client
measure "websocket"   ws_client
```

```bash
chmod +x code/measure_transports.sh
./code/measure_transports.sh
```

**Expected** (order-of-magnitude; absolute numbers vary by kernel and TLS):
```
polling(1s)    capture_bytes=71040   per_msg=7104
sse            capture_bytes=9860    per_msg=986
websocket      capture_bytes=6180    per_msg=618
```

✅ Roughly **11× more bytes for polling than WebSocket** at a one-second poll
interval — and polling's cost is paid whether or not there's anything to say,
which is the real point. Record these in `code/results.md`.

> Note that SSE is much closer to WebSocket than to polling. Most of polling's
> cost is HTTP headers and TCP setup, not the payload. This is why "SSE is
> basically fine" is a defensible position, and why Pulse keeps it as the
> fallback rather than something more exotic.

---

## Part E — Watch a proxy kill your connection

This is the single most common WebSocket production bug. Cause it deliberately.

`code/nginx-broken.conf`:
```nginx
events {}
http {
  upstream pulse { server host.docker.internal:8000; }
  server {
    listen 80;
    location / {
      proxy_pass http://pulse;
      proxy_http_version 1.1;
      proxy_set_header Upgrade    $http_upgrade;
      proxy_set_header Connection "upgrade";
      proxy_read_timeout 20s;          # <-- deliberately short (default is 60s)
    }
  }
}
```

```bash
docker run -d --name nginx-broken -p 8090:80 \
  --add-host=host.docker.internal:host-gateway \
  -v "$PWD/code/nginx-broken.conf:/etc/nginx/nginx.conf:ro" nginx:alpine

# connect through the proxy and just WAIT — send nothing
websocat -v ws://localhost:8090/ws-raw
```

**Expected — after exactly 20 seconds, with no warning:**
```
welcome 4b1e7c39
[INFO  websocat] Connection finished
```

✅ The connection died silently at the proxy's `proxy_read_timeout`. Neither the
client nor the server did anything wrong, and Django logged nothing — the socket
just closed. This is what "my WebSockets drop every 60 seconds" always is.

**Confirm the diagnosis** — connect directly, bypassing nginx, and wait 30 s:

```bash
websocat -v ws://localhost:8000/ws-raw
```
**Expected:** still connected after a minute. The server is innocent.

Now fix it two ways and verify both.

**Fix 1 — raise the timeout (only fixes proxies you control):**
```nginx
proxy_read_timeout 3600s;
```
```bash
docker restart nginx-broken
websocat -v ws://localhost:8090/ws-raw    # survives well past 20s
```

**Fix 2 — keep the connection non-idle** so no proxy anywhere can decide it's
dead. `websocat` can send its own pings; and Uvicorn can too:

```bash
# client-side heartbeat every 10s survives even the 20s timeout
websocat -v --ping-interval 10 ws://localhost:8090/ws-raw
```

Restore `proxy_read_timeout 20s;`, `docker restart nginx-broken`, and reconnect
with the ping interval.

**Expected:** survives indefinitely, even with `proxy_read_timeout 20s`, because
a ping every 10 s keeps the socket non-idle at the proxy.

You can also make **Uvicorn** send server-side pings, which protects clients that
don't ping:

```bash
uvicorn pulse.asgi:application --port 8000 --ws-ping-interval 10 --ws-ping-timeout 20
```

✅ **This is why Module 04 configures an application heartbeat at 10 seconds** on
top of Uvicorn's frame-level ping. Uvicorn's ping is a WebSocket *control* frame;
some corporate proxies strip control frames, so the JSON-protocol heartbeat in
Module 04 rides inside a normal *data* frame that nothing touches. Fixing the
proxy config only fixes proxies you control; heartbeats fix the NAT gateway in a
customer's office that you'll never see.

Now break it the other way — remove `proxy_http_version 1.1`:

```nginx
      # proxy_http_version 1.1;
```
```bash
docker restart nginx-broken
websocat -v ws://localhost:8090/ws-raw
```

**Expected — the handshake fails outright:**
```
[ERROR websocat] Error: WebSocketError: Received unexpected status code (400 Bad Request)
```

Because HTTP/1.0 has no `Upgrade` semantics, nginx never forwards the upgrade and
Django's ASGI server answers with a plain HTTP error. Two config lines, two
completely different failure modes, both extremely common.

**Bonus — the SSE buffering trap.** Add an SSE `location` *without*
`proxy_buffering off`:
```nginx
location /transport/sse { proxy_pass http://pulse; }   # buffering ON (default)
```
```bash
docker restart nginx-broken
curl -N -H 'Accept: text/event-stream' localhost:8090/transport/sse &
curl -s -X POST localhost:8000/transport/publish -d 'buffered?'
```
**Expected:** the event does **not** appear promptly in the SSE terminal — nginx
is holding it in a buffer. This is why your `sse` view sets `X-Accel-Buffering:
no` (nginx honours that header even without the location directive). Confirm the
header fixes it.

Clean up:
```bash
docker rm -f nginx-broken
```

---

## What you measured

| Measurement | Reference | Yours |
|-------------|-----------|-------|
| WS overhead server→client | 2 bytes | |
| WS overhead client→server | 6 bytes (mask) | |
| Bytes/msg: polling vs SSE vs WS | 7104 / 986 / 618 | |
| Held connections that kill 2 gunicorn sync workers | 2 | |
| Held connections an async worker shrugs off | 3 (and 30,000) | |
| Time to silent death behind a 20 s proxy timeout | 20 s | |
| Heartbeat interval that survives it | 10 s | |

---

## What you learned

- The handshake is a SHA-1 of a nonce plus a fixed GUID — you computed it, and
  Uvicorn's `websockets` library computed the same thing.
- A WebSocket frame costs 2 bytes server→client, 6 client→server, and you can
  decode one from hex with fifteen lines of Python.
- All three "doesn't let go" transports need **ASGI**; you proved WSGI dies on two
  held connections and async shrugs off three.
- SSE has resume (`Last-Event-ID`) **built into the protocol**; WebSocket makes
  you build it ([`10`](../10-ordering-and-delivery-semantics/)).
- Proxies kill idle connections silently, and **heartbeats — not proxy config —
  are the portable fix**, which is why Module 04 adds an application heartbeat.

Now do [`challenge.md`](./challenge.md).

Then: [Module 04 — Channels Chat on a Single Node](../04-channels-chat-single-node/).
