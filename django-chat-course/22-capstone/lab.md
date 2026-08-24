# Lab 22 — Wire It All Together

**You'll:** derive the topology from a cost model instead of guessing it, assemble
the complete stack, fail the acceptance test on purpose, fix it with a number you
re-derive, pass it, run the chaos suite *under* that load, and produce the two
documents the capstone is actually graded on.

⏱️ ~8+ hours. This is the integration of everything; budget a full day and do
Parts A–C in one sitting.

> **Scale to your hardware.** The targets below are for 100,000 connections. If
> your machine cannot, run 20,000 with the *same* room structure — 96 rooms of 200
> plus one of 800 — and record the scale factor. Every finding in this lab is
> about the shape of the curve. The shape does not change; only the axis labels do.
>
> Generator-side setup is [Module 06](../06-load-testing-harness/) Part B and it is
> not optional: `ulimit -n`, `net.ipv4.ip_local_port_range`, and more than one
> source IP once you pass ~28,000 sockets from a single host.

All paths are relative to the repo root. The capstone stack lives in
`infra/capstone/`.

---

## Part A — Derive the topology before you deploy anything

The temptation is `docker compose up` and then measure. Resist it for forty
minutes. You have a cost model; use it, and then find out how wrong it was.

### A1 — State the workload as numbers

```bash
mkdir -p infra/capstone && cd infra/capstone
cat > workload.md <<'EOF'
100,000 connections
  480 rooms x 200 members = 96,000   1 msg/user/180s
    1 room  x 4,000        =  4,000   12 msg/hour, members read-mostly
inbound  steady   96,000/180              =     533 msg/s
outbound steady   533 x 199 + 0.003x3,999 = 106,080 msg/s
burst             5x, 2-minute window     = 530,400 msg/s
EOF
```

The only line that matters is the last one. **Nobody sizes a chat system for its
inbound rate**, and the dashboards that show you inbound are lying to you by a
factor of 199 — [Module 06](../06-load-testing-harness/) made you write
`inbound × room_size = outbound` on the wall for exactly this moment.

### A2 — Compute the channel-layer ceiling

[Module 07](../07-scale-out-redis-channel-layer/) measured Redis's cost per
`group_send` as `55 µs + 46 µs × W`, where `W` is the number of **worker
processes** subscribed to the room. [Module 19](../19-kubernetes-ha-and-multiregion/)
turned it into a ceiling for `S` channel-layer shards.

`code/ceiling.py`:

```python
#!/usr/bin/env python3
"""Channel-layer ceiling from Module 07's regression + Module 19's shard math."""
FIXED_US, PER_WORKER_US = 55, 46          # Module 07, Task 1 regression
BUDGET_US = 950_000                       # 95% of one Redis thread, per shard
RECIPIENTS = 199                          # a 200-member room

def ceiling(workers: int, shards: int) -> int:
    per_send = FIXED_US + PER_WORKER_US * workers
    return int(shards * BUDGET_US / per_send) * RECIPIENTS

for pods in (1, 2, 3, 4, 5):
    w = pods * 4                          # 4 uvicorn workers per pod (Module 19)
    row = [f"{ceiling(w, s):>10,}" for s in (3, 4, 5)]
    print(f"{pods} pods / {w:>2} workers  " + "  ".join(row))
```

```bash
python3 code/ceiling.py
```
**Expected:**
```
1 pods /  4 workers   2,372,876   3,163,901   3,954,926
2 pods /  8 workers   1,340,663   1,787,617   2,234,571
3 pods / 12 workers     934,305   1,245,740   1,557,175
4 pods / 16 workers     716,997     955,996   1,194,995
5 pods / 20 workers     581,677     775,503     969,329
```

✅ **Every column falls as you add pods.** That is the `46 µs × W` term, and it is
the defining constraint of this system. Read the "3 shards" column: four pods on
Module 18's three-shard channel layer gives you **717,000 outbound msg/s**.

### A3 — Pick the topology, and show your work

Two constraints, applied in order.

**Constraint 1 — connections.** At ≈45 KB per idle connection plus kernel socket
buffers, [Module 15](../15-async-sync-and-raw-asgi/) puts a worker's practical
ceiling near **40,000**. Four pods × 4 workers holds 100,000 at **6,250
connections per worker** — 16% of the ceiling. Connections are not close to
binding, and that is worth saying out loud because on the JVM twin they are the
binding constraint.

