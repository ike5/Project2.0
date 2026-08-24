# Lab 11 — Presence That Heals Itself, Limits That Actually Hold

**You'll:** build TTL presence on a sorted set and prove a `kill -9` cannot leave a
ghost, measure exactly how late and how lossy keyspace notifications are, induce a
2.3-million-frame-per-second presence storm and cut it by 117×, catch
`group_expiry` silently making a live socket deaf, watch three reconnect-backoff
policies produce wildly different herds, and write a token bucket in Lua that
allows exactly the limit where the non-atomic version overshoots by 41%.

⏱️ ~110 min. Work in `apps/pulse`.

```bash
docker compose -p pulse-dev -f ../../infra/compose.dev.yml up -d
alias r='docker exec -i pulse-redis redis-cli'
```

---

## Part A — Presence that cannot leave a ghost

Copy [`code/presence.py`](./code/presence.py) to `chat/presence.py` and wire it
into the consumer:

```python
# chat/consumers.py
from .presence import PresenceTracker, HEARTBEAT_S
from .streams import fanout

presence = PresenceTracker(fanout.redis)     # shares the worker's connection pool


class ChatConsumer(AsyncJsonWebsocketConsumer):

    async def _join(self, room_key: str):
        self.rooms.add(room_key)
        first = registry.add(room_key, self)
        if first:
            await manager.ensure_consuming(room_key)
        await presence.touch(room_key, self.user.username)
        presence.start()                      # idempotent; one sweep task/worker

    async def _leave(self, room_key: str):
        self.rooms.discard(room_key)
        await presence.leave(room_key, self.user.username)   # best-effort only
        if registry.remove(room_key, self):
            await manager.stop_consuming(room_key)
            presence.forget(room_key)

    async def _on_ping(self, content):
        for room_key in self.rooms:
            await presence.touch(room_key, self.user.username)
        await self.send_json({"v": 1, "type": "pong", "room": self.room.key,
                              "ts": now_ms(),
                              "data": {"ts": content["data"]["ts"],
                                       "server_ts": now_ms()}})
```

Connect two clients to `room.general` and look at the key:

```bash
r ZRANGE 'room:{room.general}:presence' 0 -1 WITHSCORES
r TYPE   'room:{room.general}:presence'
```
**Expected — usernames scored by their expiry timestamp in ms:**
```
1) "alice"
2) "1735689630123"
3) "bob"
4) "1735689630451"
(integer) 2
zset
```

✅ The expiry lives *inside* the collection you have to read anyway. That is the
property to look for when choosing a Redis structure: **does the read do the
maintenance for free?**

```bash
r ZREMRANGEBYSCORE 'room:{room.general}:presence' -inf $(( $(date +%s) * 1000 ))
r ZRANGE 'room:{room.general}:presence' 0 -1
```
**Expected — nothing expired yet, both still there:**
```
(integer) 0
1) "alice"
2) "bob"
```

### The graceful-disconnect test (the easy one)

Close alice's browser tab, then:

```bash
r ZRANGE 'room:{room.general}:presence' 0 -1
```
**Expected:**
```
1) "bob"
```
Gone in ~50 ms, because `disconnect()` ran and `presence.leave()` did a `ZREM`.

### The ungraceful test (the one that matters)

Now prove the design does not *depend* on that. Reconnect alice, then kill the
worker process holding her socket:

```bash
r ZRANGE 'room:{room.general}:presence' 0 -1
kill -9 $(pgrep -f 'PULSE_NODE_ID=node-a')
r ZRANGE 'room:{room.general}:presence' 0 -1
sleep 31
r ZREMRANGEBYSCORE 'room:{room.general}:presence' -inf $(( $(date +%s) * 1000 ))
r ZRANGE 'room:{room.general}:presence' 0 -1
```
**Expected:**
```
1) "alice"
2) "bob"
1) "alice"        <-- still there immediately after the kill; disconnect() never ran
2) "bob"
(integer) 1       <-- one member expired
1) "bob"
```

✅ **`disconnect()` never ran and alice went offline anyway, in 30 seconds, with
no cleanup code.** Try the same drill against a `SET`/`DEL` design and alice stays
green until someone restarts Redis.

Now do the same to the *client* instead of the server — the realistic case:

```bash
# alice's laptop lid closes: no close frame, just silence
sudo iptables -I OUTPUT -p tcp --dport 8000 -m owner --uid-owner "$(id -u)" -j DROP
sleep 35
curl -s localhost:8000/api/rooms/room.general/presence | jq
```
**Expected:**
```json
{"room": "room.general", "online": ["bob"]}
```

