# Cheatsheet — Redis for Chat

---

## The mental model

Redis executes **one command at a time on one thread**. Everything follows from
that:

- Every single command is atomic. You never need a lock for one command.
- `MULTI/EXEC` and Lua scripts are atomic *as a unit* for the same reason.
- **A slow command blocks every other client.** `KEYS *`, `SMEMBERS` on a
  million-member set, `LRANGE big 0 -1` — these are outages, not queries.
- Latency is dominated by round trips, not by Redis. Pipeline.

---

## Commands by use case

### Session / connection registry
```bash
HSET  session:{abc123} user 42 node app-2 since 1735689600
EXPIRE session:{abc123} 90
HGETALL session:{abc123}
SADD  user:{42}:sessions abc123
SREM  user:{42}:sessions abc123
```

### Presence with TTL heartbeats
```bash
SET  presence:{42} online EX 45         # refreshed by heartbeat every 15s
EXISTS presence:{42}
# bulk check without N round trips:
MGET presence:{1} presence:{2} presence:{3}
```

### Unread counters
```bash
HINCRBY unread:{42} room:7 1
HGETALL unread:{42}
HDEL    unread:{42} room:7              # mark read
```

### Recent-messages cache (capped)
```bash
LPUSH  room:{7}:recent '{"id":...}'
LTRIM  room:{7}:recent 0 49             # keep newest 50
LRANGE room:{7}:recent 0 19
```

### Rate limiting (see the Lua script below)
```bash
INCR  rate:{42}:1735689600
EXPIRE rate:{42}:1735689600 60          # fixed window — simple, bursty at edges
```

---

## Pub/Sub — at-most-once

```bash
SUBSCRIBE room.7
PSUBSCRIBE room.*                       # pattern; costs more, avoid at scale
PUBLISH room.7 '{"body":"hi"}'          # returns # of receivers, NOT delivery proof

# Redis 7+, cluster-friendly: routes by slot instead of broadcasting cluster-wide
SSUBSCRIBE room.7
SPUBLISH  room.7 '{"body":"hi"}'
```

**What you get:** microsecond fan-out, zero storage.
**What you don't get:** persistence, replay, acknowledgement, or delivery to a
subscriber that was reconnecting. `PUBLISH` returning `0` means nobody was
listening — and Redis does not care.

Use it for: typing indicators, presence blips, cursor positions — anything where
a lost update is corrected by the next one 3 seconds later.

---

## Streams — at-least-once

```bash
# produce (with approximate trim — the ~ matters, it's much cheaper)
XADD room:{7}:stream MAXLEN '~' 10000 '*' body 'hi' sender 42 cid 'c-9f3'

# consumer group setup ($ = only new entries; 0 = from the beginning)
XGROUP CREATE room:{7}:stream fanout '$' MKSTREAM

# read as a member of the group
XREADGROUP GROUP fanout consumer-app-1 COUNT 100 BLOCK 5000 STREAMS room:{7}:stream '>'
#   '>'  = entries never delivered to anyone in this group
#   '0'  = MY pending entries (redelivery after a crash)

# acknowledge — until you do, it sits in the PEL
XACK room:{7}:stream fanout 1735689600000-0

# inspect the Pending Entries List
XPENDING room:{7}:stream fanout
XPENDING room:{7}:stream fanout - + 10 consumer-app-1

# reclaim work from a dead consumer (idle > 30s)
XAUTOCLAIM room:{7}:stream fanout consumer-app-2 30000 0 COUNT 100

# housekeeping
XLEN room:{7}:stream
XRANGE room:{7}:stream - + COUNT 5
XINFO STREAM room:{7}:stream
XINFO GROUPS room:{7}:stream
XTRIM room:{7}:stream MINID '~' 1735689600000
```

### Stream IDs
`<millisecondsTime>-<sequence>` — e.g. `1735689600123-0`. Monotonically
increasing, so `XRANGE` is a time range scan and the ID *is* a cursor. `*` lets
Redis assign one.

### Pub/Sub vs Streams

| | Pub/Sub | Streams |
|---|---------|---------|
| Delivery | At-most-once | At-least-once |
| Persistence | None | Yes, until trimmed |
| Replay after reconnect | Impossible | `XREADGROUP ... 0` or `XRANGE` |
| Consumer scaling | Every subscriber gets everything | Group splits the work |
| Memory cost | ~0 | Grows until trimmed — **budget for it** |
| Backpressure signal | None | `XLEN`, `XPENDING` depth |
| Good for | Typing, presence | Messages, anything durable |

