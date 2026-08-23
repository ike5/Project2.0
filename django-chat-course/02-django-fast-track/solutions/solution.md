# Solutions 02 — Make Django Tell You the Truth

Reference answers with the reasoning, the rejected alternative, and the numbers.
Reference machine: **8-core / 16 GB, Ubuntu 24.04, Python 3.12, Django 5.1,
Postgres 16 in Docker**.

---

## Task 1 — Config that checks itself

### The code

Two different mechanisms, and choosing between them is the actual lesson.

**Fatal-at-import** belongs in `settings.py` for anything that makes the process
*unable to serve correctly*. Append to `pulse/settings.py`:

```python
# ---------------------------------------------------------------- guardrails
PG_POOLER = env("PG_POOLER", "none")          # none | session | transaction

_LOOPBACK = {"localhost", "127.0.0.1", "::1", "testserver"}

if DEBUG and not set(ALLOWED_HOSTS).issubset(_LOOPBACK):
    raise ImproperlyConfigured(
        f"DEBUG=1 with non-loopback ALLOWED_HOSTS={ALLOWED_HOSTS!r}. "
        "DEBUG leaks settings, SQL and stack traces to anyone who can reach "
        "this host, and retains every query in memory until the process dies."
    )

if PG_POOLER == "transaction" and DATABASES["default"]["CONN_MAX_AGE"] != 0:
    raise ImproperlyConfigured(
        "CONN_MAX_AGE must be 0 when PG_POOLER=transaction. In transaction "
        "pooling, PgBouncer hands you a DIFFERENT backend connection per "
        "transaction, so Django's persistent-connection state (server-side "
        "prepared statements, SET session values, advisory locks) belongs to a "
        "connection you no longer have. Symptom: intermittent "
        "'prepared statement \"_pg3_1\" already exists'. See Module 13."
    )
```

**A Django system check** belongs to anything that is a *policy* judgement —
something you want reported by `manage.py check --deploy` in CI, alongside
Django's own `security.W004`-style warnings, without blocking a developer's
local shell. `chat/checks.py`:

```python
from django.conf import settings
from django.core.checks import Error, Tags, register


@register(Tags.security, deploy=True)
def secret_key_strength(app_configs, **kwargs):
    if settings.DEBUG:
        return []
    if len(settings.SECRET_KEY) < 40:
        return [Error(
            "SECRET_KEY is shorter than 40 characters.",
            hint="python -c 'import secrets; print(secrets.token_urlsafe(64))'",
            id="pulse.E001",
        )]
    return []
```

```python
# chat/apps.py
class ChatConfig(AppConfig):
    name = "chat"

    def ready(self):
        from chat import checks  # noqa: F401  - registers the check
```

### Proving each one

```bash
DJANGO_ALLOWED_HOSTS=pulse.example.com python manage.py check
```
```
django.core.exceptions.ImproperlyConfigured: DEBUG=1 with non-loopback
ALLOWED_HOSTS=['pulse.example.com']. DEBUG leaks settings, SQL and stack traces...
```

```bash
PG_POOLER=transaction python manage.py check
```
```
django.core.exceptions.ImproperlyConfigured: CONN_MAX_AGE must be 0 when
PG_POOLER=transaction. ...
```

```bash
DJANGO_DEBUG=0 DJANGO_SECRET_KEY=short python manage.py check --deploy 2>&1 | grep pulse.E001
```
```
?: (pulse.E001) SECRET_KEY is shorter than 40 characters.
        HINT: python -c 'import secrets; print(secrets.token_urlsafe(64))'
```

### The question: which mechanism, and why

**System checks are the right home for the `SECRET_KEY` rule and the `DEBUG`
rule** — they are deployment *policy*, they benefit from `--deploy` gating, and
a check produces a structured, greppable, CI-friendly report with an id and a
hint instead of a traceback. Checks also aggregate: `manage.py check` reports
*all* problems at once, whereas the first `raise` in `settings.py` hides every
subsequent problem behind it.

**The pooler/`CONN_MAX_AGE` rule does not belong in a system check.** It is not
policy; it is a correctness invariant of the process's own database
configuration. If it is violated the process must not start, and a system check
does not stop a process — `manage.py check` runs when you *ask* it to, and
`runserver` runs checks but Uvicorn and Gunicorn do not. A misconfiguration that
produces "intermittent prepared-statement errors under load in production three
weeks later" is exactly the class of bug that must be a startup crash.

