# Lab 05 — Build a Protocol You Could Actually Ship

**You'll:** write a dependency-free ULID generator and prove it sorts by time;
build the envelope codec — strict on the way in, tolerant on the way out;
migrate `Message` to carry `client_id`, `seq` and `reply_to` using the
three-step add/backfill/enforce pattern; write the idempotent
allocate-and-insert as a single synchronous transaction called across the async
bridge; wire the full ack ladder; **prove idempotency under 64 concurrent
retries**; **prove gap detection catches a message you deliberately drop**;
replace disconnect-on-bad-input with `error` frames; make the browser client do
optimistic send with `client_id` reconciliation (and watch the double-bubble bug
first); and measure what the envelope costs in bytes and in CPU.

⏱️ ~130 min. Work in `django-chat-course/apps/pulse`.

```bash
cd django-chat-course/apps/pulse
source ../../.venv/bin/activate
set -a; source env.dev; set +a
docker compose -p pulse-dev -f ../../infra/compose.dev.yml up -d
```

> **Run one worker for this whole lab.** `uvicorn ... --workers 1`. Module 04
> showed you why; until Module 07 there is no cross-process delivery and the
> measurements here would be meaningless with more.

Reference machine: **8-core / 16 GB, Ubuntu 24.04, Python 3.12, Django 5.1,
Channels 4.1, Postgres 16, Uvicorn + uvloop.**

---

## Part A — A ULID, in fifteen lines

`client_id` must be **time-sortable** so the dedup index stays dense (Module 12
measures why at 50 million rows). Python 3.12 has no `uuid7()`, and this is too
small to be a dependency. Create `chat/ids.py`:

```python
"""ULID: 48 bits of millisecond timestamp + 80 bits of randomness,
Crockford base32, 26 characters, lexicographically sortable by time.

Deliberately not a dependency. The same reasoning as Module 12's
code/snowflake.py: an ID scheme you cannot read is an ID scheme you cannot
debug at 3am.
"""
import os
import time

_ALPHABET = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"      # Crockford: no I, L, O, U
_last_ms = 0
_last_rand = 0


def _b32(value: int, length: int) -> str:
    out = []
    for _ in range(length):
        out.append(_ALPHABET[value & 0x1F])
        value >>= 5
    return "".join(reversed(out))


def ulid() -> str:
    """Monotonic within a millisecond: same ms => increment the random part."""
    global _last_ms, _last_rand
    ms = int(time.time() * 1000)
    if ms == _last_ms:
        _last_rand += 1                       # strictly increasing, same ms
    else:
        _last_ms, _last_rand = ms, int.from_bytes(os.urandom(10), "big")
    return _b32(ms, 10) + _b32(_last_rand & ((1 << 80) - 1), 16)
```

```bash
python -c "
from chat.ids import ulid
import time
a = [ulid() for _ in range(5)]
time.sleep(0.01)
b = [ulid() for _ in range(5)]
for x in a + b: print(x)
print('sorted by generation order:', (a + b) == sorted(a + b))
print('length:', len({len(x) for x in a+b}), 'distinct lengths')
"
```

**Expected:**
```
01JQ8Z4K7M8YQ2VBXR3N5TDGWH
01JQ8Z4K7M8YQ2VBXR3N5TDGWJ
01JQ8Z4K7M8YQ2VBXR3N5TDGWK
01JQ8Z4K7M8YQ2VBXR3N5TDGWM
01JQ8Z4K7M8YQ2VBXR3N5TDGWN
01JQ8Z4K7XPQF0A6HC2E9JR4TB
...
sorted by generation order: True
length: 1 distinct lengths
```

✅ Note the first ten characters are identical within a millisecond and then
advance — that is the timestamp prefix. Sorting the strings sorts by creation
time, which is what keeps a B-tree index on `client_id` appending to its
rightmost leaf instead of scattering. Compare to `uuid4()`:

```bash
python -c "
import uuid
u = [str(uuid.uuid4()) for _ in range(5)]
print('\n'.join(u)); print('sorted:', u == sorted(u))"
```
**Expected:** `sorted: False` — and it will be false essentially always. That is
the property Module 12 charges you for.

---

## Part B — The envelope codec

Create `chat/protocol.py`. Two functions and one rule: **strict inbound,
tolerant outbound.**

