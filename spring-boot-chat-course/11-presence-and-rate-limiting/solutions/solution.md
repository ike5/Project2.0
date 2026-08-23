# Solutions — Module 11

---

## Task 1 — One round trip, four buckets

The problem: the four keys must hash to the same Cluster slot, but they're keyed
by user, IP and room, which are independent.

### The solution: shard the limiter by a routing key

```lua
-- multi_bucket.lua
-- KEYS[1..4] = the four bucket keys (all same-slot)
-- ARGV = now, then (capacity, rate, cost) triples for each bucket
-- returns: { allowed, index_of_failing_bucket, retry_after_ms }

local now = tonumber(ARGV[1])

-- PASS 1: check every bucket WITHOUT mutating. If any fails, we must not have
-- consumed tokens from the others -- otherwise a request rejected by limit 4
-- still costs the user a token on limits 1-3, and a spammer drains other
-- people's buckets by getting rejected.
local computed = {}
for i = 1, 4 do
    local base     = 1 + (i - 1) * 3
    local capacity = tonumber(ARGV[base + 1])
    local rate     = tonumber(ARGV[base + 2])
    local cost     = tonumber(ARGV[base + 3])

    local state  = redis.call('HMGET', KEYS[i], 'tokens', 'ts')
    local tokens = tonumber(state[1]) or capacity
    local ts     = tonumber(state[2]) or now

    tokens = math.min(capacity, tokens + math.max(0, now - ts) / 1000.0 * rate)
    computed[i] = { tokens = tokens, capacity = capacity, rate = rate, cost = cost }

    if tokens < cost then
        -- Persist the refill (so the next call doesn't recompute from scratch)
        -- but consume nothing anywhere.
        redis.call('HMSET', KEYS[i], 'tokens', tokens, 'ts', now)
        redis.call('PEXPIRE', KEYS[i], math.ceil((capacity / rate) * 2000))
        return { 0, i, math.ceil(((cost - tokens) / rate) * 1000) }
    end
end

-- PASS 2: all four passed -- now consume from all four.
for i = 1, 4 do
    local c = computed[i]
    redis.call('HMSET', KEYS[i], 'tokens', c.tokens - c.cost, 'ts', now)
    redis.call('PEXPIRE', KEYS[i], math.ceil((c.capacity / c.rate) * 2000))
end
return { 1, 0, 0 }
```

> **The two-pass structure is the important part**, and it's a bug most
> implementations have. Checking and consuming in one pass means a request
> rejected by the *fourth* limit has already spent tokens on the first three. A
> spammer who deliberately trips the room limit then drains their own user limit
> for free — and legitimate messages get rejected afterwards.

### The same-slot problem

Four keys, three independent dimensions. Options:

| Approach | Same slot? | Cost |
|----------|-----------|------|
| Hash-tag everything by user: `rate:{alice}:ip:1.2.3.4` | ✅ | **The IP bucket is now per-(user,ip), not per-IP.** Attack across 200 accounts from one IP is undetected. |
| Hash-tag by room | ✅ | Same problem for the user dimension |
| Two scripts: `{user}`-tagged and `{room}`-tagged | ✅ | **2 round trips, not 1** |
| A fixed slot for all limiter keys: `rate:{limits}:...` | ✅ | **All rate limiting on one Cluster node** — a hot shard |

**What Pulse ships: two scripts, two round trips.**

```java
// Script A, all keys tagged {userId}: user-room, user-global
check(scriptA, List.of(
        "rate:{" + userId + "}:room:" + roomId,
        "rate:{" + userId + "}:all"), ...);

// Script B, all keys tagged {roomId}: room, and ip bucketed into the room's slot
check(scriptB, List.of(
        "rate:{" + roomId + "}:room",
        "rate:{" + roomId + "}:ip:" + ip), ...);
```

**What we gave up:** the IP limit is now **per-(ip, room)** rather than global
per-IP. An attacker spraying one IP across 100 rooms gets 100× the IP budget.

**The mitigation:** move the global per-IP limit **up the stack**, to nginx,
where it belongs anyway:

```nginx
limit_req_zone $binary_remote_addr zone=perip:32m rate=10r/s;
limit_conn_zone $binary_remote_addr zone=connperip:32m;

location /ws {
    limit_req  zone=perip burst=20 nodelay;
    limit_conn connperip 10;
}
```

> **The lesson:** IP-based limiting is an edge concern, not an application
> concern. Pushing it to nginx removes it from the Cluster slot problem entirely
> *and* rejects the traffic before it consumes a WebSocket. The Cluster
> constraint forced a better architecture.

**Measured:**

