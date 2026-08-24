/**
 * apps/pulse-web/src/lib/room-store.ts
 *
 * One instance per room. Owns the four things that make the client half of
 * Pulse's guarantee actually hold:
 *
 *   1. THE CURSOR      -- persisted, and written AFTER the message, never before
 *   2. GAP DETECTION   -- on the highest CONTIGUOUS seq, with a 500 ms debounce
 *   3. DEDUP           -- by seq for delivery, by client_id for reconciliation
 *   4. THE OUTBOX      -- persisted, replayed on reconnect, safe because
 *                         client_id makes a replay idempotent
 *
 * Messages live in a Map keyed by `client_id ?? String(id)` and every write is
 * an UPSERT. An array with push() is the wrong data structure and it is the one
 * everybody reaches for first -- because §3.1 says message.ack and message.new
 * "MAY arrive in either order", so arrival order tells you nothing.
 */

import {
  ClientId, Envelope, ErrorFrame, MessageAck, MessageNew, ResumeBatch, Seq,
  envelope,
} from './protocol';

export type SendState =
  | 'pending' | 'sent' | 'delivered' | 'failed' | 'queued-offline' | 'rate_limited';

export interface UiMessage {
  key: string;                  // client_id ?? String(id) -- the Map key
  client_id?: ClientId;
  id?: number;
  seq?: Seq;
  sender: string;
  body: string;
  ts: number;                   // SERVER clock (§1). Never Date.now().
  state: SendState;
  retryAfterMs?: number;
  reply_to?: number | null;
}

const GAP_DEBOUNCE_MS = 500;    // Module 10 measured both sides of this
const OUTBOX_KEY = (room: string) => `pulse:outbox:${room}`;
const CURSOR_KEY = (room: string) => `pulse:cursor:${room}`;

export class RoomStore {
  /** The highest seq below which there are NO holes. NOT the highest seen. */
  private contiguous: Seq;
  /** Out-of-order arrivals, held until the hole in front of them fills. */
  private buffer = new Map<Seq, MessageNew>();
  private messages = new Map<string, UiMessage>();
  private repairTimer: ReturnType<typeof setTimeout> | null = null;
  private outbox: Envelope[] = [];

  constructor(
    readonly room: string,
    initial: UiMessage[],
    initialSeq: Seq,
    private send: (env: Envelope, priority?: 'must' | 'may' | 'lossy') => boolean,
    private onChange: () => void,
  ) {
    // The server render IS the initial cursor (see the README). Prefer a
    // persisted cursor when it is AHEAD -- the user may have read further in
    // another tab since this page was rendered.
    this.contiguous = Math.max(initialSeq, loadCursor(room));
    for (const m of initial) this.messages.set(m.key, m);
    this.outbox = loadOutbox(room);
  }

  get cursor(): Seq { return this.contiguous; }
  /** Sorted by seq, NOT by arrival. Optimistic bubbles sort last. */
  list(): UiMessage[] {
    return [...this.messages.values()].sort(
      (a, b) => (a.seq ?? Number.MAX_SAFE_INTEGER) - (b.seq ?? Number.MAX_SAFE_INTEGER),
    );
  }

  // =====================================================================
  // Inbound
  // =====================================================================

  handle(env: Envelope): void {
    if (env.room !== this.room) return;
    switch (env.type) {
      case 'message.new':   this.onNew(env.data as MessageNew, env.ts); break;
      case 'message.ack':   this.onAck(env.data as MessageAck); break;
      case 'resume.batch':  this.onResumeBatch(env.data as ResumeBatch, env.ts); break;
      case 'error':         this.onError(env.data as ErrorFrame); break;
      case 'room.subscribed': break;
      default: return;      // §1: clients MUST ignore unknown types.
    }
    this.onChange();
  }