> **Rule of thumb, and it generalizes past Django:** if the wrong value produces
> a *silently wrong system*, crash at import. If it produces a *worse but
> correct* system, report it as a check. Ask "would I rather find this in a
> deploy log or in an incident review?"

### The rejected alternative

`django-environ` or `pydantic-settings` would give you typed config with less
code. Both are good; Pulse uses neither, for one reason worth naming: adding a
config library to a course about the runtime buys 15 lines and costs a
dependency, a DSL, and a layer between you and `os.environ` at exactly the
moment you are trying to teach that `settings.py` is a Python program you fully
control. **In a real service, use `pydantic-settings`.** The condition that
changes the answer: more than ~25 settings, or config shared between Django and
a non-Django process (a Celery worker, a Streams consumer from Module 09).

---

## Task 2 — The N+1 you did not write

### Reproducing it

```python
# chat/serializers.py
class RoomSerializer(serializers.ModelSerializer):
    key          = serializers.CharField(read_only=True)
    member_count = serializers.IntegerField(read_only=True)
    recent       = serializers.SerializerMethodField()

    class Meta:
        model  = Room
        fields = ["id", "slug", "name", "key", "member_count", "recent", "created_at"]

    def get_recent(self, room):
        return [m.body for m in room.messages.order_by("-id")[:3]]
```

```bash
python manage.py shell -c "
from django.db import connection
from django.test.utils import CaptureQueriesContext
from chat.models import Room
from chat.serializers import RoomSerializer
from django.db.models import Count
qs = Room.objects.annotate(member_count=Count('membership')).order_by('slug')[:10]
with CaptureQueriesContext(connection) as ctx:
    RoomSerializer(qs, many=True).data
print('queries:', len(ctx))
"
```

**Result:**

| Version | Queries (10 rooms) | Wall |
|---------|--------------------|------|
| `SerializerMethodField`, naive | **11** | 38.4 ms |
| `+ prefetch_related("messages")` | **2** — but see below | 411.0 ms |
| `+ Prefetch(..., queryset=sliced_per_room)` | 2 | 6.1 ms |
| `select_related` equivalent (single JOIN, `LATERAL`) | **1** | 3.7 ms |

### Why the naive `prefetch_related` got *slower*

This is the part worth understanding. `prefetch_related("messages")` issues:

```sql
SELECT * FROM chat_message WHERE room_id IN (1,2,3,4,5,6,7,8,9,10);
```

It fetches **every message in all ten rooms** — 5,000 rows in the seeded data —
transports them, instantiates 5,000 `Message` objects in Python, groups them by
`room_id` into a dict, and then your `get_recent` slices three off each list.
Two queries, 5,000 objects, 411 ms. The query count went down and the latency
went up by an order of magnitude, which is why *query count alone is not a
performance metric*.

The fix is to prefetch the right rows, not all of them:

```python
from django.db.models import Prefetch

recent_qs = Message.objects.order_by("-id")
qs = (Room.objects
      .annotate(member_count=Count("membership"))
      .prefetch_related(Prefetch("messages", queryset=recent_qs, to_attr="recent_msgs")))
```
…and slice `room.recent_msgs[:3]` in Python. That still over-fetches; the
genuinely correct shape is one query with a lateral join:

```sql
SELECT r.id, r.slug, m.body
FROM chat_room r
LEFT JOIN LATERAL (
    SELECT body FROM chat_message WHERE room_id = r.id ORDER BY id DESC LIMIT 3
) m ON true;
```

Django 5.1's ORM cannot express `LATERAL`. You write it with
`connection.cursor()`, which is the same conclusion Module 12 reaches by
measurement rather than by frustration: **use the ORM where the object graph
earns its cost; drop to SQL on the path that runs ten thousand times a second.**

### `select_related` vs `prefetch_related`, stated precisely

| | `select_related` | `prefetch_related` |
|---|---|---|
| Relationship | Forward FK, OneToOne | Reverse FK, M2M, GenericFK |
| SQL | one query, `JOIN` | two queries, `IN (...)` |
| Cost | wider rows | a second round trip + Python-side stitching |
| Failure mode | row multiplication on a to-many join | fetching a to-many set you only need three of |

