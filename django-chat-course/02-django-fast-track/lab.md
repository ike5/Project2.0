# Lab 02 — Build the Pulse Skeleton, and Find Django's Seam

**You'll:** generate the `pulse` project and the `chat` app; wire 12-factor
settings that crash on a missing variable; define the custom user model **before
the first migration** and then *prove* what happens if you don't; add `Room`,
`Membership` and a first `Message`; migrate against the dev Compose stack; build
the DRF surface (rooms, history, health, ticket stub); reproduce N+1 and kill it;
prove with a stopwatch that a WSGI server cannot hold concurrent connections and
an ASGI one can; trigger `SynchronousOnlyOperation` on purpose; count the threads
in Django's sync-under-ASGI pool; and confirm Uvicorn is really serving your
`asgi.py` on uvloop.

⏱️ ~110 min. Work in `django-chat-course/apps/pulse` — this directory is where
Pulse lives for the next twenty modules.

> **Everything you create here survives to Module 22.** This is not a throwaway
> tutorial project. Module 04 adds consumers to this `chat` app, Module 05 adds
> the envelope, Module 12 rewrites this `Message` table with raw DDL, and Module
> 18 runs three copies of it behind nginx. Name things like you mean it.

Reference machine for every number below: **8-core / 16 GB, Ubuntu 24.04,
Python 3.12, Django 5.1**. Yours will differ; the ratios are the lesson.

---

## Part A — Create the project

The data tier first. From the course root:

```bash
cd django-chat-course
docker compose -p pulse-dev -f infra/compose.dev.yml up -d
docker compose -p pulse-dev -f infra/compose.dev.yml ps
```

**Expected:** both services healthy — this is the same stack
[`VERIFY.md`](../VERIFY.md) §10 smoke-tested:
```
NAME             IMAGE                STATUS
pulse-postgres   postgres:16-alpine   Up 12 seconds (healthy)
pulse-redis      redis:7-alpine       Up 12 seconds (healthy)
```

Now the project. We use one virtualenv for the whole course, at the course root,
so Modules 01–22 share it:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --quiet \
    "django==5.1.*" "djangorestframework==3.15.*" \
    "psycopg[binary]==3.2.*" \
    "uvicorn[standard]==0.30.*" "gunicorn==22.*"
mkdir -p apps/pulse && cd apps/pulse
django-admin startproject pulse .
python manage.py startapp chat
```

> The trailing `.` in `startproject pulse .` matters. Without it Django creates
> `pulse/pulse/` — a nested directory that adds nothing and confuses every
> `docker build` context you will ever write. With it you get `manage.py` at the
> top and the *project package* `pulse/` beside the *app package* `chat/`.

```bash
find . -name '*.py' -not -path './.venv/*' | sort
```

**Expected:**
```
./chat/__init__.py
./chat/admin.py
./chat/apps.py
./chat/migrations/__init__.py
./chat/models.py
./chat/tests.py
./chat/views.py
./manage.py
./pulse/__init__.py
./pulse/asgi.py
./pulse/settings.py
./pulse/urls.py
./pulse/wsgi.py
```

✅ Note that `startproject` gave you **both** `wsgi.py` and `asgi.py`. Django
does not choose for you; the *server you run* chooses. Part G makes that choice
visible with a stopwatch.

---

## Part B — Settings that fail fast

`settings.py` is executed Python, so 12-factor config is just code. Replace the
top of `pulse/settings.py` (keep `BASE_DIR`, replace everything down to and
including `DATABASES`):

```python
# pulse/settings.py
from pathlib import Path
import os

from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent

_UNSET = object()


def env(key, default=_UNSET, cast=str):
    """Read one environment variable. No default => missing is a startup crash."""
    raw = os.environ.get(key, _UNSET if default is _UNSET else default)
    if raw is _UNSET:
        raise ImproperlyConfigured(
            f"missing required environment variable {key!r} "
            f"(see apps/pulse/env.dev for the development values)"
        )
    return cast(raw)


def as_bool(v):
    return str(v).strip().lower() in {"1", "true", "yes", "on"}


def as_list(v):
    return [s.strip() for s in str(v).split(",") if s.strip()]


# ---------------------------------------------------------------- core
SECRET_KEY    = env("DJANGO_SECRET_KEY")                       # no default. deliberate.
DEBUG         = env("DJANGO_DEBUG", "0", cast=as_bool)
ALLOWED_HOSTS = env("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1", cast=as_list)

# The one irreversible decision in this module. See Part C.
AUTH_USER_MODEL = "chat.User"

# Channels reads this from Module 04 onward. Setting it now is one less thing
# to forget at 11pm when consumers "silently never run".
ASGI_APPLICATION = "pulse.asgi.application"

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "chat",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
]

ROOT_URLCONF = "pulse.urls"
WSGI_APPLICATION = "pulse.wsgi.application"

