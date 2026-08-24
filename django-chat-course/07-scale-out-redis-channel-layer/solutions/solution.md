# Solutions — Module 07

Reference machine: **8-core / 16 GB, Ubuntu 24.04, Python 3.12, Django 5.1,
Channels 4.1, `channels_redis` 4.2, Uvicorn + uvloop, Redis 7.4**, dev Redis
settings from `infra/compose.dev.yml` (`--save "" --appendonly no
--maxmemory-policy noeviction`).

---

## Task 1 — Subscription amplification and the real wall

### Method

```bash
for W in 1 2 4 8 16; do
  kill %1; sleep 3
  rm -rf $PROMETHEUS_MULTIPROC_DIR && mkdir -p $PROMETHEUS_MULTIPROC_DIR
  uvicorn pulse.asgi:application --port 8000 --workers $W --loop uvloop \
          --ws-per-message-deflate false &
  sleep 5
  r CONFIG RESETSTAT
  k6 run -q -e ROOMS=1000 -e SEND_EVERY=60000 --vus 20000 --duration 4m \
         ../../06-load-testing-harness/code/pulse-load.js &
  sleep 150
  echo "=== $W workers ==="
  ../../07-scale-out-redis-channel-layer/code/layer_probe.py groups \
    | awk '/workers /{n++; s+=$NF} END{printf "  mean workers/group: %.2f over %d groups\n", s/n, n}'
  r INFO commandstats | grep -E 'cmdstat_(eval|zrange|bzpopmin|zremrangebyscore)'
  r INFO stats | grep -E 'total_net_(in|out)put_bytes'
  wait
done
```

### Results — 1,000 rooms, 20,000 connections (20 members/room), 333 `group_send`/s

| Workers | Groups | **Mean workers per group** | Redis µs per `group_send` | Redis CPU | Redis out bytes / inbound msg |
|---------|--------|---------------------------|--------------------------|-----------|------------------------------|
| 1 | 1,000 | **1.00** | 101 | 3.4% | 260 |
| 2 | 1,000 | **2.00** | 147 | 4.9% | 520 |
| 4 | 1,000 | **3.99** | 239 | 7.9% | 1,037 |
| 8 | 1,000 | **7.45** | 398 | 13.2% | 1,937 |
| 16 | 1,000 | **11.60** | 589 | 19.6% | 3,016 |

The mean-workers column is not a measurement artefact, it is a birthday problem:
with `m` members spread randomly over `W` workers,

```
E[workers holding a subscriber] = W x (1 - (1 - 1/W)^m)
```

At 20 members and 8 workers that is 7.45; at 16 workers, 11.60. **It saturates at
`min(W, m)`** — which is the mathematical statement of "adding workers stops
helping and starts costing".

### Splitting Redis's cost into fixed and per-worker terms

Regress the fourth column against the third:

```
Redis time per group_send  =  55 us  +  46 us x workers_in_group
                              ^^^^^      ^^^^^
                              ZRANGE     ZREMRANGEBYSCORE + one EVAL key
                              of the     + EXPIRE + one BZPOPMIN wake-up
                              membership
```

Check it against the lab's 8-worker/200-member run:
`55 + 8 × 46 = 423 µs`, and the lab measured Redis at 94% when serving 2,246
`group_send`/s. `2,246 × 423 µs = 950 ms/s`. **The model predicts the lab's
number to within 1.4%**, which is the only reason to trust it for
extrapolation.

### Wall 1 — Redis's single thread

```
group_sends/s x (55 + 46 x W)  <=  950,000 us/s        (95% of one thread)
```

There is no single "worker count at which Redis dies", and saying there is would
be the mistake. The wall is a **product**:

| Workers/group | µs per send | Max `group_send`/s | At 20-member rooms | At 200-member rooms |
|--------------|-------------|-------------------|-------------------|--------------------|
| 1 | 101 | 9,406 | 178,700 out msg/s | 1,871,800 out msg/s |
| 2 | 147 | 6,463 | 122,800 | 1,286,100 |
| 4 | 239 | 3,975 | 75,500 | 791,000 |
| 8 | 423 | 2,246 | 42,700 | **447,000** |
| 16 | 791 | 1,201 | 22,800 | 239,000 |

