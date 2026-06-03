# Challenge 09 — Become the Debugger

Solutions in [`solutions/`](./solutions/). Try first.

## Tasks

1. **Cold diagnosis.** Have a friend (or your past self) apply one of the broken
   manifests without telling you which. Using **only** `kubectl get/describe/logs`,
   identify the failure class and state the exact line of evidence you used.

2. **Fix a CrashLoop for real.** Create a Deployment of `web-api:1.0` with a
   *liveness* probe pointing at `/wrong` and a 1s period. Watch it CrashLoop, prove
   from `describe` that the **probe** (not the app) is the culprit, and fix it.

3. **Service-has-no-endpoints.** Deploy `web-api` with a Service whose `targetPort`
   is wrong (e.g. 80 instead of 8080). The Service has endpoints but connections
   hang. Diagnose and fix, explaining how this differs from a *selector* mismatch.

4. **Query metrics.** With kube-prometheus-stack running, use either Grafana's
   Explore or Prometheus to find the **top 3 Pods by CPU** right now.

5. **Stretch:** Use `kubectl debug` to troubleshoot a Pod running a distroless-style
   image (`gcr.io/distroless/static` won't even sleep — use any shell-less image, or
   simulate by not relying on its shell) and inspect its network from the debug container.

## Success criteria
- [ ] Correctly classified a blind-applied failure with cited evidence.
- [ ] Distinguished a failing-probe CrashLoop from an app crash and fixed it.
- [ ] Fixed a `targetPort` bug and explained selector-mismatch vs port-mismatch.
- [ ] Retrieved top CPU Pods from Prometheus/Grafana.
