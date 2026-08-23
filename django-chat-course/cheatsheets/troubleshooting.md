# Cheatsheet — Troubleshooting Decision Trees (Django / Channels / asyncio)

Symptom → cause → fix. Work top to bottom; the first matching branch is usually
right. Everything here is Python-specific or Python-flavoured — the generic
distributed-systems trees are in [`docker-ha.md`](./docker-ha.md) and the storage
ones in [`postgres-scale.md`](./postgres-scale.md).

**Before anything else, three commands:**

```bash
PYTHONASYNCIODEBUG=1 uvicorn pulse.asgi:application --workers 1   # names blocking calls
curl -s localhost:8000/metrics | grep -E 'chat_event_loop_lag|chat_connections_active'
py-spy dump --pid $(pgrep -f 'uvicorn pulse.asgi' | head -1)      # what is the loop doing NOW
```

`py-spy` is this course's `jstack`. It attaches to a *running* process without
restarting it and prints every thread's Python stack — including the event-loop
thread, which is the one you care about. Install it (`pip install py-spy`) before
you need it, not during the incident.

---

## 0. The three exceptions you will actually see

### `SynchronousOnlyOperation: You cannot call this from an async context`

```
django.core.exceptions.SynchronousOnlyOperation: You cannot call this from an
async context - use a thread or sync_to_async.
```

**What it means:** you touched the synchronous Django ORM from inside a coroutine
running on the event loop. Django *detects* this and refuses, on purpose.

**This exception is a gift.** It is Django saving you from the Module 15 disaster
— a blocking database call on the loop that stalls every connection on the
worker. It is not a bug to work around; it is a design rule being enforced.

```python
# WRONG — the ORM is synchronous
async def receive_json(self, content):
    Message.objects.create(room_id=self.room, body=content["body"])

# RIGHT (a) — Django's native async ORM (4.1+), preferred for simple queries
    msg = await Message.objects.acreate(room_id=self.room, body=content["body"])
    exists = await Membership.objects.filter(...).aexists()
    async for m in Message.objects.filter(room_id=r)[:50]:
        ...

# RIGHT (b) — the threadpool bridge, for anything not async-aware
from channels.db import database_sync_to_async

    msg = await database_sync_to_async(Message.objects.create)(
        room_id=self.room, body=content["body"])
```

⚠️ **Use `database_sync_to_async`, never plain `sync_to_async`, for ORM work.**
It also closes the thread's database connection afterwards; plain `sync_to_async`
leaks one Postgres connection per threadpool thread and you will hit
`FATAL: sorry, too many clients already` hours later with no obvious cause.

**Where it *doesn't* fire, and that's the danger:** raw `psycopg` cursors, a
third-party client, `requests`, `time.sleep`, `hashlib.pbkdf2_hmac`, a
catastrophic regex. Django can't see those. They block just as hard and raise
nothing. That is what `PYTHONASYNCIODEBUG=1` and `flake8-async` are for.

### `SynchronousOnlyOperation` from a *sync* consumer or a Celery task

Same exception, opposite cause: you're in synchronous code but an async context
is active up the stack (a `sync_to_async` wrapper, a `JsonWebsocketConsumer`
handler that Channels runs on the threadpool inside a loop). Wrap the *async*
call instead:

```python
from asgiref.sync import async_to_sync
async_to_sync(self.channel_layer.group_send)(room, {"type": "chat.message", ...})
```

### `RuntimeError: You cannot use AsyncToSync in the same thread as an async event loop`

You called `async_to_sync(...)` from code already running on the loop. The fix is
to stop bouncing: if you're in async code, `await` the coroutine directly.

```
Is the code you're in `async def`?
├─ yes → just `await` it. Delete the async_to_sync.
└─ no  → is a loop running in this thread?
    ├─ yes (you're inside sync_to_async / a sync consumer)
    │      → async_to_sync is correct HERE; asgiref runs it on the outer loop
    └─ no  (a Celery task, a management command, a DRF sync view)
           → async_to_sync is correct and will spin up a loop
```

---

## 1. WebSocket connections fail or drop

