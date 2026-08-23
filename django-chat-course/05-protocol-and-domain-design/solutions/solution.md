# Solutions 05 — Harden the Protocol

Reference answers, the reasoning, the rejected alternatives, and the numbers.
Reference machine: **8-core / 16 GB, Ubuntu 24.04, Python 3.12, Django 5.1,
Channels 4.1, Postgres 16 in Docker, Uvicorn + uvloop, one worker.**

---

## Task 1 — The sequence hole

### Proving it

```python
# chat/tests_protocol.py
import asyncio, json
from django.test import TransactionTestCase        # NOT TestCase: we need real commits
import websockets

from chat.ids import ulid
from chat.models import Message, Room, RoomSequence


class SequenceContiguity(TransactionTestCase):
    URL = "ws://localhost:8000/ws/room/general/?as=u0"

    def _seqs(self):
        return list(Message.objects.filter(room__slug="general")
                    .order_by("seq").values_list("seq", flat=True))

    def test_retries_do_not_burn_sequences(self):
        cid = ulid()

        async def attempt():
            async with websockets.connect(self.URL, ping_interval=None) as ws:
                await ws.recv()
                await ws.send(json.dumps({"v": 1, "type": "message.create",
                                          "data": {"client_id": cid, "body": "x"}}))
                while True:
                    env = json.loads(await ws.recv())
                    if env["type"] == "message.ack":
                        return env["data"]

        async def storm():
            async with asyncio.TaskGroup() as tg:
                return [tg.create_task(attempt()) for _ in range(64)]

        before = RoomSequence.objects.get(room__slug="general").last_seq
        asyncio.run(storm())
        after = RoomSequence.objects.get(room__slug="general").last_seq

        self.assertEqual(Message.objects.filter(client_id=cid).count(), 1)
        self.assertEqual(after - before, 1,
                         f"burned {after - before - 1} sequence numbers")
        seqs = self._seqs()
        self.assertEqual(seqs, list(range(seqs[0], seqs[0] + len(seqs))),
                         "sequences are not contiguous")
```

```
FAIL: test_retries_do_not_burn_sequences
AssertionError: 64 != 1 : burned 63 sequence numbers
```

### The fix

The bug is an ordering bug: the counter is bumped unconditionally, before the
insert decides whether it will happen. Reorder so **only the winning insert
advances the counter**, and take a row lock so two winners cannot pick the same
number.

```python
# chat/service.py
@database_sync_to_async
def send_message(*, room_id, sender_id, client_id, body, reply_to=None) -> SendResult:
    with transaction.atomic(), connection.cursor() as cur:
        # 1. FAST PATH: is this a retry? No lock, no allocation, no contention.
        #    In a retry storm this is the branch 63 of 64 attempts take.
        cur.execute("""
            SELECT id, seq, created_at FROM chat_message
            WHERE room_id = %s AND client_id = %s
        """, [room_id, client_id])
        if (row := cur.fetchone()) is not None:
            return SendResult(row[0], row[1], int(row[2].timestamp() * 1000), True)

        # 2. Serialize writers FOR THIS ROOM ONLY. Other rooms are unaffected:
        #    the lock is on one row of chat_roomsequence.
        cur.execute("""
            INSERT INTO chat_roomsequence (room_id, last_seq) VALUES (%s, 0)
            ON CONFLICT (room_id) DO NOTHING
        """, [room_id])
        cur.execute("SELECT last_seq FROM chat_roomsequence WHERE room_id = %s "
                    "FOR UPDATE", [room_id])
        next_seq = cur.fetchone()[0] + 1

        # 3. Insert. Still ON CONFLICT DO NOTHING, because a racer may have
        #    committed between step 1's snapshot and step 2's lock.
        cur.execute("""
            INSERT INTO chat_message
                (room_id, sender_id, client_id, seq, body, reply_to_id, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, now())
            ON CONFLICT (room_id, client_id) DO NOTHING
            RETURNING id, seq, created_at
        """, [room_id, sender_id, client_id, next_seq, body, reply_to])
        row = cur.fetchone()

        if row is None:
            # We lost the race after taking the lock. Release it WITHOUT
            # bumping -- this is the entire fix.
            cur.execute("SELECT id, seq, created_at FROM chat_message "
                        "WHERE room_id = %s AND client_id = %s", [room_id, client_id])
            row = cur.fetchone()
            return SendResult(row[0], row[1], int(row[2].timestamp() * 1000), True)

        # 4. We won. NOW advance the counter, inside the same transaction.
        cur.execute("UPDATE chat_roomsequence SET last_seq = %s WHERE room_id = %s",
                    [next_seq, room_id])
        return SendResult(row[0], row[1], int(row[2].timestamp() * 1000), False)
```

