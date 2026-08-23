# Module 09 — Redis Streams & Consumer Groups

**Goal:** Fix Module 07's message loss with at-least-once delivery — and
understand precisely why "exactly-once" is a sleight of hand that you are about
to perform. Along the way, confront the fact that `channels_redis` will not do
this for you, and build the Streams-backed fan-out it refuses to be.

⏱️ ~5 hours · **Prerequisites:** Modules 00–08.

---

## What was actually wrong

Module 07's failure was not that Pub/Sub is unreliable. It's that **there was no
record of the message** for a reconnecting subscriber to catch up from.

```
Pub/Sub:  PUBLISH writes bytes to whoever is connected right now. Then forgets.
          A subscriber that was away has no way to ask "what did I miss?"
          because there is no "what" — nothing was stored.
```

That is exactly what `RedisChannelLayer` does under the hood: every
`group_send` becomes a `PUBLISH` (in recent `channels_redis`, a `BLMOVE`-fed
per-process receive queue, but still fire-and-forget with no replayable log).
When you `docker pause` Redis for 1.5 seconds, the messages published during the
pause reach a channel layer that has no subscribers ready, and they evaporate.
Module 07 measured **29 of 200 lost** — roughly 15%.

Retries don't help (the publisher doesn't know it failed). Acknowledgements
don't help (there's nothing to re-send). The fix has to be **storage**.

> **Why `channels_redis` can't just fix this.** The channel layer's contract is
> "deliver to whoever is subscribed *now*." It is a transport, not a log. Adding
> replay would mean giving every channel a durable backlog and every consumer a
> cursor — which is a different data structure (a stream) with a different cost
> model. So Channels stays a transport, and **you build the log yourself.** That
> is the whole Django-specific arc of this module: `channels_redis` gets you to
> Module 07 and no further.

---

## Streams: an append-only log

```bash
XADD room:{7}:stream '*' payload '{"type":"message.new",...}'
"1735689600123-0"
```

That return value is the entry ID: `<milliseconds>-<sequence>`. Monotonically
increasing, assigned by Redis, and — critically — **it is also a cursor**.

```bash
XRANGE room:{7}:stream 1735689600123-0 +      # everything from here on
XLEN   room:{7}:stream
XINFO STREAM room:{7}:stream
```

A stream is a radix tree of "macro nodes," each holding many entries with a
shared field-name dictionary. That's why streams are memory-efficient for
homogeneous entries — the field name `payload` is stored once per node, not once
per entry.

**The difference from Pub/Sub, in one line:** with a stream, a subscriber that
was gone for 30 seconds can ask what it missed. That capability is the entire
module.

---

## Consumer groups

A stream alone gives you replay. A **consumer group** gives you work
distribution and acknowledgement.

```bash
XGROUP CREATE room:{7}:stream fanout '$' MKSTREAM
#                             ^group  ^start from NEW entries only ($) or the
#                                      beginning (0)

XREADGROUP GROUP fanout worker-a COUNT 100 BLOCK 5000 STREAMS room:{7}:stream '>'
#                       ^consumer name                                        ^ '>' =
#                                                          entries never delivered
#                                                          to anyone in this group
```

```
                    stream: [ e1 e2 e3 e4 e5 e6 ]
                                   │
                    group "fanout" │
                    ┌──────────────┼──────────────┐
                    ▼              ▼              ▼
                 worker-a       worker-b       worker-c
                 gets e1,e4     gets e2,e5     gets e3,e6

   Each entry goes to EXACTLY ONE consumer in the group.
   Until XACK'd, it stays in that consumer's Pending Entries List.
```

### The PEL — where the guarantee lives

```bash
XPENDING room:{7}:stream fanout
```
```
1) (integer) 3                    # how many pending
2) "1735689600123-0"              # smallest pending id
3) "1735689600890-0"              # largest
4) 1) 1) "worker-a"
      2) "2"
   2) 1) "worker-b"
      2) "1"
```

The Pending Entries List records, per consumer, every entry that was
**delivered but not acknowledged**. This is the state that makes at-least-once
work:

```
worker-a reads e4 ──▶ e4 enters worker-a's PEL
worker-a's process is SIGKILL'd before it delivers e4
                   ──▶ e4 is STILL in the PEL

worker-b runs XAUTOCLAIM, takes ownership of e4, delivers it, XACKs.
                   ──▶ nothing was lost
```

```bash
XAUTOCLAIM room:{7}:stream fanout worker-b 30000 0 COUNT 100
#                                          ^min-idle-time: only claim entries
#                                           nobody has touched for 30 seconds
```

### Reading your own pending entries

```bash
XREADGROUP GROUP fanout worker-a COUNT 100 STREAMS room:{7}:stream 0
#                                                                  ^ '0' not '>'
```

`0` means "my pending entries," which is what a **restarted** worker reads
first: anything it was mid-delivery when it died. `>` means "new entries nobody
has seen."

