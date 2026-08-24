# Module 07 — Scaling Out with the Redis Channel Layer

**Goal:** Break Module 04's wall with `channels_redis` — get your other seven
cores, measure exactly what the Redis hop costs, and then deliberately prove
that the thing you just built **loses messages**, so you know precisely what
at-most-once delivery is worth.

⏱️ ~5 hours · **Prerequisites:** Modules 00–06. You need the baseline from
[Module 06](../06-load-testing-harness/) — every number here is a comparison
against it.

---

## The problem, restated precisely

Module 04 Part H ended with `u0` on worker 53002 and `u1` on worker 53003, in
the same room, permanently invisible to each other. The reason is not a bug:

```
              one 8-core machine, uvicorn --workers 2

   worker pid 53002                      worker pid 53003
   ┌─────────────────────────────┐       ┌─────────────────────────────┐
   │ InMemoryChannelLayer        │       │ InMemoryChannelLayer        │
   │   groups = {                │       │   groups = {                │
   │     "room.7": {             │       │     "room.7": {             │
   │        "…!QK7pZm": t        │       │        "…!Lw9xRt": t        │
   │     }                       │       │     }                       │
   │   }                         │       │   }                         │
   └─────────────────────────────┘       └─────────────────────────────┘
        heap of process 53002                 heap of process 53003
                │                                     │
                └──────────── no path ────────────────┘
```

Two `dict`s in two address spaces. There is no code that could join them,
because there is no shared memory between OS processes.

**And on the JVM this would have been optional.** One JVM uses all eight cores
from one heap; the equivalent wall only appears when you deploy a *second
machine*. Python's GIL means eight cores is eight processes, so
**you need a cross-process channel layer to use your second CPU core** — not
your second server. That is the sentence this whole module earns.

The Module 06 baseline is a **one-core** number for exactly this reason:
p50 11 ms, p99 138 ms, and a knee at **≈150,000 outbound msg/s**. The other
seven cores are behind a network hop.

---

## The shape of the fix

```
                 alice                              bob
                   │                                 │
              ┌────▼───────┐                   ┌─────▼──────┐
              │ worker A   │                   │  worker B  │
              └────┬───────┘                   └─────▲──────┘
                   │ 1. group_send("room.7", …)      │ 4. local fan-out to
                   │                                 │    B's own sockets
              ┌────▼─────────────────────────────────┴────┐
              │                   Redis                    │
              │  2. one write per WORKER with a subscriber  │
              │  3. each worker's receive loop wakes        │
              └─────────────────────────────────────────────┘
```

The critical property, and the one people get wrong when they estimate Redis
capacity:

> **`group_send` costs one Redis operation per *worker process* that holds a
> subscriber — not one per room member.**

A 200-member room spread over 8 workers costs **8** Redis writes, not 200. The
199-way fan-out still happens, but it happens inside each worker, on its own
core, exactly as it did in Module 06. Redis moves the message **between
processes**; your event loop still moves it **to sockets**.

So the in-process fan-out does not go away — it gets a friend. And the CPU cost
you measured and tuned in Module 06 is still there, per worker, unchanged.

---

## `channels_redis` ships two layers, and they are not variants

This is the module's first real decision, and most tutorials skip it.

### `channels_redis.core.RedisChannelLayer` — mailboxes in sorted sets

```python
CHANNEL_LAYERS = {"default": {
    "BACKEND": "channels_redis.core.RedisChannelLayer",
    "CONFIG": {"hosts": [{"address": "redis://localhost:6379/0"}]}}}
```

Decompiled to its essentials:

| Operation | What Redis actually does |
|-----------|--------------------------|
| `group_add(g, ch)` | `ZADD asgi:group:<g> <now> <ch>` then `EXPIRE … 86400` |
| `group_discard(g, ch)` | `ZREM asgi:group:<g> <ch>` |
| `group_send(g, msg)` | `ZREMRANGEBYSCORE` (drop expired members) → `ZRANGE` (read every member) → group them **by worker** → one `EVAL` that `ZADD`s the msgpack'd message into each worker's mailbox ZSET and `EXPIRE`s it |
| receive loop | one `BZPOPMIN` per worker, plus a `$inflight` backup ZSET so a cancelled receive does not lose the message |

