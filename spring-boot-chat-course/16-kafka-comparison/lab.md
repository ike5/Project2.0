# Lab 16 — Kafka, Measured

**You'll:** run the fan-out on Kafka in KRaft mode, benchmark it against Redis
Streams, trigger a rebalance and measure the outage, then eliminate rebalances
with cooperative assignment and static membership.

⏱️ ~100 min.

> **Low-memory path:** one broker instead of three, `replication.factor=1`.
> Every latency and throughput number holds; you lose the durability drills, so
> read Part F rather than running it.

---

## Part A — Kafka in KRaft mode

No ZooKeeper. `infra/compose.kafka.yml`:

```yaml
name: pulse-kafka

x-broker: &broker
  image: apache/kafka:3.8.0
  environment: &broker-env
    KAFKA_PROCESS_ROLES: broker,controller
    KAFKA_CONTROLLER_QUORUM_VOTERS: 1@kafka1:9093,2@kafka2:9093,3@kafka3:9093
    KAFKA_LISTENERS: PLAINTEXT://:9092,CONTROLLER://:9093
    KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: PLAINTEXT:PLAINTEXT,CONTROLLER:PLAINTEXT
    KAFKA_CONTROLLER_LISTENER_NAMES: CONTROLLER
    KAFKA_INTER_BROKER_LISTENER_NAME: PLAINTEXT
    KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 3
    KAFKA_TRANSACTION_STATE_LOG_REPLICATION_FACTOR: 3
    KAFKA_TRANSACTION_STATE_LOG_MIN_ISR: 2
    KAFKA_DEFAULT_REPLICATION_FACTOR: 3
    KAFKA_MIN_INSYNC_REPLICAS: 2
    KAFKA_NUM_PARTITIONS: 64
    KAFKA_LOG_RETENTION_HOURS: 24
    CLUSTER_ID: pulse-cluster-0000000000
  healthcheck:
    test: ["CMD-SHELL", "/opt/kafka/bin/kafka-broker-api-versions.sh --bootstrap-server localhost:9092 || exit 1"]
    interval: 10s
    retries: 20

services:
  kafka1:
    <<: *broker
    ports: [ "19092:9092" ]
    environment:
      <<: *broker-env
      KAFKA_NODE_ID: 1
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka1:9092,EXTERNAL://localhost:19092
  kafka2:
    <<: *broker
    ports: [ "19093:9092" ]
    environment: { <<: *broker-env, KAFKA_NODE_ID: 2,
                   KAFKA_ADVERTISED_LISTENERS: "PLAINTEXT://kafka2:9092,EXTERNAL://localhost:19093" }
  kafka3:
    <<: *broker
    ports: [ "19094:9092" ]
    environment: { <<: *broker-env, KAFKA_NODE_ID: 3,
                   KAFKA_ADVERTISED_LISTENERS: "PLAINTEXT://kafka3:9092,EXTERNAL://localhost:19094" }
```

```bash
docker compose -f infra/compose.kafka.yml up -d --wait
alias kt='docker exec pulse-kafka-kafka1-1 /opt/kafka/bin/kafka-topics.sh --bootstrap-server localhost:9092'

kt --create --topic chat-messages --partitions 64 --replication-factor 3 \
   --config min.insync.replicas=2 --config retention.ms=86400000 \
   --config compression.type=lz4
kt --describe --topic chat-messages | head -5
```
**Expected:**
```
Topic: chat-messages  PartitionCount: 64  ReplicationFactor: 3
	Configs: min.insync.replicas=2,compression.type=lz4,retention.ms=86400000
	Topic: chat-messages Partition: 0 Leader: 2 Replicas: 2,3,1 Isr: 2,3,1
	Topic: chat-messages Partition: 1 Leader: 3 Replicas: 3,1,2 Isr: 3,1,2
```

> **Why 64 partitions?** It's the parallelism ceiling: one partition is consumed
> by at most one consumer *in a group*. With 8 nodes each in its own group, all
> 64 are read by all 8 — partition count here governs producer parallelism and
> per-partition throughput, not consumer scaling. 64 is comfortable for a 3-broker
> cluster; the challenge asks you to justify it properly.

---

## Part B — The Kafka fan-out

```xml
<dependency>
  <groupId>org.springframework.kafka</groupId>
  <artifactId>spring-kafka</artifactId>
</dependency>
```

