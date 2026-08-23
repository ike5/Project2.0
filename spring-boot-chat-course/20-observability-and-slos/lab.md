# Lab 20 — Instrument What Users Notice

**You'll:** stand up Prometheus, Grafana and Tempo; measure true end-to-end
delivery; propagate trace context across the outbox and the Redis Stream; define
four SLOs with burn-rate alerts; and then re-run Module 18's drills to find out
whether your dashboard actually explains them.

⏱️ ~100 min.

---

## Part A — The stack

`infra/obs/compose.obs.yml`:
```yaml
name: pulse-obs

services:
  prometheus:
    image: prom/prometheus:v2.54.1
    ports: [ "9090:9090" ]
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - ./rules:/etc/prometheus/rules:ro
    command:
      - --config.file=/etc/prometheus/prometheus.yml
      - --storage.tsdb.retention.time=15d
      - --enable-feature=exemplar-storage      # links metrics to traces

  tempo:
    image: grafana/tempo:2.6.0
    ports: [ "3200:3200", "4317:4317" ]
    volumes: [ ./tempo.yml:/etc/tempo.yml:ro ]
    command: [ "-config.file=/etc/tempo.yml" ]

  loki:
    image: grafana/loki:3.2.0
    ports: [ "3100:3100" ]

  grafana:
    image: grafana/grafana:11.2.0
    ports: [ "3000:3000" ]
    environment:
      GF_AUTH_ANONYMOUS_ENABLED: "true"
      GF_AUTH_ANONYMOUS_ORG_ROLE: Admin
      GF_FEATURE_TOGGLES_ENABLE: traceToMetrics,traceqlEditor
    volumes:
      - ./grafana/provisioning:/etc/grafana/provisioning:ro
      - ./grafana/dashboards:/var/lib/grafana/dashboards:ro
```

`infra/obs/prometheus.yml`:
```yaml
global:
  scrape_interval: 15s
  external_labels: { cluster: pulse-local }

rule_files: [ /etc/prometheus/rules/*.yml ]

scrape_configs:
  - job_name: pulse
    metrics_path: /actuator/prometheus
    static_configs:
      - targets: [ pulse-1:8080, pulse-2:8080, pulse-3:8080 ]
  - job_name: redis
    static_configs: [ { targets: [ redis-exporter:9121 ] } ]
  - job_name: postgres
    static_configs: [ { targets: [ postgres-exporter:9187 ] } ]
```

Tempo's key setting — the histogram/trace link:
```yaml
# tempo.yml
metrics_generator:
  processor:
    span_metrics:
      dimensions: [ chat.room_size_bucket, chat.outcome ]
  storage:
    remote_write: [ { url: http://prometheus:9090/api/v1/write } ]
```

```bash
docker compose -f infra/obs/compose.obs.yml up -d --wait
open http://localhost:3000
```

App side:
```xml
<dependency>
  <groupId>io.micrometer</groupId>
  <artifactId>micrometer-tracing-bridge-otel</artifactId>
</dependency>
<dependency>
  <groupId>io.opentelemetry</groupId>
  <artifactId>opentelemetry-exporter-otlp</artifactId>
</dependency>
```
```yaml
management:
  tracing:
    sampling.probability: 0.01          # 1% baseline; tail sampling in the collector
  otlp.tracing.endpoint: http://tempo:4317
  metrics.distribution:
    percentiles-histogram:
      chat.fanout.latency: true
      chat.delivery.latency: true
    slo:
      chat.delivery.latency: 50ms,100ms,250ms,500ms,1s,2s,5s
```

---

## Part B — Measure delivery, not enqueue

Module 06's `chat.fanout.latency` measured **enqueue** time — `convertAndSend`
returns as soon as the message is on `brokerChannel`. That number was 21 ms while
users experienced 192 ms.

Measure the real thing: the moment bytes leave for the *last* recipient.

`src/main/java/com/pulse/metrics/DeliveryMetrics.java`:

