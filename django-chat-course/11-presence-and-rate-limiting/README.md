# Module 11 — Presence, Typing & Rate Limiting

**Goal:** Build the state that isn't messages — who is online, who is typing, who
is sending too much — and understand why presence is routinely the *most
expensive* subsystem in a chat product despite carrying the least valuable data.

⏱️ ~5 hours · **Prerequisites:** Modules 00–10.

---

## Presence is soft state with no source of truth

Every other piece of state in Pulse has an owner. A message is owned by Postgres.
A sequence number is owned by the Redis counter, with Postgres as the recovery
floor. A read cursor is owned by `chat_readcursor`.

Presence has no owner, and this is not a design failure — it is the nature of the
thing. "Alice is online" is a claim about the *present moment* on a machine you do
not control, communicated over a network that can drop the retraction. The question
"is Alice online?" has no answer that is true for longer than it takes to ask.

So presence is **soft state**: a claim with an expiry date, refreshed by whoever
made it, and correct by construction only in the sense that it is never *wrongly
durable*. Once you accept that framing, every design decision follows from it.

### Why the obvious design is wrong

```python
async def connect(self):
    await redis.set(f"presence:{self.user.id}", "online")     # on connect

async def disconnect(self, code):
    await redis.delete(f"presence:{self.user.id}")            # on disconnect
```

This is Module 09's lesson in a new costume: **the disconnect event is not
guaranteed to happen.** A `kill -9` on the worker, an OOM kill, a NAT table
eviction, a laptop lid closing on a train — and that key says `online` forever.
Worse, in Channels specifically:

- `disconnect()` runs in the same event loop as the socket. If the worker process
  dies, it never runs at all.
- If the *client* vanishes without a close frame, Uvicorn does not notice until
  TCP gives up, which by default is minutes.
- If `disconnect()` raises — say, Redis is briefly unreachable — Channels logs it
  and moves on. Your cleanup is gone and nothing retried it.

**Any cleanup that depends on a graceful event is a leak.** This is the third time
this course has said that, and it will not be the last.

### The correct design: liveness, not events

```
SET presence:{user}:{channel} 1 EX 30       # refreshed by every heartbeat
```

- The client heartbeats every **10 s** (protocol §3.4 — a `ping` frame inside the
  data channel, not a WebSocket control frame, because some proxies strip those).
- The TTL is **30 s** — three missed beats.
- A crashed worker's users go offline automatically, with no cleanup code
  anywhere.
- The state is *derived from liveness*, not from an event you hope arrives.

The ratio matters. TTL = 3× heartbeat is the standard choice: one lost heartbeat
must not flap a user offline, and three missed beats is a strong signal. Tighten it
to 2× and a single GC pause on the client — or one dropped frame — produces a
visible flicker. Loosen it to 6× and a crashed node's users linger for a minute,
which users read as the product being broken.

### Detecting the *transition*

TTL expiry gives you the state. It does not give you the event, and you need the
event to tell other people.

**Tempting and wrong: keyspace notifications.**

```bash
redis-cli CONFIG SET notify-keyspace-events Ex
redis-cli SUBSCRIBE '__keyevent@0__:expired'
```

Three reasons this fails in production, and the lab measures all three:

1. **It is Pub/Sub** — at-most-once, exactly the delivery semantic Module 07 proved
   loses messages. A worker that is reconnecting misses the expiry, and that user
   stays green forever with nothing to correct it.
2. **The event fires when Redis actually deletes the key**, which for the lazy
   expiration path can be long after the TTL elapsed. The lab measures p50 **0.4 s**
   and p99 **22 s** for a key nobody touches.
3. **In Redis Cluster the event fires on the node owning the key**, so only
   subscribers of that node hear it — and Module 18 moves you to Cluster.

There is a fourth reason that is specific to Django, and it is the one that
settles it: **you would need one subscriber per worker process.** Eight workers per
box means eight connections each receiving *every* expiry event in the entire
system, filtering out the 99.9% that concern rooms they do not serve. That is the
process-per-core model turning a cheap idea into an expensive one, which is a
pattern you should now recognize on sight.

**What Pulse does instead: compute presence on read, on a timer, per worker.**

