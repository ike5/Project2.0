/**
 * apps/pulse-web/public/pulse-worker.js  (authored here as TypeScript)
 *
 * A SharedWorker holding ONE Pulse socket for ALL of a user's tabs.
 *
 * WHY IT IS WORTH THE COMPLEXITY
 * ------------------------------
 * Module 06 pinned the cost of an idle WebSocket connection at ~45 KB of
 * application memory plus kernel socket buffers, and ~40,000 connections per
 * Uvicorn worker process before memory pressure. Multiply the two savings:
 *
 *   one socket per room, per tab :  20 rooms x 3 tabs = 60 sockets/user
 *   multiplexed, per tab         :   1 room-mux  x 3 tabs =  3 sockets/user
 *   multiplexed, SharedWorker    :                          1 socket/user
 *
 * 60x. At 40,000 connections per worker process that is the difference between
 * ~660 and ~40,000 concurrent USERS on one worker. It is not a micro-
 * optimization; it is a capacity decision made in the client.
 *
 * THE STATE SPLIT — the part everyone gets wrong
 * ----------------------------------------------
 * IN THE WORKER (shared, one copy):
 *   * the socket, the reconnect state machine, the heartbeat
 *   * the room subscription set
 *   * the DELIVERY cursor per room -- because it describes what the SOCKET has
 *     received, and there is now exactly one socket
 *   * the offline outbox -- one queue, or two tabs replay the same message
 *     twice (harmless, thanks to client_id, but it burns rate-limit budget)
 *
 * IN EACH TAB (per-tab, N copies):
 *   * the rendered message list and scroll position
 *   * the virtualizer's measurement cache
 *   * the composer's draft text
 *   * which room this tab is LOOKING at -- Module 11's viewport subscription
 *     is per tab, because presence traffic is min(room_size, viewport) and the
 *     viewport is a property of a window, not of a user
 *
 * Module 10's challenge drew the line that settles the cursor question:
 * DELIVERY cursors are per-device, READ cursors are per-user. The delivery
 * cursor moves into the worker (one device, one socket). The read cursor
 * (`read.upto`, §3.3) was always a server-side high-water mark, so tabs may
 * both send it and the max wins -- no coordination needed.
 *
 * WHAT A SharedWorker CANNOT DO
 * -----------------------------
 *   * No `requestAnimationFrame`. The batching in connection.ts falls back to
 *     setTimeout(16) -- which is why that fallback exists.
 *   * No `document`, no DOM, no `window`.
 *   * Not available in every browser context (some mobile browsers, some
 *     privacy modes, and no Safari support before 16.4). YOU MUST HAVE A
 *     FALLBACK: `if (typeof SharedWorker === 'undefined')` -> per-tab
 *     connection. Lab Part H builds it.
 *   * It does NOT die when one tab closes. It dies when the LAST port
 *     disconnects -- and only after some browsers' grace period, so a
 *     reconnecting user may find a worker that already holds a live socket.
 *     That is a feature; make sure your code handles "already connected".
 */

/// <reference lib="webworker" />

import { PulseConnection } from './connection';
import { Envelope } from './protocol';

declare const self: SharedWorkerGlobalScope;

// ---------------------------------------------------------------------------
// Messages between tab and worker
// ---------------------------------------------------------------------------

type ToWorker =
  | { t: 'hello'; baseUrl: string }
  | { t: 'join'; room: string; fromSeq: number }
  | { t: 'leave'; room: string }
  | { t: 'cursor'; room: string; seq: number }
  | { t: 'send'; env: Envelope; priority?: 'must' | 'may' | 'lossy' }
  | { t: 'focus'; room: string | null };          // Module 11 viewport, per tab

type FromWorker =
  | { t: 'frame'; env: Envelope }
  | { t: 'state'; state: string }
  | { t: 'sent'; ok: boolean; clientId?: string }
  | { t: 'revoked'; room: string; reason?: string };

// ---------------------------------------------------------------------------
// Worker-global state — ONE copy, shared by every port
// ---------------------------------------------------------------------------

const ports = new Set<MessagePort>();
/** room -> how many tabs want it. A room leaves the socket at zero, not at one
 *  tab closing -- otherwise closing tab A unsubscribes tab B. */
const refcount = new Map<string, number>();
/** The DELIVERY cursor. One socket, one cursor. This is the state that used to
 *  race between tabs in localStorage. */
const cursors = new Map<string, number>();

let conn: PulseConnection | null = null;

function broadcast(msg: FromWorker): void {
  for (const p of ports) {
    try { p.postMessage(msg); }
    catch { ports.delete(p); }            // the tab went away mid-post
  }
}

