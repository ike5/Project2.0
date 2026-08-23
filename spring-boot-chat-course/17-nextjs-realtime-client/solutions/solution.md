# Solutions — Module 17

---

## Task 1 — Four client-side bugs

### Bug 1 — Cursor saved before render (loss on reload)

```ts
// BROKEN
private deliver(m: Message) {
  this.lastContiguous = m.seq!;
  this.saveCursor();                    // saved
  this.byKey.set(m.clientId, m);
  this.notify();                        // ...but the render can still fail
}
```

**Reproduce:** throw inside `MessageRow` for one message shape (a message with a
`replyTo` pointing at a deleted parent, say). React unmounts the subtree; the
cursor is already advanced.

**Symptom:** reload the page — the message is gone forever. Resume starts *after*
it.

**Fix:** advance the cursor only after the message is committed to the store, and
make rendering defensive:
```ts
private deliver(m: Message) {
  this.byKey.set(m.clientId ?? m.id!, m);
  this.lastContiguous = m.seq!;
  this.saveCursor();
}
```
plus an error boundary per row, so one bad message can't take down the list.

> Same principle as Module 09's ack-after-process: **never advance a cursor
> before the work it represents has succeeded.**

### Bug 2 — Two tabs racing the cursor (multi-tab)

**Reproduce:**
```
tab A: room.7 open, reads to seq 500, writes pulse:cursor:room.7 = 500
tab B: room.7 open in background, at seq 300, writes ... = 300
tab A: reload
tab A: resumes from 300, re-downloads 200 messages it already had
```
Worse, in the other order:
```
tab B (stale, at 300) writes 300
tab A (at 500) reloads, resumes from 300  -- 200 duplicate deliveries
```
And the genuinely bad case: tab B is at 500, tab A is at 300, tab B writes last →
**tab A never sees messages 301–500.**

**Symptom:** intermittent missing messages, only with multiple tabs, only after a
reload. Extremely hard to reproduce on demand.

**Fix — monotonic writes, and cross-tab awareness:**
```ts
private saveCursor() {
  try {
    const key = `pulse:cursor:${this.roomId}`;
    const stored = Number(localStorage.getItem(key) ?? 0);
    // NEVER move a cursor backwards. Same GREATEST() logic as the server's
    // read_cursors table (Module 10).
    if (this.lastContiguous > stored) {
      localStorage.setItem(key, String(this.lastContiguous));
    }
  } catch {}
}

// And listen for other tabs advancing it
window.addEventListener('storage', (e) => {
  if (e.key !== `pulse:cursor:${this.roomId}` || !e.newValue) return;
  const other = Number(e.newValue);
  if (other > this.lastContiguous) {
    // Another tab is ahead. We're missing messages -- resume, don't just jump.
    this.requestResume();
  }
});
```

**Verify:**
```
tab A at 500, tab B at 300
tab B saveCursor(300) -> stored is 500, write SKIPPED
tab A reload -> resumes from 500  ✓
```

### Bug 3 — Optimistic bubble never reconciles under latency (latency-only)

```ts
// BROKEN: the ack handler runs before the optimistic message is in the map,
// because setState is async and the map write was inside a React state update.
setMessages(prev => new Map(prev).set(clientId, optimistic));
conn.publish(...);                       // ack can arrive before the state commits
```

**Reproduce:**
```bash
sudo tc qdisc add dev lo root netem delay 5ms          # FAST, not slow
```
With a very fast server, the ack can arrive in the same tick as the optimistic
render. `onAck` looks up `clientId`, finds nothing, and returns.

**Symptom:** the message stays grey ("pending") forever, then flips to "failed"
after the 10-second timeout — even though it was delivered. Only reproduces on a
fast network, which is why it survives testing on a slow laptop.

**Fix:** keep the store outside React state. The lab's `RoomStore` uses a plain
`Map` mutated synchronously, with `notify()` triggering the re-render — so the
write is committed before `publish()` is even called. That's the reason for the
design, and this bug is why.

