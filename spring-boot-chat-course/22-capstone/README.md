# Module 22 — Capstone: Pulse at 100k

**Goal:** Wire everything together into one deployable system, hit a real load
target, survive a chaos drill under that load, and defend the whole design in a
written architecture review.

⏱️ ~8+ hours · **Prerequisites:** all of Modules 00–21.

---

## What the capstone is

Every prior module built or measured one piece. The capstone is the integration:
a single Pulse deployment that must **simultaneously** hold 100,000 concurrent
connections, deliver at its SLO, survive you killing its database primary, defend
against a flood, and be observable while it does all of it.

It is deliberately not new material. It is the proof that the pieces compose —
which is a different and harder thing than the pieces working individually.

---

## The four deliverables

**1. A running system** that passes an acceptance test at target load.

**2. A chaos run** — the full Module 18 drill suite, executed while the acceptance
load is running, with measured RTO/RPO for each.

**3. A written architecture review** — the document you would defend to a skeptical
senior engineer, with the numbers behind every decision and the alternatives you
rejected.

**4. A production-readiness assessment** — an honest accounting of what is done,
what is faked, and what you would not ship without.

---

## The target

```
100,000 concurrent WebSocket connections
     1,000 rooms, average 100 members (p95 room size 1,000)
       ~1 message per user per 3 minutes  = 556 inbound msg/s
     fan-out amplification 100x           = 55,600 outbound msg/s
        peak burst 10x                    = 556,000 outbound msg/s

SLO 1: 99.9% of messages delivered within 500ms (30-day)
SLO 2: 99.99% delivery success
SLO 3: 99.9% connection success
SLO 4: < 0.01% of rooms with a permanent sequence gap

Survive, under the above load, with RPO 0 and RTO < 30s:
  - Redis primary kill
  - Postgres primary kill
  - App node kill
  - A rolling deploy
  - A distributed flood
```

At 100k connections and 71 KB/connection (Module 15's tuned figure), that's
~7 GB of connection state, which at ~35,000 connections/node (Module 19's HPA
math) means **3 app nodes minimum, 4 for headroom.**

> **Scale it to your hardware.** If your laptop can't do 100,000, do 20,000 with
> the same room structure and note the scale factor. Every conclusion holds; the
> capstone is about *composition under load*, not the absolute number.

---

## The complete architecture

```
                          ┌────────────────────┐
   Next.js clients ──wss──▶│  nginx / ingress   │  cookie-consistent-hash,
   (Module 17)            │  ws-aware, drained  │  handshake rate-limited
                          └─────────┬──────────┘
                    ┌───────────────┼───────────────┐
                ┌───▼───┐       ┌───▼───┐       ┌───▼───┐
                │pulse-1│       │pulse-2│       │pulse-N│  virtual threads (M01)
                │ STOMP │       │ STOMP │       │ STOMP │  graceful drain (M18/19)
                └───┬───┘       └───┬───┘       └───┬───┘  JWT+ticket auth (M21)
                    └───────┬───────┴───────┬───────┘
              ┌─────────────┼───────────────┼─────────────┐
        ┌─────▼──────┐  ┌───▼────────┐  ┌───▼──────────┐  │
        │Redis Cluster│  │  Postgres  │  │   Prometheus │  │
        │ Streams:    │  │  Patroni   │  │  Tempo/Loki  │  │
        │  fan-out(M09)│  │  sharded   │  │  SLOs (M20)  │  │
        │ Hashes:     │  │  partitioned│ └──────────────┘  │
        │  presence   │  │  outbox(M13)│                   │
        │  unread(M11)│  │  PgBouncer  │◀── outbox relay ──┘
        └─────────────┘  └────────────┘    (M13)
```

Every box is a module:

| Component | Module | What it provides |
|-----------|--------|------------------|
| Virtual-thread STOMP server | 01, 04 | Connection density, working chat |
| Protocol (clientId, seq, ack) | 05 | Idempotency, gap detection |
| Redis Streams fan-out | 07, 09 | At-least-once cross-node delivery |
| Resume + offline | 10, 17 | The last-hop guarantee |
| Presence + rate limits | 11 | Bounded presence, abuse control |
| Partitioned sharded Postgres | 12, 13, 14 | Durable store, instant retention |
| Transactional outbox | 13 | No dual-write hole |
| HA (Sentinel/Patroni/PDB) | 18, 19 | RTO<30s, RPO 0 |
| SLOs + tracing | 20 | Knowing whether it works |
| Auth + abuse defense | 21 | Not getting owned |

---

## The rubric

Your capstone is assessed on five axes. The reference solution scores itself
against this, honestly.

| Axis | What "excellent" means |
|------|------------------------|
| **Correctness** | Zero message loss across every chaos drill; every SLI measured, not asserted |
| **Performance** | Hits the load target with p99 inside SLO; the knee is known and you operate below it |
| **Resilience** | RTO<30s / RPO 0 on every drill; failures are visible and bounded |
| **Observability** | Every incident question answerable from the dashboard in under a minute |
| **Judgment** | Every major decision defended with numbers *and* its rejected alternative; production gaps named honestly |

The fifth axis is the one that matters most, and it's the whole point of the
course: **can you defend the design, including what you chose not to do?**

---

## The architecture review document

This is the real deliverable. It must contain, for each major decision:

1. **The decision**, in one sentence.
2. **The evidence** — the measurement that supports it, from your own runs.
3. **The alternative you rejected**, and the number that rejected it.
4. **The condition that would change it** — what would have to be true for the
   other choice to win.

A decision without all four is an assertion. The course has spent 22 modules
generating the four for every choice; the review collects them.

---

## What's next

The lab wires the full stack, runs the acceptance test, executes the chaos suite
under load, and produces the review. The solution is a complete reference
architecture review and a production-readiness assessment that is honest about
what a course can and cannot build.

See you in [`lab.md`](./lab.md).
