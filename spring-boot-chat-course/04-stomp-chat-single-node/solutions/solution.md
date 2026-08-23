# Solutions — Module 04

---

## Task 1 — Close the `/topic` publish hole

### Prove it exists

```bash
printf 'CONNECT\naccept-version:1.2\nAuthorization:user:mallory\n\n\x00\n' \
        > /tmp/forge.stomp
printf 'SEND\ndestination:/topic/room.7\ncontent-type:application/json\n\n{"id":"forged","sender":"admin","body":"everyone is fired","ts":0}\x00\n' \
        >> /tmp/forge.stomp
cat /tmp/forge.stomp | websocat -n --text ws://localhost:8080/ws
```

**Expected — in every subscriber's client:**
```
{"id":"forged","sender":"admin","body":"everyone is fired","ts":0}
```

✅ Mallory published as "admin", with no controller involved. No validation, no
persistence, no rate limit, no audit trail. The `Principal` was never consulted
because **`/topic` goes straight to the broker**.

### Close it

```java
package com.pulse.ws;

import org.springframework.messaging.*;
import org.springframework.messaging.simp.stomp.*;
import org.springframework.messaging.support.*;
import org.springframework.stereotype.Component;

@Component
public class DestinationGuardInterceptor implements ChannelInterceptor {

    private static final java.util.Set<StompCommand> PUBLISHING =
            java.util.Set.of(StompCommand.SEND);

    @Override
    public Message<?> preSend(Message<?> message, MessageChannel channel) {
        var accessor = MessageHeaderAccessor.getAccessor(message, StompHeaderAccessor.class);
        if (accessor == null || accessor.getCommand() == null) return message;
        if (!PUBLISHING.contains(accessor.getCommand())) return message;

        String destination = accessor.getDestination();
        if (destination == null || !(destination.startsWith("/app/"))) {
            throw new IllegalArgumentException(
                    "clients may only SEND to /app/**, got: " + destination);
        }
        return message;
    }
}
```

Register it (order matters — after auth, so we know who to blame in the log):

```java
registration.interceptors(authInterceptor, destinationGuardInterceptor);
```

**Expected after the fix:**
```
ERROR
message:Failed to send message to ExecutorSubscribableChannel
java.lang.IllegalArgumentException: clients may only SEND to /app/**, got: /topic/room.7
```

✅ Subscribers receive nothing.

> **Why an interceptor and not `@MessageMapping` validation:** by the time your
> controller runs, a `/topic` send has already bypassed it. The check must happen
> on `clientInboundChannel`, before routing. This is the same reason
> authentication lives here.

**Belt and braces:** you can also stop trusting the client's claimed sender
entirely, which the lab's controller already does — it uses
`principal.getName()`, never a field from the payload. Both defenses matter; the
interceptor stops the frame, the controller stops the impersonation.

---

## Task 2 — Subscribe-time authorization, and the revocation gap

```java
@Component
public class SubscriptionAuthInterceptor implements ChannelInterceptor {

    private static final Pattern ROOM = Pattern.compile("^/topic/room\\.([^.]+)(\\.presence)?$");

    private final RoomMembershipService membership;

    @Override
    public Message<?> preSend(Message<?> message, MessageChannel channel) {
        var accessor = MessageHeaderAccessor.getAccessor(message, StompHeaderAccessor.class);
        if (accessor == null || !StompCommand.SUBSCRIBE.equals(accessor.getCommand()))
            return message;

        String destination = accessor.getDestination();
        if (destination == null) return message;

        // /user/** destinations are already session-scoped by Spring — safe.
        if (destination.startsWith("/user/")) return message;

        Matcher m = ROOM.matcher(destination);
        if (!m.matches())
            throw new IllegalArgumentException("unknown destination: " + destination);

        String roomId = m.group(1);
        String user = accessor.getUser().getName();
        if (!membership.isMember(user, roomId))
            throw new AccessDeniedException(user + " is not a member of " + roomId);

        return message;
    }
}
```

Test:
```bash
# alice is not in room.99
printf 'CONNECT\naccept-version:1.2\nAuthorization:user:alice\n\n\x00\nSUBSCRIBE\nid:s\ndestination:/topic/room.99\n\n\x00\n' \
  | websocat -n --text ws://localhost:8080/ws
```
**Expected:**
```
ERROR
message:...AccessDeniedException: alice is not a member of 99
```

### Why subscribe-time checking is necessary but not sufficient

**Because subscriptions are long-lived and permissions are not.**

The check runs **once**, at subscribe time. A user subscribed at 09:00 and
removed from the room at 09:05 keeps receiving every message until they
disconnect — potentially for hours. Removing someone from a private channel does
not, by itself, stop delivering that channel's messages to them.

