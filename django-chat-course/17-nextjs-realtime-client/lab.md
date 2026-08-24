# Lab 17 — Build the Client Half of the Guarantee

**You'll:** scaffold `apps/pulse-web/`, build the connection manager (close
codes, full jitter, `control` frames, ticket auth), the per-room store (cursor,
gaps, dedup, optimistic reconciliation), the multiplexed socket with its
protocol-compatible fallback, a virtualized list, an offline outbox, rAF
batching — then run Module 10's two-minute-disconnect drill in a real browser and
watch 98 messages come back.

⏱️ ~130 min.

> **Prerequisite that is not a module:** Node 20+ and a running Pulse backend on
> `localhost:8000`. `docker compose -p pulse-dev -f infra/compose.dev.yml up -d`
> and `uvicorn pulse.asgi:application --loop uvloop --workers 8 --port 8000`.

Reference machine: **8-core / 16 GB, Ubuntu 24.04, Chrome 128, Node 20.**
Everything in this lab is measured in the browser's own tooling — the Performance
panel and `performance.memory` — so your numbers will vary by machine more than
the server-side ones did. The **ratios** are the result.

---

## Part A — Scaffold

```bash
cd apps
npx create-next-app@latest pulse-web \
  --typescript --tailwind --eslint --app --src-dir --no-import-alias
cd pulse-web
npm i @tanstack/react-virtual
```

No STOMP client, no `socket.io`, no `uuid`. Pulse speaks a raw JSON protocol you
designed and the browser's `WebSocket` is the whole transport layer. The one
dependency is the virtualizer, because variable-height measurement caching is
genuinely hard and not what this module is teaching.

`next.config.ts`:
```ts
const nextConfig = {
  async rewrites() {
    return [
      // DRF: history (CursorPagination, Module 12) and ws tickets (Module 21).
      { source: '/api/:path*', destination: 'http://localhost:8000/api/:path*' },
    ];
  },
};
export default nextConfig;
```

> **Only `/api` is proxied.** The WebSocket connects directly to
> `ws://localhost:8000`, because Next's dev-server rewrite does not proxy
> WebSocket upgrades. In production nginx does both (Module 18), and it is
> nginx's `proxy_set_header Upgrade` that makes it work — which is exactly the
> config Module 03 showed proxies getting wrong.

Copy the four reference files:

```bash
cp ../../17-nextjs-realtime-client/code/protocol.ts    src/lib/
cp ../../17-nextjs-realtime-client/code/connection.ts  src/lib/
cp ../../17-nextjs-realtime-client/code/room-store.ts  src/lib/
cp ../../17-nextjs-realtime-client/code/pulse-worker.ts src/lib/
```

Read `protocol.ts` first. It is a transcription of
[`pulse-protocol-v1.md`](../05-protocol-and-domain-design/code/pulse-protocol-v1.md),
which is **normative** — if they disagree, the spec is right.

---

## Part B — The server render is the cursor

`src/app/rooms/[slug]/page.tsx` — a **Server Component**:

```tsx
import ChatClient from './ChatClient';

async function fetchHistory(slug: string, limit: number) {
  // DRF CursorPagination -- keyset underneath (Module 12), so this is 0.86 ms
  // at page 1 and 0.86 ms at page 100,000.
  const r = await fetch(
    `http://localhost:8000/api/rooms/${slug}/messages/?limit=${limit}`,
    { cache: 'no-store' });
  return (await r.json()).results as Array<{ id: number; seq: number;
    sender: string; body: string; ts: number }>;
}

export default async function RoomPage({ params }: { params: { slug: string } }) {
  const initial = (await fetchHistory(params.slug, 50)).reverse();
  return (
    <ChatClient
      roomKey={`room.${params.slug}`}
      initial={initial}
      initialSeq={initial.at(-1)?.seq ?? 0}
    />
  );
}
```

```bash
npm run dev
curl -s localhost:3000/rooms/general | grep -o 'data-seq="[0-9]*"' | tail -1
```
**Expected:**
```
data-seq="48213"
```
✅ **Fifty messages in the HTML, before any JavaScript runs.** And `initialSeq`
is 48213, which the client will resume from — so there is never a window where
the socket is connected and the client does not know where it is.

> The handoff is the interesting part and it is easy to get subtly wrong: if the
> Server Component fetched history and the client resumed from `0`, you would
> download those 50 messages twice — once as HTML, once over the socket. At
> 20,000 connections that is a self-inflicted denial of service every time
> someone refreshes.

---

## Part C — The connection manager

`src/lib/connection.ts` is in place; wire it up in a client component.

```tsx
'use client';
import { useEffect, useRef, useState } from 'react';
import { PulseConnection } from '@/lib/connection';

