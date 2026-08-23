# Cheatsheet — Docker & High Availability

---

## What "HA" actually means

Not "it never breaks." It's two numbers:

- **RTO** (Recovery Time Objective) — how long you're degraded.
- **RPO** (Recovery Point Objective) — how much data you lose.

| Design | RTO | RPO |
|--------|-----|-----|
| Single node + backups | Hours | Up to backup interval |
| Single node + streaming replica, manual promote | Minutes (a human must wake) | ~0 |
| Sentinel / Patroni auto-failover | 10–30 s | 0 with sync repl, ~ms with async |
| Multi-region active/active | ~0 | Conflict resolution becomes *your* problem |

Every step down that table costs money and complexity. Pick deliberately.

---

## The three HA rules

1. **Quorum needs odd numbers.** 3 sentinels, 3 etcd nodes, 3 Kafka controllers.
   Two nodes cannot agree which one is dead.
2. **Failover requires fencing.** If a demoted primary can still accept writes,
   you have split-brain, and split-brain is worse than downtime because it's
   silent.
3. **HA is only real if you've tested it.** An untested failover path is a
   theory. Module 18 is entirely drills.

---

## Compose fundamentals for HA

### Healthchecks are not optional

`depends_on` without `condition: service_healthy` only waits for the container to
*start*, not to be *usable*. This is the #1 cause of "it works on the second
`up`."

```yaml
services:
  postgres:
    image: postgres:16-alpine
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U pulse -d pulse"]
      interval: 5s
      timeout: 3s
      retries: 10
      start_period: 10s

  redis:
    image: redis:7-alpine
    healthcheck:
      test: ["CMD", "redis-cli", "PING"]
      interval: 5s
      timeout: 3s
      retries: 10

  app:
    depends_on:
      postgres: { condition: service_healthy }
      redis:    { condition: service_healthy }
    healthcheck:
      test: ["CMD", "curl", "-fsS", "http://localhost:8080/actuator/health/readiness"]
      interval: 10s
      timeout: 3s
      retries: 3
      start_period: 40s          # JVM startup — without this you get restart loops
```

> `start_period` failures don't count toward `retries`. For a Spring Boot app,
> set it generously or Docker will kill your app while it's still booting.

### Scaling and dependencies

```bash
docker compose up -d --scale app=3
docker compose ps
docker compose logs -f --tail=50 app
docker compose exec app sh
docker compose restart app
docker compose down -v            # -v also drops volumes. You want this between drills.
```

### Resource limits — so one container can't eat the host

```yaml
    deploy:
      resources:
        limits:   { cpus: '2.0', memory: 2G }
        reservations: { cpus: '0.5', memory: 512M }
```
(Compose v2 honours `deploy.resources.limits` without Swarm.)

For the JVM, also tell it about the limit:
```yaml
    environment:
      JAVA_TOOL_OPTIONS: "-XX:MaxRAMPercentage=75 -XX:+UseZGC -XX:+ZGenerational"
```

### Graceful shutdown — the WebSocket-specific bit

```yaml
    stop_grace_period: 60s      # default is 10s — far too short to drain sockets
    stop_signal: SIGTERM
```
```properties
server.shutdown=graceful
spring.lifecycle.timeout-per-shutdown-phase=45s
```
Without this, a deploy hard-kills every open socket and 30,000 clients reconnect
simultaneously. See "thundering herd" below.

---

## Topology: the full HA stack

```
                         ┌──────────┐
     clients  ──────────▶│  nginx   │  sticky by ip_hash / cookie
                         └────┬─────┘
                  ┌───────────┼───────────┐
              ┌───▼───┐   ┌───▼───┐   ┌───▼───┐
              │ app-1 │   │ app-2 │   │ app-3 │
              └───┬───┘   └───┬───┘   └───┬───┘
          ┌───────┴───────────┴───────────┴───────┐
          │                                       │
   ┌──────▼───────┐                       ┌───────▼────────┐
   │ Redis Cluster│                       │    HAProxy     │
   │  3 primaries │                       │  :5000 write   │
   │  3 replicas  │                       │  :5001 read    │
   └──────────────┘                       └───────┬────────┘
   (fan-out + state)                    ┌─────────┼─────────┐
                                   ┌────▼───┐ ┌───▼────┐ ┌──▼─────┐
                                   │patroni1│ │patroni2│ │patroni3│
                                   │primary │ │replica │ │replica │
                                   └────┬───┘ └───┬────┘ └──┬─────┘
                                        └─────────┼─────────┘
                                              ┌───▼───┐
                                              │ etcd  │ (3 nodes)
                                              └───────┘
```