✅ **30 seconds, not the 15 minutes TCP would have taken to notice.** That gap —
between "the socket is still open as far as the kernel is concerned" and "this
user is not there" — is the entire reason presence is heartbeat-driven and not
socket-driven.

> **Why TTL = 3× heartbeat?** Tighten it to 2× and one lost frame or one client-side
> GC pause flaps a user offline and back, which users read as the product being
> broken. Loosen it to 6× and a crashed node's users stay green for a minute. Three
> missed beats is a strong signal and 30 s is under the threshold where anyone
> complains.

---

## Part B — Why not keyspace notifications, measured

The design everyone reaches for first. Turn it on and measure both of its
problems.

```bash
r CONFIG SET notify-keyspace-events Ex
```

`code/expiry_latency.py`:

```python
"""How long after a TTL elapses does the expiry event actually arrive?"""
import asyncio, os, statistics, time
import redis.asyncio as aioredis

N = 2000
TTL = 2.0


async def main():
    r = aioredis.from_url(os.environ.get("REDIS_URL", "redis://localhost:6379"),
                          decode_responses=True)
    sub = r.pubsub()
    await sub.subscribe("__keyevent@0__:expired")

    deadlines = {}
    for i in range(N):
        k = f"probe:{i}"
        deadlines[k] = time.time() + TTL
        await r.set(k, "1", ex=int(TTL))

    # 20,000 unrelated keys, so Redis' active-expiry cycle has to sample among
    # them — which is the realistic case, not an empty database.
    pipe = r.pipeline(transaction=False)
    for i in range(20000):
        pipe.set(f"noise:{i}", "1", ex=3600)
    await pipe.execute()

    lags = []
    deadline = time.time() + 90
    while len(lags) < N and time.time() < deadline:
        msg = await sub.get_message(ignore_subscribe_messages=True, timeout=1.0)
        if msg and msg["data"] in deadlines:
            lags.append(time.time() - deadlines.pop(msg["data"]))

    lags.sort()
    print(f"events received : {len(lags)} / {N}")
    print(f"lag p50         : {statistics.median(lags):.2f}s")
    print(f"lag p99         : {lags[int(len(lags) * 0.99)]:.2f}s")
    print(f"lag max         : {lags[-1]:.2f}s")
    await r.aclose()


asyncio.run(main())
```

```bash
python code/expiry_latency.py
```
**Expected:**
```
events received : 2000 / 2000
lag p50         : 0.42s
lag p99         : 21.8s
lag max         : 44.1s
```

✅ **p99 of 21.8 seconds.** Redis expires keys two ways: *lazily*, when something
touches the key, and *actively*, via a background cycle that samples 20 random
keys with a TTL every 100 ms and only keeps going while more than 25% of the
sample was expired. A key nobody touches waits for the sampler to happen upon it.
Your green dot is 22 seconds stale at p99, which is worse than the 30-second TTL
you were trying to improve on.

### And it loses events

```bash
python code/expiry_latency.py &
sleep 1
docker pause pulse-redis && sleep 1.5 && docker unpause pulse-redis
wait
```
**Expected:**
```
events received : 1691 / 2000
```

✅ **309 of 2,000 lost — 15.5%,** which is Module 07's Pub/Sub loss figure
reproduced exactly, because it *is* Pub/Sub. Every one of those is a user who
stays green forever with nothing in the system to correct it.

### And the roster query is a landmine

Suppose you stored one key per user instead. Finding who is in a room means
`SCAN` or `KEYS`:

```bash
r EVAL "for i=1,20000 do redis.call('SET', 'presence:u'..i, '1', 'EX', 3600) end return 1" 0
r CONFIG RESETSTAT
r --latency-history -i 2 &
LAT=$!
r KEYS 'presence:*' > /dev/null
sleep 3; kill $LAT
r SLOWLOG GET 1
```
**Expected:**
```
min: 0, max: 41, avg: 3.71 (198 samples)
1) 1) (integer) 1
   2) (integer) 1735689600
   3) (integer) 41208
   4) 1) "KEYS"
      2) "presence:*"
```

✅ **41 ms on the single thread** — Module 08's lesson with a presence payload.
Every message in every room in the entire system waited 41 ms for a green dot.

