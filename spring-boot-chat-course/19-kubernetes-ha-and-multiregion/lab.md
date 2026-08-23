# Lab 19 — Zero-Drop Deploys and a Second Region

**You'll:** port the stack to `kind`, get a rolling deploy that drops zero
messages and zero connections-without-warning, prove a PDB blocks a
quorum-breaking drain, and build edge-terminated multi-region with room affinity.

⏱️ ~120 min. Needs ~10 GB RAM.

> **Low-memory path:** a single-node `kind` cluster with 2 app replicas. You lose
> the topology-spread and node-drain drills (there's only one node); everything
> else works. The lab flags which parts to skip.

---

## Part A — The cluster

`manifests/kind-cluster.yaml`:
```yaml
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
  - role: control-plane
    kubeadmConfigPatches:
      - |
        kind: InitConfiguration
        nodeRegistration:
          kubeletExtraArgs:
            node-labels: "ingress-ready=true"
    extraPortMappings:
      - { containerPort: 80,  hostPort: 8090, protocol: TCP }
      - { containerPort: 443, hostPort: 8443, protocol: TCP }
  - role: worker
    labels: { topology.kubernetes.io/zone: zone-a }
  - role: worker
    labels: { topology.kubernetes.io/zone: zone-b }
  - role: worker
    labels: { topology.kubernetes.io/zone: zone-c }
```

```bash
kind create cluster --name pulse --config manifests/kind-cluster.yaml
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml
kubectl wait --namespace ingress-nginx --for=condition=ready pod \
  --selector=app.kubernetes.io/component=controller --timeout=180s
kubectl get nodes -L topology.kubernetes.io/zone
```
**Expected:**
```
NAME                  STATUS   ROLES           ZONE
pulse-control-plane   Ready    control-plane
pulse-worker          Ready    <none>          zone-a
pulse-worker2         Ready    <none>          zone-b
pulse-worker3         Ready    <none>          zone-c
```

---

## Part B — Redis as a StatefulSet

`manifests/redis.yaml`:
```yaml
apiVersion: v1
kind: Service
metadata: { name: redis }
spec:
  clusterIP: None                       # HEADLESS -> per-pod DNS
  selector: { app: redis }
  ports: [ { port: 6379, name: redis } ]
---
apiVersion: apps/v1
kind: StatefulSet
metadata: { name: redis }
spec:
  serviceName: redis
  replicas: 3
  selector: { matchLabels: { app: redis } }
  template:
    metadata: { labels: { app: redis } }
    spec:
      terminationGracePeriodSeconds: 30
      # A quorum in one zone is not a quorum.
      topologySpreadConstraints:
        - maxSkew: 1
          topologyKey: topology.kubernetes.io/zone
          whenUnsatisfiable: DoNotSchedule
          labelSelector: { matchLabels: { app: redis } }
      containers:
        - name: redis
          image: redis:7-alpine
          command: ["/bin/sh", "-c"]
          args:
            - |
              ORDINAL=${HOSTNAME##*-}
              if [ "$ORDINAL" = "0" ]; then
                exec redis-server /conf/redis.conf
              else
                exec redis-server /conf/redis.conf --replicaof redis-0.redis 6379
              fi
          ports: [ { containerPort: 6379 } ]
          resources:
            requests: { cpu: 500m, memory: 1Gi }
            limits:   { cpu: "2",  memory: 2Gi }
          readinessProbe:
            exec: { command: ["redis-cli", "PING"] }
            initialDelaySeconds: 5
            periodSeconds: 3
          livenessProbe:
            exec: { command: ["redis-cli", "PING"] }
            initialDelaySeconds: 15
            periodSeconds: 10
            failureThreshold: 5         # generous: a busy Redis can be slow to reply
          volumeMounts:
            - { name: conf, mountPath: /conf }
            - { name: data, mountPath: /data }
      volumes:
        - name: conf
          configMap: { name: redis-config }
  volumeClaimTemplates:
    - metadata: { name: data }
      spec:
        accessModes: [ReadWriteOnce]
        resources: { requests: { storage: 5Gi } }
---
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata: { name: redis }
spec:
  minAvailable: 2                       # replicas - 1. NEVER equal to replicas.
  selector: { matchLabels: { app: redis } }
```

```bash
kubectl apply -f manifests/redis.yaml
kubectl rollout status statefulset/redis
kubectl get pods -l app=redis -o wide
```
**Expected — one per zone:**
```
NAME      READY   STATUS    NODE
redis-0   1/1     Running   pulse-worker
redis-1   1/1     Running   pulse-worker2
redis-2   1/1     Running   pulse-worker3
```
```bash
kubectl exec redis-1 -- redis-cli INFO replication | head -3
```
```
role:slave
master_host:redis-0.redis
```
✅ Stable per-pod DNS working. Delete `redis-1` and it comes back on a
(possibly different) node with the same name and the same volume.

**Prove the topology constraint bites** (skip on the single-node path):
```bash
kubectl scale statefulset/redis --replicas=4
kubectl get pod redis-3
```
**Expected:**
```
NAME      READY   STATUS    
redis-3   0/1     Pending
```
```bash
kubectl describe pod redis-3 | grep -A3 Events
```
```
Warning  FailedScheduling  0/4 nodes are available: 1 node(s) had untolerated taint,
3 node(s) didn't match pod topology spread constraints.
```
✅ **Pending, not silently co-located.** With `ScheduleAnyway` it would have
landed a fourth Redis in zone-a and you'd never know.

```bash
kubectl scale statefulset/redis --replicas=3
```

---

## Part C — Postgres via CloudNativePG

```bash
kubectl apply --server-side -f \
  https://raw.githubusercontent.com/cloudnative-pg/cloudnative-pg/release-1.24/releases/cnpg-1.24.0.yaml
kubectl wait --for=condition=Available deployment/cnpg-controller-manager -n cnpg-system --timeout=180s
```

`manifests/postgres.yaml`:
```yaml
apiVersion: postgresql.cnpg.io/v1
kind: Cluster
metadata: { name: pulse-pg }
spec:
  instances: 3
  imageName: ghcr.io/cloudnative-pg/postgresql:16.4

  postgresql:
    parameters:
      max_connections: "200"
      shared_buffers: "512MB"
      log_min_duration_statement: "200"
      wal_level: "replica"
    # Synchronous replication: RPO 0, matching Module 18's target.
    synchronous:
      method: any
      number: 1

  bootstrap:
    initdb: { database: pulse, owner: pulse, secret: { name: pulse-pg-credentials } }

  storage: { size: 20Gi }

  # The operator handles this; we just declare intent.
  affinity:
    topologyKey: topology.kubernetes.io/zone
    enablePodAntiAffinity: true

  resources:
    requests: { cpu: 500m, memory: 1Gi }
    limits:   { cpu: "2",  memory: 2Gi }

  monitoring: { enablePodMonitor: true }
```

```bash
kubectl apply -f manifests/postgres.yaml
kubectl wait --for=condition=Ready cluster/pulse-pg --timeout=600s
kubectl get cluster pulse-pg
kubectl get svc -l cnpg.io/cluster=pulse-pg
```
**Expected:**
```
NAME       AGE   INSTANCES   READY   STATUS                     PRIMARY
pulse-pg   4m    3           3       Cluster in healthy state   pulse-pg-1

NAME            TYPE        PORT(S)
pulse-pg-rw     ClusterIP   5432/TCP     <-- writes: always the primary
pulse-pg-ro     ClusterIP   5432/TCP     <-- reads: replicas only
pulse-pg-r      ClusterIP   5432/TCP     <-- reads: any instance
```

✅ **The operator gives you `-rw` and `-ro` Services**, which is exactly what
Module 18's HAProxy config was doing by hand — the operator updates the endpoints
on failover.

---

## Part D — The app, with a drain that works

`manifests/pulse.yaml`:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata: { name: pulse }
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 0          # never drop below capacity
      maxSurge: 1                # one at a time
  selector: { matchLabels: { app: pulse } }
  template:
    metadata: { labels: { app: pulse } }
    spec:
      # 90s: enough for 10,000 sockets to be told to leave.
      terminationGracePeriodSeconds: 90
      topologySpreadConstraints:
        - maxSkew: 1
          topologyKey: topology.kubernetes.io/zone
          whenUnsatisfiable: ScheduleAnyway      # app pods: a preference, not a rule
          labelSelector: { matchLabels: { app: pulse } }
      containers:
        - name: pulse
          image: pulse:local
          env:
            - name: PULSE_NODE_ID
              valueFrom: { fieldRef: { fieldPath: metadata.name } }
            - name: SPRING_DATASOURCE_URL
              value: jdbc:postgresql://pulse-pg-rw:5432/pulse?prepareThreshold=0
            - name: SPRING_DATASOURCE_REPLICA_URL
              value: jdbc:postgresql://pulse-pg-ro:5432/pulse
            - name: JAVA_TOOL_OPTIONS
              value: "-XX:MaxRAMPercentage=70 -XX:+UseZGC -XX:+ZGenerational"
          ports: [ { containerPort: 8080 } ]
          resources:
            requests: { cpu: "1", memory: 2Gi }
            limits:   { cpu: "2", memory: 3Gi }

          lifecycle:
            preStop:
              exec:
                command:
                  - /bin/sh
                  - -c
                  # THE sleep: endpoint removal is CONCURRENT with SIGTERM and
                  # takes time to propagate to every kube-proxy. Without this,
                  # new handshakes are still routed here after we stop accepting.
                  - "sleep 5 && curl -fsS -XPOST localhost:8080/actuator/drain && sleep 2"

          startupProbe:                       # JVM startup; separate from liveness
            httpGet: { path: /actuator/health/liveness, port: 8080 }
            failureThreshold: 30
            periodSeconds: 2
          readinessProbe:
            httpGet: { path: /actuator/health/readiness, port: 8080 }
            periodSeconds: 3
            failureThreshold: 2
          livenessProbe:
            httpGet: { path: /actuator/health/liveness, port: 8080 }
            periodSeconds: 10
            failureThreshold: 6               # deliberately slow: see Module 02
---
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata: { name: pulse }
spec:
  maxUnavailable: 1
  selector: { matchLabels: { app: pulse } }
```

The drain endpoint:
```java
@RestController
public class DrainController {

    private final AtomicBoolean draining = new AtomicBoolean(false);

    @PostMapping("/actuator/drain")
    public ResponseEntity<String> drain() {
        if (!draining.compareAndSet(false, true))
            return ResponseEntity.ok("already draining");

        availability.setReadiness(ReadinessState.REFUSING_TRAFFIC);   // LB stops sending

        var sessions = registry.allSessions();
        log.info("draining {} sessions", sessions.size());

        for (var s : sessions) {
            // Each client gets its OWN jittered return time (Module 10/17).
            template.convertAndSendToUser(s.user(), "/queue/control",
                    Envelope.of("control", null, json.valueToTree(new Control(
                            "reconnect", "draining",
                            ThreadLocalRandom.current().nextLong(1_000, 30_000)))));
        }
        sleepQuietly(1_500);                          // let the frames flush
        sessions.forEach(s -> close(s, 1001, "server_draining"));

        return ResponseEntity.ok("drained " + sessions.size());
    }
}
```

`manifests/ingress.yaml`:
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: pulse
  annotations:
    nginx.ingress.kubernetes.io/affinity: "cookie"
    nginx.ingress.kubernetes.io/session-cookie-name: "pulse-node"
    nginx.ingress.kubernetes.io/affinity-mode: "persistent"
    # 60s is the default and it KILLS IDLE WEBSOCKETS (Module 03, again).
    nginx.ingress.kubernetes.io/proxy-read-timeout: "3600"
    nginx.ingress.kubernetes.io/proxy-send-timeout: "3600"
spec:
  ingressClassName: nginx
  rules:
    - http:
        paths:
          - { path: /, pathType: Prefix, backend: { service: { name: pulse, port: { number: 8080 } } } }
```

```bash
kind load docker-image pulse:local --name pulse
kubectl apply -f manifests/pulse.yaml -f manifests/ingress.yaml
kubectl rollout status deployment/pulse
curl -s localhost:8090/actuator/health | jq -r .status
```
```
UP
```

---

## Part E — The zero-drop rolling deploy

**The headline drill.** Load first:

```bash
k6 run -e HOST=localhost:8090 -e ROOMS=100 -e SEND_EVERY=5000 \
       --vus 10000 --duration 10m \
       ../../06-load-testing-harness/code/pulse-load.js &
sleep 120
```

### Attempt 1 — no `preStop`

```bash
kubectl patch deployment pulse --type=json \
  -p='[{"op":"remove","path":"/spec/template/spec/containers/0/lifecycle"}]'
kubectl set image deployment/pulse pulse=pulse:v2
kubectl rollout status deployment/pulse
```
**Expected:**
```
fanout_latency_ms: p(99)=8,410ms
ws_errors: 4.12%
sequence_gaps: 0
connections dropped with code 1006: 9,841
handshakes rejected during rollout: 1,204
```
❌ **1,204 handshakes were routed to pods that had already stopped accepting**,
and 9,841 clients got a bare TCP close with no reason.

### Attempt 2 — `preStop` with the drain, but no `sleep`

```bash
kubectl patch deployment pulse --patch-file manifests/patches/prestop-nosleep.yaml
kubectl rollout restart deployment/pulse && kubectl rollout status deployment/pulse
```
```
ws_errors: 0.41%
connections dropped with code 1006: 0
connections closed with code 1001: 9,904
handshakes rejected during rollout: 118        <-- still!
```
✅ Clients now get a reason and a `retryAfter`. ❌ But **118 handshakes still
failed**, because endpoint removal hadn't propagated when SIGTERM arrived.

Prove the mechanism:
```bash
kubectl get endpointslices -l kubernetes.io/service-name=pulse -w
```
**Expected during a rollout:**
```
(t=0.00) pulse-abc  ["10.244.1.5","10.244.2.7","10.244.3.4"]
(t=0.62) pulse-abc  ["10.244.2.7","10.244.3.4"]        <-- 620ms to remove
```
620 ms during which the ingress still routes to a pod that stopped accepting at
t=0.

### Attempt 3 — the full sequence

```bash
kubectl patch deployment pulse --patch-file manifests/patches/prestop-full.yaml
kubectl rollout restart deployment/pulse && kubectl rollout status deployment/pulse
```
**Expected:**
```
fanout_latency_ms: p(99)=241ms          (baseline 214ms)
ws_errors: 0.00%
sequence_gaps: 0
connections closed with code 1001: 9,912
handshakes rejected during rollout: 0
messages lost: 0
reconnect peak: 194/s over 31s
total rollout duration: 2m 47s
```

✅ **Zero errors, zero lost messages, p99 barely moved.**

| | No preStop | preStop, no sleep | **Full sequence** |
|---|-----------|-------------------|-------------------|
| p99 during | 8,410 ms | 1,890 ms | **241 ms** |
| `ws_errors` | 4.12% | 0.41% | **0.00%** |
| Rejected handshakes | 1,204 | 118 | **0** |
| Close code | 1006 (unknown) | 1001 + retryAfter | 1001 + retryAfter |
| Messages lost | 0 | 0 | **0** |

> Note messages were never lost in any attempt — the Streams backbone and outbox
> saw to that. What varied was **connection experience**, which is what users
> actually perceive: a socket that dies with no explanation versus one that says
> "come back in 14 seconds."

Watch a single pod's drain:
```bash
kubectl logs -f deployment/pulse -c pulse | grep -E 'draining|drained'
```
```
INFO c.p.web.DrainController : draining 3,304 sessions
INFO c.p.web.DrainController : drained 3304
INFO o.s.b.w.e.tomcat : Commencing graceful shutdown
INFO o.s.b.w.e.tomcat : Graceful shutdown complete
```

---

## Part F — The PodDisruptionBudget

**Skip on the single-node path.**

```bash
kubectl get pods -l app=redis -o wide
```
```
redis-0   pulse-worker    (zone-a)
redis-1   pulse-worker2   (zone-b)
redis-2   pulse-worker3   (zone-c)
```

Drain one node — allowed:
```bash
kubectl drain pulse-worker --ignore-daemonsets --delete-emptydir-data --timeout=120s
kubectl get pdb redis
```
```
NAME    MIN AVAILABLE   ALLOWED DISRUPTIONS
redis   2               0
```
✅ redis-0 evicted; **`ALLOWED DISRUPTIONS` is now 0.**

Try to drain a second — blocked:
```bash
kubectl drain pulse-worker2 --ignore-daemonsets --delete-emptydir-data --timeout=60s
```
**Expected:**
```
evicting pod default/redis-1
error when evicting pods/"redis-1" -n "default" (will retry after 5s):
  Cannot evict pod as it would violate the pod's disruption budget.
```

✅ **The API server refused.** In Compose this was a wiki page saying "don't do
this." Here it is enforced against `kubectl drain`, the cluster autoscaler, and
node upgrades alike.

```bash
kubectl uncordon pulse-worker
kubectl uncordon pulse-worker2
```

**Now demonstrate the PDB footgun:**
```bash
kubectl patch pdb redis --type=json -p='[{"op":"replace","path":"/spec/minAvailable","value":3}]'
kubectl drain pulse-worker --ignore-daemonsets --timeout=60s
```
```
error when evicting pods/"redis-0": Cannot evict pod as it would violate the pod's
disruption budget.
(retries forever)
```
❌ **No node can ever be drained.** Your cluster upgrade hangs indefinitely, and
the error doesn't say "your PDB is impossible." Restore:
```bash
kubectl patch pdb redis --type=json -p='[{"op":"replace","path":"/spec/minAvailable","value":2}]'
```

> **Rule: `minAvailable = replicas - 1`, or `maxUnavailable: 1`. Never
> `minAvailable == replicas`.**

---

## Part G — Failover drills, k8s edition

Re-run Module 18's drills against Kubernetes and compare.

```bash
./code/k8s-drill.sh "pg-primary-kill" \
  "kubectl delete pod \$(kubectl get pods -l cnpg.io/instanceRole=primary -o name)"
```
**Expected:**
```
cnpg: Primary pulse-pg-1 is not healthy, triggering failover
cnpg: Promoting pulse-pg-2 to primary
cnpg: Updating service pulse-pg-rw endpoints
pg-primary-kill              RTO=  9.40s  RPO=0 msgs  p99=1,840ms
```
✅ **9.4 s versus Compose's 11.8 s** — the operator reacts to the pod deletion
event rather than waiting for a TTL to expire.

```bash
./code/k8s-drill.sh "node-failure" "docker kill pulse-worker2"
```
**Expected:**
```
node-failure                 RTO= 41.20s  RPO=0 msgs  p99=6,410ms
```
⚠️ **41 seconds** — much worse than the Compose equivalent. Why:

```bash
kubectl get nodes
```
```
NAME             STATUS     AGE
pulse-worker2    NotReady   42m
```
```
node-monitor-grace-period:  40s      # kubelet must miss heartbeats
pod-eviction-timeout:       (then) pods marked for deletion
```

**Kubernetes takes ~40 seconds to declare a node dead**, by design — it would
rather be slow than evict pods during a transient network blip. Your application
must therefore detect the failure itself.

Which Pulse does: the Redis Sentinel quorum and CloudNativePG both noticed within
10 seconds and failed over. The 41 seconds is how long until the *pods* were
rescheduled, which only affects capacity, not availability.

**The lesson:** don't rely on Kubernetes for failure detection of stateful
services. Kubernetes reschedules; **your quorum protocol fails over.**

---

## Part H — Multi-region with room affinity

Two `kind` clusters standing in for two regions.

```bash
kind create cluster --name pulse-us --config manifests/kind-cluster.yaml
kind create cluster --name pulse-eu --config manifests/kind-eu.yaml
```

Simulate the WAN:
```bash
docker exec pulse-eu-control-plane sh -c \
  "tc qdisc add dev eth0 root netem delay 90ms 10ms"     # ~US-EU RTT
```

### Room affinity

```java
@Component
public class RegionRouter {

    @Value("${pulse.region}") private String localRegion;

    /** A room's home region is derived from its ID -- no lookup, no coordination. */
    public String homeRegionOf(String roomId) {
        return regionAssignment.get(roomId)            // explicit override, cached
                .orElseGet(() -> REGIONS[Math.floorMod(hash(roomId), REGIONS.length)]);
    }

    public boolean isLocal(String roomId) {
        return localRegion.equals(homeRegionOf(roomId));
    }
}
```

```java
public SendResult send(String roomId, String sender, MessageCreate create) {
    if (regionRouter.isLocal(roomId)) return doSend(roomId, sender, create);

    // Forward to the home region. The client's optimistic render (Module 05)
    // means the user does not wait for this.
    crossRegionForwards.increment();
    return regionClient.forward(regionRouter.homeRegionOf(roomId), roomId, sender, create);
}
```

Reads stay local, from a replica:
```java
public List<MessageNew> scrollback(String roomId, long cursor, int limit) {
    return localReplica.scrollback(roomId, cursor, limit);      // ALWAYS local
}
```

### Measured

```bash
k6 run -e HOST=localhost:8090 -e REGION_MIX=0.5 code/multiregion-load.js
```
**Expected:**

| | Local room | Cross-region room |
|---|-----------|-------------------|
| Send → ack (p50) | 18 ms | **204 ms** |
| Send → ack (p99) | 94 ms | **412 ms** |
| **Perceived send latency** (optimistic render) | **0 ms** | **0 ms** |
| Scrollback (p50) | 16 ms | **16 ms** (local replica) |
| Fan-out to local members | 21 ms | **198 ms** |
| Fan-out to home-region members | 198 ms | 21 ms |

✅ **The user never waits to send** — optimistic rendering means the 204 ms is
invisible until the tick appears. Reads are always local. The cost is
**delivery** latency for members who aren't in the room's home region.

### The partition drill

```bash
docker network disconnect kind pulse-eu-control-plane
```
**Expected in EU:**
```
WARN c.p.region.RegionClient : cannot reach region US, marking degraded
```
```bash
# Sending to a US-home room from EU:
curl -s localhost:8091/api/test/send -d '{"room":"room.7"}'
```
```
{"error":"region_unavailable","message":"room.7 is hosted in US, which is unreachable","retryAfterMs":5000}
```
✅ **EU refuses the write rather than accepting one it cannot sequence.**
Reading `room.7` still works from the EU replica — degraded, not down.

Prove no divergence after healing:
```bash
docker network connect kind pulse-eu-control-plane
sleep 30
./code/compare_regions.sh room.7
```
```
US seq range: 1..48213
EU seq range: 1..48213
divergent sequences: 0
```

> **The alternative — letting EU sequence independently — produces two messages
> with seq 501 and breaks every client's gap detection permanently.** Refusing
> the write is the correct trade, and it's only tolerable because chat sends are
> infrequent and retryable.

Record it:
```markdown
## Module 19 — Kubernetes and multi-region

- Rolling deploy: no preStop 4.12% errors / 1,204 rejected handshakes
                  full sequence 0.00% / 0 / p99 241ms (baseline 214ms)
  The `sleep 5` in preStop is worth 118 rejected handshakes -- endpoint
  removal takes ~620ms to propagate.
- PDB blocks a quorum-breaking drain (enforced, not documented)
- minAvailable == replicas makes nodes undrainable forever
- PG failover: 9.4s in k8s (event-driven) vs 11.8s in Compose (TTL-driven)
- Node failure: 41s for k8s to notice; quorum protocols noticed in 10s
  => do not rely on k8s for stateful failure detection
- Multi-region, room affinity: cross-region send p50 204ms, PERCEIVED 0ms
  (optimistic render); reads always local; partition = read-only, no divergence
```

---

## What you built

- The full HA stack on Kubernetes: StatefulSets with per-pod DNS, CloudNativePG,
  topology spread that leaves pods `Pending` rather than co-locating a quorum.
- **A genuinely zero-drop rolling deploy**, built up in three attempts so the
  contribution of each piece is measured — including the `sleep 5` that most
  people omit.
- A PDB proven to block a quorum-breaking drain, and the impossible-PDB footgun.
- Failover drills compared against Compose, with the finding that **Kubernetes
  reschedules but your quorum protocol fails over.**
- Multi-region with room affinity, measured, including the partition behaviour
  that keeps sequences from diverging.

Now do [`challenge.md`](./challenge.md).

Then: [Module 20 — Observability & SLOs](../20-observability-and-slos/).
