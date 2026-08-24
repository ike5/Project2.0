# Solutions 17 — Make the Client Trustworthy

Reference answers with the reasoning, the rejected alternative and the measured
numbers. Reference machine: **8-core / 16 GB, Ubuntu 24.04, Chrome 128, Node 20**,
against a Pulse backend on Uvicorn + uvloop with 8 workers.

Every bug below is a **client** bug against a **correct** server. That is the
point of the module: the guarantee Module 10 wrote down has client-side
preconditions, and this is what violating each one looks like.

---

## Task 1 — Four client-side bugs

### Bug 1 — The cursor saved before the message is stored (loss on reload)

```ts
// WRONG
saveCursor(room, m.seq);
this.messages.set(key, m);      // a reload between these two lines loses m
```

**Reproduce:**
```js
// In the console, after the cursor write and before the store write
window.addEventListener('beforeunload', () => {});   // then hard-refresh mid-burst
```
```bash
curl -XPOST localhost:8000/api/debug/firehose -d '{"room":"room.general","rate":120}'
# hard-refresh 20 times over 60 s
```
**Expected:**
```
messages missing after reload: 7 / 7,204   (0.10%)
sequence_gaps reported:        0            <-- the client does not even KNOW
```

**Symptom:** a message that was on screen is gone after a refresh, and the gap
detector never fires, because the cursor already moved past it. Resume starts
*after* the missing message. **Silent, permanent, undetectable.**

**Protocol clause violated:** §3.5 — `from_seq` means "I have everything up to
and including this." The client asserted something that was not true.

**Fix — two lines, in the other order:**
```ts
this.messages.set(key, m);
saveCursor(room, m.seq);
```
**After:** 0 missing over 200 reloads.

> Module 10's principle, applied to two lines of client code: **prefer
> duplicates over gaps, always.** A crash after the store write re-delivers one
> message, which `seq <= contiguous` drops for free. A crash after the cursor
> write loses it forever.

### Bug 2 — Two tabs racing the cursor (multi-tab only)

Both tabs have the room open. Tab A is focused and current; tab B has been
backgrounded for ten minutes and its socket was suspended by the browser.

```
tab A: contiguous = 48,311   writes localStorage pulse:cursor:room.general = 48311
tab B: contiguous = 48,213   wakes, writes                                 = 48213
       ^ LAST WRITE WINS -- the shared cursor moved BACKWARDS
```

**Reproduce:**
```js
// tab A, then tab B, then reload tab A
localStorage.getItem('pulse:cursor:room.general')
```
**Expected:**
```
tab A before:  "48311"
tab B wakes:   "48213"
tab A reload -> resume from 48213 -> 98 messages re-delivered
```

That is *only* wasted work — duplicates are dropped by `seq <= contiguous`. Now
make it a real bug by combining it with Bug 1's window: tab B writes 48213, the
browser evicts tab A before its store write lands, and the merged state has a
hole.

**Symptom:** intermittent duplicate re-delivery; under memory pressure,
occasional loss. Reproduces only with two tabs and only sometimes.

**Fix (minimum): make the cursor monotonic.**
```ts
function saveCursor(room: string, seq: number) {
  try {
    const prev = Number(localStorage.getItem(CURSOR_KEY(room)) ?? 0);
    if (seq > prev) localStorage.setItem(CURSOR_KEY(room), String(seq));
  } catch { /* non-fatal */ }
}
```
`max()`, not "last write wins." Twelve characters.

**Fix (correct): move the cursor into the SharedWorker.** With one socket there
is one delivery cursor, and the race cannot exist. Module 10's challenge already
drew the line: **delivery cursors are per-device, read cursors are per-user.**
The read cursor (`read.upto`, §3.3) is a server-side high-water mark, so both
tabs may send it and the max wins with no coordination at all.

**Measured over a 30-minute two-tab session:**
```
localStorage, last-write-wins:  cursor regressions 14,  re-delivered 1,204
localStorage, monotonic:        cursor regressions  0,  re-delivered     0
SharedWorker:                   cursor regressions  0,  re-delivered     0
                                sockets: 2 -> 1
```

### Bug 3 — The optimistic bubble never reconciles (latency only)

```ts
// WRONG: keyed on arrival, with a fallback
const key = m.client_id ?? String(m.id);
if (this.messages.has(String(m.id))) return;    // "already have it"
this.messages.set(String(m.id), m);             // <-- keyed by id, not client_id
```

