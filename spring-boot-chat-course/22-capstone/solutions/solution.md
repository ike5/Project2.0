# Solutions — Module 22 (Capstone)

This is the reference capstone. It includes the two required documents
(architecture review and production-readiness) and worked answers to the
challenge. **The point of the reference is not to be copied — it's to show what
"defensible" looks like, including the parts that are honestly incomplete.**

---

## Task 1 — Your knee, and a 1M-user plan

### Finding the knee

Push the acceptance test past 100k:
```bash
for target in 100000 150000 200000 250000; do
  k6 run -e TARGET=$target code/acceptance.js
done
```
**Expected (4 nodes, tuned):**
```
100,000: all SLOs green, p99 284ms
150,000: all green, p99 388ms
200,000: connect_success 99.7% (SLO BREACH), p99 462ms
250,000: connect_success 98.1%, p99 1,840ms, delivery_success 99.94%
```

**The knee is ~185,000 connections on 4 nodes**, and **connection success breaks
first** — not latency, not delivery. Diagnose:
```bash
kubectl top pods -l app=pulse
```
```
pulse-1  1.8 cores  7.4Gi/8Gi   <-- MEMORY bound, at 46,000 connections
```

✅ **Memory-bound at ~46k connections/node**, matching Module 15's 71 KB/conn
math (7 GB / 71 KB ≈ 98k theoretical, ~46k practical with JVM overhead and
headroom). The binding resource is per-connection memory, exactly as Module 06
predicted and Module 15 measured.

### The 1M-user plan

```
1,000,000 concurrent connections
  ÷ 46,000/node (measured, conservative)
  = 22 app nodes (26 for N+2 headroom and rolling-deploy surge)

Fan-out at 1M users, 100-member rooms, peak 10x:
  inbound peak:  1,000,000 / 18s = 55,600 msg/s
  outbound peak: × 100 = 5,560,000 msg/s
  ÷ Redis Streams ceiling ~85k/node/consumer-group (Module 09 challenge)
  ... but per-node consumer groups mean each of 26 nodes reads everything
  ... 26 nodes × 85k = the read amplification wall from Module 09
  => Redis Streams DOES NOT SCALE to 26 nodes (saturates at ~9)
```

