# Cheatsheet — Docker & High Availability (Django/ASGI edition)

Companion to [`../18-compose-ha-and-chaos/`](../18-compose-ha-and-chaos/). The
data tier here is identical to the JVM twin's — Sentinel, Patroni, etcd, HAProxy
— because **failover time is a property of the datastore's quorum protocol, not
of the application runtime**. What is different is everything above the load
balancer: draining Uvicorn worker *processes*, `redis-py` timeouts, and the fact
that each worker holds its own sockets and nobody else's.

---

## What "HA" actually means

Not "it never breaks." Two numbers:

- **RTO** (Recovery Time Objective) — how long you're degraded.
- **RPO** (Recovery Point Objective) — how much data you lose.

| Design | RTO | RPO | Cost |
|--------|-----|-----|------|
| Single node + nightly backups | hours | up to 24 h | 1× |
| Single node + streaming replica, manual promote | minutes (a human must wake) | ~0 | 2× |
| **Sentinel / Patroni auto-failover** | **10–30 s** | 0 (sync) / ~ms (async) | 3× |
| Multi-region active/active | ~0 | conflict resolution becomes *your* problem | 6×+ |

Pulse targets row three: **RTO < 30 s, RPO = 0.** Module 18 measures whether it
achieves that, which is a different question from whether it was *configured*
for it. Configuration is a hypothesis; the drill is the experiment.

---

## The three HA rules

1. **Quorum needs odd numbers.** 3 sentinels (quorum 2), 3 etcd nodes, 3 Patroni
   members. Two of anything is not HA — it's two single points of failure that
   can disagree.
2. **Failover requires fencing.** A demoted primary that can still accept writes
   gives you split-brain, which is worse than downtime because downtime is
   visible and divergence is not.
3. **HA is only real if you've tested it.** An untested failover path is a
   theory. A failover that is invisible at zero traffic can drop 40% of messages
   at 5,000 msg/s.

---

## Compose fundamentals

### Healthchecks are not optional

`depends_on` without `condition: service_healthy` waits for the container to
*start*, not to be *usable*. This is the #1 cause of "it works on the second
`up`."

```yaml
services:
  postgres:
    image: postgres:16-alpine
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U pulse -d pulse"]
      interval: 3s
      timeout: 3s
      retries: 20
      start_period: 10s

  redis:
    image: redis:7-alpine
    healthcheck:
      test: ["CMD", "redis-cli", "PING"]
      interval: 3s
      retries: 10

  pulse-1:
    depends_on:
      postgres: { condition: service_healthy }
      redis:    { condition: service_healthy }
    healthcheck:
      # No curl in a slim Python image — use Python itself.
      test: ["CMD", "python", "-c",
             "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8000/readyz').status==200 else 1)"]
      interval: 5s
      timeout: 3s
      retries: 3
      start_period: 20s      # Django app-registry population + migrations check
```

> `start_period` failures don't count toward `retries`. Django's ASGI boot
> (settings import, app registry, `channels_redis` connection) is fast compared
> to a JVM but not instant — 20 s is the safe number. Too short and you get a
> restart loop that looks like a crash.

### `/healthz` vs `/readyz` — the distinction that saves you

| Endpoint | Question | Who reads it | What a 503 does |
|----------|----------|--------------|-----------------|
| `/healthz` (liveness) | Is the process alive at all? | container runtime / k8s | **restarts the process** |
| `/readyz` (readiness) | Should I get traffic right now? | nginx / k8s Service | **sheds traffic** |

Put **capacity** signals (queue depth, fan-out p99) on *readiness only*. On
liveness, a global load spike fails all three nodes at once and the runtime
restarts them into a loop — turning a capacity problem into a total outage.
Module 18's brownout drill measures exactly this: RPO 4,102 → 0 and p99
14,200 ms → 418 ms once the capacity signal moved to readiness.

### Compose commands worth memorizing

```bash
docker compose -f infra/ha/compose.ha.yml up -d --wait      # --wait blocks on healthchecks
docker compose -f infra/ha/compose.ha.yml ps --format 'table {{.Name}}\t{{.Status}}'
docker compose -f infra/ha/compose.ha.yml logs -f --tail=50 pulse-1
docker compose -f infra/ha/compose.ha.yml exec pulse-1 sh
docker compose -f infra/ha/compose.ha.yml up -d --force-recreate pulse-1
docker compose -f infra/ha/compose.ha.yml down -v           # -v drops volumes. Do this between drills.
```