---

## Lua — atomic multi-step logic

Redis runs the whole script without interleaving other commands.

**Token-bucket rate limiter** (Module 11):
```lua
-- KEYS[1]=bucket key  ARGV[1]=capacity ARGV[2]=refill/sec ARGV[3]=now_ms ARGV[4]=cost
local b = redis.call('HMGET', KEYS[1], 'tokens', 'ts')
local cap, rate, now, cost = tonumber(ARGV[1]), tonumber(ARGV[2]), tonumber(ARGV[3]), tonumber(ARGV[4])
local tokens = tonumber(b[1]) or cap
local ts     = tonumber(b[2]) or now
tokens = math.min(cap, tokens + (now - ts) / 1000 * rate)
if tokens < cost then
  redis.call('HMSET', KEYS[1], 'tokens', tokens, 'ts', now)
  redis.call('PEXPIRE', KEYS[1], math.ceil(cap / rate * 1000))
  return {0, math.floor((cost - tokens) / rate * 1000)}   -- denied, retry_after_ms
end
redis.call('HMSET', KEYS[1], 'tokens', tokens - cost, 'ts', now)
redis.call('PEXPIRE', KEYS[1], math.ceil(cap / rate * 1000))
return {1, 0}
```

```bash
redis-cli SCRIPT LOAD "$(cat bucket.lua)"       # → sha
redis-cli EVALSHA <sha> 1 rate:{42} 20 5 "$(date +%s%3N)" 1
```

> **Cluster rule:** every key a script touches must hash to the same slot. Use
> hash tags: `rate:{42}`, `seq:{42}` → same slot. Never compute key names inside
> the script.

---

## Cluster

```bash
redis-cli --cluster create \
  127.0.0.1:7000 127.0.0.1:7001 127.0.0.1:7002 \
  127.0.0.1:7003 127.0.0.1:7004 127.0.0.1:7005 \
  --cluster-replicas 1

redis-cli -c -p 7000 CLUSTER INFO
redis-cli -c -p 7000 CLUSTER NODES
redis-cli -c -p 7000 CLUSTER SHARDS
redis-cli -p 7000 CLUSTER KEYSLOT "room:{7}:stream"
redis-cli --cluster check 127.0.0.1:7000
redis-cli --cluster rebalance 127.0.0.1:7000
```

- **16384 hash slots**, distributed across primaries. `slot = CRC16(key) mod 16384`.
- With a **hash tag**, only the text between the first `{` and the next `}` is
  hashed. `room:{7}:stream` and `room:{7}:seq` → same slot → multi-key ops work.
- `-c` makes `redis-cli` follow `MOVED`/`ASK` redirects. Without it you get an
  error and think the cluster is broken.
- Multi-key commands across slots are **rejected**, not silently slow.

## Sentinel

```bash
redis-cli -p 26379 SENTINEL master pulse
redis-cli -p 26379 SENTINEL replicas pulse
redis-cli -p 26379 SENTINEL get-master-addr-by-name pulse
redis-cli -p 26379 SENTINEL failover pulse      # force one, for drills
```

Minimal `sentinel.conf`:
```
sentinel monitor pulse redis-1 6379 2
sentinel down-after-milliseconds pulse 5000
sentinel failover-timeout pulse 10000
sentinel parallel-syncs pulse 1
```
`2` is the **quorum** — how many sentinels must agree the primary is down. Run
3 sentinels with quorum 2; two sentinels with quorum 1 will split-brain.

### Sentinel vs Cluster

| | Sentinel | Cluster |
|---|---------|---------|
| Sharding | No — one dataset | Yes — 16384 slots |
| HA | Yes | Yes |
| Client complexity | Ask sentinel for the address | Cluster-aware client, follows redirects |
| Multi-key ops | Unrestricted | Same-slot only |
| Use when | Dataset fits one node; you want HA | Dataset or throughput exceeds one node |

---

## Persistence

