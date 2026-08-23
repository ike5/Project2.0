# VERIFY — Confirm Your Environment

Run this **after Module 00** and before Module 01. It takes ~15 minutes and
proves every tool the course depends on actually works on your machine.

If any step fails, fix it now. Debugging your toolchain in Module 18 while three
Redis nodes are mid-failover is not the experience we're going for.

---

## 0. Resource budget

The heavy modules (18, 19, 22) run a lot of containers. Check you have room:

```bash
free -g 2>/dev/null || vm_stat | head -3   # Linux || macOS
docker system df
df -h .
```

**Expected:** at least **16 GB total RAM** (12 GB works with the low-memory path
in Module 00), and **40 GB free disk**.

| Phase | Containers | Approx RAM |
|-------|-----------|-----------|
| 0–1 | postgres, redis | ~1 GB |
| 2 | + redis-2, 2× app (uvicorn) | ~2.5 GB |
| 3 | + replica, pgbouncer, celery, redis-broker | ~4 GB |
| 4 | + kafka (KRaft), cassandra | ~6 GB |
| 5 (Compose HA) | 3× redis + 3× sentinel, 3× patroni, etcd, haproxy, 3× app, nginx | ~9 GB |
| 5 (k8s) | kind, 3 nodes | ~10 GB |

> Python worker processes are cheap at rest but multiply: an 8-worker Uvicorn
> deployment is 8 processes, each with its own interpreter and event loop. The
> per-worker base RSS (~60–90 MB) is why the multi-instance phases add up.

---

## 1. Python 3.12

```bash
python3 --version
```

**Expected:** `Python 3.12.x` or newer.
```
Python 3.12.7
```

⚠️ This course uses `TaskGroup`, `asyncio.timeout()`, and modern typing that need
**3.11+**; 3.12 is what the reference numbers were measured on. If `python3`
reports 3.10 or earlier, install 3.12 (Module 00 covers `pyenv` / `uv`) before
continuing.