```
test_retries_do_not_burn_sequences ... ok
test_distinct_messages_get_contiguous_sequences ... ok
```

The second test matters as much as the first — a fix that makes retries safe by
serializing everything through a single value would be trivially "correct" and
useless:

```python
    def test_distinct_messages_get_contiguous_sequences(self):
        # 64 DIFFERENT client_ids, concurrently.
        ...
        self.assertEqual(len(set(seqs)), 64)
        self.assertEqual(sorted(seqs), list(range(min(seqs), min(seqs) + 64)))
```

### The cost

Sustained `message.create` throughput, one room, one worker, `DEBUG=0`:

| Version | msg/s into **one** room | msg/s across **64** rooms | Correct? |
|---------|------------------------|---------------------------|----------|
| Lab version (bump first) | 4,120 | 4,090 | ❌ burns sequences |
| Fixed (lock, bump on win) | **2,850** | **4,060** | ✅ |
| Fixed, retry-heavy (90% duplicates) | **9,400** | 9,380 | ✅ |

Three readings:

1. **−31% on a single hot room.** `FOR UPDATE` serializes writers for that room,
   so per-room write throughput is now bounded by lock hold time (~0.35 ms). This
   is a real ceiling and it is the right shape: a room is a serial thing.
   Messages in different rooms do not contend, which the 64-room column proves.
2. **Retries got 3.3× faster**, because the fast path in step 1 does one indexed
   lookup and returns — no lock, no allocation, no write. The workload the fix
   was written for is the workload it optimizes.
3. **2,850 msg/s into one room is far above anything real.** Module 06's
   moderate-load baseline is 333 inbound msg/s across 100 rooms. A single room
   sustaining 2,850 msg/s is a room with tens of thousands of active typers.
   Module 14 revisits per-room write ceilings when it shards.

### The rejected alternatives

| Alternative | Why not |
|-------------|---------|
| **A Postgres `SEQUENCE` per room** | Sequences are *deliberately* non-transactional — that is their entire value. A rolled-back or conflicting insert burns the value, which is precisely the bug. Also: one relation per room does not scale to a million rooms. |
| **`INCR room:{id}:seq` in Redis** | ~0.1 ms and no lock, so it is faster. But the counter now lives in a different system from the row, so a crash between `INCR` and `INSERT` burns a number — the same bug in a new place — and you cannot roll it back. Module 10 revisits this **with** Module 13's transactional outbox, which is what makes it safe. |
| **`row_number() OVER (ORDER BY id)` at read time** | No burn is possible, and it is genuinely elegant. But `seq` must be known at *ack* time so the client can render "sent ✓" and store a resume cursor, and a read-time sequence changes when a row is deleted. Both are fatal for Module 10. |
| **`SERIALIZABLE` isolation and retry on 40001** | Correct, and it moves the contention from an explicit lock you can reason about to a serialization failure you must handle everywhere. `FOR UPDATE` on one well-known row is easier to explain in an incident. |

> **The general lesson:** an idempotency key protects the *insert*. It does not
> protect side effects you perform *before* deciding whether the insert will
> happen. Audit every "allocate, then maybe write" pair in a system that
> retries — sequence numbers, ID reservations, quota decrements, outbound
> webhook slots. This class of bug leaves no error in any log.

---

## Task 2 — Typing indicators that do not melt the room

### The three layers

**Client (debounce).**

```js
let lastTyping = 0;
input.addEventListener("input", () => {
  const now = Date.now();
  if (now - lastTyping > 3000) {                 // at most 1 per 3s
    lastTyping = now;
    ws.send(JSON.stringify({v: 1, type: "typing.start", data: {}}));
  }
});
```

**Server (aggregate + expire).** One task per room per worker, emitting at 1 Hz
only when something changed:

```python
# chat/typing.py
import asyncio, time
from collections import defaultdict

from channels.layers import get_channel_layer

TYPING_TTL = 5.0          # a silent typer disappears after this
TICK = 1.0                # at most one typing.update per room per second

_typers: dict[str, dict[str, float]] = defaultdict(dict)   # room -> {user: expires}
_dirty: set[str] = set()
_task: asyncio.Task | None = None


def note_typing(room: str, user: str) -> None:
    _typers[room][user] = time.monotonic() + TYPING_TTL
    _dirty.add(room)


async def _pump():
    layer = get_channel_layer()
    while True:
        await asyncio.sleep(TICK)
        now = time.monotonic()
        for room in list(_typers):
            live = {u: e for u, e in _typers[room].items() if e > now}
            if live != _typers[room]:
                _dirty.add(room)                  # someone expired
            _typers[room] = live
            if room in _dirty:
                _dirty.discard(room)
                await layer.group_send(room, {"type": "chat.typing",
                                              "users": sorted(live)})
                if not live:
                    _typers.pop(room, None)


def start():
    global _task
    if _task is None:
        _task = asyncio.ensure_future(_pump())
```

```python
# chat/consumers.py
    async def _on_typing_start(self, data):
        note_typing(self.group, self.user.username)

    async def chat_typing(self, event):
        await self.send_json(envelope("typing.update", self.group, now_ms(),
                                      users=event["users"]))
```

### The measurement

200-member room, 20 people typing simultaneously for 60 seconds, keystroke rate
4/s each:

| Layer | Frames/s to clients | Reduction |
|-------|--------------------|-----------|
| Naive: one `typing.update` per keystroke | 20 × 4 × 200 = **16,000** | — |
| + client debounce (1 per 3 s) | 20 × 0.33 × 200 = **1,333** | 12× |
| + server aggregation (1 per room per second) | 1 × 200 = **200** | **80×** |
| + suppress when unchanged (measured, real typing) | **137** | **117×** |

✅ **80× by construction, 117× measured**, because real typists pause and the
"only emit when the set changed" rule skips those ticks.

### How it scales, and why that is the point

```
without aggregation:  frames/s = typers × debounced_rate × members
with aggregation:     frames/s = members × TICK⁻¹
```

Typers scale with room size (roughly 10% of a room types during a busy minute),
so the naive form is **quadratic in room size** and the aggregated form is
**linear**. At 200 members the ratio is 80×; at 2,000 members it is 800×.

That is the same arithmetic as the README's delivery-receipt trap and Module
11's presence storms, and it is the single most transferable idea in this
module: **when a per-event signal fans out to N recipients and is produced by
O(N) participants, you must aggregate or you have written an N² system.**

⚠️ `_typers` is a **per-worker dict**, so this has exactly Module 04's wall: with
two workers each aggregates only its own typers and clients see half the list.
Module 11 rebuilds it on Redis TTL keys. Notice the pattern — *every* piece of
derived room state in Phase 1 has this bug.

---

## Task 3 — A defensible dedup window

### What an index entry actually costs

Measure, do not estimate:

```bash
docker exec -i pulse-postgres psql -U pulse -d pulse -c "
SELECT pg_size_pretty(pg_relation_size('uq_message_room_client')) AS idx,
       count(*) AS rows,
       pg_relation_size('uq_message_room_client')::float / count(*) AS bytes_per_row
FROM chat_message;"
```

At 2,000,000 rows with 26-character ULIDs:

```
    idx    |  rows   | bytes_per_row
-----------+---------+---------------
 118 MB    | 2000000 |          61.9
```

**61.9 bytes per entry**: 8 (`room_id` bigint) + 27 (varlena header + 26 chars)
= 35 bytes of key, plus an 8-byte tuple header, a 4-byte line pointer, alignment
padding, and B-tree fill factor (90% by default). Note this is the *index* only —
the `client_id` column in the heap costs another 27 bytes per row.

### The horizons

At the course's target of **10,000 messages/second**:

| Window | Entries | Index size | Verdict |
|--------|---------|-----------|---------|
| 5 minutes | 3.0 M | **186 MB** | Trivial. Also too short — see below. |
| 1 hour | 36 M | **2.2 GB** | Fine. Fits in RAM on any real box. |
| 48 hours | 1.73 G | **107 GB** | Large but survivable with partitioning. |
| 7 days | 6.05 G | **375 GB** | The index alone rivals the data. |
| Forever (1 year) | 315 G | **19.5 TB** | 26% of the pinned 74 TB/year budget, spent on preventing duplicates nobody would ever send. |

