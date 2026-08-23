# Module 05 — Protocol & Domain Design

**Goal:** Design the message envelope, the identity scheme, and the
acknowledgement ladder that every later module depends on — because protocol
mistakes are the ones you cannot refactor away once clients are in the wild.

⏱️ ~5 hours · **Prerequisites:** Modules 00–04. You need the working
`RoomConsumer` from [Module 04](../04-channels-chat-single-node/).

> **This is the Python twin of the JVM course's
> [`05-protocol-and-domain-design`](../../spring-boot-chat-course/05-protocol-and-domain-design/),
> and it has more work to do.** The JVM twin adopts STOMP, which already answers
> "how do I subscribe," "how do I ack," "how do I send an error that isn't a
> disconnect." Django Channels ships no subprotocol. **The envelope you design
> here IS Pulse's protocol** — there is nothing underneath it. That is a cost
> (you will re-derive things STOMP wrote down in 1998) and an opportunity (there
> is no black box between you and the wire).

---

## Why this module comes before scaling

You can rewrite your fan-out layer on a Tuesday. You cannot rewrite your wire
protocol, because installed clients speak the old one and will keep speaking it
for years — the Android app you shipped in March, the browser tab someone has
had open since Thursday, the integration a customer built against your beta.

Three decisions made here determine whether Modules 09–17 are straightforward or
impossible:

1. **Does the client generate an ID before sending?** If not, you cannot dedup,
   which means you cannot safely retry, which means you cannot have at-least-once
   delivery — and Module 09's entire Streams design collapses.
2. **Is there a per-room sequence number?** If not, a client can never *know* it
   missed a message; it can only notice, eventually, by comparing with a
   colleague. Module 10's resume has nowhere to stand.
3. **Is there a version field?** If not, your first protocol change is a flag day.

Get these three right and the rest of the course is mechanical. Get them wrong
and you will discover it in Module 10, when it is expensive.

---

## The envelope

Every frame in both directions shares one shape:

```json
{
  "v":    1,
  "type": "message.new",
  "room": "room.7",
  "ts":   1735689600123,
  "data": { "id": 7241938, "client_id": "01JQ8Z4K7M…", "seq": 48213,
            "sender": "alice", "body": "ok" }
}
```

| Field | Why it exists |
|-------|--------------|
| `v` | Protocol version. Costs one byte; buys the ability to change anything later. |
| `type` | Namespaced verb (`message.create`, `presence.update`, `typing.start`). One socket carries every kind of traffic; the client routes on a single `switch`. |
| `room` | Routing key. Redundant with the URL path, and deliberately so — see below. |
| `ts` | **Server** time at emission, epoch milliseconds. Never the client's clock. |
| `data` | Type-specific payload. Everything type-dependent lives here and nowhere else. |

### Why `room` is duplicated

The socket already knows its room — it is in the URL (`/ws/room/7/`) and in
`self.group`. Repeating it in every frame costs about 14 bytes. Worth it because:

- **Transport independence.** In Module 09 these envelopes travel through Redis
  Streams, which have no URL. In Module 13 they sit in a Postgres outbox table.
  In Module 16 they are Kafka records. A self-describing payload survives all
  three; a payload that needs its transport's metadata does not.
- **Debuggability.** An envelope in a log line, a `XRANGE` dump, or a Kafka
  console consumer is interpretable on its own.
- **Client-side multiplexing.** Module 17's client runs **one** socket across all
  rooms (and across browser tabs, via a `SharedWorker`). Without `room` in the
  payload, the client would have to thread routing context through every
  callback.

> **The principle:** make payloads self-describing. Any field you can only
> reconstruct from transport metadata becomes a bug the moment you change
> transports — and you change transports **three times** in this course.

### Wire types vs channel-layer event types

Channels dispatches `group_send({"type": "chat.message", ...})` to a method named
`chat_message` — dots become underscores. It is tempting to reuse the wire type
so `message.new` dispatches to `message_new` and the consumer just forwards the
dict.

**Don't.** They are two namespaces with two audiences and two rates of change:

```
   client  ──"message.create"──▶  consumer  ──"chat.message"──▶  channel layer
                                                                       │
   client  ◀──"message.new"────  consumer  ◀──"chat.message"──────────┘
```

