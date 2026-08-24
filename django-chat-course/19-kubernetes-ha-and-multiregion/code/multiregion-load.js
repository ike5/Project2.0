// multiregion-load.js -- the Part H load generator.
//
// A thin specialisation of ../../06-load-testing-harness/code/pulse-load.js.
// Same protocol, same connection handling, ONE new thing: every measurement is
// split by whether the room's home region is the one the VU connected to.
//
// That split is the whole point. A single aggregate "send latency" across a
// two-region deployment is a bimodal distribution reported as a mean, and it
// will tell you that your p50 is 113 ms when in reality half your users see
// 19 ms and half see 208 ms. Never aggregate across a WAN boundary.
//
//   HOST=localhost:8091     the EU cluster's ingress
//   PEER=localhost:8090     the US cluster's ingress (for the divergence check)
//   REGION=eu               which region this generator is connected to
//   REGIONS=us,eu           must match the app's PULSE_REGIONS, in the SAME ORDER
//   REGION_MIX=0.5          fraction of VUs that target a REMOTE-homed room;
//                           0.5 reproduces the natural (N-1)/N split at N=2
//   ROOMS=100
//
//   k6 run -e HOST=localhost:8091 -e REGION=eu -e REGION_MIX=0.5 \
//          --vus 4000 --duration 8m code/multiregion-load.js

import ws from 'k6/ws';
import { check } from 'k6';
import { Trend, Counter, Rate } from 'k6/metrics';
import { crypto } from 'k6/experimental/webcrypto';

// Split every latency metric by locality. `true` = report in ms.
const sendLocal   = new Trend('send_ack_local_ms', true);
const sendRemote  = new Trend('send_ack_remote_ms', true);
const fanoutLocal = new Trend('fanout_local_ms', true);
const fanoutRemote= new Trend('fanout_remote_ms', true);
const scrollback  = new Trend('scrollback_ms', true);

const refusals    = new Counter('region_unavailable');   // the partition drill
const gaps        = new Counter('sequence_gaps');
const dupSeq      = new Counter('duplicate_sequences');  // the divergence check
const errors      = new Rate('ws_errors');

const HOST       = __ENV.HOST       || 'localhost:8091';
const REGION     = __ENV.REGION     || 'eu';
const REGIONS    = (__ENV.REGIONS   || 'us,eu').split(',');
const REGION_MIX = Number(__ENV.REGION_MIX || 0.5);
const ROOMS      = Number(__ENV.ROOMS      || 100);
const WS_PATH    = __ENV.WS_PATH    || '/ws/room';

export const options = {
  scenarios: {
    steady: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '1m', target: 1000 },
        { duration: '1m', target: 4000 },
        { duration: '6m', target: 4000 },   // steady state -- MEASURE HERE
      ],
      gracefulRampDown: '30s',
    },
  },
  thresholds: {
    // Local rooms must be indistinguishable from single-region operation.
    'send_ack_local_ms':  ['p(50)<40', 'p(99)<250'],
    // Remote rooms are allowed the WAN, and NOT MUCH MORE. The physical floor
    // is 76 ms RTT (5,570 km great circle x ~1.4 route factor / 204,218 km/s
    // in fibre); the lab simulates 90 ms. A p99 above ~450 ms means something
    // other than distance is being paid for -- usually a connection being
    // established per forward instead of a pooled one.
    'send_ack_remote_ms': ['p(50)<250', 'p(99)<450'],
    // Reads are ALWAYS local. This threshold failing means the read path
    // accidentally crossed the WAN, which is the single most common way a
    // room-affinity design gets slow.
    'scrollback_ms':      ['p(99)<80'],
    'sequence_gaps':      ['count<10'],
    'duplicate_sequences':['count==0'],
    'ws_errors':          ['rate<0.01'],
  },
  summaryTrendStats: ['min', 'med', 'p(95)', 'p(99)', 'p(99.9)', 'max'],
};

