# Module 10 — Ordering & Delivery Semantics

**Goal:** Close the last gap — the server-to-client hop — with resume cursors,
gap detection, offline queues and read receipts. And confront the ordering
guarantees you can actually make, versus the ones users assume you made.

⏱️ ~5 hours · **Prerequisites:** Modules 00–09.

---

## The gap that's left

Module 09 made messages durable **between servers**. It did nothing for the last
hop:

```
   Postgres ──✅──▶ Redis Stream ──✅──▶ app node ──❓──▶ browser
   durable          at-least-once        fan-out       fire and forget
```

A WebSocket write is `socket.send(bytes)`. It returns as soon as the bytes are in
a kernel buffer. If the client's phone is entering a tunnel:

- The bytes sit in the send buffer.
- TCP retries for ~15 minutes, then gives up.
- Your server eventually sees a close.
- **The message is gone**, and the server acked it to Redis long ago.

So the guarantee chain breaks at exactly the point the user experiences it.

---

## Resume cursors

The fix is the same one SSE gets for free (Module 03): the client tells you where
it got to, and you send it the difference.

```
client                                          server
  │  RESUME { room: "7", fromSeq: 48213 }         │
  ├──────────────────────────────────────────────▶│
  │                                                │  SELECT ... WHERE room_id=7
  │                                                │    AND seq > 48213
  │                                                │    ORDER BY seq LIMIT 200
  │  resume.batch { messages: [...], hasMore }    │
  │◀──────────────────────────────────────────────┤
  │  RESUME { fromSeq: 48413 }  (if hasMore)      │
  ├──────────────────────────────────────────────▶│
```

Three requirements, and each is a real design decision:

**1. The client must persist `lastSeq` across reloads.** In `localStorage`, per
room. A client that forgets its cursor on refresh re-downloads everything, which
at scale is a self-inflicted DDoS every time you deploy a frontend change.

**2. Resume must be bounded.** A client gone for a week cannot receive 400,000
messages over a WebSocket. Cap the batch, set `hasMore`, and above some threshold
tell the client to **abandon the cursor and load a fresh page of history** via
the normal REST path.

**3. Resume must be idempotent with live delivery.** Between "server reads the
database" and "client resubscribes," new messages arrive. Deliver them twice
rather than lose them, and let the client dedup on `seq` — the ordering that
makes this safe is explained below.

---

## The subscribe-then-resume race

This is the subtle bug, and it's worth drawing.

**Wrong order — messages lost:**
```
t=0  client sends RESUME fromSeq=100
t=1  server queries: returns 101..150
t=2  message 151 is published — client is NOT subscribed yet — lost forever
t=3  client subscribes
t=4  message 152 arrives live
     client has 101-150, 152.  151 is a permanent hole.
```

**Right order — messages duplicated, which is fine:**
```
t=0  client SUBSCRIBES first (live messages start buffering client-side)
t=1  client sends RESUME fromSeq=100
t=2  message 151 published → delivered live, client buffers it
t=3  server query returns 101..151
t=4  client merges: 151 seen twice → deduped by seq
```

> **Always subscribe before resuming.** Prefer duplicates over gaps, always,
> because duplicates are removable and gaps are not. This is the same principle
> as at-least-once delivery, applied one layer up.

---

## Gap detection

The client tracks the highest **contiguous** sequence it has, plus a buffer of
out-of-order arrivals:

```js
if (msg.seq === lastContiguous + 1) {
  render(msg); lastContiguous++;
  drainBuffer();                       // anything now contiguous
} else if (msg.seq > lastContiguous + 1) {
  buffer.set(msg.seq, msg);            // hold it
  scheduleGapRepair(lastContiguous);   // ask the server, after a delay
} else {
  /* duplicate — drop */
}
```

**`scheduleGapRepair` must be debounced.** Under a burst, messages routinely
arrive slightly out of order for tens of milliseconds. Firing a resume request
on every apparent gap turns transient reordering into a request storm. Wait
~500 ms; most gaps close on their own.

### Permanent gaps

Module 05's challenge found one: a sequence number can be allocated and never
used, leaving a hole that will never fill. A client would ask for it forever.

The server must be able to say so:

```json
{ "type": "resume.batch", "messages": [...], "gaps": [48214], "hasMore": false }
```

