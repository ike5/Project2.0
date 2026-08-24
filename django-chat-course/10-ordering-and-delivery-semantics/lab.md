# Lab 10 — Break Ordering On Purpose, Then Close the Last Gap

**You'll:** reproduce the ordering bug Module 09 introduced and count it, kill it
with one Lua script, harden the sequencer against a Redis restart, build `resume`
and debounced gap repair, sever a client's network for two minutes and prove it
loses nothing, watch a reconnect land on a different worker process, and measure
all three delivery semantics side by side.

⏱️ ~110 min. Work in `apps/pulse` — the Django project you have grown since
Module 04.

```bash
docker compose -p pulse-dev -f ../../infra/compose.dev.yml up -d
alias r='docker exec -i pulse-redis redis-cli'
alias pg='docker exec -i pulse-postgres psql -U pulse -d pulse'
```

Everything below assumes Module 09's files exist: `chat/streams.py`,
`chat/registry.py`, `chat/consumer_loop.py`, and a `ChatConsumer` that XADDs
instead of `group_send`ing.

---

## Part A — Make the ordering bug happen, and count it

Module 09's send path is two independent awaits:

```python
seq = await allocate_seq(room_id)                 # Redis INCR
entry_id = await fanout.append(room_id, envelope) # XADD
```

At one sender this is fine. Let us find out what 64 concurrent senders do to it.

Create `code/inversion_probe.py`:

```python
"""Count sequence inversions and burned sequence numbers in the room's stream."""
import asyncio, json, os, sys, time
import redis.asyncio as aioredis

ROOM = sys.argv[1] if len(sys.argv) > 1 else "room.probe"
CONC = int(os.environ.get("CONC", "64"))
EACH = int(os.environ.get("EACH", "200"))
SPLIT = os.environ.get("SPLIT", "1") == "1"   # 1 = Module 09's two round trips

SEQ = f"room:{{{ROOM}}}:seq"
STREAM = f"room:{{{ROOM}}}:stream"

LUA = """
local seq = redis.call('INCR', KEYS[1])
local payload = string.gsub(ARGV[1], '__SEQ__', tostring(seq), 1)
local id = redis.call('XADD', KEYS[2], 'MAXLEN', '~', ARGV[2], '*', 'payload', payload)
return {seq, id}
"""


async def main():
    r = aioredis.from_url(os.environ.get("REDIS_URL", "redis://localhost:6379"),
                          decode_responses=True)
    await r.delete(SEQ, STREAM)
    script = r.register_script(LUA)

    async def send_split(n, i):
        seq = await r.incr(SEQ)                     # round trip 1
        env = {"data": {"seq": seq, "client_id": f"c-{n}-{i}"}}
        await r.xadd(STREAM, {"payload": json.dumps(env)},
                     maxlen=10000, approximate=True)   # round trip 2

    async def send_atomic(n, i):
        env = {"data": {"seq": "__SEQ__", "client_id": f"c-{n}-{i}"}}
        await script(keys=[SEQ, STREAM],
                     args=[json.dumps(env, separators=(",", ":")), 10000])

    send = send_split if SPLIT else send_atomic

    async def worker(n):
        for i in range(EACH):
            await send(n, i)

    t0 = time.perf_counter()
    await asyncio.gather(*(worker(n) for n in range(CONC)))
    dt = time.perf_counter() - t0

    entries = await r.xrange(STREAM, "-", "+")
    seqs = [json.loads(f["payload"])["data"]["seq"] for _i, f in entries]
    inversions = sum(1 for a, b in zip(seqs, seqs[1:]) if b < a)
    expected = CONC * EACH
    missing = expected - len(set(seqs))

    print(f"mode        : {'split (Module 09)' if SPLIT else 'atomic Lua'}")
    print(f"sent        : {expected}")
    print(f"in stream   : {len(seqs)}")
    print(f"inversions  : {inversions}  ({inversions / expected:.2%})")
    print(f"burned seqs : {missing}")
    print(f"throughput  : {expected / dt:,.0f} sends/s")
    await r.aclose()


asyncio.run(main())
```

Run it against the split path, first with one sender:

```bash
CONC=1 EACH=10000 SPLIT=1 python code/inversion_probe.py room.probe
```
**Expected:**
```
mode        : split (Module 09)
sent        : 10000
in stream   : 10000
inversions  : 0  (0.00%)
burned seqs : 0
throughput  : 15,910 sends/s
```

✅ Clean. This is why the bug survived Module 09: with one client, there is no
interleaving. Now turn on concurrency.

```bash
CONC=64 EACH=157 SPLIT=1 python code/inversion_probe.py room.probe
```
**Expected:**
```
mode        : split (Module 09)
sent        : 10048
in stream   : 10048
inversions  : 412  (4.10%)
burned seqs : 0
throughput  : 18,412 sends/s
```

✅ **412 inversions per 10,048 messages.** Every one of those is a client that
receives seq 482 before 481, renders them backwards if it trusts arrival order, or
fires a spurious repair request if it does not.

Look at one directly:

```bash
r XRANGE 'room:{room.probe}:stream' - + COUNT 6
```
**Expected — note that the seq values are not monotonic:**
```
1) 1) "1735689600123-0"
   2) 1) "payload"
      2) "{\"data\": {\"seq\": 1, \"client_id\": \"c-0-0\"}}"
2) 1) "1735689600123-1"
   2) 1) "payload"
      2) "{\"data\": {\"seq\": 3, \"client_id\": \"c-2-0\"}}"
3) 1) "1735689600123-2"
   2) 1) "payload"
      2) "{\"data\": {\"seq\": 2, \"client_id\": \"c-1-0\"}}"
```

Stream order is `1, 3, 2`. The consumer loop reads the stream in stream order, so
that is the order every socket in every worker receives.

### Now burn a sequence number

The other half of the bug. Make the `XADD` fail after the `INCR` succeeds:

```bash
r CONFIG SET maxmemory 1
CONC=1 EACH=20 SPLIT=1 python code/inversion_probe.py room.burn || true
r CONFIG SET maxmemory 1gb
r GET 'room:{room.burn}:seq'
r XLEN 'room:{room.burn}:stream'
```
**Expected:**
```
OK
...OOM command not allowed when used memory > 'maxmemory'.
OK
"1"
(integer) 0
```

✅ **The counter is at 1 and the stream is empty.** Sequence number 1 has been
allocated and will never appear in any message. Every client that joins this room
will wait for seq 1 forever, and re-issue `resume` every 500 ms while it waits.

Record both:
```markdown
## Module 10 — the Module 09 send path

- 1 sender  : 0 inversions
- 64 senders: 412 inversions per 10,048  (4.10%)
- INCR succeeds + XADD fails -> a permanently burned seq -> per-client repair loop
```

---

## Part B — One Lua script fixes both

Redis is single-threaded and a script runs to completion with no interleaving
(Module 08). Put the `INCR` and the `XADD` inside one.

Copy [`code/sequence.py`](./code/sequence.py) to `chat/sequence.py`. The script is
the whole idea:

```lua
local seq = redis.call('INCR', KEYS[1])
local payload = string.gsub(ARGV[1], '__SEQ__', tostring(seq), 1)
local entry_id = redis.call('XADD', KEYS[2], 'MAXLEN', '~', ARGV[2], '*',
                            'payload', payload)
return {seq, entry_id}
```

> **Both keys carry the `{room_id}` hash tag** Module 09 added. A Lua script may
> only touch keys in one Cluster slot; without the tag this works fine on a single
> Redis and dies with `CROSSSLOT Keys in request don't hash to the same slot` the
> moment you reach Module 18. Fix it now, when it costs nothing.

> **Why substitute a token instead of building JSON in Lua?** `cjson.encode`
> inside Redis does not preserve key order and turns an empty object into `[]`.
> Encode in Python where you control it; let Lua do one `gsub`.

Re-run the probe in atomic mode:

```bash
CONC=64 EACH=157 SPLIT=0 python code/inversion_probe.py room.probe2
```
**Expected:**
```
mode        : atomic Lua
sent        : 10048
in stream   : 10048
inversions  : 0  (0.00%)
burned seqs : 0
throughput  : 31,904 sends/s
```

✅ **Zero inversions, zero burned sequence numbers — and 1.73× the throughput,**
because you removed a network round trip from every send.

Push it further to be sure it is not a small-sample artefact:

```bash
CONC=64 EACH=15625 SPLIT=0 python code/inversion_probe.py room.probe3
```
```
sent        : 1000000
inversions  : 0  (0.00%)
burned seqs : 0
throughput  : 30,881 sends/s
```

✅ **Zero in a million.**

### What the alternative would have cost

Module 05 allocated sequences in Postgres, inside the same transaction as the
insert. That is also gapless — and it puts a row lock on `chat_roomsequence` in
front of every send. Measure it:

```bash
pg -c "SELECT 1" >/dev/null
python manage.py shell -c "
import time
from django.db import connection
N = 5000
t0 = time.perf_counter()
with connection.cursor() as cur:
    for i in range(N):
        cur.execute('''INSERT INTO chat_roomsequence (room_id, last_seq)
                       SELECT id, 1 FROM chat_room WHERE slug='general'
                       ON CONFLICT (room_id) DO UPDATE
                         SET last_seq = chat_roomsequence.last_seq + 1
                       RETURNING last_seq''')
        cur.fetchone()
print(f'{N / (time.perf_counter() - t0):,.0f} allocations/s (single sender)')
"
```
**Expected:**
```
2,914 allocations/s (single sender)
```

And that is the *uncontended* number. With 64 senders on one room they serialize
on the same row, and p99 goes from 0.34 ms to 34 ms.

| Allocator | Gapless | Ordered | Sends/s per room | p99 @ 64 senders |
|-----------|---------|---------|------------------|------------------|
| Postgres `ON CONFLICT … RETURNING` (Module 05) | ✅ | ✅ | 2,914 | 34.1 ms |
| Redis `INCR` + separate `XADD` (Module 09) | ❌ | ❌ | 18,412 | 2.4 ms |
| **Redis Lua `INCR`+`XADD` (this module)** | ✅ | ✅ | **31,904** | **1.8 ms** |

