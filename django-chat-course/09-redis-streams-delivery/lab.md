# Lab 09 — Stop Losing Messages

**You'll:** drive Streams from `redis-cli` to learn the protocol, then build a
custom Streams-backed fan-out in `redis-py` with per-worker consumer groups,
re-run Module 07's loss test and lose nothing, kill a worker mid-flight and watch
`XAUTOCLAIM` recover it, prove idempotency absorbs the duplicate, and measure
what durability costs.

⏱️ ~100 min. Work in `django-chat-course/apps/pulse`.

```bash
alias r='docker exec -i pulse-redis redis-cli'
```

All Redis work uses the **async** `redis-py` client (`redis.asyncio`), because it
runs inside the asyncio event loop that Channels lives in. Blocking the loop with
the *sync* client would stall every connection on the worker — the cardinal sin
of Module 01, which Module 15 measures. Confirm the client is present:

```bash
python -c "import redis.asyncio as r; print(r.Redis)"
```
**Expected:**
```
<class 'redis.asyncio.client.Redis'>
```
> `redis-py` ≥ 4.2 ships the async client in-tree (the old `aioredis` package is
> merged into it). Pin `redis>=5.0` in `requirements.txt`.

---

## Part A — Streams by hand first

Before writing Python, drive the whole protocol from `redis-cli`. Ten minutes
here saves an hour of debugging later.

```bash
r DEL 'room:{7}:stream'
r XADD 'room:{7}:stream' '*' payload 'first'
r XADD 'room:{7}:stream' '*' payload 'second'
r XLEN 'room:{7}:stream'
```
**Expected:**
```
"1735689600123-0"
"1735689600456-0"
(integer) 2
```

Create two groups — one per simulated worker process:

```bash
r XGROUP CREATE 'room:{7}:stream' worker-a 0 MKSTREAM
r XGROUP CREATE 'room:{7}:stream' worker-b 0 MKSTREAM
r XINFO GROUPS 'room:{7}:stream'
```
**Expected:**
```
1)  1) "name"              2) "worker-a"
    3) "consumers"         4) (integer) 0
    5) "pending"           6) (integer) 0
    7) "last-delivered-id" 8) "0-0"
2)  1) "name"              2) "worker-b"
    ...
```

> `0` as the start ID means "from the beginning." `$` means "only new entries."
> For a worker joining an existing room you want `$` — otherwise it replays the
> entire history on startup. The lab uses `0` here so you can see both entries.

Now read as worker-a. **Both groups get everything** — that's the replication
property that makes Option B a fan-out:

```bash
r XREADGROUP GROUP worker-a consumer-1 COUNT 10 STREAMS 'room:{7}:stream' '>'
r XREADGROUP GROUP worker-b consumer-1 COUNT 10 STREAMS 'room:{7}:stream' '>'
```
**Expected — identical output from both:**
```
1) 1) "room:{7}:stream"
   2) 1) 1) "1735689600123-0"
         2) 1) "payload" 2) "first"
      2) 1) "1735689600456-0"
         2) 1) "payload" 2) "second"
```

Now look at the PEL — nothing has been acked:

```bash
r XPENDING 'room:{7}:stream' worker-a
```
**Expected:**
```
1) (integer) 2
2) "1735689600123-0"
3) "1735689600456-0"
4) 1) 1) "consumer-1"
      2) "2"
```

Read `>` again — **nothing new**, because these entries were already delivered:

```bash
r XREADGROUP GROUP worker-a consumer-1 COUNT 10 STREAMS 'room:{7}:stream' '>'
```
**Expected:**
```
(nil)
```

But read `0` and you get **your own pending entries back**:

```bash
r XREADGROUP GROUP worker-a consumer-1 COUNT 10 STREAMS 'room:{7}:stream' 0
```
**Expected:** both entries again.

✅ **That is crash recovery.** A restarted worker reads `0` first to recover what
it was mid-delivery.

Acknowledge one and watch the PEL shrink:

```bash
r XACK 'room:{7}:stream' worker-a 1735689600123-0
r XPENDING 'room:{7}:stream' worker-a
```
**Expected:**
```
(integer) 1
1) (integer) 1
2) "1735689600456-0"
3) "1735689600456-0"
```

### Simulate a dead consumer

```bash
# consumer-1 "dies" holding one entry. consumer-2 claims it after 5s idle.
sleep 6
r XAUTOCLAIM 'room:{7}:stream' worker-a consumer-2 5000 0 COUNT 10
```
**Expected:**
```
1) "0-0"                                   # next cursor
2) 1) 1) "1735689600456-0"
      2) 1) "payload" 2) "second"
3) (empty array)                           # entries that no longer exist
```
```bash
r XPENDING 'room:{7}:stream' worker-a - + 10
```
**Expected — ownership transferred:**
```
1) 1) "1735689600456-0"
   2) "consumer-2"
   3) (integer) 142
   4) (integer) 2                          # delivery count is now 2
```

✅ **The entry moved to a live consumer and its delivery count incremented.**
That delivery count is how you detect poison messages — an entry delivered 10
times is one nobody can process (Challenge Task 1).

---

## Part B — The Streams fan-out

Now build it in Python. `apps/pulse/chat/streams.py`:

```python
import json
import os
import time

import redis.asyncio as aioredis
from prometheus_client import Counter, Histogram

# A unique id for THIS worker process. Group name == worker id, so every worker
# process gets its own group and therefore every entry (the replication property).
# os.getpid() is stable for the life of the process; the node name disambiguates
# across machines. This is "node-a" in the JVM twin, one per process here.
WORKER_ID = f"{os.environ.get('PULSE_NODE_ID', 'node')}-{os.getpid()}"

STREAM_MAXLEN = int(os.environ.get("PULSE_STREAM_MAXLEN", "10000"))

_appended = Counter("pulse_stream_appended_total", "entries XADDed")
_delivered = Counter("pulse_stream_delivered_total", "entries broadcast locally")
_duplicates = Counter("pulse_stream_duplicates_total", "redeliveries absorbed by client_id")
_claimed = Counter("pulse_stream_claimed_total", "entries recovered via XAUTOCLAIM")
_append_latency = Histogram("pulse_stream_append_seconds", "XADD latency")


def stream_key(room_id: str) -> str:
    # Hash tag {room_id} keeps the stream and its seq counter (Module 10) in the
    # same Cluster slot, so a future Lua script can touch both atomically.
    return f"room:{{{room_id}}}:stream"


class StreamFanout:
    """Owns the async redis client and the XADD side of the fan-out."""

    def __init__(self, url: str = None):
        self.redis = aioredis.from_url(
            url or os.environ.get("REDIS_URL", "redis://localhost:6379"),
            decode_responses=True,
        )

    async def append(self, room_id: str, envelope: dict) -> str:
        """Publish a message to the room's durable stream. Returns the entry id."""
        payload = json.dumps(envelope, separators=(",", ":"))
        start = time.perf_counter()
        # maxlen with approximate=True == 'MAXLEN ~': trim whole macro-nodes only.
        # The ~ is not a nicety — exact trimming is O(n) on every single XADD.
        entry_id = await self.redis.xadd(
            stream_key(room_id),
            {"payload": payload},
            maxlen=STREAM_MAXLEN,
            approximate=True,
        )
        _append_latency.observe(time.perf_counter() - start)
        _appended.inc()
        return entry_id


# Process-wide singletons. One redis connection pool per worker.
fanout = StreamFanout()
```

The `LocalRegistry` — what replaces the channel layer's group membership.
`apps/pulse/chat/registry.py`:

