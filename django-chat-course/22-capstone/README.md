# Module 22 — Capstone: Pulse at 100k

**Goal:** Assemble every piece into one deployment, hit a stated load target under
stated constraints, survive a chaos run *while that load is running*, and defend
the whole design in a written architecture review that names its own rejected
alternatives and its own production gaps.

⏱️ ~8+ hours · **Prerequisites:** all of Modules 00–21. Every number you are asked
to defend here, you measured yourself in an earlier module.

> **The Python twin of
> [`spring-boot-chat-course/22-capstone`](../../spring-boot-chat-course/22-capstone/).**
> Same target, same four deliverables, same rubric. The JVM twin's capstone is
> **memory-bound**: it runs out of heap at ~46,000 connections per node and the
> capacity plan is "add nodes." Yours is not. Yours is bound by a **single Redis
> thread being told about a message once per subscribed worker process**, and the
> most important thing you will discover in this module is that **adding app
> replicas makes it worse**. That is the whole course arriving at once.

---

## What the capstone is, and what it is not

Every prior module built or measured one piece. The capstone is the integration:
one Pulse deployment that must **simultaneously** hold 100,000 concurrent
connections, deliver inside its SLOs, survive you killing its Redis and Postgres
primaries under that load, hold up against a distributed flood, and be observable
while it does all of it.

It is deliberately **not new material**, and deliberately **not a
build-one-more-feature exercise**. There is no new consumer to write, no new table
to migrate. The capstone is proof that the pieces *compose* — which is a different
and much harder thing than the pieces working individually — and proof that you can
**defend the composition**.

The last part is the point. Twenty-two modules have produced, for every decision,
four things: the decision, a measurement, an alternative you rejected, and the
condition that would flip it. The capstone collects them and makes you argue.

---

## The four deliverables

**1. A running system** that passes an acceptance test at target load, from
`pulse.settings.capstone` — every profile the course built, on at once.

**2. A chaos run** — Module 18's drill suite, executed *while* the acceptance load
is running, with a measured RTO and RPO for every drill.

**3. A written architecture review** — the document you would defend to a hostile
senior engineer, with the number behind every decision and the alternative each
one beat.

**4. A production-readiness assessment** — an honest accounting of what works,
what is faked, and what you would refuse to ship without. This one is graded on
being *unflattering*.

---

## The target

```
100,000 concurrent WebSocket connections

    480 chat rooms   x  200 members  =  96,000 sockets   1 msg / user / 180 s
      1 announcements x 4,000 members =   4,000 sockets   12 msg / hour, read-mostly
                                        --------
                                         100,000

  inbound  steady    96,000 / 180 s                  =        533 msg/s
  outbound steady    533 x 199  +  0.003 x 3,999     =    106,000 msg/s
  amplification                                            199x
  peak burst         5x for a 2-minute window        =    530,000 msg/s

SLO 1  Delivery success     >= 99.99%   (30-day)
SLO 2  Delivery latency     >= 99.9% of deliveries under 500 ms
SLO 3  Connection success   >= 99.9%
SLO 4  Sequence integrity   <  0.01% of rooms with a permanent gap

Survive, UNDER that load, with RPO 0 and RTO <= 15 s:
  - a channel-layer shard primary killed, and paused
  - a Postgres primary killed
  - an app pod killed
  - an app pod browning out (still "healthy", just slow)
  - a full rolling deploy
  - a distributed flood from 200 accounts on 200 source IPs
```

The four SLOs are [Module 20](../20-observability-and-slos/)'s, unchanged. The
RTO/RPO thresholds are [Module 18](../18-compose-ha-and-chaos/)'s, unchanged — note
they are **tighter than the JVM twin's 30 s**, because your Module 18 measured
worst-case 12.4 s once tuned and there is no reason to grade yourself against a
number you already beat.

> **Scale it to your hardware.** If your laptop cannot hold 100,000 sockets, run
> 20,000 with the *same room structure and the same amplification*, and record the
> scale factor. Every conclusion in this module is about the **shape** of the
> capacity curve, not the absolute number — and the shape is identical at 20k.
> [Module 06](../06-load-testing-harness/)'s generator-side tuning (`ulimit -n`,
> ephemeral port range, multiple source IPs) applies unchanged and is not optional.

---

## The architecture you are defending

