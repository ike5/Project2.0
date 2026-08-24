# Lab 19 — Zero-Drop Deploys and a Second Region

**You'll:** port the Module 18 stack to `kind`, build a genuinely zero-drop
rolling deploy in three attempts so you can see what each piece contributes,
prove a PodDisruptionBudget blocks a quorum-breaking drain, measure the
replica-count knee against Module 07's channel-layer cost model, re-run the
Module 18 drills against Kubernetes, and build edge-terminated multi-region with
room affinity.

⏱️ ~140 min. Needs ~10 GB RAM for the four-node path.

> **Low-memory path (~5 GB):** delete the three `worker` entries from
> `code/k8s/kind-cluster.yaml` and run a single node with 2 app replicas. You
> lose Part G (node drains, PDB enforcement, topology spread) because there is
> nowhere to drain to, and Part F's 3-replica measurement will be CPU-starved
> rather than Redis-bound. Everything else works. Parts are flagged.

All paths are relative to the repo root. Manifests live in
[`code/k8s/`](./code/k8s/); the drill harness is
[`code/k8s-drill.sh`](./code/k8s-drill.sh).

---

## Part A — The cluster

```bash
cd django-chat-course
kind create cluster --name pulse --config 19-kubernetes-ha-and-multiregion/code/k8s/kind-cluster.yaml
kubectl get nodes -L topology.kubernetes.io/zone
```
**Expected:**
```
NAME                  STATUS   ROLES           AGE   ZONE
pulse-control-plane   Ready    control-plane   64s
pulse-worker          Ready    <none>          42s   zone-a
pulse-worker2         Ready    <none>          42s   zone-b
pulse-worker3         Ready    <none>          42s   zone-c
```

The zone labels are fake and the scheduler believes them completely. That is what
makes local topology drills possible.

Install the ingress controller and apply the controller-level settings:

```bash
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml
kubectl wait -n ingress-nginx --for=condition=ready pod \
  --selector=app.kubernetes.io/component=controller --timeout=180s

# Only the ConfigMap document from ingress.yaml — the Ingress itself comes later.
kubectl -n ingress-nginx patch configmap ingress-nginx-controller --type merge -p "$(
  yq 'select(.kind == "ConfigMap")' 19-kubernetes-ha-and-multiregion/code/k8s/ingress.yaml | yq -o json
)"
kubectl -n ingress-nginx rollout restart deployment ingress-nginx-controller
```
**Expected:**
```
configmap/ingress-nginx-controller patched
deployment.apps/ingress-nginx-controller restarted
```

Confirm the setting that matters most took:
```bash
kubectl -n ingress-nginx exec deploy/ingress-nginx-controller -- \
  grep -m1 'proxy_read_timeout' /etc/nginx/nginx.conf
```
**Expected:**
```
proxy_read_timeout 3600s;
```
✅ **The default was 60 seconds.** ingress-nginx is a *different* nginx from the
one you configured in Module 18, with different defaults, and it silently kills
idle WebSockets. Module 11's 10-second heartbeat means healthy sockets never
idle that long — so the failure only appears for users whose browser backgrounded
the tab and throttled its timers, and it looks exactly like a client bug.

---

## Part B — Redis, two topologies

Module 18 concluded with **two Redis topologies for two jobs**, because
`channels_redis` shards by group name and knows nothing about cluster hash slots.
A plain `PUBLISH` on a Redis Cluster is broadcast to every node: the right answer
at roughly triple the cost, forever, with no error to tell you.

```bash
kubectl apply -f 19-kubernetes-ha-and-multiregion/code/k8s/redis.yaml
kubectl rollout status statefulset/redis-cl
kubectl get pods -l tier=channel-layer -o wide
```
**Expected — one per zone, and note that these are *independent shards*, not
replicas of each other:**
```
NAME         READY   STATUS    NODE            ZONE
redis-cl-0   1/1     Running   pulse-worker    zone-a
redis-cl-1   1/1     Running   pulse-worker2   zone-b
redis-cl-2   1/1     Running   pulse-worker3   zone-c
```

Per-pod DNS is the reason these are a StatefulSet rather than a Deployment:

```bash
kubectl run dnstest --rm -it --restart=Never --image=busybox:1.36 -- \
  nslookup redis-cl-1.redis-cl.default.svc.cluster.local
```
**Expected:**
```
Name:      redis-cl-1.redis-cl.default.svc.cluster.local
Address 1: 10.244.2.7 redis-cl-1.redis-cl.default.svc.cluster.local
```
✅ **`CHANNEL_LAYERS["hosts"]` lists three specific names.** Delete `redis-cl-1`
and it comes back — possibly on a different node — with the same name. A
Deployment cannot give you that, which is why the app tier (Part D) is a
Deployment and this is not.

### Form the state cluster

```bash
kubectl rollout status statefulset/redis-state
kubectl exec redis-state-0 -- redis-cli --cluster create --cluster-yes --cluster-replicas 1 \
  $(for i in 0 1 2 3 4 5; do
      echo -n "$(kubectl get pod redis-state-$i -o jsonpath='{.status.podIP}'):6379 "
    done)
```
**Expected:**
```
>>> Performing hash slots allocation on 6 nodes...
Master[0] -> Slots 0 - 5460
Master[1] -> Slots 5461 - 10922
Master[2] -> Slots 10923 - 16383
[OK] All 16384 slots covered.
```

Verify the hash tags you have been placing since Module 08 still do their job:

