#!/usr/bin/env python3
"""
partitioner_check.py — prove that Python's two Kafka clients disagree about
where a room's messages go, and that the disagreement destroys the one guarantee
you adopted Kafka for.

    python partitioner_check.py

Run it BEFORE you trust `kafka_layer.py`, and run it again after any client
upgrade. It needs a running cluster and a topic named `partitioner-probe`:

    kt --create --topic partitioner-probe --partitions 64 --replication-factor 3

THE FACT
--------
Kafka's ordering guarantee is PER PARTITION. `key -> partition` is computed
CLIENT-SIDE, by the producer, and the clients do not agree on the hash:

    Java producer (DefaultPartitioner)      murmur2
    aiokafka                                murmur2   (Java-compatible)
    confluent-kafka / librdkafka            consistent_random  <-- CRC32

So a room whose messages are produced by both clients lands in two partitions,
and there is no ordering guarantee across them. Symptoms in production:

  * `seq` gaps that the client's gap detector reports and `resume` never fills,
    because the messages ARE delivered -- just late and out of order.
  * A room that is fine for months, until a second service starts producing to
    it with a different client.
  * Reproduces on nothing, because both producers are individually correct.

THE FIX (one line, in your config from the first commit)

    Producer({..., "partitioner": "murmur2_random"})

THE GENERAL LESSON
------------------
When a hash function is part of a wire contract, PIN IT EXPLICITLY. Module 14
said the same thing about `zlib.crc32` versus Python's PYTHONHASHSEED-randomized
`hash()`. A default is not a contract.
"""

from __future__ import annotations

import json
import sys
import time

BOOTSTRAP = "localhost:19092,localhost:19093,localhost:19094"
TOPIC = "partitioner-probe"

# Room.key values -- the composed key, never the bare slug (Module 05).
ROOMS = ["room.7", "room.general", "room.42", "room.random", "room.support"]


def produce_confluent(partitioner: str) -> dict[str, int]:
    from confluent_kafka import Producer

    landed: dict[str, int] = {}

    def on_delivery(err, msg):
        if err:
            print(f"  delivery error: {err}", file=sys.stderr)
            return
        landed[msg.key().decode()] = msg.partition()

    p = Producer({
        "bootstrap.servers": BOOTSTRAP,
        "partitioner": partitioner,
        "acks": "all",
    })
    for room in ROOMS:
        p.produce(TOPIC, key=room.encode(),
                  value=json.dumps({"probe": partitioner}).encode(),
                  on_delivery=on_delivery)
    p.flush(10.0)
    return landed


def produce_aiokafka() -> dict[str, int]:
    import asyncio
    from aiokafka import AIOKafkaProducer

    async def run() -> dict[str, int]:
        landed: dict[str, int] = {}
        p = AIOKafkaProducer(bootstrap_servers=BOOTSTRAP, acks="all")
        await p.start()
        try:
            for room in ROOMS:
                md = await p.send_and_wait(
                    TOPIC, key=room.encode(),
                    value=json.dumps({"probe": "aiokafka"}).encode())
                landed[room] = md.partition
        finally:
            await p.stop()
        return landed

    return asyncio.run(run())


def main() -> None:
    print("Producing the same five room keys with three configurations.\n")

    results = {
        "confluent-kafka DEFAULT (consistent_random / CRC32)":
            produce_confluent("consistent_random"),
        "confluent-kafka partitioner=murmur2_random":
            produce_confluent("murmur2_random"),
        "aiokafka DEFAULT (murmur2, Java-compatible)":
            produce_aiokafka(),
    }
    time.sleep(0.5)

    width = max(len(r) for r in ROOMS) + 2
    header = "room".ljust(width) + "".join(f"{i:>10}" for i in range(len(results)))
    print(header)
    print("-" * len(header))
    for room in ROOMS:
        row = room.ljust(width)
        for landed in results.values():
            row += f"{landed.get(room, -1):>10}"
        print(row)
    print()
    for i, name in enumerate(results):
        print(f"  column {i}: {name}")
    print()

    default_conf = results["confluent-kafka DEFAULT (consistent_random / CRC32)"]
    fixed_conf = results["confluent-kafka partitioner=murmur2_random"]
    aio = results["aiokafka DEFAULT (murmur2, Java-compatible)"]

    disagreements = [r for r in ROOMS if default_conf.get(r) != aio.get(r)]
    agreements = [r for r in ROOMS if fixed_conf.get(r) == aio.get(r)]

    print(f"confluent DEFAULT vs aiokafka:      {len(disagreements)}/{len(ROOMS)} "
          f"rooms land on DIFFERENT partitions")
    print(f"confluent murmur2_random vs aiokafka: {len(agreements)}/{len(ROOMS)} "
          f"rooms agree")
    print()
    if disagreements and len(agreements) == len(ROOMS):
        print("RESULT: the default partitioners disagree; murmur2_random fixes it.")
        print("        Set it explicitly. A default is not a contract.")
    elif not disagreements:
        print("RESULT: no disagreement observed. Your librdkafka version may have")
        print("        changed its default -- which is exactly why you PIN it.")
    sys.exit(0)


if __name__ == "__main__":
    main()