`application-kafka.yml`:
```yaml
spring:
  kafka:
    bootstrap-servers: localhost:19092,localhost:19093,localhost:19094
    producer:
      acks: all                          # durability: on disk on >= min.insync.replicas
      compression-type: lz4
      properties:
        enable.idempotence: true         # no duplicates from producer retries
        max.in.flight.requests.per.connection: 5
        linger.ms: 5                     # batch for 5ms -- THE latency/throughput knob
        batch.size: 65536
    consumer:
      group-id: node-${pulse.node-id}    # ONE GROUP PER NODE (Module 09's shape)
      auto-offset-reset: latest
      enable-auto-commit: false          # we commit after processing
      max-poll-records: 500
      properties:
        partition.assignment.strategy: org.apache.kafka.clients.consumer.CooperativeStickyAssignor
        group.instance.id: node-${pulse.node-id}     # static membership
        session.timeout.ms: 45000
    listener:
      ack-mode: manual                   # at-least-once
      concurrency: 8                     # 8 threads per node across 64 partitions
```

`src/main/java/com/pulse/fanout/KafkaFanout.java`:

```java
package com.pulse.fanout;

import org.apache.kafka.clients.producer.ProducerRecord;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.kafka.support.Acknowledgment;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.stereotype.Component;

@Component
@Profile("kafka")
public class KafkaFanout {

    private static final String TOPIC = "chat-messages";

    private final KafkaTemplate<String, String> kafka;
    private final SimpMessagingTemplate broker;

    /** The KEY is the roomId. Same key -> same partition -> per-room ordering. */
    public CompletableFuture<SendResult<String, String>> append(String roomId, Envelope e) {
        var record = new ProducerRecord<>(TOPIC, roomId, json.writeValueAsString(e));
        record.headers().add("room", roomId.getBytes());
        record.headers().add("origin", nodeId.getBytes());
        return kafka.send(record);
    }

    @KafkaListener(topics = TOPIC)
    public void consume(ConsumerRecord<String, String> record, Acknowledgment ack) {
        try {
            var envelope = json.readValue(record.value(), Envelope.class);
            broker.convertAndSend("/topic/room." + record.key(), envelope);
            ack.acknowledge();                     // AFTER processing: at-least-once
            delivered.increment();
        } catch (Exception e) {
            // Do NOT ack. The offset stays; this record is redelivered on the
            // next poll or after a rebalance.
            log.error("delivery failed for {}@{}", record.topic(), record.offset(), e);
            deliveryFailures.increment();
        }
    }
}
```

> ⚠️ **Not acking in Kafka is coarser than not acking in Redis Streams.** Kafka
> tracks *one offset per partition*, not per record. Failing record N and acking
> N+1 would mark N as done. The correct handling is to not ack the batch and let
> the whole batch redeliver — which means **your consumer must be idempotent for
> the whole batch**, not just for one record. Module 05's `clientId` covers this.

Run it:
```bash
SPRING_PROFILES_ACTIVE=kafka PULSE_NODE_ID=a SERVER_PORT=8080 ./mvnw spring-boot:run
SPRING_PROFILES_ACTIVE=kafka PULSE_NODE_ID=b SERVER_PORT=8081 ./mvnw spring-boot:run
```
```bash
./code/stomp.sh alice room.7          # -> node-a
/tmp/s8081.sh bob room.7              # -> node-b
```
**Expected:** cross-instance chat works, as it did with Redis.

Watch the topic:
```bash
docker exec pulse-kafka-kafka1-1 /opt/kafka/bin/kafka-console-consumer.sh \
  --bootstrap-server localhost:9092 --topic chat-messages \
  --property print.key=true --property print.partition=true --from-beginning
```
**Expected:**
```
Partition:41	room.7	{"v":1,"type":"message.new","room":"7","data":{...}}
Partition:41	room.7	{"v":1,"type":"message.new","room":"7","data":{...}}
```
✅ **Same partition every time** — `hash("room.7") % 64 = 41`. That's the
ordering guarantee, visible.

---

## Part C — Head to head

Identical k6 workload against both backbones, alternated across three rounds.

```bash
./code/backbone_bench.sh -e ROOMS=100 -e SEND_EVERY=60000
```

**Expected (median of 3, 2 nodes, 20,000 connections):**

| | Redis Streams | Kafka |
|---|--------------|-------|
| **p50 fan-out** | **21 ms** | 34 ms |
| p95 | **79 ms** | 98 ms |
| p99 | **192 ms** | 214 ms |
| p99.9 | 910 ms | **740 ms** |
| Append (producer) p50 | **0.9 ms** | 6.2 ms |
| Backbone CPU | 51% (1 core) | **89%** (across 3 brokers) |
| Backbone RSS | **1.9 GB** | 4.2 GB (3 × 1.4) |
| Disk written / hour | 0 | **8.4 GB** |

