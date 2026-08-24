# Solutions — Module 08

Reference machine: **8-core / 16 GB, Ubuntu 24.04, Redis 7.4.1 in Docker,
Python 3.12, `redis-py` 5.x**, Pulse on 8 Uvicorn workers with
`RedisChannelLayer` from Module 07.

---

## Task 1 — The latency budget, in round trips

### The floor

```bash
docker exec pulse-redis redis-cli --intrinsic-latency 60
```
**Expected:**
```
Max latency so far: 1 microseconds.
Max latency so far: 41 microseconds.
Max latency so far: 412 microseconds.

1948372910 total runs
Worst run took 412x longer than the average latency.
```

**41 µs typical, 412 µs worst — with no Redis involved at all.** That is the
kernel failing to reschedule a busy loop: frequency scaling, background
processes, a hypervisor. Redis can never be faster than it, and no Redis tuning
touches it. Spikes into the hundreds of microseconds are normal on a laptop; on
a dedicated server expect under 100 µs; **if you see milliseconds, stop tuning
Redis and go fix the host.**

### Round trips under three loads

```bash
docker exec pulse-redis redis-cli --latency-history -i 5
./code/redis_doctor.py --only floor --only thread
```

| Load | RTT p50 | RTT p99 | RTT max | Redis `usec_per_call` | Kernel floor | Everything else |
|------|---------|---------|---------|----------------------|--------------|-----------------|
| Idle | 0.108 ms | 0.284 ms | 1.91 ms | 1.4 µs (`ping`) | 0.041 ms | 0.066 ms |
| Module 06 baseline (66,307 out/s) | 0.121 ms | 0.412 ms | 3.20 ms | 25 µs (`bzpopmin`) | 0.041 ms | 0.055 ms |
| 8-worker knee (441,000 out/s) | **0.394 ms** | **11.8 ms** | **41.2 ms** | 40 µs (`eval`) | 0.041 ms | **11.7 ms** |

### Reading the decomposition

**Redis's own work is 1.4–40 µs. The round trip is 108–394 µs.** At the
baseline, Redis is responsible for roughly **20%** of the median round trip; the
rest is syscall overhead and scheduling on both ends.

**At the knee the p99 jumps 29× while the p50 jumps 3×.** That gap is queueing
on the single thread, and it is the entire story of this module: Redis's *mean*
cost is a property of your commands, and its *tail* is a property of your
utilisation.

### The round-trip budget

```
p99 fan-out budget                          200 ms
Module 07 measured, 8 workers, at 66k out/s 181 ms
                                            ------
available for ADDITIONAL sequential Redis    19 ms
```

Budget at the **tail**, not the mean, and the reason is not conservatism — it is
that the delays are **correlated**. Every one of your round trips queues behind
the same single thread, so a busy Redis makes all of them slow at once. Adding
mean latencies would be defensible for independent delays; these are not
independent.

| Operating point | p99 RTT | Round trips you can afford |
|-----------------|---------|---------------------------|
| Idle | 0.284 ms | 66 |
| Baseline (66k out/s) | 0.412 ms | **46** |
| Safe operating point (65% of knee, 287k out/s) | 2.1 ms | **9** |
| **At the knee (441k out/s)** | **11.8 ms** | **1** |

✅ **Design for nine sequential Redis round trips per message, and remember that
number is only true if you are not at the knee.** The most useful line in that
table is the last one: at the knee you can afford *one*, which means "operate at
65%" is not a comfort margin — it is what makes a multi-step Redis design
possible at all.

### Auditing Pulse's send path

```bash
r CONFIG RESETSTAT
# send exactly one message
r INFO commandstats | grep -c cmdstat_
r MONITOR &     # one message only, then kill it
```

Today, one `message.create` costs:

| # | Round trip | Scales with |
|---|-----------|-------------|
| 1 | `ZREMRANGEBYSCORE pulse:group:room.7` | — |
| 2 | `ZRANGE pulse:group:room.7 0 -1` | **reply size ∝ room members** |
| 3 | one pipeline of `ZREMRANGEBYSCORE`, one per worker | — (pipelined) |
| 4 | `EVAL` (`ZADD` + `EXPIRE` per worker) | argument size ∝ workers |
| | **4 sequential round trips**, and Postgres does the sequence allocation | |

