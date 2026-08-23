# Pulse — Production Readiness Assessment

The temptation in a capstone is to claim completion. The skill — and the final
lesson of the course — is naming what isn't ready. This document is deliberately
unflattering.

---

## Done and verified

Each of these works and has a test or drill that proves it:

- **Chat core** — rooms, presence, receipts, typing (Modules 04, 11) — smoke test.
- **Delivery guarantee** — at-least-once + idempotency, 0 loss across every chaos
  drill (Modules 05, 09, 13, 22).
- **Resume** — 2-minute disconnect loses 0 (Modules 10, 17), verified in a real
  browser via Playwright.
- **HA** — RTO<12.4s / RPO 0 on every drill under 100k load (Modules 18, 22).
- **SLOs** — all four green at target load; every SLI measured, not asserted
  (Module 20, 22).
- **Auth** — JWT + ticket, revocation, CSWSH blocked, each proven against an
  attack (Module 21).
- **Observability** — every incident question answerable in <1min; blind-tested
  (Modules 18, 20).

---

## Done but not production-grade

Works in the lab; needs hardening before real traffic:

- **Ticket store** is in-process. Trivially wrong for multiple nodes — must be
  Redis (a 10-line change we didn't make because the lab ran single-issuer).
- **Rate-limit tuning** is set for the benchmark workload. Real limits need
  product input on legitimate usage patterns.
- **The anomaly detector** uses hand-tuned heuristics (account age, content
  similarity). Production wants a trained model and a feedback loop from
  moderator actions.
- **Partition management** is a scheduled job. Production wants pg_partman with
  monitoring and the runway alert from Module 13's challenge.
- **The outbox relay** is fenced (Module 18 challenge) but hasn't run for months;
  the pruning job's behaviour at billions of rows is untested.

---

## Faked for the course

Honest about the shortcuts:

- **Auth issuer** — a test JWT signer, not a real IdP/OAuth provider.
- **Push notifications** — stubbed. APNs/FCM integration, batching, and
  do-not-disturb are a whole subsystem the course named but didn't build.
- **E2EE** (Module 21) — RSA-OAEP + AES-GCM to demonstrate the tradeoff, not the
  Signal Double Ratchet. Real E2EE needs X3DH, per-device ratcheting, and safety
  numbers.
- **Search** — deliberately out (Module 12). "Search goes to Elasticsearch" is
  named, not built (challenge Task 6 sketches it).
- **Bot/integration platform** — none.
- **Media/file uploads** — none (cross-referenced to spring-boot-course's MinIO
  work, not integrated).

---

## Would not ship without (release-blockers)

1. **A real auth issuer.** The test signer is a security hole, full stop.
2. **Ticket store in Redis.** In-process breaks the moment you have >1 node,
   which is always.
3. **Automatic room-size-threshold switchover to fan-out-on-read.** The hot-room
   flaw (Module 14) is mitigated in *design* but not *automated* — a viral room
   would degrade before anyone reacted.
4. **A decision on Redis Cluster resharding** (capstone Task 2 gap): either fix
   the sequence-gap-under-reshard bug or adopt a scheduled-maintenance policy.
5. **Either managed Postgres or a funded on-call rotation** for self-managed
   Patroni. Module 19 was explicit that self-managed needs a reason and a team.

---

## Explicitly out of scope (decided, not forgotten)

- **Multi-region write capability** — Module 19 argued edge-terminated
  single-region is 70% of the benefit for 15% of the cost. A deliberate choice.
- **Wide-column storage** — Module 14's benchmark said sharded Postgres wins at
  our scale. Revisit at >300k writes/s.
- **Kafka** — Module 16's decision, conditional on staying under ~8 nodes and one
  consumer.

---

## Honest summary

This is a faithful reference architecture. It passes its SLOs at 100,000
connections, survives every chaos drill with RPO 0, and can be defended decision
by decision.

**It is not a product.** The gap between "passes the capstone" and "serves real
users" is precisely the five release-blockers above — a real auth issuer, a
distributed ticket store, automated hot-room handling, a resharding policy, and a
production database posture.

That gap is the capstone's final lesson. **A system that works in the lab is a
hypothesis about a system that works in production.** Knowing the difference —
being able to list exactly what stands between the two — is the deliverable. A
readiness doc that said "everything is ready" would be the one result that fails
this capstone.