**The ZSET avoids all three problems at once:** the roster is `O(log N + M)` on a
key you already know the name of, the cleanup is a side effect of that read, and
there is no event to lose because there is no event.

```bash
r CONFIG SET notify-keyspace-events ""
r FLUSHDB
```

---

## Part C — Induce the presence storm, then cut it 117×

Set up the pinned Module 06 baseline: 20,000 connections, 100 rooms, 200 members,
each user in 20 rooms.

First, the naive broadcast — every presence change goes to every member of every
room the user is in:

```bash
export PULSE_PRESENCE_MODE=broadcast
export PULSE_ROOMS_PER_USER=20
locust -f code/locust_storm.py --headless -u 20000 -r 20000 --run-time 2m \
       --host http://localhost:8000
```

Watch the server's own counter, not Locust's numbers (coordinated omission — see
the header of `locust_storm.py`):

```bash
watch -n1 "curl -s localhost:8000/metrics | grep -E 'pulse_presence_frames_total'"
```
**Expected, at the peak of the reconnect:**
```
rate(pulse_presence_frames_total) = 2,341,000 /s
```

and the damage:
```
pulse_message_delivery_seconds p99  : 8.42
pulse_channel_full_total            : 41,208
uvicorn worker CPU                  : 8 x 100%
```

✅ **2.34 million presence frames per second** against a pinned fan-out knee of
**150,000/s** — 15.6× over. Chat did not degrade; chat *stopped*, and 41,208
sockets were dropped for slow-consumer backpressure (Module 04's `ChannelFull`
rule doing its job on the wrong traffic).

Now apply the three mitigations one at a time and re-measure.

**Mitigation 1 — aggregate and debounce to 1 Hz per room.** This is
`SWEEP_INTERVAL_S = 1.0` plus the `if current == previous: return` early-out in
`presence.py`:

```bash
export PULSE_PRESENCE_MODE=sweep
# re-run the same locust command
```
```
rate(pulse_presence_frames_total) = 400,100 /s
```
✅ **5.9×.** The structural win is not the ratio — it is that outbound traffic now
depends on **time**, not on the number of changes. Twenty joins or twenty thousand,
it is one frame per room per second. A hard bound on the worst case is worth more
than a big improvement in the average case, because the worst case is when you get
paged.

**Mitigation 2 — only the room the user is looking at.** A client watching a
20-room sidebar does not need live presence for all 20; it needs it for the one
that is open.

```python
# chat/consumers.py
async def _on_focus(self, content):
    """presence.watch — additive optional type; protocol §1 makes this compatible."""
    self.focused = content["data"]["room"]
```
```python
# presence.py, in _sweep_room
for sub in registry.subscribers(room_key):
    if getattr(sub, "focused", None) not in (None, room_key):
        continue                       # not looking at this room
    await sub.send_json(envelope)
```

```bash
export PULSE_PRESENCE_FOCUS=1
# re-run
```
```
rate(pulse_presence_frames_total) = 20,020 /s
```
✅ **20× more.**

**Mitigation 3 — suppress above 500 members.** No change to the numbers in this
run (the rooms are 200 members), but set it and prove it:

```bash
r ZADD 'room:{room.big}:presence' $(for i in $(seq 1 600); do echo "$(( $(date +%s) * 1000 + 60000 )) u$i"; done)
curl -s localhost:8000/api/rooms/room.big/presence | jq '.online | length'
curl -s localhost:8000/metrics | grep 'pulse_presence_frames_total'
```
**Expected — the roster endpoint still answers, the push does not fire:**
```
600
pulse_presence_frames_total 20020.0     <-- unchanged
```

The final scoreboard:

| Configuration | Presence frames/s | vs knee (150k/s) |
|---------------|-------------------|------------------|
| Naive broadcast | 2,341,000 | **15.6× over** |
| + 1 Hz aggregation | 400,100 | 2.7× over |
| + focused room only | **20,020** | 0.13× — comfortable |
| + suppress > 500 members | 20,020 | bounds the tail |

✅ **117× total, and presence stops being the largest traffic source in the
system.** Record it:

```markdown
## Module 11 — Presence

- 20,000 conns / 100 rooms / 200 members / 20 rooms per user, mass reconnect
  - naive broadcast : 2,341,000 frames/s (15.6x the 150k/s knee) -> chat stops
  - 1 Hz aggregate  :   400,100 frames/s
  - focused room    :    20,020 frames/s   (117x total)
- Redis cost of the sweep: 8 workers x 100 rooms x 1 Hz = 800 ZRANGEBYSCORE/s
- Heartbeat cost: 20,000 conns / 10 s = 2,000 ZADD/s
```

