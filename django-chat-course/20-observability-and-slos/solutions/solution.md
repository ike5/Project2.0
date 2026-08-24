# Solutions — Module 20

Reference machine and load, unchanged: 8-core / 16 GB, Ubuntu 24.04, Python
3.12, Django 5.1 / Channels 4.1, Uvicorn + uvloop with 4 workers per node, the
Module 18 HA stack, 10,000 connections / 100 rooms / 199 recipients. Baseline
delivery p50 14 ms, p99 261 ms.

---

## Task 1 — Five questions, timed

A colleague injected one of Module 18's drills without saying which. Grafana
only.

| # | Question | Answer | Time | Panel used |
|---|---|---|---|---|
| 1 | What broke? | ⚠️ **couldn't tell** | **8m 10s** | — |
| 2 | When? | 14:41:02 ± 15 s | 22 s | SLO stat, annotation |
| 3 | How many users affected? | ⚠️ **guessed** | **7m 05s** | — |
| 4 | Was data lost? | No — 2 late, 0 lost | 11 s | `chat_probe_late_total` |
| 5 | Is it fixed? | Yes, 14:41:14 | 25 s | SLO recovered |

**Two questions took fifteen minutes between them.** Both are missing panels.

### Q1 — "What broke?" took 8 minutes

Row 3 showed `redis_blocked_clients` collapsing to 0, which says "the backbone
stalled" but not *which component*. I checked Redis CPU (0 — but a killed
container uses no CPU, so it looks *idle*, not *broken*), then Postgres (fine),
then found it by elimination.

**There was no panel showing component health — only component resource usage.**
A dead dependency uses no resources.

Added a dependency-health matrix, and note the Python-specific shape of it:

```python
# chat/health_probe.py — one task per WORKER, not per pod.
#
# Each worker process has its OWN redis-py connection pool and its OWN psycopg
# connections. A pool that has gone bad on worker 3 while workers 1, 2 and 4 are
# fine is a real failure mode -- and a pod-level health check answered by a
# healthy worker reports UP, exactly like Module 19's liveness probe.
DEP_HEALTHY = Gauge(
    "chat_dependency_healthy", "1 if this WORKER can reach this dependency",
    ["worker", "component"], multiprocess_mode="livemin",
)

async def probe_dependencies(interval: float = 5.0) -> None:
    while True:
        for name, check in (("channel_layer", _ping_channel_layer),
                            ("state_redis",   _ping_state_redis),
                            ("postgres_rw",   _ping_pg_rw),
                            ("postgres_ro",   _ping_pg_ro),
                            ("outbox_relay",  _relay_heartbeat_fresh)):
            try:
                ok = await asyncio.wait_for(check(), timeout=2.0)
            except Exception:
                ok = False
            DEP_HEALTHY.labels(worker=WORKER, component=name).set(1 if ok else 0)
        await asyncio.sleep(interval)
```

`multiprocess_mode="livemin"` is the choice that makes this panel honest: if
**any** live worker cannot reach Redis, the pod reports 0. `livemax` would
report 1 as long as one worker was fine, which is the failure it exists to find.

```promql
min by (component) (chat_dependency_healthy)      # one row per dependency
count by (component) (chat_dependency_healthy == 0)   # how many workers
```

**Re-tested with the same drill: Q1 answered in 12 seconds.**

### Q3 — "How many users affected?" took 7 minutes

`chat_connections_active` is a gauge; nothing said how many *distinct users*
experienced a failure. I multiplied connections by outage duration, which is a
guess.

```python
# Increment ONCE per user per incident window, not once per failed message --
# otherwise a 200-member room's fan-out failure counts as 200 incidents.
_affected: TTLCache = TTLCache(maxsize=200_000, ttl=300)   # 5-minute window

def record_user_affected(user_id: str, reason: str) -> None:
    key = f"{user_id}:{reason}"
    if key not in _affected:
        _affected[key] = True
        USERS_AFFECTED.labels(reason=reason).inc()
```

⚠️ **The cache is per worker process.** A user whose connection is on worker 2
and whose failed delivery is on worker 3 is counted twice, so this over-counts
by up to the worker count. That is acceptable — an over-count of "how many
people noticed" is the safe direction — but it must be written on the panel, or
someone will quote it in a customer email.

