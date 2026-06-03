# Challenge 09 — Reference Solution

### 1. Cold diagnosis — the evidence map
| Status | Command | The line that proves it |
|--------|---------|-------------------------|
| ImagePullBackOff | `describe` Events | `Failed to pull image ...: not found` |
| CrashLoopBackOff | `logs --previous` | the app's error / non-zero exit |
| CreateContainerConfigError | `describe` Events | `configmap "X" not found` |
| Pending | `describe` Events | `0/3 nodes available: Insufficient memory` |

### 2. Failing-probe CrashLoop
```yaml
livenessProbe:
  httpGet: { path: /wrong, port: 8080 }
  periodSeconds: 1
  failureThreshold: 1
```
```bash
kubectl get pods -l app=web -w           # RESTARTS climbs, CrashLoopBackOff
kubectl describe pod <pod> | grep -A2 Liveness
#  Liveness probe failed: HTTP probe failed with statuscode: 404
kubectl logs <pod>                       # app logs look HEALTHY -> it's the probe, not the app
```
Fix: point liveness at `/healthz`, raise `initialDelaySeconds`/`failureThreshold`.
> Key tell: the **app logs are clean** but `describe` shows probe failures →
> the probe is killing a healthy app.

### 3. Service-has-no-endpoints vs wrong targetPort
```bash
kubectl get endpoints web      # endpoints EXIST (selector is fine)...
# ...but curling hangs because targetPort 80 hits a closed port (app listens on 8080)
kubectl get svc web -o jsonpath='{.spec.ports[0].targetPort}{"\n"}'   # 80 — wrong
kubectl patch svc web -p '{"spec":{"ports":[{"port":80,"targetPort":8080}]}}'
```
> **Selector mismatch** → `get endpoints` is *empty* (no Pods matched).
> **targetPort mismatch** → endpoints are *present* but connections fail/timeout
> because traffic is sent to a port nothing listens on.

### 4. Top 3 Pods by CPU (PromQL)
```
topk(3, sum(rate(container_cpu_usage_seconds_total{container!=""}[5m])) by (pod))
```
Run in Prometheus (`:9090`) or Grafana Explore. Or quickly: `kubectl top pods -A --sort-by=cpu | head`.

### 5. kubectl debug
```bash
kubectl run target --image=nginx:1.27
kubectl debug -it target --image=busybox:1.36 --target=target -- sh
  netstat -tlnp 2>/dev/null; wget -qO- localhost:80 | head -3
  exit
kubectl delete pod target
```
> The ephemeral container shares the target Pod's network namespace, so `localhost`
> reaches the target's app even though the target image has no shell of its own.