  private onNew(m: MessageNew, ts: number): void {
    if (m.seq <= this.contiguous) return;          // duplicate; drop, silently

    if (m.seq === this.contiguous + 1) {
      this.commit(m, ts);
      this.contiguous = m.seq;
      // Drain whatever the buffer was holding behind this hole.
      while (this.buffer.has(this.contiguous + 1)) {
        const next = this.buffer.get(this.contiguous + 1)!;
        this.buffer.delete(next.seq);
        this.commit(next, ts);
        this.contiguous = next.seq;
      }
      this.persistCursor();
      this.cancelRepair();
      return;
    }

    // A GAP. Buffer and schedule a DEBOUNCED repair.
    //
    // The debounce is not an optimization, it is correctness of a sort. Under
    // load frames routinely arrive tens of ms out of order: different sockets,
    // TCP retransmits, an XAUTOCLAIM redelivering a 30-second-old entry
    // (Module 09). Firing `resume` on every apparent gap converts transient
    // reordering into a request storm aimed at the database, at exactly the
    // moment the system is already struggling -- and Module 11's rl:resume
    // limiter (5 burst, 0.1/s) then freezes the room.
    //
    // Module 10 measured it: 300 ms of reordering -> 0 repairs. 900 ms -> 1.
    // With the debounce at 0, the same 900 ms -> 3.
    this.buffer.set(m.seq, m);
    this.scheduleRepair();
  }

  private commit(m: MessageNew, ts: number): void {
    const key = m.client_id ?? String(m.id);
    const existing = this.messages.get(key);
    // UPSERT. If this is our own message coming back through the fan-out, the
    // optimistic bubble is already here under the same client_id -- we promote
    // it rather than creating a second one. THIS is the double-render bug, and
    // §3.1 echoes client_id in message.new specifically so it is fixable.
    this.messages.set(key, {
      key,
      client_id: m.client_id,
      id: m.id,
      seq: m.seq,
      sender: m.sender,
      body: m.body,
      reply_to: m.reply_to,
      ts,
      state: existing?.state === 'pending' ? 'sent' : (existing?.state ?? 'sent'),
    });
  }

  private onAck(a: MessageAck): void {
    const m = this.messages.get(a.client_id);
    if (!m) return;                 // ack arrived before new; new will upsert
    m.id = a.id;
    m.seq = a.seq;
    m.state = 'sent';
    m.retryAfterMs = undefined;
    this.removeFromOutbox(a.client_id);
    // NOTE: the ack does NOT advance the cursor. `a.seq` is OUR message's seq;
    // there may be other rooms' -- other senders' -- messages between our
    // cursor and it. The cursor advances only through contiguous delivery.
  }

  private onResumeBatch(b: ResumeBatch, ts: number): void {
    for (const m of b.messages) this.onNew(m, ts);

    if (!b.has_more) {
      // THE MOST IMPORTANT LINE IN THIS FILE.
      //
      // to_seq means "this batch covers everything up to and INCLUDING to_seq"
      // -- not "the seq of the last message here". Advancing to
      // b.messages.at(-1).seq instead re-requests the same permanent hole
      // forever: a dead-lettered poison message, or a seq allocated by a
      // process that died before publishing (Module 16 task 4).
      //
      // The server has CONFIRMED nothing will ever fill that hole. Step over it.
      this.contiguous = Math.max(this.contiguous, b.to_seq);
      this.buffer.clear();
      this.persistCursor();
      this.cancelRepair();
    } else {
      // Keep pulling. §3.5: the server truncates and sets has_more.
      this.send(envelope('resume', this.room, { from_seq: this.contiguous }));
    }
  }

