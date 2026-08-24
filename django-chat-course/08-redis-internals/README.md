# Module 08 — Redis Internals

**Goal:** Understand *why* Redis behaved the way Module 07 measured — why one
thread was your ceiling at eight workers, why one command in a debug console
can add three seconds to every user's message, and how a decision about key
names you make today turns Module 18's Cluster migration from a rewrite into a
config change.

⏱️ ~5 hours · **Prerequisites:** Modules 00–07. Module 07 left you with a
working two-layer backplane and a wall: **Redis's single thread at 94%, and an
eighth worker that made things worse.** This module is why.

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

Every property people find surprising about Redis follows from that one fact.

**1. Every command is atomic — for free.** There is no interleaving, so `INCR`
cannot lose an update and `SETNX` cannot race. You never need a lock for one
command. This is why Redis is such a good coordination primitive, and it is why
Module 05's `INCR room:{7}:seq` is a correct sequence generator in three
characters.

**2. `MULTI`/`EXEC` and Lua scripts are atomic — for the same reason.** Not
because of transaction machinery, but because nothing else runs while they do.

**3. A slow command is an outage.**
```
KEYS *                     on 10M keys: ~3 seconds
SMEMBERS big_set           on 5M members: ~1.5 s + a 200 MB reply buffer
LRANGE list 0 -1           on 1M items: ~800 ms
XRANGE stream - +          on a 1M-entry stream: seconds
FLUSHALL                   (synchronous by default): seconds
```
During those seconds **every other client waits**, including all eight of your
workers' `BZPOPMIN` loops. Your chat p99 becomes three seconds because someone
ran `KEYS` in a console.

**4. Redis is rarely bound by the work you think it is doing.** Module 07's
measurement said Redis spends **55 µs + 46 µs per worker** on a `group_send` —
and most of that 46 µs is not the `ZADD`, it is waking a blocked client and
writing to its socket. Which is why the fix for a saturated Redis is almost
never "make the commands cheaper".

### "But Redis 6 added threads"

It added **I/O threads** — parallel `read()`/`write()` on client sockets and
parallel protocol parsing. **Command execution is still serial on one thread.**

```
io-threads 4
io-threads-do-reads yes
```

This helps when you are saturated on socket syscalls: many clients, large
payloads, lots of small replies. **That is close to Pulse's profile**, so the
lab measures it rather than dismissing it — and the result is not what the
marketing implies. It does nothing at all for a slow command.

---

## RESP — the wire protocol

Redis's protocol is deliberately trivial. You can speak it with `nc`, and
[`code/resp.py`](./code/resp.py) implements a complete reader in sixty lines.

```
Client:  *3\r\n$3\r\nSET\r\n$5\r\nhello\r\n$5\r\nworld\r\n
Server:  +OK\r\n
```

`*3` = an array of 3 elements. `$3` = a bulk string of 3 bytes. That is it.

| Prefix | Type (RESP2) |
|--------|-------------|
| `+` | Simple string — `+OK` |
| `-` | Error — `-ERR unknown command` |
| `:` | Integer — `:1000` |
| `$` | Bulk string — `$5\r\nhello` (`$-1` = nil) |
| `*` | Array — `*2\r\n…` |

**RESP3** (Redis 6+, opt in with `HELLO 3`) adds types that matter here:

| Prefix | Type | Why it matters to Pulse |
|--------|------|------------------------|
| `%` | Map | `XINFO`, `CONFIG GET`, `INFO` return real maps instead of flat arrays you re-pair by index — a genuine, recurring source of client bugs |
| `~` | Set | `SMEMBERS` returns a set, not an array implying an order that is not there |
| `,` | Double | No floats round-tripping through strings |
| `>` | **Push** | **Out-of-band messages on a normal connection** |

That last one is the important one. **In RESP2 a connection in `SUBSCRIBE` mode
may only run subscribe-family commands** — which is precisely why Module 07's
`RedisPubSubChannelLayer` holds two connections per worker (`_redis` and
`_pubsub`). RESP3 push messages let one connection carry both, and they are what
makes client-side caching (`CLIENT TRACKING`) possible at all.

### Why the protocol's simplicity is a design decision

Parsing RESP is a few hundred lines. That means client libraries exist for
everything and are hard to get wrong; you can debug with `nc`, `telnet` or
`tcpdump` and *read the bytes*; and parsing cost is negligible, so the single
thread spends its time on real work. Compare with a binary protocol behind a
schema registry. Redis chose "boring and inspectable", and that is a large part
of why it is operable at 3 a.m.

---

## The command mix Pulse actually issues