That last row is the argument. **A 19.5 TB index to defend against a retry that
stopped being possible after ten minutes is not engineering, it is superstition.**

### How long does a retry actually need to be honoured?

Three windows, and they are not the same:

1. **In-flight retry** — full-jitter exponential backoff, base 500 ms, cap 30 s,
   8 attempts. Worst case ≈ **4 minutes**.
2. **Reconnect retry** — the client reconnects and replays its unacked outbox.
   Bounded by the reconnect policy, ≈ **10 minutes** in Module 17's client.
3. **Offline outbox** — Module 17 holds unsent messages in IndexedDB across a
   browser restart. A user closes their laptop on Friday and opens it Monday:
   **72 hours**.

So the honest answer is: **the guarantee must cover the offline outbox, and the
offline outbox is the expensive part.** Pulse's decision:

> **Idempotency is guaranteed for 48 hours.** A `message.create` whose
> `client_id` encodes a timestamp older than 48 hours is rejected with
> `client_id_expired` rather than silently risking a duplicate.

The ULID makes this checkable with no state at all — the first 10 characters
*are* the millisecond timestamp:

```python
def ulid_ms(cid: str) -> int:
    v = 0
    for ch in cid[:10]:
        v = (v << 5) | _ALPHABET.index(ch)
    return v


DEDUP_WINDOW_MS = 48 * 3600 * 1000

if now_ms() - ulid_ms(client_id) > DEDUP_WINDOW_MS:
    raise ProtocolError("client_id_expired",
                        "this message is older than the idempotency window; "
                        "regenerate client_id or discard",
                        window_hours=48)
```

✅ **A self-describing ID turns an unbounded guarantee into a bounded, checkable
one**, and the client gets a specific error instead of a duplicate message. This
is the payoff for choosing ULID over UUIDv4 that has nothing to do with index
locality.

The 48-hour window is enforced physically by Module 13's time partitioning: the
unique index becomes per-partition, old partitions are dropped, and **uniqueness
therefore holds only within the retained window** — which is exactly the
guarantee we just documented, rather than an accident.

### The two-tier cache

```python
# chat/dedup.py
import time
from collections import OrderedDict

HOT_TTL = 300.0          # 5 minutes: covers windows 1 and 2 above
HOT_MAX = 200_000        # ~24 MB. Bounded, because unbounded caches are leaks.

_hot: OrderedDict[tuple[int, str], tuple] = OrderedDict()


def get(room_id: int, client_id: str):
    key = (room_id, client_id)
    hit = _hot.get(key)
    if hit is None:
        return None
    result, at = hit
    if time.monotonic() - at > HOT_TTL:
        _hot.pop(key, None)
        return None
    _hot.move_to_end(key)
    return result


def put(room_id: int, client_id: str, result) -> None:
    _hot[(room_id, client_id)] = (result, time.monotonic())
    _hot.move_to_end((room_id, client_id))
    while len(_hot) > HOT_MAX:
        _hot.popitem(last=False)
```

Wire it as a *cache*, never as the guarantee:

```python
async def send_message_cached(**kw):
    if (hit := dedup.get(kw["room_id"], kw["client_id"])) is not None:
        return SendResult(*hit[:3], duplicate=True)
    result = await send_message(**kw)                 # the DB is the source of truth
    dedup.put(kw["room_id"], kw["client_id"], (result.id, result.seq, result.ts))
    return result
```

### Proving correctness across an eviction

```python
def test_correct_after_cache_eviction(self):
    cid = ulid()
    first = send(cid)
    self.assertFalse(first["duplicate"])

    dedup._hot.clear()                     # simulate eviction / worker restart

    second = send(cid)
    self.assertTrue(second["duplicate"])
    self.assertEqual((first["id"], first["seq"]), (second["id"], second["seq"]))
    self.assertEqual(Message.objects.filter(client_id=cid).count(), 1)
```
```
test_correct_after_cache_eviction ... ok
```

