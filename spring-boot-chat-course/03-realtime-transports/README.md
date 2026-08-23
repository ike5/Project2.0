# Module 03 — Real-Time Transports on the Wire

**Goal:** Understand every way a server can push data to a browser, at the level
of individual bytes on the socket — so that when a proxy silently kills your
connections every 60 seconds, you know exactly which layer to blame.

⏱️ ~5 hours · **Prerequisites:** Modules 00–02.

---

## The fundamental problem

HTTP was designed around one rule: **the client asks, the server answers.** There
is no way for a server to speak first. Every real-time technology on the web is a
workaround for that single sentence.

There are exactly three workarounds, and everything else is a variation:

1. **Ask repeatedly** (polling).
2. **Ask once and don't let go** (long polling, SSE).
3. **Stop speaking HTTP** (WebSocket, WebTransport).

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
with cookies), a TLS record, server-side auth and routing, a database or cache
hit, and a response. For nothing.

```
10,000 users × 1 poll / 3s = 3,333 req/s
  ... to deliver, on average, almost nothing
```

**Latency:** uniformly distributed between 0 and the poll interval. Average
interval/2.

**When polling is genuinely correct** — and it often is, so don't be snobbish
about it:

- Update frequency is naturally low (a build status, a daily report).
- You have very few clients.
- You need to work through infrastructure you don't control.
- You want zero server-side connection state — which makes horizontal scaling,
  deploys, and failover completely trivial. That's a real engineering benefit,
  not a consolation prize.

The reason chat doesn't use it is amplification: at 200-member rooms, polling
turns 33 inbound messages/second into millions of wasted requests.

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
connections** — which is exactly the Module 01 problem, and why long polling on a
thread-per-request server was a disaster, and why virtual threads make it viable
again.

**The gap problem:** between the server's response and the client's next request
there is a window — typically 1–50 ms — where the client isn't listening. A
message published in that window must be buffered server-side (keyed by the
`since` cursor) or it's lost. Every long-polling implementation needs this, and
this is where the concept of a **resume cursor** first appears. You'll build the
real version in Module 10.

Spring supports this natively with `DeferredResult` or `SseEmitter`. It remains
a genuinely reasonable fallback.

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

**What SSE gives you for free:**

- **Automatic reconnection** in the browser's `EventSource`, with a
  server-controlled interval (`retry: 3000`).
- **Resume built into the protocol.** The browser remembers the last `id:` and
  sends it as `Last-Event-ID` on reconnect. That's the resume cursor, standardized.
- Plain HTTP — so proxies, CDNs, HTTP/2 multiplexing, and compression all work
  normally.

**What it costs you:**

- **One direction only.** Client → server needs a separate POST. For chat that's
  actually fine — sends are infrequent and a POST is a perfectly good way to
  send one.
- **Text only** (UTF-8). Binary needs base64, at a 33% size penalty.
- **The HTTP/1.1 six-connection limit.** A browser allows ~6 connections per
  origin; an SSE stream permanently occupies one. Open the app in three tabs and
  half your connection budget is gone. **HTTP/2 fixes this completely** (streams
  are multiplexed over one connection) — so *SSE over HTTP/2 is a genuinely
  strong choice* and much better than its reputation suggests.

> **Would SSE work for Pulse?** Yes, honestly. SSE down + POST up is a
> legitimate chat architecture, used in production by real products. It's
> simpler to operate than WebSocket and survives proxies better. We choose
> WebSocket because message rates are high enough that per-message POST overhead
> matters, and because typing indicators and read receipts make the upstream
> channel chatty. But if someone in a design review proposes SSE, "that's not
> real-time" is a wrong answer.

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

That constant GUID does one job: it proves the server **understood** the
WebSocket handshake rather than being a naive HTTP server or cache that echoed
something back. It is not authentication and provides no security.

After `101`, the TCP connection carries WebSocket frames in both directions until
someone closes it. No more HTTP.

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
argument.

A client→server frame is 6 bytes minimum, because clients **must** mask:

```
0x81 0x82 0x37 0xfa 0x21 0x3d 0x5f 0x93
 │    │    └──────┬───────┘   └────┬───┘
 │    │       mask key         masked payload
 │    └── MASK=1, length=2
 └── FIN=1, text
```

`payload[i] = masked[i] XOR key[i % 4]` → `0x5f^0x37='h'`, `0x93^0xfa='i'`.

### Why masking exists (it isn't security)

