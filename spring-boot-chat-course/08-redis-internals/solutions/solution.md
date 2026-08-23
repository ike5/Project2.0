# Solutions — Module 08

---

## Task 1 — The latency budget

```bash
docker exec pulse-redis redis-cli --intrinsic-latency 60
```
**Expected:**
```
Max latency so far: 1 microseconds.
Max latency so far: 41 microseconds.
Max latency so far: 189 microseconds.
Max latency so far: 412 microseconds.

1948372910 total runs
Worst run took 412x longer than the average latency.
```

**Intrinsic floor: ~41 µs typical, 412 µs worst case.** That's the *kernel*
failing to reschedule a busy loop — no Redis involved. Redis can never beat it.

> On a laptop, spikes to 400+ µs are normal (CPU frequency scaling, background
> processes). On a dedicated server you'd expect under 100 µs. If you see
> milliseconds, you have a host problem — a noisy neighbour or a hypervisor —
> and no amount of Redis tuning will help.

Round-trip under load:

```bash
docker exec pulse-redis redis-cli --latency-history -i 5
```

| Load | RTT avg | RTT max | Redis `usec_per_call` | Network + syscall |
|------|---------|---------|----------------------|-------------------|
| Idle | 0.11 ms | 0.9 ms | 1.4 µs | ~0.108 ms |
| 50,000 ops/s | 0.14 ms | 2.1 ms | 1.8 µs | ~0.138 ms |
| 200,000 ops/s | 0.38 ms | 11.4 ms | 4.2 µs | ~0.376 ms |

### The breakdown

**Redis's own work is 1–4 µs. The round trip is 110–380 µs.**
Redis is responsible for **~1%** of the latency you observe. The other 99% is
loopback syscall overhead and scheduling.

At 200k ops/s the max jumps to 11.4 ms — that's queueing on the single thread
plus scheduler contention, and it's the number that owns your tail.

### The round-trip budget

```
p99 fan-out budget:            200 ms
Reserve for JVM + fan-out:     140 ms   (Module 06: p99 was 147ms with no Redis)
Available for Redis:            60 ms

At p99 RTT (use max, not avg — you're budgeting the tail):
  idle-ish load  (2.1 ms):   60 / 2.1  = 28 round trips
  heavy load    (11.4 ms):   60 / 11.4 = 5 round trips
```

**Design for 5 sequential Redis round trips per message, maximum.**

Pulse's send path currently uses:
1. `INCR` sequence (Module 09)
2. `XADD` to the stream
3. `HINCRBY` unread counts — **× number of recipients** ← the problem

That third one is N round trips, not one. At a 200-member room that's 200 round
trips = **2.3 seconds at heavy load.** It must be a pipeline or a Lua script,
which is Task 4.

> **The reusable technique:** budget in *round trips*, not milliseconds. Round
> trips are what you control at design time; milliseconds are what the
> environment gives you.

---

## Task 2 — Unbounded keys

```bash
r --bigkeys
r --memkeys
r --scan --pattern '*' | head -10000 | while read k; do
  ttl=$(r TTL "$k"); [ "$ttl" = "-1" ] && echo "NO TTL: $k"
done | sed 's/:[0-9]*$/:*/' | sort | uniq -c | sort -rn
```

**Expected:**
```
Biggest hash   found 'unread:8231' has 4102 fields
Biggest stream found 'room:{9}:stream' has 8214112 entries
Biggest set    found 'user:412:sessions' has 39104 members

  84213 NO TTL: pulse.room.*
  41022 NO TTL: room:*:stream
  38914 NO TTL: unread:*
   9142 NO TTL: user:*:sessions
```

### The audit

| Pattern | Growth bound | Verdict |
|---------|-------------|---------|
| `room:{N}:stream` | **none** — `XADD` without `MAXLEN` | 🔴 **LEAK** — 8.2M entries in one room |
| `unread:{userId}` | rooms per user; never cleaned when a room is deleted | 🔴 **LEAK** — 4,102 fields on one user |
| `user:{id}:sessions` | should be ~3; **`SREM` only runs on clean disconnect** | 🔴 **LEAK** — 39,104 members |
| `presence:{id}` | TTL 45 s | ✅ bounded |
| `rate:{id}` | `PEXPIRE` in the Lua script | ✅ bounded |
| `dedup:{room}:{cid}` | TTL 5 min | ✅ bounded |