```java
package com.pulse.metrics;

import io.micrometer.core.instrument.*;
import org.springframework.stereotype.Component;

@Component
public class DeliveryMetrics {

    private final Timer deliveryLatency;      // send -> LAST recipient
    private final Timer perRecipientLatency;  // send -> each recipient
    private final Counter published, deliveryAttempts, deliveryFailures;
    private final DistributionSummary fanoutSize;

    public DeliveryMetrics(MeterRegistry registry) {
        this.deliveryLatency = Timer.builder("chat.delivery.latency")
                .description("send() until the LAST recipient's socket was written")
                .publishPercentileHistogram()          // AGGREGATABLE (README)
                .minimumExpectedValue(Duration.ofMillis(1))
                .maximumExpectedValue(Duration.ofSeconds(30))
                .register(registry);

        this.perRecipientLatency = Timer.builder("chat.delivery.recipient.latency")
                .publishPercentileHistogram().register(registry);

        this.published        = Counter.builder("chat.published").register(registry);
        this.deliveryAttempts = Counter.builder("chat.delivery.attempts").register(registry);
        this.deliveryFailures = Counter.builder("chat.delivery.failures").register(registry);
        this.fanoutSize       = DistributionSummary.builder("chat.fanout.size")
                .publishPercentileHistogram().register(registry);
    }

    /**
     * Called once per message, after every recipient's write has been attempted.
     * `originTs` travels IN the envelope, so this works even though the send and
     * the delivery happen on different nodes.
     */
    public void recordDelivery(long originTs, int recipients, int failures, String roomSizeBucket) {
        long elapsed = System.currentTimeMillis() - originTs;

        deliveryLatency.record(elapsed, TimeUnit.MILLISECONDS);
        published.increment();
        deliveryAttempts.increment(recipients);
        deliveryFailures.increment(failures);
        fanoutSize.record(recipients);
    }

    /** Bucket, never label by room id (cardinality -- see the README). */
    public static String bucket(int recipients) {
        if (recipients <= 10)   return "small";
        if (recipients <= 200)  return "medium";
        if (recipients <= 2000) return "large";
        return "huge";
    }
}
```

Wire it into the delivery path:

```java
void deliver(String roomId, MapRecord<String, String, String> record) {
    var envelope = json.readValue(record.getValue().get("payload"), Envelope.class);
    var targets = sessions.sessionsInRoom(roomId);

    int failures = 0;
    for (String sessionId : targets) {
        long t0 = System.nanoTime();
        try {
            sendToSession(sessionId, envelope);
            metrics.recordRecipient(System.nanoTime() - t0);
        } catch (Exception e) {
            failures++;                     // a failed delivery is an SLI event
        }
    }
    metrics.recordDelivery(envelope.ts(), targets.size(), failures,
                           DeliveryMetrics.bucket(targets.size()));
}
```

Compare the two:
```bash
k6 run -e ROOMS=100 -e SEND_EVERY=5000 --vus 10000 --duration 5m \
       ../../06-load-testing-harness/code/pulse-load.js
curl -s localhost:8080/actuator/prometheus | grep -E 'chat_(fanout|delivery)_latency.*quantile'
```
**Expected:**
```
chat_fanout_latency_seconds{quantile="0.99"}   0.021      <-- enqueue: 21ms
chat_delivery_latency_seconds{quantile="0.99"} 0.194      <-- REAL: 194ms
```

✅ **9× difference.** The enqueue metric is not wrong, it's answering a different
question — and it's the number that would have made Module 06's broken server
look healthy.

Keep both, and label them so nobody confuses them again:
```java
.description("send() until the LAST recipient's socket was written")
```

---

## Part C — Trace across the outbox and the stream

Three process boundaries, none of which propagate context.

```java
@Component
public class TracedOutboxRelay {

    private final TextMapPropagator propagator = W3CTraceContextPropagator.getInstance();

    // --- producing side: the send path writes the outbox row ---
    @Transactional
    public void enqueue(String roomId, Envelope envelope) {
        var carrier = new HashMap<String, String>();
        propagator.inject(Context.current(), carrier, HashMap::put);   // "traceparent"

        jdbc.sql("""
                INSERT INTO outbox (aggregate_id, event_type, payload, trace_context)
                VALUES (:room, :type, :payload::jsonb, :trace::jsonb)
                """)
                .param("room", roomId)
                .param("payload", json.writeValueAsString(envelope))
                .param("trace", json.writeValueAsString(carrier))       // <-- carried
                .update();
    }

    // --- relay: restore the trace, then carry it into Redis ---
    public void relay(OutboxRow row) {
        Context parent = propagator.extract(Context.current(),
                json.readValue(row.traceContext(), MAP_TYPE), MAP_GETTER);

        Span span = tracer.spanBuilder("outbox.relay")
                .setParent(parent)
                .setSpanKind(SpanKind.PRODUCER)
                .setAttribute("outbox.id", row.id())
                .setAttribute("outbox.age_ms", row.ageMillis())          // backlog visibility
                .startSpan();

        try (Scope s = span.makeCurrent()) {
            var fields = new HashMap<String, String>();
            fields.put("payload", row.payload());
            propagator.inject(Context.current(), fields, Map::put);      // into the stream
            redis.opsForStream().add(StreamRecords.newRecord()
                    .in(streamKey(row.aggregateId())).ofMap(fields));
        } finally {
            span.end();
        }
    }
}
```

