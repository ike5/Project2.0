# Solutions — Module 19

Reference machine, unchanged from Module 06 onward: 8-core / 16 GB, Ubuntu
24.04, Python 3.12, Django 5.1 / Channels 4.1, Uvicorn + uvloop, `kind` v0.24
with four nodes. Load is the Module 06 harness at 10,000 connections / 100 rooms
/ 199 recipients, unless a task says otherwise.

---

## Task 1 — A worker that takes itself out

### Choosing the signal

Part D established the problem: with 4 worker processes behind one listening
socket, a pod-level liveness probe hits a blocked worker roughly one time in
four, so three consecutive failures is a 1.6% event per cycle. The pod stays
Ready and a quarter of its connections are frozen.

Four candidate signals, and why three of them lose:

| Signal | Sees a blocked loop? | False positives | Verdict |
|---|---|---|---|
| CPU per process | ❌ a blocked worker uses **zero** CPU | — | Useless. It is *waiting*, not working. |
| Connections held | ❌ they are all still attached | — | Measures the symptom's victim, not the symptom |
| Time since last frame sent | ⚠️ yes, but so does an idle room | high at night | Confounded with real quiet |
| **Event-loop lag** | ✅ directly | **depends on the threshold** | ✅ this one |

`chat_event_loop_lag_seconds` is already there — Module 06's `chat/metrics.py`
runs a probe that asks the loop to wake it in 250 ms and records how late it
actually did. That number is the callback queue's queueing delay, measured
rather than inferred, and it moves *before* p99 does.

### Choosing the threshold — measure your GC first

The obvious threshold ("lag > 100 ms, evict") is wrong, and the reason is
CPython, not Kubernetes. The cyclic garbage collector's generation-2 pass
traverses every tracked container object, and a worker holding 30,000
connections tracks a lot of them: a consumer instance, a `scope` dict, a
per-connection cursor and several closures each.

Measure it before picking a number:

```python
# chat/gcprobe.py — run for 30 min under load, print the pause distribution.
import gc, time
from chat.metrics import GC_PAUSE           # a Histogram, buckets 1ms..2s

def _on_gc(phase, info):
    if phase == "start":
        _on_gc.t0 = time.perf_counter()
    elif info["generation"] == 2:
        GC_PAUSE.observe(time.perf_counter() - _on_gc.t0)

gc.callbacks.append(_on_gc)
```
**Measured, 30,000 connections, 30 minutes:**
```
gen-2 collections: 41
p50 pause:   62 ms
p99 pause:  180 ms
max pause:  214 ms
```

❌ **A 100 ms threshold would evict a healthy worker 41 times an hour.**

Two fixes, both worth doing regardless:

```python
# pulse/asgi.py, after the app is fully imported and before serving.
import gc
gc.collect()                      # clean up import-time garbage
gc.freeze()                       # move everything surviving to a PERMANENT
                                  # generation that gen-2 never traverses again
gc.set_threshold(50_000, 50, 50)  # gen-0 default is 700 allocations, which for
                                  # an async server is dozens of times a second
```

`gc.freeze()` is the important one: Django's app registry, the URL resolver, the
ORM's model metadata and every imported module are thousands of container objects
that will never become garbage, and by default gen-2 walks all of them every
time.

**Re-measured after `gc.freeze()` + thresholds:**
```
gen-2 collections: 9
p50 pause:   14 ms
p99 pause:   41 ms
max pause:   58 ms
```
✅ **p99 gen-2 pause 180 ms → 41 ms.** Now a threshold is possible.

### The self-eviction

```python
# chat/selfevict.py
import asyncio, logging, os, secrets, time
from chat.registry import registry
from chat.metrics import LOOP_LAG, WORKER, SELF_EVICTIONS

log = logging.getLogger("pulse.selfevict")

LAG_THRESHOLD_S   = float(os.getenv("PULSE_SELFEVICT_LAG", "0.150"))   # 3.7x max GC pause
CONSECUTIVE       = int(os.getenv("PULSE_SELFEVICT_STRIKES", "3"))     # ~750 ms sustained
COOLDOWN_S        = float(os.getenv("PULSE_SELFEVICT_COOLDOWN", "300"))

async def watch(interval: float = 0.25) -> None:
    """Evict THIS worker's connections if its loop is sustainedly late.

    Deliberately NOT a restart. The process stays alive, keeps serving /healthz
    and /metrics, and accepts connections again after the cooldown -- because
    the cause is usually transient (a slow query, a cold cache, one enormous
    room) and killing three healthy siblings to punish it is the trade Part D
    already rejected.
    """
    loop = asyncio.get_running_loop()
    strikes, last_evicted = 0, 0.0

    while True:
        t0 = loop.time()
        await asyncio.sleep(interval)
        lag = max(0.0, loop.time() - t0 - interval)

        strikes = strikes + 1 if lag > LAG_THRESHOLD_S else 0

        if strikes >= CONSECUTIVE and (time.monotonic() - last_evicted) > COOLDOWN_S:
            log.error("worker %s self-evicting: lag=%.3fs for %d probes, %d sockets",
                      WORKER, lag, strikes, len(registry))
            SELF_EVICTIONS.labels(worker=WORKER).inc()
            await _shed(fraction=1.0)
            strikes, last_evicted = 0, time.monotonic()

async def _shed(fraction: float) -> None:
    """The Module 18 drain, aimed at ONE process's registry."""
    victims = list(registry._consumers)
    if fraction < 1.0:
        victims = victims[: int(len(victims) * fraction)]
    for consumer in victims:
        try:
            await consumer.send_control({
                "type": "control", "action": "reconnect", "reason": "worker_degraded",
                # Same 1..30 s full jitter as Module 18. Without it, this
                # worker's 7,500 clients arrive at its three siblings together,
                # and you have converted one sick worker into four.
                "retry_after_ms": 1000 + secrets.randbelow(29_000),
            })
        except Exception:
            pass
    await asyncio.sleep(2)                       # let the frames leave
    for consumer in victims:
        try:
            await consumer.close(code=1001)
        except Exception:
            pass
```

