# Challenge 15 — Prove and Push HA

No step-by-step this time. Use what you learned. Reference solutions are in
[`solutions/`](./solutions/) — try first!

## Tasks

1. **Scale on connections, not CPU.** Describe (and, if you have Prometheus from
   Module 16, implement) scaling `web` on an *active WebSocket connections* custom
   metric via the Prometheus Adapter. Why is this better than CPU for chat?

2. **Surge test the rollout.** Trigger a rolling update while a script posts a message
   every 200ms. Confirm zero failed writes across the rollout, and explain how
   `maxUnavailable: 0` + readiness probes achieve that.

3. **Tune graceful shutdown.** Make a Celery task sleep 20s, enqueue several, then
   `kubectl delete` a worker pod mid-task. Verify the in-flight task finishes (warm
   shutdown) within the grace period and the rest are re-queued, not lost.

4. **PDB math.** With `web` at 3 replicas and `minAvailable: 1`, how many pods can a
   drain evict at once? Change to `maxUnavailable: 1` and explain the difference in
   behavior.

5. **Stretch:** A single user's two browser tabs connect to two different web pods.
   Trace exactly how a message they send reaches both tabs, naming every hop
   (consumer → channel layer → group → sockets). Why does this *require* the Redis
   channel layer at 3 replicas?

## Success criteria
- [ ] You can justify connection-based scaling for WebSockets.
- [ ] A rollout under continuous writes drops zero requests.
- [ ] In-flight Celery tasks survive a pod delete via warm shutdown.
- [ ] You can compute PDB eviction allowances.
- [ ] You can trace cross-pod delivery through the channel layer.
