# Cheatsheet — WebSocket & STOMP

---

## The WebSocket handshake

**Client request:**
```http
GET /ws HTTP/1.1
Host: chat.example.com
Upgrade: websocket
Connection: Upgrade
Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==
Sec-WebSocket-Version: 13
Origin: https://chat.example.com
Sec-WebSocket-Protocol: v12.stomp
```

**Server response:**
```http
HTTP/1.1 101 Switching Protocols
Upgrade: websocket
Connection: Upgrade
Sec-WebSocket-Accept: s3pPLMBiTxaQ9kYGzzhZRbK+xOo=
Sec-WebSocket-Protocol: v12.stomp
```

`Sec-WebSocket-Accept` = `base64(sha1(key + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"))`.
The GUID is a constant from the RFC. It proves the server understood the
handshake — it is **not** authentication.

> **`Origin` is your only browser-side defense.** CORS does not apply to
> WebSocket. Validate it server-side or you have a CSWSH hole.

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

**Minimum frame sizes:** a server→client text frame costs **2 bytes** of
overhead; a client→server one costs **6** (2 + 4-byte mask). At 100k
connections × 1 heartbeat/30 s that overhead is real but small — your JSON
payload dominates.

### Close codes worth knowing

| Code | Meaning |
|------|---------|
| 1000 | Normal closure |
| 1001 | Going away (server shutting down / page navigating) |
| 1006 | **Abnormal** — no close frame was received. You never send this; it's what a client library reports when the TCP connection just died. The most common code you'll see in production. |
| 1009 | Message too big |
| 1011 | Internal server error |
| 4000–4999 | Application-defined. Use these for "token expired", "kicked", "rate limited". |

---

## STOMP 1.2 frames

```
COMMAND
header1:value1
header2:value2
<blank line>
Body^@
```

`^@` is a NULL octet (`\0`) terminating the frame.

### Client → server

| Command | Purpose | Key headers |
|---------|---------|-------------|
| `CONNECT` / `STOMP` | Open a session | `accept-version`, `host`, `heart-beat`, `login`, `passcode` |
| `SEND` | Publish | `destination`, `content-type`, `receipt` |
| `SUBSCRIBE` | Listen | `destination`, `id`, `ack` |
| `UNSUBSCRIBE` | Stop listening | `id` |
| `ACK` / `NACK` | Confirm/reject a message | `id` |
| `BEGIN`/`COMMIT`/`ABORT` | Transactions | `transaction` |
| `DISCONNECT` | Graceful close | `receipt` |

### Server → client

| Command | Purpose | Key headers |
|---------|---------|-------------|
| `CONNECTED` | Session established | `version`, `heart-beat`, `session` |
| `MESSAGE` | Delivery | `destination`, `message-id`, `subscription` |
| `RECEIPT` | Confirms a frame with a `receipt` header | `receipt-id` |
| `ERROR` | Something went wrong; connection closes after | `message` |

### `ack` modes on SUBSCRIBE

| Mode | Behaviour |
|------|-----------|
| `auto` (default) | Server assumes delivery succeeded the moment it writes the frame. Fire-and-forget. |
| `client` | Client must `ACK`; an `ACK` acknowledges that message **and all before it** on that subscription. |
| `client-individual` | Client must `ACK` each message separately. |

> Spring's **simple broker ignores `ack` modes**. If you need real acks with the
> simple broker, you implement them at the application level — which is exactly
> what Module 10 does.

### Heart-beating

`heart-beat:<cx>,<cy>` where `cx` = "I can send every ms", `cy` = "I want to
receive every ms". The negotiated outgoing interval is
`max(sender's cx, receiver's cy)`; `0` on either side disables that direction.

```
CONNECT      heart-beat:10000,10000
CONNECTED    heart-beat:10000,10000
```
→ Both sides send an EOL byte (`\n`) at least every 10 s.

---

## Spring annotations and types

