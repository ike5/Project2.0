# Module 20 — Observability & SLOs

**Goal:** Instrument a system whose defining property is that **nothing is a
request** — no request id, no response, no status code — using a runtime where
**your process is not the unit of observation**, and then define SLOs that
correspond to something a user would actually complain about.

⏱️ ~5 hours · **Prerequisites:** Modules 00–19.

> The Django/Python twin of
> [`spring-boot-chat-course/20-observability-and-slos`](../../spring-boot-chat-course/20-observability-and-slos/).
> The SLO mathematics, the burn-rate windows and the cardinality arithmetic are
> identical — those are properties of Prometheus and of queueing, not of a
> runtime. Three things are genuinely different and they are why this module
> exists separately: **exposing metrics from N worker processes**, **tracing
> across a WebSocket boundary that has no request scope**, and **making a
> blocked event loop visible**, which is the failure the JVM's thread-per-request
> model cannot produce and Python's cannot avoid.

---

## Why chat breaks every observability default

Every default assumes a request/response cycle:

| Standard assumption | Chat reality |
|---|---|
| A request has a response | A message has **N deliveries**, to different sockets, at different times |
| Latency = response − request | Latency spans **two connections**, two processes, and a Redis hop |
| Errors are status codes | A message that silently never arrives has no status code |
| A trace follows one execution context | Fan-out crosses a Redis Stream, a channel layer, and N sockets |
| Traffic = requests/second | Inbound rate is a **lie**; `inbound × room size` is the load |
| One process = one instrumented unit | **One pod = four worker processes with four separate registries** |

The consequence is a dashboard that is entirely green while nobody can chat.
Module 06 measured exactly that case: 200,000 messages/second logged, with an
8-second p99.

That last row is Python's contribution and it is the one nothing warns you about.

---

## RED and USE, adapted

**RED** at the service level:

| | Standard | Chat |
|---|---|---|
| **Rate** | requests/sec | **inbound msg/s AND outbound msg/s** — report both, always, plus the ratio |
| **Errors** | 5xx rate | send rejections + **undelivered messages** + sequence gaps |
| **Duration** | response time | **send → last recipient's socket write** |

Module 06 built the amplification ratio into `chat/metrics.py` for exactly this
reason: `rate(chat_messages_outbound_total) / rate(chat_messages_inbound_total)`
*is* your fan-out factor, live, and it is the number that turns "traffic looks
normal" into "traffic is normal and load has tripled because someone joined a
5,000-person room."

**USE** at the resource level. Saturation is the row people skip and the one that
predicts outages:

| Resource | Utilization | **Saturation** ← the leading indicator |
|---|---|---|
| Worker process | CPU % | **`chat_event_loop_lag_seconds`** |
| App pod | connections | **connections / measured ceiling** |
| Channel layer | ops/sec | **`blocked_clients` on the Redis shard** |
| Redis Streams | ops/sec | **`XPENDING` depth, consumer lag** |
| Postgres | active connections | **PgBouncer `cl_waiting`** |
| Outbox relay | rows/sec | **`outbox_backlog`, oldest row age** |

Every one of those was built in an earlier module because it was the thing that
broke first. This module puts them on one dashboard, in the order you look at
them during an incident.

---

## The Python problem: N processes, N registries

This is the section with no JVM equivalent, and getting it wrong makes every
number in this module wrong.

Each pod runs Uvicorn with 4 worker **processes**
([Module 07](../07-scale-out-redis-channel-layer/) measured 4 as the sweet spot;
[Module 19](../19-kubernetes-ha-and-multiregion/) explains what that does to your
HPA ceiling). `prometheus_client` keeps its registry in module globals, so there
are four of them, and `GET /metrics` is answered by whichever worker the kernel
handed the connection to.

```
scrape  ──▶  :8000  ──kernel──▶  worker 1 │ 2 │ 3 │ 4
                                    ▲
                     one random quarter of the truth
```

Your connection count is a quarter of reality, and it *changes which quarter*
between scrapes, so the graph looks like noise rather than like a bug.

### Multiprocess mode

```python
# Set BEFORE importing prometheus_client anywhere.
os.environ["PROMETHEUS_MULTIPROC_DIR"] = "/run/prom"
```

Every metric now writes to an mmap file named for its type and the writer's PID.
The exposition endpoint builds a fresh registry and merges them:

```python
def registry():
    if "PROMETHEUS_MULTIPROC_DIR" in os.environ:
        reg = CollectorRegistry()
        multiprocess.MultiProcessCollector(reg)     # merges every worker's files
        return reg
    from prometheus_client import REGISTRY
    return REGISTRY
```

That is already in Module 06's `chat/metrics.py`. Three things about it are
load-bearing:

**1. Counters and histograms merge by summing. Gauges do not, and you must say
how.** `multiprocess_mode` is not optional:

| Mode | Merge | Use for |
|---|---|---|
| `all` (default) | one series **per PID** | almost nothing — this is a cardinality leak |
| `livesum` | sum over **live** processes | **connection counts, queue depths** |
| `livemax` | max over live processes | **event-loop lag** — the worst worker is the truth |
| `min` / `max` | over all processes ever | high-water marks |

Module 06 chose `livesum` for `chat_connections_active` and `livemax` for
`chat_event_loop_lag_seconds`, and both choices are the whole reason those
metrics mean anything. `livemax` on the lag gauge is the same argument as
Module 19's liveness probe: **one blocked worker of four averages away to
nothing and maxes to the truth.**

**2. You lose exemplars.** `prometheus_client` does not support exemplars in
multiprocess mode. The metric→trace click-through that every OpenTelemetry
tutorial demonstrates — click the p99 spike, land in a slow trace — **does not
work in a multi-worker Python service.** The lab builds the replacement:
Tempo's span-metrics generator plus a `worker` attribute on every span, so you
navigate by worker and time window instead of by exemplar. It is two clicks
instead of one, and knowing this in advance saves you an afternoon of assuming
your collector is misconfigured.

**3. The files leak, and the leak is a *latency* bug.** `prometheus_client`
never deletes a dead process's files unless you call
`multiprocess.mark_process_dead(pid)`. Every worker restart — a deploy, an
OOMKill, Module 19's self-eviction — leaves a permanent set behind, and the
collector reads and merges **all** of them on every scrape. The lab measures
scrape latency going from 28 ms to 1.4 seconds after 200 dead PIDs, at which
point Prometheus starts hitting `scrape_timeout` and marks the target down.

> **The rejected alternative:** run `--workers 1` and one pod per worker, so
> each process is its own scrape target with its own registry, exemplars intact,
> no merging. It genuinely works and it is what the JVM effectively does. The
> cost is Module 19's replica arithmetic: each pod is a separate set of
> channel-layer subscriptions, so four single-worker pods cost the same 4 × 46 µs
> of Redis's single thread as one four-worker pod, plus four times the pod
> overhead and four times the DNS, TLS and connection-pool footprint. **Pick
> multiprocess mode and lose exemplars; pick one-worker pods and pay for pods.**
> Pulse picks the first, because the second click is cheaper than the pods.

---

## Histograms, never client-computed percentiles

Module 06 established this and it is worth restating because it silently breaks
everything from Module 07 onward:

```python
# RIGHT: ships bucket counts, which Prometheus can sum across workers and pods.
Histogram("chat_delivery_latency_seconds", ..., buckets=(...))

# WRONG: a gauge holding "my p99". The p99 of twelve workers is NOT the mean of
# twelve p99s, and no amount of PromQL can recover the real one from the twelve.
Gauge("chat_delivery_p99_seconds", ...)
```

The multiprocess merge makes this sharper, not softer: buckets sum correctly
across processes; a percentile gauge merges into nonsense whichever
`multiprocess_mode` you pick.

Pick buckets that straddle your SLO boundary, or the SLI is unmeasurable:

```python
buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)
#                                     ^^^ the 500 ms SLO threshold MUST be an
#                                         exact bucket edge, or you interpolate
```

---

## Cardinality

```
series = product of every label's cardinality
```

Prometheus needs roughly **3 KB of RAM per active series**.