**Breaking point 1: the fan-out backbone.** At 26 nodes, per-node consumer groups
saturate Redis (Module 09's challenge measured this at ~9 nodes). The plan must
switch to **the fan-out tier from Module 09's solution** — dedicated fan-out
nodes with room affinity (3 per room by consistent hash), forwarding to app
nodes — OR to Kafka (Module 16 named "node count > 8" as the first trigger).

**Breaking point 2: the sequencer.** One `INCR` per room per message. At
5.5M outbound / 100 = 55,600 room-writes/s across 1,000 rooms is fine — but a
single **hot room** (a 500,000-member announcement channel) is one `INCR` on one
Redis slot, and Module 14 showed a hot key cannot be split by adding hardware.
The plan must cap room size and switch huge rooms to **fan-out-on-read** (Module
12, Module 14).

**The plan:**

| Tier | 100k | 1M |
|------|------|-----|
| App nodes | 4 | **26** |
| Fan-out | per-node consumer groups | **dedicated fan-out tier, room affinity** (or Kafka) |
| Redis | 6-node Cluster | **Cluster, 12 primaries, sharded by room** |
| Postgres | 4 logical shards / 1 physical | **4096 logical / 16 physical** (Module 14) |
| Cost/month (AWS) | ~$3,660 | **~$38,000** |
| Team to operate | 1–2 | **a dedicated platform team** |

> **The honest conclusion:** the architecture in this course scales to ~150k
> comfortably and ~500k with the fan-out-tier change. Past that, it becomes a
> different system with a different team, and that's the point at which "buy or
> build the fan-out edge in Rust/Go" (Module 06's capacity plan) is the real
> decision. **Knowing where your architecture stops is more valuable than
> claiming it doesn't.**

---

## Task 2 — A novel failure, each way

### One it survives: a slow Postgres replica poisoning reads

Not in the drill suite. Induce it:
```bash
docker exec capstone-pg-replica psql -c "SELECT pg_sleep(300)"  # block replay
```
**Expected:**
```
[replica lag climbs to 300s]
ReadRouter: replica marked UNUSABLE (lag 300s)   <-- Module 13's monitor
all reads move to primary; delivery_success unchanged 99.99%
```
✅ **Survived** — Module 13's replica health monitor demoted the lagging replica.
Reads went to the primary; users noticed nothing. This composed correctly from a
Module 13 mechanism the drill suite never exercised.

### One it doesn't: a Redis Cluster slot migration under load

```bash
docker exec capstone-redis-1 redis-cli --cluster reshard capstone-redis-1:6379 \
  --cluster-from <node> --cluster-to <node> --cluster-slots 1000 --cluster-yes
# while the acceptance load runs
```
**Expected:**
```
[during migration]
io.lettuce.core.RedisCommandExecutionException: ASK 5461 redis-3:6379
delivery_success dips to 99.2%   <-- SLO BREACH
sequence_gaps: 41
```
❌ **Failed.** During a live slot migration, keys are briefly split between the
source and destination node (`ASK` redirects), and the Lettuce client's handling
of `ASK` under high throughput dropped some stream reads. **Sequence gaps
appeared** — a real correctness failure.

**Root cause:** the append (Lua, Module 08) and the stream read are on the same
slot, but *during* migration a `MULTI`/Lua touching that slot can fail
mid-reshard, and the retry wasn't idempotent for the seq allocation.

**Fix (in scope):** make the reshard-time retry idempotent — the seq allocation
already is (Module 05's `ON CONFLICT`), but the *Redis* seq counter isn't. Move
the authoritative seq to the outbox-backed Postgres path during migrations, or:

**Fix (out of scope — documented as a gap):**
```markdown
## PRODUCTION GAP: live Redis Cluster resharding
Resharding under load causes brief sequence gaps (measured: 41 over a 1,000-slot
migration at 100k load). Mitigation: reshard during low-traffic windows, or
migrate to the fan-out-tier architecture where the sequencer is decoupled from
Cluster slots. Release-blocker for a system that must reshard without a
maintenance window; acceptable with scheduled maintenance.
```

> **This is the capstone's real lesson.** The system survives everything on the
> drill list and fails something that wasn't. **A fixed test suite proves you
> handle the failures you thought of.** The novel-failure task is where you learn
> what you didn't.

---

## Task 3 — One measured improvement

**Chosen: the L1 rate-limiter (Module 21's Task 4 solution).**

Why this one over the alternatives:

| Candidate improvement | Benefit | Cost | Verdict |
|----------------------|---------|------|---------|
| Socket buffer tuning (Module 06) | +27% conn density | already applied | done |
| WebFlux hot path (Module 15) | +20% density | 2.6x debug cost, no STOMP | rejected |
| L1 rate limiter | +3% throughput on hot path | ~40 lines | ✅ **best ratio** |
| Fan-out tier (Module 09) | scales past 9 nodes | weeks of work | not needed at 100k |

The L1 limiter: a per-node in-process token bucket in front of the Redis Lua
bucket, so 95% of messages never make a rate-limit round trip.

**Before/after acceptance test:**
```
Before:  p99 284ms, throughput knee 700k/s, Redis CPU 51%
After:   p99 268ms, throughput knee 740k/s, Redis CPU 44%
```
✅ **+6% throughput, −6% p99, −7% Redis CPU for 40 lines.** The justification is
the ratio: every other improvement either was already done, cost too much
(WebFlux), or wasn't needed yet (fan-out tier). This is the highest
benefit-per-line change remaining.

---

## Task 4 — The runbook

See [`RUNBOOK.md`](./RUNBOOK.md) (excerpt in Module 18's solution). Blind-test
result:
```
Injected: distributed flood (blind)
Engineer followed SLO-2 (delivery success) alert -> anomaly detector page ->
identified quarantine in 4 minutes. ✅
Injected: Redis slot migration gap (the Task 2 failure, blind)
Engineer had NO runbook entry (it's a documented gap, not an alert).
Spent 18 minutes before checking the gaps doc. ✅ found it, but slow.
Fix: add an alert for sequence_gaps > 0 that links directly to the gaps doc.
```

> The blind test found the same thing Module 18's did: **the gap without an alert
> is worse than the gap without a fix.** Added `chat_sequence_gaps > 0` → page,
> linking to the known-gaps document.

---

## Task 5 — Three objections, answered

**Objection 1: "Redis Streams is a single point of failure for delivery. Kafka
would be more durable."**

*Rebut with a number, then concede partially.* Redis Streams with the outbox
(Module 13) lost **0/200** on a Redis kill in Module 09's re-test, because the
outbox republishes. So the durability objection is answered — Postgres is the
source of truth. **But** Module 16 measured that Redis saturates at ~9 consuming
nodes, and the 1M-user plan (Task 1) needs 26. **Concede:** past ~150k users,
Kafka or the fan-out tier is correct, and the review's "would change if" already
says so.

**Objection 2: "Sharding by room means a hot room can't be scaled. That's a
design flaw."**

*Concede and point to the mitigation.* Correct — Module 14 proved a hot partition
can't be split. **But** it's a bounded flaw: room size is capped (Module 21), and
huge rooms switch to fan-out-on-read (Module 12/14). The sequencer for a
500k-member announcement channel is a read-mostly workload, not a write-hot one.
**The flaw is real and the mitigation is designed**; what's not built is the
automatic switchover at the threshold — that's a named production gap.

**Objection 3: "You're running your own Postgres HA with Patroni. Just use RDS
and stop maintaining a database."**

*Concede almost entirely.* This is the strongest objection and the honest answer
is "you're probably right." Module 19 said as much: "a managed database is less
operational work, and running your own should be a decision with a reason."
**The reason here is pedagogical** — the course builds it so you understand what
the operator does. **In production, RDS Multi-AZ or Aurora is the correct default**
unless you have a specific reason (cost at scale, a feature RDS lacks, existing
Postgres expertise). The review's production-readiness doc lists "self-managed
Postgres" under "would reconsider for production."

> **Two of three objections are substantially conceded.** That is what a good
> architecture review looks like — not a defense of every choice, but an honest
> map of which choices are firm and which are pedagogical or provisional.

---

## Task 6 (stretch) — What I'd build next

**Message search at scale.**

The most-requested chat feature the course deliberately skipped (Module 12: "no
FTS in Postgres, search goes elsewhere").

**Architecture:**
```
outbox relay (Module 13) ──┬──▶ Redis Streams (delivery)
                           └──▶ Kafka ──▶ Elasticsearch/OpenSearch indexer
                                          (the second consumer Module 16 said
                                           would flip the Redis-vs-Kafka decision)
```
- The outbox already exists; add a second publish target (Module 16's Task 6
  dual-backbone, done correctly *from the outbox* so there's no divergence).
- An indexer consumer group on Kafka feeds OpenSearch.
- Search queries hit OpenSearch, authz-filtered by the user's room membership.

**Most disrupted module: 16.** Adding a search consumer is precisely the trigger
Module 16 named — "the moment a second consumer appears, Kafka's shape is right
and Redis Streams' is wrong." So **shipping search likely means adding Kafka**,
which changes the fan-out backbone decision. The whole system's "Redis Streams
over Kafka" conclusion is conditional on there being one consumer; search removes
that condition.

**Effort:** ~4 engineer-weeks. The hard parts are not the indexer (a week) but:
- Authz on search results (you can't return messages from rooms the user left) —
  the Module 21 delivery-time authz problem, at query time.
- Reindexing on edits/deletes (Module 12's edit path must fan out to the index).
- E2EE rooms are unsearchable server-side (Module 21) — the search UX must handle
  "this room's messages aren't in results" gracefully.

> The instructive part: **the feature that looks like "just add Elasticsearch" is
> actually the feature that reopens the biggest architectural decision in the
> course.** That's the kind of second-order consequence the whole course was
> training you to see.

---

## ARCHITECTURE_REVIEW.md (reference)

The complete review lives in
[`ARCHITECTURE_REVIEW.md`](./ARCHITECTURE_REVIEW.md). Nine decisions, each with
decision / evidence / rejected alternative / falsifying condition. It scores
**excellent on judgment** specifically because two of nine decisions are
conceded-provisional (self-managed Postgres, Redis-over-Kafka), not defended to
the death.

## PRODUCTION_READINESS.md (reference)

The complete assessment lives in
[`PRODUCTION_READINESS.md`](./PRODUCTION_READINESS.md). Its headline:

```markdown
## Would not ship without
1. Real auth issuer (currently a test JWT signer) — RELEASE BLOCKER
2. Automatic room-size-threshold switchover to fan-out-on-read — the hot-room
   flaw is mitigated in design but not automated
3. Redis Cluster resharding without sequence gaps (Task 2 gap) — or a
   scheduled-maintenance policy
4. Managed Postgres, or a funded on-call rotation for self-managed Patroni

## Faked for the course
- Ticket store is in-process (should be Redis, trivially)
- Push notifications are stubbed
- E2EE uses RSA-OAEP + AES-GCM, not the Signal Double Ratchet
- The abuse ML signals are heuristics, not a trained model

## Honest summary
This is a faithful reference architecture that passes its SLOs and survives its
drills. It is NOT a product. The gap between "passes the capstone" and "handles
real users" is exactly the four release-blockers above — which is itself the
capstone's final lesson: a system that works in the lab is a hypothesis about a
system that works in production.
```

---

## Scoring this capstone against the rubric

| Axis | Score | Why |
|------|-------|-----|
| Correctness | **Excellent** | 0 message loss on every drill; every SLI measured, not asserted; found a real correctness bug (Task 2 reshard) |
| Performance | **Excellent** | Hits 100k with SLOs green; knee found at 185k; operates below it |
| Resilience | **Strong** | RTO<30s/RPO 0 on all drills; the 24k-reconnect wart named, not hidden |
| Observability | **Excellent** | Every incident question answerable in <1min (Module 20); blind test passed |
| **Judgment** | **Excellent** | Every decision carries its rejected alternative; 2 of 9 conceded as provisional; production gaps named honestly, including 4 release-blockers |

The judgment axis is excellent **not despite** the concessions but **because of
them.** A capstone that defended every choice and claimed production-readiness
would fail the one axis the whole course exists to teach: knowing what you built,
what you didn't, and why.
