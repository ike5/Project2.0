# Module 15 — Rebuilding the Hot Path in WebFlux

**Goal:** Build the same chat server on an event loop, benchmark it head to head
against virtual threads, and be able to say — with numbers — which one you'd
choose and why.

⏱️ ~6 hours · **Prerequisites:** Modules 00–14.

---

## The question this module answers

Module 01 named two families of answer to "how do we stop paying for an OS thread
while we wait?"

- **Answer B, virtual threads** — keep blocking code; make blocking cheap. This
  is what Pulse has been built on for fourteen modules.
- **Answer A, the event loop** — never block; invert the code into callbacks or
  a reactive pipeline.

Everything so far has assumed B. Now you build A and measure the difference,
because "reactive is faster" and "virtual threads made reactive obsolete" are
both claims you'll hear, and neither is quite right.

---

## Reactor in the amount you need

```java
Mono<Message>      // 0 or 1 items, eventually
Flux<Message>      // 0..N items, eventually
```

Both are **lazy**: nothing happens until something subscribes. A `Mono` you build
and don't subscribe to does nothing at all — which is the single most common
first bug.

```java
// Blocking (what Pulse has)
Message m = repository.save(msg);
broker.send(roomId, m);
return m;

// Reactive
return repository.save(msg)                          // Mono<Message>
        .flatMap(saved -> broker.send(roomId, saved) // Mono<Void>
                                .thenReturn(saved));
```

| Operator | Does |
|----------|------|
| `map` | Transform each item, synchronously |
| `flatMap` | Transform into another publisher and flatten — **this is where async chains** |
| `then` / `thenReturn` | Ignore the result, continue |
| `zip` | Combine several publishers when all complete |
| `filter`, `take`, `bufferTimeout` | As they sound |
| `onErrorResume` | Recover |
| `doOnNext`, `doOnError` | Side effects, no transformation |

`flatMap` versus `map` is the distinction that matters: `map` returns a value,
`flatMap` returns a *publisher*. Using `map` where you needed `flatMap` gives you
a `Mono<Mono<T>>` that never resolves.

---

## The rule: never block the event loop

Netty runs a small number of event-loop threads (default: `2 × cores`). Each owns
thousands of connections. **Anything that blocks one stalls every connection it
owns.**

```java
// CATASTROPHIC in WebFlux
public Mono<Message> send(MessageCreate c) {
    Message m = jdbcRepository.save(c);          // JDBC BLOCKS
    return Mono.just(m);
}
```

At 5,000 connections per event loop, a 50 ms JDBC call adds 50 ms of latency to
**all 5,000**, not just the caller's.

This is why the reactive ecosystem needs its own driver for everything:

| Blocking | Reactive |
|----------|----------|
| JDBC | **R2DBC** |
| Jedis / Lettuce sync | **Lettuce reactive** |
| `RestTemplate` | `WebClient` |
| `InputStream` | `DataBuffer` flux |
| JPA / Hibernate | **nothing equivalent** — R2DBC is closer to JDBC than to JPA |

That last row is a real cost: **there is no reactive JPA.** You write SQL.

**BlockHound** detects violations at runtime, and you should treat it as
mandatory:

```java
BlockHound.install();
// throws: reactor.blockhound.BlockingOperationError:
//         Blocking call! java.net.SocketInputStream#socketRead0
```

---

## Backpressure — the thing virtual threads don't have

This is the genuinely distinctive capability, and it's usually under-sold.

```java
Flux<Message> stream = redis.receive(streamKey);     // producer
stream.subscribe(this::deliverToClients);            // consumer
```

If the producer emits faster than the consumer handles, what happens?

- **With virtual threads:** work queues up in a `ThreadPoolTaskExecutor`'s queue.
  If unbounded (the default — Module 04), your heap absorbs the difference until
  it can't. There is no signal back to the producer.
- **With Reactor:** the subscriber **requests** N items. The producer sends at
  most N. This is a first-class protocol between the two ends
  (`Subscription.request(n)`), and it propagates all the way back.