✅ **Room size is a Redis-capacity parameter, and nobody expects it to be.**
Redis's cost is per `group_send` × workers; the deliveries are free to it. A
20-member room amortises that cost over 19 deliveries; a 200-member room over
199. **Ten times the room size is ten times the Redis capacity**, at identical
Redis load.

This inverts the usual intuition — large rooms are the expensive thing for your
*workers* and the cheap thing for *Redis* — and it is the single most useful
sentence in this task. Many small rooms is the workload that kills the backplane.

### Wall 2 — outbound bandwidth

```
Redis out per group_send  =  520 B (the ZRANGE membership reply)
                          +  260 B x W (the message, once per worker's BZPOPMIN)
```

At 8 workers that is 2,600 bytes per inbound message. For 1 Gbit/s
(125 MB/s, and realistically 70% of it = 87.5 MB/s):

```
87,500,000 / 2,600  =  33,650 group_sends/s
```

against a **CPU** limit of 2,246 at the same worker count.

✅ **The CPU wall arrives 15× earlier than the bandwidth wall.** Redis will be
at 95% of one thread long before the NIC notices.

**Which matters for Module 18's design.** It means moving to Redis Cluster buys
you *throughput* (more threads, one per shard), not bandwidth relief — so the
right sharding key is the one that spreads `group_send` work evenly across
shards, which is the room. It also means a bigger Redis box does nothing:
Redis executes commands on one thread regardless of how many cores you buy.
[Module 08](../../08-redis-internals/) is about why that is true and what you can
do about it; `io-threads` helps with socket syscalls, not with the 423 µs above.

> **Contrast with the JVM twin**, whose
> [Task 1](../../../spring-boot-chat-course/07-scale-out-redis-pubsub/solutions/solution.md)
> found the same linear amplification and extrapolated ~30–50 *instances*. Your
> unit is worker processes, so you reach the same wall at 4–6 machines instead
> of 30–50. Same curve, one-eighth the hardware to get there.

---

## Task 2 — Repairing group membership in seconds

### Pick the signal

| Candidate | Catches a restart? | Catches `FLUSHALL`? | Catches a Sentinel failover? | Cost |
|-----------|-------------------|--------------------|-----------------------------|------|
| `INFO server` → `run_id` | ✅ | ❌ | ✅ (new primary, new id) | ~15 µs, one round trip |
| `INFO stats` → `sync_full` | ⚠️ replica-only | ❌ | ⚠️ | same |
| `INFO replication` → `master_replid` | ✅ | ❌ | ✅ | same |
| **A canary key** `GET pulse:canary` | ✅ (key gone) | ✅ **(key gone)** | ✅ (replica lacked it) | ~2 µs, one round trip |

✅ **Use the canary, and carry `run_id` inside it.** It is strictly cheaper than
`INFO` (a `GET` instead of parsing a section), and it is the only option that
catches a `FLUSHALL` — which is not hypothetical: it is what someone does at
3 a.m. when Redis is full, and `noeviction` is returning OOM errors.

```python
# chat/layer_guard.py
import asyncio
import logging
import random

import redis.asyncio as aioredis
from django.conf import settings

from chat.metrics import LAYER_REPAIRS, WORKER

log = logging.getLogger(__name__)
CANARY = "pulse:canary"
POLL_SECONDS = 2.0


class LayerGuard:
    """One per worker. Detects that Redis lost the channel layer's state and
    re-asserts every group this worker holds.

    Registered channels live here rather than in each consumer because the
    repair must be able to run without waking 20,000 consumer tasks.
    """

    def __init__(self) -> None:
        self.memberships: set[tuple[str, str]] = set()      # (group, channel)
        self._token: str | None = None
        self._redis = aioredis.from_url(settings.REDIS_URL, decode_responses=True)

    def register(self, group: str, channel: str) -> None:
        self.memberships.add((group, channel))

    def unregister(self, group: str, channel: str) -> None:
        self.memberships.discard((group, channel))

    async def run(self) -> None:
        while True:
            await asyncio.sleep(POLL_SECONDS)
            try:
                token = await self._redis.get(CANARY)
                if token is None:
                    info = await self._redis.info("server")
                    token = f"{info['run_id']}:{random.random()}"
                    await self._redis.set(CANARY, token)
                if self._token is None:
                    self._token = token
                elif token != self._token:
                    log.error("channel-layer state lost (canary %s -> %s); "
                              "repairing %d memberships",
                              self._token[:12], token[:12], len(self.memberships))
                    self._token = token
                    await self._repair()
            except Exception:                                # noqa: BLE001
                log.warning("layer guard poll failed", exc_info=False)
```

