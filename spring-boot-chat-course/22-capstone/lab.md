# Lab 22 — Wire It All Together

**You'll:** assemble the complete stack, pass an acceptance test at target load,
run the full chaos suite *under* that load, and produce the architecture review.

⏱️ ~8+ hours. This is the integration of everything; budget accordingly.

> **Scale to your hardware.** Targets below are for 100,000 connections. If your
> machine can't, use 20,000 with the same room structure and record the scale
> factor. The capstone tests composition, not the absolute number.

---

## Part A — Assemble the stack

Everything is already built across Modules 04–21. The capstone wires it into one
deployment. Use the HA Compose stack (Module 18) or the k8s manifests (Module 19).

```bash
cd spring-boot-chat-course/apps/pulse
./mvnw -DskipTests package
docker build -t pulse:capstone .

cd ../../infra/capstone
docker compose -f compose.capstone.yml up -d --wait
docker compose -f compose.capstone.yml ps --format 'table {{.Name}}\t{{.Status}}' | grep -c healthy
```
**Expected:**
```
18        # nginx, 4 app, 6 redis (cluster), 3 patroni, 3 etcd, pgbouncer + haproxy
```

The capstone `application-capstone.yml` composes every profile:
```yaml
spring:
  profiles:
    include: [ ha, security, observability ]
  threads.virtual.enabled: true                       # M01
pulse:
  fanout: { backbone: redis-streams, dedup-window: 5m }   # M09
  presence: { mode: viewport, sweep-interval: 20s }       # M11
  limits: { max-room-size: 50000, max-message-bytes: 65536 }  # M21
  stream: { replay-window: PT5M }                         # M09
  shards: { logical: 4096, physical: 4 }                  # M14
```

Smoke test — the VERIFY chain end to end:
```bash
./code/capstone-smoke.sh
```
**Expected:**
```
✅ auth: ticket issued, JWT verified, connected
✅ send: message persisted (seq assigned), acked, broadcast
✅ cross-node: alice@node-1 <-> bob@node-4 exchange messages
✅ resume: 2-min disconnect, 0 lost
✅ presence: viewport subscription, sweep working
✅ rate limit: 429 after burst
✅ outbox: crash-after-persist recovered
✅ observability: delivery latency, SLOs, traces flowing
```

---

## Part B — The acceptance test

`code/acceptance.js` — the full target load, with every SLI asserted:

```js
import ws from 'k6/ws';
import { check } from 'k6';
import { Trend, Counter, Rate } from 'k6/metrics';

const deliveryLatency = new Trend('delivery_latency_ms', true);
const deliverySuccess = new Rate('delivery_success');
const connectSuccess  = new Rate('connect_success');
const sequenceGaps    = new Counter('sequence_gaps');
const NUL = String.fromCharCode(0);

export const options = {
  scenarios: {
    // Ramp to 100k over 10 min, hold for 20, measuring the hold window.
    steady: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '10m', target: 100000 },
        { duration: '20m', target: 100000 },   // <-- MEASURE HERE
        { duration: '5m',  target: 0 },
      ],
      gracefulRampDown: '60s',
    },
    // A 10x burst during the steady window, to hit the peak fan-out target.
    burst: {
      executor: 'constant-arrival-rate',
      rate: 5000, timeUnit: '1s', duration: '2m',
      preAllocatedVUs: 2000, maxVUs: 10000,
      startTime: '20m',
    },
  },
  thresholds: {
    'delivery_latency_ms': ['p(99)<500'],       // SLO 1
    'delivery_success':    ['rate>0.9999'],     // SLO 2
    'connect_success':     ['rate>0.999'],      // SLO 3
    'sequence_gaps':       ['count<10'],        // SLO 4
  },
  summaryTrendStats: ['min','med','p(95)','p(99)','p(99.9)','max'],
};

export default function () {
  const room = `room.${__VU % 1000}`;
  const user = `u${__VU}`;
  let lastSeq = 0;

  // Full auth flow (Module 21)
  const ticket = getTicket(user);
  const jwt = getJwt(user);

  const res = ws.connect(`ws://ingress/ws?ticket=${ticket}`, {}, (socket) => {
    connectSuccess.add(true);
    socket.on('open', () => {
      socket.send(`CONNECT\naccept-version:1.2\nheart-beat:10000,10000\nAuthorization:Bearer ${jwt}\n\n${NUL}`);
      socket.send(`SUBSCRIBE\nid:s0\ndestination:/topic/${room}\n\n${NUL}`);
      socket.send(`SUBSCRIBE\nid:s1\ndestination:/user/queue/ack\n\n${NUL}`);
      socket.setTimeout(() => socket.setInterval(() => {
        const t = Date.now();
        socket.send(`SEND\ndestination:/app/${room}/send\ncontent-type:application/json\n\n{"clientId":"c-${__VU}-${t}","body":"t=${t}"}${NUL}`);
      }, 180000), Math.random() * 180000);
    });
    socket.on('message', (raw) => {
      const body = raw.slice(raw.indexOf('\n\n') + 2).replace(/\x00$/, '');
      if (!body.startsWith('{')) return;
      let env; try { env = JSON.parse(body); } catch (e) { return; }
      if (env.type !== 'message.new') return;
      const m = env.data, match = /t=(\d+)/.exec(m.body);
      if (match) { deliveryLatency.add(Date.now() - Number(match[1])); deliverySuccess.add(true); }
      if (lastSeq && m.seq > lastSeq + 1) sequenceGaps.add(m.seq - lastSeq - 1);
      lastSeq = Math.max(lastSeq, m.seq);
    });
    socket.on('error', () => deliverySuccess.add(false));
    socket.setTimeout(() => socket.close(), 35 * 60 * 1000);
  });
  check(res, { 'handshake 101': (r) => r && r.status === 101 }) || connectSuccess.add(false);
}
```

Prepare the generator (Module 06's discipline):
```bash
ulimit -n 500000
sudo sysctl -w net.ipv4.ip_local_port_range="10000 65535"
# 100k connections from one host needs multiple source IPs; use a distributed
# k6 run or 4 generator hosts. See code/distributed-generators.sh
```

```bash
./code/collect.sh /tmp/capstone-metrics.csv &
k6 run --out experimental-prometheus-rw code/acceptance.js
```

**Expected (reference: 4 app nodes × 8 vCPU / 8 GB, tuned per Module 15):**
```
     ✓ handshake 101
     delivery_latency_ms....: min=3 med=24 p(95)=118 p(99)=284 p(99.9)=890 max=4102
     delivery_success.......: 99.994%  ✓ 187,204,882  ✗ 11,204
     connect_success........: 99.97%
     sequence_gaps..........: 4
     open_connections.......: 100,000

     ✓ delivery_latency_ms  p(99)<500
     ✓ delivery_success     rate>0.9999
     ✓ connect_success      rate>0.999
     ✓ sequence_gaps        count<10
