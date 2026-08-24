# Pulse — Architecture Review

**Audience:** a skeptical senior engineer who will ask "why not X?" for every line
and will not accept "it's the standard choice" as an answer.

**System:** Pulse, a real-time chat backbone on Django 5.1 / Channels 4.1 /
Uvicorn + uvloop, backed by Redis 7.2 and PostgreSQL 16.

**Target and result:** 100,000 concurrent WebSocket connections; 480 rooms of 200
members plus one announcement room of 4,000; 533 inbound msg/s, 106,080 outbound
steady, 530,400 outbound at a 5× burst. All four SLOs met (delivery success
99.993%, p99 delivery 296 ms against a 500 ms target, connection success 99.96%,
3 permanent sequence gaps). RPO 0 across eight chaos drills run under that load,
worst RTO 13.2 s.

**Format:** each decision states the decision, the evidence that supports it, the
alternative it beat and the number that beat it, and the condition under which the
alternative wins. **A decision missing any of the four is an assertion, not a
decision.** Three of the ten below are labelled **PROVISIONAL** — they are bets
whose odds are written down, and one of them is the runtime.

---

## 1. Transport and protocol: raw WebSocket with a hand-designed JSON envelope

**Decision.** Bidirectional traffic over a single WebSocket per user, carrying a
self-describing JSON envelope (`v`, `type`, `room`, `ts`, `data`) that Pulse
defines itself. No subprotocol. SSE-down + POST-up documented as a fallback for
hostile networks but not implemented.

**Evidence.** [Module 03](../../03-realtime-transports/) measured bytes on the
wire: WebSocket at 610 B/message against polling's 6,843 B and SSE's 921 B. Pulse's
upstream chatter — typing, read receipts, per-message acks, resume requests,
viewport updates — makes the 6-byte upstream frame decisive; an SSE design pays a
~500 B POST for every one of those. The envelope survived three transport changes
without a field change (Redis Streams in Module 09, a Postgres outbox row in
Module 13, a Kafka record in Module 16), which is the property `room` being
"redundant" with the URL was bought for.

**Rejected alternative.** STOMP over WebSocket, via one of the Python STOMP
libraries. It is what the JVM twin uses and it answers subscribe/ack/error for
free. Rejected because Channels ships no subprotocol support, the Python STOMP
libraries are not written for 100,000 concurrent sockets, and adopting a 1998 frame
format to get three verbs we would still have to extend is a poor trade. The cost
is real and stated: [Module 05](../../05-protocol-and-domain-design/) re-derives
things STOMP wrote down decades ago.

**Would change if.** Upstream traffic collapsed to chat sends only (debounced
typing plus batched acks would do most of it), *or* we had to run behind customer
proxies that strip `Upgrade`. Then SSE + POST becomes primary and gets
`Last-Event-ID` resume for free. This is the weakest of our firm decisions and
Module 03's own analysis concedes it.

---

## 2. Runtime: async Channels consumers, one Uvicorn worker per core — **PROVISIONAL**

**Decision.** The connection layer is `AsyncJsonWebsocketConsumer` on
Uvicorn + uvloop, four worker processes per pod, one per allocated core. All ORM
access goes through `database_sync_to_async` or Django's native async queries.

**Evidence.** [Module 15](../../15-async-sync-and-raw-asgi/) measured async
consumers at **≈45 KB per connection** against sync (threadpool) consumers at
**≈120 KB**, and the sync model's 12-thread pool is a hard ceiling under fan-out
where the loop is not. [Module 01](../../01-python-async-concurrency/) established
why there is no third option: Python has no virtual threads, one async worker uses
one core, and you scale CPU with processes. In the capstone run we hold 6,250
connections per worker at 16% of the memory ceiling, and after the Task 3
improvement worker CPU peaks at 61% during the burst.

**Rejected alternative.** Two of them.
*Sync consumers:* simpler, immune to the blocking-the-loop footgun by construction,
and 2.7× the memory per connection with a hard threadpool ceiling. Right for an
internal tool; wrong at 100,000 sockets.
*Raw ASGI (Starlette / the `websockets` library):* Module 15 measured **28 KB per
connection**, 38% denser than Channels — and costs us groups, auth, routing, the
consumer lifecycle and all of Module 10's resume wiring, several hundred lines to
rebuild and own forever. We use 16% of our memory ceiling; buying density we do not
need with code we would have to maintain is a bad trade *today*.