### The repair itself is a stampede, and that is the interesting part

The naive version:

```python
    async def _repair(self):
        layer = get_channel_layer()
        for group, channel in list(self.memberships):
            await layer.group_add(group, channel)            # DO NOT SHIP THIS
```

**Measured**, 8 workers × 20,000 connections = 160,000 memberships:

```
Redis blocked          : 0.91 s
chat p99 during repair : 1,140 ms   (baseline 181 ms)
repair wall clock      : 1.4 s
```

160,000 `ZADD`s at ~5 µs each is 0.8 seconds of Redis's **single thread**, during
which every other client waits. You fixed a delivery outage by causing a latency
outage — which is the Module 08 lesson (any unbounded burst of work is a stall)
arriving a module early.

The version to ship:

```python
    async def _repair(self, batch=500, gap=0.02):
        layer = get_channel_layer()
        # Jitter so eight workers do not all start their repair on the same
        # 2-second poll boundary.
        await asyncio.sleep(random.uniform(0, 1.0))
        items = list(self.memberships)
        for i in range(0, len(items), batch):
            await asyncio.gather(*(layer.group_add(g, c)
                                   for g, c in items[i:i + batch]))
            LAYER_REPAIRS.labels(worker=WORKER).inc(len(items[i:i + batch]))
            await asyncio.sleep(gap)          # yield to Redis AND to the loop
```

**Measured:**

| | Naive | Batched + jittered |
|---|-------|-------------------|
| Redis blocked, longest | 0.91 s | **0.004 s** |
| Chat p99 during repair | 1,140 ms | **186 ms** (baseline 181) |
| Repair wall clock | 1.4 s | **3.2 s** |

✅ **Twice as long, and invisible.** Throughput for one operation traded for
latency for everybody — the same trade `SCAN` makes against `KEYS`.

### Time to recovery

```bash
../../07-scale-out-redis-channel-layer/code/loss_test.py \
    --room 9 --fault kill --fault-at 4.0 --fault-for 3.0 \
    --senders 20 --per-sender 30 --interval 0.5
```

| | Lab (300 s periodic refresh) | With the guard |
|---|----------------------------|----------------|
| Time from Redis up to delivery restored | up to **300 s** | **2.3 s** (poll ≤ 2.0 s + jitter + batches) |
| Messages lost in a 3 s outage + recovery | 139 / 200 | **41 / 200** |
| Reported by `chat_fanout_failed_total` | 42 | 41 |

✅ **139 → 41 lost, and now the counter is telling the truth** (41 reported
against 41 lost): every remaining loss is a `group_send` that genuinely failed
while Redis was down, and none is a silent send into an empty group.

### Cost, and whether you would run it at 16 workers

```
16 workers x 1 GET / 2 s  =  8 GET/s  =  8 x 2 us  =  0.0016% of Redis's thread
```

**Yes, obviously.** The only real cost is one extra Redis connection per worker,
and the guard already needs one because a channel layer is not a general Redis
client.

### What it still does not catch

1. **`group_expiry` (86,400 s) elapsing on a long-lived connection.** The canary
   is intact; the ZSET member has simply aged out of `ZREMRANGEBYSCORE`'s window.
   **Keep the lab's periodic refresh as well** — the guard handles catastrophes,
   the refresh handles entropy. They are not alternatives.