### Fix 1 — stream trimming

```java
// BEFORE
redis.opsForStream().add(StreamRecords.newRecord().in(streamKey).ofMap(fields));

// AFTER — approximate trim is much cheaper (whole macro-nodes only)
redis.opsForStream().add(
    StreamRecords.newRecord().in(streamKey).ofMap(fields),
    XAddOptions.maxlen(10_000).approximateTrimming(true));
```

**Measured:**
```bash
r XLEN 'room:{9}:stream'      # before: 8214112
r MEMORY USAGE 'room:{9}:stream'
```
```
8214112
1284918232          # 1.2 GB in ONE room
```
After a `MAXLEN ~ 10000` policy and a one-off `XTRIM`:
```
10214               # note: ~ means approximate, so slightly over
14892104            # 14 MB
```

**86× reduction.** The `~` matters: exact trimming walks entries, approximate
trimming drops whole macro-nodes and is O(1)-ish.

### Fix 2 — session set leak

The `SREM` only ran on `SessionDisconnectEvent`, which does **not** fire when a
node is killed. Every crashed node leaves its sessions in every user's set
forever.

```java
// Sessions expire on their own; the set is rebuilt from the members that exist.
public void registerSession(String userId, String sessionId) {
    String key = "user:{" + userId + "}:sessions";
    redis.opsForZSet().add(key, sessionId, System.currentTimeMillis());
    redis.expire(key, Duration.ofHours(25));                    // backstop
}

/** Called on every read; O(log n) and self-healing. */
public Set<String> liveSessions(String userId) {
    String key = "user:{" + userId + "}:sessions";
    long cutoff = System.currentTimeMillis() - Duration.ofMinutes(2).toMillis();
    redis.opsForZSet().removeRangeByScore(key, 0, cutoff);      // evict the dead
    return redis.opsForZSet().range(key, 0, -1);
}
```

Switching `SET` → `ZSET` scored by last-heartbeat makes the cleanup **implicit**
rather than dependent on a disconnect event that may never arrive.

> **The general principle:** any cleanup that depends on a graceful event is a
> leak, because processes do not always die gracefully. Every key needs either a
> TTL or a size bound that doesn't rely on a callback.

### The automated check

```java
@Component
public class KeyBudgetCheck {

    private record Budget(String pattern, long maxSize, String type) {}

    private static final List<Budget> BUDGETS = List.of(
        new Budget("room:*:stream",    20_000, "stream"),
        new Budget("unread:*",            500, "hash"),
        new Budget("user:*:sessions",      50, "zset"));

    @Scheduled(fixedRate = 300_000)
    public void check() {
        for (Budget b : BUDGETS) {
            // SCAN, never KEYS — Part D of the lab explains why.
            var options = ScanOptions.scanOptions().match(b.pattern()).count(500).build();
            try (Cursor<byte[]> cursor = redis.executeWithStickyConnection(
                    conn -> conn.keyCommands().scan(options))) {
                while (cursor.hasNext()) {
                    String key = new String(cursor.next());
                    long size = sizeOf(key, b.type());
                    if (size > b.maxSize()) {
                        log.error("KEY BUDGET EXCEEDED: {} has {} (max {})", key, size, b.maxSize());
                        budgetViolations.increment();
                    }
                }
            }
        }
    }
}
```
Wire `budgetViolations > 0` to a readiness detail and an alert. **A leak you
detect in five minutes is a bug; a leak you detect in three months is an
incident.**

---

## Task 3 — `noeviction` vs `allkeys-lru`

```bash
r CONFIG SET maxmemory 256mb
r CONFIG SET maxmemory-policy noeviction
k6 run -e SEND_EVERY=1000 --vus 5000 --duration 5m ../06-load-testing-harness/code/pulse-load.js
```

### With `noeviction`

**Application log, within 40 seconds:**
```
ERROR c.p.fanout.RedisFanout : failed to publish to room 41
org.springframework.data.redis.RedisSystemException: Error in execution;
  nested exception is io.lettuce.core.RedisCommandExecutionException:
  OOM command not allowed when used memory > 'maxmemory'.
```
**k6:**
```
ws_errors: 41.20%
```
**Client experience:** sends fail with an error frame; the client retries with
the same `clientId` and gets the same error. **The user sees "failed to send".**

