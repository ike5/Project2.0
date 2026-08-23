# Solutions — Module 09

---

## Task 1 — Dead-lettering poison messages

An entry that always raises during `persist_idempotent` or `send_json` never gets
acked, sits in the PEL, and is reclaimed forever. Detect it by delivery count and
quarantine it.

```python
MAX_DELIVERIES = 5

async def _process_and_ack(self, room_id, key, entry_id, fields):
    try:
        envelope = json.loads(fields["payload"])
        created = await persist_idempotent(envelope)
        if not created:
            _duplicates.inc()
        else:
            for sub in registry.subscribers(room_id):
                await sub.send_json(envelope)
            _delivered.inc()
        await fanout.redis.xack(key, self.group(), entry_id)
    except Exception as e:
        deliveries = await self._delivery_count(key, entry_id)
        if deliveries >= MAX_DELIVERIES:
            await self._dead_letter(room_id, key, entry_id, fields, e, deliveries)
        else:
            log.warning("delivery %s failed (attempt %d) for room %s",
                        entry_id, deliveries, room_id, exc_info=True)

async def _delivery_count(self, key, entry_id) -> int:
    pending = await fanout.redis.xpending_range(
        key, self.group(), min=entry_id, max=entry_id, count=1)
    return pending[0]["times_delivered"] if pending else 1

async def _dead_letter(self, room_id, key, entry_id, fields, cause, deliveries):
    dlq = dict(fields)
    dlq.update({
        "original_id": entry_id,
        "deliveries": str(deliveries),
        "error": f"{type(cause).__name__}: {cause}",
        "failed_at": str(now_ms()),
        "worker": WORKER_ID,
    })
    await fanout.redis.xadd(f"room:{{{room_id}}}:dlq", dlq, maxlen=1000, approximate=True)
    # Ack the original ONLY after the DLQ write succeeds. If the DLQ write fails
    # we leave it pending and try again — losing it silently is the one outcome
    # we must not allow.
    await fanout.redis.xack(key, self.group(), entry_id)
    _dead_lettered.inc()
    log.error("DEAD LETTER: %s in room %s after %d attempts", entry_id, room_id, deliveries)
```

Prove it:
```bash
export PULSE_POISON_BODY="ALWAYS_FAIL"    # persist_idempotent raises on this body
./code/publish.sh room.13 "ALWAYS_FAIL"
sleep 180                                  # 5 attempts × 30s claim interval
r XLEN 'room:{13}:dlq'
r XRANGE 'room:{13}:dlq' - + COUNT 1
r XPENDING 'room:{13}:stream' node-a-0
```
**Expected:**
```
(integer) 1
1) 1) "1735689800456-0"
   2)  1) "payload"      2) "{\"v\":1,\"type\":\"message.new\",...}"
       3) "original_id"  4) "1735689700123-0"
       5) "deliveries"   6) "5"
       7) "error"        8) "DeliveryException: ALWAYS_FAIL"
       9) "failed_at"   10) "1735689800000"
      11) "worker"      12) "node-a-0"
1) (integer) 0
```
✅ Quarantined, PEL clean, full context preserved.

### Choosing N

N=5, derived rather than guessed.

**Lower bound — how many retries does a *transient* failure need?** Measured
causes of delivery exceptions in the load tests:

| Cause | Resolves within | Attempts needed |
|-------|----------------|-----------------|
| `send_json` on a socket mid-close | < 1 s | 1 |
| Redis reconnect in flight | 2–5 s | 1 |
| `database_sync_to_async` threadpool exhausted | 5–30 s | 1–2 |
| Postgres connection pool exhausted | 5–30 s | 1–2 |

With a 30-second claim interval, **N=3 covers 90 seconds of transient trouble**,
which exceeds every observed transient cause. N=5 gives 150 seconds of margin.

**Upper bound — what does a retry cost?**
```
1 poison entry × 1 retry / 30s × 8 workers = 16 wasted deliveries/minute
```
Negligible for one entry. But a **poison *class*** — a bad deploy where every v2
envelope raises on v1 workers — is thousands of entries × N retries, and the
retries themselves become the outage. N must be small enough that a systemic
failure drains to the DLQ quickly rather than looping.

**N=5.** Below 3 you'd DLQ recoverable messages during a normal threadpool blip;
above ~8 a systemic poison event spends too long thrashing.

> **Add a circuit breaker on top.** If the DLQ rate exceeds ~1% of throughput,
> stop retrying entirely and fail the worker's readiness probe (Module 07's
> policy). Individual poison messages are a data problem; a poison *rate* is a
> deploy problem, and the response is to stop taking traffic, not to keep
> retrying.