| | Wire type | Channel-layer event type |
|---|-----------|--------------------------|
| Audience | Clients you cannot redeploy | Your own consumers |
| Changing it | A protocol break, needs `v` | A refactor, needs a deploy |
| Namespace | `message.*`, `presence.*`, `typing.*`, `read.*`, `control`, `error` | `chat.*` |
| Shape | The envelope | Whatever is convenient |

The two are not one-to-one: one `chat.message` event produces one `message.new`
frame **per recipient**, and each recipient's frame may differ (their own
messages carry `client_id` for reconciliation; other people's do not need it).
Collapsing the namespaces means an internal rename becomes a wire break.

---

## The three-ID rule

Every message has **three** identities. Conflating any two of them is the most
common protocol bug in chat.

```json
{ "client_id": "01JQ8Z4K7M8YQ2VBXR3N5TDGWH",   ← the CLIENT, before the first send
  "id":        7241938472948572160,            ← the SERVER, at persist time
  "seq":       48213 }                         ← the SERVER, per room, monotonic
```

| ID | Generated by | Purpose | Lifetime |
|----|-------------|---------|----------|
| `client_id` | Client, before the first send attempt | **Idempotency.** The server recognizes a retry and returns the original result instead of creating a duplicate. | Until the dedup window expires |
| `id` | Server, at persist time | Canonical identity for edits, deletes, replies, reactions | Forever |
| `seq` | Server, per room, monotonic, gapless | **Gap detection and resume.** | Forever |

### Why the client must generate an ID

```
Client sends ──▶ Server persists ──▶ ACK ──✗ (the network dies HERE)
Client times out, retries ──▶ Server persists AGAIN ──▶ duplicate
```

The network failed *after* the server did the work. The client cannot
distinguish that from "the server never got it." Its only options are:

- **Retry** — and risk a duplicate, unless the server can recognize the retry.
- **Don't retry** — and risk losing a message the user believes they sent.

Both are bad. `client_id` makes retry safe:

```sql
INSERT INTO chat_message (room_id, client_id, sender_id, body, seq, ...)
VALUES (...)
ON CONFLICT (room_id, client_id) DO NOTHING
RETURNING id, seq;
```

No rows returned means it was a retry — look up and return the original result.
**The retry is now free**, and the client may retry as aggressively as it likes.

> **This is what "exactly-once" actually means in practice.** Nobody achieves
> exactly-once *delivery*; the network forbids it. What real systems deliver is
> at-least-once delivery plus **idempotent processing**, which is
> observationally identical and is achievable. `client_id` is the whole trick,
> and Module 09 leans on it entirely when a Redis Streams consumer redelivers.

**Use a time-sortable ID — ULID or UUIDv7 — not UUIDv4.** Random v4 keys scatter
across a B-tree, so the dedup index's hot pages are the whole index. Time-ordered
keys keep inserts on the rightmost leaf and let you range-delete expired entries
instead of scanning. Module 12 measures the difference at 50 million rows; here,
just know the reason.

Python note: `uuid.uuid7()` does not exist before 3.14, and the point of the ID
is small enough that Pulse ships a 15-line ULID generator (lab Part A) rather
than a dependency — the same choice Module 12 makes for Snowflake in
[`code/snowflake.py`](../12-postgres-message-store/code/snowflake.py).

### Why sequence numbers, and why per-room

Message IDs are globally unique but say nothing about **completeness**. A client
holding `7241938472948572160` and `7241938472948572400` has no idea whether
anything sits between them.

```
seq: 48211  48212  48213  ██████  48215
                            ↑
              the client KNOWS it is missing 48214
```

Per-room, not global, because:

- A global sequence is a single point of contention — one counter every message
  in the system must serialize on. Module 14 kills it outright when you shard.
- A client only cares about the rooms it is in. A global gap is meaningless to
  it, and would fire constantly.
- Per-room sequences let each room's stream be resumed independently, which is
  what Module 10's `resume` frame does and what Module 17's client needs when it
  reconnects with twelve rooms open.

The `seq` **is** the resume cursor. It must be **gapless**, which is a stronger
property than "monotonic" and the reason the lab's first implementation is wrong
and the challenge makes you fix it.

---

## Serialization, and where your CPU goes