```bash
kubectl exec redis-state-0 -- redis-cli -c CLUSTER KEYSLOT "room:{7}:seq"
kubectl exec redis-state-0 -- redis-cli -c CLUSTER KEYSLOT "room:{7}:stream"
kubectl exec redis-state-0 -- redis-cli -c CLUSTER KEYSLOT "presence:{7}"
```
**Expected — the same slot, three times:**
```
(integer) 1716
(integer) 1716
(integer) 1716
```
✅ **Slot 1716 for all three**, because only the text between the first `{` and
the first `}` is hashed. `room:{7}:seq` and `room:{7}:stream` and `presence:{7}`
all hash `7`. Four characters of hash tag, decided in Module 08 on a
single-node Redis, are why the Lua scripts in Modules 09, 10 and 11 run here
without a rewrite.

### Prove the topology constraint bites

**Skip on the single-node path.**

```bash
kubectl scale statefulset/redis-state --replicas=7
kubectl get pod redis-state-6
```
**Expected:**
```
NAME             READY   STATUS
redis-state-6    0/1     Pending
```
```bash
kubectl describe pod redis-state-6 | grep -A2 'Events:'
```
```
Warning  FailedScheduling  0/4 nodes are available: 1 node(s) had untolerated
taint {node-role.kubernetes.io/control-plane: }, 3 node(s) didn't match pod
topology spread constraints.
```
✅ **`Pending`, not silently co-located.** With `whenUnsatisfiable:
ScheduleAnyway` — which is what the app tier uses — this pod would have landed a
third state-Redis in zone-a and nothing would have told you. A `Pending` pod is a
visible problem; a co-located quorum is an invisible one that becomes visible
during the outage.

```bash
kubectl scale statefulset/redis-state --replicas=6
```

---

## Part C — Postgres via CloudNativePG

```bash
kubectl apply --server-side -f \
  https://raw.githubusercontent.com/cloudnative-pg/cloudnative-pg/release-1.24/releases/cnpg-1.24.0.yaml
kubectl wait --for=condition=Available deployment/cnpg-controller-manager \
  -n cnpg-system --timeout=180s

kubectl apply -f 19-kubernetes-ha-and-multiregion/code/k8s/postgres.yaml
kubectl wait --for=condition=Ready cluster/pulse-pg --timeout=600s
kubectl get cluster pulse-pg
kubectl get svc -l cnpg.io/cluster=pulse-pg
```
**Expected:**
```
NAME       AGE   INSTANCES   READY   STATUS                     PRIMARY
pulse-pg   4m    3           3       Cluster in healthy state   pulse-pg-1

NAME          TYPE        PORT(S)
pulse-pg-rw   ClusterIP   5432/TCP    <-- writes: always the current primary
pulse-pg-ro   ClusterIP   5432/TCP    <-- reads: replicas only
pulse-pg-r    ClusterIP   5432/TCP    <-- reads: any instance
```

✅ **`-rw` and `-ro` are exactly what Module 18's HAProxy `:5000` and `:5001`
were doing by hand**, except the operator updates the endpoints on failover
instead of HAProxy polling each Patroni's `/primary`.

One CRD replaced eight containers:

| Module 18 (Compose) | Module 19 (Kubernetes) |
|---|---|
| 3 × Patroni | `spec.instances: 3` |
| 3 × etcd | **the Kubernetes API server is the DCS** |
| HAProxy `:5000` / `:5001` | `pulse-pg-rw` / `pulse-pg-ro` Services |
| PgBouncer container | the `Pooler` CRD |

That second row is the biggest structural change in the module and Part G
measures what it costs.

### Django's side has not changed at all

```bash
kubectl get configmap pulse-db-config -o jsonpath='{.data}' | jq
```
```json
{
  "PULSE_DB_WRITE_HOST": "pulse-pg-pool-rw",
  "PULSE_DB_READ_HOST": "pulse-pg-ro",
  "PULSE_DB_PREPARE_THRESHOLD": "none",
  "PULSE_DB_CONN_MAX_AGE": "0"
}
```

Those last two are Module 13 findings and an operator does not fix them:

```python
# pulse/settings/k8s.py
DATABASES = {
    "default": {                                    # writes, via the Pooler
        "ENGINE": "django.db.backends.postgresql",
        "HOST": os.environ["PULSE_DB_WRITE_HOST"],
        "OPTIONS": {
            # psycopg3 prepares a statement after 5 executions. Behind a
            # TRANSACTION-mode pooler the 6th execution may land on a different
            # server connection, which has never heard of the statement.
            "prepare_threshold": None,
        },
        "CONN_MAX_AGE": 0,   # Django's pool and PgBouncer's pool are both pools
    },
    "replica": {                                    # reads, via pulse-pg-ro
        "ENGINE": "django.db.backends.postgresql",
        "HOST": os.environ["PULSE_DB_READ_HOST"],
        "OPTIONS": {"prepare_threshold": None},
        "CONN_MAX_AGE": 0,
    },
}
DATABASE_ROUTERS = ["chat.routers.ReplicaRouter"]    # Module 13, unchanged
```

Prove the router is pointed at a real replica:
```bash
kubectl exec -it pulse-pg-2 -- psql -U postgres -c 'SELECT pg_is_in_recovery();'
```
```
 pg_is_in_recovery
-------------------
 t
```

---

## Part D — The app, and the trap that eats your drain

Build and load the image:

```bash
docker build -t pulse:local apps/pulse
kind load docker-image pulse:local --name pulse
kubectl apply -f 19-kubernetes-ha-and-multiregion/code/k8s/pulse.yaml
kubectl apply -f <(yq 'select(.kind == "Ingress")' \
                     19-kubernetes-ha-and-multiregion/code/k8s/ingress.yaml)
kubectl rollout status deployment/pulse
curl -s localhost:8090/readyz | jq
```
**Expected:**
```json
{ "status": "up", "outbound_queue": 0, "worker": "pid-9" }
```