# ---------------------------------------------------------------- data
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME":     env("PG_DB",   "pulse"),
        "USER":     env("PG_USER", "pulse"),
        "PASSWORD": env("PG_PASSWORD"),                        # no default. deliberate.
        "HOST":     env("PG_HOST", "localhost"),
        "PORT":     env("PG_PORT", "5432"),
        # Reuse a connection for 60s instead of a fresh TCP+TLS+auth handshake
        # per request. Module 13 shows how violently this interacts with
        # PgBouncer in transaction pooling mode — remember you set it.
        "CONN_MAX_AGE": env("PG_CONN_MAX_AGE", "60", cast=int),
        "CONN_HEALTH_CHECKS": True,
    }
}

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "UNAUTHENTICATED_USER": "django.contrib.auth.models.AnonymousUser",
}
```

Now the development values, in a file you **never commit**:

```bash
cat > env.dev <<'EOF'
DJANGO_SECRET_KEY=dev-only-not-a-secret-change-me
DJANGO_DEBUG=1
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
PG_DB=pulse
PG_USER=pulse
PG_PASSWORD=pulse
PG_HOST=localhost
PG_PORT=5432
EOF
echo -e ".venv/\nenv.dev\n*.sqlite3\n__pycache__/" > .gitignore
```

Load it into your shell (do this in every terminal you use for the rest of the
course):

```bash
set -a; source env.dev; set +a
python manage.py check
```

**Expected:**
```
System check identified no issues (0 silenced).
```

Now prove the fail-fast actually fails:

```bash
( unset DJANGO_SECRET_KEY; python manage.py check )
```

**Expected — a crash at *import*, naming the variable:**
```
django.core.exceptions.ImproperlyConfigured: missing required environment
variable 'DJANGO_SECRET_KEY' (see apps/pulse/env.dev for the development values)
```

✅ **That traceback is the feature.** Compare it to the alternative:
`SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "insecure-fallback")`, which
produces a server that boots, serves traffic, signs session cookies with a
publicly known key, and tells nobody. A container that exits in three seconds
with the variable name in the log is a fixed deploy; a container that boots
insecure is a breach in six months.

This is the Python equivalent of the JVM twin's
[`@ConfigurationProperties` validation](../../spring-boot-chat-course/02-spring-fast-track/),
and it took four lines instead of a validation annotation, because `settings.py`
is a program.

---

## Part C — The custom user model, before anything else

**Do not run `migrate` yet.** Read this part first.

`chat/models.py`:

```python
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Pulse's user.

    Empty today, on purpose. Module 21 hangs JWT key material, ticket
    revocation state, and per-user abuse counters off this model; Module 11
    hangs presence preferences off it. None of that is possible later if
    AUTH_USER_MODEL is still django.contrib.auth.User, because swapping it
    after the first migrate means surgery on every foreign key in the database.

    An empty subclass costs nothing and buys you the option. Take it.
    """
    display_name = models.CharField(max_length=80, blank=True)

    def __str__(self):
        return self.username
```

You already set `AUTH_USER_MODEL = "chat.User"` in Part B. Now make the first
migration and *read it before running it*:

```bash
python manage.py makemigrations chat
python manage.py sqlmigrate chat 0001 | head -20
```

**Expected:**
```
Migrations for 'chat':
  chat/migrations/0001_initial.py
    + Create model User
```
```sql
BEGIN;
--
-- Create model User
--
CREATE TABLE "chat_user" ("id" bigint NOT NULL PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY,
    "password" varchar(128) NOT NULL, "last_login" timestamp with time zone NULL,
    "is_superuser" boolean NOT NULL, "username" varchar(150) NOT NULL UNIQUE, ...
```

> `sqlmigrate` is the habit to build now. It costs two seconds and it is the
> only way to know what a migration will actually do to a table. In Module 13
> you will read the SQL of a partitioning migration extremely carefully.

### Now prove the warning, on a scratch database

The README said swapping `AUTH_USER_MODEL` after the first `migrate` means
surgery. Don't take it on faith — reproduce the exact failure in a database you
can throw away.

```bash
docker exec pulse-postgres createdb -U pulse scratch

# 1. Migrate a "we'll add a custom user later" project: comment AUTH_USER_MODEL out.
sed -i 's/^AUTH_USER_MODEL/# AUTH_USER_MODEL/' pulse/settings.py
PG_DB=scratch python manage.py migrate 2>&1 | tail -4
```

**Expected** — everything applies cleanly, using `auth.User`:
```
  Applying auth.0012_alter_user_first_name_max_length... OK
  Applying chat.0001_initial... OK
  Applying sessions.0001_initial... OK
```

```bash
# 2. Two months later, you decide you need a custom user after all.
sed -i 's/^# AUTH_USER_MODEL/AUTH_USER_MODEL/' pulse/settings.py
PG_DB=scratch python manage.py migrate 2>&1 | tail -6
```

**Expected — the failure, by name:**
```
django.db.migrations.exceptions.InconsistentMigrationHistory: Migration
admin.0001_initial is applied before its dependency chat.0001_initial on
database 'scratch'.
```

✅ Read that carefully, because it is not an arbitrary complaint.
`admin.0001_initial` declares a dependency on `settings.AUTH_USER_MODEL`'s app.
When you migrated with `auth.User`, that resolved to `auth` and applied fine.
After the swap it resolves to `chat`, and Django discovers it applied the admin
tables *before* the app that now owns users. There is no automatic fix: every
`user_id` foreign key in the database points at `auth_user`, and Django will not
rewrite them for you.

The real-world remedies are all bad — a hand-written data migration that
repoints every FK, or `--fake` plus manual DDL, or a dump/restore. That is why
Pulse defines `chat.User` on day one, in a lab, before a single table exists.

Clean up the scratch database:

```bash
docker exec pulse-postgres dropdb -U pulse scratch
```

---

## Part D — Room, Membership, and a first Message

Append to `chat/models.py`:

```python
class Room(models.Model):
    """A chat room. `slug` is the short handle; `key` is what goes on the wire."""
    slug       = models.SlugField(max_length=64, unique=True)   # "general", "7"
    name       = models.CharField(max_length=120)
    created_at = models.DateTimeField(auto_now_add=True)
    members    = models.ManyToManyField(
        "chat.User", through="chat.Membership", related_name="rooms"
    )

    class Meta:
        indexes = [models.Index(fields=["created_at"])]

    @property
    def key(self) -> str:
        """The one string that identifies this room everywhere outside the ORM.

        It is the Channels group name (Module 04), the envelope's `room` field
        (Module 05), and messages.room_id in the store (Module 12). One string,
        one meaning, in every layer — that is not an accident, it is a design
        rule: any identifier that has to be reconstructed differently per layer
        becomes a bug the first time you change transports.
        """
        return f"room.{self.slug}"

    def __str__(self):
        return self.key


class Membership(models.Model):
    """Explicit through-model: joins carry data (role, join time, mute state)."""

    class Role(models.TextChoices):
        MEMBER = "member", "Member"
        ADMIN  = "admin",  "Admin"

    user      = models.ForeignKey("chat.User", on_delete=models.CASCADE)
    room      = models.ForeignKey(Room, on_delete=models.CASCADE)
    role      = models.CharField(max_length=16, choices=Role.choices, default=Role.MEMBER)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "room"], name="uq_membership"),
        ]
        # The hot query is "is user U in room R?" at connect time (Module 04)
        # and at delivery time (Module 21). Index for that, not for admin lists.
        indexes = [models.Index(fields=["room", "user"])]


class Message(models.Model):
    """The naive, ORM-idiomatic message.

    Foreign keys to Room and User, an auto bigint pk, no sequence, no
    idempotency key. Module 05 adds `client_id` and `seq`; Module 12 measures
    this shape at fifty million rows, deletes the foreign keys, and replaces
    the whole table with hand-written DDL. Build the honest version first so
    the replacement is a *result*, not a preference.
    """
    room       = models.ForeignKey(Room, on_delete=models.CASCADE, related_name="messages")
    sender     = models.ForeignKey("chat.User", on_delete=models.PROTECT)
    body       = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["room", "-id"], name="idx_msg_scrollback")]
```

Why `Membership` is an explicit model rather than a bare `ManyToManyField`: the
moment a join carries *data* — a role, a mute flag, a `last_read_seq` (Module
10) — the implicit through-table cannot hold it, and retrofitting one means a
table rename. Model the relationship you actually have.

```bash
python manage.py makemigrations chat
python manage.py sqlmigrate chat 0002 | grep -E 'CREATE (TABLE|INDEX|UNIQUE)'
```

**Expected:**
```
CREATE TABLE "chat_room" ("id" bigint NOT NULL PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY, ...
CREATE TABLE "chat_membership" ("id" bigint NOT NULL PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY, ...
CREATE TABLE "chat_message" ("id" bigint NOT NULL PRIMARY KEY GENERATED BY DEFAULT AS IDENTITY, ...
CREATE UNIQUE INDEX "uq_membership" ON "chat_membership" ("user_id", "room_id");
CREATE INDEX "chat_membership_room_id_user_id_..." ON "chat_membership" ("room_id", "user_id");
CREATE INDEX "idx_msg_scrollback" ON "chat_message" ("room_id", "id" DESC);
```

Apply for real, against the Compose Postgres:

```bash
python manage.py migrate
```

**Expected** (tail):
```
  Applying chat.0001_initial... OK
  Applying admin.0001_initial... OK
  ...
  Applying chat.0002_room_membership_message... OK
  Applying sessions.0001_initial... OK
```

Seed enough data to have something to break:

```bash
python manage.py shell -c "
from chat.models import User, Room, Membership, Message
import random
users = [User.objects.create_user(username=f'u{i}', password='x',
                                  display_name=f'User {i}') for i in range(50)]
room = Room.objects.create(slug='general', name='General')
Membership.objects.bulk_create(Membership(user=u, room=room) for u in users)
Message.objects.bulk_create(
    Message(room=room, sender=random.choice(users), body=f'message {i}')
    for i in range(500))
print(room.key, Message.objects.count(), 'messages')
"
```

**Expected:**
```
room.general 500 messages
```

---

## Part E — The DRF surface

Pulse's HTTP API is small and deliberate: rooms are boring CRUD (a `ModelViewSet`
earns its keep), while history, health and tickets are each one query with a
specific shape (hand-written `@api_view` functions, because a serializer on the
scrollback path is pure overhead — Module 12 measures it).

`chat/serializers.py`:

```python
from rest_framework import serializers

from chat.models import Message, Room


class RoomSerializer(serializers.ModelSerializer):
    key          = serializers.CharField(read_only=True)
    member_count = serializers.IntegerField(read_only=True)

    class Meta:
        model  = Room
        fields = ["id", "slug", "name", "key", "member_count", "created_at"]


class MessageSerializer(serializers.ModelSerializer):
    sender = serializers.CharField(source="sender.username", read_only=True)

    class Meta:
        model  = Message
        fields = ["id", "sender", "body", "created_at"]
```

`chat/views.py`:

```python
import asyncio
import os
import secrets
import threading
import time

from django.db import connection
from django.db.models import Count
from django.http import JsonResponse
from rest_framework import viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from chat.models import Message, Room
from chat.serializers import MessageSerializer, RoomSerializer


class RoomViewSet(viewsets.ModelViewSet):
    """Boring CRUD. Low rate, object-graph-shaped: let DRF do it."""
    serializer_class = RoomSerializer

    def get_queryset(self):
        # annotate() instead of a per-row .members.count() — one query, not N.
        return Room.objects.annotate(member_count=Count("membership")).order_by("slug")


@api_view(["GET"])
def history(request, slug):
    """Scrollback. Keyset ('seek') pagination, never OFFSET.

    `?before=<id>&limit=50` walks backwards through idx_msg_scrollback. Module
    12 proves OFFSET 1000000 costs 380 ms while this costs 0.9 ms, and replaces
    even this with a raw cursor + JsonResponse.
    """
    limit  = min(int(request.query_params.get("limit", 50)), 200)
    before = request.query_params.get("before")

    qs = Message.objects.filter(room__slug=slug).select_related("sender")
    if before:
        qs = qs.filter(id__lt=int(before))
    rows = list(qs.order_by("-id")[:limit])

    return Response({
        "room":     f"room.{slug}",
        "messages": MessageSerializer(reversed(rows), many=True).data,
        "next_before": rows[-1].id if len(rows) == limit else None,
    })


@api_view(["GET"])
@permission_classes([AllowAny])
def health(request):
    """Liveness + readiness. Kept honest: it actually touches the database."""
    t0 = time.perf_counter()
    try:
        with connection.cursor() as cur:
            cur.execute("SELECT 1")
            cur.fetchone()
        db_ms, db_ok = (time.perf_counter() - t0) * 1000, True
    except Exception:                                    # noqa: BLE001 - report, don't raise
        db_ms, db_ok = (time.perf_counter() - t0) * 1000, False

    return Response(
        {"status": "ok" if db_ok else "degraded",
         "db": {"ok": db_ok, "ms": round(db_ms, 2)},
         "pid": os.getpid()},
        status=200 if db_ok else 503,
    )


# --- Module 21 replaces this entire block with signed, single-use Redis tickets.
_TICKETS: dict[str, tuple[int, float]] = {}          # token -> (user_id, expires_at)


@api_view(["POST"])
def ws_ticket(request):
    """Stub: mint a short-lived ticket for the WebSocket handshake.

    A browser's `new WebSocket(url)` cannot set an Authorization header, so the
    credential has to ride in the URL — and URLs end up in access logs. The
    mitigation is that this token is *single-use* and *short-lived*, so a log
    leak is worth nothing. It lives in a process-local dict today, which means
    it does not survive a restart and does not work with two workers. That is
    the same wall Module 04 hits with the channel layer, and Module 21 fixes
    both with Redis.
    """
    token = secrets.token_urlsafe(24)
    _TICKETS[token] = (request.user.id, time.time() + 30)
    return Response({"ticket": token, "expires_in": 30})


# --- Part G/H demo endpoints. Removed at the end of the lab.
def slow_sync(request):
    time.sleep(2.0)                                  # blocking, on purpose
    return JsonResponse({"kind": "sync", "pid": os.getpid(),
                         "thread": threading.current_thread().name})


async def slow_async(request):
    await asyncio.sleep(2.0)                         # cooperative
    return JsonResponse({"kind": "async", "pid": os.getpid(),
                         "thread": threading.current_thread().name})
```

`pulse/urls.py`:

```python
from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from chat import views

router = DefaultRouter()
router.register("rooms", views.RoomViewSet, basename="room")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include(router.urls)),
    path("api/rooms/<slug:slug>/history/", views.history),
    path("api/health/",    views.health),
    path("api/ws-ticket/", views.ws_ticket),
    path("api/slow-sync/",  views.slow_sync),
    path("api/slow-async/", views.slow_async),
]
```

Run it under **Uvicorn**, not `runserver` — start as you mean to continue:

```bash
uvicorn pulse.asgi:application --host 127.0.0.1 --port 8000
```

**Expected:**
```
INFO:     Started server process [48210]
INFO:     Waiting for application startup.
WARNING:  ASGI 'lifespan' protocol appears unsupported.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

> That `lifespan` warning is expected and harmless: Django's `ASGIHandler`
> handles `scope["type"] == "http"` and nothing else, so Uvicorn's startup
> handshake gets no answer. It is also a preview of Module 04's central fact —
> `get_asgi_application()` does not know what a `websocket` scope is either.
> Silence it with `--lifespan off` if it bothers you.

In another terminal (with `env.dev` sourced):

```bash
curl -s localhost:8000/api/health/ | python -m json.tool
```

**Expected:**
```json
{
    "status": "ok",
    "db": { "ok": true, "ms": 0.71 },
    "pid": 48210
}
```

```bash
curl -s "localhost:8000/api/rooms/general/history/?limit=3" | python -m json.tool
```

**Expected:**
```json
{
    "room": "room.general",
    "messages": [
        { "id": 498, "sender": "u17", "body": "message 497", "created_at": "..." },
        { "id": 499, "sender": "u3",  "body": "message 498", "created_at": "..." },
        { "id": 500, "sender": "u41", "body": "message 499", "created_at": "..." }
    ],
    "next_before": 498
}
```

✅ The rooms endpoints need a session, so they 403 from `curl`. That is DRF's
`IsAuthenticated` default doing its job. Confirm:

```bash
curl -s -o /dev/null -w '%{http_code}\n' localhost:8000/api/rooms/
```
**Expected:** `403`

---

## Part F — N+1, seen and killed

Turn on SQL logging so the queries are not a matter of opinion. Add to
`settings.py`:

```python
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "loggers": {
        # Only fires when DEBUG=True. That is fine here and a memory leak in
        # production — see the DEBUG warning below.
        "django.db.backends": {"handlers": ["console"],
                               "level": env("SQL_LOG_LEVEL", "INFO")},
    },
}
```

Now measure, in the shell, using `CaptureQueriesContext` — which counts queries
without needing you to read a wall of SQL:

```bash
python manage.py shell -c "
import time
from django.db import connection, reset_queries
from django.test.utils import CaptureQueriesContext
from chat.models import Message

def bench(label, fn):
    reset_queries()
    with CaptureQueriesContext(connection) as ctx:
        t0 = time.perf_counter(); n = fn(); dt = (time.perf_counter()-t0)*1000
    print(f'{label:<34} rows={n:<4} queries={len(ctx):<4} {dt:8.1f} ms')

qs = Message.objects.filter(room__slug='general').order_by('-id')[:200]

bench('naive (touch m.sender.username)',
      lambda: len([m.sender.username for m in qs]))
bench('select_related(\"sender\")',
      lambda: len([m.sender.username for m in qs.select_related('sender')]))
bench('.values(sender__username, body)',
      lambda: len(list(qs.values('id','body','sender__username'))))
"
```

**Expected:**
```
naive (touch m.sender.username)     rows=200  queries=201   146.8 ms
select_related("sender")            rows=200  queries=1       4.2 ms
.values(sender__username, body)     rows=200  queries=1       1.9 ms
```

✅ Three numbers, three lessons:

- **201 → 1 queries.** The lazy `QuerySet` executed once for the messages, then
  once *per row* to resolve `m.sender`. 146 ms of that is 200 round trips to a
  database on localhost. Over a real network at 1 ms RTT it is 350 ms, and it
  scales with page size, so it gets worse exactly when it matters.
- **`select_related` is a JOIN**, one query, same objects. Use it for forward FK
  and OneToOne. Reverse FK and M2M need `prefetch_related`, which is a *second*
  query plus in-Python stitching — cheaper than N+1, never as cheap as a JOIN.
- **`.values()` is 2.2× faster than `select_related`** even at one query each,
  because it skips model instantiation. Constructing 200 `Message` objects plus
  200 `User` objects is ~1,200 Python attribute writes on your one event-loop
  core. Module 12 takes this further and drops history to
  `connection.cursor()` + `JsonResponse`.

Now the DEBUG trap, because it is the one that kills load tests:

```bash
python manage.py shell -c "
from django.conf import settings
from django.db import connection
from chat.models import Message
print('DEBUG =', settings.DEBUG)
for _ in range(2000):
    Message.objects.filter(room__slug='general').only('id').first()
print('queries retained in memory:', len(connection.queries))
"
```

**Expected:**
```
DEBUG = True
queries retained in memory: 2000
```

✅ With `DEBUG=True`, Django appends every SQL string and its timing to
`connection.queries` **and never frees it**. A worker doing 5,000 queries a
second accumulates hundreds of megabytes an hour and then dies looking like a
memory leak in your code. Run the same loop with `DJANGO_DEBUG=0` and the count
is `0`. This is why every measurement in this course runs with `DEBUG=0`, and
why Module 06's harness asserts it before it starts.

---

## Part G — The stopwatch: WSGI cannot hold connections, ASGI can

The README argued this from the type signatures. Now time it.

**Round 1 — WSGI, two sync workers.** In one terminal:

```bash
gunicorn pulse.wsgi:application --workers 2 --threads 1 --bind 127.0.0.1:8001
```

In another:

```bash
time ( for i in $(seq 1 10); do curl -s localhost:8001/api/slow-sync/ >/dev/null & done; wait )
```

**Expected — ten 2-second requests take twenty seconds:**
```
real    0m20.09s
```

Two workers × one thread = two concurrent requests. The other eight queued in
the kernel accept backlog. **This is not a tuning problem.** Nothing was
CPU-bound; both workers were asleep inside `time.sleep`. The concurrency limit
is the number of OS threads, and OS threads are the resource Module 01 showed
you run out of at ~32,000 — long before you reach chat scale.

**Round 2 — ASGI, one worker, async view:**

```bash
uvicorn pulse.asgi:application --host 127.0.0.1 --port 8000     # already running
time ( for i in $(seq 1 10); do curl -s localhost:8000/api/slow-async/ >/dev/null & done; wait )
```

**Expected — ten 2-second requests take two seconds:**
```
real    0m2.07s
```

Ten coroutines parked at `await asyncio.sleep(2)`. **One process, one thread,
one core.** Push it:

```bash
time ( for i in $(seq 1 500); do curl -s localhost:8000/api/slow-async/ >/dev/null & done; wait )
```

**Expected:**
```
real    0m2.61s
```

✅ 500 concurrent held requests, 2.6 seconds, one worker. That is the ratio the
whole course rests on. Record it.

**Round 3 — the subtle one. A *sync* view under ASGI.**

Django does not refuse to serve `def` views under ASGI; it runs them in a
thread pool via `sync_to_async`. So they work — up to the size of that pool,
and the pool is bounded. Find out how bounded by making the view report its
thread:

```bash
for i in $(seq 1 100); do curl -s localhost:8000/api/slow-sync/ & done \
  | python -c "
import sys, json
names = {json.loads(l)['thread'] for l in sys.stdin if l.strip()}
print(f'{len(names)} distinct worker threads served 100 requests')
print(sorted(names)[:6], '...')
"
```

**Expected** (the pool size is `min(32, cpu_count + 4)` = 12 on an 8-core box):
```
12 distinct worker threads served 100 requests
['asyncio_0', 'asyncio_1', 'asyncio_10', 'asyncio_11', 'asyncio_2', 'asyncio_3'] ...
```

And time it:

```bash
time ( for i in $(seq 1 100); do curl -s localhost:8000/api/slow-sync/ >/dev/null & done; wait )
```

**Expected — 100 requests ÷ 12 threads × 2 s ≈ 17 s:**
```
real    0m17.12s
```

✅ **This is Module 01's "concurrency is free, resources are not" in Django's
own plumbing.** The async view served 500 concurrent requests in 2.6 s; the sync
view served 100 in 17 s, because it queued on a twelve-thread pool. Nothing
errored. Nothing logged. Your p99 just went from 2 s to 17 s and the only
visible difference in the source is the word `async`.

Remember this pool — you meet it again in Module 04 as
`database_sync_to_async`, and in Module 15 where one blocking ORM call in an
async consumer takes p99 from ~60 ms to multiple seconds for *every connection
on the worker*.

> asgiref sizes this pool from the `ASGI_THREADS` environment variable where
> the ASGI server honours it, but servers differ. Counting distinct thread names
> like you just did works everywhere and tells you the truth about the server
> you are actually running.

Stop gunicorn; you are done with WSGI for the rest of the course.

---

## Part H — Trigger `SynchronousOnlyOperation` on purpose

Add to `chat/views.py`:

```python
from asgiref.sync import sync_to_async
from chat.models import Membership, Room


async def room_stats_broken(request, slug):
    room = Room.objects.get(slug=slug)               # sync ORM, called from async
    return JsonResponse({"room": room.key})


async def room_stats(request, slug):
    room    = await Room.objects.aget(slug=slug)                     # async ORM
    members = await Membership.objects.filter(room=room).acount()
    # Transactions are still sync-only, so anything transactional crosses the
    # bridge as one unit -- this is why Module 05's idempotent send is a single
    # sync function called from async, not a chain of awaits.
    recent  = await sync_to_async(
        lambda: list(Message.objects.filter(room=room)
                     .order_by("-id").values_list("body", flat=True)[:3])
    )()
    return JsonResponse({"room": room.key, "members": members, "recent": recent})
```

Route both:

```python
    path("api/rooms/<slug:slug>/stats-broken/", views.room_stats_broken),
    path("api/rooms/<slug:slug>/stats/",        views.room_stats),
```

```bash
curl -s localhost:8000/api/rooms/general/stats-broken/ | head -3
```

**Expected — a 500, and in the Uvicorn log:**
```
django.core.exceptions.SynchronousOnlyOperation: You cannot call this from an
async context - use a thread or sync_to_async.
```

✅ **That exception is Django protecting you.** The sync ORM call would have
blocked the event loop — and with it every other connection this worker holds.
Django cannot make it safe, so it refuses.

```bash
curl -s localhost:8000/api/rooms/general/stats/ | python -m json.tool
```

**Expected:**
```json
{
    "room": "room.general",
    "members": 50,
    "recent": ["message 499", "message 498", "message 497"]
}
```

Now the escape hatch, so you recognize it in a code review:

```bash
DJANGO_ALLOW_ASYNC_UNSAFE=1 uvicorn pulse.asgi:application --port 8002 &
sleep 2
curl -s localhost:8002/api/rooms/general/stats-broken/
```

**Expected — it "works":**
```json
{"room": "room.general"}
```

✅ And that is the trap. `DJANGO_ALLOW_ASYNC_UNSAFE` **disables the check, not
the problem.** The query still blocks the loop; you have merely removed the
alarm. It exists so Jupyter notebooks can use the ORM inside IPython's event
loop. If you find it in a Dockerfile, you have found a bug. Kill that server:

```bash
kill %1
```

---

## Part I — Middleware, and the adaptation you are paying for

Django inspects every middleware for `sync_capable` / `async_capable` and
inserts a threadpool hop at each boundary. Make it visible. Create
`chat/middleware.py`:

```python
import threading

from asgiref.sync import iscoroutinefunction, markcoroutinefunction


class SyncTimingMiddleware:
    """A perfectly ordinary sync middleware. Note what it costs under ASGI."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request._mw_thread = threading.current_thread().name
        return self.get_response(request)


