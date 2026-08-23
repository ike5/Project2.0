# apps/ — the code you build across the course

Two applications grow here as you work the modules. **They are built
incrementally in the labs** — this directory starts nearly empty on purpose, the
same way a real project starts as an empty repo.

```
apps/
├── pulse/       ← the Django backend        (Module 02 onward)
└── pulse-web/   ← the Next.js client        (Module 17)
```

---

## `pulse/` — the Django backend

One Django **project** called `pulse` containing one **app** called `chat`. (In
Django's vocabulary a *project* is the deployable unit that owns settings and
routing; an *app* is a reusable bundle of models, views and consumers inside it.
Module 02 makes this distinction properly.)

By the capstone, `pulse` is a horizontally-scaled, HA, observable chat backbone.

### The layout it grows into

```
apps/pulse/
├── manage.py
├── pyproject.toml            # uv-managed; Django 5.1, Channels 4.1, DRF, channels_redis
├── Dockerfile                # multi-stage, non-root, uvloop (Module 18)
├── pulse/                    # the PROJECT package — settings, ASGI entrypoint
│   ├── __init__.py
│   ├── settings/
│   │   ├── base.py           # Module 02
│   │   ├── dev.py            # InMemoryChannelLayer, one worker      (Modules 02–06)
│   │   ├── redis.py          # RedisChannelLayer                     (Module 07+)
│   │   ├── ha.py             # Sentinel, PgBouncer, prepare_threshold(Module 18)
│   │   └── capstone.py       # everything at once                    (Module 22)
│   ├── asgi.py               # ProtocolTypeRouter + lifespan hook    (Modules 02, 18)
│   ├── wsgi.py               # exists only so Module 02 can contrast it
│   ├── celery.py             # the outbox relay + beat tasks         (Module 13)
│   └── urls.py
└── chat/                     # the APP — everything domain-shaped
    ├── models.py             # Room, Membership, Message, Outbox     (Modules 02, 12, 13)
    ├── migrations/           # including RunSQL partition DDL        (Module 13)
    ├── consumers.py          # AsyncJsonWebsocketConsumer            (Module 04+)
    ├── routing.py            # websocket_urlpatterns
    ├── middleware.py         # ticket auth for the handshake         (Module 21)
    ├── envelope.py           # the JSON protocol + schema versioning (Module 05)
    ├── layers.py             # the custom Streams-backed channel layer (Module 09)
    ├── presence.py           # TTL heartbeats, viewport subs         (Module 11)
    ├── ratelimit.py          # token buckets in Lua                  (Module 11)
    ├── routers.py            # Django DB routers: replica + shards   (Modules 13, 14)
    ├── registry.py           # per-process connection registry       (Module 18)
    ├── drain.py              # two-phase SIGTERM + lifespan drain    (Module 18)
    ├── metrics.py            # prometheus_client histograms/gauges   (Modules 06, 20)
    ├── health.py             # /healthz (liveness), /readyz (capacity)
    ├── api/                  # DRF: history, tickets, admin actions
    └── tests/
```

### Milestone → module map

| Milestone | Module | State of `pulse/` |
|-----------|--------|-------------------|
| Project skeleton | 02 | `django-admin startproject`, ASGI entrypoint, DRF wired, `runserver` shown to be the wrong tool |
| Working chat | 04 | `AsyncJsonWebsocketConsumer`, groups, presence — on the **InMemoryChannelLayer**, which is then proven not to span worker processes |
| Protocol | 05 | The envelope, client id + server id, per-room `seq`, the ack ladder, schema version |
| Measured | 06 | `prometheus_client` instrumentation, event-loop-lag probe, the k6/Locust harness in `../06-*/code/` |
| Scaled out | 07–11 | `channels_redis` backplane → a custom Streams layer → resume cursors → presence and rate limiting |
| Durable | 12–14 | Snowflake IDs, keyset pagination, partitioning, replicas behind a DB router, the outbox relayed by Celery, then shards |
| Alternatives | 15–16 | `consumers_bench.py` (sync twin), a raw-ASGI `websockets` edge in the module's `code/`, a Kafka profile |
| Client | 17 | (the other app — see below) |
| HA | 18–19 | Connection registry, ASGI drain, capacity-aware readiness; runs under the HA Compose stack and then on `kind` |
| Observable | 20 | Traces across the outbox and the Stream, four SLOs, burn-rate alerts |
| Secured | 21 | `OriginValidator`, ticket middleware, first-frame JWT, cluster-wide revocation, abuse detection |
| Capstone | 22 | Everything, under `pulse.settings.capstone` |

Generate the skeleton with the exact command in
[`02-django-fast-track/lab.md`](../02-django-fast-track/lab.md) Part A.

> ⚠️ **The one setting that changes the most across the course** is
> `CHANNEL_LAYERS`. It starts as `InMemoryChannelLayer` *specifically so Module
> 04 can prove it doesn't span worker processes*, becomes `channels_redis` in
> Module 07, gains a custom Streams-backed layer in Module 09, and points at
> Sentinel in Module 18. That progression is the spine of the whole course — the
> settings file is where you can watch it happen.

---

## `pulse-web/` — the Next.js client

Built in Module 17, with TypeScript and the App Router. It is the client half of
every guarantee the backend makes:

- a **virtualized** message list (a 300k-message room must not be 300k DOM nodes),
- **optimistic send** with `clientId` reconciliation against the server id,
- an **offline outbox** that replays on reconnect — and which Module 21's
  challenge shows looks exactly like a burst to a token-bucket rate limiter,
- **gap detection** on the per-room `seq` from Module 05, driving resume,
- **full-jitter reconnect**, which Module 18 measures as the difference between a
  214/s and a 3,341/s reconnect peak,
- a **`SharedWorker`** holding one socket across all of a user's tabs.

Scaffold it with the command in
[`17-nextjs-realtime-client/lab.md`](../17-nextjs-realtime-client/lab.md) Part A.

---

## Why the code isn't pre-written here

This repo's pedagogy (see [`../../PEDAGOGY.md`](../../PEDAGOGY.md)) is *learn by
doing* — 80% hands on keys. Every file that belongs in these apps is written,
with full context and an explanation of the alternative it beat, inside a lab.
Pre-populating them would turn "build it" into "read it," which is the opposite
of the point.

Reference implementations of the genuinely tricky pieces — the Streams-backed
channel layer, the Snowflake generator, the Lua token bucket, the ASGI drain, the
ticket middleware — live in each module's `solutions/`. When you're stuck, that's
where to look. **After** you've tried.

---

## Running what you've built

Everything data-tier lives in [`../infra/`](../infra/). The usual loop:

```bash
docker compose -p pulse-dev -f ../infra/compose.dev.yml up -d      # Postgres + Redis
cd pulse && source ../../.venv/bin/activate
python manage.py migrate
uvicorn pulse.asgi:application --loop uvloop --workers 8 --port 8000
```

> **One worker process per core** (Module 01). Eight workers means eight
> interpreters, eight GILs, eight event loops — and **eight channel layers**
> unless Redis is configured. If two browser tabs can't see each other's
> messages, that is not a bug; that is Module 04's wall, and
> [`../cheatsheets/troubleshooting.md`](../cheatsheets/troubleshooting.md) tree 2
> is where to confirm it.