### Resource limits

```yaml
    deploy:
      resources:
        limits:       { cpus: '2.0', memory: 2G }
        reservations: { cpus: '0.5', memory: 512M }
```
Compose v2 honours `deploy.resources.limits` without Swarm.

**The Python-specific note:** the JVM needs `-XX:MaxRAMPercentage` to learn its
cgroup limit. CPython has no heap to size — it just allocates until the cgroup
OOM-killer takes it. What you *do* need to size is **worker count**: give a
container 2 CPUs and run 8 Uvicorn workers and you have 8 processes fighting for
2 cores, each with its own interpreter, its own memory, and its own event loop
that now turns over slowly. **Workers should match the CPU limit, not the host's
core count.**

```yaml
    environment:
      WEB_CONCURRENCY: "2"        # uvicorn --workers reads this
    deploy:
      resources:
        limits: { cpus: '2.0' }
```

### Graceful shutdown — the WebSocket-specific bit

```yaml
    stop_grace_period: 60s        # default is 10s — nowhere near enough to drain sockets
    stop_signal: SIGTERM
```
```bash
uvicorn pulse.asgi:application --host 0.0.0.0 --port 8000 \
        --workers 4 --timeout-graceful-shutdown 45
```

`stop_grace_period` must exceed `--timeout-graceful-shutdown`, which must exceed
your drain time. Get the ordering wrong and Docker SIGKILLs the container
mid-drain — you built the whole mechanism and then hard-killed 10,000 sockets
anyway.

---

## Draining an ASGI app (there is no framework hook)

On the JVM this is `@PreDestroy` plus `server.shutdown: graceful`. **In ASGI
there is no framework method that hands you "all your sockets."** You assemble
the drain from three pieces:

```
1. a per-PROCESS connection registry     (consumers add/discard themselves)
2. the ASGI lifespan.shutdown message    (Uvicorn fires it after it stops accept())
3. a two-phase SIGTERM handler           (flip readiness FIRST, then defer to Uvicorn)
```

The sequence, and why each step exists:

```
SIGTERM arrives
  Phase 1:  readiness -> DRAINING          /readyz returns 503
            await sleep(DRAIN_DELAY=6s)    ← let nginx's healthcheck notice (2 intervals)
  Phase 2:  defer to Uvicorn's shutdown
            -> Uvicorn stops accept(), fires lifespan.shutdown
            -> broadcast control{reconnect, retry_after_ms=jitter} to every socket
            -> await sleep(2)              ← let the frames actually leave
            -> close(code=1001)            ← "going away", a real close frame
  bounded by --timeout-graceful-shutdown 45, then stop_grace_period 60s
```

**Why `DRAIN_DELAY` matters:** if you drain only inside `lifespan.shutdown`,
Uvicorn has *already* stopped accepting by then — so during the window between
SIGTERM and nginx noticing, new handshakes are routed to a socket that refuses
them. This is the same reason Kubernetes needs `preStop: sleep` (Module 19).

```python
# the jitter that prevents the thundering herd
import secrets
retry_after_ms = 1000 + secrets.randbelow(29_000)      # 1s..30s, per client
```

> **Process-per-core reminder (Module 01):** Uvicorn's master forwards SIGTERM to
> every worker, and **each worker drains its own registry** — the registry is
> process-local because the connections are. There is no cross-process "all
> sockets" list and you don't want one: a worker knows exactly the set it must
> close. Same GIL/process boundary that forced Redis on you in Module 04, showing
> up again at shutdown.

**Measured payoff (Module 18, 10,000 connections, rolling deploy of 3 nodes):**

| | Hard restart | Graceful drain |
|---|-------------|----------------|
| RTO | 18.4 s | **0 s** |
| Messages lost | 2,841 | **0** |
| Close code seen by clients | 1006 (unknown) | **1001 + retry_after** |
| Time for clients to notice | median 47 s | **median 4 ms** |
| Reconnect peak | 3,341/s | **189/s** |
| p99 during | 9,120 ms | **290 ms** |

Five independent decisions produce that, and no one of them is sufficient:
`stop_grace_period: 60s`, `--timeout-graceful-shutdown 45`, the readiness flip
before Uvicorn stops accepting, the `control` frame in the Module 05 protocol,
and full-jitter reconnect in the Module 17 client.

