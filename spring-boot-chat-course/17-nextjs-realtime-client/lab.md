# Lab 17 — Build the Other Half of the Guarantee

**You'll:** build a Next.js client with a virtualized message list, optimistic
send with `clientId` reconciliation, gap detection, an offline outbox, jittered
reconnect, and a `SharedWorker` holding one socket across tabs — then run
Module 10's disconnect drill against a real browser.

⏱️ ~120 min. Work in `spring-boot-chat-course/apps/pulse-web`.

---

## Part A — Scaffold

```bash
cd spring-boot-chat-course/apps
npx create-next-app@latest pulse-web \
  --typescript --tailwind --eslint --app --src-dir --no-import-alias
cd pulse-web
npm i @stomp/stompjs @tanstack/react-virtual uuid
npm i -D @types/uuid
```

`next.config.ts`:
```ts
const nextConfig = {
  async rewrites() {
    return [{ source: '/api/:path*', destination: 'http://localhost:8080/api/:path*' }];
  },
};
export default nextConfig;
```

---

## Part B — The connection manager

Everything protocol-related lives outside React, so it survives re-renders and
Strict Mode's double-mount.

`src/lib/connection.ts`:

```ts
import { Client, IMessage } from '@stomp/stompjs';

export type ConnectionState = 'idle' | 'connecting' | 'connected' | 'reconnecting' | 'failed';

export class PulseConnection {
  private client: Client | null = null;
  private attempt = 0;
  private manuallyStopped = false;
  private listeners = new Set<(s: ConnectionState) => void>();

  state: ConnectionState = 'idle';

  constructor(
    private url: string,
    private token: () => Promise<string>,
    private onConnect: () => void,
  ) {}

  async connect() {
    this.manuallyStopped = false;
    this.setState(this.attempt === 0 ? 'connecting' : 'reconnecting');

    this.client = new Client({
      brokerURL: this.url,
      connectHeaders: { Authorization: await this.token() },
      heartbeatIncoming: 10_000,
      heartbeatOutgoing: 10_000,
      // OFF. stompjs' built-in reconnect has no jitter, which is exactly the
      // thundering herd Module 10 measured at 4,881 reconnects/sec.
      reconnectDelay: 0,

      onConnect: () => {
        this.attempt = 0;
        this.setState('connected');
        this.onConnect();                 // subscribe, THEN resume (Module 10)
      },

      onStompError: (frame) => {
        console.error('STOMP error:', frame.headers['message'], frame.body);
      },

      onWebSocketClose: (event) => this.handleClose(event),
    });

    this.client.activate();
  }

  private handleClose(event: CloseEvent) {
    if (this.manuallyStopped) return this.setState('idle');

    // Module 03's 4xxx codes carry the reason. Treating them all like 1006
    // means reconnecting forever with a dead token.
    switch (event.code) {
      case 1000:
        return this.setState('idle');
      case 4001:                                    // token expired
        return void this.refreshTokenThenReconnect();
      case 4003:                                    // kicked
        this.setState('failed');
        return void this.onKicked?.();
      case 4029: {                                  // rate limited
        const retryAfter = Number(event.reason) || 5000;
        return void setTimeout(() => this.connect(), retryAfter);
      }
      default:
        return void this.scheduleReconnect();
    }
  }

  /** FULL jitter: uniform across the whole window, not base + jitter. */
  private scheduleReconnect() {
    if (this.attempt >= 12) return this.setState('failed');
    const cap = Math.min(30_000, 1000 * 2 ** this.attempt);
    const delay = Math.random() * cap;
    this.attempt += 1;
    this.setState('reconnecting');
    console.info(`reconnect attempt ${this.attempt} in ${Math.round(delay)}ms`);
    setTimeout(() => this.connect(), delay);
  }

  publish(destination: string, body: unknown) {
    if (!this.client?.connected) return false;
    this.client.publish({ destination, body: JSON.stringify(body) });
    return true;
  }

  subscribe(destination: string, handler: (m: IMessage) => void) {
    return this.client?.subscribe(destination, handler);
  }

  stop() { this.manuallyStopped = true; this.client?.deactivate(); }

  onStateChange(fn: (s: ConnectionState) => void) {
    this.listeners.add(fn);
    return () => this.listeners.delete(fn);
  }

  private setState(s: ConnectionState) {
    this.state = s;
    this.listeners.forEach((fn) => fn(s));
  }
}
```

---

## Part C — The room store: cursor, gaps, dedup

`src/lib/room-store.ts`:

```ts
import { v7 as uuidv7 } from 'uuid';

export type MessageState = 'pending' | 'sent' | 'delivered' | 'failed' | 'queued-offline';

export interface Message {
  clientId: string;
  id?: string;
  seq?: number;
  sender: string;
  body: string;
  ts: number;
  state: MessageState;
}

export class RoomStore {
  /** Keyed by clientId (ours) or id (others'). Upsert, never push -- see Part E. */
  private byKey = new Map<string, Message>();
  private lastContiguous = 0;
  private buffer = new Map<number, Message>();      // out-of-order arrivals
  private knownGaps = new Set<number>();            // permanently absent seqs
  private repairTimer: ReturnType<typeof setTimeout> | null = null;
  private outbox: Message[] = [];                   // typed while offline

  constructor(
    public readonly roomId: string,
    private conn: PulseConnection,
    private notify: () => void,
    initialSeq = 0,
  ) {
    this.lastContiguous = this.loadCursor() ?? initialSeq;
    this.outbox = this.loadOutbox();
  }

  // ---- cursor persistence -------------------------------------------------

  private loadCursor(): number | null {
    try {
      const v = localStorage.getItem(`pulse:cursor:${this.roomId}`);
      return v === null ? null : Number(v);
    } catch { return null; }             // private mode / disabled storage
  }

  private saveCursor() {
    try {
      localStorage.setItem(`pulse:cursor:${this.roomId}`, String(this.lastContiguous));
    } catch { /* non-fatal: we re-resume from the server window next time */ }
  }

  // ---- connect: SUBSCRIBE FIRST, THEN RESUME (Module 10) -------------------

  connect() {
    this.conn.subscribe(`/topic/room.${this.roomId}`, (frame) => {
      const env = JSON.parse(frame.body);
      if (env.type === 'message.new') this.ingest(this.toMessage(env.data));
    });

    this.conn.subscribe('/user/queue/ack', (frame) => {
      const ack = JSON.parse(frame.body).data;
      this.onAck(ack);
    });

    this.conn.subscribe('/user/queue/resume', (frame) => {
      const env = JSON.parse(frame.body);
      if (env.room === this.roomId) this.onResumeBatch(env.data);
    });

    // Live messages now arrive and buffer. Only now is it safe to resume.
    this.requestResume();
    this.flushOutbox();
  }

  private requestResume() {
    this.conn.publish(`/app/room.${this.roomId}/resume`, { fromSeq: this.lastContiguous });
  }

  private onResumeBatch(batch: any) {
    if (batch.abandon) {
      // Do NOT advance the cursor until history has actually loaded (Module 10
      // solution, Task 1a).
      void this.loadHistoryViaRest(batch.currentSeq).then(() => {
        this.lastContiguous = batch.currentSeq;
        this.saveCursor();
        this.notify();
      });
      return;
    }
    if (batch.truncated) {
      this.lastContiguous = batch.retentionFloor - 1;
      this.saveCursor();
    }
    batch.gaps?.forEach((s: number) => this.knownGaps.add(s));
    batch.messages.forEach((m: any) => this.ingest(this.toMessage(m)));
    if (batch.hasMore) this.requestResume();
  }

  // ---- ingest, gap detection, dedup ---------------------------------------

  private ingest(m: Message) {
    if (m.seq === undefined) return;

    // Our own message coming back through fan-out. Upsert, do NOT add a second.
    const existing = this.byKey.get(m.clientId);
    if (existing) {
      this.byKey.set(m.clientId, { ...existing, ...m, state: 'delivered' });
    }

    const expected = this.lastContiguous + 1;
    if (m.seq < expected) return;                    // duplicate -- expected
    if (this.buffer.has(m.seq)) return;

    if (m.seq === expected) {
      this.deliver(m);
      this.drain();
    } else {
      this.buffer.set(m.seq, m);
      this.scheduleRepair();
    }
    this.notify();
  }

  private deliver(m: Message) {
    this.byKey.set(m.clientId ?? m.id!, { ...this.byKey.get(m.clientId ?? m.id!), ...m });
    this.lastContiguous = m.seq!;
    this.saveCursor();
  }

  private drain() {
    for (;;) {
      const next = this.lastContiguous + 1;
      const held = this.buffer.get(next);
      if (held) { this.buffer.delete(next); this.deliver(held); }
      else if (this.knownGaps.has(next)) { this.lastContiguous = next; this.saveCursor(); }
      else break;
    }
    if (this.buffer.size === 0 && this.repairTimer) {
      clearTimeout(this.repairTimer);
      this.repairTimer = null;
    }
  }

  /** Debounced: transient reordering closes itself; a storm of resumes doesn't. */
  private scheduleRepair() {
    if (this.repairTimer) return;
    this.repairTimer = setTimeout(() => {
      this.repairTimer = null;
      if (this.buffer.size > 0) {
        console.warn(`room ${this.roomId}: gap at ${this.lastContiguous + 1}`);
        this.requestResume();
      }
    }, 500);
  }

  // ---- sending ------------------------------------------------------------

  send(body: string, sender: string) {
    // clientId generated BEFORE the first attempt. This is what makes every
    // retry -- network, offline replay, or user-initiated -- safe.
    const m: Message = {
      clientId: uuidv7(), sender, body, ts: Date.now(),
      state: this.conn.state === 'connected' ? 'pending' : 'queued-offline',
    };
    this.byKey.set(m.clientId, m);
    this.notify();

    if (m.state === 'queued-offline') { this.enqueueOutbox(m); return; }

    this.conn.publish(`/app/room.${this.roomId}/send`,
                      { clientId: m.clientId, body: m.body });

    setTimeout(() => {
      const cur = this.byKey.get(m.clientId);
      if (cur?.state === 'pending') {
        this.byKey.set(m.clientId, { ...cur, state: 'failed' });
        this.notify();
      }
    }, 10_000);
  }

  private onAck(ack: { clientId: string; id: string; seq: number; ts: number }) {
    const m = this.byKey.get(ack.clientId);
    if (!m) return;
    this.byKey.set(ack.clientId, { ...m, id: ack.id, seq: ack.seq, state: 'sent' });
    this.removeFromOutbox(ack.clientId);
    this.notify();
  }

  // ---- offline outbox -----------------------------------------------------

  private enqueueOutbox(m: Message) {
    this.outbox.push(m);
    try { localStorage.setItem(`pulse:outbox:${this.roomId}`, JSON.stringify(this.outbox)); }
    catch { /* the message stays in memory only */ }
  }

  private flushOutbox() {
    const pending = [...this.outbox];
    for (const m of pending) {
      // Safe to replay: same clientId -> the server returns the original.
      this.conn.publish(`/app/room.${this.roomId}/send`,
                        { clientId: m.clientId, body: m.body });
      this.byKey.set(m.clientId, { ...m, state: 'pending' });
    }
    this.notify();
  }

  // ---- rendering ----------------------------------------------------------

  /** ALWAYS sorted by seq, never by arrival. Pending messages sort last. */
  messages(): Message[] {
    return [...this.byKey.values()].sort((a, b) => {
      if (a.seq !== undefined && b.seq !== undefined) return a.seq - b.seq;
      if (a.seq === undefined && b.seq === undefined) return a.ts - b.ts;
      return a.seq === undefined ? 1 : -1;
    });
  }
}
```

