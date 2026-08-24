# Lab 20 — Instrument What Users Notice

**You'll:** stand up Prometheus, Grafana, Loki, Tempo and an OpenTelemetry
collector; get metrics out of four worker processes and measure what that costs;
measure true end-to-end delivery against the enqueue number everyone
accidentally reports; trace a message across the channel layer and the Redis
Stream; make Module 15's blocking call visible in a metric *and* a trace; define
four SLOs with two-window burn-rate alerts; and then re-run Module 18's drills
to find out whether the dashboard actually explains them.

⏱️ ~110 min. Needs ~2 GB on top of whatever stack you are measuring.

All paths are relative to the repo root. The observability tier is
[`infra/obs/`](../infra/obs/); the instrumentation lives in
[`code/`](./code/).

---

## Part A — The stack

Bring up the thing you are measuring **first** — `compose.obs.yml` joins its
network:

```bash
docker compose -p pulse-ha -f infra/ha/compose.ha.yml up -d --wait
```

Now the config files. [`infra/obs/compose.obs.yml`](../infra/obs/compose.obs.yml)
already exists and is heavily commented; these four do not, because the settings
in them are the lesson.

`infra/obs/prometheus.yml`:
```yaml
global:
  scrape_interval: 15s
  scrape_timeout: 10s               # remember this number for Part B
  external_labels: { cluster: pulse-local }

rule_files: [ /etc/prometheus/rules/*.yml ]

scrape_configs:
  - job_name: pulse
    metrics_path: /metrics
    static_configs:
      - targets: [ "pulse-1:8000", "pulse-2:8000", "pulse-3:8000" ]
    relabel_configs:
      - source_labels: [__address__]
        regex: '([^:]+):.*'
        target_label: pod           # so `max by (pod)` works
        replacement: '$1'

  - job_name: otel-collector        # span metrics + the collector's own health
    static_configs: [ { targets: [ "pulse-otelcol:8889" ] } ]

  - job_name: redis
    static_configs: [ { targets: [ "pulse-redis-exporter:9121" ] } ]

  - job_name: postgres
    static_configs: [ { targets: [ "pulse-pg-exporter:9187" ] } ]

  - job_name: prober                # Part F
    static_configs: [ { targets: [ "host.docker.internal:9200" ] } ]
```

`infra/obs/tempo.yaml` — the two blocks that matter:
```yaml
server: { http_listen_port: 3200 }

distributor:
  receivers:
    otlp: { protocols: { grpc: { endpoint: "0.0.0.0:4317" } } }

storage:
  trace:
    backend: local
    local: { path: /var/tempo/blocks }
    wal:   { path: /var/tempo/wal }

# THIS is how you get the metric->trace path back after losing exemplars.
# Tempo derives RED metrics from spans and remote-writes them to Prometheus, so
# a latency histogram exists that is DEFINITELY backed by traces you still have.
metrics_generator:
  processor:
    span_metrics:
      # Dimensions become labels. Keep them low-cardinality for exactly the
      # reasons in the README: pulse.worker (~12) and room_size_bucket (4) are
      # fine; chat.room (100,000) would take Prometheus down from the trace side.
      dimensions: [ pulse.worker, pulse.pod, chat.room_size_bucket ]
    service_graphs: {}
  storage:
    path: /var/tempo/generator
    remote_write:
      - url: http://pulse-prometheus:9090/api/v1/write
        send_exemplars: true
overrides:
  defaults:
    metrics_generator:
      processors: [ span-metrics, service-graphs ]
```

`infra/obs/otel-collector.yaml`:
```yaml
receivers:
  otlp:
    protocols:
      grpc: { endpoint: "0.0.0.0:4317" }
      http: { endpoint: "0.0.0.0:4318" }
  filelog:
    include: [ /var/lib/docker/containers/*/*-json.log ]
    operators:
      - type: json_parser                        # Docker's envelope
        timestamp: { parse_from: attributes.time, layout: '%Y-%m-%dT%H:%M:%S.%fZ' }
      - type: json_parser                        # Pulse's own structured line
        parse_from: attributes.log
        on_error: send                           # not every container is ours
      # Promote trace_id/span_id to real trace context so Grafana can pivot
      # log -> trace. In the LINE, never as a Loki label (see the README).
      - type: trace_parser
        trace_id: { parse_from: attributes.trace_id }
        span_id:  { parse_from: attributes.span_id }

processors:
  # FIRST in every pipeline. Tail sampling buffers whole traces; without a
  # limiter the collector OOMs before it drops anything, and an OOMed collector
  # loses the traces from the incident that killed it.
  memory_limiter: { check_interval: 1s, limit_mib: 600, spike_limit_mib: 150 }

  tail_sampling:
    decision_wait: 10s        # must exceed your p99.9 trace duration or slow
                              # traces are judged before they finish
    num_traces: 100000
    policies:
      - { name: errors, type: status_code, status_code: { status_codes: [ERROR] } }
      - { name: slow,   type: latency,     latency: { threshold_ms: 500 } }
      - { name: base,   type: probabilistic, probabilistic: { sampling_percentage: 5 } }

  batch: { timeout: 2s, send_batch_size: 1024 }

exporters:
  otlp/tempo: { endpoint: pulse-tempo:4317, tls: { insecure: true } }
  loki:       { endpoint: http://pulse-loki:3100/loki/api/v1/push }
  prometheus: { endpoint: "0.0.0.0:8889" }

service:
  extensions: [ health_check ]
  pipelines:
    traces:
      receivers: [otlp]
      processors: [memory_limiter, tail_sampling, batch]
      exporters: [otlp/tempo]
    logs:
      receivers: [filelog, otlp]
      processors: [memory_limiter, batch]
      exporters: [loki]
extensions:
  health_check: { endpoint: "0.0.0.0:13133" }
```

