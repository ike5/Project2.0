# Lab 16 — Run the Fan-Out on Kafka, Then Compare Honestly

**You'll:** stand up Kafka in KRaft mode, catch Python's two Kafka clients
partitioning the same room differently, run both fan-out topologies, measure them
against Redis Streams on latency, throughput, lag and resource cost, sweep the
worker count until Redis saturates and Kafka does not, trigger rebalances and
then eliminate them, and kill brokers until writes are correctly refused.

⏱️ ~110 min.

> **Stop the Module 14 stack first.** Three JVMs plus Scylla plus six Postgres
> shards will not fit. `docker compose -p pulse-shard down` and
> `docker compose -p pulse-scylla down`.
>
> **Low-memory path:** one broker, `replication.factor=1`,
> `min.insync.replicas=1`. You lose Part F entirely — a single broker cannot
> teach durability — and every other part holds.

Reference machine: **8-core / 16 GB, Ubuntu 24.04, Python 3.12, Kafka 3.8 (KRaft),
Redis 7.2, Uvicorn + uvloop, Django 5.1 / Channels 4.1.**

---

## Part A — Kafka in KRaft mode

```bash
docker compose -p pulse-kafka -f infra/compose.kafka.yml up -d --wait
alias kt='docker exec pulse-kafka1 /opt/kafka/bin/kafka-topics.sh --bootstrap-server localhost:9092'
alias kg='docker exec pulse-kafka1 /opt/kafka/bin/kafka-consumer-groups.sh --bootstrap-server localhost:9092'

docker exec pulse-kafka1 /opt/kafka/bin/kafka-metadata-quorum.sh \
    --bootstrap-server localhost:9092 describe --status
```
**Expected:**
```
ClusterId:              X049LBsKSZiId2ZVRDMiEQ
LeaderId:               2
LeaderEpoch:            4
CurrentVoters:          [1,2,3]
CurrentObservers:       []
```
✅ Three voters, no ZooKeeper. The controller quorum is the brokers themselves.

```bash
kt --create --topic chat-messages --partitions 64 --replication-factor 3 \
   --config min.insync.replicas=2 \
   --config retention.ms=86400000 \
   --config compression.type=lz4
kt --describe --topic chat-messages | head -4
```
**Expected:**
```
Topic: chat-messages	PartitionCount: 64	ReplicationFactor: 3
	Configs: min.insync.replicas=2,compression.type=lz4,retention.ms=86400000
	Topic: chat-messages	Partition: 0	Leader: 2	Replicas: 2,3,1	Isr: 2,3,1
	Topic: chat-messages	Partition: 1	Leader: 3	Replicas: 3,1,2	Isr: 3,1,2
```
✅ `Isr: 2,3,1` — all three replicas are in-sync. Watch this list in Part F.

### A1. Feel the partition-count constraint

Module 09 gave every room its own stream. Try that here:

```bash
time kt --create --topic per-room-probe --partitions 10000 --replication-factor 3
```
**Expected:**
```
Created topic per-room-probe.

real	1m52.418s
```
```bash
docker stats --no-stream pulse-kafka1 --format '{{.MemUsage}} {{.CPUPerc}}'
docker exec pulse-kafka1 sh -c 'ls /tmp/kraft-combined-logs | wc -l'
```
**Expected:**
```
1.71GiB / 15.6GiB   94.20%
10004
```
✅ **Ten thousand partitions took 112 seconds to create and produced 10,004
directories on each of three brokers.** Pulse has a million rooms. This is the
difference between "a key" and "a partition," and it is why rooms must share.

```bash
kt --delete --topic per-room-probe
```

> **The pattern, for the third time in this course:** hash to a fixed number of
> buckets, map buckets to machines, move buckets rather than rehash. Module 14
> used 4,096 logical shards. Redis Cluster uses 16,384 slots. Kafka uses
> `num_partitions` — and *its* buckets are expensive, so the count is small and
> ~15,600 rooms share a log.

---

