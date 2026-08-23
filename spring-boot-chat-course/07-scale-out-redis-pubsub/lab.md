# Lab 07 — The Redis Backplane, and Its Cost

**You'll:** build the Pub/Sub backplane, prove cross-instance chat works,
measure the latency the Redis hop adds, put nginx in front with sticky sessions,
and then **make it lose messages on purpose** and count them.

⏱️ ~100 min. Work in `spring-boot-chat-course/apps/pulse`.

---

## Part A — The relay

Two halves: publish local sends to Redis, and re-broadcast anything Redis
delivers to the local broker.

`src/main/java/com/pulse/fanout/RedisFanout.java`:

```java
package com.pulse.fanout;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.pulse.protocol.Envelope;
import io.micrometer.core.instrument.Counter;
import io.micrometer.core.instrument.MeterRegistry;
import org.springframework.data.redis.connection.MessageListener;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.messaging.simp.SimpMessagingTemplate;
import org.springframework.stereotype.Component;

@Component
public class RedisFanout implements MessageListener {

    /** Identifies THIS instance, so we can drop our own echo. */
    private final String nodeId;

    private final StringRedisTemplate redis;
    private final SimpMessagingTemplate broker;
    private final ObjectMapper json;
    private final Counter published, receivedRemote, droppedSelf;

    public RedisFanout(StringRedisTemplate redis, SimpMessagingTemplate broker,
                       ObjectMapper json, MeterRegistry metrics,
                       @Value("${pulse.node-id}") String nodeId) {
        this.redis = redis;
        this.broker = broker;
        this.json = json;
        this.nodeId = nodeId;
        this.published      = Counter.builder("fanout.published").register(metrics);
        this.receivedRemote = Counter.builder("fanout.received.remote").register(metrics);
        this.droppedSelf    = Counter.builder("fanout.dropped.self").register(metrics);
    }

    /** Called by ChatController instead of template.convertAndSend(). */
    public void publish(String roomId, Envelope envelope) {
        try {
            var wrapper = new Wrapper(nodeId, envelope);
            redis.convertAndSend(channel(roomId), json.writeValueAsString(wrapper));
            published.increment();
        } catch (Exception e) {
            throw new FanoutException("failed to publish to room " + roomId, e);
        }
    }

    /** Called by RedisMessageListenerContainer for every message on a subscribed channel. */
    @Override
    public void onMessage(org.springframework.data.redis.connection.Message message, byte[] pattern) {
        try {
            var wrapper = json.readValue(message.getBody(), Wrapper.class);

            // We receive our own publishes too. Deliver them locally exactly once:
            // ChatController already handed this to the local broker before publishing.
            if (nodeId.equals(wrapper.origin())) {
                droppedSelf.increment();
                return;
            }

            receivedRemote.increment();
            String roomId = wrapper.envelope().room();
            broker.convertAndSend("/topic/room." + roomId, wrapper.envelope());

        } catch (Exception e) {
            // A poison message must NOT kill the listener thread — that would
            // silently stop all fan-out on this node.
            log.error("dropping malformed fanout message", e);
        }
    }

    public static String channel(String roomId) { return "pulse.room." + roomId; }

    public record Wrapper(String origin, Envelope envelope) {}
}
```

> **The `origin` field matters.** Redis delivers a publish back to the publishing
> instance too. Without the check you'd either double-deliver locally, or have to
> not deliver locally at all and pay a Redis round trip for same-node recipients
> (which for a well-balanced cluster is most of them). Dropping the echo is the
> cheap correct answer.

---

## Part B — Subscribe only to rooms we care about

Subscribing every instance to every room is the amplification problem from the
README. Subscribe lazily, on first local subscriber; unsubscribe on last.

`src/main/java/com/pulse/fanout/RoomSubscriptionManager.java`:

```java
package com.pulse.fanout;

import org.springframework.data.redis.listener.ChannelTopic;
import org.springframework.data.redis.listener.RedisMessageListenerContainer;
import org.springframework.stereotype.Component;

import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicInteger;

@Component
public class RoomSubscriptionManager {

    private final RedisMessageListenerContainer container;
    private final RedisFanout listener;

    /** roomId -> how many LOCAL sessions are subscribed. */
    private final Map<String, AtomicInteger> localSubscribers = new ConcurrentHashMap<>();

    public void roomJoined(String roomId) {
        // compute() so the count check and the subscribe are atomic together —
        // otherwise two joins can both see 0 and both subscribe.
        localSubscribers.compute(roomId, (id, count) -> {
            if (count == null) {
                container.addMessageListener(listener, new ChannelTopic(RedisFanout.channel(id)));
                return new AtomicInteger(1);
            }
            count.incrementAndGet();
            return count;
        });
    }

    public void roomLeft(String roomId) {
        localSubscribers.computeIfPresent(roomId, (id, count) -> {
            if (count.decrementAndGet() > 0) return count;
            container.removeMessageListener(listener, new ChannelTopic(RedisFanout.channel(id)));
            return null;                       // removes the map entry — no leak
        });
    }

    public int subscribedRooms() { return localSubscribers.size(); }
}
```

Wire it into `PresenceListener`:

```java
@EventListener
public void onSubscribe(SessionSubscribeEvent event) {
    // ... existing code ...
    registry.subscribe(accessor.getSessionId(), roomId);
    subscriptions.roomJoined(roomId);                    // <-- new
}

@EventListener
public void onDisconnect(SessionDisconnectEvent event) {
    var rooms = registry.roomsFor(sessionId);
    // ... announce departure ...
    registry.disconnect(sessionId);
    rooms.forEach(subscriptions::roomLeft);              // <-- new
}
```

Configure the container:

```java
@Bean
public RedisMessageListenerContainer listenerContainer(RedisConnectionFactory factory) {
    var container = new RedisMessageListenerContainer();
    container.setConnectionFactory(factory);

    // This pool dispatches every inbound fanout message. Too small and it becomes
    // your new bottleneck; watch its queue like you watch clientOutboundChannel.
    var executor = new ThreadPoolTaskExecutor();
    executor.setCorePoolSize(8);
    executor.setMaxPoolSize(32);
    executor.setQueueCapacity(10_000);
    executor.setThreadNamePrefix("redis-fanout-");
    executor.initialize();
    container.setTaskExecutor(executor);

    return container;
}
```

And give each instance an identity — `application.yml`:

```yaml
pulse:
  node-id: ${HOSTNAME:${random.uuid}}
```

---

## Part C — Wire the controller

```java
@MessageMapping("/room.{roomId}/send")
public void send(@DestinationVariable String roomId,
                 @Payload @Valid MessageCreate create,
                 Principal principal) {

    var result = messages.send(roomId, principal.getName(), create);
    var envelope = Envelope.of("message.new", roomId, json.valueToTree(result.message()));

    template.convertAndSendToUser(principal.getName(), "/queue/ack", ackEnvelope(result));
    if (result.wasRetry()) return;

    template.convertAndSend("/topic/room." + roomId, envelope);   // local subscribers
    fanout.publish(roomId, envelope);                              // everyone else
}
```

> ⚠️ **Order matters, and not for the reason you'd guess.** Local delivery first
> means same-node recipients see the message with zero Redis latency. But it also
> means that if `fanout.publish` throws, local users have it and remote users
> don't — a *split* view. Module 13's outbox makes this atomic. For now, note the
> hazard.

---

## Part D — Prove it works

```bash
docker compose -f ../../infra/compose.dev.yml up -d

SERVER_PORT=8080 PULSE_NODE_ID=node-a ./mvnw spring-boot:run
SERVER_PORT=8081 PULSE_NODE_ID=node-b ./mvnw spring-boot:run
```

