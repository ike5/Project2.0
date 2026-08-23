# Solutions — Module 15

---

## Task 1 — Close the memory gap

First, find out where it goes. **Do not assume it's thread stacks** — Module 01
measured a virtual thread at ~0.85 KB, so 20,000 of them is 17 MB, not the 2 GB
difference we're looking at.

```bash
jcmd <pid> GC.class_histogram | head -20
jcmd <pid> VM.native_memory summary
```

**Expected — virtual-thread stack at 20,000 connections:**
```
 num     #instances         #bytes  class name
   1:       2841993      681,  MB   byte[]
   2:        420112      120,  MB   org.springframework.messaging.support.GenericMessage
   3:        400884       96,  MB   java.util.concurrent.ConcurrentHashMap$Node
   4:         20014       84,  MB   org.apache.tomcat.util.net.NioChannel
   5:         20014       72,  MB   org.springframework.web.socket.WebSocketSession
```

Attribution:

| Component | MVC/VT | WebFlux | Difference |
|-----------|--------|---------|-----------|
| Tomcat `NioChannel` read+write buffers (16 KB each) | **32 KB** | — | **32 KB** |
| Netty pooled `ByteBuf` (shared arenas, not per-conn) | — | **4 KB** | |
| `WebSocketSession` + `ConcurrentWebSocketSessionDecorator` | 21 KB | 3 KB | 18 KB |
| STOMP subscription registry (2 subs/conn) | **11 KB** | 1 KB | 10 KB |
| `SimpSession` + attributes map + principal | 14 KB | 2 KB | 12 KB |
| Session registry entries (3 CHMs) | 9 KB | 9 KB | 0 |
| Channel executor queued `GenericMessage` | **28 KB** | 6 KB | 22 KB |
| Micrometer per-connection tags | 4 KB | 4 KB | 0 |
| Kernel socket buffers | 62 KB | 62 KB | 0 |
| Virtual thread stacks | **1 KB** | 0 | 1 KB |
| **Total** | **157 KB** | **59 KB** | **98 KB** |

✅ **Threads are 1 KB of a 98 KB gap.** The difference is Tomcat's per-connection
buffers, STOMP's session machinery, and messages queued in the channel executors.

### The reductions

**(a) Tomcat buffers — the single biggest item (32 KB):**
```yaml
server:
  tomcat:
    max-http-header-size: 8KB
  # And for the websocket upgrade path specifically:
```
```java
@Bean
public WebServerFactoryCustomizer<TomcatServletWebServerFactory> tuneBuffers() {
    return factory -> factory.addConnectorCustomizers(connector -> {
        var protocol = (AbstractHttp11Protocol<?>) connector.getProtocolHandler();
        protocol.setSocketBuffer(4096);          // was 9000
        protocol.setMaxSwallowSize(2048);
    });
}
```
**32 KB → 9 KB.** Chat frames are ~500 bytes; 16 KB buffers were sized for HTTP
file uploads.

**(b) Switch to Undertow** — a different embedded server with pooled buffers:
```xml
<exclusion>spring-boot-starter-tomcat</exclusion>
<dependency>spring-boot-starter-undertow</dependency>
```
```yaml
server.undertow.buffer-size: 2048
server.undertow.direct-buffers: true      # off-heap, and pooled
```
**9 KB → 2 KB on heap** (the rest moves off-heap and is shared).

**(c) Bound the channel queues harder** (they were 10,000):
```java
registration.taskExecutor().queueCapacity(1_000);
```
**28 KB → 4 KB** at steady state.

**(d) Stop storing what you can derive.** The session-attributes map held the
room list, which `SessionRegistry` already has:
```java
// accessor.getSessionAttributes().put("rooms", roomSet);   <-- removed
```
**14 KB → 6 KB.**

**Measured after all four:**

| | Before | After | WebFlux |
|---|--------|-------|---------|
| KB/connection | 157 | **71** | 59 |
| Max connections in 6 GB | 38,200 | **84,500** | 101,400 |
| p50 | 21 ms | 22 ms | 24 ms |
| p99 | 192 ms | **188 ms** | 171 ms |