| Path | Latency | Hit rate (retry-heavy workload) |
|------|---------|--------------------------------|
| Cache hit | **0.02 ms** | 99.4% |
| Cache miss → DB fast path | 0.31 ms | 0.6% |
| DB insert path (new message) | 1.14 ms | — |

✅ **The cache is a 15× latency win on retries and it changes no guarantee.** The
correctness argument survives clearing it at any moment, which is what makes it
safe to keep in a per-process dict that dies with the worker — the one piece of
Phase-1 per-worker state in this course that is *allowed* to be per-worker,
precisely because it is a cache and not state.

---

## Task 4 — Break compatibility on purpose

Baseline: the Module 05 browser client, v1, working.

### (a) Add a required field to `message.create`

```python
REQUIRED_FIELDS["message.create"] = {"client_id", "body", "idempotency_scope"}
```

**Symptom, immediately:**
```json
{"v":1,"type":"error","data":{"code":"missing_fields",
 "fields":["idempotency_scope"],"client_id":"01JQ…"}}
```
The optimistic bubble turns crimson and reads `✗ missing_fields`. Every send
fails; the user cannot post at all.

**Detectability: EASY.** Loud, immediate, attributable to a specific frame,
carries a machine-readable code and the offending `client_id`, and shows up as a
100% error rate on `pulse_protocol_errors_total{code="missing_fields"}` within
one deploy minute. You will roll back before the pager finishes vibrating.

### (b) Change `seq` from a number to a string

```python
seq=str(result.seq)
```

**Symptom:** messages still render. Presence still works. Everything looks
fine — and then:

```
GAP: expected NaN, got 48214 (missing NaN)
GAP: expected NaN, got 48215 (missing NaN)
GAP: expected NaN, got 48216 (missing NaN)
```