```python
from collections import defaultdict


class LocalRegistry:
    """
    room_id -> set of connected consumers ON THIS WORKER PROCESS ONLY.

    This is the InMemoryChannelLayer reduced to its one honest job (Module 04):
    deliver to local sockets. The cross-process hop is the Redis stream, so this
    never needs to reach another process — which is exactly why an in-memory dict
    is correct here where it was fatally wrong in Module 04.
    """

    def __init__(self):
        self._rooms: dict[str, set] = defaultdict(set)

    def add(self, room_id: str, consumer) -> bool:
        first = len(self._rooms[room_id]) == 0
        self._rooms[room_id].add(consumer)
        return first  # True if this is the room's first local subscriber

    def remove(self, room_id: str, consumer) -> bool:
        self._rooms[room_id].discard(consumer)
        empty = len(self._rooms[room_id]) == 0
        if empty:
            self._rooms.pop(room_id, None)
        return empty  # True if that was the last local subscriber

    def subscribers(self, room_id: str):
        return list(self._rooms.get(room_id, ()))

    def active_rooms(self):
        return list(self._rooms.keys())


registry = LocalRegistry()
```

---

## Part C — The three-phase consumer loop

The heart of the module: recover mine, read new, claim the dead. One asyncio
task per active room, started when this worker gains its first local subscriber
for that room. `apps/pulse/chat/consumer_loop.py`:

```python
import asyncio
import json
import logging

from channels.db import database_sync_to_async

from .registry import registry
from .streams import fanout, stream_key, WORKER_ID, _delivered, _duplicates, _claimed

log = logging.getLogger("pulse.streams")

CLAIM_MIN_IDLE_MS = 30_000     # only steal work idle for 30s (must exceed p99.9 processing)
CLAIM_SWEEP_EVERY = 30.0       # run XAUTOCLAIM every 30s
READ_BLOCK_MS = 2_000
READ_COUNT = 100


@database_sync_to_async
def persist_idempotent(envelope: dict) -> bool:
    """
    Insert the message; return True if newly created, False if it was a retry.
    The Django ORM is SYNC — calling it directly in this async loop would block
    the event loop and stall every socket on the worker (Module 01, measured in
    Module 15). database_sync_to_async moves it to a threadpool.

    The unique constraint (room_id, client_id) from Module 05 does the dedup.
    """
    from .models import Message  # the model built in Module 05

    data = envelope["data"]
    _obj, created = Message.objects.get_or_create(
        room_id=envelope["room"],
        client_id=data["client_id"],
        defaults={
            "id": data["id"],
            "seq": data["seq"],
            "sender": data["sender"],
            "body": data["body"],
            "reply_to": data.get("reply_to"),
        },
    )
    return created


class StreamConsumerManager:
    """One consumer task per room, per worker process."""

    def __init__(self):
        self._tasks: dict[str, asyncio.Task] = {}

    def group(self) -> str:
        return WORKER_ID

    async def ensure_consuming(self, room_id: str):
        if room_id in self._tasks:
            return
        await self._ensure_group(room_id)
        self._tasks[room_id] = asyncio.create_task(self._consume(room_id))

    async def stop_consuming(self, room_id: str):
        task = self._tasks.pop(room_id, None)
        if task:
            task.cancel()

    async def _ensure_group(self, room_id: str):
        try:
            # '$' = only new entries. Starting at 0 would replay the whole room
            # history to a worker that just gained one subscriber.
            await fanout.redis.xgroup_create(
                stream_key(room_id), self.group(), id="$", mkstream=True
            )
        except aioredis_error_busygroup:
            pass  # group already exists — fine

    async def _consume(self, room_id: str):
        key = stream_key(room_id)

        # PHASE 1 — recover entries THIS consumer had in flight when it died.
        await self._recover_own_pending(room_id, key)

        last_sweep = asyncio.get_event_loop().time()
        while True:
            try:
                # PHASE 2 — new entries. '>' == ReadOffset.lastConsumed. BLOCK so
                # we are not polling. Getting '>' vs '0' backwards is THE classic
                # Streams bug: '0' here re-reads your PEL forever, never seeing new.
                resp = await fanout.redis.xreadgroup(
                    self.group(), WORKER_ID, {key: ">"},
                    count=READ_COUNT, block=READ_BLOCK_MS,
                )
                for _stream, entries in resp or []:
                    for entry_id, fields in entries:
                        await self._process_and_ack(room_id, key, entry_id, fields)

                # PHASE 3 — periodically claim work abandoned by dead workers.
                now = asyncio.get_event_loop().time()
                if now - last_sweep > CLAIM_SWEEP_EVERY:
                    await self._claim_abandoned(room_id, key)
                    last_sweep = now

            except asyncio.CancelledError:
                raise
            except Exception:
                log.warning("consume loop error for room %s, backing off", room_id, exc_info=True)
                await asyncio.sleep(1.0)   # do not hot-spin against a dead Redis

    async def _recover_own_pending(self, room_id: str, key: str):
        while True:
            resp = await fanout.redis.xreadgroup(
                self.group(), WORKER_ID, {key: "0"},   # '0' == MY pending
                count=READ_COUNT,
            )
            entries = resp[0][1] if resp else []
            if not entries:
                return
            log.info("recovering %d pending entries for room %s", len(entries), room_id)
            for entry_id, fields in entries:
                await self._process_and_ack(room_id, key, entry_id, fields)

    async def _claim_abandoned(self, room_id: str, key: str):
        # xautoclaim returns (next_cursor, claimed_entries, deleted_ids).
        cursor = "0-0"
        while True:
            cursor, entries, _deleted = await fanout.redis.xautoclaim(
                key, self.group(), WORKER_ID,
                min_idle_time=CLAIM_MIN_IDLE_MS, start_id=cursor, count=READ_COUNT,
            )
            for entry_id, fields in entries:
                _claimed.inc()
                await self._process_and_ack(room_id, key, entry_id, fields)
            if cursor == "0-0":
                break   # XAUTOCLAIM is paginated; loop until the cursor wraps

    async def _process_and_ack(self, room_id, key, entry_id, fields):
        """
        ACK AFTER processing. This is the at-least-once choice: a crash between
        deliver and xack causes a redelivery, which persist_idempotent absorbs.
        Acking first would be at-most-once (Challenge Task 4 measures both).
        """
        try:
            envelope = json.loads(fields["payload"])
            created = await persist_idempotent(envelope)
            if not created:
                # A redelivery. The row already exists — do NOT broadcast a
                # second time. This is the exactly-once illusion, working.
                _duplicates.inc()
            else:
                for sub in registry.subscribers(room_id):
                    await sub.send_json(envelope)
                _delivered.inc()
            await fanout.redis.xack(key, self.group(), entry_id)
        except Exception:
            # Do NOT ack. The entry stays in the PEL and will be redelivered or
            # claimed. If it is poison, the delivery count reveals it (Task 1).
            log.error("delivery failed for %s in room %s", entry_id, room_id, exc_info=True)


# redis-py raises redis.exceptions.ResponseError with 'BUSYGROUP' in the message.
from redis.exceptions import ResponseError


class aioredis_error_busygroup(ResponseError):
    pass


# Small helper so the try/except above reads cleanly:
def _is_busygroup(exc: Exception) -> bool:
    return isinstance(exc, ResponseError) and "BUSYGROUP" in str(exc)


manager = StreamConsumerManager()
```