**Constraint 2 — burst fan-out.** [Module 06](../06-load-testing-harness/)'s rule:
operate at 60–70% of the knee, never 95%, because the 30% you appear to waste is
what absorbs a failover, a burst, and the load from a pod that just died.

```
burst 530,400 / 717,000 (3 shards)  =  74%   ❌ inside the target, outside the rule
burst 530,400 / 956,000 (4 shards)  =  55%   ✅
steady 106,080 / 956,000            =  11%
```

✅ **The capstone needs a fourth channel-layer shard.** Nothing in Modules 00–21
told you that. Module 18 built three because three was enough for 10,000
connections; the capstone's burst target and Module 07's per-worker term together
say four.

Write the derivation down next to the number — this is the paragraph the
architecture review's decision #7 is built from:

```bash
cat >> workload.md <<'EOF'

TOPOLOGY (derived, not chosen)
  4 pods x 4 uvicorn+uvloop workers = 16 subscribed worker processes
  100,000 / 16 = 6,250 conns/worker  (16% of the ~40,000 memory ceiling)
  channel layer: 4 Sentinel-managed shards
    ceiling = 4 x 950,000 / (55 + 46x16) x 199 = 956,000 out msg/s
    burst 530,400 = 55% of ceiling      (Module 06's rule: <= 65%)
    3 shards would be 74% -- inside the target, outside the rule
  maxReplicas = 4. NOT a round number: replica 5 drops the ceiling to 776,000.
EOF
```

> ⚠️ **`maxReplicas` is a measured constant here.** An HPA that scales on
> connections will happily give you a fifth pod, which lowers your fan-out ceiling
> by 19% at the exact moment you needed more of it. Module 19 said this; the
> capstone is where it costs you if you ignored it.

---

## Part B — Assemble the stack

Everything is already built across Modules 04–21. The capstone composes it.

### B1 — The settings module that turns everything on

`apps/pulse/pulse/settings/capstone.py`:

```python
from .ha import *                                    # Module 18: Sentinel, PgBouncer, drain

DEBUG = False
ALLOWED_HOSTS = ["pulse.local", "nginx"]

# --- Module 07 + 09: two layers, on purpose -------------------------------
CHANNEL_LAYERS = {
    "default": {                                     # message path: bounded, alertable
        "BACKEND": "chat.layers.StreamsChannelLayer", # Module 09
        "CONFIG": {
            "shards": [                              # Module 18 built 3; Part A says 4
                {"sentinels": [("sentinel-a", 26379)], "master_name": "cl-0"},
                {"sentinels": [("sentinel-b", 26379)], "master_name": "cl-1"},
                {"sentinels": [("sentinel-c", 26379)], "master_name": "cl-2"},
                {"sentinels": [("sentinel-d", 26379)], "master_name": "cl-3"},
            ],
            "capacity": 3000,                        # Module 07's derivation. Part C breaks it.
            "expiry": 10,
            "group_expiry": 300,                     # Module 18 finding: NOT the 86,400 default
            "socket_timeout": 2.0,                   # Module 18: pause RTO 14.8s -> 9.1s
        },
    },
    "ephemeral": {                                   # typing/presence/cursors: at-most-once
        "BACKEND": "channels_redis.pubsub.RedisPubSubChannelLayer",
        "CONFIG": {"hosts": [("redis-state", 6379)]},
    },
}

PULSE = {
    "FANOUT":   {"backbone": "redis-streams", "dedup_window": 300},   # M09
    "PRESENCE": {"mode": "viewport", "sweep_interval": 20,
                 "reconnect_grace": 30, "max_evict_fraction": 0.05},  # M11 + M18
    "LIMITS":   {"max_room_members": 50_000, "max_message_bytes": 65_536,
                 "outstanding_tickets": 20},                          # M21
    "RESUME":   {"window_seconds": 300, "max_batch": 200,
                 "abandon_after": 5_000},                             # M10
    "SHARDS":   {"logical": 4096, "physical": 4},                     # M14
    "AUTHZ":    {"cache_ttl": 10},                                    # M21 challenge
}

DATABASE_ROUTERS = ["chat.routers.ReplicaRouter", "chat.routers.ShardRouter"]  # M13, M14
```

Every line above is a decision from a numbered module. If you cannot say which
module and which measurement produced a line, that is a gap in your review, not a
gap in the settings file.

### B2 — Bring it up