export default function ChatClient({ roomKey, initial, initialSeq }: Props) {
  // OUTSIDE React's render cycle. A `useState(new PulseConnection(...))` would
  // construct one on every render; a `useEffect` that connects would run TWICE
  // under Strict Mode and open two sockets.
  const connRef = useRef<PulseConnection | null>(null);
  const [state, setState] = useState('idle');

  useEffect(() => {
    const conn = new PulseConnection({
      baseUrl: 'ws://localhost:8000',
      mintTicket: async () => (await (await fetch('/api/ws-ticket/',
        { method: 'POST', credentials: 'include' })).json()).ticket,
      onFrame: (env) => storeRef.current?.handle(env),
      onStateChange: setState,
    });
    connRef.current = conn;
    conn.join(roomKey, initialSeq);
    void conn.connect();
    return () => conn.stop();          // Strict Mode calls this between mounts
  }, [roomKey]);
  ...
}
```

```bash
# In the browser console:
# > performance.getEntriesByType('resource').filter(r => r.name.includes('ws-ticket'))
```
**Expected:** exactly **one** ticket request per mount cycle in production, and
**two** in development — the second because Strict Mode remounts. If you see two
*sockets* rather than two tickets, the connection is inside React and needs to
come out.

### C1. Prove the close codes are handled

The protocol's `4xxx` codes are **not** the ones the STOMP course uses. Test each:

```bash
# Terminal 1: a socket with a deliberately invalid ticket
python - <<'PY'
import asyncio, websockets
async def go():
    try:
        await websockets.connect("ws://localhost:8000/ws/rooms/?ticket=garbage")
    except websockets.InvalidStatus as e:
        print("handshake rejected:", e.response.status_code)
    except websockets.ConnectionClosed as e:
        print("closed with:", e.code, e.reason)
asyncio.run(go())
PY
```
**Expected:**
```
closed with: 4401 Unauthenticated
```

In the browser, force each case and watch the console:

| Force it with | Expected client behaviour |
|---------------|--------------------------|
| `curl -XPOST localhost:8000/api/debug/close/4401` | new ticket minted, reconnect, **attempt counter resets to 0** |
| `.../close/4403` | state `failed`, room marked revoked, **no reconnect** |
| `.../close/4429` | reconnect scheduled with `attempt >= 8` → 30 s cap |
| `.../close/4008` | inbox cleared, reconnect, warning logged |
| `docker pause pulse-uvicorn` | close `1006`, full-jitter reconnect |

**Expected console, for 4403:**
```
room room.general revoked: removed from channel
state: failed
```
✅ **No reconnect.** A client that treats `4403` like `1006` reconnects forever
against an authorization decision that will never change, and every one of those
attempts costs the server a handshake and a ticket validation.

### C2. Measure the jitter

```bash
node 17-nextjs-realtime-client/code/reconnect_sim.mjs \
     --clients 500 --strategy all --attempts 4
```
**Expected** (a distribution, so ±10% run to run; the *ratios* are the result):
```
fixed  (500 clients, base=1000ms, cap=30000ms, 100ms buckets)
  attempt 0:  peak   5000 reconnects/s at t=1.00s  p50=1.00s  spread=0.00s
  attempt 3:  peak   5000 reconnects/s at t=1.00s  p50=1.00s  spread=0.00s

base-plus  (base * 2**attempt + random()*base)
  attempt 0:  peak    590 reconnects/s at t=1.50s  p50=1.51s  spread=1.00s
  attempt 3:  peak    620 reconnects/s at t=8.80s  p50=8.53s  spread=0.99s

full  (random() * min(cap, base * 2**attempt))
  attempt 0:  peak    680 reconnects/s at t=0.20s  p50=0.50s  spread=1.00s
  attempt 3:  peak    130 reconnects/s at t=7.30s  p50=3.89s  spread=7.98s