### The liveness probe cannot see a blocked worker

Before trusting any of this, measure the blind spot the README claimed.

Each pod runs Uvicorn with **4 worker processes** sharing one listening socket.
Ask `/healthz` which worker answered, twenty times:

```bash
for i in $(seq 20); do curl -s localhost:8090/healthz | jq -r .worker; done | sort | uniq -c
```
**Expected — roughly even, and different every run:**
```
   6 pid-9
   4 pid-10
   5 pid-11
   5 pid-12
```

Now block one worker's event loop the way Module 15 did, with a synchronous ORM
call in an async consumer:

```bash
kubectl exec deploy/pulse -- python -c "
import os, signal, time
# Send SIGUSR1 to ONE worker; the app's debug handler runs time.sleep(30) on
# the event loop, which is exactly what a sync ORM call does.
os.kill(int(open('/run/pulse/workers').read().split()[0]), signal.SIGUSR1)"

# Watch the pod's status for 60 seconds.
kubectl get pod -l app=pulse -w --output-watch-events &
for i in $(seq 20); do curl -s -m2 localhost:8090/healthz -o /dev/null -w '%{http_code} '; done; echo
```
**Expected:**
```
200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200
```
```
NAME                     READY   STATUS    RESTARTS   AGE
pulse-7d4f8c9b4-x8k2     1/1     Running   0          6m      <-- unchanged
```

❌ **Twenty consecutive 200s, zero restarts, and a quarter of that pod's
connections are frozen.** The blocked worker never calls `accept()`, so the
kernel hands every probe to a healthy worker. With `failureThreshold: 3` you
need three consecutive probes to land on the blocked worker: `0.25³ = 1.6%` per
cycle.

Now look at the signal that *does* see it:
```bash
kubectl exec deploy/pulse -- curl -s localhost:8000/metrics \
  | grep chat_event_loop_lag_seconds
```
**Expected:**
```
chat_event_loop_lag_seconds{worker="pid-9"}   0.0004
chat_event_loop_lag_seconds{worker="pid-10"}  29.7412      <-- there it is
chat_event_loop_lag_seconds{worker="pid-11"}  0.0003
chat_event_loop_lag_seconds{worker="pid-12"}  0.0005
```

✅ **The `worker` label is doing all the work.** Aggregate it with `avg` and you
get 7.4 seconds, which looks like a mildly unhealthy pod. Aggregate it with
`max` and you get the truth. [Module 20](../20-observability-and-slos/) builds
the alert; the point here is that **Kubernetes probes are pod-granular and your
failure domain is process-granular.** Anything smaller than a pod, Kubernetes
cannot see — a direct consequence of the GIL forcing several processes per box
([Module 01](../01-python-async-concurrency/)).

> **Do not "fix" this with liveness.** Restarting the pod kills three healthy
> workers to punish one, and a restart is the most expensive action available to
> a socket server. The challenge builds the right fix: a worker that takes
> *itself* out.

---

## Part E — The zero-drop rolling deploy, in three attempts

**The headline drill.** Put load on first and leave it there for the whole part:

```bash
k6 run -e HOST=localhost:8090 -e ROOMS=100 -e SEND_EVERY=5000 \
       --vus 10000 --duration 25m \
       ../06-load-testing-harness/code/pulse-load.js &
sleep 120
```

Baseline, for comparison against Module 18's HA stack:
```
fanout_latency_ms: p(50)=14ms  p(99)=272ms
ws_errors: 0.00%
```
(Module 18's Compose baseline was p99 261 ms. The extra 11 ms is the ingress
hop; the two are otherwise the same stack.)

### Attempt 1 — the shell-form `CMD`

This is not a strawman. It is the most common Dockerfile in Python, and it
deletes your entire drain.

```bash
kubectl set image deployment/pulse pulse=pulse:v2-shellform
kubectl rollout status deployment/pulse
```
**Expected:**
```
deployment "pulse" successfully rolled out
```
```
fanout_latency_ms: p(99)=8,720ms
ws_errors: 4.31%
connections closed with code 1006: 9,882
connections closed with code 1001:      0
handshakes rejected during rollout: 1,341
messages lost: 2,610
median time for a client to notice: 46s
```

❌ **Zero 1001 closes. The drain never ran.** The rollout went green, the pods
terminated, and 9,882 clients got a bare TCP close.

```bash
kubectl logs deployment/pulse --previous | grep -c 'pulse.drain'
```
```
0
```

The image:
```dockerfile
CMD uvicorn pulse.asgi:application --host 0.0.0.0 --port 8000 --workers 4
```

Docker's **shell form** wraps that in `/bin/sh -c`. The shell becomes PID 1,
receives SIGTERM, and does not forward it. Uvicorn never learns it is shutting
down, `lifespan.shutdown` never fires, the connection registry is never drained,
and 90 seconds later the kubelet SIGKILLs everything.

Prove the mechanism:
```bash
kubectl exec deploy/pulse -- ps -o pid,comm
```
```
PID   COMMAND
  1   sh                 <-- PID 1 is the shell
  7   uvicorn
  9   uvicorn
 ...
```

Fix it — exec form, so Uvicorn is PID 1:
```dockerfile
CMD ["uvicorn", "pulse.asgi:application", "--host", "0.0.0.0", "--port", "8000", \
     "--workers", "4", "--timeout-graceful-shutdown", "45"]
```
```bash
kubectl set image deployment/pulse pulse=pulse:v2
kubectl rollout status deployment/pulse
kubectl exec deploy/pulse -- ps -o pid,comm | head -3
```
```
PID   COMMAND
  1   uvicorn            <-- ✅
```

