# Lab 17 — Deploy, Load, and Break It

**You'll:** deploy the complete app to the HA cluster, run the acceptance checklist,
load-test, and execute all six failure drills.

⏱️ ~2–3 h. Everything from Modules 13–16 installed (operators, metrics-server,
ingress, cert-manager). Run from `slack-clone-course`.

---

## Part A — Build, load, deploy

```bash
# fresh images
docker build -t slack-backend:rc1 ./apps/slack-backend
docker build -t slack-frontend:rc1 \
  --build-arg NEXT_PUBLIC_API_URL=https://slack.local \
  --build-arg NEXT_PUBLIC_WS_URL=wss://slack.local ./apps/slack-frontend
kind load docker-image slack-backend:rc1 slack-frontend:rc1 --name slack

# data tier (operators) + app + HA + hardening
kubectl apply -f k8s/data/postgres-cluster.yaml -f k8s/data/redis-failover.yaml
kubectl apply -k k8s/base
kubectl apply -f k8s/data/config-operators.yaml
kubectl set image -n slack deploy/web web=slack-backend:rc1
kubectl set image -n slack deploy/worker worker=slack-backend:rc1
kubectl set image -n slack deploy/beat beat=slack-backend:rc1
kubectl set image -n slack deploy/frontend frontend=slack-frontend:rc1
kubectl apply -f k8s/ha/hpa.yaml -f k8s/ha/pdb.yaml
kubectl patch deploy/web -n slack --patch-file k8s/ha/anti-affinity-patch.yaml
kubectl apply -f k8s/hardening/tls.yaml
kubectl rollout restart deploy/web deploy/worker deploy/beat -n slack
```

Run migrations and seed an admin/workspace:
```bash
kubectl delete job migrate -n slack 2>/dev/null; kubectl apply -f k8s/base/migrate-job.yaml
kubectl wait -n slack --for=condition=complete job/migrate --timeout=180s
```
✅ **Checkpoint:** every pod `Ready`; `kubectl get cluster slack-pg -n slack` healthy.

---

## Part B — Acceptance checklist

Walk the table in the README at <https://slack.local>: auth, live chat across two
browsers, an @mention email in MailHog, an upload to MinIO, a search, and an incoming
webhook post. Tick every box. Then run [../VERIFY.md](../VERIFY.md) §9 (and earlier
sections as needed).

---

## Part C — Load test

```bash
# many connections hammering the API; for WS load, script multiple wscat clients
kubectl run -n slack load --image=williamyeh/hey --restart=Never -- \
  -z 180s -c 150 https://web:8000/api/health/
watch kubectl get hpa,pods -n slack
```
✅ Record: peak web replica count, and that the app stayed responsive. Scale subsides
after load stops.

---

## Part D — The six failure drills

Keep two browsers chatting throughout. For each, note what users experienced.

```bash
# 1. web pod
kubectl delete pod -n slack $(kubectl get pod -n slack -l app=web -o name | head -1 | cut -d/ -f2)
# 2. worker mid-task (enqueue a slow task first)
kubectl delete pod -n slack $(kubectl get pod -n slack -l app=worker -o name | head -1 | cut -d/ -f2)
# 3. postgres primary
kubectl delete pod -n slack $(kubectl get cluster slack-pg -n slack -o jsonpath='{.status.currentPrimary}')
# 4. redis master
kubectl delete pod -n slack -l app.kubernetes.io/component=redis,redisfailovers.databases.spotahome.com/name=slack-redis 2>/dev/null | head -1
# 5. drain a node
NODE=$(kubectl get pod -n slack -l app=web -o jsonpath='{.items[0].spec.nodeName}')
kubectl drain "$NODE" --ignore-daemonsets --delete-emptydir-data --force; kubectl uncordon "$NODE"
# 6. rolling update under load
kubectl set image -n slack deploy/web web=slack-backend:rc1 && kubectl rollout status -n slack deploy/web
```
✅ **Pass criteria:** in every drill the app stayed available or recovered within
seconds, and no committed message was lost.

---

## Part E — Write the runbook

Create `RUNBOOK.md`: architecture diagram, deploy + rollback commands, the six drills
and their observed outcomes, and known limitations / next steps.

---

## What you accomplished
You deployed a real-time, async, highly-available Slack clone to Kubernetes and
**proved** it survives failures. That's a genuine production system — and a portfolio
centerpiece. 🎉

➡️ Final flourish: the **[challenge](./challenge.md)** — extend it with a feature of
your own.