✅ **11× the Postgres allocator, with the same guarantee.** This is a rare trade
where the fast option is also the correct one — take it, and say why in your
architecture review.

### Wire it into the consumer

`chat/consumers.py`, replacing Module 09's `_on_message`:

```python
from .sequence import SequenceAllocator
from .streams import fanout

allocator = SequenceAllocator(fanout.redis)   # shares the worker's pool


async def _on_message(self, content):
    data = content["data"]
    envelope = {
        "v": 1,
        "type": "message.new",
        "room": self.room.key,          # "room.<slug>" — group name, wire field,
        "ts": now_ms(),                 #  and store identity, all one string
        "data": {
            "id": new_server_id(),
            "client_id": data["client_id"],
            "seq": "__SEQ__",           # the Lua script fills this in
            "sender": self.user.username,
            "body": data["body"],
            "reply_to": data.get("reply_to"),
        },
    }
    seq, entry_id = await allocator.send(self.room.key, envelope)

    # message.ack goes only to the sender (protocol §3.1). message.new reaches
    # everyone — including the sender — from the consumer loop, which is why the
    # ack and the broadcast are two independent frames that may arrive in either
    # order.
    await self.send_json({
        "v": 1, "type": "message.ack", "room": self.room.key, "ts": now_ms(),
        "data": {"client_id": data["client_id"], "id": envelope["data"]["id"],
                 "seq": seq, "duplicate": False},
    })
```

`Room.key` is the shared convention: `slug` is the bare handle (`general`), and

```python
class Room(models.Model):
    slug = models.SlugField(unique=True)

    @property
    def key(self) -> str:
        return f"room.{self.slug}"
```

composes the one string that is simultaneously the channel-layer group name, the
`room` field in every envelope, and the room identity in the message store. One
string, three jobs, zero conversion functions scattered through the codebase.

---

## Part C — Survive a Redis restart

`compose.dev.yml` runs Redis with `--save "" --appendonly no`. That is deliberate
(see `infra/README.md`) and it has exactly one consequence you must handle.

```bash
r GET 'room:{room.general}:seq'
docker restart pulse-redis && sleep 3
r GET 'room:{room.general}:seq'
```
**Expected:**
```
"503"
(nil)
```

Now send one message with a naive allocator and watch the disaster:

```bash
python manage.py sendmsg room.general "after the restart"
r GET 'room:{room.general}:seq'
pg -c "SELECT max(m.seq) FROM chat_message m JOIN chat_room r ON r.id=m.room_id
       WHERE r.slug='general';"
```
**Expected — the counter restarted at 1 while the store is at 503:**
```
"1"
 max
-----
 503
```

Every client's cursor is at 503. It now receives seq 1, decides it is a duplicate,
and drops it — silently, forever. And the *next* insert violates
`UNIQUE (room_id, seq)`.

`SequenceAllocator._ensure_recovered` fixes this, once per room per process:

```python
async def recover_high_water_mark(self, room_id: str) -> int:
    known = await _max_seq_in_store(room_id)      # SELECT coalesce(max(seq), 0)
    if known == 0:
        return 0
    return int(await self._set_if_lower(keys=[seq_key(room_id)], args=[known]))
```

with the Lua that makes it safe for all eight workers to run simultaneously:

```lua
local current = tonumber(redis.call('GET', KEYS[1]) or '0')
local floor = tonumber(ARGV[1])
if current < floor then redis.call('SET', KEYS[1], floor); return floor end
return current
```

> **Why a script and not `SETNX`?** Because eight worker processes hit this within
> milliseconds of each other, and between one worker's `GET` and its `SET`,
> another has already allocated seq 504. `SETNX` also fails to help if the counter
> exists but is *too low*, which is exactly the restart-then-one-message case you
> just produced. Compare-and-set in Lua handles both.

Redo the drill:

```bash
r DEL 'room:{room.general}:seq'
python manage.py sendmsg room.general "after the restart, with recovery"
r GET 'room:{room.general}:seq'
```
**Expected — the counter resumed above the known maximum:**
```
"504"
```

✅ **Recovered.** Note the cost: one `SELECT max(seq)` per room per worker process
per Redis lifetime. On a box with 8 workers and 1,000 active rooms that is 8,000
indexed lookups spread over the first few seconds after a restart — measurable,
bounded, and vastly cheaper than the alternative.

---

## Part D — The state resume needs

Two tables. Create `chat/migrations/0003_sequences.py`:

```python
from django.db import migrations, models


class Migration(migrations.Migration):
    # Yes, this shares the "0003" prefix with Module 05's 0003_protocol_fields.
    # Django orders migrations by the DEPENDENCY GRAPH, not by filename — the
    # number is a human convenience, not a key. We keep this exact name because
    # Module 12's RunSQL migration depends on it by name.
    dependencies = [("chat", "0003_protocol_fields")]

    operations = [
        migrations.CreateModel(
            name="ReadCursor",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("last_read_seq", models.BigIntegerField(default=0)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("room", models.ForeignKey("chat.Room", on_delete=models.CASCADE)),
                ("user", models.ForeignKey("auth.User", on_delete=models.CASCADE)),
            ],
            options={"constraints": []},
        ),
        migrations.AddConstraint(
            model_name="readcursor",
            constraint=models.UniqueConstraint(
                fields=["room", "user"], name="uq_readcursor_room_user"),
        ),
        migrations.CreateModel(
            name="SequenceGap",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("seq", models.BigIntegerField()),
                ("reason", models.TextField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("room", models.ForeignKey("chat.Room", on_delete=models.CASCADE)),
            ],
        ),
        migrations.AddConstraint(
            model_name="sequencegap",
            constraint=models.UniqueConstraint(
                fields=["room", "seq"], name="uq_sequencegap_room_seq"),
        ),
        # The resume query: WHERE room_id = %s AND seq > %s ORDER BY seq.
        # Module 12 makes (room_id, seq) the PRIMARY KEY, at which point this
        # index becomes redundant and that migration drops it.
        migrations.AddIndex(
            model_name="message",
            index=models.Index(fields=["room", "seq"], name="idx_message_resume"),
        ),
    ]
```

```bash
python manage.py migrate chat
pg -c "\d chat_readcursor"
```
**Expected:**
```
                    Table "public.chat_readcursor"
    Column     |           Type           | Nullable
---------------+--------------------------+----------
 id            | bigint                   | not null
 last_read_seq | bigint                   | not null
 updated_at    | timestamp with time zone | not null
 room_id       | bigint                   | not null
 user_id       | bigint                   | not null
Indexes:
    "chat_readcursor_pkey" PRIMARY KEY, btree (id)
    "uq_readcursor_room_user" UNIQUE CONSTRAINT, btree (room_id, user_id)
```

> **`ReadCursor` is one row per (user, room) and 16 bytes of payload.** It is the
> offline queue, the unread badge, and the read receipt, all at once. Compare it
> with a per-user message queue: 1M users × 20 rooms × 100 unread is
> **2,000,000,000 rows** in the queue design versus **20,000,000 rows ≈ 320 MB**
> here. Derive, don't store.

`SequenceGap` is the tombstone table for the one residual gap source: an entry that
is in the stream and can never be persisted (a poison payload that an operator
dead-letters). Module 09's consumer loop already refuses to `XACK` on failure; add
the dead-letter branch:

```python
# chat/consumer_loop.py — in _process_and_ack's except branch
if int(fields.get("delivery_count", 0)) >= 5:
    await record_dead_letter(room_id, envelope["data"]["seq"], entry_id)
    await fanout.redis.xack(key, self.group(), entry_id)   # stop redelivering
```

Now copy [`code/resume.py`](./code/resume.py) to `chat/resume.py` and dispatch it:

```python
# chat/consumers.py
from . import resume as resume_svc

async def receive_json(self, content):
    mtype = content.get("type")
    if mtype == "join":
        await self._join(content["room"])
    elif mtype == "message.create":
        await self._on_message(content)
    elif mtype == "resume":
        await self._on_resume(content)
    elif mtype == "read.upto":
        await self._on_read(content)
    elif mtype == "ping":
        await self.send_json({"v": 1, "type": "pong", "room": self.room.key,
                              "ts": now_ms(),
                              "data": {"ts": content["data"]["ts"],
                                       "server_ts": now_ms()}})
    else:
        await self._error("unknown_type", f"no handler for {mtype!r}")


async def _on_resume(self, content):
    result = await resume_svc.resume(self.room.key, content["data"].get("from_seq", 0))
    await self.send_json({"v": 1, "type": "resume.batch", "room": self.room.key,
                          "ts": now_ms(), "data": result.as_data()})
```

Test it by hand. Send ten messages, then resume from four:

```bash
for i in $(seq 1 10); do python manage.py sendmsg room.20 "history-$i"; done

python - <<'PY'
import asyncio, json, websockets

async def main():
    async with websockets.connect("ws://localhost:8000/ws/room/20/?as=alice",
                                  subprotocols=["pulse.v1"]) as ws:
        await ws.send(json.dumps({"v":1,"type":"join","room":"room.20","data":{}}))
        await ws.send(json.dumps({"v":1,"type":"resume","room":"room.20",
                                  "data":{"from_seq":4}}))
        while True:
            env = json.loads(await ws.recv())
            if env["type"] == "resume.batch":
                d = env["data"]
                print("seqs      :", [m["seq"] for m in d["messages"]])
                print("from_seq  :", d["from_seq"])
                print("to_seq    :", d["to_seq"])
                print("has_more  :", d["has_more"])
                return

asyncio.run(main())
PY
```
**Expected — messages 5 through 10 only:**
```
seqs      : [5, 6, 7, 8, 9, 10]
from_seq  : 4
to_seq    : 10
has_more  : False
```

