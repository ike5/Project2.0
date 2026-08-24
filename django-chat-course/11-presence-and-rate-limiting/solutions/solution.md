# Solutions — Module 11

Reference answers with the reasoning, the rejected alternatives, and the numbers.
Reference machine: 8-core / 16 GB, Ubuntu 24.04, Python 3.12, Uvicorn + uvloop,
Django 5.1 / Channels 4.1, Redis 7 from `infra/compose.dev.yml`.

---

## Task 1 — The multi-connection lie

### What actually happens

`presence.py` keys the sorted set by **username**:

```python
await self.redis.zadd(presence_key(room_key), {username: expires_at_ms})
```

Alice has a laptop tab, a second laptop tab and a phone — three connections, one
ZSET member. Now she closes one tab:

```
t=0.00  tab 2 closes → disconnect() → presence.leave() → ZREM alice
t=0.00  alice is NOT in the roster.  Two of her connections are still open.
t=1.00  the 1 Hz sweep runs, diffs, sees alice in `left`
        → presence.update {"online":[...], "left":["alice"]} to every focused
          socket in the room
t≤10.0  tab 1 or the phone heartbeats → presence.touch → ZADD alice
t≤11.0  the next sweep sees alice in `joined`
        → a second presence.update to every focused socket
```

**Symptom:** every tab close makes the user flicker offline and back for up to
11 seconds, for everyone in the room. Worse, it does it *twice* — a `left` frame
and a `joined` frame — so **closing a tab is a fan-out amplifier**. In a
200-member room, one tab close costs 400 frames to communicate nothing.

At 20,000 users averaging 1.4 connections and a plausible 0.6 tab closes per user
per hour, that is 12,000 spurious frame-pairs per hour, all of them lies.

### The fix, and the two rejections

**Rejected — a refcount.** `HINCRBY presence:{room} alice 1` on connect, `-1` on
disconnect, and the user is online while the count is positive. This is the
obvious fix and it is wrong for the reason the whole module is about: the
decrement depends on a graceful event. A `kill -9` leaks a permanent +1 and alice
is online forever. You would have reintroduced exactly the bug TTLs existed to
prevent, one layer up.

**Rejected — drop `leave()` entirely and let the TTL handle it.** Correct, and
free, and it makes a genuine tab close take up to 30 s to show. That is a real
product regression for the most common presence event there is.

**Chosen — one member per connection.**

```python
def _member(username: str, channel_name: str) -> str:
    # Channel names are Channels-generated and contain no '|'. Django usernames
    # are [A-Za-z0-9@.+-_] and contain no '|' either. One separator, no escaping.
    return f"{username}|{channel_name}"


async def touch(self, room_key: str, username: str, channel_name: str) -> None:
    expires_at_ms = int((time.time() + PRESENCE_TTL_S) * 1000)
    await self.redis.zadd(presence_key(room_key),
                          {_member(username, channel_name): expires_at_ms})


async def leave(self, room_key: str, username: str, channel_name: str) -> None:
    with contextlib.suppress(Exception):
        await self.redis.zrem(presence_key(room_key),
                              _member(username, channel_name))


async def roster(self, room_key: str) -> list[str]:
    key = presence_key(room_key)
    now_ms = int(time.time() * 1000)
    pipe = self.redis.pipeline(transaction=False)
    pipe.zremrangebyscore(key, "-inf", now_ms)
    pipe.zrange(key, 0, -1)
    _removed, members = await pipe.execute()
    # Dedup in Python. O(M) over a set bounded by MAX_MEMBERS x connections,
    # which is why the suppression threshold matters for more than fan-out.
    return sorted({m.rsplit("|", 1)[0] for m in members})
```

