# Lab 10 — Package with Helm & Kustomize

**You'll:** install/override/upgrade/rollback a Helm chart, then render and apply
Kustomize dev/prod overlays — and compare the two approaches. ⏱️ ~70 min.

> Prereqs: cluster up; `helm` installed; `web-api:1.0` (and ideally `web-api:2.0`) loaded.

---

## Part 1 — Helm

### A. Render before installing (always review!)
```bash
cd 10-packaging-helm-kustomize/manifests/helm
helm template web ./web-api            # see the fully-rendered YAML, no cluster changes
helm lint ./web-api                    # catch chart mistakes
```
✅ Note how `{{ .Values.replicaCount }}` etc. resolved to real values, and names got
the `web-` release prefix from `_helpers.tpl`.

### B. Install a release
```bash
helm install web ./web-api
helm list
kubectl get deploy,svc,pods -l app.kubernetes.io/instance=web
```
✅ A release named `web`; objects are `web-web-api`. 2 replicas (the chart default).

### C. Override values
```bash
# one-off override:
helm upgrade web ./web-api --set replicaCount=4 --set config.color=gold
kubectl get pods -l app.kubernetes.io/instance=web      # 4 now
# a whole prod values file:
helm upgrade web ./web-api -f values-prod.yaml
kubectl get deploy web-web-api -o jsonpath='{.spec.replicas}{"\n"}'   # 5
```

### D. Revisions, upgrade, rollback
```bash
helm history web                       # see revisions 1,2,3...
helm rollback web 1                    # back to the very first install
helm history web                       # a new revision recording the rollback
```
✅ Helm tracks every change as a revision — instant, auditable rollbacks.

### E. Uninstall
```bash
helm uninstall web
```

---

## Part 2 — Kustomize (built into kubectl)

### A. Inspect the structure
```bash
cd ../kustomize
find . -name kustomization.yaml
```
One `base/` with plain YAML; two overlays (`dev`, `prod`) that only express differences.

### B. Render each environment (review the diff)
```bash
kubectl kustomize overlays/dev    | grep -E 'name:|replicas:|value:'
kubectl kustomize overlays/prod   | grep -E 'name:|replicas:|value:'
```
✅ `dev` → names `dev-web-api`, 1 replica, COLOR lime. `prod` → `prod-web-api`,
5 replicas, COLOR crimson. Same base, different overlays — **no templating language**.

### C. Apply an environment
```bash
kubectl apply -k overlays/dev
kubectl get deploy,svc -l app.kubernetes.io/part-of=web-api-demo
kubectl get pods -l app=web-api                # 1 dev pod
```

### D. Apply prod alongside it (different name prefix = no collision)
```bash
kubectl apply -k overlays/prod
kubectl get deploy                              # dev-web-api (1) and prod-web-api (5)
```

### E. Clean up
```bash
kubectl delete -k overlays/dev
kubectl delete -k overlays/prod
```

---

## Reflection: which would you reach for?
- You're shipping `web-api` for *other teams* to install with their own settings →
  **Helm** (values + versioned releases).
- You maintain *your own* `web-api` across dev/stage/prod → **Kustomize** is simpler
  (plain YAML, kubectl-native, just the diffs).

## What you learned
- Helm: charts, values, `template`/`lint`, install/upgrade/rollback, revisions.
- Kustomize: base + overlays, `namePrefix`, `replicas`, patches, `apply -k`.
- The decision criteria between them.

➡️ **[challenge.md](./challenge.md)** then [Module 11](../11-security-rbac-policies/).