```bash
./code/stomp.sh alice room.7                          # -> 8080
sed 's/8080/8081/' code/stomp.sh > /tmp/s8081.sh && chmod +x /tmp/s8081.sh
/tmp/s8081.sh bob room.7                              # -> 8081
```

Type in alice's terminal.

**Expected in bob's terminal — the thing that didn't work in Module 04:**
```
MESSAGE
destination:/topic/room.7
subscription:sub-0

{"v":1,"type":"message.new","ts":1735689600123,"room":"7",
 "data":{"id":"136099384856576000","clientId":"c-18342","seq":41,
         "sender":"alice","body":"hello across instances","ts":1735689600123}}
```

Watch it happen on the wire:
```bash
docker exec pulse-redis redis-cli PSUBSCRIBE 'pulse.room.*'
```
**Expected:**
```
1) "pmessage"
2) "pulse.room.*"
3) "pulse.room.7"
4) "{\"origin\":\"node-a\",\"envelope\":{\"v\":1,\"type\":\"message.new\",...}}"
```

Confirm the counters:
```bash
curl -s localhost:8080/actuator/metrics/fanout.published    | jq '.measurements[0].value'
curl -s localhost:8080/actuator/metrics/fanout.dropped.self | jq '.measurements[0].value'
curl -s localhost:8081/actuator/metrics/fanout.received.remote | jq '.measurements[0].value'
```
**Expected:**
```
5      # node-a published 5
5      # node-a dropped its own 5 echoes
5      # node-b received all 5
```

Confirm lazy subscription is working:
```bash
docker exec pulse-redis redis-cli PUBSUB CHANNELS 'pulse.room.*'
```
**Expected — only rooms with actual subscribers:**
```
1) "pulse.room.7"
```

Disconnect both clients, wait a moment, re-check:
```
(empty array)
```

✅ The subscription was released. Without `roomLeft`, this list grows forever.

---

## Part E — Measure the cost of the hop

Re-run Module 06's benchmark, unchanged, and compare.

```bash
k6 run -e ROOMS=100 -e SEND_EVERY=60000 ../../06-load-testing-harness/code/pulse-load.js
```

**Expected — single instance, no Redis (Module 06 baseline):**
```
fanout_latency_ms: med=14  p(95)=61   p(99)=147  p(99.9)=890
```

**Expected — two instances behind the backplane:**
```
fanout_latency_ms: med=17  p(95)=68   p(99)=161  p(99.9)=910
```

| | 1 node, no Redis | 2 nodes + Redis | Delta |
|---|-----------------|-----------------|-------|
| p50 | 14 ms | 17 ms | **+3 ms** |
| p95 | 61 ms | 68 ms | +7 ms |
| p99 | 147 ms | 161 ms | +14 ms |
| Max conns | 20,000 | **40,000** | **2×** |
| Knee (outbound msg/s) | 450,000 | **870,000** | **1.93×** |

✅ **~3 ms of p50 for nearly linear horizontal scaling.** That is a very good
trade, and now you have the number rather than a belief.

Note the knee scaled 1.93×, not 2×. The missing 7% is the Redis round trip plus
the dispatch thread pool. Find where it goes:

```bash
docker exec pulse-redis redis-cli --latency
docker exec pulse-redis redis-cli INFO stats | grep -E 'instantaneous_ops|pubsub'
```
**Expected:**
```
min: 0, max: 2, avg: 0.11 (1482 samples)

instantaneous_ops_per_sec:3891
pubsub_channels:100
```

Redis itself is doing 0.11 ms and is nowhere near loaded. The cost is in your
JVM's serialize → socket → deserialize → dispatch path, not in Redis.

---

## Part F — nginx with sticky sessions

`infra/nginx.conf`:

```nginx
events { worker_connections 65535; }

http {
  map $http_upgrade $connection_upgrade {
    default upgrade;
    ''      close;
  }

  # Consistent hash on a cookie we set ourselves. Unlike ip_hash this survives
  # carrier NAT (thousands of users behind one IP) and rebalances only 1/n of
  # clients when the upstream list changes.
  upstream pulse {
    hash $cookie_pulse_node consistent;
    server host.docker.internal:8080 max_fails=3 fail_timeout=10s;
    server host.docker.internal:8081 max_fails=3 fail_timeout=10s;
  }

  server {
    listen 80;

    location / {
      # Assign a sticky key on first contact.
      if ($cookie_pulse_node = "") {
        add_header Set-Cookie "pulse_node=$request_id; Path=/; HttpOnly; SameSite=Lax";
      }

      proxy_pass http://pulse;
      proxy_http_version 1.1;                      # REQUIRED for Upgrade
      proxy_set_header Upgrade    $http_upgrade;
      proxy_set_header Connection $connection_upgrade;
      proxy_set_header Host       $host;
      proxy_set_header X-Real-IP  $remote_addr;

      proxy_read_timeout 3600s;                    # default 60s kills idle sockets
      proxy_send_timeout 3600s;
      proxy_buffering    off;
    }
  }
}
```

```bash
docker run -d --name pulse-nginx -p 8090:80 \
  --add-host=host.docker.internal:host-gateway \
  -v "$PWD/infra/nginx.conf:/etc/nginx/nginx.conf:ro" nginx:alpine

for i in 1 2 3 4 5; do
  curl -s -c /tmp/c$i -b /tmp/c$i localhost:8090/actuator/info \
    -o /dev/null -w '%{http_code} '
  curl -s -b /tmp/c$i localhost:8090/whoami-node
done
```

**Expected** — each cookie jar consistently reaches one node:
```
200 node-a
200 node-b
200 node-a
200 node-a
200 node-b
```

Repeat with the same jars and confirm nothing moves. Now kill node-b:

```bash
# stop the 8081 process
for i in 2 5; do curl -s -b /tmp/c$i localhost:8090/whoami-node; done
```
**Expected:**
```
node-a
node-a
```

✅ nginx marked 8081 down after `max_fails` and redistributed. Those clients'
WebSocket connections were dropped and had to reconnect — which is exactly what
Module 18's thundering herd is about.

---

## Part G — Make it lose messages

**This is the point of the module.** Do not skip it.

`code/loss_test.sh`:

```bash
#!/usr/bin/env bash
# Publish a numbered sequence while breaking node-b's Redis connection.
# Count what bob actually received.
set -euo pipefail

TOTAL=200
OUT=/tmp/bob-received.txt
: > "$OUT"

# bob listens on node-b (8081) and logs every seq he sees
( /tmp/s8081.sh bob room.9 | grep -o '"seq":[0-9]*' >> "$OUT" ) &
LISTENER=$!
sleep 2

echo "publishing 1..${TOTAL} via node-a, pausing redis at message 80"
for i in $(seq 1 $TOTAL); do
  if [ "$i" -eq 80 ]; then
    echo ">>> docker pause pulse-redis"
    docker pause pulse-redis
  fi
  if [ "$i" -eq 110 ]; then
    echo ">>> docker unpause pulse-redis"
    docker unpause pulse-redis
  fi
  ./code/publish.sh room.9 "msg-$i" || true
  sleep 0.05
done

sleep 5
kill $LISTENER 2>/dev/null || true

RECEIVED=$(sort -u "$OUT" | wc -l)
echo "published: $TOTAL   received: $RECEIVED   LOST: $((TOTAL - RECEIVED))"
```

```bash
chmod +x code/loss_test.sh
./code/loss_test.sh
```

**Expected:**
```
publishing 1..200 via node-a, pausing redis at message 80
>>> docker pause pulse-redis
>>> docker unpause pulse-redis
published: 200   received: 171   LOST: 29
```

✅ **29 messages gone. Permanently.**

Now look at what the system reported about it:

```bash
curl -s localhost:8080/actuator/metrics/fanout.published | jq '.measurements[0].value'
grep -iE 'error|warn|exception' /tmp/node-a.log | tail -5
grep -iE 'error|warn|exception' /tmp/node-b.log | tail -5
```