Now prove the clamp. A hostile client:

```bash
python - <<'PY'
import asyncio, json, websockets

async def ask(from_seq):
    async with websockets.connect("ws://localhost:8000/ws/room/20/?as=alice",
                                  subprotocols=["pulse.v1"]) as ws:
        await ws.send(json.dumps({"v":1,"type":"join","room":"room.20","data":{}}))
        await ws.send(json.dumps({"v":1,"type":"resume","room":"room.20",
                                  "data":{"from_seq":from_seq}}))
        while True:
            env = json.loads(await ws.recv())
            if env["type"] == "resume.batch":
                d = env["data"]
                print(f"from_seq={from_seq!r:>14} -> returned {len(d['messages'])}"
                      f" rows, from_seq={d['from_seq']}, to_seq={d['to_seq']}")
                return

asyncio.run(asyncio.gather(ask(-1), ask(0), ask(10**18)))
PY
```
**Expected:**
```
from_seq=            -1 -> returned 10 rows, from_seq=0, to_seq=10
from_seq=             0 -> returned 10 rows, from_seq=0, to_seq=10
from_seq= 1000000000000000000 -> returned 0 rows, from_seq=10, to_seq=10
```

✅ **`-1` clamps to 0 and `10^18` clamps to the room maximum.** Neither can force
an unbounded scan. The clamp is three characters of code and it is the difference
between a resume endpoint and a denial-of-service endpoint.

---

## Part E — The client, and the debounce that stops a storm

Copy [`code/pulse-room.js`](./code/pulse-room.js) into
`chat/static/chat/pulse-room.js` and load it from Module 04's room template.

The two lines that matter are in `onopen`:

```js
this.send({ v: 1, type: "join", room: this.roomKey, data: {} });   // FIRST
this.requestResume();                                              // SECOND
```

> **Join before you resume.** If you resume first, a message published between the
> server's `SELECT` and your `registry.add()` reaches nobody and leaves a hole
> that resume has already scrolled past. Join first and that message arrives
> twice, which `ingest()` drops on `seq <= contiguous`. Duplicates are removable;
> holes are not.
>
> There is a Django-specific trap here. If your `_join` handler `await`s the ORM
> before calling `registry.add()` —
> ```python
> self.room = await self._load_room_if_member(...)   # ~4 ms in a threadpool
> registry.add(self.room.key, self)                  # too late
> ```
> — then the window is 4 milliseconds wide instead of microseconds, and it is
> reliably hit under a mass reconnect. Resolve membership on `connect`, before
> `accept()`; by `join` time the room object is already in hand.

### Prove the debounce

Add a debug endpoint that delivers three messages out of order with a controllable
delay. `chat/views.py`:

```python
@require_POST
def debug_reorder(request):
    """DEBUG-ONLY. Deliver the room's last 3 messages as 3, 2, then 1-after-delay."""
    assert settings.DEBUG
    payload = json.loads(request.body)
    room_key, delay_ms = payload["room"], int(payload.get("delay_ms", 300))
    async_to_sync(_reorder)(room_key, delay_ms)
    return JsonResponse({"ok": True})


async def _reorder(room_key, delay_ms):
    msgs = await last_three(room_key)                # [m1, m2, m3]
    subs = registry.subscribers(room_key)
    for sub in subs:
        await sub.send_json(envelope_for(msgs[2]))
        await sub.send_json(envelope_for(msgs[1]))
    async def late():
        await asyncio.sleep(delay_ms / 1000)
        for sub in subs:
            await sub.send_json(envelope_for(msgs[0]))
    asyncio.create_task(late())
```

Open the room in a browser, then:

```bash
curl -sX POST localhost:8000/debug/reorder \
     -H 'content-type: application/json' \
     -d '{"room":"room.20","delay_ms":300}'
```
**Expected in the browser console:**
```
(nothing)
```
and messages render in order 8, 9, 10.

✅ **A 300 ms reordering absorbed with zero repair requests.** Now exceed the
debounce:

```bash
curl -sX POST localhost:8000/debug/reorder \
     -H 'content-type: application/json' \
     -d '{"room":"room.20","delay_ms":900}'
```
**Expected:**
```
[room.20] gap at 8; repairing
```
one line, then messages 8, 9, 10 render in order.

✅ **One repair request, not two.** Finally, set `REPAIR_DEBOUNCE_MS = 0` and
re-run the 900 ms case:

```
[room.20] gap at 8; repairing
[room.20] gap at 8; repairing
[room.20] gap at 8; repairing
```

✅ **Three requests for one gap** — from one client. Multiply by 20,000 clients
during a fan-out hiccup and you have converted a transient blip into a database
outage. The debounce is 500 ms because it must exceed normal reordering (which the
Lua fix reduced to network jitter, tens of milliseconds) and stay well under human
perception (~200 ms is noticeable for *rendering*, but this is a repair path that
only runs when something is already wrong).

