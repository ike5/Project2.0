# Lab 07 — The Redis Backplane, and Its Cost

**You'll:** swap one settings dict and watch Module 04's wall disappear; read
the channel layer's state straight out of Redis; measure what the hop costs
(**+4 ms p50**) and take that 4 ms apart into its four components; measure the
scaling factor (**1.90×, not 2×**) and account for the missing 5%; discover the
worker count at which **adding a worker makes it slower**; put nginx in front
with sticky sessions; run the two `channels_redis` layers head to head; and then
**pause Redis under load and count exactly what disappears** — twice, because
the second failure mode is far worse than the first and produces no errors at
all.

⏱️ ~110 min. Work in `django-chat-course/apps/pulse`.

```bash
cd django-chat-course/apps/pulse
source ../../.venv/bin/activate
set -a; source env.dev; set +a
docker compose -p pulse-dev -f ../../infra/compose.dev.yml up -d
pip install --quiet "channels-redis==4.2.*"
alias r='docker exec -i pulse-redis redis-cli'
r PING
```
**Expected:** `PONG`

Reference machine: **8-core / 16 GB, Ubuntu 24.04, Python 3.12, Django 5.1,
Channels 4.1, `channels_redis` 4.2, Uvicorn + uvloop, Redis 7.4.**

Every number below is a comparison against the Module 06 baseline: **p50 11 ms,
p95 52 ms, p99 138 ms, p99.9 640 ms at 20,000 connections and 66,307 outbound
msg/s, knee ≈150,000 outbound msg/s, one worker, one core.**

---

## Part A — Swap the layer

`pulse/settings.py` — replace the whole `CHANNEL_LAYERS` block:

```python
REDIS_URL = env("REDIS_URL", "redis://localhost:6379/0")

CHANNEL_LAYERS = {
    # The message path. Mailboxes are Redis sorted sets; group membership is
    # a sorted set in Redis too. Read the README's decompilation table before
    # you change any of these four numbers.
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [{
                "address": REDIS_URL,
                # WITHOUT THESE, A PAUSED REDIS HANGS EVERY CONSUMER FOREVER.
                # redis-py's default socket_timeout is None: an await that
                # never returns, on a loop that then never runs anything else.
                # A 1-second timeout turns an unbounded hang into a countable
                # failure -- which is what Part I counts.
                "socket_timeout": 1.0,
                "socket_connect_timeout": 1.0,
                "health_check_interval": 15,
            }],
            "prefix": "pulse",

            # capacity is PER WORKER MAILBOX, not per connection. The default
            # of 100 was sized for a world where a channel was one consumer;
            # in channels_redis every connection on a worker shares ONE
            # mailbox key, so 100 is roughly 0.5 seconds of fan-out for a
            # worker holding 20,000 sockets. 1,500 is ~2 s of headroom at the
            # Module 06 safe operating point. Part I shows what happens above
            # it, and it is not what you would guess.
            "capacity": 1500,

            # How long an undelivered message survives in a mailbox. The
            # default is 60 s. For chat, a 60-second-old frame is worse than
            # useless: the client has already reconnected and resumed
            # (Module 10), and delivering it now inserts a message into the
            # past. 10 s is longer than any reconnect and shorter than any
            # user's patience.
            "expiry": 10,

            # How long a group membership survives without a refresh. Part I
            # explains why this number is a trap and Part I's fix is why we
            # leave it at the default rather than lowering it.
            "group_expiry": 86400,
        },
    },

    # The ephemeral path: typing, presence blips, cursors. Actual Redis
    # Pub/Sub -- one PUBLISH per send, no storage, no capacity, no bound.
    # Part J wires it; the README's table says why it is a second layer and
    # not the only layer.
    "ephemeral": {
        "BACKEND": "channels_redis.pubsub.RedisPubSubChannelLayer",
        "CONFIG": {"hosts": [{"address": REDIS_URL, "socket_timeout": 1.0}],
                   "prefix": "pulse.eph"},
    },
}
```

That is the entire change to the message path. `self.channel_layer.group_add`,
`group_send` and `group_discard` are the same three calls Module 04 wrote; the
object behind them is different.

Verify Channels agrees:

```bash
python manage.py shell -c "
from channels.layers import get_channel_layer
d, e = get_channel_layer(), get_channel_layer('ephemeral')
print(type(d).__module__ + '.' + type(d).__qualname__, d.prefix, d.capacity, d.expiry)
print(type(e).__module__ + '.' + type(e).__qualname__)
"
```
**Expected:**
```
channels_redis.core.RedisChannelLayer pulse 1500 10
channels_redis.pubsub.RedisPubSubChannelLayer
```

---

## Part B — The wall is gone

Start **two** workers — the exact command that broke in Module 04:

```bash
uvicorn pulse.asgi:application --host 127.0.0.1 --port 8000 --workers 2 \
        --loop uvloop --ws-per-message-deflate false --ws-max-queue 64 \
        --log-level warning &
sleep 3
```

Two terminals, same room, and check the `pid` field:

```bash
websocat "ws://localhost:8000/ws/room/general/?as=u0"
websocat "ws://localhost:8000/ws/room/general/?as=u1"
```
**Expected — two different pids, as before:**
```
{"type": "hello", "room": "room.general", "you": "u0", "pid": 61002, "channel": "pulsespecific.7c1a09bb!QK7pZm", "online": ["u0"]}
{"type": "hello", "room": "room.general", "you": "u1", "pid": 61003, "channel": "pulsespecific.e4f7233d!Lw9xRt", "online": ["u1"]}
```