---

## Topology: the full HA stack

```
                         ┌──────────┐
     clients  ──────────▶│  nginx   │  cookie-consistent-hash, WS-aware, drains
                         └────┬─────┘
                  ┌───────────┼───────────┐
              ┌───▼───┐   ┌───▼───┐   ┌───▼───┐
              │pulse-1│   │pulse-2│   │pulse-3│  Uvicorn+uvloop, N workers each
              └───┬───┘   └───┬───┘   └───┬───┘
          ┌───────┴───────────┴───────────┴───────┐
          │                                       │
   ┌──────▼────────┐                      ┌───────▼────────┐
   │ Redis         │                      │    HAProxy     │
   │ 3 primaries   │                      │  :5000 write   │
   │ 3 replicas    │                      │  :5001 read    │
   └───────────────┘                      └───────┬────────┘
   channel layer +                     ┌──────────┼──────────┐
   Streams + presence             ┌────▼───┐ ┌────▼───┐ ┌────▼───┐
                                  │patroni1│ │patroni2│ │patroni3│
                                  │primary │ │replica │ │replica │
                                  └────┬───┘ └────┬───┘ └────┬───┘
                                       └──────────┼──────────┘
                                             ┌────▼────┐
                                             │  etcd   │ 3 nodes
                                             └─────────┘
                                     (PgBouncer sits in front of :5000)
```

Fifteen containers, ~9 GB. The low-memory path swaps Cluster for Sentinel and
runs 2 app nodes.

---

## Nginx: WebSocket-aware load balancing

```nginx
events { worker_connections 65535; }
http {
  map $http_upgrade $connection_upgrade { default upgrade; '' close; }

  upstream pulse {
    hash $cookie_pulse_node consistent;    # survives NAT; remaps only 1/n on change
    server pulse-1:8000 max_fails=2 fail_timeout=5s;
    server pulse-2:8000 max_fails=2 fail_timeout=5s;
    server pulse-3:8000 max_fails=2 fail_timeout=5s;
  }

  server {
    listen 80;
    location = /readyz { proxy_pass http://pulse; }     # so nginx can drop a draining node

    location / {
      proxy_pass http://pulse;
      proxy_http_version 1.1;                # REQUIRED — 1.0 cannot Upgrade
      proxy_set_header Upgrade    $http_upgrade;
      proxy_set_header Connection $connection_upgrade;
      proxy_set_header Host       $host;
      proxy_read_timeout 3600s;              # default 60s KILLS IDLE SOCKETS
      proxy_send_timeout 3600s;
      proxy_buffering    off;                # never buffer a stream
      proxy_next_upstream error timeout http_502 http_503;
    }
  }
}
```

> **The two classic WebSocket-behind-nginx bugs:** forgetting
> `proxy_http_version 1.1` (handshake fails outright) and leaving
> `proxy_read_timeout` at 60 s (sockets die every minute and you blame the
> client).

**Stickiness:** `ip_hash` is easy but breaks behind carrier NAT (thousands of
users share one IP) and reshuffles when the upstream list changes.
`hash $cookie_… consistent` remaps only ~1/n of clients when a node leaves.

**Do you still need stickiness once Redis is the backplane?** Yes — not for
message routing (Redis handles that) but for the state a worker keeps locally:
the consumer instance, the resume cursor in memory, the presence heartbeat
timer. Losing stickiness means a reconnect lands elsewhere and re-does that
work. It's a cost, not a correctness bug.

### Handshake rate limiting — do it here, not in the app

```nginx
limit_req_zone  $binary_remote_addr zone=handshake:32m rate=5r/s;
limit_conn_zone $binary_remote_addr zone=conns:32m;

location /ws/ {
    limit_req  zone=handshake burst=10 nodelay;
    limit_conn conns 20;
    proxy_pass http://pulse;
}
```

A flood that reaches Uvicorn has already cost a TCP connection, a TLS handshake,
an asyncio Task and a `connect()` coroutine — and it competes for the **one core
that worker owns**. Rejecting it at nginx costs a counter increment. This matters
more in Python than on the JVM (Module 21).

---

## Redis Sentinel in Compose

