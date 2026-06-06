# Challenge 16 — Production Readiness Review

No step-by-step this time. Use what you learned. Reference solutions are in
[`solutions/`](./solutions/) — try first!

## Tasks

1. **Alert on the golden signals.** Add a Prometheus alert rule that fires when the
   web 5xx error rate exceeds 5% for 5 minutes, and route it somewhere (Alertmanager →
   a webhook). Describe what you'd page on vs. only ticket.

2. **Lock down the pods.** Add a `securityContext` to web: `runAsNonRoot: true`,
   `readOnlyRootFilesystem: true`, `allowPrivilegeEscalation: false`, drop all
   capabilities. Fix anything that breaks (e.g. a writable tmp dir).

3. **Real secrets.** Replace the committed Secret with **Sealed Secrets** (or External
   Secrets). Show that only the encrypted form is in git and the controller decrypts it
   in-cluster.

4. **Namespace quota.** Add a `ResourceQuota` + `LimitRange` to the `slack` namespace.
   Demonstrate that a pod with no resource requests gets the default, and that
   exceeding the quota is rejected.

5. **Stretch:** Write the CI/CD pipeline (as YAML or prose) that tests, builds, scans,
   pushes by digest, runs the migration Job, and does a gated rollout with automatic
   rollback on a failed health check. Identify the one step that most reduces the chance
   of a bad deploy reaching users.

## Success criteria
- [ ] An error-rate alert fires and routes correctly.
- [ ] Web runs with a hardened securityContext.
- [ ] Secrets live encrypted in git and decrypt in-cluster.
- [ ] A namespace quota + limit range govern resources.
- [ ] You can describe a safe CI/CD pipeline and its key safeguard.