Two consequences worth pinning to the wall:

- **The message is *stored*.** It sits in a ZSET until a worker pops it or
  `expiry` (default 60 s) passes. That is meaningfully better than fire-and-forget
  — and still not at-least-once, for reasons three sections down.
- **Group membership lives in Redis.** `asgi:group:room.7` is server-side state
  with an 86,400-second TTL. When Redis restarts, *that state is gone* and
  nothing rebuilds it, because the consumers that would call `group_add` are
  already connected and will never call it again. Remember this; the lab makes
  it happen.

### `channels_redis.pubsub.RedisPubSubChannelLayer` — actual Pub/Sub

```python
CHANNEL_LAYERS = {"default": {
    "BACKEND": "channels_redis.pubsub.RedisPubSubChannelLayer",
    "CONFIG": {"hosts": ["redis://localhost:6379/0"]}}}
```

| Operation | What Redis actually does |
|-----------|--------------------------|
| `group_add(g, ch)` | `SUBSCRIBE asgi__group__<g>` — **once per worker**, tracked in a process-local `dict` |
| `group_discard(g, ch)` | remove from the local dict; `UNSUBSCRIBE` when the last local member leaves |
| `group_send(g, msg)` | **one `PUBLISH`.** That is the entire operation. |
| receive loop | `pubsub.get_message()`, then `put_nowait` into a per-channel `asyncio.Queue` |

- **Cheaper per send** — one `PUBLISH` versus a `ZRANGE` + `EVAL`, and no
  server-side membership to read.
- **Group membership is in-process**, so a Redis restart self-heals: `redis-py`
  re-subscribes and the local dict was never lost.
- **The per-channel queue is `asyncio.Queue()` with no `maxsize`.** There is no
  capacity, no backpressure, and no over-capacity signal. Module 06's slow
  consumer takes the worker's heap with it, and nothing counts it.

### The comparison you have to make yourself

| | `RedisChannelLayer` (core) | `RedisPubSubChannelLayer` |
|---|---------------------------|---------------------------|
| Delivery | at-most-once (stored, 60 s, unacked) | **at-most-once** (never stored) |
| Redis ops per `group_send` | `ZRANGE` + 1 `EVAL` over W keys | **1 `PUBLISH`** |
| Membership lives | in **Redis** (ZSET, 24 h TTL) | in the **worker** (dict + SUBSCRIBE) |
| Survives a Redis restart | ❌ groups vanish, silently, forever | ✅ re-subscribes |
| Slow-consumer bound | `capacity` per mailbox, **logged not raised** | ❌ **none** |
| Message ordering | per-mailbox, arrival order | per-channel, arrival order |
| Redis memory | mailboxes + group ZSETs | ~0 |

Pulse takes **`RedisChannelLayer`** as `CHANNEL_LAYERS["default"]` and
**`RedisPubSubChannelLayer`** as a second, explicitly-named `"ephemeral"` layer.
The reasoning, and the condition that would change it, are the subject of the
lab's Part E — and the answer is *not* obvious, which is why you measure it
rather than accept it.

---

## Pub/Sub semantics, stated exactly

```bash
SUBSCRIBE room.7
PUBLISH room.7 '{"type":"message.new",…}'
(integer) 2                # number of subscribers it WROTE BYTES TO
```

Redis keeps a `dict` of channel → list of client connections. `PUBLISH` walks
the list and writes to each socket. That is the whole implementation, which
tells you its properties exactly:

| Property | Value |
|----------|-------|
| Delivery | **At-most-once** |
| Persistence | **None.** Not written anywhere, ever. |
| Replay | **Impossible.** There is nothing to replay from. |
| Acknowledgement | None. `PUBLISH` returns a count, not a guarantee. |
| Latency | Microseconds. It is a socket write. |
| Backpressure | A slow subscriber fills `client-output-buffer-limit pubsub`, then is **disconnected** |

**The return value lies to you.** `(integer) 2` means "I wrote these bytes to
two sockets." If a subscriber's TCP connection dies between the write and the
read, the message is gone and `PUBLISH` still said `2`. And if it returns `0`,
Redis does not care — nothing is stored, nothing retries.

**The core layer is not exempt.** Its message *is* stored, so it survives a
subscriber being briefly busy. It does not survive:

- the `EVAL` failing because Redis was unreachable (Channels does not retry);
- `expiry` seconds passing with no worker popping it;
- a mailbox at `capacity` — the `EVAL` **skips** that mailbox and `group_send`
  logs `"N of M channels over capacity in group G"` at **INFO**, then returns
  successfully;
- Redis restarting, which takes the group ZSETs with it.

Four silent-loss paths, none of which raise. **At-most-once is the documented
contract for both layers.** The bug would be shipping chat on top of it and
assuming otherwise.

---

## The failure you will demonstrate

```
t=0    worker B holds bob's connection, subscribed to room.7
t=1    Redis is paused (a GC pause, a failover, a network partition — they
       all look like this from the client's side: a hang, not an error)
t=2    alice sends; worker A's group_send hits its socket timeout and raises
t=3    Channels logs the exception; the ASGI application returns
t=4    Redis resumes; A and B reconnect cleanly
t=5    bob never receives the t=2 message, and never will
```

**Nothing you would page on happened.** No data was corrupted, no invariant was
violated, no alert fired. Bob just... does not have a message, and the first
report you get is "chat drops messages sometimes" — the worst bug report in
software.

The lab makes it deterministic with `docker pause` and counts exactly what is
lost: **29 of 200 messages, 14.5%**, with `chat_messages_outbound_total` cheerfully
reporting all 200 as delivered.

That number is what
[`09-redis-streams-delivery`](../09-redis-streams-delivery/) exists to take to
zero, and it costs +5 ms p50 and ~600 bytes of Redis per message to do it. You
cannot judge whether that is a good trade until you have measured the 14.5%.

---

## When at-most-once is exactly right

Do not over-learn the lesson. Most chat traffic *should* be on this layer:

| Traffic | Semantics needed | Why |
|---------|-----------------|-----|
| **Typing indicators** | At-most-once ✅ | Superseded in 3 s. A lost one is invisible. |
| **Presence join/leave** | At-most-once ✅ | TTL-based state (Module 11); the next heartbeat repairs it. |
| **Cursor / scroll position** | At-most-once ✅ | Latest value wins. |
| **Live viewer count** | At-most-once ✅ | Approximate by nature. |
| **Chat messages** | At-least-once ❌ | A permanent hole in history. |
| **Read receipts** | At-least-once-ish | Monotonic, so a loss self-heals — but users notice. |
| **Membership revocation** | At-least-once ❌ | A missed "you were removed" is a security hole. |

Pulse ends up running **both**: the channel layer for the top group, Streams for
the bottom. `pulse-protocol-v1.md` already anticipates the split — it says
typing traffic "MUST NOT be given durable delivery" — and the routing decision
is made **per message type**, not per system. Being able to defend that split is
the point of this module.

---

## Subscription amplification, Python flavour

Here is the scaling trap that arrives *with* the backplane.

Every worker holding a subscriber to a room must receive every message for that
room. With users distributed randomly:

```
Redis writes per message  =  workers that hold at least one subscriber
```

The JVM twin says "instances". You have to say **worker processes**, and there
are eight per box:

```
1,000 rooms, 200 members each, 3 machines x 8 workers = 24 processes
users spread randomly
  -> nearly every room has a subscriber in nearly every process
  -> every message is written by Redis 24 times
```

