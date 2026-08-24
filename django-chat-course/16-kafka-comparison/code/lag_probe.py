#!/usr/bin/env python3
"""
lag_probe.py — consumer lag as a Prometheus gauge, and the same number computed
for Redis Streams so the comparison in lab Part C is apples to apples.

    python lag_probe.py --backend kafka  --interval 5
    python lag_probe.py --backend redis  --interval 5
    curl -s localhost:9310/metrics | grep pulse_fanout_lag

WHY LAG IS THE METRIC
---------------------
Every other signal a fan-out emits is a rate or a latency, and both look fine
while you are falling behind: throughput is constant right up until the buffer
is full, and the latency you measure is the latency of messages you actually
delivered. LAG is the only number that says "there are N messages that exist and
you have not delivered yet," which is the thing your users are experiencing.

Kafka gives it to you for free -- LOG-END-OFFSET minus CURRENT-OFFSET, per
partition, from one API call. That is a genuine day-two advantage over Redis
Streams, and it is unglamorous enough that comparisons usually skip it.

Redis Streams can be made to produce the same number, and the cost of doing so
is itself a finding: `XINFO GROUPS` per STREAM, and Pulse has one stream per
ROOM. At 1,000 rooms that is 1,000 round trips per scrape. At a million rooms it
is not a monitoring strategy, it is an outage. The workaround below samples the
busiest N rooms, which is honest but is NOT the same metric -- you are blind to
a cold room that has stalled.
"""

from __future__ import annotations

import argparse
import asyncio
import os

from prometheus_client import Gauge, start_http_server

LAG = Gauge("pulse_fanout_lag", "Undelivered messages behind the tail",
            ["backend", "group", "partition"])
LAG_TOTAL = Gauge("pulse_fanout_lag_total", "Total lag across all partitions",
                  ["backend", "group"])
SCRAPE_COST = Gauge("pulse_fanout_lag_scrape_seconds",
                    "How long computing lag took", ["backend"])

BOOTSTRAP = os.getenv("PULSE_KAFKA", "localhost:19092")
REDIS_URL = os.getenv("PULSE_REDIS", "redis://localhost:6379")


# ---------------------------------------------------------------------------
# Kafka: one AdminClient call, all groups, all partitions.
# ---------------------------------------------------------------------------

async def probe_kafka(groups: list[str]) -> None:
    from aiokafka.admin import AIOKafkaAdminClient
    from aiokafka import AIOKafkaConsumer, TopicPartition

    admin = AIOKafkaAdminClient(bootstrap_servers=BOOTSTRAP)
    await admin.start()
    # A consumer purely to read end offsets. It joins NO group -- passing a
    # group_id here would make the probe a member and trigger a rebalance every
    # scrape, which is a monitoring tool causing the outage it monitors.
    reader = AIOKafkaConsumer(bootstrap_servers=BOOTSTRAP)
    await reader.start()
    try:
        while True:
            t0 = asyncio.get_running_loop().time()
            for group in groups:
                committed = await admin.list_consumer_group_offsets(group)
                if not committed:
                    continue
                tps = list(committed)
                ends = await reader.end_offsets(tps)
                total = 0
                for tp in tps:
                    off = committed[tp].offset
                    lag = max(0, ends[tp] - off)
                    total += lag
                    LAG.labels("kafka", group, str(tp.partition)).set(lag)
                LAG_TOTAL.labels("kafka", group).set(total)
            SCRAPE_COST.labels("kafka").set(
                asyncio.get_running_loop().time() - t0)
            await asyncio.sleep(INTERVAL)
    finally:
        await reader.stop()
        await admin.close()


# ---------------------------------------------------------------------------
# Redis Streams: per-STREAM, which is per-ROOM, which is the problem.
# ---------------------------------------------------------------------------

async def probe_redis(top_n: int) -> None:
    import redis.asyncio as aioredis

    r = aioredis.from_url(REDIS_URL, decode_responses=True)
    try:
        while True:
            t0 = asyncio.get_running_loop().time()

            # SAMPLING, not measuring. Pulse tracks the busiest rooms in a
            # sorted set (Module 11's viewport work maintains it); we scrape
            # those. A COLD room whose consumer has stalled is invisible here,
            # and that is a real blind spot you must write down rather than
            # paper over.
            rooms = await r.zrevrange("pulse:rooms:busiest", 0, top_n - 1)

            total = 0
            for room in rooms:
                key = f"room:{{{room}}}:stream"      # hash tag colocates the
                                                    # room's keys on one slot
                length = await r.xlen(key)
                for g in await r.xinfo_groups(key):
                    # `entries-read` exists from Redis 7.0 and is the closest
                    # thing to a Kafka offset. `lag` is reported directly by
                    # 7.0+ and is None when Redis cannot determine it (after a
                    # trim that removed un-read entries) -- which is a real
                    # difference from Kafka, where the offset is always
                    # meaningful.
                    lag = g.get("lag")
                    if lag is None:
                        lag = max(0, length - (g.get("entries-read") or 0))
                    total += lag
                    LAG.labels("redis", g["name"], room).set(lag)
            LAG_TOTAL.labels("redis", "all").set(total)
            SCRAPE_COST.labels("redis").set(
                asyncio.get_running_loop().time() - t0)
            await asyncio.sleep(INTERVAL)
    finally:
        await r.aclose()


INTERVAL = 5.0


def main() -> None:
    global INTERVAL
    ap = argparse.ArgumentParser()
    ap.add_argument("--backend", choices=["kafka", "redis"], required=True)
    ap.add_argument("--interval", type=float, default=5.0)
    ap.add_argument("--port", type=int, default=9310)
    ap.add_argument("--groups", default="",
                    help="kafka: comma-separated group ids to probe")
    ap.add_argument("--top", type=int, default=100,
                    help="redis: how many of the busiest rooms to sample")
    a = ap.parse_args()
    INTERVAL = a.interval

    start_http_server(a.port)
    print(f"lag probe on :{a.port}/metrics  backend={a.backend}")

    if a.backend == "kafka":
        groups = [g for g in a.groups.split(",") if g] or [
            f"pulse-node-{n}-{w}" for n in "abc" for w in range(8)
        ]
        asyncio.run(probe_kafka(groups))
    else:
        asyncio.run(probe_redis(a.top))


if __name__ == "__main__":
    main()