Generic Redis advice is useless without knowing your own workload. Here is
Pulse's, as of Module 07, measured with `INFO commandstats`.

**`RedisChannelLayer` (the message path), per `group_send`:**

| Command | Times | What it is |
|---------|-------|-----------|
| `ZREMRANGEBYSCORE` on the group key | 1 | drop members older than `group_expiry` |
| `ZRANGE <group> 0 -1` | 1 | read the membership — **reply size scales with room size** |
| `ZREMRANGEBYSCORE` on each mailbox | W | drop messages older than `expiry` |
| `EVAL` (one script, W keys) | 1 | `ZADD` the msgpack'd message + `EXPIRE`, per mailbox |
| `BZPOPMIN` returning | W | one blocked worker woken per destination |

**`RedisPubSubChannelLayer` (the ephemeral path), per `group_send`:**

| Command | Times |
|---------|-------|
| `PUBLISH <group channel>` | **1** |

**Everything else Pulse will store in Redis, and where it comes from:**

| Key | Type | Module | Bounded by |
|-----|------|--------|-----------|
| `pulse:group:room.<slug>` | zset | 07 | `group_expiry` |
| `pulsespecific.<worker>!` | zset | 07 | `capacity` + `expiry` |
| `room:{<slug>}:seq` | string | 05 | one integer |
| `room:{<slug>}:stream` | stream | 09 | `XADD MAXLEN ~` |
| `presence:{<user>}` | string | 11 | TTL 45 s |
| `rate:{<user>}:*` | hash | 11 | `PEXPIRE` inside the Lua script |
| `unread:{<user>}` | hash | 10 | rooms per user — **see the encoding cliff** |
| `wsticket:{<user>}:*` | string | 21 | TTL 30 s |

**Notice the braces.** Everything Pulse *owns* is hash-tagged by the entity that
multi-key operations group on. Everything `channels_redis` owns is not, because
it was not written for Cluster. That distinction is the last section of this
README and the reason Module 18 works.

---

## Pipelining: the optimisation that matters most

```
Without pipelining — 3 round trips:      With pipelining — 1 round trip:
  -> SET a 1   <- OK    (0.2 ms)           -> SET a 1 / SET b 2 / SET c 3
  -> SET b 2   <- OK    (0.2 ms)                        <- OK OK OK  (0.25 ms)
  -> SET c 3   <- OK    (0.2 ms)
                 total 0.6 ms                            total 0.25 ms
```

At 100 commands the difference is 20 ms versus 0.5 ms. **40×, and Redis did the
same amount of work in both cases.** The network was the cost.

⚠️ **Pipelining is not a transaction.** Another client's commands may interleave
between your pipelined entries. If you need atomicity, use `MULTI` or Lua.

There is a Python-specific wrinkle worth measuring, and the lab does: in an
async application, **many coroutines each issuing one command** already overlap
their round trips through the connection pool, so the gap between "naive async"
and "explicit pipeline" is much smaller than the gap between "naive sync" and
"pipeline". Whether it is small enough to skip the pipeline is a number, not an
opinion.

---

## Encodings — the silent, irreversible memory cliff

Redis stores small collections in compact encodings and switches to full ones
above a threshold. Crossing it can multiply memory by 5–10× with no warning, and
**it never converts back.**

| Type | Compact | Threshold | Full |
|------|---------|-----------|------|
| Hash | `listpack` | `hash-max-listpack-entries` (128), `-value` (64) | `hashtable` |
| List | `listpack` | `list-max-listpack-size` (128) | `quicklist` |
| Set | `intset` / `listpack` | `set-max-intset-entries` (512) | `hashtable` |
| ZSet | `listpack` | `zset-max-listpack-entries` (128) | `skiplist` |

A `listpack` is a flat contiguous byte array — no pointers, no hash table, no
per-entry overhead. Lookups are O(n), which is *faster* than a hash table for
small n because it is cache-resident.

**Where this bites Pulse:** `unread:{<user>}` is a hash of room → count. A user
in 100 rooms is a `listpack` at ~2 KB. A user in 129 rooms is a `hashtable` at
~9.5 KB. **4× for one more room, permanently.** At a million users that is 1.9 GB
versus 9.5 GB.

It also bites `channels_redis` in a way nobody documents: `pulse:group:room.7`
is a **zset**, and a room with more than `zset-max-listpack-entries` (128)
members converts to a skiplist. The lab measures whether that matters.

---

## Memory: where it actually goes

