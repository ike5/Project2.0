# Chat at Scale: Spring Boot, Redis & the Real-Time Backbone 💬⚡

A hands-on, local-first course that takes you from **"what actually happens when
a browser opens a WebSocket"** to a **sharded, replicated, self-healing chat
backbone** that survives you killing its database primary mid-conversation.

This is not a "add `@EnableWebSocketMessageBroker` and ship it" tutorial. Every
architectural claim in this course is **measured on your laptop** before you're
asked to believe it. You will build the naive version, load-test it until it
breaks, read the numbers, and *then* learn the primitive that fixes it — and the
three alternatives you rejected, and why.

> **Who this is for:** You are a strong backend engineer in *some* stack —
> Node, Python, Go, Ruby, C# — who has shipped real systems. Java and Spring are
> new or rusty. You want to understand real-time messaging at the level where you
> can defend your design in an architecture review, not just wire up a starter.

> **The thesis:** High-volume chat is not a framework problem. It is a
> **connection-state problem**, a **fan-out problem**, a **delivery-semantics
> problem**, and a **write-amplification problem** — four separate problems that
> happen to share a UI. Frameworks solve none of them for you. This course
> teaches you to see all four.

---

## Why this course is different

- **You break it before you fix it.** Module 06 load-tests your single-node chat
  server until it falls over, and you record the exact number. Module 07 explains
  why that number exists. Every scaling module ends with a new number.
- **Alternatives are first-class, not footnotes.** You don't just learn Redis
  Pub/Sub — you watch it *lose messages* on reconnect, rebuild on Redis Streams,
  then run the identical workload on Kafka and compare durability, ordering,
  partitioning, and operational cost. You finish able to say *why* you chose one.
- **Two runtimes, benchmarked head-to-head.** You build the chat spine on Spring
  MVC + STOMP with Java 21 virtual threads, then rebuild the hot path in WebFlux
  and measure both. You learn the thread-per-connection vs event-loop tradeoff by
  watching it on a graph, not by reading a blog post.
- **High availability you can actually kill.** Redis Sentinel and Redis Cluster,
  Postgres streaming replication with Patroni, HAProxy, PgBouncer — all in Docker
  Compose on your machine. Then you `docker kill` the primary and watch failover
  while a load test is running, and count the dropped messages.
- **The database story goes all the way down.** Message ID design (Snowflake vs
  UUIDv7 vs bigserial), keyset pagination, declarative partitioning, read
  replicas, the outbox pattern, app-level sharding — then the same data modelled
  in Cassandra to show you why the chat giants left relational behind.

---

## The arc

