# Lab 11 — Presence Without the Storm

**You'll:** build TTL presence with viewport subscriptions, aggregated typing, a
Lua token bucket and multi-dimensional limits — then induce a 10,000-user
presence storm and measure what each mitigation is worth.

⏱️ ~100 min. Work in `spring-boot-chat-course/apps/pulse`.

```bash
alias r='docker exec -i pulse-redis redis-cli'
```

---

## Part A — TTL presence

`src/main/java/com/pulse/presence/PresenceService.java`:

```java
package com.pulse.presence;

import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Service;

import java.time.Duration;
import java.util.*;
import java.util.stream.Collectors;

@Service
public class PresenceService {

    /** 3 missed heartbeats before we call someone offline. */
    private static final Duration TTL = Duration.ofSeconds(45);
    private static final Duration HEARTBEAT = Duration.ofSeconds(15);

    private final StringRedisTemplate redis;

    private static String key(String userId) { return "presence:{" + userId + "}"; }

    /** Called on connect and on every client heartbeat. */
    public void touch(String userId, String state) {
        redis.opsForValue().set(key(userId), state, TTL);
    }

    /**
     * Presence is COMPUTED from key existence, never from a stored
     * connect/disconnect event. A killed node's users expire on their own.
     */
    public boolean isOnline(String userId) {
        return Boolean.TRUE.equals(redis.hasKey(key(userId)));
    }

    /** One round trip for N users, not N. This is the whole game (Module 08). */
    public Map<String, String> statusOf(Collection<String> userIds) {
        if (userIds.isEmpty()) return Map.of();

        List<String> ids = List.copyOf(userIds);
        List<String> keys = ids.stream().map(PresenceService::key).toList();
        List<String> values = redis.opsForValue().multiGet(keys);

        var result = new HashMap<String, String>(ids.size());
        for (int i = 0; i < ids.size(); i++) {
            String v = values == null ? null : values.get(i);
            result.put(ids.get(i), v == null ? "offline" : v);
        }
        return result;
    }

    /** Explicit sign-out. Note we do NOT rely on this for correctness. */
    public void goOffline(String userId) {
        redis.delete(key(userId));
    }
}
```

Prove the TTL does the work:

```bash
r SET 'presence:{42}' online EX 45
r TTL 'presence:{42}'
r EXISTS 'presence:{42}'
sleep 46
r EXISTS 'presence:{42}'
```
**Expected:**
```
OK
(integer) 45
(integer) 1
(integer) 0
```

✅ No cleanup code ran. Now prove the naive design fails — set presence without a
TTL and `kill -9` the node:

```bash
r SET 'presence:{99}' online          # no EX
kill -9 $(pgrep -f 'PULSE_NODE_ID=node-b')
sleep 60
r GET 'presence:{99}'
```
**Expected:**
```
"online"
```
✅ **Still online, an hour from now, forever.** That's the leak TTLs prevent.

---

## Part B — The heartbeat

STOMP heartbeats keep the *socket* alive (Module 03); this keeps the *presence
key* alive. They're different things and you need both.

```java
@MessageMapping("/presence/heartbeat")
public void heartbeat(@Payload HeartbeatRequest request, Principal principal) {
    presence.touch(principal.getName(), request.state());     // online | away
}
```

```js
setInterval(() => {
  if (!client.connected) return;
  client.publish({
    destination: '/app/presence/heartbeat',
    body: JSON.stringify({ state: document.hidden ? 'away' : 'online' }),
  });
}, 15000);
```

> `document.hidden` gives you `away` for free — a backgrounded tab. That single
> line removes most of the "why is my colleague green at 3am" complaints.

Watch it work:
```bash
watch -n1 "docker exec pulse-redis redis-cli TTL 'presence:{alice}'"
```
**Expected — sawtooth between 30 and 45:**
```
(integer) 44
(integer) 43
...
(integer) 31
(integer) 45      <-- heartbeat landed
```

---

