# Challenge 03 — Own the Deployment Lifecycle

Solutions in [`solutions/`](./solutions/). Try first.

## Tasks

1. **Author from scratch.** Without copying `web-deploy.yaml`, write a new manifest
   `mychal.yaml` for a Deployment named `api` with **4 replicas** of `web-api:1.0`
   (remember `imagePullPolicy: Never`), labels `app=api` and `tier=backend`, and
   the env var `COLOR=orange`. Apply it and confirm 4 Pods Running.

2. **Controlled rollout.** Configure the Deployment's rolling-update strategy so
   that during an update **at most 1 Pod is unavailable** and **at most 1 extra**
   Pod is created (`maxUnavailable: 1`, `maxSurge: 1`). Then update the image to
   `web-api:2.0` and watch the rollout respect those limits.

3. **Deliberate broken rollout + recovery.** Update the image to a tag that doesn't
   exist (e.g. `web-api:does-not-exist`). Observe what happens to the rollout and
   the Pods. Then recover with a rollback. Explain why the app stayed up the whole time.

4. **Pause/resume (stretch).** Use `kubectl rollout pause` and `resume` to batch
   multiple changes (image + env) into a single rollout instead of two.

## Success criteria
- [ ] `api` Deployment runs 4 Pods with the required labels and env.
- [ ] Your `strategy.rollingUpdate` limits are set and visible in `kubectl describe`.
- [ ] You triggered a failing rollout, saw new Pods stuck (ImagePullBackOff) while
      old Pods kept serving, and rolled back.
- [ ] You can explain how rolling updates protect availability.