Also make `onAck` resilient to genuine out-of-order:
```ts
private onAck(ack) {
  const m = this.byKey.get(ack.clientId);
  if (!m) {
    // Ack for something we don't know about: record it so a later ingest
    // can pick it up rather than dropping it.
    this.orphanAcks.set(ack.clientId, ack);
    return;
  }
  ...
}
```

### Bug 4 — `clientId` regenerated on retry (duplication)

```ts
// BROKEN
function retry(message: Message) {
  send(message.body, message.sender);      // generates a NEW clientId
}
```

**Reproduce:** send a message, kill the network before the ack, restore it, click
Retry.

**Symptom:**
```
alice: hello   ✓
alice: hello   ✓        <-- two rows in Postgres, two different client_ids
```

✅ This defeats **the entire idempotency chain** built in Module 05. The server
did everything right; the client handed it two different logical messages.

**Fix:**
```ts
retry(clientId: string) {
  const m = this.byKey.get(clientId);
  if (!m) return;
  this.byKey.set(clientId, { ...m, state: 'pending' });
  // SAME clientId. This is the whole point of generating it before attempt #1.
  this.conn.publish(`/app/room.${this.roomId}/send`,
                    { clientId, body: m.body });
  this.notify();
}
```

**Verify:**
```bash
docker exec pulse-postgres psql -U pulse -d pulse -c \
  "SELECT client_id, count(*) FROM messages WHERE room_id='room.7' GROUP BY 1 HAVING count(*) > 1;"
```
```
(0 rows)
```

> Bugs 1 and 4 are the same mistake in different places: **the client must treat
> `clientId` and the cursor as durable facts about a message, not as
> per-attempt values.**

---

## Task 2 — In-band token refresh

**Server side** — warn before expiry rather than closing:

```java
@Scheduled(fixedRate = 30_000)
public void warnExpiringTokens() {
    sessionRegistry.allSessions().forEach(session -> {
        Instant expiry = session.tokenExpiry();
        Duration remaining = Duration.between(Instant.now(), expiry);

        if (remaining.isNegative()) {
            close(session, 4001, "token_expired");
        } else if (remaining.toMinutes() < 2 && !session.warned()) {
            session.markWarned();
            template.convertAndSendToUser(session.user(), "/queue/control",
                    Envelope.of("control", null, json.valueToTree(
                            new Control("reauth", "token_expiring",
                                        remaining.toMillis()))));
        }
    });
}
```

```java
@MessageMapping("/auth/refresh")
public void refresh(@Payload RefreshRequest request, Principal principal,
                    SimpMessageHeaderAccessor headers) {
    var verified = tokenService.verify(request.token());
    if (!verified.getName().equals(principal.getName()))
        throw new AccessDeniedException("token identity mismatch");

    // Update the session's expiry IN PLACE. The socket is untouched.
    sessionRegistry.updateTokenExpiry(headers.getSessionId(), verified.expiry());
    template.convertAndSendToUser(principal.getName(), "/queue/control",
            Envelope.of("control", null, json.valueToTree(
                    new Control("reauth_ok", null, null))));
}
```

> The identity check matters: without it, a valid token for user B refreshes
> user A's session and the socket silently changes owner.

**Client side:**

```ts
conn.subscribe('/user/queue/control', async (frame) => {
  const c = JSON.parse(frame.body).data;
  if (c.action !== 'reauth') return;

  try {
    const fresh = await refreshToken();                 // HTTP call to /api/auth/refresh
    conn.publish('/app/auth/refresh', { token: fresh });
  } catch (err) {
    // Refresh failed. Do NOT wait to be kicked -- tell the user now, while the
    // socket still works, so they can act.
    onAuthFailure('Your session is expiring. Please sign in again.');
    // Keep the socket alive until the server closes it: messages still flow,
    // and a successful sign-in elsewhere may refresh it.
  }
});
```

**Prove nothing is lost across the refresh:**