Datasources, rules, and the custom Postgres queries the exporter needs:
```bash
mkdir -p infra/obs/rules infra/obs/grafana/provisioning/datasources infra/obs/grafana/dashboards
cp 20-observability-and-slos/code/slo_rules.yml infra/obs/rules/slo.yml
cat > infra/obs/pg-queries.yaml <<'YAML'
pg_replication:
  query: "SELECT application_name, EXTRACT(EPOCH FROM replay_lag) AS replay_lag_seconds
           FROM pg_stat_replication"
  metrics:
    - application_name: { usage: LABEL }
    - replay_lag_seconds: { usage: GAUGE, description: "Replica replay lag" }
pg_partitions:
  # Module 13's runway metric. Running out of future partitions is a total write
  # outage whose error message ('no partition of relation found for row') sounds
  # like a bug in your code.
  query: "SELECT count(*) AS ahead FROM pg_class c JOIN pg_inherits i ON i.inhrelid = c.oid
           WHERE c.relname ~ '^messages_[0-9]{6}$' AND c.relname > to_char(now(), 'YYYYMM')"
  metrics:
    - ahead: { usage: GAUGE, description: "Future time partitions that exist" }
YAML
```

`infra/obs/grafana/provisioning/datasources/all.yml`:
```yaml
apiVersion: 1
datasources:
  - { name: Prometheus, type: prometheus, uid: prom, url: http://pulse-prometheus:9090, isDefault: true }
  - name: Loki
    type: loki
    uid: loki
    url: http://pulse-loki:3100
    jsonData:
      derivedFields:
        # Turns a trace_id in a LOG LINE into a link to the trace. This is the
        # replacement for exemplars in the log direction.
        - { name: TraceID, matcherRegex: '"trace_id":"(\w+)"', url: '$${__value.raw}', datasourceUid: tempo }
  - name: Tempo
    type: tempo
    uid: tempo
    url: http://pulse-tempo:3200
    jsonData:
      tracesToLogsV2:
        datasourceUid: loki
        filterByTraceID: true
        tags: [ { key: 'pulse.pod', value: 'pod' } ]
      tracesToMetrics:
        datasourceUid: prom
        tags: [ { key: 'pulse.worker', value: 'worker' } ]
```

```bash
docker compose -p pulse-obs -f infra/obs/compose.obs.yml up -d --wait
docker compose -p pulse-obs -f infra/obs/compose.obs.yml ps --format 'table {{.Name}}\t{{.Status}}'
```
**Expected:**
```
NAME                   STATUS
pulse-grafana          Up 40 seconds
pulse-loki             Up 1 minute (healthy)
pulse-otelcol          Up 50 seconds (healthy)
pulse-prometheus       Up 1 minute (healthy)
pulse-tempo            Up 1 minute (healthy)
pulse-redis-exporter   Up 1 minute
pulse-pg-exporter      Up 1 minute
```

> ⚠️ **`network pulse-ha_default declared as external, but could not be found`**
> means you started this stack first. Bring up the thing you are measuring, then
> this. It reads like a bug in the compose file and is not one.

---

## Part B — Getting metrics out of four processes

**Do this before anything else, because every number in the rest of the lab
depends on it.**

Each `pulse-N` container runs Uvicorn with 4 worker processes. `prometheus_client`
keeps its registry in module globals, so there are four registries, and `GET
/metrics` is answered by whichever worker `accept()`ed the scrape.

Scrape by hand, six times, with the app holding a known number of connections:

```bash
k6 run -e HOST=localhost:8080 -e ROOMS=100 --vus 10000 --duration 20m \
       06-load-testing-harness/code/pulse-load.js &
sleep 90
for i in $(seq 6); do
  curl -s localhost:8001/metrics | grep '^chat_connections_active'
done
```
**Expected — and this is the bug:**
```
chat_connections_active{worker="pid-9"}  2514.0
chat_connections_active{worker="pid-11"} 2489.0
chat_connections_active{worker="pid-9"}  2517.0
chat_connections_active{worker="pid-12"} 2503.0
chat_connections_active{worker="pid-10"} 2498.0
chat_connections_active{worker="pid-12"} 2506.0
```

❌ **Roughly a quarter of the truth, and a different quarter each time.** The node
holds ~10,000 connections. A graph of this looks like noise around 2,500 and
teaches you nothing — worse, `sum()` over the scrape targets gives you 7,500 and
you will believe it.

### Turn on multiprocess mode

```python
# pulse/asgi.py — BEFORE prometheus_client is imported anywhere.
import os
os.environ.setdefault("PROMETHEUS_MULTIPROC_DIR", "/run/prom")
os.makedirs("/run/prom", exist_ok=True)
```
```yaml
# infra/ha/compose.ha.yml, on each pulse-N service
environment:
  PROMETHEUS_MULTIPROC_DIR: /run/prom
tmpfs:
  - /run/prom:size=64m
```
```bash
docker compose -p pulse-ha -f infra/ha/compose.ha.yml up -d --force-recreate pulse-1
sleep 90
for i in $(seq 3); do curl -s localhost:8001/metrics | grep '^chat_connections_active'; done
```
**Expected:**
```
chat_connections_active 10043.0
chat_connections_active 10041.0
chat_connections_active 10044.0
```
✅ **Stable, and the whole node.** Note the `worker` label is gone: with
`multiprocess_mode="livesum"` the collector sums across live processes and drops
the label, which is exactly what you want for a capacity number.

