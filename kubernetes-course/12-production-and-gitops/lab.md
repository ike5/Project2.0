# Lab 12 — Quotas, Disruption Budgets & GitOps with Argo CD

**You'll:** put guardrails on a namespace, add a PodDisruptionBudget, then install
Argo CD and let it deploy + self-heal an app straight from Git. ⏱️ ~80 min.

> Prereqs: cluster up; internet access (Argo CD pulls images & your repo).

---

## Part A — ResourceQuota & LimitRange

```bash
cd 12-production-and-gitops
kubectl create namespace team-a
kubectl apply -f manifests/quota.yaml
kubectl apply -f manifests/limitrange.yaml
kubectl describe resourcequota team-a-quota -n team-a
```

Watch the LimitRange inject defaults. Create a Pod with NO resources set:
```bash
kubectl run nodefaults -n team-a --image=nginx:1.27
kubectl get pod nodefaults -n team-a -o jsonpath='{.spec.containers[0].resources}{"\n"}'
```
✅ It got `requests` and `limits` from the LimitRange even though you specified none.

Hit the quota ceiling on purpose:
```bash
# pods quota is 10; LimitRange gives each 100m request. Try to exceed requests.cpu=2:
kubectl create deployment hog -n team-a --image=nginx:1.27 --replicas=25
kubectl get deploy hog -n team-a              # fewer than 25 available
kubectl describe replicaset -n team-a -l app=hog | grep -i forbidden | head -1
```
✅ The ReplicaSet can't create all Pods — `exceeded quota`. Quotas protect the cluster.

Cleanup:
```bash
kubectl delete deployment hog nodefaults -n team-a --ignore-not-found
```

## Part B — PodDisruptionBudget

```bash
kubectl create deployment web -n team-a --image=nginx:1.27 --replicas=3
kubectl label deployment web -n team-a app=web --overwrite
kubectl apply -f manifests/pdb.yaml
kubectl get pdb web-pdb -n team-a              # ALLOWED DISRUPTIONS: 1 (3 running, min 2)
```
Try to drain a node and watch the PDB protect availability:
```bash
kubectl drain k8s-course-worker --ignore-daemonsets --delete-emptydir-data --force --timeout=30s
# eviction respects the PDB: it won't take pods below minAvailable=2
kubectl uncordon k8s-course-worker
```
Cleanup: `kubectl delete ns team-a`

## Part C — Install Argo CD

```bash
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
kubectl -n argocd rollout status deployment/argocd-server --timeout=180s
kubectl get pods -n argocd
```

Log in to the UI:
```bash
# initial admin password:
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath='{.data.password}' | base64 -d ; echo
kubectl port-forward -n argocd svc/argocd-server 8080:443
```
Open <https://localhost:8080> (accept the self-signed cert) → user `admin` + that password.

## Part D — Deploy an app from Git

> First, **push this course to your own GitHub repo** and edit
> `manifests/argocd-application.yaml` so `repoURL` points at YOUR repo. Argo CD must
> be able to reach it (public repo, or add credentials).

```bash
kubectl apply -f manifests/argocd-application.yaml
kubectl get application -n argocd gitops-web
# watch it sync:
kubectl get pods -n gitops -w        # gitops-web pods appear, deployed BY Argo CD. Ctrl+C
```
✅ You never ran `kubectl apply` for the app itself — Argo CD pulled it from Git and
created the namespace + Deployment + Service. In the UI you'll see it **Synced** and **Healthy**.

## Part E — Watch self-heal revert drift

Make a manual change and watch Argo CD undo it:
```bash
kubectl scale deployment gitops-web -n gitops --replicas=5
kubectl get deploy gitops-web -n gitops -w
# within moments Argo CD detects drift (Git says 2) and scales it BACK to 2. Ctrl+C
```
✅ **This is GitOps self-heal**: the cluster is forced to match Git, not your `kubectl`.

To *actually* change replicas, edit `manifests/gitops-app/deployment.yaml` (set
`replicas: 4`), commit, and push — Argo CD syncs the new desired state. (`git revert`
is your rollback.)

## Cleanup
```bash
kubectl delete -f manifests/argocd-application.yaml
kubectl delete ns gitops --ignore-not-found
# optional: remove Argo CD
# kubectl delete ns argocd
```

## What you learned
- ResourceQuota + LimitRange keep namespaces within bounds and inject sane defaults.
- PodDisruptionBudgets protect availability during voluntary disruptions.
- Argo CD makes **Git the source of truth**: it deploys from a repo and self-heals drift.

➡️ **[challenge.md](./challenge.md)** then the **[Capstone](../13-capstone/)**.
