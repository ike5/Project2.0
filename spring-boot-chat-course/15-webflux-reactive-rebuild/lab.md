# Lab 15 — Two Runtimes, One Benchmark

**You'll:** build `pulse-reactive` with WebFlux, R2DBC and reactive Lettuce,
catch a blocking call with BlockHound, then run the identical k6 workload against
both stacks and compare them at every percentile.

⏱️ ~110 min.

---

## Part A — The reactive project

```bash
cd spring-boot-chat-course/apps

curl https://start.spring.io/starter.zip \
  -d type=maven-project -d language=java -d bootVersion=3.4.1 -d javaVersion=21 \
  -d groupId=com.pulse -d artifactId=pulse-reactive -d packageName=com.pulse \
  -d dependencies=webflux,data-r2dbc,postgresql,data-redis-reactive,actuator,validation \
  -o pulse-reactive.zip

unzip -q pulse-reactive.zip -d pulse-reactive && rm pulse-reactive.zip
cd pulse-reactive
```

Add R2DBC's Postgres driver and BlockHound:
```xml
<dependency>
  <groupId>org.postgresql</groupId>
  <artifactId>r2dbc-postgresql</artifactId>
  <scope>runtime</scope>
</dependency>
<dependency>
  <groupId>io.projectreactor.tools</groupId>
  <artifactId>blockhound</artifactId>
  <version>1.0.10.RELEASE</version>
</dependency>
```

`application.yml`:
```yaml
spring:
  application.name: pulse-reactive
  r2dbc:
    url: r2dbc:postgresql://localhost:5432/pulse
    username: pulse
    password: pulse
    pool:
      initial-size: 10
      max-size: 20            # same as Hikari, for a fair comparison
  data:
    redis:
      host: localhost
      port: 6379

server:
  port: 8081                  # so both stacks can run side by side

management:
  endpoints.web.exposure.include: health,metrics,prometheus,threaddump
  metrics.tags.application: pulse-reactive
```

> **Same pool size on both stacks.** Giving reactive a bigger pool would measure
> the pool, not the runtime.

---

## Part B — Reactive WebSocket, without STOMP

Spring WebFlux has no STOMP broker — `@EnableWebSocketMessageBroker` is
servlet-only. That is itself a finding worth recording: **you lose Spring's STOMP
machinery entirely** and hand-roll the protocol.

`src/main/java/com/pulse/ws/ReactiveChatHandler.java`:

```java
package com.pulse.ws;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.stereotype.Component;
import org.springframework.web.reactive.socket.*;
import reactor.core.publisher.*;

import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

@Component
public class ReactiveChatHandler implements WebSocketHandler {

    /** sessionId -> the sink we push outbound frames into. */
    private final Map<String, Sinks.Many<String>> outbound = new ConcurrentHashMap<>();
    /** roomId -> sessionIds */
    private final Map<String, Set<String>> rooms = new ConcurrentHashMap<>();

    private final MessageService messages;
    private final ObjectMapper json;

    @Override
    public Mono<Void> handle(WebSocketSession session) {
        String sessionId = session.getId();

        // Sinks.many().unicast() with a BOUNDED buffer: this is the backpressure
        // boundary for one client. Compare to Module 04, where the equivalent
        // (WebSocketSession's outbound buffer) was configured, not expressed.
        Sinks.Many<String> sink = Sinks.many().unicast()
                .onBackpressureBuffer(new ArrayBlockingQueue<>(1000));
        outbound.put(sessionId, sink);

        Mono<Void> send = session.send(
                sink.asFlux()
                    .map(session::textMessage)
                    .doOnError(e -> log.warn("send failed for {}", sessionId, e)));

        Mono<Void> receive = session.receive()
                .map(WebSocketMessage::getPayloadAsText)
                .flatMap(payload -> handleFrame(sessionId, payload)
                        .onErrorResume(e -> {
                            // One bad frame must not terminate the session.
                            emit(sessionId, errorFrame(e));
                            return Mono.empty();
                        }))
                .then();

        // zip so either side completing tears the session down cleanly.
        return Mono.zip(send, receive)
                   .doFinally(sig -> cleanup(sessionId))
                   .then();
    }

    private Mono<Void> handleFrame(String sessionId, String payload) {
        var frame = parse(payload);
        return switch (frame.type()) {
            case "subscribe" -> subscribe(sessionId, frame.room());
            case "message.create" -> messages
                    .send(frame.room(), userOf(sessionId), frame.data())
                    .flatMap(result -> emitAck(sessionId, result))
                    .then();
            default -> Mono.empty();          // forward compatibility (Module 05)
        };
    }

    /** Local fan-out. tryEmitNext is NON-BLOCKING and returns a result you must check. */
    void broadcastLocal(String roomId, String frame) {
        var members = rooms.getOrDefault(roomId, Set.of());
        for (String sessionId : members) {
            var sink = outbound.get(sessionId);
            if (sink == null) continue;
            var result = sink.tryEmitNext(frame);
            if (result.isFailure()) {
                // The bounded buffer is full: this client is slow. The policy is
                // explicit here, where Module 04's was a config property.
                slowConsumerDrops.increment();
                if (result == Sinks.EmitResult.FAIL_OVERFLOW) close(sessionId, 1009);
            }
        }
    }
}
```

