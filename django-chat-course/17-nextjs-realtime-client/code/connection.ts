/**
 * apps/pulse-web/src/lib/connection.ts
 *
 * The Pulse connection manager. Everything protocol-related lives OUTSIDE
 * React, in a plain class, so it survives re-renders and -- critically --
 * Strict Mode's double-mount, which otherwise opens two sockets in development
 * and produces duplicate-message bugs that do not exist in production.
 *
 * Responsibilities, and nothing else:
 *   * one WebSocket, multiplexing N rooms (with a v1-compatible fallback to
 *     one socket per room)
 *   * ticket auth, close-code handling, `control` frames
 *   * FULL-jitter reconnect
 *   * the §3.4 heartbeat
 *   * outbound backpressure via bufferedAmount
 *   * inbound batching to one flush per animation frame
 *
 * It does NOT know about cursors, gaps, dedup or rendering. That is
 * room-store.ts, one instance per room. Keeping the split sharp is what makes
 * the SharedWorker version possible at all (lab Part H).
 */

import {
  CLOSE, ControlFrame, Envelope, ErrorFrame, ERROR_POLICY, envelope,
} from './protocol';

export type ConnectionState =
  | 'idle' | 'connecting' | 'connected' | 'reconnecting' | 'failed';

export interface ConnectionOptions {
  /** e.g. ws://localhost:8000 -- Django/Uvicorn, per apps/README.md */
  baseUrl: string;
  /** POST /api/ws-ticket/ -> a single-use opaque ticket (protocol §1). */
  mintTicket: () => Promise<string>;
  onFrame: (env: Envelope) => void;
  onStateChange?: (s: ConnectionState) => void;
  /** Fired when the server says this room is gone for good (4403 / revoked). */
  onRoomRevoked?: (room: string, reason?: string) => void;
}

const HEARTBEAT_MS = 10_000;          // §3.4
const BACKPRESSURE_BYTES = 256 * 1024;
const MAX_ATTEMPTS = 12;
const MAX_BACKOFF_MS = 30_000;

export class PulseConnection {
  state: ConnectionState = 'idle';

  private ws: WebSocket | null = null;
  private attempt = 0;
  private stopped = false;
  private heartbeat: ReturnType<typeof setInterval> | null = null;
  private lastRttMs = 0;

  /** room -> the from_seq to resume from on (re)connect. */
  private rooms = new Map<string, number>();

  /** Set when the server rejects `room.subscribe` with `unknown_type`. */
  private multiplexSupported = true;

  /** Inbound frames waiting for the next animation frame. */
  private inbox: Envelope[] = [];
  private flushScheduled = false;

  constructor(private opts: ConnectionOptions) {}

  // -- lifecycle --------------------------------------------------------

  async connect(): Promise<void> {
    this.stopped = false;
    this.setState(this.attempt === 0 ? 'connecting' : 'reconnecting');

    let ticket: string;
    try {
      ticket = await this.opts.mintTicket();
    } catch {
      // The ticket endpoint is down, or the session expired. Back off like any
      // other failure rather than hammering /api/ws-ticket/ -- which is the
      // endpoint Module 21 rate-limits hardest, because a reconnect storm hits
      // it before it hits the socket.
      return this.scheduleReconnect();
    }

    const path = this.multiplexSupported ? '/ws/rooms/' : this.singleRoomPath();
    const url = `${this.opts.baseUrl}${path}?ticket=${encodeURIComponent(ticket)}`;

    // The subprotocol is how a v1 server identifies itself (§1). A server that
    // echoes nothing is pre-v1 (Module 04) and MUST be treated as
    // v1-compatible -- so this is a hint, never an assertion.
    this.ws = new WebSocket(url, ['pulse.v1']);
    this.ws.onopen = () => this.onOpen();
    this.ws.onmessage = (e) => this.onMessage(e);
    this.ws.onclose = (e) => this.onClose(e);
    this.ws.onerror = () => { /* onclose always follows; handle it there */ };
  }