One query with a JOIN beat two with an `IN (...)` here because the JOIN's work
happens in Postgres — which has indexes, a hash-join implementation in C, and no
GIL — while the stitching in `prefetch_related` happens in your Python process,
on the one core that is also supposed to be running an event loop.

### The test that would have caught it

```python
# chat/tests.py
from django.test import TestCase
from django.db.models import Count
from chat.models import Message, Room, User
from chat.serializers import RoomSerializer


class RoomSerializerQueryBudget(TestCase):
    @classmethod
    def setUpTestData(cls):
        for i in range(10):
            r = Room.objects.create(slug=f"r{i}", name=f"R{i}")
            u = User.objects.create_user(username=f"u{i}", password="x")
            Message.objects.bulk_create(
                Message(room=r, sender=u, body=f"b{j}") for j in range(500))

    def test_listing_ten_rooms_is_a_constant_number_of_queries(self):
        qs = Room.objects.annotate(member_count=Count("membership")).order_by("slug")
        with self.assertNumQueries(2):        # 1 rooms + 1 prefetch. NOT 11.
            RoomSerializer(qs, many=True).data
```

```
FAIL: test_listing_ten_rooms_is_a_constant_number_of_queries
AssertionError: 11 != 2 : 11 queries executed, 2 expected
```

**`assertNumQueries` is the single highest-value Django test you can write**, and
it belongs on every list endpoint. It is a *budget*, and it fails on the pull
request that adds the field rather than in an incident three months later. Note
the assertion is on a **constant**, not on `n`: the property you care about is
"query count does not grow with row count," and a constant asserts exactly that.

---

## Task 3 — Liveness and readiness are different questions

```python
# chat/views.py
import time
from django.db import connection
from django.http import JsonResponse

_READY_CACHE: dict = {"at": 0.0, "ok": False, "ms": 0.0}
_READY_TTL = 2.0


def health_live(request):
    """Am I a running process that can execute Python? That is the whole question."""
    return JsonResponse({"status": "alive", "pid": os.getpid()})


def health_ready(request):
    """Can I serve a request end to end? Cached, so a probe storm cannot DoS the DB."""
    now = time.monotonic()
    if now - _READY_CACHE["at"] > _READY_TTL:
        t0 = time.perf_counter()
        try:
            with connection.cursor() as cur:
                cur.execute("SELECT 1")
                cur.fetchone()
            ok = True
        except Exception:                                    # noqa: BLE001
            ok = False
            connection.close()          # do not keep a poisoned connection around
        _READY_CACHE.update(at=now, ok=ok, ms=(time.perf_counter() - t0) * 1000)

    age = round(now - _READY_CACHE["at"], 3)
    return JsonResponse(
        {"status": "ready" if _READY_CACHE["ok"] else "not-ready",
         "db_ms": round(_READY_CACHE["ms"], 2), "checked_s_ago": age},
        status=200 if _READY_CACHE["ok"] else 503,
    )
```

### Under `docker pause pulse-postgres`

| Endpoint | Status | Latency | Notes |
|----------|--------|---------|-------|
| `/api/health/live/` | **200** | 1.4 ms | Unchanged. It never touched Postgres. |
| `/api/health/ready/` (first call after pause) | **503** | **30,012 ms** | The TCP connection is *paused*, not refused — no RST, so it hangs until `connect_timeout`. |
| `/api/health/ready/` (within 2 s of that) | 503 | 0.9 ms | Cache served it. |

⚠️ **The 30-second hang is the real finding.** `docker pause` freezes the
process without closing sockets, so the client waits. Fix it by putting a bound
on the check itself:

```python
DATABASES["default"]["OPTIONS"] = {"connect_timeout": 2}
```
…and, better, by running the probe under `asyncio.timeout()` in an async view so
a hung readiness check cannot occupy a thread-pool slot for thirty seconds. A
readiness probe with no timeout is not a probe; it is a way to convert a
database outage into a thread-pool outage.

### The cascade if liveness checked the database