This is a real and commonly-shipped vulnerability. The same class of bug affects
JWT expiry on long-lived sockets (Module 21).

### The missing half — revocation

Two mechanisms, and you want both:

**1. Actively evict on membership change.**

```java
@Service
public class RoomMembershipService {

    private final SessionRegistry registry;
    private final SimpMessagingTemplate template;
    private final SimpUserRegistry userRegistry;

    @Transactional
    public void removeMember(String userId, String roomId) {
        repository.delete(userId, roomId);
        evictSubscriptions(userId, roomId);
    }

    private void evictSubscriptions(String userId, String roomId) {
        var user = userRegistry.getUser(userId);
        if (user == null) return;                      // not connected here

        for (SimpSession session : user.getSessions()) {
            for (SimpSubscription sub : session.getSubscriptions()) {
                if (("/topic/room." + roomId).equals(sub.getDestination())) {
                    // Tell the client to unsubscribe, and tell OUR broker to forget it.
                    template.convertAndSendToUser(userId, "/queue/control",
                            new Control("unsubscribe", "/topic/room." + roomId, "removed_from_room"));
                    unsubscribeServerSide(session.getId(), sub.getId());
                }
            }
        }
    }

    /** Synthesize an UNSUBSCRIBE frame so the broker drops the registration
        even if the client ignores our control message. */
    private void unsubscribeServerSide(String sessionId, String subscriptionId) {
        var accessor = StompHeaderAccessor.create(StompCommand.UNSUBSCRIBE);
        accessor.setSessionId(sessionId);
        accessor.setSubscriptionId(subscriptionId);
        accessor.setLeaveMutable(true);
        clientInboundChannel.send(
                MessageBuilder.createMessage(new byte[0], accessor.getMessageHeaders()));
    }
}
```

> Telling the client to unsubscribe is **not enough on its own** — a hostile
> client simply won't. The synthesized `UNSUBSCRIBE` on `clientInboundChannel` is
> what actually removes the entry from the broker's map. That's the enforcing
> half.

**2. Re-check at delivery time for sensitive rooms.**

```java
// In an outbound ChannelInterceptor, for rooms flagged private:
if (room.isPrivate() && !membership.isMemberCached(user, roomId)) {
    return null;      // returning null from preSend DROPS the message
}
```

This costs a cache lookup on every delivered message — real money at fan-out
scale. Apply it selectively to private/sensitive rooms, and rely on eviction for
the rest.

> ⚠️ **The multi-instance version of this problem is worse.** `SimpUserRegistry`
> only knows about sessions on *this* JVM. A user connected to instance B is
> invisible to instance A's eviction code. In Module 07 you'll publish revocation
> events over Redis so every instance evicts. Note this as a Phase 2 requirement.

---

## Task 3 — The slow consumer

### The attacking client

```java
// SlowConsumer.java — connects, subscribes, then NEVER reads.
public class SlowConsumer {
    public static void main(String[] args) throws Exception {
        var s = new Socket("localhost", 8080);
        s.setReceiveBufferSize(1024);            // tiny receive window
        var out = s.getOutputStream();

        out.write(handshake().getBytes());       // raw WS handshake (see Module 03)
        Thread.sleep(200);
        out.write(wsFrame("CONNECT\naccept-version:1.2\nAuthorization:user:slowpoke\n\n\0"));
        Thread.sleep(200);
        out.write(wsFrame("SUBSCRIBE\nid:s0\ndestination:/topic/room.7\n\n\0"));
        out.flush();

        System.out.println("subscribed; now sleeping forever without reading");
        Thread.sleep(Long.MAX_VALUE);            // <-- never calls recv()
    }
}
```

### Without limits

```java
// registration.setSendBufferSizeLimit(...) REMOVED
```
```bash
java SlowConsumer.java &
for i in $(seq 1 10000); do ./code/publish.sh room.7 "flood-$i"; done
watch -n1 'curl -s localhost:8080/actuator/metrics/jvm.memory.used | jq ".measurements[0].value"'
```

**Expected:**
```
heap after 1,000 msgs:   142 MB
heap after 5,000 msgs:   688 MB
heap after 9,400 msgs:  1.9 GB
java.lang.OutOfMemoryError: Java heap space
```

The messages pile up in the session's outbound buffer because the TCP send
buffer is full and the client never drains it. **One client took down the server
for everyone.**

### With limits

```java
registration.setSendBufferSizeLimit(512 * 1024)
            .setSendTimeLimit(20 * 1000);
```