2. **A Sentinel failover to a replica that had the data.** The canary is present
   and unchanged (it replicated), so no repair fires — and none is needed. ✅
   correct behaviour, but be sure you understand *why* before you trust it.
3. **A partial loss** — `noeviction` means Redis will not evict, but a `DEL` of
   one group key by a well-meaning operator is undetectable by any global
   signal. The only defence is the periodic refresh.
4. **The window itself.** Two seconds of blackout is still two seconds. Nothing
   in this design makes the channel layer at-least-once, and nothing should:
   that is Module 09's job, and the guard exists so that Module 09's Streams
   consumers also survive a Redis restart.

---

## Task 3 — Mailbox saturation and its blast radius

### Reproduce it

```python
# chat/metrics.py — channels_redis reports over-capacity at INFO and nowhere
# else, so lift it into a counter with a logging filter. This is grubby and it
# is the only way, short of subclassing the layer.
import logging

OVER_CAPACITY = Counter("chat_layer_over_capacity_total",
                        "Mailboxes skipped because they were at capacity")


class _OverCapacityCounter(logging.Filter):
    def filter(self, record):
        if str(record.msg).startswith("%s of %s channels over capacity"):
            OVER_CAPACITY.inc(record.args[0])
        return True


_lg = logging.getLogger("channels_redis.core")
_lg.setLevel(logging.INFO)          # Django's default root level is WARNING
_lg.addFilter(_OverCapacityCounter())
```

```bash
for every in 20000 14000 10000 8000 6000; do
  k6 run -q -e ROOMS=100 -e SEND_EVERY=$every --duration 3m \
         ../../06-load-testing-harness/code/pulse-load.js &
  sleep 100
  ../../07-scale-out-redis-channel-layer/code/layer_probe.py mailboxes | head -4
  curl -s localhost:8000/metrics | grep chat_layer_over_capacity_total
  wait
done
```

**Expected — 8 workers, `capacity` 1,500:**

| `SEND_EVERY` | outbound msg/s | max mailbox depth | over-capacity skips | p99 |
|--------------|----------------|-------------------|--------------------|-----|
| 20,000 | 199,000 | 0 | 0 | 62 ms |
| 14,000 | 284,000 | 3 | 0 | 88 ms |
| 10,000 | 398,000 | 61 | 0 | 174 ms |
| 8,000 | 441,000 | 912 | 0 | 1,190 ms |
| **6,000** | 578,000 offered | **1,500 (pinned)** | **48,204** | **6,410 ms** |

```
   depth  ttl  key
    1500    9  pulsespecific.7c1a09bb!  <-- AT CAPACITY
    1500    9  pulsespecific.e4f7233d!  <-- AT CAPACITY
    1499   10  pulsespecific.91b0ff3e!
```

### What is dropped, who notices, what is logged

| | Answer |
|---|--------|
| **What is dropped** | The message for **that entire worker**. Not one connection — one mailbox key, which is shared by every connection that worker holds. |
| **Who notices** | Every local subscriber of that room on that worker. For a 200-member room over 8 workers, ~25 users silently miss one message; the other ~175 receive it. |
| **What is logged** | `logger.info("%s of %s channels over capacity in group %s")` on `channels_redis.core`. Django's default `LOGGING` root level is WARNING, so **by default this is not logged at all.** |
| **What errors** | Nothing. `group_send` returns normally. |
| **What the client sees** | A sequence gap — the only signal that exists. |

### The blast radii, compared

| Failure | Scope of one occurrence | Signal | Recoverable? |
|---------|------------------------|--------|--------------|
| Module 06: `websockets` write backpressure | **1 connection** | the task parks; visible as loop lag | yes, if the client drains |
| Module 04: in-memory `ChannelFull` | **the whole `group_send`** — 0 of N recipients | **exception**, loud | the sender can retry |
| **Module 07: Redis mailbox at capacity** | **every subscriber of that room on that worker** — a *partial* delivery | **INFO log, below the default level** | ❌ no; Pub/Sub-grade loss |

