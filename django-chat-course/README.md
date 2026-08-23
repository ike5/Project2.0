# Chat at Scale: Django, Channels, Redis & the Real-Time Backbone 💬⚡

A hands-on, local-first course that takes you from **"what actually happens when
a browser opens a WebSocket"** to a **sharded, replicated, self-healing chat
backbone** that survives you killing its database primary mid-conversation.

This is not a "add `AsyncJsonWebsocketConsumer` and ship it" tutorial. Every
architectural claim in this course is **measured on your laptop** before you're
asked to believe it. You will build the naive version, load-test it until it
breaks, read the numbers, and *then* learn the primitive that fixes it — and the
alternatives you rejected, and why.

> **Who this is for:** You are a strong backend engineer in *some* stack —
> Node, Go, Ruby, C#, Java — who has shipped real systems. Python is comfortable
> but Django Channels, asyncio at scale, and the Python process model are new or
> rusty. You want to understand real-time messaging at the level where you can
> defend your design in an architecture review, not just wire up a starter.

> **The thesis:** High-volume chat is not a framework problem. It is a
> **connection-state problem**, a **fan-out problem**, a **delivery-semantics
> problem**, and a **write-amplification problem** — four separate problems that
> happen to share a UI. Frameworks solve none of them for you. This course
> teaches you to see all four, and to defend each decision with the alternative
> you rejected and the condition that would change your mind.

---

## Why this course is different

- **You break it before you fix it.** Module 04 proves the in-memory channel
  layer can't even reach a second worker process *on the same machine*. Module 06
  load-tests your single-node chat server until it falls over, and you record the
  exact number. Module 07 explains why that number exists. Every scaling module
  ends with a new number.
- **The GIL is a first-class character, not a footnote.** Python has no virtual
  threads. One async worker process pins to one CPU core; you scale CPU by running
  one worker *process* per core, which is exactly why your channel layer has to
  cross processes — and therefore why you reach for Redis *sooner and more
  fundamentally* than a JVM shop would. You learn this by watching two workers on
  one box fail to see each other, not by reading a blog post.
- **Alternatives are first-class.** You don't just learn the Redis Pub/Sub
  channel layer — you watch it *lose ~15% of messages* on a `docker pause`,
  rebuild delivery on Redis Streams with consumer groups, then run the identical
  workload on Kafka and compare durability, ordering, partitioning, and
  operational cost. You finish able to say *why* you chose one.
- **Two runtimes, benchmarked head-to-head.** You build the chat spine on async
  Channels consumers, then rebuild the hot path with sync (threadpool) consumers
  and again on **raw ASGI** (Starlette / the `websockets` library), and measure
  all three. You learn the event-loop-vs-threadpool tradeoff — and the honest
  "should you even use Django for this?" question — on a graph.
- **High availability you can actually kill.** Redis Sentinel and Redis Cluster,
  Postgres streaming replication with Patroni, HAProxy, PgBouncer — all in Docker
  Compose on your machine. Then you `docker kill` the primary and watch failover
  while a load test is running, and count the dropped messages.
- **The database story goes all the way down.** Message ID design (Snowflake vs
  UUIDv7 vs bigint), keyset pagination, declarative partitioning by time via
  `RunSQL` migrations, read replicas behind a Django DB router, the transactional
  outbox relayed by Celery, app-level sharding — then the same data modelled in
  Cassandra/ScyllaDB to show you why the chat giants left relational behind.

---

## The arc

```
                    ┌─────────────────────────────────────────┐
  PHASE 0           │  00 Setup    01 Python Async & the GIL  │
  Foundations       │  02 Django Fast-Track  03 Transports    │
                    └────────────────────┬────────────────────┘
                                         │  "I understand the wire and the loop"
                    ┌────────────────────▼────────────────────┐
  PHASE 1           │  04 Channels Chat   05 Protocol Design  │
  One node          │  06 Load Harness ── FIND THE CEILING 💥 │
                    └────────────────────┬────────────────────┘
                                         │  "Two workers can't even see each other"
                    ┌────────────────────▼────────────────────┐
  PHASE 2           │  07 Redis Channel Layer 08 Internals    │
  The backbone      │  09 Streams  10 Semantics  11 Presence  │
                    └────────────────────┬────────────────────┘
                                         │  "Messages survive a reconnect"
                    ┌────────────────────▼────────────────────┐
  PHASE 3           │  12 Message Store  13 Partition/Replica │
  Durable state     │  14 Sharding & Wide-Column              │
                    └────────────────────┬────────────────────┘
                                         │  "Writes scale past one box"
                    ┌────────────────────▼────────────────────┐
  PHASE 4           │  15 Async/Sync/Raw-ASGI 16 Kafka Compare│
  The alternatives  │  17 Next.js Client                      │
                    └────────────────────┬────────────────────┘
                                         │  "I can defend my choices"
                    ┌────────────────────▼────────────────────┐
  PHASE 5           │  18 Compose HA + Chaos  19 Kubernetes   │
  Never goes down   │  20 Observability & SLOs                │
                    └────────────────────┬────────────────────┘
                                         │  "It heals while I watch"
                    ┌────────────────────▼────────────────────┐
  PHASE 6           │  21 Security & Abuse   22 CAPSTONE 🏁   │
  Ship it           │                                         │
                    └─────────────────────────────────────────┘
```