> **The tell is that attempt 1 looks like it works.** Every Kubernetes-visible
> signal was green. Only the close-code distribution in the client says
> otherwise, which is why this drill counts close codes rather than trusting
> `rollout status`.

### Attempt 2 — drain runs, but no `preStop`

```bash
kubectl patch deployment pulse --type=json \
  -p='[{"op":"remove","path":"/spec/template/spec/containers/0/lifecycle"}]'
kubectl rollout restart deployment/pulse && kubectl rollout status deployment/pulse
```
**Expected:**
```
fanout_latency_ms: p(99)=1,940ms
ws_errors: 0.38%
connections closed with code 1006:     0
connections closed with code 1001: 9,908   (with retry_after_ms)
handshakes rejected during rollout:  118   <-- still!
messages lost: 0
```

✅ Clients now get a reason and a jittered `retry_after_ms`.
❌ **118 handshakes still failed.**

Prove why:
```bash
kubectl get endpointslices -l kubernetes.io/service-name=pulse -w \
  -o custom-columns='TS:.metadata.creationTimestamp,ADDRS:.endpoints[*].addresses'
```
**Expected during a rollout:**
```
(t=0.000)  ["10.244.1.5","10.244.2.7"]
(t=0.618)  ["10.244.2.7"]                 <-- 618 ms to remove one endpoint
```

Endpoint removal and SIGTERM are **concurrent**. Removal has to propagate through
the endpoints controller, every kube-proxy, every node's iptables rules, and the
ingress controller's upstream list. That took 618 ms here, during which the
ingress kept routing new upgrade requests to a pod that had already stopped
calling `accept()`.

### Attempt 3 — the full sequence

```bash
kubectl apply -f 19-kubernetes-ha-and-multiregion/code/k8s/pulse.yaml   # preStop back
kubectl rollout restart deployment/pulse && kubectl rollout status deployment/pulse
```
**Expected:**
```
fanout_latency_ms: p(50)=15ms  p(99)=284ms        (baseline 272ms)
ws_errors: 0.00%
sequence_gaps: 0
connections closed with code 1001: 9,921   (with retry_after_ms)
handshakes rejected during rollout: 0
messages lost: 0
reconnect peak: 196/s over 33s
total rollout duration: 3m 12s
```

✅ **Zero errors, zero lost messages, p99 up 12 ms from baseline.**

| | Shell-form CMD | exec form, no preStop | **Full sequence** |
|---|---|---|---|
| p99 during | 8,720 ms | 1,940 ms | **284 ms** |
| `ws_errors` | 4.31% | 0.38% | **0.00%** |
| Rejected handshakes | 1,341 | 118 | **0** |
| Close code | 1006 (unknown) | 1001 + `retry_after_ms` | 1001 + `retry_after_ms` |
| Messages lost | 2,610 | 0 | **0** |
| Client notices in | median 46 s | median 4 ms | **median 4 ms** |

Watch one pod drain:
```bash
kubectl logs -f deployment/pulse | grep -E 'pulse.drain'
```
```
pulse.drain  draining 3,307 sessions
pulse.drain  drained 3,307 sessions
```

### The double-wait, measured

Module 18's SIGTERM handler already waits `PULSE_DRAIN_DELAY` seconds before
deferring to Uvicorn — for the same reason `preStop` sleeps: to let the load
balancer notice. In Kubernetes, `preStop` has already done that wait *before
SIGTERM was sent*. Leaving it set makes you wait twice.

```bash
kubectl set env deployment/pulse PULSE_DRAIN_DELAY=6
kubectl rollout restart deployment/pulse && time kubectl rollout status deployment/pulse
kubectl set env deployment/pulse PULSE_DRAIN_DELAY=0
```
**Expected:**
```
                          DRAIN_DELAY=6    DRAIN_DELAY=0
per-pod drain wall time      15.2 s           9.1 s
total rollout duration      4m 26s          3m 12s
handshakes rejected              0               0
messages lost                    0               0
```

✅ **Six seconds per pod, bought nothing.** At 2 replicas it is 74 seconds of
deploy; at 30 replicas it is 3 minutes, and it comes out of a
`terminationGracePeriodSeconds` budget that has no partial credit.

> Two mechanisms solving the same problem, one from each platform, composing
> into double the delay. Look for this whenever you port a Compose stack —
> retries and timeouts stack the same way, and nothing warns you.

Record it:
```markdown
## Module 19 — rolling deploys

- shell-form CMD -> sh is PID 1 -> SIGTERM not forwarded -> NO DRAIN AT ALL.
  9,882 x 1006 closes, 2,610 messages lost, rollout still reported success.
- preStop sleep 6 is worth 118 rejected handshakes: endpoint removal took
  618 ms to propagate and SIGTERM is concurrent with it.
- PULSE_DRAIN_DELAY must be 0 under k8s; preStop already waited. 6 s/pod wasted.
- Full sequence: 0 errors, 0 lost, p99 284 ms vs 272 ms baseline.
```

---

## Part F — The replica-count knee

**This is the part that decides your HPA**, and it is where Module 07's cost
model becomes an operational limit.

Module 07 measured the channel layer against Redis's single thread:

```
fixed per group_send      55 µs
per subscribed worker     46 µs
```

Each replica runs **4** worker processes, so each replica adds 4 to that
multiplier. With three channel-layer shards, each shard sees a third of the
`group_send` traffic:

```
group_sends/s = 3 shards × 0.95 × 1,000,000 µs ÷ (55 + 46·W) µs
outbound/s    = group_sends/s × 199 recipients
```