`"48213" + 1` is `"482131"` in JavaScript, so `seq !== last + 1` is true for
every message. The client's gap detector fires on **every single message** and
(with Module 10's resume wired) issues a `resume` for each one.

Measured on a 200-member room at 10 msg/s: **inbound `resume` frames went from
0/s to 2,000/s**, each triggering a database query and a batch response. Server
CPU 34% → 100% of the core; p99 fan-out 5.4 ms → 3,100 ms. The UI still looked
correct for about ninety seconds, then stopped updating because the loop was
saturated.

**Detectability: MEDIUM.** Nothing errors, and the *symptom* (server melting) is
three layers away from the *cause* (a JSON type). Your dashboards show CPU and
`resume` rate, not "seq is a string." Diagnosis time in the reference run: 22
minutes, and only because someone opened DevTools.

### (c) Change `ts` from milliseconds to seconds

```python
ts=int(time.time())
```

**Symptom:** every message displays a timestamp of **21 January 1970**, or, if
the client renders relative time, "55 years ago". Nothing errors. No metric
moves. Delivery, ordering, dedup, resume, presence — all still correct, because
nothing in the system *computes* with `ts`.

Then it gets worse. Module 17's client drops frames it considers stale
(`Date.now() - env.ts > 30_000` → "this is a replay, ignore it"). Every frame is
now 55 years stale. **The client silently discards 100% of messages while
reporting a healthy connection.**

**Detectability: HARD, and this is the point.** There is:
- no error frame,
- no exception on either side,
- no schema violation — it is an `int`, as declared, in range,
- no type-system violation — TypeScript, Pydantic, JSON Schema and protobuf all
  validate `ts: number` and all pass,
- no metric that moves until a *human* says "why does everything say 1970?"

### The ranking, and why (c) is the dangerous class

```
(a) required field added   →  loud, immediate, machine-readable      EASY
(b) type changed           →  silent locally, catastrophic remotely  MEDIUM
(c) MEANING changed        →  silent everywhere, forever             HARD
```

**(c) is the most dangerous class of protocol change because every validation
tool we have validates shape, and meaning has no shape.** A schema registry does
not know that `ts` is milliseconds. A JSON Schema `"type": "integer"` passes. A
protobuf `int64 ts = 4` passes. A TypeScript `ts: number` compiles. The entire
apparatus of static contract enforcement is blind to it, which is why "change the
meaning of a value" is the only row in the README's evolution table with two ❌.

### What would have caught each one, before deploy

| Change | Mechanism |
|--------|-----------|
| (a) required field | **A conformance suite**: run the *previous* client's exact frames against the new server in CI. Ten canned frames, one assertion each — the cheapest test in this course. |
| (b) type change | The same conformance suite, asserting **types**, not just success: `assert isinstance(ack["data"]["seq"], int)`. Also a generated client type (OpenAPI/AsyncAPI → TS) would fail to compile. |
| (c) meaning change | **Golden-frame snapshot tests** with a frozen clock, byte-compared against a committed fixture — plus the only durable defence: **encode units in names.** `ts_ms`, `retry_after_ms`, `ttl_s`. A rename is a loud break (row 6 of the table); a silent unit change is not. Pulse's protocol spec names every duration field with its unit for exactly this reason. |

> **The rule to take away:** never change what a field *means*. Add a new field
> with a new name, populate both during the deprecation window, and use the
> version metric from lab Part H to decide when the old one can go. It costs
> eight bytes and it is the difference between a deploy and an incident review.

---

## Task 5 (Stretch) — `resume`, and the reconnect storm

### The implementation

```python
# chat/service.py
RESUME_LIMIT = 500


@database_sync_to_async
def resume_from(room_id: int, from_seq: int, limit: int = RESUME_LIMIT):
    """Ascending seq range scan on uq_message_room_seq (room_id, seq).

    .values() rather than model instances: Module 02 measured 2.2x, and this is
    the one query whose row count is unbounded by anything the user did.
    """
    rows = list(Message.objects
                .filter(room_id=room_id, seq__gt=from_seq)
                .order_by("seq")
                .values("id", "seq", "client_id", "body", "created_at",
                        "sender__username", "reply_to_id")[:limit + 1])
    has_more = len(rows) > limit
    return rows[:limit], has_more
```
```python
# chat/consumers.py
    async def _on_resume(self, data):
        rows, has_more = await resume_from(self.room.id, data["from_seq"])
        await self.send_json(envelope(
            "resume.batch", self.group, now_ms(),
            from_seq=data["from_seq"],
            to_seq=rows[-1]["seq"] if rows else data["from_seq"],
            has_more=has_more,
            messages=[{"id": r["id"], "seq": r["seq"], "client_id": r["client_id"],
                       "sender": r["sender__username"], "body": r["body"],
                       "ts": int(r["created_at"].timestamp() * 1000),
                       "reply_to": r["reply_to_id"]} for r in rows]))
```

```bash
docker exec -i pulse-postgres psql -U pulse -d pulse -c "
EXPLAIN (ANALYZE, BUFFERS)
SELECT id, seq, client_id, body, created_at FROM chat_message
WHERE room_id = 1 AND seq > 48213 ORDER BY seq LIMIT 501;"
```
**Expected:**
```
 Limit  (cost=0.43..38.21 rows=120 width=64) (actual time=0.021..0.084 rows=120 loops=1)
   ->  Index Scan using uq_message_room_seq on chat_message
         Index Cond: ((room_id = 1) AND (seq > 48213))
         Buffers: shared hit=7
 Execution Time: 0.118 ms
```

✅ **Seven buffer hits and 0.118 ms** — because `(room_id, seq)` is exactly the
index this query wants, in exactly this order. That is not luck; the constraint
that guarantees gapless sequences is the same B-tree that serves resume. Module
12 makes `(room_id, seq)` the *primary key* for this reason.

### One client, two minutes offline

Room doing 1 message/second (Module 10 pins this scenario at **98 messages lost
without resume and 0 with**; at 1 msg/s the reference run produced 120):

| Metric | Value |
|--------|-------|
| Messages returned | 120 |
| SQL time | 0.12 ms |
| Python: rows → dicts | 0.68 ms |
| `json.dumps` of the batch | 0.31 ms |
| `resume.batch` frame size | **18,412 bytes** |
| Total server work | **1.11 ms** |

Trivial. Now stop being fooled by the single-client number.

### Five thousand clients reconnect at once

Module 18's scenario: a rolling deploy drains a node and 5,000 clients reconnect
within ~200 ms.

```
5,000 × 120 messages       =    600,000 rows read
5,000 × 1.11 ms            =      5.6 core-seconds  ← on ONE core
5,000 × 18,412 bytes       =     92 MB of outbound buffers, allocated at once
```

**What breaks first, measured:**

| Candidate | Reality |
|-----------|---------|
| Postgres | 5,000 × 0.12 ms = 0.6 s of DB time, spread over the pool. **Not the bottleneck.** |
| The `database_sync_to_async` threadpool (12) | 5,000 × 0.12 ms / 12 = 50 ms. **Not the bottleneck.** |
| **The event loop** | **5.6 core-seconds of Python on one core, arriving in 200 ms.** ← this |
| Worker RSS | 96 MB → **412 MB** spike as 92 MB of frames queue in transport buffers, plus the row dicts |

Measured on the reference machine: the worker's loop was saturated for **8.4
seconds**. During that window, **p99 fan-out latency for the 15,000 connections
that were *not* reconnecting went from 5.4 ms to 4,210 ms** — a 780× degradation
for users who did nothing. Two of them hit their client-side timeout and
reconnected, which added to the storm.

✅ **The resume feature, working perfectly, is a self-inflicted denial of
service.** Nothing errored. This is the Module 01 lesson yet again: 5,000
concurrent coroutines are free, and the one core they share is not.

### Mitigations, measured

| Mitigation | Drain time | p99 for uninvolved connections | Notes |
|-----------|-----------|-------------------------------|-------|
| None | 8.4 s | **4,210 ms** | — |
| Batch cap 500 + `has_more` | 8.4 s | 4,180 ms | Bounds the *worst* client, not the storm |
| **Server-side `Semaphore(64)` around resume** | 9.1 s | **6.9 ms** | Module 01 Part F, applied |
| **Client full-jitter reconnect over 30 s** (Module 17) | 30 s | **6.1 ms** | The best fix, and it is on the client |
| `control{action:"drain", retry_after_ms}` on shutdown (Module 18) | 30 s | 5.9 ms | The server *tells* clients how to spread |
| Raw cursor instead of `.values()` (Module 12) | 6.1 s | 3,900 ms | 1.4× on the CPU, does not fix the shape |

```python
RESUME_ADMISSION = asyncio.Semaphore(64)

    async def _on_resume(self, data):
        async with RESUME_ADMISSION:              # queue BEFORE doing work
            rows, has_more = await resume_from(...)
        await self.send_json(...)
```

**Read the semaphore row carefully: total drain time got 8% *worse* and the
latency for everyone else got 610× *better*.** The work did not change; the
queueing moved from a place that destroys latency for everyone to a place where
it is bounded and only affects the reconnecting clients — who are already
waiting, and who will not notice 140 extra milliseconds.

That is the exact result Module 01's Part F produced with 5,000 coroutines
against a 20-connection pool (p99 12,470 ms → 118 ms), reproduced here on a real
feature. **Admission control is not a performance optimization; it is a decision
about who absorbs the queue.**

The honest ordering of fixes: **fix the client first** (full jitter — it costs
nothing and removes the storm), **then** add server-side admission control
(because a client you do not control will eventually storm you anyway), **then**
optimize the query. Module 10 ships all three, Module 17 builds the client half,
and Module 18 tests the whole thing by draining a node under load.

---

## What the solutions taught

- **An idempotency key protects the insert, not the side effects you performed
  before deciding to insert.** The fix is ordering: allocate only on the winning
  write. The cost is 31% of single-room write throughput and zero across rooms.
- **When a per-event signal fans out to N recipients and is produced by O(N)
  participants, you have an N² system** unless you aggregate. Typing: 80× by
  construction, 117× measured, and the ratio grows with room size.
- **An unbounded guarantee is a design smell.** A 19.5 TB dedup index defends
  against retries that stopped being possible after ten minutes. A ULID's
  embedded timestamp turns "forever" into a checkable 48 hours with a specific
  error code.
- **Meaning has no shape, so no schema validates it.** Changing `ts` from ms to s
  passes every type system in existence and silently discards 100% of messages.
  Encode units in names; add fields, never redefine them.
- **A feature that is 1.11 ms for one client is 8.4 seconds for five thousand**,
  and the fix is to decide deliberately who waits. Admission control made the
  drain 8% slower and everyone else 610× faster.

Next: [Module 06 — The Load-Testing Harness](../../06-load-testing-harness/)
generates this protocol at 20,000 connections and breaks the single worker on
purpose. Then [Module 07](../../07-scale-out-redis-channel-layer/) finally lets
you use more than one.
