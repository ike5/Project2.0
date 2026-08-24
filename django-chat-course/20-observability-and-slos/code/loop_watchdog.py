#!/usr/bin/env python3
"""Event-loop stall detection — reference copy of `chat/loop_watchdog.py`.

Module 15 proved that ONE synchronous ORM call in an async consumer takes p99
from 61 ms to 9,340 ms **for every connection that worker holds**. This file
makes that failure visible in three places at once:

  1. a gauge   -- how bad is the worst stall right now
  2. a counter -- what FRACTION of wall-clock time this worker has lost
  3. a span    -- so the stall appears in Tempo next to the messages it delayed

Number 3 is the interesting one, and the reason is structural:

    THE VICTIM'S TRACE NEVER CONTAINS THE CULPRIT.

Alice's message is slow. Open its trace: every span in it is fast, and there is
a nine-second GAP between the parent starting and the first child starting. The
work that consumed those nine seconds belonged to a different connection, in a
different trace, possibly in a different room. The two share nothing except an
event loop.

So you correlate by WORKER and TIME. Every span carries `pulse.worker`
(chat/tracing.py); this file emits a span for the stall itself; and the query
that answers "why was Alice's message slow" becomes one TraceQL line:

    { name = "asyncio.loop_stall" && span.pulse.worker = "pid-10" }

with the time range set to Alice's gap.

WHY NOT asyncio's own debug mode:

    loop.set_debug(True)   # logs: Executing <Handle ...> took 0.612 seconds

`slow_callback_duration` defaults to 100 ms. Module 15's realistic version is
not one 612 ms call -- it is a 12 ms query run 83 times a second, which
saturates the loop to rho = 0.997 without any single callback crossing the
threshold. Nothing warns. Lower the threshold to 20 ms and it fires 83 times a
second, which is a log volume problem rather than a signal. The lag RATIO below
is one number and it sees both cases.
"""

from __future__ import annotations

import asyncio
import os
import time

from opentelemetry import trace
from opentelemetry.trace import SpanKind, Status, StatusCode
from prometheus_client import Counter, Gauge

WORKER = os.environ.get("PULSE_WORKER") or f"pid-{os.getpid()}"
tracer = trace.get_tracer("pulse.asyncio")

# "How late was the last timer?" -- the size of the current stall.
# `livemax`, not `livesum` or the default `all`: with four workers merged, the
# average hides a frozen one and the max IS the truth. This is the same argument
# as Module 19's liveness probe, one level down.
LOOP_LAG = Gauge(
    "chat_event_loop_lag_seconds",
    "How late the loop woke a timer that asked for a fixed delay",
    ["worker"],
    multiprocess_mode="livemax",
)

# "How much of this worker's wall-clock time is queueing delay?"
# rate() of this is a dimensionless ratio: 0.0 healthy, 0.5 = half of real time
# spent late, 1.0 = falling behind as fast as time passes. Counters merge by
# SUMMING across workers, so divide by the live worker count in PromQL, or keep
# the `worker` label and use max by (pod).
LOOP_LAG_TOTAL = Counter(
    "chat_event_loop_lag_seconds_total",
    "Accumulated lateness. rate() of this is the loop's saturation.",
    ["worker"],
)

STALLS = Counter(
    "chat_event_loop_stalls_total",
    "Stalls exceeding the alerting threshold",
    ["worker"],
)

TASKS_ALIVE = Gauge(
    "chat_asyncio_tasks",
    "Live asyncio Tasks on this worker's loop (~1 per connection + housekeeping)",
    ["worker"],
    multiprocess_mode="livesum",
)

# 150 ms. Defended in Module 19's solution: it is 3.7x the measured p99 CPython
# gen-2 GC pause (41 ms, after gc.freeze()). Before gc.freeze() the p99 pause is
# 180 ms and no useful threshold exists below half a second -- so if you are
# tuning this number, fix the GC first.
STALL_THRESHOLD_S = float(os.getenv("PULSE_STALL_THRESHOLD", "0.150"))
PROBE_INTERVAL_S = float(os.getenv("PULSE_LAG_PROBE_INTERVAL", "0.25"))


