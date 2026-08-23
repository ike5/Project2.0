# Lab 00 — Install the Toolchain

**You'll:** install Python 3.12, `uv`, Docker, k6, Locust, Node and websocat;
start the dev data tier; and record your machine's baseline connection limits —
the numbers that cap everything else.

⏱️ ~60 min. Run from the repo root unless a step says otherwise.

---

## Part A — Python 3.12

Python 3.12 is the floor for this course. Earlier versions work for most of it,
but 3.12's `asyncio` internals and interpreter speed are what the reference
numbers assume.

### macOS
```bash
brew install python@3.12
python3.12 --version
```

### Linux (deadsnakes on Debian/Ubuntu)
```bash
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt update && sudo apt install -y python3.12 python3.12-venv python3.12-dev
```

### Linux (Fedora/RHEL)
```bash
sudo dnf install -y python3.12 python3.12-devel
```

Confirm:
```bash
python3.12 --version
```

**Expected:**
```
Python 3.12.7
```

Now install **`uv`**, the package manager the labs use (plain `pip`/`venv` works
too — every `uv pip` command has a `pip` equivalent):

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source "$HOME/.local/bin/env" 2>/dev/null || export PATH="$HOME/.local/bin:$PATH"
uv --version
```

**Expected:**
```
uv 0.5.11
```

Prove asyncio works and that you're on a real 3.12 event loop — this is the
feature everything else in Phase 1 rests on:

```bash
python3.12 - <<'PY'
import asyncio, sys
async def main():
    loop = asyncio.get_running_loop()
    print(f"python={sys.version.split()[0]}  loop={type(loop).__name__}")
asyncio.run(main())
PY
```

**Expected:**
```
python=3.12.7  loop=_UnixSelectorEventLoop
```

✅ Note `_UnixSelectorEventLoop` — that's the **stdlib** event loop, built on
`epoll`. In Module 01 you'll replace it with **uvloop** (a libuv-based loop) and
measure the difference. Right now, seeing the selector loop is the point: this is
the machinery that lets one Python thread watch tens of thousands of sockets.

---

## Part B — A course virtualenv

Make one environment you'll reuse through Phase 1, so the async labs have Django,
Channels, and the tools they import.

```bash
cd django-chat-course
uv venv --python 3.12 .venv
source .venv/bin/activate           # Windows: .venv\Scripts\activate
uv pip install \
  "django==5.1.*" \
  "channels[daphne]==4.1.*" \
  "channels-redis==4.2.*" \
  "uvicorn[standard]==0.32.*" \
  "uvloop==0.21.*" \
  "djangorestframework==3.15.*" \
  "psycopg[binary]==3.2.*" \
  "redis==5.2.*" \
  "locust==2.32.*"
```

**Expected** (last line):
```
Installed 40 packages in 1.83s
```

> `uvicorn[standard]` pulls in `uvloop` and `httptools`; we also pin `uvloop`
> explicitly because Module 01 imports it directly to benchmark it against the
> stdlib loop. `channels[daphne]` gives you the Daphne ASGI server; Uvicorn is
> installed separately because Module 15 races them.

Confirm the key imports resolve:

```bash
python -c "import django, channels, uvicorn, uvloop, rest_framework, psycopg, redis, locust; \
print('django', django.get_version()); print('channels', channels.__version__)"
```

**Expected:**
```
django 5.1.4
channels 4.1.0
```

---

## Part C — Docker & Compose v2

### macOS
```bash
brew install --cask docker    # then launch Docker Desktop once
```
In Docker Desktop → Settings → Resources, give it at least **8 GB RAM** (12 GB
if you plan to do Module 19's kind cluster). macOS runs containers in a VM, so
this limit is real and separate from your machine's RAM.

### Linux
```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker "$USER"
newgrp docker                  # or log out and back in
```

Confirm:
```bash
docker --version
docker compose version
docker run --rm hello-world | head -3
```

**Expected:**
```
Docker version 27.3.1, build ce12230
Docker Compose version v2.29.7