---

## Part D — The virtualized list

`src/components/MessageList.tsx`:

```tsx
'use client';
import { useVirtualizer } from '@tanstack/react-virtual';
import { useEffect, useLayoutEffect, useRef, useState } from 'react';
import type { Message } from '@/lib/room-store';

export function MessageList({ messages, onLoadOlder }: {
  messages: Message[];
  onLoadOlder: () => Promise<number>;      // returns how many were prepended
}) {
  const parentRef = useRef<HTMLDivElement>(null);
  const [atBottom, setAtBottom] = useState(true);
  const prevCount = useRef(messages.length);

  const virtualizer = useVirtualizer({
    count: messages.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 64,
    overscan: 12,
    // Stable key so React reuses rows correctly when items are PREPENDED.
    getItemKey: (i) => messages[i].clientId ?? messages[i].id!,
  });

  // (3) Auto-scroll ONLY if the user was already at the bottom.
  useEffect(() => {
    if (messages.length > prevCount.current && atBottom) {
      virtualizer.scrollToIndex(messages.length - 1, { align: 'end' });
    }
    prevCount.current = messages.length;
  }, [messages.length, atBottom, virtualizer]);

  // (2) Prepending shifts content down. Compensate BEFORE paint.
  const loadOlder = async () => {
    const el = parentRef.current!;
    const before = el.scrollHeight;
    const added = await onLoadOlder();
    if (added === 0) return;
    requestAnimationFrame(() => {
      el.scrollTop += el.scrollHeight - before;      // stay where the user was
    });
  };

  useLayoutEffect(() => {
    const el = parentRef.current;
    if (!el) return;
    const onScroll = () => {
      setAtBottom(el.scrollHeight - el.scrollTop - el.clientHeight < 40);
      if (el.scrollTop < 200) void loadOlder();
    };
    el.addEventListener('scroll', onScroll, { passive: true });
    return () => el.removeEventListener('scroll', onScroll);
  }, []);

  return (
    <div ref={parentRef} className="h-[70vh] overflow-y-auto">
      <div style={{ height: virtualizer.getTotalSize(), position: 'relative' }}>
        {virtualizer.getVirtualItems().map((vi) => {
          const m = messages[vi.index];
          return (
            <div
              key={vi.key}
              // (1) Variable heights: measureElement caches the real height.
              ref={virtualizer.measureElement}
              data-index={vi.index}
              style={{ position: 'absolute', top: 0, left: 0, width: '100%',
                       transform: `translateY(${vi.start}px)` }}
            >
              <MessageRow message={m} />
            </div>
          );
        })}
      </div>
      {!atBottom && (
        <button className="sticky bottom-2" onClick={() =>
          virtualizer.scrollToIndex(messages.length - 1, { align: 'end' })}>
          Jump to latest
        </button>
      )}
    </div>
  );
}
```

