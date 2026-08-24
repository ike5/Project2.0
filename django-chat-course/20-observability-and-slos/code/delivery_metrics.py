#!/usr/bin/env python3
"""Delivery instrumentation — the reference copy of `chat/delivery_metrics.py`.

Module 06's `chat/metrics.py` measured the six numbers that predict a chat
server's death. This file adds the four that define its SLIs, and it exists as a
separate module for one reason: **`chat_group_send_seconds` is not delivery
latency and people keep quoting it as if it were.**

    chat_group_send_seconds     how long group_send() took to ENQUEUE a fan-out
    chat_delivery_latency       origin_ts -> the LAST recipient's socket write

Module 06's harness already measures the second one from the client side, which
is the honest way -- only a receiver knows when it received. This file measures
the server's half so you have a number without a load generator attached, and so
the SLO can be evaluated continuously in production rather than during a test.

The two numbers differ by roughly 12x on the Module 18 HA stack (22 ms vs
261 ms). Neither is wrong; they answer different questions. The enqueue number
is the one that would have made Module 06's broken server look healthy.

MULTIPROCESS RULES (see the module README):
  - Counters and Histograms merge by SUMMING across worker processes. No
    `worker` label needed, and adding one multiplies your series count for
    nothing.
  - Gauges need an explicit `multiprocess_mode` or you get one series per PID.
  - Exemplars DO NOT WORK in multiprocess mode. Do not add `exemplar=` calls and
    then wonder why Grafana's exemplar dots never appear.

Usage:

    from chat.delivery_metrics import record_delivery, record_handshake, bucket
"""

from __future__ import annotations

import time
from prometheus_client import Counter, Gauge, Histogram

# ---------------------------------------------------------------------------
# SLI 2 -- delivery latency.
# ---------------------------------------------------------------------------
# Bucket edges are not decoration. `histogram_quantile` INTERPOLATES within a
# bucket, so an SLO threshold that is not an exact edge is an estimate. 0.5 is
# here because the SLO is 500 ms; 0.1 and 1.0 are here because those are the
# thresholds the challenge's user-tolerance study lands on.
DELIVERY_LATENCY = Histogram(
    "chat_delivery_latency_seconds",
    "origin_ts until the LAST recipient's socket was written",
    buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)

# Per-recipient, for diagnosing a slow tail INSIDE one fan-out. Separate metric,
# because mixing "the whole fan-out" and "one socket" into one histogram makes
# both unreadable.
RECIPIENT_LATENCY = Histogram(
    "chat_delivery_recipient_latency_seconds",
    "origin_ts until ONE recipient's socket was written",
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 5.0),
)

# ---------------------------------------------------------------------------
# SLI 1 -- delivery success. attempts - failures over expected recipients.
# ---------------------------------------------------------------------------
# This CANNOT see the last hop: a frame written to a socket whose owner never
# received it counts as a success here. That gap is why prober.py exists, and
# saying so in the metric's own description is cheaper than saying it in a
# postmortem.
PUBLISHED = Counter("chat_published_total", "Messages accepted and sequenced")
DELIVERY_ATTEMPTS = Counter(
    "chat_delivery_attempts_total",
    "Individual socket writes attempted (increments by ROOM SIZE, not by 1)",
)
DELIVERY_FAILURES = Counter(
    "chat_delivery_failures_total",
    "Socket writes that raised. NOT the same as 'the user did not receive it'",
    ["reason"],           # closed | backpressure | serialize | unknown -- 4 values
)

FANOUT_SIZE = Histogram(
    "chat_fanout_size",
    "Recipients per published message",
    buckets=(1, 5, 10, 25, 50, 100, 200, 500, 1000, 2000, 5000),
)

# ---------------------------------------------------------------------------
# SLI 3 -- connection success.
# ---------------------------------------------------------------------------
# `outcome` has five values, on purpose. "rejected" and "failed" are different
# incidents: the first is your admission control working (Module 19), the second
# is a bug. Collapsing them into one counter loses the distinction exactly when
# you need it.
HANDSHAKES = Counter(
    "chat_handshake_total",
    "WebSocket handshake outcomes",
    ["outcome"],          # success | rejected_capacity | rejected_auth | rejected_rate | failed
)