Hello from Docker!
```

⚠️ `docker compose` (space) not `docker-compose` (hyphen). Compose v1 is EOL and
several files in this course use v2-only syntax such as top-level `name:`.

---

## Part D — k6 (primary) and Locust (Python-native)

**k6** generates WebSocket load. It's written in Go, so it holds tens of
thousands of sockets on a laptop that Locust would choke on.

```bash
# macOS
brew install k6

# Debian/Ubuntu
sudo gpg -k
sudo gpg --no-default-keyring --keyring /usr/share/keyrings/k6-archive-keyring.gpg \
     --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys C5AD17C747E3415A3642D57D77C6C491D6AC1D69
echo "deb [signed-by=/usr/share/keyrings/k6-archive-keyring.gpg] https://dl.k6.io/deb stable main" \
     | sudo tee /etc/apt/sources.list.d/k6.list
sudo apt update && sudo apt install -y k6

# Fedora/RHEL
sudo dnf install -y https://dl.k6.io/rpm/repo.rpm && sudo dnf install -y k6
```

```bash
k6 version
```

**Expected:**
```
k6 v0.54.0 (go1.23.2, linux/amd64)
```

**Locust** you already installed into the venv in Part B. Confirm it runs:

```bash
locust --version
```

**Expected:**
```
locust 2.32.3
```

> **Why both?** k6 is what you'll trust for the ceiling numbers — it's cheap per
> socket and honest about latency. Locust is Python, so its user classes read
> like the code your audience already writes, and it's easy to model complex
> client behaviour in. Module 06 runs the *same* load with both and shows you
> where Locust's numbers drift (coordinated omission — it stops counting latency
> while it's busy, so it flatters itself under overload). Knowing that failure
> mode is worth more than the tool.

---

## Part E — Node 20+, websocat, jq

```bash
# Node via nvm (recommended — Module 17 needs 20+)
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash
source ~/.nvm/nvm.sh
nvm install 20 && nvm use 20

# websocat
brew install websocat                                    # macOS
cargo install websocat                                   # any platform with Rust
# or grab a static binary from github.com/vi/websocat/releases

# jq
brew install jq          # macOS
sudo apt install -y jq   # Debian/Ubuntu
```

```bash
node --version && npm --version && websocat --version && jq --version
```

**Expected:**
```
v20.18.0
10.8.2
websocat 1.13.0
jq-1.7.1
```

> **No websocat?** Every lab step using it has an alternative noted. The easiest
> is `npm i -g wscat` (`wscat -c ws://localhost:8000/ws/...`). websocat is worth
> having for Module 03, where you send raw frames by hand.

---

## Part F — Start the dev data tier

Create the infra directory and its compose file. Two services for Phase 0–1:
Postgres 16 and Redis 7.

```bash
mkdir -p infra
```

Create `infra/compose.dev.yml`:

```yaml
# Phase 0-1 development stack: just the data tier.
# The app runs on your host (uvicorn/daphne) so you can attach a debugger.
#
#   docker compose -f infra/compose.dev.yml up -d
#   docker compose -f infra/compose.dev.yml ps        # both must be (healthy)
#   docker compose -f infra/compose.dev.yml down -v   # -v drops volumes too

name: pulse-dev

services:
  postgres:
    image: postgres:16-alpine
    container_name: pulse-postgres
    environment:
      POSTGRES_USER: pulse
      POSTGRES_PASSWORD: pulse
      POSTGRES_DB: pulse
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U pulse -d pulse"]
      interval: 5s
      timeout: 3s
      retries: 10
      start_period: 10s
    command:
      - "postgres"
      - "-c"
      - "log_min_duration_statement=200"   # log anything slower than 200ms
      - "-c"
      - "shared_preload_libraries=pg_stat_statements"
      - "-c"
      - "max_connections=100"

  redis:
    image: redis:7-alpine
    container_name: pulse-redis
    ports:
      - "6379:6379"
    volumes:
      - redisdata:/data
    healthcheck:
      test: ["CMD", "redis-cli", "PING"]
      interval: 5s
      timeout: 3s
      retries: 10
    command:
      - "redis-server"
      - "--appendonly"
      - "yes"
      - "--maxmemory"
      - "512mb"
      - "--maxmemory-policy"
      - "noeviction"          # a chat backbone must NOT silently drop state;
                              # we want the error, loudly. Module 08 discusses.
      - "--slowlog-log-slower-than"
      - "5000"                # microseconds

volumes:
  pgdata:
  redisdata:
```