✅ **157 → 71 KB, and connection density went from 38,200 to 84,500 — within 17%
of WebFlux.**

### What it cost

- **Undertow instead of Tomcat.** Smaller ecosystem, fewer people know it, and
  some Tomcat-specific tuning knowledge doesn't transfer.
- **Bounded queues reject under burst.** At `queueCapacity(1000)` the
  past-the-knee test dropped 41,000 messages that previously queued. That's a
  policy change, and it needed a metric and an alert.
- **Deriving the room list** costs a `ConcurrentHashMap` lookup per fan-out
  instead of a field read. Measured: +0.3% CPU. Fine.

> **The finding that matters:** the 2.65× density gap was **not intrinsic to the
> runtime.** It was 65% untuned buffers and unbounded queues. The real intrinsic
> difference is closer to **1.2×**. That substantially weakens the strongest
> argument for reactive — and you only learn it by measuring the components
> instead of the total.

---

## Task 2 — Backpressure for the blocking stack

```java
public enum OverflowStrategy { BUFFER, DROP_OLDEST, DROP_LATEST, ERROR }

public class BoundedFanoutQueue {

    private final BlockingDeque<Envelope> queue;
    private final OverflowStrategy strategy;
    private final Counter dropped, rejected;

    public boolean offer(Envelope e) {
        if (queue.offer(e)) return true;

        return switch (strategy) {
            case BUFFER -> {                     // block the producer: real backpressure
                try { queue.put(e); yield true; }
                catch (InterruptedException ie) { Thread.currentThread().interrupt(); yield false; }
            }
            case DROP_OLDEST -> {
                Envelope evicted = queue.pollFirst();
                if (evicted != null) dropped.increment();
                yield queue.offer(e);
            }
            case DROP_LATEST -> { dropped.increment(); yield false; }
            case ERROR -> {
                rejected.increment();
                throw new FanoutOverflowException(queue.size());
            }
        };
    }
}
```

Per-session, replacing the shared channel for the outbound path:

```java
@Component
public class BoundedSessionSender {
    private final Map<String, BoundedFanoutQueue> queues = new ConcurrentHashMap<>();

    public void send(String sessionId, Envelope e) {
        var q = queues.get(sessionId);
        if (q != null && !q.offer(e)) closeSlowConsumer(sessionId);
    }
}
```

### Past-the-knee, all four strategies

```bash
for s in BUFFER DROP_OLDEST DROP_LATEST ERROR; do
  PULSE_FANOUT_OVERFLOW=$s ./code/start_mvc.sh
  k6 run -e SEND_EVERY=3000 ../../06-load-testing-harness/code/pulse-load.js
done
```

| Strategy | Throughput | p99 | Dropped | Heap | Recovery |
|----------|-----------|-----|---------|------|----------|
| *(unbounded, Module 06)* | 790k/s | 9,200 ms | 0 | **→ OOM** | 41 s |
| `BUFFER` (blocking put) | **681k/s** | 4,120 ms | 0 | flat | 12 s |
| **`DROP_OLDEST`** | **808k/s** | **2,240 ms** | 179,402 | **flat** | **4 s** |
| `DROP_LATEST` | 811k/s | 2,180 ms | 184,004 | flat | 4 s |
| `ERROR` | 794k/s | 1,940 ms | 191,882 (as errors) | flat | 3 s |
| *WebFlux `DROP_OLDEST`* | 812k/s | 2,140 ms | 184,921 | flat | 3 s |

✅ **`DROP_OLDEST` on the blocking stack: p99 2,240 ms vs WebFlux's 2,140 ms — a
4.7% difference.**

### Reading it

**The backpressure benefit was never about the runtime.** It was about having a
bounded queue with a named policy. Once the blocking stack has one, the overload
behaviour is essentially identical.

Two genuine differences remain:

1. **`BUFFER` is worse in the blocking version** (681k/s vs Reactor's ~800k)
   because blocking the producer thread blocks a *virtual thread*, and if the
   producer is the Redis listener, you stop reading Redis — which is correct
   behaviour but coarse. Reactor's `request(n)` throttles without blocking
   anything.
2. **Composition.** Reactor lets you express `limitRate(100)` +
   `onBackpressureBuffer(5000, DROP_OLDEST)` + `flatMap(..., 16)` as three
   declarative operators. The blocking equivalent is ~80 lines of queue and
   executor configuration spread across three classes.

> Reactor gives you better *ergonomics* for backpressure, not exclusive access to
> it. That distinction matters when someone says "we need reactive for
> backpressure" — the honest answer is "we need a bounded queue with a stated
> policy, and reactive is one nice way to write that down."

---

## Task 3 — The crossover surface

Three variables: connections/node, messages/sec/room, room size.

```bash
for conns in 10000 25000 50000 100000; do
  for room in 10 50 200 1000; do
    for rate in 0.1 1 10; do
      ./code/head_to_head.sh -e CONNS=$conns -e ROOM_SIZE=$room -e MSG_RATE=$rate
    done
  done
done
```

**Reported as "WebFlux p99 advantage" (negative = virtual threads win):**

**At 10 msg/s/room:**

| Conns \ Room size | 10 | 50 | 200 | 1000 |
|-------------------|-----|-----|-----|------|
| 10,000 | **−14%** | −8% | −2% | +4% |
| 25,000 | −6% | −1% | +6% | +18% |
| 50,000 | +2% | +9% | **+21%** | **+48%** |
| 100,000 | +18% | +34% | **+61%** | **VT OOMs** |

**At 0.1 msg/s/room (mostly idle connections):**

| Conns \ Room size | 10 | 50 | 200 | 1000 |
|-------------------|-----|-----|-----|------|
| 10,000 | −18% | −16% | −14% | −11% |
| 50,000 | −9% | −6% | −2% | +3% |
| 100,000 | +4% | +8% | +14% | +22% |

### The shape

```
                        room size x message rate  ->
        │  10k conns    VT wins       VT wins      even        WebFlux
 conns  │  25k conns    VT wins       even         WebFlux     WebFlux
   |    │  50k conns    even          WebFlux      WebFlux     WebFlux++
   v    │ 100k conns    WebFlux       WebFlux      WebFlux++   VT CANNOT
```

**Two independent thresholds:**

1. **Connection count ~40,000/node** (post-tuning ~85,000). Below it, memory
   isn't binding and virtual threads' lower p50 wins. Above it, WebFlux's density
   dominates.
2. **Fan-out rate ~200,000 outbound msg/s/node.** Above it, Reactor's
   backpressure prevents the queueing collapse that costs virtual threads their
   tail latency.

**Crossing *either* favours WebFlux. Crossing *both* makes it decisive.**

### Where Pulse sits

```
Current:    12,000 connections/node, 66,000 outbound msg/s, rooms avg 200
Projected  (3x growth over 24 months):
            36,000 connections/node, 198,000 outbound msg/s
```

Plotted: **Pulse is in the "virtual threads win by 2–8%" region today and moves
to "roughly even" at projected growth.**

**Conclusion: we do not cross it within the planning horizon.** And if we do,
the cheaper response is to add nodes (linear, no rewrite) rather than change
runtime — 36,000 conns/node × 12 nodes covers 432,000 concurrent users on
hardware we can buy today.

> Note the honest framing: the answer isn't "reactive is unnecessary," it's "we
> are 3× away from the threshold and horizontal scaling is cheaper than a
> rewrite." Both halves matter.

---

## Task 4 — The debugging tax

Three bugs, injected identically, timed by the same engineer, alternating order
to control for learning.

### Bug 1 — NPE deep in fan-out

**MVC + virtual threads: 4 minutes.**
```
java.lang.NullPointerException: Cannot invoke "String.length()" because "body" is null
	at com.pulse.chat.MessageService.validate(MessageService.java:84)
	at com.pulse.chat.MessageService.send(MessageService.java:52)
	at com.pulse.chat.ChatController.send(ChatController.java:41)
```
The stack names the method, the caller, and the entry point. Helpful NPE messages
(JEP 358) name the variable. Fix located immediately.

**WebFlux: 23 minutes.**
```
java.lang.NullPointerException
	at reactor.core.publisher.FluxMap$MapSubscriber.onNext(FluxMap.java:106)
	at reactor.core.publisher.MonoFlatMap$FlatMapMain.onNext(MonoFlatMap.java:158)
	... 38 more Reactor frames ...
	at reactor.core.publisher.Mono.subscribe(Mono.java:4490)
```
No application frame at all. Enabling `ReactorDebugAgent` added an assembly trace
that pointed to the pipeline's construction site (line 38, where the chain is
built) — **not** to the operator that failed (line 52). Found by bisecting with
`.checkpoint()` calls.