**Nothing in the send path scales in *round-trip count* with room size — yet.**
What scales is #2's **reply size**: a 500-member room means a 500-element
`ZRANGE` reply built on the single thread, every message. That is a per-round-
trip cost, not an extra round trip, and it is why Module 07's model has a fixed
55 µs term that is really "35 µs of `ZRANGE` at 200 members".

**The first path that will scale in round trips is Module 11's presence
lookup** — "who is online in this room?" — which is N `GET`s for N members.
Task 4 pre-empts it, because at a 500-member room and the knee's 11.8 ms p99
RTT, 499 sequential round trips is **5.9 seconds**.

Budget remaining after the send path:

```
4 round trips used of 9 available at the safe operating point
   -> Module 09 may add 1 (append.lua does INCR + XADD in ONE call)
   -> Module 11 may add 1 (the rate-limit script is one EVALSHA)
   -> Module 10 may add 1 (unread increments, pipelined)
   -> 2 spare
```

> **The reusable technique:** budget in *round trips*, not milliseconds. Round
> trips are what you control at design time; milliseconds are what the
> environment gives you. And write the budget down, because the fifth engineer
> to touch the send path will not derive it independently.

---

## Task 2 — Growth bounds, leaks, and fragmentation

### The audit

```bash
r --bigkeys
r --memkeys
r --scan --pattern '*' | head -20000 | while read -r k; do
  [ "$(r TTL "$k")" = "-1" ] && echo "$k"
done | sed -E 's/[0-9a-zA-Z_.-]+$/*/' | sort | uniq -c | sort -rn | head
```

**Expected:**
```
Biggest zset   found 'pulse:group:room.41' has 200 members
Biggest hash   found 'unread:8231' has 4102 fields
Biggest set    found 'user:412:sessions' has 39104 members
Biggest stream found 'room:{9}:stream' has 8214112 entries

  84213 unread:*
  41022 room:*:seq
   9142 user:*:sessions
```

| Pattern | What bounds it | Verdict |
|---------|---------------|---------|
| `pulse:group:room.*` | `group_expiry` TTL, refreshed by Module 07's heartbeat | ✅ |
| `pulsespecific.*` | `capacity` 1500 + `expiry` 10 s | ✅ |
| `presence:{u}` | TTL 45 s | ✅ |
| `rate:{u}:*` | `PEXPIRE` inside the Lua script | ✅ |
| `wsticket:{u}:*` | TTL 30 s | ✅ |
| `room:{s}:stream` | **nothing** — `XADD` without `MAXLEN` | 🔴 **LEAK** (8.2 M entries, 1.2 GB in one room) |
| `unread:{u}` | rooms per user; never cleaned when a room is deleted | 🔴 **LEAK** (4,102 fields) |
| `user:{u}:sessions` | should be ~3; **`SREM` only runs on clean disconnect** | 🔴 **LEAK** (39,104 members) |
| `room:{s}:seq` | one integer per room; never deleted | ⚠️ bounded by room count, but see below |

### Fix 1 — remove the dependence on graceful cleanup

`user:{u}:sessions` is the one to fix first, because it is a leak **by
construction**: the `SREM` runs in `disconnect()`, and `disconnect()` does not
run when a worker is `SIGKILL`ed, OOM-killed, or evicted by Kubernetes. Every
ungraceful worker death leaves its sessions in every affected user's set,
forever.

```python
# BEFORE — correct only if processes always die politely
await r.sadd(f"user:{{{uid}}}:sessions", self.channel_name)
# ... in disconnect():
await r.srem(f"user:{{{uid}}}:sessions", self.channel_name)
```
```python
# AFTER — a sorted set scored by last heartbeat. Cleanup is implicit.
SESSION_TTL = 120          # > 2x the 10 s protocol heartbeat, < any human patience

async def touch_session(r, uid: str, channel: str) -> None:
    key = f"user:{{{uid}}}:sessions"
    async with r.pipeline(transaction=False) as pipe:
        pipe.zadd(key, {channel: time.time()})
        pipe.expire(key, 86_400)              # backstop for a user who vanishes
        await pipe.execute()

async def live_sessions(r, uid: str) -> list[str]:
    """O(log n), self-healing, and it does not care how anything died."""
    key = f"user:{{{uid}}}:sessions"
    async with r.pipeline(transaction=False) as pipe:
        pipe.zremrangebyscore(key, 0, time.time() - SESSION_TTL)
        pipe.zrange(key, 0, -1)
        _, members = await pipe.execute()
    return members
```