Measure it. For each replica count, ramp `SEND_EVERY` down until p99 hockey-sticks:

```bash
for r in 1 2 3 4; do
  kubectl scale deployment/pulse --replicas=$r
  kubectl rollout status deployment/pulse
  sleep 90                                    # let connections rebalance
  for every in 8000 5000 3000 2000 1500; do
    kubectl exec redis-cl-0 -- redis-cli CONFIG RESETSTAT
    k6 run -q -e HOST=localhost:8090 -e ROOMS=100 -e SEND_EVERY=$every \
           --vus 10000 --duration 3m \
           --summary-export=/tmp/knee-r$r-$every.json \
           ../06-load-testing-harness/code/pulse-load.js
    sleep 45
  done
done
```

**Expected:**

| Replicas | Workers | Predicted Redis ceiling | Python ceiling | **Measured knee** | Binds |
|---|---|---|---|---|---|
| 1 | 4 | 2,373,000 | ~521,000 | **518,000** | Python |
| 2 | 8 | 1,341,000 | ~1,010,000 | **1,004,000** | Python |
| **3** | **12** | **934,000** | ~1,490,000 | **908,000** | **Redis** |
| 4 | 16 | 717,000 | ~1,950,000 | **694,000** | Redis |

```
knee │        ● 2 replicas (1,004k)
 out │       ╱  ● 3 replicas (908k)   <- WORSE THAN TWO
 /s  │      ╱      ● 4 (694k)
     │  ● 1 (518k)
     └──────────────────────────────  replicas
```

✅ **The third replica is the new eighth worker.** The 1-replica number lands
within 0.6% of Module 07's 4-worker measurement (521,000), and the 3- and
4-replica numbers land within 3.2% of the arithmetic above. The model is not a
metaphor; it predicts.

Confirm which resource is actually saturated:
```bash
kubectl exec redis-cl-0 -- redis-cli --stat &
kubectl exec redis-cl-0 -- redis-cli INFO commandstats | grep -E 'cmdstat_(eval|bzpopmin)'
```
**Expected at the 3-replica knee:**
```
cmdstat_eval:calls=1521000,usec=83655000,usec_per_call=55.00
cmdstat_bzpopmin:calls=18252000,usec=456300000,usec_per_call=25.00

keys  mem     clients blocked requests     connections
1104  38.7M   26      12      52014 (+0)   28
```
`blocked=12` — one blocked client per subscribed worker process, all waiting on
the same single thread.

```bash
kubectl top pods -l app=pulse
```
```
NAME                   CPU(cores)   MEMORY(bytes)
pulse-7d4f8c9b4-x8k2   2410m        2214Mi        <-- 60% of a 4-core limit
pulse-7d4f8c9b4-p2m9   2388m        2201Mi
pulse-7d4f8c9b4-k4n1   2402m        2208Mi
```
✅ **60% CPU and the system is at its ceiling.** An HPA targeting 70% CPU would
add a fourth replica and make things *worse*. This is the whole argument of
`hpa.yaml`.

### Wire the HPA

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install prom-adapter prometheus-community/prometheus-adapter -n monitoring \
     --create-namespace -f 19-kubernetes-ha-and-multiregion/code/k8s/prometheus-adapter-values.yaml
kubectl apply -f <(yq 'select(.kind == "HorizontalPodAutoscaler")' \
                     19-kubernetes-ha-and-multiregion/code/k8s/hpa.yaml)
kubectl get hpa pulse
```
**Expected:**
```
NAME    REFERENCE          TARGETS                          MINPODS MAXPODS REPLICAS
pulse   Deployment/pulse   331m/650m, 400u/10m              2       3       2
```

`331m` is 0.331 — a third of the connection budget used. `400u` is 400 µs of
event-loop lag, four percent of the 10 ms threshold.

Surge the connections and watch it react:
```bash
k6 run -e HOST=localhost:8090 --vus 26000 --duration 8m \
       ../06-load-testing-harness/code/pulse-load.js &
kubectl get hpa pulse -w
```
**Expected:**
```
TARGETS              REPLICAS
331m/650m, 400u/10m  2
712m/650m, 1m/10m    2        <-- over target
712m/650m, 1m/10m    3        <-- scaled up, 38s after crossing
480m/650m, 900u/10m  3
```
✅ **Scaled on connection budget, not CPU** (which never left 40%).

Now stop the load and watch it *not* scale down:
```bash
kill %1; kubectl get hpa pulse -w
```
```
TARGETS              REPLICAS
88m/650m, 300u/10m   3
88m/650m, 300u/10m   3        (+2m)
88m/650m, 300u/10m   3        (+8m)
88m/650m, 300u/10m   2        (+10m 12s)
```
✅ **Ten minutes of stabilization before removing a pod.** Scaling up costs a
pod; scaling down costs everyone on that pod a reconnect. The asymmetry in
`behavior` is the design, not a conservative default.

---

## Part G — Drills, Kubernetes edition

**Skip Part G's node drills on the single-node path.**

Re-run Module 18's drills against Kubernetes so the numbers sit in one table.
`code/k8s-drill.sh` prints the same format on purpose.

### The PodDisruptionBudget

```bash
kubectl get pods -l app=redis-state -o wide | head -4
kubectl drain pulse-worker --ignore-daemonsets --delete-emptydir-data --timeout=120s
kubectl get pdb redis-state
```
**Expected:**
```
NAME          MIN AVAILABLE   ALLOWED DISRUPTIONS
redis-state   5               0
```
✅ One state-Redis pod evicted; **`ALLOWED DISRUPTIONS` is now 0.**

Try a second node:
```bash
kubectl drain pulse-worker2 --ignore-daemonsets --delete-emptydir-data --timeout=60s
```
```
evicting pod default/redis-state-3
error when evicting pods/"redis-state-3" -n "default" (will retry after 5s):
  Cannot evict pod as it would violate the pod's disruption budget.