### `multiprocess_mode` is not optional

Change one gauge to the default and look:

```python
LOOP_LAG = Gauge("chat_event_loop_lag_seconds", ..., ["worker"])   # no mode
```
```
chat_event_loop_lag_seconds{worker="pid-9",pid="9"}   0.0004
chat_event_loop_lag_seconds{worker="pid-10",pid="10"} 0.0003
chat_event_loop_lag_seconds{worker="pid-11",pid="11"} 0.0005
chat_event_loop_lag_seconds{worker="pid-12",pid="12"} 0.0004
```
❌ **The default is `all`: one series per PID, forever, including dead ones.**
Across a week of deploys that is a slow cardinality leak nobody attributes to a
Gauge with four labels.

| Metric | Mode | Why |
|---|---|---|
| `chat_connections_active` | `livesum` | a pod total |
| `chat_outbound_queue_depth` | `livesum` | a pod total |
| `chat_event_loop_lag_seconds` | **`livemax`** | **the worst worker is the truth** |
| `chat_max_connections` | `max` | every worker reports the same constant |

`livemax` on the lag gauge is the same argument as Module 19's liveness probe,
one level down: one blocked worker of four averages away to nothing.

### The file leak, which is a latency bug

```bash
docker exec pulse-ha-pulse-1-1 ls /run/prom | wc -l
docker exec pulse-ha-pulse-1-1 sh -c 'time curl -s -o /dev/null localhost:8000/metrics'
```
**Expected, fresh:**
```
48
real    0m0.028s
```

Now restart the workers 50 times — which is what a week of deploys, OOMKills and
Module 19 self-evictions looks like:

```bash
for i in $(seq 50); do docker exec pulse-ha-pulse-1-1 pkill -HUP -f 'uvicorn'; sleep 1; done
docker exec pulse-ha-pulse-1-1 ls /run/prom | wc -l
docker exec pulse-ha-pulse-1-1 sh -c 'time curl -s -o /dev/null localhost:8000/metrics'
```
**Expected:**
```
812
real    0m1.421s
```
❌ **50× the files, 50× the scrape time.** `prometheus_client` writes one mmap
file per (metric type, PID) and **never deletes them**. The collector reads and
merges all of them on every scrape.

At `scrape_timeout: 10s` you have roughly 350 dead workers of headroom, after
which Prometheus marks the target **down** and you lose the metrics for a node
that is serving perfectly. Nothing in any log says why.

```python
# chat/metrics.py — Uvicorn's master knows when a worker exits.
from prometheus_client import multiprocess

def on_worker_exit(pid: int) -> None:
    multiprocess.mark_process_dead(pid)   # merges its counters, deletes its gauges
```
```bash
docker compose -p pulse-ha -f infra/ha/compose.ha.yml up -d --force-recreate pulse-1
# ... repeat the 50 restarts ...
docker exec pulse-ha-pulse-1-1 ls /run/prom | wc -l
```
```
48
```
✅ Constant.

> **And one more, which Module 19 pays for:** `tmpfs` (and Kubernetes'
> `emptyDir: {medium: Memory}`) is charged to the container's **memory** cgroup.
> 41 MiB of stale metric files is 41 MiB off your connection budget — about 900
> connections at ≈45 KB each — and it is invisible to `tracemalloc`, to `py-spy`
> and to every Python-level memory profile, because Python is not holding it.

### Exemplars: confirm they are gone

```bash
curl -s -H 'Accept: application/openmetrics-text' localhost:8001/metrics \
  | grep -c '#'          # exemplars are appended after a '#' on a bucket line
```
```
0
```
❌ **`prometheus_client` does not support exemplars in multiprocess mode.** The
"click the p99 spike, land in the slow trace" workflow from every OpenTelemetry
tutorial does not work here. Part D builds the replacement.

---

## Part C — Measure delivery, not enqueue

Module 06's `chat_group_send_seconds` measures how long `group_send()` took to
**enqueue** a fan-out. That is a real number and it is not delivery latency —
`group_send` returns as soon as the channel layer has the message.

Add the real one. `chat/delivery_metrics.py` is
[`code/delivery_metrics.py`](./code/delivery_metrics.py); wire it into the
delivery path:

```python
async def chat_message(self, event: dict) -> None:
    envelope = event["envelope"]
    origin_ts = envelope["ts"]              # Module 05's field, set by the SENDER
    targets = self.room_local_sockets()

    failures = 0
    for consumer in targets:
        try:
            await consumer.send_json(envelope)
            record_recipient(origin_ts)
        except Exception:
            failures += 1                   # a failed delivery is an SLI event
    record_delivery(origin_ts, len(targets), failures)
```

`origin_ts` travelling **inside the envelope** is what makes this work at all:
the send happened on one worker in one container and the delivery happens on
another, so there is no shared clock to subtract from except the one the message
carries.

```bash
sleep 300
curl -s localhost:8001/metrics | grep -E 'chat_(group_send|delivery_latency)_seconds_(bucket|count)' \
  | grep -E 'le="0.025"|le="0.5"|_count'
```
**Expected:**
```
chat_group_send_seconds_bucket{le="0.025"}        184102
chat_group_send_seconds_count                     186204
chat_delivery_latency_seconds_bucket{le="0.5"}   36894011
chat_delivery_latency_seconds_count              37041988
```
```promql
histogram_quantile(0.99, sum by (le) (rate(chat_group_send_seconds_bucket[5m])))
histogram_quantile(0.99, sum by (le) (rate(chat_delivery_latency_seconds_bucket[5m])))
```
```
0.022      <-- enqueue: 22 ms
0.261      <-- REAL: 261 ms
```