```python
"""Pulse wire protocol v1. Normative reference: 05-.../code/pulse-protocol-v1.md

Inbound (client -> server) is STRICT: unknown types and unexpected fields are
errors, because a client sending a field you do not honour is a client whose
author believes it works.

Outbound-shaped parsing (anything a future server might send) is TOLERANT:
unknown keys are preserved and ignored. That asymmetry is Module 04's
challenge-1 rule and it is the whole of forward compatibility.
"""
from dataclasses import dataclass, field
from typing import Any

PROTOCOL_VERSION = 1
MAX_BODY = 4096          # ~1,000 characters in any script. Slack's limit is 4,000.

# The allowlist IS the schema. Nothing outside it reaches a group_send.
CLIENT_FIELDS: dict[str, set[str]] = {
    "message.create": {"client_id", "body", "reply_to"},
    "message.edit":   {"id", "body"},
    "message.delete": {"id"},
    "typing.start":   set(),
    "read.upto":      {"seq"},
    "resume":         {"from_seq"},
    "ping":           {"ts"},
}

REQUIRED_FIELDS: dict[str, set[str]] = {
    "message.create": {"client_id", "body"},
    "message.edit":   {"id", "body"},
    "message.delete": {"id"},
    "read.upto":      {"seq"},
    "resume":         {"from_seq"},
}


class ProtocolError(Exception):
    """Carries a machine-readable code so the client can branch, not just log."""

    def __init__(self, code: str, message: str, **extra):
        super().__init__(message)
        self.code, self.message, self.extra = code, message, extra

    def frame(self, client_id: str | None = None) -> dict:
        data = {"code": self.code, "message": self.message, **self.extra}
        if client_id:
            data["client_id"] = client_id
        return {"v": PROTOCOL_VERSION, "type": "error", "ts": 0, "data": data}


@dataclass(slots=True)
class Inbound:
    type: str
    data: dict[str, Any] = field(default_factory=dict)


def parse_inbound(raw: Any) -> Inbound:
    if not isinstance(raw, dict):
        raise ProtocolError("bad_frame", "frame must be a JSON object")

    v = raw.get("v", PROTOCOL_VERSION)
    if not isinstance(v, int) or v > PROTOCOL_VERSION:
        raise ProtocolError("unsupported_version",
                            f"this server speaks protocol v{PROTOCOL_VERSION}",
                            server_version=PROTOCOL_VERSION, client_version=v)

    mtype = raw.get("type")
    allowed = CLIENT_FIELDS.get(mtype)
    if allowed is None:
        raise ProtocolError("unknown_type", f"unknown type {mtype!r}")

    data = raw.get("data")
    if data is None:                      # Module 04 spoke flat frames. Accept both.
        data = {k: v for k, v in raw.items() if k not in {"v", "type", "room", "ts"}}
    if not isinstance(data, dict):
        raise ProtocolError("bad_frame", "`data` must be an object")

    extra = set(data) - allowed
    if extra:
        raise ProtocolError("unexpected_fields",
                            "fields this server does not honour",
                            fields=sorted(extra)[:8])

    missing = REQUIRED_FIELDS.get(mtype, set()) - set(data)
    if missing:
        raise ProtocolError("missing_fields", "required fields absent",
                            fields=sorted(missing))

    if mtype == "message.create":
        body = data.get("body")
        if not isinstance(body, str) or not body.strip():
            raise ProtocolError("empty_body", "body must be a non-empty string")
        if len(body) > MAX_BODY:
            raise ProtocolError("body_too_long", f"body exceeds {MAX_BODY} chars",
                                max=MAX_BODY, got=len(body))
        cid = data.get("client_id")
        if not isinstance(cid, str) or not (10 <= len(cid) <= 64):
            raise ProtocolError("bad_client_id",
                                "client_id must be a 10-64 char string (ULID)")

    return Inbound(type=mtype, data=data)


def envelope(mtype: str, room: str, ts: int, **data) -> dict:
    """Every server->client frame goes through here. One shape, no exceptions."""
    return {"v": PROTOCOL_VERSION, "type": mtype, "room": room, "ts": ts,
            "data": data}
```

Test it before you wire it — the protocol is the one thing worth unit-testing in
this course:

```bash
python - <<'EOF'
import django, os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pulse.settings"); django.setup()
from chat.protocol import parse_inbound, ProtocolError, envelope
from chat.ids import ulid

ok = {"v":1,"type":"message.create","data":{"client_id":ulid(),"body":"hi"}}
print("ok        ->", parse_inbound(ok).type)

cases = [
    {"type":"message.create","data":{"client_id":ulid(),"body":"hi","sender":"admin"}},
    {"type":"message.create","data":{"client_id":ulid(),"body":"   "}},
    {"type":"message.create","data":{"client_id":"short","body":"hi"}},
    {"type":"message.create","data":{"client_id":ulid(),"body":"A"*5000}},
    {"type":"chat.message","data":{}},
    {"v":2,"type":"message.create","data":{"client_id":ulid(),"body":"hi"}},
    {"type":"message.create","data":{"body":"hi"}},
]
for c in cases:
    try:
        parse_inbound(c); print("UNEXPECTEDLY OK:", c)
    except ProtocolError as e:
        print(f"{e.code:<20} {e.message}  {e.extra or ''}")
EOF
```

**Expected:**
```
ok        -> message.create
unexpected_fields    fields this server does not honour  {'fields': ['sender']}
empty_body           body must be a non-empty string  
bad_client_id        client_id must be a 10-64 char string (ULID)  
body_too_long        body exceeds 4096 chars  {'max': 4096, 'got': 5000}
unknown_type         unknown type 'chat.message'  
unsupported_version  this server speaks protocol v1  {'server_version': 1, 'client_version': 2}
missing_fields       required fields absent  {'fields': ['client_id']}
```

✅ Two of those deserve a second look.

**`unknown_type: 'chat.message'`** — a client tried to inject an *internal
channel-layer event type*. It is rejected because `CLIENT_FIELDS` has no entry
for it, which is exactly why the README insists the two namespaces stay
separate. If wire types and event types were the same vocabulary, this frame
would have been a remote fan-out trigger.

**`unsupported_version`** carries `server_version` in the error, so a v2 client
learns what to downgrade to instead of retrying forever.

---

## Part C — Migrate the domain model

`Message` currently has `room`, `sender`, `body`, `created_at`. It needs
`client_id`, `seq`, `reply_to`, and a per-room sequence counter.

`chat/models.py` — update `Message`, add `RoomSequence`:

```python
class Message(models.Model):
    room       = models.ForeignKey(Room, on_delete=models.CASCADE, related_name="messages")
    sender     = models.ForeignKey("chat.User", on_delete=models.PROTECT)
    client_id  = models.CharField(max_length=64)          # ULID, from the client
    seq        = models.BigIntegerField()                 # per-room, gapless
    body       = models.TextField()
    reply_to   = models.ForeignKey("self", null=True, blank=True,
                                   on_delete=models.SET_NULL, related_name="replies")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["room", "-id"], name="idx_msg_scrollback")]
        constraints = [
            # THE idempotency guarantee. Not an optimization: the database
            # enforces it, so two concurrent retries cannot both win.
            models.UniqueConstraint(fields=["room", "client_id"],
                                    name="uq_message_room_client"),
            # Gapless per-room ordering, enforced rather than assumed.
            models.UniqueConstraint(fields=["room", "seq"],
                                    name="uq_message_room_seq"),
        ]


class RoomSequence(models.Model):
    """One row per room. `last_seq` is the high-water mark handed out so far.

    A separate table rather than a column on Room because the update rate is
    completely different: Room is read constantly and written almost never;
    this row is written once per message. Putting them together means every
    message write bloats a Room tuple and every Room read competes with it.
    """
    room     = models.OneToOneField(Room, on_delete=models.CASCADE,
                                    primary_key=True, related_name="sequence")
    last_seq = models.BigIntegerField(default=0)
```

Now the migration. **Do not let `makemigrations` add non-null columns to a table
with rows** — it will ask for a one-off default and give every existing message
`seq = 0`, which violates the unique constraint you just declared. Write the
canonical three-step migration by hand:
`chat/migrations/0003_protocol_fields.py`

```python
from django.db import migrations, models
import django.db.models.deletion


def backfill(apps, schema_editor):
    """Assign a per-room seq and a synthetic client_id to pre-protocol rows.

    Runs inside the migration's transaction. Fine at lab scale (500 rows);
    at ten million rows this is exactly the kind of migration Module 13
    teaches you to batch and run outside a single transaction.
    """
    Message = apps.get_model("chat", "Message")
    RoomSequence = apps.get_model("chat", "RoomSequence")
    for room_id in Message.objects.values_list("room_id", flat=True).distinct():
        n = 0
        for n, m in enumerate(
                Message.objects.filter(room_id=room_id).order_by("id"), start=1):
            Message.objects.filter(pk=m.pk).update(
                seq=n, client_id=f"legacy-{m.pk:016d}")
        RoomSequence.objects.update_or_create(room_id=room_id,
                                              defaults={"last_seq": n})


class Migration(migrations.Migration):
    dependencies = [("chat", "0002_room_membership_message")]

    operations = [
        migrations.CreateModel(
            name="RoomSequence",
            fields=[
                ("room", models.OneToOneField(
                    on_delete=django.db.models.deletion.CASCADE, primary_key=True,
                    serialize=False, related_name="sequence", to="chat.room")),
                ("last_seq", models.BigIntegerField(default=0)),
            ],
        ),
        # 1. ADD, nullable — never blocks, never needs a default.
        migrations.AddField("message", "client_id",
                            models.CharField(max_length=64, null=True)),
        migrations.AddField("message", "seq",
                            models.BigIntegerField(null=True)),
        migrations.AddField("message", "reply_to", models.ForeignKey(
            null=True, blank=True, on_delete=django.db.models.deletion.SET_NULL,
            related_name="replies", to="chat.message")),
        # 2. BACKFILL.
        migrations.RunPython(backfill, migrations.RunPython.noop),
        # 3. ENFORCE.
        migrations.AlterField("message", "client_id",
                              models.CharField(max_length=64)),
        migrations.AlterField("message", "seq", models.BigIntegerField()),
        migrations.AddConstraint("message", models.UniqueConstraint(
            fields=["room", "client_id"], name="uq_message_room_client")),
        migrations.AddConstraint("message", models.UniqueConstraint(
            fields=["room", "seq"], name="uq_message_room_seq")),
    ]
```

```bash
python manage.py sqlmigrate chat 0003 | grep -E '^(ALTER|CREATE)' | head
python manage.py migrate chat
```

**Expected:**
```sql
CREATE TABLE "chat_roomsequence" ("room_id" bigint NOT NULL PRIMARY KEY, "last_seq" bigint NOT NULL);
ALTER TABLE "chat_message" ADD COLUMN "client_id" varchar(64) NULL;
ALTER TABLE "chat_message" ADD COLUMN "seq" bigint NULL;
ALTER TABLE "chat_message" ADD COLUMN "reply_to_id" bigint NULL ...;
ALTER TABLE "chat_message" ALTER COLUMN "client_id" SET NOT NULL;
CREATE UNIQUE INDEX "uq_message_room_client" ON "chat_message" ("room_id", "client_id");
CREATE UNIQUE INDEX "uq_message_room_seq" ON "chat_message" ("room_id", "seq");
```
```
  Applying chat.0003_protocol_fields... OK
```

Verify the backfill:

```bash
docker exec -i pulse-postgres psql -U pulse -d pulse -c "
SELECT r.slug, count(*) AS msgs, min(m.seq), max(m.seq), s.last_seq
FROM chat_message m JOIN chat_room r ON r.id=m.room_id
JOIN chat_roomsequence s ON s.room_id=r.id GROUP BY 1,5;"
```

**Expected — contiguous from 1, and `last_seq` matching:**
```
  slug   | msgs | min | max | last_seq
---------+------+-----+-----+----------
 general |  502 |   1 | 502 |      502
```

