# Module 18 — Compose HA & Chaos Drills

**Goal:** Build genuine high availability in Docker Compose for the Django stack —
Redis Sentinel and Cluster, Patroni-managed Postgres, HAProxy, PgBouncer, and a
fleet of Uvicorn app instances behind a WebSocket-aware nginx that **drains
gracefully** — and then kill every component while a load test runs, and count
what it cost.

⏱️ ~7 hours · **Prerequisites:** Modules 00–17.

> This is the Django/asyncio twin of
> [`spring-boot-chat-course/18-compose-ha-and-chaos`](../../spring-boot-chat-course/18-compose-ha-and-chaos/).
> The infrastructure — Sentinel, Patroni, etcd, HAProxy, the eleven drills, the
> RTO/RPO framing — is **identical**, because failover time is a property of the
> datastore's quorum protocol, not of the application runtime. What changes is the
> app tier: instead of Spring's `@PreDestroy` + `server.shutdown: graceful`, you
> drain **Uvicorn workers** through the **ASGI lifespan protocol**, a SIGTERM
> handler, and a per-process consumer registry. The graceful-drain section is
> where the Python model earns its own chapter.

---

## HA is two numbers, not a checkbox

| | Definition |
|---|-----------|
| **RTO** — Recovery Time Objective | How long you're degraded |
| **RPO** — Recovery Point Objective | How much data you lose |

Every design is a point on that plane, and every point has a price:

| Design | RTO | RPO | Cost |
|--------|-----|-----|------|
| Single node + nightly backups | **hours** | up to 24 h | 1× |
| Single node + streaming replica, manual promote | minutes (a human must wake) | ~0 | 2× |
| **Automatic failover (Sentinel / Patroni)** | **10–30 s** | 0 (sync) / ~ms (async) | 3× |
| Multi-region active/active | ~0 | **conflict resolution becomes your problem** | 6×+ |

Pulse targets the third row: **RTO under 30 seconds, RPO zero.** The lab measures
whether it achieves that, which is a different question from whether it was
*configured* for it. Configuration is a hypothesis; the drill is the experiment.

---

## The three rules

**1. Quorum needs odd numbers.**
Two nodes cannot agree which one is dead. Three sentinels with quorum 2, three
etcd nodes, three Patroni members. Two of anything is not HA — it's two single
points of failure that can disagree.

**2. Failover requires fencing.**
If a demoted primary can still accept writes, you have **split-brain**: two nodes
both believing they're primary, both accepting writes, silently diverging. That
is worse than downtime, because downtime is visible and divergence is not. You
find out about divergence weeks later, from a customer.

**3. HA is only real if you've tested it.**
An untested failover path is a theory. Most of this module is drills, because the
configuration is the easy part and the behaviour *under load* is the part that
surprises you. A failover that is invisible with zero traffic can drop 40% of
messages at 5,000 msg/s.

---

## The topology

```
                         ┌──────────┐
     clients  ──────────▶│  nginx   │  cookie-consistent-hash, WS-aware, drains
                         └────┬─────┘
                  ┌───────────┼───────────┐
              ┌───▼───┐   ┌───▼───┐   ┌───▼───┐
              │pulse-1│   │pulse-2│   │pulse-3│  Uvicorn+uvloop, graceful ASGI drain
              └───┬───┘   └───┬───┘   └───┬───┘
          ┌───────┴───────────┴───────────┴───────┐
          │                                       │
   ┌──────▼───────┐                       ┌───────▼────────┐
   │ Redis         │                       │    HAProxy     │
   │  3 primaries  │                       │  :5000 write   │
   │  3 replicas   │                       │  :5001 read    │
   │  (Cluster)    │                       └───────┬────────┘
   └───────────────┘                    ┌──────────┼──────────┐
   fan-out + state                 ┌────▼───┐ ┌────▼───┐ ┌────▼───┐
   (channel layer +                │patroni1│ │patroni2│ │patroni3│
    Streams + presence)            │primary │ │replica │ │replica │
                                   └────┬───┘ └────┬───┘ └────┬───┘
                                        └──────────┼──────────┘
                                              ┌────▼────┐
                                              │  etcd   │ 3 nodes
                                              └─────────┘
                                        (PgBouncer sits in front of :5000)
```

Fifteen containers. Module 00's resource budget said ~9 GB; the lab has a
low-memory path that swaps Cluster for Sentinel and drops to 2 app nodes.

---

## Redis: Sentinel or Cluster?

| | Sentinel | Cluster |
|---|---------|---------|
| Sharding | ❌ one dataset | ✅ 16,384 hash slots |
| HA | ✅ | ✅ |
| Client complexity | ask a sentinel for the address | cluster-aware client, follows `MOVED`/`ASK` |
| Multi-key operations | unrestricted | **same-slot only** |
| Failover time | `down-after` + election ≈ 10–15 s | ≈ 5–15 s |
| Use when | the dataset fits one node | throughput or size exceeds one node |