## Part C — Viewport subscriptions

The most important optimization: a client watches ~20 users, not 500.

```java
@MessageMapping("/presence/watch")
public void watch(@Payload WatchRequest request, Principal principal,
                  SimpMessageHeaderAccessor headers) {

    // A client can only ask about people it shares a room with, and no more
    // than MAX_WATCH of them. Both bounds matter: the first is privacy, the
    // second stops one client asking about 100,000 users.
    var allowed = membership.visibleTo(principal.getName(), request.users(), MAX_WATCH);
    watchRegistry.set(headers.getSessionId(), allowed);

    // Immediate snapshot so the UI isn't blank while waiting for a diff.
    template.convertAndSendToUser(principal.getName(), "/queue/presence",
            Envelope.of("presence.snapshot", null,
                    json.valueToTree(presence.statusOf(allowed))));
}
```

```js
// Client: recompute the watch set when the visible list changes,
// debounced so scrolling doesn't spam it.
const updateWatch = debounce(() => {
  const visible = [...document.querySelectorAll('[data-user][data-visible=true]')]
                    .map(el => el.dataset.user);
  client.publish({ destination: '/app/presence/watch',
                   body: JSON.stringify({ users: visible }) });
}, 300);

new IntersectionObserver(entries => {
  entries.forEach(e => e.target.dataset.visible = String(e.isIntersecting));
  updateWatch();
}).observe(memberList);
```

---

## Part D — The sweeper

Transitions come from a periodic diff, not from keyspace notifications.

```java
@Component
public class PresenceSweeper {

    /** What we last told clients, so we only send changes. */
    private final Map<String, String> lastAnnounced = new ConcurrentHashMap<>();

    @Scheduled(fixedRate = 20_000)
    public void sweep() {
        // Only users somebody is actually watching. This is what makes the
        // sweep cost O(watched) instead of O(all users).
        Set<String> watched = watchRegistry.allWatchedUsers();
        if (watched.isEmpty()) return;

        Map<String, String> current = presence.statusOf(watched);   // ONE MGET

        var changes = new HashMap<String, String>();
        current.forEach((userId, state) -> {
            String previous = lastAnnounced.get(userId);
            if (!state.equals(previous)) {
                changes.put(userId, state);
                lastAnnounced.put(userId, state);
            }
        });

        // Forget users nobody watches, so the map doesn't grow forever.
        lastAnnounced.keySet().retainAll(watched);

        if (changes.isEmpty()) return;

        // Send each session only the subset it watches.
        watchRegistry.forEachSession((sessionId, watchedByThisSession) -> {
            var relevant = changes.entrySet().stream()
                    .filter(e -> watchedByThisSession.contains(e.getKey()))
                    .collect(Collectors.toMap(Map.Entry::getKey, Map.Entry::getValue));
            if (relevant.isEmpty()) return;
            sendToSession(sessionId, Envelope.of("presence.update", null,
                    json.valueToTree(relevant)));
        });

        presenceChanges.increment(changes.size());
    }
}
```

Two properties worth noting:

- **It cannot get permanently stuck.** Unlike an event stream, a missed sweep is
  repaired by the next one 20 seconds later. Worst-case staleness is bounded by
  the sweep interval, not by whether a notification was delivered.
- **`retainAll` is the leak fix.** Without it, `lastAnnounced` accumulates an
  entry per user ever watched.

Watch it:
```bash
curl -s localhost:8080/actuator/metrics/presence.changes | jq '.measurements[0].value'
```

---

## Part E — Aggregated typing