```yaml
x-sentinel: &sentinel
  image: redis:7-alpine
  entrypoint: /entrypoint.sh
  volumes:
    - ./sentinel.conf.template:/etc/redis/sentinel.conf.template:ro
    - ./sentinel-entrypoint.sh:/entrypoint.sh:ro
  depends_on: [redis-1, redis-2, redis-3]

services:
  sentinel-1: { <<: *sentinel, ports: ["26379:26379"] }
  sentinel-2: { <<: *sentinel, ports: ["26380:26379"] }
  sentinel-3: { <<: *sentinel, ports: ["26381:26379"] }
```

⚠️ **Sentinel rewrites its own config file** (it persists the discovered
topology). Mounting one read-only file into three sentinels fails on startup with
a confusing permission error. Copy the template per-container:

```sh
#!/bin/sh
set -e
cp /etc/redis/sentinel.conf.template /tmp/sentinel.conf
chmod 644 /tmp/sentinel.conf
exec redis-sentinel /tmp/sentinel.conf
```

```
port 26379
sentinel monitor pulse redis-1 6379 2
sentinel down-after-milliseconds pulse 5000
sentinel failover-timeout pulse 10000
sentinel parallel-syncs pulse 1
sentinel resolve-hostnames yes
```

`2` is the quorum with **three** sentinels. Two sentinels with quorum 1 will
split-brain — each can independently declare a failover.

```bash
docker exec pulse-ha-sentinel-1-1 redis-cli -p 26379 SENTINEL get-master-addr-by-name pulse
docker exec pulse-ha-sentinel-1-1 redis-cli -p 26379 SENTINEL sentinels pulse | grep -c name
docker exec pulse-ha-sentinel-1-1 redis-cli -p 26379 SENTINEL failover pulse    # force one
watch -n1 'docker exec -T pulse-ha-sentinel-1-1 redis-cli -p 26379 SENTINEL get-master-addr-by-name pulse'
```

Also set on the primaries — it removes seconds from your RTO at exactly the wrong
moment:
```
--repl-diskless-sync yes --repl-diskless-sync-delay 0
```
Without it a promoted primary forks and writes an RDB to disk before replicas can
sync.

### Pointing Channels at Sentinel — and the one setting that matters

```python
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.pubsub.RedisPubSubChannelLayer",
        "CONFIG": {
            "hosts": [{
                "sentinels": [("sentinel-1", 26379),
                              ("sentinel-2", 26379),
                              ("sentinel-3", 26379)],
                "master_name": "pulse",
                "socket_timeout": 2.0,          # redis-py default is None — NO TIMEOUT
                "socket_connect_timeout": 2.0,
                "socket_keepalive": True,
            }],
        },
    },
}
```

> 🐍 **The Python-specific landmine.** `redis-py`'s default `socket_timeout` is
> `None`. On a `docker pause`d primary the TCP connection stays open and nothing
> ever arrives, so a `None` timeout **never fires** — and the awaiting coroutine
> holds the event loop's attention on a call that will never return, taking every
> connection on that worker with it. Module 18 measures it: RTO 14.8 s → 9.1 s
> and p99 8,940 ms → 2,180 ms from those two lines.

---

## Patroni + etcd + HAProxy

Patroni holds a **leader lock with a TTL** in etcd. If the leader can't renew it,
Patroni **demotes itself** — that's the fencing, and it works for a network
partition, not just a crash.

```
t=0    primary is partitioned from etcd
t=15   primary cannot renew the leader key -> Patroni DEMOTES ITSELF
t=20   a replica acquires the leader key and promotes
```

```yaml
      PATRONI_TTL: "15"           # leader lock TTL      — dominates your RTO
      PATRONI_LOOP_WAIT: "5"      # how often Patroni checks
      PATRONI_RETRY_TIMEOUT: "5"
```

**Constraint:** `TTL >= loop_wait * 2 + retry_timeout`. 15/5/5 satisfies it with
zero margin and is about as low as is safe. Measured effect: PG kill RTO
24.1 s → 11.8 s. The cost is that a brief etcd hiccup can now trigger an
unnecessary failover.

```haproxy
listen postgres_write
    bind *:5000
    option httpchk GET /primary            # Patroni's REST API answers 200 only on the primary
    http-check expect status 200
    default-server inter 3s fall 3 rise 2 on-marked-down shutdown-sessions
    server pg1 patroni1:5432 check port 8008
    server pg2 patroni2:5432 check port 8008
    server pg3 patroni3:5432 check port 8008

listen postgres_read
    bind *:5001
    balance roundrobin
    option httpchk GET /replica
    http-check expect status 200
    default-server inter 3s fall 3 rise 2 on-marked-down shutdown-sessions
    server pg1 patroni1:5432 check port 8008
    server pg2 patroni2:5432 check port 8008
    server pg3 patroni3:5432 check port 8008
```