---

## Prerequisites

- A Mac or Linux machine with **~16 GB RAM free** and ~40 GB disk. The HA modules
  run a lot of containers; Module 00 includes a resource-budget table and a
  low-memory path.
- **Docker** and **Docker Compose v2**. Everything data-tier runs in containers.
- Comfort with a terminal, Git, HTTP, and SQL. You should have built and operated
  a real backend service before — this course assumes that experience and spends
  its time on what's *new*.
- **Python is assumed; Django is not.** You should read Python comfortably.
  Module 01 is an asyncio + concurrency primer aimed at people who understand
  concurrency in *some* language, and Module 02 is a Django + DRF fast-track
  framed entirely around building the chat service skeleton. If you have never
  touched `async def`, start at Module 01 and don't skip it — the whole course
  stands on it.
- **No Kubernetes experience required**, though Module 19 goes faster if you've
  done [`kubernetes-course`](../kubernetes-course/).

---

## The learning path

Work the modules **in order**. Each one grows the same app and assumes every
prior module.

### Phase 0 — Foundations

| # | Module | You'll build / learn | Est. |
|---|--------|----------------------|------|
| 00 | [Setup & Orientation](./00-setup/) | Python 3.12, Docker, k6, Node; resource budget; the four problems of chat | 2 h |
| 01 | [Python Async & Concurrency for Real-Time](./01-python-async-concurrency/) | The event loop, `async def` vs threads, uvloop, **the GIL**, why blocking the loop is the whole ballgame, the process-per-core worker model | 4 h |
| 02 | [Django Fast-Track for Real-Time](./02-django-fast-track/) | ASGI vs WSGI, apps, models, migrations, settings, DRF — and why `runserver` and sync views can't do realtime, taught by building the chat skeleton | 4 h |
| 03 | [Real-Time Transports on the Wire](./03-realtime-transports/) | Polling, long-poll, SSE (with `Last-Event-ID` resume), WebSocket (RFC 6455 framing byte-by-byte), WebTransport; what proxies do to each | 5 h |

### Phase 1 — One node, and its ceiling

| # | Module | You'll build / learn | Est. |
|---|--------|----------------------|------|
| 04 | [Channels Chat on a Single Node](./04-channels-chat-single-node/) | `AsyncJsonWebsocketConsumer`, groups, ASGI routing, the **InMemoryChannelLayer** — and proving it **can't span worker processes on one box** | 5 h |
| 05 | [Protocol & Domain Design](./05-protocol-and-domain-design/) | The JSON envelope, client-generated id + server id (idempotency), per-room sequence numbers (gap detection), the ack ladder, schema versioning | 5 h |
| 06 | [The Load-Testing Harness](./06-load-testing-harness/) | k6 + Locust for WebSocket; measure connections/node and p99 fan-out, and **break the single node on purpose** | 5 h |

### Phase 2 — The Redis backbone

| # | Module | You'll build / learn | Est. |
|---|--------|----------------------|------|
| 07 | [Scaling Out: The Redis Channel Layer](./07-scale-out-redis-channel-layer/) | `channels_redis` as the Pub/Sub backplane, sticky sessions, at-most-once — and **proving message loss** with a `docker pause` | 5 h |
| 08 | [Redis Internals](./08-redis-internals/) | RESP2/3, the single-threaded event loop, encodings, RDB vs AOF, `redis-cli --latency`, Lua atomicity — and taking Redis down with `KEYS` | 5 h |
| 09 | [Redis Streams & Consumer Groups](./09-redis-streams-delivery/) | `XADD`/`XREADGROUP`/`XACK`, the PEL, `XAUTOCLAIM`, at-least-once, the exactly-once illusion — building a **custom Streams-backed layer** | 5 h |
| 10 | [Ordering & Delivery Semantics](./10-ordering-and-delivery-semantics/) | Sequence numbers, gap detection, resume-from-cursor, derived offline queues, read receipts, unread counts | 5 h |
| 11 | [Presence, Typing & Rate Limiting](./11-presence-and-rate-limiting/) | TTL heartbeat presence, viewport subscriptions, presence storms, token buckets in Lua, distributed locks and why Redlock is contested | 5 h |

### Phase 3 — Durable state