A correct consumer loop does both:
```
1. Read '0' — recover my own unfinished work. Loop until empty.
2. Read '>' — process new work (BLOCK, so we don't poll).
3. On a timer, XAUTOCLAIM — recover work from consumers that died.
```

Skipping step 1 or 3 means messages sit in the PEL forever, delivered to nobody.

---

## The Python twist: your "nodes" are processes

The JVM twin runs one consumer group per **node**. On an 8-core box the JVM
holds all its connections in one process, so 3 nodes means 3 groups.

Django does not get that luxury, and Module 01 told you why. **One async worker
process pins one core.** You scale CPU by running one Uvicorn worker per core —
8 processes on an 8-core box — and Module 04 proved the sharpest consequence:
the `InMemoryChannelLayer` does not span those processes. A message that lands
on worker A's socket cannot reach worker B's socket without going through Redis.

So the unit that must "receive every entry" is the **worker process**, not the
machine. Our consumer group is **per worker process**:

```
3 machines × 8 workers = 24 worker processes
                       = 24 consumer groups per room
                       = every entry read and acked 24 times
```

The JVM's O(nodes) read amplification becomes O(nodes × cores) here. That is not
a bug — it is the honest cost of the process-per-core model, and it is why the
Streams fan-out saturates Redis sooner in Python than on the JVM (the pinned
single-node fan-out knee is ~150k out msg/s here versus ~450k on the JVM for the
same reason: per-message Python overhead, times more processes touching Redis).
The challenge measures exactly where this wall is, and Module 13's dedicated
fan-out tier is the escape hatch. For now, **worker process = node** everywhere
below.

---

## At-least-once, and the exactly-once illusion

**At-least-once** is what a consumer group gives you: every entry is delivered
one or more times.

The duplicate case is unavoidable:
```
1. XREADGROUP delivers e5
2. worker delivers e5 (persists it, broadcasts it to local sockets)
3. worker process dies BEFORE XACK
4. XAUTOCLAIM redelivers e5
5. e5 is processed a second time
```

You cannot close this window. Whatever order you choose:
- **Ack before processing** → at-most-once. A crash after the ack loses the
  message.
- **Ack after processing** → at-least-once. A crash before the ack duplicates
  it.

There is no third option, because the ack and the processing are not atomic and
cannot be made atomic across two systems.

### So how does anyone claim exactly-once?

They don't, quite. What they deliver is:

> **at-least-once delivery + idempotent processing = observationally
> exactly-once**

Which is why Module 05 made you put a `client_id` on every message and a unique
constraint `(room_id, client_id)` in Postgres. **You already built the half that
makes this work.** The duplicate arrives; the insert is a no-op; the broadcast
is suppressed; the observable behaviour is indistinguishable from exactly-once.

```python
created = await persist_idempotent(envelope)   # ON CONFLICT DO NOTHING
if not created:
    await redis.xack(stream_key, group, entry_id)   # already stored — just ack
    duplicates.inc()
    return                                           # do NOT broadcast again
```

> **The reframing that matters:** "exactly-once" is not a delivery guarantee you
> buy from a broker. It is a property of your *consumer* that you design in.
> Kafka's "exactly-once semantics" (Module 16) is the same trick with more
> machinery — transactional offsets making the ack and the write atomic *within
> Kafka*. Cross-system — Redis to Postgres to a WebSocket — it's still your
> idempotency key.

---

## The memory cost you must budget for

Pub/Sub cost nothing to store. Streams cost real memory, and it grows.

```
one entry ≈ 100 bytes overhead + your fields
1,000 rooms × 10,000 entries × 600 bytes ≈ 6 GB
```

```bash
XADD room:{7}:stream MAXLEN '~' 10000 '*' payload '...'
#                          ^ APPROXIMATE — this matters enormously
```

The `~` lets Redis trim only whole macro nodes. Exact trimming (`MAXLEN 10000`
without `~`) walks and removes individual entries — O(n) work on the single
thread, on every `XADD`. Module 08 taught you that any O(n) command is a stall;
this is that lesson with a payload.

```bash
XTRIM room:{7}:stream MINID '~' 1735689600000     # trim by TIME, not count
```

`MINID` is usually the better policy for chat: "keep the last 10 minutes" bounds
memory by *rate* rather than by count, which is what you actually care about for
a replay buffer. The challenge sizes it from measured data.

⚠️ **Trimming does not remove PEL entries.** A trimmed entry that was never acked
stays in the PEL as a reference to an ID that no longer exists. `XAUTOCLAIM`
will report it and — in Redis 7 — remove it from the PEL, returning it in the
"deleted" array. Handle that array or your PEL grows forever. (Challenge Task 3.)

---

## Two ways to build fan-out on Streams

This is the design decision of the module.

### Option A — one stream per room, one group, all workers consume

```
room:{7}:stream  ──group "fanout"──▶  worker-a, worker-b, worker-c
```

Each entry goes to **exactly one** worker. That worker must then deliver it to
subscribers on the *other* workers — which needs another hop. **Wrong shape for
fan-out.** Consumer groups distribute work; fan-out needs replication.