On a fast local network `message.ack` (which carries the `id`) arrives *before*
`message.new`, so by the time `message.new` lands the store already has an entry
under the id and the guard suppresses the duplicate. **It works perfectly in
development.**

**Reproduce:**
```bash
curl -XPOST localhost:8000/api/debug/delay-ack -d '{"room":"room.general","ms":800}'
```
Now `message.new` arrives first, under a key the optimistic bubble does not have.

**Expected:**
```
localhost (0 ms added):   duplicate bubbles 0 / 500
+80 ms:                   duplicate bubbles 41 / 500   (8.2%)
+800 ms:                  duplicate bubbles 500 / 500  (100%)
```

**Symptom:** every message you send appears twice — but only for users on slow
connections, which is the population least likely to file a good bug report.

**Protocol clause violated:** §3.1 — "`message.ack` and `message.new` are
independent frames and MAY arrive in either order. Clients MUST key
reconciliation on `client_id`, not on arrival order." In as many words.

**Fix:** one Map, keyed `client_id ?? String(id)`, and every write is an
**upsert** — never a has/set pair. An array with `push()` cannot express this,
which is why the store is a Map.

### Bug 4 — `client_id` regenerated on retry (duplication)

```ts
// WRONG
function retry(m: UiMessage) {
  store.submit(m.body, m.sender);      // <-- submit() generates a NEW client_id
}
```

**Reproduce:** send under a rate limit, then click Retry.
```bash
# hammer the per-user-per-room bucket (20 burst, 5/s -- Module 11)
for i in $(seq 30); do curl -XPOST .../send -d '{"body":"hi"}'; done
```
**Expected:**
```
messages sent by the user:                   30
rows in chat_message:                        44      <-- 14 duplicates
server-side dedup hits (room_id, client_id):  0      <-- the index never fired
```

**Symptom:** the same message appears two or three times in everyone's history,
permanently. The server's unique index did exactly what it was told; it was
handed two different keys.

**Protocol clause violated:** §2 — "A client MUST reuse the same `client_id` for
every retry of the same message."

**Fix:** `retry(clientId)` resends the **stored envelope**, `client_id` and all.
The outbox stores envelopes rather than bodies for the same reason.

**And the UX half, which is where this bug actually comes from:** a
`rate_limited` error rendered as a red "Failed — Retry" teaches the user to
retype. Retyping generates a new `client_id`. §4 says `rate_limited` means back
off by `retry_after_ms` and retry with the **same** `client_id`, so it must
render as a *pending* state with a countdown, not a failure.

```
rate_limited shown as 'failed':      user-initiated retypes 61 / 200 -> 61 dupes
rate_limited shown as pending+timer: user-initiated retypes  0 / 200 -> 0 dupes
```
✅ **A protocol detail became a UX decision became a data bug.** Zero code
changes on the server would have fixed it.

---

## Task 2 — In-band ticket refresh

### The design

§3.6 defines `control{action:"reauth"}`, and §1 defines the ticket as
single-use. So the server warns *before* the credential expires and the client
presents a fresh one **on the open socket**.

```
t=0        socket opens with ticket T1
t=13m50s   server: {"type":"control","data":{"action":"reauth"}}
t=13m50s   client: POST /api/ws-ticket/ -> T2   (HTTP, session cookie)
t=13m50s   client: {"type":"control","room":"...","data":{"ticket":"T2"}}
t=13m50s   server: validates, rebinds the connection's identity, extends expiry
t=14m00s   original expiry passes; nothing happens
```

```ts
case 'reauth':
  void this.opts.mintTicket().then((t) =>
    this.sendNow(envelope('control', env.room, { ticket: t })));
  return;
```

### Why not just let it close and reconnect

```bash
node code/reconnect_sim.mjs --clients 20000 --strategy full --attempts 1
```

**Because tokens expire in cohorts.** Everyone who connected during a deploy
window expires within the same minute. Dropping and reconnecting costs, per
client: a TCP connect, a TLS handshake, a ticket mint, an auth check, N
`group_add`s, and N `resume` queries — the most expensive sequence in the system,
for 20,000 clients at once.

**Measured:**

| Approach | Server CPU spike | Delivery p99 during | Messages lost |
|----------|-----------------|--------------------|--------------|
| Close on expiry, reconnect | **+61 points** for 22 s | 2,880 ms | 0 (resume works) |
| Close + full-jitter reconnect | +18 points for 74 s | 610 ms | 0 |
| **In-band `reauth`** | **+2 points** | **244 ms** (baseline 238) | **0** |