```ts
test('token refresh does not drop messages', async ({ page }) => {
  await page.goto('/rooms/70');
  await page.evaluate(() => (window as any).__forceTokenExpiry(90_000)); // 90s

  const before = await countMessages(page);
  await publishFromServer('room.70', 200, 'during-refresh');  // spans the refresh
  await page.waitForTimeout(120_000);

  await expect(page.getByTestId('msg-count')).toHaveText(String(before + 200));
  // Critically: the SAME socket
  expect(await page.evaluate(() => (window as any).__socketGeneration)).toBe(1);
});
```
**Expected:**
```
token refresh does not drop messages (2.1m) PASSED
  socket generation: 1  (never reconnected)
  messages: 200/200
```

**When the refresh fails:**
```
[client] reauth requested, 118s remaining
[client] refresh failed: 401
[client] showing sign-in prompt; socket still open
(118s later)
[server] closing session 4b1e7c39 code=4001 token_expired
[client] close 4001 -> refreshTokenThenReconnect
[client] refresh failed again -> state=failed, no reconnect loop
```
✅ **No infinite reconnect loop**, because 4001 is handled distinctly from 1006.
The user gets ~2 minutes of warning to re-authenticate before anything breaks.

---

## Task 3 — Edits and deletes in a virtualized list

```ts
// The virtualizer caches measured heights by item key. A changed height with
// the same key means stale offsets and a visible jump.
const virtualizer = useVirtualizer({
  count: messages.length,
  getScrollElement: () => parentRef.current,
  estimateSize: () => 64,
  getItemKey: (i) => messages[i].clientId ?? messages[i].id!,
});

// On edit: invalidate that item's cached measurement.
useEffect(() => {
  if (!lastEditedIndex) return;
  virtualizer.resizeItem(lastEditedIndex, undefined);   // force re-measure
}, [lastEditedIndex, virtualizer]);
```

**Measure the displacement.** Instrument it:
```ts
const measureDisplacement = (fn: () => void) => {
  const el = parentRef.current!;
  const anchorEl = el.querySelector('[data-anchor="true"]') as HTMLElement;
  const before = anchorEl.getBoundingClientRect().top;
  fn();
  requestAnimationFrame(() => {
    const after = anchorEl.getBoundingClientRect().top;
    console.log('displacement:', Math.round(after - before), 'px');
  });
};
```

**Expected — naive:**
```
edit a message above the viewport (3 lines -> 1 line):   displacement: -48 px
delete a message above the viewport:                      displacement: -64 px
edit 5 messages above the viewport:                       displacement: -214 px
```
The user is reading and the text slides upward under them.

### The fix: anchor-based scroll compensation

```tsx
function useScrollAnchor(parentRef: RefObject<HTMLDivElement>) {
  const anchor = useRef<{ key: string; offset: number } | null>(null);

  // Before a mutation, remember WHERE the topmost visible item is.
  const capture = useCallback(() => {
    const el = parentRef.current;
    if (!el) return;
    const rows = el.querySelectorAll('[data-msg-key]');
    for (const row of rows) {
      const rect = (row as HTMLElement).getBoundingClientRect();
      if (rect.bottom > el.getBoundingClientRect().top) {
        anchor.current = {
          key: (row as HTMLElement).dataset.msgKey!,
          offset: rect.top - el.getBoundingClientRect().top,
        };
        return;
      }
    }
  }, [parentRef]);

  // After it, restore that item to the same screen position.
  const restore = useCallback(() => {
    const el = parentRef.current;
    if (!el || !anchor.current) return;
    const row = el.querySelector(`[data-msg-key="${anchor.current.key}"]`) as HTMLElement;
    if (!row) return;
    const now = row.getBoundingClientRect().top - el.getBoundingClientRect().top;
    el.scrollTop += now - anchor.current.offset;
  }, [parentRef]);

  return { capture, restore };
}
```
```tsx
useLayoutEffect(() => { restore(); }, [messages, restore]);
useEffect(() => { capture(); }, [capture]);
```

**Expected after:**
```
edit a message above the viewport:      displacement: 0 px
delete a message above the viewport:    displacement: 0 px
edit 5 messages above the viewport:     displacement: 1 px
prepend 50 older messages:              displacement: 0 px
```