Bring it up:

```bash
docker compose -f infra/compose.dev.yml up -d
docker compose -f infra/compose.dev.yml ps
```

**Expected** — both `(healthy)`, which may take ~15 seconds:
```
NAME             IMAGE                STATUS                   PORTS
pulse-postgres   postgres:16-alpine   Up 18 seconds (healthy)  0.0.0.0:5432->5432/tcp
pulse-redis      redis:7-alpine       Up 18 seconds (healthy)  0.0.0.0:6379->6379/tcp
```

If a container shows `(health: starting)` for more than a minute, check
`docker compose -f infra/compose.dev.yml logs postgres`.

Confirm both actually answer:

```bash
docker exec pulse-redis redis-cli PING
docker exec pulse-postgres psql -U pulse -d pulse -c "SELECT version();" | head -3
```

**Expected:**
```
PONG
                                                 version
---------------------------------------------------------------------------------------------------------
 PostgreSQL 16.4 on x86_64-pc-linux-musl, compiled by gcc (Alpine 13.2.1_git20240309) 13.2.1 20240309, 64-bit
```

### Why these settings?

Two choices worth noting now, because you'll revisit both:

- **`--maxmemory-policy noeviction`** on Redis. It means Redis returns an *error*
  when full rather than silently discarding keys. For a cache you'd want
  `allkeys-lru`; for a message backbone, silent data loss is the worst possible
  failure mode. Module 08 argues this properly, and Module 07 shows you what
  losing messages actually looks like.
- **`log_min_duration_statement=200`** on Postgres. Anything slower than 200 ms
  lands in the log. In Module 12 you'll watch a query cross that line under
  keyset-vs-offset pagination and learn why.

---

## Part G — Record your machine

You'll generate the real Django project in Module 04. For now, start the results
file the whole course writes into.

Create `results.md` at the course root — **this file matters**. Modules 06, 07,
09, 15, 16, 18 and 22 all compare against numbers you record here.

```bash
cat > results.md <<'EOF'
# Pulse — Benchmark Log

Every measured number in this course lands here. Always record the context:
machine, Python version, worker count, workload shape, and duration. A number
without context is noise.

## Machine

- CPU (cores):
- RAM:
- OS:
- Python:
- Docker RAM limit (macOS only):

## Baseline (Module 00)

- Process FD limit (`ulimit -n`):
- System FD limit (`/proc/sys/fs/file-max`):
- Ephemeral port range:
- Idle container RSS — postgres / redis:

## Module 01 — asyncio vs threads

- asyncio Tasks created before failure:
- OS threads created before failure:
- Blocking-the-loop penalty (time.sleep vs asyncio.sleep):
- uvloop vs stdlib loop throughput:
- Unbounded concurrency p99, with/without Semaphore:

## Module 06 — Single-node ceiling

- Max stable connections per worker / per node:
- Bytes per connection:
- p50 / p95 / p99 fan-out latency at that load:
- What broke first:

## Module 07 — channel layer hop cost, message loss on pause

## Module 09 — Pub/Sub vs Streams

## Module 15 — async vs sync vs raw ASGI

## Module 16 — Redis vs Kafka

## Module 18 — Failover cost

## Module 22 — Capstone target
EOF
```

Fill in the **Machine** section now:

```bash
{
  echo "cores: $(nproc 2>/dev/null || sysctl -n hw.ncpu)"
  echo "ram:   $(free -h 2>/dev/null | awk '/Mem:/{print $2}' || echo "$(($(sysctl -n hw.memsize)/1073741824))Gi")"
  echo "os:    $(uname -sr)"
  echo "py:    $(python3.12 --version)"
}
```