Send from terminal 1:
```json
{"v":1,"type":"message.create","data":{"client_id":"01JQ8Z4K7M8YQ2VBXR3N5TDGWH","body":"can you hear me now"}}
```

**Expected — in *both* terminals:**
```json
{"v": 1, "type": "message.new", "room": "room.general", "ts": 1735689600241, "data": {"id": 5031, "seq": 5031, "client_id": "01JQ8Z4K7M8YQ2VBXR3N5TDGWH", "sender": "u0", "body": "can you hear me now", "reply_to": null}}
```

✅ **Module 04's cliffhanger, resolved by a settings dict.**

Now the quantitative version — Module 04's `crosstalk` mode measured 100% / 52%
/ 26% delivery at 1 / 2 / 4 workers:

```bash
for w in 1 2 4 8; do
  kill %1 2>/dev/null; sleep 2
  uvicorn pulse.asgi:application --port 8000 --workers $w --loop uvloop \
          --ws-per-message-deflate false --log-level warning &
  sleep 4
  printf "workers=%d  " "$w"
  python ../../04-channels-chat-single-node/code/wsprobe.py crosstalk \
         --room general --pairs 50
done
```

**Expected:**
```
workers=1  50/50 message pairs delivered across connections  (100.0%)
workers=2  50/50 message pairs delivered across connections  (100.0%)
workers=4  50/50 message pairs delivered across connections  (100.0%)
workers=8  50/50 message pairs delivered across connections  (100.0%)
```

✅ **100% at every worker count.** Module 04's table read 100 / 52 / 26; this one
reads 100 / 100 / 100 / 100. **You can now use all eight cores.**

---

## Part C — Read the layer's state out of Redis

Module 04 printed the channel layer as a Python dict. Do the same thing now:

```bash
../../07-scale-out-redis-channel-layer/code/layer_probe.py groups
```

**Expected (8 workers, a few clients in `general`):**
```
pulse:group:room.general
    members      4   ttl   86397s   workers 3
      worker 7c1a09bb  2 channels
      worker e4f7233d  1 channels
      worker 91b0ff3e  1 channels
```

✅ **The distributed system, printed again — this time it is a sorted set.**
Four channel names, three worker processes, one 24-hour TTL. Compare with
Module 04's output: same information, one shared copy instead of N disjoint
ones.

Read the raw keys so the naming never surprises you later:

```bash
r --scan --pattern 'pulse*' | sort | head
r ZRANGE 'pulse:group:room.general' 0 -1 WITHSCORES | head -4
r TYPE 'pulse:group:room.general'
```
**Expected:**
```
pulse:group:room.general
pulsespecific.7c1a09bb!
pulsespecific.91b0ff3e!
pulsespecific.e4f7233d!
```
```
1) "specific.7c1a09bb!QK7pZm"
2) "1735689598.4127"
...
zset
```

> ⚠️ **Note the asymmetry**: the group key is `pulse:group:…` with a colon, and
> the mailbox key is `pulsespecific.…` with none. That is real — `_group_key()`
> formats `f"{prefix}:group:{group}"` while the mailbox key is `prefix + channel`
> — and it will confuse you exactly once when you write a `SCAN` pattern.
> **One mailbox key per worker process**, not per connection. That is the single
> most important thing on this screen.

### The property that decides your Redis capacity

```bash
# put 200 clients in room 7 across 8 workers, then look
python ../../04-channels-chat-single-node/code/wsprobe.py hold \
       --n 200 --room 7 --user rp &
sleep 5
../../07-scale-out-redis-channel-layer/code/layer_probe.py amplification --room 7
```

**Expected:**
```
group room.7
  room members (channels) : 200
  worker processes        : 8
  Redis writes per send   : 8
  socket writes per send  : 200  (done by the workers, on their own cores)
  amplification absorbed locally: 25.0x
```

✅ **A 200-member room costs Redis 8 writes, not 200.** The 199-way fan-out is
still real — it is still the CPU cost you tuned in Module 06 — but it happens
inside each worker's event loop, on its own core, which is exactly where you
want it.

Watch one `group_send` on the wire:

```bash
r MONITOR &
websocat "ws://localhost:8000/ws/room/7/?as=u0" <<< \
  '{"v":1,"type":"message.create","data":{"client_id":"01JQ8Z4K7M8YQ2VBXR3N5TDX1","body":"trace me"}}'
sleep 1; kill %1
```

**Expected — five kinds of command, in this order:**
```
"ZREMRANGEBYSCORE" "pulse:group:room.7" "0" "1735603200"
"ZRANGE" "pulse:group:room.7" "0" "-1"
"ZREMRANGEBYSCORE" "pulsespecific.7c1a09bb!" "0" "1735689590"
"ZREMRANGEBYSCORE" "pulsespecific.e4f7233d!" "0" "1735689590"
... (one per worker)
"EVAL" "\n local over_capacity = 0\n ..." "8" "pulsespecific.7c1a09bb!" ... 
"BZPOPMIN" "pulsespecific.7c1a09bb!" "5"
```

Read it as an algorithm: *drop expired members, read the membership, drop
expired messages from each destination mailbox, then one atomic script that
appends the message to every mailbox and refreshes its TTL.* Then each worker's
blocked `BZPOPMIN` returns.