The mask is random per frame and the key is sent in the clear, so it provides
zero confidentiality. It exists to defeat **cache poisoning**: without it, an
attacker could craft a WebSocket payload that looks like a valid HTTP request to
a transparent proxy that doesn't understand WebSocket, tricking it into caching
attacker-controlled content for a real URL. Random masking makes the bytes
unpredictable, so you can't construct a payload that survives as valid HTTP.

It costs a XOR pass over every client→server byte. Cheap, but non-zero at scale.

### Control frames and the liveness problem

`0x9` ping, `0xA` pong, `0x8` close. Control frames must be ≤125 bytes and
cannot be fragmented.

**This matters because TCP won't tell you a connection died.** If a phone goes
into a tunnel, no FIN or RST is sent — the socket stays "open" on your server
indefinitely, holding a file descriptor and a session entry. Without a
heartbeat, your connection count only goes up.

```
Server                     Client (phone, now in a tunnel)
  │  ping ────────────────▶ ✗
  │  (no pong within 30s)
  │  → declare dead, close, free the FD, fire presence-offline
```

STOMP adds its own application-level heartbeat on top (Module 04), which also
works through proxies that eat control frames.

### Close codes you'll actually see

| Code | Meaning |
|------|---------|
| 1000 | Normal |
| 1001 | Going away (server shutting down, page navigating) |
| **1006** | **Abnormal — no close frame arrived.** You never *send* this; it's what a client reports when TCP just died. The most common code in production, and it tells you almost nothing. |
| 1009 | Message too big |
| 1011 | Server error |
| 4000–4999 | **Application-defined — use these.** "token expired", "kicked", "rate limited", "server draining, reconnect in N ms" |

> Designing your 4xxx codes is real protocol work. A client that receives 4001
> ("token expired") can refresh and reconnect immediately; a client that receives
> 1006 has to guess. Module 21 defines Pulse's full set.

---

## Option 5 — WebTransport (HTTP/3 / QUIC)

The newest option, and worth knowing about even though you won't build on it here.

WebSocket rides on TCP, which means **head-of-line blocking**: one lost packet
stalls every message behind it, even unrelated ones. On a lossy mobile network
that's a real latency source.

WebTransport runs over QUIC and gives you:
- **Multiple independent streams** on one connection — a lost packet on the
  typing-indicator stream doesn't stall messages.
- **Unreliable datagrams** — perfect for presence and typing, where a lost
  update is superseded a second later anyway.
- Connection migration: a phone switching Wi-Fi → cellular keeps the connection.

**Why not use it for Pulse:** browser support is still uneven, server-side
support in the JVM ecosystem is immature, and many corporate networks block
UDP/443 outright. It's the right thing to watch, not yet the right thing to bet
a course on. Module 03's challenge has you reason about which Pulse traffic
*would* move to datagrams if it were available — that's the useful exercise.

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
| HTTP/2 multiplexed | Yes | Yes | **Yes** | No* | n/a (HTTP/3) |
| Browser support | 100% | 100% | 98% | 98% | ~70% |

\* RFC 8441 defines WebSocket over HTTP/2, but support is inconsistent enough
that it's not something to rely on.

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
10–30 seconds. They keep the connection non-idle at every layer, and — critically
— they let you *detect* the dead ones. Without heartbeats, both sides think a
NAT-evicted connection is fine, forever.

```yaml
# Module 04 wires this
heart-beat: 10000,10000     # STOMP: EOL byte every 10s in each direction
```

---

## The decision, for Pulse

**WebSocket + STOMP, with SSE as a documented fallback.**

- Message rate and bidirectional chatter (typing, receipts, acks) justify the
  framing efficiency.
- STOMP gives us subscriptions, destinations, and acks without inventing a
  protocol (Module 05 shows how much work that saves).
- SSE + POST remains the fallback for hostile networks — and by Module 10 the
  resume-cursor machinery is transport-independent, so switching transports
  doesn't change the delivery semantics.

We are **not** using SockJS. It was essential in 2015; today it adds a
significant complexity tax (three fallback transports to test, an extra URL
scheme, a session layer above the socket) for browsers that essentially no longer
exist. If you need a fallback, plain SSE is simpler and better.

---

## What's next

The lab has you speak all four protocols by hand — decoding WebSocket frames
byte by byte, watching an nginx timeout kill a socket, and measuring the actual
bytes-on-the-wire difference between polling, SSE, and WebSocket.

See you in [`lab.md`](./lab.md).
