# Pulse — Architecture Review

**Reviewer audience:** a skeptical senior engineer who will ask "why not X?" for
every decision. Each decision below carries its evidence, the alternative it beat,
and the condition under which the alternative would win.

**Target:** 100,000 concurrent connections, 1,000 rooms (avg 100 members), SLOs:
99.9% delivery under 500ms, 99.99% delivery success, 99.9% connection success,
<0.01% rooms with a permanent gap.

---

## 1. Transport: WebSocket + STOMP, SSE fallback

**Decision.** Bidirectional traffic over WebSocket with the STOMP subprotocol;
SSE-down + POST-up documented as a fallback for hostile networks.

**Evidence.** Module 03 measured bytes-on-the-wire: WebSocket 610 B/msg vs polling
6,843 B/msg vs SSE 921 B/msg. Pulse's upstream chatter (typing, receipts,
per-message acks) makes the 6-byte upstream WebSocket frame decisive — an SSE
design would need a ~500 B POST per upstream event.

**Rejected alternative.** SSE + POST. It gets free reconnection and a
standardized resume cursor (`Last-Event-ID`), and works through every proxy. We
rejected it on upstream cost, but Module 03's own analysis concedes that a
3-second typing debounce plus batched acks would collapse that cost — so this is
the *weakest* of our firm decisions.

**Would change if.** Upstream traffic dropped to chat sends only, or we had to
run behind customer proxies that strip `Upgrade`. Then SSE becomes primary.

---

## 2. Runtime: Spring MVC + Java 21 virtual threads

**Decision.** The connection layer is Spring MVC + STOMP on virtual threads.

**Evidence.** Module 15 head-to-head at scale: virtual threads hold 100k
connections at 71 KB/conn (tuned) vs WebFlux's 59 KB — a 1.2x gap, not the 2.65x
the untuned number implied. p50 is 3ms better on virtual threads; debugging
measured 2.6x slower on WebFlux.

**Rejected alternative.** WebFlux. Wins density and backpressure ergonomics, but
Module 15's challenge showed the density gap is mostly untuned buffers, and
WebFlux has no STOMP (Module 04's challenge: ~300 lines of hand-rolled protocol).
The *hybrid* (MVC connections + reactive fan-out consumer) beat both and is our
fallback if the fan-out path needs backpressure we can't get otherwise.

**Would change if.** Connection density becomes binding — Module 15's crossover
surface puts that above ~85k conn/node. We run 25k/node. At 3x growth we'd
re-measure, and even then adding nodes beats a rewrite.

---

## 3. Fan-out backbone: Redis Streams, per-node consumer groups

**Decision.** Cross-node delivery over Redis Streams, one consumer group per node,
at-least-once.

**Evidence.** Module 09 re-ran Module 07's loss test and lost 0/200 (vs 29/200 on
Pub/Sub). Latency cost +4ms p50 over Pub/Sub. Module 07: Pub/Sub silently lost
messages with zero errors surfaced.

**Rejected alternative.** Kafka. Module 16 measured Kafka flat to 16+ consuming
nodes where Redis saturates at ~9, with zero loss on a broker kill and free
replay. We chose Redis because we already run it (presence, rate limits, unread,
dedup) and run only 4 nodes. **This is a firm decision at our scale and a wrong
one past it.**

**Would change if — and this is the sharpest condition in the review.** Any of:
node count > 8 (Module 09's saturation point); a second consumer appears (search,
analytics, moderation — Module 16 measured the second consumer costing Redis 858%
of chat p99 vs Kafka's 7%); or replay beyond minutes is needed. The first two are
plausible within a year.

---

## 4. Delivery semantics: at-least-once + idempotent processing

**Decision.** At-least-once delivery everywhere, made observationally exactly-once
by a client-generated `clientId` and a unique index.

**Evidence.** Module 05's concurrency test creates 7 duplicate rows from 64
concurrent retries *without* the unique index and 0 *with* it. Module 09 and 13
proved the duplicate from redelivery and relay-crash is absorbed with 0 duplicate
rows.

**Rejected alternative.** Trying for true exactly-once. Module 09, 16 and the
outbox all demonstrated it's unachievable across system boundaries (WebSocket +
Postgres aren't in any broker's transaction). Kafka EOS (Module 16) fixes none of
Pulse's actual failure modes.

**Would change if.** Never, within these system boundaries — this is the one
decision with no realistic falsifying condition, because it's a theorem, not a
preference.

---

## 5. Storage: sharded, partitioned PostgreSQL

**Decision.** Messages in Postgres, sharded by room (4096 logical shards),
time-partitioned within each shard, Snowflake IDs.