> **Why three steps instead of one?** A single `ADD COLUMN ... NOT NULL DEFAULT
> 'x'` is fast in Postgres 11+ but still rewrites nothing while lying about
> history, and the constraint would be added before the data is correct. The
> add/backfill/enforce shape is the one that works on a table you cannot lock,
> and Module 13 runs it against a partitioned table where the difference is an
> outage.

---

## Part D — The idempotent send

This is the heart of the module: **allocate a sequence and insert a message,
atomically, idempotently, once.**

`transaction.atomic()` is **sync-only** in Django 5.1, so the whole unit is one
synchronous function crossing the bridge — not a chain of `await`s. Create
`chat/service.py`:

```python
from dataclasses import dataclass

from channels.db import database_sync_to_async
from django.db import connection, transaction


@dataclass(slots=True)
class SendResult:
    id: int
    seq: int
    ts: int
    duplicate: bool


@database_sync_to_async
def send_message(*, room_id: int, sender_id: int, client_id: str,
                 body: str, reply_to: int | None = None) -> SendResult:
    """Allocate a per-room seq and insert, idempotently on (room, client_id).

    One sync function, one transaction, called from async via
    database_sync_to_async. Not three awaits: transaction.atomic() is sync-only
    (Module 02), and 'allocate then insert' must be atomic or two senders
    interleave and both get the same seq.
    """
    with transaction.atomic(), connection.cursor() as cur:
        # 1. Allocate. UPSERT so a room's first message creates the counter.
        cur.execute("""
            INSERT INTO chat_roomsequence (room_id, last_seq) VALUES (%s, 1)
            ON CONFLICT (room_id)
            DO UPDATE SET last_seq = chat_roomsequence.last_seq + 1
            RETURNING last_seq
        """, [room_id])
        seq = cur.fetchone()[0]

        # 2. Insert, idempotently. DO NOTHING + RETURNING gives us zero rows
        #    on a retry, which is how we detect one without a second SELECT
        #    in the common case.
        cur.execute("""
            INSERT INTO chat_message
                (room_id, sender_id, client_id, seq, body, reply_to_id, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, now())
            ON CONFLICT (room_id, client_id) DO NOTHING
            RETURNING id, seq, created_at
        """, [room_id, sender_id, client_id, seq, body, reply_to])
        row = cur.fetchone()

        if row is not None:
            return SendResult(row[0], row[1], int(row[2].timestamp() * 1000), False)

        # 3. It was a retry. Return the ORIGINAL result, so the client's
        #    optimistic bubble reconciles to the same id and seq it would
        #    have got the first time.
        cur.execute("""
            SELECT id, seq, created_at FROM chat_message
            WHERE room_id = %s AND client_id = %s
        """, [room_id, client_id])
        row = cur.fetchone()
        return SendResult(row[0], row[1], int(row[2].timestamp() * 1000), True)
```

> ⚠️ **This function contains a real bug and you are going to leave it there for
> now.** Step 1 allocates a sequence *before* step 2 decides whether it will
> insert. On a retry, the allocation still commits — so a sequence number is
> **burned**, leaving a permanent hole that every client's gap detector will
> report as a missing message forever. Challenge task 1 makes you reproduce it
> under concurrency and fix it. Notice it now; fix it there.

Why raw SQL rather than `get_or_create`? Because `get_or_create` is
`SELECT`-then-`INSERT`, which is not atomic: two concurrent retries both see no
row, both insert, one raises `IntegrityError`, and you are back to writing the
conflict handling by hand — but now with an exception on the hot path and a
wasted round trip. `ON CONFLICT ... DO NOTHING RETURNING` does it in one
statement, in the database, where the unique index is.

---

## Part E — Wire the ack ladder

Rewrite `RoomConsumer.receive_json` in `chat/consumers.py`:

```python
import time

from chat.protocol import ProtocolError, envelope, parse_inbound
from chat.service import send_message


def now_ms() -> int:
    return int(time.time() * 1000)


class RoomConsumer(AsyncJsonWebsocketConsumer):
    # ... connect() / disconnect() unchanged from Module 04 ...

    async def receive_json(self, content, **kwargs):
        try:
            frame = parse_inbound(content)
        except ProtocolError as e:
            # An ERROR FRAME, not a disconnect. Closing the socket over a
            # 4-character body is how a validation bug becomes a reconnect storm.
            cid = (content or {}).get("data", {}).get("client_id") \
                if isinstance(content, dict) else None
            await self.send_json({**e.frame(cid), "ts": now_ms(),
                                  "room": getattr(self, "group", "")})
            return

        handler = getattr(self, f"_on_{frame.type.replace('.', '_')}", None)
        if handler is None:
            await self.send_json(envelope("error", self.group, now_ms(),
                                          code="not_implemented", message=frame.type))
            return
        await handler(frame.data)

    # ---------------------------------------------------------------- handlers
    async def _on_ping(self, data):
        await self.send_json(envelope("pong", self.group, now_ms(),
                                      ts=data.get("ts")))

    async def _on_message_create(self, data):
        result = await send_message(
            room_id=self.room.id, sender_id=self.user.id,
            client_id=data["client_id"], body=data["body"].strip(),
            reply_to=data.get("reply_to"))

        # RUNG 2 of the ladder: ack the SENDER with the canonical identity.
        await self.send_json(envelope(
            "message.ack", self.group, result.ts,
            client_id=data["client_id"], id=result.id, seq=result.seq,
            duplicate=result.duplicate))

        if result.duplicate:
            # Already fanned out the first time. Fanning out again would show
            # every OTHER member a second copy -- the ack is idempotent, the
            # broadcast must not be repeated.
            return

        await self.channel_layer.group_send(self.group, {
            "type": "chat.message",              # INTERNAL vocabulary
            "id": result.id, "seq": result.seq, "ts": result.ts,
            "client_id": data["client_id"],      # echoed for reconciliation
            "sender": self.user.username, "body": data["body"].strip(),
            "reply_to": data.get("reply_to"),
        })

    # ------------------------------------------------- channel-layer handlers
    async def chat_message(self, event):
        await self.send_json(envelope(
            "message.new", self.group, event["ts"],
            id=event["id"], seq=event["seq"], client_id=event["client_id"],
            sender=event["sender"], body=event["body"],
            reply_to=event.get("reply_to")))
```