```java
// --- consuming side: restore before delivering ---
void deliver(String roomId, MapRecord<String, String, String> record) {
    Context parent = propagator.extract(Context.current(), record.getValue(), MAP_GETTER);

    Span span = tracer.spanBuilder("chat.fanout")
            .setParent(parent)
            .setSpanKind(SpanKind.CONSUMER)
            .setAttribute("chat.room_size_bucket", bucket(targets.size()))
            .setAttribute("chat.recipients", targets.size())      // ATTRIBUTE, not 200 spans
            .startSpan();
    try (Scope s = span.makeCurrent()) {
        // ... deliver to all recipients inside ONE span ...
    } finally {
        span.end();
    }
}
```

**Expected in Tempo** — one trace spanning three processes:
```
chat.send                          node-a     18.4ms
├── messages.insert                node-a      2.1ms
├── outbox.insert                  node-a      0.9ms
└── (async)
    outbox.relay                   node-b     41.2ms   outbox.age_ms=38
    └── redis.xadd                 node-b      1.8ms
        └── (async)
            chat.fanout            node-c    142.8ms   chat.recipients=199
            ├── redis.xreadgroup   node-c      2.1ms
            ├── deliver.batch      node-c    138.2ms
            └── redis.xack         node-c      1.1ms
```

✅ **`outbox.age_ms=38`** immediately tells you the relay was 38 ms behind — a
number you'd otherwise have to infer from a backlog gauge.

**Sampling**, because 400k msg/s cannot all be traced. Tail-sample in the
collector:
```yaml
# otel-collector.yml
processors:
  tail_sampling:
    decision_wait: 10s
    policies:
      - name: errors
        type: status_code
        status_code: { status_codes: [ERROR] }         # keep 100% of errors
      - name: slow
        type: latency
        latency: { threshold_ms: 500 }                 # keep 100% of slow
      - name: baseline
        type: probabilistic
        probabilistic: { sampling_percentage: 0.1 }    # 0.1% of the rest
```
**Measured:** 4,000 spans/s at 1% head sampling → **412 spans/s** with tail
sampling, **and every slow or failed trace is retained**. That's the trade you
want: you never need a trace of a fast, successful message.

---

## Part D — Measure the undeliverable

SLI 1 is delivery success, and you cannot count what didn't happen.