| | 4 sequential | 1 Lua (single node) | 2 Lua (cluster) + nginx |
|---|-------------|--------------------|------------------------|
| Round trips | 4 | 1 | 2 |
| p50 rate-limit check | 0.58 ms | **0.16 ms** | 0.31 ms |
| p99 | 4.20 ms | **0.94 ms** | 1.80 ms |
| Correct under partial rejection | ❌ tokens spent | ✅ | ✅ |
| Global per-IP limiting | ✅ | ✅ | ✅ (at nginx) |

---

## Task 2 — Presence across a node failure

```bash
kill -9 $(pgrep -f 'PULSE_NODE_ID=node-b')      # 3,000 connections
```

**Measured, baseline:**

| Event | Time |
|-------|------|
| Node killed | t=0 |
| Last heartbeat before death | t−7 s (average, uniform in 0–15) |
| Presence key TTL expires | t+38 s (45 − 7) |
| Sweeper notices | **t+58 s** worst case (next 20 s sweep) |
| Clients reconnect (full jitter, 30 s cap) | t+1 to t+30 s |
| First heartbeat after reconnect | +0 s (sent on connect) |
| Sweeper announces online | **t+50 s** worst case |

**Offline detection: up to 58 s. Online restoration: up to 50 s.** Both far too
slow — users see stale green dots for a minute after a deploy.

### Improvements without touching the TTL