**Measured**, after a deliberate `kill -9` of four workers holding 40,000
sessions:

| | `SET` + `SREM` | `ZSET` + prune-on-read |
| Stale members after 4 SIGKILLs | **39,104** | **0** (within 120 s) |
| Bytes for one heavy user | 1.9 MB | 4.2 KB |
| Cost per read | `SMEMBERS` O(n) | `ZREMRANGEBYSCORE` + `ZRANGE`, one pipeline |

> **The principle, and it generalises past Redis:** *any cleanup that depends on
> a graceful event is a leak, because processes do not always die gracefully.*
> Every key needs a TTL, a size bound, or a prune-on-read — never a callback.

### Fix 2 — bound the unread hash, and keep it a listpack

```python
# BEFORE
await r.hincrby(f"unread:{{{uid}}}", room_key, 1)
```
```python
# AFTER
UNREAD_SHARDS = 4          # keeps each shard under hash-max-listpack-entries

def unread_key(uid: str, room_key: str) -> str:
    # The hash tag keeps all four shards on ONE slot, so a user's unread state
    # is still readable in a single pipeline in Cluster.
    shard = zlib.crc32(room_key.encode()) % UNREAD_SHARDS
    return f"unread:{{{uid}}}:{shard}"

async def bump_unread(r, uid: str, room_key: str) -> None:
    key = unread_key(uid, room_key)
    async with r.pipeline(transaction=False) as pipe:
        pipe.hincrby(key, room_key, 1)
        pipe.expire(key, 90 * 86_400)          # a user who never returns
        await pipe.execute()
```

Plus a reconciler that removes rooms the user is no longer a member of —
because membership changes in Postgres and Redis has no way to know:

```python
@shared_task                      # Celery, nightly (Module 13 owns the beat)
def prune_unread(uid: str) -> None:
    live = {r.key for r in Room.objects.filter(membership__user_id=uid)}
    for shard in range(UNREAD_SHARDS):
        key = f"unread:{{{uid}}}:{shard}"
        stale = set(redis.hkeys(key)) - live
        if stale:
            redis.hdel(key, *stale)
```

**Measured** on the worst user (4,102 fields):

| | Before | After |
|---|--------|-------|
| Encoding | `hashtable` | **`listpack` × 4** |
| Bytes | 298,104 | **31,880** (−89%) |
| Fields in the largest shard | 4,102 | 1,041 → 118 after pruning |
| At 1 M users | ~9.5 GB | **~1.1 GB** |

### The one you must not "fix" with a TTL

`room:{s}:seq` has no TTL and should not get one. **Expiring a sequence counter
resets it to zero, so the next message reuses a `seq` that already exists** —
and Module 05's `UNIQUE (room_id, seq)` constraint then rejects it, or worse,
every connected client's gap detector concludes the room jumped backwards.

Some state must not expire. For that state you need a **reconciler**, not a TTL:

```python
def repair_room_sequence(room) -> int:
    """Redis lost the counter. Postgres is the source of truth."""
    high = Message.objects.filter(room=room).aggregate(Max("seq"))["seq__max"] or 0
    redis.set(f"room:{{{room.slug}}}:seq", high)      # not SETNX: we are repairing
    return high
```

That is 12 lines and it is the difference between "Redis restarted" and "this
room's history is corrupt". Wire it into Module 07's `LayerGuard`, which already
knows when Redis lost its state.

### Fragmentation

```bash
r FLUSHALL; r CONFIG SET activedefrag no
# varied sizes are the ingredient -- uniform sizes barely fragment
for i in $(seq 1 200); do
  r EVAL "for j=1,20000 do
            redis.call('SET','frag:'..ARGV[1]..':'..j, string.rep('x', (j % 17) * 137))
          end" 0 "$i" > /dev/null
done
r INFO memory | grep -E 'used_memory_human|rss_human|fragmentation_ratio'
```
**Expected:**
```
used_memory_human:3.11G
used_memory_rss_human:3.28G
mem_fragmentation_ratio:1.05
```

