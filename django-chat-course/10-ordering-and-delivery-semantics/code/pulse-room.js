/*
 * apps/pulse/chat/static/chat/pulse-room.js
 *
 * The client half of the guarantee. Module 17 rebuilds this in TypeScript inside
 * a React client with a SharedWorker; this version is deliberately dependency-free
 * so it can be dropped into the Module 04 room template and driven from a browser
 * console or from Node.
 *
 * Four responsibilities, in the order they matter:
 *
 *   1. JOIN BEFORE RESUME.  Live frames must already be arriving (and buffering)
 *      before the resume query runs, or a message published between the query and
 *      the subscription is a permanent hole.
 *   2. CONTIGUITY.          Track the highest contiguous seq; buffer anything
 *      ahead of it; drop anything at or behind it.
 *   3. DEBOUNCED REPAIR.    Never fire a resume on a gap that is 200 ms old.
 *      Transient reordering is normal; a repair storm is not.
 *   4. PERSIST THE CURSOR.  In localStorage, per room, and tolerate it being
 *      unavailable (private mode, storage disabled, quota exceeded).
 */

const REPAIR_DEBOUNCE_MS = 500; // absorbs transient reordering; see lab Part D
const MAX_BUFFER = 2000; // beyond this, stop buffering and resume instead
const READ_DEBOUNCE_MS = 2000; // protocol §3.3 says at most 1 per 2 s per room
const PING_INTERVAL_MS = 10000; // protocol §3.4

export class PulseRoom {
  /**
   * @param {string} roomKey  the composed key, e.g. "room.general" — this is
   *                          simultaneously the group name, the envelope's
   *                          `room` field and the store's room identity.
   * @param {(msg: object) => void} onMessage
   */
  constructor(roomKey, onMessage, opts = {}) {
    this.roomKey = roomKey;
    this.slug = roomKey.replace(/^room\./, "");
    this.onMessage = onMessage;
    this.log = opts.log || console.log.bind(console);

    this.contiguous = this.loadCursor();
    this.buffer = new Map(); // seq -> message data, ahead of contiguous
    this.repairTimer = null;
    this.resuming = false;

    this.pendingRead = 0;
    this.readTimer = null;

    this.attempt = 0;
    this.ws = null;
    this.stats = { delivered: 0, duplicates: 0, repairs: 0, arrivalInversions: 0 };
    this._lastArrival = 0;
  }

  // ---------------------------------------------------------------- cursor

  loadCursor() {
    try {
      return Number(localStorage.getItem(`pulse:cursor:${this.roomKey}`) || 0);
    } catch (e) {
      return 0; // private mode / storage disabled — we just re-resume from 0
    }
  }

  saveCursor() {
    try {
      localStorage.setItem(`pulse:cursor:${this.roomKey}`, String(this.contiguous));
    } catch (e) {
      /* non-fatal; the server clamps and the abandon path bounds the cost */
    }
  }

  // ------------------------------------------------------------- transport

  connect(user) {
    const proto = location.protocol === "https:" ? "wss" : "ws";
    const url = `${proto}://${location.host}/ws/room/${this.slug}/?as=${encodeURIComponent(user)}`;
    // Offer the subprotocol so a v1 server can echo it (protocol preamble).
    this.ws = new WebSocket(url, "pulse.v1");

    this.ws.onopen = () => {
      this.attempt = 0;
      this.log(`[${this.roomKey}] connected`);

      // STEP 1 — join. Live frames start flowing into ingest() immediately.
      this.send({ v: 1, type: "join", room: this.roomKey, data: {} });

      // STEP 2 — only now ask for history. Anything published in between
      // arrives twice, which ingest() drops. The other order loses it.
      this.requestResume();

      this.pingTimer = setInterval(
        () => this.send({ v: 1, type: "ping", room: this.roomKey, data: { ts: Date.now() } }),
        PING_INTERVAL_MS,
      );
    };

    this.ws.onmessage = (ev) => this.onFrame(JSON.parse(ev.data));
    this.ws.onclose = (ev) => this.onClose(ev, user);
  }