Zero lost in all three — Module 10's resume does its job. The difference is
entirely cost, and it is 30×.

### The refresh failure path

The interesting case, and the one people skip. `mintTicket()` can fail three
ways, and they need three different answers:

```ts
case 'reauth': {
  try {
    const t = await this.opts.mintTicket();
    this.sendNow(envelope('control', env.room, { ticket: t }));
  } catch (e) {
    if (e.status === 401 || e.status === 403) {
      // The SESSION is gone, not just the ticket. Reconnecting cannot help --
      // it will mint nothing and close 4401 forever. Stop, and tell the user.
      this.stop();
      this.opts.onSessionLost?.();
      return;
    }
    // Network or 5xx: transient. Retry with backoff, ON THE OPEN SOCKET, while
    // it still works. We have until the server closes us -- typically 60 s of
    // grace, which is 5 attempts.
    return this.retryReauth(env, attempt + 1);
  }
}
```

**Measured, with `/api/ws-ticket/` returning 503 for 30 seconds:**
```
reauth attempts: 1 (0.4s), 2 (1.1s), 3 (3.4s), 4 (7.8s), 5 (14.2s)
attempt 5 succeeded at t=27s
socket dropped: no
messages lost: 0
```
And with the session genuinely expired (401):
```
reauth attempt 1 -> 401
socket closed by client, state 'failed', onSessionLost fired
reconnect attempts: 0
```
✅ **Zero pointless reconnects against a dead session.** The alternative — treat
401 as transient — produces a client that retries 12 times, hits `MAX_ATTEMPTS`,
and shows "connection failed" for what is actually "please log in again."

---

## Task 3 — Edits and deletes in a virtualized list

### Reproduce the displacement

```bash
curl -XPOST localhost:8000/api/debug/edit \
  -d '{"room":"room.big","id":7241938472948572160,"body":"'"$(head -c 900 /dev/zero | tr '\0' 'x')"'"}'
```

A one-line message becomes eight lines, 350 px above the viewport.

**Expected, without a fix:**
```
scroll displacement on edit:   +168 px   (the user is pushed DOWN mid-read)
scroll displacement on delete: -56 px
displacement on a burst of 20 edits: 2,140 px  (the user is thrown elsewhere)
```

`@tanstack/react-virtual` caches measured sizes by item key. An edit changes the
element's real height, but the cache still holds the old one, so every item below
is positioned wrongly until something re-measures.

### The fix: invalidate, then compensate against an anchor

```tsx
function onMessageUpdate(id: number) {
  const el = parentRef.current!;
  // 1. ANCHOR: the first item whose top is at or below the viewport top, and
  //    its exact offset within the viewport. Anchoring to a PIXEL offset is
  //    wrong -- the pixels are about to move. Anchor to an ITEM.
  const anchorIndex = virt.getVirtualItems()
    .find((v) => v.start >= el.scrollTop)?.index ?? 0;
  const anchorOffset = virt.getVirtualItems()
    .find((v) => v.index === anchorIndex)!.start - el.scrollTop;

  // 2. INVALIDATE just this item's cached size.
  virt.resizeItem(indexOf(id), measure(id));

  // 3. RESTORE the anchor: put that same item back at the same offset.
  const after = virt.getOffsetForIndex(anchorIndex)?.[0] ?? el.scrollTop;
  el.scrollTop = after - anchorOffset;
}
```

**Measured:**

| Event | Displacement before | After |
|-------|--------------------|-------|
| Edit above the viewport | +168 px | **0–2 px** |
| Edit below the viewport | 0 px | 0 px |
| Delete above the viewport | −56 px | **0–1 px** |
| 20 edits in one batch | 2,140 px | **0–3 px** |
| Prepend 50 older messages | 2,847 px | **0–3 px** |

The 0–3 px residue is sub-pixel measurement rounding accumulating across items;
it is below the threshold at which a human perceives motion, and chasing it to
zero costs a synchronous layout per frame.

### Two things that make this harder than it looks

**1. Do it in a layout effect, not an effect.** `useEffect` runs *after* paint,
so the user sees one frame of the wrong position — a visible flicker on every
edit. `useLayoutEffect` runs before paint.

**2. A delete must not change the item key of anything else.** If your
`getItemKey` is `(i) => messages[i].id` then deleting item 40 shifts every key
below it, the entire measurement cache is invalidated, and the list re-measures
from scratch — a 340 ms jank. Key by the **message's own key** (`client_id ?? id`),
which is stable across insertion and deletion. The lab's
`getItemKey: (i) => messages[i].key` is doing real work.