```bash
redis-cli INFO memory
```
```
used_memory_human:2.14G           # what Redis thinks it is using
used_memory_rss_human:2.89G       # what the OS gave it
mem_fragmentation_ratio:1.35      # rss / used
used_memory_peak_human:4.02G      # the high-water mark
maxmemory_human:1.00G
maxmemory_policy:noeviction
mem_allocator:jemalloc-5.3.0
```

**`mem_fragmentation_ratio` is the number people misread:**

| Ratio | Meaning |
|-------|---------|
| ~1.0 | Healthy |
| **> 1.5** | Real fragmentation — consider `activedefrag yes` |
| **< 1.0** | **The OS has swapped Redis out.** An emergency: every latency assumption in this course is void. Disable swap. |

**`used_memory_peak` matters** because jemalloc does not promptly return freed
memory to the OS. A workload that spiked to 4 GB keeps an RSS near 4 GB after
dropping to 2 GB. **Size containers on peak, not average** — Module 19's
`resources.limits` uses this number.

---

## Eviction is a semantic decision, not a tuning knob

| Policy | Behaviour |
|--------|-----------|
| `noeviction` | **Return an error** on writes when full |
| `allkeys-lru` | Evict least-recently-used, any key |
| `volatile-lru` | Evict LRU among keys **with a TTL** |
| `allkeys-lfu` | Evict least-*frequently*-used |
| `volatile-ttl` | Evict shortest-TTL first |

For a **cache**, `allkeys-lru` is right — losing a cached value costs a
recomputation.

For Pulse, `infra/compose.dev.yml` already pins **`noeviction`**, and this
module is where you defend it. Under `allkeys-lru`, memory pressure silently
deletes whichever key Redis feels like: a `room:{7}:seq` counter (every client
sees a gap and triggers a resume storm), a `pulse:group:room.7` (Module 07's
139-of-200 failure, on a Tuesday, with no restart), or a stream entry (a message
gone with no error anywhere). Under `noeviction` the write fails loudly, your
consumer raises, your alert fires, and you fix the sizing.

**A loud failure you can page on beats silent data loss.** If you must mix
caches and correctness state in one Redis, use `volatile-lru` and put TTLs
**only** on the cache keys — then evictions can only touch things that were
disposable by construction. Or, better, run two Redises.

---

## Persistence: RDB, AOF, and the case for neither

| | RDB | AOF |
|---|-----|-----|
| What | Point-in-time snapshot | Log of every write command |
| Restart | Fast (load a compact file) | Slow (replay the log) |
| Loss window | Everything since the last snapshot | `appendfsync` dependent |
| Cost | A `fork()` | A `fork()` on rewrite, plus continuous writes |

### The fork problem

Both use `fork()` to snapshot without blocking. Copy-on-write means the child
initially shares pages — but every page the *parent* writes gets copied. **On a
write-heavy Redis, RSS can approach 2× during a save.**

```bash
redis-cli INFO persistence | grep -E 'latest_fork_usec|rdb_last_bgsave_status'
```
```
latest_fork_usec:184000        # 184 ms during which every client waited
```

That is a stop-the-world pause, and it will appear in your chat p99.9 as a spike
that correlates with **nothing in your application logs**. Module 07 measured
p99.9 at 712 ms; a 271 ms fork lands right on top of it.

### The case for turning it off

Pulse's dev Redis runs `--save "" --appendonly no`, deliberately. Postgres is the
source of truth (Module 12), the outbox can replay (Module 13), and on restart
you *want* an empty Redis — stale presence entries and half-consumed streams are
worse than none.

**But Module 07 showed the bill for that choice**: an empty Redis after a restart
means the core layer's group ZSETs are gone, which cost 139 of 200 messages and
never recovered until you built the guard. **Persistence is not about durability
here; it is about how much state you have accidentally made Redis authoritative
for.** That is the argument the challenge makes you settle with data.

---

## Latency diagnosis, in the order that converges fastest

```bash
redis-cli --intrinsic-latency 30   # 1. the MACHINE's floor, no Redis involved
redis-cli --latency                # 2. actual round trip, live
redis-cli --stat                   # 3. ops/s, memory, clients, once a second
redis-cli INFO commandstats        # 4. WHO is spending the single thread
redis-cli SLOWLOG GET 10           # 5. what already blocked it
redis-cli MEMORY DOCTOR            # 6. a second opinion on INFO memory
```

`--intrinsic-latency` is the underrated one. It measures how long the *kernel*
takes to schedule a busy loop. If it reports 800 µs, Redis can never be faster
than that and your problem is the host — a noisy neighbour, frequency scaling, a
hypervisor — not Redis.

