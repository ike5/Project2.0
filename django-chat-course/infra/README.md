# infra/ — the stacks you run

Compose files, config, and (from Module 19) Kubernetes manifests for everything
that isn't application code. Like [`../apps/`](../apps/), these are **built up
across the modules** rather than shipped whole — each lab creates the file it
needs, explains every setting in it, and then breaks something with it.

Exactly one file is present from the start.

```
infra/
├── compose.dev.yml       ← PRESENT NOW. Postgres + Redis. The VERIFY target.
├── compose.replica.yml   ← Module 13
├── pgbouncer.ini         ← Module 13
├── compose.shards.yml    ← Module 14
├── compose.scylla.yml    ← Module 14
├── compose.kafka.yml     ← Module 16
├── ha/                   ← Module 18   (compose.ha.yml + Sentinel/Patroni/HAProxy/nginx config)
├── obs/                  ← Module 20   (compose.obs.yml + dashboards, rules)
└── capstone/             ← Module 22   (everything composed)
```

| File / dir | Module | Purpose |
|------------|--------|---------|
| `compose.dev.yml` | 00 | The dev data tier for Modules 00–12: one Postgres, one Redis. **Present now** — [`../VERIFY.md`](../VERIFY.md) needs it before Module 01. |
| `compose.replica.yml` | 13 | Primary + streaming replica, so the Django DB router has somewhere to send reads |
| `pgbouncer.ini` | 13 | Transaction-mode pooling (and the `prepare_threshold` consequence) |
| `compose.shards.yml` | 14 | Two physical Postgres shards behind an app-level shard router |
| `compose.scylla.yml` | 14 | ScyllaDB, for the wide-column comparison |
| `compose.kafka.yml` | 16 | 3-broker Kafka in KRaft mode (no ZooKeeper) |
| `ha/compose.ha.yml` | 18 | The 15-container HA stack: 3 Redis + 3 Sentinel, 3 etcd, 3 Patroni, HAProxy, PgBouncer, 3 app nodes, nginx |
| `obs/compose.obs.yml` | 20 | Prometheus, Grafana, Tempo, Loki + provisioned dashboards and alert rules |
| `capstone/` | 22 | The full stack under one project name, for the capstone load + chaos run |
| k8s manifests | 19 | Not here — see [`../19-kubernetes-ha-and-multiregion/manifests/`](../19-kubernetes-ha-and-multiregion/) |

---

## `compose.dev.yml` — what's in it and why

This is the stack Modules 00–12 run against: **one Postgres, one Redis, nothing
clever.** It is deliberately small. The whole point of Phases 0 and 1 is to find
the ceiling of a single node, and you cannot find a ceiling you have already
engineered around.

```bash
docker compose -p pulse-dev -f infra/compose.dev.yml up -d
docker compose -p pulse-dev -f infra/compose.dev.yml ps
docker compose -p pulse-dev -f infra/compose.dev.yml down -v      # note the -v
```

Services, credentials and ports (VERIFY.md §10 asserts all of these — if you
rename anything here, fix VERIFY.md too):

| Service | Container | Image | Published | Credentials |
|---------|-----------|-------|-----------|-------------|
| `postgres` | `pulse-postgres` | `postgres:16-alpine` | `5432:5432` | `pulse` / `pulse` / db `pulse` |
| `redis` | `pulse-redis` | `redis:7-alpine` | `6379:6379` | none |

Both carry real healthchecks — `pg_isready -U pulse -d pulse` and `redis-cli
PING` — because `depends_on` without `condition: service_healthy` waits for a
container to *start*, not to be *usable*.

### The two settings the file argues about

The file is heavily commented on purpose; read it. Two choices matter enough to
restate here, because later modules lean on them:

**1. `log_min_duration_statement=200` on Postgres.** Every statement slower than
200 ms is logged. This is your first profiling signal and it costs nothing at dev
volumes. Module 12 has you scroll a ten-million-row table and watch this log fill
with the sequential scan you didn't know you wrote; Module 13 watches it go quiet
after the partition prune. 200 ms sits well above a healthy indexed lookup (~1 ms)
and well below what a human notices (~500 ms), so the log contains only things
worth reading.

**2. `--maxmemory-policy noeviction` on Redis — and this one is worth arguing
about.** Redis here is **not a cache**. It holds the channel layer, per-room
sequence counters (Module 05), the Streams fan-out log (Module 09), presence keys
(Module 11), rate-limit buckets, and single-use auth tickets (Module 21). *Every
one of those is a correctness surface.*