```java
@Service
public class TypingService {

    private static final long TTL_MS = 5_000;

    private final Map<String, Map<String, Long>> typers = new ConcurrentHashMap<>();
    private final Set<String> dirty = ConcurrentHashMap.newKeySet();

    public void startTyping(String roomId, String user) {
        typers.computeIfAbsent(roomId, k -> new ConcurrentHashMap<>())
              .put(user, System.currentTimeMillis() + TTL_MS);
        dirty.add(roomId);                       // MARK, do not broadcast
    }

    public void stopTyping(String roomId, String user) {
        var room = typers.get(roomId);
        if (room != null && room.remove(user) != null) dirty.add(roomId);
    }

    /** ONE frame per room per second, and only for rooms that changed. */
    @Scheduled(fixedRate = 1000)
    public void flush() {
        long now = System.currentTimeMillis();

        typers.forEach((roomId, room) -> {
            if (room.entrySet().removeIf(e -> e.getValue() < now)) dirty.add(roomId);
            if (room.isEmpty()) typers.remove(roomId, room);
        });

        var toFlush = Set.copyOf(dirty);
        dirty.removeAll(toFlush);

        for (String roomId : toFlush) {
            var users = List.copyOf(typers.getOrDefault(roomId, Map.of()).keySet());
            // Ephemeral: Pub/Sub, not Streams (Module 09's routing rule).
            fanout.publishEphemeral(roomId, Envelope.of("typing.update", roomId,
                    json.valueToTree(Map.of("users", users))));
        }
    }
}
```

Client debounce:
```js
let lastTypingSent = 0;
input.addEventListener('input', () => {
  const now = Date.now();
  if (now - lastTypingSent < 3000) return;
  lastTypingSent = now;
  client.publish({ destination: `/app/${room}/typing`, body: '{}' });
});
```

Measure it:
```bash
k6 run -e TYPERS=20 -e ROOM_SIZE=200 --duration 60s code/typing-load.js
```

**Expected:**

| Design | Client→server | Server→client | Total |
|--------|--------------|---------------|-------|
| Every keystroke, broadcast each | 6,000 | 1,194,000 | 1,200,000 |
| Debounced 3 s only | 400 | 79,600 | 80,000 |
| **Debounced + aggregated** | **400** | **11,940** | **12,340** |

✅ **97× vs naive.** And the aggregated number is bounded by *time*, so it does
not grow with the number of typers.

---

## Part F — The Lua token bucket

`src/main/resources/scripts/token_bucket.lua`:

```lua
-- KEYS[1] = bucket key (must include a hash tag for Cluster)
-- ARGV[1] = capacity
-- ARGV[2] = refill tokens per second
-- ARGV[3] = now (epoch millis, passed IN — never call TIME in a script that
--           might run on a replica; it breaks determinism)
-- ARGV[4] = cost
-- returns: { allowed(1|0), tokens_remaining, retry_after_ms }

local state    = redis.call('HMGET', KEYS[1], 'tokens', 'ts')
local capacity = tonumber(ARGV[1])
local rate     = tonumber(ARGV[2])
local now      = tonumber(ARGV[3])
local cost     = tonumber(ARGV[4])

local tokens = tonumber(state[1])
local ts     = tonumber(state[2])
if tokens == nil then tokens = capacity end
if ts == nil then ts = now end

-- Continuous refill: elapsed time since we last looked, times the rate.
local elapsed = math.max(0, now - ts) / 1000.0
tokens = math.min(capacity, tokens + elapsed * rate)

-- Idle buckets expire on their own, so we never accumulate dead keys.
local ttl = math.ceil((capacity / rate) * 2000)

if tokens < cost then
    redis.call('HMSET', KEYS[1], 'tokens', tokens, 'ts', now)
    redis.call('PEXPIRE', KEYS[1], ttl)
    local retry = math.ceil(((cost - tokens) / rate) * 1000)
    return { 0, math.floor(tokens), retry }
end

tokens = tokens - cost
redis.call('HMSET', KEYS[1], 'tokens', tokens, 'ts', now)
redis.call('PEXPIRE', KEYS[1], ttl)
return { 1, math.floor(tokens), 0 }
```

> ⚠️ **`now` is passed in, not read from `TIME` inside the script.** Redis
> requires scripts to be deterministic (historically for replication, still good
> practice), and `TIME` is not. Passing the timestamp also lets you test the
> refill logic without sleeping.

