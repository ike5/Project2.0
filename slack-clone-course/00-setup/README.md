# Module 00 — Setup & Orientation

**Goal:** install the toolchain, run Postgres + Redis locally in containers, and
create the multi-node Kubernetes cluster you'll deploy to later.

⏱️ ~1 hour · 🎯 By the end you'll have every tool installed, the data services
running, and a healthy local cluster.

> You won't write app code yet. This module gets the moving parts in place so every
> later lab "just works."

---

## 1. What we're installing and why

| Tool | What it is | Why we need it |
|------|-----------|----------------|
| **Python 3.12** | Backend language | Django, DRF, Celery, Channels all run on it |
| **Node 20+** | Frontend runtime | Builds and runs the Next.js client |
| **Docker** | Container runtime | Runs Postgres/Redis locally and, later, the whole stack |
| **kind** | "Kubernetes IN Docker" | A real multi-node cluster on your laptop, free |
| **kubectl** | Kubernetes CLI | How you talk to the cluster |
| **helm** | K8s package manager | Installs operators (CloudNativePG, Redis) and add-ons |

> **Already did the [Docker primer](../../kubernetes-course/01-containers-docker/)?**
> Then containers, images, and `docker run` are familiar — we build on that here
> and won't re-explain the basics.

---

## 2. Install (Mac via Homebrew; Linux notes inline)

```bash
# Mac
brew install python@3.12 node kind kubectl helm
brew install --cask docker        # then launch Docker.app once

# Linux (Debian/Ubuntu): use your package manager + the official Docker repo,
# and install kind/kubectl/helm from their release pages. See each tool's docs.
```

Verify everything (see [VERIFY.md](../VERIFY.md) §0):
```bash
python3.12 --version && node --version && docker version && kind version
```

---

## 3. Run Postgres + Redis locally

We develop against the same engines we ship: **Postgres 16** and **Redis 7**, in
containers. The provided [`compose.dev.yml`](./compose.dev.yml) also runs
**MailHog** (a fake SMTP server with a web inbox) and **MinIO** (S3-compatible
storage) — you'll need those from Module 07 and 11.

```bash
cd 00-setup
docker compose -f compose.dev.yml up -d
docker compose -f compose.dev.yml ps
```

✅ Expected: four healthy services.
```
NAME       SERVICE    STATUS
postgres   postgres   running (healthy)
redis      redis      running (healthy)
mailhog    mailhog    running
minio      minio      running (healthy)
```

Open the dashboards to prove they work:
- MailHog inbox → <http://localhost:8025>
- MinIO console → <http://localhost:9001> (user/pass `minioadmin`/`minioadmin`)

Stop them at the end of a session (data persists in named volumes):
```bash
docker compose -f compose.dev.yml stop
```

---

## 4. Create your Kubernetes cluster

You won't deploy to Kubernetes until Module 13, but creating the cluster now
confirms your machine can run it. We use the same **1 control-plane + 2 worker**
kind config style as the Kubernetes course, so failover and anti-affinity labs
later actually *do something*.

```bash
./scripts/create-cluster.sh        # ~1 minute
./scripts/verify-setup.sh
```

✅ Expected: **3 nodes `Ready`**.
```
slack-control-plane   Ready   control-plane
slack-worker          Ready   <none>
slack-worker2         Ready   <none>
```

Tear it down when you don't need it (frees RAM; recreating takes ~1 min):
```bash
./scripts/delete-cluster.sh
```

---

## 5. The big picture

Here's everything you'll build and how it connects. Keep this map in mind — each
module fills in one box.

```
        Browser ──HTTP──► Next.js (frontend)
           │  ▲                  │
   WebSocket  │ HTTP/JSON        │ HTTP/JSON
           ▼  │                  ▼
   ┌────────────────────────────────────────┐
   │            Django backend              │
   │  DRF (REST)   Channels (WebSockets)    │
   └───┬───────────────┬───────────┬────────┘
       │               │           │
     Postgres        Redis       Celery worker + Beat
   (data of record) (channel     (email, notifications,
                     layer,       webhook delivery)
                     cache,         │
                     broker)        ▼
                                  MailHog / SMTP, webhooks
```

---

## 6. Do the lab

Confirm the whole toolchain end-to-end: bring up the data services, connect to
Postgres and Redis from the CLI, and spin the cluster up and down.

👉 **[lab.md](./lab.md)**

Then test yourself: 👉 **[challenge.md](./challenge.md)**

---

## Key terms (see [GLOSSARY](../GLOSSARY.md))

Docker · kind · kubectl · helm · Redis · Postgres · MailHog · MinIO

**Next →** [Module 01: Architecture & Domain Model](../01-architecture-domain/)
