# Module 08 — Redis Internals

**Goal:** Understand *why* Redis is fast, *why* one bad command can stall your
entire cluster, and how its memory model turns a working system into an OOM —
so that Modules 09–13 are engineering rather than incantation.

⏱️ ~5 hours · **Prerequisites:** Modules 00–07.

---

## One thread, and everything that follows

```
                    ┌──────────────────────────────────┐
   client 1  ──────▶│                                  │
   client 2  ──────▶│   ONE thread runs commands.      │
   client 3  ──────▶│   One at a time. To completion.  │
   ...       ──────▶│                                  │
   client 50000 ───▶└──────────────────────────────────┘
```

Every property people find surprising about Redis follows from this single fact.

**1. Every command is atomic — for free.**
There is no interleaving, so `INCR` cannot lose an update and `SETNX` cannot
race. You never need a lock for one command. This is why Redis is such a good
coordination primitive.

**2. `MULTI`/`EXEC` and Lua scripts are atomic — for the same reason.**
Not because of clever transaction machinery, but because nothing else runs while
they do.

**3. A slow command is an outage.**
```
KEYS *                     on 10M keys: ~2 seconds
SMEMBERS big_set           on 5M members: ~1.5 seconds + a 200MB reply buffer
LRANGE list 0 -1           on 1M items: ~800ms
FLUSHALL                   (synchronous by default): seconds
```
During those seconds **every other client waits**. Your p99 becomes 2 seconds
because someone ran `KEYS` in a debug console.

**4. Redis is rarely CPU-bound in the way you'd expect.**
Most workloads are bound by network round trips, not by Redis's work. Which is
why pipelining matters more than almost any other optimization.

### "But Redis 6 added threads"

It added **I/O threads** — parallel `read()`/`write()` on client sockets and
parallel protocol parsing. Command *execution* is still serial on one thread.

```
io-threads 4
io-threads-do-reads yes
```

This helps when you're saturated on socket syscalls (many clients, large
payloads). It does nothing for a slow command. Enable it if `INFO commandstats`
shows low `usec_per_call` but high latency — that gap is syscall overhead.

---

## RESP — the wire protocol

Redis's protocol is deliberately trivial. You can speak it with `nc`.

```
Client:  *3\r\n$3\r\nSET\r\n$5\r\nhello\r\n$5\r\nworld\r\n
Server:  +OK\r\n
```

`*3` = an array of 3 elements. `$3` = a bulk string of 3 bytes. That's it.

| Prefix | Type (RESP2) |
|--------|-------------|
| `+` | Simple string — `+OK` |
| `-` | Error — `-ERR unknown command` |
| `:` | Integer — `:1000` |
| `$` | Bulk string — `$5\r\nhello` |
| `*` | Array — `*2\r\n...` |

**RESP3** (Redis 6+, `HELLO 3`) adds native types that matter for us:

| Prefix | Type | Why it matters |
|--------|------|----------------|
| `%` | Map | `XINFO`/`CONFIG GET` return real maps, not flat arrays you re-pair by index |
| `~` | Set | `SMEMBERS` returns a set, not an ordered array implying order that isn't there |
| `,` | Double | No float round-tripping through strings |
| `>` | **Push** | **Out-of-band messages on a normal connection** |

That last one is the important one. In RESP2, a connection in `SUBSCRIBE` mode
can only run subscribe commands — which is why Module 07 needed a second
connection. RESP3 push messages let one connection carry both, and it's what
makes client-side caching (`CLIENT TRACKING`) possible.

### Why the protocol's simplicity is a design decision

Parsing RESP is a few hundred lines. That means:
- Client libraries exist for everything and are hard to get wrong.
- You can debug with `nc`, `telnet`, or `tcpdump` and *read the bytes*.
- Parsing cost is negligible, so the single thread spends its time on real work.

Compare to a binary protocol with a schema registry. Redis chose "boring and
inspectable," and it's a large part of why it's operable.

---

## Pipelining: the optimization that matters most

```
Without pipelining — 3 round trips:
  → SET a 1      ← OK       (0.2ms RTT)
  → SET b 2      ← OK       (0.2ms)
  → SET c 3      ← OK       (0.2ms)
                            total 0.6ms

With pipelining — 1 round trip:
  → SET a 1 / SET b 2 / SET c 3
                 ← OK OK OK  (0.25ms)
                            total 0.25ms
```