✅ **11.9× apart**, and 261 ms is exactly the Module 18 HA baseline the load
generator has been reporting all along — which is the point. The client-side
harness had the right number; the server had a smaller one and no reason to
doubt it.

Keep both, and make the descriptions do the arguing:
```python
GROUP_SEND       = Histogram("chat_group_send_seconds",
                             "Time for group_send() to ENQUEUE a fan-out. NOT delivery.")
DELIVERY_LATENCY = Histogram("chat_delivery_latency_seconds",
                             "origin_ts until the LAST recipient's socket was written")
```

> The enqueue number is not wrong; it answers "is the channel layer keeping up?"
> It is the number that would have made Module 06's 200,000 msg/s server with an
> 8-second p99 look perfectly healthy.

---

## Part D — Tracing across the WebSocket boundary

### First, see the trap

Instrument naively and look at what you get:

```python
from opentelemetry.instrumentation.asgi import OpenTelemetryMiddleware
application = OpenTelemetryMiddleware(application)          # the obvious thing
```
```bash
sleep 120
curl -s 'localhost:3200/api/search?tags=service.name%3Dpulse&limit=5' | jq -r \
  '.traces[] | "\(.rootTraceName)  dur=\(.durationMs)ms  spans=\(.spanSet.matched)"'
```
**Expected:**
```
(nothing)
```
```bash
# Where did they go? Ask for traces that are still open.
docker logs pulse-otelcol 2>&1 | grep -i 'span' | tail -3
```
```
info  Traces exported  {"#spans": 0}
```

❌ **Nothing, for two minutes.** `OpenTelemetryMiddleware` opens a server span
when an ASGI scope begins and ends it when the scope ends. For `websocket` that
is the **whole connection** — and `BatchSpanProcessor` exports on span *end*.
Ten thousand six-hour spans are ten thousand six-hour blind spots.

Wait for a client to disconnect and look at one:
```bash
curl -s "localhost:3200/api/traces/$TRACE_ID" | jq '.batches[0].scopeSpans[0].spans[0]
  | {name, events: (.events|length), attributes: (.attributes|length)}'
```
```json
{ "name": "/ws/room/7/ websocket", "events": 128, "attributes": 11 }
```
❌ **Exactly 128 events.** The SDK's `max_events_per_span` default is 128, and
this connection produced 4,100 receive/send events. The other 3,972 were
discarded with no error, no log, and no metric.

### The fix: span the message

Use [`code/otel_ws.py`](./code/otel_ws.py):

```python
from chat.tracing import configure_tracing, TracedConsumerMixin, excluded_urls_for_asgi

configure_tracing()
application = OpenTelemetryMiddleware(application, excluded_urls=excluded_urls_for_asgi())

class ChatConsumer(TracedConsumerMixin, AsyncJsonWebsocketConsumer):
    ...
```

```bash
sleep 60
curl -s 'localhost:3200/api/search?tags=service.name%3Dpulse&limit=3' | jq -r \
  '.traces[] | "\(.rootTraceName)  dur=\(.durationMs)ms"'
```
**Expected:**
```
chat.message.create  dur=284ms
chat.message.create  dur=196ms
chat.connect         dur=41ms
```
✅ **The unit of work is a message.** Connection lifetime is a gauge
(`chat_connections_active`), which is what it always should have been.

### Propagate across the two hops that lose context

```bash
TRACE=$(curl -s 'localhost:3200/api/search?tags=service.name%3Dpulse%20name%3Dchat.message.create&limit=1' \
        | jq -r '.traces[0].traceID')
curl -s "localhost:3200/api/traces/$TRACE" | jq -r \
  '.batches[].scopeSpans[].spans[] | "\(.name)  \(.attributes[]|select(.key=="pulse.worker").value.stringValue)"'
```
**Expected before wiring the propagation — three separate traces:**
```
chat.message.create   pid-9
```
```
chat.fanout           pid-27      <-- a DIFFERENT trace id
```

The channel layer is a Redis round trip. A `contextvar` does not survive it.

```python
# sending side
event["_trace"] = inject()
await self.channel_layer.group_send(self.room.key, event)

# receiving side
with fanout_span(self.room.key, len(targets), event.get("_trace")):
    ...
```

Same for the Redis Stream (Module 09) and the outbox row (Module 13):
```python
await state.xadd(f"room:{{{room.slug}}}:stream", {**fields, **inject()})
```
```sql
INSERT INTO outbox (aggregate_id, event_type, payload, trace_context)
VALUES (%s, %s, %s::jsonb, %s::jsonb)
```

**Expected after — one trace, three processes:**
```
chat.message.create          pulse-1  pid-9    284.1ms
├── chat.dedup               pulse-1  pid-9      0.9ms
├── chat.sequence            pulse-1  pid-9      1.4ms
├── db.insert messages       pulse-1  pid-9      6.2ms
├── db.insert outbox         pulse-1  pid-9      1.1ms
└── (async)
    outbox.relay             celery   pid-4     38.4ms   outbox.age_ms=34
    └── redis.xadd           celery   pid-4      1.7ms
        └── (async)
            chat.fanout      pulse-3  pid-27   211.8ms   chat.recipients=199
            ├── redis.xreadgroup       pid-27     2.2ms
            ├── deliver.batch          pid-27   206.4ms
            └── redis.xack             pid-27     1.0ms
```

