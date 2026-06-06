# Challenge 15 — Reference Solution

### 1. Scale on connections
> Expose a gauge of active WebSocket connections (increment on `connect`, decrement on
> `disconnect`) at `/metrics`, scrape it with Prometheus, and surface it through the
> **Prometheus Adapter** as a custom metric. The HPA then targets, say, 500
> connections/pod. This beats CPU because an idle-but-connected user consumes a
> connection and memory while using almost no CPU — so CPU underestimates real load and
> the app would be starved of pods exactly when many users are connected.
```yaml
metrics:
  - type: Pods
    pods:
      metric: {name: websocket_connections}
      target: {type: AverageValue, averageValue: "500"}
```

### 2. Surge test
```bash
( while true; do curl -s -o /dev/null -X POST .../api/messages/ -d '...'; sleep 0.2; done ) &
kubectl set image -n slack deploy/web web=slack-backend:v3
kubectl rollout status -n slack deploy/web
```
> `maxUnavailable: 0` means the old pods keep serving until a **new** pod passes its
> readiness probe and joins the Service; only then is an old pod removed. Capacity never
> dips, so writes never fail.

### 3. Graceful shutdown
```python
@shared_task
def slow(): import time; time.sleep(20)
```
```bash
kubectl delete pod -n slack <worker-pod>
```
> Celery's warm shutdown (SIGTERM) stops fetching new tasks and finishes the current
> one; `terminationGracePeriodSeconds: 60` gives it time. Tasks still queued are left on
> the broker for other workers — nothing is lost. (Only a SIGKILL after the grace period
> would interrupt the in-flight task, which is why the period must exceed your longest task.)

### 4. PDB math
> With 3 replicas and `minAvailable: 1`, a drain may evict **up to 2** at once (it must
> keep ≥1). With `maxUnavailable: 1`, it may evict **only 1** at a time (it must keep
> ≥2). `maxUnavailable` is stricter for availability here — fewer pods go down
> simultaneously, at the cost of slower drains.

### 5. Cross-pod trace
> 1. Tab A's socket lives on **web-pod-1**; tab B's on **web-pod-2**; both joined group
>    `channel_<id>` via `group_add`. 2. Tab A sends `message.new`; **web-pod-1**'s
>    consumer writes the row and calls `group_send("channel_<id>", …)`. 3. `group_send`
>    publishes to **Redis** (the channel layer). 4. **Every** web pod subscribed to that
>    group — pod-1 *and* pod-2 — receives it. 5. Each pod's `broadcast_event` handler
>    pushes it down the sockets it holds, so tab A (pod-1) and tab B (pod-2) both render
>    it. Without the **Redis** channel layer, pod-1 could only reach sockets it holds
>    locally, so tab B on pod-2 would never see the message — in-memory channels can't
>    cross processes.