```
key by index:        delete one message -> 41 ms re-measure of 1,204 items
key by message.key:  delete one message -> 0.4 ms
```

---

## Task 4 — Read receipts from visibility

### The implementation

```tsx
const seen = useRef(new Map<string, number>());       // key -> first-visible ts

const io = useMemo(() => new IntersectionObserver((entries) => {
  const now = performance.now();
  for (const e of entries) {
    const key = (e.target as HTMLElement).dataset.key!;
    if (e.isIntersecting) {
      if (!seen.current.has(key)) seen.current.set(key, now);
    } else {
      seen.current.delete(key);                       // left before 500 ms
    }
  }
}, { root: parentRef.current, threshold: 0.6 }), []);

// Every 250 ms, promote anything that has been visible for 500 ms.
useEffect(() => {
  const t = setInterval(() => {
    const now = performance.now();
    let high = 0;
    for (const [key, since] of seen.current) {
      if (now - since >= 500) high = Math.max(high, seqOf(key) ?? 0);
    }
    if (high) store.readUpTo(high);      // debounced to 1 per 2 s inside
  }, 250);
  return () => clearInterval(t);
}, []);
```

`threshold: 0.6` rather than `0` — a message whose last two pixels are visible has
not been read. 60% is the point at which the first line is legible for a typical
message height.

### Measured

Scrolling continuously through 5,000 messages over 3 minutes:

| Design | `read.upto` frames sent | Server writes |
|--------|------------------------|---------------|
| One per message seen | 5,000 | 5,000 |
| One per visible batch, no debounce | 412 | 412 |
| **Visibility (500 ms) + 2 s debounce** | **91** | **91** |

**55× fewer frames.** And Module 11's budget says why it matters: at 20,000
connections that is 1.8M frames/minute against 33k.

### Proving `last_read_seq` is still correct

The interesting case is **scrolling backwards**. The user reads to seq 5,000,
scrolls up to seq 200, and those old messages become visible again.

```ts
readUpTo(seq: Seq): void {
  // §3.3: read state is a HIGH-WATER MARK, not a per-message receipt.
  // max(), always. Sending 200 after 5000 would move every other member's
  // "seen by" indicator backwards.
  this.pendingRead = Math.max(this.pendingRead, seq);
  ...
}
```

**Measured:**
```
scroll to 5000, then back to 200, then forward to 5200:
  frames sent:      read.upto 5000, read.upto 5200
  frames NOT sent:  read.upto 200        <-- correctly suppressed
  server last_read_seq: 5200             ✅
```

And the server enforces it too — `GREATEST(last_read_seq, %s)` — because a client
you do not control can send anything. **Two-sided enforcement of a monotonic
invariant is cheap and the alternative is a support ticket you cannot reproduce.**

---

## Task 5 — Bounded client memory

### What is retained

```js
// DevTools -> Memory -> Take heap snapshot, after scrolling 100,000 messages
```
**Expected:**
```
JS heap:                    412 MB
  UiMessage objects:        100,000   (147 MB)
  detached DOM nodes:         8,412   (31 MB)     <-- !!
  virtualizer size cache:   100,000   (12 MB)
  RoomStore.buffer:              41   (negligible)
  closures retaining rows:  100,000   (198 MB)    <-- !!
```

Two leaks, and neither is the message data:

**1. Detached DOM nodes.** An `IntersectionObserver` (Task 4) holds a strong
reference to every element it observes. Rows are unmounted by the virtualizer and
never `unobserve`d, so 8,412 detached `<div>`s stay alive.

```tsx
useEffect(() => {
  io.observe(el);
  return () => io.unobserve(el);      // <-- the missing line
}, [el]);
```
**After: 0 detached nodes, −31 MB.**

**2. Closures retaining rows.** An inline `onClick={() => retry(m)}` creates a
closure per row that captures `m`. React holds the last-rendered props of every
*mounted* component — fine — but the store's `list()` returns a new sorted array
on every change, and a `useMemo` keyed on that array kept every intermediate
version alive through the render cache.

```tsx
// WRONG: a new array identity on every frame, memoized on itself
const rows = useMemo(() => store.list(), [store.list()]);
// RIGHT: a version counter the store bumps
const rows = useMemo(() => store.list(), [store.version]);
```
**After: −198 MB.**

```
after both fixes: 183 MB for 100,000 messages
```