**Expected:**
```
heap stays flat at ~180 MB
```
and in the log, at roughly **message 1,100** (512 KB / ~460 bytes per message):
```
WARN o.s.w.s.m.SubProtocolWebSocketHandler : Closing session due to exception for
  ConcurrentWebSocketSessionDecorator[session=StandardWebSocketSession[id=7f3a, uri=/ws]]
org.springframework.web.socket.handler.SessionLimitExceededException:
  Buffer size 524891 exceeded the allowed limit 524288
```

✅ Session closed, everyone else unaffected, heap flat.

| | Without limits | With limits |
|---|---------------|-------------|
| Heap at 10k messages | OOM at ~9,400 | flat, ~180 MB |
| Session closed at | never | ~1,100 messages |
| Other clients | **all dead** | unaffected |
| Exception | `OutOfMemoryError` | `SessionLimitExceededException` |

> **`SessionLimitExceededException` is not an error to suppress.** It's the
> safety valve reporting that it worked. If you see it constantly, the question
> is "why are these clients slow?" (mobile networks? a fan-out storm? a client
> bug?) — not "how do I raise the limit?"

**Sizing guidance:** buffer limit should be roughly
`peak_burst_messages × average_message_size`. For Pulse: a 5,000-member room
burst of 20 messages at ~500 bytes = 10 KB, so 512 KB gives ~50× headroom. Set
`setSendTimeLimit` to well under your heartbeat timeout so a stalled write is
detected before the heartbeat gives up.

---

## Task 4 — The outbound channel ceiling

```bash
k6 run --vus 200 --duration 2m code/fanout.js      # 200 subscribers, 1 room
watch -n1 'curl -s localhost:8080/actuator/prometheus | grep stomp_channel_queued'
```

Reference results (8-core, `corePoolSize=16`, 200-member room):

| Inbound msg/s | Outbound msg/s | `stomp_channel_queued{outbound}` | p99 |
|---------------|----------------|----------------------------------|-----|
| 10 | 2,000 | 0 | 8 ms |
| 50 | 10,000 | 0 (spikes to ~40) | 22 ms |
| 100 | 20,000 | **persistently 200–900** | 180 ms |
| 150 | 30,000 | 4,000 and climbing | 1,400 ms |
| 200 | 40,000 | unbounded growth | OOM in ~6 min |

**Saturation point: ~90 inbound msg/s into a 200-member room ≈ 18,000 outbound
msg/s** on this hardware. Above that the queue never drains.

### With `queueCapacity(100)`

**Expected at 150 msg/s:**
```
org.springframework.core.task.TaskRejectedException: Executor
[java.util.concurrent.ThreadPoolExecutor@3f2a...[Running, pool size = 64,
active threads = 64, queued tasks = 100, completed tasks = 1284933]]
did not accept task
```

Messages are dropped, the exception is logged, and **the server stays up**.

### Why a bounded queue that throws beats an unbounded one that doesn't

1. **Failure becomes visible and immediate.** `TaskRejectedException` at message
   N is a diagnosable event with a timestamp and a stack trace. An unbounded
   queue produces `OutOfMemoryError` six minutes later, in an unrelated thread,
   after the JVM has spent two minutes in GC death-spiral — by which time the
   cause is untraceable.
2. **The blast radius is bounded.** Rejecting message N affects message N. An
   OOM kills every connection on the node, and those clients then reconnect to
   your other nodes, which are also near saturation. That's how one hot room
   takes down a cluster.
3. **It's a backpressure signal you can act on.** Rejections are a metric. Alert
   on them, autoscale on them, shed load on them. Heap growth is a metric too,
   but by the time it's alarming you have seconds, not minutes.
4. **You get to choose the policy.** `CallerRunsPolicy` throttles the producer
   naturally (the inbound thread does the delivery work, so it stops accepting
   new inbound frames). `DiscardOldestPolicy` is defensible for presence.
   `AbortPolicy` is right for messages. An unbounded queue makes that choice for
   you, badly.

**The general principle:** *every queue in a distributed system must be bounded
somewhere.* If you can't name the bound, it's your heap, and your heap is a very
expensive place to discover the number.

---

## Task 5 — The fan-out cost curve

Reference, fixed 10 msg/s inbound, p99 send→last-delivery:

| Room size | Outbound msg/s | p50 | p99 | p99.9 |
|-----------|----------------|-----|-----|-------|
| 10 | 100 | 2 ms | 4 ms | 7 ms |
| 100 | 1,000 | 3 ms | 11 ms | 24 ms |
| 1,000 | 10,000 | 9 ms | 88 ms | 310 ms |
| 5,000 | 50,000 | 61 ms | **1,240 ms** | 4,100 ms |