```
Handshake never returns 101
├─ Nothing in the server log at all?
│   └─ You are running WSGI. `runserver` without `channels` in INSTALLED_APPS,
│      or gunicorn with a sync worker, cannot upgrade. Run an ASGI server:
│        uvicorn pulse.asgi:application --loop uvloop
├─ 403 at the proxy?
│   ├─ nginx: missing `proxy_http_version 1.1`      -> add it
│   ├─ nginx: missing Upgrade/Connection headers    -> add the `map` block
│   └─ Channels: OriginValidator rejected it
│      log: "Rejected WebSocket from disallowed origin: http://…"
│      -> add the origin, or you just watched CSWSH protection work (Module 21)
├─ 500 with "ValueError: Django can only handle ASGI/HTTP connections, not websocket"?
│   └─ Your ProtocolTypeRouter has no "websocket" key, or asgi.py exports the
│      plain get_asgi_application() instead of the ProtocolTypeRouter.
├─ 404?
│   └─ Path mismatch. Channels re_path patterns are matched WITHOUT the leading
│      slash in some setups and with it in others — log `scope["path"]` and look.
└─ 4401/4403 close immediately after 101?
    └─ Your own auth (Module 21): expired/consumed ticket, or ticket/JWT
       identity mismatch. Working as designed.

Connects, then dies after a fixed interval
├─ ~60s, very consistent   -> nginx `proxy_read_timeout` (default 60s). Raise it.
├─ ~30-120s behind a cloud LB -> LB idle timeout. Raise it AND send app-level pings.
└─ Random, mobile clients  -> NAT idle eviction. Heartbeat every 15-30s.

Connects, dies under load only
├─ OSError: [Errno 24] Too many open files
│   -> ulimit -n on the container AND the host. One socket = one FD.
├─ Close code 1009  -> frame exceeded the size limit. Uvicorn: --ws-max-size.
├─ Close code 1011  -> an unhandled exception in your consumer. Read the traceback.
├─ Close code 1006 en masse -> the worker died or was hard-killed (no close frame).
│   -> check for OOM: `dmesg | grep -i oom`, and see tree 3.
└─ Connections stop being ACCEPTED around 28,000, from one load generator
    -> ephemeral ports on the CLIENT, not a server ceiling (Module 06).

Everything works with 1 worker, breaks with --workers 8
└─ THE Module 04 wall. See tree 2.
```

---

## 2. Messages vanish between two connected clients

```
Both clients connected, sender sees its own echo, receiver gets nothing
├─ Running more than one worker PROCESS with the InMemoryChannelLayer?
│   ** THIS IS THE MODULE 04 WALL AND IT IS THE #1 CAUSE. **
│   The in-memory layer's groups are a plain dict in ONE process's heap.
│   Worker 0 and worker 3 share NO memory. There is no code that could join
│   them. Two workers on ONE machine already cannot deliver to each other.
│   -> settings: CHANNEL_LAYERS -> channels_redis. Not optional. Not "later".
│      Confirm which layer you're on:
│        python -c "from channels.layers import get_channel_layer; print(get_channel_layer())"
│      InMemoryChannelLayer in anything but a single-process test = broken.
├─ Group name mismatch
│   -> Channels group names allow only [A-Za-z0-9_.-] and max 100 chars.
│      A room id with a ':' or a space silently never matches. Log both sides.
├─ The consumer has no handler method for the event `type`
│   -> group_send({"type": "chat.message"}) dispatches to `chat_message`.
│      Dots become underscores. No method = the message is DROPPED, and in
│      older Channels it's a silent drop with a log line you're not reading:
│        "No handler for message type chat.message"
└─ You called group_add AFTER accept() and the first message raced it
    -> group_add before accept(), or buffer until subscribed.

Messages lost only around a reconnect / a Redis blip
└─ You're on the Pub/Sub channel layer. This is AT-MOST-ONCE — working as
   designed (Module 07 measures ~15% loss on a `docker pause`).
   -> Module 09: a Streams-backed layer + consumer groups + a resume cursor.

Messages lost only under load
├─ ChannelFull raised, or group_send silently dropping
│   -> The channel layer has a per-channel `capacity` (default 100) and
│      `expiry` (default 60s). A slow consumer's channel fills; further sends
│      to it are dropped. Raise capacity, or fix the slow consumer — the
│      backpressure is telling you something true.
├─ Redis `evicted_keys` > 0 in INFO stats
│   ** With maxmemory-policy allkeys-lru, Redis SILENTLY deletes your sequence
│      counters, presence keys and stream entries. This is why the course pins
│      `noeviction` (see infra/compose.dev.yml). **
│   -> raise maxmemory, trim streams (XTRIM MAXLEN ~), keep noeviction.
└─ Consumer crashed mid-batch, entries stuck in the PEL
   -> XPENDING to confirm, XAUTOCLAIM to recover (Module 09).

Persisted but never delivered (or delivered but never persisted)
└─ Classic dual-write. -> transactional outbox + Celery relay (Module 13).

"Lost" but actually just out of order
└─ Client rendered by arrival time. -> order by `seq` client-side and detect
   gaps by sequence number (Modules 05/10).
```