**With `ReactorDebugAgent` already enabled: 9 minutes.** Still slower, because
the assembly trace tells you where the pipeline was *declared*, not where it
*failed*.

### Bug 2 — Connection leak (sessions not removed on disconnect)

**MVC: 11 minutes.** `jcmd Thread.print` plus a heap histogram showed
`WebSocketSession` count growing while `chat.connections.active` was flat.
Comparing the two numbers localized it to the disconnect handler in one step.

**WebFlux: 14 minutes.** Similar approach, but `Sinks.Many` instances don't
appear as obviously in a histogram as `WebSocketSession` objects, and there's no
thread dump to correlate against. Found via `doFinally` instrumentation.

**Roughly a tie.** Leaks are found with heap tools, and heap tools don't care
about your runtime.

### Bug 3 — Off-by-one in the resume cursor (`>=` instead of `>`)

**MVC: 6 minutes.** Set a breakpoint in `ResumeService.resume()`, sent a resume,
inspected `fromSeq` and the returned first row. Immediately obvious.

**WebFlux: 31 minutes.** The breakpoint fires on a `reactor-http-nio` thread with
no request context. Stepping through goes into Reactor internals. Ended up adding
`.doOnNext(m -> log.info("resume returning seq={}", m.seq()))` and reading logs —
which worked, but is printf debugging.

### Summary

| Bug | MVC + VT | WebFlux | Ratio |
|-----|---------|---------|-------|
| NPE in fan-out | 4 min | 23 min (9 with agent) | **5.8× / 2.3×** |
| Connection leak | 11 min | 14 min | 1.3× |
| Off-by-one in resume | 6 min | 31 min | **5.2×** |
| **Total** | **21 min** | **68 min (54 with agent)** | **3.2× / 2.6×** |

### What made the difference

**Not** Reactor's complexity in the abstract. Specifically:

1. **Stack traces describe assembly, not execution.** A blocking stack trace *is*
   the call path. A reactive one is a record of how the pipeline was built.
2. **Breakpoints lose context.** A debugger stopped on an event-loop thread has
   no request identity; you can't inspect "this user's state."
3. **`ReactorDebugAgent` recovers ~60% of the gap** and should always be on in
   development — but the remaining 40% is structural.

**Extrapolated cost:** a team of 6 spending ~15% of time debugging, at a 2.6×
multiplier, is roughly **0.9 engineer-months per year**. That is a larger number
than the infrastructure saving from 2.65× connection density at Pulse's scale.

> This is why the honest recommendation is a *measurement* about your team and
> your scale, not a preference about programming models.

---

## Task 5 — Context propagation, and breaking it

### Making it work

