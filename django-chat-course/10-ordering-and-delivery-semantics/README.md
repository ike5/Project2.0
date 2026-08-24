# Module 10 — Ordering & Delivery Semantics

**Goal:** Close the last hop — server to browser — and be able to state, in one
paragraph with its caveats, exactly what Pulse guarantees. Along the way, discover
that the architecture you built in Module 09 quietly broke the *gapless* promise
Module 05 made, and fix it with one Lua script.

⏱️ ~5 hours · **Prerequisites:** Modules 00–09.

---

## Where the guarantee stops

Module 09 made messages durable **between worker processes**. Look at what it did
*not* touch:

```
  Postgres ──✅──▶ Redis Stream ──✅──▶ worker process ──❓──▶ browser
  durable          at-least-once        registry fan-out      fire and forget
                   (PEL + XAUTOCLAIM)                          no ack, no replay
```

The last arrow is `await consumer.send_json(envelope)`. In Channels that becomes
an ASGI `websocket.send` — which resolves as soon as the bytes are handed to the
transport. If the recipient's phone is entering a tunnel:

1. The bytes sit in a kernel send buffer.
2. TCP retransmits for ~15 minutes and gives up.
3. Uvicorn eventually surfaces a close to your consumer.
4. **The message is gone**, and the stream entry was `XACK`ed long ago.

So the chain that was carefully made durable for its first three hops is
fire-and-forget on the hop the user actually experiences. That is Module 10's
subject, and it is the last structural hole in the delivery path.

---

## Three delivery semantics, and the one you actually ship

You have now built enough machinery to state all three precisely. Memorize this
table; it is the vocabulary for every design review you will ever sit in.

| Semantic | Implementation | Loses | Duplicates | Where Pulse uses it |
|----------|----------------|-------|------------|---------------------|
| **At-most-once** | Acknowledge *before* processing. Or: publish and forget. | Yes, on any crash after the ack | Never | Typing, presence, read receipts, cursor positions |
| **At-least-once** | Acknowledge *after* processing. Retry until acked. | Never | Yes, on any crash between processing and the ack | Chat messages, membership changes |
| **"Exactly-once"** | At-least-once **+ an idempotency key** the consumer enforces | Never | Yes on the wire, never *observably* | Chat messages, once `(room, client_id)` is enforced |

The third row is not a fourth mechanism. It is the second row plus a unique
constraint. Module 09 said this; here is the sharper form:

> **Exactly-once is not a property of a delivery system. It is a property of a
> consumer.** No broker can give it to you across a system boundary, because the
> acknowledgement and the side effect live in different systems and cannot be made
> atomic. What you can build is a consumer for which a redelivery is a no-op — and
> then the observable behaviour is indistinguishable from exactly-once.

The word "observably" is doing real work. On the wire, duplicates absolutely
happen. The lab counts them. What the *user* sees is one message, because
`INSERT … ON CONFLICT (room_id, client_id) DO NOTHING` returns zero rows the
second time and the broadcast is suppressed.

### The window you cannot close

```
1. XREADGROUP delivers entry e5 to worker-a
2. worker-a persists e5 and sends it to 40 local sockets
3. worker-a is SIGKILLed here                    ← the window
4. XAUTOCLAIM hands e5 to worker-b after 30 s
5. worker-b persists e5   → ON CONFLICT, zero rows
6. worker-b does NOT re-broadcast
```

Move the `XACK` to step 2 and the window becomes a *loss* window instead of a
*duplicate* window. There is no ordering of two operations in two systems that
makes both windows vanish. Pick which failure you prefer, then engineer around it.
Chat prefers duplicates, because a duplicate is removable and a hole is not.

---

## Per-room ordering, and the price of global ordering

**What Pulse guarantees:** every client of a room observes that room's messages in
the same `seq` order, and can detect any gap in it.

**What Pulse does not guarantee:** that `seq` order across two different rooms
reflects wall-clock order, or that it matches the order humans pressed Enter.