At 24× a message that would have cost one write costs 24. **You have moved the
wall, not removed it** — and you hit it at one-eighth the machine count a JVM
shop would.

The escape hatches all exist and all appear later:

- **Sharded Pub/Sub** (`SSUBSCRIBE`/`SPUBLISH`, Redis 7) routes by hash slot so
  only the owning cluster node fans out — [Module 18](../18-compose-ha-and-chaos/).
- **Room affinity**: consistent-hash rooms onto a subset of workers so a room
  reaches 3 processes, not 24 — [Module 14](../14-sharding-and-wide-column/).
- **Fan-out on read** for large rooms: stop pushing entirely.

The challenge measures the amplification at 1, 2, 4 and 8 workers and
extrapolates the wall.

---

## Sticky sessions: still needed?

With a shared backplane, must the load balancer pin a client to one worker?

**Strictly, no.** Any worker can serve any user; messages reach all of them.

**Practically, yes, for three reasons that are all weaker than people assume:**

1. **Local session state.** The consumer object, its `scope`, and the socket
   itself live in one process. A client cannot be *moved* — only disconnected
   and reconnected.
2. **Reconnect locality.** A client that lands on the same worker finds a warm
   dedup cache and an existing presence entry.
3. **Debuggability.** "Which process is this user on?" has an answer.

And stickiness has a real, measurable cost you will feel in Module 18: **it
makes rolling deploys drop connections**, because draining a worker necessarily
disconnects everyone pinned to it.

```nginx
upstream pulse {
    # ip_hash;                     # modulo, not consistent: N changes remap ~all
    hash $cookie_pulse_node consistent;
}
```

`ip_hash` is a modulo scheme *and* it clumps: every user behind one corporate
NAT lands on one worker. The lab measures both, and the challenge quantifies
what stickiness actually buys.

---

## Why not something else?

| Option | Gets you | Costs you |
|--------|----------|-----------|
| **`channels_redis`** (this module) | Cross-process fan-out for one settings dict; reuses the Redis you already need for sequences, presence, rate limits, tickets | You implement delivery guarantees yourself (Module 09) |
| **RabbitMQ** via a custom layer | Real ack semantics, durable queues, mature ops story | A second stateful system, its own HA and partition semantics, two extra hops, and **you would still write the channel layer** — Channels has no RabbitMQ backend |
| **Kafka** (Module 16) | Durable log, replay from any offset | Heavy for fan-out; rebalances stall consumption; high fixed ops cost |
| **`multiprocessing.Manager` / shared memory** | No extra process | You have now written a channel layer — serialization, liveness, cleanup, backpressure — badly, and only for one machine |
| **Room→worker affinity, no shared layer** | No Redis at all | A user in twelve rooms needs twelve sockets on twelve workers; one hot room melts one core while seven idle |

Pulse chooses Redis because **it already needs Redis**, and because having the
semantics be explicit and inspectable is the entire point of this course. Once
you have built at-least-once yourself (Module 09), choosing a managed broker
later is an informed decision instead of a hope.

> **A note on `redis-py` and Pub/Sub.** In RESP2, a connection in subscribe mode
> may only run subscribe-related commands, so the Pub/Sub layer needs **at least
> two connections**: one subscriber, one for everything else. `redis-py` handles
> this for you, and [Module 08](../08-redis-internals/) shows you the RESP3 push
> type that removes the requirement entirely.

---

## What's next

The lab swaps one settings dict and re-runs Module 04's `crosstalk` test at
100%; measures the cost of the hop (**+4 ms p50**) and the scaling factor
(**1.9×, not 2×** — and explains where the missing 5% went); puts nginx in front
with cookie-based consistent hashing; runs a head-to-head between the two
channel layers; and then **pauses Redis under load and counts the messages that
disappear**.

See you in [`lab.md`](./lab.md).