```

✅ **All four SLOs met at 100,000 connections.** During the burst:
```
burst window: 556,000 outbound msg/s peak
p99 during burst: 412ms  (still inside SLO)
outbound queue max: 3,102 (drained, never saturated)
```

Record the operating point:
```markdown
## Module 22 — Acceptance

- 100,000 connections, 1,000 rooms, 100x amplification
- Steady: 556 in / 55,600 out msg/s; burst 556,000 out/s
- p50/p99/p99.9 delivery: 24 / 284 / 890 ms
- delivery success 99.994%, connect success 99.97%, gaps 4
- 4 app nodes, ~25,000 connections each, 71 KB/connection
- Knee: ~700,000 outbound msg/s cluster; operating at 8% of it steady, 79% at burst
```

---

## Part C — Chaos under load

**The hard test: run the Module 18 drill suite while the acceptance load is
running.** A failover with zero traffic is easy; one at 100k connections and
556k outbound msg/s is the real thing.

```bash
# Start the 30-minute acceptance load, then inject drills during the steady window
k6 run code/acceptance.js &
sleep 720                                    # ramp complete, in steady state

./code/capstone-chaos.sh
```

`code/capstone-chaos.sh` runs each drill 3 minutes apart, under load:
```bash
run_drill "redis-primary-kill"  "docker kill capstone-redis-1"  "docker start capstone-redis-1"
sleep 180
run_drill "pg-primary-kill"     "kubectl delete pod \$(pg_primary)" ""
sleep 180
run_drill "app-node-kill"       "docker kill capstone-pulse-1"  "docker start capstone-pulse-1"
sleep 180
run_drill "rolling-deploy"      "./code/rolling_deploy.sh"      ""
sleep 180
run_drill "distributed-flood"   "./code/distributed-flood.sh --accounts 200 --ips 200" ""
```

**Expected — the capstone scoreboard, under 100k-connection load:**

| Drill | RTO | RPO | p99 during | SLO held? |
|-------|-----|-----|-----------|-----------|
| Redis primary kill | 8.2 s | **0** | 412 ms | ✅ |
| Postgres primary kill | 11.4 s | **0** | 890 ms | ⚠️ p99 briefly 890 |
| App node kill | 4.8 s | **0** | 1,240 ms | ⚠️ 24,000 clients reconnected |
| Rolling deploy | **0 s** | **0** | 302 ms | ✅ |
| Distributed flood | n/a | **0** | 318 ms | ✅ (quarantined in 14s) |

✅ **RPO 0 on every drill under full load.** Two drills briefly pushed p99 to
~890 ms — outside the 500 ms *instantaneous* target, but the drills are within the
error budget (SLO 1 is a 30-day 99.9%, and these are seconds-long).

The app-node kill is the honest wart: **24,000 clients reconnected**, and even
with full jitter that's a real event. Watch it:
```bash
# During the app-node-kill drill:
watch -n1 'curl -s prometheus:9090/api/v1/query?query="sum(rate(chat_handshake_total[10s]))" | jq -r ".data.result[0].value[1]"'
```
```
reconnect peak: 812/s over 34s   (jittered; would be 24,000/s without it)
delivery_success during: 99.98%  (SLO held)
```

Record it:
```markdown
## Module 22 — Chaos under load