With an eviction policy, memory pressure makes Redis quietly delete whichever key
it likes. Lose a sequence counter and every client sees a gap and triggers a
resume storm. Lose a presence key and a user appears offline. Lose a stream entry
and a message is gone with no error anywhere. **Silent partial data loss is the
worst possible failure mode for a message backbone.** `noeviction` converts it
into a loud, immediate, attributable failure: writes return OOM errors, your
consumer raises, your alert fires. A visible outage beats invisible corruption
every time. (Module 08 argues the other side for genuinely cache-shaped data;
Module 09 sizes the Streams memory budget so you don't hit the wall.)

Persistence is **off** in dev (`--save "" --appendonly no`). Redis is a transport
and derived state; the Postgres outbox (Module 13) is the source of truth.
Turning RDB/AOF off also removes fork-induced latency spikes from every number
you measure in Modules 06–11, which matters when you're chasing a 138 ms p99.
`slowlog-log-slower-than 5000` (µs) is on so Module 08's `KEYS` demonstration
shows up as evidence rather than as a vibe.

### Networking

Compose creates the default bridge network `pulse-dev_default`. Services reach
each other by **service name** (`postgres`, `redis`) — those are the hosts you put
in Django's `DATABASES` / `CHANNEL_LAYERS` when the app also runs in Compose.
Running Django on the host instead? Use `localhost` and the published ports.

> Half of "it works on my machine, not in the container" is this one line.
> `redis://localhost:6379` inside a container means *that container*, and the
> error you get is a connection refused with no clue attached.

---

## What replaces it, and when

Later phases **replace** `compose.dev.yml` rather than extending it, so each
stack is a self-contained thing you can reason about:

```
Modules 00–12   compose.dev.yml           postgres + redis                       ~1 GB
Module 13       compose.replica.yml       + replica + PgBouncer                  ~2 GB
Module 14       compose.shards.yml        2 shards                               ~2 GB
                compose.scylla.yml        + ScyllaDB (run separately)            ~4 GB
Module 16       compose.kafka.yml         3 KRaft brokers                        ~3 GB
Module 18       ha/compose.ha.yml         the 15-container HA stack              ~9 GB
Module 20       obs/compose.obs.yml       Prometheus/Grafana/Tempo/Loki          ~2 GB
Module 22       capstone/                 HA + observability + the app           ~11 GB
```

Module 00's resource-budget table covers the low-memory paths. The important one:
**Module 18 has an 8–12 GB path** that runs Redis Sentinel instead of Cluster
(3 redis + 3 sentinel instead of 6 cluster nodes) and 2 app instances instead of
3. You lose the resharding drills; every failover drill still works.

Use a distinct `-p` project name per stack so they don't collide:

```bash
docker compose -p pulse-dev      -f infra/compose.dev.yml       up -d
docker compose -p pulse-ha       -f infra/ha/compose.ha.yml     up -d --wait
docker compose -p pulse-obs      -f infra/obs/compose.obs.yml   up -d
```

And **stop the previous stack before starting the next** — they publish the same
host ports (5432, 6379) and the second one fails with `port is already
allocated`, which reads like a Docker bug and is not one.

---

## Conventions every file in here follows

- **Pinned image tags.** `postgres:16-alpine`, `redis:7-alpine`,
  `haproxy:2.9-alpine`. Never `latest` for anything you'd page someone about.
- **A real healthcheck on every stateful service**, and
  `depends_on: { condition: service_healthy }` on everything that needs it.
- **`stop_grace_period` set deliberately.** The 10 s default is fine for
  Postgres and nowhere near enough for an app node draining 10,000 WebSockets
  (Module 18 uses 60 s).
- **Named volumes, not bind mounts**, for data directories — so `down -v` is a
  clean reset and nothing lands in your working tree.
- **Comments explain the *why*, including the rejected alternative.**
  `compose.dev.yml` is the template: if a setting is unusual, the file says what
  it's protecting against.

---

## Related reference

- [`../cheatsheets/docker-ha.md`](../cheatsheets/docker-ha.md) — healthchecks,
  nginx WebSocket config, Sentinel/Patroni/HAProxy recipes, `kill` vs `pause`,
  and the drill scoreboard.
- [`../cheatsheets/troubleshooting.md`](../cheatsheets/troubleshooting.md) §8 —
  the Compose failures that waste the most time.
- [`../VERIFY.md`](../VERIFY.md) — the smoke test for `compose.dev.yml`. Run it
  before Module 01.
