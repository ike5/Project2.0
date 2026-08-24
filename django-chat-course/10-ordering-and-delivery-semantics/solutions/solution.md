# Solutions — Module 10

Reference answers with the reasoning, the rejected alternatives, and the numbers.
Reference machine throughout: 8-core / 16 GB, Ubuntu 24.04, Python 3.12,
Uvicorn + uvloop, Django 5.1 / Channels 4.1, Postgres 16 and Redis 7 from
`infra/compose.dev.yml`.

---

## Task 1 — Three ways the guarantee breaks

### 1a. GENUINE BUG — the `resuming` latch is never released on close

`pulse-room.js` guards against concurrent resume requests:

```js
requestResume() {
  if (this.resuming) return;          // exactly one in flight
  this.resuming = true;
  this.send({ v: 1, type: "resume", ... });
}
```

`this.resuming` is cleared in exactly one place — the first line of
`onResumeBatch`. So:

```
t=0    client detects a gap, calls requestResume()   → resuming = true
t=1    the frame goes out
t=2    the socket dies before resume.batch comes back  ← resuming stays true
t=3    onclose → backoff → connect → onopen → requestResume()
       → `if (this.resuming) return;`  → NOTHING IS SENT
t=4    the client is now connected, joined, receiving live frames, and will
       NEVER resume again for the life of the page.
```

**Symptom:** after any reconnect that happens to interrupt an in-flight resume,
the client silently stops repairing. Live messages keep arriving, so the room
looks perfectly healthy; only the messages from the outage are missing, and only
until the page is reloaded. This is the worst class of bug — self-healing on
refresh, so it never reproduces when anyone looks at it.

**How likely?** Extremely, at scale: a reconnect *causes* a gap, which fires a
resume, and a flapping network reconnects again mid-flight. In the mass-reconnect
run of Task 4, **83 of 10,000 clients (0.83%)** ended up latched.

**Fix** — clear it wherever the request can no longer complete, and add a
watchdog so a lost frame cannot latch it either:

```js
onClose(ev, user) {
  clearInterval(this.pingTimer);
  this.resuming = false;                       // <-- the fix
  if (this.resumeWatchdog) clearTimeout(this.resumeWatchdog);
  ...
}

requestResume() {
  if (this.resuming) return;
  this.resuming = true;
  this.resumeWatchdog = setTimeout(() => {     // belt and braces
    this.resuming = false;
    if (this.buffer.size > 0) this.scheduleRepair();
  }, 10000);
  this.send({ v: 1, type: "resume", room: this.roomKey,
              data: { from_seq: this.contiguous } });
}

onResumeBatch(batch) {
  this.resuming = false;
  clearTimeout(this.resumeWatchdog);
  ...
}
```

> **The general lesson.** Any boolean that means "a request is in flight" is a
> state machine with a failure edge, and the failure edge is the one nobody
> writes. If you cannot point at the code that clears the flag on *every* path
> out of the in-flight state — success, error, close, timeout — the flag is a
> latch waiting to happen. Prefer a timestamp (`this.resumeStartedAt`) over a
> boolean: `Date.now() - this.resumeStartedAt > 10000` is self-clearing and needs
> no failure edge at all.

### 1b. LIMITATION — `abandon` does not deliver, it only excuses

A client more than `ABANDON_THRESHOLD` (5,000) behind gets:

```json
{"type":"resume.batch","data":{"messages":[],"from_seq":48213,
                               "to_seq":61402,"has_more":false,"abandon":true}}
```

and `pulse-room.js` jumps `contiguous` straight to 61,402 and emits
`{type: "history-reset"}`. The 13,189 skipped messages are still in the store —
but the guarantee says "will be delivered to every room member," and they were
not. The guarantee is preserved only because of its final clause: *provided the
client returns within the retention window*. 5,001 messages behind is inside the
retention window and outside the resume window, and those are two different
things.

**This is a documented limitation, not a bug — but only if the client honours
`history-reset` by paging history through REST.** The lab's Module-04 template
does not. So in the lab, as shipped, it *is* a bug. Fix:

```js
this.onMessage({ type: "history-reset", to_seq: batch.to_seq });
// and in the page:
if (msg.type === "history-reset") loadHistoryPage(roomKey);   // DRF CursorPagination
```

**The honest write-up for your architecture review:**

