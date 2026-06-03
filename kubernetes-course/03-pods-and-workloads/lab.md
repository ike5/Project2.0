# Lab 03 — Deploy, Scale, Update, Roll Back

**You'll:** run a 3-replica Deployment, scale it, see load balancing across Pods,
do a rolling update to v2, then roll back. ⏱️ ~50 min.

> Prereqs: cluster up; `web-api:1.0` loaded (`kind load docker-image web-api:1.0 --name k8s-course`).

---

## Part A — Deploy

```bash
cd 03-pods-and-workloads
kubectl apply -f manifests/web-deploy.yaml
kubectl get deploy,rs,pods -l app=web
```
✅ Expected: 1 Deployment, 1 ReplicaSet (`web-xxxxx`), 3 Pods (`web-xxxxx-yyyyy`)
all `Running`. Notice the naming: `<deployment>-<replicaset-hash>-<pod-id>`.

See which nodes they landed on:
```bash
kubectl get pods -l app=web -o wide
```
✅ The scheduler likely spread them across both worker nodes.

## Part B — Inspect the ownership chain

```bash
kubectl describe deploy web | head -30        # strategy, replicas, events
RS=$(kubectl get rs -l app=web -o jsonpath='{.items[0].metadata.name}')
kubectl get rs "$RS" -o jsonpath='owner: {.metadata.ownerReferences[0].kind}/{.metadata.ownerReferences[0].name}{"\n"}'
POD=$(kubectl get pod -l app=web -o jsonpath='{.items[0].metadata.name}')
kubectl get pod "$POD" -o jsonpath='owner: {.metadata.ownerReferences[0].kind}/{.metadata.ownerReferences[0].name}{"\n"}'
```
✅ Pod is owned by the ReplicaSet, which is owned by the Deployment.

## Part C — Self-healing

```bash
kubectl delete pod "$POD"
kubectl get pods -l app=web -w     # a replacement appears, back to 3. Ctrl+C
```

## Part D — Scale

```bash
kubectl scale deployment web --replicas=5
kubectl get pods -l app=web        # 5 now
kubectl scale deployment web --replicas=3
```
(Or edit `replicas:` in the YAML and `kubectl apply` — declarative is preferred.)

## Part E — Watch load balancing across Pods

Port-forward goes to a single Pod, so to *see* load balancing we'll hit each Pod's
`served_by`. First, exec into a temporary client and curl the Pods directly:
```bash
# get the Pod IPs
kubectl get pods -l app=web -o jsonpath='{range .items[*]}{.status.podIP}{"\n"}{end}'

# spin up a throwaway client in the cluster and hit them
kubectl run client --rm -it --image=busybox:1.36 --restart=Never -- sh
  # inside (replace with real IPs you listed above):
  wget -qO- http://<pod-ip-1>:8080/ ; echo
  wget -qO- http://<pod-ip-2>:8080/ ; echo
  exit
```
✅ Each responds with a different `served_by` (the pod name). In Module 05 a Service
will load-balance across these automatically.

## Part F — Rolling update to v2

Build and load a v2 image with a visibly different config:
```bash
# from the app dir, build a v2 (we'll just change COLOR via the manifest, and tag a new image)
cd ../apps/web-api
docker build -t web-api:2.0 .
kind load docker-image web-api:2.0 --name k8s-course
cd ../../03-pods-and-workloads
```
Trigger the rolling update (change image + an env var), watching it happen:
```bash
kubectl set image deployment/web web-api=web-api:2.0
kubectl set env  deployment/web COLOR=green APP_VERSION=2.0.0
kubectl rollout status deployment/web        # blocks until complete
```
Observe the two ReplicaSets during/after:
```bash
kubectl get rs -l app=web        # old RS scaled to 0, new RS at 3
kubectl rollout history deployment/web
```

## Part G — Roll back

```bash
kubectl rollout undo deployment/web
kubectl rollout status deployment/web
kubectl get rs -l app=web        # the previous RS is active again
```
✅ Rollback is instant because the old ReplicaSet was kept around.

## Part H — Init containers & sidecars

```bash
kubectl apply -f manifests/pod-with-init.yaml
kubectl get pod init-demo -w      # watch: Init:0/1 → PodInitializing → Running. Ctrl+C
kubectl logs init-demo -c setup   # the init container's output
kubectl port-forward pod/init-demo 8081:80 &
curl -s localhost:8081/ ; echo    # "Prepared by init at ..." — written by the init container!
kill %1
```
✅ The main nginx served a file created by the init container via a shared volume.

## Cleanup
```bash
kubectl delete -f manifests/
```

## What you learned
- Deployment → ReplicaSet → Pod ownership and naming.
- Scaling, self-healing, rolling updates, and instant rollbacks.
- Init containers prepare state before the app starts; sidecars run alongside.

➡️ **[challenge.md](./challenge.md)** then [Module 04](../04-configuration/).
