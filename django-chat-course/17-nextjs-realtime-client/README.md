# Module 17 — The Next.js Real-Time Client

**Goal:** Build the client half of every guarantee this course has made — because
a resume cursor the client persists incorrectly is a data-loss bug, and a
reconnect without jitter is a self-inflicted outage.

⏱️ ~6 hours · **Prerequisites:** Modules 00–16. No prior React needed beyond
"components render from state." TypeScript is used throughout and explained where
it is doing real work.

> The Django/Python twin of
> [`spring-boot-chat-course/17-nextjs-realtime-client`](../../spring-boot-chat-course/17-nextjs-realtime-client/).
> The client is the one place where the two courses genuinely converge: a browser
> is a browser. What differs is the **protocol** — the JVM twin speaks STOMP over
> SockJS, Pulse speaks the raw JSON envelope you designed in
> [Module 05](../05-protocol-and-domain-design/). Every frame, every error code,
> every close code in this module comes from
> [`pulse-protocol-v1.md`](../05-protocol-and-domain-design/code/pulse-protocol-v1.md),
> which is **normative**. If this module and that file disagree, that file wins.

---

## Why the client is load-bearing

[Module 10](../10-ordering-and-delivery-semantics/) stated Pulse's guarantee.
Read it again and notice where the conditions live:

> Every message accepted by the server will be delivered to every room member at
> least once, in per-room sequence order, and a client can detect and repair any
> gap — **provided the client returns within the retention window and correctly
> persists its cursor.**

Every conditional in that sentence is **client-side**:

| Server guarantee | Client obligation | Failure if broken |
|-----------------|-------------------|-------------------|
| `resume` from `from_seq` (§3.5) | **persist the cursor durably** | silent message loss on reload |
| Gapless `seq` (§2) | track the highest **contiguous** seq, not the highest seen | undetected holes |
| Idempotency via `client_id` (§2) | **generate it before the first attempt** and reuse it on every retry | duplicates on retry |
| Ordering by `seq` | render sorted by `seq`, not by arrival | visibly wrong history |
| Rate limits (Module 11) | honour `retry_after_ms` on the `rate_limited` error frame | a retry storm aimed at a system already saying "slow down" |
| Presence/typing budget (Module 11) | debounce typing to 1 per 3 s, receipts to 1 per 2 s | 97× the traffic the server sized for |
| Graceful drain (Module 18) | **jittered** reconnect on `control{action:"drain"}` | a 3,341/s reconnect peak instead of 214/s |

A perfect server plus a naive client is a broken product. This module builds the
other half — and, in the process, gives you a second opinion on every protocol
decision, because a spec is only as good as the second implementation of it.

---

## Server Components and WebSockets do not mix

Next.js App Router defaults to **React Server Components**: rendered on the
server, no browser JavaScript, no state, no effects. A WebSocket is stateful,
long-lived and browser-only. So:

```
app/
├── layout.tsx                 Server Component  — shell, fonts, metadata
├── rooms/[slug]/page.tsx      Server Component  — fetch initial history (fast, SEO-able)
│   └── <ChatClient />         'use client'      — the socket lives here
```

The useful pattern is **server-rendered initial history, client-rendered live
updates**:

1. The Server Component fetches the last 50 messages over HTTP — DRF's
   `CursorPagination` from [Module 12](../12-postgres-message-store/), which is
   keyset underneath and therefore flat at any depth. The user sees content on
   first paint with no socket connected.
2. The Client Component mounts, connects, joins, and **resumes from the `seq` of
   the last server-rendered message.**

```tsx
// app/rooms/[slug]/page.tsx  — Server Component
const initial = await fetchHistory(slug, 50);
return <ChatClient roomKey={`room.${slug}`}
                   initial={initial}
                   initialSeq={initial.at(-1)?.seq ?? 0} />;
```

That handoff is the interesting part: **the server render *is* the initial
cursor**, so there is no window in which the client is connected and does not
know where it is.

> ⚠️ **React Strict Mode double-mounts every component in development.** A
> `useEffect` that opens a socket will open two, and you will spend an afternoon
> debugging duplicate messages that do not exist in production. Keep the
> connection **outside React** — a plain class, created once, referenced by the
> component. Every serious realtime React app arrives at this.

---

## One socket, many rooms

Protocol §1 says the v1 URL is `/ws/room/<slug>/` — one socket per room — and
notes that **Module 17 multiplexes many rooms over one socket, which is why
`room` appears in every envelope.** Here is that, done compatibly.

```
v1 (Modules 04–16):       ws://host/ws/room/general/?ticket=…    one socket per room
v1 + multiplex (M17):     ws://host/ws/rooms/?ticket=…           one socket, N rooms
```

The multiplexed endpoint adds exactly three message types:

| Type | Direction | `data` |
|------|-----------|--------|
| `room.subscribe` | C→S | `room` in the envelope; `from_seq` (opt) |
| `room.unsubscribe` | C→S | `room` in the envelope |
| `room.subscribed` | S→C | `room`, `last_seq` |

Protocol §1 defines **adding a new `type` as a compatible change**, so this is
still `v: 1` and no version bump is required. Two rules make it safe:

- **The server MUST keep serving `/ws/room/<slug>/`.** Older clients exist; the
  capstone's chaos run uses them.
- **The client MUST fall back.** A server that does not implement multiplexing
  replies with `{"type":"error","data":{"code":"unknown_type"}}` (§4), and the
  correct response is to close and open one socket per room — not to retry, and
  not to fail. §4's table says `unknown_type` means "do not retry", and this is
  what acting on that looks like.

### What multiplexing buys, and what it costs

| | One socket per room | One socket, N rooms |
|---|--------------------|--------------------|
| Sockets for a user in 20 rooms | 20 | **1** |
| Server memory (≈45 KB/conn, Module 06) | 900 KB | **45 KB** |
| Handshakes on reconnect | **20** | 1 |
| Head-of-line blocking | per room | **across all rooms** |
| A slow room | affects itself | **affects every room on that socket** |
| Close code granularity | per room (`4403` closes one room) | **`4403` must not close the socket** |

The last two rows are the real cost. A single `4403 not authorized` must now be
delivered as an **error frame naming the room**, not as a close — which is exactly
what §4 already requires ("an `error` frame MUST NOT close the connection") and
exactly why `not_a_member` is an error code rather than a close code.

Twenty sockets per user against 45 KB each is 900 KB; at Module 06's ~40,000
connections per worker process, multiplexing is the difference between 2,000 and
40,000 *users* on a worker. It is not a micro-optimization.

---

## Where the cursor lives

`localStorage` is the obvious choice and it is **not sufficient**:

| Storage | Survives reload | Survives tab close | Shared across tabs | Fails when |
|---------|----------------|-------------------|--------------------|-----------|
| React state | ❌ | ❌ | ❌ | always |
| `sessionStorage` | ✅ | ❌ | ❌ | new tab |
| `localStorage` | ✅ | ✅ | ✅ (racily) | private mode, quota, disabled |
| **IndexedDB** | ✅ | ✅ | ✅ | rarely |

Two real problems:

**1. `localStorage` throws.** Safari private mode, quota exceeded, and enterprise
policies all make `setItem` throw. An unguarded write breaks the app on the
platforms where you have no debugger.

```ts
function saveCursor(room: string, seq: number) {
  try { localStorage.setItem(`pulse:cursor:${room}`, String(seq)); }
  catch { /* non-fatal: we re-resume from the server's window next time */ }
}
```

**2. Multiple tabs race.** Two tabs of the same room each advance the cursor;
whichever writes last wins, and the other tab's position is lost. Module 10's
challenge already drew the distinction that resolves this: **delivery cursors are
per-device, read cursors are per-user.** So tabs share a *read* cursor (`read.upto`,
§3.3, which is a server-side high-water mark anyway) and keep their own *delivery*
position.

The clean fix is a **`SharedWorker`** holding one socket for all tabs. It is more
work, and it also cuts your connection count by the average tab multiplier —
which for a chat app people leave open is 2–4×. Combined with room multiplexing
that is a **40–80× reduction** in sockets per user. The lab builds both.

### The write-order rule that is a data-loss bug if you get it wrong

```ts
// WRONG — the cursor advances before the message is in the store
saveCursor(room, msg.seq);
store.upsert(msg);            // <-- a crash here loses msg, permanently

// RIGHT
store.upsert(msg);
saveCursor(room, msg.seq);    // <-- a crash here re-delivers msg, which is free
```

That is Module 10's principle — **prefer duplicates over gaps, always** — applied
to two lines of client code. Duplicates are removable; gaps are not.

---

## Optimistic send, and the reconciliation trap

[Module 05](../05-protocol-and-domain-design/) designed this. Here it is as a
state machine.

```
1. User hits enter
2. Generate client_id (UUIDv7 — time-ordered, §2 allows ULID or UUIDv7)
3. Render immediately, state='pending'
4. Send message.create
5. message.ack arrives  → match on client_id → state='sent', record id and seq
6. message.new arrives with the SAME client_id → must NOT create a second bubble
```

**Step 6 is the trap.** Protocol §3.1 is explicit: `message.new` goes to every
member of the room **including the sender** — which is why `client_id` is echoed
in it. Without reconciliation on `client_id`, every message you send appears
twice. Every chat client has shipped this bug at least once.

And §3.1 adds the detail that makes a naive implementation fail intermittently:

> `message.ack` and `message.new` are independent frames and MAY arrive in either
> order. Clients MUST key reconciliation on `client_id`, not on arrival order.