This is the section the JVM twin does not need, and it is worth five minutes.

Module 04 measured a 200-member fan-out at 34% of one core, and named the three
costs: a `deepcopy` per recipient, a **JSON encode per recipient**, and a socket
write per recipient. Module 06 finds the knee at **≈150,000 outbound msg/s** —
about a third of the JVM twin's ≈450,000 — and the encoder is a real part of
that gap.

Measured on the reference machine, encoding one Pulse envelope (≈167 bytes):

| Encoder | µs/encode | Envelopes/s on one core | Notes |
|---------|-----------|------------------------|-------|
| `json.dumps` (stdlib) | 3.9 | 256,000 | The default. Pure-ish C, but builds a `str` then encodes UTF-8. |
| `json.dumps` + `separators=(",",":")` | 3.4 | 294,000 | Free. Also 8% smaller on the wire. |
| `orjson.dumps` | 0.8 | **1,250,000** | Returns `bytes` directly. Handles `datetime`/`UUID` natively. |
| `msgpack.packb` | 1.1 | 909,000 | 41% smaller, and **unreadable in DevTools**. |

Two conclusions, and the second one matters more:

1. **The encoder is worth changing and the format is not.** `orjson` is a
   drop-in that quadruples encode throughput; switching to MessagePack costs you
   every debugging tool you have and buys less than `orjson` does. Module 15
   benchmarks `orjson` in the hot path.
2. **Encoding is not the bottleneck anyway.** At 150,000 msg/s, `json.dumps` is
   ~0.6 of a core-second per second — real, but the `deepcopy`, the ASGI
   `send()` plumbing, and the socket writes together cost more. **Measure before
   you optimize the part that is easy to see.**

### Field naming: verbose vs terse

```json
{"v":1,"type":"message.new","room":"room.7","ts":1735689600123,"data":{"id":7241938,"client_id":"01JQ8Z4K7M8YQ2VBXR3N5TDGWH","seq":48213,"sender":"alice","body":"ok"}}
```
That is **167 bytes for a 2-byte message.**

| Approach | Saving | Cost |
|----------|--------|------|
| Verbose JSON | — | Readable in every tool ever built |
| Short keys (`{"v":1,"t":"m.n","d":{...}}`) | ~28% | Unreadable; needs a mapping doc nobody updates |
| MessagePack / CBOR | ~41% | Binary; DevTools shows garbage |
| Protobuf / FlatBuffers | ~60% | Schema registry, codegen, versioning discipline |

**Pulse keeps verbose JSON**, and the reasoning is the kind of judgement this
course is about: at Pulse's target scale, bandwidth is not the constraint
(Module 04 showed CPU and the event loop are), and readable frames in DevTools
are worth real money in debugging time. Revisit if **mobile data cost becomes a
product concern** — which is exactly when Discord and Slack moved to binary
encodings, and not before.

---

## The acknowledgement ladder

"Delivered" is not one thing. Chat UIs show four distinct states and each needs a
different signal:

```
   ┌─────────┐  send   ┌──────────┐  server   ┌───────────┐  recipient  ┌──────┐
   │ pending │────────▶│  queued  │──────────▶│ delivered │────────────▶│ read │
   │  (grey) │         │   (✓)    │           │   (✓✓)    │             │(blue)│
   └─────────┘         └──────────┘           └───────────┘             └──────┘
   optimistic          message.ack             per-recipient            read.update
   local render        (persisted, has seq)    delivery receipt         (debounced)
```

| State | Signal | Who sends it | Cost |
|-------|--------|-------------|------|
| **pending** | none — render optimistically | the client itself | free |
| **queued** | `message.ack` with `id` + `seq` | server → sender | 1 frame per message |
| **delivered** | delivery receipt | each recipient → server → sender | **N frames per message** |
| **read** | `read.update` | recipient (debounced) → server → sender | ~1 frame per read burst |

⚠️ **The "delivered" row is a scaling trap that inverts your fan-out.** A message
to 500 people produces 500 receipts aimed at **one** connection — a 500×
amplification pointed at a single socket, and that socket belongs to a phone.

How real systems handle it:

- **1:1 DMs** — full delivery receipts. N=1, so it is free.
- **Small groups** — receipts, often aggregated ("3 of 5").
- **Large rooms** — **no delivery receipts at all.** Slack does not tell you who
  received your `#general` message. That is an architecture decision, not an
  oversight.

**Pulse:** `message.ack` always; delivery receipts only for rooms under a
configurable threshold (default 16 members); read receipts always, but debounced
client-side to at most one per 2 seconds per room. Module 10 implements the read
side; Module 11 does the same arithmetic for typing indicators and finds the same
answer.

### Optimistic send and reconciliation

```
1. User hits Enter.
2. Client generates client_id, renders the bubble immediately, state=pending.
3. Client sends message.create {client_id, body}.
4. Server ACKs: message.ack {client_id, id, seq, ts}.
5. Client MATCHES ON client_id and upgrades the existing bubble to state=queued.
6. The broadcast arrives: message.new {..., client_id, ...}. The client sees
   client_id is already rendered and does NOT add a second bubble.
```

**Step 6 is why `client_id` must be echoed in the broadcast, not just in the
ack.** Without it the sender sees their own message twice: once optimistically,
once from the fan-out. Every chat client has shipped this bug at least once.

And note the ordering hazard hiding in step 5: the ack and the broadcast are two
independent frames and **the broadcast can arrive first**. On the in-memory layer
the consumer's own `group_send` may complete before the `send_json` of the ack;
over Redis (Module 07) the race is wider. The client must handle either order,
which means reconciliation is keyed on `client_id`, not on arrival sequence.

---

## Ordering: what you can and cannot promise

**You can promise:** messages within one room are delivered to every client in
`seq` order, and a client can detect a gap.

**You cannot promise:** that `seq` order matches the order users pressed Enter.
Two people in different cities pressing Enter "at the same time" have no
meaningful global order — the server assigns one and it is arbitrary. This is not
a limitation to fix; it is special relativity with worse latency.

Practical consequences, all of which the Module 17 client obeys:

- **Sort the UI by `seq`, never by a client timestamp.** Client clocks are wrong,
  sometimes by hours, sometimes deliberately.
- **Display the server's `ts`.**
- When an optimistic message receives a `seq` *lower* than one already rendered,
  **the bubble must move**. Append-only clients show messages out of order after
  a slow send. Design for it.
- Threads and replies reference a parent `id`, which sidesteps ordering entirely
  for the cases users care most about.

---

## Schema evolution

The rules that keep a `v:1` client working forever:

| Change | Safe? | Why |
|--------|-------|-----|
| Add an optional field | ✅ | Old clients ignore unknown fields — **if you told them to** |
| Add a new `type` | ✅ | Old clients ignore unknown types — **if you told them to** |
| Make an optional field required | ❌ | Old clients don't send it |
| Remove a field | ❌ | Old clients read it |
| Change a field's type | ❌ | Silent corruption; the worst kind |
| Rename a field | ❌ | That is a remove plus an add |
| Change the meaning of a value | ❌❌ | The most dangerous, because *nothing detects it* |

Both "if you told them to" clauses are load-bearing, and in Python they are one
line each:

```python
# Server side: parse into a shape that TOLERATES unknown keys.
@dataclass(slots=True)
class Envelope:
    v: int
    type: str
    room: str
    ts: int
    data: dict                       # NOT a dataclass. Deliberately.

    @classmethod
    def parse(cls, raw: dict) -> "Envelope":
        return cls(v=raw.get("v", 1), type=raw["type"], room=raw.get("room", ""),
                   ts=raw.get("ts", 0), data=raw.get("data") or {})
        # ^ note what is missing: any error for extra keys.
```
```js
// Client side: the `default` case IS the compatibility guarantee.
switch (env.type) {
  case "message.new":     return renderMessage(env.data);
  case "presence.update": return renderPresence(env.data);
  default:                return;        // forward compatibility, on purpose
}
```

> **Why `data` is a plain dict and not a typed model:** a strict schema on the
> *inbound* server path is good (lab Part B builds one, and Module 04's challenge
> argued for an allowlist). A strict schema on the *outbound-parsed-by-old-code*
> path is a liability — the whole point is to survive fields you have never heard
> of. Pydantic's `model_config = {"extra": "ignore"}` and a dataclass with a
> catch-all dict express the same idea; use one deliberately.

