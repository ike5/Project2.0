# Module 03 — Real-Time Transports on the Wire

**Goal:** Understand every way a server can push data to a browser, at the level
of individual bytes on the socket — so that when a proxy silently kills your
connections every 60 seconds, you know exactly which layer to blame, and so that
you understand *why Django needs ASGI at all* before you write a single
consumer.

⏱️ ~5 hours · **Prerequisites:** Modules 00–02.

---

## The fundamental problem

HTTP was designed around one rule: **the client asks, the server answers.** There
is no way, in the base protocol, for a server to speak first. Every real-time
technology on the web is a workaround for that single sentence.

There are exactly three workarounds, and everything else is a variation:

1. **Ask repeatedly** (polling).
2. **Ask once and don't let go** (long polling, SSE).
3. **Stop speaking HTTP** (WebSocket, WebTransport).

This is the *same* problem the JVM twin's
[`03-realtime-transports`](../../spring-boot-chat-course/03-realtime-transports/)
opens with, and the wire protocols are identical — HTTP and RFC 6455 don't care
what language your server is written in. What changes on the Django side is the
*runtime model underneath* each workaround, and that difference is the whole
reason this course exists.

### The Django-specific twist: WSGI cannot do two of the three

Every workaround that "doesn't let go" — long polling, SSE, WebSocket — needs the
server to **hold a connection open while doing almost nothing**, thousands of
times over. That is precisely the workload the classic Django deployment model is
worst at.

```
WSGI (gunicorn sync workers, `runserver`)      ASGI (uvicorn/daphne, async views + Channels)
──────────────────────────────────────         ────────────────────────────────────────────
one request  ⇒  one OS thread, blocked          one request  ⇒  one asyncio Task, cheap
held-open request  ⇒  thread parked, gone        held-open request ⇒  coroutine suspended, ~free
1,000 held requests ⇒  1,000 threads ⇒  dead     1,000 held requests ⇒  1,000 tasks ⇒  fine
no way to push at all (request/response only)    the server can `await queue.get()` and push
```

A WSGI worker is a thread that runs your view top to bottom and then is free for
the next request. If your view *doesn't return* — because it's holding a long
poll open, or streaming an endless SSE response — that thread is occupied for the
entire lifetime of the connection. gunicorn's default is a *handful* of sync
workers per core. A hundred idle SSE clients exhaust them, and the hundred-and-
first user gets a connection refused. `manage.py runserver` is worse: it is a
development server that buffers responses and was never meant to stream at all.

**This is why the course pivots to ASGI in Module 02 and never looks back.** Under
ASGI, a held-open connection is a *suspended coroutine* on a single event-loop
thread — the Module 01 lesson made concrete. One Uvicorn worker process holds
tens of thousands of them on one core. Everything in this module that "doesn't
let go" assumes you are running under ASGI (Uvicorn with uvloop, or Daphne). We
will *prove* the WSGI failure in the lab, because seeing gunicorn refuse the
101st SSE client is worth more than reading this paragraph.

> **Term, defined once.** **ASGI** (Asynchronous Server Gateway Interface) is the
> async successor to WSGI: instead of a single blocking `application(environ,
> start_response)` call, an ASGI app is an `async` callable that receives
> `send`/`receive` coroutines and can therefore stream, push, and hold
> connections without occupying a thread. Uvicorn, Daphne, Granian, and
> Hypercorn are ASGI *servers*; Django 5.1's async views and Channels are ASGI
> *applications*.

---

## Option 1 — Polling

```
Client                          Server
  │  GET /messages?since=42       │
  ├──────────────────────────────▶│
  │◀──────────────────────────────┤  200 []      (nothing)
  │        ... wait 3s ...        │
  │  GET /messages?since=42       │
  ├──────────────────────────────▶│
  │◀──────────────────────────────┤  200 []      (nothing)
  │        ... wait 3s ...        │
  │  GET /messages?since=42       │
  ├──────────────────────────────▶│
  │◀──────────────────────────────┤  200 [msg43] (finally)
```

**Cost per empty poll:** a full HTTP request — headers (typically 500–800 bytes
with cookies), a TLS record, Django's URL routing, the middleware stack, session
deserialization, an auth check, a database or cache hit, and a rendered response.
For nothing.

```
10,000 users × 1 poll / 3s = 3,333 req/s
  ... to deliver, on average, almost nothing
```

**Latency:** uniformly distributed between 0 and the poll interval. Average
interval/2.

**When polling is genuinely correct** — and it often is, so don't be snobbish
about it:

- Update frequency is naturally low (a build status, a daily report, a
  cron-driven dashboard).
- You have very few clients.
- You need to work through infrastructure you don't control.
- You want **zero server-side connection state**, which makes horizontal scaling,
  deploys, and failover completely trivial. A poll is a stateless request; any
  worker on any node can serve it; you can deploy by killing every process at
  once and nobody notices. That's a real engineering benefit, not a consolation
  prize — and it's the one thing every "doesn't let go" transport gives up.

Polling is also the one transport that runs **perfectly well on plain WSGI
Django**, precisely because it holds nothing open. If your realtime needs are
modest, a polled `@api_view` on gunicorn is a legitimate, boring, correct answer
that will never page you at 3 a.m.

The reason chat doesn't use it is amplification: at 200-member rooms, polling
turns 33 inbound messages/second into millions of wasted requests, and the
database bears every one.

---

## Option 2 — Long polling

```
Client                          Server
  │  GET /messages?since=42       │
  ├──────────────────────────────▶│  ... holds the request open ...
  │                               │  ... 28 seconds pass ...
  │◀──────────────────────────────┤  200 [msg43]   (as soon as it exists)
  │  GET /messages?since=43       │  (client immediately re-asks)
  ├──────────────────────────────▶│
```

Latency approaches real-time. The cost moves from wasted requests to **held
connections** — which is exactly the Module 01 problem, and the exact place the
runtime model decides whether this is viable.

On WSGI, a long poll parks a worker thread for up to 30 seconds doing nothing but
waiting. This is why long polling had a terrible reputation for a decade: on
thread-per-request servers it was a denial-of-service you inflicted on yourself.
On async Django (an `async def` view under ASGI), the same held request is a
coroutine `await`-ing an `asyncio.Event` — it costs a few kilobytes and no
thread. **The technique didn't change; the runtime did.** This is the Python
analog of the JVM twin's "virtual threads make long polling viable again" — same
conclusion, different mechanism (there, cheap threads; here, cheap coroutines on
one thread).

**The gap problem:** between the server's response and the client's next request
there is a window — typically 1–50 ms — where the client isn't listening. A
message published in that window must be buffered server-side (keyed by the
`since` cursor) or it's lost. Every long-polling implementation needs this, and
this is where the concept of a **resume cursor** first appears. You'll build the
real version in [`10-ordering-and-delivery-semantics`](../10-ordering-and-delivery-semantics/).

Django has no `DeferredResult` equivalent, but it doesn't need one: an `async
def` view that `await`s a shared `asyncio.Event` or pulls from an `asyncio.Queue`
*is* a deferred result. You'll write one in the lab in about fifteen lines.

---

## Option 3 — Server-Sent Events (SSE)

One HTTP response that never ends.

```http
GET /stream HTTP/1.1
Accept: text/event-stream

HTTP/1.1 200 OK
Content-Type: text/event-stream
Cache-Control: no-cache
Connection: keep-alive
X-Accel-Buffering: no

id: 43
event: message
data: {"room":7,"body":"hello"}

id: 44
event: message
data: {"room":7,"body":"world"}

: this is a comment, used as a keep-alive ping

```

The wire format is trivially simple: `field: value` lines, a blank line
terminates an event. Multiple `data:` lines are concatenated with newlines.

**In Django, SSE is a `StreamingHttpResponse` wrapped around an async
generator.** That's the whole implementation:

```python
async def sse(request):
    async def event_stream():
        async for msg in subscribe(request):        # your source of events
            yield f"id: {msg.id}\nevent: message\ndata: {json.dumps(msg.body)}\n\n"
    resp = StreamingHttpResponse(event_stream(),
                                 content_type="text/event-stream")
    resp["Cache-Control"] = "no-cache"
    resp["X-Accel-Buffering"] = "no"                # tell nginx: do NOT buffer
    return resp