So the store is a `Map` keyed by `client_id`-or-`id`, and every write is an
**upsert**. An array with `push` is the wrong data structure, and it is the one
everybody reaches for first.

### The failure states the UI must express

| State | Cause | UI |
|-------|-------|-----|
| `pending` | in flight | grey, no tick |
| `sent` | `message.ack` received | one tick |
| `delivered` | `read.update` from a recipient (small rooms only — §3.3 caps it at 16 members) | two ticks |
| `failed` | an `error` frame with this `client_id`, or a timeout with no ack | red, **Retry** |
| `queued-offline` | no connection | clock icon; sends on reconnect |
| `rate_limited` | `error{code:"rate_limited"}` with `retry_after_ms` | grey with a countdown; auto-retries |

The last two matter more than they look:

- The **offline outbox** means a user who types on a train expects the message to
  send when they reconnect. That needs a persisted queue, replayed on reconnect —
  and it is safe to replay **only because `client_id` makes it idempotent**.
- **`rate_limited` is not `failed`.** §4 says: back off by `retry_after_ms`, then
  retry with the **same `client_id`**. Showing it as a red failure teaches the
  user to retype, which regenerates the `client_id`, which turns one message into
  two. A protocol detail becomes a UX decision becomes a data bug.

---

## Reconnect: full jitter, and read the close code

[Module 18](../18-compose-ha-and-chaos/) measures this: a fixed retry produces a
**3,341/second** reconnect peak; full jitter produces **214/second**.

```ts
// WRONG — 10,000 clients all return at t+1s
setTimeout(reconnect, 1000);

// WRONG — they all wait at least `base`, then arrive in a narrow window
setTimeout(reconnect, base + Math.random() * 1000);

// RIGHT — arrivals spread uniformly across the whole window
const delay = Math.random() * Math.min(30_000, 1000 * 2 ** attempt);
```

The middle one is the version people write when they have heard of jitter, and it
is barely better than the first: the arrival distribution is still a narrow band,
just displaced. **Full jitter samples the entire window**, which is the property
that flattens the peak.

### The close codes are from the protocol, and they are not the JVM twin's

Protocol §4 defines the application range. Note that these differ from the
`4001/4003/4029` the STOMP course uses — Pulse chose the `4xxx` values that echo
their HTTP analogues, and a client that assumes the wrong ones reconnects forever
with a dead ticket.

| Close code | Meaning | Client action |
|-----------|---------|---------------|
| `1000` | normal | **do not reconnect** |
| `1001` | going away (deploy) | reconnect with full jitter |
| `1006` | abnormal — no frame received; the network died | reconnect with full jitter |
| `1009` | frame exceeded the transport limit | reconnect; **do not resend that frame** |
| `4008` | slow consumer — the server dropped you to protect the room | reconnect, and **reduce your own send rate** |
| `4009` | application-level frame too large | reconnect; fix the frame |
| `4401` | unauthenticated | **mint a new ticket**, then reconnect |
| `4403` | authenticated but not authorized for this room | do not reconnect *for that room*; show why |
| `4429` | sustained abuse (Module 21) | long backoff; honour any `retry_after_ms` you were last given |

Two of these are client bugs reported by the server, and they deserve different
handling from "the network died":

- **`4008` slow consumer.** *You* were too slow to drain your socket. Reconnecting
  at the same rate reproduces it immediately. The correct response is to reconnect
  *and* shed work — stop rendering every frame, drop typing indicators, batch
  harder. See "Backpressure" below.
- **`4429`** means Module 21's abuse detection decided you are hostile.
  Reconnecting aggressively confirms it.

### `control` frames, which are not close codes

§3.6 defines `control` with four actions, and they arrive on a **live** socket:

| `action` | Meaning | Client action |
|----------|---------|---------------|
| `drain` | this node is going away (Module 18) | finish in-flight sends, then reconnect after **full jitter over `retry_after_ms`** |
| `reauth` | present a fresh ticket in-band (Module 21) | refresh and re-authenticate **without dropping the socket** |
| `revoked` | membership removed | leave the room; do not resubscribe |
| `rate_limited` | Module 11 | back off |

`drain` is the one that makes zero-downtime deploys work. The server asks nicely
*before* closing, so the client can reconnect to a healthy node on its own
schedule rather than all at once when the node dies. A client that ignores
`control` still works — it just turns every deploy into the 3,341/s peak.

---

## Gap detection, with the debounce that is correctness

Module 10 specified the algorithm; it belongs in the client, per room:

```
if seq === contiguous + 1   → render, advance, drain the buffer
if seq >  contiguous + 1    → buffer it, schedule a debounced repair
if seq <= contiguous        → duplicate, drop
```