## Part B — Produce Pulse's envelopes, and catch the clients disagreeing

```bash
pip install aiokafka confluent-kafka
kt --create --topic partitioner-probe --partitions 64 --replication-factor 3
python 16-kafka-comparison/code/partitioner_check.py
```
**Expected:**
```
room                    0         1         2
-----------------------------------------------
room.7                 41        18        18
room.general           59        26        26
room.42                 6        60        60
room.random            23        44        44
room.support           12         2         2

  column 0: confluent-kafka DEFAULT (consistent_random / CRC32)
  column 1: confluent-kafka partitioner=murmur2_random
  column 2: aiokafka DEFAULT (murmur2, Java-compatible)

confluent DEFAULT vs aiokafka:      5/5 rooms land on DIFFERENT partitions
confluent murmur2_random vs aiokafka: 5/5 rooms agree

RESULT: the default partitioners disagree; murmur2_random fixes it.
        Set it explicitly. A default is not a contract.
```

✅ **Five out of five.** `confluent-kafka` wraps librdkafka, whose default
partitioner is `consistent_random` (CRC32-based). `aiokafka` implements the
Java `DefaultPartitioner`, which is murmur2. Same room key, different partition.

Why this is a **correctness** bug and not a curiosity: Kafka's ordering guarantee
is **per partition**. A room produced by both clients has messages in two
partitions and therefore **no ordering guarantee at all** — the one property you
adopted Kafka for. The symptom is `seq` gaps that the client's gap detector
(Module 10) reports and that `resume` never fills, because the messages *are*
delivered, just out of order and late.

The fix is one line, and it belongs in your config from the first commit:

```python
Producer({"bootstrap.servers": ..., "partitioner": "murmur2_random"})
```

> **When a hash function is part of a wire contract, pin it explicitly.** Module
> 14 said this about `zlib.crc32` versus Python's `PYTHONHASHSEED`-randomized
> `hash()`. Here it costs you ordering instead of routing. A default is not a
> contract.

### B1. Wire it into Pulse

Copy [`code/kafka_layer.py`](./code/kafka_layer.py) into
`apps/pulse/chat/kafka_layer.py` and add a settings module:

```python
# pulse/settings/kafka.py
from .redis import *          # presence, rate limits, unread, dedup: still Redis

PULSE_FANOUT = "kafka"        # "streams" (Module 09) | "kafka"
PULSE_KAFKA = "localhost:19092,localhost:19093,localhost:19094"
PULSE_KAFKA_TOPOLOGY = "A"    # A = group per worker process, B = shared group
```

Note what is *not* moving: presence (Module 11), rate-limit buckets, unread
counters, dedup keys and auth tickets stay in Redis. **Kafka replaces the fan-out
log, not Redis.** Anyone proposing "let's move to Kafka" should be asked which of
those five they intend to rebuild.

```bash
PULSE_WORKER_ID=0 uvicorn pulse.asgi:application \
    --loop uvloop --workers 8 --port 8000 \
    --env-file <(echo DJANGO_SETTINGS_MODULE=pulse.settings.kafka)
```
**Expected in the log, eight times:**
```
kafka consumer started: group=pulse-lab-0
kafka consumer started: group=pulse-lab-1
...
```
✅ Eight worker processes, **eight consumer groups**, each reading all 64
partitions. Confirm from the broker's side:

```bash
kg --list | sort
```
**Expected:**
```
pulse-lab-0
pulse-lab-1
...
pulse-lab-7
```

Open two browser tabs on different rooms and send messages. Cross-worker chat
works exactly as it did with the Redis channel layer and with Streams — which is
the point: the protocol did not change, only the transport underneath it.

---

## Part C — Head to head

Same harness as Module 09: 20,000 connections, 100 rooms, 200 members, 2 nodes ×
8 workers.

```bash
python 16-kafka-comparison/code/lag_probe.py --backend kafka --interval 5 &
locust -f 06-load-testing-harness/code/locustfile.py \
    --headless -u 20000 -r 500 -t 10m --host ws://localhost:8000
```