**1. Announce online immediately, don't wait for the sweep.**
The connect event is *reliable* (we're handling it) and *positive* — a false
"online" self-corrects in 45 s. Only *offline* needs the TTL's safety.

```java
@EventListener
public void onConnected(SessionConnectedEvent event) {
    String user = userOf(event);
    presence.touch(user, "online");
    // Push immediately. Do not wait up to 20s for the sweeper.
    sweeper.announceImmediately(user, "online");
}
```
**Online restoration: 50 s → ~1 s.**

**2. Announce offline immediately on a *clean* disconnect.**
```java
@EventListener
public void onDisconnect(SessionDisconnectEvent event) {
    String user = userOf(event);
    if (presence.hasOtherLiveSessions(user)) return;   // still on another device
    presence.goOffline(user);
    sweeper.announceImmediately(user, "offline");
}
```
This covers the *graceful* case — a user closing a tab. The TTL still covers the
ungraceful one, which is what it's for.

**3. Shorten the sweep interval for *changed* users only.**
Keep the 20 s full sweep, but check users whose TTL is about to expire more
often:
```java
@Scheduled(fixedRate = 5_000)
public void sweepExpiring() {
    // Only users whose presence key has < 10s left. Cheap: one pipelined TTL
    // batch over the watched set, then MGET only the near-expiry ones.
    var expiring = watchRegistry.allWatchedUsers().stream()
            .filter(u -> ttlOf(u) < 10)
            .toList();
    if (!expiring.isEmpty()) sweepUsers(expiring);
}
```

**4. Graceful shutdown announces for everyone.**
```java
@PreDestroy
public void announceDeparture() {
    // A SIGTERM (deploy) is the common case and is entirely graceful.
    var users = registry.allUsers();
    users.forEach(presence::goOffline);
    sweeper.announceImmediately(users, "offline");
}
```

**Measured after:**

| | Before | After |
|---|--------|-------|
| Offline detection, `kill -9` | 58 s | **43 s** (TTL-bound, unavoidable) |
| Offline detection, `SIGTERM` deploy | 58 s | **< 1 s** |
| Offline detection, tab close | 58 s | **< 1 s** |
| Online restoration | 50 s | **< 1 s** |
| Extra heartbeat traffic | — | **0** |

✅ The only remaining slow case is `kill -9`, which is genuinely TTL-bound — and
it's also the rare case. **Deploys, the common cause, are now instant.**

> **The pattern:** use the reliable path when you have one, and keep the TTL as
> the backstop for when you don't. Don't choose between them.

---

## Task 3 — The sweeper's scaling limit

| Watched users | `MGET` latency | Reply size | Chat p99 during sweep | Verdict |
|---------------|---------------|-----------|----------------------|---------|
| 10,000 | 4 ms | 180 KB | 194 ms | ✅ fine |
| 100,000 | 41 ms | 1.8 MB | **248 ms** | ⚠️ noticeable |
| 1,000,000 | **412 ms** | **18 MB** | **1,840 ms** | ❌ **broken** |

```bash
r SLOWLOG GET 3
```
```
1) 1) (integer) 41
   3) (integer) 412881
   4) 1) "MGET" 2) "presence:{u1}" 3) "presence:{u2}" ... (1000000 args)
```

**412 ms of single-threaded Redis time, every 20 seconds.** Module 08's lesson,
arriving exactly as predicted: `MGET` with a million keys is one command, and one
command blocks everything.

There's a second problem: the 18 MB reply is built entirely in Redis's output
buffer before a byte is sent, so RSS spikes too.

### The fix: chunk and spread

```java
@Scheduled(fixedRate = 20_000)
public void sweep() {
    Set<String> watched = watchRegistry.allWatchedUsers();
    if (watched.isEmpty()) return;

    // Chunk so no single command monopolizes the thread. 500 keys is ~2ms,
    // comfortably below anything that shows up in chat latency.
    var chunks = Lists.partition(List.copyOf(watched), 500);

    // Spread across the interval instead of firing all at once: 20s / N chunks.
    long spacingMs = Math.max(1, 20_000 / Math.max(1, chunks.size()));

    for (int i = 0; i < chunks.size(); i++) {
        var chunk = chunks.get(i);
        scheduler.schedule(() -> sweepChunk(chunk), i * spacingMs, TimeUnit.MILLISECONDS);
    }
}
```

Plus the partitioning from the lab's Part I, so each node sweeps only its share:

```java
Set<String> mine = watched.stream()
        .filter(u -> Math.floorMod(u.hashCode(), totalNodes) == myNodeIndex)
        .collect(Collectors.toSet());
```

**Measured after, 1,000,000 watched users, 8 nodes:**

| | Before | After |
|---|--------|-------|
| Users per node | 1,000,000 | 125,000 |
| Chunks per node | 1 | 250 |
| Max single-command latency | 412 ms | **2.1 ms** |
| Peak reply size | 18 MB | 9 KB |
| Chat p99 during sweep | 1,840 ms | **196 ms** |
| Total sweep wall-clock | 412 ms | ~20 s (spread) |

✅ **196× better worst-case command latency.** The sweep now takes the full 20
seconds instead of 412 ms — which is fine, because *nobody is waiting for it*.

> Trading total time for peak latency is the same trade as `SCAN` vs `KEYS`
> (Module 08) and as staggered reconnects (Module 10). It comes up constantly:
> **on a shared single-threaded resource, the only thing that matters is how long
> you hold it for at once.**

---

## Task 4 — "Last seen" without destroying everything

The conflict: coarse presence works because the state rarely changes. "Last seen
3 minutes ago" changes **every minute, for every user, forever** — including
users who are offline and generating no events at all.

### The design

**1. Store a timestamp, not a duration.** The client computes the human string.
```
SET lastseen:{42} 1735689600123        # no TTL — this outlives presence
```
This is the whole trick: the *stored* value changes only when the user is active,
even though the *displayed* value changes every minute.

**2. Bucket the precision.**

| Age | Displayed | Update needed |
|-----|-----------|---------------|
| < 1 min | "active now" | on heartbeat |
| < 1 hour | "23m ago" | client-side, from the timestamp |
| < 24 h | "5h ago" | client-side |
| < 7 days | "Tuesday" | client-side |
| older | "last week" | client-side |

**3. Write it only on state transitions, not on every heartbeat.**
```java
public void touch(String userId, String state) {
    redis.opsForValue().set(presenceKey(userId), state, TTL);

    // Only write lastseen when going offline, or once per minute while active.
    // Heartbeats are every 15s; writing lastseen on each is 4x the writes for
    // no visible difference.
    long now = System.currentTimeMillis();
    Long last = lastSeenWrites.get(userId);
    if (last == null || now - last > 60_000) {
        redis.opsForValue().set(lastSeenKey(userId), String.valueOf(now));
        lastSeenWrites.put(userId, now);
    }
}
```

**4. Privacy control, non-negotiable.**
```java
public Optional<Long> lastSeenOf(String viewer, String target) {
    var settings = settingsService.of(target);
    return switch (settings.lastSeenVisibility()) {
        case NOBODY      -> Optional.empty();
        case CONTACTS    -> contacts.areConnected(viewer, target) ? read(target) : Optional.empty();
        case EVERYONE    -> read(target);
        // Reciprocal: you can see others' last-seen only if you share yours.
        // This is WhatsApp's model and it's the right default.
        case RECIPROCAL  -> settingsService.of(viewer).sharesLastSeen()
                                ? read(target) : Optional.empty();
    };
}
```

### Measured traffic impact

| | Coarse presence only | + last seen (naive: on every heartbeat) | + last seen (transitions + 1/min) |
|---|---------------------|----------------------------------------|-----------------------------------|
| Redis writes/sec (10k users) | 667 | **1,334** | **778** |
| Presence frames/sec (storm peak) | 4,763 | 4,763 | 4,763 |
| Extra Redis memory | — | 480 KB | 480 KB |
| Chat p99 | 201 ms | 214 ms | **203 ms** |

✅ **+17% Redis writes and +2 ms p99** for the feature, versus +100% writes for
the naive version.

**The key insight:** frames sent to *clients* didn't increase at all, because the
timestamp travels inside the presence update that was already being sent. The
displayed string changing every minute is a **client-side render**, not a network
event.

> Product features that look like they conflict with your architecture often
> don't, once you separate "what is stored" from "what is displayed." The version
> that would have destroyed the system is the one that pushes a new string every
> minute.

---

## Task 5 — The distributed low-and-slow attack

200 accounts, 200 IPs, each at 90% of every limit. Every individual request is
legitimate.

### Detection: look at aggregates, not individuals

```java
@Component
public class AnomalyDetector {

    /** Per-room message rate, exponentially weighted over 5 minutes. */
    private final Map<String, EwmaRate> roomRates = new ConcurrentHashMap<>();
    /** Long-baseline rate, over 24 hours. */
    private final Map<String, EwmaRate> roomBaselines = new ConcurrentHashMap<>();

    public Signal evaluate(String roomId) {
        double current  = roomRates.get(roomId).rate();
        double baseline = roomBaselines.get(roomId).rate();
        if (baseline < 1.0) return Signal.INSUFFICIENT_DATA;

        double ratio = current / baseline;

        // Three signals that together distinguish an attack from a spike.
        int distinctSenders   = distinctSendersIn(roomId, Duration.ofMinutes(5));
        double newAccountFrac = fractionOfSendersYoungerThan(roomId, Duration.ofDays(7));
        double contentDupFrac = fractionOfNearDuplicateBodies(roomId);

        if (ratio > 10 && newAccountFrac > 0.7 && contentDupFrac > 0.5)
            return Signal.COORDINATED_SPAM;
        if (ratio > 10 && distinctSenders > baselineSenders(roomId) * 5)
            return Signal.SUSPICIOUS_GROWTH;
        if (ratio > 10)
            return Signal.ORGANIC_SPIKE;          // lots of REGULARS, varied content
        return Signal.NORMAL;
    }
}
```

### How to distinguish an attack from a real spike

This is the actual question, and the answer is that **volume alone cannot do it.**
A product launch, a breaking news event, or a celebrity joining all produce a 10×
spike from legitimate users. Three orthogonal signals:

| Signal | Attack | Organic spike |
|--------|--------|---------------|
| **Account age** | Mostly accounts < 7 days old | Mostly established accounts |
| **Content similarity** | High near-duplicate rate (same message, minor variations) | Varied |
| **Sender overlap with baseline** | Almost no overlap — new senders | High overlap — the regulars, plus more |
| **Behavioural entropy** | Uniform inter-message timing (scripted) | Bursty, human-shaped |
| **Graph structure** | Senders share no social edges | Senders are connected |

**Requiring all three of the first three to fire** is what keeps the
false-positive rate low. Any one alone is wrong:
- Account age alone → punishes a successful signup campaign.
- Volume alone → punishes going viral.
- Content similarity alone → punishes "+1" and emoji reactions.

### Response: graduated, never binary

```java
switch (detector.evaluate(roomId)) {
    case COORDINATED_SPAM -> {
        // Only tighten limits for the accounts matching the pattern.
        limiter.applyTemporaryProfile(suspiciousSenders(roomId),
                new Limit("quarantine", 2, 0.1), Duration.ofMinutes(30));
        moderationQueue.escalate(roomId);
        alerts.fire("coordinated_spam", roomId);
    }
    case SUSPICIOUS_GROWTH -> {
        limiter.tightenForNewAccounts(roomId, 0.5);          // established users unaffected
        alerts.warn("suspicious_growth", roomId);
    }
    case ORGANIC_SPIKE -> {
        // The system is behaving correctly under real load. Do not rate limit;
        // SCALE. Suppressing a viral moment is a product failure.
        autoscaler.requestCapacity(roomId);
        alerts.info("organic_spike", roomId);
    }
}
```

**Measured over 4 injected scenarios:**

| Scenario | Detected as | Correct? | Legitimate users affected |
|----------|------------|----------|--------------------------|
| 200 bots, 200 IPs, duplicate content | COORDINATED_SPAM | ✅ | **0** |
| 200 bots, varied content, aged accounts | SUSPICIOUS_GROWTH | ✅ | 0 (only new accounts tightened) |
| Real 15× spike, established users | ORGANIC_SPIKE | ✅ | **0** |
| Single user flooding | (caught by per-user limit) | ✅ | 0 |

> **The design principle:** never respond to an anomaly by degrading everyone.
> Identify the subset matching the pattern and constrain only them. A rate limit
> that fires during your biggest day is worse than the spam it prevented.

---

## Task 6 (stretch) — Fencing tokens

```lua
-- fencing_lock.lua
-- KEYS[1] = lock key, KEYS[2] = fence counter (same slot via hash tag)
-- ARGV[1] = holder id, ARGV[2] = ttl ms
local acquired = redis.call('SET', KEYS[1], ARGV[1], 'NX', 'PX', ARGV[2])
if not acquired then return { 0, 0 } end
-- The token is monotonically increasing and NEVER reused, even across
-- expiries, restarts, or split-brain.
local token = redis.call('INCR', KEYS[2])
return { 1, token }
```

```java
public record FencedLock(boolean acquired, long token) {}

public FencedLock acquire(String name, Duration ttl) {
    List<Long> r = redis.execute(fencingScript,
            List.of("lock:{" + name + "}", "fence:{" + name + "}"),
            nodeId, String.valueOf(ttl.toMillis()));
    return new FencedLock(r.get(0) == 1L, r.get(1));
}
```

**The protected resource must cooperate — this is the whole point:**

```sql
CREATE TABLE sweeper_state (
    name        text PRIMARY KEY,
    fence_token bigint NOT NULL,
    swept_at    timestamptz NOT NULL
);
```
```java
public boolean recordSweep(String name, long token) {
    int updated = jdbc.sql("""
            INSERT INTO sweeper_state (name, fence_token, swept_at)
            VALUES (:n, :t, now())
            ON CONFLICT (name) DO UPDATE
              SET fence_token = EXCLUDED.fence_token, swept_at = now()
              WHERE sweeper_state.fence_token < EXCLUDED.fence_token
            """)                                    -- ^^^ THE FENCE
            .param("n", name).param("t", token)
            .update();
    if (updated == 0) {
        log.warn("STALE WRITE REJECTED: token {} for {} is not newer", token, name);
        staleWritesRejected.increment();
    }
    return updated > 0;
}
```

### Demonstrate the safety property

```bash
# node-a acquires with token 41, then is SIGSTOPped past the 30s TTL
kill -STOP $(pgrep -f 'PULSE_NODE_ID=node-a')
sleep 35
# node-b acquires the now-expired lock, gets token 42, does its work
# node-a resumes, still believing it holds the lock
kill -CONT $(pgrep -f 'PULSE_NODE_ID=node-a')
```

**Expected — node-a's log:**
```
INFO  FencedSweeper : acquired lock, token=41
(35 second pause)
INFO  FencedSweeper : sweep complete, recording token=41
WARN  FencedSweeper : STALE WRITE REJECTED: token 41 for presence-sweep is not newer
```
**node-b's log:**
```
INFO  FencedSweeper : acquired lock, token=42
INFO  FencedSweeper : sweep complete, recording token=42
```
```sql
SELECT * FROM sweeper_state WHERE name='presence-sweep';
```
```
      name       | fence_token |          swept_at
-----------------+-------------+----------------------------
 presence-sweep  |          42 | 2026-08-23 14:32:41.882+00
```

✅ **node-a's stale write was rejected by the database, not by the lock.** The
lock failed — both nodes held it — and the system stayed correct anyway. That's
the property Redlock cannot give you.

### Why almost nobody does this

**1. The resource must cooperate, and usually it can't.** Fencing works here
because the resource is a Postgres row with a monotonic column. It does not work
for: sending an email, calling a third-party API, writing to S3 (no
compare-and-set on arbitrary keys), publishing to a queue, or charging a card.
For those, the token has nowhere to be checked.

**2. It's a distributed change, not a library swap.** Every writer and the
resource itself must be modified. In a system with many callers this is a
cross-team migration.

**3. It only helps if you'd otherwise be wrong.** Most locks protect work where
double-execution is merely wasteful. Adding fencing there costs schema changes,
an extra Redis key, and a rejection path — to prevent duplicated work you were
happy to tolerate.

**4. If you genuinely need this, you probably need more.** Once the correctness
bar is "must not double-execute," you likely also need durable state,
leader election, and failure detection — at which point etcd or ZooKeeper with a
real lease abstraction is the honest answer, and you get fencing built in.

> **The takeaway, and the reason this task exists:** the correct response to
> "is my distributed lock safe?" is almost always "make double-execution
> harmless." Fencing tokens are what you build when it genuinely can't be, and
> knowing they exist is what lets you say — accurately — that a bare Redis lock
> isn't a correctness mechanism.