> **`{key: ">"}` vs `{key: "0"}` is the single most important line in this file.**
> `>` delivers new entries and adds them to your PEL. `0` re-reads your existing
> PEL. Reading `0` in the main loop means you reprocess your pending list forever
> and never see a new message — a bug that passes every unit test and fails in
> production the moment a real backlog exists.

Fix the `_ensure_group` except clause to use the real check (the class above was
illustrative):

```python
    async def _ensure_group(self, room_id: str):
        try:
            await fanout.redis.xgroup_create(
                stream_key(room_id), self.group(), id="$", mkstream=True
            )
        except ResponseError as e:
            if "BUSYGROUP" not in str(e):
                raise
```

---

## Part D — Wire it into the consumer

`apps/pulse/chat/consumers.py` — the `AsyncJsonWebsocketConsumer` from Module 04,
now talking to Streams instead of `group_send`:

```python
from channels.generic.websocket import AsyncJsonWebsocketConsumer

from .registry import registry
from .consumer_loop import manager
from .streams import fanout
from .sequence import allocate_seq   # Module 10 builds this; a Redis INCR for now


class ChatConsumer(AsyncJsonWebsocketConsumer):

    async def connect(self):
        self.user = self.scope["user"]
        self.rooms = set()
        await self.accept()

    async def disconnect(self, code):
        for room_id in list(self.rooms):
            await self._leave(room_id)

    async def receive_json(self, content):
        mtype = content.get("type")
        if mtype == "join":
            await self._join(content["room"])
        elif mtype == "message.create":
            await self._on_message(content)

    async def _join(self, room_id: str):
        self.rooms.add(room_id)
        first = registry.add(room_id, self)
        if first:
            # First local subscriber for this room ⇒ start this worker's consumer.
            await manager.ensure_consuming(room_id)

    async def _leave(self, room_id: str):
        self.rooms.discard(room_id)
        empty = registry.remove(room_id, self)
        if empty:
            await manager.stop_consuming(room_id)

    async def _on_message(self, content):
        room_id = content["room"]
        data = content["data"]
        seq = await allocate_seq(room_id)
        envelope = {
            "v": 1, "type": "message.new", "room": room_id, "ts": now_ms(),
            "data": {
                "id": new_server_id(), "client_id": data["client_id"], "seq": seq,
                "sender": self.user.username, "body": data["body"],
                "reply_to": data.get("reply_to"),
            },
        }
        # The ONLY thing the inbound path does now: allocate seq, XADD, ack sender.
        # Persistence and broadcast happen in the consumer loop (Part C), so a
        # redelivery re-runs both and the idempotent insert absorbs it.
        entry_id = await fanout.append(room_id, envelope)
        await self.send_json({"v": 1, "type": "ack", "room": room_id,
                              "data": {"client_id": data["client_id"], "seq": seq,
                                       "entry_id": entry_id}})
```