Now delete an **interleaved** 90%:

```bash
for i in $(seq 1 200); do
  r EVAL "for j=1,20000 do
            if j % 10 ~= 0 then redis.call('DEL','frag:'..ARGV[1]..':'..j) end
          end" 0 "$i" > /dev/null
done
r INFO memory | grep -E 'used_memory_human|rss_human|fragmentation_ratio'
```
**Expected:**
```
used_memory_human:318.42M
used_memory_rss_human:2.94G
mem_fragmentation_ratio:9.46
```

✅ **Redis reports 318 MB. The OS still has 2.94 GB.** With a 4 GB container
limit you are one spike from an OOM kill while `used_memory` insists everything
is fine.

### Why the OS cannot reclaim it

Memory returns to the OS in **pages** (4 KB), via `munmap` or `MADV_DONTNEED`,
and only when an *entire* page is free.

```
one 4 KB page after the interleaved delete:

 ┌────┬────┬────┬────┬────┬────┬────┬────┐
 │FREE│FREE│FREE│FREE│FREE│FREE│FREE│LIVE│   <- one live object
 └────┴────┴────┴────┴────┴────┴────┴────┘
                                      ↑
              this page CANNOT be returned to the OS
```

jemalloc also bins allocations into **size classes** with per-class arenas: a
freed 137-byte object can be reused by another 137-byte allocation and cannot
satisfy a 2 KB request. So a workload whose *size distribution shifts* fragments
even with no deletions at all — which is exactly what a chat system does as
message lengths and room sizes change over a day.

### The cost of fixing it

```bash
r CONFIG SET activedefrag yes
r CONFIG SET active-defrag-ignore-bytes 100mb
r CONFIG SET active-defrag-threshold-lower 10
r CONFIG SET active-defrag-cycle-min 5
r CONFIG SET active-defrag-cycle-max 25
```

With chat load running:
```
used_memory_rss_human:2.94G  ratio:9.46   redis_cpu:21%   chat p99:181ms
used_memory_rss_human:2.11G  ratio:6.80   redis_cpu:39%   chat p99:204ms
used_memory_rss_human:1.24G  ratio:3.99   redis_cpu:44%   chat p99:226ms
used_memory_rss_human:522.1M ratio:1.64   redis_cpu:43%   chat p99:221ms
used_memory_rss_human:381.2M ratio:1.20   redis_cpu:22%   chat p99:184ms
```

| | Baseline | Defragmenting |
|---|---------|---------------|
| Redis CPU | 21% | **44%** |
| Chat p99 | 181 ms | **226 ms** (+25%) |
| Chat p99.9 | 712 ms | 980 ms (+38%) |
| RSS | 2.94 GB | **381 MB** in ~50 s |

**Recommendation: `activedefrag yes` permanently, with a conservative
`active-defrag-cycle-max`.** Steady-state cost is near zero because it only runs
above the threshold, and the alternative is discovering a 9× RSS multiplier
during an incident. Note the mechanism, because it explains the CPU: active
defrag *copies live objects to new allocations and updates pointers* — real
work, on the single thread, in increments bounded by the cycle settings. Those
settings are your latency budget for it; `cycle-max 25` means "never spend more
than 25% of the thread on defrag".

### The check that runs itself

```python
# chat/tasks.py
from celery import shared_task
from prometheus_client import Gauge

KEY_BUDGET = Gauge("chat_key_budget_violations",
                   "Key patterns exceeding their documented growth bound",
                   ["pattern"])

BUDGETS = {                      # the same table as redis_doctor.py's
    "pulse:group:*":   ("zset", 50_000),
    "pulsespecific.*": ("zset", 3_000),
    "room:*:stream":   ("stream", 20_000),
    "unread:*":        ("hash", 500),
    "user:*:sessions": ("zset", 50),
}


@shared_task
def audit_key_budgets() -> None:
    for pattern, (ktype, limit) in BUDGETS.items():
        worst, worst_key = 0, ""
        # SCAN, never KEYS -- Part E is the reason, and this task runs in
        # production where Part E's demonstration would be an incident.
        for key in redis.scan_iter(match=pattern, count=500):
            size = SIZERS[ktype](key)
            if size > worst:
                worst, worst_key = size, key
        KEY_BUDGET.labels(pattern=pattern).set(max(0, worst - limit))
        if worst > limit:
            log.error("KEY BUDGET EXCEEDED: %s has %d (max %d)",
                      worst_key, worst, limit)
```
```yaml
- alert: RedisKeyBudgetExceeded
  expr: chat_key_budget_violations > 0
  for: 15m
  severity: ticket
  annotations:
    summary: "{{ $labels.pattern }} has outgrown its documented bound"
```