`INFO commandstats` is where you find the culprit:
```
cmdstat_eval:calls=4821993,usec=8679587,usec_per_call=1.80
cmdstat_keys:calls=3,usec=6104882,usec_per_call=2034960.67
```
**Three `KEYS` calls consumed 6.1 seconds of your single thread.** That is your
outage, and it is one line of output.

[`code/redis_doctor.py`](./code/redis_doctor.py) asks all six in order and adds
the one thing `redis-cli` will not: which of Pulse's key patterns have no bound
on their growth.

⚠️ **`MONITOR` is a footgun.** It streams every command to your terminal and can
halve throughput. Development only.

---

## Lua: atomicity you control

```lua
-- KEYS[1] = counter, ARGV[1] = limit
local current = tonumber(redis.call('GET', KEYS[1]) or '0')
if current >= tonumber(ARGV[1]) then return 0 end
redis.call('INCR', KEYS[1])
return 1
```

The whole script runs without interleaving. That check-then-act, which is a race
in your application, is free here.

**Three rules:**

1. **Declare every key in `KEYS`. Never build a key name inside the script.**
   Cluster must know statically which slots you touch.
2. **All keys must hash to the same slot in Cluster.** Hash tags: `rate:{42}`,
   `room:{7}:seq`.
3. **Scripts must be deterministic, bounded and short.** A slow script blocks
   everything; `lua-time-limit` (default 5 s) only makes Redis start answering
   `-BUSY`. It does not kill the script — `SCRIPT KILL` does, and **it refuses
   once the script has written anything.** At that point your only option is
   `SHUTDOWN NOSAVE`.

From Python, `redis-py` handles `SCRIPT LOAD`/`EVALSHA` with a fallback:

```python
append = r.register_script(open("code/append.lua").read())
seq, entry_id = await append(keys=[f"room:{{{slug}}}:seq",
                                   f"room:{{{slug}}}:stream"],
                             args=[10_000, client_id, sender, body, ts])
```

You pay the script body's bandwidth once, not per call.

---

## Hash tags — the decision you make today for Module 18

Redis Cluster splits the keyspace into **16,384 hash slots**:
`slot = CRC16(key) mod 16384`. A multi-key command whose keys span slots is
**rejected**, not silently slow:

```
(error) CROSSSLOT Keys in request don't hash to the same slot
```

A **hash tag** overrides what gets hashed: only the text between the first `{`
and the next `}`. So

```
room:{7}:seq      -> CRC16("7") -> slot 1716
room:{7}:stream   -> CRC16("7") -> slot 1716      same node, same script
```

**On a single Redis the braces do absolutely nothing.** That is exactly why you
add them now. Renaming every key in a running system is a migration with a
dual-write window; adding braces to key names you have not shipped yet is free.

**The rule, stated so you can apply it to a key you invent in Module 21:**
*tag by the entity that your multi-key operations group on.* For Pulse that is
almost always the **room** (`room:{<slug>}:*`, because sequence + stream + trim
are one atomic unit) or the **user** (`rate:{<uid>}:*`, `unread:{<uid>}`,
`presence:{<uid>}`, because rate-limit buckets are checked together).

Where it goes wrong is subtle and Module 18 finds a real example: a key tagged
by its own random value, or by node, or by whatever was convenient — which
works perfectly on one Redis, and is a `CROSSSLOT` error the day you cluster,
five modules later, under load, during a migration.

```bash
redis-cli CLUSTER KEYSLOT "room:{7}:seq"
redis-cli CLUSTER KEYSLOT "room:{7}:stream"
```
Those two lines work on a single node too, and they are the cheapest CI check in
this course. The challenge builds it.

> **What you cannot fix with tags:** `channels_redis` was not written for
> Cluster. `pulse:group:room.7` and `pulsespecific.<worker>!` have no tags, and
> `group_send`'s `EVAL` touches one key per worker — which in Cluster is a
> guaranteed `CROSSSLOT`. That is not a bug you can configure around; it is why
> Module 18 discusses sharded Pub/Sub (`SSUBSCRIBE`/`SPUBLISH`) and why Module
> 09's Streams path — whose keys you *do* own and *have* tagged — clusters
> cleanly. **Own your keys.**

---

## What's next

The lab has you speak RESP by hand and watch a RESP3 push arrive on a busy
connection; measure the pipelining win at 0 ms and 1 ms RTT; profile the exact
command mix your own channel layer issues; cross an encoding threshold and watch
memory jump 4× irreversibly; **stall live chat for three seconds with one
command** and then do the same work with `SCAN` for free; catch a fork pause in
your p99.9; decide persistence and eviction with data; and load the `append.lua`
script that Modules 09 and 18 both depend on.

See you in [`lab.md`](./lab.md).
