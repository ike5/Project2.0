# Module 11 — Presence, Typing & Rate Limiting

**Goal:** Build the state that isn't messages — who's online, who's typing, who's
sending too much — and understand why presence is often the *most expensive*
subsystem in a chat product despite carrying the least valuable data.

⏱️ ~5 hours · **Prerequisites:** Modules 00–10.

---

## Presence is a fan-out problem wearing a different hat

A green dot next to a name looks trivial. Here's the arithmetic:

```
10,000 users, each in 20 rooms, each room averaging 50 members

One user comes online:
  → notify everyone who shares a room with them
  → 20 rooms × 49 others = 980 notifications

All 10,000 come online after a deploy:
  → 10,000 × 980 = 9,800,000 notifications
  → in the ~30 seconds it takes everyone to reconnect
  → 326,000 messages/second
```

**That is more traffic than your actual chat**, for data whose value is a
coloured circle. And it arrives in a burst, at exactly the moment your system is
most fragile — just after a deploy or a failover.

This is the **presence storm**, and it's why large products quietly weaken
presence: coarse buckets (online/away/offline, not last-seen-at), aggressive
debouncing, subscription only to *visible* users, or dropping presence in large
rooms entirely.

---

## Presence state: TTL, not events

The naive design stores presence and updates it on connect/disconnect:

```
SET presence:42 online          # on connect
DEL presence:42                 # on disconnect
```

This is wrong, and the reason is Module 09's lesson in a new costume: **the
disconnect event is not guaranteed to happen.** A killed node, a NAT eviction, an
OOM — and that key says `online` forever.

The correct design makes presence **self-expiring**:

```
SET presence:42 online EX 45           # client heartbeats every 15s
```

- Heartbeat refreshes the TTL. Three missed heartbeats and it expires.
- A crashed node's users go offline automatically, with no cleanup code.
- The state is **derived from liveness**, not from an event you hope arrives.

> **The general principle, third appearance in this course:** any cleanup that
> depends on a graceful event is a leak. TTLs are cleanup that can't be skipped.

### Detecting the transition

TTL expiry gives you the *state* but not the *event*. You need the transition to
notify others.

**Tempting and wrong: keyspace notifications.**
```bash
CONFIG SET notify-keyspace-events Ex
SUBSCRIBE __keyevent@0__:expired
```
This works in a demo and fails in production, for three reasons:

1. It's delivered over **Pub/Sub** — at-most-once. A node that's reconnecting
   misses the expiry and that user stays green forever.
2. Expiry events fire when Redis actually *deletes* the key, which for the lazy
   expiration path can be **long** after the TTL elapsed — up to minutes for a
   key nobody touches.
3. In Redis Cluster, the event fires on the node owning the key, so only
   subscribers of that node hear it.

**What Pulse does instead: poll on read, plus a coarse sweeper.**

```java
// Presence is computed, not pushed. A missing key IS "offline".
public boolean isOnline(String userId) {
    return redis.hasKey("presence:{" + userId + "}");
}
```

Checking N users is one `MGET`, not N round trips. The transition notification
comes from a sweeper that runs every ~20 seconds and diffs against what it
announced last — coarse, cheap, and it cannot get permanently stuck.

---

## Bounding the storm

Four techniques, all of which real products use:

**1. Subscribe to presence, don't broadcast it.**
A client watching a 500-member room doesn't need presence for all 500 — it needs
it for the ~20 currently rendered. Have the client tell you which:

```
presence.watch { users: ["u1","u2",...,"u20"] }
```
This turns O(room size) into O(viewport), which is a constant.

**2. Aggregate and debounce.**
One presence update per room per second, listing changes — not one frame per
user per change. Module 05's typing aggregation, applied to presence.

**3. Coarse states.**
`online | away | offline`, not `last seen 3 seconds ago`. A precise last-seen
timestamp changes constantly and forces an update every time.

**4. Suppress in large rooms.**
Above a threshold, don't send presence at all. Nobody meaningfully consumes the
online status of 5,000 people.

```
presence traffic = min(room_size, viewport) × changes/sec × rooms
```
Only one of those factors is under your control, and it's the first one.

---

## Typing indicators: the highest-volume, lowest-value traffic

Module 05 designed the protocol; the numbers justify it:

| Design | Frames for 20 typers in a 200-member room over 60 s |
|--------|---------------------------------------------------|
| Every keystroke, broadcast each | 1,200,000 |
| Debounced 3 s, broadcast each | 80,000 |
| **Debounced + aggregated 1 Hz** | **12,340** |

The aggregation win is the structural one: it makes outbound traffic depend on
**time**, not on the number of typers. Twenty typers or two thousand, it's one
frame per room per second. That's a **hard bound on the worst case**, which is
worth more than the average-case saving.

Typing rides Pub/Sub (Module 09's routing rule): at-most-once, superseded within
seconds, zero storage.

---

## Rate limiting: the token bucket

Fixed windows are simple and wrong at the boundary:

```
limit: 10 per minute
12:00:59 → 10 messages   ✓ allowed
12:01:00 → 10 messages   ✓ allowed (new window)
         = 20 messages in one second
```

**Token bucket** fixes it: tokens refill continuously at a fixed rate, up to a
cap. Each action costs one.

```
capacity 20, refill 5/sec

  tokens
    20 │████████████████████
       │        ╲
    10 │          ╲___      ← burst of 10 spends half
       │              ╲___
     0 │                   ╲___   ← sustained sending drains it
       └──────────────────────────── time
                                     refills at 5/sec regardless
```

Allows a **burst** (paste three messages at once — legitimate) while bounding the
**sustained rate**. That's exactly the behaviour chat wants.

It must be atomic — read tokens, compute refill, check, decrement — which is
Module 08's Lua lesson: a check-then-act across a network is a race; the same
logic in Lua is not.

### Where to limit

| Layer | Limits | Why |
|-------|--------|-----|
| Connection handshake | Connections per IP per minute | Stops reconnect storms and socket exhaustion |
| Per user, per room | Messages/sec | The obvious one |
| Per user, global | Messages/sec across all rooms | Stops spraying one message across 100 rooms |
| Per IP | Messages/sec | Stops one host running 500 accounts |
| Per room | Total messages/sec | Protects everyone in a room from one flood |
| **Resume requests** | Per user per minute | The most expensive operation a client can request (Module 10) |

You need most of these. A single per-user limit is trivially bypassed by
attacking a different dimension.

---

## Distributed locks, and why Redlock is contested

At some point you'll want "only one node should do X." The Redis answer:

```
SET lock:job:cleanup <random-token> NX PX 30000
```

Single-instance, this is correct: `NX` is atomic, `PX` bounds the damage if the
holder dies, and the random token lets you release safely:

```lua
if redis.call('GET', KEYS[1]) == ARGV[1] then
    return redis.call('DEL', KEYS[1])
end
return 0
```

> ⚠️ **Never `DEL` a lock without checking the token.** If your work overran the
> TTL, the lock is someone else's now and you'd be releasing theirs.

**Redlock** extends this to N independent Redis instances, requiring a majority.
Martin Kleppmann's critique and Salvatore Sanfilippo's reply are both worth
reading in full; the short version:

> Redlock's safety depends on bounded clock drift and bounded process pauses.
> Neither is guaranteed. A GC pause longer than the lock TTL means you believe
> you hold a lock that has expired and been granted to someone else — and no
> amount of Redis quorum detects that, because the failure is in *your* process.

The practical resolutions:

1. **Use fencing tokens.** The lock returns a monotonically increasing number;
   the protected resource rejects writes with a stale token. This makes the lock
   safe *even if* it's held twice. It requires the resource to cooperate, which
   is why it's rare — and it's the only actually-correct answer.
2. **Use a real consensus system** (etcd, ZooKeeper) when correctness matters.
   Module 18 uses etcd for Patroni for exactly this reason.
3. **Don't need the lock.** Usually the best option. Make the operation
   idempotent, or partition the work so each node owns a disjoint slice by
   consistent hash. Pulse does this for its background jobs.

> **The honest position:** a Redis lock is a *performance optimization* that
> usually prevents duplicate work. It is not a correctness mechanism. Design so
> that a double-execution is harmless, and then the lock's failure modes stop
> mattering.

---

## What's next

The lab builds TTL presence with viewport subscriptions, aggregated typing, a Lua
token bucket, and multi-dimensional limits — then induces a presence storm and
measures the difference the mitigations make.

See you in [`lab.md`](./lab.md).