Redis wins p50 by 13 ms, mostly in the append: **0.9 ms versus 6.2 ms.**

Find out why:
```bash
docker exec pulse-kafka-kafka1-1 /opt/kafka/bin/kafka-run-class.sh \
  kafka.tools.JmxTool --object-name 'kafka.network:type=RequestMetrics,name=TotalTimeMs,request=Produce' \
  --one-time true
```
**Expected:**
```
Mean: 5.8   99thPercentile: 21.4
```

It's `acks=all` plus `linger.ms=5`. Test the knob:

```bash
for linger in 0 5 20; do
  for acks in 1 all; do
    KAFKA_LINGER_MS=$linger KAFKA_ACKS=$acks ./code/backbone_bench.sh -e ROOMS=100
  done
done
```

**Expected:**

| `linger.ms` | `acks` | Append p50 | Fan-out p50 | Throughput | Loss on broker kill |
|-------------|--------|-----------|-------------|-----------|---------------------|
| 0 | 1 | **0.8 ms** | **22 ms** | 610k/s | **up to 1 batch** |
| 0 | all | 3.1 ms | 28 ms | 690k/s | **0** |
| 5 | 1 | 1.9 ms | 24 ms | 780k/s | up to 1 batch |
| **5** | **all** | 6.2 ms | 34 ms | **840k/s** | **0** |
| 20 | all | 21.4 ms | 52 ms | **910k/s** | 0 |

✅ **`linger.ms` is a pure latency-for-throughput trade**, and it's yours to set.
At `linger.ms=0, acks=all` Kafka's append is 3.1 ms and fan-out p50 is 28 ms —
within 7 ms of Redis, with real durability.

**Set `linger.ms=0` for chat.** The throughput you give up (840k → 690k) is
capacity you don't need; the 8 ms of latency is felt by every user.

---

## Part D — Where Kafka wins: high fan-out

Redis pays CPU on **one thread** per read. Kafka serves reads from the page cache
with `sendfile`. Scale the node count and watch them diverge.

```bash
for nodes in 1 2 4 8 16; do
  ./code/backbone_bench.sh --nodes $nodes -e ROOMS=1000 -e SEND_EVERY=10000
done
```

**Expected:**

| Nodes | Redis CPU | Redis p99 | Kafka CPU (total) | Kafka p99 |
|-------|-----------|-----------|-------------------|-----------|
| 1 | 24% | 168 ms | 41% | 198 ms |
| 2 | 51% | 192 ms | 52% | 214 ms |
| 4 | **89%** | 412 ms | 71% | 228 ms |
| 8 | **100% (saturated)** | **2,140 ms** | 94% | **241 ms** |
| 16 | 100%, dropping | **timeouts** | 148% (3 brokers) | **288 ms** |

```
p99 (ms)
 2000 │                          ● Redis
      │                        ╱
 1000 │                      ╱
      │                    ╱
  400 │                 ●
      │            ╱
  200 │ ●───●───●─────────────●───●───● Kafka
      └───┬───┬───┬───────────┬───────┬──── nodes
          1   2   4           8      16
```

✅ **Redis saturates at ~8 consuming nodes; Kafka is flat to 16 and beyond.**

The mechanism:
```bash
docker exec pulse-redis redis-cli INFO commandstats | grep xreadgroup
```
```
cmdstat_xreadgroup:calls=1284933,usec=42184921,usec_per_call=32.83
```
32.8 µs per `XREADGROUP` × 8 nodes × the message rate, all on **one thread**.

```bash
docker exec pulse-kafka-kafka1-1 /opt/kafka/bin/kafka-run-class.sh kafka.tools.JmxTool \
  --object-name 'kafka.server:type=BrokerTopicMetrics,name=BytesOutPerSec' --one-time true
```
```
OneMinuteRate: 412884120.0        # 412 MB/s out
```
Kafka served 412 MB/s of consumer reads at 94% CPU across three brokers, because
all eight consumers read the **same recent offsets**, which are in the page cache,
and `sendfile` copies them to sockets without passing through userspace.

> **This is Module 09's challenge finding, confirmed from the other side.** The
> per-group read amplification that caps Redis Streams at ~9 nodes is exactly
> what Kafka's architecture is designed for.

---

## Part E — Rebalances

**The operational cost people underestimate.** First, with the defaults.