class AsyncTimingMiddleware:
    """The same middleware, async-native. No hop."""

    async_capable = True
    sync_capable  = False

    def __init__(self, get_response):
        self.get_response = get_response
        if iscoroutinefunction(self.get_response):
            markcoroutinefunction(self)

    async def __call__(self, request):
        request._mw_thread = threading.current_thread().name
        return await self.get_response(request)
```

Add a view that reports both thread names:

```python
async def where_am_i(request):
    return JsonResponse({
        "middleware_thread": getattr(request, "_mw_thread", "?"),
        "view_thread":       threading.current_thread().name,
    })
```
```python
    path("api/where/", views.where_am_i),
```

Run with the **sync** middleware first:

```bash
# add "chat.middleware.SyncTimingMiddleware" to the end of MIDDLEWARE, restart
curl -s localhost:8000/api/where/
```

**Expected — two different threads:**
```json
{"middleware_thread": "asyncio_3", "view_thread": "MainThread"}
```

Swap it for `chat.middleware.AsyncTimingMiddleware` and restart:

**Expected — one thread, the event loop's:**
```json
{"middleware_thread": "MainThread", "view_thread": "MainThread"}
```

✅ The sync middleware ran on a *pool thread*, which means every request paid a
`sync_to_async` hop in and an `async_to_sync` hop out — two context switches and
a slot in the twelve-thread pool from Part G, on every request, forever. At low
rate it is invisible. At 5,000 req/s it is the pool from Part G, saturated, for
a middleware that sets one attribute.

**Auditing `MIDDLEWARE` is real performance work under ASGI.** Django's own
middleware is mostly async-capable in 5.1; third-party middleware often is not,
and one sync entry in an otherwise-async stack forces the hop for every request
regardless of where it sits in the list.

> **And the fact that matters most for the rest of this course:** none of this
> runs for a WebSocket. `MIDDLEWARE` applies to `scope["type"] == "http"` only.
> Your WebSocket connections in Module 04 pass through a completely different,
> ASGI-level middleware stack, which is why `scope["user"]` does not exist until
> something explicitly puts it there.

---

## Part J — Prove Uvicorn is serving *your* `asgi.py`, on uvloop

Three claims worth verifying rather than assuming: the server is running ASGI,
it is running *your* file, and the loop is uvloop.

Add a self-describing endpoint:

```python
import asyncio, sys