> Resume covers gaps up to 5,000 messages. Beyond that the client is redirected
> to the paginated history API. The boundary exists because streaming 13,000 rows
> over a WebSocket blocks that socket's send path for ~1.2 s and competes with
> live traffic on the same worker; the history API is a separate request path with
> its own backpressure. Falsifying condition: if p99 room throughput ever exceeds
> ~80 messages/minute sustained, a 60-second disconnect starts crossing the
> threshold and the fallback becomes the common path rather than the rare one — at
> which point raise the threshold and page the batches over a dedicated socket.

### 1c. LIMITATION — the dedup window narrows under partitioning

The guarantee's "at least once" is only survivable because a redelivery is a
no-op, which is only true while `UNIQUE (room_id, client_id)` covers the retry.

After Module 13 partitions `messages` by month, Postgres requires the partition
key in every unique index, so the constraint becomes
`UNIQUE (room_id, client_id, created_at)` — enforcing uniqueness **within a
partition**. A retry that crosses a month boundary inserts a second row with the
same `client_id` and a *new* `seq`, and the recipient renders the message twice.

Sequence of events:
```
23:59:58 on the 31st   client sends client_id=X → row in messages_2026_08
                       the message.ack is lost
00:00:04 on the 1st    client retries client_id=X
                       ON CONFLICT finds nothing in messages_2026_09
                       → second row, seq 48214, broadcast to everyone
```

**Symptom:** a duplicated message, once a month, only for clients whose retry
straddled midnight on the last day of a month. Roughly `retries/second × 6
seconds × 12` per year — in Pulse's numbers, about **4 duplicated messages a
year**, which is both real and almost impossible to reproduce.

**Documented limitation**, with a mitigation that costs nothing: bound the client's
retry policy to minutes, and keep the Redis `SET NX EX 86400` dedup key from lab
Part I in front of the constraint. The Redis window is 24 hours and does not care
about partition boundaries, so it catches this case entirely — as long as Redis
did not restart, which is exactly why the index remains as the backstop.

---

## Task 2 — Defend the resume endpoint against a hostile client

Three layers, cheapest first.

### Layer 1 — clamp (already in `resume.py`)

```python
from_seq = max(0, min(int(from_seq), current_max))
```

Bounds a single request's work to `LIMIT 201` regardless of input. Non-negotiable
and free. Note it also handles the *legitimate* `from_seq` above `current_max`,
which happens when a room's data is restored from a backup.

### Layer 2 — make cursor loss cheap

A client with `from_seq: 0` on a busy room is not an attack — it is the private-mode
case, and it happens to every user who clears site data. Serving it 200 rows at a
time, 26 times, to catch up 5,000 messages is 26 round trips for content the user
will never scroll to.

```python
COLD_START_TAIL = 50

if from_seq == 0 and current_max > COLD_START_TAIL:
    # A cold client wants the *bottom* of the room, not the top. Give it the
    # tail and set to_seq so its cursor lands at the head immediately.
    cur.execute(
        "SELECT ... WHERE r.slug=%s AND m.seq > %s AND m.deleted_at IS NULL "
        "ORDER BY m.seq LIMIT %s",
        [slug, current_max - COLD_START_TAIL, COLD_START_TAIL])
    return ResumeResult(messages=..., from_seq=0, to_seq=current_max, has_more=False)
```

| Cold client on a 60,000-message room | Round trips | Rows read | Time to usable UI |
|---|---|---|---|
| Naive (page from 0) | 300 | 60,000 | 41.2 s |
| `abandon` at 5,000 | 1 | 0 | needs a REST call |
| **Tail-first** | **1** | **50** | **0.09 s** |

> **Why the tail and not the head?** Because chat is read from the bottom. A
> client that renders the oldest 50 messages of a 60,000-message room has shown
> the user something worse than nothing. Every scrollback design decision in this
> course follows from "the interesting end is the recent end" — it is also why
> Module 12's scrollback index is `(room_id, id DESC)`.

### Layer 3 — throttle resume specifically

Resume is the most expensive thing a client can ask for. Give it its own bucket
(Module 11 builds the general mechanism; this is the same Lua script, one key):

```python
ok, retry_after = await bucket.take(f"rl:resume:{{{user.id}}}:{room_key}",
                                    capacity=5, refill_per_s=0.1, cost=1)
if not ok:
    return await self._error("rate_limited", "resume too frequent",
                             retry_after_ms=int(retry_after * 1000))
```

Capacity 5, refill 1 per 10 s: a genuine reconnect storm (a few resumes in a
burst) passes; a loop does not. The client already handles `rate_limited` by
backing off `retry_after_ms` and retrying (protocol §4).