  private onOpen(): void {
    this.attempt = 0;
    this.setState('connected');
    this.startHeartbeat();

    // SUBSCRIBE FIRST, THEN RESUME. Module 10's rule, and the one race
    // everybody gets wrong:
    //
    //   wrong: resume -> server queries 101..150 -> 151 is published while we
    //          are not subscribed -> we join -> 152 arrives live.
    //          We hold 101-150 and 152. 151 is a PERMANENT hole that resume
    //          already passed over.
    //
    //   right: subscribe -> 151 arrives live and buffers -> resume returns
    //          101..151 -> we merge and drop the duplicate by seq.
    //
    // Prefer duplicates over gaps, always. Duplicates are removable.
    for (const [room, fromSeq] of this.rooms) {
      this.sendNow(envelope('room.subscribe', room, { from_seq: fromSeq }));
    }
    for (const [room, fromSeq] of this.rooms) {
      this.sendNow(envelope('resume', room, { from_seq: fromSeq }));
    }
  }

  // -- rooms ------------------------------------------------------------

  join(room: string, fromSeq: number): void {
    this.rooms.set(room, fromSeq);
    if (this.state === 'connected') {
      this.sendNow(envelope('room.subscribe', room, { from_seq: fromSeq }));
      this.sendNow(envelope('resume', room, { from_seq: fromSeq }));
    }
  }

  leave(room: string): void {
    this.rooms.delete(room);
    if (this.state === 'connected') {
      this.sendNow(envelope('room.unsubscribe', room, {}));
    }
  }

  /** The store calls this as its cursor advances, so a reconnect resumes right. */
  setCursor(room: string, seq: number): void {
    if (this.rooms.has(room)) this.rooms.set(room, seq);
  }

  private singleRoomPath(): string {
    // Fallback mode: v1's one-socket-per-room URL. A real fallback opens N
    // connections; this class handles one, so the caller creates N instances.
    const first = this.rooms.keys().next().value ?? 'room.general';
    return `/ws/room/${first.replace(/^room\./, '')}/`;
  }

  // -- sending ----------------------------------------------------------

  /**
   * Returns false when the frame was NOT sent, so the caller can queue it.
   *
   * `priority` is the backpressure budget, and the protocol defined it before
   * anyone needed it:
   *   'must'  message.create, room.subscribe, resume -- never dropped
   *   'may'   read.upto      -- a HIGH-WATER MARK (§3.3); a later one
   *                             supersedes an earlier one, so dropping is free
   *   'lossy' typing.start   -- "explicitly at-most-once and lossy" (§3.2)
   */
  send(env: Envelope, priority: 'must' | 'may' | 'lossy' = 'must'): boolean {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) return false;

    // send() NEVER blocks -- it buffers. On a bad network that buffer grows
    // until the tab's memory does, and then the server closes you with 4008
    // for being a slow consumer, which you will misread as a server problem.
    const buffered = this.ws.bufferedAmount;
    if (priority === 'lossy' && buffered > BACKPRESSURE_BYTES / 4) return false;
    if (priority === 'may' && buffered > BACKPRESSURE_BYTES / 2) return false;
    if (priority === 'must' && buffered > BACKPRESSURE_BYTES) return false;