| Reorder delay | Debounce 500 ms | Debounce 0 |
|---------------|-----------------|------------|
| 300 ms | 0 requests | 2 requests |
| 900 ms | 1 request | 3 requests |
| 30 s (an `XAUTOCLAIM` redelivery) | 1 request | 61 requests |

---

## Part F — The two-minute disconnect test

**The headline test of the module.** Copy
[`code/disconnect_test.sh`](./code/disconnect_test.sh) and give yourself a Node
client and a `sendmsg` command.

`chat/management/commands/sendmsg.py`:

```python
from asgiref.sync import async_to_sync
from django.core.management.base import BaseCommand

from chat.sequence import SequenceAllocator
from chat.streams import fanout
from chat.utils import now_ms, new_server_id


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("room")
        parser.add_argument("body")

    def handle(self, room, body, **_):
        allocator = SequenceAllocator(fanout.redis)
        env = {"v": 1, "type": "message.new", "room": room, "ts": now_ms(),
               "data": {"id": new_server_id(), "client_id": f"cli-{now_ms()}",
                        "seq": "__SEQ__", "sender": "alice", "body": body,
                        "reply_to": None}}
        seq, entry_id = async_to_sync(allocator.send)(room, env)
        self.stdout.write(f"seq={seq} entry={entry_id}")
```

Run it **without** resume first — comment out `this.requestResume()` in
`onopen` — so you see the damage before the fix:

```bash
chmod +x code/disconnect_test.sh
PULSE_NO_RESUME=1 ./code/disconnect_test.sh
```
**Expected:**
```
>>> starting bob (resume=off)
>>> 40 messages before the cut
>>> severing bob's connection for 120s
>>> restoring the network
>>> waiting 15s for reconnect + resume to settle

expected: 160   received: 62   distinct: 62   duplicates: 0   arrived in order: yes
GAP: 40 -> 139
```

✅ **98 messages permanently missing**, and note what the client experienced: no
error, no warning, a clean-looking reconnect, and a conversation with a
two-minute hole in it that nobody will notice until someone asks "did you see what
I said?"

Now restore `requestResume()` and re-run:

```bash
./code/disconnect_test.sh
```
**Expected:**
```
>>> starting bob (resume=on)
>>> severing bob's connection for 120s
>>> restoring the network
>>> waiting 15s for reconnect + resume to settle

expected: 160   received: 167   distinct: 160   duplicates: 7   arrived in order: yes
```

✅ **All 160 delivered, in order, with 7 duplicates the client deduped.**

Those seven duplicates are join-before-resume working exactly as designed:
messages that arrived live *while* the resume query was running got delivered
twice, and `ingest()` dropped the second copy on `seq <= contiguous`.

The client log shows the recovery shape:

```
[room.30] closed 1006; retry 1 in 743ms
[room.30] closed 1006; retry 2 in 1,208ms
[room.30] closed 1006; retry 5 in 18,900ms
[room.30] connected
[room.30] resume from_seq=40 -> 140 messages, to_seq=140, has_more=false
```

Record it:
```markdown
## Module 10 — Resume

- 2-minute network cut, 100 messages missed during the outage
  - without resume: 98 lost permanently, silently, no error anywhere
  - with resume:     0 lost, 7 duplicates deduped client-side, order preserved
- Resume batch 200, abandon threshold 5,000, repair debounce 500 ms
```

---

## Part G — Reconnect to a different worker process

This is the Python-specific twist, and it is worth doing by hand.

Start two workers:

```bash
PULSE_NODE_ID=node-a uvicorn pulse.asgi:application --port 8000 &
PULSE_NODE_ID=node-b uvicorn pulse.asgi:application --port 8001 &
```

Connect a client to 8000, join `room.40`, send a few messages, then look at the
consumer groups:

```bash
for i in $(seq 1 5); do python manage.py sendmsg room.40 "m-$i"; done
r XINFO GROUPS 'room:{room.40}:stream'
```
**Expected — one group, because only worker A has a subscriber:**
```
1) 1) "name"
   2) "node-a-52104"
   3) "last-delivered-id"
   4) "1735689600555-0"
   5) "pending"
   6) (integer) 0
```

Now kill the client, publish 20 more messages, and reconnect to **8001**:

```bash
for i in $(seq 6 25); do python manage.py sendmsg room.40 "m-$i"; done
# reconnect the client to ws://localhost:8001/ws/room/40/
r XINFO GROUPS 'room:{room.40}:stream'
```
**Expected — a second group, created at `$`:**
```
1) 1) "name"
   2) "node-a-52104"
   ...
2) 1) "name"
   2) "node-b-52107"
   3) "last-delivered-id"
   4) "1735689632119-0"        <-- the CURRENT tail, not where the client was
   5) "pending"
   6) (integer) 0
```

**Worker B's group starts at "now."** The twenty messages published while the
client was away were never delivered to worker B's group and never will be —
`XGROUP CREATE … '$'` is not a mistake, it is the only sane default (starting at
`0` would replay every trimmed-window message to a worker that just gained one
subscriber).

Turn resume off and count what the client got:

```
messages received after reconnect: 0
seq range in the store:            1..25
client's contiguous:               5
```