```

✅ **The API server refused.** In Module 18 this was a sentence in a runbook. Here
it is enforced against `kubectl drain`, the cluster autoscaler, and node upgrades
alike — and it is the one genuinely new capability Kubernetes brings.

Now the footgun:
```bash
kubectl uncordon pulse-worker pulse-worker2
kubectl patch pdb redis-state --type=json -p='[{"op":"replace","path":"/spec/minAvailable","value":6}]'
kubectl drain pulse-worker --ignore-daemonsets --timeout=45s
```
```
error when evicting pods/"redis-state-0": Cannot evict pod as it would violate
the pod's disruption budget.
evicting pod default/redis-state-0
error when evicting pods/"redis-state-0": Cannot evict pod as it would violate
the pod's disruption budget.
(retries until the timeout, forever without one)
```
❌ **No node can ever be drained again**, your cluster upgrade hangs, and the
error does not say "your PDB is impossible."

```bash
kubectl patch pdb redis-state --type=json -p='[{"op":"replace","path":"/spec/minAvailable","value":5}]'
```

> **Rule: `minAvailable = replicas − 1`, or `maxUnavailable: 1`. Never
> `minAvailable == replicas`.**

### Postgres failover

```bash
./19-kubernetes-ha-and-multiregion/code/k8s-drill.sh "pg-primary-kill" \
  "kubectl delete pod \$(kubectl get pods -l cnpg.io/instanceRole=primary -o name)"
```
**Expected:**
```
cnpg  Instance pulse-pg-1 is not healthy, triggering failover
cnpg  Promoting pulse-pg-2 to primary
cnpg  Updating pulse-pg-rw endpoints -> pulse-pg-2
pg-primary-kill    RTO=  8.90s  RPO=0 msgs (27,914 sent, 27,914 received)  p99=1,970ms  restarts=0 evicted=0 pending=0
```
✅ **8.9 s versus Module 18's tuned 11.8 s.** CloudNativePG reacts to the
pod-deletion *event* through the API server; Patroni waits for a 15-second
leader-lock TTL to expire. Event-driven beats TTL-driven when the event exists.

### Redis state-cluster failover

```bash
./19-kubernetes-ha-and-multiregion/code/k8s-drill.sh "redis-state-primary-kill" \
  "kubectl delete pod redis-state-0"
```
```
redis-state-primary-kill   RTO=  6.80s  RPO=0 msgs  p99=294ms  restarts=0 evicted=0 pending=0
```
✅ Essentially identical to Module 18's 7.4 s, and it should be: **failover time
is a property of the quorum protocol, not the orchestrator.** Both runs use
`cluster-node-timeout 5000`.

### App pod kill

```bash
./19-kubernetes-ha-and-multiregion/code/k8s-drill.sh "app-pod-kill" \
  "kubectl delete pod \$(kubectl get pods -l app=pulse -o name | head -1)"
```
```
app-pod-kill               RTO=  4.60s  RPO=0 msgs  p99=1,790ms  restarts=0 evicted=0 pending=0
```
✅ Matches Module 18's 4.2 s. `kubectl delete pod` sends SIGTERM, so this
exercises the same graceful path as the rolling deploy.

### Node failure — where Kubernetes is *worse* than Compose

```bash
./19-kubernetes-ha-and-multiregion/code/k8s-drill.sh "node-failure" \
  "docker kill pulse-worker2" "docker start pulse-worker2"
```
**Expected:**
```
node-failure               RTO= 41.80s  RPO=1,208 msgs  p99=9,240ms  restarts=0 evicted=0 pending=2
```

⚠️ **41.8 seconds.** Find out why:
```bash
kubectl get nodes
kubectl get endpointslices -l kubernetes.io/service-name=pulse \
  -o jsonpath='{.items[*].endpoints[*].conditions.ready}'
```
```
NAME            STATUS     AGE
pulse-worker2   NotReady   58m

true true          <-- the DEAD pod is still listed as Ready
```

**The Service kept routing into a black hole for forty seconds.** Here is the
mechanism, and it is worth internalising:

> **Kubernetes Service endpoints are driven by the kubelet's *report*, not by an
> active health check from the proxy.** The readiness probe runs on the node.
> When the node is gone, nobody runs it, and nobody updates the report. The
> control plane only decides the node is dead after
> `--node-monitor-grace-period`, which defaults to **40 seconds**.

Module 18's nginx *actively probed* each upstream and removed the dead node in
two healthcheck intervals — about 6 seconds. Kubernetes traded that for a system
that will not evict pods during a transient network blip. For a stateless HTTP
service with client retries that is the right trade. For a socket server holding
10,000 connections it is 40 seconds of failed upgrades.

Two mitigations, and you want the first:

```yaml
# 1. Let the ingress do its own active health checking, like Module 18's nginx.
nginx.ingress.kubernetes.io/upstream-fail-timeout: "5"
nginx.ingress.kubernetes.io/upstream-max-fails: "2"
```
```bash
# 2. (cluster-admin, and a blunt instrument) shorten the grace period
--node-monitor-grace-period=16s     # on kube-controller-manager
```
Re-run with the ingress annotations:
```
node-failure-v2            RTO=  7.20s  RPO=0 msgs  p99=2,410ms
```
✅ **41.8 s → 7.2 s**, and the 40-second control-plane timeout is untouched. The
ingress stopped waiting for Kubernetes to have an opinion.

> **The general lesson, and it is the same one Module 18 reached from the other
> direction: Kubernetes reschedules; your data plane must detect failure
> itself.** Do not put the control plane in your availability path.

### Control-plane loss

```bash
./19-kubernetes-ha-and-multiregion/code/k8s-drill.sh "control-plane-down" \
  "docker exec pulse-control-plane systemctl stop kubelet; sleep 90" \
  "docker exec pulse-control-plane systemctl start kubelet"