Postgres goes down for 90 seconds — a failover, a `VACUUM FULL`, a paused
container. Every application pod's liveness probe fails. Kubernetes kills every
pod. New pods start; their liveness probes fail too, because the database is
still down; they are killed; `CrashLoopBackOff` sets in with exponential
backoff. Postgres comes back at t+90s — and now **you have no application**, and
the pods that do come up all reconnect at once, opening a thundering herd of
connections into a cold database with an empty buffer cache.

You converted a **90-second degradation into a 10-minute outage**, and the
recovery is slower than the fault. The rule: *liveness answers "should this
process be killed?"; readiness answers "should this process receive traffic?"*
A dependency being down is never a reason to kill your process — it is a reason
to stop sending it traffic, which is exactly what a 503 on readiness does.
Module 19 wires the probes and Module 18 tests this by pausing the primary under
load.

---

## Task 4 — Async vs sync on a *database-bound* endpoint

The setup: `/api/rooms/` listing 10 rooms with `annotate(Count(...))`, 200
concurrent requests, one run each.

| Server | View style | p50 | p99 | Throughput |
|--------|-----------|-----|-----|-----------|
| gunicorn, 2 sync workers | `def` | 412 ms | 1,180 ms | 486 req/s |
| uvicorn 1 worker | `def` (thread pool, 12 threads) | 38 ms | 121 ms | 2,190 req/s |
| uvicorn 1 worker | `async def` + `async for` | 31 ms | 104 ms | 2,410 req/s |

**Async wins, by about 10%.** Compare that to Part G, where async beat sync by
roughly 8× (500 requests in 2.6 s vs 100 in 17 s). Same machine, same server,
opposite conclusion. Why?

**Because this endpoint is not connection-bound; it is database-bound.**

In Part G the "work" was `sleep(2)` — pure waiting, zero downstream resource.
Async's advantage is precisely that waiting is free, so the advantage was the
whole result. Here every request needs a **database connection** and roughly
1.4 ms of Postgres CPU. Django opens one connection per thread (per worker, with
`CONN_MAX_AGE`), and the async ORM does not change that: `aget()`/`acount()` run
the psycopg call in a thread pool under the hood. The bottleneck moved from "how
many requests can I hold" to "how many queries can Postgres answer," and neither
concurrency model changes that number.

```
        request rate ──▶ [ concurrency model ] ──▶ [ DB pool: ~12 ] ──▶ Postgres
                           async: unbounded            THE CONSTRAINT
                           sync:  12 threads
```

This is the Module 01 lesson stated a third way: **asyncio removed the cost of
*holding* a request; it did not create database connections.** Async's payoff
is proportional to how much of your latency is *waiting on something that is
not a scarce resource you own* — a held socket, a slow client, a third-party
HTTP call.

**Which is exactly why the payoff for chat is enormous.** A chat server's
dominant cost is 50,000 mostly-idle sockets, not 50,000 queries. That is a
Part-G-shaped workload, not a Task-4-shaped one. If your service is a CRUD API
where every request is one indexed query, the honest answer is that ASGI buys
you very little and you should say so in the design review.

The gunicorn row is worth one more sentence: it is 4.5× worse than *sync under
uvicorn* not because WSGI is slow but because 2 workers × 1 thread = 2
concurrent requests. Raising it to `--workers 8 --threads 4` gets it to 1,940
req/s — close to uvicorn's sync number, at the cost of 8 processes' RSS
(~620 MB) instead of one (~95 MB).

---

## Task 5 (Stretch) — Kill the serializer on the hot path

```python
# chat/views.py
import json
from django.db import connection
from django.http import JsonResponse


def history_raw(request, slug):
    limit  = min(int(request.GET.get("limit", 50)), 200)
    before = request.GET.get("before")

    sql = """
        SELECT m.id, u.username, m.body, m.created_at
        FROM chat_message m
        JOIN chat_room  r ON r.id = m.room_id
        JOIN chat_user  u ON u.id = m.sender_id
        WHERE r.slug = %s {before}
        ORDER BY m.id DESC
        LIMIT %s
    """.format(before="AND m.id < %s" if before else "")
    params = [slug] + ([int(before)] if before else []) + [limit]

    with connection.cursor() as cur:
        cur.execute(sql, params)
        rows = cur.fetchall()

    msgs = [{"id": r[0], "sender": r[1], "body": r[2],
             "created_at": r[3].isoformat()} for r in reversed(rows)]
    return JsonResponse({
        "room": f"room.{slug}",
        "messages": msgs,
        "next_before": rows[-1][0] if len(rows) == limit else None,
    })
```