  private onError(e: ErrorFrame): void {
    if (!e.client_id) return;       // not about a specific message of ours
    const m = this.messages.get(e.client_id);
    if (!m) return;

    if (e.code === 'rate_limited') {
      // NOT 'failed'. §4: back off by retry_after_ms, then retry with the SAME
      // client_id. Showing this as a red failure teaches the user to retype,
      // which regenerates the client_id, which turns one message into two.
      // A protocol detail becomes a UX decision becomes a data bug.
      m.state = 'rate_limited';
      m.retryAfterMs = e.retry_after_ms ?? 2000;
      setTimeout(() => this.retry(e.client_id!), m.retryAfterMs);
      return;
    }
    m.state = 'failed';
    this.removeFromOutbox(e.client_id);
  }

  // =====================================================================
  // Gap repair
  // =====================================================================

  private scheduleRepair(): void {
    if (this.repairTimer) return;
    this.repairTimer = setTimeout(() => {
      this.repairTimer = null;
      if (this.buffer.size === 0) return;
      this.send(envelope('resume', this.room, { from_seq: this.contiguous }));
    }, GAP_DEBOUNCE_MS);
  }

  private cancelRepair(): void {
    if (this.repairTimer) clearTimeout(this.repairTimer);
    this.repairTimer = null;
  }

  // =====================================================================
  // Outbound: optimistic send, the outbox, retries
  // =====================================================================

  submit(body: string, sender: string, replyTo?: number): void {
    // Generated BEFORE the first attempt, and reused for every retry. §2.
    // Generating it inside the retry path is the classic duplication bug:
    // the server's UNIQUE (room_id, client_id) sees two different keys and
    // stores two messages.
    const clientId = uuidv7();
    const env = envelope('message.create', this.room, {
      client_id: clientId, body, reply_to: replyTo,
    });

    this.messages.set(clientId, {
      key: clientId, client_id: clientId, sender, body,
      ts: Date.now(),        // provisional ONLY; replaced by the server's ts
      state: 'pending', reply_to: replyTo,
    });

    if (!this.send(env, 'must')) {
      this.messages.get(clientId)!.state = 'queued-offline';
      this.outbox.push(env);
      this.persistOutbox();
    }
    this.onChange();
  }

  /** Called on reconnect. Safe to replay because client_id is idempotent. */
  flushOutbox(): void {
    const queued = this.outbox;
    this.outbox = [];
    this.persistOutbox();

    // Paced, NOT in a burst. Module 11's per-user-per-room bucket is 20 burst
    // and 5/s; an outbox of 40 messages replayed at once is indistinguishable
    // from a flood, gets rate_limited, and the retries make it worse. Module
    // 21's challenge is exactly this scenario.
    queued.forEach((env, i) => {
      setTimeout(() => {
        const cid = (env.data as { client_id: string }).client_id;
        if (this.send(env, 'must')) {
          const m = this.messages.get(cid);
          if (m) m.state = 'pending';
          this.onChange();
        } else {
          this.outbox.push(env);
          this.persistOutbox();
        }
      }, i * 250);                       // 4/s -- under the 5/s refill
    });
  }

  retry(clientId: ClientId): void {
    const m = this.messages.get(clientId);
    if (!m || m.state === 'sent' || m.state === 'delivered') return;
    m.state = 'pending';
    // SAME client_id. This is the whole point of §2.
    this.send(envelope('message.create', this.room, {
      client_id: clientId, body: m.body, reply_to: m.reply_to ?? undefined,
    }), 'must');
    this.onChange();
  }

  // =====================================================================
  // Debounced, droppable outbound signals (§3.2, §3.3)
  // =====================================================================

  private lastTyping = 0;
  typing(): void {
    // §3.2: rate limited to 1 per 3 s per room, at-most-once, lossy. The
    // server enforces it too; doing it here as well is what keeps you off the
    // limiter, which returns an error frame you would have to handle.
    const now = Date.now();
    if (now - this.lastTyping < 3000) return;
    this.lastTyping = now;
    this.send(envelope('typing.start', this.room, {}), 'lossy');
  }

