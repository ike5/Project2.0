#!/usr/bin/env python3
"""Pulse server-side instrumentation — the reference copy of `chat/metrics.py`.

Django's HTTP metrics come from `django-prometheus`, but the WebSocket path is
invisible to it: WSGI-era middleware never runs on an ASGI `websocket` scope.
So the six numbers that predict a chat server's death are built here by hand.

Design rules this file exists to enforce:

1. **Histograms, not client-computed percentiles.** A `Histogram` ships bucket
   counts, which aggregate correctly across workers and nodes. A gauge holding
   "my p99" does not: the p99 of eight workers is NOT the mean of eight p99s.
   Getting this wrong makes every dashboard from Module 07 onward quietly wrong.

2. **One `worker` label, low cardinality.** Never label by room, user, or
   channel name. 100,000 rooms x 12 buckets is a Prometheus outage
   (Module 20 measures the cardinality bill).

3. **The event-loop lag probe is the leading indicator.** One async worker is
   one core; when that core falls behind, `asyncio.sleep(0.25)` starts
   returning late, and it starts returning late *before* p99 moves. Everything
   else in this file is a lagging indicator by comparison.

Multi-worker note: with `uvicorn --workers N` every worker is a separate
process with its own registry, and `/metrics` hits whichever worker the kernel
picked. Set PROMETHEUS_MULTIPROC_DIR before importing this module and the
collector merges them; Module 07 does exactly that. With `--workers 1`
(Modules 05-06) it does not matter.

Usage inside the app:

    from chat.metrics import (CONNS, GROUP_SEND, LOOP_LAG, MESSAGES_IN,
                              MESSAGES_OUT, WORKER, start_lag_probe)
"""

from __future__ import annotations

import asyncio
import os

from prometheus_client import CollectorRegistry, Counter, Gauge, Histogram, multiprocess

# The worker's identity. os.getpid() is stable for the life of the process and
# is what `chat/views.py:layer_debug` already reports, so the two agree.
WORKER = os.environ.get("PULSE_WORKER") or f"pid-{os.getpid()}"

# ---------------------------------------------------------------------------
# The six metrics, in the order you look at them during an incident.
# ---------------------------------------------------------------------------

# The leading indicator. Sustained lag above ~10 ms means this worker's single
# core cannot drain its callback queue: you are at or past the knee.
LOOP_LAG = Gauge(
    "chat_event_loop_lag_seconds",
    "How late the event loop woke a timer that asked for a fixed delay",
    ["worker"],
    multiprocess_mode="livemax",
)

# The denominator for everything. Divide RSS by it for bytes/connection.
CONNS = Gauge(
    "chat_connections_active",
    "Open WebSocket connections held by this worker",
    ["worker"],
    multiprocess_mode="livesum",
)

# The ENQUEUE half of latency: how long group_send() took to hand the fan-out
# to the channel layer. This is NOT end-to-end delivery latency -- the load
# generator measures that, because only a receiver knows when it received.
# Explicit buckets, in seconds, spanning "in-process dict write" (1 ms) to
# "something is badly wrong" (5 s).
GROUP_SEND = Histogram(
    "chat_group_send_seconds",
    "Time for group_send() to enqueue a fan-out onto the channel layer",
    buckets=(0.001, 0.002, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5),
)

MESSAGES_IN = Counter(
    "chat_messages_inbound_total",
    "Frames of type message.create accepted from clients",
)

# Incremented by the ROOM SIZE on every fan-out, not by one. rate() of this
# divided by rate() of the inbound counter IS your amplification factor, live.
MESSAGES_OUT = Counter(
    "chat_messages_outbound_total",
    "Individual socket deliveries produced by fan-out",
)

# Failure mode #5: the slow consumer. Uvicorn/websockets buffers frames the
# client has not drained; nothing applies backpressure to your consumer.
SEND_BUFFER = Gauge(
    "chat_send_buffer_bytes_max",
    "Largest per-connection unflushed write buffer seen on this worker",
    ["worker"],
    multiprocess_mode="livemax",
)


# ---------------------------------------------------------------------------
# The event-loop lag probe
# ---------------------------------------------------------------------------
async def _lag_probe(interval: float = 0.25) -> None:
    """Ask the loop to wake us in `interval`; record how late it actually did.

    `loop.time()` is a monotonic clock, so this is immune to NTP steps. The
    number it produces is the queueing delay of the loop's callback queue --
    exactly the `rho/(1-rho)` term from the README's queueing-theory sidebar,
    measured directly instead of inferred.
    """
    loop = asyncio.get_running_loop()
    gauge = LOOP_LAG.labels(worker=WORKER)
    while True:
        t0 = loop.time()
        await asyncio.sleep(interval)
        gauge.set(max(0.0, loop.time() - t0 - interval))


_probe_task: asyncio.Task | None = None


def start_lag_probe(interval: float = 0.25) -> None:
    """Idempotent. Safe to call from the first consumer's connect()."""
    global _probe_task
    if _probe_task is None or _probe_task.done():
        _probe_task = asyncio.ensure_future(_lag_probe(interval))


# ---------------------------------------------------------------------------
# Exposition
# ---------------------------------------------------------------------------
def registry() -> CollectorRegistry:
    """Return the registry `/metrics` should render.

    With PROMETHEUS_MULTIPROC_DIR set, build a fresh registry and let
    MultiProcessCollector merge every worker's mmap files. Without it, the
    default process-local registry is correct and cheaper.
    """
    if "PROMETHEUS_MULTIPROC_DIR" in os.environ:
        reg = CollectorRegistry()
        multiprocess.MultiProcessCollector(reg)
        return reg
    from prometheus_client import REGISTRY

    return REGISTRY


if __name__ == "__main__":
    # Smoke test: run the probe against a deliberately blocked loop and show
    # that the gauge sees the block. This is the whole module in six lines.
    import time

    async def main() -> None:
        start_lag_probe(0.05)
        await asyncio.sleep(0.3)
        print(f"idle loop lag      : {LOOP_LAG.labels(worker=WORKER)._value.get():.4f} s")
        time.sleep(0.8)  # the cardinal sin, on purpose
        await asyncio.sleep(0.3)
        print(f"after a 0.8 s block: {LOOP_LAG.labels(worker=WORKER)._value.get():.4f} s")

    asyncio.run(main())