⚠️ **`MONITOR` can halve Redis's throughput.** It is a development tool. Never
leave it running, and Module 08 shows you what it costs.

---

## Part D — Keep the Module 06 rig working across eight workers

`/metrics` now hits whichever worker the kernel picked, so
`chat_connections_active` reads 1/8 of the truth. Fix it properly:

```bash
export PROMETHEUS_MULTIPROC_DIR=/tmp/pulse-prom
rm -rf $PROMETHEUS_MULTIPROC_DIR && mkdir -p $PROMETHEUS_MULTIPROC_DIR
uvicorn pulse.asgi:application --port 8000 --workers 8 --loop uvloop \
        --ws-per-message-deflate false --ws-max-queue 64 --log-level warning &
sleep 4
curl -s localhost:8000/metrics | grep -E 'chat_connections_active|chat_event_loop_lag'
```

**Expected — one series per worker, merged from mmap files:**
```
chat_connections_active{worker="pid-61002"} 2503.0
chat_connections_active{worker="pid-61003"} 2497.0
... (8 lines)
chat_event_loop_lag_seconds{worker="pid-61002"} 0.0012
```

`code/metrics.py` already handled this: it built a fresh `CollectorRegistry`
with a `MultiProcessCollector` when the env var is present. The `Gauge`s were
declared `multiprocess_mode="livesum"` (connections add across workers) and
`"livemax"` (loop lag is the *worst* worker's, not the sum — a summed lag gauge
is meaningless and Module 20 will page on this one).

> ⚠️ **Clean `PROMETHEUS_MULTIPROC_DIR` on every start.** The mmap files are
> keyed by pid; a restarted worker gets a new pid and the old file lingers
> forever, so `chat_connections_active` slowly climbs to a number no worker
> believes. This is the most common `prometheus_client` bug in production.

---

## Part E — What the hop costs

Isolate the hop from the parallelism: **one worker**, both layers, the identical
Module 06 workload.

```bash
for backend in memory redis; do
  kill %1; sleep 3
  CHANNEL_BACKEND=$backend uvicorn pulse.asgi:application --port 8000 \
      --workers 1 --loop uvloop --ws-per-message-deflate false \
      --ws-max-queue 64 --log-level warning &
  sleep 4
  echo "=== $backend ==="
  k6 run -q -e ROOMS=100 -e SEND_EVERY=60000 --duration 5m \
         --summary-export=/tmp/hop-$backend.json \
         ../../06-load-testing-harness/code/pulse-load.js
  sleep 45
done
```

**Expected:**

| | 1 worker, in-memory | 1 worker, Redis layer | Delta |
|---|--------------------|----------------------|-------|
| p50 | 11 ms | **15 ms** | **+4 ms** |
| p95 | 52 ms | 60 ms | +8 ms |
| p99 | 138 ms | 158 ms | +20 ms |
| p99.9 | 640 ms | 712 ms | +72 ms |
| Worker CPU at 66,307 out/s | 44% | **41%** | **−3 pts** |
| Redis CPU | — | 4% | |
| Redis memory | — | 8 MB | |

Two surprises in that table, and both are worth a minute.

**The worker got *cheaper*.** The in-memory layer `deepcopy`s the event dict
once per recipient — 11.5% of a core in Module 06's profile. The Redis layer
msgpack-serialises it **once** and each worker deserialises **once**. You added
a network hop and removed CPU.

**The p99 grew five times faster than the p50 (+20 ms vs +4 ms).** A hop's cost
is not a constant; it is a constant *plus* a queueing term, and the queueing term
is what the tail is made of.

### Take the 4 ms apart

```bash
r INFO commandstats | grep -E 'cmdstat_(eval|zrange|bzpopmin|zremrangebyscore)'
r --latency
```
**Expected:**
```
cmdstat_eval:calls=19984,usec=799360,usec_per_call=40.00
cmdstat_zrange:calls=19984,usec=699440,usec_per_call=35.00
cmdstat_zremrangebyscore:calls=39968,usec=199840,usec_per_call=5.00
cmdstat_bzpopmin:calls=19992,usec=499800,usec_per_call=25.00

min: 0, max: 3, avg: 0.11 (1497 samples)
```

| Component | Contribution to p50 | How measured |
|-----------|--------------------|--------------|
| Redis command execution | **0.11 ms** | `usec_per_call` × commands per message |
| Loopback round trips (2) | **0.22 ms** | `redis-cli --latency` avg |
| msgpack pack + unpack | **0.31 ms** | `timeit` on the serialised event |
| **Event-loop scheduling: 4 extra `await` points on a 44%-busy loop** | **3.24 ms** | the remainder — confirmed below |
| Misc (dict churn, `__asgi_channel__` routing) | 0.12 ms | |
| **Total** | **4.00 ms** | matches the measured delta |

Confirm the big one rather than assuming it. Re-run with the loop nearly idle:

```bash
k6 run -q --vus 1000 -e ROOMS=50 -e SEND_EVERY=60000 --duration 3m \
       ../../06-load-testing-harness/code/pulse-load.js
```
**Expected:**
```
in-memory,  1,000 conns:  p50 3 ms
redis,      1,000 conns:  p50 3.9 ms      (+0.9 ms)
```

✅ **The same hop costs 0.9 ms on an idle loop and 4.0 ms on a 44%-busy one.**
Redis did not get slower — your event loop did. Every `await` is a yield to a
scheduler whose queue depth is proportional to how loaded the worker is, and the
Redis path adds four of them.

