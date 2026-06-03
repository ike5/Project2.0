# Challenge 07 — Reference Solution

### 1. Parallel batch Job
```yaml
apiVersion: batch/v1
kind: Job
metadata: { name: batch }
spec:
  completions: 6
  parallelism: 3
  template:
    spec:
      restartPolicy: OnFailure
      containers:
        - name: work
          image: busybox:1.36
          command: ["sh","-c","sleep $((RANDOM%3+1)); echo done on $(hostname)"]
```
```bash
kubectl apply -f batch.yaml
kubectl get job batch -w           # COMPLETIONS 0/6 → 6/6
kubectl get pods -l job-name=batch # 6 Completed
```

### 2. A failing Job
```yaml
apiVersion: batch/v1
kind: Job
metadata: { name: flaky }
spec:
  backoffLimit: 2
  template:
    spec:
      restartPolicy: Never
      containers:
        - name: fail
          image: busybox:1.36
          command: ["sh","-c","echo trying; exit 1"]
```
```bash
kubectl apply -f flaky.yaml
kubectl get job flaky -w           # never completes; eventually BackoffLimitExceeded
kubectl describe job flaky | tail  # Events show retries + "Job has reached the specified backoff limit"
```
> Backoff/failure is reported in the **Job's Events** (`kubectl describe job`) and
> its `.status.conditions` (`type: Failed`).

### 3. Scheduled cleanup CronJob
```yaml
apiVersion: batch/v1
kind: CronJob
metadata: { name: cleanup }
spec:
  schedule: "*/2 * * * *"
  concurrencyPolicy: Forbid
  successfulJobsHistoryLimit: 2
  jobTemplate:
    spec:
      template:
        spec:
          restartPolicy: OnFailure
          containers:
            - name: clean
              image: busybox:1.36
              command: ["sh","-c","echo cleaning at $(date)"]
```
```bash
kubectl apply -f cleanup.yaml
# wait a few minutes:
kubectl get jobs        # never more than 2 successful 'cleanup-*' retained
kubectl delete cronjob cleanup
```

### 4. StatefulSet scaling
```bash
kubectl apply -f manifests/statefulset.yaml
kubectl scale statefulset web --replicas=3
kubectl get pods -l app=stateful-web -w    # web-2 created AFTER web-0/web-1 are Ready
kubectl get pvc                            # new data-web-2 appears
kubectl scale statefulset web --replicas=1
kubectl get pods -l app=stateful-web       # web-2 then web-1 terminate (reverse order)
kubectl get pvc                            # data-web-1, data-web-2 REMAIN (not deleted)
```
> Scale-down is reverse-ordinal and **preserves PVCs** — so scaling back up re-binds
> the same data. You delete PVCs manually if you truly want the data gone.

### 5. Decision drill
- **(a) Redis cluster → StatefulSet.** Needs stable identity + per-node persistence.
- **(b) Nightly DB backup → CronJob.** Scheduled, run-to-completion.
- **(c) node-exporter → DaemonSet.** One agent on every node.
- **(d) Stateless REST API → Deployment.** Interchangeable replicas, rolling updates.

Cleanup:
```bash
kubectl delete -f batch.yaml -f flaky.yaml --ignore-not-found
kubectl delete statefulset web --ignore-not-found
kubectl delete pvc -l app=stateful-web --ignore-not-found
```