`on-marked-down shutdown-sessions` is fencing at the proxy layer — it kills
existing connections to a demoted node so a psycopg connection with an open
transaction can't keep writing.

```bash
docker exec pulse-ha-patroni1-1 patronictl -c /home/postgres/postgres.yml list
docker exec pulse-ha-patroni1-1 patronictl -c /home/postgres/postgres.yml switchover   # planned
docker exec pulse-ha-patroni1-1 patronictl -c /home/postgres/postgres.yml failover     # unplanned
docker exec pulse-ha-etcd1-1 etcdctl get --prefix /service/pulse
curl -s localhost:8008/primary -o /dev/null -w '%{http_code}\n'
curl -s localhost:7000 | grep -oE '(UP|DOWN)' | head -6                  # HAProxy stats
```

### The psycopg + PgBouncer setting you cannot skip

With PgBouncer in **transaction pooling** mode, a psycopg3 connection may run
each transaction on a different server connection, so **server-side prepared
statements break**:

```python
DATABASES["default"]["OPTIONS"] = {"prepare_threshold": None}   # default is 5
DATABASES["default"]["CONN_MAX_AGE"] = 0                        # let PgBouncer own pooling
```

The exact analog of the JVM twin's `?prepareThreshold=0` on the JDBC URL — same
failure, different client library. Symptom if you skip it: intermittent
`prepared statement "_pg3_1" already exists` under load only.

---

## Chaos drill commands

```bash
docker kill <c>                      # SIGKILL — instant, clean TCP RST
docker pause <c>                     # freeze — looks like a hang. THE MEAN ONE.
docker unpause <c>
docker stop -t 60 <c>                # SIGTERM then SIGKILL — tests graceful drain
docker network disconnect <net> <c>  # partition. Split-brain testing.
docker network connect <net> <c>     # heal it — now watch reconciliation
docker update --cpus 0.1 <c>         # brownout: slow, not dead. Usually the worst.
```

Inside a container (needs `--cap-add=NET_ADMIN`):
```bash
tc qdisc add dev eth0 root netem delay 200ms 50ms      # latency + jitter
tc qdisc add dev eth0 root netem loss 5%               # packet loss
tc qdisc del dev eth0 root                             # heal
```

### `pause` versus `kill` — the most important distinction here

| | `docker kill` | `docker pause` |
|---|--------------|----------------|
| TCP behaviour | socket closes, RST sent | **connection stays open, nothing flows** |
| Client detection | milliseconds | **whatever your timeout is** |
| Resembles | a process crash | **a partition, a GC pause, a hung disk** |
| More common in production? | | **this one** |

**Systems that handle `kill` gracefully often fall over on `pause`.** In Python
this is sharper than elsewhere: a frozen dependency with no client timeout
freezes the *worker's event loop*, and therefore every connection that worker
holds — not just the one request that touched it.

**Always run a load test during the drill.** A drill without one tells you the
cluster reconfigured; a drill with one tells you how many users noticed. The
number *is* the deliverable.

---

## Container image hygiene for Python

```dockerfile
# ---- build ----
FROM python:3.12-slim AS build
ENV PYTHONDONTWRITEBYTECODE=1 PIP_NO_CACHE_DIR=1
WORKDIR /src
RUN pip install uv
COPY pyproject.toml uv.lock ./
RUN uv export --frozen --no-dev -o requirements.txt \
 && pip wheel -r requirements.txt -w /wheels        # cached layer — deps change rarely

# ---- run ----
FROM python:3.12-slim
RUN useradd -r -u 10001 app
COPY --from=build /wheels /wheels
RUN pip install --no-index --find-links=/wheels /wheels/* && rm -rf /wheels
USER app
WORKDIR /app
COPY --chown=app . .
ENV PYTHONUNBUFFERED=1 PYTHONFAULTHANDLER=1 WEB_CONCURRENCY=4
EXPOSE 8000
CMD ["uvicorn", "pulse.asgi:application", "--host", "0.0.0.0", "--port", "8000", \
     "--loop", "uvloop", "--timeout-graceful-shutdown", "45"]
```

