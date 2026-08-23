# Module 09 — Redis Streams & Consumer Groups

**Goal:** Fix Module 07's message loss with at-least-once delivery — and
understand precisely why "exactly-once" is a sleight of hand that you are about
to perform.

⏱️ ~5 hours · **Prerequisites:** Modules 00–08.

---

## What was actually wrong

Module 07's failure was not that Pub/Sub is unreliable. It's that **there was no
record of the message** for a reconnecting subscriber to catch up from.

```
Pub/Sub:  PUBLISH writes bytes to whoever is connected. Then forgets.
          A subscriber that was away has no way to ask "what did I miss?"
          because there is no "what" — nothing was stored.
```

Retries don't help (the publisher doesn't know it failed). Acknowledgements don't
help (there's nothing to re-send). The fix has to be **storage**.

---

## Streams: an append-only log

```bash
XADD room:{7}:stream '*' body 'hello' sender 'alice'
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
homogeneous entries — the field names `body` and `sender` are stored once per
node, not once per entry.

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

XREADGROUP GROUP fanout node-a COUNT 100 BLOCK 5000 STREAMS room:{7}:stream '>'
#                       ^consumer name                                      ^ '>' = 
#                                                          entries never delivered
#                                                          to anyone in this group
```

```
                    stream: [ e1 e2 e3 e4 e5 e6 ]
                                   │
                    group "fanout" │
                    ┌──────────────┼──────────────┐
                    ▼              ▼              ▼
                 node-a         node-b         node-c
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
4) 1) 1) "node-a"
      2) "2"
   2) 1) "node-b"
      2) "1"
```

The Pending Entries List records, per consumer, every entry that was **delivered
but not acknowledged**. This is the state that makes at-least-once work:

```
node-a reads e4 ──▶ e4 enters node-a's PEL
node-a crashes before processing e4
                 ──▶ e4 is STILL in the PEL

node-b runs XAUTOCLAIM, takes ownership of e4, processes it, XACKs.
                 ──▶ nothing was lost
```

```bash
XAUTOCLAIM room:{7}:stream fanout node-b 30000 0 COUNT 100
#                                        ^min-idle-time: only claim entries
#                                         nobody has touched for 30 seconds
```

### Reading your own pending entries

```bash
XREADGROUP GROUP fanout node-a COUNT 100 STREAMS room:{7}:stream 0
#                                                                ^ '0' not '>'
```

`0` means "my pending entries," which is what a **restarted** consumer reads
first: anything it was mid-processing when it died. `>` means "new entries
nobody has seen."

A correct consumer loop does both:
```
1. Read '0' — recover my own unfinished work. Loop until empty.
2. Read '>' — process new work.
3. On a timer, XAUTOCLAIM — recover work from consumers that died.
```

Skipping step 1 or 3 means messages sit in the PEL forever, delivered to nobody.

---

## At-least-once, and the exactly-once illusion

**At-least-once** is what a consumer group gives you: every entry is delivered
one or more times.

The duplicate case is unavoidable:
```
1. XREADGROUP delivers e5
2. consumer processes e5 (broadcasts it, writes it)
3. consumer crashes BEFORE XACK
4. XAUTOCLAIM redelivers e5
5. e5 is processed a second time
```

You cannot close this window. Whatever order you choose:
- **Ack before processing** → at-most-once. A crash after the ack loses the
  message.
- **Ack after processing** → at-least-once. A crash before the ack duplicates it.

There is no third option, because the ack and the processing are not atomic and
cannot be made atomic across two systems.

### So how does anyone claim exactly-once?

They don't, quite. What they deliver is:

> **at-least-once delivery + idempotent processing = observationally
> exactly-once**

Which is why Module 05 made you put a `clientId` on every message and a unique
index in Postgres. **You already built the half that makes this work.** The
duplicate arrives; the insert is a no-op; the broadcast is suppressed; the
observable behaviour is indistinguishable from exactly-once.

```java
var result = repository.insertIdempotent(...);
if (result.wasRetry()) {
    redis.acknowledge(streamKey, group, entryId);   // already done — just ack
    return;
}
```

> **The reframing that matters:** "exactly-once" is not a delivery guarantee you
> buy from a broker. It is a property of your *consumer* that you design in.
> Kafka's "exactly-once semantics" (Module 16) is the same trick with more
> machinery — transactional offsets making the ack and the write atomic *within
> Kafka*. Cross-system, it's still your idempotency key.

---

## The memory cost you must budget for

Pub/Sub cost nothing to store. Streams cost real memory, and it grows.

```
one entry ≈ 100 bytes overhead + your fields
1,000 rooms × 10,000 entries × 600 bytes = 6 GB
```

```bash
XADD room:{7}:stream MAXLEN '~' 10000 '*' body 'hi'
#                            ^ APPROXIMATE — this matters enormously
```

The `~` lets Redis trim only whole macro nodes. Exact trimming (`MAXLEN 10000`
without `~`) walks and removes individual entries — O(n) work on the single
thread, on every `XADD`.

```bash
XTRIM room:{7}:stream MINID '~' 1735689600000     # trim by TIME, not count
```

`MINID` is usually the better policy for chat: "keep the last 10 minutes"
bounds memory by *rate* rather than by count, which is what you actually care
about for a replay buffer.

⚠️ **Trimming does not remove PEL entries.** A trimmed entry that was never
acked stays in the PEL as a reference to an ID that no longer exists.
`XAUTOCLAIM` will report it and — in Redis 7 — remove it from the PEL, returning
it in the "deleted" array. Handle that array or your PEL grows forever.

---

## Two ways to build fan-out on Streams

This is the design decision of the module.

### Option A — one stream per room, one group, all instances consume

```
room:{7}:stream  ──group "fanout"──▶  node-a, node-b, node-c
```

Each entry goes to **exactly one** node. That node must then deliver it to
subscribers on the *other* nodes — which needs another hop. **Wrong shape for
fan-out.** Consumer groups distribute work; fan-out needs replication.

### Option B — one stream per room, one group **per node**

```
room:{7}:stream ──group "node-a"──▶ node-a
                ──group "node-b"──▶ node-b
                ──group "node-c"──▶ node-c
```

Each node has its own group, so **every node receives every entry** — replication
— while each node still gets per-entry acks, a PEL, and crash recovery.

✅ **This is what Pulse uses.** The cost is one PEL per node per room and N
deliveries per entry, which is the same N as Pub/Sub had.

### Option C — one stream per *node*, publisher routes

```
node-a:inbox  ← publisher XADDs a copy for each node with a subscriber
```

Fewer streams, but the publisher must know the subscriber topology, and a copy
per node multiplies storage. Used by systems that need per-node backpressure
visibility. Noted, not chosen.

---

## What Streams still don't fix

Be precise about the remaining gaps, because Modules 10 and 13 exist for them:

| Gap | Status after this module | Fixed in |
|-----|-------------------------|----------|
| Message lost on Redis reconnect | ✅ **fixed** — replay from the PEL/stream | — |
| Consumer crash mid-processing | ✅ **fixed** — `XAUTOCLAIM` | — |
| Duplicate delivery | ✅ **handled** — idempotent insert | (Module 05) |
| **Client** disconnects and misses messages | ❌ still broken | **Module 10** |
| Client can't tell it missed something | ❌ still broken | **Module 10** |
| Persisted to Postgres but never published | ❌ still broken | **Module 13** |
| Redis restarts and loses the stream | ⚠️ partial | Module 13 (outbox replay) |

Note the fourth row especially. Streams protect the message *between servers*.
The last hop — server to browser — is still Pub/Sub-grade, because a WebSocket
write is fire-and-forget. That's Module 10's whole subject.

---

## When Streams are the wrong choice

Don't over-apply this:

| Traffic | Use |
|---------|-----|
| Chat messages | **Streams** — a loss is a permanent hole |
| Room membership changes | **Streams** — a missed removal is a security bug |
| Typing indicators | **Pub/Sub** — superseded in 3 s, storage is pure waste |
| Presence heartbeats | **Pub/Sub** — TTL state, self-healing |
| Cursor positions | **Pub/Sub** |

Putting typing indicators in a stream would multiply your Redis memory by roughly
10× to protect data whose value expires in three seconds. Pulse runs both, and
the routing decision is made per message type.

---

## What's next

The lab converts the fan-out to Streams, re-runs Module 07's loss test (and
loses nothing), kills a consumer mid-processing to watch `XAUTOCLAIM` recover,
measures the memory and latency cost, and builds the PEL monitoring you'll need
in Module 20.

See you in [`lab.md`](./lab.md).
