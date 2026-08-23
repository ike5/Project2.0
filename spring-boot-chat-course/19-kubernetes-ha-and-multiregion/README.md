# Module 19 — Kubernetes HA & Multi-Region

**Goal:** Port the Compose HA stack to Kubernetes, get zero-drop rolling deploys
for a *stateful socket* workload, and understand honestly what multi-region costs
a chat system.

⏱️ ~6 hours · **Prerequisites:** Modules 00–18. Kubernetes basics help but aren't
assumed — cross-references [`kubernetes-course`](../../kubernetes-course/)
throughout.

---

## What Kubernetes actually changes

Module 18's Compose stack already had HA. Kubernetes doesn't add high
availability — it adds **automation of the things you were doing by hand**:

| Compose | Kubernetes |
|---------|-----------|
| `docker compose up -d --scale app=3` | Deployment `replicas: 3`, self-healing |
| Manual restart on failure | kubelet restarts, controller replaces |
| `stop_grace_period: 60s` | `terminationGracePeriodSeconds` + `preStop` |
| `depends_on: service_healthy` | readiness gates, init containers |
| Static container placement | scheduler + topology spread |
| Manual rolling deploy script | `RollingUpdate` with `maxUnavailable` |
| "don't drain two Redis nodes at once" (a wiki page) | **PodDisruptionBudget** (enforced) |

**The PDB is the genuinely new capability.** In Compose, "don't take down two of
three etcd nodes during maintenance" is a convention someone can violate. In
Kubernetes it's an object the API server enforces against `kubectl drain`.

---

## StatefulSet versus Deployment

| | Deployment | StatefulSet |
|---|-----------|-------------|
| Pod names | random (`pulse-7d4f-x8k2`) | **ordinal and stable** (`redis-0`, `redis-1`) |
| Storage | shared or none | **one PVC per pod, follows the pod** |
| Start/stop order | parallel | **ordered** (0, then 1, then 2) |
| DNS | one Service | **per-pod DNS** (`redis-0.redis.default.svc`) |
| Use for | the app tier | **Redis, Postgres, etcd** |

The per-pod DNS matters more than it looks. Redis replication needs
`replicaof redis-0.redis`, and that name must survive a pod restart on a
different node. A Deployment cannot give you that.

```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata: { name: redis }
spec:
  serviceName: redis            # <-- REQUIRED for per-pod DNS
  replicas: 3
  volumeClaimTemplates:
    - metadata: { name: data }
      spec:
        accessModes: [ReadWriteOnce]
        resources: { requests: { storage: 10Gi } }
```