```
                    ┌─────────────────────────────────────────┐
  PHASE 0           │  00 Setup    01 Java 21 Concurrency     │
  Foundations       │  02 Spring Fast-Track  03 Transports    │
                    └────────────────────┬────────────────────┘
                                         │  "I understand the wire"
                    ┌────────────────────▼────────────────────┐
  PHASE 1           │  04 STOMP Chat   05 Protocol Design     │
  One node          │  06 Load Harness ── FIND THE CEILING 💥 │
                    └────────────────────┬────────────────────┘
                                         │  "One box dies at N users"
                    ┌────────────────────▼────────────────────┐
  PHASE 2           │  07 Pub/Sub Fan-Out  08 Redis Internals │
  The backbone      │  09 Streams  10 Semantics  11 Presence  │
                    └────────────────────┬────────────────────┘
                                         │  "Messages survive a reconnect"
                    ┌────────────────────▼────────────────────┐
  PHASE 3           │  12 Message Store  13 Partition/Replica │
  Durable state     │  14 Sharding & Wide-Column              │
                    └────────────────────┬────────────────────┘
                                         │  "Writes scale past one box"
                    ┌────────────────────▼────────────────────┐
  PHASE 4           │  15 WebFlux Rebuild  16 Kafka Compare   │
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
- **No Java or Spring experience required.** Module 01 is a Java 21 concurrency
  primer aimed at people who already understand concurrency in another language,
  and Module 02 is a Spring fast-track framed entirely around a chat service.
- **No Kubernetes experience required**, though Module 19 goes faster if you've
  done [`kubernetes-course`](../kubernetes-course/).

---

## The learning path

Work the modules **in order**. Each one grows the same app and assumes every
prior module.

### Phase 0 — Foundations

| # | Module | You'll build / learn | Est. |
|---|--------|----------------------|------|
| 00 | [Setup & Orientation](./00-setup/) | JDK 21, Docker, k6, Node; resource budget; the four problems of chat | 2 h |
| 01 | [Java 21 Concurrency for Real-Time](./01-java21-concurrency/) | Platform vs virtual threads, structured concurrency, the JMM, why blocking I/O is the whole ballgame | 4 h |
| 02 | [Spring Boot Fast-Track](./02-spring-fast-track/) | DI, beans, config, profiles, Actuator — taught by building the chat service's skeleton | 4 h |
| 03 | [Real-Time Transports on the Wire](./03-realtime-transports/) | Polling, long-poll, SSE, WebSocket (RFC 6455 framing byte-by-byte), WebTransport; what proxies do to each | 5 h |

### Phase 1 — One node, and its ceiling

| # | Module | You'll build / learn | Est. |
|---|--------|----------------------|------|
| 04 | [STOMP Chat on a Single Node](./04-stomp-chat-single-node/) | `@EnableWebSocketMessageBroker`, the simple broker, sessions, subscriptions, a working chat | 5 h |
| 05 | [Protocol & Domain Design](./05-protocol-and-domain-design/) | Message envelopes, client-generated IDs, idempotency, ack protocols, schema versioning | 5 h |
| 06 | [The Load-Testing Harness](./06-load-testing-harness/) | k6 + Gatling for WebSocket; measure connections/node, p99 fan-out, and **break your server on purpose** | 5 h |

### Phase 2 — The Redis backbone

| # | Module | You'll build / learn | Est. |
|---|--------|----------------------|------|
| 07 | [Scaling Out: Pub/Sub Fan-Out](./07-scale-out-redis-pubsub/) | Sticky sessions, the two-nodes problem, Redis as a backplane, at-most-once delivery — and **proving message loss** | 5 h |
| 08 | [Redis Internals](./08-redis-internals/) | RESP3, the single-threaded event loop, data structure encodings, RDB vs AOF, `redis-cli --latency`, Lua atomicity | 5 h |
| 09 | [Redis Streams & Consumer Groups](./09-redis-streams-delivery/) | `XADD`/`XREADGROUP`/`XACK`, the PEL, claim/retry, at-least-once, the exactly-once illusion | 5 h |
| 10 | [Ordering & Delivery Semantics](./10-ordering-and-delivery-semantics/) | Sequence numbers, gap detection, resume-from-cursor, offline queues, read receipts, unread counts | 5 h |
| 11 | [Presence, Typing & Rate Limiting](./11-presence-and-rate-limiting/) | TTL heartbeats, presence fan-out storms, token buckets in Lua, distributed locks and why Redlock is contested | 5 h |

### Phase 3 — Durable state

| # | Module | You'll build / learn | Est. |
|---|--------|----------------------|------|
| 12 | [The Message Store](./12-postgres-message-store/) | Schema design, Snowflake vs UUIDv7 vs bigserial, keyset pagination, index strategy, write amplification | 5 h |
| 13 | [Partitioning, Replication & Pooling](./13-partitioning-replication-pooling/) | Declarative partitioning by time, read replicas and replica lag, PgBouncer, the transactional outbox | 5 h |
| 14 | [Sharding & Wide-Column](./14-sharding-and-wide-column/) | App-level sharding, resharding pain, then the same chat data in Cassandra — and why Discord did it | 6 h |

### Phase 4 — The alternatives, measured

| # | Module | You'll build / learn | Est. |
|---|--------|----------------------|------|
| 15 | [Rebuilding the Hot Path in WebFlux](./15-webflux-reactive-rebuild/) | Reactor, backpressure, context propagation, Netty — then a **head-to-head benchmark** vs virtual threads | 6 h |
| 16 | [The Same Workload on Kafka](./16-kafka-comparison/) | Partitions, keys and ordering, consumer groups, retention, compaction — and an honest ops-cost comparison | 5 h |
| 17 | [The Next.js Real-Time Client](./17-nextjs-realtime-client/) | STOMP over WebSocket in React, reconnect/backoff, virtualized lists, optimistic send, offline queue | 6 h |

### Phase 5 — Never goes down

| # | Module | You'll build / learn | Est. |
|---|--------|----------------------|------|
| 18 | [Compose HA & Chaos Drills](./18-compose-ha-and-chaos/) | Redis Sentinel → Redis Cluster, Patroni + HAProxy + PgBouncer, Nginx sticky LB — then **kill every primary** | 7 h |
| 19 | [Kubernetes HA & Multi-Region](./19-kubernetes-ha-and-multiregion/) | StatefulSets, operators, PDBs, topology spread, zero-drop rolling deploys, cross-region fan-out | 6 h |
| 20 | [Observability & SLOs](./20-observability-and-slos/) | RED/USE metrics for a socket server, tracing an async fan-out, SLIs that matter for chat, alerting | 5 h |

### Phase 6 — Ship it

| # | Module | You'll build / learn | Est. |
|---|--------|----------------------|------|
| 21 | [Security & Abuse at Scale](./21-security-and-abuse-at-scale/) | WebSocket auth, token rotation on long-lived sockets, flood control, moderation, E2EE tradeoffs | 5 h |
| 22 | [Capstone — Pulse at 100k](./22-capstone/) | Wire it all together, hit a target load, survive a chaos drill, defend it in a written architecture review | 8 h |

**Total: ~110 hours of focused, hands-on work.**

---

## How each module is structured

```
NN-topic/
├── README.md      ← Concepts in plain language. Read this first.
├── lab.md         ← Step-by-step guided build with expected output. Do this second.
├── code/          ← Reference files the lab adds to the app (when applicable).
├── challenge.md   ← An unguided task to prove you understood it. Do this third.
└── solutions/     ← Reference answers — peek only after you've tried.
```

**The rhythm for every module:** read `README.md` → follow `lab.md` hands-on →
attempt `challenge.md` solo → check `solutions/`.

---

## The app you're building

One service under [`apps/pulse/`](./apps/pulse/) grows across the whole course,
with a React client under [`apps/pulse-web/`](./apps/pulse-web/).

It starts as "a STOMP endpoint that echoes a string" and ends as:

- A horizontally-scaled Spring Boot service holding tens of thousands of
  concurrent WebSocket connections per node.
- Fan-out over Redis Streams with consumer groups, at-least-once delivery,
  client-side dedup, and gap-detecting resume.
- Presence, typing indicators, read receipts, and unread counts that don't
  melt under a presence storm.
- A partitioned Postgres message store behind PgBouncer with read replicas,
  fronted by an app-level shard router.
- A transactional outbox so a message is never persisted-but-not-delivered
  (or delivered-but-not-persisted).
- Full HA: Redis Cluster, Patroni-managed Postgres, and a load balancer that
  survives you killing any single container.
- Prometheus metrics, distributed traces across the async fan-out, and SLOs
  with real alert rules.

---

## Reference material

| File | What it's for |
|------|---------------|
| [`GLOSSARY.md`](./GLOSSARY.md) | Plain-English definitions of every term, organized by topic |
| [`VERIFY.md`](./VERIFY.md) | End-to-end smoke test — confirm your environment before Module 01 |
| [`cheatsheets/websocket-stomp.md`](./cheatsheets/websocket-stomp.md) | Frame formats, STOMP commands, Spring annotations |
| [`cheatsheets/redis.md`](./cheatsheets/redis.md) | Commands by use case, Streams recipes, Cluster/Sentinel ops |
| [`cheatsheets/postgres-scale.md`](./cheatsheets/postgres-scale.md) | Partitioning, replication, pooling, EXPLAIN reading |
| [`cheatsheets/docker-ha.md`](./cheatsheets/docker-ha.md) | Compose HA topologies, healthchecks, failover commands |
| [`cheatsheets/load-testing.md`](./cheatsheets/load-testing.md) | k6 + Gatling WebSocket recipes, reading percentiles honestly |
| [`cheatsheets/troubleshooting.md`](./cheatsheets/troubleshooting.md) | Decision trees: dropped sockets, lost messages, replica lag, OOM |

---

## Related courses in this repo

This course sits in the middle of an existing pathway:

- **[`spring-boot-course`](../spring-boot-course/)** — if you want the broad
  Spring Boot foundation (REST, JPA, JWT, testing, OpenAPI) before or alongside
  this one. This course deliberately does *not* re-teach that material; it
  fast-tracks only what chat needs in Module 02.
- **[`kubernetes-course`](../kubernetes-course/)** — the deep Kubernetes
  foundation. Module 19 here assumes only the basics and cross-references it.
- **[`slack-clone-course`](../slack-clone-course/)** — the same product domain
  built on **Django Channels + Next.js**. Working both is genuinely valuable:
  you see how a different runtime model (Python ASGI) solves identical problems,
  and where the solutions converge.
- **[`linux-course`](../linux-course/)** — useful background for the chaos and
  networking drills in Module 18.

---

## Philosophy

- **Learn by doing.** 80% of your time is hands on keys.
- **Production patterns, not toys.** One real app, grown across 23 modules.
- **Deliberate failure.** You will kill primaries, drop packets, exhaust
  connection pools, and induce replica lag — on purpose, while watching.
- **Measure, don't assume.** Every performance claim comes with a benchmark you
  run yourself.
- **Local-first.** Everything runs on one laptop with free tools.
- **Modern and idiomatic.** Java 21, Spring Boot 3.x, Redis 7.x, Postgres 16,
  Next.js App Router. No legacy patterns.

---

Start with **[Module 00 — Setup & Orientation](./00-setup/)**.