```bash
cd apps/pulse && docker build -t pulse:capstone .
cd ../../infra/capstone
docker compose -p pulse-capstone -f compose.capstone.yml up -d --wait
docker compose -p pulse-capstone -f compose.capstone.yml ps \
  --format 'table {{.Name}}\t{{.Status}}' | grep -c healthy
```
**Expected:**
```
27
```

```
nginx                    1     Module 18
pulse-1..4               4     Module 19 pod shape, 4 workers each
channel-layer 0..3       4     Redis primaries        } Module 18
  + replicas             4                            } Sentinel-managed
  + sentinels            4                            }
redis-state              1     seq, streams, presence, buckets   Modules 08-11
redis-tickets            1     maxmemory-policy allkeys-lru      Module 21 challenge
postgres primary+replica 2     CloudNativePG / Patroni           Modules 13, 19
pgbouncer                1     transaction pooling               Module 13
celery-relay + beat      2     the outbox                        Module 13
prometheus/grafana/tempo 3     Module 20
```

> **Note the two separate Redises that are not the channel layer.** Module 21's
> challenge found that ticket farming can OOM a `noeviction` backbone Redis and
> take chat down; tickets live on their own `allkeys-lru` instance. That is a
> capstone-visible consequence of a challenge finding, and the review should cite
> it.

### B3 — The smoke test: the whole VERIFY chain, end to end

```bash
./code/capstone-smoke.sh
```
**Expected:**
```
✅ auth        ticket issued (GETDEL), JWT verified in first frame, identity cross-checked
✅ origin      forged Origin rejected at handshake (CSWSH blocked)
✅ send        seq allocated + XADD in ONE Lua call, acked in 2.1 ms
✅ idempotent  same client_id sent 3x -> 1 row, 1 delivery
✅ cross-pod   alice@pulse-1 <-> bob@pulse-4, 199 recipients, p50 26 ms
✅ resume      120 s disconnect, 84 messages replayed, 0 lost, 0 gaps
✅ presence    viewport subscription active, sweeper diffing, storm guard armed
✅ ratelimit   burst of 25 -> 20 delivered, 5 rejected with retry_after
✅ outbox      SIGKILL between XADD and commit -> relay republished, 0 lost, 0 dupes
✅ shards      room.7 -> logical 3824 -> physical 2 (crc32("room.7") % 4096)
✅ observe     delivery latency histogram, 4 SLO recording rules, traces joined
```

If any line is red, stop. The capstone is a composition test; a broken component
produces a confusing composition result and you will spend an hour blaming the
wrong module.

> The `shards` line is worth checking by hand, because a wrong shard function is
> silent for months and then loses a room:
> ```bash
> python3 -c "import zlib; print(zlib.crc32(b'room.7') % 4096)"   # 3824
> docker exec pulse-capstone-redis-state-1 redis-cli CLUSTER KEYSLOT 'room:{7}:seq'
> docker exec pulse-capstone-redis-state-1 redis-cli CLUSTER KEYSLOT 'room:{7}:stream'
> ```
> **Expected:** `3824`, then `1716` twice — the two keys share a slot because of
> the `{7}` hash tag, which is the only reason Module 10's Lua script is legal
> under Cluster.

---

## Part C — The acceptance test

### C1 — The test

`code/acceptance.js` — the full target load with every SLI asserted. It speaks
Pulse's own envelope ([Module 05](../05-protocol-and-domain-design/)); there is no
subprotocol to frame, which makes the generator simpler than the JVM twin's.