✅ **`outbox.age_ms=34`** tells you the relay was 34 ms behind without you having
to correlate a backlog gauge by hand.

> **What propagates for free, and it surprises people:** `contextvars` are copied
> into `asyncio.create_task`, and `asgiref` copies the context across
> `database_sync_to_async`'s threadpool boundary. A trace survives
> `await database_sync_to_async(Room.objects.get)(slug=slug)` unchanged. It does
> not survive anything that serialises to Redis or a broker, because at that
> point your context is not a variable, it is a network message.

### Tail sampling

```bash
curl -s localhost:8889/metrics | grep -E 'otelcol_processor_tail_sampling_(count_traces_sampled|global_count_traces_sampled)'
```
**Expected:**
```
otelcol_receiver_accepted_spans{...}          6014     # per second, at the knee
otelcol_exporter_sent_spans{exporter="otlp/tempo"}  334
```
✅ **6,000 → 334 spans/second, an 18× reduction, with 100% of slow and errored
traces retained.** You never need a trace of a fast, successful message.

Prove the retention rather than trusting it:
```bash
curl -s 'localhost:3200/api/search?q=%7B%20duration%20%3E%20500ms%20%7D&limit=100' \
  | jq '.traces | length'
```
```
100
```

### Get the metric→trace path back without exemplars

Part B established that multiprocess Python cannot emit exemplars. Tempo's
span-metrics generator is the replacement: it derives a latency histogram
**from spans you still have**, labelled by worker.

```promql
histogram_quantile(0.99, sum by (le, pulse_worker) (
  rate(traces_spanmetrics_latency_bucket{span_name="chat.fanout"}[5m])))
```
```
{pulse_worker="pid-27"}  0.213
{pulse_worker="pid-9"}   0.198
{pulse_worker="pid-41"}  0.204
```

Two clicks instead of one: the panel names the worker, and a TraceQL query on
that worker and time range names the trace.

```
{ span.pulse.worker = "pid-27" && duration > 500ms }
```

---

## Part E — Make Module 15's blocking call visible

**The centrepiece.** Module 15 measured one synchronous ORM call in an async
consumer taking p99 from **61 ms to 9,340 ms for every connection on that
worker**. Reproduce it and watch three instruments react.

Wire the watchdog ([`code/loop_watchdog.py`](./code/loop_watchdog.py)) into
`lifespan.startup`, then inject the bug:

```python
# chat/consumers.py — the cardinal sin, on purpose.
async def _on_message_create(self, content):
    #  WRONG: the ORM is synchronous and this runs ON the event loop.
    #  ~12 ms on a cold, unindexed lookup. Not slow. Just not free.
    room = Room.objects.get(slug=self.slug)          # was: database_sync_to_async
    ...
```

```bash
docker compose -p pulse-ha -f infra/ha/compose.ha.yml up -d --force-recreate pulse-1
sleep 240
```

### Instrument 1 — asyncio's own debug mode, which misses it

```bash
docker logs pulse-ha-pulse-1-1 2>&1 | grep -c 'Executing <Handle'
```
**Expected:**
```
0
```
❌ **Not one warning.** `loop.set_debug(True)`'s `slow_callback_duration` defaults
to **100 ms** and no single call is slow — it is a 12 ms query run 83 times a
second. Lower it to 20 ms and it fires 83 times a second, which is a log-volume
problem, not a signal. (The `took 0.612 seconds` example in
[`cheatsheets/troubleshooting.md`](../cheatsheets/troubleshooting.md) §3 is the
*easy* version of this failure. This is the common one.)

### Instrument 2 — the lag gauge and the lag ratio

```bash
curl -s localhost:8001/metrics | grep -E '^chat_event_loop_lag'
```
**Expected:**
```
chat_event_loop_lag_seconds        1.9412
chat_event_loop_lag_seconds_total{worker="pid-9"}  173.84
```
```promql
max by (pod) (chat_event_loop_lag_seconds)
max by (pod) (rate(chat_event_loop_lag_seconds_total[1m]))
```
```
1.941        <-- the size of the current stall
0.891        <-- 89% of wall-clock time is queueing delay
```

| | Baseline | With the blocking call |
|---|---|---|
| `chat_event_loop_lag_seconds` (livemax) | **0.0004** | **1.94** |
| lag ratio, `rate(..._total[1m])` | **0.004** | **0.89** |
| delivery p99 | **61 ms** | **9,340 ms** |
| worker CPU | 61% | **58%** ← unchanged |
| `asyncio` slow-callback warnings | 0 | **0** |

✅ **The two lag numbers are the only instruments that moved before the users
did.** CPU went *down*, because a blocked loop is waiting, not working.

The ratio is the one to alert on:
```
0.00  healthy
0.30  page (slo_rules.yml: EventLoopSaturated)
0.89  every connection on this worker has a multi-second p99
```

### Instrument 3 — the trace, and why the victim's trace is useless

Find a slow message and open it:

```bash
curl -s 'localhost:3200/api/search?q=%7B%20duration%20%3E%205s%20%7D&limit=1' | jq -r '.traces[0].traceID'
curl -s "localhost:3200/api/traces/$TRACE" | jq -r \
  '.batches[].scopeSpans[].spans[] | "\(.name)  start=\(.startTimeUnixNano)  dur=\((.endTimeUnixNano|tonumber - (.startTimeUnixNano|tonumber))/1e6)ms"'
```
**Expected:**
```
chat.message.create   start=...000   dur=9184.2ms
chat.dedup            start=...107   dur=0.9ms
chat.sequence         start=...109   dur=1.2ms
db.insert messages    start=...110   dur=5.8ms
```
```
chat.message.create  ├──────────────── 9,184 ms ─────────────────┤
chat.dedup                                             ├─0.9ms─┤
                     └──── 9,176 ms of NOTHING ───────┘
```

❌ **Every child span is fast, and there is a nine-second gap before the first
one.** The trace tells you exactly *when* the time went and nothing at all about
*where*. The work that consumed it belonged to a different connection, in a
different trace, possibly in a different room. **They share nothing but an event
loop.**

Now the watchdog's span:

```bash
curl -s 'localhost:3200/api/search?q=%7B%20name%20%3D%20%22asyncio.loop_stall%22%20%7D&limit=3' \
  | jq -r '.traces[] | "\(.startTimeUnixNano) dur=\(.durationMs)ms"'
```
```
...  dur=9210ms
...  dur=8940ms
...  dur=9402ms
```
```bash
curl -s "localhost:3200/api/traces/$STALL_TRACE" | jq -r '.batches[0].scopeSpans[0].spans[0].attributes[]
  | "\(.key)=\(.value.stringValue // .value.intValue // .value.doubleValue)"'
```
```
pulse.worker=pid-9
pulse.pod=pulse-1
asyncio.lag_peak_ms=1941.2
asyncio.duration_ms=9210.4
asyncio.tasks_alive=5014
```

✅ **`asyncio.tasks_alive=5014`** — this stall delayed five thousand people. A
stall with 12 tasks alive delayed nobody and you can stop reading.

**The query that closes the incident**, with the time range set to the victim's
gap:
```
{ name = "asyncio.loop_stall" && span.pulse.worker = "pid-9" }
```

Then confirm what was on the loop:
```bash
docker exec pulse-ha-pulse-1-1 py-spy dump --pid 9
```
```
Thread 9 (active): "MainThread"
    execute (psycopg/cursor.py:732)
    _execute_sql (django/db/models/sql/compiler.py:1562)
    get (django/db/models/query.py:645)
    _on_message_create (chat/consumers.py:118)      <-- there it is
```

> **The generalisable rule:** in an event-loop runtime the culprit is never in
> the victim's trace. Put the worker id on every span, emit a span for the stall
> itself, and correlate by **worker and time window**. That is why
> `chat/tracing.py` sets `pulse.worker` on a `Resource` rather than
> per-call-site — it must be impossible to forget.

Fix it and re-measure:
```python
room = await database_sync_to_async(Room.objects.get)(slug=self.slug)
```
```
chat_event_loop_lag_seconds   0.0005
lag ratio                     0.005
delivery p99                  63 ms
asyncio.loop_stall spans      0
```

---

## Part F — Four SLOs, a prober, and burn-rate alerts

### The prober

SLI 1 is delivery success and you cannot count what did not happen. Server-side
metrics count a `send()` that did not raise as a success, so they miss a frame
buffered for a vanished client, a `group_expiry` expiry making a live socket deaf
(Module 11), and the ~15% the Pub/Sub channel layer lost on Module 07's
`docker pause` with **zero errors anywhere**.

```bash
python 20-observability-and-slos/code/prober.py \
  --sender-node localhost:8001 --receiver-node localhost:8002 \
  --room probe --port 9200 &
sleep 120
curl -s localhost:9200/metrics | grep -E '^chat_probe'
```
**Expected in steady state:**
```
chat_probe_delivered_total    12.0
chat_probe_undelivered_total   0.0
chat_probe_late_total          0.0
chat_probe_latency_seconds_sum 3.19
```

The two nodes matter. Point both sockets at the same node and the probe never
crosses the channel layer, reporting 100% success during a total backbone
outage — the prober warns you about this on startup for exactly that reason.

Run Module 18's Redis pause drill and watch the distinction the prober exists to
make:
```bash
docker pause pulse-ha-redis-1-1 && sleep 20 && docker unpause pulse-ha-redis-1-1
curl -s localhost:9200/metrics | grep -E 'undelivered|late'
```
```
chat_probe_undelivered_total  2.0
chat_probe_late_total         2.0
```
✅ **Two messages were counted undelivered at the 5-second deadline and then
arrived.** The Streams backbone buffered them (Module 09) — they were **late,
not lost**, and no server-side metric can tell those apart.

### The rules

```bash
curl -XPOST localhost:9090/-/reload
curl -s 'localhost:9090/api/v1/query?query=sli:delivery_success:ratio_rate5m' | jq -r '.data.result[0].value[1]'
curl -s 'localhost:9090/api/v1/query?query=slo:delivery_success:budget_remaining' | jq -r '.data.result[0].value[1]'
```
**Expected:**
```
0.99998
0.84
```
**84% of the 30-day budget remaining.** Ship freely.

The full rule set is [`code/slo_rules.yml`](./code/slo_rules.yml). Three details
in it are worth reading rather than copying:

**1. `clamp_min(denominator, 1)` everywhere.** At 03:00 the denominator can be
zero, `0/0` is NaN, NaN compares false against every threshold, and your alert
silently stops evaluating during exactly the window when nobody is watching.

**2. The budget is computed from recorded `sli:*` series, not from raw buckets.**
That is what lets a 30-day error budget live on a Prometheus with 15-day raw
retention — `avg_over_time` on a 30-second series for 30 days is 86,400 points.

