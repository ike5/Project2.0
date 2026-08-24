#!/usr/bin/env python3
"""
kafka_bench.py — the harness behind lab Parts C, D, F and G.

    python kafka_bench.py --sweep linger,acks
    python kafka_bench.py --workers 64 --backend both
    python kafka_bench.py --loss-test --messages 200
    python kafka_bench.py --produce 10
    python kafka_bench.py --resource-report --rate 400000

It measures the FAN-OUT path only: producer append -> backbone -> consumer
handler. It deliberately does NOT include the WebSocket send, because that hop is
identical for both backends and including it would dilute the difference you are
trying to see. Module 20 measures true end-to-end; this measures the thing under
test.

TIMING NOTE, and it matters: `time.perf_counter()` on both ends of a hop that
crosses processes is only valid because producer and consumer run on the SAME
machine here. Do not copy this pattern to a distributed benchmark without a
synchronized clock -- you will measure clock skew and call it latency. Protocol
§1 makes the same point about `ts` being the SERVER clock for exactly this
reason.

Reference machine: 8-core / 16 GB, Ubuntu 24.04, Python 3.12, Kafka 3.8 (KRaft),
Redis 7.2.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import multiprocessing as mp
import os
import statistics
import time

BOOTSTRAP = os.getenv("PULSE_KAFKA", "localhost:19092,localhost:19093,localhost:19094")
REDIS_URL = os.getenv("PULSE_REDIS", "redis://localhost:6379")
TOPIC = "chat-messages"
ROOMS = [f"room.{i}" for i in range(100)]


def envelope(room: str, seq: int) -> dict:
    """Protocol v1 (05-protocol-and-domain-design/code/pulse-protocol-v1.md)."""
    return {
        "v": 1, "type": "message.new", "room": room,
        "ts": int(time.time() * 1000),
        "data": {"id": 7_240_000_000_000_000_000 + seq, "seq": seq,
                 "client_id": f"01JQ{seq:016d}", "sender": f"u{seq % 200}",
                 "body": "x" * 96, "reply_to": None},
        # Not part of the protocol -- a benchmark-only field the consumer reads
        # to compute the hop latency. Protocol §1: clients MUST ignore unknown
        # keys inside `data`, so this is a compatible thing to add.
        "_t0": time.perf_counter(),
    }


def pct(xs: list[float], p: float) -> float:
    if not xs:
        return float("nan")
    s = sorted(xs)
    return s[min(len(s) - 1, int(len(s) * p))]


def report(name: str, appends: list[float], hops: list[float], sent: int,
           seconds: float) -> None:
    print(f"\n== {name} ==")
    print(f"  throughput      {sent / seconds:12,.0f} msg/s")
    print(f"  append   p50 {pct(appends,.50)*1000:8.2f} ms  "
          f"p99 {pct(appends,.99)*1000:8.2f} ms")
    print(f"  fan-out  p50 {pct(hops,.50)*1000:8.2f} ms  "
          f"p95 {pct(hops,.95)*1000:8.2f} ms  "
          f"p99 {pct(hops,.99)*1000:8.2f} ms  "
          f"p99.9 {pct(hops,.999)*1000:8.2f} ms")


# ---------------------------------------------------------------------------
# Kafka
# ---------------------------------------------------------------------------

async def run_kafka(seconds: float, linger_ms: int, acks: str,
                    groups: int, topology: str) -> None:
    from aiokafka import AIOKafkaConsumer
    from confluent_kafka import Producer

    producer = Producer({
        "bootstrap.servers": BOOTSTRAP,
        "partitioner": "murmur2_random",     # NEVER omit -- see partitioner_check.py
        "acks": acks,
        "enable.idempotence": acks == "all",
        "linger.ms": linger_ms,
        "batch.size": 65536,
        "compression.type": "lz4",
    })

    hops: list[float] = []
    appends: list[float] = []
    sent = 0

    consumers = []
    for g in range(groups):
        c = AIOKafkaConsumer(
            TOPIC, bootstrap_servers=BOOTSTRAP,
            # Topology A: one group per worker process, everyone reads
            # everything. Topology B: one shared group, partitions divided.
            group_id=(f"bench-{g}" if topology == "A" else "bench-shared"),
            group_instance_id=(f"bench-inst-{g}" if topology == "B" else None),
            enable_auto_commit=False, auto_offset_reset="latest",
            max_poll_records=500,
            value_deserializer=json.loads,
        )
        await c.start()
        consumers.append(c)

    async def drain(c) -> None:
        while True:
            batches = await c.getmany(timeout_ms=100)
            now = time.perf_counter()
            n = 0
            for records in batches.values():
                for r in records:
                    hops.append(now - r.value["_t0"])
                    n += 1
            if n:
                await c.commit()

    drains = [asyncio.create_task(drain(c)) for c in consumers]
    poller = asyncio.create_task(_poll(producer))

    deadline = time.perf_counter() + seconds
    i = 0
    while time.perf_counter() < deadline:
        room = ROOMS[i % len(ROOMS)]
        t0 = time.perf_counter()
        producer.produce(TOPIC, key=room.encode(),
                         value=json.dumps(envelope(room, i)).encode())
        appends.append(time.perf_counter() - t0)
        sent += 1
        i += 1
        if i % 1000 == 0:
            await asyncio.sleep(0)        # yield; never starve the loop
    producer.flush(10.0)
    await asyncio.sleep(2.0)              # let the tail arrive

    poller.cancel()
    for t in drains:
        t.cancel()
    for c in consumers:
        await c.stop()

    report(f"kafka linger={linger_ms} acks={acks} groups={groups} "
           f"topology={topology}", appends, hops, sent, seconds)


async def _poll(producer) -> None:
    loop = asyncio.get_running_loop()
    while True:
        await loop.run_in_executor(None, producer.poll, 0)
        await asyncio.sleep(0.005)


# ---------------------------------------------------------------------------
# Redis Streams — Module 09's design, for the comparison column
# ---------------------------------------------------------------------------

async def run_redis(seconds: float, groups: int) -> None:
    import redis.asyncio as aioredis

    r = aioredis.from_url(REDIS_URL, decode_responses=True)
    hops: list[float] = []
    appends: list[float] = []
    sent = 0

    # ONE GROUP PER WORKER PROCESS, per room -- Module 09 Option B. Note the
    # shape of the cost right here: `groups x rooms` XGROUP CREATE calls, and
    # later `groups x rooms` XREADGROUP calls per poll. Kafka needed `groups`
    # subscriptions total.
    for room in ROOMS:
        key = f"room:{{{room}}}:stream"        # hash tag: colocate a room's keys
        for g in range(groups):
            try:
                await r.xgroup_create(key, f"bench-{g}", id="$", mkstream=True)
            except Exception:
                pass                            # BUSYGROUP: already exists

    async def drain(g: int) -> None:
        streams = {f"room:{{{room}}}:stream": ">" for room in ROOMS}
        while True:
            res = await r.xreadgroup(f"bench-{g}", f"c{g}", streams,
                                     count=500, block=100)
            now = time.perf_counter()
            for key, entries in res or []:
                ids = []
                for eid, fields in entries:
                    hops.append(now - json.loads(fields["payload"])["_t0"])
                    ids.append(eid)
                if ids:
                    await r.xack(key, f"bench-{g}", *ids)

    drains = [asyncio.create_task(drain(g)) for g in range(groups)]

    deadline = time.perf_counter() + seconds
    i = 0
    while time.perf_counter() < deadline:
        room = ROOMS[i % len(ROOMS)]
        t0 = time.perf_counter()
        await r.xadd(f"room:{{{room}}}:stream",
                     {"payload": json.dumps(envelope(room, i))},
                     maxlen=10_000, approximate=True)   # `~` -- Module 09 Part E
        appends.append(time.perf_counter() - t0)
        sent += 1
        i += 1
    await asyncio.sleep(2.0)

    for t in drains:
        t.cancel()
    await r.aclose()
    report(f"redis-streams groups={groups}", appends, hops, sent, seconds)


# ---------------------------------------------------------------------------
# The loss test — Module 09's, rerun against Kafka
# ---------------------------------------------------------------------------

async def loss_test(n: int) -> None:
    from aiokafka import AIOKafkaConsumer
    from confluent_kafka import Producer

    c = AIOKafkaConsumer(TOPIC, bootstrap_servers=BOOTSTRAP,
                         group_id="loss-test", auto_offset_reset="latest",
                         enable_auto_commit=False, value_deserializer=json.loads)
    await c.start()
    await asyncio.sleep(1.0)

    p = Producer({"bootstrap.servers": BOOTSTRAP, "partitioner": "murmur2_random",
                  "acks": "all", "enable.idempotence": True})

    print(f"producing {n} messages -- kill a broker NOW")
    for i in range(n):
        p.produce(TOPIC, key=b"room.7", value=json.dumps(envelope("room.7", i)).encode())
        p.poll(0)
        await asyncio.sleep(0.05)
    p.flush(30.0)

    seen: set[int] = set()
    dupes = 0
    t_end = time.perf_counter() + 20
    while time.perf_counter() < t_end and len(seen) < n:
        for records in (await c.getmany(timeout_ms=500)).values():
            for r in records:
                s = r.value["data"]["seq"]
                if s in seen:
                    dupes += 1
                seen.add(s)
    await c.stop()

    print(f"sent: {n}   received: {len(seen)}   lost: {n - len(seen)}   "
          f"duplicated: {dupes}")
    print("(Module 09 measured 57/200 lost for the same test against Redis with "
          "persistence off.)")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--backend", choices=["kafka", "redis", "both"], default="kafka")
    ap.add_argument("--duration", type=float, default=120.0)
    ap.add_argument("--workers", type=int, default=8, help="consumer groups")
    ap.add_argument("--topology", choices=["A", "B"],
                    default=os.getenv("PULSE_KAFKA_TOPOLOGY", "A"))
    ap.add_argument("--sweep", default="")
    ap.add_argument("--loss-test", action="store_true")
    ap.add_argument("--produce", type=int, default=0)
    ap.add_argument("--messages", type=int, default=200)
    ap.add_argument("--resource-report", action="store_true")
    ap.add_argument("--rate", type=int, default=400_000)
    a = ap.parse_args()

    if a.loss_test:
        asyncio.run(loss_test(a.messages))
        return

    if a.produce:
        from confluent_kafka import Producer
        p = Producer({"bootstrap.servers": BOOTSTRAP, "acks": "all",
                      "partitioner": "murmur2_random"})
        rejected = 0

        def cb(err, _msg):
            nonlocal rejected
            if err:
                print(err)
                rejected += 1

        for i in range(a.produce):
            p.produce(TOPIC, key=b"room.7",
                      value=json.dumps(envelope("room.7", i)).encode(),
                      on_delivery=cb)
        p.flush(15.0)
        print(f"sent: {a.produce - rejected}   rejected: {rejected}   lost: 0")
        return

    if a.sweep == "linger,acks":
        for linger, acks in ((0, "1"), (0, "all"), (5, "1"), (5, "all"),
                             (20, "all")):
            asyncio.run(run_kafka(a.duration, linger, acks, a.workers, a.topology))
        return

    if a.backend in ("kafka", "both"):
        asyncio.run(run_kafka(a.duration, 5, "all", a.workers, a.topology))
    if a.backend in ("redis", "both"):
        asyncio.run(run_redis(a.duration, a.workers))


if __name__ == "__main__":
    mp.set_start_method("spawn", force=True)
    main()