**When you genuinely must break compatibility:** bump `v`, support both for a
deprecation window, negotiate at connect time (`Sec-WebSocket-Protocol: pulse.v1`
— which Module 04 already wired), and **emit a metric tagged by client version**
so you can measure how many old clients remain before deciding to drop support.
Deprecation without telemetry is guessing.

---

## The Pulse protocol, v1

```
message.create   client→server   { client_id, body, reply_to? }
message.ack      server→client   { client_id, id, seq, ts }
message.new      server→client   { id, client_id, seq, sender, body, ts, reply_to? }
message.edit     client→server   { id, body }
message.delete   client→server   { id }

typing.start     client→server   { }                     (rate limited, at-most-once)
typing.update    server→client   { users: [...] }        (aggregated, debounced)

read.upto        client→server   { seq }                 (debounced 2s client-side)
read.update      server→client   { user, seq }

resume           client→server   { from_seq }            (Module 10)
resume.batch     server→client   { messages: [...], has_more, from_seq, to_seq }

presence.update  server→client   { user, state, online: [...] }
ping / pong      both ways       { ts }                  (10s heartbeat, Module 03)

control          server→client   { action, reason?, retry_after_ms? }
error            server→client   { code, message, client_id? }
```

Three things to notice:

- **`typing.*` is deliberately at-most-once and aggregated.** It is the traffic
  with the highest volume and the lowest value. Module 09 sends it over Pub/Sub
  while messages go over Streams — *different semantics for different traffic*
  is a design decision, not an inconsistency.
- **`control` exists from day one.** It is how the server says "I am draining,
  reconnect in 3,400 ms with jitter" (Module 18) or "your token expired, re-auth"
  (Module 21). Retrofitting a control channel later is painful, and it is
  free now.
- **`error` is a frame, not a disconnect.** Closing the socket to report a
  4-character message body is how you turn a validation error into a reconnect
  storm. Reserve close codes for conditions the connection cannot continue past
  (`4401` unauthenticated, `4403` unauthorized, `4008` too slow, `4009` frame too
  large).

The normative reference lives in
[`code/pulse-protocol-v1.md`](./code/pulse-protocol-v1.md), which every later
module links to.

---

## The domain model behind it

The protocol implies a schema. Three pieces:

```
┌────────────────────┐        ┌─────────────────────────────────────┐
│ Room               │        │ Message                             │
│  slug   (unique)   │◀──────┤  room     FK                        │
│  key = "room.<s>"  │        │  sender   FK                        │
└────────────────────┘        │  client_id  ← idempotency           │
          ▲                   │  seq        ← gapless, per room     │
          │                   │  body, reply_to, created_at         │
┌─────────┴──────────┐        │  UNIQUE (room, client_id)  ◀────────┼── the guarantee
│ RoomSequence       │        │  UNIQUE (room, seq)                 │
│  room  (1:1)       │        └─────────────────────────────────────┘
│  last_seq          │
└────────────────────┘
```

- **`UNIQUE (room_id, client_id)`** is not an optimization; it is the
  idempotency guarantee, enforced by the database rather than by application
  logic that races. Module 12 measures its cost honestly: it reduces write
  throughput by **21%** (224k → 177k rows/s) and it is worth every point.
- **`RoomSequence.last_seq`** is a per-room counter. Allocating from it under
  concurrency is where the interesting bug lives, and the challenge makes you
  find it: allocate *before* the insert and a lost race burns a sequence number,
  leaving a permanent hole that every client reports as a missing message
  forever.
- **The whole allocate-and-insert must be one transaction**, and
  `transaction.atomic()` is **sync-only** in Django 5.1. So the idempotent send
  is a single synchronous function called across the bridge with
  `@database_sync_to_async` — not a chain of `await`s. This is the concrete case
  the Module 02 README warned about, and the lab writes it.

---

## What's next

The lab implements a ULID generator, the envelope codec with strict inbound
parsing and tolerant outbound parsing, the idempotent-insert-with-sequence
transaction, the full ack ladder, optimistic send in the browser client, gap
detection, and an `error` frame path — then proves idempotency under 64
concurrent retries and proves gap detection catches a deliberately dropped
message.

See you in [`lab.md`](./lab.md).
