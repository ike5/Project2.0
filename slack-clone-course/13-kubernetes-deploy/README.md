# Module 13 — Kubernetes Deployment

**Goal:** run the whole app on a real Kubernetes cluster — Deployments for web,
worker, beat, and frontend; Services; an Ingress; config and secrets; and migrations
as a Job.

⏱️ ~3 hours · 🎯 Prereq: Module 12 (images build). The kind cluster from Module 00.

> Compose was one machine. Kubernetes runs the app across a *cluster*, restarts
> crashed pods, rolls out new versions, and (next modules) heals failures and scales.
> New to Kubernetes? The [Kubernetes course](../../kubernetes-course/) goes deep; here
> we apply it to our app.

---

## 1. The object model for our app

```
Ingress (slack.local)
  ├── /api,/ws,/admin → Service: web  → Deployment web   (Django ASGI, 2 replicas)
  └── /               → Service: frontend → Deployment frontend (Next.js, 2 replicas)
Deployment worker (Celery, 2 replicas)      ConfigMap: backend-config
Deployment beat   (Celery Beat, 1 replica)  Secret:    backend-secret
Job: migrate (runs once)                     simple Postgres/Redis (HA in Module 14)
```

- **Deployment** keeps N identical pods running and does rolling updates.
- **Service** is a stable in-cluster address load-balancing across a Deployment's pods.
- **Ingress** maps outside HTTP(S) to Services by path (and keeps WebSockets open).
- **ConfigMap / Secret** carry the same 12-factor env you used in compose.

## 2. One image, three Deployments

The backend image (Module 12) runs as **web**, **worker**, and **beat** — three
Deployments, same image, different `args`. Note two correctness rules baked into the
manifests:

- **beat has exactly 1 replica** with a `Recreate` strategy — two schedulers would
  enqueue every periodic task twice.
- **workers and web scale freely** (2+ replicas now; autoscaled in Module 15).

## 3. Config and secrets

`backend-config` (ConfigMap) holds non-secret env; `backend-secret` (Secret) holds
`SECRET_KEY` and storage keys. Both are injected with `envFrom`, so a pod's
environment is exactly what your settings expect. *Secrets are templates here — real
clusters source them from a sealed-secrets/external-secrets system and never commit them.*

## 4. Health probes drive everything

Each web/frontend pod has a **readiness** and **liveness** probe hitting
`/api/health/` (Module 02). Readiness gates traffic — a pod gets no requests until it
passes; liveness restarts a wedged pod. These probes are what make rolling updates and
self-healing actually safe.

## 5. Migrations as a Job

A Deployment runs forever; migrations must run **once**. The `migrate` Job runs
`entrypoint.sh migrate` to completion. You apply it (and wait for success) **before**
rolling out web pods, so the schema is ready and two web replicas don't race to migrate.

## 6. Local images into kind

kind can't see your local Docker images, so you **build then load** them (the gotcha
from the Docker primer):

```bash
kind load docker-image slack-backend:dev slack-frontend:dev --name slack
```
With `imagePullPolicy: IfNotPresent`, the kubelet uses the loaded image instead of
pulling from a registry.

---

## 7. Do the lab

Build and load the images, install the nginx ingress, apply the manifests, run the
migration Job, and reach the full app at `http://slack.local` — running on Kubernetes.

👉 **[lab.md](./lab.md)**

Then test yourself: 👉 **[challenge.md](./challenge.md)**

---

## Key terms (see [GLOSSARY](../GLOSSARY.md))

Deployment · Service · Ingress · ConfigMap · Secret · Job · probe · imagePullPolicy

**Next →** [Module 14: Stateful Data Tier (Operators)](../14-stateful-operators/)
