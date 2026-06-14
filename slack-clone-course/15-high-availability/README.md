# Module 15 — High Availability & Scaling

**Goal:** make the app survive failures and absorb load — autoscaling, disruption
budgets, anti-affinity, zero-downtime rollouts, and the specifics of scaling
WebSockets and Celery.

⏱️ ~3 hours · 🎯 Prereq: Module 14 (HA data tier). metrics-server installed.

> The data tier is HA. Now the *app* tier: enough replicas in the right places, with
> rules so Kubernetes never takes them all down at once — and a real failure drill to
> prove it.

---

## 1. Autoscaling with the HPA

`k8s/ha/hpa.yaml` adds **HorizontalPodAutoscalers** for web (2→8) and worker (2→10),
targeting ~70% CPU. When a traffic spike pushes CPU up, the HPA adds pods; when it
subsides, it scales back down. It needs the **metrics-server** to read pod CPU.

> WebSocket load is often **connection-bound**, not CPU-bound. CPU is a starting
> signal; in production you'd scale web on a custom metric like *active connections*
> (via Prometheus Adapter) — noted in the challenge.

## 2. PodDisruptionBudgets

A **PDB** protects against *voluntary* disruptions — node drains, cluster upgrades.
`minAvailable: 1` on web/frontend/worker tells Kubernetes "you may evict pods for
maintenance, but never below one healthy pod here." Without a PDB, draining a node
could briefly take every replica of a service down at once.

## 3. Anti-affinity: don't put all eggs in one node

Two web replicas on the **same** node both die if that node dies — no real HA.
`k8s/ha/anti-affinity-patch.yaml` adds **pod anti-affinity** so the scheduler spreads
web pods across nodes. (CloudNativePG already does this for Postgres.) Now a node
failure costs you at most one replica of each service.

## 4. Zero-downtime rollouts

The Deployments use `RollingUpdate` with `maxUnavailable: 0, maxSurge: 1`: Kubernetes
brings up a new pod, waits for its **readiness probe**, shifts traffic, then retires an
old one — never dropping below full capacity. Combined with the migration-Job-first
ordering (Module 13), deploys are invisible to users.

## 5. Scaling WebSockets correctly

With 3 web replicas, a user is connected to *one* pod, but a message may be created on
*another*. This already works because the **Redis channel layer** (Module 05) is the
shared bus — `group_send` on Pod A reaches the socket on Pod B. That's the whole reason
we used Redis channels instead of in-memory. Two operational notes:
- The ingress keeps long-lived WebSocket connections open (timeout annotations).
- On a rollout, a pod's WebSockets drop; the client's **reconnect-with-backoff**
  (Module 10) re-establishes them on a surviving/new pod.

## 6. Graceful shutdown

When a pod is told to stop, in-flight work shouldn't be lost:
- **Celery workers** get `terminationGracePeriodSeconds: 60` and Celery's warm
  shutdown finishes the current task before exiting (then re-queues the rest).
- **Web** pods drain readiness first so the Service stops sending new requests before
  the process exits.

## 7. The failure drills (the real proof)

HA is only real if you test it. You'll:
- delete a web pod under load → traffic never stops (other replica + fast reschedule),
- delete the Postgres primary → operator promotes a replica, app reconnects,
- drain a node → PDBs + anti-affinity keep every service serving.

---

## 8. Do the lab

Install metrics-server, apply the HPA/PDB/anti-affinity, load-test to watch web
autoscale, then run the failure drills and confirm the app stays available.

👉 **[lab.md](./lab.md)**

Then test yourself: 👉 **[challenge.md](./challenge.md)**

---

## Key terms (see [GLOSSARY](../GLOSSARY.md))

HPA · PodDisruptionBudget · anti-affinity · rolling update · graceful shutdown · channel layer

**Next →** [Module 16: Production Hardening](../16-production-hardening/)