---

## Nginx: WebSocket-aware load balancing

```nginx
map $http_upgrade $connection_upgrade {
    default upgrade;
    ''      close;
}

upstream pulse {
    ip_hash;                       # sticky. Or use a cookie-based hash.
    server app-1:8080 max_fails=3 fail_timeout=10s;
    server app-2:8080 max_fails=3 fail_timeout=10s;
    server app-3:8080 max_fails=3 fail_timeout=10s;
}

server {
    listen 80;
    location /ws {
        proxy_pass http://pulse;
        proxy_http_version 1.1;                     # REQUIRED — 1.0 can't upgrade
        proxy_set_header Upgrade    $http_upgrade;
        proxy_set_header Connection $connection_upgrade;
        proxy_set_header Host       $host;
        proxy_set_header X-Real-IP  $remote_addr;

        proxy_read_timeout  3600s;    # default 60s KILLS IDLE SOCKETS
        proxy_send_timeout  3600s;
        proxy_buffering     off;      # don't buffer a stream
    }
}
```

> **The two classic WebSocket-behind-nginx bugs:** forgetting
> `proxy_http_version 1.1` (handshake fails outright) and leaving
> `proxy_read_timeout` at 60 s (sockets die every minute and you blame the
> client). Both are in Module 18's deliberate-breakage list.

**Sticky sessions:** `ip_hash` is easy but breaks behind carrier NAT (thousands
of users share an IP) and rebalances when the upstream list changes. Once you
have the Redis backplane, you arguably don't *need* stickiness at all — that's a
Module 07 discussion, and the answer is "you still want it, for the session
state you keep locally."

---

## Redis Sentinel in Compose

```yaml
  redis-1:
    image: redis:7-alpine
    command: redis-server --appendonly yes
  redis-2:
    image: redis:7-alpine
    command: redis-server --appendonly yes --replicaof redis-1 6379
  redis-3:
    image: redis:7-alpine
    command: redis-server --appendonly yes --replicaof redis-1 6379
  sentinel-1: &sentinel
    image: redis:7-alpine
    command: redis-sentinel /etc/redis/sentinel.conf
    volumes: [ ./sentinel.conf:/etc/redis/sentinel.conf ]
  sentinel-2: *sentinel
  sentinel-3: *sentinel
```

> ⚠️ Sentinel **rewrites its own config file**. Mounting the same read-only file
> into three sentinels fails. Copy it per-container in an entrypoint, or use
> three separate files. This bites everyone once.

**Drill it:**
```bash
docker compose exec sentinel-1 redis-cli -p 26379 SENTINEL get-master-addr-by-name pulse
docker kill redis-1                     # or: docker pause redis-1  (nastier — no TCP RST)
watch -n1 'docker compose exec -T sentinel-1 redis-cli -p 26379 SENTINEL get-master-addr-by-name pulse'
```
**Expected:** after `down-after-milliseconds` + election, the address flips to
redis-2 or redis-3.

`docker pause` is the better drill: `kill` closes the socket cleanly, so clients
notice instantly. `pause` looks like a hung node — which is what actually happens
in production, and much harder to handle.

---

## Patroni + etcd + HAProxy

```yaml
  haproxy:
    image: haproxy:2.9-alpine
    ports: [ "5000:5000", "5001:5001", "7000:7000" ]
```

```haproxy
listen postgres_write
    bind *:5000
    option httpchk GET /primary          # Patroni's REST API answers 200 only on the primary
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
    server pg1 patroni1:5432 check port 8008
    server pg2 patroni2:5432 check port 8008
    server pg3 patroni3:5432 check port 8008
```

`on-marked-down shutdown-sessions` is what kills connections to a demoted
primary — that's your fencing at the proxy layer.

