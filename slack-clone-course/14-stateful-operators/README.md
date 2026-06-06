# Module 14 — Stateful Data Tier with Operators

**Goal:** replace the toy single-pod Postgres and Redis with **highly-available**,
self-healing clusters managed by operators — CloudNativePG for Postgres and the
redis-operator for Redis.

⏱️ ~3 hours · 🎯 Prereq: Module 13 (app running on k8s).

> Stateless web/worker pods are easy to make HA — just run more. **Databases are
> hard:** failover, replication, backups, and data integrity. Operators encode that
> hard-won expertise so you don't have to hand-roll it.

---

## 1. Why the simple data pods aren't enough

In Module 13, Postgres and Redis were single Deployments. If that pod (or its node)
dies, **the whole app is down** until it reschedules — and the data is at risk. Chat
is "always on," so we need the data tier to survive a failure with little or no
interruption. That means replication + automatic failover — exactly what operators do.

## 2. What an operator is

An **operator** is a controller that manages a complex app via **custom resources**.
You declare a `Cluster` (Postgres) or `RedisFailover` (Redis) object describing *what
you want*; the operator continuously runs the *how*: provisioning, configuring
replication, promoting a new primary on failure, taking backups, and rejoining
recovered members. It's the Kubernetes reconciliation loop, specialized for a database.

## 3. CloudNativePG: HA Postgres

`k8s/data/postgres-cluster.yaml` declares a 3-instance cluster:

```yaml
kind: Cluster
spec:
  instances: 3                 # 1 primary + 2 streaming replicas
  primaryUpdateStrategy: unsupervised
  affinity:
    enablePodAntiAffinity: true # spread across nodes
```

The operator creates three Services:
- **`slack-pg-rw`** → always the **current primary** (writes),
- **`slack-pg-ro`** → replicas (read-only),
- **`slack-pg-r`** → any instance.

The magic is **`-rw` follows failover**: if the primary dies, the operator promotes a
replica and repoints `-rw` at it. Your app — pointed at `slack-pg-rw` — just
reconnects to the new primary. No manual intervention.

## 4. redis-operator: HA Redis

`k8s/data/redis-failover.yaml` declares a `RedisFailover`: N Redis replicas guarded by
N **Sentinels**. Sentinel watches the master; if it dies, Sentinels elect a replica as
the new master. This matters doubly for us because Redis is **both** the Celery broker
**and** the Channels channel layer — losing it would freeze real-time messaging and
background jobs.

## 5. Repointing the app

`k8s/data/config-operators.yaml` overrides `backend-config` so the app talks to the
operator services:

```
DATABASE_URL → postgres://slack:slackpass@slack-pg-rw:5432/slack
REDIS_URL    → redis://rfr-slack-redis:6379/0
```

Apply it, `kubectl rollout restart` the backend, and the app now runs on the HA tier.

## 6. Backups & PITR (briefly)

CloudNativePG can stream WAL and base backups to object storage (S3/MinIO) for
**point-in-time recovery** — you configure a `backup` section and a `ScheduledBackup`.
HA protects against *failure*; backups protect against *mistakes* (a bad migration, a
`DELETE` gone wrong). You need both. You'll wire a scheduled backup in the challenge.

---

## 7. Do the lab

Install both operators, create the HA Postgres and Redis clusters, migrate the app's
data onto them, repoint the app, and confirm three Postgres instances with one primary.

👉 **[lab.md](./lab.md)**

Then test yourself: 👉 **[challenge.md](./challenge.md)**

---

## Key terms (see [GLOSSARY](../GLOSSARY.md))

operator · custom resource · CloudNativePG · failover · Sentinel · `-rw` service · PITR

**Next →** [Module 15: High Availability & Scaling](../15-high-availability/)