At 100 commands the difference is 20 ms versus 0.5 ms. **40×, and Redis did the
same amount of work in both cases.** The network was the cost.

```java
redis.executePipelined((RedisCallback<Object>) connection -> {
    for (var m : batch) connection.stringCommands().set(key(m), value(m));
    return null;
});
```

⚠️ **Pipelining is not a transaction.** Commands may interleave with other
clients' commands between pipelined entries. If you need atomicity, use `MULTI`
or Lua.

---

## Data structure encodings — the silent 10× memory cliff

Redis stores small collections in compact encodings and switches to full ones
above a threshold. Crossing the threshold can multiply memory by 5–10× with no
warning.

| Type | Compact | Threshold config | Full |
|------|---------|------------------|------|
| Hash | `listpack` | `hash-max-listpack-entries` (128), `-value` (64) | `hashtable` |
| List | `listpack` | `list-max-listpack-size` (128) | `quicklist` |
| Set | `intset` / `listpack` | `set-max-intset-entries` (512) | `hashtable` |
| ZSet | `listpack` | `zset-max-listpack-entries` (128) | `skiplist` |

```bash
redis-cli OBJECT ENCODING unread:42
```

A `listpack` is a flat contiguous byte array — no pointers, no hash table, no
per-entry overhead. Lookups are O(n), which is *faster* than a hash table for
small n because it's cache-resident.

**Where this bites Pulse:** `unread:{userId}` is a hash of `roomId → count`.
A user in 100 rooms: `listpack`, ~2 KB. A user in 200 rooms: `hashtable`,
~14 KB. **7× for one more room.**

At a million users that's 2 GB versus 14 GB. Worth knowing which side of the line
your data lives on:

```bash
redis-cli MEMORY USAGE unread:42
redis-cli --bigkeys
```

---

## Memory: where it actually goes

```bash
redis-cli INFO memory
```
```
used_memory_human:2.14G           # what Redis thinks it's using
used_memory_rss_human:2.89G       # what the OS gave it
mem_fragmentation_ratio:1.35      # rss / used
used_memory_peak_human:4.02G      # the high-water mark
maxmemory_human:4.00G
maxmemory_policy:noeviction
mem_allocator:jemalloc-5.3.0
```

**`mem_fragmentation_ratio`** is the number people misread:

| Ratio | Meaning |
|-------|---------|
| ~1.0 | Healthy |
| **> 1.5** | Real fragmentation — enable `activedefrag yes` |
| **< 1.0** | **The OS has swapped Redis out.** This is an emergency; Redis's latency assumptions are destroyed. Disable swap. |

**`used_memory_peak`** matters because Redis doesn't return freed memory to the
OS promptly (jemalloc holds it). A workload that spiked to 4 GB keeps an RSS near
4 GB even after dropping to 2 GB. Size containers on peak, not average.

### Eviction policy is a semantic decision, not a tuning knob

| Policy | Behaviour |
|--------|-----------|
| `noeviction` | **Return an error** on writes when full |
| `allkeys-lru` | Evict least-recently-used, any key |
| `volatile-lru` | Evict LRU among keys **with a TTL** |
| `allkeys-lfu` | Evict least-*frequently*-used |
| `volatile-ttl` | Evict shortest-TTL first |

For a **cache**, `allkeys-lru` is right — losing a cached value costs a
recomputation.

For Pulse's **message backbone**, `noeviction` is right, and the reasoning is the
whole point: under `allkeys-lru`, running out of memory silently deletes a room's
stream, and messages vanish with no error anywhere. Under `noeviction`, `XADD`
fails loudly, the send returns an error, and the client retries. **A loud failure
you can page on beats silent data loss.**

If you mix caches and streams in one Redis, `volatile-lru` plus TTLs only on
cache keys gets you both. Or — better — run two Redises.

---

## Persistence: RDB, AOF, and why you might want neither

| | RDB | AOF |
|---|-----|-----|
| What | Point-in-time snapshot | Log of every write command |
| Restart | Fast (load a compact file) | Slow (replay the log) |
| Loss window | Everything since the last snapshot | `appendfsync` dependent |
| Cost | A `fork()` | A `fork()` on rewrite, plus continuous writes |