```bash
# Temporarily use the eager assignor and no static membership
KAFKA_ASSIGNOR=org.apache.kafka.clients.consumer.RangeAssignor \
KAFKA_STATIC_MEMBERSHIP=false ./code/start_kafka_nodes.sh 8

k6 run -e ROOMS=1000 --vus 20000 --duration 5m code/pulse-load.js &
sleep 90
docker restart pulse-node-c
```

**Expected in every node's log:**
```
INFO o.a.k.c.c.i.ConsumerCoordinator : Revoke previously assigned partitions
      chat-messages-0, chat-messages-1, ... chat-messages-63
INFO o.a.k.c.c.i.ConsumerCoordinator : (Re-)joining group
INFO o.a.k.c.c.i.ConsumerCoordinator : Successfully joined group with generation 14
INFO o.a.k.c.c.i.ConsumerCoordinator : Notifying assignor about the new Assignment
```
And in k6:
```
fanout_latency_ms: p(99)=6,410ms     (baseline 214ms)
```
```bash
curl -s localhost:8080/actuator/metrics/kafka.consumer.fetch.manager.records.lag.max | jq
```
**Expected — a consumption gap:**
```
rebalance duration: 5.8s
messages not delivered during the gap: 41,204
```

✅ **5.8 seconds of no delivery on *every* node because one pod restarted.**
During a rolling deploy of 8 nodes that's 8 rebalances ≈ **46 seconds** of
degraded delivery.

### Now fix it

```yaml
        partition.assignment.strategy: org.apache.kafka.clients.consumer.CooperativeStickyAssignor
        group.instance.id: node-${pulse.node-id}
        session.timeout.ms: 45000
```

```bash
./code/start_kafka_nodes.sh 8            # with the fixes
sleep 90
docker restart pulse-node-c
```

**Expected:**
```
(no revocation logs on nodes a, b, d-h at all)
node-c: INFO ConsumerCoordinator : Rejoining group with static member id node-c
node-c: INFO ConsumerCoordinator : Resuming from committed offsets
```
```
fanout_latency_ms: p(99)=228ms      (baseline 214ms)
messages not delivered: 0
rebalance duration: 0s (no rebalance occurred)
```

✅ **Zero rebalances, zero delivery gap.** Static membership let node-c reclaim
its own partitions on restart; it returned within `session.timeout.ms` so the
coordinator never declared it dead.

Test the case where it *doesn't* come back:
```bash
docker stop pulse-node-c && sleep 60          # exceeds session.timeout.ms
```
**Expected:**
```
INFO ConsumerCoordinator : Member node-c has left the group
(cooperative rebalance: only node-c's 8 partitions are reassigned)
fanout p99: 241ms       messages not delivered: 0
```
✅ **Cooperative assignment moved only the 8 orphaned partitions.** The other 56
were never revoked.

Record it:
```markdown
## Module 16 — Kafka rebalances

- Eager + no static membership: pod restart = 5.8s cluster-wide delivery gap,
  41,204 messages delayed, p99 214ms -> 6,410ms
- Cooperative + static membership: pod restart = ZERO rebalances, p99 228ms
- Genuine node loss: only that node's partitions move, p99 241ms, 0 lost
```

---

## Part F — Durability

Redis Streams' weak point (Module 09: 57/200 lost on a Redis kill+restart).

```bash
./code/loss_test.sh --backbone kafka
```
```
>>> docker kill pulse-kafka-kafka2-1
>>> docker start pulse-kafka-kafka2-1
published: 200   received: 200   LOST: 0
```
```bash
kt --describe --topic chat-messages | grep 'Isr:' | head -3
```
**Expected — during the outage:**
```
	Topic: chat-messages Partition: 0 Leader: 3 Replicas: 2,3,1 Isr: 3,1
```
Leader moved from broker 2 to broker 3, ISR shrank to 2 — still ≥
`min.insync.replicas`, so writes continued.

Kill two of three:
```bash
docker kill pulse-kafka-kafka2-1 pulse-kafka-kafka3-1
./code/publish.sh room.9 "will this work?"
```
**Expected:**
```
org.apache.kafka.common.errors.NotEnoughReplicasException:
  Messages are rejected since there are fewer in-sync replicas than required.
```
✅ **It refuses the write rather than accepting one it can't make durable.**
That's `min.insync.replicas=2` working exactly as configured, and it's the same
principle as Module 08's `noeviction`: **a loud failure beats silent data loss.**

