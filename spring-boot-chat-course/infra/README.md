# infra/ — the stacks you run

Compose files, k8s manifests, and config for the data tier and HA stack. Like
`apps/`, these are **built up across the modules** rather than pre-written; the
labs create each file with full explanation.

| File / dir | Module | Purpose |
|------------|--------|---------|
| `compose.dev.yml` | 00 | Phase 0–1 dev data tier (postgres + redis). **Present now** — it's the VERIFY target. |
| `compose.replica.yml` | 13 | Streaming replication |
| `pgbouncer.ini` | 13 | Connection pooling |
| `compose.shards.yml` | 14 | Logical sharding across physical Postgres |
| `compose.scylla.yml` | 14 | The wide-column comparison |
| `compose.kafka.yml` | 16 | 3-broker KRaft cluster |
| `ha/` | 18 | The full 15-container HA stack (Sentinel, Patroni, HAProxy, nginx) |
| `obs/` | 20 | Prometheus, Grafana, Tempo, Loki + dashboards and rules |
| k8s manifests | 19 | See `../19-*/manifests/` |
| `capstone/` | 22 | Everything composed |

`compose.dev.yml` is the only file present from the start, because
[`../VERIFY.md`](../VERIFY.md) needs it before Module 01. Everything else you
create as you reach the module that uses it.