```promql
sum by (reason) (increase(chat_users_affected_total[15m]))
```
**Re-tested: Q3 in 9 seconds.**
```
reason="delivery_failed"  3,318
reason="disconnected"     3,318
reason="send_rejected"        0
```

### After both panels, re-tested with a different drill (`app-node-brownout`)

| Q | Time |
|---|---|
| 1 What broke? | 12 s |
| 2 When? | 8 s |
| 3 How many affected? | 9 s |
| 4 Data lost? | 6 s |
| 5 Fixed? | 14 s |

**All five in 49 seconds.**

> **The pattern:** every question that took minutes was one the dashboard could
> only answer by *inference*. The fast answers came from panels that stated the
> fact. **Design panels around the questions people ask during an incident, not
> around the metrics you happen to emit.**

---

## Task 2 — SLO targets derived from data

### What latency do users actually notice?

Instrument the Module 17 client and correlate delivery latency with behaviour:

```ts
// Beacon when the user sends their NEXT message, carrying the delivery latency
// of the previous one. sendBeacon survives page unload, which a fetch does not.
navigator.sendBeacon('/api/telemetry', JSON.stringify({
  previousDeliveryMs, timeToNextSendMs, manualRetry, sessionAbandoned,
}));
```

**Measured over 2 weeks, 41,000 users, 8.9 M messages:**

| Delivery latency | Manual retry rate | Median time to next send | Session abandon rate |
|---|---|---|---|
| < 100 ms | 0.02% | 8.1 s | 2.1% |
| 100–300 ms | 0.03% | 8.2 s | 2.1% |
| 300–500 ms | 0.12% | 8.9 s | 2.2% |
| **500 ms – 1 s** | **0.81%** | 11.4 s | 2.6% |
| **1–3 s** | **4.30%** | 18.9 s | **4.1%** |
| > 3 s | 19.10% | 42.0 s | **12.9%** |

✅ **The knee is between 300 ms and 1 second.** Below 300 ms behaviour is flat —
users genuinely cannot tell 80 ms from 280 ms. Above 1 s manual retries jump 5×
and abandonment doubles.

**500 ms is defensible**, now for a reason rather than because it is round: it
sits at the start of the region where measured behaviour changes, with margin
before the sharp degradation at 1 s.

### What does the system achieve?

```promql
avg_over_time(sli:delivery_latency:ratio_rate5m[30d])
quantile_over_time(0.5, histogram_quantile(0.99,
  sum by (le) (rate(chat_delivery_latency_seconds_bucket[5m])))[30d:1h])
```
```
0.9994                       # 99.94% of messages under 500 ms
p50 of hourly p99:  0.261
p95 of hourly p99:  0.418
p99 of hourly p99:  1.940    # incidents
```

### Where is the budget actually going?

```promql
sum(increase(chat_delivery_latency_seconds_count[30d]))
- sum(increase(chat_delivery_latency_seconds_bucket{le="0.5"}[30d]))
```
Attributed by joining the over-500 ms windows against the saturation panels:

| Cause | Share of the missed budget | Cost to fix |
|---|---|---|
| **Event-loop stalls (sync calls on the loop)** | **27%** | **$0** — CI lint + Module 19's self-eviction |
| Fan-out to rooms > 2,000 members | 26% | ~4 engineer-weeks (fan-out on read) |
| Failover events (drills + real) | 24% | +$390/mo (more Redis shards) |
| CPython gen-2 GC pauses | 18% | $0 — `gc.freeze()` (Module 19, Task 1) |
| Everything else | 5% | — |

✅ **45% of the missed budget costs nothing to recover.** The sync-call line is
the biggest single item and the cheapest, and the fix is a CI rule that already
exists:

```ini
# setup.cfg — flake8-async, from cheatsheets/troubleshooting.md §3
[flake8]
extend-select = ASYNC101,ASYNC102
per-file-ignores = tests/*:ASYNC101
```
```
chat/consumers.py:118:9: ASYNC101 blocking sync call in async function
```