```

Three things in that output, and the third is the one nobody expects:

1. **Fixed never spreads at all** — `spread=0.00s` on every attempt. The peak is
   the entire fleet, in one bucket, forever. Backing off does not help if
   everyone backs off by the same amount.
2. **`base-plus` — the version people write after they have *heard* of jitter —
   stops improving.** Its band is a constant 1 s wide no matter how far the
   backoff has grown, so by attempt 3 it is a 1 s band inside an 8 s window and
   its peak is *unchanged* from attempt 0. Full jitter's peak fell 5×.
3. **Full jitter's p50 is the *earliest* of the three** at attempt 0 — 0.50 s
   against 1.00 s and 1.51 s. The strategy that is kindest to the server also
   reconnects half your users sooner, because it starts filling the window at
   t=0 instead of waiting out the whole backoff first. That is a rare thing and
   it is worth noticing.

⚠️ **Peak rate is bucket-width dependent.** Re-run with `--bucket 20` and every
peak quadruples. Quoting a peak without its measurement window is how two people
benchmark the same backoff and disagree. Module 18 measures the real thing
against the real cluster — **3,341/s fixed against 214/s full jitter at 20,000
clients** — where the peak is also bounded by how fast the server can accept.
This tool shows you *why* those two numbers differ by 15×.

---

## Part D — The room store: cursor, gaps, dedup

`src/lib/room-store.ts` is in place. Wire it:

```tsx
const storeRef = useRef<RoomStore | null>(null);
const [messages, setMessages] = useState<UiMessage[]>(initial);

if (!storeRef.current) {
  storeRef.current = new RoomStore(
    roomKey,
    initial.map(toUi),
    initialSeq,
    (env, p) => connRef.current?.send(env, p) ?? false,
    () => setMessages(storeRef.current!.list()),
  );
}
```

### D1. Prove gap detection, with and without the debounce

```bash
# Reorder frames by 300 ms on the way out
curl -XPOST localhost:8000/api/debug/reorder -d '{"room":"room.general","jitter_ms":300}'
```
Watch `pulse:resume` requests in the Django log for 60 seconds.
**Expected:**
```
resume requests: 0
sequence gaps observed by client: 41
gaps healed by buffering alone:   41
```
✅ **Forty-one gaps, zero repair requests.** The 500 ms debounce absorbed all of
them, because the missing frame arrived within the window.

```bash
curl -XPOST localhost:8000/api/debug/reorder -d '{"room":"room.general","jitter_ms":900}'
```
**Expected:**
```
resume requests: 1
```
Now set `GAP_DEBOUNCE_MS = 0` in `room-store.ts` and re-run the 900 ms case:
**Expected:**
```
resume requests: 3
```
✅ **1 versus 3.** Module 10 measured exactly this. The debounce is not an
optimization: at scale, three resume requests per reordering event, times 20,000
clients, aimed at the database, at the moment the system is already struggling —
and Module 11's `rl:resume` bucket (5 burst, 0.1/s) then rate-limits the client,
so the room appears frozen to the user.

Put it back to 500.

### D2. Prove `to_seq`, the permanent-gap mechanism

Manufacture a hole the server can never fill — a message the fan-out
dead-lettered:

```bash
curl -XPOST localhost:8000/api/debug/poison -d '{"room":"room.general","seq":48250}'
```

**With the correct implementation** (`this.contiguous = max(contiguous, b.to_seq)`):
```
client: gap at 48250, resume from 48249
server: resume.batch from_seq=48249 to_seq=48310 has_more=false messages=[48251..48310]
client: cursor -> 48310    ✅ stepped over the hole
resume requests after: 0
```

**Now break it** — change the line to `this.contiguous = last.seq`:
```
client: gap at 48250, resume from 48249
server: resume.batch ... messages=[48251..48310]
client: cursor -> 48310, but buffer still holds a gap at 48250
        -> repair fires again in 500 ms
        -> and again
        -> and again
resume requests in 60 s: 47
then: {"type":"error","data":{"code":"rate_limited","retry_after_ms":9600}}
room appears frozen
```
✅ **The single most consequential line in the client**, and the reason Module 10
insisted that `to_seq` means *"this batch covers everything up to and including"*
rather than *"the last message here"*. Read specs carefully.

### D3. Prove the double-render bug, then fix it

Comment out the upsert in `commit()` and use `this.messages.set(String(m.id), …)`:

```
you type "hello"
  -> optimistic bubble under key 01JQ8Z…  (client_id)
  -> message.new arrives, keyed by id 7241938472948572160
  -> TWO BUBBLES