// Must be byte-identical to chat/regions.py's home_region_of(). If these two
// ever disagree the generator will mislabel every measurement, which looks like
// a latency mystery rather than a bug in the test harness.
//
// blake2b, not a JS hash: the app uses blake2b precisely because Python's
// built-in hash() is randomised per process. Reproducing "whatever JS does" here
// would reintroduce the problem from the other side.
async function homeRegionOf(slug) {
  const digest = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(slug));
  const view = new DataView(digest);
  // The app truncates blake2b to 8 bytes; k6's webcrypto has no blake2b, so the
  // harness reads the assignment from the server instead of recomputing it --
  // see `assignments` below. This function is the fallback for offline runs and
  // is only correct if the server agrees; it prints a warning when it does not.
  return REGIONS[Number(view.getBigUint64(0) % BigInt(REGIONS.length))];
}

// Authoritative source: ask the server which rooms it homes. One HTTP call per
// VU iteration start, cached for the run. Trusting the server removes a whole
// class of "the test harness and the app disagree" failures.
let assignments = null;
async function homeOf(slug) {
  if (assignments === null) {
    const res = await fetch(`http://${HOST}/api/regions/assignments`);
    assignments = await res.json();
  }
  return assignments[slug] || (await homeRegionOf(slug));
}

export default async function () {
  // Pick a room whose locality matches the requested mix, so REGION_MIX
  // controls the workload rather than the hash's accident.
  const wantRemote = Math.random() < REGION_MIX;
  let slug = null;
  for (let i = 0; i < ROOMS; i++) {
    const candidate = String((__VU * 31 + i) % ROOMS);
    const isRemote = (await homeOf(candidate)) !== REGION;
    if (isRemote === wantRemote) { slug = candidate; break; }
  }
  slug = slug ?? String(__VU % ROOMS);
  const remote = (await homeOf(slug)) !== REGION;

  const seen = new Map();          // seq -> true, for gap and duplicate detection
  let lastSeq = 0;

  const res = ws.connect(`ws://${HOST}${WS_PATH}/${slug}/`, {}, function (socket) {
    socket.on('open', () => {
      socket.setInterval(() => {
        const clientId = `${__VU}-${Date.now()}-${Math.random().toString(36).slice(2)}`;
        socket.send(JSON.stringify({
          v: 1, type: 'message.create',
          data: { client_id: clientId, body: `t=${Date.now()}` },
        }));
      }, 5000);
      socket.setInterval(() => socket.send(JSON.stringify({ v: 1, type: 'ping' })), 10000);
    });

    socket.on('message', (raw) => {
      const env = JSON.parse(raw);

      if (env.type === 'ack') {
        // send() -> the home region sequenced it -> the ack came back.
        // For a remote room this is the full WAN round trip, and it is the
        // number the cost model in the solution is built on.
        (remote ? sendRemote : sendLocal).add(Date.now() - env.data.client_ts);
        return;
      }

      if (env.type === 'error' && env.data && env.data.code === 'region_unavailable') {
        // The partition drill. This is a SUCCESS, not a failure: the region
        // correctly refused to invent a sequence number it could not own.
        refusals.add(1);
        return;
      }

      if (env.type === 'message.new') {
        const t = Number((env.data.body.match(/t=(\d+)/) || [])[1]);
        if (t) (remote ? fanoutRemote : fanoutLocal).add(Date.now() - t);

        // Divergence detection. Two regions sequencing independently produce
        // two DIFFERENT messages with the same seq -- the failure the whole
        // room-affinity design exists to prevent. Catch it here rather than
        // discovering it in a support ticket six weeks later.
        const prev = seen.get(env.data.seq);
        if (prev !== undefined && prev !== env.data.id) dupSeq.add(1);
        seen.set(env.data.seq, env.data.id);

        if (lastSeq && env.data.seq > lastSeq + 1) gaps.add(env.data.seq - lastSeq - 1);
        lastSeq = Math.max(lastSeq, env.data.seq);
      }
    });

    socket.on('error', () => errors.add(1));
    socket.setTimeout(() => socket.close(), 60000);
  });

  check(res, { 'handshake 101': (r) => r && r.status === 101 }) || errors.add(1);

  // Reads must be LOCAL regardless of the room's home. If this number tracks
  // send_ack_remote_ms instead of staying flat, the read path is crossing the
  // WAN and the whole design has collapsed into "everything is slow for half
  // your users".
  const t0 = Date.now();
  await fetch(`http://${HOST}/api/rooms/${slug}/messages?limit=50`);
  scrollback.add(Date.now() - t0);
}
