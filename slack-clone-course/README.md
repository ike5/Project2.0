# Slack Clone: From Scratch to Production 💬

A hands-on, local-first course that takes you from an **empty repo** to a
**real-time chat app running highly-available on Kubernetes** — Django + Postgres +
Redis on the backend, Next.js on the frontend, Celery for email and notifications,
webhooks for integrations, all built and shipped on your own machine, for free.

> **Who this is for:** You can write some Python and JavaScript and are comfortable
> in a terminal. You want to build a *real* product — workspaces, channels, live
> messages, presence, notifications — and learn the production patterns
> (async workers, WebSockets at scale, HA databases) that hobby tutorials skip.

> **Web only.** This course builds the **web** app. A native phone app is a
> separate course — the API and WebSocket layer you build here is exactly what a
> mobile client would consume.

---

## Why this course is different

- **Learn by building one real app.** Every module grows the *same* Slack clone —
  `apps/slack-backend` (Django) and `apps/slack-frontend` (Next.js). No throwaway toys.
- **Real-time is first-class.** You'll use **Django Channels** over a **Redis
  channel layer** for true WebSocket messaging, presence, and typing indicators —
  not polling.
- **Production patterns, not demos.** SimpleJWT auth with refresh rotation, Celery
  workers + Beat for email and notification fan-out, signed webhooks, object-storage
  uploads, Postgres full-text search.
- **Genuine high availability.** You'll deploy to a real multi-node Kubernetes
  cluster (kind) and run the data tier with **operators** — CloudNativePG for
  Postgres, a Redis operator for Redis — then *kill the database primary on purpose*
  and watch it heal.

---

## Prerequisites

- A Mac or Linux machine with **~8 GB RAM free** and ~20 GB disk.
- **Python 3.12**, **Node 20+**, and **Docker** (Module 00 installs the rest).
- Comfort with a terminal and basic Git. You do **not** need prior Django, React,
  Celery, or Kubernetes experience — each is introduced from the ground up.
- **Containers:** this course *uses* Docker but does not re-teach it. If you're new
  to images/containers, do the
  [Docker primer](../kubernetes-course/01-containers-docker/) first (≈1.5 h).

---

## The learning path

Work through the modules **in order** — each one adds to the app you're building.

| # | Module | You'll build / learn | Est. time |
|---|--------|----------------------|-----------|
| 00 | [Setup & Orientation](./00-setup/) | Install the toolchain; run Postgres + Redis locally; create your kind cluster | 1 h |
| 01 | [Architecture & Domain Model](./01-architecture-domain/) | Design the system: workspaces, channels, DMs, threads, presence, notifications | 1.5 h |
| 02 | [Django + Postgres Foundations](./02-django-postgres/) | Project layout, 12-factor settings, core models, migrations, admin | 2.5 h |
| 03 | [Auth with SimpleJWT](./03-auth-simplejwt/) | Register/login, access + refresh tokens, rotation, workspace permissions | 2.5 h |
| 04 | [REST API with DRF](./04-rest-api-drf/) | Serializers, viewsets, channels/messages CRUD, cursor pagination, OpenAPI | 2.5 h |
| 05 | [Real-time with Channels](./05-realtime-channels/) | ASGI, Redis channel layer, consumers, JWT over WebSocket, typing indicators | 3 h |
| 06 | [Presence & Caching with Redis](./06-redis-presence-cache/) | Online presence, unread counts, caching hot reads, rate limiting | 2 h |
| 07 | [Celery: Email & Notifications](./07-celery-email-notifications/) | Workers + Beat, transactional email, mention/DM fan-out, digests, retries | 3 h |
| 08 | [Webhooks & Integrations](./08-webhooks-integrations/) | Incoming/outgoing webhooks, slash commands, HMAC signing, retry delivery | 2.5 h |
| 09 | [Next.js Frontend Foundations](./09-nextjs-foundations/) | App Router, API client, SimpleJWT auth flow, protected routes | 3 h |
| 10 | [Real-time UI & CSS](./10-realtime-ui-css/) | WebSocket hook, message list, sidebar, optimistic send, presence/typing UI, theming | 3.5 h |
| 11 | [Uploads & Search](./11-uploads-search/) | Presigned uploads to object storage, reactions, threads, full-text search | 3 h |
| 12 | [Containerizing the Stack](./12-docker-compose-stack/) | Multi-stage Dockerfiles + `docker-compose` for the whole app | 2.5 h |
| 13 | [Kubernetes Deployment](./13-kubernetes-deploy/) | Deployments, Services, Ingress, ConfigMaps/Secrets, migration Jobs — onto kind | 3 h |
| 14 | [Stateful Data Tier (Operators)](./14-stateful-operators/) | HA Postgres with CloudNativePG; HA Redis; PVCs and backups | 3 h |
| 15 | [High Availability & Scaling](./15-high-availability/) | Replicas, HPA, PDBs, anti-affinity, scaling WebSockets, zero-downtime rollouts | 3 h |
| 16 | [Production Hardening](./16-production-hardening/) | Logging, Prometheus + Grafana, Sentry, NetworkPolicies, TLS, CI/CD | 3 h |
| 17 | [Capstone](./17-capstone/) | Ship the full clone on the HA cluster; load test; failure drills | 4+ h |

**Total: a realistic ~45 hours of focused, hands-on work.** Take it at your own pace.

---

## How each module is structured

```
NN-topic/
├── README.md      ← Concepts in plain language. Read this first.
├── lab.md         ← Step-by-step guided build with expected output. Do this second.
├── code/          ← Reference files the lab adds to the app.
├── challenge.md   ← An unguided task to prove you understood it. Do this third.
└── solutions/     ← Reference answers — peek only after you've tried.
```

**The rhythm for every module:** read `README.md` → follow `lab.md` hands-on →
attempt `challenge.md` solo → check `solutions/`.

---

## The app you're building

Two apps under [`apps/`](./apps/) grow with you across the whole course:

- **[apps/slack-backend/](./apps/slack-backend/)** — the Django + DRF + Channels +
  Celery backend (the API and real-time engine).
- **[apps/slack-frontend/](./apps/slack-frontend/)** — the Next.js web client.

By the capstone they form a working Slack clone: sign in, join a workspace, chat
live across channels and DMs, get @-mention emails, drop in files, and search history.

---

## Reference material (keep these open)

- **[cheatsheets/django-drf.md](./cheatsheets/django-drf.md)** — ORM, migrations, DRF.
- **[cheatsheets/channels-websockets.md](./cheatsheets/channels-websockets.md)** — consumers & channel layers.
- **[cheatsheets/celery.md](./cheatsheets/celery.md)** — tasks, Beat, retries.
- **[cheatsheets/nextjs-react.md](./cheatsheets/nextjs-react.md)** — App Router & hooks.
- **[cheatsheets/kubectl-helm.md](./cheatsheets/kubectl-helm.md)** — deploy commands.
- **[GLOSSARY.md](./GLOSSARY.md)** — every term defined in plain English.
- **[VERIFY.md](./VERIFY.md)** — end-to-end smoke test to confirm your stack works.

---

## Quick start

```bash
# 1. Install the toolchain (Module 00 explains each tool)
cd slack-clone-course/00-setup
cat README.md

# 2. Bring up Postgres + Redis for local dev
docker compose -f compose.dev.yml up -d

# 3. Start learning
cd ../01-architecture-domain && cat README.md
```

---

Ready? **→ [Start with Module 00: Setup & Orientation](./00-setup/)**