**Expected (median of 3):**

| | Redis Streams (M09) | Kafka, `aiokafka` | Kafka, `confluent` + thread |
|---|--------------------|-------------------|----------------------------|
| **Fan-out p50** | **20 ms** | 41 ms | 31 ms |
| p95 | **74 ms** | 118 ms | 96 ms |
| p99 | **186 ms** | 246 ms | 208 ms |
| **p99.9** | 880 ms | 690 ms | **640 ms** |
| Producer append p50 | **0.9 ms** | 8.4 ms | 5.9 ms |
| Consumer CPU per worker | **11%** | 34% | 14% |
| Backbone CPU | **54%** (1 Redis core) | 91% (3 broker cores) | 91% |
| Backbone RSS | **2.1 GB** | 4.4 GB (3 × 1.47) | 4.4 GB |
| Disk written / hour | **0** | 9.1 GB | 9.1 GB |
| Disk retained (24 h) | **0** | 218 GB | 218 GB |

### C1. Read the client column, because it is the Python story

```
Fan-out p50:  41 ms (aiokafka)  vs  31 ms (confluent-kafka)
Consumer CPU: 34%   (aiokafka)  vs  14%  (confluent-kafka)
```

`aiokafka` is pure Python: every record is decoded, decompressed and framed in
the interpreter. `confluent-kafka` wraps librdkafka in C and does that work
outside the GIL — **2.4× less CPU per worker for the same traffic.**

And you cannot simply take the faster one, because `confluent-kafka`'s `poll()`
**blocks**. Calling it from the event loop that owns 2,500 WebSocket connections
is Module 15's cardinal sin, and Module 15 measured what it costs: p99 from
~60 ms to **multiple seconds for every connection on that worker**.

Prove it, because it is worth seeing once:

```bash
PULSE_KAFKA_CLIENT=confluent-inline uvicorn pulse.asgi:application \
    --loop uvloop --workers 8 --port 8000
locust -f 06-load-testing-harness/code/locustfile.py --headless -u 20000 -t 2m
```
**Expected:**
```
fanout p99:  208ms -> 4,180ms
event loop lag p99: 3.1ms -> 2,890ms
ws_errors: 11.4%   (client-side heartbeat timeouts)
```
✅ **The faster client made everything 20× slower**, because it stalled the loop.
The threaded producer + `aiokafka` consumer split in `kafka_layer.py` exists for
exactly this reason: put the C client where blocking is fine (a dedicated
producer thread), keep the async client where the sockets are.

### C2. Consumer lag — the metric Redis never gave you

```bash
curl -s localhost:9310/metrics | grep pulse_fanout_lag_total
```
**Expected:**
```
pulse_fanout_lag_total{backend="kafka",group="pulse-lab-0"} 31
pulse_fanout_lag_total{backend="kafka",group="pulse-lab-1"} 1847
...
pulse_fanout_lag_scrape_seconds{backend="kafka"} 0.041
```
✅ Group 1 is 1,847 messages behind. One number, one API call, per group, per
partition. **This is the single best health signal a log-based fan-out has**, and
it is why Kafka is easier to operate than its reputation suggests.

Now the same for Redis Streams:

```bash
python 16-kafka-comparison/code/lag_probe.py --backend redis --top 100 &
curl -s localhost:9310/metrics | grep scrape_seconds
```
**Expected:**
```
pulse_fanout_lag_scrape_seconds{backend="redis"} 0.412
```
✅ **Ten times the scrape cost for 100 of 1,000 rooms.** `XINFO GROUPS` is
per-stream, and Pulse has one stream per room. At a million rooms it is not a
monitoring strategy — and the sampling workaround is blind to a cold room whose
consumer has stalled, which is precisely the failure you wanted to catch.

Write that down. It is unglamorous and it is real.

### C3. Sweep `linger.ms` and `acks`

```bash
python 16-kafka-comparison/code/kafka_bench.py --sweep linger,acks
```
**Expected:**

