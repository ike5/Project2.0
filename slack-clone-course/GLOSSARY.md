# Glossary

Plain-English definitions of every term used in this course. Skim it now; come back
whenever a word trips you up.

## Backend: Django & DRF

- **Django** — A "batteries-included" Python web framework: ORM, migrations, admin,
  auth, and routing out of the box.
- **DRF (Django REST Framework)** — The library that turns Django models into JSON
  REST APIs (serializers, viewsets, routers, permissions).
- **ORM (Object-Relational Mapper)** — Lets you query the database with Python
  objects (`Message.objects.filter(...)`) instead of raw SQL.
- **Migration** — A versioned file describing a database schema change. `makemigrations`
  writes them; `migrate` applies them.
- **Serializer** — DRF class that converts between model instances and JSON, and
  validates incoming data.
- **ViewSet** — A class bundling the CRUD actions (list/create/retrieve/update/destroy)
  for a resource; wired to URLs by a **router**.
- **Cursor pagination** — Paginating by an opaque pointer (not page numbers) so new
  rows don't shift results — essential for an ever-growing message feed.
- **12-factor config** — Reading settings (DB URL, secrets) from environment
  variables so the same image runs in dev, staging, and prod.

## Auth

- **SimpleJWT** — DRF add-on that issues JSON Web Tokens for auth.
- **Access token** — A short-lived signed token sent on every API request to prove
  who you are.
- **Refresh token** — A longer-lived token used only to mint new access tokens
  without re-logging-in.
- **Rotation** — Issuing a brand-new refresh token each time one is used, and
  blacklisting the old one, so a stolen token has a short useful life.
- **Permission class** — A DRF hook that decides whether a request may proceed
  (e.g. "must be a member of this workspace").
- **Throttling** — Rate-limiting requests per user/IP to prevent abuse.

## Real-time: Channels & WebSockets

- **WebSocket** — A persistent, two-way connection between browser and server — how
  messages arrive instantly instead of by polling.
- **ASGI** — The async server interface Django uses for WebSockets (vs WSGI, which is
  request/response only).
- **Django Channels** — The library that adds WebSocket/ASGI support to Django via
  **consumers**.
- **Consumer** — The WebSocket equivalent of a view: handles connect, receive, and
  disconnect events.
- **Channel layer** — A shared message bus (backed by **Redis**) that lets one
  server push an event to WebSocket connections held by *other* servers.
- **Group** — A named set of connections (e.g. everyone watching `#general`) you can
  broadcast to at once.

## Redis

- **Redis** — An in-memory data store used here three ways: the Channels **channel
  layer**, the Celery **broker**, and a **cache** (presence, unread counts, rate limits).
- **Presence** — Who's online/away right now, tracked with short-lived Redis keys
  that expire if a client stops heartbeating.
- **TTL (time to live)** — An expiry on a Redis key; presence and rate-limit keys use it.

## Async: Celery

- **Celery** — A distributed task queue: run slow work (sending email, notification
  fan-out) outside the request/response cycle.
- **Broker** — The queue Celery puts tasks on (Redis, here).
- **Worker** — A process that pulls tasks off the broker and runs them.
- **Celery Beat** — A scheduler that enqueues periodic tasks (e.g. nightly digest emails).
- **Idempotent** — A task safe to run more than once with the same effect — important
  because workers retry.

## Webhooks

- **Webhook** — An HTTP callback: one system POSTs an event to another's URL.
- **Incoming webhook** — A URL *we* expose so external tools can post messages into a channel.
- **Outgoing webhook / event subscription** — *We* POST events (e.g. "new message")
  to a URL the integration registered.
- **Slash command** — A `/command` typed in chat that triggers a server action or
  external request.
- **HMAC signature** — A keyed hash sent in a header so the receiver can verify a
  payload's authenticity and integrity.

## Frontend: Next.js & React

- **React** — The UI library; you build the app from composable **components**.
- **Next.js** — A React framework adding routing, build tooling, and server rendering.
- **App Router** — Next.js's file-system router (`app/` directory) with layouts and
  route segments.
- **Hook** — A reusable React function (`useState`, `useEffect`, our `useChannelSocket`)
  that adds state/behavior to a component.
- **Optimistic update** — Showing a sent message instantly in the UI before the
  server confirms it, then reconciling.
- **CSS module** — A `.module.css` file whose class names are locally scoped to one component.

## Storage & search

- **Object storage** — A service for blobs/files (S3, or **MinIO** locally) — where
  uploaded attachments live.
- **Presigned URL** — A temporary, signed URL that lets the browser upload directly
  to object storage without routing bytes through your API.
- **Full-text search** — Postgres's built-in text search (`tsvector`/`tsquery`) used
  to search message history.

## Docker & Kubernetes

- **Image / container** — See the [Docker primer](../kubernetes-course/01-containers-docker/).
- **Multi-stage build** — A Dockerfile that builds in one stage and copies only the
  artifacts into a small final image.
- **Deployment** — A Kubernetes object that keeps N identical Pods running and rolls
  out new versions.
- **Service** — A stable in-cluster address that load-balances across a Deployment's Pods.
- **Ingress** — Routes outside HTTP traffic to Services by host/path.
- **ConfigMap / Secret** — Kubernetes objects holding config / sensitive values,
  injected as env vars or files.
- **Job** — A run-to-completion Pod; we use one to run database migrations.
- **HPA (Horizontal Pod Autoscaler)** — Scales Pod count up/down based on CPU or
  custom metrics.
- **PDB (PodDisruptionBudget)** — Guarantees a minimum number of Pods stay up during
  voluntary disruptions (node drains, rollouts).
- **Anti-affinity** — A scheduling rule spreading replicas across nodes so one node
  failing doesn't take them all down.
- **Operator** — A controller that manages a complex app (like a database) using
  custom resources — it knows how to fail over, back up, and heal.
- **CloudNativePG** — A Postgres operator that runs an HA Postgres cluster with
  automatic failover.
- **StatefulSet** — The workload type for stateful apps needing stable identity and
  storage (what operators build on).
- **cert-manager** — Automates issuing/renewing TLS certificates in the cluster.
- **NetworkPolicy** — A firewall rule controlling which Pods may talk to which.
