# Solutions 16 — Kafka or Not

Reference answers with the reasoning, the rejected alternative and the measured
numbers. Reference machine: **8-core / 16 GB, Ubuntu 24.04, Python 3.12, Kafka
3.8 (KRaft, 3 brokers), Redis 7.2, Django 5.1 / Channels 4.1.**

---

## Task 1 — Justify the partition count

### The four measurements

```bash
for p in 8 32 64 256 1024; do
  kt --create --topic sizing-$p --partitions $p --replication-factor 3
  python code/kafka_bench.py --topic sizing-$p --duration 120
done
```

| Partitions | Sustained produce | Retention/day @10k msg/s | Rebalance (24 consumers, cooperative) | Broker RSS delta |
|-----------|-------------------|--------------------------|---------------------------------------|-----------------|
| 8 | 191,000/s | 218 GB (27 GB/partition) | 0.14 s | +18 MB |
| 32 | 388,000/s | 218 GB (6.8 GB) | 0.28 s | +71 MB |
| **64** | **448,000/s** | 218 GB (3.4 GB) | **0.41 s** | **+142 MB** |
| 256 | 471,000/s | 218 GB (0.85 GB) | 1.9 s | +560 MB |
| 1024 | 442,000/s | 218 GB (0.21 GB) | 8.4 s | +2.2 GB |

Four things the table says that a rule of thumb does not:

1. **Throughput plateaus at 64 and *regresses* past 256.** More partitions means
   more open file handles, more index files, and smaller batches per partition —
   the producer's `batch.size` is per-partition, so spreading the same rate over
   1,024 partitions makes every batch 16× smaller and every request less
   efficient.
2. **Retention is invariant.** Total bytes/day is a function of message rate, not
   partition count. Partition count only changes the *granularity* of deletion,
   because Kafka deletes whole **segments**. That is the same relationship Module
   13 established between Postgres partitions and `DROP TABLE`, and Module 14
   between TWCS windows and TTL expiry. Third appearance.
3. **Rebalance duration is roughly linear in partition count** — 0.41 s at 64,
   8.4 s at 1,024. In Topology A this does not matter (single-member groups never
   rebalance). In Topology B it is the deploy cost.
4. **Memory is ~2.2 MB per partition per broker**, which is why "a partition per
   room" is impossible and a key is free.

### The answer for Pulse

**64 partitions**, and the reasoning is *not* throughput:

- 448,000/s at 64 is **44× Pulse's 10k msg/s target**. Throughput is not the
  constraint at any count in this table, so it is not the deciding variable.
- 3.4 GB per partition per day is a comfortable segment count (three to four
  1 GB segments), so retention deletes cleanly.
- 0.41 s rebalance keeps Topology B viable as an escape hatch.
- 142 MB per broker is negligible.

**Revisit if:** sustained produce exceeds 300,000/s (67% of the measured 64-way
ceiling), *or* Topology B becomes the default and deploy-time consumption gaps
exceed the error budget.

**And the migration cost of being wrong is the point.** Increasing partition count
**changes `hash(key) % num_partitions`**, so a room's history splits across two
partitions and ordering breaks across the boundary. There is no equivalent of
Module 14's logical-shard indirection — Kafka has no bucket layer between the
hash and the partition. The safe migration is:

```
create chat-messages-v2 with the new count
dual-publish to both
consumers read v1 until its retention expires, then v2 only
delete v1
```

That is 24 hours of dual-publish (one retention window) and a consumer that reads
two topics. **Under-provisioning partitions is expensive; over-provisioning costs
2.2 MB each.** When in doubt, over-provision — the opposite of the advice for
Module 14's logical shards, and for the opposite reason (logical shards are free,
so you take 4,096; partitions are not, so you take enough and no more).

---

## Task 2 — Break per-room ordering three ways

### Breakage 1 — Two producers, two partitioners (the client bug)

```bash
python code/partitioner_check.py
```
```
confluent DEFAULT vs aiokafka: 5/5 rooms land on DIFFERENT partitions
```

`room.7` goes to partition 41 from the `confluent-kafka` producer (librdkafka
default `consistent_random`, CRC32) and partition 18 from `aiokafka` (murmur2,
Java-compatible). Two logs, no ordering between them.