Register it:
```java
@Bean
public HandlerMapping wsMapping(ReactiveChatHandler handler) {
    return new SimpleUrlHandlerMapping(Map.of("/ws", handler), -1);
}
```

> Note what just happened: ~120 lines to replace what
> `@EnableWebSocketMessageBroker` gave you for free — sessions, subscriptions,
> destinations, heartbeats, and the ack protocol. **That is a real cost and it
> belongs in the comparison**, not in a footnote.

---

## Part C — R2DBC

```java
@Repository
public class ReactiveMessageRepository {

    private final DatabaseClient db;

    public Mono<MessageNew> insertIdempotent(long id, String roomId, long seq,
                                             String sender, String clientId, String body) {
        return db.sql("""
                INSERT INTO messages (id, room_id, seq, sender, client_id, body)
                VALUES (:id,:room,:seq,:sender,:cid,:body)
                ON CONFLICT (room_id, client_id, created_at) DO NOTHING
                RETURNING id, client_id, seq, room_id, sender, body,
                          extract(epoch from created_at)*1000 AS ts
                """)
                .bind("id", id).bind("room", roomId).bind("seq", seq)
                .bind("sender", sender).bind("cid", clientId).bind("body", body)
                .map(this::toMessage)
                .one()
                .switchIfEmpty(findByClientId(roomId, clientId));   // it was a retry
    }

    public Flux<MessageNew> scrollback(String roomId, long cursorSeq, int limit) {
        return db.sql("""
                SELECT id, client_id, seq, room_id, sender, body,
                       extract(epoch from created_at)*1000 AS ts
                FROM messages
                WHERE room_id = :room AND seq < :seq AND deleted_at IS NULL
                ORDER BY seq DESC LIMIT :limit
                """)
                .bind("room", roomId).bind("seq", cursorSeq).bind("limit", limit)
                .map(this::toMessage)
                .all();
    }
}
```

**What you lose relative to Module 12's `JdbcClient`:**
- No JPA at all — every query is SQL. (Which Pulse mostly wanted anyway.)
- `@Transactional` works but is `TransactionalOperator`-based; the semantics are
  subtly different and it does not compose with blocking code.
- Flyway is blocking, so migrations run on a separate blocking datasource at
  startup. Slightly awkward, entirely workable.

---

## Part D — Reactive Redis Streams