**A leak you detect in fifteen minutes is a bug. A leak you detect in three
months is an incident**, and 8.2 million stream entries in one room is what
three months looks like.

---

## Task 3 — The hash-tag CI gate

### Make keys unguessable to a linter by making them impossible to write inline

The robust design is not "parse the source for key literals" — it is "there is
exactly one place keys are built, and the test knows about it."

```python
# chat/keys.py -- the ONLY place a Redis key name is constructed.
"""Every key Pulse owns, and the slot family it belongs to.

The hash tag is the entity that multi-key operations group on. Get that wrong
and everything works until Module 18 puts Redis in Cluster.

Every builder takes the tag token as its FIRST positional argument and
everything else keyword-only, so the CI gate can call all of them uniformly.
"""
from functools import partial

# --- family: ROOM. Sequence + stream + PEL are one atomic unit. ------------
def room_seq(slug: str) -> str:      return f"room:{{{slug}}}:seq"
def room_stream(slug: str) -> str:   return f"room:{{{slug}}}:stream"
def room_cursor(slug: str) -> str:   return f"room:{{{slug}}}:cursor"

# --- family: USER. Rate buckets and presence are checked together. ---------
def presence(uid: str) -> str:       return f"presence:{{{uid}}}"
def rate_global(uid: str) -> str:    return f"rate:{{{uid}}}:all"
def rate_room(uid: str, *, slug: str) -> str: return f"rate:{{{uid}}}:room:{slug}"
def unread(uid: str, *, shard: int) -> str:  return f"unread:{{{uid}}}:{shard}"
def sessions(uid: str) -> str:       return f"user:{{{uid}}}:sessions"
def ws_ticket(uid: str, token: str) -> str: return f"wsticket:{{{uid}}}:{token}"
def ticket_set(uid: str) -> str:     return f"tkset:{{{uid}}}"

# A family is a list of zero-argument-after-the-token builders, so the gate can
# call every one of them with the same token and compare slots. Anything with
# extra arguments is bound here, at the one place that knows what they mean.
SLOT_FAMILIES = {
    "room": [room_seq, room_stream, room_cursor],
    "user": [presence, rate_global, sessions, ticket_set,
             partial(rate_room, slug="general"),
             partial(unread, shard=0), partial(unread, shard=3)],
}
```

```python
# chat/tests/test_hash_tags.py
import pytest
from chat import keys

TOKENS = ["7", "general", "42", "01JQ8Z4K7M8YQ2VBXR3N5TDGWH", "a-b_c.d"]


@pytest.mark.parametrize("family", sorted(keys.SLOT_FAMILIES))
@pytest.mark.parametrize("token", TOKENS)
def test_family_shares_one_slot(redis_client, family, token):
    """Every key in a family must hash to the same slot for EVERY token.

    CLUSTER KEYSLOT works on a standalone Redis -- which is the entire point:
    this gate runs today, five modules before there is a cluster.
    """
    built = [fn(token) for fn in keys.SLOT_FAMILIES[family]]
    slots = {redis_client.execute_command("CLUSTER", "KEYSLOT", k) for k in built}
    assert len(slots) == 1, f"{family}/{token} spans slots: " + \
        ", ".join(f"{k}->{redis_client.execute_command('CLUSTER','KEYSLOT',k)}"
                  for k in built)


def test_no_inline_key_literals():
    """Nothing outside chat/keys.py may build a Redis key.

    Crude, and it works: any string literal containing a colon and a brace, or
    matching a known prefix, must live in keys.py.
    """
    import pathlib, re
    pattern = re.compile(r"['\"](?:room|presence|rate|unread|user|wsticket|tkset):")
    offenders = []
    for path in pathlib.Path("chat").rglob("*.py"):
        if path.name == "keys.py" or "tests" in path.parts:
            continue
        for n, line in enumerate(path.read_text().splitlines(), 1):
            if pattern.search(line):
                offenders.append(f"{path}:{n}: {line.strip()}")
    assert not offenders, "build keys in chat/keys.py:\n" + "\n".join(offenders)
```