(`allocate_seq`, `now_ms`, `new_server_id` are one-liners; Module 10 hardens
`allocate_seq` with Postgres recovery.)

Start two workers so you have two consumer groups:

```bash
PULSE_NODE_ID=node-a uvicorn pulse.asgi:application --port 8000 &
PULSE_NODE_ID=node-b uvicorn pulse.asgi:application --port 8001 &
```

---

## Part E — Re-run the loss test

**The moment of truth.** Same script as Module 07, unchanged.

```bash
./code/loss_test.sh
```

**Expected — Module 07 with the RedisChannelLayer (Pub/Sub):**
```
published: 200   received: 171   LOST: 29
```

**Expected — now, with Streams:**
```
publishing 1..200 via node-a, pausing redis at message 80
>>> docker pause pulse-redis
>>> docker unpause pulse-redis
published: 200   received: 200   LOST: 0
```

✅ **Zero lost.**

Watch what happened during the pause:

```bash
r XINFO GROUPS 'room:{9}:stream'
```
**Expected right after the unpause:**
```
1) 1) "name"              2) "node-b-48213"
   3) "consumers"         4) (integer) 1
   5) "pending"           6) (integer) 27          <-- the backlog
   7) "last-delivered-id" 8) "1735689612891-0"
   9) "entries-read"     10) (integer) 200
  11) "lag"              12) (integer) 0
```

And a few seconds later:
```
   5) "pending"           6) (integer) 0
```

The 27 entries node-b couldn't receive during the pause were **still in the
stream**. When it reconnected, `XREADGROUP >` delivered them in order. Nothing
retried, nothing was cleverly recovered — they were simply *stored*.

Now the harder variant. Kill Redis entirely with persistence off:

```bash
docker kill pulse-redis && docker start pulse-redis
./code/loss_test.sh
```
**Expected:**
```
published: 200   received: 143   LOST: 57
```

⚠️ **Streams do not survive a Redis restart without persistence.** The stream is
in memory. This is the gap Module 13's outbox closes — Postgres holds the message
and can republish.

Note it honestly in `results.md`:
```markdown
- Streams, Redis PAUSED 1.5s:    0/200 lost   (was 29/200 with the channel layer)
- Streams, Redis KILLED+restart: 57/200 lost  (needs the outbox — Module 13)
```

