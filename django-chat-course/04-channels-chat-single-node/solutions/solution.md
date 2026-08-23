# Solutions 04 — Make the Channel Layer Show You Its Limits

Reference answers, the reasoning, the rejected alternatives, and the numbers.
Reference machine: **8-core / 16 GB, Ubuntu 24.04, Python 3.12, Django 5.1,
Channels 4.1, Uvicorn + uvloop**, single node, `InMemoryChannelLayer`.

---

## Task 1 — What a client is allowed to influence

### Attack A — impersonation. It fails, and you should know why.

```bash
websocat "ws://localhost:8000/ws/room/general/?as=u0"
```
```json
{"type":"message.create","body":"fire everyone","sender":"admin"}
```

**Result:**
```
{"type": "message.new", "id": 612, "sender": "u0", "body": "fire everyone", "ts": ...}
```

The `sender` field was ignored, because the consumer never reads it:

```python
await self.channel_layer.group_send(self.group, {
    "type": "chat.message",
    "sender": self.user.username,      # from scope["user"], set by middleware
    ...})
```

`self.user` came from the ASGI scope at connect time and is not reachable from
the wire. **Identity is established once, at the handshake, and never re-read
from client input.** That is not an accident of this code; it is the property to
preserve.

### Attack B — cross-room injection. Also fails, until someone "cleans up" the code.

```json
{"type":"message.create","body":"leak","room":"room.random"}
```
**Result:** delivered to `room.general` only. `self.group` is derived from
`scope["url_route"]` at connect and is immutable for the connection's lifetime.

Now watch it break. This is the refactor a reviewer would wave through:

```python
# "less repetition!" — and a remote code path controlled by the client
await self.channel_layer.group_send(content.get("room", self.group), {
    "type": "chat.message", **content, "sender": self.user.username})
```

```json
{"type":"message.create","body":"leak","room":"room.random"}
```
**Result:** delivered to every member of `room.random`, from a client authorized
only for `general`. And worse — because `**content` spreads *every* client key
into the event dict:

```json
{"type":"message.create","body":"x","room":"room.random","ts":0}
```
overrides the server timestamp, and

```json
{"type":"message.create","body":"x","room":"room.general","id":1}
```
forges a message id, which in Module 05 becomes a forged idempotency key and in
Module 10 a forged resume cursor.

### Attack C — the hole that is actually open today

Neither of the above works, but this does:

```bash
python - <<'EOF'
import asyncio, json, websockets
async def main():
    async with websockets.connect("ws://localhost:8000/ws/room/general/?as=u0",
                                  max_size=None) as ws:
        await ws.recv()
        await ws.send(json.dumps({"type": "message.create", "body": "A" * 8_000_000}))
        print(json.loads(await ws.recv())["type"])
asyncio.run(main())
EOF
```

**Result:**
```
message.new
```

An 8 MB message was accepted, written to Postgres, and then **`deepcopy`'d once
per group member and JSON-encoded once per member**. In a 200-member room that
is 1.6 GB of allocation and ~4 seconds of one core, from one frame, from one
unprivileged user. Worker RSS during the test: **96 MB → 2.1 GB**, and every
other connection on that worker was frozen for the duration.

Two fixes, and you want both:

```bash
# 1. At the transport: refuse the frame before Python ever sees the string.
uvicorn pulse.asgi:application --ws-max-size 65536 --loop uvloop
```
```python
# 2. In the consumer: an explicit, application-level limit with a real reason.
MAX_BODY = 4096          # ~1,000 characters of any script; Slack's is 4,000

if len(body) > MAX_BODY:
    await self.send_json({"type": "error", "code": "body_too_long",
                          "max": MAX_BODY})
    return
```

The transport limit protects the *worker*; the application limit gives the
*user* an error frame instead of a mysterious disconnect. `--ws-max-size` alone
closes the socket with `1009`, which a client cannot distinguish from a network
fault.