### Plant a realistic mistake

Module 21 will mint single-use WebSocket tickets. The natural way to write it:

```python
# the mistake -- and it is a genuinely reasonable-looking one
def ws_ticket(token: str) -> str:  return f"wsticket:{{{token}}}"   # tag = the ticket
def ticket_set(uid: str) -> str:   return f"tkset:{{{uid}}}"        # tag = the user
```
used together in one pipeline:
```python
async with r.pipeline(transaction=False) as pipe:
    pipe.setex(keys.ws_ticket(token), 30, uid)
    pipe.sadd(keys.ticket_set(uid), token)
    await pipe.execute()
```

**Expected from the gate:**
```
FAILED chat/tests/test_hash_tags.py::test_family_shares_one_slot[7-user]
E   AssertionError: user/7 spans slots:
E     presence:{7}->1716, rate:{7}:all->1716, unread:{7}:0->1716,
E     user:{7}:sessions->1716, wsticket:{01JQ8Z...}->5836, tkset:{7}->1716
```

**The fix is to tag by the entity the operation groups on** — the user — which
means putting the user *inside* the ticket so the handshake can still find it
from the ticket string alone:

```python
def mint(uid: str) -> str:
    return f"{uid}.{secrets.token_urlsafe(24)}"      # "4711.Xh2f…"

def ws_ticket(uid: str, token: str) -> str:
    return f"wsticket:{{{uid}}}:{token}"
```

✅ Gate green. **And note what just happened: a Cluster constraint changed the
format of a security token, five modules before there is a cluster.** That is
the kind of coupling you want to discover in a unit test, not in Module 18's
migration window.

### The gate's two blind spots

**Blind spot 1 — a slug or user id containing a brace.**

```bash
r CLUSTER KEYSLOT 'room:{a}b}:seq'
r CLUSTER KEYSLOT 'room:{a}:seq'
```
```
(integer) 15495
(integer) 15495          <-- the SAME slot as a different room
```

Redis hashes only between the *first* `{` and the *next* `}`. A room slugged
`a}b` collides in-slot with room `a`, and — worse — the key names themselves can
be made to collide. The gate cannot catch this because it tests tokens you chose.

**What catches it:** a slug validator, enforced at the model layer, not at the
key layer.
```python
slug = models.SlugField(validators=[RegexValidator(r"^[a-z0-9][a-z0-9._-]{0,63}$")])
```
Module 04's route regex `[\w.-]+` already excludes braces from the URL, but
`Room.objects.create(slug=...)` in a management command does not. Validate at
the model.

**Blind spot 2 — a multi-key operation across two *different* families.**

```python
await r.mget(*[keys.presence(u) for u in room_members])     # 500 different users
```
Every key is correctly tagged. They are correctly tagged **by different users**,
so they span up to 500 slots and `MGET` is a `CROSSSLOT`. The gate only checks
declared families and this call site declares nothing.

**What catches it:** running the test suite against a real cluster.
```bash
for p in 7000 7001 7002; do
  docker run -d --name rc$p -p $p:$p redis:7-alpine redis-server \
    --port $p --cluster-enabled yes --cluster-config-file n$p.conf
done
redis-cli --cluster create 127.0.0.1:7000 127.0.0.1:7001 127.0.0.1:7002 --cluster-yes
pytest chat/tests -q --redis-url redis://localhost:7000
```
Thirty seconds of CI setup, and it is what Module 18 does. **The static gate is
the cheap 80%; a three-node cluster in CI is the other 20%, and you want both.**

---

## Task 4 — Pipeline versus Lua on a real hot path

The path: **"who in this 500-member room is online?"**, which Module 11 needs on
every join and every presence refresh.

### Version A — the way it gets written

```python
async def online_in_room(r, member_ids):
    online = []
    for uid in member_ids:                       # 499 sequential round trips
        if await r.get(keys.presence(uid)):
            online.append(uid)
    return online
```