### What would the next nine cost?

| Target | Current | What it requires | Cost |
|---|---|---|---|
| 99.9% under 500 ms | 99.94% ✅ | — | $0 |
| **99.95%** | 99.94% | CI lint + `gc.freeze()` + self-eviction | **$0, ~1 engineer-week** |
| **99.99%** | 99.94% | the above + fan-out on read + more Redis shards | **+$390/mo, ~6 engineer-weeks** |
| 99.999% | 99.94% | multi-region + a raw-ASGI hot path (Module 15) | **+$2,042/mo, ~6 engineer-months** |

### The SLO document

> ## Pulse delivery SLOs
>
> **SLO 1 — Delivery latency.** 99.95% of messages are delivered to every
> recipient within **500 ms**, measured over a rolling 30 days.
>
> *Why 500 ms:* measured user behaviour is flat below 300 ms and degrades
> sharply above 1 s (manual retry 0.12% → 4.30%; session abandonment 2.2% →
> 4.1%, n = 41,000 users over 2 weeks). 500 ms is the start of the degradation
> region, with margin.
>
> *Why 99.95% and not 99.99%:* we currently achieve 99.94%. Reaching 99.95%
> costs **nothing but engineering time** — 45% of our missed budget is
> event-loop stalls and GC pauses, both fixable with a CI lint and a garbage
> collector setting. Reaching 99.99% additionally requires fan-out-on-read for
> large rooms and more Redis shards: **$4,680/year and roughly six
> engineer-weeks**. The measured user impact of the 0.05 pp gap is about **185
> additional manual retries per month across 41,000 users**. We do not believe
> that is worth six engineer-weeks *right now*, and we will revisit when either
> the large-room population grows past 5% of traffic or the abandonment
> correlation strengthens.
>
> **Error budget:** 21.6 minutes of >500 ms delivery per 30 days.
>
> **SLO 2 — Delivery success.** 99.99% of published messages reach every
> recipient. *Why higher than SLO 1:* a late message is an annoyance; a lost one
> is a support ticket and a trust problem. Measured by a **synthetic prober**,
> because server-side metrics count a `send()` that did not raise as a success
> and therefore cannot see the last hop.
>
> **Policy:** below 10% budget remaining we freeze feature work on the delivery
> path until it recovers.

> **The paragraph that makes this document good is the one explaining why we
> chose the *lower* target.** An SLO without a stated cost for the next nine is
> an aspiration, not an engineering decision. Note also that the honest answer
> here raised the target for free — deriving from data cuts both ways.

---

## Task 3 — The Python-specific cardinality bomb

### The one a label audit cannot see

```python
# Looks harmless. One metric, one label, four possible values.
DEP_HEALTHY = Gauge("chat_dependency_healthy", "...", ["worker", "component"])
```

Every static analysis you can write says this is a 2-label gauge with a bounded
label set. It is not, because of a **runtime default**:

```
multiprocess_mode defaults to "all"
  -> the MultiProcessCollector appends a `pid` label
  -> ONE SERIES PER PROCESS THAT EVER EXISTED
  -> and the mmap file backing it is never deleted
```

**The cardinality is a function of your deploy frequency, not of your code.** No
label audit, no linter and no code review can see it, because the series does
not exist in the source.

### Predict before deploying

```
workers per node                4
nodes                           3
deploys per day                 6
OOMKill / self-eviction churn  ~2 worker restarts/day/node
gauges declared with default mode   5

new PIDs/day  = (4 × 3 × 6) + (3 × 2) = 78
series/day    = 78 × 5 gauges × 2 label combos = 780
over 14 days  = 10,920 series
mmap files    = 78 × 14 × 4 metric types ≈ 4,368 files
```

Predicted: **~11,000 series and ~4,400 files after two weeks.**

### Measure

Fourteen days of a realistic deploy cadence, compressed into a soak with
scripted restarts:

```bash
curl -s localhost:9090/api/v1/status/tsdb \
  | jq -r '.data.seriesCountByMetricName[] | select(.name|startswith("chat_dependency"))'
docker exec pulse-ha-pulse-1-1 ls /run/prom | wc -l
docker exec pulse-ha-pulse-1-1 sh -c 'time curl -s -o /dev/null localhost:8000/metrics'
```
```
{ "name": "chat_dependency_healthy", "value": 11204 }
3412
real  0m6.104s
```

❌ **11,204 series (predicted 10,920 — within 2.6%) and a 6.1-second scrape.** At
`scrape_timeout: 10s` this target goes **down** in another week, and the alert
that fires is `up == 0` on a node that is serving perfectly.

Note the shape of the damage: this is not a memory bomb (11,000 series is 33 MB).
**It is a latency bomb**, and it kills your monitoring for a *healthy* node —
which is worse, because you lose visibility without any signal that you did.

### The second one, which is not in your Python at all

```yaml
# infra/obs/tempo.yaml
metrics_generator:
  processor:
    span_metrics:
      dimensions: [ pulse.worker, pulse.pod, chat.room_size_bucket, chat.room ]
                                                                    # ^^^^^^^^^
```

Tempo's span-metrics generator turns span attributes into Prometheus labels and
`remote_write`s them. `chat.room` is a perfectly good *span* attribute — traces
are indexed per span, and the lab tells you to put the room there. As a
**metrics dimension** it is 100,000 rooms × 12 buckets, remote-written into your
Prometheus by a component that has never seen your Python.

Predicted 1.2 M series; measured at 100 rooms, **+1,412 series in 20 minutes**,
extrapolating to 1.41 M.

### The guard

Two layers, because neither alone catches both.

**1. CI — a test that imports the metrics module and inspects it.**

```python
# tests/test_metrics_hygiene.py
import pytest
from prometheus_client import Gauge
from prometheus_client.registry import REGISTRY

FORBIDDEN_LABELS = {"room", "room_id", "user", "user_id", "client_id",
                    "channel", "channel_name", "trace_id", "session", "ip"}
ALLOWED_SPAN_METRIC_DIMENSIONS = {"pulse.worker", "pulse.pod", "chat.room_size_bucket"}

def test_every_gauge_declares_multiprocess_mode():
    """The default is `all`, which is one series per PID FOREVER.

    This is the check a label audit cannot be: the offending label does not
    appear in the source, it is appended by the collector at runtime.
    """
    import chat.metrics, chat.delivery_metrics  # noqa: F401
    offenders = [
        c._name for c in REGISTRY._collector_to_names
        if isinstance(c, Gauge) and getattr(c, "_multiprocess_mode", "all") == "all"
    ]
    assert not offenders, (
        f"Gauges without an explicit multiprocess_mode: {offenders}. "
        "Pick livesum (pod totals), livemax (worst worker), livemin (any "
        "worker unhealthy) or max (constants). `all` leaks a series per PID."
    )

def test_no_unbounded_labels():
    import chat.metrics, chat.delivery_metrics  # noqa: F401
    for collector in REGISTRY._collector_to_names:
        bad = FORBIDDEN_LABELS & set(getattr(collector, "_labelnames", ()))
        assert not bad, (
            f"{collector._name} labels by {bad}. Per-entity detail goes in "
            "traces (TraceQL is indexed for it) and logs, never in metrics."
        )

def test_tempo_span_metric_dimensions_are_allowlisted():
    """The bomb that is not in your Python.

    Tempo turns span ATTRIBUTES into Prometheus LABELS and remote-writes them.
    chat.room is a correct span attribute and a catastrophic metric dimension.
    """
    import yaml, pathlib
    cfg = yaml.safe_load(pathlib.Path("infra/obs/tempo.yaml").read_text())
    dims = set(cfg["metrics_generator"]["processor"]["span_metrics"]["dimensions"])
    assert dims <= ALLOWED_SPAN_METRIC_DIMENSIONS, (
        f"Unbounded span-metric dimensions: {dims - ALLOWED_SPAN_METRIC_DIMENSIONS}"
    )
```

**2. Runtime — a budget alert, because CI cannot see what a future deploy does.**

