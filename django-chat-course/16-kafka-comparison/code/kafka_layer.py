"""
apps/pulse/chat/kafka_layer.py — Pulse's fan-out on Kafka instead of Redis
Streams, as a drop-in replacement for Module 09's `chat/layers.py`.

    pip install aiokafka confluent-kafka

TOPOLOGY A: ONE CONSUMER GROUP PER WORKER PROCESS
-------------------------------------------------
Module 09 established that Pulse's unit of consumption is the WORKER PROCESS,
not the machine, because one async worker pins one core and the
InMemoryChannelLayer does not span processes. That fact, carried onto Kafka:

    3 nodes x 8 Uvicorn workers = 24 consumer groups
    24 groups x 64 partitions   = 1,536 partition assignments
    every entry is read and committed 24 times

24x read amplification -- the same shape Module 09 measured for Streams, with a
crucial difference: Redis pays CPU on ONE thread for every read, while Kafka
serves 24 consumers reading the same recent offsets out of the page cache with
sendfile. That is why the curves cross (lab Part D).

The quiet bonus: a consumer group with exactly ONE member never rebalances.
There is nothing to reassign. Kafka's most notorious operational problem simply
does not occur in Topology A. Topology B (`FanoutTierConsumer` at the bottom of
this file) is 1x read amplification and does rebalance, and lab Part E measures
what that costs.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import socket
from typing import Awaitable, Callable

from aiokafka import AIOKafkaConsumer, TopicPartition
from aiokafka.coordinator.assignors.sticky.sticky_assignor import (
    StickyPartitionAssignor,
)
from confluent_kafka import Producer

log = logging.getLogger("pulse.kafka")

TOPIC = "chat-messages"
BOOTSTRAP = os.getenv("PULSE_KAFKA", "localhost:19092,localhost:19093,localhost:19094")

# ONE identity per worker process, reused rather than reinvented. The same
# PULSE_WORKER_ID feeds Module 12's Snowflake worker-id bits and Module 14's
# fleet-fencing key. It MUST be stable across restarts: static membership
# (group.instance.id) is the whole rebalance mitigation, and a value derived
# from a PID or a UUID changes on restart and silently does nothing.
WORKER = f"{socket.gethostname()}-{os.getenv('PULSE_WORKER_ID', '0')}"


# ===========================================================================
# PRODUCER — confluent-kafka (librdkafka, C), driven from a thread
# ===========================================================================

def build_producer() -> Producer:
    return Producer({
        "bootstrap.servers": BOOTSTRAP,
        "client.id": WORKER,

        # ------------------------------------------------------------------
        # THE ONE LINE THAT IS A CORRECTNESS BUG IF YOU OMIT IT.
        #
        # librdkafka's default partitioner is `consistent_random` (CRC32).
        # The Java producer's default -- and aiokafka's -- is murmur2. Two
        # producers, the same room key, DIFFERENT partitions. Kafka's ordering
        # guarantee is per PARTITION, so a room produced by both clients has no
        # ordering guarantee at all: the single thing you adopted Kafka for.
        #
        # Verify with code/partitioner_check.py before you trust this file.
        # ------------------------------------------------------------------
        "partitioner": "murmur2_random",

        # acks=all + min.insync.replicas=2 (set on the topic) is the PAIR that
        # means durability. acks=all alone waits for the in-sync SET, which can
        # be one replica.
        "acks": "all",
        "enable.idempotence": True,      # dedups producer retries within Kafka
        "max.in.flight.requests.per.connection": 5,   # max with idempotence on

        # linger.ms trades latency for batching. Part C sweeps it; 5 ms is the
        # measured knee for Pulse's fan-out, where a message already costs
        # ~20 ms end to end and 5 ms of batching buys 21% more throughput.
        "linger.ms": 5,
        "batch.size": 65536,
        "compression.type": "lz4",       # zstd compresses better and costs CPU
                                         # Pulse does not have (Module 01)
        "queue.buffering.max.messages": 500_000,
    })


class ThreadedProducer:
    """
    confluent-kafka's Producer is a C client whose `poll()` must be called to
    fire delivery callbacks -- and `poll()` BLOCKS. Calling it from an async
    consumer blocks the event loop and stalls every connection that worker
    holds: Module 15's cardinal sin, reached through a Kafka client.

    `produce()` itself is non-blocking (it enqueues into librdkafka's internal
    queue, which has its own background threads), so the only thing that needs
    a thread is the poll loop. One thread, per process, for the life of the
    process. NOT a threadpool task -- Module 14 showed what borrowing from
    asgiref's bounded pool does to the send path.
    """

    def __init__(self) -> None:
        self._p = build_producer()
        self._stop = asyncio.Event()
        self._task: asyncio.Task | None = None

    async def start(self) -> None:
        self._task = asyncio.create_task(self._poll_forever())

    async def _poll_forever(self) -> None:
        loop = asyncio.get_running_loop()
        while not self._stop.is_set():
            # 0 = "fire whatever callbacks are ready, then return". Run it in a
            # thread anyway: even with timeout 0 it takes the librdkafka lock.
            await loop.run_in_executor(None, self._p.poll, 0)
            await asyncio.sleep(0.005)

    def publish(self, room_key: str, envelope: dict) -> None:
        """
        Fire and forget onto the partition that owns this room.

        `key=room_key` is what preserves per-room ordering: same key -> same
        partition -> one log -> Kafka's ordering guarantee applies. The key is
        Room.key ("room.7"), the SAME string that is the channel-layer group
        name, the `room` field in the envelope, and the `room_id` column in the
        store. One string, four jobs now.
        """
        self._p.produce(
            TOPIC,
            key=room_key.encode(),
            value=json.dumps(envelope, separators=(",", ":")).encode(),
            on_delivery=self._on_delivery,
        )

    @staticmethod
    def _on_delivery(err, msg) -> None:
        if err is not None:
            # A delivery failure here is the dual-write hole from Module 13,
            # unchanged: the message is in Postgres and will never be
            # delivered. The outbox relay is what catches it -- and note that
            # adopting Kafka does NOT let you delete the outbox unless you also
            # make Kafka the durable record.
            log.error("kafka delivery failed: %s", err)
            from .metrics import fanout_publish_failures
            fanout_publish_failures.inc()

    async def stop(self) -> None:
        self._stop.set()
        if self._task:
            await self._task
        # flush() blocks; do it in a thread, and give it a real timeout. A
        # SIGTERM handler that calls flush() on the event loop is how a graceful
        # drain (Module 18) becomes a 30-second hang.
        await asyncio.get_running_loop().run_in_executor(None, self._p.flush, 10.0)


# ===========================================================================
# CONSUMER — aiokafka, native asyncio, one group per worker process
# ===========================================================================

Handler = Callable[[dict], Awaitable[None]]


class WorkerGroupConsumer:
    """
    Topology A. This worker process gets its own consumer group, so it receives
    EVERY message in the topic and delivers to whichever of its local sockets
    care. Exactly Module 09's Option B, in Kafka's vocabulary.

    aiokafka rather than confluent-kafka here, deliberately: this loop lives
    inside the event loop that owns the WebSocket connections, and a blocking
    poll would stall them. The cost is pure-Python decode per message, which is
    the same per-message Python tax Module 06 identified as the reason Pulse's
    fan-out knee is ~150k out msg/s against the JVM twin's ~450k.
    """

    def __init__(self, handler: Handler) -> None:
        self.handler = handler
        self.consumer: AIOKafkaConsumer | None = None
        self._task: asyncio.Task | None = None

    async def start(self) -> None:
        self.consumer = AIOKafkaConsumer(
            TOPIC,
            bootstrap_servers=BOOTSTRAP,
            # ONE GROUP PER WORKER PROCESS. This is the whole topology.
            group_id=f"pulse-{WORKER}",
            client_id=WORKER,

            # AT-LEAST-ONCE. Commit AFTER processing, never before. Module 10's
            # table, unchanged: ack-before-process is at-most-once and loses on
            # a crash; ack-after-process duplicates on a crash. Chat prefers
            # duplicates, because a duplicate is removable and a hole is not --
            # and Module 05's client_id makes the duplicate free.
            enable_auto_commit=False,

            # Where a BRAND NEW group starts. `latest`, not `earliest`: a worker
            # process that has never run before must NOT replay 24 hours of
            # history to sockets that were not connected for it. Resume from a
            # client's cursor is the mechanism for catching a client up
            # (Module 10, protocol §3.5); the fan-out log is not.
            auto_offset_reset="latest",

            max_poll_records=500,
            # Long, because "processing" includes a Postgres write. A consumer
            # that exceeds max_poll_interval_ms is declared DEAD and its
            # partitions are reassigned -- which in Topology A means to nobody,
            # since the group has one member, and the symptom is a worker that
            # silently stops receiving.
            max_poll_interval_ms=300_000,
            session_timeout_ms=45_000,
            heartbeat_interval_ms=3_000,

            value_deserializer=lambda b: json.loads(b),
            key_deserializer=lambda b: b.decode() if b else None,
        )
        await self.consumer.start()
        self._task = asyncio.create_task(self._consume_forever())
        log.info("kafka consumer started: group=pulse-%s", WORKER)

    async def _consume_forever(self) -> None:
        assert self.consumer
        while True:
            batches = await self.consumer.getmany(timeout_ms=200)
            if not batches:
                continue
            for tp, records in batches.items():
                for record in records:
                    try:
                        await self.handler(record.value)
                    except Exception:
                        # A poison message that raises on every attempt would
                        # block this partition forever if we did not commit
                        # past it. Log it, count it, move on -- and accept the
                        # permanent gap, which Module 10's `to_seq` in
                        # resume.batch is designed to step a client over.
                        log.exception("handler failed at %s:%s offset %s",
                                      tp.topic, tp.partition, record.offset)
                        from .metrics import fanout_poison
                        fanout_poison.inc()
            # ONE commit per batch, after processing. Committing per record
            # multiplies __consumer_offsets traffic by 500 and buys nothing:
            # the redelivery window shrinks from one batch to one record, and
            # the consumer is idempotent either way.
            await self.consumer.commit()

    async def lag(self) -> dict[int, int]:
        """
        Consumer lag, per partition. THE metric Redis Streams cannot give you
        cheaply: XPENDING reports un-acked entries, not distance from the tail,
        and computing real lag from XINFO GROUPS is one round trip per ROOM --
        a million of them at Pulse's room count.
        """
        assert self.consumer
        assigned = self.consumer.assignment()
        end = await self.consumer.end_offsets(list(assigned))
        return {
            tp.partition: end[tp] - (await self.consumer.position(tp))
            for tp in assigned
        }

    async def stop(self) -> None:
        if self._task:
            self._task.cancel()
        if self.consumer:
            await self.consumer.stop()


# ===========================================================================
# TOPOLOGY B — one shared group, 24 consumers over 64 partitions
# ===========================================================================

class FanoutTierConsumer(WorkerGroupConsumer):
    """
    1x read amplification instead of 24x. Each consumer owns 2-3 partitions and
    then RE-FANS-OUT over the channel layer to whichever worker processes hold
    the sockets for those rooms.

    Three things this costs, and the lab measures all three:

    1. AN EXTRA HOP. Kafka -> consumer -> channel layer -> socket, instead of
       Kafka -> socket. Measured at +7 ms p50 in Part C.
    2. REBALANCES. Twenty-four members in one group means every deploy, every
       restart, every slow consumer triggers a reassignment. Part E measures a
       3.8 s cluster-wide consumption gap under the eager protocol, 0.4 s under
       cooperative, and ZERO with static membership -- provided the consumer
       returns within session_timeout_ms.
    3. HEAD-OF-LINE BLOCKING GETS WORSE. In Topology A a slow worker delays only
       its own sockets. Here it delays every room in its 2-3 partitions -- which
       at 64 partitions and a million rooms is ~47,000 rooms.

    Use it when read bandwidth is the binding constraint (Part D's crossover),
    not by default.
    """

    async def start(self) -> None:
        self.consumer = AIOKafkaConsumer(
            TOPIC,
            bootstrap_servers=BOOTSTRAP,
            group_id="pulse-fanout",                # ONE group, shared
            client_id=WORKER,

            # STATIC MEMBERSHIP. A restarting consumer reclaims ITS OWN
            # partitions with no rebalance at all, as long as it comes back
            # within session_timeout_ms. Must be unique per worker PROCESS and
            # stable across restarts -- hence WORKER, not a PID.
            group_instance_id=f"pulse-{WORKER}",

            # Cooperative/sticky: revoke only the partitions that must move.
            # Under the default eager protocol EVERY consumer revokes EVERY
            # partition on every rebalance, and consumption stops cluster-wide.
            partition_assignment_strategy=[StickyPartitionAssignor],

            enable_auto_commit=False,
            auto_offset_reset="latest",
            max_poll_records=500,
            max_poll_interval_ms=300_000,
            session_timeout_ms=45_000,
            value_deserializer=lambda b: json.loads(b),
            key_deserializer=lambda b: b.decode() if b else None,
        )
        await self.consumer.start()
        self._task = asyncio.create_task(self._consume_forever())
        log.info("kafka fan-out tier started: group=pulse-fanout instance=%s", WORKER)


# ===========================================================================
# Wiring, for the ASGI lifespan hook (Module 18 owns lifespan properly)
# ===========================================================================

async def start_kafka_backbone(deliver_local: Handler) -> tuple:
    producer = ThreadedProducer()
    await producer.start()
    consumer = (
        FanoutTierConsumer(deliver_local)
        if os.getenv("PULSE_KAFKA_TOPOLOGY") == "B"
        else WorkerGroupConsumer(deliver_local)
    )
    await consumer.start()
    return producer, consumer
