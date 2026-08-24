#!/usr/bin/env node
/**
 * reconnect_sim.mjs — how three backoff strategies distribute N clients'
 * reconnect attempts over time. Pure arithmetic; no network, no server.
 *
 *   node reconnect_sim.mjs --clients 500  --strategy fixed
 *   node reconnect_sim.mjs --clients 500  --strategy base-plus
 *   node reconnect_sim.mjs --clients 500  --strategy full
 *   node reconnect_sim.mjs --clients 20000 --strategy all --attempts 6
 *
 * WHY THIS IS A SIMULATION AND NOT A LOAD TEST
 * --------------------------------------------
 * The peak reconnect rate is a property of the DELAY DISTRIBUTION, not of your
 * network or your server. Simulating it makes the mechanism visible in
 * milliseconds instead of hiding it inside a 20,000-client k6 run -- and it
 * lets you check the 20,000-client number that Module 18 measures against a
 * real cluster without needing the cluster.
 *
 * THE THREE STRATEGIES
 *   fixed       setTimeout(fn, 1000)
 *               Every client returns in the same millisecond. The peak IS the
 *               fleet size.
 *
 *   base-plus   setTimeout(fn, base * 2**attempt + Math.random() * base)
 *               The version people write once they have HEARD of jitter.
 *               Arrivals spread over a FIXED `base`-wide band that slides
 *               later as the attempt grows -- so the band gets NARROWER
 *               relative to the window with every retry, and every client
 *               waits at least the full backoff before it starts.
 *
 *   full        setTimeout(fn, Math.random() * min(cap, base * 2**attempt))
 *               Uniform across the WHOLE window, starting at zero. This is the
 *               property that flattens the peak, and it is why AWS's
 *               "Exponential Backoff and Jitter" post recommends it over the
 *               other two.
 *
 * Module 18 measures the real thing at 20,000 clients: 3,341/s fixed against
 * 214/s full jitter. Run this with --clients 20000 and check it.
 */

const args = Object.fromEntries(
  process.argv.slice(2).flatMap((a, i, all) =>
    a.startsWith('--') ? [[a.slice(2), all[i + 1]]] : []));

const CLIENTS = Number(args.clients ?? 500);
const ATTEMPTS = Number(args.attempts ?? 1);
const BASE_MS = Number(args.base ?? 1000);
const CAP_MS = Number(args.cap ?? 30_000);
const BUCKET_MS = Number(args.bucket ?? 100);

/**
 * One client's delay, in ms, for a given attempt number (0-based).
 * These three functions are the entire subject of this file.
 */
const STRATEGIES = {
  fixed: () => BASE_MS,

  'base-plus': (attempt) =>
    Math.min(CAP_MS, BASE_MS * 2 ** attempt) + Math.random() * BASE_MS,

  full: (attempt) =>
    Math.random() * Math.min(CAP_MS, BASE_MS * 2 ** attempt),
};

/**
 * Simulate one attempt round and return {peakPerSec, peakAtMs, p50, p99}.
 *
 * Note the bucket width: 100 ms by default. PEAK RATE IS BUCKET-WIDTH-DEPENDENT
 * -- a 1 ms bucket reports a higher peak than a 1 s bucket for the same
 * distribution -- and quoting one without the other is how two people benchmark
 * the same backoff and disagree. 100 ms is roughly the granularity at which a
 * server's accept queue and your alerting both care. Change it with --bucket
 * and watch every number move; that is the lesson, not a bug.
 */
function simulate(strategy, attempt) {
  const delays = Array.from({ length: CLIENTS }, () =>
    STRATEGIES[strategy](attempt));

  const buckets = new Map();
  for (const d of delays) {
    const b = Math.floor(d / BUCKET_MS);
    buckets.set(b, (buckets.get(b) ?? 0) + 1);
  }

  let peak = 0;
  let peakBucket = 0;
  for (const [b, n] of buckets) {
    if (n > peak) { peak = n; peakBucket = b; }
  }

  const sorted = delays.sort((a, b) => a - b);
  return {
    peakPerSec: Math.round(peak * (1000 / BUCKET_MS)),
    peakAtMs: peakBucket * BUCKET_MS,
    p50: sorted[Math.floor(CLIENTS * 0.5)],
    p99: sorted[Math.floor(CLIENTS * 0.99)],
    spreadMs: sorted[CLIENTS - 1] - sorted[0],
  };
}

function run(strategy) {
  console.log(`\n${strategy}  (${CLIENTS} clients, base=${BASE_MS}ms, ` +
              `cap=${CAP_MS}ms, ${BUCKET_MS}ms buckets)`);
  for (let attempt = 0; attempt < ATTEMPTS; attempt++) {
    const r = simulate(strategy, attempt);
    console.log(
      `  attempt ${attempt}:  peak ${String(r.peakPerSec).padStart(6)} ` +
      `reconnects/s at t=${(r.peakAtMs / 1000).toFixed(2)}s   ` +
      `p50=${(r.p50 / 1000).toFixed(2)}s  p99=${(r.p99 / 1000).toFixed(2)}s  ` +
      `spread=${(r.spreadMs / 1000).toFixed(2)}s`);
  }
}

const which = args.strategy ?? 'all';
if (which === 'all') {
  for (const s of Object.keys(STRATEGIES)) run(s);
  console.log(`
Read the 'spread' column across attempts. Fixed never spreads at all: every
client is in one bucket, so the peak IS the fleet size divided by the bucket
width. base-plus spreads over a constant ${BASE_MS}ms no matter how far the
backoff has grown, so by attempt 3 it is a 1s band inside an 8s window. Full
jitter spreads over the WHOLE window and starts filling at t=0 -- which is why
its peak is lowest AND its p50 is earliest. The strategy that is kindest to the
server also reconnects half your users sooner. That is a rare thing and it is
worth noticing.

These are DISTRIBUTIONS, not measurements. The peak a real server observes is
also bounded by how fast it can accept -- Module 18 measures 3,341/s against
214/s on the real cluster at 20,000 clients. This tool shows you WHY those two
numbers differ by 15x.`);
} else {
  run(which);
}