Now prove **asyncio** actually runs coroutines concurrently — this is the feature
the whole course leans on (it is this course's answer to "prove virtual threads
work"):

```bash
cat > /tmp/async_check.py <<'EOF'
import asyncio, time

async def work(n):
    await asyncio.sleep(0.5)          # non-blocking sleep — yields to the loop
    return n

async def main():
    t0 = time.perf_counter()
    async with asyncio.TaskGroup() as tg:        # 3.11+ structured concurrency
        tasks = [tg.create_task(work(i)) for i in range(100)]
    dt = time.perf_counter() - t0
    got = sorted(t.result() for t in tasks)
    print(f"ran {len(got)} coroutines concurrently in {dt:.2f}s "
          f"(serial would be {100*0.5:.0f}s)")
    print("loop:", asyncio.get_running_loop().__class__.__module__)

asyncio.run(main())
EOF
python3 /tmp/async_check.py
```

**Expected:** 100 coroutines finish in ~half a second, not 50 seconds — proving
they ran concurrently on one thread:
```
ran 100 coroutines concurrently in 0.50s (serial would be 50s)
loop: asyncio.unix_events
```

✅ If the elapsed time is ~0.5s, your event loop schedules coroutines correctly.
If it's ~50s, something is very wrong with your interpreter.

Now prove **uvloop** installs and swaps in (Module 01 measures it against the
stdlib loop):

```bash
python3 -m pip install --quiet uvloop
python3 - <<'EOF'
import asyncio, uvloop
uvloop.install()
async def main():
    print("loop:", asyncio.get_running_loop().__class__.__module__)
asyncio.run(main())
EOF
```

**Expected:**
```
loop: uvloop
```

✅ `uvloop` (not `asyncio.unix_events`) means the libuv loop is active. On some
distros you may need `python3-dev`/build tools for the wheel; Module 00 notes the
fixes.

---

## 2. Django 5.1 + Channels 4.1

Install into a throwaway virtualenv and confirm the imports and versions:

```bash
python3 -m venv /tmp/verify-venv
/tmp/verify-venv/bin/pip install --quiet "django==5.1.*" "channels==4.1.*" \
    "channels_redis" "daphne" "uvicorn[standard]" "djangorestframework"
/tmp/verify-venv/bin/python - <<'EOF'
import django, channels, channels_redis, daphne, rest_framework
import uvicorn
print("django       ", django.get_version())
print("channels     ", channels.__version__)
print("channels_redis", channels_redis.__version__)
print("daphne       ", daphne.__version__)
print("uvicorn      ", uvicorn.__version__)
# prove the async consumer base class and the channel-layer API import
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.layers import get_channel_layer
print("AsyncJsonWebsocketConsumer OK; get_channel_layer OK")
EOF
```

**Expected:** versions on the `5.1.x` / `4.1.x` lines and the final OK line:
```
django        5.1.x
channels      4.1.x
channels_redis 4.x.x
daphne        4.x.x
uvicorn       0.3x.x
AsyncJsonWebsocketConsumer OK; get_channel_layer OK
```

✅ If `import channels` fails with an ASGI/Django version error, your Django is
too old or too new for Channels 4.1 — pin the versions above.

---

## 3. Docker and Compose v2

```bash
docker --version
docker compose version
docker run --rm hello-world | head -2
```

**Expected:**
```
Docker version 27.x.x, build ...
Docker Compose version v2.29.x
Hello from Docker!
```

Note: `docker compose` (space), not `docker-compose` (hyphen). Compose v1 is
end-of-life and several files in this course use v2-only syntax.

---

## 4. Redis 7

```bash
docker run -d --name verify-redis -p 6379:6379 redis:7-alpine
docker exec verify-redis redis-cli PING
docker exec verify-redis redis-cli INFO server | grep redis_version
```

**Expected:**
```
PONG
redis_version:7.4.1
```

Prove **Streams** exist (Module 09 depends on them) and **RESP3** is available
(Module 08):

```bash
docker exec verify-redis redis-cli XADD verify '*' hello world
docker exec verify-redis redis-cli XLEN verify
docker exec verify-redis redis-cli -3 HELLO 3 | head -4
```

**Expected:** an ID like `1735689600000-0`, then:
```
(integer) 1
```
and a `HELLO 3` reply listing `proto` → `3`.

Clean up:
```bash
docker rm -f verify-redis
```

---

## 5. Postgres 16

```bash
docker run -d --name verify-pg -e POSTGRES_PASSWORD=pulse -p 5432:5432 postgres:16-alpine
sleep 5
docker exec verify-pg psql -U postgres -c "SELECT version();"
```

**Expected:** a line beginning
```
 PostgreSQL 16.x on x86_64-pc-linux-gnu ...
```

Prove **declarative partitioning** works (Module 13 builds on it via `RunSQL`
migrations):

```bash
docker exec verify-pg psql -U postgres -c "
CREATE TABLE t (id bigint, created_at timestamptz) PARTITION BY RANGE (created_at);
CREATE TABLE t_2026_01 PARTITION OF t FOR VALUES FROM ('2026-01-01') TO ('2026-02-01');
INSERT INTO t VALUES (1, '2026-01-15');
SELECT tableoid::regclass AS partition, id FROM t;"
```

**Expected:**
```
 partition | id
-----------+----
 t_2026_01 |  1
```

✅ The row landed in the child table, not the parent. That's partition routing
working — the mechanism Module 13 uses to make retention a `DROP TABLE`.

Clean up:
```bash
docker rm -f verify-pg
```

---

## 6. k6 (WebSocket load testing)

```bash
k6 version
```

**Expected:** `k6 v0.5x.x` or newer.

Prove the WebSocket module is present:

```bash
cat > /tmp/ws-check.js <<'EOF'
import ws from 'k6/ws';
import { check } from 'k6';
export default function () {
  const res = ws.connect('wss://echo.websocket.org', {}, function (socket) {
    socket.on('open', () => { socket.send('ping'); });
    socket.on('message', (m) => { console.log('got: ' + m); socket.close(); });
    socket.setTimeout(() => socket.close(), 3000);
  });
  check(res, { 'handshake was 101': (r) => r && r.status === 101 });
}
EOF
k6 run --vus 1 --iterations 1 /tmp/ws-check.js
```

**Expected:** a summary containing
```
✓ handshake was 101
```

⚠️ If you're offline or behind a proxy that blocks the public echo server, this
step fails on the *network*, not on k6. Module 06 runs everything against your
own local server, so a `k6 version` output alone is sufficient to proceed.

---

## 7. Locust (the Python-native load generator)

Locust matters in this course because it's **Python** — the language you're
already writing — so your load scripts share code and mental model with your app.
Module 06 shows it beside k6 and is honest about its coordinated-omission
behaviour.

```bash
/tmp/verify-venv/bin/pip install --quiet locust
/tmp/verify-venv/bin/locust --version
```

**Expected:** `locust 2.x.x`.

Confirm the WebSocket client library the labs use imports (Locust has no built-in
WebSocket user, so we drive one with `websocket-client`):

```bash
/tmp/verify-venv/bin/pip install --quiet websocket-client
/tmp/verify-venv/bin/python -c "import websocket; print('websocket-client', websocket.__version__)"
```

**Expected:** `websocket-client 1.x.x`.

---

## 8. Node 20+ (for the Next.js client in Module 17)

```bash
node --version
npm --version
```

**Expected:** `v20.x` or newer, npm `10.x` or newer.

---

## 9. `websocat` (manual socket poking)

Used throughout for talking to your server by hand.

```bash
websocat --version
```

**Expected:** `websocat 1.13.x` or similar. Module 00 covers installation; if
you'd rather not install it, every `websocat` step has a `wscat` (npm) or browser
console alternative noted in the lab.

---

## 10. End-to-end smoke test

This starts the whole Phase-1 data tier from
[`infra/compose.dev.yml`](./infra/compose.dev.yml) and confirms the pieces talk to
each other. It is the exact stack Modules 00–12 run against.

```bash
cd django-chat-course/infra
docker compose -p pulse-dev -f compose.dev.yml up -d
docker compose -p pulse-dev -f compose.dev.yml ps
```

**Expected:** both services `running (healthy)`:
```
NAME             IMAGE               STATUS
pulse-postgres   postgres:16-alpine  Up 20 seconds (healthy)
pulse-redis      redis:7-alpine      Up 20 seconds (healthy)
```

Confirm connectivity from your host:

```bash
docker exec pulse-redis redis-cli PING
docker exec pulse-postgres psql -U pulse -d pulse -c "SELECT 1 AS ok;"
```

**Expected:**
```
PONG
 ok
----
  1
```

Confirm the two deliberate settings baked into the dev stack are actually applied
(you'll rely on both later):

```bash
# Redis must NOT evict — it's a transport/state store, losing a key silently is a bug
docker exec pulse-redis redis-cli CONFIG GET maxmemory-policy
# Postgres logs any statement slower than 200ms — your first profiling signal
docker exec pulse-postgres psql -U pulse -d pulse -c "SHOW log_min_duration_statement;"
```

**Expected:**
```
1) "maxmemory-policy"
2) "noeviction"
```
and `log_min_duration_statement` = `200ms`.

Tear down when you're done verifying:

```bash
docker compose -p pulse-dev -f compose.dev.yml down -v
```

---

## Checklist

- [ ] `python3 --version` shows 3.12+, the 100-coroutine test finishes in ~0.5s
- [ ] `uvloop` imports and reports loop module `uvloop`
- [ ] Django 5.1 + Channels 4.1 import; `AsyncJsonWebsocketConsumer` imports
- [ ] `docker compose version` shows v2
- [ ] Redis 7 responds `PONG`, `XADD` works, `HELLO 3` returns proto 3
- [ ] Postgres 16 runs and routes a row into a partition
- [ ] `k6 version` works
- [ ] `locust --version` works and `websocket-client` imports
- [ ] `node --version` shows 20+
- [ ] `websocat --version` works (or you've chosen an alternative)
- [ ] The dev Compose stack comes up healthy, both services answer, and
      `maxmemory-policy=noeviction` + `log_min_duration_statement=200ms` are set

All checked? Go to
**[Module 01 — Python Async & Concurrency for Real-Time](./01-python-async-concurrency/)**.

---

## If something failed

See [`cheatsheets/troubleshooting.md`](./cheatsheets/troubleshooting.md) for
decision trees. The four most common problems:

| Symptom | Usual cause | Fix |
|---------|-------------|-----|
| `python3` is 3.10/3.11, not 3.12 | System Python is old | `pyenv install 3.12` (or `uv python install 3.12`); re-open the shell |
| `uvloop` wheel fails to build | Missing build toolchain | Install `python3-dev` + a C compiler, or use the prebuilt wheel for your platform |
| `import channels` fails on ASGI version | Django/Channels mismatch | Pin `django==5.1.*` and `channels==4.1.*` exactly, in a clean venv |
| `port is already allocated` | A stray container from a prior step | `docker ps -a`, then `docker rm -f <name>` |
| Postgres container exits immediately | Stale volume with a different password | `docker compose -p pulse-dev down -v` (note the `-v`) |
