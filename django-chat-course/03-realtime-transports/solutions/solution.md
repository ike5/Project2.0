# Solutions — Module 03

---

## Task 1 — A frame encoder, and a handshake from scratch

`code/ws_raw.py`:

```python
#!/usr/bin/env python3
"""A minimal WebSocket client: handshake + frame codec, no libraries."""
import base64, hashlib, os, socket, struct, sys

GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"

def encode(payload: bytes, opcode: int = 0x1, mask: bool = True) -> bytes:
    frame = bytearray()
    frame.append(0x80 | opcode)                       # FIN=1

    n = len(payload)
    mask_bit = 0x80 if mask else 0x00
    if n < 126:
        frame.append(mask_bit | n)
    elif n < 65536:
        frame.append(mask_bit | 126)
        frame += struct.pack(">H", n)                 # 16-bit
    else:
        frame.append(mask_bit | 127)
        frame += struct.pack(">Q", n)                 # 64-bit

    if mask:
        key = os.urandom(4)
        frame += key
        frame += bytes(b ^ key[i % 4] for i, b in enumerate(payload))
    else:
        frame += payload
    return bytes(frame)

def handshake(sock, host, path):
    key = base64.b64encode(os.urandom(16)).decode()
    req = (f"GET {path} HTTP/1.1\r\n"
           f"Host: {host}\r\n"
           f"Upgrade: websocket\r\n"
           f"Connection: Upgrade\r\n"
           f"Sec-WebSocket-Key: {key}\r\n"
           f"Sec-WebSocket-Version: 13\r\n\r\n")
    sock.sendall(req.encode())

    resp = b""
    while b"\r\n\r\n" not in resp:
        resp += sock.recv(4096)
    head = resp.split(b"\r\n\r\n")[0].decode()
    assert "101" in head.split("\r\n")[0], head

    expected = base64.b64encode(hashlib.sha1((key + GUID).encode()).digest()).decode()
    got = [l.split(": ", 1)[1] for l in head.split("\r\n")
           if l.lower().startswith("sec-websocket-accept")][0]
    assert got == expected, f"accept mismatch: {got} != {expected}"
    print(f"handshake OK  key={key}  accept={got}")
    return resp.split(b"\r\n\r\n", 1)[1]

def read_frame(sock, buffered=b""):
    def need(n, buf):
        while len(buf) < n:
            buf += sock.recv(4096)
        return buf
    buf = need(2, buffered)
    length = buf[1] & 0x7F
    i = 2
    if length == 126:
        buf = need(4, buf); length = struct.unpack(">H", buf[2:4])[0]; i = 4
    elif length == 127:
        buf = need(10, buf); length = struct.unpack(">Q", buf[2:10])[0]; i = 10
    buf = need(i + length, buf)
    return buf[i:i+length], buf[i+length:]

if __name__ == "__main__":
    s = socket.create_connection(("localhost", 8000))
    rest = handshake(s, "localhost:8000", "/ws-raw")
    payload, rest = read_frame(s, rest)
    print("server said:", payload.decode())

    for size in (2, 200, 70000):
        body = b"x" * size
        frame = encode(body)
        header_len = len(frame) - size - 4       # minus the 4-byte mask key
        print(f"payload={size:6d}  header={header_len} bytes  first_bytes={frame[:4].hex()}")

    s.sendall(encode(b"hello from raw python"))
    payload, rest = read_frame(s, rest)
    print("echo:", payload.decode())
    s.sendall(encode(b"", opcode=0x8))           # close
    s.close()
```

```bash
python3 code/ws_raw.py
```

**Expected:**
```
handshake OK  key=x3JJHMbDL1EzLkh9GBhXDw==  accept=HSmrc0sMlYUkAGmm5OPpG2HaGWk=
server said: welcome 7c2f8a11
payload=     2  header=2 bytes  first_bytes=81823f9c
payload=   200  header=4 bytes  first_bytes=81fe00c8
payload= 70000  header=10 bytes first_bytes=81ff0000
echo: hello from raw python
```

✅ Header is 2, 4, and 10 bytes as designed, and Uvicorn's `websockets` layer
accepted a frame your own code built. There is no magic in the abstraction — you
just re-implemented it.

> **A Python-specific note the JVM twin doesn't have.** Python integers are
> arbitrary-precision, so the `>Q` 64-bit pack never has to worry about signed
> overflow the way Java's `long` does. The RFC still forbids the top bit of the
> 64-bit length being set (max 2⁶³−1) so that *signed-64 languages* can't misread
> the length as negative — a courtesy your Python encoder benefits from without
> ever being at risk itself.