---

## Task 2 — Size the replay window from data

### Measure disconnect durations

Record the gap between a socket's `disconnect` and the same user's next
`connect`:

```python
# in ChatConsumer
async def disconnect(self, code):
    _disconnected_at[self.user.id] = time.time()
    ...

async def connect(self):
    was = _disconnected_at.pop(self.scope["user"].id, None)
    if was is not None:
        reconnect_gap.observe(time.time() - was)
    ...
```

**Expected, over a 30-minute run with induced network churn:**

| Percentile | Gap |
|-----------|-----|
| p50 | 1.2 s |
| p90 | 4.8 s |
| p99 | 31 s |
| p99.9 | **186 s** |
| max | 1,840 s (a laptop that was closed) |

### Message rate per room

| Percentile | msg/s |
|-----------|-------|
| p50 | 0.3 |
| p90 | 2.1 |
| p99 | **14.0** |
| max | 61 |

### The calculation

Cover p99.9 of disconnects (186 s), rounded to **5 minutes** for margin:

```
quiet room (p50, 0.3 msg/s):   0.3 × 300 =     90 entries
busy room  (p99, 14 msg/s):     14 × 300 =  4,200 entries
extreme    (max, 61 msg/s):     61 × 300 = 18,300 entries
```

**`MAXLEN 10000` is simultaneously 100× too generous for a quiet room and 45%
too small for the busiest one.** That's the case against a count-based bound.

### `MINID` implementation

Run it from a periodic task, not on every `XADD` (which would put the trim on the
hot path):

```python
REPLAY_WINDOW_S = 300

class StreamFanout:
    async def append(self, room_id, envelope):
        payload = json.dumps(envelope, separators=(",", ":"))
        # MAXLEN as a hard safety cap so one pathological room can't eat all
        # memory; MINID (below) does the real work.
        return await self.redis.xadd(
            stream_key(room_id), {"payload": payload}, maxlen=50_000, approximate=True)


async def trim_by_age_forever():
    while True:
        cutoff = int((time.time() - REPLAY_WINDOW_S) * 1000)
        for room_id in registry.active_rooms():
            await fanout.redis.xtrim(stream_key(room_id), minid=cutoff, approximate=True)
        await asyncio.sleep(60)
```

### Measured difference

| Room type | `MAXLEN ~ 10000` | `MINID ~ 5min` | Change |
|-----------|-----------------|----------------|--------|
| Quiet (0.3 msg/s) | 10,214 / 6.1 MB | **94 / 61 KB** | **−99%** |
| Busy (14 msg/s) | 10,214 / 6.1 MB | **4,238 / 2.6 MB** | −57% |
| Extreme (61 msg/s) | 10,214 / 6.1 MB (**window truncates to 2.8 min**) | 18,401 / 11.2 MB | +84% |

**Total for 1,000 rooms** at the measured distribution:
```
MAXLEN 10000:  6.1 GB
MINID 5min:    412 MB          -- 15× less
```

✅ **15× less memory, *and* the busiest rooms now get the full 5-minute window
they previously didn't.** Count-based trimming penalizes exactly the rooms that
need the buffer most. Keep `MAXLEN 50000` as a hard cap so a single runaway room
can't exhaust Redis — belt and braces, with `MINID` doing the routine work.

---

## Task 3 — Trimmed but unacked

```bash
r XADD 'room:{14}:stream' '*' payload 'a'
r XADD 'room:{14}:stream' '*' payload 'b'
r XGROUP CREATE 'room:{14}:stream' g 0
r XREADGROUP GROUP g c1 COUNT 10 STREAMS 'room:{14}:stream' '>'   # both now pending
r XTRIM 'room:{14}:stream' MAXLEN 0                                # delete both entries
r XLEN 'room:{14}:stream'
r XPENDING 'room:{14}:stream' g
```
**Expected:**
```
(integer) 0
1) (integer) 2                       <-- PEL still references deleted entries
2) "1735689900123-0"
3) "1735689900456-0"
4) 1) 1) "c1"
      2) "2"
```

✅ **The stream is empty but the PEL says two entries are pending.** They can
never be delivered — they don't exist. Left alone, this PEL entry is permanent.

```bash
sleep 1
r XAUTOCLAIM 'room:{14}:stream' g c2 0 0 COUNT 10
```
**Expected:**
```
1) "0-0"
2) (empty array)                     <-- nothing claimable
3) 1) "1735689900123-0"              <-- THE DELETED-IDS LIST
   2) "1735689900456-0"
```