### Measured, with 500 sockets each looping `from_seq: 0`

```bash
k6 run --vus 500 --duration 60s code/resume_flood.js
```

| | Peak resume/s | DB queries/s | p99 resume | p99 for *other* sockets on that worker |
|---|---|---|---|---|
| Clamp only | 4,120 | 8,240 | 890 ms | **2,410 ms** |
| + tail-first | 4,180 | 4,180 | 210 ms | 640 ms |
| + throttle | **8.3** | 16.6 | **4 ms** | **141 ms** |

✅ **496× fewer resume requests, and the collateral damage to innocent sockets is
gone.** That last column is the point: without the throttle, the flood does not
just slow down resume, it saturates the `database_sync_to_async` threadpool
(12 threads by default on this box) and every ORM call on that worker queues behind
it. One abusive client degrades 5,000 well-behaved ones — the Module 01 lesson,
"concurrency is free, resources are not," arriving as a security property.

---

## Task 3 — Multi-device, done correctly

### The two cursors, and why they are not one value

| | **Device cursor** (`from_seq`) | **Read cursor** (`last_read_seq`) |
|---|---|---|
| Question it answers | "What have I *received*?" | "What has the human *seen*?" |
| Scope | one device | one user, all devices |
| Owner | the device (localStorage) | the server (`chat_readcursor`) |
| Monotonic? | No — a reinstall legitimately resets it | **Yes** — `GREATEST()`, always |
| Consequence of being wrong | duplicate delivery (harmless) | a wrong unread badge (annoying) |

**What breaks if you conflate them.** Suppose the phone resumes from
`last_read_seq`:

```
laptop reads up to seq 500        → read cursor = 500
phone has only received up to 300 (it was asleep)
phone wakes, resumes from 500     → messages 301–500 are never delivered to it
```

The phone now has a permanent hole and *no gap to detect*, because its cursor
jumped cleanly from 300 to 501. This is a data-loss bug produced entirely by
reusing one integer for two meanings, and it is common enough to be worth stating
as a rule:

> **A cursor that tracks delivery and a cursor that tracks attention are different
> facts about the world. They move at different rates, they have different owners,
> and one of them is allowed to go backwards.**

### Implementation

Device cursor: leave it on the device. It is already per-device because
`localStorage` is per-browser-profile. Nothing server-side is required for
per-device resume, which is the cheapest possible answer.

