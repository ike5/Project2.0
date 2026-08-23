# Module 18 — Compose HA & Chaos Drills

**Goal:** Build genuine high availability in Docker Compose — Redis Sentinel and
Cluster, Patroni-managed Postgres, HAProxy, PgBouncer, a WebSocket-aware load
balancer — and then kill every component while a load test runs, and count what
it cost.

⏱️ ~7 hours · **Prerequisites:** Modules 00–17.

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

Pulse targets the third row: **RTO under 30 seconds, RPO zero.** The lab
measures whether it achieves that, which is a different question from whether it
was configured for it.

---

## The three rules

**1. Quorum needs odd numbers.**
Two nodes cannot agree which one is dead. Three sentinels with quorum 2, three
etcd nodes, three Kafka controllers. Two of anything is not HA — it's two single
points of failure that can disagree.

**2. Failover requires fencing.**
If a demoted primary can still accept writes, you have **split-brain**: two nodes
both believing they're primary, both accepting writes, silently diverging. That
is worse than downtime, because downtime is visible and divergence is not.

**3. HA is only real if you've tested it.**
An untested failover path is a theory. Most of this module is drills, because the
configuration is the easy part and the behaviour under load is the part that
surprises you.

---

## The topology

```
                         ┌──────────┐
     clients  ──────────▶│  nginx   │  cookie-consistent-hash, WS-aware
                         └────┬─────┘
                  ┌───────────┼───────────┐
              ┌───▼───┐   ┌───▼───┐   ┌───▼───┐
              │pulse-1│   │pulse-2│   │pulse-3│  graceful drain on SIGTERM
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
                                   │patroni1│ │patroni2│ │patroni3│
                                   │primary │ │replica │ │replica │
                                   └────┬───┘ └────┬───┘ └────┬───┘
                                        └──────────┼──────────┘
                                              ┌────▼────┐
                                              │  etcd   │ 3 nodes
                                              └─────────┘
```

Fifteen containers. Module 00's resource budget said ~9 GB; the lab has a
low-memory path.

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
interesting failures live: the moment you move to Cluster, every Lua script and
every multi-key operation must respect hash tags — which is why Modules 08 and 11
put `{roomId}` and `{userId}` in every key name.

⚠️ **The Sentinel Compose trap:** Sentinel **rewrites its own config file** at
runtime. Mounting one read-only file into three sentinel containers fails on
startup with a confusing error. Copy per-container in an entrypoint.

---

## Postgres: Patroni, etcd, HAProxy

**Patroni** is a supervisor around Postgres. It stores cluster state in etcd,
holds a **leader lock with a TTL**, and if the leader fails to renew it, the
remaining members elect a new one and reconfigure replication.

The leader lock's TTL is the fencing mechanism:

```
t=0    primary is partitioned from etcd
t=15   primary cannot renew the leader key -> Patroni DEMOTES IT ITSELF
t=20   a replica acquires the leader key and promotes
```

The old primary demotes **because it lost the lock**, not because anyone told it
to. That's what prevents split-brain when the network — not the process — failed.

**HAProxy** routes by asking each Patroni's REST API:

```haproxy
listen postgres_write
    bind *:5000
    option httpchk GET /primary          # 200 ONLY on the current primary
    default-server on-marked-down shutdown-sessions
```

`on-marked-down shutdown-sessions` is the second half of fencing: it **kills
existing connections** to a demoted primary, so an app holding an open
transaction can't keep writing to it.

---

## WebSockets make deploys hard

A rolling deploy of a stateless HTTP service is invisible. A rolling deploy of a
socket server disconnects everyone on the drained node.

```
node-1 receives SIGTERM
  → stop accepting new connections (readiness false)
  → 10,000 existing sockets... now what?
```

You cannot migrate a socket. You can only:

1. **Close them gracefully with a reason**, so clients reconnect deliberately
   rather than discovering a dead TCP connection 60 seconds later.
2. **Tell them when to come back**, with per-client jitter, so 10,000 clients
   don't return simultaneously.

```java
sessions.forEach(s -> send(s, control("reconnect", "draining",
        ThreadLocalRandom.current().nextLong(1_000, 30_000))));
```

That `retryAfterMs` is the server's half of Module 10's full-jitter reconnect.
Without it you get the **thundering herd**: every client the node held returns at
once, to the two remaining nodes, which were already carrying extra load.

```
                      deploy
                        │
   connections  ────────┼────╲              ← node drains
                        │      ╲___
                        │          ╲╱╲      ← herd arrives, saturates
                        │             ╲___
```

---

## The `pause` versus `kill` distinction

This is the most important operational insight in the module.

| | `docker kill` | `docker pause` |
|---|--------------|----------------|
| TCP behaviour | socket closes, RST sent | **connection stays open, nothing flows** |
| Client detection | milliseconds | **whatever your timeout is** |
| Resembles | a process crash | **a network partition, a GC pause, a hung disk** |
| Which is more common in production? | | **this one** |

A clean kill is the *easy* failure: everything notices immediately. A pause looks
healthy to every TCP-level check and is only detected by application timeouts.

**Systems that handle `kill` gracefully often fall over on `pause`**, and the lab
measures both for every component.

---

## Chaos, methodically

```bash
docker kill <c>                      # SIGKILL — clean, instant
docker pause <c>                     # freeze — the mean one
docker stop -t 30 <c>                # SIGTERM then SIGKILL — tests graceful shutdown
docker network disconnect <net> <c>  # partition — split-brain testing
docker update --cpus 0.1 <c>         # brownout: slow, not dead. Often worst of all.
```

**Always run a load test during the drill.** A failover that's invisible with
zero traffic can drop 40% of messages at 5,000 msg/s. The number *is* the
deliverable.

---

## What's next

The lab builds the full stack, then runs eleven drills: kill and pause every
component, partition the network, brown out a node, and do a rolling deploy —
each with a load test running and each producing a measured RTO and RPO.

See you in [`lab.md`](./lab.md).