| Annotation / type | Purpose |
|-------------------|---------|
| `@EnableWebSocketMessageBroker` | Turns on STOMP-over-WebSocket support |
| `WebSocketMessageBrokerConfigurer` | The config hook: register endpoints, configure the broker, tune channels |
| `registerStompEndpoints(r)` | `r.addEndpoint("/ws").setAllowedOrigins(...)` |
| `configureMessageBroker(r)` | `r.enableSimpleBroker("/topic","/queue")`, `r.setApplicationDestinationPrefixes("/app")`, `r.setUserDestinationPrefix("/user")` |
| `@MessageMapping("/room/{id}")` | Handle an inbound `SEND` to `/app/room/{id}` |
| `@SubscribeMapping` | Handle a `SUBSCRIBE` and return a one-shot reply (not a broadcast) |
| `@SendTo("/topic/room.{id}")` | Broadcast the return value |
| `@SendToUser("/queue/replies")` | Send only to the calling user's session(s) |
| `@DestinationVariable` | Bind a `{placeholder}` from the destination |
| `@Payload`, `@Header`, `@Headers` | Bind body and headers |
| `SimpMessagingTemplate` | Publish from anywhere: `convertAndSend(dest, payload)`, `convertAndSendToUser(user, dest, payload)` |
| `SimpUserRegistry` | Which users are connected **to this instance** (not cluster-wide — that's Module 11) |
| `ChannelInterceptor` | Intercept frames on `clientInboundChannel` — where WebSocket auth goes |
| `SessionConnectedEvent` / `SessionDisconnectEvent` | Lifecycle hooks for presence |

### Destination prefix conventions

```
/app/...     → routed to @MessageMapping in your code
/topic/...   → broadcast to all subscribers
/queue/...   → point-to-point
/user/...    → resolved per-session by UserDestinationMessageHandler
```

`convertAndSendToUser("alice", "/queue/replies", p)` actually publishes to
`/queue/replies-user<sessionId>` for each of alice's sessions.

### The three channels (and their thread pools)

```
   client                                                 client
     │  SEND                                                ▲ MESSAGE
     ▼                                                      │
┌──────────────────┐    ┌────────────┐    ┌──────────────────────┐
│clientInboundChannel│─▶│  @Message  │─▶│ clientOutboundChannel │
│  (default 1× core)│   │  Mapping   │   │   (default 1× core)   │
└──────────────────┘    └─────┬──────┘    └──────────▲───────────┘
                              │ brokerChannel        │
                              ▼                      │
                        ┌──────────────┐             │
                        │ SimpleBroker │─────────────┘
                        └──────────────┘
```

```java
@Override
public void configureClientInboundChannel(ChannelRegistration r) {
    r.taskExecutor().corePoolSize(16).maxPoolSize(32).queueCapacity(1000);
}
```

> Each channel has an **unbounded-by-default queue**. Under a fan-out storm, the
> queue is where your heap goes. Module 06 makes this happen on purpose.

---

## Transport limits to tune

```java
@Override
public void configureWebSocketTransport(WebSocketTransportRegistration r) {
    r.setMessageSizeLimit(64 * 1024);       // max inbound message
    r.setSendBufferSizeLimit(512 * 1024);   // per-session outbound buffer
    r.setSendTimeLimit(20 * 1000);          // slow-consumer kill switch
}
```

`setSendBufferSizeLimit` + `setSendTimeLimit` are your **slow-consumer
protection**. Without them one phone on a bad train connection can hold
megabytes of your heap.

---

## Manual poking

```bash
# raw connect
websocat ws://localhost:8080/ws

# STOMP by hand (^@ is Ctrl-V Ctrl-@ in most terminals; \x00 with -b)
websocat -b ws://localhost:8080/ws
CONNECT
accept-version:1.2
host:localhost

<NUL>
```

Easier: use the `stomp.py`/Node scripts in `06-load-testing-harness/code/`.

```bash
# see the handshake only
curl -i -N -H "Connection: Upgrade" -H "Upgrade: websocket" \
     -H "Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==" \
     -H "Sec-WebSocket-Version: 13" \
     http://localhost:8080/ws
```
**Expected:** `HTTP/1.1 101 Switching Protocols`.

---

## Transport decision table

| Need | Use |
|------|-----|
| Server → client only, HTTP-friendly, auto-reconnect | **SSE** |
| Bidirectional, low latency, high message rate | **WebSocket** |
| Bidirectional but must cross a hostile proxy | WebSocket + **SockJS** fallback |
| Many independent streams, mobile network churn | **WebTransport** (HTTP/3) — watch, don't bet yet |
| Occasional updates, tiny scale, no infra | **Polling** — genuinely fine, stop apologizing for it |