✅ **214 px → 1 px.** Note this also subsumes the prepend compensation from the
lab, which was a special case of the same problem.

> Modern browsers have `overflow-anchor: auto` (CSS scroll anchoring) which does
> this natively — but it is **disabled inside a virtualized container**, because
> absolutely-positioned rows give it nothing to anchor to. You have to do it
> yourself.

---

## Task 4 — Read receipts, driven by visibility

```tsx
function useReadTracking(roomId: string, conn: PulseConnection) {
  const pending = useRef(0);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const dwellTimers = useRef(new Map<number, ReturnType<typeof setTimeout>>());

  const observer = useMemo(() => new IntersectionObserver((entries) => {
    for (const entry of entries) {
      const seq = Number((entry.target as HTMLElement).dataset.seq);
      if (!seq) continue;

      if (entry.isIntersecting) {
        // "Read" means visible for 500ms, not merely scrolled past.
        dwellTimers.current.set(seq, setTimeout(() => {
          pending.current = Math.max(pending.current, seq);
          scheduleFlush();
        }, 500));
      } else {
        clearTimeout(dwellTimers.current.get(seq));
        dwellTimers.current.delete(seq);
      }
    }
  }, { threshold: 0.6 }), []);

  // Debounce: at most one receipt per 2s per room.
  const scheduleFlush = () => {
    if (timer.current) return;
    timer.current = setTimeout(() => {
      timer.current = null;
      if (pending.current > 0) {
        conn.publish(`/app/room.${roomId}/read`, { seq: pending.current });
      }
    }, 2000);
  };

  // Don't lose the last receipt when the tab closes.
  useEffect(() => {
    const flush = () => {
      if (pending.current > 0) {
        navigator.sendBeacon(`/api/rooms/${roomId}/read`,
                             JSON.stringify({ seq: pending.current }));
      }
    };
    document.addEventListener('visibilitychange', () => {
      if (document.hidden) flush();
    });
    window.addEventListener('pagehide', flush);
    return () => { /* cleanup */ };
  }, [roomId]);

  return observer;
}
```

**Measured over 5 minutes of active reading (scrolling through ~400 messages):**

| | Receipts sent |
|---|--------------|
| One per message rendered | **412** |
| One per message actually read (500 ms dwell) | 188 |
| **Debounced 2 s** | **18** |

✅ **23× fewer**, and the user-visible behaviour is identical.

**Prove the server state is still correct:**
```bash
docker exec pulse-postgres psql -U pulse -d pulse -c \
  "SELECT last_read_seq FROM read_cursors WHERE user_id='alice' AND room_id='room.7';"
```
```
 last_read_seq
---------------
           412
```
✅ Exactly the highest seq that was actually read. `GREATEST()` on the server
(Module 10) makes the debounced, possibly-out-of-order receipts converge to the
right value.

**And scroll fast, without dwelling:**
```
scrolled from seq 1 to seq 412 in 1.2 seconds
receipts sent: 1
last_read_seq: 8          <-- only what was genuinely visible for 500ms
```
✅ The dwell requirement prevented marking 400 messages read that nobody looked
at. Without it, "mark all as read" happens by accident every time someone
scrolls.

---

## Task 5 — Client memory

```bash
# DevTools → Memory → Allocation timeline, scroll through 100,000 messages
```

**Expected — naive:**
```
after loading 100,000 messages:  heap 1,840 MB
  byKey Map:                            412 MB   (100,000 Message objects)
  virtualizer measurement cache:         84 MB
  DOM nodes:                             12 MB   (virtualized -- fine)
  DETACHED DOM nodes:                   918 MB   <-- the leak
  IntersectionObserver targets:          61 MB   <-- also a leak
```

Two real leaks:

**1. Detached DOM.** The `IntersectionObserver` from Task 4 holds references to
elements the virtualizer has already unmounted, so they can't be collected.
```ts
// Fix: unobserve on unmount
useEffect(() => {
  const el = rowRef.current;
  if (el) observer.observe(el);
  return () => { if (el) observer.unobserve(el); };   // <-- was missing
}, [observer]);
```
**918 MB → 4 MB.**

**2. Unbounded `byKey`.** Every message ever seen stays in memory forever.

### The bounded window

```ts
export class RoomStore {
  private static readonly WINDOW = 2_000;      // keep in memory
  private static readonly TRIM_TO = 1_500;     // trim down to this

  private trimIfNeeded() {
    if (this.byKey.size <= RoomStore.WINDOW) return;

    const sorted = this.messages();
    const drop = sorted.slice(0, sorted.length - RoomStore.TRIM_TO);

    for (const m of drop) {
      // NEVER drop something that isn't durable yet.
      if (m.state === 'pending' || m.state === 'queued-offline' || m.state === 'failed') continue;
      this.byKey.delete(m.clientId ?? m.id!);
    }
    // Remember where the window starts, so scroll-back knows what to fetch.
    this.windowFloorSeq = this.messages()[0]?.seq ?? 0;
  }

  /** Scroll-back past the window: fetch from the server. */
  async loadOlder(): Promise<number> {
    const res = await fetch(
      `/api/rooms/${this.roomId}/messages?before=${this.windowFloorSeq}&limit=50`);
    const older: Message[] = await res.json();
    older.forEach(m => this.byKey.set(m.id!, m));
    this.windowFloorSeq = older[0]?.seq ?? this.windowFloorSeq;
    this.notify();
    return older.length;
  }
}
```

**Measured:**

| | Unbounded | Bounded (2,000) |
|---|-----------|-----------------|
| Heap after 100,000 messages | 1,840 MB | **112 MB** |
| Heap after leak fixes only | 922 MB | — |
| Heap after both | — | **112 MB** |
| Scroll-back beyond the window | instant | **~80 ms** (one fetch) |
| Time to interactive | 12.4 s | **0.9 s** |
| Mobile Safari (2 GB device) | **crashes** | works |

✅ **16× less memory.** The cost is one HTTP fetch when scrolling past 2,000
messages back — which measured at 80 ms and is indistinguishable from the
virtualizer's own loading behaviour.

> The `state === 'pending'` guard matters: trimming an unsent message would
> silently delete something the user typed. **Never evict data that isn't durable
> somewhere else** — the same rule as Module 13's outbox.

---

## Task 6 (stretch) — Correct worker/tab state split

The lab's version shares a *connection*. Sharing the connection but not the
*state* is worse than not sharing at all, because now N tabs receive every frame
and each independently advances the same `localStorage` cursor.

### The split

| State | Lives in | Why |
|-------|----------|-----|
| WebSocket connection | **worker** | one per browser, obviously |
| Subscriptions | **worker** | subscribing N times gets N copies of every message |
| **Message store (`byKey`)** | **worker** | one canonical copy; tabs render from it |
| **Delivery cursor (`lastContiguous`)** | **worker** | this is per-*device*, and the worker IS the device |
| Gap buffer, known gaps | **worker** | part of the delivery state machine |
| Offline outbox | **worker** | one queue; two tabs must not double-send |
| Scroll position | **tab** | genuinely per-view |
| Virtualizer measurement cache | **tab** | depends on that tab's viewport width |
| "Jump to latest" visibility | **tab** | per-view |
| Draft text | **tab** | per-view |
| Read receipt observer | **tab** | depends on what THAT tab has visible |

**The rule that falls out: protocol state in the worker, view state in the tab.**