```
**Expected in the UI:** every message you send appears twice, permanently.

✅ This is the bug every chat client has shipped at least once. §3.1 exists to
make it fixable: `message.new` goes to every member **including the sender**, and
it echoes `client_id` precisely so the sender can recognize its own bubble.

Restore the upsert. Then prove the *other* half — that ack and new may arrive in
either order:

```bash
curl -XPOST localhost:8000/api/debug/delay-ack -d '{"room":"room.general","ms":800}'
```
**Expected:**
```
t+12ms   message.new  (client_id 01JQ8Z…)  -> upsert, state stays 'pending'
t+812ms  message.ack  (client_id 01JQ8Z…)  -> id and seq recorded, state 'sent'
bubbles rendered: 1
```
✅ One bubble, in either order, because reconciliation is keyed on `client_id`
and never on arrival order — which §3.1 requires in as many words.

---

## Part E — Multiplexing, and the fallback that proves you read §4

The v1 URL is one socket per room. `connection.ts` opens `/ws/rooms/` and sends
`room.subscribe` per room.

```tsx
conn.join('room.general', 48213);
conn.join('room.random', 9104);
conn.join('room.support', 331);
```
```bash
# Server side
docker exec pulse-redis redis-cli CLIENT LIST | grep -c pulse
```
**Expected:**
```
1
```
✅ **Three rooms, one socket.** At Module 06's ~45 KB per connection, a user in
20 rooms costs 45 KB instead of 900 KB, and one handshake on reconnect instead of
twenty.

Now point the client at a server that does not implement it:

```bash
PULSE_MULTIPLEX=0 uvicorn pulse.asgi:application --port 8001
# and set baseUrl to ws://localhost:8001
```
**Expected in the console:**
```
{"type":"error","room":"room.general","data":{"code":"unknown_type",
 "message":"server does not implement room.subscribe"}}
server does not multiplex; falling back to one socket per room
state: connecting
state: connected
```
✅ The client degraded to v1 automatically. §4's table says `unknown_type` means
"bug or version skew — **do not retry**", and this is what acting on that
actually looks like: not a log line, a design decision.

> **Adding a `type` is a compatible change (§1), so this is still `v: 1`.** What
> makes it *safe* is the fallback, not the compatibility rule. A client that
> assumes its extension exists is a client that breaks on the one node in the
> cluster that has not finished deploying.

---

## Part F — The virtualized list, and what it is worth

```bash
curl -XPOST localhost:8000/api/debug/seed -d '{"room":"room.big","count":50000}'
```

### F1. Naive first, so the number means something

```tsx
{messages.map((m) => <MessageRow key={m.key} m={m} />)}
```

Chrome DevTools → Performance, record a mount and a scroll to the middle:

**Expected:**
```
mount:            1,640 ms
DOM nodes:        487,412
JS heap:          412 MB
scroll:           6 fps
```
Then 300,000 messages:
```
Aw, Snap!  (tab out of memory)
```

### F2. Virtualized

```tsx
const virt = useVirtualizer({
  count: messages.length,
  getScrollElement: () => parentRef.current,
  estimateSize: () => 56,
  overscan: 12,
  getItemKey: (i) => messages[i].key,   // <- the key must be STABLE across
                                         //    prepends, or the cache is garbage
});
```
**Expected:**
```
mount:            41 ms          (40x)
DOM nodes:        1,204          (405x)
JS heap:          34 MB          (12x)
scroll:           60 fps
300,000 messages: 38 MB, 44 ms mount, 60 fps
```
✅ The tab survives 300,000 messages using **less memory than 50,000 unvirtualized
used at rest**.

### F3. The two chat-specific problems the virtualizer does not solve

**Prepending shifts everything down.** Load older history and watch the scroll
position jump:

```tsx
async function loadOlder() {
  const before = parentRef.current!.scrollHeight;
  await store.prepend(await fetchHistory(slug, 50, oldestSeq));
  // Compensate: the content grew ABOVE the viewport, so add the delta.
  parentRef.current!.scrollTop += parentRef.current!.scrollHeight - before;
}
```
**Expected:**
```
without compensation: scroll displacement 2,847 px  (user is thrown to a
                      random point in history)