async def runtime(request):
    loop = asyncio.get_running_loop()
    return JsonResponse({
        "loop":        type(loop).__module__ + "." + type(loop).__qualname__,
        "python":      sys.version.split()[0],
        "pid":         os.getpid(),
        "asgi_module": __import__("pulse.asgi", fromlist=["application"]).__file__,
    })
```
```python
    path("api/runtime/", views.runtime),
```

```bash
uvicorn pulse.asgi:application --port 8000 --loop uvloop &
sleep 2
curl -s localhost:8000/api/runtime/ | python -m json.tool
```

**Expected:**
```json
{
    "loop": "uvloop.Loop",
    "python": "3.12.7",
    "pid": 49331,
    "asgi_module": "/home/you/django-chat-course/apps/pulse/pulse/asgi.py"
}
```

✅ Three proofs in one response. `uvloop.Loop` — not `asyncio.unix_events` —
means the libuv loop from Module 01's Part E (2.8× on raw task-switch
throughput) is live. The `asgi_module` path is *your* file, not something
Uvicorn synthesized. And you got a running loop at all, which a WSGI server
could never have given you.

Contrast:

```bash
kill %1
uvicorn pulse.asgi:application --port 8000 --loop asyncio &
sleep 2
curl -s localhost:8000/api/runtime/ | python -c "import sys,json; print(json.load(sys.stdin)['loop'])"
```

**Expected:**
```
asyncio.unix_events._UnixSelectorEventLoop
```

Put `--loop uvloop` back. Every reference number in this course assumes it.

Finally, confirm the process model you will use from Module 06 onward — one
worker process per core, because the GIL means one process uses one core:

```bash
kill %1
uvicorn pulse.asgi:application --port 8000 --loop uvloop --workers 4 &
sleep 3
for i in 1 2 3 4 5 6 7 8; do curl -s localhost:8000/api/health/ \
  | python -c "import sys,json; print(json.load(sys.stdin)['pid'])"; done | sort -u