---

## 3. Latency is bad, or one worker is frozen

This is the tree that separates Python from every other runtime. **In an async
worker, one slow synchronous call does not slow one request — it freezes every
connection that process holds.**

```
p50 fine, p99 terrible
├─ chat_event_loop_lag_seconds elevated?
│   ** The loop is the bottleneck. Find what's on it. **
│   -> PYTHONASYNCIODEBUG=1 and look for:
│        WARNING asyncio Executing <Task ... receive_json()> took 0.612 seconds
│   -> py-spy dump --pid <worker>: the loop thread's stack IS the culprit
│   -> py-spy record -o flame.svg --pid <worker> --duration 30
├─ Threadpool saturated (sync consumers, or lots of database_sync_to_async)?
│   -> default executor is min(32, cpu+4) = 12 on an 8-core box.
│      Symptom: CPU idle, p99 climbing, everything queued.
│      -> ASGI_THREADS / set a wider executor, AND bound admission with a
│         Semaphore. Widening alone just moves the queue (Module 01 Part F).
├─ DB connection pool wait
│   -> see tree 4.
└─ A slow Redis command
    -> redis-cli SLOWLOG GET 10; INFO commandstats. Look for KEYS, SMEMBERS,
       LRANGE on a big key (Module 08).

Everything on ONE worker is slow; other workers are fine
└─ That worker's loop is blocked. Classic causes, in frequency order:
     1. an un-wrapped ORM call (the cardinal sin)
     2. `requests`/`urllib` instead of `httpx`/`aiohttp`
     3. `time.sleep` instead of `asyncio.sleep`
     4. a big `json.loads`/`json.dumps` on the loop (a 10 MB frame)
     5. bcrypt/pbkdf2/argon2 password hashing inline in a consumer
     6. a catastrophically-backtracking regex on user content
     7. reading a file synchronously (`open().read()`) on the loop
   -> All seven are the same bug. All seven are also a DoS primitive if user
      input can steer you into them (Module 21).

Everything is uniformly slow
├─ One worker per core? `--workers $(nproc)`. One worker on 8 cores uses 1 core.
├─ uvloop actually on?
│     python -c "import asyncio,uvloop; uvloop.install(); print(type(asyncio.new_event_loop()))"
│     -> <class 'uvloop.Loop'>.  Not on = ~20% left on the table for one flag.
├─ redis-cli --latency > 1ms on loopback -> Redis or the host is saturated
└─ CPU pinned at 100% of ONE core per worker
    -> You are at the wall. The GIL means no tuning inside Python moves it.
       Fewer messages, or more processes (Module 06/07).

Latency grows over time, resets on restart
└─ A leak. Graph, in this order: chat_connections_active vs RSS, channel-layer
   group sizes, XPENDING depth, and any dict that isn't cleaned on disconnect.
   See tree 5.

Fine with 1 node, bad with 3
├─ Every node subscribes to every room -> shard subscriptions
├─ Redis is now the bottleneck -> INFO stats ops/sec; consider Cluster
└─ The cross-node hop added a round trip -> expected: ≈ +4 ms p50 (Module 07).
   Measure, don't panic.
```

