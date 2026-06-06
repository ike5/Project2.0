# Lab 15 — Autoscale and Survive Failures

**You'll:** enable metrics, apply HPA/PDB/anti-affinity, load-test to watch web
autoscale, then run failure drills proving the app stays up.

⏱️ ~60 min. The Module 14 HA deployment running. Run from `slack-clone-course`.

---

## Part A — Metrics + HA objects

```bash
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
# on kind, allow insecure kubelet TLS:
kubectl -n kube-system patch deploy metrics-server --type=json \
  -p='[{"op":"add","path":"/spec/template/spec/containers/0/args/-","value":"--kubelet-insecure-tls"}]'
kubectl -n kube-system rollout status deploy/metrics-server

kubectl apply -f k8s/ha/hpa.yaml
kubectl apply -f k8s/ha/pdb.yaml
kubectl patch deploy/web -n slack --patch-file k8s/ha/anti-affinity-patch.yaml
```
✅ Check: `kubectl get hpa -n slack` shows targets (not `<unknown>`) after ~30s.

---

## Part B — Watch web spread across nodes

```bash
kubectl get pods -n slack -l app=web -o wide | awk '{print $1, $7}'
```
✅ Expected: the two web pods are on **different** nodes (anti-affinity).

---

## Part C — Load-test → autoscale

Generate load against the health endpoint:
```bash
kubectl run -n slack load --image=williamyeh/hey --restart=Never -- \
  -z 120s -c 80 http://web:8000/api/health/
watch kubectl get hpa,pods -n slack
```
✅ Expected: web CPU climbs past 70%, the HPA raises replicas (toward 8). Stop the load
and watch it scale back down after the stabilization window.

---

## Part D — Drill 1: kill a web pod under load

In one terminal, hammer the app; in another:
```bash
kubectl delete pod -n slack -l app=web --field-selector=status.phase=Running \
  $(kubectl get pod -n slack -l app=web -o name | head -1 | cut -d/ -f2) 2>/dev/null
kubectl get pods -n slack -l app=web -w
```
✅ Expected: requests keep succeeding (the other replica serves) while a replacement
schedules. **Zero user-visible downtime.**

---

## Part E — Drill 2: kill the Postgres primary

With two browsers chatting:
```bash
PRIMARY=$(kubectl get cluster slack-pg -n slack -o jsonpath='{.status.currentPrimary}')
kubectl delete pod "$PRIMARY" -n slack
kubectl get cluster slack-pg -n slack -w
```
✅ Expected: a replica is promoted within seconds, `slack-pg-rw` repoints, and the app
reconnects. A few requests may blip, then recover — no data lost.

---

## Part F — Drill 3: drain a node

```bash
NODE=$(kubectl get pod -n slack -l app=web -o jsonpath='{.items[0].spec.nodeName}')
kubectl drain "$NODE" --ignore-daemonsets --delete-emptydir-data --force
kubectl get pods -n slack -o wide
kubectl uncordon "$NODE"
```
✅ Expected: the PDB stops the drain from removing the last web pod; evicted pods
reschedule onto other nodes; the app stays reachable throughout.

---

## What you learned
- The HPA scales web/worker on CPU (with metrics-server).
- PDBs + anti-affinity keep at least one replica up through drains and node loss.
- Rolling updates and reconnecting WebSocket clients make deploys seamless.
- The failure drills *prove* the app is genuinely highly available.

➡️ Now try the **[challenge](./challenge.md)**, then move to
[Module 16](../16-production-hardening/).