    this.ws.send(JSON.stringify(env));
    return true;
  }

  private sendNow(env: Envelope): void {
    this.ws?.readyState === WebSocket.OPEN && this.ws.send(JSON.stringify(env));
  }

  // -- receiving --------------------------------------------------------

  private onMessage(e: MessageEvent): void {
    let env: Envelope;
    try {
      env = JSON.parse(e.data as string);
    } catch {
      return;                            // §1: be liberal. Drop, do not throw.
    }

    // Frames the CONNECTION owns are handled synchronously; everything else is
    // batched for React. Handling `control` on the next animation frame would
    // delay a drain by up to 16 ms for no reason, and would let a `reauth`
    // race the socket close.
    switch (env.type) {
      case 'pong':
        this.lastRttMs = Date.now() - ((env.data as { ts: number }).ts ?? 0);
        return;
      case 'control':
        return this.onControl(env as Envelope<ControlFrame>);
      case 'error':
        this.onError(env as Envelope<ErrorFrame>);
        break;                           // ALSO forward it: the store must mark
                                         // the right bubble failed.
      default:
        break;                           // §1: unknown types fall through and
                                         // are ignored by the store's default.
    }

    this.inbox.push(env);
    if (!this.flushScheduled) {
      this.flushScheduled = true;
      // ONE flush per animation frame. A busy room delivers 340 frames/s; one
      // setState per frame is 340 renders/s, 6 fps, and eventually a 4008
      // close because you stopped draining the socket. Batching bounds renders
      // at 60/s regardless of arrival rate.
      //
      // Same shape as Module 11's presence aggregation: make the work depend
      // on TIME, not on the number of events, so the worst case is bounded.
      const flush = () => {
        this.flushScheduled = false;
        const batch = this.inbox;
        this.inbox = [];
        for (const frame of batch) this.opts.onFrame(frame);
      };
      typeof requestAnimationFrame === 'function'
        ? requestAnimationFrame(flush)
        : setTimeout(flush, 16);         // SharedWorker has no rAF (Part H)
    }
  }

  private onControl(env: Envelope<ControlFrame>): void {
    const { action, reason, retry_after_ms } = env.data;
    switch (action) {
      case 'drain': {
        // Module 18. The server is asking NICELY, before it closes. Reconnect
        // on our own schedule -- FULL jitter across the whole window -- rather
        // than all at once when the node dies. This is the difference between
        // a 214/s and a 3,341/s reconnect peak.
        const cap = retry_after_ms ?? 5_000;
        this.stopped = false;
        this.closeSocket(CLOSE.NORMAL);
        setTimeout(() => this.connect(), Math.random() * cap);
        return;
      }
      case 'reauth':
        // Module 21: re-authenticate IN-BAND, without dropping the socket.
        // Dropping it costs a handshake, an auth check, N group_adds and N
        // resumes -- for every connected client at once, because tokens expire
        // in cohorts.
        void this.opts.mintTicket().then((t) =>
          this.sendNow(envelope('control' as never, env.room, { ticket: t })));
        return;
      case 'revoked':
        this.rooms.delete(env.room);
        this.opts.onRoomRevoked?.(env.room, reason);
        return;
      case 'rate_limited':
        return;                          // the store shows the countdown
      default:
        return;                          // §1: ignore unknown actions
    }
  }

  private onError(env: Envelope<ErrorFrame>): void {
    const { code } = env.data;

    // The multiplexing fallback, and the only place §4's `unknown_type`
    // policy ("do not retry") turns into a design decision rather than a log
    // line: the server is pre-multiplex, so stop asking and reopen per room.
    if (code === 'unknown_type' && this.multiplexSupported) {
      console.warn('server does not multiplex; falling back to one socket per room');
      this.multiplexSupported = false;
      this.closeSocket(CLOSE.NORMAL);
      void this.connect();
      return;
    }

    if (ERROR_POLICY[code as string] === 'bug') {
      // A client bug reported by the server. Retrying reproduces it. This
      // belongs in your error tracker, not in a retry loop.
      console.error('protocol violation from this client:', env.data);
    }
    // NOTE: no close, no reconnect. §4: "An `error` frame MUST NOT close the
    // connection." Answering "too much traffic" with a reconnect is answering
    // it with more traffic.
  }

  // -- closing and reconnecting ----------------------------------------

  private onClose(e: CloseEvent): void {
    this.stopHeartbeat();
    if (this.stopped) return this.setState('idle');

    switch (e.code) {
      case CLOSE.NORMAL:
        return this.setState('idle');

      case CLOSE.UNAUTHENTICATED:
        // Mint a NEW ticket (they are single-use, §1) and reconnect. A client
        // that treats 4401 like 1006 reconnects forever with a dead ticket and
        // never surfaces the real problem.
        this.attempt = 0;
        return void this.connect();

      case CLOSE.FORBIDDEN: {
        // Authorization lost for a room, not for the socket. In multiplexed
        // mode the server SHOULD have sent `error{not_a_member}` instead --
        // but handle the close too, because a v1 single-room server will use
        // it and the client must not loop.
        for (const room of this.rooms.keys()) this.opts.onRoomRevoked?.(room, e.reason);
        this.rooms.clear();
        return this.setState('failed');
      }

      case CLOSE.SLOW_CONSUMER:
        // OUR fault: we stopped draining the socket. Reconnecting at the same
        // rate reproduces it in seconds. Shed work first -- the batching above
        // is the mechanism; here we tell the app to reduce its own load.
        console.warn('closed as a slow consumer (4008); shedding work');
        this.inbox = [];
        return this.scheduleReconnect();

      case CLOSE.ABUSE: {
        // Module 21 decided we are hostile. Reconnecting aggressively confirms
        // it. Start the backoff near its ceiling.
        this.attempt = Math.max(this.attempt, 8);
        return this.scheduleReconnect();
      }

      case CLOSE.TOO_LARGE_TRANSPORT:
      case CLOSE.TOO_LARGE_APP:
        // The frame that caused this must NOT be resent. The outbox drops it
        // and marks the bubble failed; the connection itself is fine.
        console.error('frame too large; dropping it and reconnecting');
        return this.scheduleReconnect();

      default:
        // 1001 (deploy), 1006 (the network died), everything else.
        return this.scheduleReconnect();
    }
  }

  /**
   * FULL jitter: uniform across the WHOLE window.
   *
   *   setTimeout(fn, 1000)                     -> 3,341 reconnects/s (Module 18)
   *   setTimeout(fn, base + random()*1000)     -> barely better; a displaced band
   *   setTimeout(fn, random() * cap)           -> 214 reconnects/s
   *
   * The middle one is what people write after they have heard of jitter. The
   * arrival distribution is still narrow, just moved.
   */
  private scheduleReconnect(): void {
    if (this.attempt >= MAX_ATTEMPTS) return this.setState('failed');
    const cap = Math.min(MAX_BACKOFF_MS, 1000 * 2 ** this.attempt);
    const delay = Math.random() * cap;
    this.attempt += 1;
    this.setState('reconnecting');
    setTimeout(() => void this.connect(), delay);
  }

  stop(): void {
    this.stopped = true;
    this.stopHeartbeat();
    this.closeSocket(CLOSE.NORMAL);
  }

  private closeSocket(code: number): void {
    try { this.ws?.close(code); } catch { /* already closing */ }
    this.ws = null;
  }

  // -- §3.4 heartbeat ---------------------------------------------------

  private startHeartbeat(): void {
    this.stopHeartbeat();
    this.heartbeat = setInterval(() => {
      // Inside a normal DATA frame, not a WebSocket control ping -- §3.4 says
      // so because some proxies strip control frames, and Module 03 showed one
      // doing it. The `ts` echo is a free RTT sample.
      const room = this.rooms.keys().next().value ?? 'room.system';
      this.send(envelope('ping', room, { ts: Date.now() }), 'may');
    }, HEARTBEAT_MS);
  }

  private stopHeartbeat(): void {
    if (this.heartbeat) clearInterval(this.heartbeat);
    this.heartbeat = null;
  }

  get rttMs(): number { return this.lastRttMs; }

  private setState(s: ConnectionState): void {
    this.state = s;
    this.opts.onStateChange?.(s);
  }
}
