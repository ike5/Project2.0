# Module 17 — The Next.js Real-Time Client

**Goal:** Build the client half of every guarantee this course has made — because
a resume cursor the client persists incorrectly is a data-loss bug, and a
reconnect without jitter is a self-inflicted outage.

⏱️ ~6 hours · **Prerequisites:** Modules 00–16. No prior React needed beyond
"components render from state."

---

## Why the client is load-bearing

Module 10 stated Pulse's guarantee, and note its three conditions:

> Every message accepted by the server will be delivered to every room member at
> least once, in per-room sequence order, and a client can detect and repair any
> gap — **provided the client returns within the retention window and correctly
> persists its cursor.**

Every conditional in that sentence is client-side. Specifically:

| Server guarantee | Client obligation | Failure if broken |
|-----------------|-------------------|-------------------|
| Resume from `fromSeq` | **persist `lastSeq` durably** | silent message loss on reload |
| Gap detection | track the highest *contiguous* seq | undetected holes |
| Idempotency | **generate `clientId` before the first attempt** | duplicates on retry |
| Ordering by `seq` | render sorted by `seq`, not arrival | visibly wrong history |
| Backpressure | debounce typing and read receipts | 97× the traffic (Module 11) |
| Graceful failover | **jittered reconnect** | thundering herd (Module 18) |

A perfect server plus a naive client is a broken product. This module builds the
other half.

---

## Server Components and WebSockets don't mix

Next.js App Router defaults to **React Server Components** — rendered on the
server, no browser JavaScript, no state, no effects.

A WebSocket is stateful, long-lived, and browser-only. So:

```
app/
├── layout.tsx                 Server Component  — shell, fonts, metadata
├── rooms/[id]/page.tsx        Server Component  — fetch initial history (fast, SEO-able)
│   └── <ChatClient />         'use client'      — the socket lives here
```

The useful pattern is **server-rendered initial history, client-rendered live
updates**:

1. The Server Component fetches the last 50 messages with a normal HTTP call.
   The user sees content on first paint, with no socket connected.
2. The Client Component mounts, connects, subscribes, and **resumes from the seq
   of the last server-rendered message.**

That handoff is the interesting part: the server render *is* the initial cursor,
so there's no window where the client is connected but doesn't know where it is.

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

**1. `localStorage` can throw.** Safari private mode, quota exceeded, and
enterprise policies all make `setItem` throw. An unguarded write breaks the app.

```ts
function saveCursor(room: string, seq: number) {
  try { localStorage.setItem(`pulse:cursor:${room}`, String(seq)); }
  catch { /* non-fatal: we re-resume from the server's window next time */ }
}
```

**2. Multiple tabs race.** Two tabs of the same room each advance the cursor;
whichever writes last wins, and the other tab's position is lost. Module 10's
challenge established that **delivery cursors are per-device, read cursors are
per-user** — so tabs should share a *read* cursor and keep their own *delivery*
position.

The clean fix is a **`SharedWorker`** holding one socket for all tabs. It's more
work but it also cuts your connection count by the average tab multiplier — which
for a chat app people leave open is 2–4×. The lab builds both.

---

## Rendering 100,000 messages

A chat room's history exceeds what the DOM can hold. Naive rendering of 50,000
messages produces ~500,000 DOM nodes, gigabytes of memory, and multi-second
scroll jank.

**Virtualization** renders only what's visible plus a small overscan:

```
   ┌──────────────┐  ← scroll container, 50,000 items
   │              │
   │  ▓▓▓▓▓▓▓▓▓▓  │  ← ~20 rendered
   │  ▓▓▓▓▓▓▓▓▓▓  │
   │              │
   └──────────────┘
```

Chat makes this harder than a normal list, in three specific ways:

1. **Variable heights.** Messages differ; you can't compute offsets from an
   index. You need measurement and a cache.
2. **Prepending.** Loading older history adds items *above* the viewport, which
   shifts everything down — the user's scroll position jumps unless you
   compensate.
3. **Scroll anchoring.** A new message at the bottom should auto-scroll **only
   if the user was already at the bottom.** Otherwise you yank them away from
   what they were reading.

`@tanstack/react-virtual` handles (1) and most of (2). (3) is yours.

---

## Optimistic send, and the reconciliation trap

Module 05 designed this; here it is in React.

```
1. User hits enter
2. Generate clientId (UUIDv7)
3. Render immediately, state='pending'
4. Send
5. ACK arrives → match on clientId → state='sent', record seq
6. Broadcast arrives with the SAME clientId → must NOT create a second bubble
```

**Step 6 is the trap.** The sender receives their own message back through the
fan-out. Without reconciliation on `clientId`, every message you send appears
twice. Every chat client has shipped this bug at least once.

Keep messages in a `Map<clientId | id, Message>` rather than an array, and always
upsert.

### Failure states the UI must express

| State | Cause | UI |
|-------|-------|-----|
| `pending` | in flight | grey, no tick |
| `sent` | ACK received | one tick |
| `delivered` | recipient receipts (small rooms only) | two ticks |
| `failed` | error, or timeout with no ACK | red, **Retry** |
| `queued-offline` | no connection | clock icon, sends on reconnect |

The last one matters more than it looks: a user who types while offline expects
the message to send when they reconnect. That means an **outbox in the client**,
persisted, replayed on reconnect — and safe to replay because `clientId` makes it
idempotent.

---

## Reconnect: full jitter, not fixed delay

Module 10 measured this: a fixed 1-second retry gave a **4,881/sec** reconnect
peak; full jitter gave **214/sec**.

```ts
// WRONG — 10,000 clients all return at t+1s
setTimeout(reconnect, 1000);

// WRONG — they all wait at least `base`, then arrive in a narrow window
setTimeout(reconnect, base + Math.random() * 1000);

// RIGHT — arrivals spread uniformly across the whole window
const delay = Math.random() * Math.min(30_000, 1000 * 2 ** attempt);
```

And **read the close code** — Module 03 designed the 4xxx range for exactly this:

| Code | Meaning | Client action |
|------|---------|---------------|
| 1000 | normal | don't reconnect |
| 1001 | going away (deploy) | reconnect with jitter |
| 1006 | abnormal (network died) | reconnect with jitter |
| 4001 | token expired | **refresh the token, then reconnect** |
| 4003 | kicked | don't reconnect; show why |
| 4029 | rate limited | honour `retryAfter` |

A client that treats 4001 like 1006 reconnects forever with a dead token.

---

## Don't fetch on the server what the socket will send

A subtle duplication: the Server Component fetches the last 50 messages, then the
client connects and resumes — and if the resume starts from 0 it fetches them
again.

```tsx
// Server Component
const initial = await fetchHistory(roomId, 50);
return <ChatClient roomId={roomId} initial={initial}
                   initialSeq={initial.at(-1)?.seq ?? 0} />;
```

The client seeds its cursor from `initialSeq` when it has no stored one. The
server render *is* the cursor.

---

## What's next

The lab builds the client: virtualized list, optimistic send with reconciliation,
gap detection, an offline outbox, jittered reconnect, and a `SharedWorker` that
holds one socket for all tabs. Then it runs the full disconnect drill from Module
10 against a real browser.

See you in [`lab.md`](./lab.md).