**The 500 ms debounce is not an optimization.** Under load, frames routinely
arrive tens of milliseconds out of order — different sockets, TCP retransmits,
an `XAUTOCLAIM` redelivering an entry 30 seconds late (Module 09). Firing a
`resume` on every apparent gap converts transient reordering into a request storm
aimed at your database, at exactly the moment the system is already struggling —
and Module 11's `rl:resume` limiter (5 burst, 0.1/s) then rate-limits the client,
so the room appears frozen.

Module 10 measured both sides: a 300 ms reordering is absorbed with **zero**
repair requests; a 900 ms one triggers exactly **one**; with the debounce at 0,
the same 900 ms reordering triggers **three**.

### `to_seq`, and why you must not ignore it

§3.5's `resume.batch` carries `from_seq`, `to_seq` and `has_more`. Module 10 is
emphatic about what `to_seq` means:

> `to_seq` is not "the seq of the last message in this batch." It is **"this batch
> covers everything up to and including `to_seq`."**

So on a batch with `has_more: false`, the client sets its cursor to **`to_seq`**,
not to the last message it received. That single line is what steps a client over
a permanent hole — a poison message that was dead-lettered, or Module 16's
`seq`-allocated-but-never-published window. A client that advances to
`messages.at(-1).seq` instead will re-request the same hole forever.

**Join before you resume.** Module 10's ordering rule, on the client: send
`room.subscribe` first, let live frames start arriving and buffering, *then* send
`resume`. The other order leaves a permanent hole at whatever was published
between the query and the subscribe.

---

## Backpressure, in a browser

Two directions, two different problems.

**Outbound: `ws.bufferedAmount`.** A WebSocket `send()` never blocks; it buffers.
On a bad network the buffer grows without limit until the tab's memory does.

```ts
if (ws.bufferedAmount > 256 * 1024) {
  // Shed the cheap stuff FIRST: typing (at-most-once by design, §3.2), then
  // read receipts (a high-water mark, §3.3 — a later one supersedes an
  // earlier one). Never shed message.create; queue it in the outbox instead.
  return;
}
```

The protocol already told you which frames are droppable. §3.2: typing is
"explicitly at-most-once and lossy." §3.3: read state is "a high-water mark, not
a per-message receipt." **Frames whose semantics allow loss are your
backpressure budget**, and Module 05 wrote that budget down before anyone needed
it.

**Inbound: React cannot render at 400 Hz.** A busy room delivers hundreds of
frames per second. One `setState` per frame is hundreds of renders per second, a
frozen tab, and eventually a `4008` close because you stopped draining the socket.

```ts
// Accumulate into a plain object, flush once per animation frame.
pending.push(envelope);
if (!scheduled) {
  scheduled = true;
  requestAnimationFrame(() => { scheduled = false; flush(pending.splice(0)); });
}
```

**≤60 renders/second regardless of arrival rate.** The lab measures 340 frames/s
going from 340 renders/s (6 fps, unusable) to 58 renders/s (60 fps).

> Note the shape: this is the *same* fix as Module 11's presence aggregation —
> make the work depend on **time** rather than on the **number of events**, so
> the worst case is bounded. A hard bound on the worst case is worth more than a
> large improvement in the average, because the worst case is when you get paged.

---

## Rendering 100,000 messages

A chat room's history exceeds what the DOM can hold. Naively rendering 50,000
messages produces ~500,000 DOM nodes, hundreds of megabytes, and multi-second
scroll jank.

**Virtualization** renders only what is visible plus a small overscan:

```
   ┌──────────────┐  ← scroll container, 50,000 items
   │              │
   │  ▓▓▓▓▓▓▓▓▓▓  │  ← ~20 rendered
   │  ▓▓▓▓▓▓▓▓▓▓  │
   │              │
   └──────────────┘
```

Chat makes this harder than a normal list in three specific ways:

1. **Variable heights.** Messages differ; you cannot compute offsets from an
   index. You need measurement and a cache.
2. **Prepending.** Loading older history adds items *above* the viewport, which
   shifts everything down — the user's scroll position jumps unless you
   compensate.
3. **Scroll anchoring.** A new message at the bottom should auto-scroll **only if
   the user was already at the bottom.** Otherwise you yank them away from what
   they were reading.

`@tanstack/react-virtual` handles (1) and most of (2). (3) is yours, and the
challenge makes edits and deletes break (1) on purpose.

---

## What's next

The lab scaffolds `apps/pulse-web/`, builds the connection manager (close codes,
full jitter, `control` frames, ticket auth), the per-room store (cursor, gaps,
dedup, optimistic reconciliation), the multiplexed socket with its compatible
fallback, the virtualized list, the offline outbox, rAF batching, and a
`SharedWorker` holding one socket across tabs — then runs Module 10's
two-minute-disconnect drill in a real browser and proves 98 messages recovered.

See you in [`lab.md`](./lab.md).