| # | Module | You'll build / learn | Est. |
|---|--------|----------------------|------|
| 12 | [The Message Store](./12-postgres-message-store/) | Schema, Snowflake vs UUIDv7 vs bigint IDs, keyset pagination, index strategy, Django ORM vs raw SQL on the hot path, write amplification | 5 h |
| 13 | [Partitioning, Replication & Pooling](./13-partitioning-replication-pooling/) | Declarative time partitioning via `RunSQL`, read replicas via a Django **DB router**, replica lag & read-your-writes, PgBouncer with psycopg, the transactional **outbox** relayed by Celery | 5 h |
| 14 | [Sharding & Wide-Column](./14-sharding-and-wide-column/) | App-level sharding with a Django DB router, resharding pain, consistent hashing — then the same chat data in **Cassandra/ScyllaDB** | 6 h |

### Phase 4 — The alternatives, measured

| # | Module | You'll build / learn | Est. |
|---|--------|----------------------|------|
| 15 | [Async, Sync & Raw ASGI](./15-async-sync-and-raw-asgi/) | Sync (threadpool) vs async consumers, `database_sync_to_async`, the **"a blocking ORM call stalls every connection on the worker"** demo, then a raw-ASGI (Starlette/`websockets`) rebuild benchmarked head-to-head; Daphne vs Uvicorn+uvloop vs Granian | 6 h |
| 16 | [The Same Workload on Kafka](./16-kafka-comparison/) | Partitions, keys and ordering, consumer groups, rebalances, retention (KRaft mode) — and an honest ops-cost comparison vs Redis Streams | 5 h |
| 17 | [The Next.js Real-Time Client](./17-nextjs-realtime-client/) | Virtualized list, optimistic send with client-id reconciliation, offline outbox, gap detection, full-jitter reconnect, a SharedWorker for one socket across tabs | 6 h |

### Phase 5 — Never goes down

| # | Module | You'll build / learn | Est. |
|---|--------|----------------------|------|
| 18 | [Compose HA & Chaos Drills](./18-compose-ha-and-chaos/) | Redis Sentinel → Redis Cluster, Patroni + etcd + HAProxy, PgBouncer, multi-instance app behind a WebSocket-aware nginx that drains gracefully — then **kill/pause every primary under load** | 7 h |
| 19 | [Kubernetes HA & Multi-Region](./19-kubernetes-ha-and-multiregion/) | StatefulSets, an operator (CloudNativePG), PodDisruptionBudgets, topology spread, zero-drop rolling deploys for a stateful socket (`preStop sleep`), edge-terminated multi-region with room affinity | 6 h |
| 20 | [Observability & SLOs](./20-observability-and-slos/) | Prometheus/Grafana/Tempo/Loki; measure **true end-to-end delivery** not enqueue; trace across the outbox and the Redis Stream; cardinality; four SLOs with burn-rate alerts; a synthetic prober | 5 h |

### Phase 6 — Ship it

| # | Module | You'll build / learn | Est. |
|---|--------|----------------------|------|
| 21 | [Security & Abuse at Scale](./21-security-and-abuse-at-scale/) | Channels auth (origin/CSWSH — attack then block), token-in-ticket + JWT, re-auth on a long-lived socket, cluster-wide revocation, delivery-time authz, distributed abuse detection, optional E2EE for DMs | 5 h |
| 22 | [Capstone — Pulse at Scale](./22-capstone/) | Wire it all together, hit a load target, survive a chaos run *under load*, and defend it in a written architecture review with an honest production-readiness assessment | 8 h |

**Total: ~110 hours of focused, hands-on work across ~23 modules.**

---

## How each module is structured

```
NN-topic/
├── README.md      ← Concepts in plain language. Read this first.
├── lab.md         ← Step-by-step guided build with expected output. Do this second.
├── code/          ← Reference files the lab adds to the app (when applicable).
├── challenge.md   ← An unguided task to prove you understood it. Do this third.
└── solutions/     ← Reference answers with the reasoning. Peek only after you've tried.
```

**The rhythm for every module:** read `README.md` → follow `lab.md` hands-on →
attempt `challenge.md` solo → check `solutions/`. The deepest "defend the
decision" content — the rejected alternatives and the measured numbers — lives in
the solutions.

---

## The app you're building

One Django project, **`pulse`** (chat app: `chat`), grows across the whole course
under [`apps/pulse/`](./apps/pulse/), with a Next.js client under
[`apps/pulse-web/`](./apps/pulse-web/).

The code is **built incrementally in the labs** — the `apps/` directory ships
with only a README mapping milestones to modules; every file is created in a lab
with full context, and reference implementations of the tricky pieces live in
each module's `solutions/`.

It starts as "an ASGI project with one echo consumer" and ends as:

- A horizontally-scaled Channels service holding tens of thousands of concurrent
  WebSocket connections per node across a process-per-core worker fleet.