### The fork problem

Both use `fork()` to snapshot without blocking. Copy-on-write means the child
initially shares pages — but every page the parent *writes* gets copied.

**On a write-heavy Redis, RSS can approach 2× during a save.** A 4 GB Redis on an
8 GB box can OOM-kill itself mid-snapshot.

```bash
redis-cli INFO persistence | grep -E 'latest_fork_usec|rdb_last_bgsave_status'
```
```
latest_fork_usec:184000        # 184ms of BLOCKED time — every client waited
rdb_last_bgsave_status:ok
```

That `latest_fork_usec` is a stop-the-world pause. On a large instance it can be
seconds — and it will show up as a mysterious p99.9 spike in your chat latency
that correlates with nothing in your application.

### The case for turning persistence OFF

For a pure fan-out backbone, persistence may be **actively wrong**:

- Postgres (Module 12) is the source of truth. Redis holds in-flight state.
- On restart you *want* an empty Redis — stale streams and presence entries are
  worse than none.
- You avoid fork pauses entirely.
- You avoid the disk I/O.

```
save ""
appendonly no
```

**But** you then lose the pending-entries list on restart (Module 09), so
in-flight messages that were delivered-but-not-acked are gone. Whether that
matters depends on whether the outbox can replay them — which it can (Module 13).

> **This is a genuinely contested design decision, and defending your answer is
> the module's real exercise.** Pulse turns persistence off on the fan-out Redis
> and on for the presence/state Redis. The lab measures both.

---

## Latency diagnosis

```bash
redis-cli --latency                    # min/avg/max round trip, live
redis-cli --latency-history            # over time
redis-cli --intrinsic-latency 30       # the MACHINE's floor, no Redis involved
```

`--intrinsic-latency` is the underrated one. It measures how long the *kernel*
takes to schedule a busy loop. If it reports 800 µs, your Redis can never be
faster than that, and the problem is your host (a noisy neighbour, CPU frequency
scaling, or a hypervisor), not Redis.

```bash
redis-cli SLOWLOG GET 10
redis-cli CONFIG SET slowlog-log-slower-than 5000     # microseconds
redis-cli INFO commandstats
```

`INFO commandstats` is where you find the actual culprit:
```
cmdstat_xadd:calls=4821993,usec=8679587,usec_per_call=1.80
cmdstat_keys:calls=3,usec=6104882,usec_per_call=2034960.67
```
Three `KEYS` calls consumed **6.1 seconds** of your single thread. That's your
outage.

⚠️ **`MONITOR` is a footgun.** It streams every command to your terminal and can
halve throughput. Useful in development, never in production.

---

## Lua: atomicity you control

```lua
-- KEYS[1] = counter, ARGV[1] = limit
local current = tonumber(redis.call('GET', KEYS[1]) or '0')
if current >= tonumber(ARGV[1]) then return 0 end
redis.call('INCR', KEYS[1])
return 1
```

The whole script runs without interleaving. That check-then-act, which would be a
race in your application, is atomic here.

**Three rules:**

1. **Declare every key in `KEYS`, never build key names inside the script.**
   Cluster needs to know which slots you touch, statically.
2. **All keys must hash to the same slot in Cluster.** Use hash tags:
   `rate:{42}`, `bucket:{42}`.
3. **Scripts must be deterministic** and fast. A slow script blocks everything;
   `lua-time-limit` (default 5 s) only makes Redis start answering `BUSY`, it
   does not kill the script (only `SCRIPT KILL` does, and not if it has written).

```java
DefaultRedisScript<Long> script = new DefaultRedisScript<>(luaSource, Long.class);
redis.execute(script, List.of("rate:{42}"), "100");
```

Spring caches the script by SHA and uses `EVALSHA`, falling back to `EVAL` on
`NOSCRIPT` — so you pay the script body's bandwidth once, not per call.

---

## What's next

The lab has you speak RESP by hand with `nc`, measure the pipelining win, cross
an encoding threshold and watch memory jump, cause a fork pause and see it in
your chat latency, and take down your own Redis with `KEYS`.

See you in [`lab.md`](./lab.md).
