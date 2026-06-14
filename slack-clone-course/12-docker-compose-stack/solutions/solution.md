# Challenge 12 — Reference Solution

### 1. `.dockerignore`
```
# apps/slack-backend/.dockerignore
.venv/
.git/
__pycache__/
*.pyc
*.sqlite3
.env
staticfiles/
.pytest_cache/
```
Rebuild and compare: `docker images slack-backend`. The build context (the "Sending
build context" size) and image both drop because the venv and git history are no
longer copied.

### 2. App healthcheck + ordered start
```yaml
web:
  healthcheck:
    test: ["CMD", "python", "-c", "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8000/api/health/').status==200 else 1)"]
    interval: 10s
    timeout: 3s
    retries: 5
frontend:
  depends_on:
    web: {condition: service_healthy}
```

### 3. One-shot migration service
```yaml
migrate:
  build: ./apps/slack-backend
  command: ["migrate"]
  environment: *backend_env
  depends_on:
    postgres: {condition: service_healthy}
web:
  depends_on:
    migrate: {condition: service_completed_successfully}
  environment:
    <<: *backend_env
    RUN_MIGRATIONS: "0"
```
> This mirrors Kubernetes, where migrations run as a **Job** that must complete before
> the Deployment rolls out — so schema changes happen exactly once, not once per web
> replica (which would race).

### 4. Pin + scan
```dockerfile
FROM python:3.12-slim@sha256:<digest> AS builder
```
```bash
docker scout cves slack-backend:latest     # or: trivy image slack-backend:latest
```
> Pinning by digest makes builds reproducible (a tag can move). A scan might flag a
> CVE in a system lib — address it by bumping the base image to a patched digest and
> rebuilding.

### 5. Build-time env limitation
> `NEXT_PUBLIC_*` values are **inlined into the JS bundle at build time**, so the API
> URL is hard-coded into the frontend image. The same image therefore can't be
> promoted unchanged across environments the way the backend image (which reads env at
> **runtime**) can. Workarounds: build a per-environment image, or serve the config at
> runtime — e.g. expose a small `/config.json` endpoint the app fetches on load, or
> use a runtime-injected `window.__ENV__` — so one image works everywhere.
