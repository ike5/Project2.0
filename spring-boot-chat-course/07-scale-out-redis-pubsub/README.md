# Module 07 — Scaling Out: Pub/Sub Fan-Out

**Goal:** Break the single-node wall with a Redis backplane — and then
deliberately prove that the solution you just built **loses messages**, so you
understand exactly what at-most-once delivery costs.

⏱️ ~5 hours · **Prerequisites:** Modules 00–06.

---

## The problem, restated precisely

Module 04 Part I ended with alice on instance A and bob on instance B, unable to
see each other. The reason is not a bug:

```
   instance A                          instance B
   ┌──────────────────────┐            ┌──────────────────────┐
   │ SimpleBroker         │            │ SimpleBroker         │
   │  subscriptions:      │            │  subscriptions:      │
   │   /topic/room.7 ─▶   │            │   /topic/room.7 ─▶   │
   │      [alice-sess]    │            │      [bob-sess]      │
   └──────────────────────┘            └──────────────────────┘
        heap of JVM A                       heap of JVM B
              ▲                                    ▲
              └──────────── no path ───────────────┘
```

Two `ConcurrentHashMap`s in two separate processes. There is no code that could
connect them, because there is no shared memory between JVMs.

**What you need is a message bus that both instances speak to.**

---

## The shape of the fix

```
                 alice                              bob
                   │                                 │
              ┌────▼─────┐                     ┌─────▼────┐
              │instance A│                     │instance B│
              └────┬─────┘                     └─────▲────┘
                   │ 1. PUBLISH room.7                │ 4. local broker
                   │                                  │    fan-out
              ┌────▼──────────────────────────────────┴────┐
              │                   Redis                    │
              │  2. deliver to every subscriber of room.7  │
              └────────────────────────────────────────────┘
                   │ 3. both instances receive it
              ┌────▼─────┐                     ┌──────────┐
              │instance A│                     │instance B│
              └──────────┘                     └──────────┘
```

The critical detail: **every instance subscribes to every room it has a local
subscriber for.** When a message arrives from Redis, the instance hands it to its
*own* simple broker, which fans out to its *own* local sessions.

So the simple broker doesn't go away — it gets a friend. Spring's broker still
does what it's good at (fast local fan-out); Redis does what the broker can't
(crossing process boundaries).

---

## Why not just use a real broker?

Module 04's challenge had you try RabbitMQ's STOMP relay, and it worked. So why
build this?

| Option | Gets you | Costs you |
|--------|----------|-----------|
| **STOMP relay (RabbitMQ)** | Cross-instance fan-out for 10 lines of config, real ACK semantics, durable queues | A second stateful system, Erlang ops, its own HA/partition semantics, two extra network hops per message |
| **Redis backplane** (this course) | Reuses Redis you already need; explicit, inspectable semantics you control | You implement delivery guarantees yourself |
| **Kafka** (Module 16) | Durable log, replay from any offset, huge throughput | Heavy for fan-out; partition rebalances stall consumption; high ops cost |
| **Hazelcast / Ignite** | Embedded, no extra process | Cluster membership inside your app's JVM; split-brain becomes *your* problem |

Pulse chooses Redis because **it already needs Redis** — presence, rate limits,
unread counts, dedup — and because the semantics being explicit is the point of
this course. Once you've built at-least-once yourself, choosing a managed broker
later is an informed decision instead of a hope.

---

## Redis Pub/Sub: what it actually does

```bash
SUBSCRIBE room.7
PUBLISH room.7 '{"type":"message.new",...}'
(integer) 2                # <- number of subscribers that RECEIVED it
```

Redis maintains a `dict` of channel → list of client connections. `PUBLISH` walks
that list and writes to each socket. That's the whole implementation.

Which tells you its properties exactly:

| Property | Value |
|----------|-------|
| Delivery | **At-most-once** |
| Persistence | **None.** Not written anywhere, ever. |
| Replay | **Impossible.** There is nothing to replay from. |
| Acknowledgement | None. `PUBLISH` returns a count, not a guarantee. |
| Latency | Microseconds. It's a socket write. |
| Memory | ~zero |
| Backpressure | A slow subscriber gets buffered up to `client-output-buffer-limit pubsub`, then **disconnected** |

### The return value lies to you

```bash
PUBLISH room.7 "hello"
(integer) 2
```

That `2` means "I wrote these bytes to 2 sockets." It does **not** mean two
clients processed the message. If a subscriber's TCP connection dies between the
write and the read, the message is gone and `PUBLISH` still said `2`.