Under 100,000 connections + 556k outbound msg/s:
| Drill              | RTO   | RPO | p99    |
|--------------------|-------|-----|--------|
| Redis primary kill | 8.2s  | 0   | 412ms  |
| PG primary kill    | 11.4s | 0   | 890ms  |
| App node kill      | 4.8s  | 0   | 1,240ms (24k reconnects, 812/s peak) |
| Rolling deploy     | 0s    | 0   | 302ms  |
| Distributed flood  | -     | 0   | 318ms  |

RPO 0 everywhere. Two drills briefly exceeded the 500ms instantaneous target
but stayed well inside the 30-day error budget.
```

---

## Part D — The architecture review

The real deliverable. Write `ARCHITECTURE_REVIEW.md`. For each decision: the
decision, the evidence, the rejected alternative, and the falsifying condition.

The reference solution ([`solutions/ARCHITECTURE_REVIEW.md`](./solutions/ARCHITECTURE_REVIEW.md))
is complete; here is the required structure and one worked example.

```markdown
## Decision: Virtual threads on Spring MVC, not WebFlux

**Decision.** The connection layer runs on Spring MVC with STOMP and Java 21
virtual threads.

**Evidence.** Module 15's head-to-head: at 100k connections, virtual threads
hold at 71 KB/connection (after tuning) vs WebFlux's 59 KB — a 1.2x gap, not the
2.65x the untuned comparison suggested. p50 is 3ms better on virtual threads.
The debugging tax measured 2.6x higher on WebFlux (Module 15, Task 4).

**Rejected alternative.** WebFlux. It genuinely wins connection density and
backpressure ergonomics, but Module 15's challenge showed the density gap is
mostly untuned buffers, and Module 04's challenge showed WebFlux costs us STOMP
entirely (~300 lines of hand-rolled protocol).

**Would change if.** Connection density becomes the binding constraint — Module
15's crossover surface puts that above ~85k connections/node, and we run at
25k/node with 4 nodes. At 3x growth we'd re-measure; even then, adding nodes is
cheaper than a rewrite.
```

Write one of these for each of: the transport (WebSocket/STOMP), the fan-out
backbone (Redis Streams vs Kafka vs Pub/Sub), the delivery semantics (at-least-once
+ idempotency), the storage (sharded Postgres vs wide-column), the outbox, the HA
approach, and the auth model. **Seven to ten decisions, each with all four parts.**

---

## Part E — Production readiness

Write `PRODUCTION_READINESS.md` — the honest assessment. The temptation is to
claim it's done. The skill is naming what isn't.

Structure:
```markdown
## Done and verified
- [what actually works, with the test that proves it]

## Done but not production-grade
- [what works in the lab but needs hardening — with what specifically]

## Faked for the course
- [the ticket store is in-process; auth uses a test JWT issuer; ...]

## Would not ship without
- [the gaps that are release-blockers, and why]

## Explicitly out of scope
- [what we chose not to build, and the decision behind it]
```

The reference solution's assessment is deliberately unflattering — that's the
point. A production-readiness doc that says "everything is ready" is the one
finding that fails the capstone.

---

## Part F — Defend it

Present the review to someone (a colleague, a rubber duck, or your own strongest
adversarial reasoning) and have them attack each decision. For each attack:

- If they're right, revise the decision.
- If they're wrong, the review should already contain the rebuttal — the
  "would change if" section is your answer to "why not X?"

A decision you can't defend against its strongest objection is one you didn't
actually make; you defaulted into it.

```bash
./code/self-review.sh ARCHITECTURE_REVIEW.md
```
This checks each decision has all four parts and flags any that read as
assertion rather than argument.

**Expected:**
```
✅ 9 decisions, all with decision/evidence/alternative/condition
⚠️ "outbox over CDC" — the evidence is qualitative; add the WAL-slot-fills-disk
   measurement from Module 13
✅ production readiness names 7 gaps, 3 release-blockers
```

---

## What you built

- **One deployable system** integrating every module, passing all four SLOs at
  100,000 connections.
- **A chaos run under full load** — RPO 0 on every drill, with the honest warts
  (24k reconnects on a node loss) named rather than hidden.
- **An architecture review** where every decision carries its evidence and its
  rejected alternative.
- **A production-readiness assessment** honest about what a course can and cannot
  build.

You can now do the thing the course set out to teach: **not plug the technology
together, but defend why it's assembled the way it is — including what you chose
not to do.**

---

## Where to go next

- **[`kubernetes-course`](../../kubernetes-course/)** — the deep orchestration
  foundation Module 19 only sampled.
- **[`slack-clone-course`](../../slack-clone-course/)** — the same product domain
  on Django Channels + Next.js. Working both shows how a different runtime model
  solves identical problems, and where the solutions converge.
- **The Signal protocol** — if Module 21's E2EE tradeoff interested you, the
  Double Ratchet is where the real cryptography lives.
- **Discord's and Slack's engineering blogs** — the systems this course is
  modelled on, written up by the people who hit these walls first.

Congratulations. You've built a real-time system from the wire up, measured every
claim, and can defend the whole thing. That was the goal.