**Would change if — and this is the provisional part.** Past roughly **400,000
connections**, the number of *subscribed worker processes* required grows past the
point where any affordable channel-layer shard count keeps up (see decision #7 and
the capstone's 1M plan: 82 shards without room affinity, 11 with). The fix that
works is to reduce processes per room, and a Go/Rust **edge tier** — a dumb socket
terminator holding 250,000 connections per node, with every line of business logic
staying in Django behind the same Redis — delivers exactly that, while keeping
[Module 17](../../17-nextjs-realtime-client/)'s one-socket-many-rooms client
intact. **This is the only runtime decision in either course with an expiry date,
and the JVM twin never has to write it down.**

---

## 3. Fan-out backbone: Redis Streams for messages, Pub/Sub for the ephemeral path — **PROVISIONAL**

**Decision.** Cross-process message delivery runs on a custom Redis
Streams-backed channel layer with per-worker consumer groups and at-least-once
semantics. Typing, presence and cursor traffic run on a *second*, separate
`RedisPubSubChannelLayer`.

**Evidence.** [Module 07](../../07-scale-out-redis-channel-layer/) proved the
Pub/Sub channel layer loses messages silently — a `docker pause` lost ~15% with
zero errors surfaced anywhere. [Module 09](../../09-redis-streams-delivery/) re-ran
the identical test on Streams and lost **zero**, for +5 ms p50 and roughly 2× the
Redis CPU. Splitting the layers is Module 07's ADR: the Pub/Sub layer wins on every
benchmark (2.3× the fan-out knee, 11× fewer Redis commands, 2 ms lower p50) and has
**no backpressure at all** — one non-reading client grows a worker's heap at
4.1 MB/s with no bound, no counter and no log. At-most-once traffic gets the fast
layer; the message path gets the layer with a countable, alertable `capacity`.

**Rejected alternative.** Kafka. [Module 16](../../16-kafka-comparison/) is honest
about where Kafka wins and it wins here architecturally: the log is on disk, N
consumers reading recent offsets hit the same page-cache pages, and `sendfile`
serves them with no per-read CPU on a single thread — which is precisely the
resource that binds us. We chose Redis because Module 16's own scorecard puts Pulse
at **five of five** on the Redis column: we already run Redis for `seq`, presence,
buckets and tickets; we need a log *per room*, and a million keys is free where a
million partitions is impossible; our replay window is minutes by design; latency
matters more than days of durability; and we are a small team.

**Would change if.** Either of two checkable thresholds:
- **A second consumer appears** — search, analytics, moderation, ML. Module 16
  measured what that costs Redis and Kafka respectively, and the capstone's stretch
  task shows search arriving as the very next feature anyone requests.
- **Subscribed worker processes exceed ~24.** At W=24 a single shard sustains only
  163,000 outbound msg/s — six shards to carry what four carry today; the read
  amplification that makes Redis expensive is
  exactly what Kafka's page cache makes cheap.

The 1M plan crosses the second within one growth step. **This decision is firm at
our scale and wrong past it, and the boundary is a number, not a feeling.**

---

## 4. Delivery semantics: at-least-once, made observationally exactly-once

**Decision.** At-least-once everywhere, with duplicates absorbed by a
client-generated `client_id` under a `UNIQUE (room_id, client_id)` index. Per-room
`seq` is allocated and the stream entry appended in **one Lua script**, so a
sequence number exists if and only if the entry does.

**Evidence.** [Module 05](../../05-protocol-and-domain-design/)'s concurrency test
produces 7 duplicate rows from 64 concurrent retries without the unique index and
**0** with it. [Module 10](../../10-ordering-and-delivery-semantics/) found that
Module 09's design had quietly broken the gapless promise: at 64 concurrent senders
in one room, allocating `seq` and appending separately produced **412 arrival
inversions per 10,000 messages** — 4.1%, invisible at one sender per room. The Lua
script took it to 0 and dropped the send path from two round trips to one.

**Rejected alternative.** Two.
*True exactly-once:* unachievable across a system boundary, because the
acknowledgement and the side effect live in different systems and cannot be made
atomic. Kafka's EOS fixes none of Pulse's actual failure modes.
*Postgres-allocated sequence numbers:* correct, and it puts a row lock on
`chat_roomsequence` in front of every send. Module 10 measured **2,900 sends/s per
room** against Redis's **31,900**. An 11× throughput cost to move a counter.

**Would change if.** Never, within these system boundaries. This is the one
decision in the review with no realistic falsifying condition, because it is a
theorem rather than a preference — the only thing that could change it is the
boundary itself disappearing, and a browser will never be inside a Postgres
transaction.

---

## 5. Storage: sharded, time-partitioned PostgreSQL with Snowflake IDs

**Decision.** Messages live in Postgres, sharded by room across 4,096 logical
shards mapped onto physical databases by a Django DB router, time-partitioned by
month within each shard, with Snowflake IDs.

**Evidence.** [Module 12](../../12-postgres-message-store/) projected **74 TB/year**
at 10k msg/s, which is what forced the next two modules;
[Module 13](../../13-partitioning-replication-pooling/) brought that to **18.4 TB
live** with `DROP TABLE` retention, which is thousands of times faster than
`DELETE` and does not bloat. [Module 14](../../14-sharding-and-wide-column/)
benchmarked the same data on ScyllaDB: Scylla wins raw write throughput and
storage, and **loses decisively on the idempotency check**, which needs a
lightweight transaction (Paxos) where Postgres needs a unique index. That check is
load-bearing for decision #4, and decision #4 is load-bearing for the entire
delivery guarantee.

**Rejected alternative.** Cassandra/ScyllaDB. It is the right answer at a scale
where you have people who operate it, and Discord made exactly this move — *after*
outgrowing a design like this one. Wrong for us because it cannot do the outbox's
atomic dual-write (decision #6), it makes the idempotency check expensive, and it
requires every query designed before the first row is written. Module 14's honest
line: adopting it early buys a ceiling you do not need at the cost of flexibility
you do.

**Would change if.** Sustained writes exceed roughly 300k/s, *or* a
Cassandra-fluent team exists and wants to own it. Both are checkable; neither is
close.

---

## 6. The transactional outbox, dual-path

**Decision.** A send publishes to the Redis Stream *and* writes an outbox row in
the same Postgres transaction as the message. A Celery relay publishes only the
rows the stream never acknowledged, using `FOR UPDATE SKIP LOCKED`.

**Evidence.** Module 13 killed the process between persist and publish: without an
outbox, one message per crash is persisted-but-never-delivered. With an
outbox-*only* design, the send path's latency goes from 1.8 ms to **9.4 ms** and
per-room throughput from 31,904 to 11,208 sends/s — 5.2×, because you moved a Redis
round trip onto a Postgres commit. The dual path keeps the stream as the fast path
and costs **+1.9 ms** for one extra insert. Module 18's challenge then found the
relay's own failure mode: two relays running produce 2× `XADD` and **41 order
violations**, invisible in RTO/RPO because client dedup hides them — fixed by
letting Postgres arbitrate via `FOR UPDATE SKIP LOCKED`, after which two relays
scale 1.94×.

**Rejected alternative.** CDC (Debezium / logical decoding). Lower latency, and its
failure mode is the reason it is rejected: a stalled replication slot pins WAL and
fills the disk. Module 18's disk-full drill reproduced it — an `INACTIVE` slot
holding **4.2 GB of WAL**, RTO 38.4 s because Postgres does not fail fast when it
runs out of disk. An outbox backlog is a number you can `SELECT count(*)` from and
a task you can scale out. A stalled slot is a 3 a.m. page.

**Would change if.** We needed near-real-time change streams for several downstream
consumers *and* had the Connect-cluster operational maturity to run CDC safely — at
which point CDC feeds the same consumers Kafka would, and decision #3's condition
has already fired.

---

## 7. Capacity and topology: four pods, four workers each, **four** channel-layer shards

**Decision.** Pulse runs 4 pods × 4 Uvicorn+uvloop workers behind **4**
Sentinel-managed channel-layer shards, with `maxReplicas` fixed at 4 and a comment
next to it containing the arithmetic.

**Evidence.** Module 07 regressed the channel layer's cost against subscribed
worker processes at **55 µs + 46 µs × W**, and the model predicted the lab's
measured `group_send` rate to within 1.4%.
[Module 19](../../19-kubernetes-ha-and-multiregion/) turned it into a shard
ceiling. At W=16 with 4 shards that is **956,000 outbound msg/s**; the capstone's
530,400 msg/s burst is 55% of it, against
[Module 06](../../06-load-testing-harness/)'s rule of ≤65%. The measured
knee is **172,000 connections**, 4.5% below the arithmetic's 180,000, with Redis's
worst shard at 96% CPU and 73% of per-worker memory unused.

**Rejected alternative.** Two, and both are the obvious move.
*Three shards* — Module 18's stack, unchanged — puts the burst at **74%** of the
ceiling: inside the target, outside the operating rule, and the first acceptance
run proved what that costs (2,847 dropped messages, 61 sequence gaps).
*A fifth pod* — the reflex when a system is under pressure — **lowers** the ceiling
from 956,000 to 776,000, because it adds four subscribed processes and every one of
them costs 46 µs of Redis's single thread on every `group_send`. Module 07 found
this first (eight workers slower than four: 441,000 vs 521,000), Module 19 named it
("the third replica is the new eighth worker"), and it is the single most
counterintuitive property of this architecture.

**Would change if.** Sustained burst utilisation crosses 65% of the ceiling, which
happens at **~117,000 connections** on this topology. The response, in order: a
fifth shard (+25%, linear, three containers), then room affinity (3.3×, 3–4
engineer-weeks) or an edge tier. **It is never more pods.** If room affinity ever
ships, W per room falls from 16 to 4, the ceiling becomes 3,164,000, the *Python*
ceiling binds instead, and this decision is re-opened from the other side.

---

## 8. HA posture: quorum failover, capacity-aware readiness, graceful ASGI drain — **PROVISIONAL**

**Decision.** Redis Sentinel per channel-layer shard; Patroni/CloudNativePG + etcd
for Postgres behind HAProxy and PgBouncer; PodDisruptionBudgets and topology
spread; a two-phase SIGTERM drain that flips readiness *before* Uvicorn stops
accepting; readiness that reflects **capacity**, not just liveness.

**Evidence.** [Module 18](../../18-compose-ha-and-chaos/) ran eleven drills with a
load test running and the capstone ran eight of them at ten times the load: **RPO 0
on every drill**, worst RTO 13.2 s against a 15 s target. Three configuration
changes produced most of it: `socket_timeout: 2.0` on the channel layer (pause RTO
14.8 → 9.1 s, p99 8,940 → 2,180 ms — the `redis-py` default is *no timeout at
all*), `PATRONI_TTL` 30 → 15 (PG RTO 24.1 → 11.8 s), and moving the capacity signal
onto **readiness** rather than liveness (brownout RPO 4,102 → **0**). The graceful
drain turns a rolling deploy from 18.4 s / 2,841 lost into **0 s / 0 lost**, and it
took five independent decisions to get there — drop any one and it regresses.

**Rejected alternative.** Managed services (RDS/Aurora, managed Redis). Module 19
was explicit that managed is *less* work and self-managing "should be a decision
with a reason." **Our reason is pedagogical**, and that is not a reason in
production. Module 18's challenge priced our posture honestly: HA costs 8.4× the
money, +52% p99 and −8% knee, and the honest way to halve the bill is to *reduce
the ambition* (keep Redis HA, drop Patroni/etcd/HAProxy, promote Postgres by hand:
$1,180 → $390/month, PG RTO 11.8 s → ~5 minutes, reads unaffected) rather than keep
the diagram and delete the margin.

**Would change if.** For production: **reconsider immediately.** Managed is the
default unless cost at scale, a missing feature, or existing deep expertise
justifies self-management. One thing never gets cut: the graceful drain costs $0
and is the best availability spend in the entire course.

---

## 9. Presence and rate limiting: TTL state, viewport subscriptions, Lua token buckets

**Decision.** Presence is a TTL heartbeat (self-healing by construction), pushed
only for the users a client can currently see, aggregated by a diffing sweeper with
a reconnect grace period and a 5% blast-radius bound. Rate limits are token buckets
executed as Lua scripts.

**Evidence.** [Module 11](../../11-presence-and-rate-limiting/) measured a naive
presence design pushing chat p99 to **8.9 s** during a 10,000-user reconnect storm;
the viewport optimisation alone brought it to **214 ms** — worth more than
aggregation and debouncing combined. A non-atomic token bucket (read, compute,
write) allows a **41% overshoot** where the Lua version allows exactly the
configured rate. Module 18 found the sweeper's own failure: on Redis recovery it
mass-evicted 18,412 users and took p99 to 6,840 ms, fixed by a reconnect grace
period, two-tick confirmation and the 5% bound (412 ms).

**Rejected alternative.** Broadcasting presence to all room members (Module 11
measured 9.8M frames during the storm) and Redis keyspace notifications for
transitions (Pub/Sub, therefore at-most-once, therefore unreliable for exactly the
events you care about). For rate limiting: fixed and sliding windows, both of which
either allow a 2× burst at the boundary or cost far more state than 90 bytes.

**Would change if.** Mean room size dropped below **10** — measured monthly —
making broadcast presence cheap enough that the viewport machinery is not worth
maintaining. Or a "last seen" product feature requiring per-user precision, which
Module 11's challenge built at +17% presence writes.

---

## 10. Auth and abuse: single-use ticket, first-frame JWT, durable revocation

**Decision.** The handshake is authorised by a single-use 30-second Redis ticket
consumed with an atomic `GETDEL`, on a `maxmemory-policy allkeys-lru` instance
separate from the backbone. Identity comes from a verified JWT in the socket's
**first frame**, cross-checked against the ticket's subject. Revocation is
published on a durable Redis Stream with per-worker reconciliation every 10 s plus
a denylist check on connect. Delivery-time authorisation uses a per-worker
membership cache with a 10-second staleness budget.

**Evidence.** [Module 21](../../21-security-and-abuse-at-scale/) demonstrated CSWSH
stealing a live chat session and then blocked it with an explicit `OriginValidator`
— browsers do not apply the same-origin policy to WebSocket, and Channels does not
check `Origin` for you. The ticket-replay test returns 401. The Pub/Sub revocation
push was **proven lost** under a 3-second partition, which is why revocation is a
Stream: worst case 10.1 s, push still under 5 ms. The security layer costs p99
138 → 166 ms and the knee 150k → 128k out msg/s; restructuring delivery-time authz
around a cache invalidated by the revocation stream recovered the knee to 146k for
the same ≤10 s staleness budget. A red-team exercise went from time-to-first-compromise
23 minutes to **none in 3 hours**, and send-as-another-user was never achieved —
the ticket/JWT identity cross-check was the highest-value control built.

**Rejected alternative.** Session cookies via `AuthMiddlewareStack` (a CSWSH
surface, and it ties chat auth to Django sessions) and `?token=<JWT>` in the
handshake URL, which leaks the durable credential into access logs, browser
history, `Referer` headers and every error tracker. The ticket exists precisely so
that the thing in the URL is worthless thirty seconds later.

**Would change if.** Nothing on the fundamentals. Two implementation facts must
change before production and are release blockers in the readiness document: the
test JWT signer must become a real issuer, and the abuse detector's hand-tuned
heuristics need a trained model with a feedback loop from moderator actions.

---

## Summary

Ten decisions. **Seven are firm at our scale.** Three are labelled provisional, and
the labelling is the most valuable thing in this document:

| # | Decision | Why provisional | The number that flips it |
|---|---|---|---|
| **2** | Async Django/Channels for the socket edge | The runtime itself has a ceiling this architecture can reach | ~400,000 connections, where the required shard count becomes absurd (82) and an edge tier makes it 11 |
| **3** | Redis Streams over Kafka | Conditional on there being exactly one consumer and few subscribers | a second consumer, or W > ~24 subscribed worker processes |
| **8** | Self-managed Postgres and Redis HA | The reason is pedagogical, and that is not a production reason | reconsider immediately; managed is the default |

Two further notes an honest review should carry:

**The binding resource is not what you would guess, and not what the JVM twin's
is.** Pulse breaks at 172,000 connections on **one Redis thread at 96%**, with 73%
of its per-worker memory unused. The JVM twin's capstone breaks on **memory**, at
46,000 connections per node. Same architecture, same four SLOs, opposite walls —
because the JVM's unit of channel-layer subscription is an instance and ours is a
worker process. Every "just add a node" instinct inverts across that line, and
decision #7 is the one that encodes it.

**The cheapest available improvement in the whole system is unavailable.** Six
lines of nginx configuration (`hash $room consistent`) would take the fan-out
ceiling from 956,000 to 3,164,000 outbound msg/s. It is blocked by Module 17's
decision that a user gets one socket across all rooms and all tabs — a client-side
choice, made for good reasons, that priced the best server-side lever out of
existence. Neither module could have seen it alone, and it is the clearest argument
in this document for reviewing the system rather than its parts.

A review that defended all ten decisions to the death would be less trustworthy,
not more. The value here is the three concessions, the two notes above, and the
fact that every one of the seven firm decisions carries a threshold someone could
go and measure tomorrow. **That is what "we made a decision" means, as opposed to
"we defaulted into one."**