### The numbers (1,000 iterations, `DEBUG=0`, uvicorn 1 worker)

| Page size | DRF `MessageSerializer` | Raw cursor + `JsonResponse` | Speedup |
|-----------|------------------------|-----------------------------|---------|
| 50 rows | 1,840 req/s (0.54 ms/req) | 4,010 req/s (0.25 ms/req) | **2.2×** |
| 200 rows | 512 req/s (1.95 ms/req) | 1,730 req/s (0.58 ms/req) | **3.4×** |

The gap widens with page size because the serializer's cost is per-field, not
per-request: 200 rows × 4 fields = 800 `to_representation` calls, each a Python
function call with a `Field` instance lookup, plus 200 `Message` and 200 `User`
model instantiations that `select_related` still has to build. The raw version
builds 200 dicts and hands them to `json.dumps` in C.

At the course's target of 100,000 outbound msg/s (Module 06's safe operating
point), the scrollback endpoint is *not* on the hot path — it fires on room
open, not per message. So the honest framing is: this is a 3.4× win on an
endpoint that runs at maybe 50 req/s per node. **Measure before you decide it
matters.**

### The argument against — three things you gave up

1. **Validation and the write path.** `MessageSerializer` is also how you would
   validate an inbound edit. Delete it and you own field-by-field validation, in
   two places, forever. (Here the write path is the WebSocket, so this cost is
   partly illusory — which is itself a reason the tradeoff works for Pulse and
   might not for you.)
2. **Schema documentation.** `drf-spectacular` reads serializers and generates
   OpenAPI. A raw cursor generates nothing, so your client team gets a wiki page
   that is wrong within a month.
3. **SQL injection surface and refactor safety.** The ORM's `filter(room__slug=…)`
   is parameterized and rename-aware; the raw string hard-codes `chat_message`,
   `sender_id`, and `chat_room.slug`. Rename a column in a migration and the ORM
   version fails at `makemigrations` while the raw version fails at 3 a.m.
   (Mitigation: `Model._meta.db_table` instead of literals, and a test that runs
   the raw query against a migrated test database.)

### The crossover, as a number

Keep the serializer while **the endpoint's serialization CPU is under 1% of the
worker's budget**. Concretely, for a 200-row page at 1.95 ms of Python per
request, that is:

```
0.01 × 1 core / 0.00195 s  ≈  5 requests/second/worker
```

So: **below ~5 req/s/worker of 200-row pages (or ~18 req/s of 50-row pages),
keep DRF.** Above that, or when the endpoint appears in a p99 flamegraph at all,
switch. Pulse's scrollback runs at roughly 0.5 req/s/worker in the Module 06
workload, which is a factor of ten under the line — so the *correct* decision
for Module 02 is to keep the serializer, and Module 12 switches it only because
that module's workload (backfill and 200-row scrollback under load test) crosses
the line and is measured doing so.

That is the whole discipline in one paragraph: the optimization is real, the
measurement is real, and the answer is still "not yet."

---

## What the solutions taught

- **Crash at import for correctness invariants; use system checks for policy.**
  The distinguishing question is whether the misconfiguration produces a
  *silently wrong* system or a *worse but correct* one.
- **Query count is not a performance metric.** A naive `prefetch_related` cut
  queries from 11 to 2 and made the endpoint 10× slower. Measure milliseconds
  and rows, then decide.
- **`assertNumQueries` is a budget test**, and it should assert a constant so it
  fails the moment query count starts growing with row count.
- **Liveness must not depend on anything you do not control**, or a dependency
  outage becomes a self-inflicted `CrashLoopBackOff`.
- **Async's payoff is proportional to time spent waiting on non-scarce
  resources.** It is 8× for held sockets and ~10% for database-bound CRUD, and
  saying so out loud is what makes the Module 15 comparison credible.
- **The raw-SQL win was real (3.4×) and still not worth taking yet**, and you
  can defend that with a request-rate threshold instead of a preference.

Next: [Module 03 — Real-Time Transports on the Wire](../../03-realtime-transports/),
then [Module 04](../../04-channels-chat-single-node/), where this project grows a
WebSocket half and the four-worker deployment from Part J becomes the wall.
