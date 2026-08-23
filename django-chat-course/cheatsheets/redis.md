# Cheatsheet — Redis for Chat

---

## The mental model

Redis executes **one command at a time on one thread**. Everything follows from
that:

- Every single command is atomic. You never need a lock for one command.
- `MULTI/EXEC` and Lua scripts are atomic *as a unit* for the same reason.
- **A slow command blocks every other client.** `KEYS *`, `SMEMBERS` on a
  million-member set, `LRANGE big 0 -1` — these are outages, not queries.
  (Module 08 has you stall live chat with `KEYS` to feel it.)
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

### Per-room sequence numbers (gap detection — Module 05)
```bash
INCR room:{7}:seq                       # atomic; the returned value IS the seq
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

## Pub/Sub — at-most-once (this is what `channels_redis` uses)

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

> **This is the default Channels channel layer.** `RedisChannelLayer`'s
> `group_send` is a `PUBLISH`. That's *why* Module 07's `docker pause` loses ~15%
> of messages: a worker reconnecting to Redis misses everything published while it
> was away. Fine for typing indicators, presence blips, cursor positions — anything
> a later update corrects.

---

## Streams — at-least-once (your custom fan-out layer, Module 09)

```bash
# produce (with approximate trim — the ~ matters, it's much cheaper)
XADD room:{7}:stream MAXLEN '~' 10000 '*' body 'hi' sender 42 cid 'c-9f3'

# consumer group setup ($ = only new entries; 0 = from the beginning)
XGROUP CREATE room:{7}:stream fanout '$' MKSTREAM

# read as a member of the group
XREADGROUP GROUP fanout consumer-worker-1 COUNT 100 BLOCK 5000 STREAMS room:{7}:stream '>'
#   '>'  = entries never delivered to anyone in this group
#   '0'  = MY pending entries (redelivery after a crash)

# acknowledge — until you do, it sits in the PEL
XACK room:{7}:stream fanout 1735689600000-0

# inspect the Pending Entries List
XPENDING room:{7}:stream fanout
XPENDING room:{7}:stream fanout - + 10 consumer-worker-1

# reclaim work from a dead consumer (idle > 30s)
XAUTOCLAIM room:{7}:stream fanout consumer-worker-2 30000 0 COUNT 100

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
Redis assign one. This doubles as your **resume token** (Module 10): a
reconnecting client sends its last-seen ID and you `XRANGE` forward from it.

### Pub/Sub vs Streams

| | Pub/Sub | Streams |
|---|---------|---------|
| Delivery | At-most-once | At-least-once |
| Persistence | None | Yes, until trimmed |
| Replay after reconnect | Impossible | `XREADGROUP ... 0` or `XRANGE` |
| Consumer scaling | Every subscriber gets everything | Group splits the work |
| Memory cost | ~0 | Grows until trimmed — **budget for it** (~600 B/entry) |
| Backpressure signal | None | `XLEN`, `XPENDING` depth |
| In Channels | `RedisChannelLayer` (built in) | You build a custom layer (Module 09) |
| Good for | Typing, presence | Messages, anything durable |

> **The Module-09 tradeoff, measured:** Streams add ≈ +5 ms p50 and ≈ 2× Redis
> CPU and real memory — in exchange for **zero loss** where Pub/Sub lost ~15% on a
> `docker pause`. Durability is not free; it's ~5 ms and some RAM.

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

From Python (`redis-py`, async client), register once and call by SHA:
```python
import redis.asyncio as redis
r = redis.Redis(host="localhost", decode_responses=True)
bucket = r.register_script(open("bucket.lua").read())   # handles SCRIPT LOAD/EVALSHA
allowed, retry_ms = await bucket(keys=["rate:{42}"], args=[20, 5, now_ms, 1])
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
- `channels_redis` on Cluster needs sharded Pub/Sub (`SPUBLISH`/`SSUBSCRIBE`) or
  it broadcasts to every node — a Module 18 discussion.

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
`2` is the **quorum** — how many sentinels must agree the primary is down. Run 3
sentinels with quorum 2; two sentinels with quorum 1 will split-brain.

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
> But note: the course's dev Redis runs `--maxmemory-policy noeviction` — losing a
> *sequence counter* or a *presence key* to eviction is a silent correctness bug,
> which is a different question from durability across a restart.

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

Small collections use compact encodings; crossing a threshold silently makes them
5–10× bigger.

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
once. It may return duplicates. It never blocks. From Python: `async for key in
r.scan_iter(match="session:*", count=100):`.

---

## Python (`redis-py`) quick reference

Use the **async** client (`redis.asyncio`) inside async consumers — the sync
client blocks the event loop.

```python
import redis.asyncio as redis

r = redis.Redis(host="localhost", port=6379, decode_responses=True)

# most chat state is strings / hashes
await r.set("presence:42", "online", ex=45)
await r.hincrby("unread:42", "room:7", 1)
await r.lpush("room:7:recent", json_str)
await r.ltrim("room:7:recent", 0, 49)
seq = await r.incr("room:{7}:seq")             # atomic sequence number

# pipeline to kill round trips
async with r.pipeline(transaction=False) as pipe:
    pipe.lpush("room:7:recent", json_str)
    pipe.ltrim("room:7:recent", 0, 49)
    await pipe.execute()

# Streams
await r.xadd("room:{7}:stream", {"body": "hi", "sender": "42", "cid": "c-9"},
             maxlen=10000, approximate=True)
msgs = await r.xreadgroup("fanout", "worker-1",
                          {"room:{7}:stream": ">"}, count=100, block=5000)
await r.xack("room:{7}:stream", "fanout", msg_id)

# Pub/Sub
pubsub = r.pubsub()
await pubsub.subscribe("room.7")
async for message in pubsub.listen():
    ...
```

- **`decode_responses=True`** returns `str` instead of `bytes` — convenient, but
  costs a decode; skip it on the hot path if you're moving raw JSON bytes through.
- **One async client is safe to share** across coroutines in a worker — it
  multiplexes over one connection pool. Don't create a client per message.
- For the channel layer you don't call `redis-py` directly at all — you configure
  `channels_redis` in `CHANNEL_LAYERS` and use `self.channel_layer`. You reach for
  `redis-py` for the *state* Redis holds: presence, sequences, rate limits,
  streams.

```python
# settings.py — the channel layer (Pub/Sub backplane)
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {"hosts": [("redis", 6379)]},
    },
}
```
