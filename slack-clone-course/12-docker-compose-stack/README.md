# Module 12 — Containerizing the Stack

**Goal:** package the backend and frontend as lean Docker images and run the entire
app — data services, web, worker, beat, frontend — with one `docker compose up`.

⏱️ ~2.5 hours · 🎯 Prereq: Modules 02–11 (a working app). Docker installed.

> You already know Docker from the separate Docker course (and the
> [primer](../../kubernetes-course/01-containers-docker/)). This module is **not** a
> Docker tutorial — it's about containerizing *this specific stack* correctly:
> multi-stage builds, one image with several roles, and a compose file that wires
> seven services together.

---

## 1. One image, several roles

The backend image runs three different processes — **web**, **worker**, **beat** —
from the *same* code. Rather than build three images, we build **one** and let
`entrypoint.sh` switch on its first argument:

```
ENTRYPOINT ["./entrypoint.sh"]   CMD ["web"]      # default
# compose/k8s override the command:
command: ["worker"]   →  celery -A config worker
command: ["beat"]     →  celery -A config beat
```

This keeps builds fast and guarantees web/worker/beat always run identical code and
dependencies.

## 2. Multi-stage builds = small, safe images

`apps/slack-backend/Dockerfile` builds in two stages:
- **builder** installs the compiler and produces wheels,
- **runtime** copies only the wheels and app code — **no build toolchain** in the
  shipped image.

Result: a smaller image with less attack surface. We also run as a **non-root user**
and copy `requirements.txt` before the code so the (slow) dependency layer stays
cached when only code changes — the layer-ordering lesson from the Docker primer,
applied here.

The frontend uses Next's **standalone** output (`next.config.js`) so its runtime
image carries just `server.js` + the needed assets, not the whole `node_modules`.

## 3. ASGI in production

Locally you used `runserver`. In the container the web role runs **uvicorn** against
`config.asgi:application`, so HTTP *and* WebSockets work. For more processes per
container you'd front it with gunicorn (`-k uvicorn.workers.UvicornWorker -w 3`) —
noted in `entrypoint.sh`.

## 4. Config is all environment

Because settings are 12-factor (Module 02), containerizing requires **zero code
changes** — compose just sets `DATABASE_URL=postgres://…@postgres:5432/…`,
`REDIS_URL=redis://redis:6379/0`, etc., using the **service names** as hostnames on
the compose network. The same env vars become ConfigMaps/Secrets in Kubernetes
(Module 13).

## 5. The compose topology

```
frontend ─► web (ASGI) ─┬─► postgres
                        ├─► redis ◄─── worker, beat
                        ├─► mailhog
                        └─► minio
```

`web`, `worker`, and `beat` share one env block (a YAML anchor). `depends_on` with
health checks ensures Postgres/Redis are ready first. The web container migrates on
boot here (`RUN_MIGRATIONS=1`) for convenience — in Kubernetes that becomes a
dedicated migration **Job** (Module 13).

## 6. NEXT_PUBLIC is baked at build time

Next inlines `NEXT_PUBLIC_*` vars at **build** time, so the frontend image takes them
as **build args**, not runtime env. That's why compose passes them under `build.args`.

---

## 7. Do the lab

Build both images, bring the whole stack up with one command, and exercise the full
app — auth, live chat, an @mention email in MailHog, an upload to MinIO — entirely in
containers.

👉 **[lab.md](./lab.md)**

Then test yourself: 👉 **[challenge.md](./challenge.md)**

---

## Key terms (see [GLOSSARY](../GLOSSARY.md))

multi-stage build · entrypoint role · ASGI server · standalone output · build arg · compose network

**Next →** [Module 13: Kubernetes Deployment](../13-kubernetes-deploy/)