| `linger.ms` | `acks` | Append p50 | Fan-out p50 | Throughput | Loss on broker kill |
|-------------|--------|-----------|-------------|------------|---------------------|
| 0 | 1 | **0.8 ms** | **26 ms** | 340k/s | **up to 1 batch** |
| 0 | all | 3.4 ms | 33 ms | 371k/s | **0** |
| **5** | 1 | 2.1 ms | 29 ms | 402k/s | up to 1 batch |
| **5** | **all** | **5.9 ms** | **31 ms** | **448k/s** | **0** |
| 20 | all | 22.7 ms | 54 ms | 471k/s | 0 |

✅ `linger.ms=5, acks=all` is the knee: **21% more throughput than `linger=0` for
2.5 ms of added append latency**, on a path where end-to-end is already ~31 ms.
`linger=20` buys 5% more for 17 ms, which is a bad trade when the tail is what
users notice.

`acks=1` is 2.5 ms faster and loses data on a broker failure. Given that
replacing Module 13's outbox is one of Kafka's main arguments, `acks=1` gives
that up and keeps the operational cost. **Never `acks=1` for the durable path.**

---

## Part D — Where Kafka wins: the read-amplification crossover

Module 09's read amplification is O(nodes × cores) here, because the unit of
consumption is a worker process. Sweep it.

```bash
for w in 8 16 32 64 128; do
  python 16-kafka-comparison/code/kafka_bench.py --workers $w --backend both
done
```
**Expected:**

| Worker processes | Groups | Redis CPU | Redis p99 | Kafka CPU (3 brokers) | Kafka p99 |
|-----------------|--------|-----------|-----------|----------------------|-----------|
| 8 | 8 | 31% | 172 ms | 48% | 214 ms |
| 16 | 16 | 54% | 186 ms | 61% | 219 ms |
| 32 | 32 | **88%** | 402 ms | 79% | 226 ms |
| 64 | 64 | **100% (saturated)** | **2,240 ms** | 94% | 238 ms |
| 128 | 128 | 100%, dropping | **timeouts** | 141% | **271 ms** |

✅ **Redis saturates between 32 and 64 worker processes; Kafka is nearly flat to
128.** Two reasons, and both matter:

1. **Redis is single-threaded.** Every `XREADGROUP` from every consumer group is
   work on **one** core. Module 08 taught you this and Module 09 predicted this
   exact wall.
2. **Kafka's reads come out of the page cache via `sendfile`.** 128 consumers
   reading the same recent offsets hit the same pages, with no user-space copy
   and no per-read CPU on a shared thread.

**Now read the x-axis honestly.** 64 worker processes is 8 machines at 8 cores
each — a real deployment, and one Pulse would reach before it reached 1M rooms.
This is Kafka's genuine architectural advantage for high fan-out, and it is the
strongest argument in its favour in this entire module.

It is also **worse in Python than on the JVM**. The JVM twin's crossover is at 8
*nodes*; ours is at ~48 *worker processes*, which is 6 nodes. The process-per-core
model brings the wall closer, exactly as it did for connections (Module 13),
`max_connections` (Module 13) and shard-map fencing (Module 14).

### D1. Topology B, and what the extra hop costs

```bash
PULSE_KAFKA_TOPOLOGY=B python 16-kafka-comparison/code/kafka_bench.py --workers 64
```
**Expected:**
```
topology A (64 groups):  fanout p50 31ms  p99 238ms  broker CPU 94%  net 3.4 Gbit/s
topology B (1 group):    fanout p50 38ms  p99 259ms  broker CPU 22%  net 0.4 Gbit/s
                         extra channel-layer hop: +7ms p50
                         Redis CPU (for the re-fan-out): 19%
```
✅ **8.5× less broker network and CPU, for +7 ms p50 and a rebalance problem.**
Topology B is the right answer once read bandwidth binds — which the sweep above
says is past 64 workers.

Note what Topology B did: it put the channel layer back in the path. You did not
eliminate Redis; you demoted it from log to transport.

