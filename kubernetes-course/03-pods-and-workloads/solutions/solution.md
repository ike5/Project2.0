# Challenge 03 — Reference Solution

### 1. Author from scratch
See [`mychal.yaml`](./mychal.yaml).
```bash
kubectl apply -f solutions/mychal.yaml
kubectl get pods -l app=api          # 4 Running
kubectl get pods -l tier=backend     # same 4 (label selection works)
```

### 2. Controlled rollout
The strategy block is already in `mychal.yaml`:
```yaml
strategy:
  type: RollingUpdate
  rollingUpdate:
    maxUnavailable: 1
    maxSurge: 1
```
```bash
kubectl set image deployment/api web-api=web-api:2.0
kubectl rollout status deployment/api
kubectl describe deploy api | grep -A2 RollingUpdateStrategy
```

### 3. Broken rollout + recovery
```bash
kubectl set image deployment/api web-api=web-api:does-not-exist
kubectl get pods -l app=api          # a NEW pod is ImagePullBackOff; the OLD pods stay Running
kubectl rollout status deployment/api --timeout=20s   # will not complete
kubectl describe pod <the-bad-pod> | tail        # Events: pull error

# recover:
kubectl rollout undo deployment/api
kubectl rollout status deployment/api
```
> **Why the app stayed up:** a rolling update only scales down old Pods *as new ones
> become Ready*. The new (broken) Pod never became Ready, so `maxUnavailable: 1`
> kept the old Pods serving. Zero downtime even from a bad deploy.

### 4. Pause / resume
```bash
kubectl rollout pause deployment/api
kubectl set image deployment/api web-api=web-api:2.0
kubectl set env   deployment/api COLOR=teal
kubectl rollout resume deployment/api     # both changes ship in ONE rollout
kubectl rollout status deployment/api
```

Cleanup: `kubectl delete -f solutions/mychal.yaml`
