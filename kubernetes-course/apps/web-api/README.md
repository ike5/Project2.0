# Sample App: `web-api`

A tiny Flask service used throughout the course. It's intentionally minimal so the
focus stays on **Kubernetes**, not application code.

## Endpoints

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/` | Greeting + `served_by` (the pod name) — great for load-balancing demos |
| GET | `/healthz` | Liveness probe target (always 200) |
| GET | `/readyz` | Readiness probe target (200, or 503 after toggling) |
| POST | `/toggle-ready` | Flip readiness on/off at runtime |
| GET | `/config` | Echoes config + which env keys/secrets were injected |
| GET | `/work?ms=250` | Burns CPU for ~`ms` ms — used for HPA autoscaling demos |

## Configuration (via environment variables)

| Var | Default | Notes |
|-----|---------|-------|
| `GREETING` | `Hello from web-api` | injected via ConfigMap in later modules |
| `COLOR` | `blue` | |
| `APP_VERSION` | `1.0.0` | bump to demo rolling updates |
| `API_TOKEN` | `` | injected via Secret; only ever echoed masked |
| `PORT` | `8080` | listen port |

## Build & load into kind

```bash
# from this directory
docker build -t web-api:1.0 .

# kind clusters can't see your local Docker images until you load them:
kind load docker-image web-api:1.0 --name k8s-course
```

> The image tag `web-api:1.0` is what the course manifests reference. If you build
> a new version (e.g. `web-api:2.0`), remember to `kind load` it too.

## Run locally without Kubernetes (sanity check)

```bash
docker run -p 8080:8080 web-api:1.0
curl localhost:8080/         # {"message":"Hello from web-api", ...}
curl localhost:8080/config
```