### With `allkeys-lru`

```bash
r CONFIG SET maxmemory-policy allkeys-lru
```
**Application log:**
```
(nothing)
```
**k6:**
```
ws_errors: 0.00%
sequence_gaps: 184,921
```
**Client experience:** everything appears to work. Messages silently vanish from
history. Presence entries get evicted so users appear offline. Rate-limit buckets
get evicted so limits stop applying.

```bash
r INFO stats | grep evicted_keys
```
```
evicted_keys:2841993
```

### The comparison

| | `noeviction` | `allkeys-lru` |
|---|-------------|---------------|
| Error surfaced to app | ✅ `OOM command not allowed` | ❌ none |
| Messages lost | 0 (sends rejected) | **2,841,993 keys evicted** |
| `ws_errors` | 41.2% | 0.00% |
| Sequence gaps | 0 | 184,921 |
| **Time to detection** | **~15 seconds** (error rate alert) | **days** (user reports of "missing messages") |
| Recovery | retry after adding memory | **impossible** — data is gone |

### Which to ship

**`noeviction`, unambiguously, for Pulse's fan-out and state Redis.**

The reasoning is not "errors are good." It's that these are the only two options
and one of them is *undetectable*:

- Under `noeviction` the system **refuses work it cannot do**. The client knows.
  The retry with the same `clientId` succeeds once capacity returns. Nothing is
  lost, and your alerting fires in seconds.
- Under `allkeys-lru` the system **accepts work it cannot do** and quietly
  discards it. There is no error, no metric, and no way to know *which*
  messages went. The 184,921 sequence gaps are permanent holes.

The 41% error rate looks alarming next to 0%. It's the correct behaviour: it is a
capacity problem being reported as a capacity problem, instead of being laundered
into silent corruption.

**Where `allkeys-lru` is right:** a pure read-through cache, where an eviction
costs a recomputation and nothing else. If you run one Redis for both, use
`volatile-lru` and put TTLs **only** on cache keys — then evictions can only
touch things that were disposable by construction.

---

## Task 4 — Pipeline the unread-count hot path

### Before

```java
public void incrementUnread(String roomId, Set<String> memberIds, String except) {
    for (String userId : memberIds) {                 // N sequential round trips
        if (userId.equals(except)) continue;
        redis.opsForHash().increment("unread:{" + userId + "}", roomId, 1);
    }
}
```

### After — pipeline

```java
public void incrementUnread(String roomId, Set<String> memberIds, String except) {
    redis.executePipelined((RedisCallback<Object>) connection -> {
        var hash = connection.hashCommands();
        for (String userId : memberIds) {
            if (userId.equals(except)) continue;
            hash.hIncrBy(("unread:{" + userId + "}").getBytes(), roomId.getBytes(), 1);
        }
        return null;
    });
}
```

**Measured at room size 500, 100 msg/s:**

| | Sequential | Pipelined | Lua |
|---|-----------|-----------|-----|
| Redis round trips per message | 499 | **1** | 1 |
| p50 | 68 ms | **1.9 ms** | 2.1 ms |
| p99 | **1,840 ms** | **14 ms** | 12 ms |
| Redis `usec_per_call` (hincrby) | 1.3 µs | 1.3 µs | 1.1 µs |
| Redis CPU | 22% | 24% | 19% |

✅ **131× improvement at p99, and Redis did identical work.** The
`usec_per_call` is unchanged — every microsecond saved was network round trips.

### When Lua beats a pipeline, and vice versa

**Use a pipeline when:**
- The operations are independent and you only need throughput.
- The **reply set is large** — a pipeline streams replies back; a Lua script
  builds the entire reply in Redis's memory before returning it. A script
  returning 500,000 elements allocates all of it at once on the server.
- You want the operations to be *interruptible* — a long pipeline yields between
  commands; a long script does not.

**Use Lua when:**
- You need **atomicity** — no other client may interleave. A pipeline gives you
  none: another client's `DEL` can land between your commands.