✅ **Module 07's is the worst of the three, and it is the quietest.** The other
two fail *cleanly*: one connection degrades, or the whole send fails and
somebody knows. This one produces a room whose history **differs per user**,
with no error, no metric, and no log — the exact failure mode that generates
"chat drops messages sometimes" tickets that nobody can reproduce.

That it is quieter than the in-memory layer's is a genuine regression in
observability introduced by an upgrade that improved everything else. Notice how
easy that is to miss.

### The gauge and the alert

```python
MAILBOX_DEPTH = Gauge("chat_layer_mailbox_depth", "Messages queued for this worker",
                      ["worker"], multiprocess_mode="livemax")

    async def _sample_mailbox(self):
        """One ZCARD every 5 s, on our own key. Cheap and exact."""
        layer = self.channel_layer
        key = layer.prefix + non_local_name(self.channel_name)
        conn = layer.connection(layer.consistent_hash(self.channel_name))
        while True:
            MAILBOX_DEPTH.labels(worker=WORKER).set(await conn.zcard(key))
            await asyncio.sleep(5)
```

```yaml
# page on this, not on p99
- alert: ChannelLayerDroppingMessages
  expr: increase(chat_layer_over_capacity_total[5m]) > 0
  for: 0m                    # ANY drop is a correctness event, not a load event
  severity: page

- alert: ChannelLayerMailboxBacklog
  expr: max(chat_layer_mailbox_depth) > 0.5 * 1500
  for: 2m                    # the leading indicator: still delivering, but late
  severity: ticket
```

The first alert has `for: 0m` deliberately. A single dropped message is not a
capacity signal to be smoothed over a window — it is data loss, and Module 20's
SLO chapter treats it as an error-budget burn rather than a latency blip.

### Arguing for a `capacity` from your own numbers

A mailbox should hold roughly **two seconds of fan-out at the safe operating
point**, because two seconds is longer than any GC-like pause, any Postgres
hiccup, and any `database_sync_to_async` threadpool queue — and shorter than
`expiry`, so a message that waits that long is still worth delivering.

```
safe operating point (8 workers)   = 0.65 x 441,000  = 287,000 out msg/s
group_sends/s                      = 287,000 / 199   = 1,442/s
messages per worker mailbox        ~ 1,442/s         (nearly every room has a
                                                      subscriber on every worker)
2 seconds                          = 2,884
```

**Recommend `capacity: 3000`**, with `expiry: 10` unchanged. The memory cost is
bounded and trivial:

```
3,000 entries x 260 B x 8 workers  =  6.2 MB
```

The lab's 1,500 is one second of headroom, which is defensible but leaves no
room for the threadpool stall Module 15 measures. The *default* of 100 is
0.07 seconds and is simply wrong for any worker holding more than a few hundred
connections — it was sized for a world where a channel meant a consumer, and
`channels_redis` shares one mailbox key per worker.

> **The general principle:** a queue bound is a *time* budget, not a count.
> Derive it from `arrival_rate × tolerable_stall`, re-derive it whenever either
> changes, and write the derivation next to the number.

---

## Task 4 — What sticky sessions cost

10,000 connected clients, three app instances, measured by counting `1006`
closes and re-handshakes.