> **Should you run Postgres in Kubernetes?** Genuinely contested. Operators
> (CloudNativePG, Zalando's postgres-operator, Crunchy) have made it much safer
> than it was, and the lab uses CloudNativePG. But a managed database is less
> operational work, and "we run our own Postgres in k8s" should be a decision
> with a reason, not a default. The lab builds it so you understand what the
> operator is doing for you.

---

## The rolling-deploy problem, in Kubernetes terms

Module 18 solved this in Compose. Kubernetes gives you better tools and one extra
trap.

```yaml
spec:
  strategy:
    rollingUpdate:
      maxUnavailable: 0        # never go below `replicas` capacity
      maxSurge: 1              # add one, then remove one
  template:
    spec:
      terminationGracePeriodSeconds: 90
      containers:
        - name: pulse
          lifecycle:
            preStop:
              exec:
                command: ["/bin/sh", "-c", "sleep 5 && curl -XPOST localhost:8080/actuator/drain"]
```

### Why `preStop` needs that `sleep 5`

This is the trap, and it catches nearly everyone:

```
kubelet decides to terminate a pod
   ├──▶ removes it from the Service endpoints   ┐
   └──▶ runs preStop, then sends SIGTERM        ├─ THESE ARE CONCURRENT
                                                 ┘
```

Endpoint removal propagates asynchronously — through the endpoints controller, to
every kube-proxy, to every node's iptables/IPVS rules. That takes **hundreds of
milliseconds to seconds**. Meanwhile SIGTERM has already arrived and your app has
stopped accepting connections.

The window is small for HTTP (a few failed requests, retried). For **WebSocket
handshakes** it means connections routed to a pod that is already refusing them.

`sleep 5` in `preStop` delays SIGTERM long enough for endpoint removal to
propagate everywhere. It looks like a hack. It is the documented, standard
solution.

### The drain sequence that works

```
t=0.0  pod marked Terminating; endpoint removal begins
t=0.0  preStop starts: sleep 5
t=5.0  preStop curls /actuator/drain
       → readiness false
       → send control{reconnect, retryAfterMs: jitter(1000..30000)} to every session
       → close each socket with 1001
t=7.0  preStop exits; SIGTERM sent
t=7.0  Spring graceful shutdown: finish in-flight work
t=9.0  process exits
       (terminationGracePeriodSeconds=90 was never approached)
```

---

## Topology spread: don't put the quorum in one place

A three-replica StatefulSet whose pods all land on one node is not HA.

```yaml
topologySpreadConstraints:
  - maxSkew: 1
    topologyKey: topology.kubernetes.io/zone
    whenUnsatisfiable: DoNotSchedule        # NOT ScheduleAnyway
    labelSelector: { matchLabels: { app: redis } }
```

`whenUnsatisfiable: DoNotSchedule` means a pod stays `Pending` rather than
violating the spread. That is usually what you want for a quorum member — a
`Pending` pod is a visible problem; three pods in one zone is an invisible one.

`ScheduleAnyway` treats it as a preference, which silently degrades to "all in one
zone" under pressure. Module 18's etcd drill showed what that costs.

---

## PodDisruptionBudgets

```yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata: { name: etcd }
spec:
  minAvailable: 2              # of 3 — quorum must survive
  selector: { matchLabels: { app: etcd } }
```

This blocks **voluntary** disruptions — `kubectl drain`, cluster autoscaler
scale-down, node upgrades — from taking the second etcd pod. It does **not**
protect against node crashes; nothing can.

⚠️ **A PDB that can never be satisfied blocks node drains forever.** A
`minAvailable: 3` on a 3-replica set means no node can ever be drained, and your
cluster upgrade hangs. Always `minAvailable = replicas - 1` for quorum members,
or use `maxUnavailable: 1`.

---

## Sticky sessions in Kubernetes

Module 07 established that Pulse wants session affinity as an optimization.
Kubernetes gives you two mechanisms, and neither is great:

| Mechanism | How | Problem |
|-----------|-----|---------|
| `Service.sessionAffinity: ClientIP` | kube-proxy hashes the source IP | **Breaks behind NAT** — thousands of users share an IP. Also lost on endpoint changes. |
| Ingress cookie affinity (nginx-ingress) | `nginx.ingress.kubernetes.io/affinity: cookie` | Works, but only at the ingress; East-West traffic is unaffected |

The nginx-ingress annotations are the practical answer:

```yaml
annotations:
  nginx.ingress.kubernetes.io/affinity: "cookie"
  nginx.ingress.kubernetes.io/session-cookie-name: "pulse-node"
  nginx.ingress.kubernetes.io/affinity-mode: "persistent"
  nginx.ingress.kubernetes.io/upstream-hash-by: "$cookie_pulse_node"
  nginx.ingress.kubernetes.io/proxy-read-timeout: "3600"
  nginx.ingress.kubernetes.io/proxy-send-timeout: "3600"
```

⚠️ **`proxy-read-timeout` again.** The ingress default is 60 seconds. Every
WebSocket lesson from Module 03 applies identically here, and this is where
people rediscover it.

---

## Multi-region: what it actually costs

The honest section, because most multi-region chat designs are wrong.

### The fundamental problem

Pulse's ordering guarantee comes from **one sequencer per room** — a single
Redis `INCR`. That works because there is one place the counter lives.

Two regions with independent sequencers means:

```
region A: alice sends -> seq 501
region B: bob sends   -> seq 501     (different message, same number)
```

The sequence number stops identifying a message, and every client's gap detection
breaks. **Your entire delivery guarantee assumed a single writer per room.**

### The three viable architectures

**1. Room affinity (recommended).**
Each room has a **home region**. Writes to that room are forwarded there; reads
are served locally from a replica.

```
alice (EU) sends to room.7 (home: US)
  → EU edge forwards the write to US
  → US sequences and publishes
  → replicated back to EU
  → alice's own message arrives ~120ms later
```

Preserves every guarantee. Costs cross-region latency **on writes to non-local
rooms**, which for chat is bearable because sends are infrequent and rendered
optimistically (Module 05).

**2. Region-scoped rooms.**
A room simply exists in one region and users connect to that region. Simplest,
and correct — but a globally distributed team has a bad experience.

**3. Active/active with CRDTs.**
Replace total ordering with **causal** ordering (Module 10 discussed this).
Each region sequences independently; conflicts are resolved by a merge function.

This is genuinely correct and genuinely expensive: you rewrite the protocol
(vector clocks or Lamport timestamps in every message), the client's ordering
logic, and the storage model. It's what you build when you're Figma or Notion and
concurrent editing is the product. **For chat it is almost always over-engineering.**

### What multi-region does not fix

- **Latency to the sequencer** for cross-region rooms. Unavoidable in options 1
  and 2.
- **Cross-region data transfer cost.** Replicating every message to every region
  is real money — Module 18's cost model showed cross-AZ transfer at $310/month;
  cross-*region* is roughly 10× that.
- **Split-brain during a region partition.** Two regions that can't see each
  other and both accept writes to the same room will diverge. Option 1 handles
  this by making the non-home region **read-only** for that room — a deliberate
  availability sacrifice.

> **The honest recommendation:** most chat products do not need multi-region
> write capability. They need **multi-region read replicas and edge termination**
> — users connect to a nearby edge, which holds the socket and forwards to a
> single home region. That gets you most of the latency benefit for a fraction of
> the complexity.

---

## What's next

The lab ports the whole stack to `kind`, achieves a genuinely zero-drop rolling
deploy, proves the PDB blocks a quorum-breaking drain, and then builds
edge-terminated multi-region with room affinity — and measures the cross-region
write penalty.

See you in [`lab.md`](./lab.md).
