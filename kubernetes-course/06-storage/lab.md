# Lab 06 — Persist Data with PVCs

**You'll:** create a PVC, watch a PV get dynamically provisioned, write data, prove
it survives Pod deletion, and contrast with ephemeral `emptyDir`. ⏱️ ~40 min.

> Prereqs: cluster up.

---

## Part A — Inspect storage capabilities

```bash
cd 06-storage
kubectl get storageclass        # kind ships a default "standard" (local-path)
```
✅ One StorageClass marked `(default)`.

## Part B — Create a PVC and watch dynamic provisioning

```bash
kubectl apply -f manifests/pvc.yaml
kubectl get pvc data            # STATUS: Bound (a PV was auto-created for it)
kubectl get pv                  # the dynamically provisioned PersistentVolume
kubectl describe pvc data | head -20
```
✅ The PVC moved to `Bound` and a PV appeared — **dynamic provisioning** in action.
You never created the PV by hand.

> Note: with kind's local-path provisioner, binding may be `WaitForFirstConsumer` —
> the PV is created once a Pod actually uses the PVC. If STATUS is `Pending`, that's
> expected until Part C schedules the Pod.

## Part C — Mount it and write data

```bash
kubectl apply -f manifests/pod-with-pvc.yaml
kubectl wait --for=condition=Ready pod/writer --timeout=60s
kubectl get pvc data            # now Bound if it was waiting

# write a file into the persistent volume
kubectl exec writer -- sh -c 'echo "persisted at $(date)" > /data/note.txt'
kubectl exec writer -- cat /data/note.txt
```

## Part D — Prove persistence across Pod deletion

```bash
kubectl delete pod writer            # destroy the Pod (and its container filesystem)
kubectl apply -f manifests/pod-with-pvc.yaml   # recreate, mounting the SAME PVC
kubectl wait --for=condition=Ready pod/writer --timeout=60s
kubectl exec writer -- cat /data/note.txt      # the file is STILL THERE
```
✅ The data survived because it lives in the PVC/PV, not the container. This is how
databases keep their data across restarts and rescheduling.

## Part E — Contrast with emptyDir (ephemeral)

```bash
kubectl apply -f manifests/emptydir-pod.yaml
kubectl wait --for=condition=Ready pod/ephemeral --timeout=60s
kubectl exec ephemeral -- sh -c 'echo "temp data" > /scratch/temp.txt; cat /scratch/temp.txt'

kubectl delete pod ephemeral
kubectl apply -f manifests/emptydir-pod.yaml
kubectl wait --for=condition=Ready pod/ephemeral --timeout=60s
kubectl exec ephemeral -- cat /scratch/temp.txt    # No such file — it's GONE
```
✅ `emptyDir` data vanished with the Pod. Use it only for scratch/shared-temp data.

## Part F — Clean up (and see reclaim behavior)

```bash
kubectl delete pod writer ephemeral
kubectl get pv                 # the PV still exists while the PVC exists
kubectl delete pvc data
kubectl get pv                 # with Delete reclaim policy, the PV is removed too
```

## What you learned
- Container filesystems are ephemeral; PVCs give durable storage.
- You request storage with a **PVC**; a **PV** is provisioned (often automatically
  via a **StorageClass**) and bound to it.
- Pods mount the PVC and are oblivious to the underlying disk.
- `emptyDir` is ephemeral; PVCs persist across Pod deletion.

➡️ **[challenge.md](./challenge.md)** then [Module 07](../07-controllers-jobs-statefulsets/).
