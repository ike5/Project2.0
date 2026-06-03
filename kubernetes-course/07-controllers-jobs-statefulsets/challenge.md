# Challenge 07 — Pick the Right Controller

Solutions in [`solutions/`](./solutions/). Try first.

## Tasks

1. **Parallel batch Job.** Write a Job that runs a script 6 times total
   (`completions: 6`) with 3 running concurrently (`parallelism: 3`), where each
   run sleeps a random 1–3 seconds and prints its hostname. Confirm 6 Completed Pods.

2. **A failing Job.** Write a Job whose container always exits non-zero, with
   `backoffLimit: 2`. Observe the retries and the final `Failed` state. Where do you
   see the backoff/failure reported?

3. **Scheduled cleanup CronJob.** Create a CronJob that runs every 2 minutes,
   keeps only 2 successful histories, and uses `concurrencyPolicy: Forbid`. Verify
   it fires and that old Jobs are pruned.

4. **StatefulSet scaling.** Take the lab's StatefulSet, scale it to 3, and observe
   the order in which `web-2` is created and which new PVC appears. Then scale back
   to 1 and note whether the PVCs for web-1/web-2 are deleted.

5. **Decision drill.** For each, name the controller you'd use and one sentence why:
   (a) a Redis-backed cache cluster, (b) a nightly database backup, (c) a Prometheus
   node-exporter, (d) a stateless REST API.

## Success criteria
- [ ] Parallel Job completes 6/6 with parallelism 3.
- [ ] Failing Job shows retries and ends `Failed`; you found where backoff is reported.
- [ ] CronJob fires on schedule with pruned history.
- [ ] You observed ordered StatefulSet scaling and that scale-down keeps PVCs.
- [ ] Correct controller chosen for all four scenarios.