| Label | Cardinality | Safe? |
|---|---|---|
| `worker` (a pod's PIDs) | ~4 | ✅ |
| `pod` | ~10 | ✅ |
| `type` (`message.new`, `typing.start`, …) | ~10 | ✅ |
| `outcome` (ok / rejected / dropped) | ~5 | ✅ |
| `room_size_bucket` (small/medium/large/huge) | 4 | ✅ **bucket, don't label** |
| `room` | 100,000+ | ❌ |
| `user` | 1,000,000+ | ❌❌ |
| `client_id` | unbounded | ❌❌❌ |

`chat_delivery_latency_seconds` with a `room` label at 100,000 rooms and 12
buckets is **1.2 million series ≈ 3.6 GB** for one metric.

**Per-entity detail belongs in logs and traces, not metrics.** "Which room is
slow" is a trace query (`{ chat.room = "room.7" }` in TraceQL) or a log query,
and both of those are indexed for exactly that.

> **A small mercy of multiprocess mode:** because counters and histograms merge
> by *summing* rather than by adding a `worker` label, your four worker
> processes do **not** multiply your series count. Only labels you declare do.
> The Python tax on cardinality is the mmap file count, not the series count.

---

## Tracing across a boundary that has no request scope

A trace normally follows one execution context. A Pulse message crosses:

```
client → pod A worker 2 → Postgres → outbox → Celery relay
       → Redis Stream → pod B worker 1 → 199 sockets
```

Three processes, two of them in different pods, one durable queue and one
broker. Context propagates itself across none of them.

### The trap: one span per connection

`opentelemetry-instrumentation-asgi` opens a server span when an ASGI scope
begins and ends it when the scope ends. For `http` that is a request. **For
`websocket` that is the whole connection** — potentially six hours.

Three consequences, all of which the lab measures before fixing:

1. **You see nothing until the connection closes.** The `BatchSpanProcessor`
   exports on span *end*, so a six-hour connection is a six-hour blind spot.
2. **Span limits silently drop your data.** The SDK's default
   `max_events_per_span` is 128; a busy connection produces thousands of
   receive/send events and the rest are discarded with no error.
3. **The trace is useless even if you get it.** A trace containing 40,000
   messages from one user is not a trace of anything.

The fix is to **exclude `websocket` scopes from the ASGI instrumentation and
span each message instead:**

```python
# The unit of work is a MESSAGE, not a connection.
with tracer.start_as_current_span(
    "chat.send",
    kind=SpanKind.SERVER,
    attributes={
        "chat.room": room.key,                       # "room.7" — the wire id
        "chat.room_size_bucket": bucket(n),          # NOT the size, the bucket
        "pulse.worker": WORKER,                      # ← see the next section
        "pulse.pod": POD,
    },
) as span:
    ...
```

### Propagating across the hops

```python
# Producing side: put the W3C traceparent INTO the channel-layer event.
carrier: dict[str, str] = {}
TraceContextTextMapPropagator().inject(carrier)
await self.channel_layer.group_send(room.key, {
    "type": "chat.message",
    "envelope": envelope,
    "_trace": carrier,                 # travels through Redis with the payload
})

# Consuming side: restore it before doing the work.
ctx = TraceContextTextMapPropagator().extract(event.get("_trace", {}))
with tracer.start_as_current_span("chat.fanout", context=ctx, kind=SpanKind.CONSUMER):
    ...
```

The same injection goes into the Redis Stream's fields (Module 09), the outbox
row's `trace_context` column (Module 13), and the Celery task headers.

**What *does* propagate for free, and this surprises people:** `contextvars`
are copied into tasks created with `asyncio.create_task`, and `asgiref`'s
`sync_to_async` / `database_sync_to_async` copy the context across the
threadpool boundary. So a trace survives `database_sync_to_async(...)()`
unchanged. It does **not** survive anything that serialises to Redis or to a
broker, because at that point your context is not a variable, it is a network
message.

### Span the fan-out, not the recipient

```python
span.set_attribute("chat.recipients", 199)      # an ATTRIBUTE
span.set_attribute("chat.failures", 0)
```

A span per recipient is 199× your trace volume for information a histogram
already gives you better.

### Sample in the collector, not in the app

At the safe operating point of 100,000 outbound msg/s with 199-member rooms —
about 750 fan-outs/s and roughly 8 spans per message — you are generating
**6,000 spans/second**. Head sampling at 1% throws away 99% of your errors
along with 99% of everything else.

**Tail sampling** keeps 100% of what you need:

```yaml
tail_sampling:
  decision_wait: 10s
  policies:
    - { name: errors, type: status_code, status_code: { status_codes: [ERROR] } }
    - { name: slow,   type: latency,     latency: { threshold_ms: 500 } }
    - { name: base,   type: probabilistic, probabilistic: { sampling_percentage: 5 } }
```

The lab measures **6,000 → 334 spans/second, with every slow and every failed
trace retained.** You never need a trace of a fast, successful message.

---

## Making a blocked event loop visible

This is the module's centrepiece, because it is the failure
[Module 15](../15-async-sync-and-raw-asgi/) proved is catastrophic — one
synchronous ORM call in an async consumer took p99 from **61 ms to 9,340 ms for
every connection on that worker** — and it is nearly invisible to conventional
instrumentation.

### Why `asyncio` debug mode misses it

```python
loop.set_debug(True)      # logs: Executing <Handle ...> took 0.612 seconds
```

The default `slow_callback_duration` is **100 ms**. Module 15's real-world
version is not one 612 ms call; it is a 12 ms query executed 83 times a second.
No single callback is slow. **Nothing warns, and the loop is 99.7% saturated.**

Lower the threshold to 20 ms and it fires 83 times a second, which is a log
volume problem, not a signal.

### The metric that sees it: lag, and lag *ratio*

Module 06's probe asks the loop to wake it in 250 ms and records how late it
was. Add a counter alongside the gauge:

```python
LOOP_LAG = Gauge("chat_event_loop_lag_seconds", ..., multiprocess_mode="livemax")
LOOP_LAG_TOTAL = Counter("chat_event_loop_lag_seconds_total", ...)   # accumulated lateness

while True:
    t0 = loop.time()
    await asyncio.sleep(interval)
    lag = max(0.0, loop.time() - t0 - interval)
    LOOP_LAG.labels(worker=WORKER).set(lag)
    LOOP_LAG_TOTAL.labels(worker=WORKER).inc(lag)
```

```promql
rate(chat_event_loop_lag_seconds_total[1m])
```

**Seconds of lateness accumulated per second of wall clock.** A ratio of 0 is a
healthy loop; 0.5 means half of wall-clock time is queueing delay; 1.0 means the
loop is falling behind as fast as time passes.

| | Gauge (`livemax`) | Ratio (`rate` of the counter) |
|---|---|---|
| Answers | "how bad is the worst stall right now?" | "how much of this worker's time is gone?" |
| Sees a single long block | ✅ | ⚠️ diluted over the window |
| Sees death by a thousand 12 ms queries | ⚠️ only once the queue builds | ✅ **immediately** |
| Good for | alerting on a stall | **alerting on saturation** |

Keep both. The lab measures baseline **0.4 ms / 0.004** going to **1.94 s /
0.89** under Module 15's failure.

### Why the victim's trace never contains the culprit

Here is the insight that makes tracing an event-loop runtime different.

Alice's message is slow. You open its trace. Every span in it is fast — the
Redis call took 2 ms, the fan-out took 3 ms — and there is a **nine-second gap**
between the parent span starting and the first child span starting. The trace
tells you *when* the time went, and nothing about *where*.

The culprit is a different connection's coroutine, in a different trace,
possibly in a different room, that never appears in Alice's trace at all,
because they share nothing except an event loop.

**Correlate by worker and time.** That is why every span carries
`pulse.worker`, and why the lab adds a watchdog that emits a span *for the stall
itself*:

```python
# When the lag probe sees a sustained stall, emit a zero-parent span covering it.
span = tracer.start_span("asyncio.loop_stall", start_time=stall_started_ns)
span.set_attribute("pulse.worker", WORKER)
span.set_attribute("asyncio.lag_ms", lag * 1000)
span.set_attribute("asyncio.tasks_alive", len(asyncio.all_tasks(loop)))
span.set_status(Status(StatusCode.ERROR, "event loop stalled"))
span.end(end_time=stall_ended_ns)
```

Now the TraceQL query that answers "why was Alice's message slow" is:

```
{ name = "asyncio.loop_stall" && span.pulse.worker = "pid-10" }
```

with the time range set to Alice's gap. **One query, and the answer names the
worker, the lag, and how many tasks were queued behind it.**

---

## Structured logs, correlated across the Redis hop

```python
LOGGING = {
    "version": 1,
    "formatters": {"json": {"()": "pythonjsonlogger.jsonlogger.JsonFormatter",
                            "format": "%(asctime)s %(levelname)s %(name)s %(message)s"}},
    "filters": {"trace": {"()": "chat.logging.TraceContextFilter"}},
    ...
}
```

`TraceContextFilter` pulls `trace_id` and `span_id` out of the current OTel
context and puts them on every record, plus `worker`, `pod` and `room`. Loki
indexes `service`, `pod` and `level` as labels — **never `trace_id`, which is
unbounded and is the Loki equivalent of the cardinality bomb above.** Trace ids
live in the log *line*, where Loki's full-text index finds them.

The correlation id that survives the Redis hop is the trace id itself, injected
into the channel-layer event and the stream fields. That is what makes this work:

```
p99 panel → span-metrics → the slow trace → its trace_id
          → Loki: {service="pulse"} |= "<trace_id>"
          → the exact log lines from THREE processes, in order
```

---

## SLIs, SLOs and error budgets

An SLI must be something a user would complain about.

| Candidate | Good? | Why |
|---|---|---|
| Worker CPU under 80% | ❌ | Nobody has ever noticed CPU |
| Event-loop lag under 10 ms | ❌ | It is a *leading indicator*, not an experience. Alert on it, don't SLO it |
| p99 fan-out (enqueue) latency | ❌ | Measures the wrong half — see the lab |
| **Delivery success rate** | ✅ | "My message didn't arrive" |
| **Delivery latency p99** | ✅ | "Messages are slow" |
| **Connection success rate** | ✅ | "I can't connect" |
| **Sequence integrity** | ✅ | "Messages are missing from history" |

Pulse's four:

```
SLI 1  Delivery success    delivered / (published × recipients)      >= 99.99%
SLI 2  Delivery latency    fraction delivered under 500 ms           >= 99.9%
SLI 3  Connection success  successful handshakes / attempts          >= 99.9%
SLI 4  Sequence integrity  rooms with a permanent gap / rooms        <  0.01%
```

**SLI 1 is the hard one**, because you cannot count what did not happen. The lab
measures it twice: server-side (attempts minus failures over expected
recipients), which misses the last hop, and client-side with a **synthetic
prober**, which is the only thing that closes it.

### Error budgets and burn rate

99.9% over 30 days is **43 minutes**. 99.99% is **4.3 minutes**.

| Budget remaining | Policy |
|---|---|
| > 50% | Ship freely |
| 10–50% | Ship, prioritise reliability work |
| **< 10%** | **Freeze features on the delivery path** |
| Exhausted | Freeze, incident review |

Alerting on "the SLO is violated" is alerting after the fact. Alert on the
**rate of consumption**, with two windows:

```
14.4× burn over 1 h   (and 5 m)  → a 30-day budget gone in ~2 days   → page
6×    burn over 6 h   (and 30 m) → gone in ~5 days                   → page
1×    burn over 3 d   (and 6 h)  → on track to exhaust exactly       → ticket
```

**The two-window condition is what makes it usable.** A single short window
pages on every 30-second blip; requiring both a short and a long window to be
burning means a hiccup is ignored and a real problem pages within minutes.

---

## Alert on symptoms, not causes

| Bad alert | Why | Better |
|---|---|---|
| `redis_cpu > 80%` | Users do not experience CPU | `sli:delivery_latency < 0.999` |
| `pod_restarts > 0` | Restarts can be routine | `sli:connection_success < 0.999` |
| `disk_usage > 80%` | Not yet a problem | `predict_linear(disk_avail[6h], 24*3600) < 0` |

**Cause-based alerts fire constantly and get muted; symptom-based alerts fire
when something is wrong.** Keep cause metrics on dashboards for diagnosis and
alert on symptoms.

Two exceptions, both earned in earlier modules:

- **Runway alerts.** Anything that can be *exhausted* — disk, Postgres
  partitions, error budget, connection capacity, Redis memory under
  `noeviction` — deserves a predictive alert, because by the time it is a
  symptom it is an outage.
- **`chat_event_loop_lag_seconds`.** It is a cause, and you should page on it
  anyway, because Module 15 proved the gap between "this worker is saturated"
  and "every one of its 5,000 connections has a 9-second p99" is about four
  seconds. There is no time to wait for the symptom.

---

## What's next

The lab stands up [`infra/obs/compose.obs.yml`](../infra/obs/) — Prometheus,
Grafana, Loki, Tempo and an OpenTelemetry collector — gets multi-worker metrics
exposition working and measures what it costs, instruments true end-to-end
delivery latency against the enqueue number everyone accidentally measures,
propagates trace context across the channel layer and the Redis Stream, makes
Module 15's blocking call visible in both a metric and a trace, defines the four
SLOs with two-window burn-rate alerts, and then re-runs Module 18's drills to
find out whether the dashboard actually explains them.

See you in [`lab.md`](./lab.md).