with compensation:    scroll displacement 0-3 px    (measurement rounding)
```

**Auto-scroll only if they were already at the bottom.**
```tsx
const atBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 80;
if (atBottom) virt.scrollToIndex(messages.length - 1);
```
✅ 80 px of tolerance, not 0. At 0 a user reading one line above the bottom never
auto-scrolls again, and reports it as "new messages don't show up."

---

## Part G — Backpressure, in both directions

### G1. Inbound: React cannot render at 340 Hz

```bash
curl -XPOST localhost:8000/api/debug/firehose -d '{"room":"room.big","rate":340}'
```

Disable the batching in `connection.ts` (call `onFrame` directly from
`onMessage`):
**Expected:**
```
React renders/s:  340
frame rate:       6 fps
main thread:      97% scripting
after 45 s:       closed with 4008 (slow consumer)
```
✅ **The server closed you** — Module 09's registry noticed you stopped draining.
`4008` is *your* fault, and reconnecting at the same rate reproduces it in
seconds. That is why `connection.ts` clears its inbox and logs a warning on
`4008` rather than treating it like `1006`.

Re-enable the `requestAnimationFrame` batch:
**Expected:**
```
React renders/s:  58
frame rate:       60 fps
main thread:      31% scripting
4008 closes:      0
```
✅ **≤60 renders/second regardless of arrival rate.**

> Note the shape: the fix makes the work depend on **time**, not on the number
> of events, so the worst case is bounded. That is exactly Module 11's presence
> aggregation argument, one layer up. A hard bound on the worst case is worth
> more than a large improvement in the average — because the worst case is when
> you get paged.

### G2. Outbound: `bufferedAmount`

```bash
# Chrome DevTools -> Network -> throttling -> "Slow 3G"
# then paste 200 lines into the composer
```
**Expected in the console:**
```
bufferedAmount: 4,192 -> 61,880 -> 198,441 -> 271,006
typing.start dropped (lossy, buffered > 64 KB)
read.upto dropped (may, buffered > 128 KB)
message.create QUEUED to outbox (must, buffered > 256 KB)
```
✅ **The protocol told you which frames were droppable, before anyone needed to
drop them.** §3.2: typing is "explicitly at-most-once and lossy". §3.3: read state
is "a high-water mark, not a per-message receipt", so a later value supersedes an
earlier one and coalescing is free. Frames whose *semantics* allow loss are your
backpressure budget, and Module 05 wrote that budget down.

`message.create` is never dropped — it goes to the outbox.

---

## Part H — The offline outbox, and the drill

### H1. The outbox

```bash
# DevTools -> Network -> Offline
# type three messages
```
**Expected in the UI:** three bubbles with a clock icon, state `queued-offline`.
```js
JSON.parse(localStorage.getItem('pulse:outbox:room.general')).length
// 3
```
Reload the page while still offline, then go online.
**Expected:**
```
outbox restored: 3
flushing at 4/s (under Module 11's 5/s refill)
t+0ms    message.create 01JQ8Z…  -> ack
t+250ms  message.create 01JQ90…  -> ack
t+500ms  message.create 01JQ91…  -> ack
duplicates on the server: 0
```
✅ **Paced, not burst.** Replaying 40 queued messages at once is
indistinguishable from a flood: Module 11's per-user-per-room bucket is 20 burst
and 5/s, so the last 20 get `rate_limited`. Module 21's challenge is exactly this
scenario, and the fix is here rather than there.

Zero duplicates because the outbox stores the **envelope**, `client_id` and all,
so a replay is the same message — not a new one.

### H2. Module 10's drill, in a real browser

The pinned result: **a 2-minute disconnect loses 98 messages without resume, and
0 with.**

```bash
# Keep a second client sending
python 06-load-testing-harness/code/chatter.py --room general --rate 0.8 &

# In the browser: DevTools -> Network -> Offline, wait 120 s, then Online
```
**Expected in the console:**
```
state: reconnecting          (close 1006)
reconnect attempt 1 in 412ms
reconnect attempt 2 in 1,883ms
...
state: connected
room.subscribe room.general from_seq=48213
resume         room.general from_seq=48213
resume.batch   from_seq=48213 to_seq=48311 has_more=false  (98 messages)
cursor -> 48311
sequence_gaps: 0
```
✅ **Ninety-eight messages, zero gaps.** Now break the cursor — comment out
`saveCursor` — and repeat:
```
resume room.general from_seq=0
resume.batch from_seq=0 to_seq=200 has_more=true      (200 messages)
resume from_seq=200 ...                                (× 241 batches)
{"code":"rate_limited","retry_after_ms":9600}
```
✅ A client that forgets its cursor re-downloads **everything**. At 20,000
connections that is a self-inflicted denial of service every time you ship a
frontend change — which is why Module 10 listed durable cursor persistence as a
*condition* of the guarantee rather than a nicety.

### H3. One socket for all tabs

```bash
cp src/lib/pulse-worker.ts public/pulse-worker.js   # after tsc, or use a loader
```
```tsx
const worker = typeof SharedWorker !== 'undefined'
  ? new SharedWorker('/pulse-worker.js', { name: 'pulse' })
  : null;
// FALLBACK IS MANDATORY: no Safari before 16.4, absent in some privacy modes.
```

Open three tabs on three different rooms:
```bash
docker exec pulse-redis redis-cli CLIENT LIST | grep -c pulse
```
**Expected:**
```
1
```
✅ **Three tabs, three rooms, one socket.** Combined with Part E's multiplexing:

| | Sockets per user (20 rooms, 3 tabs) | Server memory @45 KB |
|---|-----------------------------------|---------------------|
| One socket per room, per tab | 60 | 2.7 MB |
| Multiplexed, per tab | 3 | 135 KB |
| **Multiplexed + SharedWorker** | **1** | **45 KB** |

**60×.** At ~40,000 connections per Uvicorn worker process (Module 06) that is the
difference between ~660 and ~40,000 concurrent *users* on one worker.

Now close one tab and confirm the other two keep working:
**Expected:**
```
port closed; refcount room.random 1 -> 0, unsubscribing
state: connected           (in the surviving tabs)
```
✅ Refcounted, not "close on first leave". Read `pulse-worker.ts`'s docstring for
the state split — the delivery cursor moves into the worker (one socket, one
cursor, `max()` on update) and the scroll position, draft text and virtualizer
cache stay per tab.

---

## What you built

- A Next.js client that speaks **exactly** the protocol from Module 05 — every
  frame, every error code, every close code — with the connection outside React
  so Strict Mode cannot double it.
- **Full-jitter reconnect**, measured against fixed and base-plus-jitter, with
  the finding that base-plus *stops improving* as the backoff grows (its band
  stays 1 s wide) while full jitter's peak falls 5× by attempt 3 — and its p50
  is the earliest of the three. Module 18 measures the real thing at
  3,341/s → 214/s.
- Close-code handling that distinguishes "get a new credential" (`4401`) from
  "the network died" (`1006`) from "this is your own fault" (`4008`) from "stop"
  (`4403`) — and `control{drain}` so a deploy costs 214/s instead of 3,341/s.
- Gap detection on the highest **contiguous** seq with a 500 ms debounce
  (1 repair instead of 3), and **`to_seq`** — the one line that steps a client
  over a permanent hole instead of asking for it 47 times a minute.
- Optimistic send with `client_id` reconciliation, proven correct with the ack
  and the broadcast arriving in either order, and `rate_limited` handled as a
  retry rather than a failure.
- Room **multiplexing** as a v1-compatible extension, with the `unknown_type`
  fallback that makes it safe to deploy.
- A virtualized list: **1,640 ms → 41 ms** to mount, 412 MB → 34 MB, 6 fps →
  60 fps, and 300,000 messages that do not crash the tab.
- Backpressure both ways: `bufferedAmount` shedding along the protocol's own
  lossy/high-water-mark lines, and rAF batching that bounds renders at 60/s.
- An offline outbox, replayed **paced** so it does not look like a flood.
- Module 10's two-minute drill in a real browser: **98 messages recovered, 0
  gaps** — and the same drill with a broken cursor, downloading everything.
- A `SharedWorker` holding **one socket for all tabs and all rooms**: 60× fewer
  connections, with the state split written down.

Now do [`challenge.md`](./challenge.md).

Then: [Module 18 — Compose HA & Chaos](../18-compose-ha-and-chaos/).