✅ **The stream position is per worker. The client's cursor cannot be one.** That
is why `resume` reads Postgres: the store is the only thing every worker agrees
about.

Turn resume back on and repeat:

```
[room.40] connected
[room.40] resume from_seq=5 -> 20 messages, to_seq=25, has_more=false
messages received after reconnect: 20   duplicates: 0   inversions: 0
```

✅ Recovered.

> On the JVM twin this hazard exists once per **node**. Here it exists once per
> **worker process** — eight times more often on the same 8-core box, because that
> is what the process-per-core model costs you (Module 01). Same shape, more
> chances to get it wrong, which is precisely why the fix has to be structural
> rather than "make sure the client reconnects to the same place."

---

## Part H — Measure all three delivery semantics

You now have every piece needed to demonstrate the table from the README. Add two
environment switches to the consumer loop:

```python
ACK_FIRST = os.environ.get("PULSE_ACK_FIRST") == "1"     # at-most-once
NO_DEDUP  = os.environ.get("PULSE_NO_DEDUP") == "1"      # skip ON CONFLICT
```

`code/semantics_test.sh` publishes 200 messages and `docker pause`s Redis for 1.5 s
in the middle (Module 07's test, re-run):

```bash
#!/usr/bin/env bash
set -euo pipefail
ROOM=room.50
run() {
  echo "--- $1"
  : > /tmp/sem.txt
  node code/bob_client.js "$ROOM" /tmp/sem.txt & C=$!
  sleep 2
  for i in $(seq 1 100); do python manage.py sendmsg "$ROOM" "s-$i" >/dev/null; done
  docker pause pulse-redis; sleep 1.5; docker unpause pulse-redis
  for i in $(seq 101 200); do python manage.py sendmsg "$ROOM" "s-$i" >/dev/null; done
  sleep 8; kill $C 2>/dev/null || true
  got=$(sort -n /tmp/sem.txt | uniq | wc -l)
  dup=$(( $(wc -l < /tmp/sem.txt) - got ))
  echo "delivered distinct: $got / 200   lost: $((200-got))   duplicates: $dup"
}
PULSE_ACK_FIRST=1 PULSE_NO_DEDUP=1 run "at-most-once  (ack before process)"
PULSE_NO_DEDUP=1                run "at-least-once (ack after process)"
                                run "at-least-once + idempotency"
```

```bash
chmod +x code/semantics_test.sh && ./code/semantics_test.sh
```
**Expected:**
```
--- at-most-once  (ack before process)
delivered distinct: 171 / 200   lost: 29   duplicates: 0
--- at-least-once (ack after process)
delivered distinct: 200 / 200   lost: 0   duplicates: 11
--- at-least-once + idempotency
delivered distinct: 200 / 200   lost: 0   duplicates: 0
```

✅ **29 lost, or 11 duplicated, or neither.** The 29 is Module 07's ~15% loss
figure reproduced exactly, which is the point: at-most-once is what you had before
Module 09, and acking first puts you right back there.

The third run still delivered 11 duplicate stream entries — check:

```bash
curl -s localhost:8000/metrics | grep pulse_stream_duplicates_total
```
```
pulse_stream_duplicates_total 11.0
```

✅ **The duplicates are on the wire and absent from the user's screen.** That gap
between `pulse_stream_delivered_total` and what the client rendered *is* the
exactly-once illusion, and now you can point at the number that proves it is an
illusion.

---

## Part I — Read receipts, unread, and the dedup window

Receipts are a high-water mark. Prove the idempotency:

```bash
for s in 50 30 50 45 60 20; do
  python manage.py readupto room.30 bob "$s"
done
pg -c "SELECT c.last_read_seq FROM chat_readcursor c
       JOIN chat_room r ON r.id=c.room_id
       JOIN auth_user u ON u.id=c.user_id
       WHERE r.slug='30' AND u.username='bob';"
```
**Expected — the maximum, regardless of arrival order:**
```
 last_read_seq
---------------
            60
```

✅ `GREATEST` absorbs out-of-order and duplicate receipts. **That is what lets
receipts ride at-most-once transport** — a lost one is repaired by the next one,
so paying for stream storage would be waste (Module 09's routing rule).

Unread, derived:

```bash
curl -s -H 'X-User: bob' localhost:8000/api/rooms/room.30/unread | jq
```
**Expected:**
```json
{ "room": "room.30", "room_seq": 300, "read_seq": 140, "unread": 160 }
```

✅ **160 unread computed from two integers**, with no queue, no per-message
storage, and no drift — because there is nothing to drift *from*.

Measure the debounce win over five minutes of active reading:

| | Receipts sent |
|---|---------------|
| One per message rendered | 438 |
| Debounced 2 s (protocol §3.3) | **19** |

**23× fewer**, identical user-visible behaviour.

### The dedup window, and the one Module 13 shrinks

Server-side idempotency is `UNIQUE (room_id, client_id)`. Size it:

```bash
pg -c "SELECT pg_size_pretty(pg_relation_size('uq_message_room_client'));"
```
```
 1418 MB
```

**1.4 GB at 50 million rows**, and it grows forever, to serve a lookup that only
matters for a few seconds after a send. Put Redis in front:

```python
async def is_duplicate(room_key: str, client_id: str) -> bool:
    # NX + EX: set only if absent, expire in 24h. One round trip, atomic.
    fresh = await redis.set(f"dedup:{{{room_key}}}:{client_id}", "1",
                            nx=True, ex=86400)
    return not fresh
```

```bash
python manage.py shell -c "
import asyncio, time
from chat.dedup import is_duplicate
async def bench(n=20000):
    t0=time.perf_counter()
    for i in range(n): await is_duplicate('room.1', f'c-{i}')
    print(f'{(time.perf_counter()-t0)/n*1000:.3f} ms/check (redis)')
asyncio.run(bench())"
```
**Expected:**
```
0.091 ms/check (redis)
```
versus **0.412 ms** for the Postgres `ON CONFLICT … RETURNING` round trip.

✅ **4.5× faster** — but be precise about what you bought. The Redis key is a
*fast path*, not the guarantee: Redis restarts and the window re-opens. The unique
index stays as the backstop. This is the same shape as every cache decision in the
course: the cache makes the common case cheap, the durable store makes the rare
case correct.

And the window itself:

| Layer | Dedup window | Cost |
|-------|--------------|------|
| Redis `SET NX EX 86400` | 24 hours | ~72 B/key, expires itself |
| `UNIQUE (room_id, client_id)` | forever | 1.4 GB and growing at 50M rows |
| After Module 13 partitions the table | **one month** | per-partition index |

That last row is the one to remember. Postgres requires the partition key in every
unique index, so Module 13's constraint becomes `(room_id, client_id, created_at)`
— which enforces uniqueness only *within a partition*. Your dedup window silently
becomes the partition width, with no application code change. Bound your client's
retry policy well inside it, and write the number down.

---

## Part J — What global ordering would have cost

Last measurement, and it is the one that settles the design argument.

Add a switch that routes every room through one counter and one stream:

```bash
export PULSE_GLOBAL_ORDER=1     # single seq key, single stream, single group
```

Then inject one sick room — a persistence path that takes 2 seconds:

```bash
export PULSE_SLOW_ROOM=room.99
export PULSE_SLOW_DELIVERY_MS=2000
k6 run --vus 2000 --duration 2m code/mixed_rooms.js   # 100 rooms, 1 of them sick
```

**Expected — per-room ordering (`PULSE_GLOBAL_ORDER` unset):**
```
room.99      p50  2,041ms   p99  2,140ms
other rooms  p50     11ms   p99    138ms
```

**Expected — global ordering:**
```
room.99      p50  2,038ms   p99  2,144ms
other rooms  p50  2,036ms   p99  2,190ms
```

✅ **Global ordering converted one sick room into a sick system.** The other 99
rooms went from a 138 ms p99 to 2,190 ms — a 15.9× regression — for an ordering
property no user can observe, because no user can watch two rooms at the same
instant with millisecond precision.

The second cost does not even need a benchmark: a global counter makes every room
dependent on every other room, which destroys the shard boundary Module 14 needs
and makes the resume query unable to use the `(room_id, seq)` index Module 12
builds the whole store around.

Record it:
```markdown
## Module 10 — Ordering

- Lua INCR+XADD: 0 inversions in 1,000,000 sends, 31,904 sends/s (was 412/10,048)
- Postgres allocator: 2,914/s and 34ms p99 at 64 senders — correct but 11x slower
- Global ordering: 1 slow room takes every other room's p99 from 138ms to 2,190ms
- Semantics: at-most-once loses 29/200; at-least-once duplicates 11/200;
             at-least-once + (room, client_id) shows the user neither
```

---

## What you built

- A **Lua script** that allocates a sequence number and appends the entry
  atomically — killing both the gap bug and the inversion bug Module 09
  introduced, and getting 1.73× throughput for free by removing a round trip.
- **High-water-mark recovery** so a Redis restart cannot reset every room's
  sequence to 1 — the single nastiest failure mode in this design.
- `resume` / `resume.batch` with bounded batches, `has_more` paging, an abandon
  threshold, a clamped `from_seq`, and `to_seq` used correctly as the
  permanent-gap step.
- A client that **joins before it resumes**, tracks contiguity, buffers ahead,
  and repairs on a 500 ms debounce that turns three requests into one.
- Proof, from a real two-minute network cut, that the difference is **98 lost
  messages versus 0**.
- The demonstration that a stream position is per worker process and therefore
  cannot be a client cursor.
- All three delivery semantics measured side by side, including the duplicates
  that exist on the wire and not on the screen.
- The head-of-line blocking that global ordering would have bought you: 138 ms →
  2,190 ms p99 for every healthy room.

**The guarantee is now complete**, with the caveats the README states.

Now do [`challenge.md`](./challenge.md).

Then: [Module 11 — Presence & Rate Limiting](../11-presence-and-rate-limiting/).