Restart and drive it by hand:

```bash
uvicorn pulse.asgi:application --port 8000 --loop uvloop --workers 1 &
websocat "ws://localhost:8000/ws/room/general/?as=u0"
```
```json
{"v":1,"type":"message.create","data":{"client_id":"01JQ8Z4K7M8YQ2VBXR3N5TDGWH","body":"first protocol message"}}
```

**Expected — two frames back, ack then broadcast:**
```json
{"v": 1, "type": "message.ack", "room": "room.general", "ts": 1735689600241, "data": {"client_id": "01JQ8Z4K7M8YQ2VBXR3N5TDGWH", "id": 503, "seq": 503, "duplicate": false}}
{"v": 1, "type": "message.new", "room": "room.general", "ts": 1735689600241, "data": {"id": 503, "seq": 503, "client_id": "01JQ8Z4K7M8YQ2VBXR3N5TDGWH", "sender": "u0", "body": "first protocol message", "reply_to": null}}
```

Now send **the exact same frame again** — a retry:

**Expected — one frame, and note `duplicate` and the identical `id`/`seq`:**
```json
{"v": 1, "type": "message.ack", "room": "room.general", "ts": 1735689600241, "data": {"client_id": "01JQ8Z4K7M8YQ2VBXR3N5TDGWH", "id": 503, "seq": 503, "duplicate": true}}
```

✅ **No second `message.new`, and no second row.** The retry got the *original*
result — same `id`, same `seq`, same `ts` — so the client's optimistic bubble
reconciles to exactly the state it would have reached had the first ack arrived.
That is idempotent processing, and it is the property Module 09's at-least-once
Streams consumer depends on absolutely.

```bash
docker exec -i pulse-postgres psql -U pulse -d pulse -c "
SELECT count(*) FROM chat_message WHERE client_id='01JQ8Z4K7M8YQ2VBXR3N5TDGWH';"
```
**Expected:** `1`

---

## Part F — Prove it under concurrency

One retry at a time proves nothing about a race. Fire 64 at once:

```bash
python - <<'EOF'
import asyncio, json, websockets
from collections import Counter

CID = "01JQ8Z4K9XCONCURRENTRETRY1"
URL = "ws://localhost:8000/ws/room/general/?as=u0"

async def attempt(i, results):
    async with websockets.connect(URL, ping_interval=None) as ws:
        await ws.recv()                                  # hello
        await ws.send(json.dumps({"v":1,"type":"message.create",
                                  "data":{"client_id":CID,"body":"64-way retry"}}))
        while True:
            env = json.loads(await ws.recv())
            if env["type"] == "message.ack":
                results.append((env["data"]["id"], env["data"]["seq"],
                                env["data"]["duplicate"]))
                return

async def main():
    results = []
    async with asyncio.TaskGroup() as tg:
        for i in range(64):
            tg.create_task(attempt(i, results))
    ids  = Counter(r[0] for r in results)
    seqs = Counter(r[1] for r in results)
    dups = Counter(r[2] for r in results)
    print("acks               :", len(results))
    print("distinct ids       :", len(ids), "->", list(ids))
    print("distinct seqs      :", len(seqs), "->", list(seqs))
    print("duplicate=True     :", dups[True], " duplicate=False:", dups[False])

asyncio.run(main())
EOF
```

**Expected:**
```
acks               : 64
distinct ids       : 1 -> [504]
distinct seqs      : 1 -> [504]
duplicate=True     : 63  duplicate=False: 1
```

```bash
docker exec -i pulse-postgres psql -U pulse -d pulse -c "
SELECT count(*) FROM chat_message WHERE client_id='01JQ8Z4K9XCONCURRENTRETRY1';"
```
**Expected:** `1`

✅ **64 concurrent attempts, one row, one id, one seq, 63 marked duplicate.** The
unique index did the arbitration — not application logic, which would have
raced. Every attempt got a *correct* answer, so a client can retry as
aggressively as its backoff policy likes.

Now look at the damage the known bug did:

```bash
docker exec -i pulse-postgres psql -U pulse -d pulse -c "
SELECT last_seq FROM chat_roomsequence s JOIN chat_room r ON r.id=s.room_id
WHERE r.slug='general';
SELECT max(seq) FROM chat_message m JOIN chat_room r ON r.id=m.room_id
WHERE r.slug='general';"
```

**Expected — the counter has run away from reality:**
```
 last_seq
----------
      567
 max
-----
 504
```

✅ **63 sequence numbers burned in one burst.** Every one of them is a permanent
hole. A client doing gap detection will forever report 63 missing messages that
never existed, and Module 10's `resume` will re-query for them on every
reconnect. Challenge task 1 is to reproduce this as a failing test and fix it.

---

## Part G — Gap detection, proved