```java
@Component
public class RateLimiter {

    private final DefaultRedisScript<List> script;

    public RateLimiter(StringRedisTemplate redis) {
        this.script = new DefaultRedisScript<>();
        this.script.setScriptSource(new ResourceScriptSource(
                new ClassPathResource("scripts/token_bucket.lua")));
        this.script.setResultType(List.class);
    }

    public Decision tryAcquire(String bucket, int capacity, double refillPerSec, int cost) {
        @SuppressWarnings("unchecked")
        List<Long> result = redis.execute(script, List.of(bucket),
                String.valueOf(capacity),
                String.valueOf(refillPerSec),
                String.valueOf(System.currentTimeMillis()),
                String.valueOf(cost));

        return new Decision(result.get(0) == 1L, result.get(1), result.get(2));
    }

    public record Decision(boolean allowed, long remaining, long retryAfterMs) {}
}
```

Test the burst-then-sustain behaviour by hand:

```bash
SHA=$(r SCRIPT LOAD "$(cat src/main/resources/scripts/token_bucket.lua)")
NOW=$(date +%s%3N)
r DEL 'rate:{alice}'

# capacity 10, refill 2/sec — spend the whole bucket
for i in $(seq 1 12); do
  r EVALSHA "$SHA" 1 'rate:{alice}' 10 2 "$NOW" 1
done
```
**Expected — 10 allowed, then denied with a retry hint:**
```
1) (integer) 1   2) (integer) 9   3) (integer) 0
...
1) (integer) 1   2) (integer) 0   3) (integer) 0
1) (integer) 0   2) (integer) 0   3) (integer) 500     <-- denied, retry in 500ms
1) (integer) 0   2) (integer) 0   3) (integer) 500
```

Now advance the clock 3 seconds (no sleep needed — that's why `now` is a
parameter):
```bash
r EVALSHA "$SHA" 1 'rate:{alice}' 10 2 "$((NOW + 3000))" 1
```
**Expected — 3 s × 2/sec = 6 tokens refilled, one spent:**
```
1) (integer) 1   2) (integer) 5   3) (integer) 0
```

✅ Continuous refill, burst tolerance, exact retry hint. **Compare a fixed
window** — implement `INCR` + `EXPIRE` and show the boundary double-spend:

```bash
r SET 'fixed:{alice}' 0 EX 60
for i in $(seq 1 10); do r INCR 'fixed:{alice}'; done    # 10 at 12:00:59
r DEL 'fixed:{alice}'                                     # window rolls
for i in $(seq 1 10); do r INCR 'fixed:{alice}'; done    # 10 more at 12:01:00
```
**20 messages in ~1 second under a "10 per minute" limit.** The token bucket
cannot do this.

---

## Part G — Multi-dimensional limits

One dimension is trivially bypassed.

```java
@Component
public class ChatRateLimiter {

    private record Limit(String name, int capacity, double refillPerSec) {}

    private static final Limit PER_USER_ROOM = new Limit("user-room",  10, 1.0);
    private static final Limit PER_USER      = new Limit("user",       30, 5.0);
    private static final Limit PER_IP        = new Limit("ip",         60, 10.0);
    private static final Limit PER_ROOM      = new Limit("room",      200, 50.0);

    public void checkOrThrow(String userId, String roomId, String ip) {
        // Check the CHEAPEST/most-specific first so a spammer is rejected before
        // we spend round trips on the broader checks.
        check(PER_USER_ROOM, "rate:{" + userId + "}:room:" + roomId, userId);
        check(PER_USER,      "rate:{" + userId + "}:all",            userId);
        check(PER_IP,        "rate:{ip:" + ip + "}",                 userId);
        check(PER_ROOM,      "rate:{room:" + roomId + "}",           userId);
    }

    private void check(Limit limit, String key, String userId) {
        var decision = limiter.tryAcquire(key, limit.capacity(), limit.refillPerSec(), 1);
        if (!decision.allowed()) {
            rejections.increment(Tags.of("limit", limit.name()));
            throw new RateLimitedException(limit.name(), decision.retryAfterMs());
        }
    }
}
```