```js
import ws from 'k6/ws';
import http from 'k6/http';
import { check } from 'k6';
import { Trend, Counter, Rate } from 'k6/metrics';

const deliveryLatency = new Trend('delivery_latency_ms', true);
const deliverySuccess = new Rate('delivery_success');
const connectSuccess  = new Rate('connect_success');
const sequenceGaps    = new Counter('sequence_gaps');

const TARGET = Number(__ENV.TARGET || 100000);
const CHAT_ROOMS = 480;

export const options = {
  scenarios: {
    steady: {                                  // ramp 10m, HOLD 20m, drain 5m
      executor: 'ramping-vus', startVUs: 0,
      stages: [{ duration: '10m', target: TARGET },
               { duration: '20m', target: TARGET },      // <-- measure here
               { duration: '5m',  target: 0 }],
      gracefulRampDown: '60s',
    },
    burst: {                                   // 5x for 2 minutes, inside the hold
      executor: 'constant-arrival-rate',
      rate: 2132, timeUnit: '1s', duration: '2m',        // 4x steady, on top of it
      preAllocatedVUs: 2000, maxVUs: 8000, startTime: '20m',
      exec: 'burstSend',
    },
  },
  thresholds: {
    'delivery_latency_ms': ['p(99)<500'],                // SLO 2
    'delivery_success':    ['rate>0.9999'],              // SLO 1
    'connect_success':     ['rate>0.999'],               // SLO 3
    'sequence_gaps':       ['count<10'],                 // SLO 4 (proxy -- see below)
  },
  summaryTrendStats: ['min', 'med', 'p(95)', 'p(99)', 'p(99.9)', 'max'],
};

function envelope(type, room, data) {
  return JSON.stringify({ v: 1, type, room, ts: Date.now(), data });
}

export default function () {
  const isAnnounce = __VU > 96000;
  const slug = isAnnounce ? 'announce' : String(__VU % CHAT_ROOMS);
  const room = `room.${slug}`;                  // Room.key = "room." + Room.slug
  const user = `u${__VU}`;
  let lastSeq = 0;

  // Module 21: single-use ticket for the handshake, JWT in the first frame.
  const ticket = http.post(`http://nginx/api/ws-ticket`, null,
                           { headers: { Authorization: `Bearer ${jwtFor(user)}` } })
                     .json('ticket');

  const res = ws.connect(`ws://nginx/ws/?ticket=${ticket}`, {}, (socket) => {
    connectSuccess.add(true);
    socket.on('open', () => {
      socket.send(envelope('auth', room, { jwt: jwtFor(user) }));   // first frame
      socket.send(envelope('join', room, { from_seq: 0 }));         // join BEFORE resume
      if (isAnnounce) return;                                       // read-only members
      // Full jitter over the 180 s period -- coordinated omission is a lie (M06).
      socket.setTimeout(() => socket.setInterval(() => {
        const t = Date.now();
        socket.send(envelope('message.create', room, {
          client_id: `c-${__VU}-${t}`, body: `t=${t}`,
        }));
      }, 180000), Math.random() * 180000);
    });

    socket.on('message', (raw) => {
      let env; try { env = JSON.parse(raw); } catch (e) { return; }
      if (env.type !== 'message.new') return;
      const m = env.data;
      const match = /t=(\d+)/.exec(m.body);
      if (match) {
        deliveryLatency.add(Date.now() - Number(match[1]));
        deliverySuccess.add(true);
      }
      if (lastSeq && m.seq > lastSeq + 1) sequenceGaps.add(m.seq - lastSeq - 1);
      lastSeq = Math.max(lastSeq, m.seq);
    });

    socket.on('error', () => deliverySuccess.add(false));
    socket.setTimeout(() => socket.close(1000), 35 * 60 * 1000);
  });
  check(res, { 'handshake 101': (r) => r && r.status === 101 }) || connectSuccess.add(false);
}
```

Three details that are easy to get wrong and invalidate the whole run:

- **`sequence_gaps` is a proxy for SLO 4, not SLO 4.** The SLI is *rooms with a
  **permanent** gap*; k6 counts *messages* apparently skipped, and most of those
  close milliseconds later when the client's debounced repair
  ([Module 10](../10-ordering-and-delivery-semantics/)) fills them. The real SLI
  comes from the `chat_rooms_with_permanent_gap` recording rule
  ([Module 20](../20-observability-and-slos/)); the k6 counter is the fast,
  in-run canary that tells you to go look. At 481 rooms, 0.01% means **zero rooms**
  — there is no rounding to hide in.

- **`join` before `resume`, always.** [Module 10](../10-ordering-and-delivery-semantics/)
  proved the other order opens a window where a message is published after your
  resume query ran and before your group membership existed — a hole `resume` has
  already passed over and will never revisit. Prefer duplicates over gaps.
- **Jitter the first send across the full 180 s period.** Without it, 96,000 VUs
  send in lockstep every three minutes and you have measured a thundering herd, not
  your workload.

### C2 — Run it

```bash
./code/collect.sh /tmp/capstone-run1.csv &
k6 run --out experimental-prometheus-rw code/acceptance.js
```

**Expected — and it fails:**
```
     ✓ handshake 101
     delivery_latency_ms....: min=4 med=27 p(95)=124 p(99)=301 p(99.9)=1,180 max=6,210
     delivery_success.......: 99.982%   ✓ 190,844,201  ✗ 34,318
     connect_success........: 99.96%
     sequence_gaps..........: 61
     open_connections.......: 100,000

     ✓ delivery_latency_ms  p(99)<500
     ✗ delivery_success     rate>0.9999   (99.982%)
     ✓ connect_success      rate>0.999
     ✗ sequence_gaps        count<10      (61)