### Version B — pipeline

```python
async def online_in_room(r, member_ids):
    async with r.pipeline(transaction=False) as pipe:
        for uid in member_ids:
            pipe.get(keys.presence(uid))
        results = await pipe.execute()
    return [u for u, v in zip(member_ids, results) if v]
```

### Version C — Lua

```lua
-- KEYS[1..N] = presence keys.  Returns the indexes that are set.
local online = {}
for i = 1, #KEYS do
    if redis.call('GET', KEYS[i]) then online[#online + 1] = i end
end
return online
```

### Measured, room size 500, 100 lookups/second, at the Module 06 baseline

| | A: sequential | B: pipeline | C: Lua | D: `MGET` |
|---|--------------|-------------|--------|-----------|
| Redis round trips | **499** | **1** | **1** | **1** |
| p50 | 62 ms | **1.8 ms** | 1.6 ms | 1.1 ms |
| **p99** | **1,910 ms** | **13 ms** | 11 ms | 8 ms |
| Redis `usec_per_call` (`get`) | 1.3 µs | 1.3 µs | — | — |
| Redis CPU | 22% | 24% | **19%** | 17% |
| Longest single-thread block | 1.3 µs | 1.3 µs | **740 µs** | 610 µs |
| Cluster-safe? | ✅ | ✅ (the client splits by slot) | ❌ `CROSSSLOT` | ❌ `CROSSSLOT` |

✅ **147× improvement at p99, and Redis did identical work.** `usec_per_call` is
unchanged at 1.3 µs — every millisecond saved was a round trip, exactly as
Part B predicted.

### When Lua beats a pipeline, and when it loses

**Use Lua when:**
- You need **atomicity** — no other client may interleave. A pipeline gives you
  none: another client's `DEL` can land between your commands.