- **Copy the lockfile and install deps before copying source.** Otherwise every
  code change reinstalls the world.
- **`PYTHONUNBUFFERED=1`** or your logs vanish into a pipe buffer and you'll
  swear the app is hung during a drill.
- **`PYTHONFAULTHANDLER=1`** gives you a stack trace on SIGSEGV/SIGABRT from a C
  extension — which is how a psycopg or hiredis bug actually presents.
- **Run as non-root. Never `latest`.** Pin digests for anything you'd page
  someone about.
- **`uvloop` explicitly**, not implicitly. `uvicorn[standard]` picks it up
  automatically, but naming it makes the deployment self-documenting and fails
  loudly if it isn't installed.

### File descriptors — the limit that surprises everyone

One WebSocket = one FD. 50,000 connections needs > 50,000 FDs, and Python raises
`OSError: [Errno 24] Too many open files`.

```yaml
    ulimits:
      nofile: { soft: 100000, hard: 100000 }
```
```bash
docker compose exec pulse-1 sh -c 'ulimit -n; ls /proc/1/fd | wc -l'
```

Host-side, for the **load generator** (Module 06):
```bash
sysctl -w net.core.somaxconn=65535
sysctl -w net.ipv4.tcp_max_syn_backlog=65535
sysctl -w net.ipv4.ip_local_port_range="10000 65535"
```
The generator runs out of ephemeral ports (~28k with the default range) long
before the server runs out of capacity — a classic false ceiling.

---

## Thundering herd on reconnect

When a node dies, every client it held reconnects **at the same instant**.

```js
// WRONG — synchronized retry storm
setTimeout(reconnect, 1000);

// RIGHT — exponential backoff with FULL jitter
const delay = Math.random() * Math.min(cap, base * 2 ** attempt);
```

Measured, Module 18, one node killed holding 3,341 connections:

| | Full jitter | Fixed 1 s retry |
|---|------------|-----------------|
| Reconnect peak | 214/s | **3,341/s** |
| RTO | 4.2 s | **41.8 s** |
| Messages lost | 0 | **1,204** |

**The recovery caused more damage than the failure.** That is the normal case,
not a surprise.

Server-side defenses:
- Rate-limit the **handshake** at nginx, not just messages.
- Send `retry_after_ms` in the drain control frame so clients don't have to guess.
- Never restart all replicas at once; stagger and wait for readiness between.
- Drain gracefully so clients get a **close frame with a code** (1001) instead of
  discovering a dead TCP socket 47 seconds later.

---

## Quick reference: the numbers from Module 18's drills

| Drill | RTO | RPO | p99 during |
|-------|-----|-----|-----------|
| Rolling deploy (graceful drain) | **0.0 s** | 0 | 290 ms |
| App node kill | 4.2 s | 0 | 1,840 ms |
| Redis primary kill | 7.4 s | 0 | 261 ms |
| Redis partition | 8.0 s | 0 | 890 ms |
| Redis primary pause (`socket_timeout=2`) | 9.1 s | 0 | 2,180 ms |
| App brownout (with load shedding) | 11.2 s | 0 | 418 ms |
| PG primary kill (TTL 15) | 11.8 s | 0 | 2,010 ms |
| PG primary pause (TTL 15) | 12.4 s | 0 | 2,290 ms |
| etcd quorum loss | 45.2 s | 0 | 8,410 ms |
| *Untuned Redis pause (`socket_timeout=None`)* | *14.8 s* | *0* | *8,940 ms* |
| *App kill, no client jitter* | *41.8 s* | *1,204* | *12,400 ms* |
| *Rolling deploy, hard restart* | *18.4 s* | *2,841* | *9,120 ms* |
| *Brownout, no load shedding* | *60.0 s* | *4,102* | *14,200 ms* |

Reference machine: 8-core / 16 GB, Ubuntu 24.04, Python 3.12, Django 5.1 /
Channels 4.1, Uvicorn + uvloop, 10,000 connections under load.

**The three config changes that bought the most:**

1. `channels_redis` `socket_timeout=2.0` — pause RTO 14.8 s → 9.1 s
2. `PATRONI_TTL` 30 → 15 — PG RTO 24.1 s → 11.8 s
3. Capacity signal on **readiness** — brownout RPO 4,102 → 0