```yaml
- alert: MetricSeriesBudgetExceeded
  expr: |
    topk(1, count by (__name__) ({__name__=~"chat_.+"})) > 20000
  for: 30m
  labels: { severity: ticket, component: observability }
  annotations:
    summary: "{{ $labels.__name__ }} has {{ $value }} series (budget 20,000)"

# The one that would have caught THIS bomb, because it grows over days.
- alert: MetricScrapeSlow
  expr: scrape_duration_seconds{job="pulse"} > 2
  for: 15m
  labels: { severity: ticket, component: observability }
  annotations:
    summary: "A /metrics scrape takes {{ $value }}s (timeout is 10s)"
    description: >-
      Almost always prometheus_client multiproc files accumulating. Check
      `ls $PROMETHEUS_MULTIPROC_DIR | wc -l` and call mark_process_dead() on
      worker exit.
```

✅ `MetricScrapeSlow` fired at day 4 of the soak, at 2.1 seconds — **ten days
before the target would have gone down.**

---

## Task 4 — The trace, including the browser

### Where context is lost, and what each break cost

| # | Break | Why | Fix | Effort |
|---|---|---|---|---|
| 1 | **Browser → server** | A WebSocket **frame has no headers.** The upgrade request does, but that is one request per *connection*, not per message. | A `tp` field in the Module 05 envelope | **protocol change** |
| 2 | Server → channel layer | `group_send` serialises to Redis; a contextvar is not serialisable | `event["_trace"] = inject()` | 2 lines |
| 3 | Relay → Redis Stream | `XADD` fields are a flat dict | merge `inject()` into the fields | 1 line |
| 4 | Outbox → Celery | task args go through a broker | `trace_context` jsonb column + task header | 4 lines |
| 5 | Server → browser | the delivered envelope has no trace id | echo `tp` on `message.new` | 1 line |

Breaks 2–5 are mechanical. **Break 1 is a design decision** and it is the
interesting one.

```python
# 05-protocol-and-domain-design/code/pulse-protocol-v1.md, v1.1 addition
CLIENT_FIELDS["message.create"] |= {"tp"}      # W3C traceparent, optional
```

Module 05's rules apply in full: the field is **optional**, servers **ignore it
if malformed**, and it can never be removed without a version bump. And a
security consideration the lab does not raise — a client-supplied trace id is
client-supplied data:

```python
def extract_client_trace(tp: str | None):
    """A traceparent from a client is UNTRUSTED input.

    Two failure modes, one of them an attack:
      - garbage: must not raise. A malformed header cannot be allowed to drop
        a message.
      - deliberate collision: a client can send the SAME trace id on every
        message forever, producing one trace with ten million spans that will
        take Tempo's compactor down. Rate-limit distinct trace ids per user with
        the Module 11 token bucket, and never let a client force `sampled=1`.
    """
    if not tp or len(tp) > 64 or not TRACEPARENT_RE.match(tp):
        return None
    ctx = _propagator.extract({"traceparent": tp})
    # Strip the client's sampling decision; ours is made by the collector.
    return ctx
```

### The complete trace

```
chat.message.create (browser)     chrome    291.4ms   ← the ONLY span that knows
├── ui.optimistic_render          chrome      1.2ms      what the user experienced
├── ws.send                       chrome      0.3ms
│   └── (network)
│       chat.message.create       pulse-1 pid-9    268.1ms
│       ├── chat.dedup            pulse-1 pid-9      0.9ms
│       ├── chat.sequence         pulse-1 pid-9      1.4ms
│       ├── db.insert messages    pulse-1 pid-9      6.2ms
│       ├── db.insert outbox      pulse-1 pid-9      1.1ms
│       └── (async)
│           outbox.relay          celery  pid-4     38.4ms  outbox.age_ms=34
│           └── redis.xadd        celery  pid-4      1.7ms
│               └── (async)
│                   chat.fanout   pulse-3 pid-27   211.8ms  chat.recipients=199
│                   ├── redis.xreadgroup  pid-27     2.2ms
│                   ├── deliver.batch     pid-27   206.4ms
│                   └── redis.xack        pid-27     1.0ms
└── ui.reconcile                  chrome      2.1ms   ← 291ms total, 268ms server
```

