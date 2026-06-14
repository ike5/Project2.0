# Challenge 12 — Ship-ready Images

No step-by-step this time. Use what you learned. Reference solutions are in
[`solutions/`](./solutions/) — try first!

## Tasks

1. **Shrink and report.** Run `docker images` and note the backend image size. Add a
   `.dockerignore` (exclude `.venv`, `.git`, `__pycache__`, tests) and rebuild —
   confirm the build context and image shrink.

2. **Healthchecks for the app.** Add a `healthcheck` to the `web` service hitting
   `/api/health/`, and make `frontend` depend on `web` being *healthy* (not just
   started).

3. **Separate the migration step.** Remove `RUN_MIGRATIONS=1` from `web` and instead
   add a one-shot `migrate` service (using `command: ["migrate"]`) that runs to
   completion before `web` starts. Explain why this is closer to the Kubernetes model.

4. **Pin and scan.** Pin the base images by digest (`python:3.12-slim@sha256:…`) and
   run a vulnerability scan (`docker scout` or `trivy`) on the backend image. Note one
   finding and how you'd address it.

5. **Stretch:** The frontend bakes `NEXT_PUBLIC_API_URL` at build time. Explain why a
   single image can't then be promoted unchanged from staging to production the way
   the backend image can — and one way to work around it.

## Success criteria
- [ ] A `.dockerignore` measurably shrinks the build context/image.
- [ ] `web` has a healthcheck and `frontend` waits for it.
- [ ] Migrations run as a separate one-shot service before `web`.
- [ ] Base images are pinned and you ran a scan.
- [ ] You can explain the build-time-env limitation of the frontend image.