That second sentence bothers people, so here is the defence.

### Global ordering costs head-of-line blocking

A single global sequencer means a single counter, which means every send in the
system serializes on one key. That is survivable — Redis is single-threaded
anyway. The killer is on the **delivery** side: to deliver in global order, a
consumer must not deliver message *n+1* until it has delivered *n*. One slow room
therefore stalls every room.

The lab measures exactly this. Inject a single room whose persistence path takes
2 seconds per message and watch what happens to *other* rooms:

| Ordering model | p99 in the slow room | p99 in the other 99 rooms |
|----------------|---------------------|---------------------------|
| Per-room `seq` | 2,140 ms | **138 ms** (unchanged) |
| Global `seq` | 2,140 ms | **2,190 ms** |

Global ordering converts one sick room into a sick system. It also destroys the
shard boundary — Module 14 shards by room precisely because rooms are independent,
and a global counter makes them dependent. And it wrecks the resume query: a
global cursor cannot use the `(room_id, seq)` index Module 12 builds the store
around.

**The rule:** order within the smallest unit anyone can perceive, and no larger.
For chat, that unit is a room. Nobody has ever noticed that a message in
`#general` and a message in `#random` were interleaved wrongly, because nobody can
observe both at the same instant with enough precision to care.

### There is no ground truth to be faithful to

Two people in different cities press Enter "simultaneously." There is no fact of
the matter about which came first — special relativity is not the reason, but the
absence of a shared clock is. The server picks one. That is not an approximation
of a correct answer; it *is* the answer, because the server's choice is the only
order everyone can agree on.

Consequences, all of which the Module 17 client obeys:

| Rule | Why |
|------|-----|
| Sort the UI by `seq`, never by a client `ts` | Client clocks are wrong — sometimes by hours, sometimes deliberately |
| Display the **server's** `ts` (protocol §1) | It is the only clock everyone shares |
| An optimistic bubble **must be able to move** | Its `seq` may land *below* one already rendered after a slow send |
| Replies carry `reply_to` | Sidesteps ordering for the one case users genuinely notice |
| Never renumber `seq` | It is a stored cursor on thousands of devices |

### Causal ordering, and why we skip it

There is a genuinely stronger model: **causal ordering**, where each message
carries the set of messages its sender had already seen (a vector clock, or a
parent set). It preserves "B was a reply to A" even across a partition, and it is
what CRDT systems use.

Pulse does not implement it because a **single sequencer per room** gives *total*
order per room, which is strictly stronger than causal order and vastly simpler.
The cost is that the sequencer is a per-room serialization point — which is fine,
because rooms are the shard boundary anyway.

You would need causal ordering if a room could be written in two regions at once.
That is Module 19's problem, and Module 19 says so.

---

## The bug Module 09 introduced

Module 05's protocol file is normative, and §2 says:

> `seq` is gapless within a room. A client observing `seq != last_seq + 1` MUST
> treat the intervening values as missing.

Module 05 honoured that by allocating the sequence number and inserting the row in
**one transaction**: `INSERT INTO chat_roomsequence … ON CONFLICT DO UPDATE SET
last_seq = last_seq + 1 RETURNING last_seq`, then the message insert, then commit.
Roll back and the counter rolls back with it. Gapless by construction.

Module 09 moved the hot path to Streams and split it into two independent awaits:

```python
seq = await allocate_seq(room_id)          # Redis INCR
envelope = {... "seq": seq ...}
entry_id = await fanout.append(room_id, envelope)   # XADD
```

Two problems, both invisible in single-client development.

**Problem 1 — gaps.** If `allocate_seq` succeeds and `fanout.append` raises (Redis
blip, worker killed, `CancelledError` from a client disconnect between the two
lines), that sequence number is burned. It will never appear in any message. Every
client's gap detector will wait for it forever and re-issue `resume` on a 500 ms
timer, permanently. One dropped `XADD` becomes a per-client request loop that
never ends.

**Problem 2 — inversions.** `await` is a yield point. Two coroutines in the same
worker can interleave:

```
task A:  seq = INCR → 481          task B:
                                   seq = INCR → 482
                                   XADD (seq 482)  ← lands first
         XADD (seq 481)            ← lands second
```

The stream now holds 482 before 481. Every worker's consumer loop reads the stream
in stream order, so every client receives 482, *then* 481. A client that renders on
arrival shows them backwards. A client with a gap detector sees a "gap" at 481 that
closes 3 ms later, and fires a repair request for nothing.

At one sender per room this never happens. At 64 concurrent senders in one room the
lab measures **412 inversions per 10,000 messages** — 4.1%, entirely invisible until
you have real concurrency.

### The fix: make allocation and append one operation

Redis is single-threaded and a Lua script runs to completion without interleaving
(Module 08). So put both steps in one script:

```lua
local seq = redis.call('INCR', KEYS[1])
local envelope = string.gsub(ARGV[1], '__SEQ__', tostring(seq))
local id = redis.call('XADD', KEYS[2], 'MAXLEN', '~', ARGV[2], '*', 'payload', envelope)
return {seq, id}
```

Both keys carry the `{room_id}` hash tag Module 09 added for exactly this reason —
they live in the same Cluster slot, so the script is legal under Redis Cluster
(Module 18).

Now a sequence number is allocated **if and only if** the entry is in the stream,
and stream order **is** sequence order. Both problems are gone in five lines, and
the send path drops from two round trips to one.

> **Why not go back to Postgres allocation?** Because Module 09 deliberately moved
> persistence *off* the send path so that a send is one Redis round trip. Putting
> the sequencer back in Postgres puts a row lock on `chat_roomsequence` in front of
> every send, which the lab measures at **2,900 sends/s per room** against Redis's
> **31,900**. The Lua script keeps the speed and restores the guarantee. That is
> the whole trade, and it is a rare one where you do not have to give anything up.

### One residual gap source, and the field that already handles it

An entry can be in the stream and still never reach the store: a poison payload
that raises on every delivery attempt, which an operator eventually dead-letters.
That leaves a real hole in `chat_message`.

You do **not** need a protocol change for this. Look at §3.5 again:

```
resume.batch   S→C   messages, from_seq, to_seq, has_more
```

`to_seq` is not "the seq of the last message in this batch." It is **"this batch
covers everything up to and including `to_seq`."** On a batch with
`has_more: false`, a client sets its cursor to `to_seq`, not to the last message it
received — which steps it over any hole the server has confirmed will never fill.

That distinction is the entire permanent-gap mechanism, and it was already in the
protocol. Read specs carefully.

---

## Resume: the client tells you where it got to

```
client                                            server
  │  {"type":"resume","data":{"from_seq":48213}}    │
  ├────────────────────────────────────────────────▶│  SELECT … WHERE room_id=%s
  │                                                  │    AND seq > 48213
  │                                                  │  ORDER BY seq LIMIT 201
  │  {"type":"resume.batch","data":{                 │
  │     "messages":[…200…],"from_seq":48213,         │
  │     "to_seq":48413,"has_more":true}}             │
  │◀────────────────────────────────────────────────┤
  │  {"type":"resume","data":{"from_seq":48413}}     │
  ├────────────────────────────────────────────────▶│
```

Three requirements, each a real decision:

**1. The client must persist `from_seq` across reloads.** `localStorage`, keyed per
room. A client that forgets its cursor on refresh re-downloads everything — which
at 20,000 connections is a self-inflicted denial of service every time you ship a
frontend change.

**2. Resume must be bounded.** A client gone for a week cannot receive 400,000
messages over a socket. Cap the batch (200), set `has_more`, and above a threshold
(5,000) tell the client to abandon the cursor and page history through the REST
endpoint instead. That endpoint is DRF `CursorPagination` — Module 12 built it, and
it is keyset under the hood, which is why it stays flat at any depth.

**3. Resume must be idempotent with live delivery**, which brings us to the one
race everybody gets wrong.

