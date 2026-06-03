# Lab 08 — Placement & Autoscaling

**You'll:** spread Pods across nodes, schedule onto a tainted node with a
toleration, install metrics-server, and watch an HPA scale under load. ⏱️ ~60 min.

> Prereqs: cluster up; `web-api:1.0` loaded.

---

## Part A — See default scheduling

```bash
cd 08-scheduling-and-scaling
kubectl create deployment many --image=web-api:1.0 --replicas=4 \
  --dry-run=client -o yaml | kubectl apply -f -
# (the create above won't set imagePullPolicy; if pods ImagePullBackOff, use the manifest approach instead)
kubectl get pods -l app=many -o wide        # spread across workers, none on control-plane
kubectl delete deployment many
```
✅ The control-plane node has no app Pods — it's **tainted** (we'll override that in C).

## Part B — Spread replicas with anti-affinity

```bash
kubectl apply -f manifests/spread-deploy.yaml
kubectl get pods -l app=spread -o wide      # each replica on a different worker
```
Now scale beyond the node count to see "preferred" (soft) behavior:
```bash
kubectl scale deployment spread --replicas=4
kubectl get pods -l app=spread -o wide      # spreads, but doubles up once nodes run out (preferred = best-effort)
kubectl delete -f manifests/spread-deploy.yaml
```
✅ `preferred` anti-affinity spreads when it can but won't block scheduling. Switch
to `requiredDuringScheduling...` to make it mandatory (and risk `Pending` Pods).

## Part C — Taints & tolerations

```bash
kubectl describe node k8s-course-control-plane | grep Taints   # the control-plane taint
kubectl apply -f manifests/toleration-pod.yaml
kubectl get pod on-control-plane -o wide      # NODE = ...control-plane
kubectl logs on-control-plane                 # "running on k8s-course-control-plane"
kubectl delete -f manifests/toleration-pod.yaml
```
✅ The toleration let the scheduler place the Pod where untolerating Pods can't go.

Experiment: taint a worker yourself, watch Pods avoid it, then remove it:
```bash
kubectl taint nodes k8s-course-worker demo=true:NoSchedule
kubectl create deployment t --image=nginx:1.27 --replicas=3
kubectl get pods -l app=t -o wide              # none land on ...worker
kubectl taint nodes k8s-course-worker demo=true:NoSchedule-   # trailing - removes it
kubectl delete deployment t
```

## Part D — Install metrics-server (for HPA & `kubectl top`)

The upstream metrics-server needs a flag to work on kind's self-signed kubelet certs:
```bash
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
# patch it to tolerate kind's kubelet TLS:
kubectl patch -n kube-system deployment metrics-server --type=json \
  -p='[{"op":"add","path":"/spec/template/spec/containers/0/args/-","value":"--kubelet-insecure-tls"}]'
kubectl rollout status -n kube-system deployment/metrics-server
sleep 20
kubectl top nodes        # CPU/memory now reported
kubectl top pods -A
```
✅ `kubectl top` returns numbers. If it says "metrics not available yet", wait ~30s.

## Part E — Autoscale under load

```bash
kubectl apply -f manifests/hpa-deploy.yaml      # web Deployment (with cpu requests) + Service
kubectl apply -f manifests/hpa.yaml
kubectl get hpa web -w &                        # watch TARGETS and REPLICAS. (we'll kill this later)
```
In another terminal, generate load by hammering the CPU-burning `/work` endpoint:
```bash
# a load generator pod inside the cluster
kubectl run loader --image=busybox:1.36 --restart=Never -- \
  sh -c 'while true; do wget -q -O- http://web/work?ms=300 >/dev/null; done'
```
Watch the HPA over the next 1–3 minutes:
```bash
kubectl get hpa web        # TARGETS climbs past 50%, REPLICAS increases (up toward 10)
kubectl get pods -l app=web
```
✅ The HPA noticed high CPU and scaled out. Now stop the load and watch it scale in:
```bash
kubectl delete pod loader
# wait a few minutes (scale-down is deliberately slow to avoid flapping)
kubectl get hpa web        # REPLICAS drifts back toward 1
```

## Cleanup
```bash
kill %1 2>/dev/null
kubectl delete -f manifests/hpa.yaml -f manifests/hpa-deploy.yaml --ignore-not-found
# (leave metrics-server installed — Module 09 uses it)
```

## What you learned
- The scheduler combines requests (capacity), affinity (preferences), and taints
  (node repulsion) to place Pods.
- Anti-affinity / topology spread give you HA across nodes.
- HPA autoscales replicas from metrics; it needs metrics-server and CPU requests.

➡️ **[challenge.md](./challenge.md)** then [Module 09](../09-observability-and-debugging/).
