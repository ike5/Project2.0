#!/usr/bin/env python3
"""Synthetic delivery prober — reference copy of `chat/prober.py`.

SLI 1 is delivery success, and **you cannot count what did not happen.**

The server-side approximation is:

    (chat_delivery_attempts_total - chat_delivery_failures_total)
    / chat_delivery_attempts_total

which counts a `socket.send()` that returned without raising as a success. It
therefore misses every failure after the write:

  - a frame buffered in the OS socket for a client that vanished
  - a frame the ingress dropped during a config reload (Module 19)
  - a `group_expiry` expiry making a live socket deaf (Module 11) -- the socket
    is fine, the membership is gone, and NOTHING raises
  - a channel-layer shard that accepted a PUBLISH and lost it (Module 07's
    docker-pause drill lost ~15% this way with zero errors anywhere)

Every one of those is invisible server-side and obvious to a receiver. So run a
receiver.

Two connections, in one room, deliberately on DIFFERENT nodes -- otherwise you
are testing an in-process dict rather than the backbone. Send a message every
10 s; if the receiver has not seen it in 5 s, count it undelivered.

    python prober.py --host localhost:8080 --room probe --port 9200

It exposes its own /metrics on `--port` so Prometheus scrapes it like anything
else, and it deliberately does NOT run inside an app pod: a prober that dies
with the thing it is monitoring reports perfect health right up until it stops
reporting anything.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import time
import uuid

import websockets
from prometheus_client import Counter, Histogram, start_http_server

PROBE_DELIVERED = Counter("chat_probe_delivered_total", "Probe messages received")
PROBE_UNDELIVERED = Counter(
    "chat_probe_undelivered_total",
    "Probe messages NOT received within the deadline",
)
PROBE_LATE = Counter(
    "chat_probe_late_total",
    "Probe messages that arrived AFTER being counted undelivered",
)
PROBE_LATENCY = Histogram(
    "chat_probe_latency_seconds",
    "send -> receive, end to end, across two nodes",
    buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)
PROBE_CONNECT_FAILURES = Counter(
    "chat_probe_connect_failures_total", "Prober handshake failures", ["side"]
)

DEADLINE_S = 5.0
INTERVAL_S = 10.0


class Prober:
    def __init__(self, sender_url: str, receiver_url: str, room: str) -> None:
        self.sender_url = sender_url
        self.receiver_url = receiver_url
        self.room = room
        self.in_flight: dict[str, float] = {}

    async def run(self) -> None:
        await asyncio.gather(self._receive_loop(), self._send_loop())

    # -- receiver ----------------------------------------------------------
    async def _receive_loop(self) -> None:
        while True:
            try:
                async with websockets.connect(self.receiver_url, ping_interval=20) as ws:
                    async for raw in ws:
                        env = json.loads(raw)
                        if env.get("type") != "message.new":
                            continue
                        body = env.get("data", {}).get("body", "")
                        if not body.startswith("probe:"):
                            continue
                        self._on_receive(body.split(":", 1)[1])
            except Exception as exc:
                PROBE_CONNECT_FAILURES.labels(side="receiver").inc()
                print(f"receiver reconnecting after {type(exc).__name__}: {exc}")
                # Full jitter, same as every other Pulse client (Module 10/17).
                # A prober that hammers a recovering server is a prober that
                # extends the outage it is measuring.
                await asyncio.sleep(1 + os.urandom(1)[0] / 255 * 4)

    def _on_receive(self, probe_id: str) -> None:
        sent_at = self.in_flight.pop(probe_id, None)
        if sent_at is None:
            # Already counted undelivered, then it turned up. This is the
            # distinction the whole prober exists to make: LATE is a latency
            # incident, LOST is a durability incident, and only one of them
            # means you owe someone an explanation about missing messages.
            PROBE_LATE.inc()
            return
        PROBE_DELIVERED.inc()
        PROBE_LATENCY.observe(time.monotonic() - sent_at)

    # -- sender ------------------------------------------------------------
    async def _send_loop(self) -> None:
        while True:
            try:
                async with websockets.connect(self.sender_url, ping_interval=20) as ws:
                    while True:
                        probe_id = uuid.uuid4().hex[:16]
                        self.in_flight[probe_id] = time.monotonic()
                        await ws.send(json.dumps({
                            "v": 1, "type": "message.create",
                            "data": {"client_id": f"probe-{probe_id}",
                                     "body": f"probe:{probe_id}"},
                        }))
                        asyncio.get_running_loop().call_later(
                            DEADLINE_S, self._expire, probe_id)
                        await asyncio.sleep(INTERVAL_S)
            except Exception as exc:
                PROBE_CONNECT_FAILURES.labels(side="sender").inc()
                print(f"sender reconnecting after {type(exc).__name__}: {exc}")
                await asyncio.sleep(1 + os.urandom(1)[0] / 255 * 4)

    def _expire(self, probe_id: str) -> None:
        if self.in_flight.pop(probe_id, None) is not None:
            PROBE_UNDELIVERED.inc()
            # ERROR-level and structured, so the burn-rate alert's runbook can
            # link straight to the line. An undelivered probe is the single
            # highest-signal log line Pulse produces.
            print(json.dumps({"level": "ERROR", "event": "probe_undelivered",
                              "probe_id": probe_id, "room": self.room}))


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--host", default="localhost:8080")
    p.add_argument("--room", default="probe")
    p.add_argument("--port", type=int, default=9200)
    # THE IMPORTANT FLAG. Both sockets must land on different nodes or the probe
    # never crosses the channel layer and reports 100% success during a total
    # backbone outage. In the HA stack, address the nodes directly rather than
    # going through nginx, whose cookie affinity would happily pin both.
    p.add_argument("--sender-node", default=None, help="e.g. localhost:8001")
    p.add_argument("--receiver-node", default=None, help="e.g. localhost:8002")
    args = p.parse_args()

    sender_host = args.sender_node or args.host
    receiver_host = args.receiver_node or args.host
    if sender_host == receiver_host:
        print("WARNING: both probe sockets target the same node. This measures a "
              "process-local dict, not the backbone. Pass --sender-node and "
              "--receiver-node.")

    start_http_server(args.port)
    prober = Prober(
        sender_url=f"ws://{sender_host}/ws/room/{args.room}/?as=probe-sender",
        receiver_url=f"ws://{receiver_host}/ws/room/{args.room}/?as=probe-receiver",
        room=args.room,
    )
    asyncio.run(prober.run())


if __name__ == "__main__":
    main()