```
                             ┌──────────────────────────────┐
   Next.js clients ───wss───▶│  nginx  (ws-aware, drains)   │  M17 client
   one socket per user,      │  handshake limit_req, cookie │  M18 nginx
   SharedWorker across tabs  │  consistent-hash stickiness  │  M21 origin+ticket
                             └──────────────┬───────────────┘
             ┌──────────────┬───────────────┼───────────────┬──────────────┐
        ┌────▼─────┐   ┌────▼─────┐    ┌────▼─────┐    ┌────▼─────┐
        │ pulse-1  │   │ pulse-2  │    │ pulse-3  │    │ pulse-4  │   M19 pods
        │ uvicorn  │   │ uvicorn  │    │ uvicorn  │    │ uvicorn  │   +uvloop
        │ 4 workers│   │ 4 workers│    │ 4 workers│    │ 4 workers│   M01/M15
        └────┬─────┘   └────┬─────┘    └────┬─────┘    └────┬─────┘
             │              │               │               │
             └──────┬───────┴───────┬───────┴───────┬───────┘
                    │               │               │
        ┌───────────▼───┐ ┌─────────▼─────┐ ┌───────▼───────┐  ┌──────────────┐
        │ channel-layer │ │  state Redis  │ │  PostgreSQL   │  │  Prometheus  │
        │  4 SHARDS     │ │  Cluster      │ │  CloudNativePG│  │  Grafana     │
        │  Sentinel x3  │ │  seq + stream │ │  PgBouncer    │  │  Tempo/Loki  │
        │  ea. (M18)    │ │  presence     │ │  partitioned  │  │  4 SLOs, two-│
        │               │ │  buckets      │ │  4096 logical │  │  window burn │
        │  M07 cost     │ │  tickets(lru) │ │  shards (M14) │  │  rates (M20) │
        │  model binds  │ │  M08/M09/M11  │ │  outbox (M13) │  └──────────────┘
        │  the WHOLE    │ │  M21          │ │       ▲       │
        │  system       │ └───────────────┘ └───────┼───────┘
        └───────────────┘                           │
                                      Celery outbox relay (M13), fenced by
                                      FOR UPDATE SKIP LOCKED (M18 challenge)
```

Every box is a module, and every box is a decision you have to defend:

| Component | Modules | What it provides | The number that justifies it |
|---|---|---|---|
| Async Channels consumers, 4 workers/pod | 01, 04, 15 | Connection density without per-connection threads | ≈45 KB/conn vs ≈120 KB sync |
| The JSON envelope: `client_id`, `id`, `seq`, `v` | 05 | Idempotency, gap detection, a future | 7 duplicate rows → 0 with the unique index |
| Lua `INCR`+`XADD` in one script | 10 | Gapless `seq` *and* stream order | 412 inversions / 10,000 → 0 |
| Custom Redis Streams layer + PEL | 09 | At-least-once across worker processes | ~15% lost on a `docker pause` → 0 |
| `RedisPubSubChannelLayer`, ephemeral path | 07 | Typing/presence/cursors, cheaply | 11× fewer Redis commands |
| Resume from cursor, offline queues | 10, 17 | The last hop, server → browser | 98 lost on a 2-min disconnect → 0 |
| TTL presence + viewport subscriptions | 11 | Presence that survives a storm | p99 8.9 s → 214 ms |
| Token buckets in Lua | 11, 21 | Abuse control that is actually atomic | 41% overshoot → exact |
| Partitioned, sharded Postgres, Snowflake IDs | 12, 13, 14 | Durable store, instant retention | 74 TB/yr → 18.4 TB live |
| Dual-path outbox + Celery relay | 13 | No persisted-but-never-delivered hole | +1.9 ms, vs 5.2× for outbox-only |
| Sentinel / CloudNativePG / capacity readiness | 18, 19 | RTO ≤ 15 s, RPO 0 | brownout RPO 4,102 → 0 |
| Four SLOs, two-window burn rates, a prober | 20 | Knowing whether any of it works | 5 incident questions in 53 s |
| Ticket + first-frame JWT + durable revocation | 21 | Not getting owned | TTFC 23 min → none in 3 h |

---

## The constraint the JVM twin does not have

Read this before you start the lab, because it determines your entire capacity
plan and it is the single most Python-specific result in the course.

[Module 07](../07-scale-out-redis-channel-layer/) regressed the channel layer's
cost against the number of **worker processes** subscribed to a group:

```
Redis time per group_send  =  55 µs  +  46 µs x W

                              ^^^^^     ^^^^^
                              read the  one more key in the EVAL,
                              membership one more BZPOPMIN wake-up
```

That per-worker term is charged against **Redis's single thread**, and `W` counts
*processes*, not machines. A JVM shop counts instances; you run one worker per
core, so a four-pod deployment is **sixteen** subscribers, not four.

