# Lab 14 — HA Postgres & Redis with Operators

**You'll:** install the CloudNativePG and redis operators, create HA clusters, point
the app at them, re-run migrations, and verify the topology.

⏱️ ~60 min. The Module 13 deployment running. Run from `slack-clone-course`.

---

## Part A — Install the operators

CloudNativePG:
```bash
kubectl apply --server-side -f \
  https://raw.githubusercontent.com/cloudnative-pg/cloudnative-pg/release-1.24/releases/cnpg-1.24.0.yaml
kubectl -n cnpg-system wait --for=condition=Available deploy/cnpg-controller-manager --timeout=120s
```

redis-operator (Helm):
```bash
helm repo add redis-operator https://spotahome.github.io/redis-operator && helm repo update
helm install redis-operator redis-operator/redis-operator -n slack
```
✅ **Checkpoint:** both operator controllers are `Running`.

---

## Part B — Create the HA clusters

```bash
kubectl apply -f k8s/data/postgres-cluster.yaml
kubectl apply -f k8s/data/redis-failover.yaml

kubectl get cluster -n slack -w           # wait until slack-pg shows 3 instances healthy
kubectl get pods -n slack -l app.kubernetes.io/component=redis
```
✅ Expected: `slack-pg-1/-2/-3` pods (one primary, two replicas) and the
`rfr-`/`rfs-` Redis + Sentinel pods.

Inspect the failover-aware services CloudNativePG created:
```bash
kubectl get svc -n slack | grep slack-pg
# slack-pg-rw (primary), slack-pg-ro (replicas), slack-pg-r (any)
```

---

## Part C — Point the app at the HA tier

```bash
kubectl apply -f k8s/data/config-operators.yaml      # overrides DATABASE_URL/REDIS_URL
kubectl rollout restart deploy/web deploy/worker deploy/beat -n slack
```

Re-run migrations against the new database:
```bash
kubectl apply -f k8s/base/migrate-job.yaml
kubectl delete job migrate -n slack 2>/dev/null; kubectl apply -f k8s/base/migrate-job.yaml
kubectl wait -n slack --for=condition=complete job/migrate --timeout=120s
```
✅ **Checkpoint:** the app comes back up, now backed by the operator clusters. Re-create
your admin/workspace (it's a fresh database) and confirm chat still works at
`http://slack.local`.

---

## Part D — Confirm one primary, and read replicas

```bash
kubectl get cluster slack-pg -n slack -o jsonpath='{.status.currentPrimary}{"\n"}'
# e.g. slack-pg-1
kubectl cnpg status slack-pg -n slack       # (with the cnpg kubectl plugin) full topology
```
✅ Expected: exactly one current primary; the other two are streaming replicas.

---

## Part E — A taste of failover (full drill in Module 15)

```bash
PRIMARY=$(kubectl get cluster slack-pg -n slack -o jsonpath='{.status.currentPrimary}')
kubectl delete pod "$PRIMARY" -n slack
kubectl get cluster slack-pg -n slack -w     # a replica is promoted; currentPrimary changes
```
✅ Expected: within seconds a **new** primary is elected and `slack-pg-rw` repoints to
it. Your app reconnects on its own.

---

## What you learned
- Operators manage databases via custom resources, handling replication and failover.
- CloudNativePG's `-rw` service always points at the live primary.
- Redis stays HA via Sentinel — vital since it's both broker and channel layer.
- Repointing the app was a config change + rollout restart, no code change.

➡️ Now try the **[challenge](./challenge.md)**, then move to
[Module 15](../15-high-availability/).