### The rule, and the allowlist

> **Nothing a client sends may influence routing, identity, or ordering.**
> Client input contributes exactly one thing: content. Everything else —
> `sender`, `room`, `ts`, `id`, `seq` — is stamped by the server from state
> established at the handshake.

Enforce it with an allowlist, not with discipline:

```python
CLIENT_FIELDS = {
    "message.create": {"body", "reply_to", "client_id"},   # client_id: Module 05
    "ping":           {"ts"},
    "read.upto":      {"seq"},
}


async def receive_json(self, content, **kwargs):
    mtype = content.get("type")
    allowed = CLIENT_FIELDS.get(mtype)
    if allowed is None:
        await self.send_json({"type": "error", "code": "unknown_type",
                              "got": str(mtype)[:32]})
        return

    extra = set(content) - allowed - {"type"}
    if extra:
        # Rejecting loudly beats ignoring silently: a client sending fields you
        # do not honour is a client whose author believes they work.
        await self.send_json({"type": "error", "code": "unexpected_fields",
                              "fields": sorted(extra)[:8]})
        return
    ...
```

> **The rejected alternative:** silently dropping unknown fields. It is what
> most codebases do, and it is *right* for **inbound server→client** parsing
> (Module 05's forward-compatibility rule: old clients must ignore new fields).
> It is wrong on the **client→server** direction, where an unknown field means
> either a bug or an attack and you want to know which. The asymmetry is
> deliberate: **be liberal in what you accept from a server you control, strict
> about what you accept from a client you do not.**

---

## Task 2 — The revocation gap

### Proving it

```bash
# terminal 1
websocat "ws://localhost:8000/ws/room/general/?as=u1"
```
```bash
# terminal 2 — kick u1 out of the room
python manage.py shell -c "
from chat.models import Membership, Room, User
Membership.objects.filter(user__username='u1', room__slug='general').delete()
print('u1 removed:', not Membership.objects.filter(
    user__username='u1', room__slug='general').exists())
"
```
```bash
# terminal 3 — someone says something confidential
websocat "ws://localhost:8000/ws/room/general/?as=u0"
{"type":"message.create","body":"salary review notes are in the doc"}
```

**Result — terminal 1, the removed user:**
```
{"type": "message.new", "id": 620, "sender": "u0", "body": "salary review notes are in the doc", "ts": ...}
```

✅ **Authorization at connect time is a check with an expiry date you never
set.** A socket lives for hours; membership changes in milliseconds. The channel
name is still in `layer.groups["room.general"]`, and `group_send` does not
consult a database.

### The three designs, measured

Baseline (Part F: 200 receivers, 10 msg/s): **p50 1.8 ms, p99 5.4 ms, 34% of one
core.**

**(a) Delivery-time authorization — check on every fan-out.**

```python
async def chat_message(self, event):
    if not await self._still_a_member():
        await self.close(code=4403)
        return
    await self.send_json({...})
```

| Variant | p50 | p99 | CPU (1 core) | Revocation latency |
|---------|-----|-----|--------------|--------------------|
| No check (baseline) | 1.8 ms | 5.4 ms | 34% | ∞ |
| DB query per delivery | 14.6 ms | **41.8 ms** | **91%** | < 1 message |
| Per-connection flag, 60 s TTL | 1.9 ms | 5.6 ms | 35% | ≤ 60 s |
| Per-connection flag, 5 s TTL | 2.4 ms | 7.1 ms | 41% | ≤ 5 s |

The DB-per-delivery row is the whole lesson: **a check on the fan-out path is
multiplied by the amplification factor.** 10 inbound messages/s × 200 members =
2,000 authorization queries/second for a room that changes membership twice a
day. It took the worker from 34% to 91% of its only core, which means it took
your capacity from 150,000 outbound msg/s to about 56,000.

**(b) Revocation broadcast.** Publish an event when membership changes; each
consumer checks whether it is the subject and closes itself.

```python
# chat/signals.py
from django.db.models.signals import post_delete
from django.dispatch import receiver
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


@receiver(post_delete, sender=Membership)
def on_membership_removed(instance, **kwargs):
    # A signal handler is SYNC code calling an ASYNC layer -> async_to_sync.
    # Safe here (no running loop in a management command / DRF sync view);
    # it would RAISE if called from inside a consumer.
    async_to_sync(get_channel_layer().group_send)(
        f"room.{instance.room.slug}",
        {"type": "chat.revoke", "user_id": instance.user_id})


# chat/consumers.py
async def chat_revoke(self, event):
    if event["user_id"] == self.user.id:
        await self.send_json({"type": "control", "action": "revoked",
                              "room": self.group})
        await self.close(code=4403)
```

**Cost:** zero on the message path. One extra fan-out per membership change,
which happens at a rate measured in changes per day, not per second.
**Revocation latency:** 38 ms measured, end to end.

**And it does not work.** Run it with `--workers 2`: the DRF view that removed
the membership ran on worker A, so `group_send` walked worker A's dict. The
revoked user is connected to worker B. **The revocation broadcast is broken by
exactly the wall this module is about**, which is a genuinely useful thing to
discover with your own hands.

**(c) Per-user control channel.** Same mechanism, different group:

```python
# in connect()
self.user_group = f"user.{self.user.id}"
await self.channel_layer.group_add(self.user_group, self.channel_name)

# from anywhere
async_to_sync(layer.group_send)(f"user.{uid}",
    {"type": "chat.control", "action": "revoked", "room": f"room.{slug}"})
```

Generalizes to everything Module 21 needs — token expiry, forced re-auth,
cluster-wide session revocation, "you have been rate limited" — for the cost of
one extra `group_add` per connection. Same cross-process limitation as (b).

### The recommendation

**Ship (a) with a short-TTL cached flag *and* (c) as the fast path**, and accept
that (c) does not work until Module 07:

```python
REVOKE_TTL = 30.0            # worst-case exposure if the control channel misses

@database_sync_to_async
def _check_membership(self):
    return Membership.objects.filter(
        user_id=self.user.id, room=self.room).exists()

async def _still_a_member(self):
    now = time.monotonic()
    if now - self._authz_at > REVOKE_TTL:
        self._authz_ok, self._authz_at = await self._check_membership(), now
    return self._authz_ok
```

The cached check costs **+0.1 ms p50 / +0.2 ms p99** and bounds worst-case
exposure at 30 seconds; the control channel makes the common case ~40 ms. The
two together are defence in depth: the fast path is best-effort, the slow path
is the guarantee, and you can state the guarantee as a number.

> **The condition that changes the answer:** if messages are regulated content
> (health, finance, minors), 30 seconds of post-revocation exposure may be
> unacceptable, and then you pay the 91%-of-a-core price and buy more nodes. The
> engineering position is not "caching is fine"; it is "here is the exposure
> window, here is the cost of shrinking it, you choose."

---

## Task 3 — The wall as a curve

`--pairs 200` at each worker count, `InMemoryChannelLayer`, one room:

| Workers | Delivered | Rate | `1/N` predicted | Gap |
|---------|-----------|------|-----------------|-----|
| 1 | 200/200 | **100.0%** | 100.0% | — |
| 2 | 105/200 | **52.5%** | 50.0% | +2.5 |
| 3 | 71/200 | **35.5%** | 33.3% | +2.2 |
| 4 | 54/200 | **27.0%** | 25.0% | +2.0 |
| 6 | 37/200 | **18.5%** | 16.7% | +1.8 |
| 8 | 28/200 | **14.0%** | 12.5% | +1.5 |

```
100% │●
     │
 75% │
     │
 50% │    ●
     │       ●
 25% │          ●      ●
     │                       ●
  0% └───┬───┬───┬───┬───┬───┬──── workers
         1   2   3   4   6   8
```

**The derivation.** `crosstalk` opens A and B back to back and asks whether B
received A's message. Delivery requires them to be on the same worker. If accept
balancing were uniform and independent, `P(same) = 1/N` exactly.

**The consistent +1.5 to +2.5 point gap** is not noise; it reproduces across
runs. Two contributing causes, both worth knowing:

1. **`SO_REUSEPORT` hashes the 4-tuple.** Uvicorn's workers all accept on one
   listening socket, and the kernel selects a worker by hashing
   `(src_ip, src_port, dst_ip, dst_port)`. The probe's two connections are made
   microseconds apart from the same source IP with **consecutive ephemeral
   ports**, so their hashes are correlated, not independent. Connect from two
   different processes with a gap between them and the gap shrinks to under 0.5
   points.
2. **The probe's own timing.** A connection made while another worker is briefly
   busy is more likely to be accepted by an idle one, which weakly correlates
   consecutive accepts.

Neither changes the shape. The shape is `1/N`.

### With four rooms: no change

| Rooms | Workers | Rate |
|-------|---------|------|
| 1 | 4 | 27.0% |
| 4 | 4 | 26.5% |

**Because the wall is a process boundary, not a topology property.** The group
name is a dict key; which key you use has no bearing on which *dict* it lives
in. Spreading load across rooms changes nothing, which is exactly why "just
partition by room" (the sticky-routing idea from the README) has to be
implemented as *connection placement*, not as room naming.

### When does this become an incident?

**At two workers.** Here is the argument to give the tech lead:

- A chat product's implicit contract is that a delivered message reaches every
  member. The tolerable failure rate is not 5% or 1%; for a product people use
  to coordinate work it is closer to **1 in 10,000**, because each loss is a
  human misunderstanding.
- At two workers, **47.5% of cross-user messages are never delivered.** That is
  not a degradation; it is a broken product.
- Worse, it is **not random per message — it is deterministic per pair.** With
  8 workers, a user in a 200-member room receives from the ~25 members who share
  their worker, always the same 25. The bug reports read *"I can see Alice's
  messages but Carol's never arrive"*, which sounds like a client bug, a mute
  setting, or a permissions problem, and will be triaged as one for a week.
- And it is **invisible in staging**, where you run one worker.

So the honest answer to "what worker count is safe" is: **one**, which caps the
node at one core (Module 06: ≈150,000 outbound msg/s). Anything above one worker
requires the cross-process layer, which is Module 07. There is no tuning in
between.

---

## Task 4 — Build a cross-process layer, then reject it

A minimal SQLite-backed layer. SQLite in WAL mode gives multi-process readers
and a single writer with real durability — enough to be honest, small enough to
read.

```python
# chat/filelayer.py
import asyncio, json, os, sqlite3, time

from channels.layers import BaseChannelLayer

SCHEMA = """
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;
CREATE TABLE IF NOT EXISTS memberships (
    grp TEXT NOT NULL, channel TEXT NOT NULL, added_at REAL NOT NULL,
    PRIMARY KEY (grp, channel));
CREATE TABLE IF NOT EXISTS mailbox (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    channel TEXT NOT NULL, payload TEXT NOT NULL, expires REAL NOT NULL);
CREATE INDEX IF NOT EXISTS mailbox_channel ON mailbox (channel, id);
"""


class SqliteChannelLayer(BaseChannelLayer):
    """A cross-process channel layer in ~60 lines. Do not ship this."""

    def __init__(self, path="/tmp/pulse-layer.db", poll=0.005, expiry=60, **kw):
        super().__init__(**kw)
        self.path, self.poll, self.expiry = path, poll, expiry
        self.db = sqlite3.connect(path, isolation_level=None, timeout=5)
        self.db.executescript(SCHEMA)
        self.prefix = f"specific.{os.getpid()}"
        self._counter = 0

    async def new_channel(self, prefix="specific"):
        self._counter += 1
        return f"{self.prefix}!{self._counter}"

    async def group_add(self, group, channel):
        self.db.execute("INSERT OR REPLACE INTO memberships VALUES (?,?,?)",
                        (group, channel, time.time()))

    async def group_discard(self, group, channel):
        self.db.execute("DELETE FROM memberships WHERE grp=? AND channel=?",
                        (group, channel))

    async def group_send(self, group, message):
        payload, exp = json.dumps(message), time.time() + self.expiry
        rows = self.db.execute(
            "SELECT channel FROM memberships WHERE grp=?", (group,)).fetchall()
        self.db.executemany(
            "INSERT INTO mailbox (channel, payload, expires) VALUES (?,?,?)",
            [(c[0], payload, exp) for c in rows])

    async def send(self, channel, message):
        self.db.execute("INSERT INTO mailbox (channel, payload, expires) VALUES (?,?,?)",
                        (channel, json.dumps(message), time.time() + self.expiry))

    async def receive(self, channel):
        while True:
            row = self.db.execute(
                "SELECT id, payload FROM mailbox WHERE channel=? ORDER BY id LIMIT 1",
                (channel,)).fetchone()
            if row:
                self.db.execute("DELETE FROM mailbox WHERE id=?", (row[0],))
                return json.loads(row[1])
            await asyncio.sleep(self.poll)      # <-- the latency floor
```

```python
CHANNEL_LAYERS = {"default": {"BACKEND": "chat.filelayer.SqliteChannelLayer",
                              "CONFIG": {"path": "/tmp/pulse-layer.db"}}}
```

```bash
uvicorn pulse.asgi:application --loop uvloop --workers 4 &
python code/wsprobe.py crosstalk --room general --pairs 50
```
**Result:**
```
50/50 message pairs delivered across connections  (100.0%)
```

✅ **It works.** Four workers, four cores, full delivery. Now measure the price
on Part F's fan-out test (200 receivers, 10 msg/s):

| Layer | p50 | p99 | p99.9 | Worker CPU | Notes |
|-------|-----|-----|-------|-----------|-------|
| `InMemoryChannelLayer`, 1 worker | 1.8 ms | 5.4 ms | 11.2 ms | 34% | broken above 1 worker |
| `SqliteChannelLayer`, 4 workers | **9.4 ms** | **63.1 ms** | **214 ms** | 78% ×4 | works |
| `RedisChannelLayer`, 4 workers (Module 07) | 5.8 ms | 16.2 ms | 44 ms | 41% ×4 | works, and crosses machines |

The 5 ms polling interval sets a floor of ~2.5 ms average added latency and
dominates p50. Drop it to 1 ms and p50 improves to 5.1 ms while CPU goes to 96%
per worker — four processes spinning on SQLite. That tradeoff, **polling
interval versus CPU**, is precisely the problem Redis's blocking `SUBSCRIBE`
solves by having the *kernel* wake you.

### The honest verdict: what I did not implement

1. **Liveness and cleanup.** A worker killed with `SIGKILL` leaves its channels
   in `memberships` forever. Every subsequent `group_send` writes mailbox rows
   nobody will ever read, and the table grows without bound. Redis's layer has
   `group_expiry` (default 86400 s) and per-channel TTLs.
2. **Backpressure.** `mailbox` has no `capacity`. The in-memory layer at least
   raises `ChannelFull` (lab Part G); this one silently converts a slow consumer
   into disk growth, which is the invisible-degradation failure mode this course
   keeps arguing against.
3. **Ordering across workers.** `AUTOINCREMENT` gives a global order for
   *inserts*, but two workers inserting concurrently interleave arbitrarily, and
   there is no per-room sequence. Module 05 needs one and Module 10 depends on
   it absolutely.
4. **Cross-machine.** It is a file. Everything above is moot the moment you have
   two nodes, which is the *entire* reason a channel layer exists.
5. **Write contention.** SQLite has one writer. At the course's target of
   100,000 outbound msg/s, `group_send` is 100,000 INSERTs/s through a single
   writer lock — three orders of magnitude past where this design stops.
6. **Durability tradeoff.** `synchronous=NORMAL` means a power cut can lose
   committed rows. `FULL` costs an fsync per `group_send`, which is ~1 ms of
   disk per *message*.
7. **No fan-out at the broker.** `group_send` writes **one row per recipient**
   from the sending process. 200 members = 200 INSERTs on the sender's core.
   (Redis Pub/Sub also fans out per-subscriber, but *inside Redis*, on a
   different machine's core. Module 09's Streams change this shape again.)

Writing that list yourself is the point of the task. **Redis is not chosen
because it is fast; it is chosen because items 1–7 are already solved, tested by
a decade of production use, and someone else is on call for them.**

---

## Task 5 (Stretch) — A detector that would have paged you

The alarming part of the lab was not the broken delivery; it was the **clean
logs**. Build the thing that would have caught it.

### Design

Each worker announces itself over the channel layer on a timer. Each worker
counts how many *distinct* workers it heard from. Compare against how many
workers actually exist — which the filesystem knows even when memory does not.

```python
# chat/partition_detector.py
import asyncio, os, time
from collections import defaultdict

from channels.layers import get_channel_layer
from prometheus_client import Gauge

HEARTBEAT_GROUP = "pulse.workers"
INTERVAL = 10.0
WINDOW = 35.0                       # tolerate two missed beats
GRACE = 30.0                        # startup: workers boot at slightly different times

REACHABLE = Gauge("pulse_channel_layer_reachable_workers",
                  "distinct worker pids heard over the channel layer", ["pid"])
OBSERVED = Gauge("pulse_channel_layer_observed_workers",
                 "worker processes actually running on this node", ["pid"])
RATIO = Gauge("pulse_channel_layer_partition_ratio",
              "reachable / observed. 1.0 = healthy. THIS is the alert.", ["pid"])

_seen: dict[int, float] = defaultdict(float)


def _observed_workers() -> int:
    """Count sibling workers via /proc. The filesystem is shared; memory is not.

    That asymmetry is the whole trick: the thing being measured (shared memory)
    is exactly the thing we cannot use to measure it.
    """
    ppid = os.getppid()
    n = 0
    for entry in os.scandir("/proc"):
        if not entry.name.isdigit():
            continue
        try:
            with open(f"/proc/{entry.name}/stat") as fh:
                if int(fh.read().split(") ", 1)[1].split()[1]) == ppid:
                    n += 1
        except (OSError, IndexError, ValueError):
            continue
    return max(n, 1)


async def run():
    layer = get_channel_layer()
    me = os.getpid()
    started = time.monotonic()
    channel = await layer.new_channel()
    await layer.group_add(HEARTBEAT_GROUP, channel)

    async def listen():
        while True:
            msg = await layer.receive(channel)
            if msg.get("type") == "worker.beat":
                _seen[msg["pid"]] = time.monotonic()

    asyncio.create_task(listen())

    while True:
        await layer.group_send(HEARTBEAT_GROUP, {"type": "worker.beat", "pid": me})
        await asyncio.sleep(INTERVAL)

        cutoff = time.monotonic() - WINDOW
        reachable = sum(1 for t in _seen.values() if t > cutoff)
        observed = _observed_workers()
        REACHABLE.labels(pid=me).set(reachable)
        OBSERVED.labels(pid=me).set(observed)
        if time.monotonic() - started > GRACE:
            RATIO.labels(pid=me).set(reachable / observed)
```

Start it from the consumer app's `ready()` or, better, from a lifespan hook so
it starts once per worker.

### It fires

```bash
uvicorn pulse.asgi:application --loop uvloop --workers 4 &
sleep 45
curl -s localhost:8000/metrics | grep partition_ratio
```
**Expected — every worker reports the same verdict:**
```
pulse_channel_layer_partition_ratio{pid="54101"} 0.25
pulse_channel_layer_partition_ratio{pid="54102"} 0.25
pulse_channel_layer_partition_ratio{pid="54103"} 0.25
pulse_channel_layer_partition_ratio{pid="54104"} 0.25
```

With `--workers 1`, or with Module 07's `RedisChannelLayer` at `--workers 4`:
```
pulse_channel_layer_partition_ratio{pid="54219"} 1.0
```

**Time to fire:** one `INTERVAL` past `GRACE`, so **40 seconds** worst case,
inside the 60-second requirement.

The alert rule (Module 20 formalizes these):

```yaml
- alert: ChannelLayerPartitioned
  expr: min(pulse_channel_layer_partition_ratio) < 0.99
  for: 2m
  annotations:
    summary: "Workers cannot reach each other over the channel layer"
    description: "Messages are being delivered to a fraction of each room.
                  Nothing else will alert on this. Check CHANNEL_LAYERS."
```

### False positives, named

A detector nobody trusts is worse than none, so:

| Condition | Why it fires | Mitigation |
|-----------|--------------|-----------|
| **Rolling deploy** | Old and new workers coexist; `observed` counts both, `reachable` lags | `for: 2m` rides it out; Module 19 also drains before replacing |
| **Worker startup skew** | Worker 4 boots 8 s after worker 1 | The `GRACE` window |
| **A worker blocked > 35 s** | It missed its beats. Ratio drops — **and this is a true positive wearing a disguise**: a worker blocked for 35 s is a worse outage than a partition | Alert on it; correlate with `chat_event_loop_lag_seconds` (Module 06) |
| **`observed` counts a non-worker child** | Uvicorn's reloader, a `--reload` watcher, a profiler | Do not run `--reload` in anything you measure; the detector then also catches that mistake |
| **Multi-node deployment (Module 18)** | `_observed_workers()` only counts *this node*, so 3 nodes × 4 workers reads as `reachable=12, observed=4` → ratio 3.0 | Clamp to `min(1.0, reachable/observed)` and add a separate `reachable_nodes` gauge |

That last row is worth sitting with: **the detector's own model of "how many
workers should I see" is the fragile part**, not the measurement. In Kubernetes
the right source is the Deployment's replica count from the API, not `/proc` —
at which point the detector has become a config-drift detector too, which is a
feature.

---

## What the solutions taught

- **Client input contributes content and nothing else.** Identity, routing,
  timestamps and ids are stamped server-side from handshake state, and an
  explicit allowlist enforces it better than a code review does.
- **Be strict about what you accept from clients, liberal about what you accept
  from servers.** The asymmetry is deliberate and it is a protocol decision, not
  a style one.
- **A check on the fan-out path is multiplied by the amplification factor.** A
  per-delivery database query took one worker from 34% to 91% of its core; a
  cached flag with a stated 30-second exposure window cost 0.2 ms.
- **The wall is `1/workers`, deterministic per user pair, and invisible in
  staging.** The incident threshold is two workers, and there is no tuning
  between "one core" and "Redis".
- **You can write a cross-process channel layer in 60 lines** — and the list of
  what it does not do (liveness, backpressure, ordering, cross-machine, write
  contention, durability) is the actual argument for Redis, now written by you.
- **Nothing in a normal observability stack detects a partitioned channel
  layer.** You have to build the probe deliberately, and its weak point is its
  model of how many peers it should have.

Next: [Module 05 — Protocol & Domain Design](../../05-protocol-and-domain-design/)
replaces this module's two-field envelope with one you could ship. Then
[Module 06](../../06-load-testing-harness/) breaks the single worker on purpose,
and [Module 07](../../07-scale-out-redis-channel-layer/) finally takes the wall
down — and then shows you what the Pub/Sub layer loses when you pause Redis.