> **Four sequential Redis round trips per message.** Module 08's budget said five
> maximum — this uses four of them. The challenge asks you to fix it; the answer
> is one Lua script checking all four buckets, which requires them to share a hash
> slot, which is why the key naming above is deliberate.

Surface the rejection as a `control` frame, not a disconnect:

```java
@MessageExceptionHandler(RateLimitedException.class)
@SendToUser("/queue/errors")
public Envelope onRateLimited(RateLimitedException e) {
    return Envelope.of("error", null, json.valueToTree(
            new Payloads.Error("rate_limited",
                    "slow down: " + e.getLimitName(), null, e.getRetryAfterMs())));
}
```

```js
client.subscribe('/user/queue/errors', f => {
  const err = JSON.parse(f.body).data;
  if (err.code === 'rate_limited') {
    showToast(`Sending too fast, retry in ${Math.ceil(err.retryAfterMs / 1000)}s`);
    disableInput(err.retryAfterMs);        // stop the user generating more rejections
  }
});
```

Test each dimension is independently effective:

```bash
./code/flood.sh --user alice --room room.1 --rate 50    # trips user-room
./code/flood.sh --user alice --rooms 100 --rate 5       # trips user (global)
./code/flood.sh --users 200 --ip 10.0.0.5 --rate 2      # trips ip
./code/flood.sh --users 500 --room room.1 --rate 1      # trips room
```
**Expected:**
```
rejected by: user-room after 10 messages
rejected by: user      after 30 messages
rejected by: ip        after 60 messages
rejected by: room      after 200 messages
```

✅ Each attack shape is caught by the dimension designed for it. Remove any one
limit and re-run to see which attack gets through.

---

## Part H — Induce the presence storm

**The measurement that justifies the whole module.**

```bash
k6 run -e USERS=10000 -e ROOMS_PER_USER=20 -e ROOM_SIZE=50 \
       code/presence-storm.js
```

The script connects 10,000 users within 30 seconds — simulating everyone
reconnecting after a deploy.

**Expected — naive (broadcast every change to every room member):**
```
presence frames sent:      9,802,441
peak frames/sec:             326,748
Redis ops/sec peak:          412,000
clientOutboundChannel queue:  84,000 (climbing)
chat message p99:             8,940 ms      <-- CHAT IS BROKEN
Redis CPU:                       100%
```

✅ **Chat p99 went from 192 ms to 8.9 seconds because of green dots.**

Now enable each mitigation in turn:

| Mitigation | Frames sent | Peak/sec | Chat p99 |
|-----------|-------------|----------|----------|
| None (broadcast all) | 9,802,441 | 326,748 | **8,940 ms** |
| + coarse states (online/away/offline) | 6,140,882 | 204,696 | 5,210 ms |
| + 20 s sweep aggregation | 891,204 | 29,706 | 940 ms |
| **+ viewport watch (20 users)** | **142,918** | **4,763** | **214 ms** |
| + suppress above 500-member rooms | 138,402 | 4,613 | **201 ms** |

```
frames/sec
  326k │●
       │ ╲
  205k │  ●
       │   ╲
   30k │     ●
       │      ╲
    5k │        ●───●
       └────────────────────
        none  coarse sweep viewport suppress
```

✅ **69× reduction, and chat p99 back to 201 ms** — essentially the Module 09
baseline of 192 ms.

**The viewport optimization is worth more than the other three combined.** That's
the structural point: aggregation and debouncing reduce a constant factor;
watching only what's visible changes the *complexity* from O(room size) to
O(viewport).