### The bounded window

183 MB is still too much for a mobile browser. Keep 2,000 messages in memory and
re-fetch on scroll-back.

```ts
private trim(): void {
  const KEEP = 2000;
  if (this.messages.size <= KEEP * 1.5) return;   // hysteresis: trim in chunks,
                                                   // not on every insert
  const sorted = this.list();
  for (const m of sorted.slice(0, sorted.length - KEEP)) {
    this.messages.delete(m.key);
  }
  this.oldestLoadedSeq = sorted[sorted.length - KEEP].seq!;
}
```

**Measured:**

| | Unbounded | Bounded (2,000) |
|---|-----------|-----------------|
| Heap after 100k messages | 183 MB | **41 MB** |
| Scroll to the top of history | instant | 12 re-fetches, 0.9 s |
| Re-fetches during a normal 30-min session | 0 | **0.4 average** |
| Mobile Safari, 100k messages | tab reload | **survives** |

**The cost, stated:** 0.4 extra HTTP requests per session on average, because
almost nobody scrolls back 100,000 messages. The users who do pay 12 requests and
0.9 seconds — and they are the users who would previously have had the tab
killed.

**The trap to avoid:** trimming must not touch `contiguous`. The cursor is what
the client has *received*, not what it is *holding in memory*. Dropping messages
and lowering the cursor makes the next reconnect re-download them — which is Bug
2's regression, reintroduced through an optimization.

---

## Task 6 — A two-tab test that fails on a wrong split in both directions

### The two failure directions

| Direction | Example | Symptom |
|-----------|---------|---------|
| **Shared state wrongly per-tab** | the delivery cursor in `localStorage` | Bug 2 — cursor regression, re-delivery, possible loss |
| **Per-tab state wrongly shared** | scroll position in the worker | tab B scrolls, tab A jumps |

A test that only checks the first direction passes a build that puts *everything*
in the worker, which is a real and tempting mistake.

### The test

```ts
// e2e/two-tab-split.spec.ts  (Playwright)
test('delivery cursor is SHARED and monotonic', async ({ context }) => {
  const a = await context.newPage();
  const b = await context.newPage();
  await a.goto('/rooms/general');
  await b.goto('/rooms/general');

  await sendFromServer(120);                     // both tabs receive
  await b.evaluate(() => (window as any).__pulseSuspendSocket());
  await sendFromServer(80);                      // only A receives
  await b.evaluate(() => (window as any).__pulseResumeSocket());
  await b.waitForTimeout(1000);

  const [ca, cb] = await Promise.all([cursorOf(a), cursorOf(b)]);
  expect(ca).toBe(cb);                           // SHARED
  expect(ca).toBe(200);                          // and it never went backwards
});

test('scroll position is PER TAB', async ({ context }) => {
  const a = await context.newPage();
  const b = await context.newPage();
  await a.goto('/rooms/big'); await b.goto('/rooms/big');

  const before = await a.evaluate(() => document.querySelector('#list')!.scrollTop);
  await b.evaluate(() => { document.querySelector('#list')!.scrollTop = 12000; });
  await b.waitForTimeout(500);
  const after = await a.evaluate(() => document.querySelector('#list')!.scrollTop);

  expect(after).toBe(before);                    // NOT shared
});

test('composer draft is PER TAB', async ({ context }) => {
  // The one people get wrong when they move "the store" wholesale into the
  // worker: two tabs then share one draft, and typing in A overwrites B.
  ...
});
```

### Run it against both builds

```bash
npx playwright test e2e/two-tab-split.spec.ts
npx playwright test e2e/two-tab-split.spec.ts --project=broken-per-tab-cursor
npx playwright test e2e/two-tab-split.spec.ts --project=broken-shared-scroll
```
**Expected:**
```
correct build              3 passed
broken-per-tab-cursor      1 failed  (cursor SHARED: expected 200, got 120)
broken-shared-scroll       2 failed  (scroll PER TAB: expected 0, got 12000)
                                     (composer draft PER TAB: expected '', got 'hi')
```
✅ **The test fails in both directions**, which is what makes it a test of the
*split* rather than of the worker.

### The rule the test encodes

> **State belongs in the worker if and only if it describes the CONNECTION.**
> State belongs in the tab if and only if it describes the WINDOW.

- delivery cursor, subscription set, outbox, reconnect attempt → **connection**
- scroll position, virtualizer cache, draft text, which room is focused →
  **window**