---

## Part E — Rebalances

Topology A never rebalances — a group with one member has nothing to reassign.
So switch to Topology B to see the problem at all.

```bash
PULSE_KAFKA_TOPOLOGY=B  # 24 consumers, one group
```

### E1. Break it with the eager protocol

```python
# temporarily, to see the default behaviour
partition_assignment_strategy=[RoundRobinPartitionAssignor]   # eager
group_instance_id=None                                        # no static membership
```
```bash
locust ... -u 20000 -t 5m &
sleep 60
docker restart pulse-app-node-c            # 8 of 24 consumers leave and return
```
**Expected in every node's log:**
```
Revoking previously assigned partitions frozenset({TopicPartition(...), ...})
(Re-)joining group pulse-fanout
Successfully joined group pulse-fanout with generation 14
```
**Expected — a cluster-wide consumption gap:**
```bash
curl -s localhost:9310/metrics | grep lag_total
```
```
t=60s   pulse_fanout_lag_total{group="pulse-fanout"} 42
t=63s   pulse_fanout_lag_total{group="pulse-fanout"} 118,401     <-- !!
t=67s   pulse_fanout_lag_total{group="pulse-fanout"} 9,204
t=71s   pulse_fanout_lag_total{group="pulse-fanout"} 61
```
```
consumption gap: 3.8 s
fanout p99 during the window: 4,120 ms
messages lost: 0        (they arrived late, not never)
```
✅ **3.8 seconds during which no message was delivered on any node**, because
under the eager protocol every consumer revokes every partition. A rolling deploy
of three nodes is three of these.

Zero lost — Kafka's log means "late" and not "gone", which is materially better
than Module 07's Pub/Sub result. But 3.8 s of silence in a chat app is a support
ticket.

### E2. Fix it, in two steps

**Cooperative first:**
```python
partition_assignment_strategy=[StickyPartitionAssignor]
```
```bash
docker restart pulse-app-node-c
```
**Expected:**
```
consumption gap: 0.4 s      (only the 16 partitions that actually moved)
fanout p99 during the window: 388 ms
```
✅ 9.5× better. Only the partitions that must move are revoked.

**Then static membership:**
```python
group_instance_id=f"pulse-{socket.gethostname()}-{os.environ['PULSE_WORKER_ID']}"
session_timeout_ms=45_000
```
```bash
docker restart pulse-app-node-c            # back within 45 s
```
**Expected:**
```
kg --describe --group pulse-fanout | grep -c ''
(no rebalance logged on any surviving consumer)

consumption gap: 0.0 s
fanout p99 during the window: 241 ms       (baseline: 238 ms)
generation: 14 -> 14                        (unchanged)
```
✅ **Zero rebalances on a rolling restart.** The returning consumers reclaimed
their own partitions because their `group.instance.id` was unchanged.

> **The identity must be per worker PROCESS and stable across restarts.**
> `f"{HOSTNAME}-{PULSE_WORKER_ID}"` — the same env var Module 12's Snowflake uses
> for its worker-id bits and Module 14's fleet fencing uses for its key. Derive
> it from a PID or a UUID and static membership silently does nothing: no error,
> no warning, just the 3.8 s gap you thought you had fixed.

Record it:
```markdown
## Module 16 — Kafka rebalances

| Strategy | Consumption gap on a node restart | p99 during |
|----------|-----------------------------------|-----------|
| eager (default)              | 3.8 s | 4,120 ms |
| cooperative/sticky           | 0.4 s |   388 ms |
| cooperative + static members | 0.0 s |   241 ms |

Topology A (group per worker process) never rebalances at all -- a
single-member group has nothing to reassign. It pays 24x read amplification
for that.
```

---

## Part F — Durability, and refusing writes on purpose

### F1. The test Module 09 failed