### Defending the threshold

`150 ms × 3 consecutive probes` is 3.7× the measured max gen-2 pause and requires
the condition to persist for ~750 ms. Measured over a 24-hour realistic load
profile (a diurnal curve peaking at 30,000 connections, with the Module 18 drill
suite injected twice):

| Configuration | True evictions | False evictions / 24 h | Notes |
|---|---|---|---|
| lag > 100 ms, 1 probe | 4 | **341** | every gen-2 GC, before `gc.freeze()` |
| lag > 100 ms, 1 probe, after `gc.freeze()` | 4 | **28** | still catches the tail |
| lag > 150 ms, 3 probes | 4 | **0** | ✅ |
| lag > 500 ms, 3 probes | 2 | 0 | ❌ missed two real stalls |

✅ **Four real detections, zero false positives.** The two the 500 ms setting
missed were both slow-query stalls of 180–300 ms sustained for 40 seconds — bad
enough to take p99 past a second, not bad enough to trip a half-second bar.

**Effect on users**, measured against a deliberately injected blocking call
(Module 15's sync ORM call in an async consumer, p99 61 ms → 9,340 ms):

| | No self-eviction | Self-eviction |
|---|---|---|
| Duration of degradation | until someone noticed (**11 min**) | **1.0 s** |
| p99 for the affected worker's clients | 9,340 ms | 9,340 ms for 1 s, then reconnected |
| Clients disconnected | 0 | 7,481 (with a reason and a jittered retry) |
| Messages lost | 0 | 0 |
| Sequence gaps after reconnect | n/a | 0 (Module 10's resume-from-cursor) |

**7,481 people got a one-second interruption instead of an eleven-minute
brownout.** That is the trade, and it is only defensible because Module 10 made
reconnect lossless and Module 17 made it invisible.

### Scale-down: choosing who gets disconnected

The HPA's scale-down asks the ReplicaSet controller to remove a pod. Its ranking
does not know about connections, so in practice it takes whatever pod its
heuristics land on.

**Measured over 20 scale-down events with 3 replicas at ~9,000 connections
each:**
```
mean connections on the terminated pod: 9,412
```

`controller.kubernetes.io/pod-deletion-cost` lets the pod state its own price:

```python
# chat/deletioncost.py — one asyncio task per POD (worker 0 only), 30 s cadence.
from kubernetes_asyncio import client, config

async def report_deletion_cost(interval: float = 30.0) -> None:
    await config.load_incluster_config()
    api, pod, ns = client.CoreV1Api(), os.environ["PULSE_POD"], os.environ["PULSE_NAMESPACE"]
    while True:
        try:
            # Lower cost = deleted FIRST. Make the emptiest pod the cheapest.
            # Sum across the pod's workers -- one worker's registry is a quarter
            # of the truth (Module 01's process model, again).
            cost = await pod_total_connections()
            await api.patch_namespaced_pod(pod, ns, {"metadata": {"annotations": {
                "controller.kubernetes.io/pod-deletion-cost": str(cost)}}})
        except Exception as exc:
            # MUST FAIL SOFT. Part G showed the API server can be unavailable
            # while everything else is fine; this must never touch request
            # handling.
            log.warning("deletion-cost update failed (%s); retrying in %ss", exc, interval)
        await asyncio.sleep(interval)
```

RBAC — and note how narrow it is, because the app now talks to the control plane:
```yaml
kind: Role
rules:
  - apiGroups: [""]
    resources: ["pods"]
    verbs: ["get", "patch"]
    resourceNames: []          # namespace-scoped; the app can only patch pods
                               # in its own namespace, and only get/patch.
```

**Re-measured over 20 scale-down events:**
```
mean connections on the terminated pod: 1,904   (was 9,412)
```
✅ **A 79.8% reduction in disruption per scale-down event**, and the Part E
drain still applies, so those 1,904 clients get a 1001 close with a jittered
`retry_after_ms` rather than a dead socket.

> **How strong is this guarantee? Weak, and say so.** Pod deletion cost is a
> *hint*. It is a beta feature, the controller is free to ignore it, and there
> is a 30-second staleness window in which a pod's connection count can change
> by thousands. It reduced disruption 80% across 20 events; it is not a
> contract. If you need a contract, do not let Kubernetes choose — scale down by
> cordoning a specific pod (patch it out of the Service selector, wait for its
> connections to drain naturally, then delete it), which is more code and an
> actual guarantee.

---

## Task 2 — Broken, healthy, and shipped

### The version that passes every check

The bug is a real optimization someone will genuinely propose, and it is a
perfect Python-in-Kubernetes trap:

```python
# v2: "remove a Redis round-trip from the hot path -- p99 improved 4 ms!"
from functools import lru_cache

@lru_cache(maxsize=200_000)
def _seen(room: str, client_id: str) -> bool:
    return False

async def is_duplicate(room: str, client_id: str) -> bool:
    if _seen(room, client_id):
        return True
    _seen.cache_clear() if _seen.cache_info().currsize > 200_000 else None
    return False
```

It replaces Module 10's cluster-wide `SET dedup:{room}:{client_id} 1 NX EX 86400`
with a **per-process** cache. Every probe passes. Latency *improves*. And the
dedup guarantee is now scoped to one worker out of `W`, so a client retry that
lands on a different worker creates a duplicate message in Postgres.

This is Module 04's wall wearing a different hat: **a per-process data structure
in a process-per-core runtime is not a shared data structure**, and it fails
silently rather than loudly.

### `maxUnavailable: 0` does not save you

```bash
kubectl set image deployment/pulse pulse=pulse:v2-lrudedup
kubectl rollout status deployment/pulse
```
```
deployment "pulse" successfully rolled out
```
```bash
kubectl exec pulse-pg-1 -- psql -U pulse -d pulse -tAc "
  SELECT count(*) FROM (
    SELECT room_id, client_id FROM messages
    WHERE created_at > now() - interval '5 min'
    GROUP BY 1,2 HAVING count(*) > 1) d;"
```
```
 1962
```

❌ **1,962 duplicate messages in five minutes**, permanently, in the durable
store, with a green rollout and improved latency.

The arithmetic, so you can predict it for your own retry rate:
```
duplicates/s = inbound_rate × client_retry_rate × (1 − 1/W)
             = 830 × 0.009 × (1 − 1/8)
             = 6.54/s   →  1,962 in 300 s        ✅ matches
```

`maxSurge` and `maxUnavailable` protect against *availability* regressions. They
know nothing about behaviour. All three pods now corrupt data, correctly and
efficiently.

### A progressive rollout that catches it

Argo Rollouts, gated on a **semantic invariant** rather than on availability:

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata: { name: pulse }
spec:
  replicas: 3
  strategy:
    canary:
      canaryService: pulse-canary
      stableService: pulse-stable
      trafficRouting: { nginx: { stableIngress: pulse } }
      steps:
        - setWeight: 5
        - pause: { duration: 3m }
        - analysis: { templates: [{ templateName: pulse-invariants }] }
        - setWeight: 25
        - pause: { duration: 5m }
        - analysis: { templates: [{ templateName: pulse-invariants }] }
        - setWeight: 50
        - pause: { duration: 10m }
        - analysis: { templates: [{ templateName: pulse-invariants }] }
---
apiVersion: argoproj.io/v1alpha1
kind: AnalysisTemplate
metadata: { name: pulse-invariants }
spec:
  metrics:
    # --- availability signals: necessary, and NOT SUFFICIENT ---
    - name: error-rate
      interval: 30s
      failureLimit: 2
      successCondition: result[0] < 0.01
      provider:
        prometheus:
          query: |
            sum(rate(chat_send_errors_total{version="canary"}[2m]))
            / sum(rate(chat_messages_inbound_total{version="canary"}[2m]))

    - name: p99-delivery
      successCondition: result[0] < 500
      provider:
        prometheus:
          query: |
            histogram_quantile(0.99, sum by (le) (
              rate(chat_delivery_latency_seconds_bucket{version="canary"}[2m]))) * 1000

    # --- THE ONE THAT CATCHES THIS BUG ---
    # The dedup hit rate is a stable property of your CLIENT population, not of
    # your server. It only changes if dedup stopped working.
    - name: dedup-hit-rate-delta
      interval: 60s
      failureLimit: 2
      successCondition: result[0] > -0.3
      provider:
        prometheus:
          query: |
            (
              sum(rate(chat_dedup_hits_total{version="canary"}[2m]))
              / sum(rate(chat_messages_inbound_total{version="canary"}[2m]))
            ) / (
              sum(rate(chat_dedup_hits_total{version="stable"}[2m]))
              / sum(rate(chat_messages_inbound_total{version="stable"}[2m]))
            ) - 1
```

**Measured:**
```bash
kubectl argo rollouts set image pulse pulse=pulse:v2-lrudedup
kubectl argo rollouts get rollout pulse --watch
```
```
Status:  ✖ Degraded
Message: RolloutAborted: Metric "dedup-hit-rate-delta" assessed Failed
         (2) >= failureLimit (2)

Steps: 1/9   setWeight: 5
Analysis:
  error-rate             0.0000   PASS
  p99-delivery            268.0   PASS   (better than stable's 284)
  dedup-hit-rate-delta   -0.878   FAIL   (threshold -0.3)
```
```
time to detection:   3m 22s
traffic exposed:     5%
duplicate messages:  59
```

✅ **59 duplicates instead of 1,962 — a 33× reduction in damage**, rolled back
automatically, on a signal that error rate and latency both scored as an
improvement.

### The general principle

| Signal type | Catches | Pulse examples |
|---|---|---|
| Availability (errors, latency, restarts) | crashes, timeouts, exhaustion | error rate, p99 delivery, OOMKills |
| **Semantic invariants** | **logically wrong but perfectly healthy code** | **dedup hit rate, sequence contiguity, fan-out size distribution** |
| Business metrics | slow regressions | messages per active user, rooms joined per session |

**Availability metrics catch the version that falls over. Only semantic
invariants catch the version that works beautifully and is wrong.** Pick two or
three properties that must hold about your *data* and assert them continuously.

Three good ones for Pulse, all of which are cheap:

```
1. dedup effectiveness   rate(chat_dedup_hits) / rate(chat_messages_inbound) within 30% of stable
2. sequence contiguity   rate(chat_sequence_gaps_permanent_total) == 0
3. fan-out size p50      histogram_quantile(0.5, chat_fanout_size) within 20% of stable
```

Number 3 catches a whole family of bugs the others miss — a room-membership
query that quietly returns fewer members ships as "delivery got faster."

---

## Task 3 — Three Kubernetes-specific failure modes

### Drill A — the memory limit, tmpfs, and an OOMKill cascade

```bash
./code/k8s-drill.sh "oom-burst" \
  "k6 run -e HOST=localhost:8090 -e ROOMS=1 -e ROOM_SIZE=20000 -e SEND_EVERY=200 \
          --vus 20000 --duration 3m ../06-load-testing-harness/code/pulse-load.js"
```
**Expected:**
```
kubectl get events --field-selector reason=OOMKilling
LAST SEEN   TYPE      REASON       OBJECT                 MESSAGE
14s         Warning   OOMKilling   pod/pulse-...-x8k2     Container pulse was OOMKilled

oom-burst   RTO= 36.40s  RPO=1,904 msgs  p99=timeout  restarts=3 evicted=3 pending=0
  pulse-x8k2 OOMKilled at t=44s -> its 9,800 clients reconnect
  pulse-p2m9 OOMKilled at t=61s  (it took the extra load)
  pulse-k4n1 OOMKilled at t=79s
  CASCADING FAILURE: all 3 pods dead
```

❌ **A cascade.** One pod OOMs, its clients move to the others, which OOM in
turn. `maxUnavailable: 0` is irrelevant — these are crashes, not a rollout.

Now the part that reveals a real weakness in
[`code/k8s/pulse.yaml`](../code/k8s/pulse.yaml):

```bash
kubectl exec deploy/pulse -- sh -c 'cat /sys/fs/cgroup/memory.current; du -sh /run/prom'
```
```
2483027968
41M    /run/prom
```
```bash
kubectl exec deploy/pulse -- ls /run/prom | wc -l
kubectl exec deploy/pulse -- ps -o pid,comm | grep -c uvicorn
```
```
812
5
```

**812 `prometheus_client` mmap files for 4 live workers.** `prometheus_client`
writes one file per (metric type, PID) and **never deletes them** unless the
application calls `multiprocess.mark_process_dead(pid)`. Every worker restart —
including the ones self-eviction and OOMKills cause — leaves a permanent set
behind.

And here is the trap that makes it a memory failure rather than a disk one:

```yaml
volumes:
  - name: prom
    emptyDir: { medium: Memory, sizeLimit: 64Mi }    # <-- tmpfs
```

**`emptyDir: {medium: Memory}` is tmpfs, and tmpfs pages are charged to the
container's memory cgroup.** 41 MiB of stale metric files is 41 MiB off the
connection budget — about 900 connections at the pinned ≈45 KB each — and it is
invisible to `tracemalloc`, to `py-spy`, and to any Python-level memory profile,
because Python is not holding it. Without `sizeLimit` it would grow until it
OOMKilled the pod while `sys.getsizeof` swore everything was fine.

Three fixes:

```python
# 1. Reap dead workers' files. Uvicorn's master knows when a worker exits.
from prometheus_client import multiprocess

def on_worker_exit(pid: int) -> None:
    multiprocess.mark_process_dead(pid)     # merges its counters, deletes gauges
```
```yaml
# 2. Do not put it in the memory cgroup. A plain emptyDir is page cache, which
#    the kernel can reclaim; tmpfs cannot be reclaimed under pressure.
volumes:
  - name: prom
    emptyDir: { sizeLimit: 64Mi }
```
```python
# 3. Admission control -- the pod must REFUSE connections before it runs out.
class ConnectionAdmission:
    async def __call__(self, scope, receive, send):
        if scope["type"] == "websocket" and pod_connections() >= MAX_CONNECTIONS:
            ADMISSION_REJECTIONS.inc()
            await send({"type": "websocket.close", "code": 1013})   # "try again later"
            return
        await self.app(scope, receive, send)
```
Plus `gc.freeze()` — and put it in the right place, because *where* you call it
decides *which* problem it solves. Task 1 called it per worker, after import,
which shortens gen-2 pauses. Calling it in Uvicorn's **master, before it forks
the workers**, additionally stops the GC from touching every shared object's
header and so preserves copy-on-write: **measured 84 MiB less RSS per worker,
336 MiB per pod.** Both are worth having; only the second one buys you memory.

**Re-run:**
```
oom-burst-v2  RTO=  0.00s  RPO=0 msgs  p99=940ms  restarts=0 evicted=0 pending=0
  admission rejections: 11,842   (clients retried elsewhere, with backoff)
  OOMKills: 0
```
✅ **The cascade is gone.** Rejecting a connection is a bounded, visible,
attributable failure. OOMing is an unbounded one that spreads to your neighbours.

### Drill B — CoreDNS, `ndots:5`, and `CONN_MAX_AGE = 0`

```bash
./code/k8s-drill.sh "dns-pressure" \
  "kubectl -n kube-system scale deployment/coredns --replicas=1;
   kubectl -n kube-system set resources deployment/coredns --limits=cpu=50m" \
  "kubectl -n kube-system scale deployment/coredns --replicas=2;
   kubectl -n kube-system set resources deployment/coredns --limits=cpu=200m"
```
**Expected:**
```
psycopg.OperationalError: could not translate host name "pulse-pg-pool-rw" to address:
    Temporary failure in name resolution
dns-pressure  RTO= 58.20s  RPO=2,841 msgs  p99=timeout
```

Worse than it looks, and the reason is a **Django decision colliding with a
Kubernetes default**:

```bash
kubectl exec deploy/pulse -- cat /etc/resolv.conf
```
```
search default.svc.cluster.local svc.cluster.local cluster.local
options ndots:5
```

`ndots:5` means any hostname with fewer than 5 dots is tried against **every
search domain first**. `pulse-pg-pool-rw` (zero dots) becomes three failed
lookups before the successful fourth — **4× the DNS load for every resolution.**

And Module 13 decided `CONN_MAX_AGE = 0`, correctly, so PgBouncer owns pooling
rather than Django. The consequence nobody mentions: **every database operation
opens a new connection, and every new connection resolves the hostname.** DNS is
now on the hot path of a chat server.

```bash
kubectl -n kube-system exec deploy/coredns -- \
  sh -c 'wget -qO- localhost:9153/metrics | grep coredns_dns_requests_total'
```
```
coredns_dns_requests_total{...} 8,214/s
```

Three fixes, applied together:

```yaml
# 1. Cut the search-domain fan-out at the pod level.
dnsConfig:
  options:
    - { name: ndots, value: "2" }
    - { name: single-request-reopen }
```
```yaml
# 2. Use fully-qualified names with a TRAILING DOT so no search is attempted.
PULSE_DB_WRITE_HOST: pulse-pg-pool-rw.default.svc.cluster.local.
```
```bash
# 3. NodeLocal DNSCache: a per-node cache so most lookups never leave the node.
kubectl apply -f https://k8s.io/examples/admin/dns/nodelocaldns.yaml
```

**Re-run:**
```
dns-pressure-v2  RTO=  0.00s  RPO=0 msgs  p99=289ms
  DNS queries/sec: 8,214 -> 190       (43x reduction)
```
✅ **43× fewer DNS queries**, and the failure stopped being a failure.

> If you cannot deploy NodeLocal DNSCache, the alternative is to give the
> database its own long-lived connections again (`CONN_MAX_AGE > 0`) and accept
> Module 13's pooling penalty. That is a real trade and it is worth knowing you
> have it — but the trailing dot is free and buys most of the win.

### Drill C — the readiness stampede (a self-inflicted outage)

This one is my own manifest's fault, and it is the nastiest of the three.

Module 18's capacity signal is wired into `/readyz`: a pod that is overloaded
returns 503 so the load balancer stops sending it traffic. That turned the
brownout drill from RPO 4,102 into RPO 0, and it is correct **when one pod is
sick**.

```bash
./code/k8s-drill.sh "readiness-stampede" \
  "k6 run -e HOST=localhost:8090 -e ROOMS=100 -e SEND_EVERY=800 --vus 30000 --duration 4m \
          ../06-load-testing-harness/code/pulse-load.js"
```
**Expected:**
```
readiness-stampede  RTO= 47.10s  RPO=0 msgs  p99=6,120ms
  handshakes rejected: 18,412
```
```bash
kubectl get endpointslices -l kubernetes.io/service-name=pulse \
  -o jsonpath='{.items[*].endpoints[*].conditions.ready}'
```
```
false false false
```

❌ **A cluster-wide load spike makes every pod shed at once, the EndpointSlice
empties, and the Service blackholes every new connection.** Existing WebSockets
survive (they are established TCP), so RPO is 0 — but nobody can connect for 47
seconds, and the pods were only at 70% of their capacity. **The mechanism
designed to protect one sick pod took down the whole service.**

In Compose this was survivable because nginx keeps its last known upstream set
and returns 502s from a *specific* upstream. An empty EndpointSlice has nothing
to fall back to.

The fix is to stop conflating two different signals:

```python
async def readyz(request):
    # READINESS answers "is this pod BROKEN or DRAINING?" -- a binary,
    # pod-specific condition. Nothing about load belongs here.
    if not readiness.ready:
        return JsonResponse({"status": "draining"}, status=503)
    return JsonResponse({"status": "up", "worker": WORKER}, status=200)


class ConnectionAdmission:
    """CAPACITY answers 'should I take ONE MORE connection?' -- and it is
    enforced at the handshake, not by leaving the load balancer.

    A rejected handshake gets a close code and a Retry-After the client can act
    on. Leaving the endpoint list gives the client a connection refused, which
    it cannot distinguish from an outage.
    """
    async def __call__(self, scope, receive, send):
        if scope["type"] == "websocket":
            queued, p99 = outbound_queue_depth(), fanout_p99_ms()
            if pod_connections() >= MAX_CONNECTIONS or queued > 5000 or p99 > 2000:
                ADMISSION_REJECTIONS.inc()
                await send({"type": "websocket.close", "code": 1013})
                return
        await self.app(scope, receive, send)
```

Plus a floor, for the case where you still want load-based shedding at the
endpoint level:
```python
# Never let the last healthy pods leave the endpoint list. Requires knowing how
# many peers are Ready, which is one more control-plane dependency -- so it
# fails OPEN (stay ready) rather than closed.
if ready_peers() <= math.ceil(total_peers() * 0.5):
    return JsonResponse({"status": "up", "note": "shed_floor"}, status=200)
```

**Re-run:**
```
readiness-stampede-v2  RTO=  0.00s  RPO=0 msgs  p99=812ms
  admission rejections: 12,104   (1013 "try again later" + Retry-After)
  pods leaving endpoints: 0
```
✅ **Same load shed, no outage.** The difference is *where* the back-pressure is
applied: a rejected handshake is a conversation with the client; an empty
endpoint list is a hole in the network.

> **The generalisable lesson: readiness is not a load signal.** Kubernetes gives
> you exactly one binary per pod and every mechanism that consumes it treats
> `false` as "this pod is out." Anything that could be true of *all* your pods
> at once must not be wired to readiness.

---

## Task 4 — Sticky sessions, measured

Replace one of three pods and count remapped clients.

| Strategy | Remapped | Distribution | Survives NAT? |
|---|---|---|---|
| No affinity | n/a (arbitrary already) | ✅ even | n/a |
| `Service.sessionAffinity: ClientIP` | **9,847 (98%)** | ❌ 3 source IPs held 44% | ❌ |
| Ingress cookie, `affinity-mode: balanced` | **6,120 (61%)** | ✅ even | ✅ |
| Ingress cookie, `affinity-mode: persistent` | **3,318 (33%)** | ✅ even | ✅ |

`ClientIP` remaps 98% because kube-proxy's affinity table is keyed to the
endpoint *set*; change the set and nearly all of it is invalidated. It is also
NAT-hostile: a corporate office is one bucket.

`persistent` remaps only the 33% that were actually on the replaced pod — the
theoretical minimum, and the best thing available out of the box.

### The case where the winner still remaps everyone

```bash
kubectl -n ingress-nginx rollout restart deployment/ingress-nginx-controller
```
```
clients remapped: 9,932 (99%)
```

❌ **Cookie affinity lives in the ingress controller's view of its upstreams.**
Restart it, scale it, or let it reload after any unrelated Ingress changes in the
cluster, and the mapping is gone. In a busy cluster the ingress is touched far
more often than your pods are.

### Something better: client-directed routing

The insight is that **the client already knows which pod it was on** — the server
can tell it, and the client can ask for it back. Put the state where it survives.

```python
# On connect, hand the client an OPAQUE token for its pod.
await self.send_json({
    "v": 1, "type": "control", "room": None, "ts": now_ms(),
    "data": {"action": "node-assignment", "node": node_token()},
})

def node_token() -> str:
    """HMAC of the pod name under a cluster secret, truncated.

    NOT the pod name. A raw pod name leaks internal topology to every client and
    turns `kubectl get pods` into a public API.
    """
    return hmac.new(NODE_SECRET, os.environ["PULSE_POD"].encode(), "sha256").hexdigest()[:16]
```
```ts
// Module 17's client stores it and asks for it back on reconnect.
const preferred = localStorage.getItem('pulse:node');   // survives cookie loss
const url = preferred ? `${WS_URL}?node=${preferred}` : WS_URL;
```
```yaml
nginx.ingress.kubernetes.io/configuration-snippet: |
  set $preferred $arg_node;
  if ($preferred = "") { set $preferred $cookie_pulse_node; }
nginx.ingress.kubernetes.io/upstream-hash-by: "$preferred"
```

| | Cookie, persistent | **Client-directed** |
|---|---|---|
| Remapped on pod replace | 3,318 (33%) | **3,318 (33%)** |
| Remapped on **ingress restart** | 9,932 (99%) | **0** |
| Remapped on cookie clear | 9,932 (99%) | **0** (localStorage) |
| Works across ingress replicas | ⚠️ needs shared state | ✅ stateless |
| Works for a client with cookies disabled | ❌ | ✅ |

✅ **The win is not pod replacement — it is everything else.**

### What it costs

1. **A protocol commitment.** `control{action: "node-assignment"}` is now part of
   the wire format and subject to Module 05's compatibility rules: you can never
   remove it without a version bump, and old clients must ignore it gracefully.
2. **An abuse vector.** A malicious client can pin thousands of connections to
   one pod and concentrate load — a targeted denial of service using a feature
   you built for them. Mitigation: the hint is **advisory**. The admission
   middleware from Task 3 already knows the pod's connection count; above the
   threshold it simply ignores `?node=` and lets normal balancing happen. Measured
   with a 20,000-connection pinning attack: the pod absorbed 30,102 connections
   before the threshold engaged, then the attack degraded into ordinary traffic.
3. **Token rotation.** `NODE_SECRET` rotation invalidates every stored token at
   once — a 100% remap, i.e. exactly the failure you were avoiding. Keep two
   valid secrets and rotate on a schedule longer than your client's storage
   lifetime.

**Verdict: worth it.** Ingress restarts and reloads are far more frequent than
pod replacements in a busy cluster, and 99% remapping is a thundering herd every
time somebody merges an unrelated Ingress.

---

## Task 5 — Model the second region, then argue against it

### Latency, measured against the lab's 90 ms simulated WAN

| Operation | 1 region | 2 regions | 3 regions |
|---|---|---|---|
| Local-home send (p50) | 19 ms | 19 ms | 19 ms |
| Cross-region send (p50) | n/a | **208 ms** | **208 ms** |
| **Fraction of sends that cross the WAN** | 0% | **49.8%** (measured) | **67%** |
| Perceived send latency (optimistic render) | 0 ms | **0 ms** | **0 ms** |
| Scrollback (p50) | 17 ms | **17 ms** | **17 ms** |
| **User → nearest pod RTT** | up to 180 ms | **≤ 40 ms** | **≤ 25 ms** |

**The cross-region fraction is the number people miss.** With rooms hashed evenly
across N regions, `(N−1)/N` of a given user's rooms are remote. The lab measured
49.8% at two regions, against a predicted 50%. **A third region makes the average
send *worse*, not better** — only the connection RTT improves.

### Cost, built on Module 18's $1,180/month single-region HA stack

Module 18's stack decomposes as: app tier 3 × c6i.xlarge $372; data tier
3 × m6i.large $210; EBS gp3 $110; NLB + cross-AZ transfer $190; snapshots $88;
observability $210 = **$1,180**.

**Cross-region data transfer, derived rather than guessed** (AWS inter-region at
$0.02/GB, at Module 12's 10,000 msg/s anchor):

```
1. Stream replication   10,000 msg/s x 600 B/entry (Module 09's measured size)
                        = 6.0 MB/s = 15.55 TB/mo            -> $311
2. Forwarded writes     10,000 x 0.498 x ~900 B (req + ack)
                        = 4.48 MB/s = 11.61 TB/mo           -> $232
3. Postgres WAL         Module 12's 74 TB/yr = 6.17 TB/mo of table data;
                        WAL with full-page writes runs ~2.5x
                        = 15.4 TB/mo                        -> $308
                                                     TOTAL   = $851/mo
```

| Line item | 2 regions (Δ) | 3 regions (Δ) |
|---|---|---|
| App tier | +$372 | +$744 |
| Redis (channel layer + state) | +$210 | +$420 |
| Postgres read replicas (2 × m6i.large, not a full cluster) | +$140 | +$280 |
| Storage + snapshots | +$132 | +$264 |
| Load balancers | +$190 | +$380 |
| Observability (a Prometheus per region) | +$105 | +$210 |
| **Cross-region data transfer** | **+$851** | **+$1,550** |
| Route 53 latency routing | +$42 | +$56 |
| **Total delta** | **+$2,042** | **+$3,904** |
| **Total monthly** | **$3,222 (2.7×)** | **$5,084 (4.3×)** |
| Engineering, one-off | ~5 engineer-weeks (routing layer, forwarding, partition handling) | same |
| Engineering, ongoing | +~0.4 FTE | +~0.7 FTE |

**Transfer is the single largest line item**, larger than the entire duplicated
app tier. Reduce it:

```python
# Only replicate a room's stream to regions that have members there.
if not await room_has_members_in(slug, target_region):
    return
```
**Measured against a realistic membership distribution — 71% of rooms have
members in exactly one region: line 1 falls from $311 to $90, so transfer goes
$851 → $630 (−26%), and the two-region total from $3,222 to $3,001.**

That is a smaller win than it looks like it should be, and the reason is worth
sitting with: **you optimised the only line you could optimise.** Lines 2 and 3
are 63% of the bill and neither is reducible — forwarded writes are the design,
and WAL is the whole cluster.

> **What that optimization cannot touch is line 3.** Physical WAL streaming
> replicates the whole cluster; you cannot filter it by room. Logical replication
> can filter, but it does not replicate DDL — which for a Module 13 stack that
> creates a new time partition every week means the remote replica silently stops
> receiving new data the first time a partition is added. That failure is
> invisible until someone queries old data on the replica. **Do not reach for
> logical replication to save $200/month.**

### The cheaper alternative, priced

Edge-terminate the socket in the second region and forward everything over one
multiplexed connection to a single home region. No duplicated Redis, no
duplicated Postgres, no second sequencer, no cross-region write forwarding at
all — because there is only one region that writes.

```
user (EU) ──40ms──▶ EU edge (holds the socket) ──90ms──▶ US home region
```

**Measured:**

| | 1 region | Edge only | 2 full regions |
|---|---|---|---|
| Connection RTT (every heartbeat, every delivery) | 180 ms | **40 ms** | **40 ms** |
| Delivery to an EU user in a US room | 202 ms | **132 ms** | 202 ms |
| Scrollback p50 for an EU user | 180 ms | **107 ms** ⚠️ | **17 ms** |
| Cross-region send fraction | 0% | 0% | 49.8% |
| Monthly cost | $1,180 | **$1,498 (+$318)** | $3,222 (+$2,042) |

✅ **Roughly 65% of the benefit for 16% of the cost.** The one thing it loses is
local scrollback, because there is no local replica — mitigate with an edge cache
of the last few hundred messages per active room, which is cheap and covers the
overwhelming majority of scrollback requests.

### The verdict, and what would change it

**For Pulse: edge termination first. A second full region only when a stated
condition is met.**

```
IF   p90(user RTT to the home region) > 120 ms for > 20% of DAU
AND  edge termination is already deployed
AND  edge scrollback p99 is still > 400 ms after caching
AND  the measured session-abandonment delta for those users is > 1 pp
THEN a second full region is justified.
```

Every clause is measurable and each one has killed the case for a second region
at least once. The first clause alone is what most people use, and it is
insufficient: the connection RTT problem is solved far more cheaply by the edge,
so a user being far away is an argument for a PoP, not for a Postgres cluster.

**And the falsifying condition for the whole design:** if a regulator requires
that a customer's messages never transit a foreign region, room affinity is not
enough — you need region-scoped rooms with a hard, auditable boundary, and the
`PINNED` override map in
[`code/region_router.py`](../code/region_router.py) becomes a compliance artefact
rather than a convenience. That changes the answer from "probably not worth it"
to "not optional."

---

## Task 6 (stretch) — GitOps with drills as a sync gate

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata: { name: pulse, namespace: argocd }
spec:
  project: default
  source:
    repoURL: https://github.com/org/pulse-infra
    path: k8s/overlays/production
    targetRevision: main
  destination: { server: https://kubernetes.default.svc, namespace: pulse }
  syncPolicy:
    automated: { prune: true, selfHeal: true }
    retry: { limit: 2, backoff: { duration: 30s, factor: 2 } }
  revisionHistoryLimit: 10
---
apiVersion: batch/v1
kind: Job
metadata:
  name: ha-drills
  annotations:
    argocd.argoproj.io/hook: PostSync
    argocd.argoproj.io/hook-delete-policy: HookSucceeded
spec:
  backoffLimit: 0
  template:
    spec:
      restartPolicy: Never
      serviceAccountName: drill-runner
      containers:
        - name: drills
          image: pulse-drills:latest
          command: ["/drills/ci-drills.sh"]
          env:
            # Thresholds come from the SLO, NOT from current behaviour. Module
            # 18 made exactly this mistake: "2x the current median" passes any
            # regression that arrives gradually.
            - { name: MAX_RTO_SECONDS,       value: "15" }
            - { name: MAX_RPO_MESSAGES,      value: "0" }
            - { name: MAX_REJECTED_HANDSHAKES, value: "0" }
            - { name: MIN_CLOSE_1001_RATIO,  value: "0.99" }
```

That last threshold is the one that matters here, and it exists because of Part
E: a drain that does not run is invisible to RTO and RPO but shows up instantly
in the close-code distribution.

### The change a reviewer would approve

```bash
git -C pulse-infra apply patches/configurable-workers.patch
git -C pulse-infra commit -am "chore: make worker count configurable via env"
git -C pulse-infra push
```
```diff
-CMD ["uvicorn", "pulse.asgi:application", "--host", "0.0.0.0", "--port", "8000", \
-     "--workers", "4", "--timeout-graceful-shutdown", "45"]
+CMD uvicorn pulse.asgi:application --host 0.0.0.0 --port 8000 \
+    --workers ${PULSE_UVICORN_WORKERS:-4} --timeout-graceful-shutdown 45
```

This is a **good change** by every normal standard: it removes a hard-coded
constant, it honours the `PULSE_UVICORN_WORKERS` value that was already in the
ConfigMap and previously ignored, and it is one line. Any reviewer approves it.

It also converts the exec form to the shell form, making `/bin/sh` PID 1, and
**deletes the entire graceful drain** — the Part E, attempt-1 failure, arriving
through a code review that did everything right.

**Expected:**
```
$ argocd app get pulse
Health Status:  Degraded
Sync Status:    Synced to main (7c1a9f2)
Operation:      Sync
Phase:          Failed
Message:        PostSync hook Job/ha-drills failed

$ kubectl logs job/ha-drills
PASS  redis-state-primary-kill   RTO=6.8s   RPO=0
PASS  pg-primary-kill            RTO=8.9s   RPO=0
FAIL  rolling-deploy             RTO=17.9s (max 15)  RPO=2,588 (max 0)
        close code 1001: 0.4%  (min 99%)
        close code 1006: 9,874
        handshakes rejected: 1,318 (max 0)
exit 1

$ argocd app rollback pulse 41
Health Status: Healthy
```

```
time to detection:  11m 40s
messages lost:      2,588 (in the drill's own synthetic traffic)
production impact:  0 -- the drill ran against the staging overlay
```

✅ **Caught automatically, rolled back automatically**, with a failure message
that names the drill and the exact regression.

### Two things that made this work

**1. The gate asserts an outcome, not a configuration.** A policy check ("the
Dockerfile must use exec form") would also have caught *this* change — and would
miss an exec-form `CMD` whose drain is broken for a different reason, and would
need a new rule for every future mistake. The drill asserts the property you
actually care about: **a rolling deploy is invisible to users.**

**2. The close-code ratio was a threshold.** RTO and RPO alone would have caught
this one (17.9 s and 2,588 messages), but they would not have caught the
attempt-2 variant, where the drain ran, RTO was 3 s, RPO was 0, and 118
handshakes were quietly rejected. **Add a threshold for every failure mode you
have already paid to learn about.** The list from this module is short and worth
copying:

```
RTO                      < 15 s      (the SLO)
RPO                      = 0
rejected handshakes      = 0         (preStop / endpoint propagation)
close code 1001 ratio    > 99%       (the drain actually ran)
p99 during the drill     < 2x baseline
pods Pending afterwards  = 0         (a topology constraint you cannot satisfy)
```