```ts
// socket.worker.ts
const stores = new Map<string, RoomStore>();     // ONE store per room, shared
const ports: MessagePort[] = [];

self.onconnect = (e) => {
  const port = e.ports[0];
  ports.push(port);
  port.start();

  port.onmessage = ({ data }) => {
    switch (data.type) {
      case 'join': {
        const store = stores.get(data.roomId)
              ?? new RoomStore(data.roomId, conn, () => broadcastSnapshot(data.roomId));
        stores.set(data.roomId, store);
        // Immediately give the new tab the current state.
        port.postMessage({ type: 'snapshot', roomId: data.roomId,
                           messages: store.messages() });
        break;
      }
      case 'send':
        stores.get(data.roomId)?.send(data.body, data.sender);   // ONE outbox
        break;
      case 'read':
        stores.get(data.roomId)?.markRead(data.seq);             // debounced once
        break;
    }
  };
};

function broadcastSnapshot(roomId: string) {
  const messages = stores.get(roomId)!.messages();
  ports.forEach(p => p.postMessage({ type: 'snapshot', roomId, messages }));
}
```

```tsx
// The tab becomes a pure view.
function useSharedRoom(roomId: string) {
  const [messages, setMessages] = useState<Message[]>([]);
  const portRef = useRef<MessagePort>();

  useEffect(() => {
    const worker = new SharedWorker(
      new URL('../lib/socket.worker.ts', import.meta.url), { type: 'module' });
    worker.port.start();
    portRef.current = worker.port;
    worker.port.onmessage = ({ data }) => {
      if (data.type === 'snapshot' && data.roomId === roomId) setMessages(data.messages);
    };
    worker.port.postMessage({ type: 'join', roomId });
    return () => worker.port.postMessage({ type: 'leave', roomId });
  }, [roomId]);

  return {
    messages,
    send: (body: string) => portRef.current?.postMessage({ type: 'send', roomId, body }),
  };
}
```

**No tab touches `localStorage` for the cursor at all.** The worker owns it, and
there is exactly one worker.

### The two-tab test

```ts
test('two tabs share one connection and one cursor', async ({ context }) => {
  const tabA = await context.newPage();
  const tabB = await context.newPage();
  await tabA.goto('/rooms/80');
  await tabB.goto('/rooms/80');

  // ONE server-side connection for two tabs
  expect(await serverConnectionCount()).toBe(1);

  await publishFromServer('room.80', 50, 'shared');
  await expect(tabA.getByTestId('msg-count')).toHaveText('50');
  await expect(tabB.getByTestId('msg-count')).toHaveText('50');

  // A send from tab A appears in tab B, ONCE
  await tabA.getByTestId('composer').fill('from A');
  await tabA.getByTestId('composer').press('Enter');
  await expect(tabB.getByText('from A')).toHaveCount(1);
  await expect(tabA.getByText('from A')).toHaveCount(1);

  // Closing tab A must not disconnect tab B
  await tabA.close();
  await publishFromServer('room.80', 10, 'after-close');
  await expect(tabB.getByTestId('msg-count')).toHaveText('61');
  expect(await serverConnectionCount()).toBe(1);

  // Closing the LAST tab does disconnect
  await tabB.close();
  await waitFor(async () => expect(await serverConnectionCount()).toBe(0));
});
```
**Expected:**
```
two tabs share one connection and one cursor (8.2s) PASSED
```

**Now break it** — give each tab its own `RoomStore` (the lab's version):
```
Error: expect(locator).toHaveCount(expected)
  Expected: 1
  Received: 2
  Locator: tabB.getByText('from A')
```
✅ Two stores means tab B ingests the message twice — once from its own
subscription and once from tab A's — and reconciliation can't help because each
store has its own map.

### Measured

| | Per-tab connection | Shared connection, per-tab store | **Shared connection + store** |
|---|-------------------|----------------------------------|------------------------------|
| Server connections (4 tabs) | 4 | **1** | **1** |
| Client heap (4 tabs) | 448 MB | 448 MB | **136 MB** |
| Duplicate renders | none | **yes** | none |
| Cursor races | yes | **yes** | **none** |
| Fan-out deliveries per message | 4 | 1 | 1 |
| Outbox double-sends | possible | **possible** | none |

> Sharing the connection was the easy half and the less valuable one. **Sharing
> the state is what actually makes multi-tab correct** — and it also cuts client
> memory by 3.3×, because four tabs stop keeping four copies of the same history.