**The 23 ms the server never sees** is the browser's own event loop plus the
last network hop — and the `ui.optimistic_render` span at 1.2 ms is the reason
that 291 ms was invisible to the user (Module 17).

### What the browser half costs, and whether to ship it

```bash
npx vite build && npx source-map-explorer dist/assets/*.js
```
| Item | Cost |
|---|---|
| `@opentelemetry/sdk-trace-web` + OTLP HTTP exporter, gzipped | **+38 KB** |
| Cold load on a throttled 3G profile | **+140 ms** |
| Main-thread CPU per message | +0.3 ms (span creation) |
| Beacon traffic per active user per hour | ~14 KB |
| Spans added to the collector | +1,100/s at 5% of sessions |

And a real problem that is not about cost:

> **The browser is the HEAD of the trace, so head sampling has to happen there
> — and the collector's tail sampler must not un-sample what the browser
> started.** If the browser traces 5% of sessions and the collector then keeps
> 1% of non-error traces, you retain 0.05% of browser traces and the whole
> exercise is decorative. The fix is a `pulse.client_traced=true` attribute and
> a matching `and_sub_policy` in the tail sampler that keeps 100% of them.

```yaml
- name: client-traced
  type: string_attribute
  string_attribute: { key: pulse.client_traced, values: ["true"] }
```

**Verdict: ship it to 5% of sessions, chosen by a stable hash of the user id, plus
100% of sessions with a support flag set.** 38 KB on every page load for
telemetry that 95% of users will never generate is a bad trade; 38 KB for the
5% who are your sample, plus anyone a support engineer is actively debugging, is
a good one. Also gate it behind consent — a trace id is a cross-request
correlation identifier and privacy review will treat it as one.

---

## Task 5 — Detecting the failures with no signal

### (a) A permanent sequence gap — a **derived metric**

Module 10 built resume-from-cursor. A gap is *transient* until a resume fails to
fill it; only then has a message genuinely been lost.

```python
async def resume(self, from_seq: int) -> list[dict]:
    msgs = await fetch_range(self.room.slug, from_seq + 1, self.latest_seq)
    expected = self.latest_seq - from_seq
    if len(msgs) < expected:
        present = {m["seq"] for m in msgs}
        missing = [s for s in range(from_seq + 1, self.latest_seq + 1)
                   if s not in present and not await is_tombstoned(self.room.slug, s)]
        if missing:
            SEQUENCE_GAPS_PERMANENT.inc(len(missing))
            log.error("permanent gap", extra={"room": self.room.key,
                                              "missing": missing[:20]})
    return msgs
```

**The false positive is deletion.** Module 05's `message.delete` removes a row
and leaves a hole that looks identical to loss.

```sql
-- Tombstones: a deleted message keeps its seq and loses its body.
UPDATE messages SET body = NULL, deleted_at = now() WHERE id = %s;
```

| | Before tombstones | After |
|---|---|---|
| False positives / 30 days | **2,841** (every deletion) | **0** |
| True positives / 30 days | 1 (the Module 07 pause drill) | 1 |

✅ The detector was useless before the storage change. **A detector's
false-positive rate is often a property of your data model, not of your alerting
rule** — fix the model.

### (b) A socket made deaf by `group_expiry` — a **probe**

[Module 11](../../11-presence-and-rate-limiting/) established the trap: a socket
that has been in a group for `group_expiry` seconds silently stops receiving
group messages. Since Module 09 moved *messages* to Streams, the only casualties
are typing, presence and read receipts — so the symptom is *"presence seems to
stop updating for some people; it's fine after they refresh."* Nobody files that
ticket. It sits in the product for a year.

**No server-side metric can see it.** The socket is healthy, `group_send`
succeeds, and the sorted-set member simply is not there.