The client marks 48214 as permanently absent and advances past it. Without this,
every such hole becomes an infinite retry loop.

---

## Offline delivery

Resume works if the client comes back. What about a user who is simply *away*?

**Do not queue per-user in memory.** A million users × an unbounded queue is an
unbounded memory leak with extra steps.

The queue you already have is **the message store itself**:

```
user's inbox = SELECT * FROM messages
               WHERE room_id IN (their rooms) AND seq > their_last_read
```

Store one small number per (user, room) — `last_read_seq` — and the entire
offline history is derivable. Storage cost: 16 bytes per membership, not per
message.

Push notifications are the genuinely separate channel, and they're a different
problem (APNs/FCM, batching, do-not-disturb) that this course notes but doesn't
build.

---

## Read receipts and unread counts

```
read.upto { room: "7", seq: 48250 }
```

Monotonic and idempotent by design: a receipt for 48250 subsumes every earlier
one. That means:

- **Lost receipts self-heal** — the next one covers the gap. So they can ride
  at-most-once transport (Module 09's ack-before-process).
- **Out-of-order receipts are safe** — `max()` on the server.
- **They can be debounced aggressively** client-side. One per 2 seconds per room
  is plenty.

**Unread counts** should be derived, not stored twice:
```
unread(user, room) = room.last_seq - user.last_read_seq
```
Two numbers you already have. Storing a separately-maintained counter creates
the classic drift bug where the badge says 3 and the room is empty.

Cache the subtraction in Redis for read speed (Module 08's `unread:{userId}`
hash), but treat the two sequence numbers as the source of truth so the cache can
always be rebuilt.

---

## What "ordering" can and cannot mean

**You can guarantee:** every client sees a room's messages in the same `seq`
order, and can detect gaps in it.

**You cannot guarantee:** that `seq` order matches the order humans pressed
enter. Two people in different cities pressing enter "simultaneously" have no
meaningful global order. The server picks one, arbitrarily, and that's the
correct behaviour — there is no ground truth to be faithful to.

**Practical consequences:**

| Rule | Why |
|------|-----|
| Sort the UI by `seq`, never by client timestamp | Client clocks are wrong, sometimes by hours, sometimes deliberately |
| Display the **server's** `ts` | It's the only clock everyone shares |
| An optimistic message **must be able to move** | Its `seq` may land below one already rendered; append-only UIs show messages out of order after a slow send |
| Replies reference a parent `id` | Sidesteps ordering entirely for the case users care most about |
| Never renumber `seq` | It's a cursor. Changing it breaks every stored client cursor. |

### Causal ordering, and why we skip it

There's a genuinely better model: **causal ordering**, where each message
references the messages its sender had seen (a vector clock or a "parent" set).
That preserves "B was a reply to A" even across partitions, and it's what CRDT
systems use.

Pulse doesn't implement it because a **single sequencer per room** — one `INCR`
in Redis — gives total order per room, which is strictly stronger than causal
order and vastly simpler. The cost is that the sequencer is a per-room
serialization point, which is fine because rooms are the natural shard boundary
(Module 14).

You'd need causal ordering if rooms could be written in more than one region
simultaneously. That's a multi-region problem, discussed in Module 19.

---

## The complete guarantee, stated honestly

After this module, Pulse promises:

> **Every message accepted by the server (i.e. acked to the sender) will be
> delivered to every room member at least once, in per-room sequence order, and
> a client can detect and repair any gap — provided the client returns within the
> retention window and correctly persists its cursor.**

Note what's conditional. The guarantee is not unconditional, and the conditions
are the interesting part:

- **"accepted by the server"** — a message lost before the ack is the client's
  problem, which is why the client retries with the same `clientId`.
- **"within the retention window"** — beyond it, you get history via REST, not
  resume.
- **"correctly persists its cursor"** — a client bug becomes a data-loss bug.
  Module 17 makes this robust.

Being able to write that paragraph, with its caveats, is the deliverable.

---

## What's next

The lab builds resume, gap detection with debounced repair, permanent-gap
handling, offline delivery from the message store, and read receipts — then kills
a client mid-conversation and proves nothing is lost.

See you in [`lab.md`](./lab.md).