Every worker already knows which rooms it serves (Module 09's `LocalRegistry`).
Once a second, for each of those rooms, it reads the room's presence set from
Redis, diffs it against what it announced last, and sends `presence.update`
**only to its own local sockets**.

```
worker-a  ──1 Hz──▶  ZREMRANGEBYSCORE + ZRANGE room:{room.7}:presence
                     diff vs last announced
                     send to local sockets in room.7 only

worker-b  ──1 Hz──▶  the same read, the same diff, its own local sockets
```

No cross-worker fan-out at all. Every worker independently computes the same
answer from the same Redis key, which is cheap (`O(log N + M)`) and — importantly
— **cannot get permanently stuck.** A worker that misses a tick recomputes
correctly on the next one. Compare with an event-driven design, where one lost
notification is wrong until something else happens to fix it.

---

## The presence storm

Here is the arithmetic that makes presence the most expensive subsystem you own.
Use Module 06's measured baseline: **20,000 connections, 100 rooms, 200 members per
room**, and assume the realistic case where a user belongs to ~20 rooms.

```
One user comes online, naive broadcast:
    20 rooms × 199 others = 3,980 notifications

All 20,000 come online after a deploy, spread over the 34 s that full-jitter
reconnect takes (Module 10):
    20,000 × 3,980           = 79,600,000 notifications
    79,600,000 / 34 s        = 2,341,000 messages/second
```

The pinned single-node fan-out knee is **150,000 outbound messages/second**
(Module 06). Presence alone wants **15.6× that** — for data whose entire semantic
content is a coloured circle, at exactly the moment your system is most fragile.

This is not a Python problem; the JVM twin gets the same shape with a bigger knee.
It is a *fan-out arithmetic* problem, and there is no runtime fast enough to make
`N × M` small.

### Four mitigations, and what each is worth

| Technique | What it changes | Frames/s during the storm |
|-----------|-----------------|---------------------------|
| Naive: one frame per user per change per room | — | 2,341,000 |
| **Aggregate + debounce to 1 Hz per room** | outbound depends on *time*, not on the number of changes | 400,000 |
| **Only the room the user is looking at** | 20 rooms → 1 | **20,000** |
| **Suppress above `PULSE_PRESENCE_MAX_MEMBERS` (500)** | large rooms get no presence at all | 20,000 |

**117× total**, and the second row is the structurally important one: aggregation
makes the worst case *bounded*. Twenty typers or two thousand, it is one frame per
room per second. A hard bound on the worst case is worth more than a large
improvement in the average case, because the worst case is when you get paged.

The fourth row deserves defending rather than apologizing for. Nobody meaningfully
consumes the online status of 5,000 people. Above a few dozen members the green
dots are decoration, and Slack, Discord and Teams all quietly stop sending them.
Say so in your design doc instead of pretending it is a bug you did not get to.

```
presence traffic = min(room_size, viewport) × changes/sec × rooms_visible
```

Only the first and last factors are under your control, and the last one is a
one-line change.

---

## Typing indicators: the highest-volume, lowest-value traffic

Module 05 designed the protocol (`typing.start` C→S, rate-limited to 1 per 3 s per
room; `typing.update` S→C, aggregated to at most 1 frame per room per second). The
numbers justify it:

| Design | Frames for 20 typers in a 200-member room over 60 s |
|--------|---------------------------------------------------|
| Every keystroke, broadcast individually | 1,200,000 |
| Debounced 3 s, broadcast individually | 80,000 |
| **Debounced + aggregated at 1 Hz** | **12,340** |

Typing rides the **channel layer** (`group_send`), not Streams — Module 09's
routing rule. It is at-most-once, superseded within three seconds, and putting it
in a durable log would multiply your Redis memory by roughly 10× to protect data
whose value expires before anyone reads it.

---

## The `group_expiry` trap

This is the Django-specific footgun of the module, and it is nastier than it looks
because Module 09 arranged for it to be invisible.

`channels_redis`' `RedisChannelLayer` stores group membership as a Redis sorted
set (`asgi:group:<name>`), with the member's channel name as the value and a
timestamp as the score. Two settings govern it:

| Setting | Default | What it does |
|---------|---------|--------------|
| `expiry` | **60 s** | A message sitting in a channel's queue longer than this is discarded |
| `group_expiry` | **86400 s** | A group *membership* older than this is discarded |

`group_expiry` means: **a socket that has been in a group for 24 hours stops
receiving group messages**, silently, unless something re-adds it. Channels 4
refreshes the membership timestamp on `group_add`, so the fix is to call
`group_add` again periodically — but nothing does that for you.

Now the part that makes it hard to catch. Module 09 moved *messages* off the
channel layer onto Redis Streams. What still rides `group_send`? Typing, presence,
read receipts — **all the ephemeral traffic.** So the symptom of a `group_expiry`
expiry is not "chat broke." It is:

> "Presence seems to stop updating for some people. It's fine after they refresh."

Nobody files that ticket. It sits in your product for a year.

**Pulse's fix, both halves:**

```python
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [os.environ["REDIS_URL"]],
            # Must exceed your longest expected socket lifetime. Ours is bounded
            # by Module 18's drain policy at ~6 hours, so 12 h is 2x headroom.
            "group_expiry": 43_200,
            # 60s is right for messages: a frame that has been queued for a
            # minute is worthless in a chat product. Do not raise this to "fix"
            # a slow consumer — Module 04 already showed that the correct answer
            # is to drop the connection, not to buffer it.
            "expiry": 60,
        },
    }
}
```

and re-add on every heartbeat, which you are already receiving every 10 seconds:

```python
async def _on_ping(self, content):
    await self.channel_layer.group_add(self.room.key, self.channel_name)  # refresh
    await self._touch_presence()
    await self.send_json({"v": 1, "type": "pong", ...})
```

The re-add is one `ZADD` plus one `EXPIRE` — at 20,000 connections heartbeating
every 10 s that is 2,000 ops/s against a Redis that does six figures. Cheap
insurance against a bug you cannot detect.

> **Module 18 revisits this**, because a graceful drain plus a reconnect storm is
> exactly the situation where a stale group membership and a fresh one coexist,
> and the arithmetic of `group_expiry` decides how long the ghost lives.

---

## Rate limiting: token bucket, and why not the alternatives

### Fixed windows are wrong at the boundary

```
limit: 10 per minute
12:00:59 → 10 messages   ✓ allowed (window A)
12:01:00 → 10 messages   ✓ allowed (window B)
         = 20 messages in one second, from a "10 per minute" limit
```

A 2× burst at every window boundary, on schedule, which an attacker will find in
minutes.

### The three real options

| Algorithm | State per key | Accuracy | Allows a burst? | Cost |
|-----------|---------------|----------|-----------------|------|
| **Token bucket** | 2 fields (`tokens`, `updated_at`) ≈ **90 B** | exact on rate, burst is a deliberate parameter | **Yes, by design** | 1 Lua call |
| Sliding window log (ZSET of timestamps) | 1 entry per request ≈ 70 B × limit — **70 KB at limit 1,000** | exact | No | `ZREMRANGEBYSCORE` + `ZCARD` + `ZADD` |
| Sliding window counter (two fixed windows, interpolated) | 2 counters ≈ 80 B | approximate (±the interpolation error) | No | 2 `INCR` + arithmetic |

**Pulse uses the token bucket**, for a reason specific to chat: pasting three
messages at once is *legitimate user behaviour*, and a sliding window that smooths
it away makes the product feel broken. The token bucket is the only one of the
three where "allow a burst of 20, then 5 per second sustained" is expressible
directly rather than approximated.

```
capacity 20, refill 5/s

  tokens
    20 │████████████████████
       │         ╲
    10 │           ╲___          ← a burst of 10 spends half the bucket
       │               ╲___
     0 │                    ╲___ ← sustained sending drains it to zero
       └────────────────────────── time
                                   refilling at 5/s throughout
```

The sliding window log is the right answer when you must be able to *prove* the
rate over a window (billing, compliance). It is the wrong answer here: 70 KB per
user per limit, times four limit tiers, times a million users, is 280 GB of Redis
to enforce a rule the token bucket enforces in 90 bytes.

### It must be atomic, and "atomic" means Lua

```python
tokens = await redis.get(key)         # ← another coroutine runs here
if int(tokens) > 0:                   # ← and here
    await redis.decr(key)             # ← and here
```

Check-then-act across a network is a race, and with 8 worker processes × hundreds
of concurrent coroutines it is a race you lose constantly. The lab measures it:
with a limit of 1,000 and 64 concurrent senders, the non-atomic version allows
**1,412** — a **41% overshoot** — while the Lua version allows exactly 1,000.

Redis is single-threaded and a script runs to completion without interleaving
(Module 08). The same trick that fixed sequence allocation in Module 10 fixes rate
limiting here, and it is worth noticing that it is the *same* trick: **whenever
you need read-modify-write across a network, the answer is one round trip that
does all three.**

### Where to limit, and why one tier is never enough

| Tier | Key | Limit | Stops |
|------|-----|-------|-------|
| Connection handshake | `rl:conn:{ip}` | 10 / min | Reconnect storms, socket exhaustion |
| Per user, per room | `rl:msg:{user}:{room}` | 20 burst, 5/s | The obvious one |
| Per user, global | `rl:msg:{user}` | 40 burst, 10/s | Spraying one message across 100 rooms |
| Per IP | `rl:ip:{ip}` | 100 burst, 20/s | One host driving 500 accounts |
| Per room | `rl:room:{room}` | 500 burst, 200/s | One flood degrading everyone in a room |
| **Resume** | `rl:resume:{user}:{room}` | 5 burst, 0.1/s | The most expensive request a client can make (Module 10) |

A single per-user limit is trivially bypassed by attacking a different dimension —
more accounts, more rooms, more sockets. You need most of these, and the per-room
limit is the one people forget: it is the only tier that protects a room's other
members from a flood that is individually within every per-user limit.

> **A Redis Cluster caveat you must know now.** A Lua script may only touch keys in
> one hash slot. `rl:msg:{user}` and `rl:room:{room}` hash differently, so you
> **cannot** check both in one atomic script under Cluster (Module 18). Your
> options: two round trips (Pulse's choice — 0.19 ms instead of 0.11 ms, and the
> tiers are independent anyway so atomicity across them buys nothing), or force
> every limiter key into one slot with a fixed tag like `{rl}`, which makes one
> Cluster node carry 100% of limiter traffic. Measure before you pick; Pulse takes
> the second round trip.

### What to do when a limit is hit

Send the protocol's error frame (§4) and **do not close the connection**:

```json
{"v":1,"type":"error","room":"room.7","ts":1735689600123,
 "data":{"code":"rate_limited","message":"slow down",
         "retry_after_ms":2400,"client_id":"01JQ8Z…"}}
```

Three details, each of which exists because the alternative is worse:

- **`retry_after_ms`** turns a guess into a schedule. Without it, a well-behaved
  client retries on its own timer and either wastes requests or waits too long.
  Compute it from the bucket: `(cost - tokens) / refill_rate`.
- **`client_id`** lets a client with several messages in flight mark the *right*
  bubble as failed. Without it the UI has to guess, and it guesses wrong.
- **The socket stays open.** Protocol §4 is explicit: an `error` frame MUST NOT
  close the connection. Closing it triggers a reconnect, which costs a handshake,
  an auth check, a `group_add`, and a resume — you have answered "too much traffic"
  with "here, have some more." Sustained abuse escalates to close code `4429`, and
  that is Module 21's job with Module 21's evidence.

Never drop silently. A rate-limited message that vanishes with no frame produces a
client that believes it sent something it did not, which is the one failure mode
the entire delivery-semantics module existed to eliminate.

---

## Distributed locks, and why Redlock is contested

Sooner or later you will want "only one worker should do X" — run the presence
sweeper, trim the streams, create tomorrow's partition. The Redis answer:

```
SET lock:job:trim <random-token> NX PX 30000
```

On a single instance this is correct: `NX` is atomic, `PX` bounds the damage if the
holder dies, and the random token lets you release safely:

```lua
if redis.call('GET', KEYS[1]) == ARGV[1] then
    return redis.call('DEL', KEYS[1])
end
return 0
```

> ⚠️ **Never `DEL` a lock without checking the token.** If your work overran the
> TTL, the lock belongs to someone else now and a bare `DEL` releases *theirs*.

**Redlock** extends this to N independent Redis instances requiring a majority.
Martin Kleppmann's critique and Salvatore Sanfilippo's reply are both worth reading
in full; the short version:

> Redlock's safety depends on bounded clock drift and bounded process pauses.
> Neither is guaranteed. A pause longer than the lock TTL means you believe you
> hold a lock that has expired and been granted to someone else — and no amount of
> Redis quorum can detect that, because the failure is in *your* process, not in
> Redis.

Python makes this concrete in a way the JVM twin's GC discussion does not: **your
worker does not have to pause to lose the lock, it only has to be blocked.** One
synchronous ORM call in an async consumer stalls the whole event loop (Module 01;
Module 15 measures it at multiple seconds). Your lock renewal task is a coroutine
on that same loop. It does not run. The lock expires. Someone else takes it. Your
coroutine wakes up and carries on believing it holds a lock, and there is no
exception anywhere.

The practical resolutions, in order:

1. **Don't need the lock.** Usually the best option and the one Pulse takes: make
   the operation idempotent, or partition the work so each worker owns a disjoint
   slice by consistent hash (`hash(room) % worker_count == my_index`). No lock, no
   failure mode, no renewal task.
2. **Use fencing tokens.** The lock returns a monotonically increasing number and
   the protected resource rejects writes carrying a stale one. This is safe *even
   if the lock is held twice*, which is the only actually-correct answer. It
   requires the resource to cooperate, which is why it is rare.
3. **Use a real consensus system** (etcd, ZooKeeper) when correctness genuinely
   depends on it. Module 18 uses etcd for Patroni for exactly this reason.

> **The honest position:** a Redis lock is a *performance optimization* that
> usually prevents duplicate work. It is not a correctness mechanism. Design so
> that a double execution is harmless, and its failure modes stop mattering.

---

## What's next

The lab builds TTL presence on a sorted set, proves keyspace notifications are
late and lossy, induces a 2.3-million-message-per-second presence storm and cuts it
by 117×, catches `group_expiry` silently disabling a live socket, writes the token
bucket in Lua, measures the 41% overshoot the non-atomic version allows, and wires
the six limit tiers into the protocol's error frame.

See you in [`lab.md`](./lab.md).