  send(obj) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(obj));
    }
  }

  onClose(ev, user) {
    clearInterval(this.pingTimer);

    // 4xxx codes are ours and are meaningful (protocol §4). 1006 means the
    // network died with no close frame, which is the common case.
    if (ev.code === 4401) return this.onNeedsAuth && this.onNeedsAuth();
    if (ev.code === 4403) return this.onRevoked && this.onRevoked();

    // FULL jitter: random() * base, not base + random(). With base + jitter,
    // 10,000 clients all wait at least `base` and then arrive inside a narrow
    // window — you have delayed the herd, not dispersed it. Module 18 measures
    // the difference; Module 11 measures what the herd does to presence.
    const base = Math.min(30000, 1000 * 2 ** this.attempt);
    const delay = Math.random() * base;
    this.attempt += 1;
    this.log(`[${this.roomKey}] closed ${ev.code}; retry ${this.attempt} in ${Math.round(delay)}ms`);
    setTimeout(() => this.connect(user), delay);
  }

  // ----------------------------------------------------------------- frames

  onFrame(env) {
    switch (env.type) {
      case "message.new":
        return this.ingest(env.data);
      case "resume.batch":
        return this.onResumeBatch(env.data);
      case "message.ack":
        return this.onAck && this.onAck(env.data);
      case "error":
        return this.onError && this.onError(env.data);
      case "pong":
        return; // free RTT sample: Date.now() - env.data.ts
      default:
        return; // protocol §1: clients MUST ignore unknown types
    }
  }

  requestResume() {
    if (this.resuming) return; // exactly one in flight
    this.resuming = true;
    this.send({
      v: 1,
      type: "resume",
      room: this.roomKey,
      data: { from_seq: this.contiguous },
    });
  }

  onResumeBatch(batch) {
    this.resuming = false;

    if (batch.abandon) {
      // Too far behind to page over a socket. Drop the cursor, jump to the
      // head, and load a page of history through the REST endpoint instead
      // (DRF CursorPagination — Module 12).
      this.log(`[${this.roomKey}] ${batch.to_seq - this.contiguous} behind; abandoning cursor`);
      this.contiguous = batch.to_seq;
      this.buffer.clear();
      this.saveCursor();
      this.onMessage({ type: "history-reset", to_seq: batch.to_seq });
      return;
    }

    batch.messages.forEach((m) => this.ingest(m));

    if (batch.has_more) {
      this.requestResume(); // keep paging
    } else {
      // THE PERMANENT-GAP STEP. `to_seq` means "this batch covers everything up
      // to and including to_seq", not "the last message I sent you". Advancing
      // to it steps over any sequence number that was allocated but whose entry
      // was dead-lettered — a hole that would otherwise make the gap detector
      // fire forever.
      if (batch.to_seq > this.contiguous) {
        this.contiguous = batch.to_seq;
        this.saveCursor();
      }
      this.drain();
    }
  }

  // ------------------------------------------------------------ contiguity

  ingest(msg) {
    if (msg.seq < this._lastArrival) this.stats.arrivalInversions += 1;
    this._lastArrival = msg.seq;

    if (msg.seq <= this.contiguous) {
      this.stats.duplicates += 1; // expected and harmless — see the README
      return;
    }
    if (this.buffer.has(msg.seq)) {
      this.stats.duplicates += 1;
      return;
    }

    if (msg.seq === this.contiguous + 1) {
      this.deliver(msg);
      this.drain();
    } else {
      if (this.buffer.size >= MAX_BUFFER) {
        // We are so far ahead of `contiguous` that buffering is the wrong tool.
        // Stop hoarding and ask the server for the missing range instead.
        this.buffer.clear();
        this.requestResume();
        return;
      }
      this.buffer.set(msg.seq, msg);
      this.scheduleRepair();
    }
  }

  deliver(msg) {
    this.onMessage(msg);
    this.contiguous = msg.seq;
    this.stats.delivered += 1;
    this.saveCursor();
  }

  drain() {
    for (;;) {
      const next = this.contiguous + 1;
      if (!this.buffer.has(next)) break;
      const m = this.buffer.get(next);
      this.buffer.delete(next);
      this.deliver(m);
    }
    if (this.buffer.size === 0 && this.repairTimer) {
      clearTimeout(this.repairTimer);
      this.repairTimer = null;
    }
  }

  /*
   * DEBOUNCED, and the debounce is the point. Frames routinely arrive tens of
   * milliseconds out of order under load; an XAUTOCLAIM redelivery can be 30 s
   * late. Firing a resume on every apparent gap turns transient reordering into
   * a request storm aimed at your database at exactly the moment it is already
   * struggling. Lab Part D measures 0 / 1 / 3 requests at 300 ms, 900 ms and
   * with the debounce disabled.
   */
  scheduleRepair() {
    if (this.repairTimer) return;
    this.repairTimer = setTimeout(() => {
      this.repairTimer = null;
      if (this.buffer.size > 0) {
        this.stats.repairs += 1;
        this.log(`[${this.roomKey}] gap at ${this.contiguous + 1}; repairing`);
        this.requestResume();
      }
    }, REPAIR_DEBOUNCE_MS);
  }

  // --------------------------------------------------------- read receipts

  markRead(seq) {
    this.pendingRead = Math.max(this.pendingRead, seq);
    if (this.readTimer) return;
    this.readTimer = setTimeout(() => {
      this.readTimer = null;
      this.send({
        v: 1,
        type: "read.upto",
        room: this.roomKey,
        data: { seq: this.pendingRead },
      });
    }, READ_DEBOUNCE_MS);
  }
}