```
```
control-plane-down         RTO=  0.00s  RPO=0 msgs  p99=278ms
```
✅ **No impact at all.** Running pods do not need the API server; traffic keeps
flowing through the kube-proxy rules already programmed into every node.

Compare with Module 18's **etcd quorum loss: RTO 45.2 s, all writes rejected.**
That is a real architectural difference and it cuts both ways:

| | Module 18 (Patroni + etcd) | Module 19 (CloudNativePG) |
|---|---|---|
| DCS unavailable | primary **demotes itself** when the leader lock expires | primary **keeps serving writes** |
| Writes during the outage | ❌ rejected | ✅ continue |
| Failover during the outage | ❌ impossible | ❌ impossible |
| Split-brain risk | **lower** — a node that cannot prove leadership stops | **higher** — leadership is assumed until the operator says otherwise |

Patroni chose consistency; CloudNativePG chose availability. Neither is wrong.
**Know which one you deployed**, because the two behave in opposite ways during
precisely the incident where you will be guessing.

What you lose during a control-plane outage regardless:
```
- no new pods scheduled
- no rescheduling on failure   <-- a pod that dies now stays dead
- no HPA scaling
- endpoint changes do not propagate
- kubectl does not work        <-- your remediation tooling is gone
```

### The scoreboard

| Drill | Compose (M18) | Kubernetes (M19) | Verdict |
|---|---|---|---|
| Rolling deploy (graceful) | 0.0 s / 0 | **0.0 s / 0** | ✅ parity |
| App node kill | 4.2 s / 0 | **4.6 s / 0** | ✅ parity |
| Redis primary kill | 7.4 s / 0 | **6.8 s / 0** | ✅ quorum protocol, not orchestrator |
| PG primary kill | 11.8 s / 0 | **8.9 s / 0** | ✅ event-driven beats TTL |
| Node / host failure | ~6 s (nginx probe) | **41.8 s / 1,208** → 7.2 s tuned | ❌ then ✅ |
| DCS / control-plane loss | 45.2 s, writes down | **0.0 s / 0** | ⚠️ different trade |
| PDB blocks a quorum drain | n/a (a wiki page) | **enforced** | ✅ new capability |

**Target was RTO < 30 s, RPO = 0.** Met everywhere once the ingress does its own
health checking.

---

## Part H — Multi-region with room affinity

Two `kind` clusters standing in for two regions.

```bash
kind create cluster --name pulse-eu \
  --config 19-kubernetes-ha-and-multiregion/code/k8s/kind-cluster.yaml
# ... apply redis.yaml, postgres.yaml, pulse.yaml with PULSE_REGION=eu ...

# Simulate the WAN. 90 ms is a realistic NYC<->London RTT with router hops; the
# physical floor is 76 ms and no amount of money gets below it.
docker exec pulse-eu-control-plane sh -c \
  "tc qdisc add dev eth0 root netem delay 45ms 5ms"     # 45ms each way
```

Verify the floor is what you think it is:
```bash
docker exec pulse-control-plane ping -c5 pulse-eu-control-plane | tail -1
```
```
rtt min/avg/max/mdev = 89.412/90.204/91.880/0.741 ms
```

### Wire the router

`chat/regions.py` is [`code/region_router.py`](./code/region_router.py). The
send path becomes:

```python
from chat.regions import route, RegionUnavailable

async def _on_message_create(self, content):
    decision = route(self.room.slug)          # BARE slug: "7", not "room.7"

    if decision.local:
        return await self._sequence_and_publish(content)

    try:
        return await forward_to(decision.home, self.room.slug, self.user, content)
    except RegionUnavailable as exc:
        # DO NOT sequence locally. A local INCR here produces a second message
        # numbered 501 and breaks gap detection for the whole room, forever.
        await self.send_json({
            "v": 1, "type": "error", "room": self.room.key,
            "ts": now_ms(),
            "data": {"code": "region_unavailable", "home": exc.home,
                     "retry_after_ms": 5000},
        })
```

Note the two identifiers doing different jobs, exactly as Module 05 defined them:
`self.room.slug` is the bare handle that gets hashed to a home region;
`self.room.key` (`f"room.{slug}"`) is what goes on the wire and into
`group_send`.

```bash
kubectl --context kind-pulse    set env deployment/pulse PULSE_REGIONS=us,eu PULSE_REGION=us
kubectl --context kind-pulse-eu set env deployment/pulse PULSE_REGIONS=us,eu PULSE_REGION=eu
kubectl --context kind-pulse exec deploy/pulse -- \
  python -c "from chat.regions import home_region_of as h; print({s: h(s) for s in ['general','7','random','42']})"
```
**Expected — deterministic, and identical in both clusters:**
```
{'general': 'eu', '7': 'us', 'random': 'us', '42': 'eu'}
```

Run it in a different pod and get the same answer. If you ever see it disagree
between two workers of the *same* pod, someone replaced `blake2b` with Python's
built-in `hash()`, which is randomised per process by `PYTHONHASHSEED`.

### Measured

```bash
k6 run -e HOST=localhost:8091 -e REGION_MIX=0.5 --vus 4000 --duration 8m \
       19-kubernetes-ha-and-multiregion/code/multiregion-load.js