| | RDB | AOF |
|---|-----|-----|
| What | Periodic point-in-time snapshot | Log of every write command |
| Restart speed | Fast | Slower (replays the log) |
| Worst-case loss | Everything since the last snapshot | `appendfsync` dependent |
| Fork cost | Full `fork()` — can double RSS via COW | Rewrite forks too |

```
save 900 1
appendonly yes
appendfsync everysec     # always = safest+slowest; no = fastest+riskiest
```

> For a **fan-out backbone**, durability is often the wrong goal — the Postgres
> outbox is your source of truth and Redis is the transport. Turning persistence
> *off* can be the correct, defensible choice. Module 08 argues both sides.

---

## Diagnostics

```bash
redis-cli INFO server | grep redis_version
redis-cli INFO clients          # connected_clients, blocked_clients
redis-cli INFO memory           # used_memory_human, maxmemory_policy, mem_fragmentation_ratio
redis-cli INFO stats            # instantaneous_ops_per_sec, keyspace_hits/misses, evicted_keys
redis-cli INFO replication      # role, connected_slaves, master_repl_offset, lag
redis-cli INFO commandstats     # per-command calls + usec_per_call  ← find the slow one
redis-cli INFO latencystats

redis-cli --latency             # min/avg/max round trip, live
redis-cli --latency-history
redis-cli --stat                # ops/sec, memory, clients, once a second
redis-cli --bigkeys             # find the key that's ruining your day
redis-cli --memkeys
redis-cli --hotkeys             # needs maxmemory-policy allkeys-lfu

redis-cli SLOWLOG GET 10
redis-cli SLOWLOG RESET
redis-cli CONFIG SET slowlog-log-slower-than 5000   # µs

redis-cli MONITOR               # every command, live. NEVER in prod — it's a
                                # firehose that can halve your throughput.
redis-cli CLIENT LIST
redis-cli CLIENT KILL ID 42
redis-cli MEMORY USAGE somekey
redis-cli OBJECT ENCODING somekey   # listpack? quicklist? intset? hashtable?
```

### Encodings that matter

Small collections use compact encodings; crossing a threshold silently makes
them 5–10× bigger.

| Type | Compact | Threshold config |
|------|---------|------------------|
| Hash | `listpack` | `hash-max-listpack-entries` (128), `-value` (64) |
| List | `listpack` → `quicklist` | `list-max-listpack-size` (128) |
| Set | `intset` / `listpack` | `set-max-intset-entries` (512) |
| ZSet | `listpack` | `zset-max-listpack-entries` (128) |

---

## Scan, never KEYS

```bash
# WRONG — O(N), blocks everything
redis-cli KEYS 'session:*'

# RIGHT — cursor-based, bounded work per call
redis-cli --scan --pattern 'session:*' | head
redis-cli SCAN 0 MATCH 'session:*' COUNT 100
HSCAN / SSCAN / ZSCAN     # the same idea inside one big key
```
`SCAN` guarantees every key present for the whole iteration is returned at least
once. It may return duplicates. It never blocks.

---

## Spring Data Redis quick reference

```java
StringRedisTemplate redis;                       // most chat state is strings
redis.opsForValue().set("presence:42", "online", Duration.ofSeconds(45));
redis.opsForHash().increment("unread:42", "room:7", 1);
redis.opsForList().leftPush("room:7:recent", json);
redis.opsForList().trim("room:7:recent", 0, 49);

// Pub/Sub
RedisMessageListenerContainer c;                 // has its own thread pool
c.addMessageListener(listener, new PatternTopic("room.*"));

// Streams
StreamMessageListenerContainer<String, MapRecord<String,String,String>> s;
s.receiveAutoAck(Consumer.from("fanout","app-1"),
        StreamOffset.create("room:7:stream", ReadOffset.lastConsumed()), handler);
// receiveAutoAck acks BEFORE your handler runs -> at-most-once. For
// at-least-once use receive(...) and XACK yourself after successful processing.

// Lua
DefaultRedisScript<List> script = new DefaultRedisScript<>(luaText, List.class);
redis.execute(script, List.of("rate:{42}"), "20", "5", now, "1");
```

**Lettuce vs Jedis:** Lettuce is the Spring Boot default — Netty-based,
thread-safe, one connection multiplexed across threads. Jedis needs a pool
(one connection per thread). For a socket server holding many virtual threads,
Lettuce's multiplexing is the right shape. Use Jedis only if you need something
Lettuce lacks.