| | Redis Streams | Redis + outbox (Module 13) | Kafka |
|---|--------------|----------------------------|-------|
| Backbone paused 1.5 s | 0 lost | 0 lost | **0 lost** |
| Backbone killed + restarted | **57/200 lost** | 0 lost (relay republishes) | **0 lost** |
| Two of three brokers lost | n/a | n/a | **writes rejected**, 0 lost |
| Machinery required | — | outbox table + relay + pruning | **none** |

✅ **Kafka gives you for free what the outbox cost us a table, a relay, a pruning
job and 52 ms of p50.** That is a real simplification and a genuine point in
Kafka's favour.

> The counter: the outbox also solves the *dual-write* problem — persisting to
> Postgres and publishing atomically. Kafka's durability doesn't help there; you'd
> still need the outbox, or CDC, or you'd accept the hole. So the machinery
> mostly stays. Worth being precise about.

---

## Part G — Resource cost

```bash
docker stats --no-stream | grep -E 'redis|kafka'
du -sh /var/lib/docker/volumes/pulse-kafka*
```

**Expected at 400,000 outbound msg/s sustained:**

| | Redis Streams | Kafka (3 brokers) |
|---|--------------|-------------------|
| RAM | **1.9 GB** | 4.2 GB |
| CPU | 89% (1 core) | 94% (3 cores) |
| Disk written/hour | **0** | 8.4 GB |
| Disk retained (24 h) | 0 | **201 GB** |
| Network (internal) | 3.1 Gbit/s | 3.4 Gbit/s |
| Containers to operate | **1** | 3 |
| Config surface | ~12 settings | **~40 settings that matter** |

The 201 GB is the one to notice: at 24-hour retention and 3× replication, Kafka
stores **three copies of a day of chat on disk**. Multiply by your retention
policy. It's cheap disk, but it's a capacity plan.

---

## The verdict

**Pulse stays on Redis Streams — but this is the closest call in the course, and
the reasoning is narrow.**

| Dimension | Winner | Margin |
|-----------|--------|--------|
| Latency (p50) | **Redis** | 22 ms vs 28 ms (`linger.ms=0`) |
| Latency (p99.9) | **Kafka** | 740 ms vs 910 ms |
| Scaling to many nodes | **Kafka** | flat to 16+; Redis saturates at ~8 |
| Durability | **Kafka** | 0 lost vs 57/200 without the outbox |
| Replay window | **Kafka** | days vs minutes |
| Additional consumers | **Kafka** | a new group; Redis needs a new consumer group per stream |
| Stream-per-entity | **Redis** | 1M keys free; 1M partitions impossible |
| Operational surface | **Redis** | 1 container vs 3, ~12 settings vs ~40 |
| Resource cost | **Redis** | 1.9 GB vs 4.2 GB, 0 disk vs 201 GB/day |
| **Already in our stack** | **Redis** | presence, rate limits, unread, dedup |

The decision comes down to two facts:

1. **Pulse runs 2–8 nodes.** Redis saturates at ~9. We are inside its envelope,
   with the outbox already covering durability.
2. **Redis is already there.** Kafka would be a second stateful system with a
   larger operational surface, for advantages we don't currently need.

**Flip to Kafka when any of these becomes true:**
- **Node count exceeds ~8** — this is the hard one, and it's the *first* trigger
  you'll hit.
- **A second consumer appears** — search indexing, analytics, moderation, ML.
  Kafka makes this a new consumer group; Redis makes it a new consumer group per
  room stream plus its own PEL, multiplying the amplification.
- **Replay beyond minutes** is required.
- **Someone else in the organization already runs Kafka.**

> Honestly: the second bullet is how most chat systems end up on Kafka. The
> moment "index messages for search" or "feed the moderation model" appears on the
> roadmap, Kafka's fan-out-to-independent-consumers model is simply the right
> shape, and Redis Streams starts fighting you.

---

## What you built

- Pulse's fan-out on a 3-broker KRaft cluster with per-room key ordering.
- A head-to-head benchmark across latency, throughput, and the `linger.ms`
  latency/throughput trade.
- **The scaling crossover measured**: Redis saturates at ~8 nodes; Kafka is flat
  to 16+.
- A rebalance outage reproduced (5.8 s cluster-wide) and eliminated with
  cooperative assignment plus static membership.
- Durability drills, including the `min.insync.replicas` write rejection.
- A decision with a named first trigger for revisiting it.

Now do [`challenge.md`](./challenge.md).

Then: [Module 17 — The Next.js Real-Time Client](../17-nextjs-realtime-client/).