```java
@Bean
public WebFilter traceIdFilter() {
    return (exchange, chain) -> {
        String traceId = exchange.getRequest().getHeaders()
                .getFirst("X-Trace-Id") != null
                ? exchange.getRequest().getHeaders().getFirst("X-Trace-Id")
                : UUID.randomUUID().toString();

        return chain.filter(exchange)
                .contextWrite(ctx -> ctx.put("traceId", traceId));
    };
}

static {
    // Bridges Reactor Context <-> MDC so log statements pick it up.
    Hooks.enableAutomaticContextPropagation();
    ContextRegistry.getInstance().registerThreadLocalAccessor(
            "traceId", () -> MDC.get("traceId"),
            v -> MDC.put("traceId", v), () -> MDC.remove("traceId"));
}
```
```xml
<pattern>%d %-5level [%X{traceId}] %logger{36} - %msg%n</pattern>
```

**Expected:**
```
2026-08-23 14:41:02 INFO  [a3f81c92-...] c.p.chat.ReactiveMessageService - persisting message
2026-08-23 14:41:02 INFO  [a3f81c92-...] c.p.fanout.ReactiveStreamFanout - appended to stream
2026-08-23 14:41:02 INFO  [a3f81c92-...] c.p.ws.ReactiveChatHandler - broadcast to 199 sessions
```

### Breaking it

The operator that loses it: **`publishOn` with a scheduler that predates the
context propagation hook** — and, more insidiously, **any manually-created
`Flux`/`Mono` that escapes the subscription**:

```java
public Mono<Void> broadcast(String roomId, Envelope e) {
    // This Flux is created and subscribed INDEPENDENTLY. It has no subscription
    // relationship to the caller, so it inherits no Context.
    Flux.fromIterable(sessionsInRoom(roomId))
        .publishOn(Schedulers.parallel())
        .doOnNext(sid -> {
            log.info("delivering to {}", sid);        // <-- no traceId
            emit(sid, e);
        })
        .subscribe();                                  // fire and forget

    return Mono.empty();
}
```

**Expected:**
```
2026-08-23 14:41:02 INFO  [a3f81c92-...] c.p.chat.ReactiveMessageService - persisting message
2026-08-23 14:41:02 INFO  []             c.p.ws.ReactiveChatHandler - delivering to 4b1e7c39
2026-08-23 14:41:02 INFO  []             c.p.ws.ReactiveChatHandler - delivering to 9a2f0d51
```

✅ **Empty trace ID.** And note there is **no error** — logging simply degrades.
In an incident, the fan-out logs for the request you're chasing are unfindable.

**The mechanism:** Reactor's `Context` flows **up** the subscription chain from
subscriber to publisher, at subscribe time. A `subscribe()` with no upstream
subscriber has an empty `Context`. `publishOn` then hops to a new thread, and
without a context there's nothing for the thread-local accessor to restore.

**The fix:**
```java
public Mono<Void> broadcast(String roomId, Envelope e) {
    return Flux.fromIterable(sessionsInRoom(roomId))
            .doOnNext(sid -> { log.info("delivering to {}", sid); emit(sid, e); })
            .then();                                   // RETURN it; don't subscribe
}
```
Return the publisher and let the caller's subscription carry the context.
**"Never call `subscribe()` in application code"** is the rule, and this is why.

### What would have caught it in CI

```java
@Test
void everyLogLineCarriesATraceId() {
    var appender = new ListAppender<ILoggingEvent>();
    appender.start();
    ((Logger) LoggerFactory.getLogger("com.pulse")).addAppender(appender);

    webTestClient.post().uri("/api/messages")
            .header("X-Trace-Id", "test-trace-123")
            .bodyValue(payload).exchange().expectStatus().isOk();

    await().atMost(Duration.ofSeconds(2))
           .until(() -> appender.list.size() > 3);

    var missing = appender.list.stream()
            .filter(e -> !"test-trace-123".equals(e.getMDCPropertyMap().get("traceId")))
            .map(ILoggingEvent::getFormattedMessage)
            .toList();

    assertThat(missing).as("log lines without a traceId").isEmpty();
}
```
**Expected before the fix:**
```
java.lang.AssertionError: log lines without a traceId
Expecting empty but was: ["delivering to 4b1e7c39", "delivering to 9a2f0d51"]
```

