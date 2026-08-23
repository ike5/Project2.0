# Lab 18 — Kill Everything

**You'll:** build the full HA stack in Compose, wire a graceful ASGI drain into
the Uvicorn app tier, then run eleven chaos drills — each with a load test
running — and record the RTO and RPO for every one.

⏱️ ~140 min. Needs ~9 GB RAM.

> **Low-memory path (8–12 GB):** run Redis Sentinel instead of Cluster (3 redis +
> 3 sentinel instead of 6), 2 app instances instead of 3, and skip Part I's
> Cluster resharding. You lose the sharding drills; every failover drill still
> works.

All paths are relative to the repo root. Infra lives in `infra/ha/`; the drill
scripts live in this module's `code/`.

---

## Part A — Redis Sentinel

`infra/ha/sentinel-entrypoint.sh` — the fix for the config-rewrite trap:

```bash
#!/bin/sh
# Sentinel REWRITES its config at runtime, so it cannot be a read-only mount.
# Copy the template to a writable location per container.
set -e
cp /etc/redis/sentinel.conf.template /tmp/sentinel.conf
chmod 644 /tmp/sentinel.conf
exec redis-sentinel /tmp/sentinel.conf
```

`infra/ha/sentinel.conf.template`:
```
port 26379
sentinel monitor pulse redis-1 6379 2
sentinel down-after-milliseconds pulse 5000
sentinel failover-timeout pulse 10000
sentinel parallel-syncs pulse 1
sentinel resolve-hostnames yes
sentinel announce-hostnames yes
```

> `quorum 2` with **three** sentinels. Two sentinels with quorum 1 will
> split-brain: each can independently declare a failover.

`infra/ha/compose.ha.yml` (Redis section):

```yaml
name: pulse-ha

x-sentinel: &sentinel
  image: redis:7-alpine
  entrypoint: /entrypoint.sh
  volumes:
    - ./sentinel.conf.template:/etc/redis/sentinel.conf.template:ro
    - ./sentinel-entrypoint.sh:/entrypoint.sh:ro
  depends_on: [redis-1, redis-2, redis-3]

services:
  redis-1:
    image: redis:7-alpine
    command: >
      redis-server --appendonly no --save ""
                   --maxmemory 2gb --maxmemory-policy noeviction
                   --repl-diskless-sync yes --repl-diskless-sync-delay 0
    healthcheck: { test: ["CMD","redis-cli","PING"], interval: 3s, retries: 10 }

  redis-2:
    image: redis:7-alpine
    command: >
      redis-server --appendonly no --save "" --replicaof redis-1 6379
                   --maxmemory 2gb --maxmemory-policy noeviction
                   --repl-diskless-sync yes --repl-diskless-sync-delay 0
    depends_on: { redis-1: { condition: service_healthy } }

  redis-3:
    image: redis:7-alpine
    command: >
      redis-server --appendonly no --save "" --replicaof redis-1 6379
                   --maxmemory 2gb --maxmemory-policy noeviction
    depends_on: { redis-1: { condition: service_healthy } }

  sentinel-1: { <<: *sentinel, ports: ["26379:26379"] }
  sentinel-2: { <<: *sentinel, ports: ["26380:26379"] }
  sentinel-3: { <<: *sentinel, ports: ["26381:26379"] }
```

> `repl-diskless-sync yes` matters for failover: without it a promoted primary
> forks and writes an RDB to disk before replicas can sync — adding seconds to
> your RTO at exactly the wrong moment.

```bash
docker compose -f infra/ha/compose.ha.yml up -d redis-1 redis-2 redis-3 sentinel-1 sentinel-2 sentinel-3
sleep 10
docker exec pulse-ha-sentinel-1-1 redis-cli -p 26379 SENTINEL get-master-addr-by-name pulse
docker exec pulse-ha-sentinel-1-1 redis-cli -p 26379 SENTINEL sentinels pulse | grep -c name
```
**Expected:**
```
1) "redis-1"
2) "6379"
2
```
✅ Primary identified, and this sentinel sees the other two.

Point the app at Sentinel — this is the `CHANNEL_LAYERS` block from the README,
plus the same host list for the Streams layer and presence client:

```python
# pulse/settings/ha.py
REDIS_SENTINELS = [("sentinel-1", 26379), ("sentinel-2", 26379), ("sentinel-3", 26379)]
REDIS_MASTER_NAME = "pulse"

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.pubsub.RedisPubSubChannelLayer",
        "CONFIG": {
            "hosts": [{
                "sentinels": REDIS_SENTINELS,
                "master_name": REDIS_MASTER_NAME,
                "socket_timeout": 2.0,           # NOT None -- see Part E
                "socket_connect_timeout": 2.0,
                "socket_keepalive": True,
            }],
        },
    },
}
```