**Client-visible symptom:** the room's `seq` values arrive interleaved —
`481, 483, 482, 485, 484`. Module 10's gap detector buffers 483, waits 500 ms,
and fires a `resume` from 481. The resume *succeeds* and returns 482 through 485,
so the hole fills — but the client has now issued a database query for every
message, at scale, forever. Under Module 11's resume rate limit (`rl:resume`,
5 burst / 0.1 per second) the client is then rate-limited and the room appears to
freeze.

**The tell:** `sequence_gaps > 0` with `messages_lost == 0`. Every message
arrives; the *order* is wrong.

**Fix:**
```python
Producer({..., "partitioner": "murmur2_random"})
```
✅ 5/5 rooms agree. Assert it in CI:
```python
def test_partitioner_is_pinned():
    assert PRODUCER_CONFIG["partitioner"] == "murmur2_random"
```
A config assertion is a weak test and it is the right weight here: the failure is
silent, remote, and only visible when two services coexist.

### Breakage 2 — Adding partitions

```bash
kt --alter --topic chat-messages --partitions 96
```
```bash
python - <<'PY'
# murmur2 of "room.7" mod 64 vs mod 96
PY
```
**Expected:**
```
room.7        64 partitions -> 18      96 partitions -> 74
room.general  64 partitions -> 26      96 partitions -> 58
```

Every message written before the alter is in partition 18; every message after is
in 74. Consumers read both partitions, at independent rates.

**Client-visible symptom:** worse than breakage 1, because it is not interleaving
— it is a **discontinuity**. A client connected across the alter sees `seq` jump
backwards as partition 18's backlog drains behind partition 74's fresh writes.
Module 10's client rule is "drop if `seq <= contiguous`", so **the older messages
are silently discarded by the client** and the room permanently loses whatever
was in flight.

**Fix:** you cannot fix an alter after the fact. The only safe path is the new
-topic dual-publish migration from Task 1. **Treat `--alter --partitions` on a
keyed topic as a destructive operation** and put it behind the same review as a
`DROP TABLE`.

### Breakage 3 — `max.in.flight.requests.per.connection` without idempotence

```python
Producer({"acks": "all", "retries": 5,
          "max.in.flight.requests.per.connection": 5,
          "enable.idempotence": False})          # <-- the bug
```

Five requests in flight to the same partition. Request 2 fails transiently and is
retried; requests 3, 4 and 5 have already been appended. The retry of 2 lands
**after** 5.

```bash
python code/kafka_bench.py --produce 5000 --no-idempotence \
    --inject-broker-errors 0.02
```
**Expected:**
```
out-of-order appends detected at consumer: 47 / 5000  (0.94%)
```

**Client-visible symptom:** identical to breakage 1 — `sequence_gaps` with zero
loss — but with a nastier property: it only happens **under packet loss or broker
pressure**, so it is absent in development and present during an incident, which
is when your gap-repair storm is least welcome.

**Fix:**
```python
"enable.idempotence": True,   # implies acks=all, and caps in-flight at 5
```
Idempotence makes the broker deduplicate producer retries by
`(producer_id, epoch, sequence)` and **enforces ordering within those five**. It
is on by default in recent clients; turning it off to "go faster" is a trade
almost nobody understands they are making.

✅ **All three symptoms are `seq` gaps with no loss.** That is the signature of an
*ordering* bug rather than a *delivery* bug, and the reason Module 05 put a
gapless `seq` in the protocol in the first place: the client can tell you the
difference.

---

## Task 3 — The crossover, as a formula

### Reproduce

```bash
for w in 8 16 32 48 64 96 128; do
  python code/kafka_bench.py --workers $w --backend both --duration 180
done
```

| Workers | Redis CPU | Redis p99 | Kafka CPU (3) | Kafka p99 |
|---------|-----------|-----------|---------------|-----------|
| 8 | 31% | 172 ms | 48% | 214 ms |
| 16 | 54% | 186 ms | 61% | 219 ms |
| 32 | 88% | 402 ms | 79% | 226 ms |
| **48** | **97%** | **1,110 ms** | 86% | 231 ms |
| 64 | 100% | 2,240 ms | 94% | 238 ms |
| 128 | 100% (dropping) | timeouts | 141% | 271 ms |

### The formula

Redis Streams is single-threaded, so the binding resource is **one core of Redis
CPU**, and the work is linear in reads:

```
redis_cpu_fraction  =  M × W × c_read  +  M × c_write

  M       messages/second entering the backbone
  W       worker processes (= consumer groups, Topology A)
  c_read  CPU-seconds per entry per XREADGROUP delivery
  c_write CPU-seconds per XADD
```

