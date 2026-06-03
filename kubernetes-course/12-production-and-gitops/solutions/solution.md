# Challenge 12 — Reference Solution

### 1. Quota enforcement proof
```bash
kubectl create ns q
kubectl create quota cpu-quota -n q --hard=requests.cpu=1
kubectl run nodefaults -n q --image=nginx:1.27        # REJECTED
#   Error ... must specify requests.cpu
```
> When a ResourceQuota constrains `requests.cpu`, **every** container must declare a
> CPU request or the create is denied. A **LimitRange** with `defaultRequest` injects
> one automatically, so authors don't have to set it on every Pod. Add a LimitRange
> and the same `kubectl run` succeeds.
```bash
kubectl delete ns q
```

### 2. Tighten a rollout with a PDB
```bash
kubectl create deployment web --image=nginx:1.27 --replicas=5
kubectl label deployment web app=web --overwrite
cat <<'EOF' | kubectl apply -f -
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata: { name: web-pdb }
spec:
  minAvailable: 80%
  selector: { matchLabels: { app: web } }
EOF
kubectl get pdb web-pdb        # ALLOWED DISRUPTIONS reflects 80% of 5 = min 4 available
kubectl drain k8s-course-worker --ignore-daemonsets --force --timeout=30s
# eviction blocks once availability would drop below 4
kubectl uncordon k8s-course-worker
kubectl delete deployment web; kubectl delete pdb web-pdb
```

### 3. GitOps change flow
```bash
# edit manifests/gitops-app/deployment.yaml: replicas: 4
git add kubernetes-course/12-production-and-gitops/manifests/gitops-app/deployment.yaml
git commit -m "scale gitops-web to 4"
git push
# Argo CD syncs within its poll interval (or click Refresh/Sync in UI):
kubectl get deploy gitops-web -n gitops -w     # -> 4 replicas

# rollback:
git revert --no-edit HEAD
git push
kubectl get deploy gitops-web -n gitops -w     # -> back to 2
```

### 4. App-of-apps (stretch)
> A single "root" Argo CD **Application** points at a Git path containing *other*
> Application manifests. Argo CD syncs the root, which creates/childs the rest. One
> repo + one root app then manages an entire platform's worth of apps declaratively;
> adding an app = committing a new Application manifest.

### 5. GitOps vs CI-with-admin-creds
> 1. **Reduced credential blast radius:** with GitOps the in-cluster agent pulls; no
>    long-lived cluster-admin kubeconfig sits in CI where it can leak. CI only needs
>    write access to *Git*.
> 2. **Auditability & drift control:** every change is a reviewed, revertible commit,
>    and Argo CD continuously detects/heals out-of-band `kubectl` changes — so the
>    live state can't silently diverge from what's in version control.
```