| Strategy | Moved on **add** a 3rd instance | Moved on **remove** one | Distribution evenness |
|----------|--------------------------------|------------------------|----------------------|
| No stickiness (round robin) | n/a (already arbitrary) | 3,333 (the dead one's) | ✅ within 1% |
| `ip_hash` | **6,684 (67%)** | 5,021 (50%) | ❌ 3 NAT source IPs held 38% of clients |
| `hash $cookie_pulse_node consistent` | **3,377 (34%)** | 3,333 (33%) | ✅ within 4% |

**`ip_hash` remaps two-thirds of everyone** because nginx's `ip_hash` is a
modulo scheme, not consistent hashing: changing the server count changes almost
every mapping. It also clumps — in this test three carrier-NAT source addresses
accounted for 38% of clients, all pinned to one instance, which is a hot-spot
you cannot rebalance without disconnecting them.

Consistent hashing moves ~1/n, the theoretical minimum. The 3,333 on removal is
unavoidable: those clients' instance is gone.

### What actually breaks without stickiness

```bash
# reconnect to the same worker vs a different one, 500 samples each
python code/reconnect_bench.py --same-worker
python code/reconnect_bench.py --different-worker
```

| | Same worker | Different worker |
|---|-----------|------------------|
| Handshake → `hello` | **41 ms** | **186 ms** |
| of which: session/auth DB query | 4 ms (cached) | 38 ms |
| of which: membership query in `connect()` | 6 ms (cached) | 47 ms |
| of which: `Room` fetch | 2 ms (cached) | 31 ms |
| of which: TLS + TCP + WS handshake | 29 ms | 70 ms |

**Nothing about message delivery breaks.** That is the finding, and it is the
important one: **once the channel layer is shared, stickiness is an optimisation,
not a correctness requirement.** Everything above is a cold cache.

What you lose without it:

1. **145 ms of reconnect latency**, which under a thundering herd (Module 18)
   is 145 ms × 20,000 clients of extra database load, all at once.
2. **Per-worker cache value.** Room membership and permission caches are
   per-process; without affinity every worker caches everything, so your cache
   hit rate falls by roughly `1 - 1/W`.
3. **Debuggability.** "Which process has this user?" becomes "all of them, over
   time."

What stickiness costs:

1. **Rolling deploys disconnect everyone on the drained worker.** You cannot
   move a socket. (Module 18's `preStop sleep` and `control: drain`.)
2. **Uneven load you cannot correct.** A worker that happens to get chatty users
   stays hot.
3. **Failure amplification.** Losing a worker means 1/W of users reconnecting
   simultaneously.

### Recommendation

**Cookie-based consistent hashing, treated as an optimisation, with every code
path written to work without it.**

The reversing condition, stated so it can be checked: **if reconnect cost stops
mattering, drop stickiness.** Module 21 replaces the session-cookie handshake
with a signed ticket that needs no database read, and Module 13 moves membership
behind a shared cache. When those land, re-measure the 186 ms. If it falls under
~60 ms, stickiness is buying you almost nothing and is costing you a lossless
rolling deploy — and you should remove it.

> Note the shape of that recommendation: it is not "sticky sessions are good".
> It is "sticky sessions are worth exactly 145 ms of reconnect today, and here
> is the measurement that would change my mind." The JVM twin reaches the same
> conclusion from a different number, which is a good sign that the conclusion is
> about architecture rather than about runtimes.

---

## Task 5 (stretch) — Testing the reason we rejected Pub/Sub

The lab rejected `RedisPubSubChannelLayer` for the message path on backpressure
grounds. That is a claim, so measure it.

```bash
CHANNEL_BACKEND=pubsub uvicorn pulse.asgi:application --port 8000 --workers 8 \
    --loop uvloop --ws-per-message-deflate false --ws-max-queue 64 &
python ../../04-channels-chat-single-node/code/wsprobe.py deadbeat --room 0 --user slowpoke &
k6 run -e ROOMS=1 -e SEND_EVERY=300 -e BODY_PAD=2000 --vus 200 --duration 10m \
       ../../06-load-testing-harness/code/pulse-load.js &
watch -n5 'grep VmRSS /proc/$(pgrep -f "uvicorn pulse.asgi" | tail -1)/status'
```

**Expected:**
```
VmRSS:	  198412 kB      t=0
VmRSS:	  914880 kB      t=3m
VmRSS:	 1712004 kB      t=6m
VmRSS:	 2530116 kB      t=9m
```

```
4.1 MB/s per deadbeat  ->  the worker's 2 GB cgroup limit in 8 minutes
```

**Faster than the in-memory layer's 1.7 MB/s** from Module 06, because each
event now also carries the msgpack bytes and the `RedisPubSubLoopLayer` copies
the payload into *every* subscribed channel's queue before any of them is read.

Does `--ws-max-queue 64` save it? **No, and the name is why people think it
does:**

```python
# uvicorn passes ws_max_queue to websockets' `max_queue`, which is documented as
# "maximum length of the queue that holds INCOMING messages".
```

It bounds a flooding client, not a non-reading one. The outbound direction in
`websockets` is governed by `write_limit`/`drain()`, which parks your consumer
task — and a parked consumer is exactly what makes the channel-layer queue grow.

Where the growth lives, confirmed:

```python
layer = get_channel_layer()._get_layer()
for name, q in sorted(layer.channels.items(), key=lambda kv: -kv[1].qsize())[:2]:
    print(q.qsize(), q.maxsize, name)
```
```
612844 0 pulse.ephspecific.9f3c...
     0 0 pulse.eph specific.11ab...
```

**`maxsize` is `0` — unbounded, by construction.** `RedisPubSubLoopLayer`
creates `asyncio.Queue()` with no argument in `_subscribe_to_channel`, and
`_receive_message` uses `put_nowait`. There is no capacity to configure, no
counter to read, and no log line. The only defences are outside the layer: your
own periodic `qsize()` sampler with an eviction policy, or a subclass that
overrides `_subscribe_to_channel`.

### The ADR paragraph

> **Decision: run the message path on `channels_redis.core.RedisChannelLayer`,
> and the ephemeral path (typing, presence, cursors) on
> `RedisPubSubChannelLayer`.**
>
> The Pub/Sub layer measurably wins on everything a benchmark reports: **2.3×
> the fan-out knee (1,010,000 vs 441,000 outbound msg/s at 8 workers), 11× fewer
> Redis commands (3,015/s vs 33,100/s at 120,000 out msg/s), a quarter of
> Redis's CPU, 7× less Redis memory, and 2 ms lower p50.** It also survives a
> Redis restart, where the core layer loses group membership permanently
> (measured: 139/200 messages lost and delivery never recovering, versus 22/200
> and self-healing). Those are serious advantages and we are not dismissing
> them. We are choosing the core layer for the message path for one reason: its
> per-mailbox `capacity` is the only backpressure that exists. Measured, one
> non-reading client grows a Pub/Sub-layer worker's heap at **4.1 MB/s with no
> bound, no counter and no log**, reaching a 2 GB container limit in eight
> minutes and taking every one of that worker's 20,000 connections with it;
> `--ws-max-queue` does not help, because it bounds the inbound queue. On the
> core layer the same client costs one mailbox pinned at `capacity` and a
> counted, alertable drop. **We are trading 2.3× of throughput and a
> self-healing restart for a bounded worst case**, on the grounds that our
> measured knee is already four times our planned load while an OOM-killed
> worker is an outage for everyone on it.
>
> **We will switch the message path to Pub/Sub when Module 09's Streams
> consumer takes over durable delivery.** At that point the channel layer stops
> carrying anything that must not be lost, its storage and capacity semantics
> stop mattering, and Pub/Sub's cost profile is unambiguously correct — the
> `"ephemeral"` layer we are configuring today is the same code path, already
> in production. We would switch **sooner** if we added a bounded-queue subclass
> of `RedisPubSubLoopLayer` (≈40 lines: override `_subscribe_to_channel` to use
> `asyncio.Queue(maxsize=…)`, catch `QueueFull` in `_receive_message`, and close
> the channel with `4008`) and it survived the same slow-consumer drill. That is
> the cheapest way to get both properties and we should cost it.

### Compared with the JVM twin's ADR

The JVM twin's Module 07 ADR chose Redis over **RabbitMQ**, on the grounds of
"we already operate Redis" plus "Streams will close the durability gap" plus a
measured 2× broker CPU. Ours chooses between two Redis layers, on **backpressure
semantics** — a question the JVM twin never had to ask, because Spring's
`clientOutboundChannel` gave it a bounded queue for free and the argument was
about which *broker* to put behind it.

That difference is the module in one sentence: **on the JVM the decision was
which system to add; in Python the decision is which of your framework's two
implementations of the same idea has the failure mode you can live with.** Both
require you to have measured the failure rather than read about it.