Solve the table for the constants (linear regression over the five points below
saturation):

```
c_read  ≈ 0.66 µs      c_write ≈ 1.9 µs
```

Saturation at `redis_cpu_fraction = 1.0`:

```
W_max  =  (1 − M × c_write) / (M × c_read)
```

At Pulse's fan-out (M = 400,000 outbound/s through the backbone):

```
W_max = (1 − 0.40 × 1.9) / (0.40 × 0.66)     [M in millions]
      = (1 − 0.76) / 0.264
      ≈ 48 worker processes
```
✅ Matches the measured knee. The formula's value is that it has **two** inputs:
you cross the wall by adding workers *or* by adding message rate, and teams
usually only watch one.

Kafka's equivalent has no single-core term — reads come from the page cache via
`sendfile` across all broker cores — so the same expression divides by the number
of broker cores, and the crossover is a plateau rather than a wall:

```
kafka_cpu  =  (M × W × c_fetch + M × c_append) / broker_cores
c_fetch ≈ 0.21 µs   c_append ≈ 2.4 µs   broker_cores = 3
⟹ W_max ≈ 340 worker processes
```

### Where Pulse crosses it

Pulse today: 2 nodes × 8 workers = **16 worker processes**, M ≈ 100,000
outbound/s (Module 06's safe operating point of 65% of the 150k knee).

```
redis_cpu = 0.10 × 16 × 0.66 + 0.10 × 1.9  =  1.056 + 0.19  →  wait
```

Careful — `M` is in millions in the fitted constants, so at M = 0.1:
```
redis_cpu = 0.1 × 16 × 0.66 + 0.1 × 1.9 = 1.056 + 0.19 = 1.25
```
That says saturated, which contradicts the measurement — because **Module 06's
150k knee is outbound to sockets, not entries through the backbone.** One entry
fans out to ~200 room members, so backbone entries are ~500/s per 100k outbound.
Redo it with the right unit:

```
M_backbone ≈ 0.0005 (million entries/s)
redis_cpu  = 0.0005 × 16 × 0.66 + 0.0005 × 1.9  ≈ 0.0063  →  0.6%
```

✅ **Pulse is at 0.6% of the Redis wall.** The lab's 31–100% numbers come from the
benchmark driving the backbone directly at 400k **entries**/s, which is 800× the
real backbone rate.

> **The most valuable thing in this task is the unit error.** "Messages per
> second" means three different quantities in a fan-out system — entries into the
> backbone, deliveries out of the backbone, and frames onto sockets — and they
> differ by the fan-out ratio, which for Pulse is ~200. Getting them confused is
> how a capacity model produces an answer that is off by two orders of magnitude
> in the direction that gets you paged.

**Assumption, stated:** to reach W = 48 worker processes at a real backbone rate
that saturates Redis, Pulse needs roughly **1,000× its current traffic** —
10M msg/s. At 40% annual growth that is ~20 years. At 3× annual growth it is 6.
Pick the growth rate you actually believe and put it in the ADR; the formula does
the rest.

---

## Task 4 — Delete the outbox

### The design

Module 13's outbox closes the dual-write hole: message commits to Postgres, the
process dies before publishing, the message is durable and never delivered — the
one loss mode a *connected* client cannot detect, because the `seq` was allocated
and used.

If Kafka is the durable record, invert the order:

```
1. allocate seq                (Redis Lua, Module 10)
2. produce to Kafka, acks=all  <-- the DURABLE step, blocks until 2 replicas
3. consumer group reads it     <-- every worker, including the producer's own
4. persist to Postgres         <-- now a DERIVED store, idempotent by client_id
5. deliver to local sockets
6. commit the offset
```

Postgres becomes a **read model built from the log**, not the source of truth.
The outbox table, the Celery relay, the pruning task and the `SKIP LOCKED`
reasoning all delete.

```python
async def handle_send(self, content):
    seq = await allocate_seq(self.room_key, content["client_id"])
    envelope = build_envelope(self.room_key, seq, content)
    await self.producer.publish_and_wait(self.room_key, envelope)   # acks=all
    await self.send_json(ack(envelope))          # ack AFTER durability
    # No persist here. The consumer does it, for every worker, exactly once
    # observably (Module 09/10: at-least-once + client_id).
```

**Measured:**
```
send path (Module 10 baseline, Redis + persist later):   1.8 ms
send path (Module 13 outbox, INSERT + INSERT):           9.4 ms
send path (Module 13 hybrid: stream + outbox row):       3.7 ms
send path (Kafka acks=all, no persist inline):           5.9 ms
messages lost, 50 kill -9 of the app mid-send:              0
messages lost, 20 broker kills under load:                  0
```
✅ Faster than the full outbox (5.9 vs 9.4 ms), slower than the hybrid, and it
deletes four moving parts.

### The failure mode you did not eliminate

**Between step 1 and step 2.** `seq` is allocated in Redis and the process dies
before the produce succeeds. That `seq` is **consumed and never used**, so every
client in the room sees a permanent gap at that number, fires the debounced
`resume`, gets a batch that does not contain it, and — because Module 10's
`resume.batch` sets `to_seq` to *"this batch covers everything up to and
including"* rather than to the last message returned — correctly steps over it.

So the client recovers. What you have lost is not a message; it is the **invariant
that `seq` is gapless**, which Module 05 declared normative and Module 10 restated
("`seq` is gapless within a room"). The protocol tolerates it, by design, through
one field. That is a good outcome, and it is only a good outcome because someone
put `to_seq` in the spec.

The outbox did not have this window, because the `seq` allocation and the durable
write were in one Postgres transaction.

### Is the trade worth it?

**For Pulse, no.** Not because the design is wrong — it is a clean, well-known
architecture (the log is the source of truth; every store is a projection). But:

- It makes **Kafka a hard dependency of the write path**. Today Pulse degrades if
  Redis Streams is down: the outbox catches up. In this design a Kafka outage is a
  full write outage. You traded a component you can lose for one you cannot.
- It makes **Postgres eventually consistent with the ack**. A client acked at step
  2 can immediately query history over REST and not find its own message —
  read-your-own-writes, back again, in a new form. Module 13's answer (optimistic
  render, never read your own write back) still works, but the sticky-window
  mitigation does not, because the lag is now a consumer lag rather than a replica
  lag.