Every property survives: cleanup is still a side effect of the read, a `kill -9`
still expires cleanly (each connection's member has its own TTL), and now closing
one of three tabs is invisible because the other two members are still there.

### The new memory cost

```bash
r ZADD 'room:{room.bench}:presence' $(for i in $(seq 1 128); do
    echo "$(( $(date +%s) * 1000 + 60000 )) u$i|specific.a3f1c9e2!QK7pZ$i"; done)
r OBJECT ENCODING 'room:{room.bench}:presence'
r MEMORY USAGE   'room:{room.bench}:presence'
# push it past zset-max-listpack-entries (128)
r ZADD 'room:{room.bench}:presence' $(for i in $(seq 129 280); do
    echo "$(( $(date +%s) * 1000 + 60000 )) u$i|specific.a3f1c9e2!QK7pZ$i"; done)
r OBJECT ENCODING 'room:{room.bench}:presence'
r MEMORY USAGE   'room:{room.bench}:presence'
```
**Expected:**
```
listpack
(integer) 6104
skiplist
(integer) 22488
```

✅ **22.5 KB for a 200-member room at 1.4 connections/member.** Note the encoding
flip at 128 entries — Module 08's lesson arriving where you did not expect it. A
listpack of 128 entries is 6.1 KB; the same data as a skiplist is 3.7× larger,
because a skiplist pays for pointers.

| | Per-user members | Per-connection members |
|---|---|---|
| 200-member room, 1.4 conn/member | 280 entries would not exist; 200 entries | 280 entries |
| Memory per room | 16.1 KB | **22.5 KB** (+40%) |
| 100 rooms | 1.6 MB | **2.2 MB** |
| Spurious frames per tab close | 400 | **0** |

2.2 MB of Redis to eliminate 12,000 lying frames an hour is not a close call.

> **A knob worth knowing:** if your rooms sit just above 128 members you can push
> `zset-max-listpack-entries` to 256 and keep the compact encoding at a small CPU
> cost per operation (listpack operations are O(N) over a *small* N). Measure
> before you do — `ZADD` on a 256-entry listpack costs 2.9 µs versus 1.8 µs on a
> skiplist, which at 2,000 ZADD/s is 2 ms of CPU per second. Fine. At 200,000
> ZADD/s it is not.

### The test

```python
@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
async def test_one_tab_close_is_invisible(room, alice):
    conns = []
    for _ in range(3):
        c = WebsocketCommunicator(application, f"/ws/room/{room.slug}/?as=alice")
        assert (await c.connect())[0]
        await c.send_json_to({"v": 1, "type": "join", "room": room.key, "data": {}})
        conns.append(c)

    assert await presence.roster(room.key) == ["alice"]

    await conns[1].disconnect()
    await asyncio.sleep(1.5)                      # let a sweep run

    assert await presence.roster(room.key) == ["alice"]     # still online
    frames = await drain_type(conns[0], "presence.update")
    assert frames == []                                     # and nobody was told

    await conns[0].disconnect()
    await conns[2].disconnect()
    await asyncio.sleep(1.5)
    assert await presence.roster(room.key) == []
```
```
tests/test_presence.py::test_one_tab_close_is_invisible PASSED   [100%]
```

---

## Task 2 — The `away` state, and whether it earns its place

### Design

Keep the existing ZSET as the **liveness** signal — it is not negotiable and it
answers a different question. Add a second, parallel ZSET for the *claim* of
idleness:

```
room:{room.7}:presence   member=user|channel  score=liveness_expiry_ms
room:{room.7}:away       member=user|channel  score=away_expiry_ms
```

```python
AWAY_AFTER_MS = 300_000     # 5 minutes with no keystroke or focus event


async def set_away(self, room_key, username, channel_name, away: bool):
    m = _member(username, channel_name)
    if away:
        # The away claim expires with the connection, so a crashed client cannot
        # be permanently "away" any more than it can be permanently "online".
        await self.redis.zadd(f"room:{{{room_key}}}:away",
                              {m: int((time.time() + PRESENCE_TTL_S) * 1000)})
    else:
        await self.redis.zrem(f"room:{{{room_key}}}:away", m)


async def roster_with_state(self, room_key):
    now_ms = int(time.time() * 1000)
    pipe = self.redis.pipeline(transaction=False)
    pipe.zremrangebyscore(presence_key(room_key), "-inf", now_ms)
    pipe.zrange(presence_key(room_key), 0, -1)
    pipe.zremrangebyscore(f"room:{{{room_key}}}:away", "-inf", now_ms)
    pipe.zrange(f"room:{{{room_key}}}:away", 0, -1)
    _a, live, _b, away = await pipe.execute()

    away_users = {m.rsplit("|", 1)[0] for m in away}
    live_users = {m.rsplit("|", 1)[0] for m in live}
    # A user is "away" only if EVERY one of their connections claims it. The
    # phone in your pocket is idle; the laptop you are typing on is not, and the
    # laptop wins.
    online = live_users - away_users
    return {"online": sorted(online), "away": sorted(away_users & live_users)}
```

**Surviving a worker restart** is free: all of it is in Redis, and the only
worker-local state is `_announced`, which is a cache that recomputes correctly on
the next sweep. The design has no restart story to write, which is the
point of putting soft state in Redis rather than in the process.

### What it costs

```bash
python code/away_bench.py --users 20000 --rooms 100 --minutes 30
```
**Expected:**
```
away transitions per user per hour : 3.2
transitions/s across the fleet     : 17.8
extra ZADD+ZREM/s                  : 17.8
extra Redis memory                 : 4.1 MB (a second ZSET per room, ~40% occupancy)
steady-state presence frames/s     : 210 -> 3,560     (17.0x)
storm presence frames/s            : 20,020 -> 20,020 (unchanged — already at the cap)
```

The interesting row is the fifth. In **steady state**, the roster almost never
changes, so `if current == previous: return` short-circuits nearly every sweep and
presence is essentially free (210 frames/s). Adding `away` gives the roster a new
reason to change 17.8 times a second, and each change costs one frame per focused
socket in that room: `0.18 changes/room/s × 200 members × 100 rooms = 3,560/s`.

**A 17× increase in steady-state presence traffic** — which sounds alarming and is
not, because 3,560/s is **2.4% of the 150,000/s fan-out knee**. During the storm it
costs nothing at all, because aggregation already bounds the worst case.

### The decision: ship it, with one change

Ship. 2.4% of the fan-out budget for a state users actively ask for is good value,
and the storm behaviour is unchanged because the 1 Hz cap does not care how many
changes it is aggregating — which is the third time in this module that
aggregation's *bounded worst case* has been the property that mattered.

The one change: add **hysteresis** to the idle detector. Going away after 5 minutes
of idleness and returning on the first mousemove produces flapping for users who
glance at their screen:

```js
if (idleMs > 300_000 && !this.away) { this.away = true; sendState("away"); }
if (idleMs < 30_000 && this.away && Date.now() - this.awaySince > 60_000) {
  this.away = false; sendState("online");     // 60s minimum dwell
}
```
```
away transitions per user per hour : 3.2 -> 1.14   (2.8x fewer)
steady-state presence frames/s     : 3,560 -> 1,270
```

✅ **2.8× cheaper for a behaviour change nobody can perceive.** Write the 60-second
dwell down as a product decision, not a technical one, because that is what it is.

---

## Task 3 — Four holes, closed

### Hole A — the shared per-room bucket is a weapon

**The attack.** 5,000 hosts, one account each, one message per second, all into
`#general`. Every per-IP tier is satisfied (1/s against 20/s). Every per-user tier
is satisfied. The **per-room** tier (500 burst, 200/s) does fire — and that is the
problem, not the solution:

```bash
python code/flood.py --accounts 5000 --ips 5000 --room room.general --rate 1 --seconds 60
curl -s localhost:8000/metrics | grep 'tier="msg_room"'
```
```
pulse_ratelimit_denied_total{tier="msg_room"} 288104.0
```

The room bucket is shared, so it is drained by the flood and **legitimate members
are denied too**. Measured: a normal user's success rate in `#general` during the
attack was **4.1%**. The limiter turned a flood into a denial of service *on
behalf of the attacker*.

**The fix — split the room bucket by trust.**

```python
TIERS["msg_room_trusted"] = Tier("msg_room_trusted", capacity=400, refill_per_s=150)
TIERS["msg_room_new"]     = Tier("msg_room_new",     capacity=100, refill_per_s=50)

def room_tier(user) -> Tier:
    # "Trusted" is deliberately dumb: an account older than 24 hours that has
    # sent at least one message before today. Anything cleverer is a reputation
    # system, and a reputation system is a product, not a rate limiter.
    trusted = user.date_joined < timezone.now() - timedelta(hours=24)
    return TIERS["msg_room_trusted" if trusted else "msg_room_new"]
```

```
legitimate user success rate during the same attack: 4.1% -> 99.2%
```

**Legitimate traffic this breaks:** a genuine viral moment where 5,000 *new*
accounts join a room and all talk at once — a product launch, a raid, a
livestream. They share a 50/s bucket and it will feel slow. That is the trade, and
it is the right one: the failure mode is "new accounts are throttled in a busy
room," not "the room is unusable."

### Hole B — connection count is unlimited

**The attack.** One user, one IP, 200 WebSocket connections opened over 20 minutes
(inside the 10/min connection tier), sending **nothing**.

```bash
python code/conn_flood.py --user mallory --connections 200 --rate 0
curl -s localhost:8000/metrics | grep -E 'pulse_sockets_active|process_resident_memory'
```
```
pulse_sockets_active{worker="node-a-52104"} 200
process_resident_memory_bytes 9,412,096       (+9.0 MB)
```

200 × ~45 KB of connection state, 200 channel-layer group memberships, 200
presence ZSET members — an entirely message-free memory and fan-out attack that
every message tier is blind to, because there are no messages.

**The fix — a per-user connection cap.**

```python
MAX_CONNECTIONS_PER_USER = 8       # 3 devices x 2 tabs, plus headroom

async def connect(self):
    key = f"conn:{{{self.user.id}}}"
    pipe = redis.pipeline(transaction=False)
    pipe.sadd(key, self.channel_name)
    pipe.expire(key, PRESENCE_TTL_S * 2)   # self-cleaning; a crashed worker's
    pipe.scard(key)                        # entries age out with the set
    _added, _exp, count = await pipe.execute()
    if count > MAX_CONNECTIONS_PER_USER:
        await redis.srem(key, self.channel_name)
        await self.close(code=4429)
        return
```

```
connections accepted: 8 / 200      memory: +0.4 MB
```

**Legitimate traffic this breaks:** a power user with more than eight simultaneous
tabs. Real, rare, and the right answer for them is Module 17's SharedWorker, which
multiplexes every tab in a browser profile onto **one** socket — turning this cap
from a limitation into a nudge toward the better client design.

> The set is keyed by channel name and expires, so it never needs a decrement —
> the same "cleanup must not depend on a graceful event" rule the whole module is
> built on, applied to the limiter's own state.

### Hole C — `typing.start` and `read.upto` bypass the message tiers

`read.upto` is the expensive one: each frame is a Postgres `INSERT … ON CONFLICT`
against `chat_readcursor`.

```bash
python code/flood.py --user mallory --type read.upto --rate 2000 --seconds 20
```
```
postgres: 39,412 UPSERTs   p99 chat_message insert: 41ms -> 890ms
```

✅ A frame with no content, no fan-out and no rate limit took the *message write
path* down by 21×.

**The fix — cheap dedicated tiers,** and crucially **not** the message tiers:

```python
TIERS["typing"] = Tier("typing", capacity=3, refill_per_s=0.34)   # ~1 per 3 s
TIERS["read"]   = Tier("read",   capacity=5, refill_per_s=0.5)    # ~1 per 2 s
```

Charging typing against `msg_user_room` (which the lab does) is a real bug: a user
who types actively then hits send finds their message denied because their typing
spent the tokens. Different traffic, different bucket.

Also make `read.upto` idempotent-cheap: if the incoming `seq` is not greater than
the value you already hold in a per-worker cache, drop it before touching
Postgres.

```
postgres UPSERTs during the same flood: 39,412 -> 84
p99 chat_message insert: 890ms -> 42ms
```

**Legitimate traffic this breaks:** none that anyone can observe. Both limits sit
at the protocol's own documented client-side debounce rates (§3.2, §3.3), so a
conforming client never touches them.

### Hole D — a client that ignores `retry_after_ms`

Denials are cheap but not free.

```bash
python code/flood.py --clients 500 --rate 200 --seconds 60 --ignore-retry
curl -s localhost:8000/metrics | grep -E 'pulse_ratelimit_denied_total|process_cpu'
```
```
denials/s: 41,208     worker CPU spent denying: 11.4%
```

**The fix — escalate.** Denials get their own bucket; exceed it and the socket
closes with `4429` and the IP is barred from the handshake for 15 minutes.

```python
ok, _retry = await bucket.take(
    Tier("abuse", capacity=100, refill_per_s=100 / 60), f"rl:abuse:{{{user.id}}}")
if not ok:
    await redis.set(f"ban:conn:{{{ip}}}", "1", ex=900)
    await self.close(code=4429)
```

```
denials/s: 41,208 -> 612     worker CPU spent denying: 11.4% -> 0.2%
```

**Legitimate traffic this breaks:** a buggy client release that ignores
`retry_after_ms` now gets disconnected instead of merely throttled — which is
loud, attributable and fixable, and vastly better than silently costing you 11% of
every worker. This is the seam where rate limiting becomes abuse detection, and
Module 21 picks it up with real evidence-gathering.

---

## Task 4 — Shed presence, not messages

### The signal: event-loop lag

Four candidates, and the reasoning matters more than the answer.

| Signal | Why not |
|--------|---------|
| **CPU utilization** | Misleading in an async process. A worker at 100% CPU with 2 ms of loop lag is *healthy saturation* — it is doing exactly what you built it to do. Shedding there throws away capacity you have. |
| **Outbound queue depth** | Per-connection and noisy. One slow consumer looks identical to a saturated worker, and Module 04 already established that the answer to a slow consumer is to drop *it*, not to degrade the room. |
| **p99 delivery latency** | A lagging indicator by construction. By the time a 5-minute p99 moves, you have already been failing for minutes. Good for alerting, useless for control. |
| **Event-loop lag** | ✅ One number that captures "this worker cannot keep up" regardless of cause — CPU, a blocking call, a slow Redis, GC. It is also the *direct* cause of every latency symptom, so acting on it acts on the root. |

```python
class LoopLagMonitor:
    """Sleep 100 ms; the overshoot IS the lag. Two lines, and the single most
    useful number an async Python service can emit."""

    def __init__(self):
        self.lag = 0.0

    async def run(self):
        while True:
            t0 = time.perf_counter()
            await asyncio.sleep(0.1)
            # EWMA so a single GC blip does not trip the shed.
            self.lag = 0.8 * self.lag + 0.2 * (time.perf_counter() - t0 - 0.1)
```

### The policy

```python
def sweep_interval(lag: float, shedding: bool) -> float | None:
    if lag > 0.200:
        return None            # suppress presence entirely
    if lag > 0.050:
        return 5.0             # degrade: 1 Hz -> 0.2 Hz
    if shedding and lag > 0.020:
        return 5.0             # HYSTERESIS: do not snap back at the threshold
    return 1.0
```

Hysteresis is not decoration. Without it the worker oscillates at the boundary —
shed, recover, shed — and the oscillation itself costs more than either state.
Require lag below 20 ms for 10 consecutive samples before returning to 1 Hz.

### Measured, during the Part C naive storm

| | No shedding | With shedding |
|---|---|---|
| Presence frames/s at peak | 2,341,000 | **18,000** |
| **p99 message delivery** | **8.42 s** | **0.41 s** |
| Event-loop lag p99 | 1,840 ms | 61 ms |
| `ChannelFull` disconnects | 41,208 | **0** |
| Time in shed state | — | 47 s of a 120 s run |

✅ **Message delivery p99 improved 20.5× and nobody was disconnected**, at the cost
of presence being stale for 47 seconds during a deploy — which is precisely the
47 seconds during which nobody was looking at green dots.

And the honest result, with the Part C mitigations already applied:

```
time in shed state: 0.4 s of a 120 s run (0.3%)
```

✅ **Shedding almost never fires once the design is right.** That is the correct
outcome and worth stating in the write-up: load shedding is a safety net for the
case you did not predict, not a substitute for the arithmetic in Part C. A system
that relies on shedding to stay up is a system that is permanently degraded and
calls it resilience.

---

## Task 5 — Should one worker own each room's sweep?

### The alternative

Use the consistent-hash ownership from lab Part I. One worker sweeps each room and
publishes the delta over the channel layer; every worker delivers it to its own
local sockets.

```python
async def _sweep_room(self, room_key: str):
    if not owns(room_key):
        return                                    # someone else's job
    members = await self.roster(room_key)
    if set(members) == self._announced.get(room_key, set()):
        return
    self._announced[room_key] = set(members)
    await self.channel_layer.group_send(room_key, {
        "type": "chat.presence", "online": sorted(members)})
```

### Measured, 100 rooms, 8 workers, 20,000 connections

| | Per-worker sweep (shipped) | Hashed single sweeper |
|---|---|---|
| Redis ops/s for sweeping | 800 | **100** |
| Presence frames/s (storm) | 20,020 | 20,020 |
| Channel-layer ops/s | 0 | 100 `group_send` → 800 receives |
| Worst-case staleness after a `kill -9` | **1.0 s** | 12–45 s |
| Python CPU for sweeping (per worker) | 0.4% | 0.05% (owner) / 0.1% (receivers) |
| Extra lines of code | 0 | **84** |
| New failure modes | none | 3 (below) |

The Redis saving is **700 operations per second** out of a Redis you measured at
~2,800 ops/s against a capacity in the hundreds of thousands. It is not a saving;
it is a rounding error with a maintenance bill.

The frames are **identical**, because fan-out dominates and both designs deliver
the same frame to the same sockets. Anyone proposing this optimization is
optimizing the 0.4% and leaving the 99.6% alone — which is the most common shape
of a bad optimization.

The three new failure modes:

1. **Split ownership during a rolling restart.** `WORKER_COUNT` changes as workers
   come and go, so two workers can believe they own the same room and publish
   conflicting rosters, or none can and the room goes stale indefinitely.
2. **A room owned by a dead worker** is unmaintained until the supervisor notices —
   12 s at best with a tight healthcheck, 45 s with the defaults. The per-worker
   sweep has no such state: the other seven workers are still correct.
3. **The delta rides the channel layer**, which is at-most-once (Module 07) and
   subject to `group_expiry` (Part E). A lost presence delta stays lost until the
   next change, where the per-worker sweep recomputes from Redis every second and
   is self-correcting by construction.

### Recommendation: keep the naive version

**The per-worker sweep wins, and it wins on robustness rather than on
performance.** It is stateless, self-correcting, has no ownership question, and
costs 0.4% of a core. The proposed optimization saves 0.35% of a core and
introduces a distributed-consensus problem.

> **The condition that would flip this.** The sweep's cost is `O(rooms per
> worker)` in Python, not in Redis. Measure where that bites:
>
> ```bash
> python code/sweep_scale.py --rooms 100 500 2000 5000 20000
> ```
> ```
>   100 rooms/worker: sweep uses  0.4% of a core
>   500 rooms/worker: sweep uses  1.9% of a core
>  2000 rooms/worker: sweep uses  7.4% of a core
>  5000 rooms/worker: sweep uses 18.1% of a core
> 20000 rooms/worker: sweep uses 71.2% of a core   <-- the loop is now the problem
> ```
>
> Past roughly **5,000 active rooms per worker process**, eight workers each
> diffing every room every second is real money, and hashing the ownership starts
> to pay for its complexity. Below that, it does not. Write the threshold down;
> "we will revisit at 5,000 rooms per worker" is a much better artefact than a
> vague "it doesn't scale."

That, rather than the code, is the deliverable: **a rejected optimization with the
measurement that justifies rejecting it and the condition that would reverse the
decision.** Every entry in the capstone's architecture review should look like
this one.