And if it returns `0`, Redis does not care. Nothing is stored. Nothing retries.

---

## The failure you will demonstrate

```
t=0    instance B subscribed to room.7, holding bob's connection
t=1    network blip; B's Redis connection drops
t=2    alice sends a message; A publishes it; Redis has 1 subscriber, writes to it
t=3    B reconnects and re-SUBSCRIBEs
t=4    bob never receives the t=2 message, and never will
```

**Nothing errored.** `PUBLISH` returned 1. A's logs are clean. B's logs show a
reconnect at INFO level. Bob just... doesn't have a message, and nobody knows.

This is the single most important thing to internalize about Pub/Sub, and the lab
makes it happen deterministically with `docker pause`.

**It is not a Redis bug.** At-most-once is the documented contract. The bug would
be shipping chat on top of it.

---

## When at-most-once is exactly right

Don't over-learn the lesson. Pub/Sub is the correct choice for a lot of chat
traffic:

| Traffic | Semantics needed | Why |
|---------|-----------------|-----|
| **Typing indicators** | At-most-once ✅ | Superseded in 3 s. A lost one is invisible. |
| **Presence blips** | At-most-once ✅ | TTL-based state; the next heartbeat repairs it. |
| **Cursor / scroll position** | At-most-once ✅ | Latest value wins. |
| **Live viewer count** | At-most-once ✅ | Approximate by nature. |
| **Chat messages** | At-least-once ❌ | A permanent hole in history. |
| **Read receipts** | At-least-once-ish | Monotonic, so a loss self-heals — but users notice. |
| **Room membership changes** | At-least-once ❌ | A missed "you were removed" is a security hole. |

Pulse ends up using **both**: Pub/Sub for the top group, Streams for the bottom.
That split is a design decision made on delivery semantics, and being able to
articulate it is the point.

---

## Sticky sessions: still needed?

With a shared backplane, does the load balancer still need to pin a client to one
instance?

**Strictly, no.** Any instance can serve any user, because messages reach all of
them.

**Practically, yes**, for three reasons:

1. **Local session state.** The `WebSocketSession` object, the subscription
   registry, and the outbound buffer live in one JVM. A client can't be
   *moved* — only disconnected and reconnected.
2. **Reconnect locality.** If a reconnecting client lands on the same node, its
   presence entry and dedup cache are warm.
3. **Debuggability.** "Which node is this user on?" has an answer.

But stickiness has a real cost you'll feel in Module 18: **it makes rolling
deploys drop connections**, because draining a node necessarily disconnects
everyone pinned to it.

```nginx
upstream pulse {
    ip_hash;                    # simple, breaks behind carrier NAT
    # better: hash $cookie_pulse_node consistent;
}
```

`ip_hash` puts every user behind one corporate NAT on one node. Use a
cookie-based consistent hash in production; the lab shows both.

---

## The subscription amplification problem

Here's a scaling trap that arrives with the backplane, and which Module 13
exists to solve. Note it now.

Every instance must subscribe to every room that has a local subscriber. With
users distributed randomly across N instances:

```
1,000 rooms, 3 instances, users spread evenly
  → nearly every room has a subscriber on every instance
  → all 3 instances subscribe to all 1,000 rooms
  → every message is delivered by Redis 3 times
```

```
Redis outbound = inbound × instances_with_a_subscriber
```

At 3 instances that's a 3× tax — annoying. At 30 instances it's a 30× tax, and
Redis becomes the bottleneck instead of your JVM. You've moved the wall, not
removed it.

**The fixes** (all in Module 13): sharded Pub/Sub (`SSUBSCRIBE`), routing rooms
to a subset of instances, or a consistent-hash assignment of rooms to nodes.

---

## Lettuce, and why the connection model matters

Spring Boot's default Redis client is **Lettuce** (Netty-based, thread-safe, one
connection multiplexed across many threads). Jedis needs a connection per thread.

For a socket server with thousands of virtual threads, Lettuce's multiplexing is
the right shape — you don't want 10,000 Redis connections.

**But Pub/Sub is special:** a connection in subscribe mode can only run
subscribe-related commands. So you need **at least two** connections: one
subscriber, one for normal commands. Spring's
`RedisMessageListenerContainer` manages the subscriber connection and its own
thread pool for dispatching messages — and that thread pool is another place a
queue can build up. Size it deliberately.

---

## What's next

The lab wires the backplane, proves alice and bob can finally see each other,
re-runs Module 06's benchmark to measure the cost of the Redis hop — then
**deliberately loses a message** and measures how many.

See you in [`lab.md`](./lab.md).