```
p99  │                                              ●  (5000)
1200 │                                            ╱
     │                                          ╱
     │                                        ╱
 300 │                                    ╱
     │                        ●  (1000) ╱
  90 │                    ╱
     │        ● (100)  ╱
  10 │  ●  ╱
     └──────┬──────┬───────┬────────┬─────  room size (log)
           10     100     1k       5k
```

### What changes shape, and why

The curve is **worse than linear** — 50× the room size gives 110× the p99. Three
compounding effects:

1. **Serialization is per-recipient, not per-message.** Spring converts the
   payload once but writes and frames it once *per session*. That's 5,000
   `ByteBuffer` allocations and 5,000 socket writes for one logical message.
   Linear so far.
2. **Thread pool saturation adds queueing.** Once outbound tasks arrive faster
   than 64 threads can drain them, each message waits behind a growing queue.
   Queueing delay grows with utilization as roughly `1/(1−ρ)` — this is the
   superlinear term, and it's why the knee is so sharp.
3. **GC pressure.** 50,000 short-lived buffers per second promotes garbage into
   the old generation, and the resulting GC pauses land in the tail. `p99.9` of
   4.1 s is mostly GC.

Plus a fourth effect the p99 hides: **the last recipient is always the worst
one.** Fan-out is sequential within a message, so recipient 5,000 waits for
4,999 writes. Measuring "the user's experience" means measuring that last one.

### Where the 200 ms p99 budget breaks

Between **1,000 and 2,000 members**. Interpolating: ~1,400 members at 10 msg/s.

But that number is a *product* — `room_size × message_rate`. The same node meets
budget with a 5,000-member room at 2 msg/s, or a 500-member room at 30 msg/s.
**Capacity is outbound messages/second (~18,000 here), not room size.**

That single reframing is what Module 06 formalizes and Module 13 attacks with
sharded subscriptions.

---

## Task 6 (stretch) — RabbitMQ STOMP relay

```yaml
# docker-compose
  rabbitmq:
    image: rabbitmq:3.13-management
    ports: [ "5672:5672", "61613:61613", "15672:15672" ]
    command: >
      bash -c "rabbitmq-plugins enable --offline rabbitmq_stomp rabbitmq_management &&
               rabbitmq-server"
```

```java
registry.enableStompBrokerRelay("/topic", "/queue")
        .setRelayHost("localhost")
        .setRelayPort(61613)
        .setClientLogin("guest").setClientPasscode("guest")
        .setSystemLogin("guest").setSystemPasscode("guest")
        .setSystemHeartbeatSendInterval(10_000)
        .setSystemHeartbeatReceiveInterval(10_000);
```

Redo Part I. **Expected: it works.** Alice on 8080 and bob on 8081 see each
other, because both instances forward to the same external broker.

### What you gained, what you gave up, and why we build on Redis anyway

> **Gained.** Cross-instance fan-out for a configuration change and zero
> application code — the single problem that ended Phase 1, solved in ten lines.
> RabbitMQ also brings durable queues, real STOMP `ACK`/`NACK` semantics
> (which the simple broker silently ignores), dead-letter exchanges, per-queue
> TTLs, and a management UI that shows exactly which destinations exist and how
> deep they are. For many products this is the correct answer and the course
> could stop here.
>
> **Given up.** Every message now makes two extra network hops (app → broker →
> app) instead of one process-local map lookup — measurably ~1–3 ms of added p50
> and a hard dependency on a component that is now in the critical path of every
> single message. You also inherit RabbitMQ's operational model: Erlang, its own
> clustering semantics, its own partition-handling policy (`pause_minority` vs
> `autoheal`, and the well-documented pain of getting that wrong), and mirrored
> or quorum queues whose failover behaviour you must now understand as deeply as
> you understand your own code.
>
> **Why Redis instead.** Three reasons, and only the third is really about
> RabbitMQ. First, **Pulse already needs Redis** for presence, rate limiting,
> unread counts, and dedup — adding a second stateful system earns its keep only
> if it does something Redis can't. Second, **Redis Streams give us the delivery
> semantics we actually want** with mechanics we control explicitly: consumer
> groups, a visible pending-entries list, and `XAUTOCLAIM` for recovery, all
> inspectable with `redis-cli` rather than hidden inside a broker's queue
> implementation. Third — and this is the pedagogical reason — **the relay hides
> the problem instead of teaching it.** "Enable the relay" doesn't tell you what
> at-least-once costs, why a reconnect loses messages, or what a consumer group
> is for. Building the backbone means that when you *do* choose a managed broker
> in production, you'll know exactly what it's doing for you.
>
> **When to choose the relay in real life:** you already run RabbitMQ, your team
> knows it, your fan-out fits in one broker, and you'd rather buy durability than
> build it. That's a good trade and you should take it.