Pulse builds **both**, because the migration from one to the other is where the
interesting failures live. The moment you move to Cluster, every Lua script and
every multi-key operation must respect hash tags — which is why Modules 08 and 11
put `{room_id}` and `{user_id}` in every key name. That decision, made five
modules ago on a single Redis, is what makes this migration a config change
instead of a rewrite.

⚠️ **The Sentinel Compose trap:** Sentinel **rewrites its own config file** at
runtime (it persists the discovered topology). Mounting one read-only file into
three sentinel containers fails on startup with a confusing permission error. Copy
the template to a writable path per-container in an entrypoint.

### channels_redis and Sentinel

Pulse's channel layer (Module 07) and custom Streams layer (Module 09) both use
`redis-py` under the hood via `channels_redis`. Pointing them at Sentinel is a
settings change, not a code change:

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
                # THE tuning that makes a pause survivable -- see the lab.
                "socket_timeout": 2.0,
                "socket_connect_timeout": 2.0,
                "socket_keepalive": True,
            }],
        },
    },
}
```

The default `socket_timeout` in `redis-py` is `None` — **no timeout at all**. On a
`docker pause` (below), a `None` timeout means the client blocks *forever* on a
frozen primary. This one setting is the difference between a 9-second and a
15-second RTO, and the lab measures it.

---

## Postgres: Patroni, etcd, HAProxy

**Patroni** is a supervisor process that runs alongside Postgres. It stores
cluster state in etcd, holds a **leader lock with a TTL**, and if the leader fails
to renew it, the remaining members elect a new leader and reconfigure streaming
replication to follow it.

The leader lock's TTL is the fencing mechanism:

```
t=0    primary is partitioned from etcd
t=15   primary cannot renew the leader key -> Patroni DEMOTES IT ITSELF
t=20   a replica acquires the leader key and promotes
```

The old primary demotes **because it lost the lock**, not because anyone told it
to. That is what prevents split-brain when the *network* — not the process —
failed. A process that thinks it is still primary but cannot prove it via the DCS
(distributed configuration store, here etcd) must assume it is not.

**HAProxy** routes by asking each Patroni's REST API which node is currently
primary:

```haproxy
listen postgres_write
    bind *:5000
    option httpchk GET /primary          # 200 ONLY on the current primary
    default-server on-marked-down shutdown-sessions
```

`on-marked-down shutdown-sessions` is the second half of fencing: it **kills
existing connections** to a node that stops being primary, so a psycopg
connection holding an open transaction cannot keep writing to a demoted node.

**Django talks to PgBouncer, PgBouncer talks to HAProxy:5000.** The write DB in
`DATABASES` points at PgBouncer; the read replica DB (routed by the Django DB
router from Module 13) points at HAProxy:5001.

### The psycopg + PgBouncer gotcha, again

Module 13 established it and HA makes it non-negotiable: with PgBouncer in
**transaction pooling** mode, a psycopg3 connection may run each transaction on a
*different* server connection, so **server-side prepared statements break**.
Disable them in Django's `OPTIONS`:

```python
DATABASES["default"]["OPTIONS"] = {"prepare_threshold": None}  # was 5 by default
```

This is the exact analog of the JVM twin's `?prepareThreshold=0` on the JDBC URL —
same failure, same fix, different client library.

---

## WebSockets make deploys hard — and Python makes the drain its own problem

A rolling deploy of a stateless HTTP service is invisible. A rolling deploy of a
socket server disconnects everyone on the drained node.

```
pulse-1 receives SIGTERM
  → stop accepting new connections (readiness false)
  → 10,000 existing sockets... now what?
```

You cannot migrate a socket. You can only:

1. **Close them gracefully with a reason**, so clients reconnect deliberately
   rather than discovering a dead TCP connection 60 seconds later.
2. **Tell them when to come back**, with per-client jitter, so 10,000 clients
   don't return simultaneously.

On the JVM this is a `@PreDestroy` hook and `server.shutdown: graceful`. **In the
Python/ASGI world there is no framework method that gets called with "here are all
your sockets."** You assemble the drain from three pieces:

### Piece 1 — a per-process connection registry

Django Channels consumers are asyncio Tasks, one per connection, living on the
worker process's event loop. There is no built-in "all sessions" collection. You
build one: a module-level registry every consumer joins on `connect` and leaves
on `disconnect`.

```python
# chat/registry.py
class ConnectionRegistry:
    def __init__(self):
        self._consumers: set["ChatConsumer"] = set()
        self.draining = False

    def add(self, consumer):    self._consumers.add(consumer)
    def discard(self, consumer): self._consumers.discard(consumer)
    def __len__(self):          return len(self._consumers)