```bash
docker compose exec patroni1 patronictl -c /etc/patroni.yml list
docker compose exec patroni1 patronictl -c /etc/patroni.yml switchover   # planned
docker compose exec patroni1 patronictl -c /etc/patroni.yml failover     # unplanned
docker compose exec etcd1 etcdctl get --prefix /service/pulse
curl -s localhost:8008/primary -o /dev/null -w '%{http_code}\n'
```

---

## Chaos drill commands

```bash
docker kill <c>                      # SIGKILL — instant, clean TCP close
docker pause <c>                     # freeze — looks like a hang. The mean one.
docker stop -t 30 <c>                # SIGTERM then SIGKILL — tests graceful shutdown
docker network disconnect <net> <c>  # partition it. Split-brain testing.
docker network connect <net> <c>     # heal it — now watch reconciliation
docker update --cpus 0.1 <c>         # brownout: slow, not dead. Often worse.
```

Inside a container (needs `--cap-add=NET_ADMIN`):
```bash
tc qdisc add dev eth0 root netem delay 200ms 50ms      # latency + jitter
tc qdisc add dev eth0 root netem loss 5%               # packet loss
tc qdisc del dev eth0 root                             # heal
```

**Always run a load test *during* the drill.** A failover that's invisible with
zero traffic can drop 40% of messages at 5k msg/s. The whole point is the number.

---

## Container image hygiene for the JVM

```dockerfile
# ---- build ----
FROM eclipse-temurin:21-jdk-alpine AS build
WORKDIR /src
COPY pom.xml .
RUN mvn -B dependency:go-offline          # cached layer — deps change rarely
COPY src ./src
RUN mvn -B -DskipTests package

# ---- run ----
FROM eclipse-temurin:21-jre-alpine
RUN addgroup -S app && adduser -S app -G app
USER app
WORKDIR /app
COPY --from=build /src/target/pulse.jar app.jar
EXPOSE 8080
ENV JAVA_TOOL_OPTIONS="-XX:MaxRAMPercentage=75 -XX:+UseZGC -XX:+ZGenerational \
                       -XX:+HeapDumpOnOutOfMemoryError -XX:HeapDumpPath=/tmp"
ENTRYPOINT ["java","-jar","/app/app.jar"]
```

- **Copy `pom.xml` and resolve dependencies before copying `src`.** Otherwise
  every source change re-downloads the internet.
- **`MaxRAMPercentage`, not `-Xmx`.** The JVM reads the cgroup limit; a
  percentage adapts when you change the container limit.
- **Run as non-root.**
- **Never `latest`.** Pin digests for anything you'd page someone about.

### File descriptors — the limit that surprises everyone

One WebSocket = one FD. 50,000 connections needs > 50,000 FDs.

```yaml
    ulimits:
      nofile: { soft: 100000, hard: 100000 }
```
```bash
docker compose exec app sh -c 'ulimit -n; ls /proc/1/fd | wc -l'
```
**Symptom if you skip it:** connections stop being accepted at almost exactly
1024 or 65535, and the log says `Too many open files`.

Also raise the kernel's connection backlog on the host for load tests:
```bash
sysctl -w net.core.somaxconn=65535
sysctl -w net.ipv4.tcp_max_syn_backlog=65535
sysctl -w net.ipv4.ip_local_port_range="10000 65535"   # for the LOAD GENERATOR
```
The load generator runs out of ephemeral ports before the server runs out of
capacity — a classic false ceiling. Module 06 covers it.

---

## Thundering herd on reconnect

When a node dies, every client it held reconnects **at the same instant**.

```js
// WRONG — synchronized retry storm
setTimeout(reconnect, 1000);

// RIGHT — exponential backoff with full jitter
const delay = Math.random() * Math.min(cap, base * 2 ** attempt);
```

Server-side defenses:
- Rate-limit the handshake endpoint, not just messages.
- Return `Retry-After` on 503.
- Stagger deploys; never restart all replicas at once (`maxUnavailable: 1`).
- Drain gracefully so clients get a **close frame with a code**, letting them
  reconnect deliberately instead of detecting a dead TCP socket 60 s later.