  private readTimer: ReturnType<typeof setTimeout> | null = null;
  private pendingRead = 0;
  readUpTo(seq: Seq): void {
    // §3.3: a HIGH-WATER MARK, debounced to at most 1 per 2 s per room. Because
    // a later value supersedes an earlier one, coalescing is free -- send the
    // max, not each one. Module 11 measured the naive version at 97x the
    // traffic.
    this.pendingRead = Math.max(this.pendingRead, seq);
    if (this.readTimer) return;
    this.readTimer = setTimeout(() => {
      this.readTimer = null;
      this.send(envelope('read.upto', this.room, { seq: this.pendingRead }), 'may');
    }, 2000);
  }

  // =====================================================================
  // Persistence
  // =====================================================================

  private persistCursor(): void {
    // WRITE ORDER: the message is already in `this.messages` before we get
    // here. Saving the cursor first and crashing between the two lines loses
    // that message PERMANENTLY -- resume would start after it. Prefer
    // duplicates over gaps, always (Module 10).
    saveCursor(this.room, this.contiguous);
  }

  private persistOutbox(): void {
    try {
      localStorage.setItem(OUTBOX_KEY(this.room), JSON.stringify(this.outbox));
    } catch { /* quota, private mode, policy. Non-fatal: we lose the queue. */ }
  }

  private removeFromOutbox(clientId: ClientId): void {
    const before = this.outbox.length;
    this.outbox = this.outbox.filter(
      (e) => (e.data as { client_id: string }).client_id !== clientId);
    if (this.outbox.length !== before) this.persistOutbox();
  }
}

// ---------------------------------------------------------------------------
// Storage helpers -- every one of these can throw. Safari private mode, quota
// exceeded, and enterprise policy all make setItem throw, on exactly the
// platforms where you have no debugger.
// ---------------------------------------------------------------------------

function saveCursor(room: string, seq: number): void {
  try { localStorage.setItem(CURSOR_KEY(room), String(seq)); }
  catch { /* we re-resume from the server's window next time */ }
}

function loadCursor(room: string): number {
  try { return Number(localStorage.getItem(CURSOR_KEY(room)) ?? 0) || 0; }
  catch { return 0; }
}

function loadOutbox(room: string): Envelope[] {
  try { return JSON.parse(localStorage.getItem(OUTBOX_KEY(room)) ?? '[]'); }
  catch { return []; }
}

// ---------------------------------------------------------------------------
// UUIDv7 — time-ordered, 36 chars, inside §2's 10–64 range.
//
// Hand-rolled rather than a dependency, for the same reason Module 12 chose
// Snowflake over UUIDv4: TIME-ORDERED IDS KEEP INSERTS SEQUENTIAL. This one
// becomes the server's UNIQUE (room_id, client_id) index key, and Module 12
// measured what a random key does to a B-tree: 6.7x slower inserts, 3.5x the
// index. The client's choice of id format is a database performance decision.
// ---------------------------------------------------------------------------

export function uuidv7(): string {
  const ms = Date.now();
  const bytes = new Uint8Array(16);
  crypto.getRandomValues(bytes);

  // 48 bits of big-endian milliseconds
  bytes[0] = (ms / 2 ** 40) & 0xff;
  bytes[1] = (ms / 2 ** 32) & 0xff;
  bytes[2] = (ms / 2 ** 24) & 0xff;
  bytes[3] = (ms / 2 ** 16) & 0xff;
  bytes[4] = (ms / 2 ** 8) & 0xff;
  bytes[5] = ms & 0xff;

  bytes[6] = 0x70 | (bytes[6] & 0x0f);      // version 7
  bytes[8] = 0x80 | (bytes[8] & 0x3f);      // RFC 4122 variant

  const hex = [...bytes].map((b) => b.toString(16).padStart(2, '0')).join('');
  return `${hex.slice(0, 8)}-${hex.slice(8, 12)}-${hex.slice(12, 16)}-` +
         `${hex.slice(16, 20)}-${hex.slice(20)}`;
}