**Expected:**
```
200
(node-a: nothing)
(node-b: "Connection reset ... reconnecting" at INFO)
```

**Node A believes it published 200 messages successfully.** No error, no
exception, no retry. The `PUBLISH` calls during the pause either blocked briefly
and then succeeded against a Redis with zero subscribers, or failed and were
logged at INFO by Lettuce's reconnect logic.

Try the nastier variant — `docker pause` looks like a *hang*, which is what real
network partitions look like. Compare with a clean kill:

```bash
# edit loss_test.sh: docker kill / docker start instead of pause / unpause
./code/loss_test.sh
```
**Expected:**
```
published: 200   received: 183   LOST: 17
```

Fewer losses, because a `kill` closes the socket immediately — Lettuce notices in
milliseconds and reconnects, whereas a `pause` leaves the TCP connection looking
healthy until a timeout fires. **The gentler-looking failure loses more data.**

Record it:
```markdown
## Module 07 — Pub/Sub loss

- Redis paused 1.5s mid-stream:  29/200 lost (14.5%)
- Redis killed 1.5s mid-stream:  17/200 lost (8.5%)
- Errors surfaced to the application: ZERO
- fanout.published counter: 200 (i.e. the metric lies)
- Latency cost of the backplane: +3ms p50, +14ms p99
- Horizontal scaling achieved: 1.93x knee for 2 nodes
```

### Why you cannot fix this with retries

The obvious instinct is "retry the publish." It doesn't work:

- **Node A doesn't know delivery failed.** `PUBLISH` returned a subscriber count,
  and a count of 0 is indistinguishable from "nobody is in that room right now,"
  which is a perfectly normal state.
- **The failure is on the *subscriber* side.** Node B was disconnected. No amount
  of publisher-side retry reaches a subscriber that isn't there.
- **Even a successful publish guarantees nothing** — it means bytes were written
  to a socket, not that anyone read them.

The problem isn't reliability of the publish. It's that **there is no record of
the message** for a reconnecting subscriber to catch up from.

That requires storage. Which is Module 09.

---

## Part H — Keep Pub/Sub for what it's good at

Before moving on, use it correctly. Route typing indicators through Pub/Sub
deliberately:

```java
@MessageMapping("/room.{roomId}/typing")
public void typing(@DestinationVariable String roomId, Principal principal) {
    typingService.startTyping(roomId, principal.getName());
    // Pub/Sub is CORRECT here: superseded within 3s, a loss is invisible,
    // and it costs zero storage.
    fanout.publishEphemeral(roomId, Envelope.of("typing.start", roomId,
            json.valueToTree(Map.of("user", principal.getName()))));
}
```

```java
public void publishEphemeral(String roomId, Envelope envelope) {
    // Separate channel prefix so Module 09 can move messages to Streams
    // without touching this path.
    redis.convertAndSend("pulse.ephemeral." + roomId, serialize(envelope));
}
```

Run the loss test against typing indicators:

**Expected:**
```
published: 200 typing events   received: 168   LOST: 32
user experience impact: none observed
```

✅ **Identical loss rate, zero user impact.** Same mechanism, completely
different verdict — because the traffic's semantics are different. That contrast
is the module's real lesson.

---

## What you built and measured

- A Redis Pub/Sub backplane with origin-tagged messages and lazy per-room
  subscription (with cleanup, so it doesn't leak channels).
- Cross-instance chat: alice and bob finally see each other.
- The measured cost: **+3 ms p50 for 1.93× the capacity.**
- nginx with cookie-based consistent hashing, and the observed cost of a node
  loss.
- **A deterministic message-loss demonstration: 29/200 lost, zero errors
  reported.**
- The same failure applied to typing indicators, where it doesn't matter.

Now do [`challenge.md`](./challenge.md).

Then: [Module 08 — Redis Internals](../08-redis-internals/).