### Option B — one stream per room, one group **per worker process**

```
room:{7}:stream ──group "worker-a"──▶ worker-a
                ──group "worker-b"──▶ worker-b
                ──group "worker-c"──▶ worker-c
```

Each worker has its own group, so **every worker receives every entry** —
replication — while each worker still gets per-entry acks, a PEL, and crash
recovery.

✅ **This is what Pulse uses.** The cost is one PEL per worker per room and N
deliveries per entry, which is the same N as the channel layer had — except N is
now processes, not machines (see "The Python twist" above).

### Option C — one stream per *worker*, publisher routes

```
worker-a:inbox  ← publisher XADDs a copy for each worker with a subscriber
```

Fewer streams, but the publisher must know the subscriber topology, and a copy
per worker multiplies storage. Used by systems that need per-worker
backpressure visibility. Noted, not chosen.

---

## How this wires into Channels

`channels_redis` is still installed — you have not thrown it away. But the
message hot path no longer flows through `group_send`. Instead:

```
 inbound (a client SEND)                    the Streams fan-out
 ─────────────────────────                  ────────────────────────────────
 ChatConsumer.receive_json()                StreamConsumer task (1 per worker)
   → allocate seq (Redis INCR)                loop:
   → XADD room:{id}:stream                      recover own pending  (XREADGROUP 0)
   → ack the sender                             read new             (XREADGROUP >)
                                                claim abandoned      (XAUTOCLAIM)
                                              for each entry:
                                                persist idempotent (Postgres)
 LocalRegistry                                 for sub in local[room]:
   room → {ChatConsumer, ...}    ◀──────────────  await sub.send_json(envelope)
   (populated in connect/disconnect
    within THIS process only)
```

The `LocalRegistry` is the piece that replaces the channel layer's group
membership. It is a plain in-process dict — it only ever needs to reach sockets
**on this worker**, because the cross-process hop is now the stream. This is the
`InMemoryChannelLayer` reduced to its one honest job: local delivery. Module 04
proved it can't do more than that; here that limitation is exactly what we want.

---

## What Streams still don't fix

Be precise about the remaining gaps, because Modules 10 and 13 exist for them:

| Gap | Status after this module | Fixed in |
|-----|-------------------------|----------|
| Message lost on Redis reconnect | ✅ **fixed** — replay from the PEL/stream | — |
| Worker crash mid-delivery | ✅ **fixed** — `XAUTOCLAIM` | — |
| Duplicate delivery | ✅ **handled** — idempotent insert | (Module 05) |
| **Client** disconnects and misses messages | ❌ still broken | **Module 10** |
| Client can't tell it missed something | ❌ still broken | **Module 10** |
| Persisted to Postgres but never published | ❌ still broken | **Module 13** |
| Redis restarts and loses the stream | ⚠️ partial | Module 13 (outbox replay) |

Note the fourth row especially. Streams protect the message *between worker
processes*. The last hop — worker to browser — is still Pub/Sub-grade, because a
WebSocket write is fire-and-forget. That's Module 10's whole subject.

---

## When Streams are the wrong choice

Don't over-apply this:

| Traffic | Use |
|---------|-----|
| Chat messages | **Streams** — a loss is a permanent hole |
| Room membership changes | **Streams** — a missed removal is a security bug |
| Typing indicators | **Pub/Sub** (`group_send`) — superseded in 3 s, storage is pure waste |
| Presence heartbeats | **Pub/Sub** — TTL state, self-healing (Module 11) |
| Cursor positions | **Pub/Sub** |

Putting typing indicators in a stream would multiply your Redis memory by
roughly 10× to protect data whose value expires in three seconds. Pulse runs
both — the durable Streams path *and* the channel layer for ephemera — and the
routing decision is made per message type. Module 11 builds the ephemeral side.

---

## Why not just use Kafka here?

You could. Kafka gives you the same replayable log with better retention
economics and real partitioning. Two reasons we don't, yet:

1. **You already run Redis.** Adding Kafka is a second stateful system to
   operate, monitor, and keep highly available — a large fixed cost for a
   feature Redis Streams already covers at this scale.
2. **Latency.** Redis Streams live in memory; a local `XADD`/`XREADGROUP` round
   trip is sub-millisecond. Kafka's durability comes from `fsync` and replication
   that add milliseconds you don't need for a 10-minute replay buffer.

Module 16 builds the Kafka version head-to-head and shows exactly where the
answer flips (retention measured in days, throughput past what one Redis thread
serves, or you need the log as a system-of-record, not a buffer).

---

## What's next

The lab converts the fan-out to Streams, re-runs Module 07's loss test (and
loses nothing), kills a worker mid-delivery to watch `XAUTOCLAIM` recover,
proves a duplicate is absorbed by the `client_id` constraint, measures the
memory and latency cost, and builds the PEL monitoring you'll need in Module 20.

See you in [`lab.md`](./lab.md).