Add a **deliberate dropper** to the consumer so you can create a gap on demand:

```python
# chat/consumers.py — TEMPORARY, for this measurement only
import os
DROP_EVERY = int(os.environ.get("PULSE_DROP_EVERY", "0"))

    async def chat_message(self, event):
        if DROP_EVERY and event["seq"] % DROP_EVERY == 0:
            return                       # silently drop. Exactly like a lost frame.
        await self.send_json(envelope("message.new", ...))
```

A client-side gap detector is eight lines. This is the same logic Module 17's
Next.js client and Module 10's `resume` are built on:

```bash
cat > /tmp/gapcheck.py <<'EOF'
import asyncio, json, websockets

async def main():
    url = "ws://localhost:8000/ws/room/general/?as=u1"
    async with websockets.connect(url, ping_interval=None) as ws:
        await ws.recv()
        last, gaps, seen = None, [], 0
        async for raw in ws:
            env = json.loads(raw)
            if env["type"] != "message.new":
                continue
            seq = env["data"]["seq"]
            if last is not None and seq != last + 1:
                gaps.append((last, seq))
                print(f"GAP: expected {last+1}, got {seq} "
                      f"(missing {seq-last-1})", flush=True)
            last, seen = seq, seen + 1
            if seen >= 30:
                break
        print(f"\nreceived {seen}, gaps {len(gaps)}: {gaps}")
asyncio.run(main())
EOF
```

Run the server with the dropper on, the detector in one terminal, and a sender
in another:

```bash
kill %1; PULSE_DROP_EVERY=7 uvicorn pulse.asgi:application --port 8000 --loop uvloop &
sleep 3
python /tmp/gapcheck.py &
# reuse Module 04's probe: 35 messages as fast as the socket accepts them
python ../../04-channels-chat-single-node/code/wsprobe.py blast \
       --room general --user u0 --n 35
```

> `wsprobe blast` sends Module 04's flat, pre-v1 frames
> (`{"type":"message.create","body":"blast-0"}`). They still work, because
> `parse_inbound` treats top-level keys as `data` when there is no `data`
> wrapper — the pre-v1 compatibility clause in
> [`code/pulse-protocol-v1.md`](./code/pulse-protocol-v1.md) §6. They will be
> rejected for a missing `client_id`, so add one first: pass
> `--n 35` after editing `blast` to emit `{"client_id": ulid(), "body": ...}`,
> or drive it with the four-line `websocat` loop below.

```bash
for i in $(seq 1 35); do
  printf '{"v":1,"type":"message.create","data":{"client_id":"01JQ8Z4KB%015d","body":"m%d"}}\n' "$i" "$i"
  sleep 0.05
done | websocat "ws://localhost:8000/ws/room/general/?as=u0" >/dev/null
```

**Expected:**
```
GAP: expected 511, got 512 (missing 1)
GAP: expected 518, got 519 (missing 1)
GAP: expected 525, got 526 (missing 1)
GAP: expected 532, got 533 (missing 1)

received 30, gaps 4: [(510, 512), (517, 519), (524, 526), (531, 533)]
```

✅ **The client detected every drop, in real time, with `last + 1`.** That is the
entire value of a gapless per-room sequence: not that messages cannot be lost,
but that **loss becomes observable**, locally, immediately, by the party who
cares.

Contrast with the alternative:

```bash
kill %1; PULSE_DROP_EVERY=7 uvicorn ... &   # same, but comment out the seq field
```
Without `seq`, the client sees a stream of messages with unique ids and no way to
know that anything is missing. It looks completely healthy. The only detection
mechanism left is a human saying "did you see what I wrote?"

What the client does *with* a detected gap is Module 10's `resume` frame:

```json
{"v":1,"type":"resume","data":{"from_seq":510}}
```

Turn the dropper off (`PULSE_DROP_EVERY=0`) before continuing.

---

## Part H — Error frames and version negotiation

Errors must not close sockets. Verify each path:

```bash
websocat "ws://localhost:8000/ws/room/general/?as=u0"
```
```json
{"v":1,"type":"message.create","data":{"client_id":"01JQ8Z4KAAAAAAAAAAAAAAAAAA","body":"  "}}
{"v":1,"type":"message.create","data":{"client_id":"01JQ8Z4KAAAAAAAAAAAAAAAAAB","body":"hi","sender":"admin"}}
{"v":9,"type":"message.create","data":{"client_id":"01JQ8Z4KAAAAAAAAAAAAAAAAAC","body":"hi"}}
{"v":1,"type":"message.create","data":{"client_id":"01JQ8Z4KAAAAAAAAAAAAAAAAAD","body":"still connected"}}
```

**Expected — four responses on one uninterrupted connection:**
```json
{"v":1,"type":"error","ts":...,"room":"room.general","data":{"code":"empty_body","message":"body must be a non-empty string","client_id":"01JQ8Z4KAAAAAAAAAAAAAAAAAA"}}
{"v":1,"type":"error","ts":...,"room":"room.general","data":{"code":"unexpected_fields","message":"fields this server does not honour","fields":["sender"],"client_id":"01JQ8Z4KAAAAAAAAAAAAAAAAAB"}}
{"v":1,"type":"error","ts":...,"room":"room.general","data":{"code":"unsupported_version","message":"this server speaks protocol v1","server_version":1,"client_version":9,"client_id":"01JQ8Z4KAAAAAAAAAAAAAAAAAC"}}
{"v":1,"type":"message.ack","room":"room.general","ts":...,"data":{"client_id":"01JQ8Z4KAAAAAAAAAAAAAAAAAD","id":535,"seq":535,"duplicate":false}}
```