```bash
python 16-kafka-comparison/code/kafka_bench.py --loss-test --messages 200 &
sleep 2
docker kill pulse-kafka2 && docker start pulse-kafka2
```
**Expected:**
```
sent: 200   received: 200   lost: 0   duplicated: 3
```
✅ Zero lost. Compare with Module 09's measurement for the same test against
Redis: **57 of 200 lost** when Redis was killed and restarted with persistence
off. The three duplicates are the producer's idempotent retry surfacing as
redelivery, and Module 05's `client_id` makes them free.

### F2. `min.insync.replicas`, felt

```bash
docker kill pulse-kafka2 pulse-kafka3        # 2 of 3 gone
kt --describe --topic chat-messages | head -3
```
**Expected:**
```
	Topic: chat-messages	Partition: 0	Leader: 1	Replicas: 2,3,1	Isr: 1
```
✅ `Isr: 1` — one in-sync replica, below `min.insync.replicas=2`.

```bash
python 16-kafka-comparison/code/kafka_bench.py --produce 10
```
**Expected:**
```
KafkaError{code=NOT_ENOUGH_REPLICAS,val=19,str="Broker: Not enough in-sync
replicas"}
sent: 0   rejected: 10   lost: 0
```
And in the app:
```
{"v":1,"type":"error","room":"room.7","ts":...,
 "data":{"code":"rate_limited","message":"backbone unavailable",
         "retry_after_ms":5000,"client_id":"01JQ8Z…"}}
```
✅ **Pulse stops accepting messages.** That is correct, and it is Module 10's
principle expressed as a broker config: **prefer a clear failure over a silent
loss.** The client sees an error frame with `retry_after_ms`, the socket stays
open (protocol §4), and the retry carries the same `client_id`.

The subtlety worth internalizing: with `min.insync.replicas=1`, that same
`acks=all` write would have been **accepted** and stored on one disk. `acks=all`
means "all *in-sync* replicas", not "all replicas." **`acks=all` alone is not
durability.**

```bash
docker start pulse-kafka2 pulse-kafka3
sleep 20 && kt --describe --topic chat-messages | head -3
```
**Expected:**
```
	Topic: chat-messages	Partition: 0	Leader: 1	Replicas: 2,3,1	Isr: 1,2,3
```
✅ ISR healed automatically. No operator action.

### F3. What Kafka would let you delete

Module 13's transactional outbox exists to close the dual-write hole: the message
commits to Postgres and the process dies before publishing, so the message is
durable and **will never be delivered** — the one loss mode a connected client
cannot detect, because the `seq` was allocated and used.

If Kafka is the durable record, the outbox goes away:

| | Redis Streams | Redis + outbox (M13) | Kafka `acks=all` |
|---|--------------|----------------------|------------------|
| Backbone paused 1.5 s | 0 lost | 0 lost | **0 lost** |
| Backbone killed + restarted | **57/200 lost** | 0 (relay republishes) | **0 lost** |
| 2 of 3 brokers lost | n/a | n/a | **writes refused, 0 lost** |
| Machinery required | — | outbox table + Celery relay + pruning + `SKIP LOCKED` | **none** |
| Write-path cost | 1.8 ms | **9.4 ms** (or +1.9 ms hybrid) | 5.9 ms |

✅ That is a real simplification and it belongs in the comparison. It is not free:
you delete a Postgres table you already run and add three brokers you do not.

---

## Part G — Resource cost, and the verdict

```bash
python 16-kafka-comparison/code/kafka_bench.py --resource-report --rate 400000
```
**Expected at 400,000 outbound msg/s sustained:**

| | Redis Streams | Kafka (3 brokers) |
|---|--------------|-------------------|
| RAM | **2.1 GB** | 4.4 GB |
| CPU | 88% (**1** core, saturated) | 94% (**3** cores) |
| Disk written / hour | **0** | 9.1 GB |
| Disk retained (24 h) | **0** | 218 GB |
| Network (internal) | 3.2 Gbit/s | 3.4 Gbit/s |
| Containers to operate | **1** | 3 (+ exporter) |
| Config surface that matters | ~12 settings | **~40 settings** |
| Client libraries to choose between | 1 | **3, and two disagree** |
| Upgrade blast radius | one process | rolling, quorum-aware |