**Evidence.** Module 14 benchmarked Postgres vs ScyllaDB: Scylla wins write
throughput and storage but loses p99.9 (compaction) and loses **26x on the
idempotency check** (LWT Paxos) — and that check is load-bearing for decision #4.
Module 13: `DROP TABLE` retention is 4,500x faster than `DELETE`.

**Rejected alternative.** ScyllaDB/Cassandra. The right answer at a scale with a
dedicated team; wrong for us because it can't do the outbox's atomic dual-write
(decision #6), makes idempotency 26x more expensive, and requires every query
designed in advance.

**Would change if.** Write rate exceeds ~300k/s sustained, or a Cassandra-fluent
team exists. Discord made exactly this move — after outgrowing this design.

---

## 6. The transactional outbox

**Decision.** Messages and their fan-out events are written in one Postgres
transaction; a relay publishes with `FOR UPDATE SKIP LOCKED`.

**Evidence.** Module 13 killed the process between persist and publish: without the
outbox, 1 message persisted-but-never-delivered per crash; with it, 0. Cost: +52ms
p50 fan-out, but −7ms send-path latency.

**Rejected alternative.** CDC (Debezium/logical decoding). Lower latency, but
Module 13's table: a stalled replication slot pins WAL and fills the disk — the
most common way people take down a Postgres they use CDC on. The outbox's failure
mode is a visible backlog gauge.

**Would change if.** We needed near-real-time change streams for many downstream
consumers *and* had the Connect-cluster ops maturity to run CDC safely. At that
point CDC feeds the same consumers Kafka would (see #3's condition).

---

## 7. HA: quorum failover (Sentinel/Patroni), tested by chaos

**Decision.** Redis Sentinel/Cluster, Patroni+etcd+HAProxy for Postgres, PDBs,
graceful drain. Every failover path proven by a chaos drill under load.

**Evidence.** Module 18/22: RTO<12.4s and RPO 0 on every drill *under 100k load*.
Fencing proven twice by demonstration (a returning primary demoted to replica).

**Rejected alternative.** Managed services (RDS Multi-AZ, ElastiCache). Module 19
was explicit: managed is *less* work and self-managed "should be a decision with a
reason." **Our reason is pedagogical.** In production, managed is the default.

**Would change if.** For production: reconsider immediately unless cost-at-scale
or a specific missing feature justifies self-management. This decision is the most
provisional in the review.

---

## 8. Presence: TTL state + viewport subscriptions

**Decision.** Presence is TTL-based (self-healing), pushed only for the users a
client can see, aggregated by a diffing sweeper.

**Evidence.** Module 11: naive presence pushed chat p99 to 8.9s during a 10k-user
reconnect storm; the viewport optimization alone brought it to 214ms — worth more
than aggregation and debouncing combined.

**Rejected alternative.** Broadcast presence to all room members; keyspace-
notification transitions. Module 11 measured the first at 9.8M frames; the second
is at-most-once (Pub/Sub) and unreliable for transitions.

**Would change if.** Rooms became small enough (avg < 10) that broadcast was
cheap, or a "last seen" feature required per-user precision (Module 11's challenge
built it at +17% writes).

---

## 9. Auth: JWT + single-use ticket, in-band re-auth

**Decision.** Handshake authorized by a single-use 30s Redis ticket; identity by a
verified JWT in the CONNECT frame with an identity cross-check; in-band re-auth
avoids reconnect; revocation is immediate cluster-wide.

**Evidence.** Module 21 demonstrated CSWSH stealing chat, then blocked it;
demonstrated the ticket replay returning 401; measured immediate revocation at
<5ms with a 0.09ms per-check cost on re-auth. The challenge proved and closed the
Pub/Sub revocation gap under partition with a reconciliation loop.

**Rejected alternative.** JWT-in-query-string (leaks to logs) or cookie (CSWSH
surface). The ticket keeps credentials out of URLs; the CONNECT-frame JWT keeps
them out of the handshake URL entirely.

**Would change if.** Never on the fundamentals — but the ticket store must move
from in-process to Redis for production (named in the readiness doc), and a real
auth issuer replaces the test signer (release-blocker).

---

## Summary

Nine decisions. **Seven are firm at our scale.** Two are honestly provisional:

- **#3 (Redis over Kafka)** flips the moment node count exceeds 8 or a second
  consumer appears — both plausible within a year.
- **#7 (self-managed Postgres HA)** is pedagogical; production should default to
  managed.

A review that defended all nine to the death would be less trustworthy, not more.
The value of this document is the two concessions and the sharp conditions on the
other seven — that is what "we made a decision" means, as opposed to "we defaulted
into one."