registry = ConnectionRegistry()   # one per worker PROCESS (see below)
```

### Piece 2 — the ASGI lifespan shutdown hook

ASGI defines a **lifespan protocol**: the server sends the app a
`lifespan.startup` message at boot and a `lifespan.shutdown` message when it is
stopping. Uvicorn fires `lifespan.shutdown` after it has stopped calling
`accept()`. That is where you broadcast the control frame and close the sockets.

### Piece 3 — a SIGTERM handler that flips readiness *first*

Here is the subtlety that mirrors Kubernetes' `preStop sleep` (Module 19). If you
only drain inside `lifespan.shutdown`, Uvicorn has *already* stopped accepting by
the time you flip readiness — so during the window between SIGTERM and nginx
noticing, new handshakes are routed to a socket that refuses them. The fix is a
two-phase SIGTERM handler:

```
SIGTERM arrives
  Phase 1:  readiness -> DRAINING     (/readyz now returns 503)
            await sleep(DRAIN_DELAY)   (let nginx's healthcheck notice; ~2 intervals)
  Phase 2:  hand control to Uvicorn's own graceful shutdown
            -> Uvicorn stops accept(), fires lifespan.shutdown
            -> broadcast control{reconnect, retry_after_ms=jitter} to every socket
            -> await sleep(flush)      (let the frames leave)
            -> close each socket with code 1001
  Uvicorn's --timeout-graceful-shutdown bounds the whole thing.
```

The control frame is the server's half of Module 10's full-jitter reconnect:

```python
import secrets

async def drain_all(registry, send_control, close):
    for consumer in list(registry._consumers):
        retry_after_ms = 1000 + secrets.randbelow(29_000)   # 1s..30s, per client
        await send_control(consumer, {
            "type": "control",
            "action": "reconnect",
            "reason": "draining",
            "retry_after_ms": retry_after_ms,
        })
    await asyncio.sleep(2)                                   # flush
    for consumer in list(registry._consumers):
        await consumer.close(code=1001)                     # "going away"
```

That `retry_after_ms` is what prevents the **thundering herd**: without it, every
client the node held returns at once, to the two remaining nodes, which were
already carrying extra load.

```
                      deploy
                        │
   connections  ────────┼────╲              ← node drains
                        │      ╲___
                        │          ╲╱╲      ← herd arrives, saturates
                        │             ╲___
```

### Uvicorn's own knob

Uvicorn has `--timeout-graceful-shutdown SECONDS`: on shutdown it stops accepting,
fires `lifespan.shutdown`, and waits up to that many seconds for in-flight tasks
to finish before cancelling them. Set it generously (45 s) so your drain has room:

```
uvicorn pulse.asgi:application --host 0.0.0.0 --port 8000 \
        --workers 4 --timeout-graceful-shutdown 45
```

> **Process-per-core reminder (Module 01):** each `pulse-N` container runs Uvicorn
> with several worker **processes** (one per core). Uvicorn's master forwards
> SIGTERM to every worker, and **each worker drains its own registry** — the
> registry is process-local because the connections are. There is no cross-process
> "all sockets" list, and you don't want one: a worker knows only its own sockets,
> which is exactly the set it must close. This is the same GIL/process boundary
> that forced Redis on you in Module 04, showing up again at shutdown.

---

## The `pause` versus `kill` distinction

This is the most important operational insight in the module.

| | `docker kill` | `docker pause` |
|---|--------------|----------------|
| TCP behaviour | socket closes, RST sent | **connection stays open, nothing flows** |
| Client detection | milliseconds | **whatever your timeout is** |
| Resembles | a process crash | **a network partition, a GC pause, a hung disk** |
| Which is more common in production? | | **this one** |

A clean kill is the *easy* failure: the kernel sends a RST and everything notices
immediately. A pause looks healthy to every TCP-level check and is only detected
by application timeouts. This is exactly why `socket_timeout=None` (the `redis-py`
default) is a landmine: on a paused primary, a `None` timeout never fires, and the
worker's event loop stalls on a Redis call that will never return — taking every
connection on that worker with it.

**Systems that handle `kill` gracefully often fall over on `pause`**, and the lab
measures both for every component.

---

## Chaos, methodically

```bash
docker kill <c>                      # SIGKILL — clean, instant
docker pause <c>                     # freeze — the mean one
docker stop -t 60 <c>                # SIGTERM then SIGKILL — tests graceful drain
docker network disconnect <net> <c>  # partition — split-brain testing
docker update --cpus 0.1 <c>         # brownout: slow, not dead. Often worst of all.
```

**Always run a load test during the drill.** The number *is* the deliverable. A
drill without a load test tells you the cluster reconfigured; a drill *with* one
tells you how many users noticed.

---

## What's next

The lab builds the full stack, then runs eleven drills: kill and pause every
component, partition the network, brown out a node, and do a rolling deploy —
each with a load test running and each producing a measured RTO and RPO. The
Django graceful-drain turns the rolling deploy from an 18-second, 2,841-message
outage into a **zero-second, zero-loss** non-event.

See you in [`lab.md`](./lab.md).