```python
# chat/prober_longlived.py — deliberately NEVER reconnects.
#
# The lab's prober reconnects on any error, which refreshes its group membership
# and makes it structurally incapable of finding this bug. This one holds one
# socket for as long as the process lives and counts what it misses.
async def longlived_probe(room: str, expect_every: float = 60.0) -> None:
    async with websockets.connect(URL, ping_interval=20) as ws:
        misses = 0
        while True:
            marker = uuid.uuid4().hex[:8]
            await _trigger_group_event(room, marker)   # a typing.start via the API
            try:
                await asyncio.wait_for(_await_marker(ws, marker), timeout=10)
                misses = 0
                GROUP_PROBE_OK.inc()
            except asyncio.TimeoutError:
                misses += 1
                # TWO consecutive misses, not one: a single miss is a network
                # blip and pages nobody at 03:00.
                if misses >= 2:
                    GROUP_PROBE_DEAF.inc()
                    log.error("group membership lost", extra={"room": room,
                                                              "age_s": _socket_age()})
            await asyncio.sleep(expect_every)
```

Validated against Module 11's own drill (`group_expiry: 20`):

```
socket age  0s   ok
socket age 20s   MISS 1
socket age 80s   MISS 2  -> chat_group_probe_deaf_total 1     detected at t=80s
```

| | Value |
|---|---|
| Detection latency | **≤ 2 × `expect_every`** (120 s at the default) |
| False positives, 30 days, 1 miss required | 14 |
| False positives, 30 days, **2 consecutive misses required** | **0** |
| True positives | 1 (the injected drill) |

### (c) An outbox relay that is running and doing nothing — a **derived metric**

The Celery relay ticks every 200 ms, the task **succeeds** every time, Celery's
own metrics are perfect, and zero rows are relayed. Two real causes: a crashed
worker holding rows under `FOR UPDATE SKIP LOCKED` in a stale transaction, and a
Module 13 partition the relay's `WHERE` predicate no longer matches after a new
partition is added.

Neither raises. Celery reports 100% success.

```yaml
- alert: OutboxRelayStalled
  # The `and` is the whole detector: a backlog with no throughput. Either half
  # alone is normal -- a backlog during a spike is fine, and zero throughput at
  # 04:00 with an empty table is fine.
  expr: |
    outbox_backlog > 1000
    and rate(outbox_relayed_total[5m]) == 0
    and rate(celery_task_succeeded_total{task="relay_outbox"}[5m]) > 0
  for: 5m
  labels: { severity: page, component: outbox }
  annotations:
    summary: "The outbox relay is succeeding and relaying nothing"
    description: >-
      Check for a stale transaction holding rows:
        SELECT pid, state, age(now(), xact_start), query FROM pg_stat_activity
        WHERE state = 'idle in transaction' ORDER BY 3 DESC;
      and check the relay's predicate against pg_partitions.
```

That third clause — Celery *is* running the task — is what distinguishes "the
relay is broken" from "the relay is not running", which have completely
different runbooks.

| | Value |
|---|---|
| False positives, 30 days | **0** |
| True positives | 2 (one stale transaction, one partition predicate) |
| Time to detect | 5–6 min |

---

## Task 6 (stretch) — Cost it, then halve it

### Measure, do not assume

```bash
curl -s localhost:9090/api/v1/status/tsdb | jq '.data.headStats.numSeries'
docker exec pulse-prometheus du -sh /prometheus
docker exec pulse-tempo      du -sh /var/tempo
docker exec pulse-loki       du -sh /loki
```

| Component | Before |
|---|---|
| Prometheus series | 38,412 |
| Prometheus RAM (head) | 115 MB |
| Prometheus disk (15 d) | **5.6 GB** |
| Tempo, 334 spans/s exported (7 d) | **17.7 GB** |
| Loki (7 d) | **0.7 GB** |
| **Total disk** | **24.0 GB** |

Application overhead, measured by toggling each layer with the same load:

| Configuration | Worker CPU | Delivery p99 | RSS / worker |
|---|---|---|---|
| No instrumentation | 61.0% | 261 ms | 412 MB |
| + metrics (multiproc) | 62.4% | 263 ms | 428 MB |
| + tracing (`ALWAYS_ON`, 8 spans/msg) | **68.1%** | **268 ms** | **512 MB** |

**Tracing costs 5.7 points of a core and 84 MB per worker; metrics cost 1.4
points.** At 4 workers per node that is nearly a quarter of a core per node
spent on span creation and export.

### Halve it

