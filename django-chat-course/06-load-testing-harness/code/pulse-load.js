// pulse-load.js -- the ceiling tool for the whole course.
//
// Speaks the Pulse v1 wire protocol from
// ../../05-protocol-and-domain-design/code/pulse-protocol-v1.md and measures
// the only latency that matters: sender's send() -> a DIFFERENT receiver's
// socket, reported at p50/p95/p99/p99.9.
//
// Modules 07, 09, 15 and 18 run this file unchanged and compare against the
// Module 06 baseline, so its metric names and env contract are frozen:
//
//   HOST=localhost:8000    server address
//   WS_PATH=/ws/room       route prefix; the slug and trailing slash are added
//   ROOMS=100              number of distinct rooms; VUs are spread over them
//   SEND_EVERY=60000       ms between one VU's sends (60000 = 1 msg/user/min)
//   BODY_PAD=40            filler bytes appended to the timestamped body
//
//   k6 run -e ROOMS=100 -e SEND_EVERY=60000 code/pulse-load.js
//   k6 run -e WS_PATH=/ws/async --vus 20000 --duration 4m code/pulse-load.js
//
// Why k6 and not Locust for capacity numbers: k6's `constant-arrival-rate`
// executor starts iterations on a schedule regardless of whether the previous
// one finished, and reports `dropped_iterations` when it cannot. Locust's
// model is closed-loop and will under-report the tail under overload. Both are
// in this module; read the README's coordinated-omission section before you
// quote a number from either.

import ws from 'k6/ws';
import { check } from 'k6';
import { Trend, Counter, Rate, Gauge } from 'k6/metrics';

const fanout   = new Trend('fanout_latency_ms', true);
const received = new Counter('msgs_received');
const sent     = new Counter('msgs_sent');
const gaps     = new Counter('sequence_gaps');
const acks     = new Counter('acks_received');
const errFrames= new Counter('error_frames');
const errors   = new Rate('ws_errors');
const conns    = new Gauge('open_connections');

const HOST       = __ENV.HOST       || 'localhost:8000';
const WS_PATH    = __ENV.WS_PATH    || '/ws/room';
const ROOMS      = Number(__ENV.ROOMS      || 100);
const SEND_EVERY = Number(__ENV.SEND_EVERY || 60000);
const BODY_PAD   = Number(__ENV.BODY_PAD   || 40);

const PAD = 'x'.repeat(BODY_PAD);

export const options = {
  scenarios: {
    ramp: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '1m', target: 2000 },
        { duration: '1m', target: 5000 },
        { duration: '1m', target: 10000 },
        { duration: '1m', target: 20000 },
        { duration: '3m', target: 20000 },   // steady state -- MEASURE HERE
      ],
      gracefulRampDown: '30s',
    },
  },
  thresholds: {
    // Derived from the Module 06 baseline (p50 11 / p95 52 / p99 138 ms) with
    // roughly 2x headroom. A gate that cries wolf gets deleted by the team.
    'fanout_latency_ms': ['p(50)<40', 'p(95)<200', 'p(99)<400'],
    'ws_errors':         ['rate<0.01'],
    'sequence_gaps':     ['count<10'],
    'error_frames':      ['count<10'],
  },
  summaryTrendStats: ['min', 'med', 'p(95)', 'p(99)', 'p(99.9)', 'max'],
  // 20,000 VUs each holding a socket: raise k6's own limits too.
  noConnectionReuse: false,
  discardResponseBodies: true,
};

export default function () {
  // Room slugs are BARE handles (Module 04's shared convention). The group
  // name and the envelope's `room` field are the composed `room.<slug>`; the
  // URL takes the bare slug.
  const slug = String(__VU % ROOMS);
  const user = `u${__VU}`;
  const url  = `ws://${HOST}${WS_PATH}/${slug}/?as=${user}`;

  let lastSeq = 0;
  let counter = 0;

  const res = ws.connect(url, { headers: {} }, function (socket) {

    socket.on('open', () => {
      conns.add(1);

      // OPEN MODEL: fire on a timer, never waiting for a reply. Jitter the
      // first send so 20,000 VUs do not all fire on the same tick -- an
      // unjittered start measures a thundering herd, not a steady state.
      socket.setTimeout(() => {
        socket.setInterval(() => {
          counter += 1;
          // The sender's clock rides INSIDE the body. The protocol's
          // allowlist rejects extra fields on message.create (by design --
          // see pulse-protocol-v1.md section 1), so there is nowhere else to
          // put it, and this is the trick that makes a cross-connection
          // measurement possible at all.
          socket.send(JSON.stringify({
            v: 1,
            type: 'message.create',
            data: {
              client_id: `k6-${__VU}-${counter}-${Date.now()}`,
              body: `t=${Date.now()} ${PAD}`,
            },
          }));
          sent.add(1);
        }, SEND_EVERY);
      }, Math.random() * SEND_EVERY);
    });

    socket.on('message', (raw) => {
      let env;
      try { env = JSON.parse(raw); } catch (e) { return; }

      switch (env.type) {
        case 'message.new': {
          const d = env.data;
          const m = /^t=(\d+)/.exec(d.body || '');
          if (m) fanout.add(Date.now() - Number(m[1]));
          received.add(1);

          // Gap detection, exactly as a real client does it (Module 05's
          // GapDetector). seq is gapless per room; a jump means loss.
          if (lastSeq && d.seq > lastSeq + 1) gaps.add(d.seq - lastSeq - 1);
          if (d.seq > lastSeq) lastSeq = d.seq;
          break;
        }
        case 'message.ack':
          acks.add(1);
          break;
        case 'error':
          // A protocol error is a BUG in this script, not server load. Count
          // it separately so it can never be mistaken for a latency result.
          errFrames.add(1);
          console.error(`error frame: ${env.data.code} ${env.data.message}`);
          break;
        default:
          break;   // hello, presence.update, pong -- not part of the metric
      }
    });

    socket.on('error', (e) => {
      if (e && e.error() !== 'websocket: close sent') errors.add(true);
    });
    socket.on('close', () => conns.add(-1));

    // Hold the socket for the whole test. Without this the VU disconnects the
    // instant the handler returns and you measure connect churn, not chat.
    socket.setTimeout(() => socket.close(), 12 * 60 * 1000);
  });

  check(res, { 'handshake 101': (r) => r && r.status === 101 });
}