# ---------------------------------------------------------------------------
# SLI 4 -- sequence integrity.
# ---------------------------------------------------------------------------
# A gap is TRANSIENT until a resume fails to fill it. Counting transient gaps as
# SLI violations makes the SLI fire on every reconnect, which is normal
# behaviour (Module 10). Only the permanent ones are a broken promise.
SEQUENCE_GAPS = Counter("chat_sequence_gaps_total", "Gaps observed by a client")
SEQUENCE_GAPS_PERMANENT = Counter(
    "chat_sequence_gaps_permanent_total",
    "Gaps a resume-from-cursor could NOT fill -- messages that are genuinely gone",
)

# ---------------------------------------------------------------------------
# Semantic invariants -- the signals that catch a healthy-but-wrong release.
# ---------------------------------------------------------------------------
# Module 19's challenge shipped a version that replaced Module 10's cluster-wide
# dedup with a per-process lru_cache. Error rate improved. p99 improved. The
# only thing that moved was this ratio, and it moved 88%.
DEDUP_HITS = Counter("chat_dedup_hits_total", "message.create rejected as a duplicate")

# ---------------------------------------------------------------------------
# Saturation.
# ---------------------------------------------------------------------------
OUTBOUND_QUEUE = Gauge(
    "chat_outbound_queue_depth",
    "Frames enqueued for sockets and not yet written, this worker",
    ["worker"],
    multiprocess_mode="livesum",   # a POD total. `all` gives one series per PID.
)
MAX_CONNECTIONS = Gauge(
    "chat_max_connections",
    "This pod's configured admission ceiling -- the HPA's denominator",
    multiprocess_mode="max",       # every worker reports the same constant
)


def bucket(recipients: int) -> str:
    """Bucket the room size. NEVER label by room id.

    100,000 rooms x 10 buckets is 1,000,000 series and ~3 GB of Prometheus. Four
    buckets is four. If you need to know WHICH room is slow, that is a trace
    query -- `{ span.chat.room = "room.7" }` -- and Tempo is indexed for it.
    """
    if recipients <= 10:
        return "small"
    if recipients <= 200:
        return "medium"
    if recipients <= 2000:
        return "large"
    return "huge"


def record_delivery(origin_ts_ms: int, recipients: int, failures: int) -> None:
    """Called ONCE per message, after every recipient's write was attempted.

    `origin_ts_ms` travels IN the envelope (Module 05's `ts` field), which is
    what makes this work at all: the send happened on one worker in one pod and
    the delivery happens on another, so there is no shared clock to subtract
    from except the one the message carries.

    Clock skew across pods is real and it is why this is a histogram rather than
    a gauge -- a few negative samples from a skewed node land in the lowest
    bucket instead of poisoning an average. Under Docker/kind every container
    shares the host clock, so the lab sees none; a real fleet with NTP sees
    single-digit milliseconds.
    """
    elapsed = max(0.0, (time.time() * 1000 - origin_ts_ms) / 1000.0)
    DELIVERY_LATENCY.observe(elapsed)
    PUBLISHED.inc()
    DELIVERY_ATTEMPTS.inc(recipients)
    FANOUT_SIZE.observe(recipients)
    if failures:
        DELIVERY_FAILURES.labels(reason="closed").inc(failures)


def record_recipient(origin_ts_ms: int) -> None:
    RECIPIENT_LATENCY.observe(max(0.0, (time.time() * 1000 - origin_ts_ms) / 1000.0))


def record_handshake(outcome: str) -> None:
    HANDSHAKES.labels(outcome=outcome).inc()


if __name__ == "__main__":
    # Smoke test: prove the two latencies are different things.
    import random
    from prometheus_client import generate_latest, REGISTRY

    origin = int(time.time() * 1000) - 261      # the Module 18 HA baseline p99
    for _ in range(1000):
        record_delivery(origin + random.randint(-40, 40), recipients=199, failures=0)
        record_handshake("success")

    out = generate_latest(REGISTRY).decode()
    for line in out.splitlines():
        if "chat_delivery_latency_seconds_bucket" in line and 'le="0.5"' in line:
            print(line)
        if line.startswith("chat_delivery_latency_seconds_count"):
            print(line)
    print("\nfraction under 500 ms is SLI 2. If le=\"0.5\" is not an exact bucket")
    print("edge, that fraction is an interpolation and your SLO is a guess.")