### Why sentinels 126/127 instead of always 64-bit

The 7-bit field can express 0–127 directly. Reserving the top two values as
escape hatches means:

- **The overwhelmingly common case costs nothing.** Chat messages, control
  frames, and heartbeats are all under 126 bytes, so they use a 2-byte header. If
  the length were always 64-bit, every frame would carry a 10-byte header — and 8
  of those 10 bytes would be zeros.
- For a 50-byte chat message, always-64-bit would mean **10 bytes of header for 50
  bytes of payload (20% overhead)** instead of 2 bytes (4%).
- The escape values are chosen so the encoding stays **self-describing and
  unambiguous**: you always know from byte 1 exactly how many more length bytes to
  read, with no lookahead.

This is the same variable-length-integer idea as UTF-8 or Protobuf varints:
optimize the common case, pay only when you need the range. At Pulse's target of
~150,000 outbound messages/second, the difference between a 2-byte and a 10-byte
header is 8 bytes × 150,000 = 1.2 MB/s of pure header on one node — small, but
free to avoid, and it compounds across a cluster.

---

## Task 2 — Masking is not security

```bash
# capture a client frame (client→server frames are masked; filter for them)
sudo tcpdump -i lo -s0 -X 'tcp port 8000' -c 10
```

Given wire bytes `81 82 37 fa 21 3d 5f 93`:

```python
masked = bytes.fromhex("5f93")
key    = bytes.fromhex("37fa213d")
plain  = bytes(b ^ key[i % 4] for i, b in enumerate(masked))
print(plain)      # b'hi'
```

**Expected:** `b'hi'` — recovered using only bytes that were on the wire.

**Two sentences:**

> Masking defends transparent intermediaries — proxies and caches that don't
> understand WebSocket — against **cache poisoning**: without an unpredictable
> per-frame XOR, an attacker could craft a payload that a naive proxy parses as a
> second, valid HTTP request and caches under an attacker-chosen URL. It provides
> no confidentiality whatsoever because the key travels in the same frame, in the
> clear, four bytes before the data it masks.

**And `Sec-WebSocket-Key`:**

> It's a random nonce, not a credential — the server's response is a deterministic
> SHA-1 of it plus a public constant, computable by anyone (you computed it in
> Part A). It proves the responder implements RFC 6455 rather than being a cache
> replaying a stored response, and nothing more. Authentication has to come from a
> cookie, a token in the query string or a single-use ticket, or a
> `Sec-WebSocket-Protocol` value — the WebSocket-auth problem Module 04 sets up
> and [`21`](../21-security-and-abuse-at-scale/) solves.

---

## Task 3 — SSE with resume, keep-alives, and no leak

The lab's `sse` view is already close. The two things to get right are (a)
replaying **before** subscribing so nothing is delivered twice, and (b)
guaranteeing the `finally` runs when the client vanishes.

```python
# chat/transport.py
import asyncio, json
from django.http import StreamingHttpResponse

async def sse(request):
    last_id = int(request.headers.get("Last-Event-ID", request.GET.get("lastId", 0)))

    async def event_stream():
        q: asyncio.Queue = asyncio.Queue()
        # Subscribe FIRST, snapshot the log, THEN replay — so a message published
        # during replay lands in the queue and is delivered exactly once (the live
        # push skips it only if it predates our snapshot cutoff).
        _WAITERS.add(q)
        try:
            cutoff = last_id
            for m in list(_LOG):
                if m["id"] > cutoff:
                    yield _sse_event(m)
                    cutoff = m["id"]
            while True:
                try:
                    m = await asyncio.wait_for(q.get(), timeout=15)
                    if m["id"] > cutoff:            # de-dup against the replay
                        yield _sse_event(m)
                        cutoff = m["id"]
                except asyncio.TimeoutError:
                    yield ": ping\n\n"
        finally:
            _WAITERS.discard(q)                    # ALWAYS runs — see below

    resp = StreamingHttpResponse(event_stream(), content_type="text/event-stream")
    resp["Cache-Control"] = "no-cache"
    resp["X-Accel-Buffering"] = "no"
    return resp
```

### The two subtle bugs this avoids

**1. The replay/live race.** If you snapshot-and-replay *before* subscribing, a
message published in the microsecond between the two steps is lost — neither the
replay nor the (not-yet-registered) queue sees it. Subscribing first and tracking
a `cutoff` means every message is delivered exactly once: by the replay loop if it
was already in `_LOG`, or by the live queue if it arrived after, with the `cutoff`
comparison suppressing the overlap. This is the async, single-process version of
the JVM twin's `CopyOnWriteArrayList` snapshot boundary — Python's GIL makes
`list(_LOG)` an atomic-enough snapshot for one process, which is all we have here
anyway (Module 04).