```

❌ **Two SLOs failed, and both failed only during the burst.** Note that latency
passed — this is not a slowness problem, it is a **loss** problem, and loss is the
one thing the whole course has been engineering away.

### C3 — Diagnose it

Go to the metric [Module 07](../07-scale-out-redis-channel-layer/) told you to page
on with `for: 0m`, because a single dropped message is a correctness event and not
a load event:

```bash
curl -sG prometheus:9090/api/v1/query \
  --data-urlencode 'query=increase(chat_layer_over_capacity_total[35m])' | jq -r '.data.result[]|.value[1]'
```
**Expected:**
```
2847
```

```bash
curl -sG prometheus:9090/api/v1/query \
  --data-urlencode 'query=max_over_time(chat_layer_mailbox_depth[35m])' | jq -r '.data.result[]|.value[1]'
```
**Expected:**
```
3000
```

✅ **The worker mailboxes hit `capacity` and dropped 2,847 messages.** The
`group_send` call raised `ChannelFull`, the layer counted it, and 25 of every 200
room members silently missed a message — which the client's gap detector then
reported as the 61 sequence gaps.

Now the interesting part: **why is `capacity: 3000` wrong here when Module 07
derived it carefully?** Re-read the derivation:

```
Module 07:  safe operating point (8 workers) = 0.65 x 441,000 = 287,000 out/s
            group_sends/s = 287,000 / 199    = 1,442/s
            2 seconds of headroom            = 2,884  ->  capacity 3000
```

The derivation is not wrong. Its **input** is. Module 07 sized the mailbox for
2 seconds at the *steady* safe operating point. The capstone's burst is
**530,400 outbound msg/s**, and nearly every room has a subscriber on nearly every
worker, so each worker's mailbox sees essentially the full `group_send` rate:

```
burst group_sends/s  =  530,400 / 199  =  2,665/s
capacity 3,000       =  3,000 / 2,665  =  1.13 seconds of headroom
```

**1.13 seconds** is shorter than a Sentinel failover, shorter than a Postgres
checkpoint, and shorter than a `database_sync_to_async` threadpool stall. Module
07's own rule — *a queue bound is a time budget, not a count; re-derive it whenever
the arrival rate changes* — has been violated by the capstone's own workload.

### C4 — Re-derive and fix

```
capacity  =  arrival_rate x tolerable_stall
          =  2,665/s x 2 s
          =  5,330    ->  capacity: 6000

memory cost = 6,000 entries x 260 B x 16 workers = 25 MB
```

```diff
-            "capacity": 3000,
+            "capacity": 6000,      # re-derived at the CAPSTONE burst rate:
+                                   # 530,400 out/s / 199 = 2,665 group_send/s x 2 s
```

```bash
docker compose -p pulse-capstone -f compose.capstone.yml up -d --force-recreate pulse-1 pulse-2 pulse-3 pulse-4
k6 run --out experimental-prometheus-rw code/acceptance.js
```

**Expected — all four green:**
```
     ✓ handshake 101
     delivery_latency_ms....: min=4 med=27 p(95)=121 p(99)=296 p(99.9)=910 max=4,380
     delivery_success.......: 99.993%   ✓ 190,861,704  ✗ 13,362
     connect_success........: 99.96%
     sequence_gaps..........: 3
     open_connections.......: 100,000

     ✓ delivery_latency_ms  p(99)<500
     ✓ delivery_success     rate>0.9999
     ✓ connect_success      rate>0.999
     ✓ sequence_gaps        count<10

     chat_layer_over_capacity_total ......: 0
     chat_layer_mailbox_depth (max) ......: 4,102 / 6,000
```

During the burst window:
```
outbound peak ........ 530,400 msg/s   (55% of the 956,000 four-shard ceiling)
p99 during burst ..... 438 ms          (inside SLO 2)
Redis CPU, worst shard 58%
worker CPU, worst pod  84%             <-- remember this for the challenge
event-loop lag p99 ... 7.4 ms
```

✅ **All four SLOs met at 100,000 connections.**

Record the operating point. This block goes verbatim into the architecture review:

```markdown
## Module 22 — Acceptance