```

`StreamingHttpResponse` with an **async** generator only works under ASGI — this
is another place WSGI simply cannot follow. And the generator must be async, not
sync: a sync generator that blocks on I/O between `yield`s blocks the event loop
(the cardinal sin of Module 01, revisited hard in
[`04-channels-chat-single-node`](../04-channels-chat-single-node/) and
[`15-async-sync-and-raw-asgi`](../15-async-sync-and-raw-asgi/)).

**What SSE gives you for free:**

- **Automatic reconnection** in the browser's `EventSource`, with a
  server-controlled interval (`retry: 3000`).
- **Resume built into the protocol.** The browser remembers the last `id:` and
  re-sends it as the `Last-Event-ID` request header on reconnect. That's the
  resume cursor, standardized. In Django you read it with
  `request.headers.get("Last-Event-ID")` and replay from there.
- Plain HTTP — so proxies, CDNs, HTTP/2 multiplexing, and compression all work
  normally.

**What it costs you:**

- **One direction only.** Client → server needs a separate `POST`. For chat that's
  actually fine — sends are infrequent and a `POST` to a normal DRF view is a
  perfectly good way to send one.
- **Text only** (UTF-8). Binary needs base64, at a 33% size penalty.
- **The HTTP/1.1 six-connection limit.** A browser allows ~6 connections per
  origin; an SSE stream permanently occupies one. Open the app in three tabs and
  half your connection budget is gone. **HTTP/2 fixes this completely** (streams
  are multiplexed over one connection) — so *SSE over HTTP/2 is a genuinely
  strong choice*, much better than its reputation.
- **The `X-Accel-Buffering` / `proxy_buffering` trap.** nginx buffers proxied
  responses by default. With buffering on, your SSE events pile up in nginx and
  arrive in bursts, or never. The `X-Accel-Buffering: no` header above is the
  fix, and you will forget it once and lose an afternoon. (The lab makes you.)

> **Would SSE work for Pulse?** Yes, honestly. SSE down + `POST` up is a
> legitimate chat architecture, used in production by real products, and it runs
> on async Django with no Channels, no Redis channel layer, and no WebSocket
> proxying config. It's simpler to operate than WebSocket and survives proxies
> better. We choose WebSocket because message rates are high enough that
> per-message `POST` overhead matters, and because typing indicators and read
> receipts make the upstream channel chatty. But if someone in a design review
> proposes SSE, "that's not real-time" is a wrong answer.

---

## Option 4 — WebSocket

Start as HTTP, then stop being HTTP.

### The handshake

```http
GET /ws HTTP/1.1
Host: chat.example.com
Upgrade: websocket
Connection: Upgrade
Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==
Sec-WebSocket-Version: 13
Origin: https://chat.example.com
```
```http
HTTP/1.1 101 Switching Protocols
Upgrade: websocket
Connection: Upgrade
Sec-WebSocket-Accept: s3pPLMBiTxaQ9kYGzzhZRbK+xOo=
```

`Sec-WebSocket-Accept` = `base64(sha1(key + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"))`.

That constant GUID (the "magic string", fixed in RFC 6455) does one job: it
proves the server **understood** the WebSocket handshake rather than being a
naive HTTP server or cache that echoed something back. It is not authentication
and provides no security.

After `101`, the TCP connection carries WebSocket frames in both directions until
someone closes it. No more HTTP. In a Django deployment this is where **Daphne or
Uvicorn takes over from Django entirely** — the ASGI server does the framing;
your Channels consumer only ever sees decoded messages. You'll never write frame
parsing in production. You will write it *once* in this lab, so the abstraction
is never mysterious.

### The frame

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

A server→client text frame carrying `hi`:

```
0x81 0x02 0x68 0x69
 │    │    └────┴── payload: 'h' 'i'
 │    └── MASK=0, length=2
 └── FIN=1, opcode=0x1 (text)
```

**Four bytes to send two.** Compare to SSE's `data: hi\n\n` (10 bytes) or a
polling response's ~200 bytes of headers. At high message rates this is the whole
argument, and it is the direct cause of the ≈45 KB-per-connection and
150,000-msg/s numbers this course pins later — small frames are what let one
Uvicorn worker fan out to so many sockets.

A client→server frame is 6 bytes minimum, because clients **must** mask:

```
0x81 0x82 0x37 0xfa 0x21 0x3d 0x5f 0x93
 │    │    └──────┬───────┘   └────┬───┘
 │    │       mask key         masked payload
 │    └── MASK=1, length=2
 └── FIN=1, text
```

`payload[i] = masked[i] XOR key[i % 4]` → `0x5f^0x37='h'`, `0x93^0xfa='i'`.

You'll decode both of these from raw hex with a Python script in the lab, and the
XOR line above is the entire "decryption."

### Why masking exists (it isn't security)

The mask is random per frame and the key is sent in the clear, so it provides
zero confidentiality. It exists to defeat **cache poisoning**: without it, an
attacker could craft a WebSocket payload that looks like a valid HTTP request to
a transparent proxy that doesn't understand WebSocket, tricking it into caching
attacker-controlled content for a real URL. Random masking makes the bytes
unpredictable, so you can't construct a payload that survives as valid HTTP.

It costs a XOR pass over every client→server byte. In a Python server that XOR
runs in C inside the ASGI server (Uvicorn/websockets), not in your consumer —
cheap, but non-zero at scale, and one more reason the *upstream* frame is the
expensive direction.

### Control frames and the liveness problem

`0x9` ping, `0xA` pong, `0x8` close. Control frames must be ≤125 bytes and
cannot be fragmented.

**This matters because TCP won't tell you a connection died.** If a phone goes
into a tunnel, no FIN or RST is sent — the socket stays "open" on your server
indefinitely, holding a file descriptor, an asyncio Task, and a channel-layer
group subscription. Without a heartbeat, your connection count only goes up, and
so does that ≈45 KB × (dead connections).

```
Server                     Client (phone, now in a tunnel)
  │  ping ────────────────▶ ✗
  │  (no pong within 30s)
  │  → declare dead, close, free the FD, fire presence-offline
```

Uvicorn and Daphne can send WebSocket-level pings for you
(`--ws-ping-interval` / `--ws-ping-timeout` on Uvicorn), and that is the first
line of defense. Module 04 adds an **application-level** heartbeat in the JSON
protocol on top, because — as you'll see below — some proxies eat control frames,
and an application ping rides inside a normal data frame that nothing strips.

### Close codes you'll actually see

| Code | Meaning |
|------|---------|
| 1000 | Normal |
| 1001 | Going away (server shutting down, page navigating) |
| **1006** | **Abnormal — no close frame arrived.** You never *send* this; it's what a client reports when TCP just died. The most common code in production, and it tells you almost nothing. |
| 1009 | Message too big |
| 1011 | Server error (a consumer raised) |
| 4000–4999 | **Application-defined — use these.** "token expired", "kicked", "rate limited", "server draining, reconnect in N ms" |

> Designing your 4xxx codes is real protocol work. A client that receives 4001
> ("token expired") can refresh and reconnect immediately; a client that receives
> 1006 has to guess. In Channels you emit them with
> `await self.close(code=4001)`, and
> [`21-security-and-abuse-at-scale`](../21-security-and-abuse-at-scale/) defines
> Pulse's full set.

---

## Option 5 — WebTransport (HTTP/3 / QUIC)

The newest option, and worth knowing about even though you won't build on it here.

WebSocket rides on TCP, which means **head-of-line blocking**: one lost packet
stalls every message behind it, even unrelated ones. On a lossy mobile network
that's a real latency source (you'll measure it in the challenge).

WebTransport runs over QUIC and gives you:
- **Multiple independent streams** on one connection — a lost packet on the
  typing-indicator stream doesn't stall messages.
- **Unreliable datagrams** — perfect for presence and typing, where a lost
  update is superseded a second later anyway.
- Connection migration: a phone switching Wi-Fi → cellular keeps the connection.

**Why not use it for Pulse:** browser support is still uneven; and on the *Django
side specifically*, the story is worse than on the JVM — Daphne and Uvicorn do
not speak HTTP/3 at all today, the ASGI spec's WebTransport extension is still
provisional, and the only Python QUIC stack (`aioquic`) is a library you'd wire
up by hand, outside Channels. Add corporate networks that block UDP/443 outright,
and it's the right thing to watch, not yet the right thing to bet a course on.
Module 03's challenge has you reason about which Pulse traffic *would* move to
datagrams if it were available — that's the useful exercise, and the insight
transfers to a design you *can* ship today (Pub/Sub for typing, Streams for
messages;
[`07-scale-out-redis-channel-layer`](../07-scale-out-redis-channel-layer/) and
[`09-redis-streams-delivery`](../09-redis-streams-delivery/)).

---

## The comparison

| | Polling | Long poll | SSE | WebSocket | WebTransport |
|---|---------|-----------|-----|-----------|--------------|
| Direction | ↕ (req/res) | ↕ (req/res) | ↓ only | ↕ | ↕ |
| Latency | interval/2 | ~real-time | ~real-time | ~real-time | ~real-time |
| Overhead/msg | ~500+ B | ~500+ B | ~10 B | **~4 B** | ~4 B |
| Binary | Yes | Yes | No (base64) | Yes | Yes |
| Auto-reconnect | n/a | Manual | **Built-in** | Manual | Manual |
| Resume cursor | Manual | Manual | **Built-in** (`Last-Event-ID`) | Manual | Manual |
| Proxy friendliness | Perfect | Good | Good | **Needs config** | Often blocked |
| Server conn state | None | Held | Held | Held | Held |
| Runs on WSGI Django | **Yes** | No (needs async) | No (needs async) | No (needs Channels) | No |
| HTTP/2 multiplexed | Yes | Yes | **Yes** | No* | n/a (HTTP/3) |
| Browser support | 100% | 100% | 98% | 98% | ~70% |

\* RFC 8441 defines WebSocket over HTTP/2, but support is inconsistent enough
that it's not something to rely on — and neither Daphne nor Uvicorn implements
it.

The "Runs on WSGI Django" row is the one that's new versus the JVM twin, and it's
the one that shapes your deployment: the moment you leave polling, you are an ASGI
shop, and everything from Module 04 onward assumes it.

---

## What proxies do to each of these

This is the section that saves you a day of debugging.

| Layer | What it does | Symptom |
|-------|--------------|---------|
| **nginx** without `proxy_http_version 1.1` | Can't upgrade — HTTP/1.0 has no `Upgrade` | Handshake fails with 400/502 |
| **nginx** default `proxy_read_timeout 60s` | Closes idle upstream connections | **Sockets die every 60 s**, blamed on the client |
| **nginx** `proxy_buffering on` (default) | Buffers the response | SSE messages arrive in bursts, or never |
| **AWS ALB / GCP LB** idle timeout (60 s default) | Same as above | Same as above |
| **Corporate proxy** stripping `Upgrade` | Handshake never completes | WebSocket fails only on the office network |
| **Transparent proxy** buffering | Breaks streaming | SSE/long-poll delayed |
| **NAT / firewall** idle eviction (30–300 s) | Silently drops the TCP mapping | Connection appears alive on both ends; nothing flows |

**The defense is the same for all of them:** application-level heartbeats every
10–30 seconds. They keep the connection non-idle at every layer, and —
critically — they let you *detect* the dead ones. Without heartbeats, both sides
think a NAT-evicted connection is fine, forever.

For Django specifically, three of these have concrete config fixes you must know:

```nginx
# The three lines that make Django + Channels work behind nginx
location /ws {
    proxy_pass http://pulse;
    proxy_http_version 1.1;                 # or the Upgrade never happens
    proxy_set_header Upgrade    $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_read_timeout 3600s;               # or idle sockets die at 60s
}
location /sse {
    proxy_pass http://pulse;
    proxy_buffering off;                    # or SSE events arrive in bursts
    proxy_read_timeout 3600s;
}
```

And in the app, the portable fix that survives proxies you *don't* control:
Module 04 sends a heartbeat frame every 10 seconds inside the JSON protocol,
plus configures Uvicorn's own WebSocket ping. You'll reproduce the failure in the
lab — an nginx `proxy_read_timeout 20s` killing an idle socket at exactly 20
seconds — and then fix it both ways.

---

## The decision, for Pulse

**WebSocket with a JSON protocol we design ourselves, with SSE as a documented
fallback.**

- Message rate and bidirectional chatter (typing, receipts, acks) justify the
  framing efficiency.
- **There is no STOMP here.** The JVM twin adopts STOMP to get subscriptions,
  destinations, acks, and heartbeats "already written down." Django Channels has
  no equivalent broker sub-protocol, and adding one would be swimming upstream.
  Instead we design a small JSON envelope — the `type`-tagged message from
  [`05-protocol-and-domain-design`](../05-protocol-and-domain-design/) — and
  Channels' *groups* give us the "address a message to some connections"
  primitive that STOMP destinations gave Spring. This is a real divergence from
  the JVM twin, and Module 05 is where it's paid for in full: everything STOMP
  handed Spring for free, we specify and build.
- SSE + POST remains the fallback for hostile networks — and by Module 10 the
  resume-cursor machinery is transport-independent, so switching transports
  doesn't change the delivery semantics.

We are **not** using SockJS or any fallback-transport shim. It was essential in
2015; today it adds a significant complexity tax for browsers that essentially no
longer exist. If you need a fallback, plain SSE is simpler and better.

---

## What's next

The lab has you speak all four protocols by hand — computing the handshake SHA-1
yourself, decoding WebSocket frames byte by byte with a Python script, building a
polling view, an async long-poll view, an async SSE view with `Last-Event-ID`
resume, and a raw Channels WebSocket — then measuring the actual bytes-on-the-wire
difference, and finally watching an nginx timeout kill an idle socket and fixing
it.

See you in [`lab.md`](./lab.md).