[Module 19](../19-kubernetes-ha-and-multiregion/) turned that into arithmetic. For
`S` Sentinel-managed channel-layer shards, each carrying `1/S` of the traffic:

```
group_sends/s   =   S x 0.95 x 1,000,000 µs   ÷   (55 + 46·W) µs
outbound/s      =   group_sends/s x 199 recipients
```

| Pods | Workers `W` | 3 shards | 4 shards | Python ceiling | Which binds |
|---|---|---|---|---|---|
| 1 | 4 | 2,373,000 | 3,164,000 | ~521,000 | Python |
| 2 | 8 | 1,341,000 | 1,788,000 | ~1,010,000 | Python |
| 3 | 12 | **934,000** | 1,245,000 | ~1,490,000 | **Redis** |
| 4 | 16 | **717,000** | **956,000** | ~1,950,000 | **Redis** |

Read the third column downward. **Every replica you add subtracts capacity.**
Module 07 found it first ("eight workers were slower than four" — 441,000 vs
521,000 outbound msg/s), Module 19 named it ("the third replica is the new eighth
worker"), and the capstone is where it decides your topology.

Your target's burst is **530,000 outbound msg/s**, and
[Module 06](../06-load-testing-harness/) says operate at 60–70% of the knee, not
95%. Four pods on Module 18's **three** shards puts you at 74% of the ceiling —
inside the target and outside the safe operating point. The lab's Part A makes you
derive that *before* you run anything, and the answer is a **fourth channel-layer
shard**, which nothing in Modules 00–21 told you to build.

> **This is what "integrative" means.** No single module contains this result. It
> falls out of Module 07's regression, Module 19's shard arithmetic, Module 06's
> safe-operating-point rule and the capstone's own burst target — four modules that
> individually say nothing about how many Redis shards you need.

---

## The rubric

Assessed on five axes. The reference solution scores itself against them, honestly.

| Axis | What "excellent" means |
|---|---|
| **Correctness** | Zero message loss across every chaos drill; every SLI *measured*, never asserted; at least one real defect found by your own testing |
| **Performance** | Hits the target with all four SLOs green; the knee is a number you measured, and you operate below it on purpose |
| **Resilience** | RTO ≤ 15 s / RPO 0 on every drill *under load*; the failures that stayed ugly are named, not hidden |
| **Observability** | Every incident question answerable from the dashboard in under a minute; the alert that was missing gets added |
| **Judgment** | Every major decision carries its evidence *and* its rejected alternative; provisional decisions are labelled provisional; production gaps are named with the word "blocker" next to the ones that are |

The fifth axis matters most and is the reason the course exists: **can you defend
the design, including the parts you chose not to build?**

---

## The architecture review document

The real deliverable. For each decision it must contain, in this order:

1. **The decision**, in one sentence.
2. **The evidence** — a measurement from *your own* runs, with the module it came
   from.
3. **The alternative you rejected**, and the number that rejected it.
4. **The condition that would change it** — what would have to become true for the
   other choice to win, stated so that someone could go and check.

A decision missing any of the four is an assertion. Twenty-two modules have
generated all four for every choice in the system; the review is where you collect
them and find out which ones you cannot actually defend.

The reference review has **ten** decisions and marks **three** of them provisional
— including the choice of Python itself. It scores excellent on judgment *because*
of the concessions, not despite them.

---

## The five open tradeoffs the course refused to close

The course deliberately left these unresolved so you would have to close them
yourself, with your own numbers, in the review:

| Tradeoff | Where it was opened | What decides it for Pulse |
|---|---|---|
| Pub/Sub vs Streams vs Kafka | 07, 09, 16 | Subscribed-worker count and the number of consumers |
| Postgres vs wide-column | 12, 14 | The idempotency check, which Modules 05/09/10 all rest on |
| Compose vs Kubernetes | 18, 19 | Whether the ceiling is set by an HPA or by arithmetic |
| Async vs sync vs raw ASGI vs a Go/Rust edge | 01, 15 | Which resource is actually binding — and today it is not the runtime |
| Self-managed vs managed data tier | 18, 19 | Whether you have a funded on-call rotation |

Every one of them has a correct answer *for Pulse at 100,000 connections* and a
different correct answer somewhere on the growth curve. The review must say where.

---

## What's next

The lab derives the topology, wires the full stack, runs the acceptance test (it
fails the first time — for a reason no single module could have told you), fixes
it, runs the chaos suite under load, and produces the two documents.

See you in [`lab.md`](./lab.md).
