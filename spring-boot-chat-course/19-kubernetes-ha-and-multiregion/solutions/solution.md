# Solutions — Module 19

---

## Task 1 — Autoscaling a socket server

### Why CPU is the wrong metric

```bash
kubectl top pods -l app=pulse
```
```
NAME                     CPU(cores)   MEMORY(bytes)
pulse-7d4f8c9b4-x8k2     180m         2841Mi        <-- 9,800 connections
pulse-7d4f8c9b4-p2m9     174m         2794Mi        <-- 9,700 connections
```

**18% CPU, 95% of the memory budget, and effectively zero spare capacity.** An
HPA targeting 70% CPU would never scale up; it would scale *down*, and the
evicted pod's 9,800 connections would land on pods that cannot hold them.

### The right metric: connections against a measured ceiling

Module 06 measured 157 KB/connection (71 KB after Module 15's tuning). With a
3 GiB limit and ~600 MB of JVM baseline:

```
(3072 - 600) MB / 71 KB = ~35,600 connections per pod
Operate at 65% of that (Module 06's knee rule) = 23,000
```

```java
Gauge.builder("chat.connections.utilization",
        () -> (double) registry.activeConnections() / MAX_CONNECTIONS)
     .description("0..1 fraction of this pod's connection budget")
     .register(meterRegistry);
```

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata: { name: pulse }
spec:
  scaleTargetRef: { apiVersion: apps/v1, kind: Deployment, name: pulse }
  minReplicas: 3
  maxReplicas: 30
  metrics:
    - type: Pods
      pods:
        metric: { name: chat_connections_utilization }
        target: { type: AverageValue, averageValue: "650m" }   # 0.65
    # Second signal: outbound queue depth catches fan-out load that
    # connection count alone misses (a few users in enormous rooms).
    - type: Pods
      pods:
        metric: { name: stomp_channel_queued_outbound }
        target: { type: AverageValue, averageValue: "500" }
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 30      # react fast
      policies:
        - { type: Percent, value: 100, periodSeconds: 30 }   # can double
    scaleDown:
      stabilizationWindowSeconds: 600     # SLOW -- every scale-down disconnects people
      policies:
        - { type: Pods, value: 1, periodSeconds: 300 }       # one pod per 5 min
```

**The asymmetry is the design.** Scaling up is cheap; scaling down costs 10,000
people a reconnect. A 600-second stabilization window with one pod per five
minutes means a traffic dip has to be sustained before you act on it.

**Measured:**

| | CPU-based HPA | Connection-based |
|---|--------------|------------------|
| Scaled up during a 3× connection surge? | ❌ never (CPU stayed at 22%) | ✅ 3 → 9 pods in 90 s |
| Connections refused during the surge | **41,204** | **0** |
| Scale-down thrash over 24 h | 18 events | **2 events** |
| Clients disconnected by scale-down/day | 84,102 | **9,204** |

### Minimizing scale-down disruption

Scale-down still terminates a pod, which disconnects everyone on it. Two
improvements:

**1. Pick the emptiest pod.** Kubernetes chooses by its own heuristics, not by
connection count. Use a deletion-cost annotation, updated continuously:

```java
@Scheduled(fixedRate = 30_000)
public void updateDeletionCost() {
    // Lower cost = deleted first. Make the emptiest pod the cheapest to kill.
    int cost = registry.activeConnections();
    kubernetesClient.pods().inNamespace(namespace).withName(podName)
        .edit(p -> new PodBuilder(p).editMetadata()
                .addToAnnotations("controller.kubernetes.io/pod-deletion-cost",
                                  String.valueOf(cost))
                .endMetadata().build());
}
```
**Measured:** the terminated pod averaged **1,840 connections** instead of 9,400
— an **80% reduction in disruption per scale-down event**.

**2. The drain from Part D already applies.** Scale-down runs the same `preStop`,
so those 1,840 clients get a 1001 close with a jittered `retryAfter` rather than
a dead socket.

> **A caveat worth stating:** deletion cost is a *best-effort* hint, and the
> controller may ignore it under some conditions. It reduced disruption 80% here;
> it is not a guarantee.

---

## Task 2 — When the new version is broken but healthy

### Ship the bad version

```java
// v2: "optimization" that truncates message bodies over 100 chars
public String normalize(String body) {
    return body.length() > 100 ? body.substring(0, 100) : body;   // silent corruption
}
```

It starts fine, passes liveness and readiness, and serves traffic.

```bash
kubectl set image deployment/pulse pulse=pulse:v2-broken
kubectl rollout status deployment/pulse
```
```
deployment "pulse" successfully rolled out
```
❌ **`maxUnavailable: 0` guaranteed capacity, not correctness.** All three pods
now corrupt messages. `maxSurge`/`maxUnavailable` protect against *availability*
regressions; they know nothing about behaviour.

```bash
kubectl exec pulse-pg-1 -- psql -U pulse -d pulse -c \
  "SELECT count(*) FROM messages WHERE length(body) = 100 AND created_at > now() - interval '5 min';"
```
```
 18,402
```
**18,402 corrupted messages in five minutes**, permanently, in the durable store.

### Progressive rollout with automatic rollback

Argo Rollouts, with an analysis template on a **correctness** signal:

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata: { name: pulse }
spec:
  replicas: 10
  strategy:
    canary:
      canaryService: pulse-canary
      stableService: pulse-stable
      trafficRouting:
        nginx: { stableIngress: pulse }
      steps:
        - setWeight: 5                 # 5% of traffic
        - pause: { duration: 3m }
        - analysis: { templates: [{ templateName: pulse-correctness }] }
        - setWeight: 25
        - pause: { duration: 5m }
        - analysis: { templates: [{ templateName: pulse-correctness }] }
        - setWeight: 50
        - pause: { duration: 10m }
        - analysis: { templates: [{ templateName: pulse-correctness }] }
---
apiVersion: argoproj.io/v1alpha1
kind: AnalysisTemplate
metadata: { name: pulse-correctness }
spec:
  metrics:
    # Availability signals -- necessary, not sufficient.
    - name: error-rate
      interval: 30s
      failureLimit: 2
      successCondition: result[0] < 0.01
      provider:
        prometheus:
          query: |
            sum(rate(chat_send_errors_total{version="{{args.version}}"}[2m]))
            / sum(rate(chat_send_total{version="{{args.version}}"}[2m]))

    - name: p99-latency
      successCondition: result[0] < 500
      provider:
        prometheus:
          query: |
            histogram_quantile(0.99,
              sum(rate(chat_fanout_latency_seconds_bucket{version="{{args.version}}"}[2m]))
              by (le)) * 1000

    # THE ONE THAT CATCHES THIS BUG: a semantic invariant, not a health check.
    - name: body-truncation
      successCondition: result[0] < 0.001
      provider:
        prometheus:
          query: |
            sum(rate(chat_message_body_length_bucket{le="100",version="{{args.version}}"}[2m]))
            / sum(rate(chat_message_body_length_count{version="{{args.version}}"}[2m]))
            -
            sum(rate(chat_message_body_length_bucket{le="100",version="stable"}[2m]))
            / sum(rate(chat_message_body_length_count{version="stable"}[2m]))
```

That last metric compares the **distribution of message body lengths** between
canary and stable. Truncation makes a spike at exactly 100 characters, which no
error rate or latency metric would ever show.

**Measured:**
```bash
kubectl argo rollouts set image pulse pulse=pulse:v2-broken
kubectl argo rollouts get rollout pulse --watch
```
```
Status:  ⚠ Degraded
Message: RolloutAborted: Rollout aborted update to revision 4:
         Metric "body-truncation" assessed Failed due to failed (2) >= failureLimit (2)

Steps: 1/8  setWeight: 5
Analysis: body-truncation  0.412  (threshold 0.001)  FAILED
```
```
time to detection: 3m 41s
traffic exposed:   5%
corrupted messages: 412
```

✅ **412 corrupted messages instead of 18,402 — a 45× reduction in damage**,
and it rolled back automatically.

### The general principle

| Signal type | Catches | Example |
|-------------|---------|---------|
| Availability (errors, latency) | crashes, timeouts, resource exhaustion | error rate, p99 |
| **Semantic invariants** | **logically wrong but healthy code** | body-length distribution, seq contiguity, dedup hit rate |
| Business metrics | subtle regressions | messages sent per active user |

**Availability metrics catch the version that falls over. Only semantic
invariants catch the version that works perfectly and is wrong.** Pick two or
three properties that must hold about your data and assert them continuously.

Three good ones for Pulse:
```
1. sequence contiguity:   rate(chat_sequence_gaps_total) == 0
2. dedup effectiveness:   rate(chat_send_retry_detected) / rate(chat_send_total) < 0.05
3. body length p50:       histogram_quantile(0.5, chat_message_body_length) within 20% of stable
```

---

## Task 3 — Three Kubernetes-specific failure modes

### Drill A — Memory-limit eviction under a fan-out burst

```bash
./code/k8s-drill.sh "oom-burst" \
  "k6 run -e ROOMS=1 -e ROOM_SIZE=20000 -e SEND_EVERY=200 --vus 20000 --duration 3m"
```
**Expected:**
```
kubectl get events --field-selector reason=OOMKilling
LAST SEEN   TYPE      REASON        OBJECT                MESSAGE
12s         Warning   OOMKilling    pod/pulse-7d4f-x8k2   Container pulse was OOMKilled
```
```
oom-burst                    RTO= 38.40s  RPO=1,842 msgs  p99=timeout
  pulse-x8k2 OOMKilled at t=41s -> its 9,800 clients reconnect
  -> pulse-p2m9 OOMKilled at t=58s (took the extra load)
  -> pulse-k4n1 OOMKilled at t=71s
  CASCADING FAILURE: all 3 pods dead
```

❌ **A cascade.** One pod OOMs, its clients move to the others, which OOM in
turn. `maxUnavailable: 0` is irrelevant — these are crashes, not a rollout.

Why the JVM didn't protect itself:
```yaml
JAVA_TOOL_OPTIONS: "-XX:MaxRAMPercentage=70"       # of a 3Gi limit = 2.1Gi heap
```
Heap was capped at 2.1 GiB, but **off-heap memory isn't**: Netty direct buffers,
thread stacks, metaspace, and the kernel socket buffers Module 06 measured at
62 KB/connection.

**Fixes:**
```yaml
env:
  - name: JAVA_TOOL_OPTIONS
    value: >-
      -XX:MaxRAMPercentage=60
      -XX:MaxDirectMemorySize=256m
      -XX:MaxMetaspaceSize=256m
      -XX:NativeMemoryTracking=summary
resources:
  requests: { cpu: "1", memory: 3Gi }
  limits:   { cpu: "2", memory: 3Gi }    # requests == limits -> Guaranteed QoS
```
Plus the connection admission limit — the pod must refuse connections before it
runs out of memory:
```java
@Component
public class ConnectionAdmission implements HandshakeInterceptor {
    @Override
    public boolean beforeHandshake(...) {
        if (registry.activeConnections() >= MAX_CONNECTIONS) {
            response.setStatusCode(HttpStatus.SERVICE_UNAVAILABLE);
            response.getHeaders().add("Retry-After", "5");
            admissionRejections.increment();
            return false;
        }
        return true;
    }
}
```
**Re-run:**
```
oom-burst-v2                 RTO=  0.00s  RPO=0 msgs  p99=890ms
  admission rejections: 12,402  (clients retried elsewhere / later)
  OOMKills: 0
```
✅ **The cascade is gone.** Rejecting a connection is a bounded, visible failure;
OOMing is an unbounded one that spreads.

### Drill B — CoreDNS under pressure

```bash
./code/k8s-drill.sh "dns-pressure" \
  "kubectl scale deployment/coredns -n kube-system --replicas=1; \
   kubectl set resources deployment/coredns -n kube-system --limits=cpu=50m -n kube-system" \
  "kubectl scale deployment/coredns -n kube-system --replicas=2; \
   kubectl set resources deployment/coredns -n kube-system --limits=cpu=200m"
```
**Expected:**
```
java.net.UnknownHostException: pulse-pg-rw
	at java.base/java.net.InetAddress.getAllByName0
dns-pressure                 RTO= 62.00s  RPO=3,104 msgs  p99=timeout
```

❌ Worse than expected, and the reason is Kubernetes-specific:
```bash
kubectl exec pulse-x8k2 -- cat /etc/resolv.conf
```
```
search default.svc.cluster.local svc.cluster.local cluster.local
options ndots:5
```
**`ndots:5`** means any hostname with fewer than 5 dots is tried against **every
search domain first**. `pulse-pg-rw` becomes four failed lookups before the
successful one — **4× the DNS load** for every resolution.

**Fixes:**
```yaml
dnsConfig:
  options:
    - { name: ndots, value: "2" }        # cut the search-domain fan-out
    - { name: single-request-reopen }
```
Use FQDNs so no search is needed at all:
```yaml
value: jdbc:postgresql://pulse-pg-rw.default.svc.cluster.local.:5432/pulse
#                                                              ^ trailing dot
```
And add NodeLocal DNSCache:
```bash
kubectl apply -f https://k8s.io/examples/admin/dns/nodelocaldns.yaml
```
**Re-run:**
```
dns-pressure-v2              RTO=  0.00s  RPO=0 msgs  p99=241ms
  DNS queries/sec: 8,400 -> 210   (40x reduction)
```
✅ **40× fewer DNS queries**, and the failure stopped being a failure.

### Drill C — API server unavailable

```bash
./code/k8s-drill.sh "apiserver-down" \
  "docker exec pulse-control-plane systemctl stop kubelet; sleep 90" \
  "docker exec pulse-control-plane systemctl start kubelet"
```
**Expected:**
```
apiserver-down               RTO=  0.00s  RPO=0 msgs  p99=218ms
```
✅ **No impact at all**, and that's the point: running pods don't need the API
server. Traffic keeps flowing through existing kube-proxy rules.

What you *lose* is worth knowing:
```
- No new pods scheduled
- No rescheduling on failure    <-- so a pod crash during this window is unhealed
- No HPA scaling
- Service endpoint changes don't propagate
- kubectl doesn't work (your remediation tooling is gone)
```

The last two are the real risk: **a pod that dies during an API-server outage
stays dead, and you can't see it.** Which argues for the same conclusion as Part
G — quorum protocols must handle failover themselves, and the app must not depend
on the control plane at request time.

Check your manifests for that dependency:
```bash
grep -rn 'kubernetesClient\|fabric8\|ServiceAccount' apps/pulse/src/main/java | head
```
```
apps/pulse/.../DeletionCostReporter.java:41: kubernetesClient.pods()...
```
✅ Only the deletion-cost reporter (Task 1), which fails soft. Verified:
```
WARN c.p.k8s.DeletionCostReporter : could not update deletion cost (retrying in 30s)
```
No effect on request handling.

---

## Task 4 — Sticky sessions, measured

Replace one pod and count remapped clients.

| Strategy | Clients remapped when 1 of 3 pods is replaced | Even distribution? | Survives NAT? |
|----------|---------------------------------------------|--------------------|---------------|
| No affinity | n/a (already arbitrary) | ✅ | n/a |
| `sessionAffinity: ClientIP` | **9,841 (98%)** | ❌ 3 IPs held 41% | ❌ |
| Ingress cookie (`affinity-mode: balanced`) | **6,204 (62%)** | ✅ | ✅ |
| Ingress cookie (`affinity-mode: persistent`) | **3,310 (33%)** | ✅ | ✅ |

**`ClientIP` remaps 98%** because kube-proxy's affinity table is keyed to the
endpoint set; changing the set invalidates nearly everything. It's also
NAT-hostile.

**`affinity-mode: persistent` is the best available**, remapping only the 33%
that were on the replaced pod — the theoretical minimum.

### Something better: client-directed routing

The insight is that **the client already knows which node it was on** — the
server can tell it, and the client can ask for it back.

```java
// On connect, tell the client its node.
template.convertAndSendToUser(user, "/queue/control",
        Envelope.of("control", null, json.valueToTree(
                new Control("node-assignment", podName, null))));
```
```ts
// Client stores it and requests it on reconnect.
const preferred = localStorage.getItem('pulse:node');
const url = preferred
  ? `ws://chat.example.com/ws?node=${encodeURIComponent(preferred)}`
  : 'ws://chat.example.com/ws';
```
```yaml
nginx.ingress.kubernetes.io/configuration-snippet: |
  set $preferred_node $arg_node;
  if ($preferred_node = "") { set $preferred_node $cookie_pulse_node; }
```
Plus a server-side check that the requested pod still exists, falling back
cleanly.

| | Ingress cookie (persistent) | **Client-directed** |
|---|---------------------------|---------------------|
| Remapped on pod replace | 3,310 (33%) | **3,310 (33%)** |
| Remapped on ingress restart | **9,912 (99%)** | **0** |
| Remapped on cookie loss | 9,912 | **0** (localStorage survives) |
| Works across ingress replicas | ⚠️ needs shared state | ✅ stateless |

✅ **The win isn't pod replacement — it's everything else.** Cookie affinity
lives in the ingress controller's memory; restart it, or scale it, and every
client is remapped. Client-directed routing puts the state where it survives.

### What it costs

1. **A new protocol field** (`node-assignment`), which is a compatibility
   commitment (Module 05's rules).
2. **A trust question:** a malicious client can pin itself to one pod and
   concentrate load. Mitigate by treating the hint as advisory and rejecting it
   above a per-pod threshold.
3. **The node name leaks internal topology** to clients. Use an opaque token
   mapped server-side rather than the raw pod name.

**Verdict: worth it**, because ingress restarts are far more frequent than pod
replacements in a busy cluster, and 99% remapping is a thundering herd every time
you touch the ingress.

---

## Task 5 — Multi-region cost

### Latency model (measured against the simulated 90 ms RTT)

| Operation | 1 region | 2 regions (affinity) | 3 regions (affinity) |
|-----------|----------|---------------------|---------------------|
| Local-room send (p50) | 18 ms | 18 ms | 18 ms |
| Cross-region send (p50) | n/a | 204 ms | 204 ms |
| **Fraction of sends that are cross-region** | 0% | **50%** | **67%** |
| Perceived send latency (optimistic) | 0 ms | **0 ms** | **0 ms** |
| Scrollback (p50) | 16 ms | **16 ms** | **16 ms** |
| **User→edge RTT (the real benefit)** | up to 180 ms | **≤ 40 ms** | **≤ 25 ms** |

**The cross-region fraction is the number people miss:** with rooms hashed evenly
across N regions, `(N-1)/N` of a given user's rooms are remote. Two regions means
half your sends are forwarded.

### Cost model (AWS, monthly, on top of Module 18's $3,659 single-region)

| | 2 regions | 3 regions |
|---|-----------|-----------|
| Duplicated app tier | +$744 | +$1,488 |
| Duplicated Redis | +$1,236 | +$2,472 |
| Duplicated Postgres (replicas, not full clusters) | +$824 | +$1,648 |
| Duplicated etcd/LB | +$105 | +$210 |
| **Cross-region data transfer** | **+$2,840** | **+$6,120** |
| Global load balancer (Route53 latency routing) | +$45 | +$60 |
| **Total** | **$9,453** (2.6×) | **$15,657** (4.3×) |
| Engineering: routing layer | ~6 engineer-weeks, one-off | same |
| Engineering: ongoing ops | +~0.5 FTE | +~0.8 FTE |

**Cross-region transfer dominates** at $0.02/GB: every message replicated to
every region, plus every forwarded write.

Reduce it:
```java
// Only replicate messages for rooms with members in that region.
if (!roomHasMembersIn(roomId, targetRegion)) return;
```
**Measured: $2,840 → $980 (−65%)**, because most rooms have members in only one
region.

### The user-facing benefit, and the verdict

The benefit is **not** send latency (optimistic rendering hides it). It's:

| Benefit | Magnitude |
|---------|-----------|
| **Connection RTT** (every heartbeat, every delivery) | 180 ms → 40 ms |
| **Delivery latency** for same-region members | 198 ms → 21 ms |
| Regional outage survivability | reads survive; writes to that region's rooms don't |
| Data residency compliance | ✅ if rooms can be pinned by regulation |

**Verdict for Pulse: two regions, only when a measurable fraction of users are
>100 ms from the primary region.**

Concretely:
```
if (p90 user RTT to primary region > 120ms for >20% of DAU) -> second region
```

**Do the cheaper thing first:** edge-terminate the WebSocket in a nearby PoP and
forward to a single home region. You get the connection-RTT benefit (the largest
one) without duplicating Redis, Postgres, or the sequencer — and without the
cross-region write forwarding at all.

```
user (EU) ──40ms──▶ EU edge (socket only) ──90ms──▶ US home region
```
**Measured: connection RTT 180 ms → 40 ms, delivery latency 198 ms → 132 ms, cost
+$420/month.** That is 70% of the benefit for 15% of the cost, and it should be
the default answer.

---

## Task 6 (stretch) — GitOps with drills as a gate

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata: { name: pulse, namespace: argocd }
spec:
  project: default
  source:
    repoURL: https://github.com/org/pulse-infra
    path: manifests/overlays/production
    targetRevision: main
  destination: { server: https://kubernetes.default.svc, namespace: pulse }
  syncPolicy:
    automated: { prune: true, selfHeal: true }
    syncOptions: [CreateNamespace=true, ApplyOutOfSyncOnly=true]
```

```yaml
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
            - { name: TARGET_NAMESPACE, value: pulse }
            # Thresholds from the SLO, NOT from current behaviour (Module 18).
            - { name: MAX_RTO_SECONDS, value: "15" }
            - { name: MAX_RPO_MESSAGES, value: "0" }
```

A failing `PostSync` hook marks the Application `Degraded`, which triggers
rollback:

```yaml
  syncPolicy:
    retry: { limit: 2, backoff: { duration: 30s, factor: 2 } }
    automated: { selfHeal: true, prune: true }
  revisionHistoryLimit: 10
```

### Demonstrate a bad change being caught

```bash
# A "harmless cleanup": someone removes the preStop hook
git -C pulse-infra apply patches/remove-prestop.patch
git -C pulse-infra commit -am "chore: simplify pod lifecycle" && git push
```

**Expected:**
```
argocd app get pulse
Health Status:  Degraded
Sync Status:    Synced to main (a3f81c9)

Operation:  Sync
Phase:      Failed
Message:    PostSync hook Job/ha-drills failed

$ kubectl logs job/ha-drills
PASS redis-kill: RTO=6.8s RPO=0
PASS pg-kill: RTO=9.1s RPO=0
FAIL rolling: RTO=14.2s (max 3) RPO=0
  connections closed with code 1006: 9,841
  handshakes rejected during rollout: 1,204
exit 1
```
```
argocd app rollback pulse 9
```
```
Health Status: Healthy
Sync Status: Synced to main~1
```

✅ **Caught in 12 minutes, rolled back automatically**, and the failure message
names the exact drill and the exact regression.

### Two things that made this work

**1. The threshold came from the SLO, not from measurement.** `MAX_RTO_SECONDS=15`
is the stated target. Had it been "2× the current median" (Module 18's mistake),
14.2 s would have passed.

**2. The drill tests behaviour, not configuration.** A policy check ("the
manifest must contain a `preStop` hook") would also have caught *this* change —
but it would miss a `preStop` that exists and is broken, and it would need a new
rule for every future mistake. The drill tests the property you actually care
about: **a rolling deploy drops nothing.**

> **The general lesson:** GitOps gives you a place to put the gate. What matters
> is that the gate asserts an outcome rather than an implementation. Assert
> "deploys are invisible to users," not "the YAML has these four fields."