**2. The leak.** In Django's ASGI SSE, when a client disappears the server does
**not** get an immediate callback. The generator stays suspended at `await q.get()`
until either (a) the ASGI server notices the disconnect and throws
`asyncio.CancelledError` into the coroutine, or (b) you next try to `yield` down a
dead socket and it raises. Uvicorn does throw `CancelledError` on disconnect — so
the `finally` runs and `_WAITERS.discard(q)` fires. **The `finally` is not
politeness; it's garbage collection.** Omit it and every dropped client leaves a
`Queue` in `_WAITERS` forever, and `_publish` slows down linearly as it iterates a
growing set of dead queues — the Python analog of the JVM twin's emitter leak.

> **A real ASGI subtlety.** `CancelledError` only arrives if the server is
> *reading* the request or the response backpressure surfaces the disconnect. For
> a purely outbound SSE stream with no client traffic, the disconnect is detected
> on the next `yield` to the closed socket — which is why the 15-second keep-alive
> earns its keep a second time: it forces a periodic write that *will* raise on a
> dead socket, bounding how long a leaked queue can linger to ~15 s. Keep-alive is
> resume-friendliness **and** leak detection.

### The test

```python
# tests/test_sse.py   (pytest -q)
import asyncio, json, pytest
from httpx import AsyncClient, ASGITransport
from pulse.asgi import application
from chat import transport

@pytest.mark.asyncio
async def test_resume_without_loss_or_duplication():
    transport._LOG.clear(); transport._SEQ = 0
    start_waiters = len(transport._WAITERS)
    client = AsyncClient(transport=ASGITransport(app=application), base_url="http://t")

    transport._publish("before")                          # id=1

    # 1. open a stream, read the replay of "before", then hard-close it
    async with client.stream("GET", "/transport/sse",
                             headers={"Accept": "text/event-stream"}) as r:
        got_first = await _read_one_event(r)
    assert '"id": 1' in got_first

    # 2. publish 5 while disconnected
    for i in range(1, 6):
        transport._publish(f"during-{i}")                 # ids 2..6

    # 3. reconnect with Last-Event-ID: 1
    ids = []
    async with client.stream("GET", "/transport/sse",
                             headers={"Last-Event-ID": "1"}) as r:
        for _ in range(5):
            ev = await _read_one_event(r)
            ids.append(json.loads(ev.split("data: ", 1)[1].strip())["id"])

    assert ids == [2, 3, 4, 5, 6], f"lost or duplicated: {ids}"
    assert len(set(ids)) == len(ids), "duplicates"

    await asyncio.sleep(0)                                 # let finally blocks run
    assert len(transport._WAITERS) == start_waiters, "queue leak in _WAITERS"

async def _read_one_event(response) -> str:
    buf = ""
    async for chunk in response.aiter_text():
        buf += chunk
        if "\n\n" in buf:
            event, buf = buf.split("\n\n", 1)
            if event.startswith(": "):                     # skip keep-alive pings
                continue
            return event + "\n\n"
```

**Expected:**
```
tests/test_sse.py::test_resume_without_loss_or_duplication PASSED
```

Remove the `finally` and the final assertion fails with `queue leak in _WAITERS`
— the leak, demonstrated.

---

## Task 4 — Head-of-line blocking

```bash
sudo tc qdisc add dev lo root netem loss 2%
```

Reference results, 100 × 100-byte messages (8-core reference machine, Uvicorn +
uvloop):

| Setup | p50 | p99 | max |
|-------|-----|-----|-----|
| No loss, 1 connection | 0.4 ms | 1.1 ms | 2 ms |
| **2% loss, 1 connection** | 0.5 ms | **214 ms** | 431 ms |
| **2% loss, 10 connections** | 0.5 ms | **28 ms** | 218 ms |

```bash
sudo tc qdisc del dev lo root
```

### Why

TCP guarantees **in-order delivery of a byte stream**. When a segment is lost, the
receiver's kernel has already got the bytes that came after it, but it **cannot
hand them to the application** — that would violate ordering. Everything waits for
the retransmission, which takes at least one RTO (~200 ms minimum on Linux,
`TCP_RTO_MIN`).

That's the 214 ms p99: not network latency, but *one* lost packet blocking every
message queued behind it on that single connection. Note this is a property of
**TCP**, not of Python or asyncio — uvloop can't help, because the stall is in the
kernel's receive buffer before your event loop ever sees the bytes.