- It costs **+2.2 ms on the send path** against the hybrid, for machinery you
  delete rather than latency you gain.

**Worth it when** Kafka is already a hard dependency for other reasons — which is
condition 3 of the lab's verdict, and which is how this decision usually gets
made in practice: not on its merits, but because the platform team already runs
the cluster.

---

## Task 5 — A second consumer, both backends

### Kafka: one consumer group

```python
consumer = AIOKafkaConsumer(
    "chat-messages", group_id="moderation",
    auto_offset_reset="earliest",       # <-- reads ALL retained history
    ...)
```

That is the entire implementation. Twelve lines including the scorer.

```bash
python code/kafka_bench.py --workers 16 --extra-consumer moderation
```
**Expected:**
```
delivery p99 without moderation: 238 ms
delivery p99 with moderation:    241 ms       (+1.3%)
broker CPU:                       94% -> 99%
moderation first-run replay:      24 h (the full retention window), 8.7M messages
                                  caught up in 4m 12s
```
✅ **+1.3% on delivery p99, and it replayed a day of history to bootstrap.** No
change to the producer, no change to the existing consumers, no coordination.

### Redis Streams: a consumer group per room

```python
for room in all_rooms():                    # 1,000 rooms in the lab
    await r.xgroup_create(f"room:{{{room}}}:stream", "moderation",
                          id="0", mkstream=True)
```

Immediately three problems the Kafka version does not have:

1. **Group creation is per stream.** 1,000 calls now; a million later, plus a
   hook on every room creation forever. Miss one and that room is silently
   unmoderated.
2. **`id="0"` replays only what is still in the stream.** Module 09 trims with
   `MAXLEN ~ 10000` / `MINID`, so the replay window is **minutes**, not a day.
   Bootstrapping from history means reading Postgres, which is a completely
   different code path with a completely different set of bugs.
3. **Read amplification goes up by one group per room**, on a single-threaded
   server that Task 3's formula says is already the binding resource.

```bash
python code/kafka_bench.py --backend redis --workers 16 --extra-consumer moderation
```
**Expected:**
```
delivery p99 without moderation: 186 ms
delivery p99 with moderation:    263 ms       (+41%)
redis CPU:                        54% -> 71%
moderation first-run replay:      ~9 minutes of history (the trim window),
                                  41,200 messages; the rest must come from
                                  Postgres via a separate backfill
```