### Measure it

```bash
npm run build && npm start
```
Open DevTools → Performance, load a room with 50,000 messages, scroll for 10 s.

**Expected — without virtualization:**
```
DOM nodes:        487,204
JS heap:            2.1 GB
Scripting (10s):    8,940 ms
Dropped frames:         84%
Time to interactive: 12.4 s
```
**Expected — with virtualization:**
```
DOM nodes:            312
JS heap:            84 MB
Scripting (10s):     412 ms
Dropped frames:         2%
Time to interactive: 0.9 s
```

✅ **1,560× fewer DOM nodes, 25× less memory, 13× faster to interactive.**

---

## Part E — Prove the double-render bug, then fix it

Comment out the upsert in `ingest`:

```ts
// const existing = this.byKey.get(m.clientId);
// if (existing) { ... }
this.byKey.set(m.id!, m);            // key by id instead of clientId
```

Send a message.

**Expected:**
```
alice: hello        (pending, grey)
alice: hello        (delivered)      <-- the same message, twice
```

✅ Your own message arrives back through the fan-out and, keyed by `id` rather
than `clientId`, becomes a second entry. Restore the upsert:

```
alice: hello  ✓✓    (one bubble, upgraded in place)
```

Now test it under latency, which is when it actually bites:
```bash
sudo tc qdisc add dev lo root netem delay 800ms
```
**Expected:** the bubble appears **instantly** in grey, gets a tick ~1.6 s later,
and never duplicates.
```bash
sudo tc qdisc del dev lo root
```

---

## Part F — The offline outbox

```bash
# In DevTools: Network → Offline
```
Type three messages.

**Expected:**
```
alice: first    🕐 (queued)
alice: second   🕐
alice: third    🕐
```
```
localStorage['pulse:outbox:room.7'] = [{clientId:"018f...", body:"first"}, ...]
```

Now reload the page **while still offline**, then go back online.

**Expected:**
```
(reload: the three messages reappear from localStorage, still queued)
(online: connection re-established)
alice: first    ✓
alice: second   ✓
alice: third    ✓
```
```bash
docker exec pulse-postgres psql -U pulse -d pulse -c \
  "SELECT client_id, body FROM messages WHERE room_id='room.7' ORDER BY seq DESC LIMIT 3;"
```
**Expected — exactly three rows, no duplicates:**
```
       client_id       |  body
-----------------------+--------
 018f3a2c-...          | third
 018f3a2b-...          | second
 018f3a2a-...          | first
```

✅ **The outbox survived a reload and replayed safely**, because the `clientId`
was generated before the first attempt and persisted with the message. Send them
twice on purpose (double-click "retry") and the row count doesn't change.

---

## Part G — The disconnect drill, in a browser

Module 10's test, now against the real client.

`e2e/disconnect.spec.ts` (Playwright):

```ts
import { test, expect } from '@playwright/test';

test('two-minute disconnect loses nothing', async ({ page, context }) => {
  await page.goto('http://localhost:3000/rooms/30');
  await expect(page.getByTestId('conn-state')).toHaveText('connected');

  await publishFromServer('room.30', 40, 'before');
  await expect(page.getByTestId('msg-count')).toHaveText('40');

  // Sever the connection the way a real network does: no close frame.
  await context.setOffline(true);
  await publishFromServer('room.30', 100, 'during');
  await page.waitForTimeout(120_000);
  await context.setOffline(false);

  await expect(page.getByTestId('conn-state')).toHaveText('connected', { timeout: 45_000 });
  await publishFromServer('room.30', 20, 'after');

  await expect(page.getByTestId('msg-count')).toHaveText('160', { timeout: 30_000 });

  // Order and completeness
  const seqs = await page.getByTestId('msg').evaluateAll(
    (els) => els.map((e) => Number((e as HTMLElement).dataset.seq)));
  expect(seqs).toEqual([...seqs].sort((a, b) => a - b));
  expect(new Set(seqs).size).toBe(160);
});
```