- You need **conditional logic on intermediate results** ("increment only if
  under the limit"). A pipeline cannot branch; branching would need a round trip,
  which defeats the purpose.
- You want to **reduce reply bandwidth** by computing a summary server-side —
  return one number instead of 500.

**Use a pipeline when:**
- The operations are **independent** and you only want throughput.
- The **reply set is large.** A pipeline streams replies back as they are
  produced; a Lua script builds the **entire** reply in Redis's memory before
  returning it. A script returning 500,000 elements allocates all of it at once,
  on the server, on the single thread.
- You want the work to be **interruptible.** A long pipeline yields between
  commands, so other clients interleave. A script does not — note version C's
  740 µs block, versus the pipeline's 1.3 µs. At 100 lookups/second that is
  7.4% of Redis's thread held in indivisible chunks.

### Why Lua loses *this* case — three reasons, and the third is fatal

1. **Atomicity buys nothing.** A presence snapshot is approximate by definition;
   Module 11's presence is TTL state that is already stale by the time you read
   it. There is no invariant to protect.
2. **The reply set is the thing Lua handles worst.** 500 results built in Redis's
   memory before any of them ships.
3. **`CROSSSLOT`.** The 500 keys are tagged by 500 *different users*, so in
   Cluster they span up to 500 slots and the script is rejected outright. **The
   pipeline is the only version that survives Module 18**, because a
   cluster-aware client splits it per node and runs the parts in parallel —
   measured at **+0.4 ms p50** versus a single-node pipeline, because it fans out
   to three nodes concurrently instead of doing one round trip.

**Verdict: pipeline.** And note that `MGET` — the fastest column in the table —
is disqualified for the same reason as Lua. **The fastest correct answer and the
fastest answer are different, and the difference only shows up five modules
later.**

**The counter-example, for balance:** Module 11's token-bucket rate limiter is
the exact opposite case. It is check-then-decrement (conditional on an
intermediate result), its keys all share a `{uid}` tag, and its reply is two
integers. **That one is Lua**, unambiguously, and the same three questions give
the opposite answer.

> ⚠️ **A slow Lua script blocks everything and cannot always be killed.**
> `SCRIPT KILL` refuses once a script has written; your only remaining option is
> `SHUTDOWN NOSAVE`. Keep scripts to tens of operations, never loops over
> unbounded input. [`code/append.lua`](../code/append.lua) does exactly two.

---

## Task 5 (stretch) — Client-side caching with RESP3 tracking

```python
import redis.asyncio as aioredis

# Broadcast mode with a prefix: Redis does NOT remember which keys each client
# read, so its bookkeeping is O(prefixes) instead of O(clients x keys). With 8
# workers x 2 connections that matters.
r = aioredis.Redis(host="localhost", protocol=3, decode_responses=True)
await r.execute_command("CLIENT", "TRACKING", "on", "BCAST", "PREFIX", "room:meta:")

local_cache: TTLCache = TTLCache(maxsize=50_000, ttl=30)      # see below


async def _invalidation_pump(pubsub) -> None:
    async for msg in pubsub.listen():
        if msg["type"] == "invalidate":
            for key in msg["data"] or ():
                local_cache.pop(key, None)
                INVALIDATIONS.inc()


async def room_meta(slug: str) -> dict:
    key = f"room:meta:{slug}"
    hit = local_cache.get(key)
    if hit is not None:
        return hit
    value = json.loads(await r.get(key) or "{}")
    local_cache[key] = value
    return value
```

**Measured — room metadata lookups, 20,000 connections, 100 rooms, 8 workers:**

| | Without tracking | With tracking |
|---|-----------------|---------------|
| Redis ops/s for room metadata | 41,200 | **310** |
| p50 lookup | 0.142 ms | **0.0004 ms** |
| Local heap | 0 | 11 MB **per worker** (88 MB per node) |
| Invalidation pushes/s | n/a | 310 |
| Redis CPU | 26% | **19%** |

✅ **133× fewer Redis operations**, because room metadata changes rarely and is
read constantly — the ideal client-side-caching profile. Note the per-worker
column: with a process-per-core model you pay the cache eight times per box,
which is a Python-specific cost the JVM twin does not have.

### The failure mode: a lost invalidation

Invalidation pushes travel over the same connection with **no acknowledgement**.
If the connection drops between Redis sending the invalidation and the client
processing it, **the client serves stale data forever.**

```
t=0   worker caches room.7 { name: "general", private: false }
t=1   an admin makes room.7 private
t=2   Redis sends the invalidate push
t=3   the connection drops in flight -- push lost
t=4   the client reconnects and re-enables tracking
t=5+  the worker still serves { private: false } ...indefinitely
```

For a room *name* that is cosmetic. For `private: true` it is an
**authorization bypass**.

### Bounding the staleness — three mechanisms, all required

**1. A TTL on every cached entry.** This is the correctness guarantee; the
invalidation is only an optimisation.
```python
local_cache = TTLCache(maxsize=50_000, ttl=30)
```
Worst case becomes 30 seconds instead of forever, at the cost of one refresh per
key per 30 s — still a ~99% reduction.

**2. Flush the whole cache on reconnect.** Any disconnect means an unknown number
of missed invalidations; the only safe assumption is that everything is stale.
```python
async def on_reconnect() -> None:
    local_cache.clear()
    await r.execute_command("CLIENT", "TRACKING", "on", "BCAST",
                            "PREFIX", "room:meta:")
```

**3. Never client-cache security-relevant data.**

```python
# CACHEABLE: name, topic, icon, created_at, member_count (approximate)
# NEVER:     is_private, membership, role, banned_until
```

### The field that must never be cached, and the bug it produces

**`Room.is_private` (and by extension membership).** Pulse authorizes a socket in
`connect()` by checking membership, and Module 21 requires **immediate
cluster-wide revocation** — "a missed *you were removed* is a security hole", in
the words of Module 07's own delivery-semantics table.

A 30-second-stale `is_private` means a user removed from a private room keeps
receiving its messages for up to 30 seconds across eight workers on every node,
with no log line and no way to know it happened. That is not a caching bug; it is
an **authorization bypass with a configurable duration**.

Permission checks stay on Redis with no local cache. The read volume is far
lower anyway — one check per connect, not one per message — so you are giving up
almost nothing.

> **The rule this illustrates, and it is bigger than Redis:** *any cache whose
> invalidation is best-effort must have a TTL, and the TTL — not the
> invalidation — is what actually bounds your staleness.* Invalidation makes the
> common case fast. The TTL is the only part that is a guarantee. If you cannot
> tolerate the TTL as your worst case, you cannot cache the value.