```

**Expected — four distinct pids:**
```
49402
49403
49404
49405
```

✅ Four independent Python processes, four interpreters, four event loops,
**four separate heaps sharing nothing**. For a stateless health check that is
free parallelism. For anything that holds state — a subscription registry, a
ticket dict, a chat room — it is a wall, and hitting that wall is the entire
subject of [Module 04](../04-channels-chat-single-node/). Notice that
`/api/ws-ticket/` is already broken under this command: a ticket minted by pid
49402 is invisible to the other three.

Clean up the lab-only endpoints (`slow_sync`, `slow_async`,
`room_stats_broken`, `where_am_i`) and their routes; keep `runtime`, `health`,
`history`, `ws_ticket`, `RoomViewSet` and `room_stats`.

```bash
kill %1
```

---

## What you measured

Record these in `apps/pulse/results-02.md`:

| Measurement | Reference | Yours |
|-------------|-----------|-------|
| Missing `DJANGO_SECRET_KEY` | crash at import, variable named | |
| Swapping `AUTH_USER_MODEL` post-migrate | `InconsistentMigrationHistory` | |
| N+1 history page (200 rows) | 201 queries / 146.8 ms | |
| `select_related("sender")` | 1 query / 4.2 ms | |
| `.values(...)` | 1 query / 1.9 ms | |
| `connection.queries` after 2,000 queries, `DEBUG=1` | 2,000 retained | |
| 10 × 2 s requests, gunicorn 2 sync workers | 20.1 s | |
| 10 × 2 s requests, uvicorn async view | 2.07 s | |
| 500 × 2 s requests, uvicorn async view | 2.61 s | |
| 100 × 2 s requests, uvicorn **sync** view | 17.1 s (12-thread pool) | |
| Sync ORM in async view | `SynchronousOnlyOperation` | |
| Sync middleware under ASGI | runs on `asyncio_N`, not `MainThread` | |
| Loop under `--loop uvloop` | `uvloop.Loop` | |
| Distinct pids with `--workers 4` | 4 | |

---

## What you built

`apps/pulse` now contains a real Django service:

```
apps/pulse/
├── manage.py
├── env.dev                      ← 12-factor values, never committed
├── pulse/
│   ├── settings.py              ← fails fast on missing config
│   ├── urls.py
│   ├── asgi.py                  ← Module 04 wraps this in a ProtocolTypeRouter
│   └── wsgi.py                  ← you will not touch this again
└── chat/
    ├── models.py                ← User (custom, day one), Room, Membership, Message
    ├── serializers.py
    ├── views.py                 ← rooms CRUD, history, health, ticket stub, runtime
    ├── middleware.py
    └── migrations/0001…0002
```

And you established five facts the rest of the course stands on:

- **Config that fails at import beats config that fails in production.**
- **`AUTH_USER_MODEL` is a day-one decision**, and you have seen the exact
  exception you get for deferring it.
- **The ORM's default is N+1**, `select_related` is a JOIN, and `.values()` beats
  both when you only need data — a 77× query reduction you measured.
- **WSGI's concurrency limit is OS threads; ASGI's is memory.** 10 requests in
  20 s versus 500 in 2.6 s, on the same machine, with the same code path.
- **Sync work under ASGI is not free** — it queues on a bounded thread pool, and
  sync ORM calls from async code raise `SynchronousOnlyOperation` deliberately.

Now do [`challenge.md`](./challenge.md).

Then: [Module 03 — Real-Time Transports on the Wire](../03-realtime-transports/),
which uses this exact project to build polling, long-poll, SSE and a raw
WebSocket side by side — and then
[Module 04](../04-channels-chat-single-node/), where the `chat` app becomes a
chat server and those four independent worker processes become a wall.