**3. `rejected_capacity` is excluded from the connection-failure numerator.**
Module 19's admission control refusing a handshake with a `Retry-After` is the
system working. Counting it as an SLO violation punishes you for the fix and
rewards you for OOMing instead.

### Verify the burn-rate alert actually fires

```bash
docker exec pulse-ha-pulse-1-1 curl -s -XPOST localhost:8000/debug/fail-deliveries?rate=0.02
sleep 180
curl -s localhost:9090/api/v1/alerts | jq -r '.data.alerts[] | "\(.labels.alertname) \(.state)"'
```
**Expected:**
```
DeliverySuccessBurnFast firing
```
```bash
docker exec pulse-ha-pulse-1-1 curl -s -XPOST localhost:8000/debug/fail-deliveries?rate=0
sleep 300
curl -s localhost:9090/api/v1/alerts | jq -r '.data.alerts[] | "\(.labels.alertname) \(.state)"'
```
```
(none)
```
✅ **Fired in 2 min 40 s, cleared in 5 minutes.** The short window is what makes
it *resolve* quickly; a 6-hour window alone would keep paging for hours after
you fixed it.

Now prove it does **not** fire on a blip:
```bash
docker exec pulse-ha-pulse-1-1 curl -s -XPOST localhost:8000/debug/fail-deliveries?rate=0.4
sleep 25
docker exec pulse-ha-pulse-1-1 curl -s -XPOST localhost:8000/debug/fail-deliveries?rate=0
sleep 300
curl -s localhost:9090/api/v1/alerts | jq '.data.alerts | length'
```
```
0
```
✅ **A 25-second, 40%-failure blip paged nobody.** The 1-hour window never got
close to the threshold. That is the whole reason for two windows.

---

## Part G — The dashboard, ordered by diagnostic sequence

`infra/obs/grafana/dashboards/pulse-overview.json` — four rows, **in this
order**, because the row order is the order you should look at them.

**Row 1 — SLOs. Is anyone affected?**
```promql
sli:delivery_success:ratio_rate5m                  # stat, threshold at 99.99%
sli:delivery_latency:ratio_rate5m                  # stat, threshold at 99.9%
sli:connection_success:ratio_rate5m                # stat
slo:delivery_success:budget_remaining              # gauge
sum(increase(chat_probe_undelivered_total[15m]))   # stat, RED if > 0
```

**Row 2 — RED. What is the system doing?**
```promql
sum(rate(chat_messages_inbound_total[1m]))                          # inbound
sum(rate(chat_delivery_attempts_total[1m]))                         # outbound
sum(rate(chat_delivery_attempts_total[1m]))
  / sum(rate(chat_messages_inbound_total[1m]))                      # AMPLIFICATION
histogram_quantile(0.50, sum by (le) (rate(chat_delivery_latency_seconds_bucket[5m])))
histogram_quantile(0.99, sum by (le) (rate(chat_delivery_latency_seconds_bucket[5m])))
histogram_quantile(0.999, sum by (le) (rate(chat_delivery_latency_seconds_bucket[5m])))
```

**Row 3 — Saturation. What breaks next?**
```promql
max by (pod) (rate(chat_event_loop_lag_seconds_total[1m]))     # THE leading indicator
topk(5, chat_event_loop_lag_seconds)                           # NOT aggregated
worker:event_loop_lag:skew                                     # >3 = one sick worker
max by (pod) (chat_outbound_queue_depth)
sum(chat_connections_active) / sum(chat_max_connections)
max(redis_blocked_clients)                                     # Module 07's ceiling
outbox_backlog
max(pgbouncer_pools_client_waiting)
```

**Row 4 — Resources. Why?**
```promql
rate(process_cpu_seconds_total{job="pulse"}[1m])
process_resident_memory_bytes{job="pulse"}
redis_commands_duration_seconds_total
pg_stat_replication_replay_lag
```

> **Row 1 says whether users are affected. Row 2 says what changed. Row 3 says
> what is about to break. Row 4 says why.** A dashboard that opens with CPU
> graphs teaches people to look at the wrong thing first, every time, forever.

---

## Part H — Re-run the drills and read the dashboard

**The real test of observability: does it explain what happened?**

```bash
cd 18-compose-ha-and-chaos
./code/drill.sh "redis-primary-kill" \
  "docker kill pulse-ha-redis-1-1" "docker start pulse-ha-redis-1-1"
```

**Expected on the dashboard:**

| Row | Signal | Verdict |
|---|---|---|
| 1 | delivery success dips to 99.94% for 7 s; budget −0.4 pp | ✅ visible and quantified |
| 1 | `chat_probe_undelivered_total` **0**, `chat_probe_late_total` **1** | ✅ late, not lost |
| 2 | outbound rate → 0, recovers; amplification unchanged | ✅ |
| 2 | delivery p99 spikes to 261 ms | ✅ |
| 3 | `redis_blocked_clients` → 0 then 12 | ✅ explains the recovery |
| 4 | Redis CPU → 0, then the replica's rises | ✅ |

✅ **Fully explained**, and the prober is what turns "delivery success dipped"
into "nothing was lost."

Now the hard one:
```bash
./code/drill.sh "app-node-brownout" \
  "docker update --cpus 0.1 pulse-ha-pulse-1-1; sleep 60" \
  "docker update --cpus 2.0 pulse-ha-pulse-1-1"
```