✅ **Three errors, no disconnect, and the fourth message worked.** Note the
`client_id` echoed into every error frame: without it, a client with three
messages in flight cannot tell *which* bubble to mark failed.

Now version negotiation at the handshake, which Module 04 already wired:

```bash
websocat --protocol pulse.v1 -v "ws://localhost:8000/ws/room/general/?as=u0" 2>&1 | head -2
websocat --protocol pulse.v9 -v "ws://localhost:8000/ws/room/general/?as=u0" 2>&1 | head -2
```

**Expected:**
```
[INFO  websocat] Connected;  Sec-WebSocket-Protocol: pulse.v1
[INFO  websocat] Connected;  (no subprotocol echoed)
```

Add the metric that makes deprecation an engineering decision rather than a
guess. Module 06 builds the full instrumentation layer; this is the first
counter, and it needs three lines of plumbing:

```bash
pip install --quiet prometheus-client
```
```python
# chat/metrics.py
from prometheus_client import CONTENT_TYPE_LATEST, Counter, generate_latest
from django.http import HttpResponse

CLIENT_VERSION = Counter("pulse_client_connections_total",
                         "connections by advertised protocol version", ["version"])
PROTOCOL_ERRORS = Counter("pulse_protocol_errors_total",
                          "rejected client frames", ["code"])


def metrics(request):
    return HttpResponse(generate_latest(), content_type=CONTENT_TYPE_LATEST)
```
```python
# pulse/urls.py
    path("metrics", chat_metrics.metrics),

# chat/consumers.py, in connect(), after computing `offered`
advertised = next((p for p in offered if p.startswith("pulse.v")), "pulse.none")
CLIENT_VERSION.labels(version=advertised).inc()

# chat/consumers.py, in the ProtocolError branch of receive_json()
PROTOCOL_ERRORS.labels(code=e.code).inc()
```

```bash
curl -s localhost:8000/metrics | grep pulse_client_connections_total
```
**Expected:**
```
pulse_client_connections_total{version="pulse.v1"} 47.0
pulse_client_connections_total{version="pulse.none"} 3.0
```

> **This is the whole discipline of protocol versioning in one counter.** When
> someone proposes v2, the question "can we drop v1?" has an answer with a
> number attached and a date it will reach zero.

---

## Part I — Optimistic send, and the double-bubble bug

First, **cause the bug**, because it is the one every chat client ships once.
In `chat_message`, drop `client_id` from the outbound frame:

```python
# TEMPORARY
await self.send_json(envelope("message.new", self.group, event["ts"],
                              id=event["id"], seq=event["seq"],
                              sender=event["sender"], body=event["body"]))
```

Update the browser client (`chat/templates/chat/room.html`) to render
optimistically:

```html
<script>
const pending = new Map();          // client_id -> DOM node

function ulid() {                   // browser-side, same shape as chat/ids.py
  const A = "0123456789ABCDEFGHJKMNPQRSTVWXYZ";
  const t = Date.now(); let s = "";
  for (let i = 9; i >= 0; i--) s = A[(t / 32 ** (9 - i)) & 31] + s;
  for (let i = 0; i < 16; i++) s += A[(Math.random() * 32) | 0];
  return s;
}

function send(body) {
  const cid = ulid();
  const node = document.createElement("div");
  node.textContent = `${who}: ${body}`;
  node.style.opacity = "0.45";                  // state = pending
  document.getElementById("log").append(node);
  pending.set(cid, node);
  ws.send(JSON.stringify({v: 1, type: "message.create",
                          data: {client_id: cid, body}}));
}

function onFrame(env) {
  const d = env.data;
  switch (env.type) {
    case "message.ack": {                        // state = queued
      const node = pending.get(d.client_id);
      if (node) { node.style.opacity = "1"; node.dataset.seq = d.seq; }
      break;
    }
    case "message.new": {
      if (d.client_id && pending.has(d.client_id)) {
        pending.delete(d.client_id);             // already on screen. STOP.
        break;
      }
      const node = document.createElement("div");
      node.textContent = `${d.sender}: ${d.body}`;
      node.dataset.seq = d.seq;
      document.getElementById("log").append(node);
      break;
    }
    case "error":
      const node = pending.get(d.client_id);
      if (node) { node.style.color = "crimson"; node.textContent += ` ✗ ${d.code}`; }
      break;
    default: break;                              // forward compatibility
  }
}
</script>
```

Reload `http://localhost:8000/room/general/?as=u0` and send a message.

**Expected — the bug:**
```
u0: hello        (faint, then solid — the optimistic bubble, acked)
u0: hello        (a second bubble, from the broadcast)
```

✅ There it is. The sender is a member of its own group, so it receives its own
`message.new` — and without `client_id` it has no way to recognize it as the
message already on screen.

Now put `client_id` back in `chat_message` and reload.

**Expected:**
```
u0: hello        (one bubble: faint -> solid, seq attached)
```

And in a second tab (`?as=u1`), exactly one bubble appears too — the *other*
user has no pending entry for that `client_id`, so it renders normally.

Test the failure path: stop the server, type a message, restart it.

**Expected:** the bubble stays faint (pending) and never turns solid. A real
client (Module 17) retries with **the same `client_id`** on reconnect, which is
safe precisely because of Part F.

---

## Part J — What the protocol costs

