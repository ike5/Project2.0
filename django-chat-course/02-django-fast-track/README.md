# Module 02 — Django Fast-Track for Real-Time

**Goal:** Get productive in Django and DRF fast, by building Pulse's skeleton —
and understand the two or three pieces of Django's machinery that actually matter
when you're about to hold 50,000 sockets, rather than the forty that don't.

⏱️ ~4 hours · **Prerequisites:** Modules 00–01. You should be comfortable in
Python and have built a backend service in *some* framework.

> **If you already know Django**, skim to
> [ASGI vs WSGI](#asgi-vs-wsgi-the-fork-in-the-road) and read that section, the
> async-story section, and the middleware section properly. They are the parts
> most working Django developers have never needed, and they are the parts the
> rest of this course stands on. Then do the lab from Part F.

> **This is the Python twin of the JVM course's
> [`02-spring-fast-track`](../../spring-boot-chat-course/02-spring-fast-track/).**
> Same job — build the skeleton, learn only the framework machinery that matters
> for a socket server. Spring's distinctive thing is auto-configuration; Django's
> is that **it is a synchronous framework with an async half bolted carefully on
> top**, and knowing exactly where that seam runs is the difference between a
> chat server and a mystery.

---

## Django in one page, for people who already know a framework

Django is a **batteries-included** framework: ORM, migrations, admin, auth,
sessions, templating, forms, caching, and a management CLI, all shipped together
and all aware of each other. There is no dependency-injection container. Wiring
is done by *module import paths in a settings file*.

| Concept | Django | Spring | Rails | NestJS |
|---------|--------|--------|-------|--------|
| Unit of code organization | **app** (a Python package listed in `INSTALLED_APPS`) | package + `@Component` | engine / concern | module |
| Route handler | view (function or class) | `@RestController` | controller action | `@Controller()` |
| ORM entity | `models.Model` subclass | `@Entity` | `ActiveRecord::Base` | Entity |
| Query API | `Model.objects` → `QuerySet` | `JpaRepository` | `ActiveRelation` | Repository |
| Migrations | `manage.py makemigrations` / `migrate` | Flyway / Liquibase | `rails db:migrate` | TypeORM migrations |
| Config | `settings.py` (a **Python module**) | `application.yml` | `config/*.rb` | `ConfigModule` |
| Middleware | `MIDDLEWARE` list of callables | Filter / Interceptor | Rack middleware | Middleware / Guard |
| HTTP API layer | **DRF** serializers + views | `@RestController` + Jackson | Jbuilder / ActiveModel | Nest + class-transformer |
| Entry point to the server | `wsgi.py` / **`asgi.py`** | embedded Tomcat | Rack | Nest factory |

Two structural facts to internalize immediately, because they explain most of
Django's behaviour:

1. **`settings.py` is executed Python, once, at import time.** It is not parsed
   config; it is a module whose module-level names Django reads. That's why you
   can compute values, read env vars, raise on missing config, and `assert` in
   it — and why a mistake in it is a startup crash, not a runtime surprise. Use
   that.
2. **The "app" is the unit of reuse and the unit of migration.** Every app owns
   its own `models.py` and its own `migrations/` directory with its own linear
   history. `django.contrib.auth` is an app. `rest_framework` is an app. `chat`
   will be an app.

### Project vs app

```
apps/pulse/                  ← the repo directory (a "project" in the loose sense)
├── manage.py                ← the CLI entry point; sets DJANGO_SETTINGS_MODULE
├── pulse/                   ← the PROJECT package: settings, urls, asgi, wsgi
│   ├── settings.py
│   ├── urls.py              ← root URL conf
│   ├── asgi.py              ← the ASGI callable  ← this course lives here
│   └── wsgi.py              ← the WSGI callable  ← this course does not
└── chat/                    ← an APP: models, views, consumers, migrations
    ├── models.py
    ├── serializers.py
    ├── views.py
    ├── consumers.py         ← added in Module 04
    ├── routing.py           ← added in Module 04
    └── migrations/
```

Pulse has exactly one app for the whole course (`chat`). That's a deliberate
simplification: app boundaries are a code-organization decision, and splitting
`chat` into `rooms`/`messages`/`presence` would buy us nothing but import
churn while teaching nothing about scale.

---

## Models and migrations

A model is a class; a table is derived from it.

```python
class Room(models.Model):
    slug       = models.SlugField(max_length=64, unique=True)   # "room.7"
    name       = models.CharField(max_length=120)
    created_at = models.DateTimeField(auto_now_add=True)
```

`makemigrations` diffs your models against the migration history and **writes a
Python file describing the operations**:

```python
operations = [
    migrations.CreateModel(name="Room", fields=[...]),
    migrations.AddIndex(model_name="room", index=...),
]
```

That file — not your models, not the database — is the source of truth for schema
history. Three consequences worth stating once:

- **`sqlmigrate` shows you the SQL before you run it.** Do this every time a
  migration touches a big table. In Module 13 you will read the SQL of a
  partitioning migration very carefully indeed.
- **Migrations are Python, so they can do anything.** `RunSQL` and `RunPython`
  are the escape hatches, and this course uses `RunSQL` heavily from Module 13
  onward for DDL the ORM cannot express (declarative partitioning, partial
  indexes with expressions, `CREATE INDEX CONCURRENTLY`).
- **`--fake` is a loaded gun.** It marks a migration as applied without running
  it. There is exactly one legitimate use (adopting an existing database) and a
  hundred illegitimate ones that end with a schema that doesn't match its
  history.

> ⚠️ **The one irreversible decision in this module: the custom user model.**
> Django lets you swap `AUTH_USER_MODEL` — but only cleanly **before the first
> `migrate`**. Doing it later means surgery on every foreign key in the database.
> Pulse defines `chat.User` in Module 02, on day one, before any migration runs,
> because Module 21 needs to hang JWT/ticket state off it. This is the single
> most common "I wish I'd known" in Django, and you get to know it now.

---

## The ORM, in the 20% that matters here

**QuerySets are lazy.** `Room.objects.filter(...)` builds a query object and
executes nothing. The database is hit when you iterate, slice with a step, call
`len()`, `list()`, `bool()`, or `.count()`. This is why you can compose filters
freely — and why a queryset accidentally evaluated inside a loop is the classic
Django performance bug.

**N+1 is the default failure mode**, and it is not subtle at chat scale:

```python
for m in Message.objects.filter(room=room)[:200]:
    print(m.sender.username)      # 200 extra queries. One per row.
```

```python
for m in Message.objects.filter(room=room).select_related("sender")[:200]:
    print(m.sender.username)      # 1 query, JOINed
```

| Tool | Use when |
|------|----------|
| `select_related("fk")` | Forward FK / OneToOne — becomes a `JOIN` in the same query |
| `prefetch_related("m2m")` | Reverse FK / M2M — a second query plus in-Python stitching |
| `.only(...)` / `.defer(...)` | The row is wide and you need three columns |
| `.values(...)` / `.values_list(...)` | You want dicts/tuples, not model instances — **much** cheaper |
| `.iterator(chunk_size=…)` | Streaming a large result without materializing it |
| `bulk_create(objs, batch_size=…)` | Many inserts; one round trip per batch |
| `.explain(analyze=True)` | Before you believe any index helped |

Model instantiation is not free in Python: constructing 200 `Message` objects
costs real CPU on your one event-loop core. Module 12 measures exactly this and
drops the message hot path to `connection.cursor()` and `values()`. **Use the ORM
where the object graph earns its cost; drop to SQL on the path that runs ten
thousand times a second.** "Always use the ORM" and "never use the ORM" are both
positions held by people who haven't profiled.

**And the fact that dominates everything after Module 03: the Django ORM is
synchronous.** Every query blocks the calling thread. In an async consumer,
"blocks the calling thread" means "blocks the event loop," which means "freezes
every connection on this worker." Module 01 named this the cardinal sin; the rest
of this README is about the seam where it lives.

---

## Settings and 12-factor config

`settings.py` is a Python module, so the 12-factor pattern is just code:

```python
import os
from django.core.exceptions import ImproperlyConfigured

def env(key, default=None, cast=str):
    value = os.environ.get(key, default)
    if value is None:
        raise ImproperlyConfigured(f"missing required environment variable {key}")
    return cast(value)

SECRET_KEY   = env("DJANGO_SECRET_KEY")                    # no default: fail fast
DEBUG        = env("DJANGO_DEBUG", "0", cast=lambda v: v == "1")
ALLOWED_HOSTS = env("DJANGO_ALLOWED_HOSTS", "localhost").split(",")
```

The point isn't the helper; it's the **fail-fast**. A missing `SECRET_KEY` should
kill the process at import, in the first second of a deploy, with the variable
name in the message — not produce a subtly insecure server that runs for a month.
This is the direct analog of the JVM twin's `@ConfigurationProperties`
validation, achieved with four lines instead of an annotation.

The settings you will actually care about in this course:

| Setting | Why it matters here |
|---------|--------------------|
| `ASGI_APPLICATION` | Points Channels/Daphne at your ASGI callable. Wrong value = your consumers silently never run. |
| `CHANNEL_LAYERS` | `InMemoryChannelLayer` (Module 04) → `RedisChannelLayer` (Module 07) |
| `DATABASES[...]["CONN_MAX_AGE"]` | Persistent connections. Interacts violently with PgBouncer (Module 13). |
| `DATABASES[...]["OPTIONS"]["pool"]` | psycopg3 pooling |
| `DATABASE_ROUTERS` | Read replicas (Module 13), sharding (Module 14) |
| `AUTH_USER_MODEL` | Set it now or never (see the warning above) |
| `DEBUG` | `DEBUG=True` **retains every SQL query in memory forever**. It is a memory leak under load, and it is why your dev server dies during a load test. |

---

## DRF, and what Pulse uses it for

Django REST Framework is the HTTP half of Pulse. The WebSocket carries the
real-time traffic; DRF carries everything that is a request/response:

```
POST /api/rooms/            create a room
GET  /api/rooms/            list my rooms
GET  /api/rooms/{slug}/history/?before=<id>&limit=50    scrollback (keyset, Module 12)
POST /api/ws-ticket/        single-use WebSocket ticket (Module 21)
GET  /api/health/           liveness/readiness
```

DRF gives you three layers, and you should pick deliberately:

| Layer | What you get | Cost |
|-------|-------------|------|
| `@api_view` function + explicit `Response` | Total control, ~15 lines | You write the CRUD |
| `APIView` / generic views | Pagination, filtering, permission plumbing | A little indirection |
| `ModelViewSet` + router | Full CRUD from one class | Endpoints you didn't design, and a serializer on your hot path |

**Pulse uses `ModelViewSet` for rooms** (boring CRUD, low rate, and the router's
URL conventions are fine) **and hand-written `@api_view` functions for history,
health, and tickets** (each is one query with a specific shape, and history
becomes raw SQL in Module 12 — a serializer there would be pure overhead on the
path that gets hammered).

> **Serializers are the DRF piece that surprises people at scale.** A DRF
> `Serializer` does per-field Python-level validation and construction. For a
> 50-message history page that's 50 × N fields of interpreted work on your one
> core. Fine at 10 req/s, measurable at 1,000. Module 12 replaces the history
> serializer with a `values()` queryset and `JsonResponse`, and measures the
> difference. Know that it's coming.

---

## ASGI vs WSGI — the fork in the road

This is the section this module exists for.

**WSGI** (Web Server Gateway Interface, PEP 3333) is one synchronous function:

```python
def application(environ, start_response):
    start_response("200 OK", [("Content-Type", "text/plain")])
    return [b"hello"]
```

One call in, one iterable out. It is *request/response by construction*. There is
no `receive`, so a WSGI app **cannot be told about anything** except the request
it was handed. There is no way to express "a WebSocket," "a long-lived stream," or
"the server speaks first," because the interface has no vocabulary for them.

**ASGI** (Asynchronous Server Gateway Interface) is one async function with two
coroutines:

```python
async def application(scope, receive, send):
    # scope["type"] is "http", "websocket", or "lifespan"
    event = await receive()          # pull the next event from the client
    await send({"type": "websocket.accept"})
```

`scope` is a dict describing the connection (type, path, headers, client
address, and anything middleware chose to attach). `receive` and `send` are
coroutines over a bidirectional event stream. That's the whole spec, and it's
enough to express WebSocket, HTTP/2 server push, SSE, and lifespan startup —
because the server can now *send without being asked*.

```
WSGI                                    ASGI
────────────────────────────            ────────────────────────────────────
one request  → one OS thread            one connection → one asyncio Task
thread is busy until you return         coroutine suspends at every await
held-open response = thread gone        held-open response = a few KB of heap
1,000 held requests ⇒ 1,000 threads     1,000 held connections ⇒ 1,000 tasks
                     ⇒ dead                                    ⇒ fine
no server-initiated messages, ever      send() whenever you like
```

### Why `runserver` and sync views fundamentally cannot do realtime

Three separate reasons, and it is worth being precise because "just use Channels"
without understanding *why* leaves you unable to debug it:

1. **The interface has no room for it.** A sync view returns a response object.
   There is no callable it could invoke to push a second message, and no event to
   receive. This is not a performance problem you can tune around — the type
   signature forbids it.
2. **The concurrency model can't hold the connections.** Even if you could stream,
   a WSGI worker occupies an OS thread for the whole lifetime of a held-open
   response. `gunicorn` sync workers default to a handful per core. A hundred
   idle SSE clients exhaust them and the hundred-and-first user gets nothing.
   (Module 03 proved this on the wire; the lab proves it again here with a
   stopwatch.)
3. **`runserver` is a development server**, single-threaded-ish by default, that
   buffers, that reloads on file change, and that Django's own docs tell you not
   to deploy. Django 5.1's `runserver` *will* serve `asgi.py` when Channels'
   `runserver` override is installed — which makes it a decent dev convenience
   and a terrible measurement target. **Every number in this course comes from
   Uvicorn or Daphne, never from `runserver`.**

The moment Pulse needs a server-initiated message — which is the moment it
becomes chat — it is an ASGI application. Everything from Module 04 onward
assumes it.

### What `asgi.py` actually is

```python
# pulse/asgi.py
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pulse.settings")

from django.core.asgi import get_asgi_application
django_asgi_app = get_asgi_application()      # handles scope["type"] == "http"
application = django_asgi_app
```

`get_asgi_application()` returns an ASGI callable that handles `http` scopes by
running Django's request/response machinery. It **does nothing for `websocket`
scopes** — it doesn't know what one is. Module 04 wraps it in a
`ProtocolTypeRouter` that dispatches `http` there and `websocket` to Channels.
That composition — an ASGI app made of ASGI apps — is the entire architecture.

---

## Django's async story, and where it stops

Django has been growing an async half since 3.0. Knowing exactly what is and
isn't async is the difference between a fast server and a mysteriously slow one.

**Async views** work today and are ordinary:

```python
async def room_stats(request, slug):
    room = await Room.objects.aget(slug=slug)
    count = await Membership.objects.filter(room=room).acount()
    return JsonResponse({"room": room.slug, "members": count})
```

**Async ORM (4.1+)** gives you `a`-prefixed coroutine versions of the query API:

| Sync | Async |
|------|-------|
| `get()` / `create()` / `save()` / `delete()` | `aget()` / `acreate()` / `asave()` / `adelete()` |
| `first()` / `last()` / `count()` / `exists()` | `afirst()` / `alast()` / `acount()` / `aexists()` |
| `get_or_create()` / `update_or_create()` | `aget_or_create()` / `aupdate_or_create()` |
| `bulk_create()` | `abulk_create()` |
| `for obj in qs:` | `async for obj in qs:` |

> ⚠️ **The honest part nobody puts in the tutorial:** these are *not* async all
> the way down. The database driver call is still synchronous; Django runs it in
> a threadpool via `sync_to_async` under the hood. You get a coroutine-shaped API
> and a non-blocked event loop — which is exactly what you need — but **not**
> more database concurrency than your threadpool and connection pool allow. The
> Module 01 lesson stands unchanged: *concurrency became free, resources did
> not.* Module 15 pulls this apart with a profiler.

**What is still synchronous, and matters:**

- **Transactions.** `transaction.atomic()` is sync-only. Async code that needs a
  transaction wraps the whole unit in `sync_to_async` (or, in a consumer,
  `database_sync_to_async`). This is why Module 05's idempotent send is a single
  sync function called from async, not a chain of `await`s.
- **`select_for_update()`**, savepoints, and most of the connection-management
  API.
- **Sessions and `django.contrib.auth`.** `request.user` in an async view is a
  lazy object whose resolution hits the database *synchronously*; use
  `await request.auser()` (Django 5.0+) instead.
- **Most third-party apps.** Anything that touches the ORM in a signal handler,
  a middleware, or a manager method is sync.
- **The admin**, the template engine's DB access, and management commands.

**The safety net you should know by name:** if you call sync ORM code directly
from a coroutine, Django raises `SynchronousOnlyOperation` — deliberately, to
stop you shipping the cardinal sin. There is an env var,
`DJANGO_ALLOW_ASYNC_UNSAFE=true`, that disables the check. **It disables the
check, not the problem.** It exists for Jupyter notebooks. If you find it in a
production Dockerfile, you have found a bug.

### The bridges, one more time

| Bridge | Direction | Use |
|--------|-----------|-----|
| `sync_to_async(fn)` | sync → awaitable | Any blocking function, from async code |
| `database_sync_to_async(fn)` | sync → awaitable | **ORM calls in a consumer.** Also manages the per-thread DB connection correctly. Always this one for ORM. |
| `async_to_sync(coro)` | async → blocking call | Calling `channel_layer.group_send` from a DRF view, a Celery task, or a signal |

`async_to_sync` shows up constantly from Module 07: an HTTP endpoint that needs
to push to a room is sync code calling an async channel layer.

---

## Middleware and the auth model

Django middleware is an onion of callables around the view:

```python
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",   # sets request.user
    "django.contrib.messages.middleware.MessageMiddleware",
]
```

Each entry is a factory: `def middleware(get_response)` returning a callable that
takes a request and returns a response, having called `get_response(request)`
somewhere in the middle. Order is the nesting order — top of the list is
outermost.

Two facts that matter for a socket server:

1. **Middleware can be async.** Django inspects each middleware for
   `async_capable`/`sync_capable` and, at a boundary between an async middleware
   and a sync one, **adapts** by wrapping in a threadpool hop. A single sync
   middleware in an otherwise-async stack forces that hop on **every request**.
   Auditing `MIDDLEWARE` is real performance work under ASGI, and the lab makes
   you look at the adaptation.
2. **None of it runs for WebSocket.** `MIDDLEWARE` applies to `scope["type"] ==
   "http"` only. A WebSocket connection never passes through
   `AuthenticationMiddleware`, so `scope["user"]` does not exist unless something
   put it there. That something is **Channels middleware** — a different, ASGI-level
   onion wrapping the WebSocket router (Module 04), and the reason Module 21's
   ticket auth is a Channels middleware and not a Django one.

**Auth, briefly:** `AUTHENTICATION_BACKENDS` is a list of classes with
`authenticate()`/`get_user()`. `request.user` is a `SimpleLazyObject` resolved on
first access — which is why touching it in an async view without `await
request.auser()` raises `SynchronousOnlyOperation`. Sessions are a
database-backed (by default) cookie keyed store. For Pulse, sessions get you
through Modules 02–04, and Module 21 replaces the handshake with a JWT-backed
single-use ticket because query strings end up in access logs.

---

## Why not FastAPI / Starlette / Flask?

The honest comparison, because this course is about defending choices — and
because for *this specific workload* the answer is genuinely close.

- **Starlette** is the ASGI toolkit FastAPI is built on: routing, middleware,
  WebSocket support, ~7k lines. It is async-native with no sync legacy, so there
  is no seam to reason about and no `SynchronousOnlyOperation`. For a pure
  socket-fan-out edge it is **faster and denser than Django + Channels**, and
  Module 15 measures exactly how much (spoiler: meaningfully, and you also lose
  groups, routing, auth, and the ORM — hundreds of lines to rebuild).
- **FastAPI** adds Pydantic validation, dependency injection, and OpenAPI
  generation on top of Starlette. Its WebSocket support is a thin, honest wrapper
  around Starlette's — **there is no channel layer**, no groups, no cross-process
  fan-out. You would build Modules 07–11 by hand. Its ORM story is
  SQLAlchemy + Alembic, which is excellent and is *more* work than Django's
  models + migrations for the same result.
- **Flask** is WSGI. Everything in the ASGI section above applies: it can serve
  the REST half beautifully and cannot serve the real-time half at all without
  bolting on a separate async server (`flask-sock` + gevent, or a sidecar). For
  Pulse that means two runtimes, two deployment stories, and a shared-state
  problem between them.

**Why Django here.** This course spends four of its six phases on Redis,
Postgres, partitioning, sharding, Kafka, Kubernetes, and observability — the
*other* four problems of chat. Django's contribution is that migrations,
database routers (Modules 13–14), the ORM, DRF, and Channels' groups/auth/routing
already exist and are boringly well-understood, so the course can spend its time
on the parts that are hard. The bet is that framework overhead is not the
constraint; fan-out, delivery semantics, and write amplification are.

**And we check the bet rather than asserting it.**
[`15-async-sync-and-raw-asgi`](../15-async-sync-and-raw-asgi/) rebuilds the hot
path on **raw ASGI** (Starlette and the bare `websockets` library) and benchmarks
it head-to-head against Channels on the same machine with the same k6 script.
If Django loses badly there, that is a result this course will report, not hide.

> **The condition that flips the answer:** if your service is *only* a socket
> edge — no ORM, no admin, no migrations, no HTTP API worth speaking of — then
> Django is paying for a lot you never use, and Starlette (or Go, per Module 01)
> is the better tool. Pulse is not that service. Be honest about which one you're
> building.

---

## What's next

The lab generates the `pulse` project and the `chat` app, wires 12-factor
settings that fail fast, defines the custom user model *before* the first
migration, adds Room and Membership, runs migrations against the dev Compose
stack, builds the DRF surface (rooms, history, health, ticket stub), demonstrates
N+1 and fixes it, **proves with a stopwatch that WSGI cannot hold concurrent
connections and ASGI can**, triggers `SynchronousOnlyOperation` on purpose, and
confirms Uvicorn is really serving your `asgi.py` on uvloop.

See you in [`lab.md`](./lab.md).
