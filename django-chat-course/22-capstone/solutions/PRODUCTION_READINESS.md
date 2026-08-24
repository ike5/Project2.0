# Pulse — Production Readiness Assessment

The temptation in a capstone is to declare completion. The skill — and the last
lesson of the course — is naming what is not ready, in the language of a release
meeting, before someone else does it for you in an incident review.

**This document is deliberately unflattering.** Nine gaps, five of them release
blockers, one of which the capstone itself created.

**Scope of the claim being assessed:** Pulse held 100,000 concurrent WebSocket
connections, met all four SLOs (delivery success 99.993%, p99 delivery 296 ms,
connection success 99.96%, 3 permanent sequence gaps), and survived eight chaos
drills under that load with RPO 0 and a worst RTO of 13.2 s.

---

## Done and verified

Each of these works and has a drill or a test that proves it — not a design
document that asserts it.

- **Chat core** — rooms, membership, presence, typing, read receipts, unread
  counts (Modules 04, 10, 11). Covered by the capstone smoke test.
- **The delivery guarantee** — at-least-once with `(room_id, client_id)`
  idempotency and Lua-atomic `seq`+`XADD`: **0 messages lost across all eight
  chaos drills at 100,000 connections** (Modules 05, 09, 10, 13).
- **Resume** — a 120-second disconnect replays 84 messages, loses 0, reports 0
  gaps (Modules 10, 17), verified in a real browser.
- **HA** — RPO 0 on 8/8 drills, worst RTO 13.2 s under full load, fencing proven
  by demonstration twice: a returning Redis primary demoted to replica, a returning
  Patroni node rejecting writes with `read-only transaction` (Modules 18, 19, 22).
- **Zero-downtime rolling deploy** — 0 s RTO, 0 messages lost, clients see close
  code 1001 with `retry_after` in a median of 4 ms (Module 18).
- **Capacity-aware readiness** — a browned-out pod removes itself before it becomes
  everyone's problem: RPO 4,102 → 0 (Module 18).
- **Auth** — CSWSH demonstrated and blocked, ticket replay rejected, identity
  cross-check never defeated in a 3-hour red-team exercise (Module 21).
- **Observability** — the five incident questions answerable from Grafana alone in
  53 seconds; four SLOs with two-window burn-rate alerts; a synthetic prober that
  closes the last hop server-side metrics cannot see (Module 20).
- **The capacity model** — Module 07's `55 µs + 46 µs × W` predicted the capstone's
  ceiling to within 4.5%, which is why decisions #7 and the 1M plan are arithmetic
  rather than opinion.

---

## Done but not production-grade

Works in the lab; needs specific hardening before real traffic.