```bash
DJANGO_SETTINGS_MODULE=pulse.settings.ha python -c \
  "from channels.layers import get_channel_layer; import asyncio; \
   asyncio.run(get_channel_layer().send('x', {'type':'ping'}))" && echo OK
```
**Expected:**
```
OK
```
✅ The channel layer resolved the primary via Sentinel and sent a message.

---

## Part B — Patroni, etcd, HAProxy

```yaml
  etcd1: &etcd
    image: quay.io/coreos/etcd:v3.5.15
    environment:
      ETCD_INITIAL_CLUSTER: etcd1=http://etcd1:2380,etcd2=http://etcd2:2380,etcd3=http://etcd3:2380
      ETCD_INITIAL_CLUSTER_STATE: new
      ETCD_INITIAL_CLUSTER_TOKEN: pulse-etcd
      ETCD_LISTEN_PEER_URLS: http://0.0.0.0:2380
      ETCD_LISTEN_CLIENT_URLS: http://0.0.0.0:2379
      ETCD_NAME: etcd1
      ETCD_ADVERTISE_CLIENT_URLS: http://etcd1:2379
      ETCD_INITIAL_ADVERTISE_PEER_URLS: http://etcd1:2380
  etcd2: { <<: *etcd, environment: { ETCD_NAME: etcd2, ... } }
  etcd3: { <<: *etcd, environment: { ETCD_NAME: etcd3, ... } }

  patroni1: &patroni
    image: ghcr.io/zalando/spilo-16:3.3-p1
    environment:
      SCOPE: pulse
      PGVERSION: "16"
      ETCD3_HOSTS: "'etcd1:2379','etcd2:2379','etcd3:2379'"
      PATRONI_SUPERUSER_USERNAME: postgres
      PATRONI_SUPERUSER_PASSWORD: pulse
      PATRONI_REPLICATION_USERNAME: replicator
      PATRONI_REPLICATION_PASSWORD: pulse
      PATRONI_admin_PASSWORD: pulse
      PATRONI_POSTGRESQL_PARAMETERS: |
        max_connections: 200
        wal_level: replica
        synchronous_commit: 'on'
        log_min_duration_statement: 200
      # THE key HA parameters -- these determine your RTO.
      PATRONI_TTL: "30"                 # leader lock TTL
      PATRONI_LOOP_WAIT: "10"           # how often Patroni checks
      PATRONI_RETRY_TIMEOUT: "10"
    depends_on: [etcd1, etcd2, etcd3]
  patroni2: { <<: *patroni }
  patroni3: { <<: *patroni }

  pgbouncer:
    image: edoburu/pgbouncer:1.23.1
    environment:
      DB_HOST: haproxy
      DB_PORT: "5000"                   # HAProxy's write listener = current primary
      DB_USER: postgres
      DB_PASSWORD: pulse
      POOL_MODE: transaction            # => Django prepare_threshold=None (README)
      MAX_CLIENT_CONN: "10000"
      DEFAULT_POOL_SIZE: "40"
    depends_on: [haproxy]

  haproxy:
    image: haproxy:2.9-alpine
    ports: [ "5000:5000", "5001:5001", "7000:7000" ]
    volumes: [ ./haproxy.cfg:/usr/local/etc/haproxy/haproxy.cfg:ro ]
    depends_on: [patroni1, patroni2, patroni3]
```