```bash
python - <<'EOF'
import json, timeit
env = {"v":1,"type":"message.new","room":"room.7","ts":1735689600123,
       "data":{"id":7241938,"client_id":"01JQ8Z4K7M8YQ2VBXR3N5TDGWH","seq":48213,
               "sender":"alice","body":"ok"}}
compact = json.dumps(env, separators=(",", ":"))
print("verbose bytes :", len(json.dumps(env)))
print("compact bytes :", len(compact))
print("body bytes    :", len(env["data"]["body"]))
print("overhead ratio: %.0fx" % (len(compact) / len(env["data"]["body"])))
n = 200_000
t = timeit.timeit(lambda: json.dumps(env, separators=(",", ":")), number=n)
print(f"json.dumps    : {t/n*1e6:.2f} us  -> {n/t:,.0f} envelopes/s on one core")
try:
    import orjson
    t2 = timeit.timeit(lambda: orjson.dumps(env), number=n)
    print(f"orjson.dumps  : {t2/n*1e6:.2f} us  -> {n/t2:,.0f}/s  ({t/t2:.1f}x)")
except ImportError:
    print("orjson.dumps  : pip install orjson to compare")
EOF
```

**Expected:**
```
verbose bytes : 185
compact bytes : 167
body bytes    : 2
overhead ratio: 84x
json.dumps    : 3.40 us  -> 294,118 envelopes/s on one core
orjson.dumps  : 0.81 us  -> 1,234,568/s  (4.2x)
```

✅ **84× overhead for a two-character message, and we are keeping it.** At
Module 06's safe operating point of 100,000 outbound msg/s, the envelope costs
16.7 MB/s of bandwidth (irrelevant on a LAN, real on mobile) and `json.dumps`
costs **0.34 of a core-second per second** out of the one core a worker has.
That is a third of your CPU budget going to serialization — which is why
Module 15 benchmarks `orjson`, and why the honest answer to "should we use
MessagePack" is "change the encoder first, and only then the format."

Measure the ack's share:

```bash
python - <<'EOF'
ack = 156     # bytes, from the Part E output
new = 180
members = 200
print(f"one send into a {members}-member room:")
print(f"  ack       : {ack} bytes  ({100*ack/(ack+new*members):.2f}% of the traffic)")
print(f"  broadcasts: {new*members:,} bytes")
EOF
```
**Expected:**
```
one send into a 200-member room:
  ack       : 156 bytes  (0.43% of the traffic)
  broadcasts: 36,000 bytes
```

✅ **The ack is 0.43% of the traffic and it is the entire basis of optimistic
send, retry safety, and the "sent ✓" state.** Compare with the delivery-receipt
row of the README's ladder: 200 receipts back to one socket would be another
36,000 bytes aimed at a single phone — 230× the ack's cost, for a feature large
rooms do not have. That arithmetic is why Pulse caps delivery receipts at
16-member rooms.

---

## What you measured

Record in `apps/pulse/results-05.md`:

| Measurement | Reference | Yours |
|-------------|-----------|-------|
| ULID sorts by generation order | True | |
| `uuid4()` sorts by generation order | False | |
| 64 concurrent retries → rows | **1** | |
| 64 concurrent retries → distinct `id`/`seq` | 1 / 1 | |
| Acks marked `duplicate` | 63 of 64 | |
| **Sequence numbers burned by the known bug** | **63** | |
| Gaps detected with `PULSE_DROP_EVERY=7` | 4 of 4 | |
| Gaps detectable without `seq` | 0 | |
| Envelope bytes (compact) for a 2-byte body | 167 (84×) | |
| `json.dumps` throughput, one core | 294,118/s | |
| `orjson.dumps` throughput, one core | 1,234,568/s (4.2×) | |
| Ack share of a 200-member send | 0.43% | |

---

## What you built

```
apps/pulse/chat/
├── ids.py            ← ULID: 26 chars, time-sortable, no dependency
├── protocol.py       ← strict inbound parse, allowlist, ProtocolError, envelope()
├── service.py        ← send_message(): one sync transaction, idempotent on
│                        (room, client_id) — with a known seq-allocation bug
├── consumers.py      ← the ack ladder, error frames, version metric
├── models.py         ← Message + client_id/seq/reply_to, RoomSequence
├── migrations/0003_protocol_fields.py   ← add / backfill / enforce
└── templates/chat/room.html             ← optimistic send + reconciliation
05-protocol-and-domain-design/code/
├── envelope.py                ← the codec as a standalone, importable module
└── pulse-protocol-v1.md       ← the normative spec later modules link to
```

And you established the four properties the rest of the course assumes:

- **`client_id` makes retry free.** 64 concurrent attempts produced one row and
  64 correct answers, arbitrated by a unique index rather than by application
  logic that races. Module 09's at-least-once Streams consumer is built entirely
  on this.
- **A gapless per-room `seq` makes loss observable.** Four deliberate drops, four
  detections, in real time, by the client. Module 10 turns each detection into a
  `resume`.
- **Errors are frames, not disconnects.** Three protocol violations on one
  uninterrupted connection, each carrying the `client_id` so the right bubble can
  be marked failed.
- **The envelope costs 84× the payload and that is the right call** — for
  reasons you can now state with numbers, and with a named condition (mobile
  data cost) that would change the answer.

Now do [`challenge.md`](./challenge.md) — task 1 is the sequence-hole bug you
watched burn 63 numbers.

Then: [Module 06 — The Load-Testing Harness](../06-load-testing-harness/),
which takes this protocol, generates it at 20,000 connections, and breaks the
single worker on purpose.