**Expected** (yours will differ — that's the point):
```
cores: 8
ram:   15Gi
os:    Linux 6.8.0-45-generic
py:    Python 3.12.7
```

Paste those into `results.md`. **The core count is the single most important
number in this file** — on the JVM twin virtual threads made core count almost
invisible; here it directly sets your worker count, because you run one Uvicorn
worker per core. An 8-core box runs 8 workers, holds 8 Python interpreters, and
has 8 independent event loops that (as Module 04 proves) cannot see each other
without Redis.

---

## Part H — Record your connection limits

These three numbers determine your hard ceiling before any code runs.

```bash
ulimit -n                             # this process
cat /proc/sys/fs/file-max 2>/dev/null || sysctl -n kern.maxfiles   # whole system
cat /proc/sys/net/ipv4/ip_local_port_range 2>/dev/null || sysctl -n net.inet.ip.portrange.first
```

**Expected** (typical Linux defaults):
```
1024
9223372036854775807
32768	60999
```

That `1024` is almost certainly what will bind first, and it's the reason
"my server stops accepting connections at exactly 1016 clients" is such a common
confused bug report (the other 8 descriptors are stdin/stdout/stderr, the
listening socket, log files, the Postgres connection, the Redis connection…).
Raise it for your shell:

```bash
ulimit -n 100000
ulimit -n
```

**Expected:**
```
100000
```

> This only affects the current shell. Module 06 shows how to set it
> persistently and inside containers. For now, just know the number exists and
> that a WebSocket server is one of the few workloads that actually hits it.

The ephemeral port range (`32768–60999` ≈ 28,000 ports) limits how many
*outbound* connections one machine can make **to one destination**. It
constrains your **load generator**, not your server — a distinction that has
fooled a great many people into thinking their server caps out at 28k. When your
k6 box "can't get past 28,000 connections," this is why, and Module 06 shows the
fix (bind multiple source IPs, or spread load across machines).

Record all three in `results.md`.

---

## Part I — A first look at what an idle socket costs

You'll measure this properly in Module 01, but here's a 30-second preview that
makes Problem 1 concrete. Open a pile of TCP connections to Redis and watch
nothing happen — cheaply.

```bash
python3.12 - <<'PY'
import socket, resource, time
conns = []
for _ in range(2000):
    s = socket.create_connection(("127.0.0.1", 6379))
    conns.append(s)
rss_kb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
# ru_maxrss is KB on Linux, bytes on macOS
rss_kb = rss_kb // 1024 if rss_kb > 5_000_000 else rss_kb
print(f"held {len(conns)} idle sockets | client RSS {rss_kb:,} KB "
      f"| {rss_kb/len(conns):.1f} KB per socket (client side only)")
PY
```

**Expected:**
```
held 2000 idle sockets | client RSS 21,340 KB | 10.7 KB per socket (client side only)
```

✅ ~10 KB per idle socket on the *client* side, and that's before any
application state, any consumer object, or any asyncio Task — just the Python
socket object plus kernel buffers. When Module 01 adds the ~45 KB of Django
Channels consumer + Task overhead on the *server* side, you'll have the full
per-connection cost that caps your node.

---

## Cleanup

Leave the dev stack running if you're going straight to Module 01 (it doesn't
need Redis, but Module 02 will). Otherwise:

```bash
docker compose -f infra/compose.dev.yml down
# add -v to also drop the volumes (a clean slate for next time)
```

---

## What you did

- Installed Python 3.12, `uv`, and a course virtualenv with Django 5.1,
  Channels 4.1, Uvicorn+uvloop, DRF, and Locust.
- Brought up Postgres 16 and Redis 7 with settings chosen deliberately, not by
  default, and confirmed both answer.
- Recorded the three limits that cap connection count, and learned which one
  binds first — and which constrains the *load generator*, not the server.
- Saw, in one preview measurement, what an idle socket costs before any app code.
- Started `results.md`, which the rest of the course writes into.

Now do [`challenge.md`](./challenge.md) — it establishes the baseline numbers
(FD ceilings, per-Task vs per-thread cost, fan-out amplification math, the cost
of an idle socket) that Module 01 and Module 06 will compare against.

Then: [Module 01 — Python Async & Concurrency for Real-Time](../01-python-async-concurrency/).
