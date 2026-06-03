# Challenge 04 — Config, Probes & Limits

Solutions in [`solutions/`](./solutions/). Try first.

## Tasks

1. **File-mounted config.** Instead of env vars, mount the `web-config` ConfigMap as
   files under `/etc/web` in a Pod. Exec in and `cat /etc/web/COLOR` to prove each
   key became a file.

2. **Right-size a workload.** Deploy `web-api` with a `startupProbe` (so a slow boot
   doesn't trip liveness), plus liveness and readiness probes. Set requests
   `cpu:100m/memory:64Mi` and limits `cpu:300m/memory:128Mi`.

3. **Fix a CrashLoop.** Apply the provided `bad-liveness.yaml` (liveness probe hits a
   path that 404s with too-short delays). Observe the `CrashLoopBackOff`, diagnose
   it from `describe`, and fix the probe so the Pod stays healthy.

4. **Stretch:** Make a change to a Secret and roll it out to a running Deployment
   such that the new value is actually picked up. Explain why a plain `kubectl apply`
   of the Secret alone isn't enough for env-injected secrets.

## Success criteria
- [ ] ConfigMap keys appear as files under the mount path.
- [ ] Your Deployment has startup + liveness + readiness probes and sane resources.
- [ ] You diagnosed the CrashLoop from the probe Events and corrected it.
- [ ] You can explain ConfigMap/Secret env hot-reload behavior.