async def watch(interval: float = PROBE_INTERVAL_S) -> None:
    """Run forever as a task on the worker's own loop.

    It has to run ON the loop it is measuring -- a thread cannot see the loop's
    callback queue, and a separate process cannot see it at all. The probe is
    therefore itself subject to the stall, which is exactly the property that
    makes it work.
    """
    loop = asyncio.get_running_loop()
    lag_gauge = LOOP_LAG.labels(worker=WORKER)
    lag_total = LOOP_LAG_TOTAL.labels(worker=WORKER)
    stalls = STALLS.labels(worker=WORKER)
    tasks = TASKS_ALIVE.labels(worker=WORKER)

    stall_started_ns: int | None = None
    stall_peak = 0.0

    while True:
        t0 = loop.time()
        wall0 = time.time_ns()
        await asyncio.sleep(interval)

        # loop.time() is monotonic, so this is immune to NTP steps -- which
        # matters, because a clock step during an incident would otherwise
        # manifest as a fictional 40-second stall.
        lag = max(0.0, loop.time() - t0 - interval)
        lag_gauge.set(lag)
        lag_total.inc(lag)
        tasks.set(len(asyncio.all_tasks(loop)))

        if lag > STALL_THRESHOLD_S:
            if stall_started_ns is None:
                stall_started_ns = wall0
                stall_peak = lag
            else:
                stall_peak = max(stall_peak, lag)
        elif stall_started_ns is not None:
            # The stall ended. Emit ONE span covering the whole episode.
            #
            # Not one span per probe: a 40-second stall would be 160 spans
            # describing the same event, and the tail sampler would keep all of
            # them because they are all "slow".
            stalls.inc()
            _emit_stall_span(stall_started_ns, time.time_ns(), stall_peak, len(asyncio.all_tasks(loop)))
            stall_started_ns, stall_peak = None, 0.0


def _emit_stall_span(start_ns: int, end_ns: int, peak_lag: float, tasks: int) -> None:
    """A ROOT span (no parent) covering the stall's wall-clock extent.

    Deliberately parentless. The stall does not belong to any one message's
    trace -- it belongs to the worker. Attaching it to whichever unlucky
    coroutine happened to be current would blame the victim.

    Explicit start_time/end_time are what make it line up on Tempo's timeline
    with the delayed spans, which is the entire point.
    """
    span = tracer.start_span(
        "asyncio.loop_stall",
        kind=SpanKind.INTERNAL,
        start_time=start_ns,
        attributes={
            "pulse.worker": WORKER,
            "pulse.pod": os.environ.get("PULSE_POD", "local"),
            "asyncio.lag_peak_ms": round(peak_lag * 1000, 1),
            "asyncio.duration_ms": round((end_ns - start_ns) / 1e6, 1),
            # Roughly one task per connection plus housekeeping. A stall with
            # 5,000 tasks alive delayed ~5,000 people; a stall with 12 delayed
            # nobody, and you can stop reading.
            "asyncio.tasks_alive": tasks,
        },
    )
    # ERROR status is not editorial -- it is what makes the collector's
    # tail-sampling `status_code` policy keep 100% of these.
    span.set_status(Status(StatusCode.ERROR, "event loop stalled"))
    span.end(end_time=end_ns)


def install(loop: asyncio.AbstractEventLoop | None = None) -> asyncio.Task:
    """Idempotent-ish helper for `lifespan.startup`."""
    loop = loop or asyncio.get_running_loop()
    # Turning debug mode on costs a few percent and buys you the callback names
    # in the traceback when something IS a single slow call. Leave the threshold
    # at 100 ms: this watchdog covers the death-by-a-thousand-cuts case, and
    # lowering it just floods the log.
    if os.getenv("PULSE_ASYNCIO_DEBUG", "0") == "1":
        loop.set_debug(True)
    return loop.create_task(watch())


if __name__ == "__main__":
    # The whole module in twelve lines: an idle loop, then a blocked one.
    async def main() -> None:
        task = install()
        await asyncio.sleep(1.0)
        idle = LOOP_LAG.labels(worker=WORKER)._value.get()
        print(f"idle loop lag           : {idle * 1000:7.2f} ms")

        time.sleep(0.9)                       # the cardinal sin, on purpose
        await asyncio.sleep(0.5)
        blocked = LOOP_LAG.labels(worker=WORKER)._value.get()
        print(f"after a 0.9 s block     : {blocked * 1000:7.2f} ms")

        total = LOOP_LAG_TOTAL.labels(worker=WORKER)._value.get()
        print(f"accumulated lateness    : {total:7.3f} s")
        print(f"ratio over ~2.4 s wall  : {total / 2.4:7.3f}   <- the SLI-adjacent number")
        task.cancel()

    asyncio.run(main())