Spreading across 10 connections means a loss only stalls the ~10% of messages on
that connection, so the aggregate p99 drops roughly 8×. But 10 connections costs
10× the handshakes, 10× the ≈45 KB-per-connection server state, and you've now got
**no ordering guarantee across connections** — which for chat is a correctness
problem, not just a cost.

**This is exactly what QUIC solves:** independent streams over one connection,
each with its own ordering, so a loss on one doesn't block the others.

### Which Pulse traffic belongs on datagrams

| Message type | Datagram? | Why |
|--------------|-----------|-----|
| **Typing indicator** | ✅ **Yes** | Superseded every ~2 s. A lost one is invisible. Retransmitting a stale "alice is typing" is actively *worse* than dropping it. |
| **Presence heartbeat** | ✅ **Yes** | Same logic — it's a TTL refresh; the next one is 15 s away and TTL is 45 s, so you tolerate two losses ([`11`](../11-presence-and-rate-limiting/)). |
| **Cursor / scroll sync** | ✅ Yes | Latest value wins. |
| **Chat message** | ❌ **No** | Must not be lost, must be ordered. This is precisely what reliable streams are for, and what per-room `seq` (Module 05) protects. |
| **Read receipt** | ❌ No — but nearly | Idempotent and monotonic (a receipt for seq 50 subsumes one for 40), so a loss self-heals on the next receipt. Rare and small; no throughput argument for datagrams, so keep it on a stream and keep it simple. |
| **Message ack** | ❌ No | Losing an ack triggers a client retry, which costs a duplicate and a dedup-cache hit (Module 05). Cheap but pointless to risk. |

**The general rule:** a message belongs on a datagram when it is **state-latest
rather than event-log** — where the next update makes the lost one irrelevant. If
losing it leaves a permanent hole in the user's history, it needs a reliable
stream.

**The takeaway that matters today:** you get most of this benefit *without QUIC*
by not sending typing indicators through the same ordering guarantees as messages.
Pulse routes typing over Redis **Pub/Sub** (at-most-once,
[`07`](../07-scale-out-redis-channel-layer/)) and messages over Redis **Streams**
(at-least-once, [`09`](../09-redis-streams-delivery/)). Different semantics for
different traffic is a design decision, not an inconsistency — and it's the
insight WebTransport would let you push down to the transport layer, if
Daphne/Uvicorn spoke HTTP/3, which they don't.

---

## Task 5 — The architecture note

> ### Pulse transport recommendation
>
> **Primary: WebSocket via Django Channels, with a JSON `type`-tagged protocol we
> design ourselves (Module 05). Fallback: SSE (down) + POST (up) on async Django.**
>
> **Assumptions this rests on:**
> - Average room size 50–500 members; p95 room size under 5,000.
> - Steady-state 1 message per user per 60 s, bursting 10×.
> - Bidirectional chatter is significant: typing indicators, read receipts, and
>   per-message acks mean the client→server channel is not idle.
> - Clients are primarily browsers and mobile web on networks we don't control.
> - We are already an **ASGI** deployment (Uvicorn + uvloop), because everything
>   past polling requires it.
>
> **Evidence** (measured, Lab 03 Part D, 10 messages over 20 s):
>
> | Transport | Bytes/msg | Overhead/frame |
> |-----------|-----------|----------------|
> | Polling (1 s) | 7,104 | ~500 B headers |
> | SSE | 986 | ~10 B |
> | WebSocket | 618 | **2 B down / 6 B up** |
>
> **Why WebSocket over SSE:** with acks, typing, and receipts, an SSE design needs
> a POST per upstream event — at ~500 bytes of headers each, upstream chatter
> costs more than the entire downstream stream. WebSocket's 6-byte upstream frame
> removes that.
>
> **Django-specific constraints baked into this choice:**
> - **No STOMP.** Unlike the JVM twin, we get no broker sub-protocol for free;
>   Channels *groups* are our addressing primitive and Module 05 designs the
>   envelope, acks, and heartbeats by hand.
> - **ASGI is mandatory** for both the primary and the fallback; WSGI can serve
>   only the polling degrade path.
> - **The channel layer is per-process** (Module 04), so even the single-node
>   design needs Redis sooner than the JVM twin — a fact that makes the WebSocket
>   choice *more* expensive to operate, and worth stating honestly.
>
> **What would change the answer:**
> - If upstream traffic dropped to only chat sends (no typing, no per-message
>   acks), **SSE + POST wins** on operational simplicity: free reconnect, free
>   resume via `Last-Event-ID`, no WebSocket proxy config, HTTP/2 multiplexing,
>   and — critically for Django — **no Channels and no Redis channel layer at
>   all**, deleting Phase 2's channel-layer complexity for the read path.
> - If we had to run behind customer-controlled corporate proxies that strip
>   `Upgrade`, SSE becomes primary, not fallback.
> - If average room size fell below ~10 and message rates were minutes apart,
>   **long polling on WSGI would be adequate** and would eliminate all
>   connection-state complexity — deleting Phases 2 and 5 of this design.