```java
@Component
public class ReactiveStreamFanout {

    private final ReactiveStringRedisTemplate redis;
    private final ReactiveChatHandler handler;

    public Mono<RecordId> append(String roomId, Envelope envelope) {
        return Mono.fromCallable(() -> json.writeValueAsString(envelope))
                .flatMap(payload -> redis.opsForStream().add(
                        StreamRecords.newRecord()
                                .in(StreamFanout.streamKey(roomId))
                                .ofMap(Map.of("payload", payload))));
    }

    /**
     * The consumer, as a Flux. Note limitRate: this is the request-N protocol
     * doing what a bounded queue does in the blocking version -- except the
     * pressure propagates back to Redis, which stops being read from.
     */
    public Disposable consume(String roomId) {
        String key = StreamFanout.streamKey(roomId);

        return redis.opsForStream()
                .read(Consumer.from(group(), nodeId),
                      StreamReadOptions.empty().count(100).block(Duration.ofSeconds(2)),
                      StreamOffset.create(key, ReadOffset.lastConsumed()))
                .limitRate(100)                          // <-- backpressure
                .onBackpressureBuffer(5_000,
                        dropped -> backpressureDrops.increment(),
                        BufferOverflowStrategy.DROP_OLDEST)
                .flatMap(record -> deliver(roomId, record)
                        .then(redis.opsForStream().acknowledge(key, group(), record.getId()))
                        .onErrorResume(e -> {
                            deliveryFailures.increment();
                            return Mono.empty();          // leave it in the PEL
                        }), 16)                           // concurrency 16
                .repeat()
                .subscribe();
    }
}
```

`limitRate(100)` plus `flatMap(..., 16)` is the whole backpressure story: request
100 at a time, process at most 16 concurrently. When the consumer is slow, Redis
simply isn't read from, and the backlog is visible in `XPENDING` rather than in
your heap.

---

## Part E — Install BlockHound and catch a real violation

```java
@SpringBootApplication
public class PulseReactiveApplication {
    public static void main(String[] args) {
        if (Boolean.getBoolean("blockhound.enabled")) {
            BlockHound.builder()
                    // Flyway at startup is legitimately blocking; allow it.
                    .allowBlockingCallsInside("org.flywaydb.core.Flyway", "migrate")
                    .install();
        }
        SpringApplication.run(PulseReactiveApplication.class, args);
    }
}
```

Now introduce a realistic mistake — the kind that gets code-reviewed through:

```java
public Mono<SendResult> send(String roomId, String sender, MessageCreate create) {
    // "It's just a cache lookup, it's fast."
    var cached = dedupCache.getIfPresent(roomId + "|" + create.clientId());   // Caffeine: fine
    if (cached != null) return Mono.just(new SendResult(cached, true));

    // But this one loads on miss, and the loader does I/O.
    var member = membershipCache.get(sender + ":" + roomId,
            k -> membershipRepository.isMemberBlocking(sender, roomId));      // <-- JDBC
    ...
}
```

```bash
./mvnw spring-boot:run -Dspring-boot.run.jvmArguments="-Dblockhound.enabled=true"
curl -X POST localhost:8081/api/test/send -d '{"room":"room.1","body":"hi"}'
```

**Expected:**
```
reactor.blockhound.BlockingOperationError: Blocking call! java.net.SocketInputStream#socketRead0
	at java.base/java.net.SocketInputStream.socketRead0(SocketInputStream.java)
	at org.postgresql.core.VisibleBufferedInputStream.readMore(VisibleBufferedInputStream.java:161)
	at com.pulse.chat.MembershipRepository.isMemberBlocking(MembershipRepository.java:41)
	at com.pulse.chat.ReactiveMessageService.send(ReactiveMessageService.java:38)
	Blocking call detected on thread reactor-http-nio-3
```

✅ **`reactor-http-nio-3`** — an event-loop thread. Without BlockHound this
wouldn't throw; it would just make every connection on that loop 8 ms slower, and
you'd never find it.

Measure what it costs before fixing it:
```bash
k6 run --vus 5000 --duration 3m ../../06-load-testing-harness/code/pulse-load.js
```
| | Without the blocking call | With it |
|---|--------------------------|---------|
| p50 | 9 ms | **412 ms** |
| p99 | 61 ms | **8,940 ms** |
| Event loop threads | 16 | 16 |
| Connections affected | — | **all 5,000** |

✅ **One 8 ms JDBC call in a cache loader made p99 8.9 seconds for everyone.**
This is the reactive tax made concrete: a mistake that costs one request in the
blocking model costs *every* request here.

The fix:
```java
return membershipRepository.isMemberReactive(sender, roomId)          // R2DBC
        .flatMap(isMember -> isMember ? doSend(...) : Mono.error(new AccessDeniedException()));
```
Or, when you genuinely must call blocking code:
```java
.subscribeOn(Schedulers.boundedElastic())    // moves it OFF the event loop
```