`infra/ha/haproxy.cfg`:
```haproxy
global
    maxconn 10000

defaults
    mode tcp
    timeout connect 5s
    timeout client  30m
    timeout server  30m
    retries 3

listen stats
    mode http
    bind *:7000
    stats enable
    stats uri /

listen postgres_write
    bind *:5000
    option httpchk GET /primary
    http-check expect status 200
    # THE FENCING LINE: kills connections to a node that stops being primary.
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

```bash
docker compose -f infra/ha/compose.ha.yml up -d etcd1 etcd2 etcd3 patroni1 patroni2 patroni3 haproxy pgbouncer
sleep 40
docker exec pulse-ha-patroni1-1 patronictl -c /home/postgres/postgres.yml list
```
**Expected:**
```
+ Cluster: pulse (7398...) -----+----+-----------+
| Member   | Host       | Role    | State     | TL | Lag in MB |
+----------+------------+---------+-----------+----+-----------+
| patroni1 | 172.24.0.5 | Leader  | running   |  1 |           |
| patroni2 | 172.24.0.6 | Replica | streaming |  1 |         0 |
| patroni3 | 172.24.0.7 | Replica | streaming |  1 |         0 |
+----------+------------+---------+-----------+----+-----------+
```
```bash
curl -s localhost:7000 | grep -oE '(UP|DOWN)' | head -6
```
✅ HAProxy shows pg1 UP on the write listener, pg2/pg3 UP on read.

Point Django at PgBouncer (writes) and HAProxy (reads). The DB router from
Module 13 already sends reads to `replica`:

```python
# pulse/settings/ha.py
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "pulse", "USER": "postgres", "PASSWORD": "pulse",
        "HOST": "pgbouncer", "PORT": "6432",
        "OPTIONS": {"prepare_threshold": None},   # PgBouncer transaction pooling
        "CONN_MAX_AGE": 0,                         # let PgBouncer own pooling
    },
    "replica": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "pulse", "USER": "postgres", "PASSWORD": "pulse",
        "HOST": "haproxy", "PORT": "5001",
        "OPTIONS": {"prepare_threshold": None},
        "CONN_MAX_AGE": 0,
    },
}
```

---

## Part C — Nginx, the app tier, and the graceful drain

`infra/ha/nginx.conf`:
```nginx
events { worker_connections 65535; }
http {
  map $http_upgrade $connection_upgrade { default upgrade; '' close; }

  upstream pulse {
    hash $cookie_pulse_node consistent;      # survives NAT; remaps only 1/n
    server pulse-1:8000 max_fails=2 fail_timeout=5s;
    server pulse-2:8000 max_fails=2 fail_timeout=5s;
    server pulse-3:8000 max_fails=2 fail_timeout=5s;
  }

  server {
    listen 80;

    # Health/readiness passthrough so nginx can drop a draining node.
    location = /readyz { proxy_pass http://pulse; }

    location / {
      if ($cookie_pulse_node = "") {
        add_header Set-Cookie "pulse_node=$request_id; Path=/; HttpOnly; SameSite=Lax";
      }
      proxy_pass http://pulse;
      proxy_http_version 1.1;                  # REQUIRED for Upgrade (Module 03)
      proxy_set_header Upgrade    $http_upgrade;
      proxy_set_header Connection $connection_upgrade;
      proxy_set_header Host       $host;
      proxy_read_timeout 3600s;                # default 60s kills idle sockets
      proxy_send_timeout 3600s;
      proxy_buffering    off;
      proxy_next_upstream error timeout http_502 http_503;
    }
  }
}
```

The app service. Note `stop_grace_period: 60s` — the default 10 s is nowhere near
enough to drain sockets, and the container would be SIGKILLed mid-drain:

```yaml
  pulse-1: &pulse
    build: ../../apps/pulse
    command: >
      uvicorn pulse.asgi:application --host 0.0.0.0 --port 8000
              --workers 4 --timeout-graceful-shutdown 45
    environment:
      DJANGO_SETTINGS_MODULE: pulse.settings.ha
      PULSE_NODE_ID: pulse-1
      PULSE_DRAIN_DELAY: "6"                    # seconds to let nginx notice (2 intervals)
    stop_grace_period: 60s
    ulimits:
      nofile: { soft: 100000, hard: 100000 }
    healthcheck:
      test: ["CMD","python","-c","import urllib.request,sys; \
              sys.exit(0 if urllib.request.urlopen('http://localhost:8000/readyz').status==200 else 1)"]
      interval: 5s
      timeout: 3s
      retries: 3
      start_period: 20s          # ASGI startup; too short causes restart loops
  pulse-2: { <<: *pulse, environment: { DJANGO_SETTINGS_MODULE: pulse.settings.ha, PULSE_NODE_ID: pulse-2, PULSE_DRAIN_DELAY: "6" } }
  pulse-3: { <<: *pulse, environment: { DJANGO_SETTINGS_MODULE: pulse.settings.ha, PULSE_NODE_ID: pulse-3, PULSE_DRAIN_DELAY: "6" } }

  nginx:
    image: nginx:1.27-alpine
    ports: [ "8080:80" ]
    volumes: [ ./nginx.conf:/etc/nginx/nginx.conf:ro ]
    depends_on: [pulse-1, pulse-2, pulse-3]
```

### The drain, in code

`apps/pulse/chat/readiness.py`:
```python
class Readiness:
    def __init__(self):
        self._state = "up"          # "up" | "draining" | "unready"
    def set(self, state): self._state = state
    @property
    def ready(self): return self._state == "up"

readiness = Readiness()
```

`apps/pulse/chat/consumers.py` — register on connect, discard on disconnect:
```python
from chat.registry import registry

class ChatConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        await self.accept()
        registry.add(self)

    async def disconnect(self, code):
        registry.discard(self)
        # ... existing group_discard / presence cleanup ...

    async def send_control(self, payload):
        await self.send_json(payload)
```

`apps/pulse/chat/drain.py` — the two-phase SIGTERM handler + lifespan hook:
```python
import asyncio, os, secrets, signal, logging
from chat.registry import registry
from chat.readiness import readiness

log = logging.getLogger("pulse.drain")
DRAIN_DELAY = float(os.getenv("PULSE_DRAIN_DELAY", "6"))

async def _drain_sockets():
    log.info("draining %d sessions", len(registry))
    for consumer in list(registry._consumers):
        retry_after_ms = 1000 + secrets.randbelow(29_000)   # 1s..30s, per client
        try:
            await consumer.send_control({
                "type": "control", "action": "reconnect",
                "reason": "draining", "retry_after_ms": retry_after_ms,
            })
        except Exception:
            pass
    await asyncio.sleep(2)                                    # let frames flush
    for consumer in list(registry._consumers):
        try:
            await consumer.close(code=1001)                  # 1001 = going away
        except Exception:
            pass
    log.info("drained %d sessions", len(registry))

def install_sigterm_drain(loop, uvicorn_default_handler):
    """Phase 1 flips readiness and waits; then we defer to Uvicorn's own
    shutdown, which fires lifespan.shutdown where Phase 2 runs."""
    def handler():
        registry.draining = True
        readiness.set("draining")            # /readyz -> 503; nginx will notice
        async def phased():
            await asyncio.sleep(DRAIN_DELAY)  # nginx healthcheck removes us
            uvicorn_default_handler()         # -> stop accept(), fire lifespan.shutdown
        loop.create_task(phased())
    loop.add_signal_handler(signal.SIGTERM, handler)

async def lifespan_shutdown():
    """Called from pulse/asgi.py on the ASGI lifespan.shutdown message."""
    await _drain_sockets()
```

`apps/pulse/chat/health.py` — the readiness view, which also carries the
**capacity** signal used by the brownout drill (Part H):
```python
from django.http import JsonResponse
from chat.readiness import readiness
from chat.metrics import outbound_queue_depth, fanout_p99_ms

async def readyz(request):
    if not readiness.ready:
        return JsonResponse({"status": "draining"}, status=503)
    # Shed BEFORE we become the reason everyone's latency is bad.
    queued, p99 = outbound_queue_depth(), fanout_p99_ms()
    if queued > 5000 or p99 > 2000:
        return JsonResponse({"status": "capacity", "outbound_queue": queued,
                             "p99_ms": p99}, status=503)
    return JsonResponse({"status": "up", "outbound_queue": queued}, status=200)

async def healthz(request):        # LIVENESS: is the process alive at all?
    return JsonResponse({"status": "alive"}, status=200)
```

Wire the lifespan hook in `apps/pulse/pulse/asgi.py` (a thin ASGI wrapper around
Channels' `ProtocolTypeRouter`). The reference wrapper is in
[`solutions/`](./solutions/solution.md).

```bash
docker compose -f infra/ha/compose.ha.yml up -d --wait
docker compose -f infra/ha/compose.ha.yml ps --format 'table {{.Name}}\t{{.Status}}'
```
**Expected — 15 services, all healthy:**
```
pulse-ha-etcd1-1       Up 3 minutes
pulse-ha-haproxy-1     Up 2 minutes
pulse-ha-nginx-1       Up 1 minute
pulse-ha-patroni1-1    Up 3 minutes (healthy)
pulse-ha-pgbouncer-1   Up 2 minutes
pulse-ha-pulse-1-1     Up 1 minute (healthy)
...
```

Confirm the drain works in isolation before you trust it under load:
```bash
# Open one socket, then stop the node it landed on.
docker compose -f infra/ha/compose.ha.yml stop -t 60 pulse-1 &
docker logs -f pulse-ha-pulse-1-1 2>&1 | grep -m2 -E 'draining|drained'
```
**Expected:**
```
pulse.drain  draining 1 sessions
pulse.drain  drained 1 sessions
```
```bash
docker compose -f infra/ha/compose.ha.yml up -d --wait pulse-1
```

---

## Part D — The drill harness

`code/drill.sh` — every drill uses this, so the numbers are comparable.

```bash
#!/usr/bin/env bash
# Usage: ./drill.sh <name> <command-to-inject-failure> [recovery-command]
set -euo pipefail
NAME="$1"; INJECT="$2"; RECOVER="${3:-}"
OUT=/tmp/drill-$NAME

# 1. Steady state
k6 run -e HOST=localhost:8080 -e ROOMS=100 -e SEND_EVERY=5000 --vus 10000 --duration 6m \
       --summary-export="$OUT-k6.json" \
       ../../06-load-testing-harness/code/pulse-load.js &
K6=$!
python3 ./code/sequence_probe.py "$OUT-seq.txt" &   # numbered messages, counts gaps
PROBE=$!
sleep 120                                            # establish a baseline

# 2. Inject
echo ">>> $(date +%s.%N) INJECT: $INJECT"
INJECT_AT=$(date +%s.%N)
eval "$INJECT"

# 3. Watch for recovery (first successful send after failure)
RECOVERED_AT=$(python3 ./code/await_recovery.py)
echo ">>> $(date +%s.%N) RECOVERED"

[ -n "$RECOVER" ] && eval "$RECOVER"
sleep 120
kill $K6 $PROBE 2>/dev/null || true; wait || true

# 4. Report
RTO=$(echo "$RECOVERED_AT - $INJECT_AT" | bc)
SENT=$(grep -c SENT "$OUT-seq.txt")
GOT=$(grep -c RECV "$OUT-seq.txt")
printf '%-28s RTO=%6.2fs  RPO=%d msgs (%d sent, %d received)  p99=%sms\n' \
  "$NAME" "$RTO" "$((SENT-GOT))" "$SENT" "$GOT" \
  "$(jq -r '.metrics.fanout_latency_ms["p(99)"]|round' "$OUT-k6.json")" \
  | tee "$OUT.summary"
```

The Python sequence probe (`code/sequence_probe.py`) is a `websockets`-based
client that sends numbered messages to a probe room and logs `SENT n` / `RECV n`,
so a gap is a lost message. It's ~40 lines; the reference is in `code/`.

---

## Part E — Drills 1–3: Redis

```bash
./code/drill.sh "redis-primary-kill" \
  "docker kill pulse-ha-redis-1-1" \
  "docker start pulse-ha-redis-1-1"
```
**Expected:**
```
>>> INJECT: docker kill pulse-ha-redis-1-1
sentinel-1: +sdown master pulse redis-1 6379
sentinel-1: +odown master pulse redis-1 6379 #quorum 2/2
sentinel-1: +switch-master pulse redis-1 6379 redis-2 6379
redis-primary-kill           RTO=  7.41s  RPO=0 msgs (28,104 sent, 28,104 received)  p99=261ms
```
✅ **7.4 seconds, zero loss.** The Streams backlog (Module 09) buffered
everything; nothing was in flight and lost because the outbox (Module 13) held the
record. Note the p99 barely moved from the 261 ms baseline — a `kill` is the
*easy* failure.

Now the mean one:
```bash
./code/drill.sh "redis-primary-pause" \
  "docker pause pulse-ha-redis-1-1; sleep 30; docker unpause pulse-ha-redis-1-1"
```
**Expected — with `socket_timeout` still at the `redis-py` default of `None`:**
```
redis-primary-pause          RTO= 14.82s  RPO=0 msgs (28,001 sent, 28,001 received)  p99=8,940ms
```
✅ **Twice the RTO and a 42× worse p99**, because a paused Redis holds every
client's TCP connection open. The event loop on each worker is stuck inside a
`redis-py` call with **no timeout**, so it cannot even service its other
connections until the OS or the unpause frees it. This is the Python failure the
README warned about: `socket_timeout=None` turns one frozen dependency into a
frozen worker.

Tune for it — the two lines already in the Part A settings:
```python
"socket_timeout": 2.0,           # was None (no timeout!)
"socket_connect_timeout": 2.0,
```
```bash
./code/drill.sh "redis-primary-pause-tuned" \
  "docker pause pulse-ha-redis-1-1; sleep 30; docker unpause pulse-ha-redis-1-1"
```
```
redis-primary-pause-tuned    RTO=  9.10s  RPO=0 msgs  p99=2,180ms
```
✅ **RTO 14.8 → 9.1 s and p99 8,940 → 2,180 ms**, for two config lines. The
timeout fires, `redis-py` raises, `channels_redis` reconnects through Sentinel to
the new primary, and the event loop keeps serving everyone else in the meantime.

The **split-brain** drill:
```bash
./code/drill.sh "redis-partition" \
  "docker network disconnect pulse-ha_default pulse-ha-redis-1-1; sleep 40" \
  "docker network connect pulse-ha_default pulse-ha-redis-1-1"
```
**Expected:**
```
redis-partition              RTO=  8.02s  RPO=0 msgs
```
Then, after reconnecting:
```bash
docker exec pulse-ha-redis-1-1 redis-cli INFO replication | head -3
```
**Expected — the old primary demoted itself:**
```
# Replication
role:slave
master_host:redis-2
```
✅ **No split-brain.** Sentinel reconfigured the returning node as a replica.

> Note: an isolated Redis primary **does** accept writes until a sentinel
> reconfigures it. Those writes are then discarded on demotion. For the Pulse
> fan-out that's acceptable — the outbox republishes and client dedup (Module 09)
> absorbs the rest. For a datastore it would not be, which is why
> `min-replicas-to-write 1` exists.

---

## Part F — Drills 4–6: Postgres

```bash
./code/drill.sh "pg-primary-kill" \
  "docker kill pulse-ha-patroni1-1" \
  "docker start pulse-ha-patroni1-1"
```
**Expected:**
```
patroni2: promoted self to leader by acquiring session lock
haproxy:  Server postgres_write/pg1 is DOWN
haproxy:  Server postgres_write/pg2 is UP
pg-primary-kill              RTO= 24.10s  RPO=0 msgs (27,904 sent, 27,904 received)  p99=4,120ms
```
✅ **24 seconds.** Slower than Redis, and the components are visible:

```
t=0.0   patroni1 killed
t=10.2  patroni2's loop_wait tick notices the leader key is stale
t=20.1  leader key TTL (30s from last renewal, ~20s remaining) expires
t=21.4  patroni2 acquires the lock and promotes
t=24.1  HAProxy's health check (inter 3s, rise 2) marks pg2 UP
```

**The TTL dominates.** Tune it:
```yaml
PATRONI_TTL: "15"
PATRONI_LOOP_WAIT: "5"
PATRONI_RETRY_TIMEOUT: "5"
```
```
pg-primary-kill-tuned        RTO= 11.82s  RPO=0 msgs  p99=2,010ms
```
✅ **24.1 → 11.8 s.** The cost: a more aggressive TTL means a brief etcd hiccup
can trigger an unnecessary failover. `TTL >= loop_wait * 2 + retry_timeout` is the
constraint; 15/5/5 satisfies it with no margin. **15 seconds is about as low as is
safe.**

The pause version:
```bash
./code/drill.sh "pg-primary-pause" \
  "docker pause pulse-ha-patroni1-1; sleep 45; docker unpause pulse-ha-patroni1-1"
```
**Expected:**
```
pg-primary-pause-tuned       RTO= 12.40s  RPO=0 msgs  p99=2,290ms
```
✅ **Barely worse than kill**, because Patroni's leader lock is TTL-based — a
paused Patroni stops renewing, which is indistinguishable from a dead one. This is
a genuinely well-designed failure detector, and the contrast with Redis's pause
behaviour is the lesson: Patroni fences on *time*, so a freeze and a crash look
identical to it.

**Fencing check** — the critical one:
```bash
docker unpause pulse-ha-patroni1-1
sleep 2
docker exec pulse-ha-patroni1-1 psql -U postgres -c \
  "INSERT INTO chat_message (id,room_id,seq,sender,client_id,body) VALUES (999,'x',999,'x','x','split-brain');"
```
**Expected:**
```
ERROR:  cannot execute INSERT in a read-only transaction
```
✅ **The returning node demoted itself to a replica before accepting a single
write.** And HAProxy's `on-marked-down shutdown-sessions` killed PgBouncer's
existing connections to it, so no in-flight transaction could sneak through.

Check for divergence:
```bash
docker exec pulse-ha-patroni1-1 patronictl -c /home/postgres/postgres.yml list
```
```
| patroni1 | Replica | streaming |  2 |         0 |
| patroni2 | Leader  | running   |  2 |           |
```
✅ Timeline 2, zero lag, no `pg_rewind` needed.

---

## Part G — Drills 7–9: the app tier

```bash
./code/drill.sh "app-node-kill" "docker kill pulse-ha-pulse-1-1" "docker start pulse-ha-pulse-1-1"
```
**Expected:**
```
app-node-kill                RTO=  4.20s  RPO=0 msgs  p99=1,840ms
  connections dropped: 3,341
  reconnect peak: 214/s
  time for all to reconnect: 34s
```
✅ Zero **message** loss (the backbone held everything), but **3,341 clients were
disconnected** — unavoidable, since you cannot migrate a socket. What matters is
that they came back at 214/s rather than all at once, because Module 17's client
uses full jitter. Note a `kill` gives clients no close frame (the process is
gone); they detect the dead TCP connection and reconnect on their own timer.

Prove the jitter matters — set the client to a fixed 1 s retry:
```bash
PULSE_CLIENT_JITTER=false ./code/drill.sh "app-node-kill-no-jitter" \
  "docker kill pulse-ha-pulse-1-1" "docker start pulse-ha-pulse-1-1"
```
```
app-node-kill-no-jitter      RTO= 41.80s  RPO=1,204 msgs  p99=12,400ms
  reconnect peak: 3,341/s   <-- all at once
  pulse-2 and pulse-3 both hit their outbound channel-layer queue capacity
```
✅ **The herd took down the surviving nodes.** RTO went from 4.2 s to 41.8 s and
1,204 messages were lost — **caused entirely by the recovery, not the failure.**

### Rolling deploy — the drill that matters most

```bash
./code/drill.sh "rolling-deploy" "./code/rolling_deploy.sh"
```

`code/rolling_deploy.sh`:
```bash
#!/usr/bin/env bash
for node in pulse-1 pulse-2 pulse-3; do
  echo ">>> draining $node"
  docker compose -f infra/ha/compose.ha.yml stop -t 60 "$node"   # SIGTERM, 60s grace
  docker compose -f infra/ha/compose.ha.yml up -d --wait "$node"
  sleep 45                                                        # let clients settle
done
```

With the graceful drain **disabled** (`PULSE_DRAIN_DELAY=0` and no lifespan hook,
so Uvicorn just stops):
```
rolling-deploy-hard          RTO= 18.40s  RPO=2,841 msgs  p99=9,120ms
  10,000 connections dropped with code 1006 (no close frame)
  clients waited for TCP timeout: median 47s to notice
```

With the drain **enabled** (the Part C code — readiness flip, `DRAIN_DELAY`,
control frame, `close(1001)`):
```
rolling-deploy-graceful      RTO=  0.00s  RPO=0 msgs  p99=290ms
  10,000 connections closed with code 1001 + retry_after_ms
  clients noticed immediately (median 4ms)
  reconnect peak: 189/s, spread over 30s
```

✅ **Zero downtime, zero message loss, p99 barely moved from the 261 ms
baseline.** A full rolling deploy of every node was invisible to users.

| | Hard restart | Graceful drain |
|---|-------------|----------------|
| RTO | 18.4 s | **0 s** |
| Messages lost | 2,841 | **0** |
| Close code seen by clients | 1006 (unknown) | **1001 + retry_after** |
| Time for clients to notice | median 47 s | **median 4 ms** |
| Reconnect peak | 3,341/s | **189/s** |
| p99 during | 9,120 ms | **290 ms** |

> This is the payoff for **five** separate decisions: `stop_grace_period: 60s`
> (Compose), `--timeout-graceful-shutdown 45` (Uvicorn), the SIGTERM handler that
> flips readiness *before* Uvicorn stops accepting (`DRAIN_DELAY`), the `control`
> frame in the protocol (Module 05), and full-jitter reconnect in the client
> (Module 17). **No single one of them would have been enough** — drop the
> `DRAIN_DELAY` and you still reject handshakes during the nginx-notice window;
> drop the control frame and clients wait for a TCP timeout.

---

## Part H — Drills 10–11: the nasty ones

### Brownout — slow, not dead

```bash
./code/drill.sh "app-node-brownout" \
  "docker update --cpus 0.1 pulse-ha-pulse-1-1; sleep 60" \
  "docker update --cpus 2.0 pulse-ha-pulse-1-1"
```
**Expected:**
```
app-node-brownout            RTO= 60.00s  RPO=4,102 msgs  p99=14,200ms
```

✅ **The worst result in the entire lab**, and it's the failure nobody tests for.

Why it's worse than a kill:
- The node is **still healthy** by every liveness check. `/healthz` returns 200,
  just slowly. nginx keeps sending it traffic.
- Its clients are stuck on a worker that can't keep up, and they don't disconnect
  because the socket is fine.
- It holds Redis stream entries in its PEL without acking, so `XPENDING` grows.
- The GIL makes it worse: 0.1 CPU means the single core each worker runs on is
  contended, so even the async event loop can't turn over — it never drains the
  backlog it accumulated.

**The mitigation is already wired in Part C's `readyz`: make readiness reflect
*capacity*, not just liveness.** The view returns 503 when
`outbound_queue_depth() > 5000` or `fanout_p99_ms() > 2000`:

```python
async def readyz(request):
    if not readiness.ready:
        return JsonResponse({"status": "draining"}, status=503)
    queued, p99 = outbound_queue_depth(), fanout_p99_ms()
    if queued > 5000 or p99 > 2000:                      # shed BEFORE we hurt everyone
        return JsonResponse({"status": "capacity"}, status=503)
    return JsonResponse({"status": "up"}, status=200)
```
```bash
./code/drill.sh "app-node-brownout-shed" \
  "docker update --cpus 0.1 pulse-ha-pulse-1-1; sleep 60" \
  "docker update --cpus 2.0 pulse-ha-pulse-1-1"
```
```
app-node-brownout-shed       RTO= 11.20s  RPO=0 msgs  p99=418ms
  pulse-1 readiness 503 at t=8.4s
  nginx removed it at t=11.2s
  its 3,341 clients reconnected to pulse-2/pulse-3 over 28s
```
✅ **RPO 4,102 → 0 and p99 14,200 → 418 ms.** The node took itself out of rotation
before it became everyone's problem.

> ⚠️ **This is exactly why capacity signals go on *readiness*, not *liveness*.** On
> liveness, all three nodes would fail simultaneously under a global load spike and
> the container runtime would restart them into a restart loop — turning a capacity
> problem into a total outage. Readiness sheds traffic; liveness kills the process.

### etcd quorum loss

```bash
./code/drill.sh "etcd-quorum-loss" \
  "docker kill pulse-ha-etcd2-1 pulse-ha-etcd3-1; sleep 45" \
  "docker start pulse-ha-etcd2-1 pulse-ha-etcd3-1"
```
**Expected:**
```
patroni1: Error communicating with DCS: etcdserver: request timed out
patroni1: DCS is not accessible, demoting self to read-only
etcd-quorum-loss             RTO= 45.20s  RPO=0 msgs  p99=8,410ms
  ALL WRITES REJECTED for 45s; reads continued
```

✅ **Losing 2 of 3 etcd nodes made the whole database read-only.** That is
correct — without a quorum, Patroni cannot know whether it's still the leader, so
it demotes rather than risk split-brain.

But note what it means: **etcd is now a single point of failure for your
database's writability.** Chat reads kept working (replicas serve reads, and the
Django DB router sends history queries there), so users could see history but not
send. The mitigation is not clever configuration — it's **running etcd on
separate failure domains from Postgres**, a Module 19 (Kubernetes topology spread)
concern.

---

## Part I — The scoreboard

```bash
cat /tmp/drill-*.summary | sort -k2 -rn
```

**Expected:**

| Drill | RTO | RPO | p99 during | Verdict |
|-------|-----|-----|-----------|---------|
| Rolling deploy (graceful) | **0.0 s** | **0** | 290 ms | ✅ invisible |
| App node kill | 4.2 s | 0 | 1,840 ms | ✅ |
| Redis primary kill | 7.4 s | 0 | 261 ms | ✅ |
| Redis partition | 8.0 s | 0 | 890 ms | ✅ no split-brain |
| Redis primary pause (tuned) | 9.1 s | 0 | 2,180 ms | ✅ |
| App brownout (with shedding) | 11.2 s | 0 | 418 ms | ✅ |
| PG primary kill (tuned) | 11.8 s | 0 | 2,010 ms | ✅ |
| PG primary pause (tuned) | 12.4 s | 0 | 2,290 ms | ✅ |
| etcd quorum loss | **45.2 s** | 0 | 8,410 ms | ⚠️ writes down |
| *App node kill, no jitter* | *41.8 s* | *1,204* | *12,400 ms* | ❌ herd |
| *Rolling deploy, hard* | *18.4 s* | *2,841* | *9,120 ms* | ❌ |
| *Brownout, no shedding* | *60.0 s* | *4,102* | *14,200 ms* | ❌ worst |

**Target was RTO < 30 s, RPO = 0.**

✅ **Met on every drill except etcd quorum loss**, which is a deliberate
availability-for-consistency trade and the correct behaviour.

Record it:
```markdown
## Module 18 — HA drills (Django/Uvicorn)

Worst RTO (excluding deliberate etcd quorum trade): 12.4s
RPO: 0 on every drill once tuned
Three configuration changes worth the most:
  1. channels_redis socket_timeout=2.0  -> pause RTO 14.8s -> 9.1s, p99 8,940 -> 2,180ms
  2. PATRONI_TTL 30 -> 15               -> PG RTO 24.1s -> 11.8s
  3. capacity signal on READINESS       -> brownout RPO 4,102 -> 0
Graceful ASGI drain + jittered reconnect turns a rolling deploy from
  18.4s/2,841 lost into 0s/0 lost.
```

---

## What you built and proved

- A 15-container HA stack: Redis Sentinel, Patroni + etcd + HAProxy, PgBouncer,
  three Uvicorn app nodes behind a WebSocket-aware nginx.
- **A graceful ASGI drain built from three Python pieces** — a per-process
  connection registry, an ASGI lifespan shutdown hook, and a two-phase SIGTERM
  handler that flips readiness *before* Uvicorn stops accepting — plus Uvicorn's
  `--timeout-graceful-shutdown`.
- **Eleven chaos drills**, each with a load test running and a measured RTO/RPO.
- **The `pause` vs `kill` distinction**, quantified: pause was 2× the RTO and 42×
  the p99 until `socket_timeout` was set — the Python-specific version of the
  lesson, since the `redis-py` default is no timeout at all.
- **Fencing proven twice** — a returning Redis primary demoted to replica, a
  returning Patroni node rejecting writes with `read-only transaction`.
- **A zero-downtime rolling deploy**, and the five independent decisions that made
  it possible.
- **The brownout**, the failure nobody tests, which was the worst result until
  capacity was wired to readiness.

Now do [`challenge.md`](./challenge.md).

Then: [Module 19 — Kubernetes HA & Multi-Region](../19-kubernetes-ha-and-multiregion/).
