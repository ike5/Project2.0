# Challenge 08 — Reference Solution

### 1. Pin to a node with nodeSelector
```bash
kubectl label node k8s-course-worker tier=hot
```
```yaml
# in the Pod template spec:
spec:
  nodeSelector:
    tier: hot
```
```bash
kubectl get pods -o wide        # all on k8s-course-worker
kubectl label node k8s-course-worker tier-     # cleanup
```

### 2. Hard (required) spread
```yaml
affinity:
  podAntiAffinity:
    requiredDuringSchedulingIgnoredDuringExecution:
      - labelSelector:
          matchLabels: { app: spread }
        topologyKey: kubernetes.io/hostname
```
```bash
kubectl scale deployment spread --replicas=3
kubectl get pods -l app=spread -o wide   # 2 Running (one per worker), 1 Pending
kubectl describe pod <pending-pod> | tail # "didn't match pod anti-affinity rules"
```
> With **required** anti-affinity and `topologyKey=hostname`, no two Pods may share a
> node. You have 2 schedulable workers, so the 3rd Pod stays **Pending** until a 3rd
> node appears. `preferred` would have doubled up instead.

### 3. Topology spread
```yaml
topologySpreadConstraints:
  - maxSkew: 1
    topologyKey: kubernetes.io/hostname
    whenUnsatisfiable: DoNotSchedule
    labelSelector:
      matchLabels: { app: spread }
```
```bash
kubectl scale deployment spread --replicas=4
kubectl get pods -l app=spread -o wide | awk '{print $7}' | sort | uniq -c  # ~2 per worker
```

### 4. Tune an HPA
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata: { name: web }
spec:
  scaleTargetRef: { apiVersion: apps/v1, kind: Deployment, name: web }
  minReplicas: 2
  maxReplicas: 6
  metrics:
    - type: Resource
      resource:
        name: cpu
        target: { type: Utilization, averageUtilization: 70 }
```
> Without `resources.requests.cpu`, utilization is `current / request` = divide by
> nothing → the HPA reports `<unknown>` for the metric and **never scales**. The
> request is the denominator the percentage is measured against.

### 5. Stretch — cordon vs taint
```bash
kubectl cordon k8s-course-worker          # marks node Unschedulable
kubectl rollout restart deployment web
kubectl get pods -l app=web -o wide       # new pods avoid the cordoned worker
kubectl uncordon k8s-course-worker
```
> **Cordon** sets the node `Unschedulable` (no *new* Pods, existing ones stay) — a
> blunt on/off used for maintenance. **Taints** are selective: they repel only Pods
> that don't tolerate a specific key/effect, so you can still allow chosen workloads.
> `kubectl drain` = cordon + evict existing Pods.