> Keep BlockHound enabled in **every** test and dev run. It is not a debugging
> tool you reach for; it is the thing that makes the reactive rule enforceable.

---

## Part F — The head-to-head benchmark

**The point of the module.** Identical k6 script, identical hardware, identical
Redis and Postgres, run alternately to control for thermal state.

`code/head_to_head.sh`:
```bash
#!/usr/bin/env bash
set -euo pipefail
for round in 1 2 3; do
  for stack in mvc reactive; do
    port=$([ "$stack" = mvc ] && echo 8080 || echo 8081)
    echo "=== round $round: $stack ==="
    ./code/start_$stack.sh
    sleep 120                                       # JIT warm-up
    k6 run -e HOST="localhost:$port" \
           --summary-export="/tmp/${stack}-r${round}.json" \
           "$@" ../../06-load-testing-harness/code/pulse-load.js
    ./code/measure_memory.sh "$stack" >> "/tmp/${stack}-mem-r${round}.txt"
    ./code/stop_$stack.sh
    sleep 90                                        # let TIME_WAIT drain
  done
done
```

### Run 1 — moderate load (20,000 connections, 200-member rooms)

```bash
./code/head_to_head.sh -e ROOMS=100 -e SEND_EVERY=60000
```

**Expected (median of 3 runs):**

| | MVC + virtual threads | WebFlux |
|---|----------------------|---------|
| Connections | 20,000 | 20,000 |
| **p50** | **21 ms** | 24 ms |
| p95 | 79 ms | 74 ms |
| p99 | 192 ms | **171 ms** |
| p99.9 | 910 ms | **680 ms** |
| **Heap after GC** | **3,140 MB** | **1,180 MB** |
| **KB per connection** | **157** | **59** |
| Live threads | 71 | **23** |
| CPU at steady state | 41% | **34%** |

✅ **WebFlux uses 2.7× less memory per connection** and slightly fewer CPU cycles.
Virtual threads win p50 by 3 ms — fewer scheduling hops for a simple path.

### Run 2 — connection density (how many fit?)

```bash
./code/head_to_head.sh -e SEND_EVERY=999999999 --vus 200000
```

**Expected:**

| | MVC + virtual threads | WebFlux |
|---|----------------------|---------|
| Max connections in 6 GB heap | **38,200** | **101,400** |
| Failure mode | `OutOfMemoryError` | `OutOfMemoryError` |
| KB/connection at the ceiling | 161 | **61** |

✅ **2.65× more connections per gigabyte.** This is reactive's headline win, and
it's real.

But note what it *isn't*: before Java 21, the same comparison against a
platform-thread server would have been **20–50×**, not 2.65×. **Virtual threads
closed most of the gap.**

### Run 3 — past the knee (overload behaviour)

```bash
./code/head_to_head.sh -e ROOMS=100 -e SEND_EVERY=3000
```

**Expected:**

| | MVC + virtual threads | WebFlux |
|---|----------------------|---------|
| Offered outbound rate | 1,326,000/s | 1,326,000/s |
| Achieved | 790,000/s | **812,000/s** |
| p99 | 9,200 ms | **2,140 ms** |
| Messages dropped | 0 (queued) | **184,921 (dropped, counted)** |
| Heap trajectory | **climbing to OOM** | flat |
| Recovery after load stops | 41 s | **3 s** |

✅ **This is the most interesting result in the module.**

WebFlux was *not* faster in throughput — 812k vs 790k, within noise. But under
overload:
- Virtual threads **queued** everything (the outbound channel), so p99 went to
  9.2 s, the heap climbed, and recovery took 41 seconds after the load stopped.
- WebFlux **dropped 184,921 messages** via `onBackpressureBuffer(DROP_OLDEST)`,
  kept p99 at 2.1 s, kept the heap flat, and recovered in 3 seconds.

**WebFlux lost data and that was the better outcome** — because it was an
*explicit policy*, it was *counted*, and it kept the system alive and responsive
for everyone else.

