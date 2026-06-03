# Lab 09 — Diagnose Failures & Stand Up Monitoring

**You'll:** debug four broken Pods using only `kubectl`, try `kubectl debug`, then
install Prometheus + Grafana and explore live dashboards. ⏱️ ~70 min.

> Prereqs: cluster up; metrics-server installed (Module 08 Part D); `web-api:1.0` loaded.

---

## Part A — Four broken Pods (diagnose before you read why)

Apply all four, then work each one. **Predict the cause before checking.**
```bash
cd 09-observability-and-debugging
kubectl apply -f manifests/
kubectl get pods        # note the different STATUS values
```

### broken-image
```bash
kubectl describe pod broken-image | sed -n '/Events/,$p'
```
🔎 Events show `Failed to pull image ... not found`. **Fix:** correct the tag.
```bash
kubectl set image pod/broken-image app=nginx:1.27 2>/dev/null || \
  echo "(pods can't change image in place — for a Deployment you'd 'set image')"
```

### broken-crash
```bash
kubectl get pod broken-crash          # CrashLoopBackOff
kubectl logs broken-crash --previous  # 'fatal: config missing' — the app told us
```
🔎 The app exits 1 on startup. In real life you'd fix the config/dependency it needs.

### broken-config
```bash
kubectl describe pod broken-config | sed -n '/Events/,$p'
```
🔎 `configmap "does-not-exist" not found` → `CreateContainerConfigError`. **Fix:**
create the ConfigMap (or correct the reference).
```bash
kubectl create configmap does-not-exist --from-literal=somekey=value
kubectl delete pod broken-config && kubectl apply -f manifests/broken-config.yaml
kubectl get pod broken-config         # now Running
```

### broken-pending
```bash
kubectl describe pod broken-pending | sed -n '/Events/,$p'
```
🔎 `0/3 nodes are available: Insufficient memory`. **Fix:** request a sane amount.

✅ You diagnosed four classic failures using only `get`/`describe`/`logs`.

## Part B — `kubectl debug` (ephemeral containers)

Some images have no shell (distroless). Attach a temporary debug container that
shares the target's namespaces:
```bash
kubectl run quiet --image=nginx:1.27
kubectl wait --for=condition=Ready pod/quiet --timeout=60s
# attach busybox tooling into the running pod:
kubectl debug -it quiet --image=busybox:1.36 --target=quiet -- sh
  # inside: you can see nginx's processes/network
  wget -qO- localhost:80 | head -3
  exit
kubectl delete pod quiet
```

## Part C — Clean up the broken Pods

```bash
kubectl delete -f manifests/ --ignore-not-found
kubectl delete configmap does-not-exist --ignore-not-found
```

## Part D — Install Prometheus + Grafana (kube-prometheus-stack)

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
helm install monitoring prometheus-community/kube-prometheus-stack \
  -n monitoring --create-namespace
kubectl rollout status -n monitoring deployment/monitoring-grafana
kubectl get pods -n monitoring      # prometheus, grafana, alertmanager, exporters
```
(This pulls several images — give it a few minutes.)

## Part E — Explore Grafana

```bash
# default admin password for this chart:
kubectl get secret -n monitoring monitoring-grafana \
  -o jsonpath='{.data.admin-password}' | base64 -d ; echo
kubectl port-forward -n monitoring svc/monitoring-grafana 3000:80
```
Open <http://localhost:3000> → log in as `admin` / (the password above) →
**Dashboards** → explore the prebuilt ones:
- **Kubernetes / Compute Resources / Cluster** — overall usage
- **Kubernetes / Compute Resources / Namespace (Pods)** — per-Pod CPU/memory
- **Node Exporter / Nodes** — node-level metrics

✅ You're now looking at real metrics scraped from your cluster. Generate load (the
`/work` endpoint from Module 08) and watch the graphs move.

Peek at Prometheus directly too:
```bash
kubectl port-forward -n monitoring svc/monitoring-kube-prometheus-prometheus 9090:9090
# open http://localhost:9090 and run a query, e.g.:  sum(rate(container_cpu_usage_seconds_total[5m])) by (pod)
```

## Cleanup (optional — it uses RAM)
```bash
helm uninstall monitoring -n monitoring
kubectl delete ns monitoring
```

## What you learned
- The `get → describe → logs --previous` reflex solves most failures.
- `kubectl debug` rescues you on shell-less images.
- kube-prometheus-stack gives you production-grade metrics + dashboards in one install.

➡️ **[challenge.md](./challenge.md)** then [Module 10](../10-packaging-helm-kustomize/).