### Naming the blocking call, three ways

```bash
# 1. asyncio debug mode — the cheapest. Turn it on in dev and CI, permanently.
PYTHONASYNCIODEBUG=1 uvicorn pulse.asgi:application --workers 1
#    WARNING asyncio Executing <Handle ...> took 0.612 seconds

# 2. py-spy on a LIVE process — no restart, works in prod
py-spy dump --pid 12841                    # instant stacks
py-spy top --pid 12841                     # live "which function is hot"
py-spy record -o flame.svg --pid 12841 --duration 30

# 3. static analysis, in CI, before it ships
pip install flake8-async
flake8 --select=ASYNC chat/
#    chat/consumers.py:41:9: ASYNC101 blocking sync call in async function
```

> `PYTHONASYNCIODEBUG=1` is this course's BlockHound. It is not a tool you reach
> for when something is wrong — it is the thing that makes "never block the loop"
> enforceable *before* something is wrong. It also costs real throughput, so:
> dev and CI yes, production no.

---

## 4. Database connection problems

```
FATAL: sorry, too many clients already
├─ Using plain sync_to_async for ORM work instead of database_sync_to_async?
│   ** Each threadpool thread opens a connection and never closes it. **
│   -> database_sync_to_async closes it. Switch, everywhere.
├─ CONN_MAX_AGE > 0 with many workers?
│   -> workers × threads × CONN_MAX_AGE-persistent connections > max_connections.
│      Behind PgBouncer, set CONN_MAX_AGE = 0 and let PgBouncer pool.
└─ Celery workers counted too? They have their own connections. Add them up:
     (uvicorn workers × threadpool) + (celery workers × concurrency) + admin

prepared statement "_pg3_1" already exists   (intermittent, under load only)
└─ psycopg3 + PgBouncer in TRANSACTION pooling mode. Each transaction may land
   on a different server connection, so server-side prepared statements break.
   -> DATABASES[...]["OPTIONS"] = {"prepare_threshold": None}
      (the analog of the JVM's ?prepareThreshold=0)

Queries fine standalone, slow inside the consumer
├─ N+1 across an async loop: `async for` + a related lookup per row
│   -> select_related/prefetch_related, or one query with __in
└─ The query is fine; you're queued behind the threadpool. See tree 3.

"I sent a message, then couldn't see it"
└─ Read-your-writes violation from a lagging replica (Module 13).
   -> route the sender's next reads to the primary briefly, or echo optimistically.

Connections leak until exhaustion, no errors anywhere
└─ An exception escaped a database_sync_to_async block in a way that skipped
   Django's connection cleanup, or you used a raw psycopg connection without a
   context manager. Check:
     SELECT state, count(*) FROM pg_stat_activity GROUP BY state;
   Lots of `idle in transaction` = a transaction you never committed or rolled
   back, and it also blocks VACUUM. Find it:
     SELECT pid, now()-xact_start AS age, query FROM pg_stat_activity
      WHERE state='idle in transaction' ORDER BY age DESC;
```

---

## 5. Memory grows until the container is OOM-killed