**Server side** — attempts versus expected:
```
delivery_success = chat_delivery_attempts - chat_delivery_failures
                   / (chat_published * avg(chat_fanout_size))
```
This catches write failures but **not** a message that was written to a socket
whose owner never received it (Module 10's last-hop gap).

**Client side** — a synthetic prober, which is the only way to close that gap:

```java
@Component
@Profile("prober")
public class DeliveryProber {

    private final Map<String, Long> inFlight = new ConcurrentHashMap<>();

    /** Two clients, in the same room, on DIFFERENT nodes. */
    @Scheduled(fixedRate = 10_000)
    public void probe() {
        String probeId = "probe-" + UUID.randomUUID();
        inFlight.put(probeId, System.nanoTime());

        senderClient.send(PROBE_ROOM, probeId, "synthetic");

        // If the receiver hasn't seen it in 5s, count it as UNDELIVERED.
        scheduler.schedule(() -> {
            if (inFlight.remove(probeId) != null) {
                probeUndelivered.increment();
                log.error("PROBE UNDELIVERED: {}", probeId);
            }
        }, 5, TimeUnit.SECONDS);
    }

    void onReceive(String probeId) {
        Long sentAt = inFlight.remove(probeId);
        if (sentAt == null) return;                    // late arrival, already counted
        probeLatency.record(System.nanoTime() - sentAt, TimeUnit.NANOSECONDS);
        probeDelivered.increment();
    }
}
```

```bash
curl -s localhost:8080/actuator/prometheus | grep chat_probe
```
**Expected in steady state:**
```
chat_probe_delivered_total 8640
chat_probe_undelivered_total 0
chat_probe_latency_seconds{quantile="0.99"} 0.186
```

Now run Module 18's Redis pause drill and watch:
```
chat_probe_undelivered_total 0        <-- Streams buffered it; nothing lost
chat_probe_latency_seconds{quantile="0.99"} 8.412   <-- but very slow
```
✅ The prober distinguishes **late** from **lost**, which the server-side metric
cannot.

> A synthetic prober is the only way to measure an end-to-end guarantee, and it's
> worth the two extra connections. It also detects failures that affect *no real
> user yet* — which is the entire point of monitoring.

---

## Part E — The four SLOs

`infra/obs/rules/slo.yml`:

```yaml
groups:
  - name: pulse-sli
    interval: 30s
    rules:
      # SLI 1 -- delivery success
      - record: sli:delivery_success:ratio_rate5m
        expr: |
          (sum(rate(chat_delivery_attempts_total[5m]))
           - sum(rate(chat_delivery_failures_total[5m])))
          / sum(rate(chat_delivery_attempts_total[5m]))

      # SLI 2 -- delivery latency (fraction of messages under 500ms)
      - record: sli:delivery_latency:ratio_rate5m
        expr: |
          sum(rate(chat_delivery_latency_seconds_bucket{le="0.5"}[5m]))
          / sum(rate(chat_delivery_latency_seconds_count[5m]))

      # SLI 3 -- connection success
      - record: sli:connection_success:ratio_rate5m
        expr: |
          sum(rate(chat_handshake_total{outcome="success"}[5m]))
          / sum(rate(chat_handshake_total[5m]))

      # SLI 4 -- sequence integrity
      - record: sli:sequence_integrity:ratio_rate5m
        expr: |
          1 - (sum(rate(chat_sequence_gaps_permanent_total[5m]))
               / sum(rate(chat_published_total[5m])))
```

### Burn-rate alerts

```yaml
  - name: pulse-slo-burn
    rules:
      # 14.4x burn over 1h => a 30-day budget gone in ~2 days. PAGE.
      - alert: DeliverySuccessBurnFast
        expr: |
          (1 - sli:delivery_success:ratio_rate5m) > (14.4 * 0.0001)
          and
          (1 - sli:delivery_success:ratio_rate1h) > (14.4 * 0.0001)
        for: 2m
        labels: { severity: page, slo: delivery_success }
        annotations:
          summary: "Burning the delivery-success budget 14x too fast"
          description: "{{ $value | humanizePercentage }} of deliveries failing"
          runbook: "docs/RUNBOOK.md#deliverysuccess"

      # 6x over 6h => exhausted in ~5 days. PAGE (less urgent).
      - alert: DeliverySuccessBurnSlow
        expr: |
          (1 - sli:delivery_success:ratio_rate30m) > (6 * 0.0001)
          and
          (1 - sli:delivery_success:ratio_rate6h) > (6 * 0.0001)
        for: 15m
        labels: { severity: page, slo: delivery_success }

      # 1x over 3 days => on track to exhaust exactly. TICKET.
      - alert: DeliverySuccessBudgetTrend
        expr: |
          (1 - sli:delivery_success:ratio_rate6h) > 0.0001
          and
          (1 - sli:delivery_success:ratio_rate3d) > 0.0001
        for: 6h
        labels: { severity: ticket, slo: delivery_success }
```

**The two-window condition matters.** A single-window alert on a 5-minute rate
fires on every brief blip. Requiring *both* a short and a long window to be
burning means a 30-second hiccup doesn't page anyone, but a sustained problem
does — quickly.

### The error budget

```yaml
      - record: slo:delivery_success:error_budget_remaining
        expr: |
          1 - (
            (1 - avg_over_time(sli:delivery_success:ratio_rate5m[30d]))
            / 0.0001
          )
```

```bash
curl -s 'localhost:9090/api/v1/query?query=slo:delivery_success:error_budget_remaining' | jq -r '.data.result[0].value[1]'
```
**Expected:**
```
0.84
```
**84% of the 30-day budget remaining.** Ship freely.

---

## Part F — The dashboard

`infra/obs/grafana/dashboards/pulse-overview.json` — four rows, in this order:

**Row 1 — SLOs (is anything wrong?)**
```promql
sli:delivery_success:ratio_rate5m                    # stat, thresholds at 99.99%
sli:delivery_latency:ratio_rate5m                    # stat
slo:delivery_success:error_budget_remaining          # gauge
sum(rate(chat_probe_undelivered_total[5m]))          # stat, red if > 0
```

**Row 2 — RED (what is the system doing?)**
```promql
# Rate -- BOTH numbers, always, with the amplification visible
sum(rate(chat_published_total[1m]))                                    # inbound
sum(rate(chat_delivery_attempts_total[1m]))                            # outbound
sum(rate(chat_delivery_attempts_total[1m])) / sum(rate(chat_published_total[1m]))  # amplification

# Duration
histogram_quantile(0.50, sum by (le) (rate(chat_delivery_latency_seconds_bucket[5m])))
histogram_quantile(0.99, sum by (le) (rate(chat_delivery_latency_seconds_bucket[5m])))
histogram_quantile(0.999, sum by (le) (rate(chat_delivery_latency_seconds_bucket[5m])))
```

**Row 3 — Saturation (what will break next?)**
```promql
max(stomp_channel_queued{channel="outbound"})        # THE leading indicator
max(stream_pending)                                  # Redis PEL depth
max(stream_lag)
outbox_backlog
max(hikaricp_connections_pending)
max(chat_connections_active) / 35600                 # fraction of the ceiling
```

**Row 4 — Resources (why?)**
```promql
rate(process_cpu_seconds_total[1m])
jvm_memory_used_bytes{area="heap"}
jvm_gc_pause_seconds_max
redis_commands_duration_seconds_total
```

> **The row order is the diagnostic order.** Row 1 says whether users are
> affected. Row 2 says what changed. Row 3 says what's about to break. Row 4 says
> why. A dashboard that opens with CPU graphs teaches people to look at the wrong
> thing first.

Import and check:
```bash
open 'http://localhost:3000/d/pulse-overview'
```

---

## Part G — Re-run the drills and read the dashboard

**The real test of observability: does it explain what happened?**

```bash
cd ../18-compose-ha-and-chaos
./code/drill.sh "redis-primary-kill" "docker kill pulse-ha-redis-1-1" "docker start pulse-ha-redis-1-1"
```

**Expected on the dashboard:**

| Row | Signal | Verdict |
|-----|--------|---------|
| 1 | delivery success dips to 99.94% for 8 s; budget −0.4% | ✅ visible and quantified |
| 1 | probe undelivered: **0** | ✅ nothing lost |
| 2 | outbound rate drops to 0, recovers | ✅ |
| 2 | p99 spikes to 214 ms | ✅ |
| 3 | **`stream_pending` spikes to 4,102 then drains** | ✅ **explains the recovery** |
| 4 | Redis CPU → 0, then a new pod's CPU rises | ✅ |

✅ **Fully explained.** `stream_pending` is the story: messages accumulated in the
PEL and drained, which is why nothing was lost.

Now the hard one:
```bash
./code/drill.sh "app-node-brownout" \
  "docker update --cpus 0.1 pulse-ha-pulse-1-1; sleep 60" \
  "docker update --cpus 2.0 pulse-ha-pulse-1-1"
```

**Expected — with only the aggregate dashboard:**
```
Row 1: delivery success 99.2%   <-- BAD, but why?
Row 2: p99 14,200ms             <-- BAD
Row 3: outbound queue max 84,102 <-- something is saturated
Row 4: CPU: aggregate looks NORMAL   <-- averaging hid it
```
❌ **The aggregate hid it.** One node at 100% and two at 30% averages to 53%.

**The fix — break the saturation row out by instance:**
```promql
stomp_channel_queued{channel="outbound"}          # NO aggregation
```
```
pulse-1: 84,102     <-- there it is
pulse-2: 12
pulse-3: 8
```

✅ Add a "worst instance" panel to Row 3 so a single-node problem can never be
averaged away:
```promql
topk(3, stomp_channel_queued{channel="outbound"})
max(stomp_channel_queued) / avg(stomp_channel_queued)   # skew: >3 means one node is sick
```

**Now the trace closes it:**
```bash
# From the p99 panel, click the exemplar to jump to a slow trace
```
```
chat.fanout   pulse-1   14,202ms   chat.recipients=199
├── redis.xreadgroup    pulse-1        2.1ms
└── deliver.batch       pulse-1   14,198ms      <-- the time is HERE
```
✅ Not Redis, not the database, not the network — **this node's delivery loop**.
Which is exactly what a brownout is.

Record it:
```markdown
## Module 20 — Observability

- Enqueue vs delivery latency: 21ms vs 194ms  (9x -- measure the right one)
- Tail sampling: 4,000 spans/s -> 412/s, keeping 100% of slow and errored
- Aggregate dashboards HIDE single-node problems: add topk() and a skew ratio
- Two-window burn-rate alerts: no pages on 30s blips, pages in 2m on real burn
- The prober is the only way to measure end-to-end delivery success
```

---

## Part H — Structured logs, correlated

```xml
<appender name="JSON" class="ch.qos.logback.core.ConsoleAppender">
  <encoder class="net.logstash.logback.encoder.LogstashEncoder">
    <includeMdcKeyName>traceId</includeMdcKeyName>
    <includeMdcKeyName>spanId</includeMdcKeyName>
    <includeMdcKeyName>roomId</includeMdcKeyName>
    <customFields>{"service":"pulse","node":"${PULSE_NODE_ID}"}</customFields>
  </encoder>
</appender>
```

**Expected:**
```json
{"@timestamp":"2026-08-23T14:41:02.884Z","level":"WARN","service":"pulse",
 "node":"pulse-1","traceId":"a3f81c92e4d5b7f1","spanId":"9b2c4e6f",
 "roomId":"room.42","message":"delivery failed for session 4b1e7c39",
 "stack_trace":"org.springframework.web.socket.handler.SessionLimitExceededException..."}
```

Wire Grafana's trace-to-logs so a span links to its log lines:
```yaml
# grafana/provisioning/datasources/tempo.yml
  jsonData:
    tracesToLogsV2:
      datasourceUid: loki
      filterByTraceID: true
      tags: [ { key: 'service.name', value: 'service' } ]
```

✅ Now: **p99 panel → exemplar → trace → the exact log lines for that message.**
That path from "the graph looks bad" to "here is the exception" is the whole
point of the module, and it takes about fifteen seconds once wired.

**And the cardinality check** — make sure you didn't create a monitoring outage:
```bash
curl -s 'localhost:9090/api/v1/status/tsdb' | jq '.data.headStats'
```
**Expected:**
```json
{ "numSeries": 41204, "numLabelPairs": 812, "chunkCount": 82408 }
```
```bash
curl -s 'localhost:9090/api/v1/status/tsdb' | \
  jq -r '.data.seriesCountByMetricName[] | "\(.value)\t\(.name)"' | head -5
```
```
8412	chat_delivery_latency_seconds_bucket
4104	chat_delivery_recipient_latency_seconds_bucket
2841	jvm_gc_pause_seconds_bucket
1204	http_server_requests_seconds_bucket
```
✅ **41,204 series, ~120 MB of Prometheus RAM.** Histograms dominate (one series
per bucket per label combination), which is expected and fine.

**Deliberately break it** to see what you avoided:
```java
Counter.builder("chat.messages.by_room").tag("roomId", roomId).register(registry);
```
```
numSeries: 841,204     (+800,000 in 20 minutes)
prometheus RSS: 2.9 GB and climbing
```
❌ One label. Revert it.

---

## What you built

- The full observability stack with exemplars linking metrics → traces → logs.
- **True end-to-end delivery latency**, 9× the enqueue number everyone measures.
- Trace context propagated across the outbox table *and* the Redis Stream, with
  tail sampling that keeps every slow and failed trace at 10× less volume.
- A synthetic prober that measures the one thing server metrics cannot: whether
  a message actually arrived.
- Four SLOs with two-window burn-rate alerts and a live error budget.
- A dashboard ordered by diagnostic sequence — **and the discovery that
  aggregation hides single-node failures**, fixed with `topk` and a skew ratio.

Now do [`challenge.md`](./challenge.md).

Then: [Module 21 — Security & Abuse at Scale](../21-security-and-abuse-at-scale/).