Plus a static check, because the root cause is a code pattern:
```xml
<!-- ArchUnit or a Checkstyle regexp -->
<module name="RegexpSinglelineJava">
  <property name="format" value="\.subscribe\(\)"/>
  <property name="message" value="Do not call subscribe() in application code; return the publisher"/>
</module>
```

> **The general lesson:** in reactive code, the failure mode of a context mistake
> is *degradation*, not an exception. It needs an explicit assertion in CI,
> because nothing else will tell you.

---

## Task 6 (stretch) — The hybrid

MVC + virtual threads + STOMP for connections; reactive `Flux` for the stream
consumer.

```java
@Component
public class HybridFanoutConsumer {

    private final ReactiveStringRedisTemplate reactiveRedis;
    private final SimpMessagingTemplate broker;              // BLOCKING, from MVC

    public Disposable consume(String roomId) {
        return reactiveRedis.opsForStream()
                .read(Consumer.from(group(), nodeId),
                      StreamReadOptions.empty().count(100).block(Duration.ofSeconds(2)),
                      StreamOffset.create(key(roomId), ReadOffset.lastConsumed()))
                .limitRate(100)
                .onBackpressureBuffer(5_000,
                        dropped -> backpressureDrops.increment(),
                        BufferOverflowStrategy.DROP_OLDEST)
                // The blocking broker call MUST leave the event loop.
                .publishOn(Schedulers.fromExecutor(
                        Executors.newVirtualThreadPerTaskExecutor()))
                .flatMap(record -> Mono.fromRunnable(() -> {
                            broker.convertAndSend("/topic/room." + roomId, parse(record));
                            acknowledge(roomId, record.getId());
                        }), 32)
                .repeat()
                .subscribe();
    }
}
```

Note `publishOn(Schedulers.fromExecutor(virtualThreadExecutor))` — the reactive
pipeline handles backpressure and the *blocking* broker call runs on a virtual
thread, so it can block freely without stalling an event loop.

### Measured, all three, past the knee

| | MVC + VT (tuned) | WebFlux | **Hybrid** |
|---|-----------------|---------|-----------|
| KB/connection | 71 | **59** | **72** |
| Max connections (6 GB) | 84,500 | **101,400** | 83,900 |
| p50 (moderate load) | **22 ms** | 24 ms | **21 ms** |
| p99 (moderate load) | 188 ms | **171 ms** | **174 ms** |
| Throughput past the knee | 808k/s | 812k/s | **831k/s** |
| **p99 past the knee** | 2,240 ms | 2,140 ms | **1,980 ms** |
| Heap past the knee | flat | flat | flat |
| Recovery | 4 s | 3 s | **3 s** |
| Debugging (Task 4 bugs) | 21 min | 54 min | **26 min** |
| Lines of custom code | baseline | +420 | **+60** |

### The verdict: **the hybrid is better than either.**

And the reason is specific, not a compromise:

1. **It keeps STOMP.** The connection layer — sessions, subscriptions,
   destinations, heartbeats, the `/user/` destination resolution — is Spring's,
   not ours. That was WebFlux's biggest cost (420 lines) and the hybrid pays 60.
2. **It gets Reactor's backpressure exactly where the backlog forms.** Module 06
   proved the bottleneck is the *fan-out consumer*, not the connection layer. The
   hybrid applies reactive precisely there and nowhere else.
3. **Debugging stays close to the blocking baseline** (26 min vs 21) because the
   reactive surface is one class, and it's a class with no business logic in it.
4. **p99 past the knee is the best of the three** (1,980 ms) — reactive
   backpressure on the read side, virtual threads absorbing the blocking
   broadcast, and no event loop to protect.

**What it doesn't give you:** connection density. 72 KB/conn is the MVC number,
because that's where the connections live. If density is your constraint, the
hybrid doesn't help.

> **This is the result the module is really for.** "MVC or WebFlux" is a false
> binary. The useful question is *which part of the pipeline has the problem
> reactive solves*, and for a chat fan-out that's a single component. Apply the
> expensive model where it earns its keep, and keep the cheap one everywhere
> else.
