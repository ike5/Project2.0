# Lab 07 — Jobs, CronJobs, DaemonSets & StatefulSets

**You'll:** run batch and scheduled work, see one-Pod-per-node, and watch a
StatefulSet's stable identities and per-Pod storage. ⏱️ ~55 min.

> Prereqs: cluster up.

---

## Part A — Job

```bash
cd 07-controllers-jobs-statefulsets
kubectl apply -f manifests/job.yaml
kubectl get job pi -w        # watch COMPLETIONS climb 0/3 → 3/3, then Ctrl+C
kubectl get pods -l job-name=pi          # 3 Completed pods
kubectl logs -l job-name=pi --tail=1     # the digits of pi
```
✅ Note: completed Pods stay `Completed` (not restarted) — that's the point of a Job.

## Part B — CronJob

```bash
kubectl apply -f manifests/cronjob.yaml
kubectl get cronjob heartbeat
# wait ~60–120s, then:
kubectl get jobs                    # heartbeat-<timestamp> jobs appear over time
kubectl get pods -l app= --field-selector=status.phase=Succeeded 2>/dev/null
kubectl logs -l job-name="$(kubectl get jobs -o jsonpath='{.items[-1:].metadata.name}')"
```
✅ A new Job (and Pod) is created each minute; old ones are pruned to the history limit.

Stop it so it doesn't keep firing:
```bash
kubectl delete cronjob heartbeat
```

## Part C — DaemonSet

```bash
kubectl apply -f manifests/daemonset.yaml
kubectl get pods -l app=node-agent -o wide
kubectl get ds node-agent
```
✅ One `node-agent` Pod per eligible node. Compare with the built-in DaemonSets:
```bash
kubectl get ds -n kube-system        # kindnet, kube-proxy run as DaemonSets
```

## Part D — StatefulSet: stable identity & per-Pod storage

```bash
kubectl apply -f manifests/statefulset.yaml
kubectl get pods -l app=stateful-web -w     # note ORDERED creation: web-0 then web-1. Ctrl+C
```
Observe the stable names and per-Pod PVCs:
```bash
kubectl get pods -l app=stateful-web        # web-0, web-1 (not random hashes)
kubectl get pvc                             # data-web-0, data-web-1 — one each
```
Each Pod wrote *its own* identity to *its own* volume:
```bash
kubectl exec web-0 -- cat /data/identity.txt    # I am web-0
kubectl exec web-1 -- cat /data/identity.txt    # I am web-1
```

### Stable identity survives deletion
```bash
kubectl delete pod web-0
kubectl get pods -l app=stateful-web -w     # a NEW pod named web-0 (same name!) appears. Ctrl+C
kubectl exec web-0 -- cat /data/identity.txt    # still "I am web-0" — reattached its OWN PVC
```
✅ Unlike a Deployment, the replacement got the **same name** and **same storage**.

### Stable DNS (headless Service)
```bash
kubectl run client --rm -it --image=busybox:1.36 --restart=Never -- sh
  nslookup web-headless           # returns BOTH pod IPs (headless)
  nslookup web-0.web-headless     # resolves the specific pod
  exit
```

## Cleanup
```bash
kubectl delete -f manifests/job.yaml -f manifests/daemonset.yaml -f manifests/statefulset.yaml --ignore-not-found
kubectl delete pvc data-web-0 data-web-1 --ignore-not-found   # StatefulSet PVCs aren't auto-deleted
```
> ⚠️ Deleting a StatefulSet does **not** delete its PVCs (so you don't lose data by
> accident). You remove them explicitly when you really mean it.

## What you learned
- Job = run-to-completion; CronJob = scheduled Job.
- DaemonSet = one Pod per node, auto-extending to new nodes.
- StatefulSet = stable names + per-Pod PVCs + ordered ops + headless DNS — the tool
  for databases and other stateful systems.

➡️ **[challenge.md](./challenge.md)** then [Module 08](../08-scheduling-and-scaling/).