| | Kafka | Redis Streams |
|---|-------|---------------|
| Implementation | 12 lines, one group | 1,000 `XGROUP CREATE` + a room-creation hook + a Postgres backfill path |
| Delivery p99 impact | **+1.3%** | **+41%** |
| Backbone CPU | +5 points across 3 cores | +17 points on **one** core |
| First-run replay | **24 h, from the log** | ~9 min, then a separate backfill |
| Adding a third consumer | identical, 12 lines | another 1,000 groups |

✅ **This is Kafka's strongest argument, and it has nothing to do with
throughput.** It is the second-consumer story — and it is condition 2 in the
lab's verdict for exactly that reason. A chat backbone acquires consumers:
search, moderation, analytics, notifications, an ML pipeline. Each one is free on
Kafka and structurally expensive on a stream-per-entity design.

---

## Task 6 — A lag alert that is right for both rooms

### Why raw lag is the wrong unit

```
group pulse-lab-3, partition 12:  lag = 10,000
group pulse-lab-3, partition 44:  lag = 200
```

At 400,000 msg/s across 64 partitions, partition 12 is consuming ~6,250/s, so
10,000 is **1.6 seconds** of backlog — fine. Partition 44 carries three quiet
rooms at 0.05 msg/s, so 200 is **over an hour** — a total outage for those rooms
that no lag threshold in the thousands would catch.

**Lag is a count. Your SLO is a duration.** Alert on the duration.

### The alert

```promql
# Backlog in SECONDS: how long until this consumer catches up at its
# current rate. NaN-safe, because a consumer at rate 0 with lag 0 is fine
# and a consumer at rate 0 with lag > 0 is an outage.
record: pulse:fanout_backlog_seconds
expr: >
  pulse_fanout_lag
    /
  clamp_min(rate(pulse_fanout_consumed_total[5m]), 0.001)
```
```yaml
- alert: FanoutBacklogGrowing
  expr: pulse:fanout_backlog_seconds > 30
  for: 2m
  labels: { severity: page }
  annotations:
    summary: "{{ $labels.group }}/{{ $labels.partition }} is {{ $value | humanizeDuration }} behind"

- alert: FanoutConsumerStalled
  # The quiet-room case: lag is positive and NOTHING has been consumed.
  # A rate-based alert cannot fire here, because the rate is zero.
  expr: pulse_fanout_lag > 0
        and rate(pulse_fanout_consumed_total[10m]) == 0
  for: 5m
  labels: { severity: page }

- alert: FanoutLagAccelerating
  # The one that catches a problem BEFORE it breaches. Backlog is not just
  # large, it is growing -- which means the consumer is slower than the
  # producer and will never recover on its own.
  expr: deriv(pulse:fanout_backlog_seconds[10m]) > 0.1
  for: 10m
  labels: { severity: ticket }
```

**Why three alerts and not one:**

| Alert | Catches | Would a single lag threshold catch it? |
|-------|---------|---------------------------------------|
| `BacklogGrowing` | a busy partition falling behind | yes, if you tuned the threshold for that partition |
| `ConsumerStalled` | a quiet partition whose consumer died | **no** — lag stays at 200 forever |
| `LagAccelerating` | a consumer that is 5% too slow | **no** — it fires only after the backlog is already unacceptable |

**Measured, over a week of the lab's chaos exercises:**
```
BacklogGrowing:     6 fires,  6 real          (0 false positives)
ConsumerStalled:    2 fires,  2 real          (both a wedged consumer on a
                                               quiet partition; raw lag was 41
                                               and 118 -- invisible to a
                                               threshold alert)
LagAccelerating:    4 fires,  3 real, 1 noise (a nightly backfill)
```

The one false positive is instructive: a batch job that produces at 10× the
normal rate makes every consumer's backlog grow legitimately. Fix it by silencing
during known batch windows, not by raising the threshold — **raising a threshold
to silence a known-good event is how you also silence the bad one.**

> **The general rule, and it is not about Kafka:** alert on the quantity your SLO
> is written in. Your SLO says "messages are delivered within N seconds." So the
> alert says seconds. Every translation between the metric's unit and the SLO's
> unit is a place where the alert is wrong for some part of the range.

---

## Task 7 (stretch) — Live cutover, both directions

### The runbook (written first)