```
RSS grows with connection count, linearly
└─ Normal. Measure BYTES PER CONNECTION = RSS ÷ chat_connections_active.
   Pinned reference: ≈45 KB/conn (async Channels), ≈28 KB (raw ASGI),
   ≈120 KB (sync consumers). Much above 45 KB = look for per-consumer state.

RSS grows while connection count is FLAT
├─ A registry never cleaned on disconnect
│   ** The #1 chat memory bug. ** A room dict that keeps an EMPTY set per room
│   leaks one set per DM conversation, forever.
│   -> delete the key when the last member leaves; assert len(registry)==0 in a
│      churn test (Module 01's challenge exists for this).
├─ Channel-layer groups holding dead channels
│   -> group_discard in disconnect(), and rely on group_expiry as a backstop.
│      Check: redis-cli --scan --pattern 'asgi:group:*' | head
│             redis-cli ZCARD asgi:group:room.7
├─ Slow consumers accumulating outbound buffers
│   -> a client that never reads makes `await send()` never drain. Bound it:
│      wrap sends in asyncio.wait_for and close the socket on timeout.
├─ A dedup/seen cache with no eviction
│   -> bounded window: a deque + a set, or cachetools.TTLCache.
└─ Tasks created and never awaited
   -> `asyncio.create_task` without keeping a reference: the task may be GC'd
      mid-flight (a real asyncio footgun), or accumulate. Keep a set:
        self._tasks.add(t); t.add_done_callback(self._tasks.discard)
      Count them:  len(asyncio.all_tasks())

Redis memory grows forever
├─ Streams never trimmed        -> XADD ... MAXLEN '~' 10000  (the ~ matters)
├─ Keys without TTL             -> redis-cli --scan | xargs -n1 redis-cli TTL
└─ mem_fragmentation_ratio > 1.5 -> activedefrag yes

Container OOM-killed with no Python traceback
└─ There is no traceback for a cgroup OOM kill; the kernel just removes you.
     dmesg | grep -i 'killed process'
     docker inspect <c> --format '{{.State.OOMKilled}}'
   -> WEB_CONCURRENCY must match the CPU/memory LIMIT, not the host's cores.
      8 workers in a 2 GB container is 8 interpreters in 2 GB.
```

Diagnostics:
```bash
python -X tracemalloc=10 -m uvicorn pulse.asgi:application     # then snapshot in a view
py-spy dump --pid <worker>
pip install pympler        # asizeof for "what is that dict actually costing"
docker stats --no-stream
cat /sys/fs/cgroup/memory.current /sys/fs/cgroup/memory.max
```

```python
# a /debug/objects view worth having in dev
import gc, tracemalloc, asyncio
from collections import Counter
def snapshot():
    return {
        "tasks": len(asyncio.all_tasks()),
        "top_types": Counter(type(o).__name__ for o in gc.get_objects()).most_common(15),
        "tracemalloc": [str(s) for s in tracemalloc.take_snapshot()
                        .statistics("lineno")[:10]],
    }
```

---

## 6. Channels-specific gotchas

```
`self.scope["user"]` is AnonymousUser and you expected a real one
├─ AuthMiddlewareStack not wrapping the URLRouter, or wrapping the wrong side
├─ The session cookie isn't sent (cross-origin) — and this is CSWSH bait anyway.
│  -> Module 21: ticket + first-frame JWT, no cookie on the handshake.
└─ You read scope["user"] in __init__ instead of connect(). Middleware runs
   between them.

`database_sync_to_async` inside a transaction behaves oddly
└─ Each call may run on a DIFFERENT threadpool thread, and Django connections
   are thread-local — so a transaction opened in one call is not visible in the
   next. Wrap the WHOLE transaction in ONE database_sync_to_async function.

Consumer state shared between connections
└─ Class attributes are shared; instance attributes are not. Assign in
   connect(), never at class level:
     class C(AsyncJsonWebsocketConsumer):
         rooms = set()          # WRONG — every connection shares this set
         async def connect(self):
             self.rooms = set() # RIGHT

threading.local() used for request context in an async consumer
** DANGEROUS. ** One thread runs thousands of interleaved connections, so
   thread-local state leaks BETWEEN USERS. Use contextvars.ContextVar.
   Note: a bare `asyncio.create_task` copies the context at creation, so a
   fire-and-forget task started before you set the var will not see it
   (Module 15, challenge task 5).

`await self.close()` doesn't seem to stop the consumer
└─ close() sends the frame; your handler keeps running. `return` after it.

Everything hangs at startup behind `docker compose up`
└─ ASGI lifespan. If your asgi.py wraps ProtocolTypeRouter and doesn't handle
   the "lifespan" scope type, some servers hang waiting for a reply. Handle it
   explicitly, or use `--lifespan off` while you debug.

Tests pass, production drops messages
└─ Tests use InMemoryChannelLayer (single process). Production is multi-worker.
   -> pytest fixture that swaps in channels_redis for integration tests, and at
      least one test that runs two workers.
```

---

## 7. Celery and background work

