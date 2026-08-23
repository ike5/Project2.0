# Module 04 — STOMP Chat on a Single Node

**Goal:** Build a working chat server — and understand exactly what Spring's
"simple broker" is doing in memory, because its limitations are the reason
Phase 2 exists.

⏱️ ~5 hours · **Prerequisites:** Modules 00–03.

---

## Why not just use raw WebSocket?

You built a raw WebSocket echo handler in Module 03. It worked. So why add a
protocol on top?

Because the moment you have more than one conversation, you need to answer:

- How does a client say "I'm interested in room 7, but not room 8"?
- How does the server address a message to *some* connections and not others?
- How does a client acknowledge a message?
- How do you send an error that isn't a disconnect?
- How do you multiplex several logical channels over one socket?

You can invent answers to all five. Everyone does — usually a JSON envelope
with a `type` field. That's a perfectly reasonable choice, and it's what many
production systems ship. But you will re-derive subscriptions, destinations,
acks, receipts, and heartbeats, and you will get the heartbeat negotiation wrong
the first time.

**STOMP is those answers, already written down**, in a spec small enough to read
in fifteen minutes.

---

## STOMP in one page

STOMP frames ride *inside* WebSocket text frames. A frame is:

```
COMMAND
header:value
header:value
<blank line>
body^@
```

where `^@` is a NUL byte. That's the entire wire format.

### The conversation

```
Client                                              Server
  │                                                   │
  │ CONNECT                                           │
  │ accept-version:1.2                                │
  │ heart-beat:10000,10000                            │
  ├──────────────────────────────────────────────────▶│
  │                                        CONNECTED  │
  │                                        version:1.2│
  │◀──────────────────────────────────────────────────┤
  │                                                   │
  │ SUBSCRIBE                                         │
  │ id:sub-0                                          │
  │ destination:/topic/room.7                         │
  ├──────────────────────────────────────────────────▶│
  │                                                   │
  │ SEND                                              │
  │ destination:/app/room.7                           │
  │ {"body":"hello"}                                  │
  ├──────────────────────────────────────────────────▶│
  │                                                   │  → @MessageMapping
  │                                                   │  → broker
  │                                          MESSAGE  │
  │                              destination:/topic/room.7
  │                              subscription:sub-0   │
  │◀──────────────────────────────────────────────────┤
```

### Destinations are just strings

`/topic/room.7` means nothing intrinsically. The broker decides. Spring's
conventions:

| Prefix | Meaning |
|--------|---------|
| `/app/**` | Routed to **your** `@MessageMapping` methods |
| `/topic/**` | Broadcast — every subscriber gets it |
| `/queue/**` | Point-to-point |
| `/user/**` | Resolved per-user by `UserDestinationMessageHandler` |

The `/app` vs `/topic` split is important and often confused:

```
SEND → /app/room.7      goes to YOUR CODE (a @MessageMapping method)
SEND → /topic/room.7    goes DIRECTLY TO THE BROKER, bypassing your code
```

If you let clients publish straight to `/topic/**`, you have no place to
validate, persist, rate-limit, or authorize. **Clients send to `/app`; only the
server publishes to `/topic`.** Module 21 makes this a hard rule with a
configuration to enforce it.

---

## What the simple broker actually is

```java
registry.enableSimpleBroker("/topic", "/queue");
```

This registers a `SimpleBrokerMessageHandler`. Strip away the abstraction and
it's approximately:

```java
class SimpleBroker {
    // destination -> (sessionId -> subscriptionId)
    private final Map<String, Map<String, String>> subscriptions = new ConcurrentHashMap<>();

    void handleSubscribe(String sessionId, String subId, String destination) {
        subscriptions.computeIfAbsent(destination, k -> new ConcurrentHashMap<>())
                     .put(sessionId, subId);
    }

    void handleMessage(String destination, Message<?> message) {
        subscriptions.getOrDefault(destination, Map.of()).forEach((sessionId, subId) ->
            clientOutboundChannel.send(addressTo(sessionId, subId, message)));
    }
}
```

**A `ConcurrentHashMap` in your JVM's heap.** That's it.

Which tells you everything about its limits:

| Property | Consequence |
|----------|-------------|
| In-memory | Restart = every subscription gone |
| Per-JVM | **Instance A knows nothing about instance B's subscribers** |
| No persistence | A message published while a client reconnects is gone |
| No acks | `ack:client` on SUBSCRIBE is *ignored* |
| No flow control beyond the channel queues | A slow consumer backs up in your heap |

The second row is the one that ends Phase 1. Two users in the same room, on two
different instances, cannot see each other. That's Module 07.

> **This is not a criticism of the simple broker.** It is fast, dependency-free,
> and correct for a single instance. Knowing precisely what it does is what lets
> you decide when you've outgrown it — which is the entire skill this course is
> teaching.

---

## The three channels (and where your latency lives)

Every frame crosses up to three `MessageChannel`s, each with **its own thread
pool and its own queue**:

```
 client
   │ SEND
   ▼
┌─────────────────────┐  default: coreSize = cores, UNBOUNDED queue
│ clientInboundChannel│
└──────────┬──────────┘
           │
    ┌──────▼───────┐
    │@MessageMapping│  ← your code runs here
    └──────┬───────┘
           │ brokerChannel
    ┌──────▼───────┐
    │ SimpleBroker │  ← subscription lookup
    └──────┬───────┘
           │
┌──────────▼──────────┐  default: coreSize = cores, UNBOUNDED queue
│clientOutboundChannel│
└──────────┬──────────┘
           │ MESSAGE
           ▼
        clients
```

Three things to internalize now, because Module 06 will make each of them hurt:

1. **The queues are unbounded by default.** Under a fan-out storm, your heap is
   where the backlog goes. There is no backpressure; there is an `OutOfMemoryError`.
2. **`clientOutboundChannel` is where fan-out amplification lands.** One inbound
   message to a 500-member room becomes 500 tasks on that channel.
3. **`spring.threads.virtual.enabled` does not touch these.** They use
   `ThreadPoolTaskExecutor`, configured separately. A lot of people set that flag
   and believe their WebSocket path is virtual-threaded. It isn't.

```java
@Override
public void configureClientInboundChannel(ChannelRegistration r) {
    r.taskExecutor().corePoolSize(16).maxPoolSize(32).queueCapacity(1000);
}
```

`queueCapacity` is the single most important line. A bounded queue that **rejects**
is vastly better than an unbounded queue that OOMs — you get a fast, visible
failure instead of a slow, invisible one.

---

## Slow consumers

One phone on a bad train connection can take down your server. Here's how:

The server writes to a socket. The socket's send buffer is full because the
client isn't reading. The write can't complete, so Spring buffers the message in
`WebSocketSession`'s outbound buffer. More messages arrive. The buffer grows.

```java
@Override
public void configureWebSocketTransport(WebSocketTransportRegistration r) {
    r.setSendBufferSizeLimit(512 * 1024);   // per session; then close it
    r.setSendTimeLimit(20 * 1000);          // slowest acceptable write
    r.setMessageSizeLimit(64 * 1024);       // largest inbound message
}
```

When a session exceeds either limit, Spring closes it. **That's correct
behaviour, not a bug** — you are choosing to lose one bad client rather than
your heap. When you see `SessionLimitExceededException` in Module 06's logs,
recognize it as the safety valve working.

---

## Authenticating a WebSocket

This is genuinely awkward and worth understanding now.

The browser's `new WebSocket(url)` API **cannot set headers**. No
`Authorization: Bearer`. Cookies are sent, but not on cross-origin connections
with modern `SameSite` defaults. So the usual options are:

| Approach | Tradeoff |
|----------|----------|
| Query param `?token=...` | Simple; **leaks into access logs and browser history**. Use a short-lived single-use ticket, not your session JWT. |
| `Sec-WebSocket-Protocol` header | The one header the browser *will* set. Hacky (it's a subprotocol field), but it works and stays out of logs. |
| Cookie | Works same-origin; needs `SameSite=None; Secure` cross-origin, and then you must handle CSWSH. |
| **Auth in the STOMP `CONNECT` frame** | Post-handshake, so the token never touches the URL. Costs one round trip and means the socket exists briefly unauthenticated. |

Pulse uses the **STOMP `CONNECT` frame** approach, via a `ChannelInterceptor`:

```java
@Component
public class AuthChannelInterceptor implements ChannelInterceptor {

    @Override
    public Message<?> preSend(Message<?> message, MessageChannel channel) {
        StompHeaderAccessor accessor =
                MessageHeaderAccessor.getAccessor(message, StompHeaderAccessor.class);

        if (accessor != null && StompCommand.CONNECT.equals(accessor.getCommand())) {
            String token = accessor.getFirstNativeHeader("Authorization");
            Principal principal = tokenService.verify(token);   // throws to reject
            accessor.setUser(principal);
        }
        return message;
    }
}
```

`accessor.setUser(principal)` attaches the identity to the **session**, so every
later frame on that socket has it — you authenticate once, not per message.

> **The problem nobody mentions:** the token expires; the socket doesn't. A
> socket open for eight hours outlives a 15-minute JWT. Module 21 solves this
> with an in-band re-auth frame. For now, note it as a known gap.

---

## Heartbeats

```java
registry.enableSimpleBroker("/topic", "/queue")
        .setHeartbeatValue(new long[]{10000, 10000})
        .setTaskScheduler(heartbeatScheduler());     // REQUIRED, or heartbeats silently do nothing
```

⚠️ **`setTaskScheduler` is not optional.** Omit it and Spring logs a warning you
won't read, and heartbeats are disabled. This has cost many people an afternoon.

The negotiation: `heart-beat:<cx>,<cy>` where `cx` = "I can send every N ms" and
`cy` = "I want to receive every N ms". The actual interval each way is
`max(sender's cx, receiver's cy)`; `0` disables that direction.

Module 03 proved why you need these: proxies and NAT gateways evict idle
connections silently, and without heartbeats neither end finds out.

---

## What's next

The lab builds the whole thing: STOMP config, a room-scoped chat, presence
events, a browser client, and then a deliberate demonstration that two server
instances cannot see each other's users.

See you in [`lab.md`](./lab.md).