Record it:
```markdown
## Module 11 — Presence

- Presence storm, 10,000 users reconnecting in 30s:
    naive:            9,802,441 frames, 326k/s peak, chat p99 8,940ms
    + coarse states:  6,140,882 frames, chat p99 5,210ms
    + 20s sweep:        891,204 frames, chat p99 940ms
    + viewport(20):     142,918 frames,   4.7k/s peak, chat p99 214ms
    + room suppress:    138,402 frames, chat p99 201ms   (baseline was 192ms)
  => 69x reduction; viewport alone is worth more than the other three
- Typing aggregation: 1,200,000 -> 12,340 frames (97x), bounded by TIME not typers
- Token bucket: burst 10, sustain 2/s; fixed window allowed 20-in-1s at the boundary
- Rate limit dimensions: user-room, user, ip, room — each catches a distinct attack
- Rate limiting costs 4 sequential Redis round trips (see the challenge)
```

---

## Part I — The lock you probably don't need

The sweeper runs on every node. Three nodes means three sweeps and three sets of
duplicate notifications.

**The tempting fix:**
```java
if (redis.opsForValue().setIfAbsent("lock:sweeper", nodeId, Duration.ofSeconds(30))) {
    sweep();
}
```

**The better fix — partition instead of lock:**
```java
@Scheduled(fixedRate = 20_000)
public void sweep() {
    // Each node sweeps only the users it hashes to. No coordination, no lock,
    // no single point of failure, and the work is actually divided.
    Set<String> mine = watchRegistry.allWatchedUsers().stream()
            .filter(u -> Math.floorMod(u.hashCode(), totalNodes) == myNodeIndex)
            .collect(Collectors.toSet());
    sweepUsers(mine);
}
```

| | Lock | Partition |
|---|------|-----------|
| Duplicate work | Prevented (mostly) | Prevented (fully) |
| Work divided | ❌ one node does everything | ✅ each does 1/n |
| Failure mode | Lock holder dies → 30 s of no sweeps | Its share is missed until rebalance |
| Correctness depends on | Bounded clock drift and GC pauses | Nothing |
| Extra Redis ops | 1 per sweep per node | 0 |

Prove the lock's failure mode:
```bash
# node-a holds the lock, then GC-pauses for 40 seconds
jcmd $(pgrep -f node-a) GC.run_finalization
kill -STOP $(pgrep -f 'PULSE_NODE_ID=node-a'); sleep 40; kill -CONT $(pgrep -f 'PULSE_NODE_ID=node-a')
```
**Expected in node-a's log:**
```
INFO  PresenceSweeper : acquired lock, sweeping
(40 second pause)
INFO  PresenceSweeper : sweep complete, releasing lock
```
Meanwhile node-b acquired the expired lock at t=30 and also swept. **Both
believed they held it.** For a presence sweep that's harmless duplicate work —
which is exactly why the lock wasn't needed.

Now imagine the same pause around a `DEL` of someone else's lock. That's the
Redlock critique, made concrete.

> **The rule:** if double-execution is harmless, you don't need a lock. If it
> isn't harmless, a Redis lock is not sufficient — you need fencing tokens or a
> consensus system. There is no middle case where a bare Redis lock is the right
> answer.

---

## What you built

- TTL-based presence that self-heals when a node is killed, with a demonstration
  of the leak the naive design produces.
- Viewport subscriptions — O(visible) instead of O(room size).
- A sweeper that diffs rather than relying on keyspace notifications, with
  bounded staleness and no permanent-stuck state.
- Aggregated typing bounded by time, not by typer count.
- An atomic Lua token bucket with burst tolerance and exact retry hints, plus the
  fixed-window failure it prevents.
- Four rate-limit dimensions, each proven to catch a distinct attack shape.
- **A measured presence storm: 69× reduction, chat p99 from 8.9 s back to 201 ms.**
- Partitioned background work instead of a distributed lock, with the lock's
  failure mode demonstrated.

Now do [`challenge.md`](./challenge.md).

Then: [Module 12 — The Message Store](../12-postgres-message-store/).