**That is the Python-specific finding of this module.** On the JVM twin the
equivalent hop cost +3 ms and it was mostly serialisation and thread handoff.
Here it is mostly **scheduling latency on a single-threaded loop**, which means
it grows with your utilisation. Budget the hop as a *fraction of your loop's
idle time*, not as a constant.

---

## Part F — The scaling factor, and the worker that made it worse

Now the point of the whole exercise. Find the knee at 1, 2, 4 and 8 workers,
with the Module 06 procedure: hold 20,000 connections and lower `SEND_EVERY`
until loop lag stays above 50 ms.

```bash
for w in 1 2 4 8; do
  kill %1; sleep 3
  rm -rf $PROMETHEUS_MULTIPROC_DIR && mkdir -p $PROMETHEUS_MULTIPROC_DIR
  uvicorn pulse.asgi:application --port 8000 --workers $w --loop uvloop \
          --ws-per-message-deflate false --ws-max-queue 64 &
  sleep 4
  for every in 60000 30000 20000 14000 10000 7000; do
    r CONFIG RESETSTAT
    k6 run -q -e ROOMS=100 -e SEND_EVERY=$every --duration 3m \
           --summary-export=/tmp/knee-w$w-$every.json \
           ../../06-load-testing-harness/code/pulse-load.js
    echo -n "w=$w every=$every  redis_cpu="
    r INFO cpu | awk -F: '/used_cpu_sys/{s=$2} /used_cpu_user/{u=$2} END{print (s+u)}'
    sleep 45
  done
done
```

**Expected:**

| Workers | Knee (outbound msg/s) | vs 1 worker | Redis CPU at the knee | p50 at 66k out/s | What binds |
|---------|----------------------|-------------|----------------------|------------------|-----------|
| 1 (in-memory) | 150,000 | 1.00× | — | 11 ms | worker core |
| 1 (Redis) | 147,000 | 0.98× | 7% | 15 ms | worker core |
| **2** | **285,000** | **1.90×** | 21% | 15 ms | worker cores |
| 4 | 521,000 | 3.47× | 63% | 16 ms | worker cores |
| **8** | **441,000** | **2.94×** | **94%** | **31 ms** | **Redis's one thread** |

```
knee │              ● 4 workers (521k)
 out │           ╱      ●  8 workers (441k)   <- WORSE THAN FOUR
 /s  │       ╱
     │   ● 2 (285k)
     │ ● 1 (147k)
     └──────────────────────────────────  workers
```

✅ **1.90×, not 2×** — and ✅ **the eighth worker made it slower.** Two findings,
two different explanations, and you should be able to give both.

### Where the missing 5% goes at two workers

Perfect scaling would be 2 × 147,000 = 294,000. You measured 285,000: a
**3.1% shortfall** against the Redis-layer single-worker number, or **5.0%**
against the in-memory 150,000 the course quotes. Profile a worker at the knee:

```bash
sudo py-spy top --pid $(pgrep -f 'uvicorn pulse.asgi' | tail -1) \
     --duration 30 --nonblocking | head -8
```
**Expected:**
```
 19.50%  19.50%    5.85s     5.85s   write (asyncio/selector_events.py)
 12.00%  15.50%    3.60s     4.65s   send (websockets/legacy/protocol.py)
  8.50%   8.50%    2.55s     2.55s   unpackb (msgpack/_unpacker)
  5.00%  31.00%    1.50s     9.30s   receive (channels_redis/core.py)
  4.00%   4.00%    1.20s     1.20s   packb (msgpack/_packer)
  2.50%  38.00%    0.75s    11.40s   group_send (channels_redis/core.py)
```

| Cost | % of a worker's core | Was it there in Module 06? |
|------|--------------------|---------------------------|
| Receive path: `BZPOPMIN` wake + `unpackb` + `__asgi_channel__` routing | **2.9%** | no — new |
| Send path: the sender's coroutine parked on the `EVAL` round trip | **1.4%** | no — new |
| Redis's single thread, which both workers wait on | 0.7% | no — new |
| `deepcopy` removed | **−1.0%** | was there, now gone |
| **Net** | **+4.0%** | ⇒ 1.90× instead of 2.00× |