**That third value is the entries `xautoclaim` removed from the PEL because they
no longer exist in the stream** (Redis 7+). Redis cleans up, but only if you
*call* `xautoclaim` — and you must not treat an empty claimed list as "nothing to
do."

### The consumer fix

redis-py returns the deleted-ids list as the third element of the tuple. Count
it:

```python
async def _claim_abandoned(self, room_id, key):
    cursor = "0-0"
    while True:
        cursor, entries, deleted = await fanout.redis.xautoclaim(
            key, self.group(), WORKER_ID,
            min_idle_time=CLAIM_MIN_IDLE_MS, start_id=cursor, count=100)
        for entry_id, fields in entries:
            await self._process_and_ack(room_id, key, entry_id, fields)
        if deleted:
            # entries trimmed before they were acked. NOT decoration: a nonzero
            # rate means your replay window is shorter than your processing time,
            # and you are silently losing messages. Alert on it.
            _trimmed_unacked.inc(len(deleted))
            log.warning("%d pending entries in room %s were trimmed before ACK — "
                        "replay window is shorter than processing time",
                        len(deleted), room_id)
        if cursor == "0-0":
            break
```

Two things this gets right that most implementations don't:

1. **`xautoclaim` is paginated.** A single call with `count=100` on a 5,000-entry
   PEL returns 100 and a non-zero cursor. Calling it once per 30-second sweep
   means a large PEL takes 25 minutes to drain. Loop until the cursor wraps to
   `0-0`.
2. **The `_trimmed_unacked` metric is an alarm, not a curiosity.** A non-zero
   rate means entries are being trimmed before they're acked — your replay window
   is shorter than your worst-case processing time. Alert on it.

Verify the PEL is clean:
```bash
r XPENDING 'room:{14}:stream' g
```
```
1) (integer) 0
```

---

## Task 4 — Ack ordering, measured

```python
ACK_FIRST = os.environ.get("PULSE_ACK_BEFORE_PROCESS") == "1"

async def _process_and_ack(self, room_id, key, entry_id, fields):
    if ACK_FIRST:
        await fanout.redis.xack(key, self.group(), entry_id)
        await self._deliver(room_id, fields)
    else:
        await self._deliver(room_id, fields)
        await fanout.redis.xack(key, self.group(), entry_id)
```

`kill -9` the worker mid-batch, 20 times each, 100 messages per run:

| | Ack **before** process | Ack **after** process |
|---|----------------------|----------------------|
| Runs | 20 | 20 |
| Messages sent | 2,000 | 2,000 |
| **Lost** | **151 (7.6%)** | **0** |
| **Duplicated** | 0 | **168 (8.4%)** |
| Duplicates that reached a client twice | 0 | **0** |
| Rows in Postgres | 1,849 | **2,000** |
| Net correctness | ❌ 151 messages gone | ✅ complete |

### Reading it

Ack-before-process lost 7.6% of messages, and the loss is **invisible**: the PEL
is empty, `XPENDING` is 0, every dashboard is green, and 151 messages simply
never existed.

Ack-after-process duplicated 8.4% — and **zero of those duplicates reached a
client**, because `persist_idempotent` returned `created=False` (the
`get_or_create` found the existing row), which suppressed the broadcast. The
duplication is entirely absorbed.

### Recommendations by message type

| Message type | Ordering | Why |
|--------------|----------|-----|
| **Chat messages** | **Ack after** | Loss is a permanent hole in history. Duplicates are free — `client_id` absorbs them. |
| **Read receipts** | **Ack before** | They're monotonic (`read.upto seq=50` subsumes `seq=40`), so a lost one self-heals on the next receipt, usually within seconds. Not worth the PEL bookkeeping — and Module 10 keeps them off Streams entirely. |
| **Typing indicators** | Not on a stream at all | Channel layer (`group_send`). Storage is waste. |
| **Membership changes** | **Ack after** | A missed "you were removed" is a security bug. |
| **Presence** | Not on a stream | Channel layer + TTL (Module 11). |

> **The decision rule:** ack-after when losing the message is worse than
> processing it twice. Ack-before when the message is *self-superseding* — when a
> later message makes the lost one irrelevant. Most chat traffic is the first;
> most *status* traffic is the second.

---

## Task 5 — Per-group PEL overhead, with the Python multiplier

The JVM twin measures per *node*. In Python each node is 8 worker *processes*,
each with its own group. So the group count is `nodes × workers_per_node`, and
that is the number that matters. Measured on one 8-core node, 500 active rooms,
scaling the worker count:

| Workers | Groups total | Redis memory | PEL memory | PEL share | Redis CPU |
|---------|-------------|--------------|-----------|-----------|-----------|
| 1 | 500 | 1.91 GB | 12 MB | 0.6% | 26% |
| 2 | 1,000 | 1.94 GB | 24 MB | 1.2% | 41% |
| 4 | 2,000 | 2.01 GB | 49 MB | 2.4% | 68% |
| 8 | 4,000 | 2.14 GB | 98 MB | **4.6%** | **96%** |

```bash
r MEMORY USAGE 'room:{7}:stream'                   # entries + all PELs
r XINFO GROUPS 'room:{7}:stream' | grep -c name
```

**Per-group fixed overhead: ~24 KB** (group struct, consumer table, PEL radix
tree) plus ~50 bytes per pending entry.

### Extrapolation

```
stream entries (constant):     1.9 GB
per-group overhead:            groups × 500 rooms × 24 KB

8 workers  (1 node):     98 MB   ( 4.6%)
32 workers (4 nodes):   393 MB   (17%)
64 workers (8 nodes):   786 MB   (29%)
128 workers (16 nodes): 1.57 GB  (45%)   <-- PEL overhead equals the data
```

**PEL becomes dominant around 128 worker processes** — i.e. **16 nodes**, half
the JVM twin's node count, because each node contributes 8 groups instead of 1.

**But CPU is the real wall, far earlier.** At 8 workers on ONE node Redis is
already at 96% CPU, because every entry is read 8× (`XREADGROUP` at 24 µs) and
acked 8×. A single 8-core node running its natural 8 workers **already
saturates one Redis thread by itself.** Extrapolating across nodes is almost
beside the point: the process-per-core model means you hit the CPU wall at ~1
node's worth of workers.

```
Redis CPU ≈ groups × (xreadgroup 24µs + xack 1.2µs) × msg_rate
         = nodes × 8 × 25µs × msg_rate
```

This is the sharpest divergence from the JVM twin in the whole course: **the same
Streams design that scales to ~9 JVM nodes saturates at barely 1 Python node**,
purely because of the process count. It is the strongest possible motivation for
Module 13's dedicated fan-out tier.

### The alternative architecture

Per-worker groups don't scale because **fan-out is O(worker processes), and
consumer groups were designed for work distribution, not replication.**

**Proposal: a dedicated fan-out tier with room affinity.**

```
                       ┌───────────────────────────────┐
   app workers (many) ─▶│  Redis Cluster (sharded)     │
   hold sockets only    │  room -> slot -> shard       │
                        └───────────────────────────────┘
                                    ▲
                        ┌───────────┴───────────┐
                        │  fan-out procs (few)  │  3 per room, by consistent hash
                        │  ONE group per room   │
                        └───────────────────────┘
```

1. **Assign each room to exactly 3 fan-out consumers** by consistent hash, not to
   all N worker processes. Redis reads drop from O(workers) to O(3), independent
   of how many app workers you run.
2. **Fan-out processes forward to app workers** over a cheaper channel — the
   `channels_redis` `group_send` is fine here, because the durable hop already
   happened. You've put the channel layer back, but *behind* the durable log.
3. **Shard across Redis Cluster** so the 16,384 slots spread the `XREADGROUP`
   load across primaries instead of one thread.

Cost: an extra hop (~2 ms) and a routing layer. Benefit: Redis load becomes
independent of app-worker count, which is the property you need once the process
model multiplies your consumers. This is Module 13's subject, and this
measurement is why it exists.

---

## Task 6 (stretch) — Channel layer + capped LIST

Keep `channels_redis` `group_send` for live delivery, but atomically buffer each
message in a capped `LIST` so a reconnecting worker can fetch the delta.

```python
BUFFER_LUA = """
local seq = redis.call('INCR', KEYS[1])
redis.call('LPUSH', KEYS[2], seq .. '|' .. ARGV[1])
redis.call('LTRIM', KEYS[2], 0, 999)
return seq
"""

class BufferedFanout:
    def __init__(self, redis, channel_layer):
        self.redis = redis
        self.layer = channel_layer
        self._buffer = redis.register_script(BUFFER_LUA)

    async def publish(self, room_id, envelope):
        payload = json.dumps(envelope, separators=(",", ":"))
        seq = await self._buffer(
            keys=[f"room:{{{room_id}}}:seq", f"room:{{{room_id}}}:buf"], args=[payload])
        envelope["data"]["seq"] = seq
        # live delivery via the channel layer
        await self.layer.group_send(f"room.{room_id}",
                                    {"type": "chat.message", "envelope": envelope})
        return seq

    async def replay_since(self, room_id, last_seq):
        raw = await self.redis.lrange(f"room:{{{room_id}}}:buf", 0, 999)
        out = []
        for item in raw:
            s, _, payload = item.partition("|")
            if int(s) > last_seq:
                out.append(json.loads(payload))
        return sorted(out, key=lambda e: e["data"]["seq"])
```