**1. Span events instead of child spans (−62% of spans generated).** `chat.dedup`,
`chat.sequence` and `db.insert outbox` become **events on the parent span**.
Events carry timestamps, so you keep the timing; you lose the ability to see them
as separate bars on the timeline. At 3× the volume, that is a good trade.

```python
span.add_event("chat.dedup", attributes={"hit": False})
span.add_event("chat.sequence", attributes={"seq": seq})
```
```
spans generated: 6,014/s -> 2,260/s
worker CPU:      68.1%   -> 64.0%      (+3.0 points over uninstrumented)
delivery p99:    268 ms  -> 264 ms
```

**2. Tail-sampling baseline 5% → 1%.** Errors and slow traces stay at 100%.
```
spans exported: 334/s -> 78/s
Tempo (7 d):    17.7 GB -> 4.1 GB
```

**3. Drop `chat_delivery_recipient_latency_seconds` (−9,214 series, 24%).** It
was the largest metric in the store and it answers a question
`chat_delivery_latency_seconds` plus `chat_fanout_size` already covers between
them.

**4. Ten buckets → seven** on the two remaining big histograms
(`chat_delivery_latency_seconds`, 6,102 series, and `chat_group_send_seconds`,
2,140), keeping 0.1, 0.5 and 1.0 because those are the SLO and user-tolerance
boundaries. **−2,061 series, another 7%** — a reminder that bucket trimming is a
much smaller lever than deleting a metric, and costs you resolution in the tail
where you most want it.

**5. Prometheus raw retention 15 d → 10 d**, with the recorded `sli:*` and
`slo:*` series shipped to a separate tiny 90-day Prometheus. **The 30-day error
budget still works**, because `slo_rules.yml` computes it from recorded series,
not from raw buckets — that design decision is what makes this cut free.

**6. Loki 7 d → 3 d**, with `level=ERROR` routed to a separate 30-day stream.

### Result

| Component | Before | After | Change |
|---|---|---|---|
| Prometheus series | 38,412 | 27,140 | −29% |
| Prometheus RAM | 115 MB | 81 MB | −30% |
| Prometheus disk | 5.6 GB | 2.6 GB | −53% (−29% series × 15 d → 10 d) |
| Tempo disk | 17.7 GB | 4.1 GB | −77% |
| Loki disk | 0.7 GB | 0.3 GB | −57% |
| **Total disk** | **24.0 GB** | **7.0 GB** | **−71%** |
| App CPU overhead | +7.1 pts | +3.0 pts | **−58%** |
| App p99 overhead | +7 ms | +3 ms | −57% |

### Re-run Task 1 to prove the capability survived

Same blind-drill protocol, a drill neither of us had used before
(`etcd-quorum-loss`):

| Q | Time before | Time after |
|---|---|---|
| 1 What broke? | 12 s | **14 s** |
| 2 When? | 8 s | **8 s** |
| 3 How many affected? | 9 s | **9 s** |
| 4 Data lost? | 6 s | **6 s** |
| 5 Fixed? | 14 s | **16 s** |

✅ **All five still answerable, 53 s versus 49 s.** Every one of them is answered
by a metric or the prober, and none of those were cut.

### What you actually lost — say it plainly

**The ability to pull up a specific named user's trace on demand.** At a 1%
baseline, a support request of the form "Priya says her 14:32 message was slow"
has a 1-in-100 chance of having a trace, and Priya's message was probably not
slow enough to be caught by the latency policy.

Mitigation, and it is worth building:

```python
# A support engineer flags a user for 15 minutes; that user's messages are
# traced at 100% and marked so the tail sampler keeps them.
if await redis.exists(f"trace:force:{{{user.id}}}"):
    span.set_attribute("pulse.force_sample", True)
```
```yaml
- name: forced
  type: boolean_attribute
  boolean_attribute: { key: pulse.force_sample, value: true }
```

**The general principle: cut sampling rates, never cut signals.** A metric or a
probe that answers an incident question costs kilobytes and must survive every
budget cut. Traces are the expensive, high-detail layer, and detail is exactly
what you can afford to sample — as long as you keep a lever to turn it back up
for one user, right now, without a deploy.