```java
stream
  .onBackpressureBuffer(1000,
        dropped -> droppedMessages.increment(),      // you SEE the loss
        BufferOverflowStrategy.DROP_OLDEST)
  .limitRate(100)                                    // request 100 at a time
  .subscribe(this::deliver);
```

You can express: buffer up to N; then drop oldest / drop latest / error /
propagate the pressure upstream. Each is a **stated policy**, not an emergent
consequence of a queue size you forgot to set.

> **This is the strongest argument for reactive in a fan-out system.** Module 06
> broke Pulse by filling an unbounded outbound queue. Backpressure makes that a
> policy decision instead of an outage.

You can build the same thing with virtual threads and a bounded queue with a
rejection handler — Module 04 did. The difference is that Reactor makes it the
default shape rather than something you must remember.

---

## Context propagation: the ergonomic tax

With virtual threads, `ThreadLocal` works. Security context, MDC logging, trace
IDs — all follow the thread naturally.

On an event loop, **there is no thread affinity**. One thread handles thousands
of requests, interleaved. `ThreadLocal` is not just wrong, it's dangerous — you
can read another user's security context.

Reactor's answer is the `Context`, carried in the subscription:

```java
return doWork()
    .contextWrite(ctx -> ctx.put("userId", userId))
    // ... twelve operators later ...
    .flatMap(x -> Mono.deferContextual(ctx ->
            handle(x, ctx.get("userId"))));
```

Spring Boot 3 bridges this to MDC and to `SecurityContextHolder` via
`ContextSnapshot`, which helps considerably — but it must be explicitly wired,
and **anything you forget silently loses the context** rather than failing.

Practical consequence: logging. `log.info("sending message")` in a virtual-thread
app carries the request's MDC automatically. In WebFlux it carries whatever the
event loop happens to have, which is usually nothing.

---

## Debugging

```
reactor.core.publisher.Operators$MonoSubscriber.onError
reactor.core.publisher.MonoFlatMap$FlatMapMain.onError
reactor.core.publisher.FluxMap$MapSubscriber.onError
...forty more frames of Reactor internals...
```

Where did this come from? The stack trace describes the **assembly** of the
pipeline, not the path through your code.

Mitigations:
```java
Hooks.onOperatorDebug();                    // full assembly traces — VERY slow
ReactorDebugAgent.init();                   // bytecode instrumentation, ~free
.checkpoint("sendMessage:persist")          // manual breadcrumbs
```

`ReactorDebugAgent` is the right default and genuinely helps. But there is an
irreducible difference: with virtual threads, a stack trace shows you the call
path, because there *is* one.

---

## What to expect from the benchmark

Reactive should win on:
- **Connections per gigabyte** — no per-connection stack at all.
- **Sustained throughput** at very high connection counts.
- Backpressure behaviour under overload.

Virtual threads should win on:
- **Development and debugging time.**
- p50 latency at moderate load (fewer scheduling hops).
- Compatibility with the entire blocking ecosystem (JPA, JDBC, most libraries).

**The interesting question is the size of the gap.** Before Java 21 it was
enormous — that's why reactive existed. Module 15's whole point is to find out
what it is now.

---

## Where this leaves the ecosystem

An honest framing, because there's a lot of noise:

- Virtual threads did **not** make reactive obsolete. Backpressure and streaming
  composition are real capabilities with no direct equivalent.
- Reactive is **no longer the only way** to get high connection density on the
  JVM, which was previously its main selling point and the reason most teams
  adopted it.
- **The efficiency argument narrowed dramatically; the composition argument did
  not.** If you're on reactive for backpressure and stream operators, stay. If
  you're on it because "blocking doesn't scale," measure — that premise changed
  in September 2023.

---

## What's next

The lab rebuilds Pulse's hot path in WebFlux with R2DBC and reactive Lettuce,
installs BlockHound and catches a real violation, then runs the identical k6
workload against both and compares connections/GB, latency at every percentile,
and behaviour past the knee.

See you in [`lab.md`](./lab.md).