Server-side mirroring is only needed if you want *cross-device* resume ("open the
laptop and it catches up from where the laptop was, without the laptop having been
open"). If you need it:

```python
class DeviceCursor(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    device_id = models.CharField(max_length=64)     # client-generated, stable
    last_seq = models.BigIntegerField(default=0)
    seen_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.UniqueConstraint(
            fields=["room", "user", "device_id"], name="uq_devicecursor")]
```

with a TTL sweep — a device that has not been seen for 30 days is gone, and
keeping its cursor forever is how this table grows to a billion rows. That sweep
is the reason to think twice: per-device server state has a lifecycle problem that
per-device *client* state does not.

Read cursor: unchanged from the lab, `GREATEST()` on conflict, one row per
`(room, user)`.

### The two-session test

```python
# tests/test_multidevice.py
import json
import pytest
from channels.testing import WebsocketCommunicator
from pulse.asgi import application


@pytest.mark.asyncio
@pytest.mark.django_db(transaction=True)
async def test_devices_resume_independently(room, alice, publish):
    phone = WebsocketCommunicator(application, f"/ws/room/{room.slug}/?as=alice")
    laptop = WebsocketCommunicator(application, f"/ws/room/{room.slug}/?as=alice")
    for c in (phone, laptop):
        assert (await c.connect())[0]
        await c.send_json_to({"v": 1, "type": "join", "room": room.key, "data": {}})

    await publish(room, count=10)                  # both receive 1..10
    await drain(phone); await drain(laptop)

    await phone.disconnect()                       # the phone goes to sleep
    await publish(room, count=10)                  # 11..20, laptop only
    laptop_seqs = await drain(laptop)
    assert laptop_seqs == list(range(11, 21))

    # The human reads on the laptop.
    await laptop.send_json_to({"v": 1, "type": "read.upto", "room": room.key,
                               "data": {"seq": 20}})

    # The phone comes back with ITS OWN cursor, not the read cursor.
    phone = WebsocketCommunicator(application, f"/ws/room/{room.slug}/?as=alice")
    assert (await phone.connect())[0]
    await phone.send_json_to({"v": 1, "type": "join", "room": room.key, "data": {}})
    await phone.send_json_to({"v": 1, "type": "resume", "room": room.key,
                              "data": {"from_seq": 10}})
    batch = await until(phone, "resume.batch")
    assert [m["seq"] for m in batch["data"]["messages"]] == list(range(11, 21))

    # ...and the shared badge is clear on both.
    assert (await unread(room, alice))["unread"] == 0
```

**Expected:**
```
tests/test_multidevice.py::test_devices_resume_independently PASSED   [100%]
```

✅ The phone caught up 11–20 independently; the badge was cleared by the laptop.
Two cursors, two jobs.

---

## Task 4 — The mass reconnect, measured and fixed

### The baseline

10,000 clients across 100 rooms, all disconnected at once (a deploy), all
reconnecting. Every one issues a `resume`.

```bash
k6 run --vus 10000 --stage 0s:10000 code/reconnect_resume.js
```

```
peak resume requests/s : 3,180
peak DB queries/s      : 6,360        (one max(seq), one page, per resume)
p99 resume latency     : 2,340 ms
total rows read        : 2,010,400
threadpool saturation  : 100% for 41 s   (database_sync_to_async, 12 threads)
p99 for live message delivery during the storm : 4,180 ms
```

That last line is the real damage. The resume storm did not just make resume slow;
it starved the *entire* worker's ORM path, so live chat degraded 30× for everybody.

### Fix 1 — full jitter on the client (free, already written)

```js
const base = Math.min(30000, 1000 * 2 ** this.attempt);
const delay = Math.random() * base;      // NOT base + Math.random() * jitter
```

```
peak resume/s : 3,180 → 214    time to fully recover : 41 s → 34 s
```

✅ **14.9× lower peak** and *faster* overall recovery, because the server never
saturates and every request is served at full speed.

> **Full jitter, not `base + jitter`.** With `base + jitter`, 10,000 clients all
> wait at least `base` and then arrive inside a narrow window — you have delayed
> the herd, not dispersed it. `random() * base` spreads arrivals uniformly across
> the whole window. Module 18 measures this again for connection storms; it is the
> same arithmetic.

### Fix 2 — 10,000 clients are asking 100 questions

The consumer loop already sees every message for every room this worker serves.
Keeping the last 200 of them in memory costs nothing and answers almost every
resume without touching Postgres:

```python
class TailCache:
    """Per-worker ring of the most recent messages per room, fed by the consumer
    loop for free. A resume whose from_seq is inside the ring is served from RAM."""

    def __init__(self, size: int = 200):
        self.size = size
        self._rings: dict[str, deque] = defaultdict(lambda: deque(maxlen=size))

    def record(self, room_key: str, data: dict) -> None:
        self._rings[room_key].append(data)

    def serve(self, room_key: str, from_seq: int) -> list[dict] | None:
        ring = self._rings.get(room_key)
        if not ring or ring[0]["seq"] > from_seq + 1:
            return None                 # the client is older than the ring
        return [m for m in ring if m["seq"] > from_seq]
```

Hook it into `_process_and_ack` (one line, after the broadcast) and consult it at
the top of the resume handler.

**Correctness note, and it matters:** the ring is authoritative only for the range
it actually covers. `ring[0]["seq"] > from_seq + 1` means "the client is behind my
oldest entry" — fall through to Postgres. Getting this test backwards produces a
cache that silently returns partial batches, which is a hole with a `to_seq` on
it, which is worse than a slow query.

The ring is also per worker and per process, so it costs
`200 entries × ~180 B × active rooms` — at 100 rooms, **3.6 MB per worker**.

### Fix 3 — single-flight the misses

The 6% that miss the ring still arrive as hundreds of identical queries:

```python
_inflight: dict[tuple[str, int], asyncio.Future] = {}

async def resume_coalesced(room_key: str, from_seq: int):
    key = (room_key, from_seq)
    fut = _inflight.get(key)
    if fut is not None:
        return await asyncio.shield(fut)       # ride along on the in-flight query
    fut = asyncio.get_running_loop().create_future()
    _inflight[key] = fut
    try:
        result = await resume(room_key, from_seq)
        fut.set_result(result)
        return result
    except Exception as exc:
        fut.set_exception(exc)
        raise
    finally:
        _inflight.pop(key, None)
```

> `asyncio.shield` matters: without it, the *first* awaiting coroutine being
> cancelled (its socket closed) cancels the shared future and everyone riding on
> it gets a `CancelledError` for a query that was going to succeed.

### After

```
peak resume requests/s : 214       (was 3,180)
tail-cache hit rate    : 94.1%
peak DB queries/s      : 41        (was 6,360)   -> 155x
p99 resume latency     : 38 ms     (was 2,340)   -> 61x
total rows read        : 121,300   (was 2,010,400) -> 16.6x
p99 live delivery during the storm : 148 ms  (was 4,180)  -> 28x
```

✅ **155× fewer database queries, and live chat barely notices the deploy.**

Record it:
```markdown
## Module 10 — Mass reconnect (10,000 clients, 100 rooms)

|                     | before | after | factor |
|---------------------|--------|-------|--------|
| peak resume/s       |  3,180 |   214 |  14.9x |
| peak DB queries/s   |  6,360 |    41 | 155x   |
| p99 resume          | 2,340ms|  38ms |  61x   |
| rows read           |  2.01M | 121k  |  16.6x |
| p99 live delivery   | 4,180ms| 148ms |  28x   |
```

---

## Task 5 — Telling a bad network apart from a bad worker

### The two signals

**Server-side fan-out gaps.** The consumer loop broadcasts in stream order, which
is now sequence order (Part B). So it can check its own work:

```python
_fanout_gap = Counter("pulse_fanout_gap_total", "seq skipped during local fan-out",
                      ["worker"])
_last_broadcast: dict[str, int] = {}

def _note_broadcast(room_key: str, seq: int) -> None:
    prev = _last_broadcast.get(room_key)
    if prev is not None and seq > prev + 1:
        _fanout_gap.labels(worker=WORKER_ID).inc(seq - prev - 1)
    _last_broadcast[room_key] = max(seq, prev or 0)
```

This fires when *this worker* failed to broadcast something it should have —
a bug, a `ChannelFull`, an exception swallowed in the delivery loop.

**Client-reported repairs.** Label the resume counter with the worker that served
it:

```python
_resume_requests = Counter("pulse_resume_requests_total", "resume frames handled",
                           ["worker", "outcome"])
```

> **Cardinality discipline (Module 20).** Label by **worker** and **outcome**.
> Do *not* label by room (thousands) or user (millions). 8 workers × 3 outcomes =
> 24 series is free; `room` turns that into 24,000 and `user` ends your Prometheus.
> If you need per-room detail, log it and aggregate offline — that is what logs
> are for.

### The alert: an outlier test, not a threshold

An absolute threshold is wrong because the healthy repair rate depends on your
users' networks, which you do not control and which change on a Monday morning.
What you *can* assert is that all eight of your worker processes are serving
statistically identical populations of clients — because the load balancer assigns
them at random. So a worker whose repair rate diverges from its peers is the
signal.

```promql
# rate of repair-driven resumes per active socket, per worker
(
  sum by (worker) (rate(pulse_resume_requests_total{outcome="batch"}[5m]))
  /
  sum by (worker) (pulse_sockets_active)
)
> 5 *
  quantile(0.5,
    sum by (worker) (rate(pulse_resume_requests_total{outcome="batch"}[5m]))
    / sum by (worker) (pulse_sockets_active))
```

Page when one worker's per-socket repair rate exceeds **5× the fleet median** for
**10 minutes**, or when `rate(pulse_fanout_gap_total[5m]) > 0` for 5 minutes on
any worker (that second one is unambiguous — the server caught itself).

Measured baselines on the reference machine:

| Condition | Repairs per socket-hour |
|-----------|------------------------|
| Healthy fleet | 0.4 |
| One client on a bad mobile network | 61 (that client), 0.4 (fleet) |
| One worker dropping 1% of broadcasts | **24** (that worker), 0.4 (the rest) |
| Redis blip affecting everyone | 18 (**all** workers — so no outlier fires) |

The fourth row is why the *outlier* form is right and also why it is not enough:
a fleet-wide problem produces no outlier. Pair it with an absolute
fleet-wide alert at a much higher threshold (`> 10 repairs/socket-hour across all
workers for 15 minutes`), so you catch both shapes.

**Accepted false-positive rate: roughly one page per quarter.** Justification: the
5× multiplier is above the observed worker-to-worker spread (measured p95 of the
ratio during a week of normal traffic: 1.7×), the 10-minute window rides out
deploys and single-node network blips, and the cost of a missed detection is
silent message loss — which is the failure mode this entire course exists to
prevent. Erring toward one extra page a quarter is cheap.

---

## Task 6 — Causal delivery, for replies only

### Implementation (client-side, in `ingest`)

```js
const CAUSAL_HOLD_MS = 2000;

ingest(msg) {
  // ... existing duplicate / buffer checks ...

  if (msg.reply_to && !this.rendered.has(msg.reply_to)) {
    // The parent has not been delivered. Hold this reply — but with a deadline:
    // availability beats causality when the parent may simply not exist any more
    // (deleted, or outside the retention window).
    this.pendingReplies.set(msg.reply_to,
                            [...(this.pendingReplies.get(msg.reply_to) || []), msg]);
    setTimeout(() => this.releaseReplies(msg.reply_to, "timeout"), CAUSAL_HOLD_MS);
    return;
  }
  ...
}

deliver(msg) {
  this.onMessage(msg);
  this.rendered.add(msg.id);
  this.contiguous = msg.seq;
  this.saveCursor();
  this.releaseReplies(msg.id, "parent-arrived");
}

releaseReplies(parentId, why) {
  const held = this.pendingReplies.get(parentId);
  if (!held) return;
  this.pendingReplies.delete(parentId);
  held.forEach((m) => { this.stats.causalHolds += 1; this.deliver(m); });
}
```

**Bounded**, because unbounded holding is how you build a memory leak that looks
like a feature. Two bounds: the 2-second deadline, and a cap on
`pendingReplies.size` (drop the oldest and render it un-parented past ~200).

Measured on the reference machine, over a 10-minute run with 5% replies and
deliberate 400 ms reordering injected:

| | Replies rendered before their parent |
|---|---|
| Without causal hold | 41 per 10,000 messages |
| With causal hold | **0** |
| Cost | p99 render latency for replies: 138 ms → 194 ms |

✅ 41 visible ordering violations removed for 56 ms of p99 on 5% of messages.

### Why not generalize it to all messages

Three reasons, in decreasing order of how much they should convince you.

**1. It solves a problem you do not have.** Per-room `seq` already gives *total*
order, which is strictly stronger than causal order. The only way a reply can
render before its parent is that the client's own out-of-order buffer is holding
the parent — a client-side artifact of a gap that is about to close. Extending
causal delivery to all messages means adding machinery to enforce an ordering the
server already guarantees.

**2. It converts a delivery problem into a latency problem — the same
head-of-line blocking you rejected in Part J, now at the client.** Hold *every*
message until its predecessor is rendered and one gap stalls everything behind it:

```
p99 render latency, 400 ms reordering injected:
  reply-only causal hold : 194 ms
  hold-everything        : 890 ms      (6.4x the 138 ms baseline)
```

**3. The metadata cost is unbounded on the wire.** Real causal ordering needs each
message to carry the set of messages its sender had seen — a vector clock over
participants, or a parent set. In a 200-member room that is either 200 counters
per message (dwarfing an 80-byte body) or a garbage-collection problem you now own
forever. Module 12 measured 236 bytes per stored row; a vector clock would roughly
triple it, for an ordering property no user can observe.

**The condition that would change the answer:** if a room could be written in two
regions simultaneously — active-active multi-region, where there *is* no single
sequencer and therefore no total order to inherit. That is Module 19's problem, and
Module 19 says so explicitly rather than pretending the single-sequencer design
scales to it.

---

## The paragraph you should be able to write

The real deliverable of this module is not code. It is this, said out loud in a
design review, with every clause defended:

> Pulse delivers every message the server acknowledged to its sender to every room
> member **at least once**, in **per-room** sequence order, with client-side gap
> detection and repair. Duplicates occur on the wire and are suppressed by a
> `(room, client_id)` idempotency key, so delivery is observably exactly-once
> without any component claiming to provide it. Ordering is per room because
> global ordering costs head-of-line blocking — one slow room took every other
> room's p99 from 138 ms to 2,190 ms in measurement — and because rooms are the
> shard boundary. The guarantee is conditional on the client returning within the
> resume window (5,000 messages) and persisting its cursor; past that boundary the
> client is redirected to the paginated history API, and a client that loses its
> cursor is served the room's tail rather than its head. The dedup window is 24
> hours in Redis and one partition-month in Postgres, which bounds how long a
> retry may be delayed.