---

## Part F — Kill a worker mid-delivery

Make delivery slow so you can kill it in the middle. Add a debug hook that sleeps
in `persist_idempotent`:

```bash
export PULSE_SLOW_DELIVERY_MS=3000     # read by persist_idempotent when set
```

Publish 20 messages to room 11, then SIGKILL node-b while it's grinding:

```bash
for i in $(seq 1 20); do ./code/publish.sh room.11 "kill-test-$i"; done
sleep 5
kill -9 $(pgrep -f 'PULSE_NODE_ID=node-b')

r XPENDING 'room:{11}:stream' node-b-48213
```
**Expected:**
```
1) (integer) 18
2) "1735689700123-0"
3) "1735689700890-0"
4) 1) 1) "48213"
      2) "18"
```

18 entries stranded in a dead worker's PEL. Restart node-b:

```bash
PULSE_NODE_ID=node-b uvicorn pulse.asgi:application --port 8001 &
```

**Expected in the log:**
```
INFO pulse.streams: recovering 18 pending entries for room 11
```

> ⚠️ **A restarted worker has a NEW pid, so a new WORKER_ID, so a new group.** Its
> old group's PEL still holds those 18 entries and nobody is reading it. This is a
> real design decision, and it differs from the JVM twin (where the node id is
> stable across restarts). Two honest options:
>
> 1. **Stable worker id** — derive `WORKER_ID` from `PULSE_NODE_ID` + a worker
>    *index* (0..N-1) assigned by your process manager, not the pid. Then a
>    restarted worker rejoins its own group and Phase 1 recovers its PEL. This is
>    what Pulse ships; set `PULSE_WORKER_INDEX` from your supervisor.
> 2. **Let XAUTOCLAIM handle it** — another live worker's Phase 3 claims the dead
>    group's entries after `min_idle`. This works too, but only if some worker
>    scans *other* groups' PELs, which needs `XPENDING` discovery.

Switch to the stable id and repeat — Phase 1 now recovers cleanly:

```bash
r XPENDING 'room:{11}:stream' node-b-0
```
**Expected:**
```
1) (integer) 0
```

✅ **Phase 1 of the consumer loop recovered every stranded entry**, because they
were still in the PEL.

Now the case where the worker never comes back — a *different* worker claims:

```bash
kill -9 $(pgrep -f 'PULSE_NODE_ID=node-b')
sleep 35
r XAUTOCLAIM 'room:{11}:stream' node-b-0 rescuer 30000 0 COUNT 100
```
**Expected:**
```
1) "0-0"
2) 1) 1) "1735689700123-0"
      2) 1) "payload" 2) "{\"v\":1,...}"
   ... 17 more
3) (empty array)
```

✅ Ownership transferred to a live consumer, which will process and ack them.

> **The 30-second `min-idle-time` is a real design parameter.** Too short and you
> steal work from a worker that's merely slow (a `database_sync_to_async`
> threadpool backed up, say), causing duplicates. Too long and recovery from a
> genuine crash is slow. It should be comfortably longer than your p99.9
> processing time.

---

## Part G — Prove the duplicate is harmless

Force a redelivery and confirm nothing bad happens. Skip the ack for 5 entries:

```bash
export PULSE_SKIP_ACK=5      # persist+broadcast but do NOT xack the next 5
for i in $(seq 1 5); do ./code/publish.sh room.12 "dup-test-$i"; done

r XPENDING 'room:{12}:stream' node-b-0
```
**Expected:**
```
1) (integer) 5
```

Unset the flag and restart node-b; the 5 entries are redelivered:

**Expected in the log:**
```
INFO  pulse.streams : recovering 5 pending entries for room 12
DEBUG pulse.streams : retry detected for client_id c-dup-test-1
DEBUG pulse.streams : retry detected for client_id c-dup-test-2
...
```