### Subscribe first. Always.

**Wrong order — a permanent hole:**
```
t=0  client sends resume from_seq=100
t=1  server queries, returns 101..150
t=2  message 151 is published — the client is NOT in the local registry yet — lost
t=3  client joins the room
t=4  message 152 arrives live
     client holds 101–150, 152.  151 is a hole that resume already passed over.
```

**Right order — duplicates, which are free:**
```
t=0  client joins the room  (registry.add → live frames start arriving and buffering)
t=1  client sends resume from_seq=100
t=2  message 151 published → delivered live → buffered client-side
t=3  server query returns 101..151
t=4  client merges; 151 seen twice, dropped by seq
```

> **Join before you resume. Prefer duplicates over gaps, always** — duplicates are
> removable, gaps are not. This is the at-least-once principle applied one layer
> up, at the socket instead of at the stream.

In Django Channels this ordering is a property of your `receive_json` dispatch: the
`join` handler must complete `registry.add()` (Module 09) before the `resume`
handler runs its query. Because both run in the same coroutine per socket, that
happens naturally — *provided* you do not `await` a database call in `join` before
`registry.add()`. The lab shows that trap.

---

## Gap detection with a debounce

The client tracks the highest **contiguous** seq plus a bounded buffer of
out-of-order arrivals:

```
if seq === contiguous + 1   → render, advance, drain the buffer
if seq >  contiguous + 1    → buffer it, schedule a debounced repair
if seq <= contiguous        → duplicate, drop
```

**The debounce is not an optimization; it is correctness of a sort.** Under load,
frames routinely arrive tens of milliseconds out of order — different sockets, TCP
retransmits, a `XAUTOCLAIM` redelivering an entry 30 seconds late. Firing a
`resume` on every apparent gap converts transient reordering into a request storm
aimed at your database, at exactly the moment the system is already struggling.

500 ms is the number. The lab proves both sides of it: a 300 ms reordering is
absorbed with **zero** repair requests; a 900 ms one triggers exactly **one**; with
the debounce set to 0, the same 900 ms reordering triggers **three**.

### The deduplication window

"Drop it if `seq <= contiguous`" is a dedup rule with an implicit window: it works
for every duplicate, forever, because `contiguous` only moves forward. That is the
client side, and it is free.

The **server** side has a real window, and it is worth naming now because Module 13
shrinks it:

- Idempotency is enforced by `UNIQUE (room_id, client_id)`. That index covers every
  message ever written — an unbounded window, at the cost of an index that is
  **1.4 GB at 50 million rows** and grows forever.
- Module 13 partitions the table by month. Postgres requires the partition key in
  every unique index, so the constraint becomes `UNIQUE (room_id, client_id,
  created_at)` — which only enforces uniqueness **within a partition.** The dedup
  window silently becomes "one month."
- That is fine, because no sane client retries a message for a month. But it is a
  guarantee that changed shape without anyone editing a line of application code,
  which is the kind of thing that ends up in a postmortem.

The lab puts a Redis dedup key with a 24-hour TTL in front of the constraint —
`SET dedup:{room}:{client_id} 1 NX EX 86400`, 0.09 ms versus 0.41 ms for the
Postgres round trip — and is explicit that the Redis layer is a *fast path*, not
the guarantee. Redis restarts; the unique index does not.

---

## Offline delivery is a subtraction, not a queue

A user who is simply *away* does not need a queue. **Do not build per-user
queues** — a million users times an unbounded list is an unbounded memory leak with
extra steps, and every one of those queues needs its own retention policy.

The queue you already have is the message store:

```
unread(user, room) = room.last_seq − user.last_read_seq
```

Store one small integer per `(user, room)` and the entire offline history is
derivable with a range scan on the primary key Module 12 chose.

| Approach | 1M users × 20 rooms × 100 unread |
|----------|----------------------------------|
| Per-user message queue | 2,000,000,000 rows |
| **Two integers** | 20,000,000 rows × 16 B = **320 MB** |