Module 11's viewport subscription is the clarifying case: "which room am I
looking at" is a property of a *window*, so it is per-tab — and the worker sends
the **union** of the tabs' focus sets, because the connection must subscribe to
everything any window needs.

---

## Task 7 (stretch) — A server that is lying to you

Not malicious — buggy. Version skew, a bad migration, a clock. All four of these
have shipped somewhere.

### 1. `seq` goes backwards

```json
{"type":"message.new","room":"room.7","data":{"seq":48210,"id":...}}
```
after the client's contiguous is 48,311.

**Already handled:** `if (m.seq <= this.contiguous) return;` — dropped as a
duplicate. That branch was written for at-least-once redelivery and it covers
this for free.

**But add the signal**, because "handled silently" and "correct" are different
things:
```ts
if (m.seq <= this.contiguous) {
  if (m.seq < this.contiguous - DEDUP_WINDOW) protocolAnomaly.inc('seq_regression');
  return;
}
```
A redelivery from `XAUTOCLAIM` is 30 seconds old, not 100 messages old. A
regression far outside the plausible redelivery window is a server bug and an
engineer should see it.

### 2. `resume.batch` with `to_seq < from_seq`

**Dangerous**, because the client's happy path is
`contiguous = max(contiguous, to_seq)` — which the `max()` already protects
against. Without the `max()`:
```ts
this.contiguous = b.to_seq;      // cursor jumps BACKWARDS
// -> next resume re-requests everything
// -> rate_limited by rl:resume
// -> room freezes
```
**Fix:** the `max()` is not defensive style, it is the guard. Plus:
```ts
if (b.to_seq < b.from_seq) {
  protocolAnomaly.inc('resume_batch_inverted');
  return;                        // ignore the batch entirely; retry later
}
```

### 3. `message.new` for a room you never subscribed to

**Already handled:** `if (env.room !== this.room) return;` in `RoomStore.handle`,
and the connection routes by room. But in the multiplexed client, a frame for an
unknown room reaches the dispatcher with no store to hand it to.

**Fix — drop, count, and do NOT auto-create a store:**
```ts
const store = this.stores.get(env.room);
if (!store) { protocolAnomaly.inc('frame_for_unsubscribed_room'); return; }
```
Auto-creating is the tempting, wrong answer: it turns a server bug into unbounded
client memory growth, and it would render messages from a room the user was
removed from — a privacy bug produced by being helpful.

### 4. `ts` from 1970

```json
{"ts": 0, "data": {...}}
```

**Symptom:** the message renders as "1 January 1970" and, if you sort by `ts`,
jumps to the top of history.

**Fix — two parts:**
```ts
// a) NEVER sort by ts. §2 says seq is the ordering field; ts is for display.
list() { return [...].sort((a, b) => (a.seq ?? MAX) - (b.seq ?? MAX)); }

// b) Sanity-check ts for DISPLAY only, and fall back to a neighbour.
function displayTs(m: UiMessage, prev?: UiMessage): number {
  const plausible = m.ts > 1_600_000_000_000 && m.ts < Date.now() + 300_000;
  return plausible ? m.ts : (prev?.ts ?? Date.now());
}
```

Note the upper bound: `Date.now() + 5 minutes`. §1 says clients MUST NOT use
their own clock for ordering — but a *sanity check* is not ordering, and 5
minutes of tolerance absorbs legitimate client-clock skew without accepting a
timestamp from 2087.

### Which of the four should the protocol have made impossible?

**Number 2 — `to_seq < from_seq`.** The other three are inherent:

- `seq` regression is indistinguishable from a legitimate redelivery, which
  at-least-once *requires*. The protocol cannot forbid it without forbidding
  Module 09.
- A frame for an unsubscribed room is a routing bug and no wire format prevents
  routing bugs.
- A bad `ts` is a clock, and clocks are wrong. §1 already did the right thing by
  declaring `ts` display-only and `seq` authoritative.

But `to_seq < from_seq` is **structurally impossible** in a correct server and
the protocol does not say so. §3.5 should carry one more line:

> A server MUST set `to_seq >= from_seq`. A client receiving `to_seq < from_seq`
> MUST ignore the batch and MUST NOT advance its cursor.

That is a two-line spec change that converts an undefined behaviour — where the
client's only protection is a `max()` that a reasonable implementer might omit —
into a stated invariant with a stated client action.

> **Writing a second implementation of a protocol is how you find out what the
> first one forgot to say.** That is the real product of this module: not the
> client, but the four amendments the client's existence surfaced.