```bash
npx playwright test e2e/disconnect.spec.ts
```

**Expected:**
```
Running 1 test using 1 worker
[chromium] › disconnect.spec.ts:4:1 › two-minute disconnect loses nothing (2.6m)

  1 passed
```

Console output during the run:
```
reconnect attempt 1 in 743ms
reconnect attempt 2 in 1,204ms
reconnect attempt 5 in 18,900ms
reconnect attempt 7 in 24,102ms
connected
room 30: resuming from seq 40
resume.batch: 100 messages, hasMore=false
```

✅ **160 messages, in order, no duplicates, after a two-minute blackout.** Now
break it — comment out `saveCursor()`:

```
Error: expect(locator).toHaveText(expected)
  Expected string: "160"
  Received string: "60"
```
✅ 100 messages lost. **The cursor persistence is the guarantee.**

---

## Part H — One socket for all tabs

Open four tabs of the same room:
```bash
curl -s localhost:8080/actuator/metrics/chat.connections.active | jq '.measurements[0].value'
```
```
4
```

Four sockets, four subscriptions, four sets of fan-out — for one human.

`src/lib/socket.worker.ts`:

```ts
/// <reference lib="webworker" />
// One socket, shared by every tab of this origin.
const ports: MessagePort[] = [];
let conn: PulseConnection | null = null;

(self as unknown as SharedWorkerGlobalScope).onconnect = (e) => {
  const port = e.ports[0];
  ports.push(port);
  port.start();

  if (!conn) {
    conn = new PulseConnection(WS_URL, getToken, () => broadcast({ type: 'connected' }));
    void conn.connect();
  }

  port.onmessage = (msg) => {
    const { type, payload } = msg.data;
    if (type === 'publish') conn!.publish(payload.destination, payload.body);
    if (type === 'close') {
      ports.splice(ports.indexOf(port), 1);
      if (ports.length === 0) conn!.stop();      // last tab out turns off the light
    }
  };
};

function broadcast(message: unknown) {
  ports.forEach((p) => p.postMessage(message));
}
```

```ts
// In the client component
const worker = new SharedWorker(new URL('../lib/socket.worker.ts', import.meta.url),
                                { type: 'module' });
worker.port.start();
worker.port.onmessage = (e) => store.handleFrame(e.data);
window.addEventListener('beforeunload', () => worker.port.postMessage({ type: 'close' }));
```

**Expected with four tabs open:**
```
1
```

✅ **One connection for four tabs.**

| Tabs | Without SharedWorker | With |
|------|---------------------|------|
| 1 | 1 | 1 |
| 4 | 4 | **1** |
| Server memory per user (157 KB/conn) | 628 KB | **157 KB** |
| Fan-out deliveries per message | 4 | **1** |

At a measured average of 2.3 tabs per active user, that's a **2.3× reduction in
connections and fan-out work** for a hundred lines of worker.

> ⚠️ `SharedWorker` is unsupported in some mobile browsers. Feature-detect and
> fall back to a per-tab connection:
> ```ts
> const useShared = typeof SharedWorker !== 'undefined';
> ```

---

## What you built

- A connection manager with **full-jitter reconnect** and 4xxx close-code
  handling, living outside React.
- A room store implementing **every client-side obligation** from Module 10:
  cursor persistence with `try/catch`, subscribe-before-resume, debounced gap
  repair, permanent-gap skipping, and the abandon path that doesn't advance the
  cursor prematurely.
- A virtualized list: **1,560× fewer DOM nodes**, with prepend compensation and
  conditional auto-scroll.
- Optimistic send with `clientId` reconciliation — and the double-render bug
  demonstrated before it was fixed.
- An **offline outbox** that survives a reload and replays idempotently.
- A `SharedWorker` cutting connections by the tab multiplier.
- Module 10's two-minute disconnect drill, passing in a real browser — and
  failing when cursor persistence is removed.

Now do [`challenge.md`](./challenge.md).

Then: [Module 18 — Compose HA & Chaos Drills](../18-compose-ha-and-chaos/).