```
Celery task calls channel_layer.group_send and nothing arrives
├─ Missing async_to_sync — group_send is a coroutine; calling it returns a
│  coroutine object that is never awaited (and Python warns to stderr, which
│  nobody reads):  RuntimeWarning: coroutine 'group_send' was never awaited
│  -> async_to_sync(get_channel_layer().group_send)(group, msg)
└─ The Celery worker points at a DIFFERENT Redis (or DB index) than the app.
   -> print settings.CHANNEL_LAYERS on both sides and compare.

Outbox relay double-delivers after a crash
└─ Expected: at-least-once. Client dedup by clientId absorbs it (Module 05/09).
   Two relays running at once is a different bug — take a lock or a lease.

The relay falls behind and nobody notices
└─ Graph the outbox backlog (unrelayed rows) as a first-class SLI. A relay that
   silently stops looks exactly like "chat is a bit slow today" (Module 20).
```

---

## 8. Docker / Compose

```
"port is already allocated"            -> docker ps -a; docker rm -f <name>
"no space left on device"              -> docker system prune -a --volumes (careful)
Container restart-loops on startup     -> healthcheck start_period too short (use 20s)
depends_on didn't wait                 -> needs `condition: service_healthy`
Config change had no effect            -> docker compose up -d --force-recreate
Stale data after a config change       -> docker compose down -v   (the -v matters)
Can't reach another service            -> use the SERVICE NAME, not localhost
Sentinel container won't start         -> it rewrites its config; can't be read-only
App can reach Redis from the host but not from a container
                                       -> REDIS_URL is redis://localhost — inside
                                          a container that's the container itself
Logs are empty during an incident      -> PYTHONUNBUFFERED=1. Always.
Sockets all die at deploy with code 1006
                                       -> no graceful drain; see docker-ha.md
```

---

## 9. The general method

When nothing in the trees fits:

1. **Reproduce it under load.** Bugs that only appear at scale are queue,
   timeout, or resource bugs. At scale they're reliable; at rest they're ghosts.
2. **Find the layer.** Client → nginx → Uvicorn worker → consumer → channel layer
   → Redis → Postgres. Time each hop (Module 20's traces). Don't guess.
3. **Ask "which process?" before "which line?"** Python's failures are
   process-shaped: one worker frozen, one worker leaking, one Celery worker on
   stale settings. `chat_connections_active{worker=…}` and per-PID CPU answer it
   in seconds and save you an hour of reading the wrong logs.
4. **Graph the queue depths.** Every hang is a queue: the threadpool's, the
   channel layer's `capacity`, PgBouncer's `cl_waiting`, Redis `XPENDING`, the
   outbox backlog.
5. **Compare against a known-good.** Same test, one worker, `InMemoryChannelLayer`,
   no Redis. If that's also slow, the distribution isn't your problem.
6. **Read the logs of the thing that died, not the thing that complained.** The
   consumer logging `ConnectionResetError` is a witness, not a suspect.

---

## Appendix — the one-line diagnosis table

| You see | It is almost always |
|---------|--------------------|
| `SynchronousOnlyOperation` | The ORM on the event loop. Django saved you. |
| Two clients can't see each other, 1 worker fine | `InMemoryChannelLayer` across processes (Module 04) |
| `Executing <Handle> took 0.6 seconds` | A blocking call on the loop (Module 15) |
| `sorry, too many clients already` | `sync_to_async` instead of `database_sync_to_async` |
| `prepared statement "_pg3_1" already exists` | PgBouncer transaction pooling; set `prepare_threshold=None` |
| p99 in seconds, CPU idle | A bounded resource with no admission control (Module 01) |
| ~15% of messages missing after a Redis blip | Pub/Sub is at-most-once. Working as designed (Module 07) |
| Plateau at exactly ~28,000 connections | Load-generator ephemeral ports (Module 06) |
| Everything dies at 1,024 connections | `ulimit -n` |
| All sockets close with 1006 on deploy | No graceful drain (Module 18) |
| Sequence counter vanished, resume storm | Redis eviction. Use `noeviction`. |
| Latency great, users say it's broken | You measured enqueue, not end-to-end delivery |
