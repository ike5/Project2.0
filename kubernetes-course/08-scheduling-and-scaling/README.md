# Module 08 — Scheduling & Scaling

**Goal:** control *where* Pods run and let the cluster *automatically* adjust how
many run based on load.

⏱️ ~2 hours · 🎯 Prereq: Modules 00–07. We'll install `metrics-server`.

---

## Part 1 — Scheduling: where do Pods land?

When you create a Pod, the **scheduler** filters nodes (which *can* run it?) then
scores them (which is *best*?). You can influence both.

### nodeSelector (simplest)
Run only on nodes with a matching label:
```yaml
spec:
  nodeSelector:
    disktype: ssd
```

### Affinity / anti-affinity (expressive)
- **nodeAffinity** — like nodeSelector but with `required` vs `preferred` and
  operators (`In`, `NotIn`, `Exists`).
- **podAffinity** — schedule near Pods with certain labels (co-locate).
- **podAntiAffinity** — schedule *away* from them (spread replicas across nodes for HA).

```yaml
affinity:
  podAntiAffinity:
    preferredDuringSchedulingIgnoredDuringExecution:
      - weight: 100
        podAffinityTerm:
          labelSelector:
            matchLabels: { app: web }
          topologyKey: kubernetes.io/hostname   # "spread across hosts"
```

### Taints & tolerations (nodes repel Pods)
A **taint** on a node repels Pods unless they have a matching **toleration**. This
is the inverse of affinity: the *node* says "stay away unless you tolerate me."
That's why your kind control-plane node normally runs no app Pods — it's tainted:
```bash
kubectl describe node k8s-course-control-plane | grep Taints
# node-role.kubernetes.io/control-plane:NoSchedule
```
A Pod with the matching toleration *may* run there.

### topologySpreadConstraints (even spreading)
Modern, declarative way to spread Pods evenly across zones/nodes:
```yaml
topologySpreadConstraints:
  - maxSkew: 1
    topologyKey: kubernetes.io/hostname
    whenUnsatisfiable: DoNotSchedule
    labelSelector:
      matchLabels: { app: web }
```

> Mental model: **affinity = Pod's preferences**, **taints = node's repulsion**,
> **requests = capacity math** (Module 04). The scheduler combines all of them.

## Part 2 — Scaling

### Manual
`kubectl scale deployment web --replicas=5` (or edit `replicas:` and apply).

### Horizontal Pod Autoscaler (HPA)
The **HPA** automatically changes `replicas` based on observed metrics (CPU by
default). It needs a metrics source — we install **metrics-server**.

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
spec:
  scaleTargetRef: { apiVersion: apps/v1, kind: Deployment, name: web }
  minReplicas: 1
  maxReplicas: 10
  metrics:
    - type: Resource
      resource:
        name: cpu
        target: { type: Utilization, averageUtilization: 50 }  # target 50% of REQUESTS
```

The HPA loop: read average CPU across Pods → compare to target → compute desired
replicas → scale. **It requires `resources.requests.cpu` to be set** (it scales
relative to the request).

> Other autoscalers exist: **VPA** (right-sizes requests/limits) and the
> **Cluster Autoscaler** (adds/removes *nodes*). HPA (more Pods) is the one you'll
> use most and the only one we run locally.

---

## Do the lab
Spread Pods across nodes, run a Pod on the tainted control-plane via a toleration,
then install metrics-server and watch an HPA scale `web-api` up under load and back
down. 👉 **[lab.md](./lab.md)**

Then: 👉 **[challenge.md](./challenge.md)**

## Manifests
- [`spread-deploy.yaml`](./manifests/spread-deploy.yaml) — anti-affinity spreading
- [`toleration-pod.yaml`](./manifests/toleration-pod.yaml) — tolerates the control-plane taint
- [`hpa-deploy.yaml`](./manifests/hpa-deploy.yaml) — Deployment with CPU requests
- [`hpa.yaml`](./manifests/hpa.yaml) — the HorizontalPodAutoscaler

## Key terms
scheduler · nodeSelector · nodeAffinity · podAffinity/anti-affinity · taint ·
toleration · topologySpreadConstraints · HPA · metrics-server · utilization

**Next →** [Module 09: Observability & Debugging](../09-observability-and-debugging/)