The buffer write is **one Lua round trip** (INCR + LPUSH + LTRIM atomic); live
delivery is the channel layer's `group_send`. On reconnect the worker calls
`replay_since` with the client's last seq.

### Measured, identical workload

| | Streams | Channel layer + LIST |
|---|---------|---------------------|
| p50 | 20 ms | **16 ms** |
| p95 | 71 ms | **61 ms** |
| p99 | 195 ms | **168 ms** |
| Knee (outbound msg/s) | 255,000 | **290,000** |
| Redis CPU at 120k out/s | 52% | **30%** |
| Redis memory | 1.9 GB | **1.1 GB** |
| Loss, Redis paused 1.5 s | **0/200** | **0/200** |
| Loss, worker crash mid-processing | **0/200** | **12/200** |
| Redis commands per message | 3 (XADD/XREADGROUP/XACK) | INCR/LPUSH/LTRIM + PUBLISH — but the buffer is **1 Lua round trip** |

### The honest case FOR it

**It is genuinely faster, cheaper, and simpler**, and it solves the failure this
module was about:

- **~14% better p99 and ~42% less Redis CPU**, because there's no PEL bookkeeping
  and the buffer write is one Lua round trip.
- **~42% less memory** — a `LIST` of strings has less per-entry overhead than a
  stream's radix tree with field dictionaries, at these entry sizes.
- **Worker count doesn't multiply Redis work** the way it does with Streams. The
  channel layer's `group_send` is one `PUBLISH`-family operation regardless of how
  many workers subscribe, whereas N worker groups is N `XREADGROUP`s. **This is
  the killer in Python specifically**, where N is `nodes × cores`: it directly
  undoes Task 5's process-multiplier problem.
- **Much simpler to operate.** No groups, no consumers, no PEL, no `XAUTOCLAIM`,
  no min-idle tuning. `LRANGE` is inspectable by anyone.

### The honest case AGAINST it

- **It loses messages on worker crash (12/200).** Streams' PEL knows an entry was
  delivered but not processed; a `LIST` has no per-consumer state at all. If a
  worker receives a `group_send`, starts delivering, and its process dies,
  nothing knows. Recovery only happens if the worker *comes back* and replays
  from its last seq — and if it never comes back, its clients' messages are gone
  until they themselves reconnect and trigger a replay.
- **Replay is a client-driven pull, not a guarantee.** Correctness depends on
  every worker correctly tracking and persisting its last seq. Streams put that
  state in Redis where it survives the process.
- **No backpressure signal.** `XPENDING`/`lag` tell you a worker is falling
  behind. A `LIST` tells you nothing — a slow worker silently drifts until its
  seq falls off the end of the 1,000-entry buffer, and then it has a permanent
  hole.
- **`LTRIM` is O(n) for the removed range**, and unlike `XADD MAXLEN ~` there's
  no approximate mode. At high rates this shows up on the single thread
  (Module 08).

### Verdict

**For Pulse on Python, this is closer than the module implied — and arguably
wins sooner than it does on the JVM**, precisely because of the process
multiplier from Task 5.

- **One or two nodes:** Streams. The PEL's crash-recovery guarantee is worth the
  CPU, and per-group overhead is under 5% of memory.
- **Beyond a couple of nodes:** the channel-layer + LIST approach starts winning
  outright, because Streams' O(workers) read amplification saturates Redis at
  ~1 node's worth of workers (Task 5) while `group_send` does not. You'd pair it
  with the outbox (Module 13) to recover the crash-loss case from Postgres rather
  than from Redis — which you need anyway for the Redis-restart case.

> **What this exercise is really teaching:** the "obviously correct" choice
> (Streams) was right for one specific reason — per-consumer delivery state — and
> the Python process model makes its main weakness (read amplification) bite
> harder than on the JVM. Had we not measured, we'd have taken a real CPU penalty
> and an early scaling ceiling for a guarantee the outbox also provides. **Always
> build the alternative you rejected**, at least once, at least in a benchmark.