And confirm the Redis cost is trivial:

```bash
r INFO commandstats | grep -E 'zadd|zrange|zremrange'
```
**Expected:**
```
cmdstat_zadd:calls=241102,usec_per_call=1.81
cmdstat_zrange:calls=96402,usec_per_call=8.94
cmdstat_zremrangebyscore:calls=96402,usec_per_call=2.11
```

✅ **~2,800 ops/s total against a Redis that does six figures.** Presence was never
expensive in Redis. It was expensive in *fan-out*, which is where every scaling
problem in this course lives.

---

## Part D — Typing, aggregated

Typing rides the **channel layer**, not Streams (Module 09's routing rule): it is
at-most-once, superseded within three seconds, and durable storage for it would be
pure waste.

```python
# chat/typing.py
TYPING_TTL_MS = 3000
TYPING_TICK_S = 1.0


async def on_typing_start(self, content):
    # Client-side debounce is 3 s (protocol §3.2); enforce it server-side too,
    # because "the client will behave" is not a security model.
    ok, retry, tier = await limiter.allow_message(
        self.user.id, self.room.key, self.scope["client"][0])
    if not ok:
        return                                    # silently drop; it is typing
    await redis.zadd(f"room:{{{self.room.key}}}:typing",
                     {self.user.username: now_ms() + TYPING_TTL_MS})


async def typing_tick(room_key):
    """One frame per room per second, listing everyone. Not one frame per typer."""
    key = f"room:{{{room_key}}}:typing"
    pipe = redis.pipeline(transaction=False)
    pipe.zremrangebyscore(key, "-inf", now_ms())
    pipe.zrange(key, 0, -1)
    _removed, users = await pipe.execute()
    if users == last_sent.get(room_key):
        return
    last_sent[room_key] = users
    await channel_layer.group_send(room_key, {
        "type": "chat.typing", "users": sorted(users)})
```

Measure it. 20 typers in a 200-member room for 60 seconds:

```bash
python code/typing_bench.py --typers 20 --members 200 --seconds 60 --mode raw
python code/typing_bench.py --typers 20 --members 200 --seconds 60 --mode debounced
python code/typing_bench.py --typers 20 --members 200 --seconds 60 --mode aggregated
```
**Expected:**
```
raw        (every keystroke broadcast individually) : 1,204,800 frames
debounced  (3s per typer, broadcast individually)   :    80,000 frames
aggregated (3s debounce + 1 Hz per room)            :    12,340 frames
```

✅ **97.6× fewer frames** and the indicator is visually identical, because a
typing dot that updates at 1 Hz looks exactly like one that updates at 60 Hz.

---

## Part E — `group_expiry` makes a live socket go deaf

The Django footgun of the module. Reproduce it at a survivable timescale.

```python
# settings.py — TEMPORARY, to reproduce in 30 seconds instead of 24 hours
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {"hosts": [os.environ["REDIS_URL"]], "group_expiry": 20},
    }
}
```

Restart the worker, connect a client to `room.general`, and **do not send
anything from it.** Then:

```bash
r ZRANGE 'asgi:group:room.general' 0 -1 WITHSCORES
r TTL   'asgi:group:room.general'
```
**Expected:**
```
1) "specific.a3f1c9e2!QK7pZm"
2) "1735689600.123"
(integer) 20
```

Send a typing frame from another client immediately — the first client sees it.
Now wait 25 seconds and send another:

```bash
sleep 25
r TTL 'asgi:group:room.general'
python manage.py sendtyping room.general bob
```
**Expected:**
```
(integer) -2
```
and **nothing arrives at the first client**, which is still connected, still
heartbeating at the TCP level, and still perfectly happy.

```bash
r EXISTS 'asgi:group:room.general'
```
```
(integer) 0
```

✅ **The socket is open and the group membership is gone.** Note what this looks
like from the outside:

- Messages still work — Module 09 moved those to Streams and the `LocalRegistry`.
- **Typing, presence and read receipts stop**, because those still ride
  `group_send`.
- It resolves on refresh.

Nobody files that ticket. Which is exactly why you have to find it here.

### The fix, both halves

```python
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [os.environ["REDIS_URL"]],
            # Must exceed the longest socket lifetime you permit. Module 18's
            # drain policy bounds ours at ~6 hours, so 12 h is 2x headroom.
            "group_expiry": 43_200,
            "expiry": 60,     # message TTL; leave it alone (see below)
        },
    }
}
```

```python
# chat/consumers.py — re-add on every heartbeat
async def _on_ping(self, content):
    await self.channel_layer.group_add(self.room.key, self.channel_name)
    for room_key in self.rooms:
        await presence.touch(room_key, self.user.username)
    await self.send_json({"v": 1, "type": "pong", ...})
```

Re-run the drill with `group_expiry: 20` still set but the heartbeat re-add in
place:

```bash
sleep 25
r TTL 'asgi:group:room.general'
python manage.py sendtyping room.general bob
```
**Expected:**
```
(integer) 17
```
and the frame arrives.

✅ **Refreshed by the heartbeat you were already sending.** Cost: one `ZADD` and
one `EXPIRE` per socket per 10 s — at 20,000 connections that is 2,000 ops/s,
which you just measured as noise.

> **Do both.** Raising `group_expiry` alone fails for any socket that outlives your
> guess. Re-adding alone fails if the heartbeat path breaks. They are independent
> failures and the fix costs nothing.
>
> **Do not raise `expiry` (60 s) to "fix" a slow consumer.** A chat frame that has
> been queued for a minute is worthless, and Module 04 already established the
> right answer: drop the connection, not the room.

Restore `group_expiry: 43_200` before moving on.

---

## Part F — Three backoff policies, three very different herds

Module 10's client already uses full jitter. Prove it matters.

```bash
for policy in fixed base_jitter full_jitter; do
  echo "=== $policy"
  PULSE_BACKOFF=$policy PULSE_STORM=herd \
    locust -f code/locust_storm.py --headless -u 5000 -r 5000 --run-time 3m \
           --host http://localhost:8000 2>/dev/null | tail -1
  curl -s localhost:8000/metrics | grep -E 'pulse_connect_peak|pulse_recovery_seconds'
done
```

**Expected:**
```
=== fixed
peak reconnects/sec: 4,881    time to fully recover: 118s   (server saturated 41s)
=== base_jitter
peak reconnects/sec: 1,942    time to fully recover:  71s
=== full_jitter
peak reconnects/sec:   214    time to fully recover:  34s
```

✅ **23× lower peak than fixed, and 9× lower than the jitter that isn't.**

Look at `base_jitter` closely — it is the one that feels correct and is not:

```js
const delay = base + Math.random() * 1000;    // WRONG
const delay = Math.random() * base;           // RIGHT
```

With `base + jitter`, every client waits *at least* `base` and then arrives inside
a 1-second window. You have delayed the herd, not dispersed it. Full jitter
spreads arrivals uniformly across the entire window, which is why the peak drops by
another 9× for the same average delay.

And notice the last column: **full jitter recovers faster overall.** Dispersal is
not a trade of latency for peak — the server never saturates, so every request is
served at full speed, and everyone is back sooner.

> This is the same arithmetic as Module 10's mass-reconnect resume storm, and
> Module 18 will hit it a third time with a Redis Sentinel failover. Three
> different subsystems, one distribution.

---

## Part G — The token bucket, and the race the naive version loses

### The fixed-window boundary, demonstrated

```bash
r DEL 'fw:alice'
# 10 per minute, fixed window
for i in $(seq 1 10); do r EVAL "
  local n = redis.call('INCR', KEYS[1])
  if n == 1 then redis.call('EXPIRE', KEYS[1], 60) end
  return n" 1 "fw:alice:$(( $(date +%s) / 60 ))" ; done
sleep 1   # cross a minute boundary (run this at :59)
for i in $(seq 1 10); do r EVAL "
  local n = redis.call('INCR', KEYS[1])
  if n == 1 then redis.call('EXPIRE', KEYS[1], 60) end
  return n" 1 "fw:alice:$(( $(date +%s) / 60 ))" ; done
```
**Expected — 20 allowed inside two seconds, from a "10 per minute" limit:**
```
(integer) 1 ... (integer) 10
(integer) 1 ... (integer) 10
```

✅ A guaranteed 2× burst at every window boundary, on a schedule an attacker can
read off a clock.

### The non-atomic version, and its overshoot

```python
# code/race_probe.py
import asyncio, os, redis.asyncio as aioredis

LIMIT, CONC, EACH = 1000, 64, 40


async def main(atomic: bool):
    r = aioredis.from_url(os.environ.get("REDIS_URL", "redis://localhost:6379"),
                          decode_responses=True)
    await r.delete("naive")
    await r.set("naive", LIMIT)
    lua = r.register_script(
        "local n = tonumber(redis.call('GET', KEYS[1]) or '0')\n"
        "if n <= 0 then return 0 end\n"
        "redis.call('DECR', KEYS[1]); return 1")

    allowed = 0

    async def worker():
        nonlocal allowed
        for _ in range(EACH):
            if atomic:
                allowed += int(await lua(keys=["naive"]))
            else:
                n = int(await r.get("naive") or 0)      # <-- yield point
                if n > 0:                               # <-- and here
                    await r.decr("naive")               # <-- and here
                    allowed += 1

    await asyncio.gather(*(worker() for _ in range(CONC)))
    print(f"{'atomic (Lua)' if atomic else 'naive (GET/DECR)':<20} "
          f"limit={LIMIT}  allowed={allowed}  overshoot={allowed - LIMIT:+d} "
          f"({(allowed - LIMIT) / LIMIT:+.1%})")
    await r.aclose()


asyncio.run(main(False))
asyncio.run(main(True))
```

```bash
python code/race_probe.py
```
**Expected:**
```
naive (GET/DECR)     limit=1000  allowed=1412  overshoot=+412 (+41.2%)
atomic (Lua)         limit=1000  allowed=1000  overshoot=+0 (+0.0%)
```

✅ **41% overshoot from a limiter that looks obviously correct.** And that is one
worker process. With eight, the coroutines are not merely interleaved — they are
in different processes, so no amount of Python-level locking would have helped.

> This is the *same* fix as Module 10's sequence allocator: whenever you need
> read-modify-write across a network, the answer is one round trip that does all
> three. Notice how often that sentence has now been true.

### The bucket itself

Copy [`code/ratelimit.lua`](./code/ratelimit.lua) to `chat/lua/ratelimit.lua` and
[`code/ratelimit.py`](./code/ratelimit.py) to `chat/ratelimit.py`.

Two things in the Lua differ from the cheatsheet version, both deliberate:

**Time comes from `redis.call('TIME')`, not from the caller.** With 8 worker
processes on 3 machines, a host whose clock is 200 ms fast hands out
`200 ms × refill_rate` free tokens on every single call, forever. Prove it:

```bash
# simulate a fast clock by passing now_ms + 200 to the cheatsheet version
python code/clock_skew_probe.py
```
**Expected:**
```
server-sourced TIME : limit 5/s, observed 5.0/s   (skew +200ms)
caller-sourced now  : limit 5/s, observed 6.0/s   (skew +200ms)  <-- 20% free
```

**It returns the remaining tokens**, so `pulse_ratelimit_tokens` shows you a tier
approaching saturation *before* it starts denying. A limiter you cannot observe is
a limiter you will tune by guessing.

Verify the shape:

```bash
python - <<'PY'
import asyncio, os, time, redis.asyncio as aioredis
from pathlib import Path

async def main():
    r = aioredis.from_url(os.environ.get("REDIS_URL","redis://localhost:6379"),
                          decode_responses=True)
    s = r.register_script(Path("chat/lua/ratelimit.lua").read_text())
    await r.delete("rl:demo")
    burst = sum(int((await s(keys=["rl:demo"], args=[20, 5, 1]))[0]) for _ in range(30))
    print(f"burst of 30 against capacity 20 -> allowed {burst}")
    ok, retry, left = await s(keys=["rl:demo"], args=[20, 5, 1])
    print(f"next call: allowed={ok} retry_after_ms={retry} tokens_left={left/1000:.2f}")
    await asyncio.sleep(2)
    ok, retry, left = await s(keys=["rl:demo"], args=[20, 5, 1])
    print(f"after 2s : allowed={ok} tokens_left={left/1000:.2f}")
    await r.aclose()

asyncio.run(main())
PY
```
**Expected:**
```
burst of 30 against capacity 20 -> allowed 20
next call: allowed=0 retry_after_ms=200 tokens_left=0.00
after 2s : allowed=1 tokens_left=9.00
```

✅ **20 allowed instantly (the burst), then exactly 5/s.** The `retry_after_ms` of
200 is `(1 - 0) / 5 × 1000` — a schedule, not a guess.

---

## Part H — Six tiers, and what a flood looks like from both ends

Wire the limiter into the consumer:

```python
# chat/consumers.py
from .ratelimit import Limiter, TokenBucket, deny

limiter = Limiter(TokenBucket(fanout.redis))


async def connect(self):
    ip = self.scope["client"][0]
    ok, retry, _tier = await limiter.allow_connection(ip)
    if not ok:
        # Before accept(), so the client gets an HTTP-level rejection and never
        # pays for a WebSocket handshake it is not allowed to have.
        await self.close(code=4429)
        return
    ...


async def _on_message(self, content):
    data = content["data"]
    ok, retry, tier = await limiter.allow_message(
        self.user.id, self.room.key, self.scope["client"][0])
    if not ok:
        return await deny(self, self.room.key, tier, retry, data.get("client_id"))
    ...   # the Module 10 send path


async def _on_resume(self, content):
    ok, retry, tier = await limiter.allow_resume(self.user.id, self.room.key)
    if not ok:
        return await deny(self, self.room.key, tier, retry, None)
    ...
```

Flood one user and watch which tier catches it:

```bash
python code/flood.py --user alice --room room.general --rate 200 --seconds 20
curl -s localhost:8000/metrics | grep pulse_ratelimit_denied_total
```
**Expected:**
```
pulse_ratelimit_denied_total{tier="msg_user_room"} 3891.0
```
✅ The most specific tier catches it first — one round trip, not four.

Now flood *across* rooms, which every per-room limit would allow:

```bash
python code/flood.py --user alice --rooms 100 --rate 200 --seconds 20
curl -s localhost:8000/metrics | grep pulse_ratelimit_denied_total
```
**Expected:**
```
pulse_ratelimit_denied_total{tier="msg_user_room"} 3891.0
pulse_ratelimit_denied_total{tier="msg_user"}     3702.0
```
✅ **The global per-user tier catches what the per-room tier structurally cannot.**
Spraying 2 messages/s into 100 rooms is inside every per-room limit and is
obviously abuse.

And from the *client's* side:

```json
{"v":1,"type":"error","room":"room.general","ts":1735689600123,
 "data":{"code":"rate_limited","message":"rate limit exceeded (msg_user_room)",
         "retry_after_ms":200,"client_id":"01JQ8Z4K7M8YQ2VBXR3N5TDGWH"}}
```

Three things to verify, because each has a wrong alternative that is easy to ship:

```bash
# 1. The socket is still open (protocol §4).
python code/flood.py --user alice --room room.general --rate 200 --seconds 20 --report-close
```
```
frames sent: 4000   errors received: 3891   socket closed: no
```
✅ Closing would have cost a handshake, an auth check, a `group_add` and a resume
— answering "too much traffic" with "here, have some more."

```bash
# 2. client_id is echoed, so the right bubble is marked failed.
# 3. retry_after_ms is a real schedule.
python code/flood.py --user alice --room room.general --rate 200 --seconds 20 --honour-retry
```
```
frames sent: 104   errors received: 4   effective rate: 5.0/s
```
✅ **A client that honours `retry_after_ms` self-regulates to exactly the limit**
with 4 wasted frames instead of 3,891. That is the whole reason the field exists.

Finally, the cost of the limiter itself:

```bash
curl -s localhost:8000/metrics | grep -E 'pulse_ratelimit_seconds'
```
```
pulse_ratelimit_seconds{quantile="0.5"}  0.00009
pulse_ratelimit_seconds{quantile="0.99"} 0.00019
```
✅ **0.19 ms p99 for four tiers**, two round trips. Compare with forcing all four
into one Cluster slot for a single atomic call: 0.11 ms, and 100% of limiter
traffic pinned to one Cluster node. Pulse pays the 0.08 ms.

---

## Part I — The lock you should not need

```bash
r SET 'lock:job:trim' "$(uuidgen)" NX PX 30000
r GET 'lock:job:trim'
r SET 'lock:job:trim' "$(uuidgen)" NX PX 30000
```
**Expected:**
```
OK
"9f1c2a4e-..."
(nil)          <-- the second attempt correctly fails
```

Release safely — **never a bare `DEL`**:

```lua
if redis.call('GET', KEYS[1]) == ARGV[1] then
    return redis.call('DEL', KEYS[1])
end
return 0
```

Now demonstrate why the lock is not a correctness mechanism, in the way that is
specific to Python. Hold the lock in an async task, then block the event loop with
one synchronous ORM call:

```python
# code/lock_loss.py
import asyncio, time, uuid
import redis.asyncio as aioredis

TOKEN = str(uuid.uuid4())


async def renew_forever(r):
    """The renewal coroutine. It is on the same event loop as everything else."""
    while True:
        await asyncio.sleep(1)
        await r.pexpire("lock:job:trim", 3000)
        print(f"{time.strftime('%H:%M:%S')} renewed")


async def main():
    r = aioredis.from_url("redis://localhost:6379", decode_responses=True)
    await r.set("lock:job:trim", TOKEN, nx=True, px=3000)
    asyncio.create_task(renew_forever(r))
    await asyncio.sleep(2)

    print("--- blocking the event loop for 6 seconds (one sync ORM call) ---")
    time.sleep(6)                       # the cardinal sin, Module 01
    print("--- back ---")

    holder = await r.get("lock:job:trim")
    print(f"I think I hold the lock. Redis says the holder is: {holder}")
    print(f"Is it me? {holder == TOKEN}")


asyncio.run(main())
```

In another terminal, steal it while the loop is blocked:

```bash
python code/lock_loss.py &
sleep 4
r SET 'lock:job:trim' "someone-else" NX PX 30000
wait
```
**Expected:**
```
14:02:01 renewed
14:02:02 renewed
--- blocking the event loop for 6 seconds (one sync ORM call) ---
--- back ---
I think I hold the lock. Redis says the holder is: someone-else
Is it me? False
```

✅ **The lock expired, someone else took it, and no exception was raised anywhere.**

Note what did *not* happen: the process did not pause, garbage-collect, or fail.
It ran one blocking call — a `Room.objects.get()` without
`database_sync_to_async`, the exact mistake Module 15 measures at multiple seconds
— and the renewal coroutine, which is on the same loop, simply did not run.

> **This is why Redlock's contested status matters to you specifically.** The
> critique's core claim is that a process pause longer than the lock TTL breaks
> safety and no quorum can detect it, because the failure is in *your* process.
> On the JVM that argument is about GC pauses. In Python it is about a single
> synchronous call in an async consumer, which is easier to write by accident and
> lasts longer.

**Pulse's answer is not a better lock. It is no lock:**

```python
def owns(room_key: str) -> bool:
    """Deterministic ownership by consistent hash. No lock, no renewal, no
    failure mode — and it partitions the work evenly for free."""
    return zlib.crc32(room_key.encode()) % WORKER_COUNT == WORKER_INDEX
```

```bash
PULSE_WORKER_COUNT=8 python code/ownership_check.py --rooms 1000
```
**Expected:**
```
worker 0: 128 rooms   worker 4: 122 rooms
worker 1: 121 rooms   worker 5: 129 rooms
worker 2: 127 rooms   worker 6: 124 rooms
worker 3: 125 rooms   worker 7: 124 rooms
overlaps: 0   unowned: 0
```

✅ **Zero overlap, zero unowned, no lock.** The cost is that a dead worker's rooms
are unmaintained until the supervisor restarts it — which is a *liveness* problem
you can monitor, rather than a *safety* problem you cannot detect. Module 18
resizes `WORKER_COUNT` under load and shows what rebalancing costs.

---

## What you built

- TTL presence on a sorted set, where **cleanup is a side effect of reading** and
  a `kill -9` cannot leave a ghost.
- Measured proof that keyspace notifications are **21.8 s late at p99 and lose
  15.5%** during a 1.5 s Redis pause, and that the alternative roster query
  (`KEYS`) stalls the single thread for **41 ms**.
- A **2,341,000 frames/s** presence storm — 15.6× the pinned fan-out knee — cut
  **117×** by aggregation, focus and suppression.
- Typing aggregated from 1,204,800 frames to **12,340**.
- The `group_expiry` trap caught in the act: a live, healthy socket that silently
  stops receiving presence and typing, fixed by a heartbeat re-add.
- Three backoff policies measured: **4,881 → 1,942 → 214** peak reconnects/s, with
  full jitter also recovering fastest.
- A Lua token bucket that allows exactly the limit where the obvious version
  overshoots by **41%**, with server-sourced time and observable token counts.
- Six limit tiers wired into the protocol's `rate_limited` error frame — socket
  stays open, `client_id` echoed, `retry_after_ms` honoured to **4 wasted frames
  instead of 3,891**.
- A demonstration that one blocking call loses you a distributed lock silently,
  and the consistent-hash ownership that means you never needed one.

Now do [`challenge.md`](./challenge.md).

Then: [Module 12 — The Postgres Message Store](../12-postgres-message-store/).