function ensureConnection(baseUrl: string): PulseConnection {
  if (conn) return conn;
  conn = new PulseConnection({
    baseUrl,
    mintTicket: async () => {
      // Tickets are single-use (§1) and minted over HTTP with the user's
      // session cookie. `credentials: 'include'` is required and is the thing
      // people forget: without it the worker's fetch is anonymous and every
      // reconnect gets 4401, forever, with no visible error.
      const r = await fetch('/api/ws-ticket/', {
        method: 'POST', credentials: 'include',
      });
      if (!r.ok) throw new Error(`ticket mint failed: ${r.status}`);
      return (await r.json()).ticket as string;
    },
    onFrame: (env) => broadcast({ t: 'frame', env }),
    onStateChange: (state) => broadcast({ t: 'state', state }),
    onRoomRevoked: (room, reason) => {
      refcount.delete(room);
      cursors.delete(room);
      broadcast({ t: 'revoked', room, reason });
    },
  });
  void conn.connect();
  return conn;
}

// ---------------------------------------------------------------------------
// Port lifecycle
// ---------------------------------------------------------------------------

self.onconnect = (e: MessageEvent) => {
  const port = e.ports[0];
  ports.add(port);
  port.start();

  port.onmessage = (ev: MessageEvent<ToWorker>) => {
    const msg = ev.data;
    switch (msg.t) {
      case 'hello': {
        const c = ensureConnection(msg.baseUrl);
        // A NEW TAB JOINING AN ALREADY-CONNECTED WORKER gets the current state
        // immediately, rather than waiting for the next state change. Without
        // this the second tab renders a "connecting..." banner over a working
        // socket -- which reads like a bug and is only a missing message.
        port.postMessage({ t: 'state', state: c.state } as FromWorker);
        // Replay the rooms this worker already holds, so the new tab knows
        // where the shared cursor is rather than resuming from its own stale
        // localStorage value.
        for (const [room, seq] of cursors) {
          port.postMessage({
            t: 'frame',
            env: { v: 1, type: 'room.subscribed', room, ts: Date.now(),
                   data: { room, last_seq: seq } },
          } as FromWorker);
        }
        break;
      }

      case 'join': {
        const n = (refcount.get(msg.room) ?? 0) + 1;
        refcount.set(msg.room, n);
        if (n === 1) {
          // First tab to want this room. Use the HIGHER of the tab's cursor
          // and the worker's -- the worker may have been receiving for this
          // room already on behalf of a tab that has since closed.
          const seq = Math.max(msg.fromSeq, cursors.get(msg.room) ?? 0);
          cursors.set(msg.room, seq);
          ensureConnection('').join(msg.room, seq);
        }
        break;
      }

      case 'leave': {
        const n = (refcount.get(msg.room) ?? 1) - 1;
        if (n <= 0) {
          refcount.delete(msg.room);
          conn?.leave(msg.room);
          // The cursor STAYS. The user is likely to come back, and re-joining
          // from a stale cursor costs a resume of everything since.
        } else {
          refcount.set(msg.room, n);
        }
        break;
      }

      case 'cursor': {
        // Monotonic only. Two tabs report cursors for the same room; taking the
        // last write (which is what localStorage did) lets a slow tab drag the
        // shared cursor BACKWARDS, which re-delivers messages the other tab
        // already showed. max() is the whole fix, and it is why this state had
        // to move here.
        const prev = cursors.get(msg.room) ?? 0;
        if (msg.seq > prev) {
          cursors.set(msg.room, msg.seq);
          conn?.setCursor(msg.room, msg.seq);
        }
        break;
      }

      case 'send': {
        const ok = conn?.send(msg.env, msg.priority ?? 'must') ?? false;
        port.postMessage({
          t: 'sent', ok,
          clientId: (msg.env.data as { client_id?: string }).client_id,
        } as FromWorker);
        break;
      }

      case 'focus':
        // Module 11's viewport subscription is PER TAB, because presence
        // traffic is min(room_size, viewport) x changes/s x rooms_visible and
        // "visible" is a property of a window. The worker forwards the union.
        break;
    }
  };

  // There is no reliable per-port 'close' event. Tabs send a leave on
  // `pagehide`; a tab that is killed does not, so refcounts drift upward and a
  // room is never unsubscribed. Reap on a timer: ping every port, drop the ones
  // that do not answer, and recompute.
};

// A dead port throws on postMessage, which is the only reliable signal we get.
setInterval(() => {
  for (const p of [...ports]) {
    try { p.postMessage({ t: 'state', state: conn?.state ?? 'idle' } as FromWorker); }
    catch { ports.delete(p); }
  }
  if (ports.size === 0) {
    // Last tab gone. Close the socket rather than holding a connection for a
    // user who is not there -- at 45 KB each, abandoned worker sockets are a
    // real number on the server side.
    conn?.stop();
    conn = null;
  }
}, 15_000);