### The verdict

| Dimension | Winner | Margin |
|-----------|--------|--------|
| Latency (p50) | **Redis** | 20 ms vs 31 ms |
| Latency (p99.9) | **Kafka** | 640 ms vs 880 ms |
| Scaling to many worker processes | **Kafka** | flat to 128; Redis saturates at ~48 |
| Durability | **Kafka** | 0 lost vs 57/200, with no outbox |
| Replay window | **Kafka** | 24 h vs minutes |
| Additional consumers | **Kafka** | a new group; Redis needs a group per stream |
| Consumer lag as a metric | **Kafka** | 1 call vs 1 per room |
| Log per entity | **Redis** | 1M keys free; 10k partitions took 112 s |
| Per-room replay | **Redis** | one `XRANGE` vs scanning a shared partition |
| Operational surface | **Redis** | 1 container, ~12 settings |
| Resource cost | **Redis** | 2.1 GB vs 4.4 GB; 0 vs 218 GB/day |
| **Already in our stack** | **Redis** | presence, rate limits, unread, dedup, tickets |

**Pulse stays on Redis Streams. For now, and for reasons that will expire.**

1. **We already run Redis** for five other correctness surfaces (Module 11's
   presence and token buckets, Module 10's unread counters, Module 09's dedup,
   Module 21's tickets). Kafka would be a *second* stateful system, not a
   replacement.
2. **A log per room is the shape of our problem.** Per-room replay is one
   `XRANGE`; on Kafka it is a partition scan with a filter.
3. **Latency at p50 is better**, and chat is a p50 product punctuated by p99
   complaints.
4. **We are below the crossover.** Pulse today is 2 nodes × 8 workers = 16 worker
   processes. Redis saturates at ~48.

**The three conditions that flip it**, and note that two are not performance:

1. **Worker processes exceed ~48** (6 nodes at 8 cores). Part D's crossover is
   measured, and it arrives sooner in Python than on the JVM because the unit is a
   process, not a machine.
2. **A second consumer appears** — search indexing, moderation, analytics, an ML
   pipeline. On Kafka that is one new consumer group reading 24 hours of history
   with zero impact on delivery. On Redis Streams it is a new consumer group **per
   room**, and a replay window measured in minutes.
3. **Someone else already runs Kafka.** If there is a platform team operating a
   cluster with an SLO, the marginal cost of a topic is near zero and every
   argument above except per-room replay evaporates. **This decides more real
   architectures than any benchmark in this course.**

---

## What you built

- Kafka 3.8 in **KRaft mode** — three brokers, three controllers, no ZooKeeper —
  and the demonstration that 10,000 partitions cost 112 seconds and 10,004
  directories per broker, while 10,000 Redis streams cost nothing.
- Pulse's envelopes on Kafka with `room.key` as the partition key, preserving
  per-room ordering — and the proof that **Python's two Kafka clients partition
  differently by default**, which silently destroys that guarantee.
- The threaded-producer / async-consumer split, and the measurement of what
  happens when you get it wrong: **p99 208 ms → 4,180 ms** from one blocking
  `poll()` on the event loop.
- Both fan-out topologies, with the read-amplification crossover measured:
  **Redis saturates at ~48 worker processes, Kafka is flat to 128.**
- Consumer lag as a first-class metric, and the honest measurement of what the
  same metric costs on Redis Streams (10× the scrape, and blind to cold rooms).
- Rebalances: **3.8 s → 0.4 s → 0.0 s**, and the identity rule that makes static
  membership actually work.
- `min.insync.replicas` felt from the client side: writes correctly **refused**
  rather than silently accepted onto one disk.
- **A defensible decision with three falsifiable conditions**, two of which have
  nothing to do with performance.

Now do [`challenge.md`](./challenge.md).

Then: [Module 17 — The Next.js Real-Time Client](../17-nextjs-realtime-client/).