**The shortfall is a per-worker fixed cost, not a per-message one**, which is
exactly why it does not get worse from 2 to 4 workers (3.47× is 87% efficient,
close to 2's 95% only because the base is bigger) and why it is not the thing
that kills you at 8.

### Why eight workers is worse than four

```bash
r INFO commandstats | grep -E 'cmdstat_(eval|zrange|bzpopmin)'
r --stat
```
**Expected at the 8-worker knee:**
```
cmdstat_eval:calls=673800,usec=53904000,usec_per_call=80.00
cmdstat_zrange:calls=673800,usec=23583000,usec_per_call=35.00
cmdstat_bzpopmin:calls=5390400,usec=134760000,usec_per_call=25.00
```
```
------- data ------ --------------------- load --------------------
keys       mem      clients blocked requests            connections
1102       41.19M   19      8       48214 (+0)          21
```

**`bzpopmin` is called eight times per `group_send`** — once per worker that
must be woken — and at 80 µs for the `EVAL` plus 8 × 25 µs of blocked-client
wakeups, Redis is spending **423 µs of its single thread per message**:

```
fixed per group_send      55 us   (ZRANGE the membership + EVAL setup)
per worker                46 us   (ZREMRANGEBYSCORE + one EVAL key + BZPOPMIN wake)

8 workers:  55 + 8 x 46  =  423 us   ->  2,246 group_sends/s at 95% of one thread
                                     ->  2,246 x 199  =  447,000 outbound msg/s
```

Measured: 441,000. **The prediction and the measurement agree to 1.4%, and
Redis's single thread — not your eight cores — is the ceiling.**

At 4 workers the same arithmetic gives 239 µs and a Redis-bound ceiling of
790,000, well above the 521,000 the workers themselves could produce. **Four
workers are CPU-bound on Python; eight are bound on one C thread in another
process.** Adding the fifth through eighth worker bought you nothing and cost
you 46 µs of Redis per worker per message.

> **Write this sentence in `results-07.md`, because it is the module's thesis:**
> *The Redis channel layer moved the wall from "one Python core" to "one Redis
> thread", and the exchange rate is about four workers.*
>
> The escape hatches are all later modules and you now know why each exists:
> [Module 09](../09-redis-streams-delivery/) changes the cost shape (one `XADD`,
> N independent readers); [Module 14](../14-sharding-and-wide-column/) shards
> rooms across workers so fewer processes subscribe to each;
> [Module 18](../18-compose-ha-and-chaos/) puts Redis in Cluster so there is
> more than one thread. None of them is a tuning flag.

### Confirm at two *machines*, not just two workers

```bash
# host A: 1 worker + the Redis container
# host B: 1 worker,  REDIS_URL=redis://hostA:6379/0
k6 run -e HOST=hostA:8000 -e ROOMS=100 -e SEND_EVERY=14000 ...
```
**Expected:**
```
2 workers, one box : knee 285,000   p50 15 ms
2 nodes, two boxes : knee 281,000   p50 17 ms   (1.87x)
```

✅ **1.87× across machines versus 1.90× across processes** — the extra 2 ms of
p50 is real ethernet instead of loopback. **In Python the process boundary and
the machine boundary cost almost the same**, which is the practical restatement
of everything Module 04 argued: you paid the distributed-systems price the
moment you wanted your second core.

---

## Part G — The two layers, head to head

Same 8-worker deployment, one settings change:

```bash
CHANNEL_BACKEND=pubsub uvicorn pulse.asgi:application --port 8000 --workers 8 ... &
```

**Expected:**

| At 8 workers, 20,000 conns | `RedisChannelLayer` | `RedisPubSubChannelLayer` |
|---|---------------------------|---------------------------|
| p50 at 66,307 out/s | 19 ms | **17 ms** |
| p95 | 71 ms | **66 ms** |
| p99 | 181 ms | **168 ms** |
| **Knee** | 441,000 | **1,010,000** |
| Redis commands/s at 120k out/s | **33,100** | **3,015** |
| Redis CPU at 120k out/s | **26%** | **9%** |
| Redis memory at the knee | 41 MB | **6 MB** |
| Lost, `docker pause` 0.75 s | **29 / 200** | 41 / 200 |
| Lost, `docker kill` + restart | **139 / 200, and permanent** | 22 / 200, self-heals |
| Slow consumer, unbounded | capped at 1,500, logged at INFO | **worker heap → OOM** |

The Pub/Sub layer wins on every performance row, by a lot: **one `PUBLISH`
instead of a `ZRANGE` plus an eight-key `EVAL` plus eight blocked-client
wakeups**, and Redis's thread does 3,015 commands/s instead of 33,100.

And Pulse keeps `RedisChannelLayer` on the message path anyway. **Defend that.**

| | Core layer | Pub/Sub layer |
|---|-----------|---------------|
| A slow consumer | mailbox stops at `capacity`; over-capacity is **counted** | unbounded `asyncio.Queue`; the worker dies |
| Redis restart | groups vanish, **permanently, silently** | re-subscribes, self-heals |
| A brief blip | message waits in the mailbox up to `expiry` | gone |

**The decision:** Pulse runs the **core layer** on the message path, because
Module 06's most expensive lesson was that one non-reading client can take a
worker's heap, and the Pub/Sub layer has *no bound at all*. A silent capacity
drop that increments a counter is a bad day; an OOM-killed worker holding 20,000
sockets is an outage for everybody on it.

**The rejected alternative and its price:** ~2.3× the knee, 3.9× fewer Redis
commands, and a restart that self-heals. That is a *large* thing to give up.

**The condition that flips the answer:** the moment Module 09's Streams path
takes over the message hot path, the core layer's storage and capacity stop
mattering — Streams provide both, better. At that point the channel layer is
only carrying ephemera, and Pub/Sub is unambiguously correct for it. **Which is
exactly what happens two modules from now**, and why the `"ephemeral"` layer in
Part A already exists.

---

## Part H — nginx and sticky sessions

```bash
kill %1
for p in 8000 8001; do
  PULSE_WORKER=node-$p uvicorn pulse.asgi:application --port $p --workers 4 \
      --loop uvloop --ws-per-message-deflate false --log-level warning &
done
docker run -d --name pulse-nginx -p 8090:80 \
  --add-host=host.docker.internal:host-gateway \
  -v "$PWD/../../07-scale-out-redis-channel-layer/code/nginx.conf:/etc/nginx/nginx.conf:ro" \
  nginx:alpine
```

```bash
for i in 1 2 3 4 5; do
  curl -s -c /tmp/c$i -b /tmp/c$i localhost:8090/api/layer-debug/ \
    | python -c "import sys,json; print(json.load(sys.stdin)['pid'])"
done
```
**Expected — five cookie jars spread across the eight worker pids:**
```
61002
61107
61004
61109
61003
```

Repeat with the same jars. **Expected:** identical pids — the hash is stable.

Now check WebSocket actually upgrades through the proxy:
```bash
websocat -v "ws://localhost:8090/ws/room/general/?as=u0" 2>&1 | head -3
```
**Expected:**
```
[INFO  websocat::ws_client_peer] Connected to ws://localhost:8090/ws/room/general/?as=u0
{"type": "hello", "room": "room.general", "you": "u0", "pid": 61002, ...}
```

Comment out `proxy_http_version 1.1;` and reload to see the classic failure:
```
[INFO  websocat] Connection finished: HTTP 400 Bad Request
```
nginx defaults to HTTP/1.0 upstream, which has no `Upgrade` semantics. **This is
the single most common "WebSocket works locally but not behind the proxy"
cause**, and the error message names nothing useful.

Kill the 8001 process and watch the redistribution:
```bash
kill %2
for i in 1 2 3 4 5; do curl -s -b /tmp/c$i localhost:8090/api/layer-debug/ \
  | python -c "import sys,json;print(json.load(sys.stdin)['pid'])"; done
```
**Expected — only 8000's pids:**
```
61002
61004
61003
61002
61004
```

✅ nginx marked the upstream down after `max_fails` and rehashed. **The clients
that were on 8001 had their WebSockets dropped** and must reconnect — which is
Module 18's thundering herd, and the reason the protocol has a `control: drain`
frame with `retry_after_ms`.

---

## Part I — Make it lose messages

**This is the point of the module. Do not skip it.**

First, stop the loss from being an exception. Right now a `group_send` against
a paused Redis raises `TimeoutError` out of `receive_json`, and Channels
responds by closing the connection — which confounds the measurement *and* is
the wrong production behaviour (the message is already committed; killing the
sender's socket does not un-commit it).

`chat/consumers.py`:

```python
from chat.metrics import FANOUT_FAILED       # Counter, add it to metrics.py

        recipients = self._group_size()
        t0 = time.perf_counter()
        try:
            await self.channel_layer.group_send(
                self.group, {"type": "chat.message", "payload": payload})
        except Exception as exc:                        # noqa: BLE001
            # The row is in Postgres and the sender has been acked. Nobody
            # else will ever see it. There is no retry that helps: we do not
            # know which workers missed it, and re-sending would duplicate for
            # the ones that did not.
            FANOUT_FAILED.inc()
            logger.warning("fanout failed for %s: %r", self.group, exc)
        else:
            GROUP_SEND.observe(time.perf_counter() - t0)
            MESSAGES_OUT.inc(recipients)
```

Restart with 8 workers. Then the control run:

```bash
../../07-scale-out-redis-channel-layer/code/loss_test.py --room 9 --fault none
```
**Expected:**
```
publishing 200 messages (20 senders x 10 @ 0.5s), fault=none at t=4.0s for 0.75s

  sent (client-side)   : 200
  acked (server seq)   : 200
  received (other node): 200
  LOST                 : 0   (0.0% of acked)
```

✅ The rig is honest. **Now break it.**

### Failure 1 — a pause. This is what a partition looks like.

```bash
r CONFIG RESETSTAT
../../07-scale-out-redis-channel-layer/code/loss_test.py \
    --room 9 --fault pause --fault-at 4.0 --fault-for 0.75
```

**Expected:**
```
  >>> t= 4.00s  docker pause pulse-redis
  >>> t= 4.75s  docker unpause pulse-redis

  sent (client-side)   : 200
  acked (server seq)   : 200
  received (other node): 171
  LOST                 : 29   (14.5% of acked)
  lost seq ranges      : 5081-5109

  Every one of those was committed to Postgres and acked to its
  sender. The hole is in delivery only, and nothing errored on
  the receiving side. Compare with chat_messages_outbound_total.
```

✅ **29 messages gone. Permanently.** Now look at what the system said about it:

```bash
curl -s localhost:8000/metrics | grep -E 'chat_(messages_outbound|fanout_failed)_total'
docker exec -i pulse-postgres psql -U pulse -d pulse -t -c \
  "SELECT count(*) FROM chat_message WHERE body LIKE 'loss probe%';"
```
**Expected:**
```
chat_messages_outbound_total 34029.0
chat_fanout_failed_total 29.0
      200
```

- **All 200 rows are in Postgres.** The database is perfectly consistent.
- **Every sender got an ack** with a real `id` and a real `seq`. From the
  senders' point of view, all 200 succeeded.
- `chat_fanout_failed_total` caught all 29 — **only because you added it eight
  minutes ago.** Out of the box there is no such metric, and this failure is
  invisible.
- The receiving side logged nothing above INFO. Its worker's `BZPOPMIN` timed
  out, `redis-py` reconnected, and it carried on.

Confirm the client would have noticed, which is the whole reason Module 05 built
gapless sequence numbers:

```bash
k6 run -q --vus 20 -e ROOMS=1 --duration 30s ../../06-load-testing-harness/code/pulse-load.js
```
```
     sequence_gaps..................: 29
```

✅ **The server cannot see the loss. The client can.** That asymmetry is the
entire design argument for `seq`, and it is what Module 10 turns into a
`resume`.

### Failure 2 — a kill. This one is much worse.

```bash
r CONFIG RESETSTAT
../../07-scale-out-redis-channel-layer/code/loss_test.py \
    --room 9 --fault kill --fault-at 4.0 --fault-for 3.0
```

**Expected:**
```
  >>> t= 4.00s  docker kill pulse-redis
  >>> t= 7.00s  docker start pulse-redis

  sent (client-side)   : 200
  acked (server seq)   : 200
  received (other node): 61
  LOST                 : 139   (69.5% of acked)
  lost seq ranges      : 5342-5480
```

```bash
curl -s localhost:8000/metrics | grep chat_fanout_failed_total
```
**Expected — and read it twice:**
```
chat_fanout_failed_total 42.0
```

✅ **139 lost, 42 reported.** The other **97 messages produced no error, no
exception, and no counter increment**, because `group_send` *succeeded*.

Find out why:

```bash
../../07-scale-out-redis-channel-layer/code/layer_probe.py groups
r --scan --pattern 'pulse:group:*' | wc -l
```
**Expected:**
```
no core-layer groups under pulse:group:*
0
```

**The group is gone.** The dev Redis runs `--save "" --appendonly no`
(`infra/compose.dev.yml`, deliberately — Module 08 makes you defend it), so a
restart comes back **empty**. `group_send` then does a `ZRANGE` on a key that
does not exist, gets an empty list, faithfully sends the message to zero
mailboxes, and returns successfully.

**And it never recovers.** `group_add` is called in `connect()`. Every consumer
is already connected. Nothing will ever call it again for the life of those
connections.

```bash
websocat "ws://localhost:8000/ws/room/9/?as=lr0"   # an existing-style client
# send from another terminal: nothing arrives, forever
```

> **This is the worst failure mode in the module**, and it is a property of
> *where the state lives*: the core layer keeps group membership in Redis, so
> Redis's durability policy silently becomes your delivery policy. The Pub/Sub
> layer keeps it in the worker's heap and re-subscribes automatically — which is
> why its `kill` number is 22, not 139.

### The fix: refresh the group registration

`chat/consumers.py`:

```python
GROUP_REFRESH_SECONDS = 300      # << group_expiry (86400); >> a Redis restart


    async def connect(self):
        # ... existing group_add / accept ...
        self._refresh = asyncio.create_task(self._refresh_group())

    async def _refresh_group(self):
        """Re-assert this channel's group membership periodically.

        group_add is a ZADD: idempotent, ~5 us of Redis, and it is the only
        thing that repairs membership after Redis loses it. It also renews
        group_expiry, which matters for connections that outlive 24 hours.
        """
        try:
            while True:
                await asyncio.sleep(GROUP_REFRESH_SECONDS)
                await self.channel_layer.group_add(self.group, self.channel_name)
        except asyncio.CancelledError:
            raise
        except Exception:                                # noqa: BLE001
            logger.warning("group refresh failed for %s", self.group)

    async def disconnect(self, code):
        if hasattr(self, "_refresh"):
            self._refresh.cancel()
        # ... existing group_discard ...
```

Cost, measured:
```
8 workers x 20,000 conns / 300 s = 533 ZADD/s  =  0.4% of Redis's thread
```

**Expected on a re-run:**
```
  LOST                 : 139  -> then delivery resumes when the refresh fires
  time to recovery     : up to 300 s
```

300 seconds of blackout is better than forever and nowhere near good enough. The
sharp version — watching Redis's `run_id` and re-adding within two seconds — is
Task 2 of [`challenge.md`](./challenge.md).

### Record it

```markdown
## Module 07 — channel-layer loss

- Control (no fault):            0 / 200 lost
- docker pause 0.75 s:          29 / 200 lost (14.5%), 29 reported by a metric
                                 we had to add ourselves
- docker kill + restart:       139 / 200 lost (69.5%), only 42 reported,
                                 and delivery NEVER recovers (group ZSET gone)
- Errors surfaced by Channels:   zero in both cases
- Rows in Postgres:              200 / 200 (the database is fine; delivery is not)
- Client-visible:                yes — 29 sequence gaps, detected by seq
- Latency cost of the backplane: +4 ms p50, +20 ms p99
- Horizontal scaling:            1.90x knee for 2 workers, 1.87x for 2 nodes
```

### Why you cannot fix this with retries

The instinct is "retry the `group_send`". It does not work:

- **The sender does not know delivery failed.** On the `kill` path `group_send`
  returned successfully, and "zero members in this group" is indistinguishable
  from the normal state of an empty room.
- **The failure is on the *subscriber* side.** No amount of publisher retry
  reaches a worker whose mailbox key was deleted or whose subscription lapsed.
- **A successful `group_send` guarantees nothing** — it means a message was
  appended to some sorted sets, not that any worker popped one.
- **A blind retry duplicates** for every worker that *did* get it, and you have
  no way to know which.

The problem is not the reliability of the write. It is that **there is no record
a recovering subscriber can catch up from.** That requires a log with cursors,
which is [Module 09](../09-redis-streams-delivery/).

---

## Part J — Use the layer for what it is good at

Route typing indicators through the Pub/Sub layer deliberately. Channels only
auto-listens on the *default* layer, so a second layer needs ten lines:

```python
from channels.layers import get_channel_layer


    async def connect(self):
        # ... default-layer group_add, accept ...
        self.eph = get_channel_layer("ephemeral")
        self.eph_channel = await self.eph.new_channel()
        await self.eph.group_add(self.group, self.eph_channel)
        self._eph_task = asyncio.create_task(self._eph_loop())

    async def _eph_loop(self):
        """Channels drives self.channel_layer for us; a second layer is ours."""
        while True:
            event = await self.eph.receive(self.eph_channel)
            await self.dispatch(event)          # same chat.* -> method routing

    async def _on_typing_start(self, data):
        # At-most-once is CORRECT here: superseded within 3 s, invisible when
        # lost, and it costs zero storage. pulse-protocol-v1.md 3.2 says this
        # traffic MUST NOT be given durable delivery.
        await self.eph.group_send(self.group, {
            "type": "chat.typing", "user": self.user.username})

    async def chat_typing(self, event):
        await self.send(text_data=dumps(envelope(
            "typing.update", self.group, now_ms(), users=[event["user"]])))

    async def disconnect(self, code):
        if hasattr(self, "_eph_task"):
            self._eph_task.cancel()
            await self.eph.group_discard(self.group, self.eph_channel)
        # ... existing cleanup ...
```

Run the identical loss test against typing traffic:

```bash
../../07-scale-out-redis-channel-layer/code/loss_test.py \
    --room 9 --fault pause --fault-for 0.75 --type typing.start
```
**Expected:**
```
  sent                 : 200 typing events
  received             : 168
  LOST                 : 32   (16.0%)
  user-visible impact  : none observed
```

✅ **A slightly *higher* loss rate and a completely different verdict.** Same
mechanism, same Redis, same pause — and it does not matter, because the next
`typing.start` three seconds later repairs the state.

**That contrast is the module's real lesson.** Delivery semantics are not a
property of your infrastructure; they are a property of the traffic, and the
same infrastructure is correct for one kind and negligent for another. A design
review that asks "is this at-least-once?" without asking "for which message
type?" is asking the wrong question.

Confirm the ephemeral layer is doing what you think:
```bash
r PUBSUB CHANNELS 'pulse.eph__group__*'
r INFO stats | grep -E 'pubsub_channels|instantaneous'
```
**Expected:**
```
1) "pulse.eph__group__room.9"
pubsub_channels:1
instantaneous_ops_per_sec:412
```

One Pub/Sub channel per room, one subscription per worker, and the message path
untouched.

---

## What you measured

Record in `apps/pulse/results-07.md`:

| Measurement | Reference | Yours |
|-------------|-----------|-------|
| Cross-worker delivery, 2 / 4 / 8 workers | 100% / 100% / 100% | |
| Redis writes per `group_send`, 200 members / 8 workers | **8** (not 200) | |
| Hop cost, 1 worker, idle loop | +0.9 ms p50 | |
| Hop cost, 1 worker, 44%-busy loop | **+4.0 ms p50**, +20 ms p99 | |
| Worker CPU change (deepcopy removed) | 44% → 41% | |
| Knee, 1 / 2 / 4 / 8 workers | 147k / **285k** / 521k / **441k** | |
| Scaling factor, 2 workers | **1.90×** | |
| Scaling factor, 2 nodes | 1.87× | |
| Redis CPU at the 8-worker knee | **94%** — the new wall | |
| Redis cost per `group_send` | 55 µs + 46 µs × workers | |
| Core vs Pub/Sub knee at 8 workers | 441k vs 1,010k | |
| Lost, `docker pause` 0.75 s | **29 / 200 (14.5%)** | |
| Lost, `docker kill` + restart | **139 / 200, permanent** | |
| Errors Channels raised | **0** | |
| Sequence gaps the client saw | 29 | |
| Typing indicators lost, same fault | 32 / 200, zero impact | |

---

## What you built

```
apps/pulse/
├── pulse/settings.py     ← two channel layers, socket timeouts, capacity 1500
└── chat/consumers.py     ← fanout-failure counting, group refresh, the
                             ephemeral typing path on a second layer
07-scale-out-redis-channel-layer/code/
├── loss_test.py          ← acked minus received, with pause / kill / control
├── layer_probe.py        ← groups, mailboxes, amplification, live watch
└── nginx.conf            ← WebSocket-aware, cookie consistent hash
```

And you established:

- **Redis gets you your other cores.** 100% cross-worker delivery at 2, 4 and 8
  workers, for one settings dict.
- **The hop costs +4 ms p50 — and it is mostly *scheduling*, not Redis.** 0.9 ms
  on an idle loop, 4.0 ms on a busy one. Budget it as a fraction of loop
  headroom, not as a constant.
- **1.90×, not 2×**, from a per-worker fixed receive cost you can name and
  measure.
- **The wall moved rather than vanished.** At eight workers Redis's single
  thread is at 94% and the knee is *lower* than at four. You bought roughly four
  cores' worth of scaling for one network hop.
- **At-most-once is real and it costs 14.5% of your messages** across a
  three-quarter-second partition — with zero errors, a perfectly consistent
  database, and a metric that had to be invented to see it.
- **A Redis restart is far worse than a partition**: 69.5% lost, never
  recovering, because group membership was state you did not know you were
  storing.
- **The same failure applied to typing indicators does not matter at all.**

Now do [`challenge.md`](./challenge.md).

Then: [Module 08 — Redis Internals](../08-redis-internals/), which explains why
one thread was your ceiling, why `KEYS` in a console is an outage, and how to
name your keys today so that Module 18's Cluster migration is a config change
instead of a rewrite.
