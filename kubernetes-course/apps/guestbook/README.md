# Sample App: `guestbook` (capstone)

A small **multi-tier** app: a stateless Flask frontend/API backed by a **Redis**
datastore. Used in the [capstone project](../../13-capstone/).

```
browser → guestbook (stateless, scalable) → redis (stateful, persistent)
```

## Endpoints
| Method | Path | Purpose |
|--------|------|---------|
| GET | `/` | HTML page: message list + submit form |
| GET | `/healthz` | liveness (process up) |
| GET | `/readyz` | readiness (can reach Redis) |
| GET | `/api/messages` | JSON list of messages |
| POST | `/api/messages` | add a message (`{"text": "..."}` or form field) |

## Config (env vars)
| Var | Default | Notes |
|-----|---------|-------|
| `REDIS_HOST` | `redis` | the Redis Service name |
| `REDIS_PORT` | `6379` | |
| `REDIS_PASSWORD` | _(none)_ | inject via a Secret |
| `PAGE_TITLE` | `Guestbook` | inject via a ConfigMap |

## Build & load into kind
```bash
cd apps/guestbook
docker build -t guestbook:1.0 .
kind load docker-image guestbook:1.0 --name k8s-course
```

## Run locally with Docker (needs a Redis)
```bash
docker network create gb 2>/dev/null || true
docker run -d --name redis --network gb redis:7-alpine
docker run --rm -p 8080:8080 --network gb -e REDIS_HOST=redis guestbook:1.0
# open http://localhost:8080
```