The same argument kills a stored `unread_count` column. Derive it. A separately
maintained counter is the classic drift bug where the badge says 3 and the room is
empty, and it drifts because the two writes are not atomic. Cache the subtraction
in Redis for read speed if you like — but keep the two sequence numbers as the
source of truth, so the cache can always be rebuilt from scratch.

Push notifications *are* a genuinely separate channel with a different delivery
model (APNs/FCM, batching, do-not-disturb). This course notes them and does not
build them.

### Read receipts are a high-water mark

`read.upto {seq: 48250}` (protocol §3.3). Monotonic and idempotent by design, which
buys three things at once:

- **A lost receipt self-heals** — the next one subsumes it. So receipts can ride
  at-most-once transport (the channel layer), and Module 09's routing rule says they
  should.
- **Out-of-order receipts are safe** — `GREATEST()` on the server.
- **They debounce hard.** One per 2 seconds per room. The lab measures 438 receipts
  over five minutes of active reading collapsing to **19**, with identical
  user-visible behaviour.

---

## What happens when you reconnect to a different worker

This is the Django-specific question, and the answer is more interesting than on
the JVM twin — because your "nodes" are worker *processes*, not machines.

Module 09 gave every worker process its own consumer group, created with `id="$"`
the first time that worker gains a local subscriber for a room. So:

```
Client's socket lands on worker-a.
Worker-a's group "node-a-52104" is at stream position 1735689612345-0.
Client disconnects. 100 messages are published.
Client reconnects — nginx or the OS picks worker-b.
Worker-b has never had a subscriber in this room, so XGROUP CREATE … '$'
   → worker-b's group starts at NOW.
   → the 100 messages the client missed are not in worker-b's PEL,
     were never delivered to worker-b's group, and never will be.
```

**The client's cursor cannot be a stream position.** Stream positions are per
worker, and the client has no idea which worker it will land on next. This is why
`resume` reads **Postgres**, not the stream: the store is the only thing that is the
same from every worker's point of view.

Note that the same is true across a deploy, a scale-up, or an OOM-kill — anything
that changes which process holds the socket. On the JVM twin this hazard exists once
per node; here it exists once per *core*, eight times more often on the same box.
Same shape, more chances to get it wrong.

Ordering across the reconnect is preserved by the client, not by the server: worker
B delivers live frames while the resume query is running, so the client sees a
burst that is out of order on arrival. Its seq buffer sorts it. The lab measures
**7 duplicates and 3 arrival inversions, rendering 0 inversions**.

---

## The complete guarantee, stated honestly

After this module, Pulse promises:

> **Every message the server acknowledged to its sender will be delivered to every
> room member at least once, in per-room `seq` order, and a client can detect and
> repair any gap — provided the client returns within the retention window and
> correctly persists its cursor.**

Every clause is load-bearing, and the conditions are the interesting part:

- **"acknowledged to its sender"** — a message lost before `message.ack` is the
  client's problem, which is why the client retries with the same `client_id`
  (protocol §2) and why the retry is a no-op.
- **"at least once"** — not once. Duplicates are on the wire; the client dedups.
- **"per-room"** — not global, and Module 14 needs it that way.
- **"within the retention window"** — beyond it, history comes from REST, not
  resume, and the client is told so with `has_more` plus an abandon signal.
- **"correctly persists its cursor"** — a client bug becomes a data-loss bug.
  Module 17 makes the client half robust; the challenge here makes the server
  defensive against a client that gets it wrong.

Being able to write that paragraph *with its caveats*, and defend each one, is the
deliverable of this module. The capstone's architecture review asks for it again.

---

## What's next

The lab makes the ordering bug happen on purpose and counts it, fixes it with one
Lua script and counts zero, builds resume and gap repair, disconnects a client for
two minutes mid-conversation and proves nothing is lost, measures all three
delivery semantics side by side, and demonstrates the head-of-line blocking that
global ordering would buy you.

See you in [`lab.md`](./lab.md).