- 100,000 connections; 480 rooms x 200 + 1 x 4,000; amplification 199x
- Steady 533 in / 106,080 out msg/s; burst 5x = 530,400 out/s for 2 min
- p50/p95/p99/p99.9 delivery: 27 / 121 / 296 / 910 ms
- delivery success 99.993%, connect success 99.96%, permanent gaps 3
- 4 pods x 4 workers = 16 subscribed processes, 6,250 conns/worker (16% of ceiling)
- 4 channel-layer shards; ceiling 956,000 out/s; burst at 55% of it
- FIRST RUN FAILED: capacity 3000 = 1.13 s of burst headroom -> 2,847 dropped,
  61 gaps. Re-derived at the burst rate -> capacity 6000 (25 MB). 0 drops.
```

> **The finding is worth more than the fix.** Module 07's number was correct for
> Module 07's workload and wrong for this one, and *nothing about the code changed*
> — only the arrival rate did. Every bounded queue in your system carries a hidden
> assumption about the rate feeding it. The capstone is where you find out which
> ones you never re-checked.

---

## Part D — Chaos, under the acceptance load

**A failover with no traffic is a demo. A failover at 100,000 connections and
530,400 outbound msg/s is the thing you are actually claiming.**

```bash
k6 run code/acceptance.js &
sleep 720                                  # ramp complete; in the steady window
./code/capstone-chaos.sh
```

`code/capstone-chaos.sh` reuses Module 18's `drill.sh` harness so the RTO and RPO
columns are comparable to the numbers you already have, and spaces drills three
minutes apart so each one recovers before the next:

```bash
run_drill "cl-shard-primary-kill"  "docker kill pulse-capstone-cl-2-1"   "docker start pulse-capstone-cl-2-1"
run_drill "cl-shard-primary-pause" "docker pause pulse-capstone-cl-2-1; sleep 20; docker unpause pulse-capstone-cl-2-1"
run_drill "pg-primary-kill"        "kubectl delete pod \$(pg_primary)"
run_drill "app-pod-kill"           "docker kill pulse-capstone-pulse-3-1" "docker start pulse-capstone-pulse-3-1"
run_drill "app-pod-brownout"       "docker update --cpus 0.2 pulse-capstone-pulse-3-1; sleep 60" \
                                   "docker update --cpus 4.0 pulse-capstone-pulse-3-1"
run_drill "rolling-deploy"         "./code/rolling_deploy.sh"
run_drill "distributed-flood"      "./code/distributed-flood.sh --accounts 200 --ips 200"
run_drill "relay-split-brain"      "docker compose up -d --scale celery-relay=2"
```

**Expected — the capstone scoreboard, under 100,000-connection load:**

| Drill | RTO | RPO | p99 during | SLO held? |
|---|---|---|---|---|
| Rolling deploy (graceful, 4 pods) | **0.0 s** | **0** | 344 ms | ✅ invisible |
| Channel-layer shard primary kill | 8.6 s | **0** | 512 ms | ✅ |
| Channel-layer shard primary pause | 10.4 s | **0** | 2,640 ms | ⚠️ p99 |
| App pod kill | 5.1 s | **0** | 2,410 ms | ⚠️ 25,000 reconnects |
| App pod brownout (capacity shedding on) | 12.9 s | **0** | 604 ms | ✅ |
| Postgres primary kill | 13.2 s | **0** | 2,880 ms | ⚠️ p99 |
| Distributed flood (200 accounts / 200 IPs) | — | **0** | 381 ms | ✅ quarantined in 16 s |
| Celery relay split-brain (2 relays) | 0.0 s | **0** | 390 ms | ✅ 0 order violations |

✅ **RPO 0 on every drill, at ten times the load Module 18 ran at.** Worst RTO
13.2 s, inside the 15 s target.

Three drills briefly pushed p99 past 500 ms. That is outside the *instantaneous*
target and comfortably inside the *SLO*, and being able to say why is the point of
[Module 20](../20-observability-and-slos/):

```
SLO 2 budget = 0.1% of 30 days  =  43 minutes of "slow"
time spent above 500 ms p99 across all eight drills = 2 min 41 s
                                                    = 6.2% of the month's budget