**Expected — with only aggregate panels:**
```
Row 1: delivery success 99.2%       <-- BAD, but why?
Row 2: p99 14,200ms                 <-- BAD
Row 3: max(outbound_queue) 84,102   <-- something is saturated
Row 4: CPU: aggregate looks NORMAL  <-- averaging hid it
```
❌ **The aggregate hid it.** One node at 100% and two at 30% averages to 53%.

Break the row out:
```promql
topk(3, chat_outbound_queue_depth)
```
```
pulse-1  84,102
pulse-2       14
pulse-3        9
```

**And now the Python-specific second level**, which the JVM twin does not have:

```promql
topk(5, chat_event_loop_lag_seconds)
```
```
{pod="pulse-1"}  1.8412
{pod="pulse-2"}  0.0004
{pod="pulse-3"}  0.0003
```

That is `livemax` merged to the pod. Go one level down by scraping a worker
directly:
```bash
docker exec pulse-ha-pulse-1-1 sh -c 'for p in $(pgrep -f uvicorn); do
  echo -n "$p "; py-spy dump --pid $p 2>/dev/null | sed -n 3p; done'
```
```
9  execute (psycopg/cursor.py:732)      <-- one worker
10 select (asyncio/selector_events.py)
11 select (asyncio/selector_events.py)
12 select (asyncio/selector_events.py)
```

✅ Add a skew panel so a single-worker or single-node problem can never be
averaged away again:
```promql
worker:event_loop_lag:skew          # max/avg. >3 means ONE thing is sick.
```

Record it:
```markdown
## Module 20 — Observability

- Multi-worker exposition: WITHOUT PROMETHEUS_MULTIPROC_DIR every gauge is a
  random quarter of the truth. WITH it you lose exemplars, and the mmap files
  leak: 48 files/28 ms scrape -> 812 files/1.42 s after 50 worker restarts, and
  Prometheus marks the target down at scrape_timeout with no explanation.
  mark_process_dead() on worker exit fixes it.
- Enqueue vs delivery latency: 22 ms vs 261 ms (11.9x). Measure the right one.
- OTel's ASGI middleware makes ONE SPAN PER CONNECTION: invisible until the
  socket closes, and exactly 128 of 4,100 events kept. Span the MESSAGE.
- Tail sampling: 6,014 -> 334 spans/s, 100% of slow and errored retained.
- Module 15's blocking call: CPU went DOWN (58%), asyncio's slow-callback
  warning never fired (12 ms < 100 ms threshold), and the lag ratio went
  0.004 -> 0.89. The victim's trace showed a 9,176 ms GAP and no cause; the
  asyncio.loop_stall span named the worker and 5,014 affected tasks.
- Two-window burn-rate alerts: fired in 2m40s on a real burn, ignored a
  25-second 40%-failure blip entirely.
- Aggregation hides single-NODE problems and multiprocess merging hides
  single-WORKER ones. topk() + a skew ratio at both levels.
```

Finally, check you did not create a monitoring outage:
```bash
curl -s localhost:9090/api/v1/status/tsdb | jq '.data.headStats'
curl -s localhost:9090/api/v1/status/tsdb \
  | jq -r '.data.seriesCountByMetricName[] | "\(.value)\t\(.name)"' | head -5
```
**Expected:**
```json
{ "numSeries": 38412, "numLabelPairs": 794, "chunkCount": 76824 }
```
```
9214   chat_delivery_recipient_latency_seconds_bucket
6102   chat_delivery_latency_seconds_bucket
4820   traces_spanmetrics_latency_bucket
2140   chat_group_send_seconds_bucket
1806   redis_command_call_duration_seconds_bucket
```
✅ **38,412 series, ~115 MB of Prometheus RAM.** Histograms dominate, which is
expected and correct.

**Now deliberately break it**, so you have seen it:
```python
DELIVERY_LATENCY = Histogram("chat_delivery_latency_seconds", ..., ["room"])
```
```
numSeries: 39,812   (+1,400 across 100 rooms in 20 minutes)
```
The lab has 100 rooms. Production has 100,000:
```
100,000 rooms x 14 series per histogram = 1,400,000 series
1,400,000 x 3 KB                        = 4.2 GB, for ONE metric
```
❌ One label. Revert it, and put the room in the **trace**, where TraceQL is
indexed for exactly that query:
```
{ span.chat.room = "room.7" && duration > 500ms }
```

---

## What you built

- The full observability tier — [`infra/obs/compose.obs.yml`](../infra/obs/) —
  with Prometheus, Grafana, Loki, Tempo and an OTel collector that does the tail
  sampling.
- **Working multi-worker metrics exposition**, and the three things it costs:
  `multiprocess_mode` on every gauge, no exemplars, and a file leak that turns
  into a scrape timeout.
- **True end-to-end delivery latency**, 11.9× the enqueue number the server was
  quietly reporting.
- Trace context propagated across the channel layer, the Redis Stream and the
  outbox — after seeing what OTel's ASGI instrumentation does to a six-hour
  connection.
- **Module 15's blocking call made visible three ways**, including the finding
  that the victim's trace never contains the culprit and the
  `asyncio.loop_stall` span that fixes it.
- Four SLOs, a synthetic prober that distinguishes *late* from *lost*, and
  two-window burn-rate alerts proven to fire on a real burn and ignore a blip.
- A dashboard ordered by diagnostic sequence — and the discovery that
  aggregation hides single-node problems while multiprocess merging hides
  single-*worker* ones.

Now do [`challenge.md`](./challenge.md).

Then: [Module 21 — Security & Abuse at Scale](../21-security-and-abuse-at-scale/).
