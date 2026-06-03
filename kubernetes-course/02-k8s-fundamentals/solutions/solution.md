# Challenge 02 — Reference Solution

### 1. Busiest node
```bash
kubectl get pods -A -o wide --sort-by=.spec.nodeName
# or count per node:
kubectl get pods -A -o jsonpath='{range .items[*]}{.spec.nodeName}{"\n"}{end}' | sort | uniq -c | sort -rn
```
The control-plane node usually has the most (it runs all the system components).

### 2. Explain imagePullPolicy
```bash
kubectl explain pod.spec.containers.imagePullPolicy
```
> Values: `Always`, `Never`, `IfNotPresent`. Defaults to `IfNotPresent` for tagged
> images and `Always` for `:latest`. (This is why we use `Never` for local kind images.)

### 3. Prove reconciliation
```bash
kubectl run solo --image=nginx:1.27
kubectl create deployment managed --image=nginx:1.27

# delete the bare pod — it stays gone:
kubectl delete pod solo
kubectl get pod solo                 # NotFound

# delete the managed pod — it comes back:
MPOD=$(kubectl get pod -l app=managed -o jsonpath='{.items[0].metadata.name}')
kubectl delete pod "$MPOD"
kubectl get pods -l app=managed      # a new pod appears
```
> The **ReplicaSet** (created and owned by the Deployment) recreated the Pod: its
> controller saw `desired=1, actual=0` and reconciled.

Cleanup: `kubectl delete deployment managed`

### 4. Cross-namespace Pod IP
```bash
kubectl create namespace team-a
kubectl run web --image=nginx:1.27 -n team-a
kubectl get pod web -n team-a -o jsonpath='{.status.podIP}{"\n"}'
```
Cleanup: `kubectl delete ns team-a`

### 5. Stretch
```bash
kubectl get pod <name> -o jsonpath='node={.spec.nodeName} phase={.status.phase}{"\n"}'
```