- Fan-out over a custom Redis Streams layer with consumer groups, at-least-once
  delivery, client-side dedup, and gap-detecting resume.
- Presence, typing indicators, read receipts, and unread counts that don't melt
  under a presence storm.
- A partitioned Postgres message store behind PgBouncer with read replicas routed
  by a Django DB router, fronted by an app-level shard router.
- A transactional outbox relayed by Celery, so a message is never
  persisted-but-not-delivered (or delivered-but-not-persisted).
- Full HA: Redis Cluster, Patroni-managed Postgres, and a load balancer that
  survives you killing any single container.
- Prometheus metrics, distributed traces across the async fan-out, and SLOs with
  real burn-rate alert rules.

---

## Reference material

| File | What it's for |
|------|---------------|
| [`GLOSSARY.md`](./GLOSSARY.md) | Plain-English definitions of every term, organized by topic |
| [`VERIFY.md`](./VERIFY.md) | End-to-end smoke test — confirm your environment before Module 01 |
| [`cheatsheets/websocket-channels.md`](./cheatsheets/websocket-channels.md) | RFC 6455 frames, ASGI scope, Channels consumer lifecycle, the channel-layer API |
| [`cheatsheets/redis.md`](./cheatsheets/redis.md) | Commands by use case, Streams recipes, Cluster/Sentinel ops, encodings |
| [`cheatsheets/postgres-scale.md`](./cheatsheets/postgres-scale.md) | ID design, keyset pagination, partitioning, replication, PgBouncer, the outbox |
| [`cheatsheets/docker-ha.md`](./cheatsheets/docker-ha.md) | Compose HA topologies, healthchecks, nginx WebSocket config, failover commands |
| [`cheatsheets/load-testing.md`](./cheatsheets/load-testing.md) | k6 + Locust WebSocket recipes, coordinated omission, reading percentiles honestly |
| [`cheatsheets/troubleshooting.md`](./cheatsheets/troubleshooting.md) | Decision trees: dropped sockets, lost messages, blocked event loops, OOM, replica lag |

---

## Related courses in this repo

This course is one of a family that approaches real-time chat from different
angles. Working more than one is the point.

- **[`spring-boot-chat-course`](../spring-boot-chat-course/)** — the **JVM twin of
  this course**. The *same* six-phase arc, the *same* "measure every claim,
  defend every decision" thesis, the *same* app called `pulse` — solved on Spring
  Boot with Java 21 virtual threads and STOMP instead of Django Channels, asyncio,
  and a process-per-core model. Working the two side by side is the most valuable
  thing you can do with either: you watch a **different runtime model** solve
  *identical* problems, see where the numbers shift (Python's per-message overhead
  makes the single-node fan-out knee lower, and the GIL makes Redis necessary
  sooner), and see where the shape of the answer stays exactly the same. This
  course cross-references the JVM twin at the exact analogous moments — Module 01
  (asyncio + GIL vs virtual threads), Module 04 (the single-node wall), Module 15
  (async-vs-sync-vs-raw-ASGI vs MVC-vs-WebFlux).
- **[`slack-clone-course`](../slack-clone-course/)** — the same product domain,
  also on **Django Channels + Next.js**, but as a **build-a-Slack product
  tutorial**: breadth- and feature-focused (channels, threads, DMs, reactions,
  search, files), where this course is depth- and architecture-focused. Take
  `slack-clone-course` to ship a product; take this one to defend it in an
  architecture review.
- **[`kubernetes-course`](../kubernetes-course/)** — the deep Kubernetes
  foundation. Module 19 here assumes only the basics and cross-references it.
- **[`linux-course`](../linux-course/)** — useful background for the chaos and
  networking drills in Module 18 (`tc netem`, `ss`, file descriptors, `sysctl`).

**Where to start if you're deciding:** want the runtime you already know? Pick
this (Python) or `spring-boot-chat-course` (JVM). Want to ship a Slack? Take
`slack-clone-course`. Want to *understand* chat at scale well enough to argue
about it? Take this one — ideally alongside its JVM twin.

---

## Philosophy

- **Learn by doing.** 80% of your time is hands on keys.
- **Production patterns, not toys.** One real app, grown across 23 modules.
- **Deliberate failure.** You will stall event loops, kill primaries, drop
  packets, exhaust connection pools, and induce replica lag — on purpose, while
  watching.
- **Measure, don't assume.** Every performance claim comes with a benchmark you
  run yourself and a reference machine it ran on.
- **Local-first.** Everything runs on one laptop with free tools. No cloud
  account required.
- **Modern and idiomatic.** Python 3.12, Django 5.1, Channels 4.1, Redis 7.x,
  Postgres 16, Next.js App Router. No legacy patterns, no `runserver` in
  production.

---

Start with **[Module 00 — Setup & Orientation](./00-setup/)**, then run
**[VERIFY.md](./VERIFY.md)** before Module 01.