### The counter-argument, in three sentences

> SSE + POST would have been the better choice on Django specifically: it runs on
> plain async views with no channel layer, gets automatic reconnection and a
> standardized resume cursor for free where WebSocket makes us hand-build both
> (Modules 10 and 17), and it sidesteps the per-process channel-layer problem that
> forces Redis into even our single-node deployment. The upstream POST overhead we
> cited is real but mostly theoretical — typing indicators debounce to one POST
> per 3 seconds and per-message acks batch, collapsing the upstream rate by an
> order of magnitude. We are, in effect, adopting Channels and Redis two modules
> early to avoid a problem a 3-second debounce would have solved.

---

## Task 6 (stretch) — `permessage-deflate`

Uvicorn's `websockets` backend negotiates `permessage-deflate` when the client
offers it; you can also disable it to compare:

```bash
uvicorn pulse.asgi:application --port 8000                          # deflate on (default when offered)
uvicorn pulse.asgi:application --port 8000 --ws-per-message-deflate false   # off
```

Reference results (measure bytes with `tcpdump`, CPU with `py-spy` or `perf`):

| Payload | Raw bytes | Compressed | Ratio | CPU (server) |
|---------|-----------|-----------|-------|--------------|
| 50 B chat message | 52 | **61** | **1.17× (BIGGER)** | +34% |
| 500 B message w/ metadata | 502 | 318 | 0.63× | +28% |
| 5 KB JSON payload | 5,004 | 802 | **0.16×** | +21% |
| 50 KB history page | 50,004 | 4,240 | 0.08× | +18% |

**Crossover: ~200–300 bytes.** Below that, DEFLATE's block headers and the
dictionary overhead cost more than the compression saves — a 50-byte message gets
*bigger*.

### Why enabling it globally on a Python fan-out server is usually wrong

1. **Typical chat messages are below the crossover.** A 50-byte message gets
   larger, and you paid CPU for the privilege.
2. **CPU is the scarce resource in a fan-out server, not bandwidth — and doubly so
   in Python.** One async worker is **one core** (the GIL; Module 01). Compression
   is CPU work that runs *on the event loop's thread* unless you offload it, so
   every millisecond spent deflating is a millisecond the loop isn't fanning out
   messages. The `websockets` library compresses **per connection**, so one
   inbound message broadcast to 500 people is compressed up to 500 times. That's
   the number that kills your 150,000-msg/s knee.
3. **Memory, against a tight budget.** Each connection with `permessage-deflate`
   and no `no_context_takeover` holds a zlib dictionary — roughly **32 KB per
   connection**. The course pins the idle connection at **≈45 KB app heap**;
   adding a 32 KB zlib context **nearly doubles it**, so 40,000 connections/worker
   becomes ~24,000 before the same memory pressure. You'd trade a third of your
   connection density for negative savings on 50-byte messages.
4. **CRIME/BREACH-class concerns.** Compressing attacker-influenced content
   alongside secrets in the same stream can leak the secrets through size. Less
   acute for WebSocket than HTTPS, but not zero.

**What to do instead:**

- Compress **selectively** at the application layer for large frames only —
  history pages, file metadata, initial room sync — and mark it in the Module 05
  envelope. Leave live messages uncompressed.
- If you do enable `permessage-deflate`, set `server_no_context_takeover` /
  `client_no_context_takeover` to bound the per-connection memory (trading ratio
  for the ≈45 KB budget).
- **Shorten your JSON field names first.** Module 05 discusses `{"v":1,"t":"m.c"}`
  vs verbose keys — that saves 30–40% with **zero** CPU cost, which on a
  GIL-bound server is the only kind of saving worth having by default.

> This is a recurring theme: the interesting question is never "is compression
> good?" but **"what is scarce here?"** On a Python fan-out server, CPU (one core
> per worker) and per-connection memory (≈45 KB budget) are scarce and bandwidth
> usually isn't — so the default answer inverts, harder than it does on the JVM.