- You need **conditional logic** based on intermediate results ("increment only
  if under the limit"). A pipeline can't branch; you'd need a round trip to
  decide, which defeats the purpose.
- You want to **reduce reply bandwidth** — the script can compute a summary
  server-side and return one number instead of 500.

**For unread counts specifically: pipeline.** The increments are independent,
atomicity across users buys nothing (each user's count is independently correct),
and the pipeline is simpler to reason about and debug.

**For the rate limiter (Module 11): Lua**, because check-then-decrement is
exactly the conditional-on-intermediate-result case.

> ⚠️ **A slow Lua script blocks everything** and cannot be killed once it has
> written (`SCRIPT KILL` refuses; only `SHUTDOWN NOSAVE` clears it). Keep scripts
> to tens of operations, never loops over unbounded input.

---

## Task 5 — Fragmentation

```bash
r FLUSHALL
r CONFIG SET activedefrag no

# varied sizes are the key ingredient — uniform sizes barely fragment
for i in $(seq 1 200); do
  r EVAL "for j=1,20000 do
            local n = (j % 17) * 137
            redis.call('SET', 'frag:'..ARGV[1]..':'..j, string.rep('x', n))
          end" 0 "$i" > /dev/null
done
r INFO memory | grep -E 'used_memory_human|used_memory_rss_human|mem_fragmentation_ratio'
```
**Expected:**
```
used_memory_human:3.11G
used_memory_rss_human:3.28G
mem_fragmentation_ratio:1.05
```

Now delete 90% — specifically, an interleaved 90%:

```bash
for i in $(seq 1 200); do
  r EVAL "for j=1,20000 do
            if j % 10 ~= 0 then redis.call('DEL', 'frag:'..ARGV[1]..':'..j) end
          end" 0 "$i" > /dev/null
done
r INFO memory | grep -E 'used_memory_human|used_memory_rss_human|mem_fragmentation_ratio'
```
**Expected:**
```
used_memory_human:318.42M
used_memory_rss_human:2.94G
mem_fragmentation_ratio:9.46
```

✅ **Redis reports 318 MB. The OS still has 2.94 GB.** A 9.46 ratio. If your
container limit is 4 GB you are one workload spike from an OOM kill, and
`used_memory` will keep telling you everything is fine.

### Why the OS doesn't reclaim it

Memory is returned to the OS in **pages** (4 KB), via `munmap` or `MADV_DONTNEED`
— and only when an *entire* page is free.

```
one 4KB page after the interleaved delete:

 ┌────┬────┬────┬────┬────┬────┬────┬────┐
 │FREE│FREE│FREE│FREE│FREE│FREE│FREE│LIVE│   <- 1 live object
 └────┴────┴────┴────┴────┴────┴────┴────┘
                                      ↑
              this page CANNOT be returned to the OS
```

jemalloc also groups allocations into size classes with per-class arenas. A
freed 137-byte object can only be reused by another 137-byte allocation; it
cannot satisfy a 2 KB request. So a workload whose size distribution *shifts*
fragments even without deletions.

### The fix

```bash
r CONFIG SET activedefrag yes
r CONFIG SET active-defrag-ignore-bytes 100mb
r CONFIG SET active-defrag-threshold-lower 10
r CONFIG SET active-defrag-cycle-min 5
r CONFIG SET active-defrag-cycle-max 25
```

Watch it work, with chat load running:

```bash
while true; do
  r INFO memory | grep -E 'used_memory_rss_human|mem_fragmentation_ratio' | tr '\n' ' '
  r INFO cpu | grep used_cpu_sys | tr -d '\r'
  sleep 10
done
```
**Expected:**
```
used_memory_rss_human:2.94G mem_fragmentation_ratio:9.46  used_cpu_sys:41.2
used_memory_rss_human:2.11G mem_fragmentation_ratio:6.80  used_cpu_sys:48.9
used_memory_rss_human:1.24G mem_fragmentation_ratio:3.99  used_cpu_sys:56.1
used_memory_rss_human:522.1M mem_fragmentation_ratio:1.64 used_cpu_sys:62.8
used_memory_rss_human:381.2M mem_fragmentation_ratio:1.20 used_cpu_sys:64.1
```

**RSS: 2.94 GB → 381 MB in ~50 seconds.**

CPU cost during defrag:

| | Baseline | Defragmenting |
|---|---------|---------------|
| Redis CPU | 51% | **74%** |
| Chat p99 | 154 ms | **198 ms** |
| Chat p99.9 | 412 ms | 640 ms |

**+23% CPU, +29% p99 while it runs.** Active defrag copies live objects to new
allocations and updates pointers — real work, done on the single thread, in small
increments controlled by `active-defrag-cycle-min/max`.

**Recommendation: leave `activedefrag yes` on permanently**, with a conservative
cycle-max. The steady-state cost is near zero (it only runs above the threshold),
and the alternative is discovering a 9× RSS multiplier during an incident.

---

## Task 6 (stretch) — Client-side caching with RESP3

```java
// Lettuce with RESP3 + tracking
var uri = RedisURI.builder().withHost("localhost").withPort(6379)
        .withProtocolVersion(ProtocolVersion.RESP3).build();
var client = RedisClient.create(uri);

Map<String, RoomMeta> localCache = new ConcurrentHashMap<>();

StatefulRedisConnection<String, String> conn = client.connect();
conn.addListener(message -> {
    if ("invalidate".equals(message.getType())) {
        List<String> keys = (List<String>) message.getContent().get(1);
        keys.forEach(localCache::remove);          // Redis told us it changed
        invalidations.increment();
    }
});
conn.sync().clientTracking(TrackingArgs.Builder.enabled());
```

**Measured — room metadata lookups, 20,000 connections, 100 rooms:**

| | Without tracking | With tracking |
|---|-----------------|---------------|
| Redis ops/s for room meta | 41,200 | **310** |
| p50 room-meta lookup | 0.14 ms | **0.0002 ms** |
| Local heap for cache | 0 | 11 MB |
| Invalidation pushes/s | n/a | 310 |
| Redis CPU | 51% | **38%** |

✅ **133× fewer Redis operations**, because room metadata changes rarely and is
read constantly. This is the ideal client-side-caching profile.

### The failure mode: a lost invalidation

Invalidation pushes travel over the same connection with **no acknowledgement**.
If the connection drops between Redis sending the invalidation and the client
processing it, **the client keeps serving stale data forever.**

```
t=0   client caches room.7 { name: "general", private: false }
t=1   admin sets room.7 private
t=2   Redis sends invalidate push
t=3   connection drops in flight — push lost
t=4   client reconnects, re-enables tracking
t=5+  client still serves { private: false }  ...indefinitely
```

For room *names* that's cosmetic. For `private: true` it is a **security bug**:
the client authorizes subscriptions against stale permissions.

### Bounding the staleness

Three mechanisms, all needed:

**1. A TTL on every cached entry** — the essential one.
```java
Cache<String, RoomMeta> localCache = Caffeine.newBuilder()
        .expireAfterWrite(Duration.ofSeconds(30))     // hard staleness bound
        .maximumSize(50_000)
        .build();
```
Now the worst case is 30 seconds, not forever. You've turned an unbounded
correctness bug into a bounded one, at the cost of one refresh per key per 30 s
(still a ~99% reduction).

**2. Flush the entire cache on reconnect.**
```java
conn.addListener(new RedisConnectionStateAdapter() {
    @Override public void onRedisConnected(RedisChannelHandler<?,?> c, SocketAddress a) {
        localCache.invalidateAll();          // we cannot know what we missed
        conn.sync().clientTracking(TrackingArgs.Builder.enabled());
    }
});
```
Any disconnect means unknown missed invalidations. The only safe assumption is
that everything is stale.

**3. Never cache security-relevant data client-side.**
```java
// Room name, topic, icon:  cacheable, 30s staleness is fine
// Room privacy, membership, permissions:  NEVER client-cached
```

**Is it worth it?** For Pulse: **yes for room display metadata, no for
permissions.** The 133× op reduction is real, and a 30-second-stale room name is
harmless. Permission checks stay on Redis with no local cache, because the
failure mode is a security hole and the read volume is far lower anyway.

> **The general rule this illustrates:** any cache whose invalidation is
> best-effort must have a TTL, and the TTL — not the invalidation — is what
> actually bounds your staleness. Invalidation is an optimization that makes the
> common case fast; the TTL is the correctness guarantee.