- **Rate-limit values** are tuned for the benchmark workload. Real limits need
  product input on legitimate usage — the offline-outbox replay after a tunnel
  looks exactly like an attack to a token bucket (Module 21's challenge), and the
  earned catch-up allowance that fixes it has never met a real user.
- **The abuse detector** uses hand-tuned heuristics (account age, content
  similarity, fan-out rate). Production wants a trained model and a feedback loop
  from moderator actions. The heuristics also lose content similarity entirely in
  E2EE rooms.
- **Partition management** is a Celery beat task. Production wants `pg_partman`,
  the runway alert from Module 13's challenge, and monitoring that pages when the
  next partition is not yet created — a missing partition is a hard insert failure,
  not a degradation.
- **The outbox pruning job** has never run against billions of rows. Its behaviour
  at that size is unknown and the relay has never been up for months.
- **Celery beat is a single scheduler.** It is not fenced, and two of them produce
  duplicate partition DDL and duplicate presence sweeps. The relay itself *is*
  fenced (`FOR UPDATE SKIP LOCKED`, Module 18's challenge); beat is not.
- **`maxReplicas: 4` is enforced by a comment and an HPA field.** Nothing prevents
  an operator from raising it during an incident, which would *lower* the fan-out
  ceiling by 19% at exactly the wrong moment. This needs an admission policy or a
  loud alert, not a comment.

---

## Faked for the course

Honest about the shortcuts, because every one of them looks finished from the
outside.

- **The JWT issuer** is a test signer with a static key. There is no IdP, no key
  rotation, no JWKS endpoint, no refresh flow.
- **Push notifications** are stubbed. APNs/FCM, batching, do-not-disturb and the
  "was it delivered to the device or just to the socket?" question are an entire
  subsystem the course named and did not build.
- **E2EE** (Module 21) uses RSA-OAEP + AES-GCM to make the tradeoff concrete, not
  the Signal Double Ratchet. Real E2EE needs X3DH, per-device ratcheting, safety
  numbers and a key-transparency story.
- **Search** is deliberately absent (Module 12: "search goes elsewhere"). The
  capstone's stretch task sketches it and finds it re-opens architecture decision
  #3.
- **Media and file uploads** — none.
- **A bot or integration platform** — none.
- **Multi-tenancy** — the shard router keys on room, not on tenant. There is no
  tenant isolation boundary anywhere in the system.
- **The load figures are laptop-scale extrapolations.** They are internally
  consistent and the model matched measurement to 4.5%, but "8 cores and 16 GB with
  Docker" is not "four production nodes," and the capstone says so rather than
  pretending otherwise.

---

## Would not ship without — release blockers

1. **A real auth issuer.** The test signer is a security hole with no mitigating
   control. Nothing else on this list matters if this one is open.
2. **A CI assertion that the ORM threadpool and the loop's default executor are
   separate objects.** The capstone's Task 2 found that welding them
   (`loop.set_default_executor(SyncToAsync.executor)`, one line added as a
   *sensible* optimisation) starves seven of sixteen workers for 22 seconds during
   a Redis failover, with every dashboard green because the loop is **starved, not
   blocked**. The fix is three lines and it is shipped. **Nothing tests it**, so the
   next well-meaning refactor re-welds them and the failure returns invisibly.
   *This blocker was created by this capstone*, which is the most useful thing on
   the list: the system got safer and the test surface did not.
3. **A contract test for the pre-serialized send path.** Task 3's improvement
   bypasses `AsyncJsonWebsocketConsumer.send_json` for a 15% p99 win. A Channels
   release that changes the consumer's send path breaks Pulse **silently** — no
   exception, wrong or unencoded frames. Pin the Channels version *and* assert the
   wire bytes in CI, or revert the optimisation.
4. **Automatic room-size-threshold switchover to fan-out-on-read.** The hot-room
   flaw is real (Module 14: a hot partition cannot be split by adding hardware) and
   bounded only by a 50,000-member cap. A 50,000-member room where everyone talks
   is **13.9 million outbound msg/s from one room** — more than fourteen times the
   current cluster's entire 956,000 msg/s fan-out ceiling. The mitigation is
   designed and not automated; a viral room degrades everyone before anyone reacts.
5. **Either managed Postgres, or a funded on-call rotation for self-managed
   Patroni.** Module 19 was explicit that self-managing needs a reason and a team.
   "We built it in a course" is a reason to understand it, not a reason to run it.

---

## Explicitly out of scope — decided, not forgotten

- **Multi-region write capability.** Module 19's analysis: edge-terminated sockets
  with a home region per room deliver most of the latency benefit for a fraction of
  the cost and complexity, and two independent sequencers destroy the per-room
  `seq` guarantee that Modules 05, 10 and 17 all stand on. A deliberate choice, and
  it is written down as one.
- **Wide-column storage.** Module 14's benchmark says sharded Postgres wins at our
  scale, mainly on the idempotency check. Revisit above ~300k sustained writes/s or
  when a Cassandra-fluent team exists.
- **Kafka.** Architecture decision #3, conditional on one consumer and fewer than
  ~24 subscribed worker processes. Both conditions are currently true and both are
  plausibly false within a year.
- **A Go/Rust socket edge.** Architecture decision #2's provisional half. The
  crossover is ~400,000 connections; we are at 100,000. Not building it now is
  correct; not having measured the crossover would not have been.
- **Raw ASGI for the hot path.** Module 15 measured 28 KB/connection against
  Channels' 45 KB — 38% denser, and we use 16% of the memory ceiling. Buying
  density we do not need with several hundred lines we would own forever is the
  wrong trade until decision #2's condition fires, and then an edge tier is the
  better version of the same idea.

---

## Honest summary

This is a faithful reference architecture. It holds 100,000 concurrent
connections, meets all four SLOs, survives eight chaos drills under that load with
RPO 0, and can be defended decision by decision with a measurement and a rejected
alternative behind each one.

**It is not a product.** The gap between "passes the capstone" and "serves real
users" is exactly the five release blockers above — a real auth issuer, two CI
assertions guarding two optimisations that are correct today and silently fragile
tomorrow, automated hot-room handling, and a production database posture.

Two of those five exist **because** of work done in this capstone. That is not an
embarrassment; it is the pattern. Every optimisation narrows the margin somewhere
else, and the only defence is writing down where.

And one thing is worth stating plainly for whoever inherits this: **the resource
that binds Pulse is not the one anybody expects.** It is not memory, not the GIL,
not Postgres. It is a single Redis thread being told about each message once per
subscribed worker process — which means the instinct that saves most systems under
load, *add another replica*, makes this one **19% worse**. That fact is in the HPA
comment, in architecture decision #7, and in the runbook, and it should be the
first thing said in the handover.

**A system that works in the lab is a hypothesis about a system that works in
production.** Being able to list exactly what stands between the two — with a
number next to each item and a name next to each blocker — is the deliverable. A
readiness document that said "everything is ready" would be the one result that
fails this capstone.