```
**Expected:**

| | Local-home room | Cross-region room |
|---|---|---|
| Send → ack (p50) | 19 ms | **208 ms** |
| Send → ack (p99) | 96 ms | **424 ms** |
| **Perceived send latency** (optimistic render) | **0 ms** | **0 ms** |
| Scrollback (p50) | 17 ms | **17 ms** (local replica) |
| Fan-out to same-region members | 22 ms | 202 ms |
| Fan-out to home-region members | 202 ms | 22 ms |

✅ **The user never waits to send.** Module 17's optimistic render puts the
message on screen instantly; the 208 ms is invisible until the delivery tick.
**Reads are always local**, which is the half of the design that makes room
affinity tolerable.

The number that decides everything:
```bash
curl -s localhost:8091/metrics | grep chat_cross_region_sends_total
```
```
chat_cross_region_sends_total{home="us"} 61402
chat_local_sends_total 61980
```
**49.8% of sends crossed the WAN.** With rooms hashed evenly across N regions,
`(N−1)/N` of a given user's rooms are remote: 50% at two regions, **67% at
three**. Adding a region makes the *average* user's experience worse on sends,
not better. Only the connection RTT improves.

### The partition drill

```bash
docker network disconnect kind pulse-eu-control-plane
```
**Expected in the EU pods:**
```
WARN pulse.regions  region us unreachable (3 consecutive timeouts), marking degraded
```
```bash
# Send to a US-homed room from EU:
curl -s localhost:8091/api/test/send -d '{"room":"7","body":"hello"}' | jq
```
```json
{ "v": 1, "type": "error", "room": "room.7",
  "data": { "code": "region_unavailable", "home": "us", "retry_after_ms": 5000 } }
```
✅ **EU refuses the write rather than inventing a sequence number.** Reading
`room.7` still works from the EU replica — degraded, not down:
```bash
curl -s 'localhost:8091/api/rooms/7/messages?limit=3' | jq -r '.[].seq'
```
```
48211
48212
48213
```

Heal it and prove there was no divergence:
```bash
docker network connect kind pulse-eu-control-plane
sleep 30
for ctx in kind-pulse kind-pulse-eu; do
  kubectl --context $ctx exec redis-state-0 -- redis-cli -c GET 'room:{7}:seq'
  kubectl --context $ctx exec pulse-pg-1 -- psql -U pulse -d pulse -tAc \
    "SELECT min(seq), max(seq), count(*), count(DISTINCT seq) FROM messages WHERE room_id='room.7';"
done
```
**Expected — identical:**
```
"48213"
1|48213|48213|48213
"48213"
1|48213|48213|48213
```
✅ **`count(*) == count(DISTINCT seq)` in both regions.** No duplicate sequence
numbers, no divergence, nothing for a client's gap detection to choke on.

> **The alternative — letting EU sequence independently during the partition —
> produces two different messages numbered 501 and breaks gap detection for
> every client in that room permanently.** A client that accepted one 501 will
> never accept the other. Refusing the write is the correct trade, and it is only
> tolerable because chat sends are infrequent, retryable, and optimistically
> rendered.

Record it:
```markdown
## Module 19 — Kubernetes and multi-region

- Liveness probes CANNOT see one blocked worker of four: 20/20 probes returned
  200 while pid-10 had 29.7 s of event-loop lag. Alert on
  max by (pod) (chat_event_loop_lag_seconds), not on the probe.
- Replica knee: 1=518k, 2=1,004k, 3=908k, 4=694k outbound msg/s.
  The THIRD REPLICA is the new eighth worker. maxReplicas=3 is measured, and
  the escape is more channel-layer shards or Module 14 room affinity, not a
  bigger number. Redis-thread arithmetic predicted it to within 3.2%.
- Node failure: 41.8 s because Service endpoints follow the KUBELET'S REPORT,
  not an active probe. Ingress-level health checking: 41.8 s -> 7.2 s.
- Control-plane loss: RTO 0 (CNPG keeps serving) vs Module 18's etcd quorum
  loss RTO 45.2 s (Patroni demotes). Opposite trades; know which you deployed.
- Multi-region room affinity: cross-region send p50 208 ms, PERCEIVED 0 ms;
  reads always local; 49.8% of sends crossed the WAN at two regions ((N-1)/N).
  Partition -> read-only for remote-homed rooms, 0 divergent sequences.
```

---

## What you built

- The Module 18 stack on Kubernetes: two Redis topologies as StatefulSets with
  per-pod DNS and opposite operational postures, CloudNativePG replacing
  Patroni + etcd + HAProxy, and topology spread that leaves a quorum member
  `Pending` rather than co-locating it.
- **A genuinely zero-drop rolling deploy**, built in three attempts so the
  contribution of each piece is measured — including the shell-form `CMD` that
  silently deletes your entire drain and still reports success.
- **The liveness blind spot**, demonstrated: 20 consecutive 200s from a pod with
  a frozen worker, and the per-worker metric that sees it.
- **The replica knee**, predicted from Module 07's cost model to within 3.2% and
  then measured — and an HPA whose `maxReplicas` is a measured constant.
- Drills scored against Module 18's, including the one place Kubernetes is
  **worse** (node failure, because endpoints follow the kubelet's report) and the
  one place it is better (control-plane loss).
- Multi-region with room affinity, the physical latency floor computed rather
  than assumed, and a partition that produced zero divergent sequence numbers.

Now do [`challenge.md`](./challenge.md).

Then: [Module 20 — Observability & SLOs](../20-observability-and-slos/).