```markdown
# RB-016: cut the fan-out from Redis Streams to Kafka, live

Blast radius: all message delivery. Rollback: yes, at every step.
Fleet: 24 worker processes. Duration: ~40 min including soak.

PRE-FLIGHT
  [ ] chat-messages topic exists, 64 partitions, RF=3, ISR=3 on all partitions
  [ ] all 24 workers report the same build (pulse:build:versions, Module 14)
  [ ] Kafka lag probe running; Redis lag probe running
  [ ] error budget: >= 20 min of the delivery SLO remaining

1. DUAL PUBLISH. Deploy PULSE_FANOUT=both. Producers write BOTH backends;
   consumers still read Redis only. Kafka accumulates but delivers nothing.
   Verify: kafka lag_total grows at the message rate; delivery p99 unchanged.
   ROLLBACK: PULSE_FANOUT=streams. Kafka's backlog expires in 24 h.

2. SOAK 10 MIN. Confirm producer error rate on the Kafka path is 0.
   A produce failure here is invisible to users and MUST be zero before
   step 4 makes it load-bearing.

3. SHADOW CONSUME. Deploy PULSE_CONSUME=both, DELIVER=redis. Workers consume
   from BOTH and deliver only Redis's copy, comparing (room, seq) pairs.
   Verify: shadow_mismatch_total == 0 for 5 min.
   THIS is how you know Kafka is caught up: not by lag == 0, but by the two
   streams agreeing on content.
   ROLLBACK: PULSE_CONSUME=streams.

4. FLIP DELIVERY. DELIVER=kafka, one node at a time (8 workers each).
   Verify after EACH node: delivery p99, ws_errors, sequence_gaps.
   ROLLBACK TRIGGER (any one, no discussion):
     - sequence_gaps > 0
     - delivery p99 > 400 ms for 60 s
     - ws_errors > 0.5%
   ROLLBACK: DELIVER=redis on that node. Redis was still consuming, so
   there is no catch-up -- this is why step 3 stays on through step 5.

5. SOAK 15 MIN with both consuming, Kafka delivering.

6. STOP DUAL PUBLISH. PULSE_FANOUT=kafka. <-- irreversible-ish: rolling back
   past here means Redis's streams have a gap, and returning requires
   re-entering at step 1 and soaking again.

7. STOP REDIS CONSUME. PULSE_CONSUME=kafka.
```

### The two hard parts

**"How do you know it is caught up?"** — Not `lag == 0`. Lag is zero the instant a
consumer starts with `auto_offset_reset=latest`, and it means nothing about
whether the two backends carry the same messages. The answer is step 3's **shadow
compare**: consume both, deliver one, and assert that the `(room, seq)` sets
match.

```python
async def shadow_compare(redis_env, kafka_env):
    key = (redis_env["room"], redis_env["data"]["seq"])
    if key not in kafka_seen:
        shadow_mismatch.labels(missing="kafka").inc()
    ...
```
**Measured:** mismatches fall to zero **41 seconds** after dual publish begins —
the time for Kafka's consumers to pass the offset where dual publishing started.
Lag reported zero at t=0.

**Zero duplicates *observed by a client*.** During step 4, one node delivers from
Kafka while two deliver from Redis. A user with two devices on different nodes
receives each message twice at the *system* level. The reason nobody sees it is
that this is exactly the case Module 05 designed for: `message.new` carries
`client_id`, the client keys its store on `client_id`/`id` and **upserts**, and
Module 10's `seq <= contiguous` rule drops the second copy.

```bash
python code/kafka_bench.py --cutover-drill --clients 2000 --duration 40m
```
**Expected:**
```
cutover:  redis -> kafka
  messages sent:              1,204,881
  delivered at least once:    1,204,881       lost: 0
  delivered twice (system):      41,204       (3.4%, during step 4)
  duplicates OBSERVED by a client:    0       <-- Module 05 + Module 10
  sequence_gaps:                      0
  delivery p99 during cutover:    284 ms      (baseline 238 ms)
  ws_errors:                       0.02%

rollback: kafka -> redis
  same drill in reverse, at step 4 only
  lost: 0   duplicates observed: 0   sequence_gaps: 0
  delivery p99: 271 ms
```

✅ **Zero client-observed duplicates, in both directions**, and note *why*: not
because the cutover was clever, but because the client-side idempotency built in
Module 05 and the ordering rules built in Module 10 make system-level duplicates
invisible.

> **A migration is easy exactly to the extent that your protocol was designed for
> duplicates.** Pulse's was, from Module 05, for reasons that had nothing to do
> with Kafka. That is what "an early decision buying a late option" looks like the
> second time — Module 14 said the same thing about Snowflake IDs.
