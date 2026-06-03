# Lab 02 — Explore the Cluster & Your First Pod

**You'll:** poke at the cluster internals, watch reconciliation heal a Pod, and go
from imperative to declarative. ⏱️ ~45 min.

> Make sure your cluster is up: `kubectl get nodes` → 3 Ready.

---

## Part A — See the architecture for real

```bash
# The "nodes" are Docker containers:
docker ps --format 'table {{.Names}}\t{{.Image}}' | grep k8s-course

# Cluster-wide view:
kubectl get nodes -o wide
kubectl cluster-info

# The control-plane components run as Pods in kube-system:
kubectl get pods -n kube-system
```
✅ You should see `kube-apiserver-...`, `etcd-...`, `kube-scheduler-...`,
`kube-controller-manager-...`, `coredns-...`, and `kindnet-...` (the CNI).

```bash
# Every kind of object the API server knows about:
kubectl api-resources | head -30
```

## Part B — kubectl is an API client (peek at the HTTP)

```bash
kubectl get pods -n kube-system -v=6     # see the HTTP request URLs
```
Notice lines like `GET https://127.0.0.1:.../api/v1/namespaces/kube-system/pods`.
That's all kubectl is doing — talking to the api-server.

## Part C — Built-in docs with `explain`

```bash
kubectl explain pod
kubectl explain pod.spec
kubectl explain pod.spec.containers.resources
```
Use this *constantly* instead of guessing field names.

## Part D — Your first Pod (imperative)

```bash
kubectl run hello --image=nginx:1.27
kubectl get pods
kubectl get pods -o wide          # which node did the scheduler pick?
kubectl describe pod hello        # read the Events: Scheduled → Pulling → Created → Started
```

Reach it:
```bash
kubectl port-forward pod/hello 8080:80 &
curl -s -o /dev/null -w "%{http_code}\n" localhost:8080   # 200
kill %1
```

## Part E — Watch reconciliation heal (the magic moment)

A bare Pod is **not** managed by a controller, so deleting it does *not* bring it
back — it just disappears. Confirm that:
```bash
kubectl delete pod hello
kubectl get pods            # gone, not recreated
```

Now compare with a Deployment (which IS reconciled):
```bash
kubectl create deployment hello --image=nginx:1.27
kubectl get pods            # one pod, name like hello-xxxx-yyyy
POD=$(kubectl get pod -l app=hello -o jsonpath='{.items[0].metadata.name}')
kubectl delete pod "$POD"
kubectl get pods -w         # watch: the deleted pod is replaced within seconds! Ctrl+C
```
✅ **This is reconciliation.** The ReplicaSet controller saw "desired 1, actual 0"
and created a replacement. You'll go deep on this in Module 03.

## Part F — Imperative → declarative

Generate YAML from an imperative command instead of writing it by hand:
```bash
kubectl create deployment hello2 --image=nginx:1.27 --dry-run=client -o yaml > manifests/hello-deploy.yaml
cat manifests/hello-deploy.yaml
```
Apply it declaratively:
```bash
kubectl apply -f manifests/hello-deploy.yaml
kubectl get deploy
```
Now edit the file (e.g. set `replicas: 2`) and re-apply — `apply` figures out the diff:
```bash
kubectl diff -f manifests/hello-deploy.yaml   # preview the change
# (after editing replicas to 2)
kubectl apply -f manifests/hello-deploy.yaml
kubectl get pods
```

## Part G — Namespaces

```bash
kubectl get ns
kubectl create namespace playground
kubectl run tmp --image=nginx:1.27 -n playground
kubectl get pods                      # default ns — tmp not shown
kubectl get pods -n playground        # there it is
kubectl get pods -A                   # every namespace
```

## Cleanup
```bash
kubectl delete deployment hello hello2
kubectl delete namespace playground
```

## What you learned
- The control plane and node components, seen live.
- `kubectl` is an API client; `explain` is your friend.
- **Bare Pods aren't healed; controllers reconcile.**
- Generate YAML imperatively, then manage it declaratively.

➡️ **[challenge.md](./challenge.md)** then [Module 03](../03-pods-and-workloads/).