You can build this in the blocking version (Module 04's bounded `queueCapacity`
plus a rejection handler) and Pulse did. The difference is that Reactor makes it
the default shape and gives you four named strategies, where the blocking version
gives you a queue size and a `RejectedExecutionHandler` you have to think to
configure.

Record it:
```markdown
## Module 15 — Virtual threads vs WebFlux

Moderate load (20k conns, 200-member rooms):
  p50        21ms  vs  24ms      (VT wins)
  p99       192ms  vs 171ms      (WebFlux wins)
  KB/conn      157  vs   59      (WebFlux 2.7x better)
  threads       71  vs   23

Connection density (6GB heap):
  38,200  vs  101,400 connections   (WebFlux 2.65x)
  -- but pre-Java-21 the gap vs platform threads was 20-50x

Past the knee:
  throughput  790k/s vs 812k/s     (tie)
  p99        9,200ms vs 2,140ms    (WebFlux 4.3x better)
  behaviour   queues to OOM  vs  drops 184,921 and stays flat
  recovery        41s  vs  3s

Cost of reactive:
  - ~120 lines to replace @EnableWebSocketMessageBroker (no STOMP in WebFlux)
  - one 8ms blocking call in a cache loader: p99 61ms -> 8,940ms for ALL clients
  - no JPA; context propagation must be wired explicitly
```

---

## Part G — Measure the development cost honestly

Not a micro-benchmark, but the number that usually decides.

| Task | MVC + virtual threads | WebFlux |
|------|----------------------|---------|
| Lines for the WebSocket layer | 180 (STOMP config + controller) | **~300** (hand-rolled protocol) |
| Lines for the data layer | 140 | 165 |
| Lines for fan-out | 210 | 240 |
| Test setup | `@SpringBootTest` + Testcontainers | + `StepVerifier`, + `BlockHound` |
| Debugging a NPE | stack trace names your method | assembly trace + `checkpoint()` |
| Adding a blocking library | works | **requires a reactive equivalent or `boundedElastic`** |
| Onboarding a new engineer | days | **weeks** |

The last row is not a joke, and it's the one that decides most real adoptions.

---

## The verdict

**Pulse stays on MVC + virtual threads.** The reasoning:

1. **2.65× connection density is real but not decisive at our scale.** 38,200
   connections/node × 8 nodes = 305,000 concurrent users. If we needed 800,000
   from the same hardware, this decision would flip.
2. **We already have bounded queues and rejection policies** (Module 04, Module
   06). Reactor's backpressure is better *ergonomics* for the same capability, not
   a capability we lack.
3. **No STOMP in WebFlux** costs us Spring's entire messaging layer — sessions,
   subscriptions, destinations, heartbeats — all of which we'd maintain
   ourselves, forever.
4. **The blocking ecosystem is our ecosystem.** JPA for room/user CRUD, Flyway,
   Testcontainers, and every library a future feature needs.
5. **The 8 ms blocking call in Part E is the risk that matters.** In the
   virtual-thread model that mistake is invisible. In WebFlux it's an outage,
   and preventing it is a permanent discipline cost across the whole team.

**When to choose WebFlux instead:**
- Connection density is the binding constraint (an IoT gateway, a market-data
  fan-out, a pure proxy).
- Your workload is genuinely stream-shaped and you'd use `windowTimeout`,
  `groupBy`, `sample`, and friends.
- Your team is already fluent, and your stack is already non-blocking end to
  end.

> If you take one thing from this module: **the efficiency argument for reactive
> narrowed by roughly an order of magnitude in September 2023, and the
> composition argument didn't move at all.** Most teams adopted reactive for the
> first reason. Very few have re-examined it.

---

## What you built

- A complete reactive Pulse: WebFlux WebSocket, R2DBC, reactive Redis Streams,
  with explicit backpressure policies.
- A caught blocking call, and the measurement of what it cost (p99 61 ms →
  8,940 ms for every client on that event loop).
- **A three-run head-to-head** covering moderate load, connection density, and
  overload behaviour.
- A decision with numbers behind it, and the conditions that would reverse it.

Now do [`challenge.md`](./challenge.md).

Then: [Module 16 — The Same Workload on Kafka](../16-kafka-comparison/).