```

**Eight deliberate catastrophes cost 6.2% of one SLO's monthly error budget.**
That is the sentence that turns "we did chaos engineering" into a number a product
owner can act on.

### D1 — The honest wart: 25,000 reconnects

The app-pod kill is the ugly one and you should not hide it:

```bash
watch -n1 'curl -sG prometheus:9090/api/v1/query \
  --data-urlencode "query=sum(rate(chat_handshake_total[10s]))" | jq -r ".data.result[0].value[1]"'
```
**Expected:**
```
reconnect peak ....... 690/s over 41 s        (full jitter, Module 17)
without jitter ....... 25,000/s over 3 s      (Module 18 measured this; do not re-run it here)
delivery_success during 99.98%                (SLO held)
ticket issuance ...... 690/s, bucket held     (Module 21's issuance limiter)
ORM threadpool ....... peaked 29/32 threads   <-- REMEMBER THIS. Part E of the challenge.
```

A quarter of your users reconnecting is a real event even when it is invisible in
the SLO, and three separate Module-21 and Module-11 mechanisms are the only reason
it stays invisible: full-jitter backoff, the ticket issuance bucket, and the
presence sweeper's 5% blast-radius bound. Remove any one and the reconnect becomes
the outage.

### D2 — Record it

```markdown
## Module 22 — Chaos under 100k-connection load

RPO 0 on 8/8 drills. Worst RTO 13.2 s (Postgres), target 15 s.
Three drills exceeded 500 ms p99 instantaneously; total 2 min 41 s of slow
delivery = 6.2% of SLO 2's 43-minute monthly budget.
Honest wart: an app-pod kill reconnects 25,000 clients. Peak 690/s only because
of full jitter + the ticket issuance bucket + the presence blast-radius bound.
Not tested: anything not on this list. See challenge Task 2.
```

---

## Part E — The architecture review

The real deliverable. Write `ARCHITECTURE_REVIEW.md`. For each decision: **the
decision, the evidence, the rejected alternative, the falsifying condition** — in
that order, every time, with no exceptions.

The reference is [`solutions/ARCHITECTURE_REVIEW.md`](./solutions/ARCHITECTURE_REVIEW.md).
Here is the required structure and one worked example:

```markdown
## Decision 7: Four pods, four workers each, four channel-layer shards

**Decision.** Pulse runs 4 pods x 4 uvicorn+uvloop workers behind 4
Sentinel-managed channel-layer shards, and `maxReplicas` is fixed at 4.

**Evidence.** Module 07 regressed the channel layer at 55 µs + 46 µs x W (worker
processes) against Redis's single thread, predicting the lab's measured
`group_send` rate to within 1.4%. Module 19's shard arithmetic gives 956,000
outbound msg/s at W=16 with 4 shards. The capstone's 530,400 msg/s burst is 55%
of that; Module 06's rule is 65%. Measured knee: 172,000 connections
(challenge Task 1), 4.4% below the arithmetic's 180,000.

**Rejected alternative.** Three shards (Module 18's stack, unchanged) puts the
burst at 74% of the ceiling. Also rejected: a fifth pod, which *lowers* the
ceiling to 776,000 because it adds four subscribed processes.

**Would change if.** Sustained burst utilization crosses 65% of the ceiling —
which happens at ~120,000 connections on this topology. The fix at that point is
a fifth shard (+25%, linear) and then room affinity (3.3x, and 3-4 engineer-weeks);
it is NOT more pods. If room affinity ever ships, W per room drops from 16 to 4
and the ceiling becomes 3,164,000 — at which point the Python ceiling binds
instead and this decision is re-opened from the other side.
```

Write one of these for **every** major decision. The reference has ten:

1. Transport and protocol (raw WebSocket + a hand-designed envelope)
2. Runtime (async Channels consumers, one worker per core)
3. Fan-out backbone (Redis Streams, with a second layer for the ephemeral path)
4. Delivery semantics (at-least-once + idempotency + Lua-atomic `seq`)
5. Storage (sharded, partitioned Postgres)
6. The outbox (dual-path, Celery relay)
7. Capacity and topology (the worked example above)
8. HA posture (quorum failover, capacity-aware readiness, graceful drain)
9. Presence and rate limiting (TTL + viewport, Lua token buckets)
10. Auth and abuse (ticket + first-frame JWT + durable revocation)

> **A review that defends all ten to the death is worse than one that concedes
> three.** The reference marks decisions 3, 8 and — most importantly — **2** as
> provisional, because the choice of Python for the socket edge has a named
> crossover the growth plan actually crosses.

---

## Part F — Production readiness

Write `PRODUCTION_READINESS.md`. The temptation is to claim it is done. The skill
is naming what is not, in the language of a release meeting.

```markdown
## Done and verified
- [what works, with the drill or test that proves it]

## Done but not production-grade
- [works in the lab; here is specifically what needs hardening]

## Faked for the course
- [the test JWT signer; the heuristic anomaly detector; ...]

## Would not ship without  (release blockers)
- [the gaps that block a release, and why each one blocks it]

## Explicitly out of scope  (decided, not forgotten)
- [what we chose not to build, and the decision behind it]

## Honest summary
```

The reference assessment is deliberately unflattering: **five release blockers, one
of which is a change this lab itself made.** A production-readiness document that
says "everything is ready" is the single finding that fails the capstone.

---

## Part G — Defend it

Take the review to someone — a colleague, a study partner, or your own strongest
adversarial reasoning — and have them attack each decision. For each attack:

- If they are right, **revise the decision** and note that you did.
- If they are wrong, your "would change if" section is already the rebuttal. If it
  isn't, the decision was never made; you defaulted into it.

```bash
./code/self-review.sh ARCHITECTURE_REVIEW.md
```
This checks every decision has all four parts and flags any whose evidence is
qualitative.

**Expected:**
```
✅ 10 decisions, all with decision / evidence / alternative / condition
⚠️  #6 "outbox over CDC" — the evidence is qualitative. Add Module 13's
    measured stalled-slot WAL growth (4.2 GB pinned by an INACTIVE slot).
⚠️  #9 "viewport presence" — the falsifying condition is not checkable.
    "if rooms get small" -> "if mean room size drops below 10, measured monthly".
✅ 3 of 10 decisions labelled provisional
✅ production readiness names 9 gaps, 5 release blockers
```

Fix both warnings. **"It depends" is not a falsifying condition; a threshold
someone could go and measure is.**

---

## What you built

- **One deployable system** integrating every module, passing all four SLOs at
  100,000 concurrent connections.
- **A topology derived from a cost model** — four channel-layer shards, because
  Module 07's per-worker term and Module 19's shard arithmetic and Module 06's
  safe-operating-point rule together said four, and no single module said anything.
- **A failed acceptance run and the re-derivation that fixed it** — Module 07's
  mailbox `capacity` was correct for its own workload and 1.13 seconds short for
  this one.
- **Eight chaos drills under full load**, RPO 0 on all of them, priced against an
  error budget: 6.2% of a month for eight deliberate catastrophes.
- **An architecture review** where every decision carries its evidence and its
  rejected alternative, and three of ten are honestly labelled provisional.
- **A production-readiness assessment** honest about what a course can and cannot
  build — including the release blocker this lab created.

You can now do the thing the course set out to teach: **not plug the technology
together, but defend why it is assembled the way it is — including what you chose
not to do, and the number that would change your mind.**

Now do [`challenge.md`](./challenge.md), which is where you find your own knee,
break the system in a way the drill list never imagined, and argue with three
people who think you are wrong.

---

## Where to go next

- **[`spring-boot-chat-course`](../../spring-boot-chat-course/)** — the JVM twin.
  If you have not worked it, work its Modules 01, 07, 15 and 22 now: you will watch
  virtual threads solve the *same* four problems and land on the *same* shape of
  answer with completely different binding constraints. Its capstone is
  memory-bound at 46,000 connections/node; yours is bound by a single Redis thread
  being told about every message sixteen times. Understanding **why the same
  architecture has a different bottleneck on a different runtime** is the most
  transferable thing in either course.
- **[`kubernetes-course`](../../kubernetes-course/)** — the orchestration depth
  Module 19 only sampled.
- **[`slack-clone-course`](../../slack-clone-course/)** — the same domain, the same
  stack, built as a product. Now that you can defend the architecture, building the
  breadth on top of it is a different and much easier exercise.
- **[`linux-course`](../../linux-course/)** — `tc netem`, `ss`, file descriptors,
  `sysctl`: everything the chaos drills leaned on.
- **The engineering blogs this course is modelled on** — Discord on Elixir and
  ScyllaDB, Slack on their gateway architecture, and Instagram's writing on running
  Django at scale, which is the closest published account of the problem you just
  solved.

Congratulations. You built a real-time system from the wire up, measured every
claim, and can defend the whole thing — including the parts where the honest answer
is "not yet, and here is the number that would change it." That was the goal.