```bash
docker exec pulse-postgres psql -U pulse -d pulse -c \
  "SELECT client_id, count(*) FROM chat_message WHERE room_id='room.12' GROUP BY 1 ORDER BY 1;"
```
**Expected:**
```
   client_id    | count
----------------+-------
 c-dup-test-1   |     1
 c-dup-test-2   |     1
 c-dup-test-3   |     1
 c-dup-test-4   |     1
 c-dup-test-5   |     1
```

✅ **Delivered twice, stored once.** The `client_id` from Module 05 plus the
`unique_together = (room_id, client_id)` constraint absorbed it. `get_or_create`
returned `created=False` on the redelivery, so `persist_idempotent` returned
`False` and the broadcast was suppressed. That's the exactly-once illusion.

Check the duplicates counter:
```bash
curl -s localhost:8000/metrics | grep pulse_stream_duplicates_total
```
```
pulse_stream_duplicates_total 5.0
```

---

## Part H — Measure what durability costs

Same k6 workload as Modules 06 and 07 (100 rooms, 1 msg/user/60s, ramp to the
knee).

```bash
k6 run -e ROOMS=100 -e SEND_EVERY=60000 ../06-load-testing-harness/code/pulse-load.js
```

**Expected** (reference machine: 8-core / 16 GB, Python 3.12, Uvicorn+uvloop,
8 workers):

| | Module 06 (1 node) | Module 07 (channel layer) | Module 09 (Streams) |
|---|-------------------|---------------------------|---------------------|
| p50 | 11 ms | 15 ms | **20 ms** |
| p95 | 52 ms | 60 ms | **71 ms** |
| p99 | 138 ms | 158 ms | **195 ms** |
| Knee (outbound msg/s) | 150,000 | 285,000 | **255,000** |
| Redis CPU at 120k out/s | n/a | 26% | **52%** |
| Redis memory | n/a | ~40 MB | **1.9 GB** |
| Messages lost (Redis pause) | n/a | **29/200** | **0/200** |

### Reading the tradeoff

**+5 ms p50, +37 ms p99, ~10% less throughput, and ~47× the Redis memory — for
zero message loss.**

Where the extra latency and CPU go:
```bash
r INFO commandstats | grep -E 'cmdstat_(xadd|xreadgroup|xack)'
```
```
cmdstat_xadd:calls=284119,usec=511414,usec_per_call=1.80
cmdstat_xreadgroup:calls=91204,usec=2189896,usec_per_call=24.01
cmdstat_xack:calls=284119,usec=340943,usec_per_call=1.20
```

`XADD` and `XACK` are ~1.5 µs. `XREADGROUP` is 24 µs — it does more work
(updating the PEL, tracking last-delivered) and returns batches. Three commands
per message instead of one, plus PEL bookkeeping. **Redis CPU doubling is the
real cost**, and in Python it doubles sooner than on the JVM: every worker
*process* reads and acks, so with 8 workers per node each entry is touched 8×
per node, not once. This is the "Python twist" from the README made numeric, and
it's what pushes you to Cluster (Module 13).

The memory is the number to plan around:
```bash
r MEMORY USAGE 'room:{7}:stream'
r XLEN 'room:{7}:stream'
```
```
6144912
10214
```
**~600 bytes per entry** at `MAXLEN ~ 10000` = ~6 MB per room. **1,000 rooms =
6 GB.** That is a capacity plan, and it's why `MAXLEN` is not optional.

Try `MINID` instead — bound by time, not count:
```bash
r XTRIM 'room:{7}:stream' MINID '~' $(( ($(date +%s) - 600) * 1000 ))
r XLEN 'room:{7}:stream'
```
For a quiet room this keeps far fewer entries; for a busy one it keeps more. **It
bounds your replay *window*, which is what a reconnecting client actually needs**
(Module 10), rather than an arbitrary count. The challenge sizes it from data.

---

## Part I — PEL monitoring

The PEL is your backlog gauge. Wire it up now; Module 20 alerts on it. Run it as
a periodic asyncio task on each worker:

```python
import asyncio
from prometheus_client import Gauge

from .streams import fanout, stream_key
from .registry import registry
from .consumer_loop import manager

pending_gauge = Gauge("pulse_stream_pending", "unacked entries", ["room"])
lag_gauge = Gauge("pulse_stream_lag", "undelivered entries", ["room"])


async def sample_pel_forever():
    while True:
        for room_id in registry.active_rooms():
            key = stream_key(room_id)
            try:
                groups = await fanout.redis.xinfo_groups(key)
            except Exception:
                continue
            for g in groups:
                if g["name"] != manager.group():
                    continue
                pending_gauge.labels(room=room_id).set(g["pending"])
                # 'lag' = entries added but not yet delivered to this group.
                lag_gauge.labels(room=room_id).set(g.get("lag") or 0)
        await asyncio.sleep(10)
```

Start it from your ASGI `lifespan` / app-ready hook so there's exactly one per
worker:

```python
# pulse/asgi.py, after the app is built
asyncio.get_event_loop().create_task(sample_pel_forever())
```

```bash
watch -n2 'curl -s localhost:8000/metrics | grep -E "pulse_stream_(pending|lag)" | head'
```
**Expected at healthy load:**
```
pulse_stream_pending{room="7"} 0.0
pulse_stream_lag{room="7"} 0.0
```
**Expected when a worker is struggling** (a slow threadpool, say):
```
pulse_stream_pending{room="7"} 4821.0
pulse_stream_lag{room="7"} 18402.0
```

✅ **`pending` and `lag` mean different things and you need both.** High
`pending` means you're reading fast but processing/acking slowly — a backed-up
`database_sync_to_async` threadpool is the usual Python cause. High `lag` means
you're not *reading* fast enough — bump `count`, or the worker's loop is starved
because something is blocking the event loop (Module 15). The fixes are
different, so the two gauges are not redundant.

Record it:
```markdown
## Module 09 — Streams

- Channel-layer loss (redis pause 1.5s): 29/200  ->  Streams: 0/200
- Streams, redis KILLED (no persistence): 57/200 lost (outbox needed, Module 13)
- Latency cost: +5ms p50, +37ms p99 vs channel layer
- Throughput cost: 285k -> 255k outbound msg/s (-10%)
- Redis CPU: 26% -> 52% (3 commands/msg + PEL bookkeeping, ×workers-per-node)
- Redis memory: 40MB -> 1.9GB (~600 bytes/entry at MAXLEN ~10000)
- Duplicate delivery on redelivery: absorbed by (room_id, client_id) constraint
- XAUTOCLAIM min-idle: 30s (must exceed p99.9 processing time)
- Worker id must be STABLE across restarts (worker index, not pid)
```

---

## What you built

- A **custom Streams-backed fan-out** in `redis-py` async, because
  `channels_redis` is a Pub/Sub transport that cannot replay — the defining
  Django task of this module.
- Per-worker consumer groups giving **replication plus acknowledgement**, with a
  `LocalRegistry` doing the local hop the channel layer used to.
- A three-phase consumer loop: recover own pending, read new, claim abandoned.
- **Zero message loss** across a Redis pause, verified with the same script that
  lost 29 messages in Module 07.
- Crash recovery proven twice: same worker restarting (with a stable id), and a
  different worker claiming.
- Duplicate delivery proven harmless via Module 05's idempotency and
  `get_or_create`.
- The measured price of durability, sharpened by the process-per-core model, and
  the memory model to budget for it.
- PEL and lag gauges — the two numbers that tell you a worker is falling behind.

**Remaining gap:** the last hop. A *client* that disconnects still misses
messages, and still can't tell. That's Module 10.

Now do [`challenge.md`](./challenge.md).

Then: [Module 10 — Ordering & Delivery Semantics](../10-ordering-and-delivery-semantics/).

For the JVM's take on the identical problem — Spring's `SimpMessagingTemplate`
and `spring-data-redis` streams, one group per node rather than per process —
see [`spring-boot-chat-course/09-redis-streams-delivery`](../../spring-boot-chat-course/09-redis-streams-delivery/).
The shape is the same; the process-per-core multiplier on the group count is the
part that is uniquely Python.
