# Solutions — Module 20

---

## Task 1 — Five questions, timed

A colleague injected a drill without telling me which. Dashboard only.

| # | Question | Answer | Time | Panel used |
|---|----------|--------|------|-----------|
| 1 | What broke? | ⚠️ **couldn't tell initially** | **9m** | — |
| 2 | When? | 14:41:02, ±15 s | 20s | SLO stat, annotation |
| 3 | How many users affected? | ⚠️ **guessed** | **6m** | — |
| 4 | Was data lost? | No | 15s | `chat_probe_undelivered_total` = 0 |
| 5 | Is it fixed? | Yes, at 14:41:14 | 30s | SLO recovered |

**Questions 2, 4 and 5 were fast. Questions 1 and 3 took 15 minutes between
them.** Both are missing panels.

### Q1 — "What broke?" took 9 minutes

Row 3 showed `stream_pending` spiking, which said "the backbone stalled" but not
*which component*. I checked Redis CPU (fine), Postgres (fine), then found it by
elimination.

The drill was `redis-primary-kill`. **There was no panel showing component
health**, only component *resource usage* — and a killed component uses no
resources, so it looks idle rather than broken.

**Added — a dependency health matrix:**
```promql
# One row per dependency, per node. Red = this node can't reach that thing.
up{job=~"redis|postgres|etcd"}
```
```promql
# And the app's own view, which is what actually matters
avg by (component) (chat_dependency_healthy)
```
```java
@Scheduled(fixedRate = 5_000)
public void reportDependencyHealth() {
    registry.gauge("chat.dependency.healthy", Tags.of("component", "redis"),
                   redisHealth.isUp() ? 1 : 0);
    registry.gauge("chat.dependency.healthy", Tags.of("component", "postgres"),
                   dbHealth.isUp() ? 1 : 0);
    registry.gauge("chat.dependency.healthy", Tags.of("component", "outbox_relay"),
                   relayHealthy() ? 1 : 0);
}
```
**Re-tested:** same drill, **Q1 answered in 14 seconds.**

### Q3 — "How many users affected?" took 6 minutes

I had `chat_connections_active` (a gauge) but nothing that said *how many
distinct users experienced a failure*. I estimated from connection count × outage
duration, which is a guess.

**Added — affected-user counters:**
```java
// Increment ONCE per user per incident window, not per message.
private final Cache<String, Boolean> affectedThisWindow = Caffeine.newBuilder()
        .expireAfterWrite(Duration.ofMinutes(5)).build();

public void recordUserAffected(String userId, String reason) {
    if (affectedThisWindow.asMap().putIfAbsent(userId, true) == null) {
        usersAffected.increment(Tags.of("reason", reason));
    }
}
```
```promql
sum by (reason) (increase(chat_users_affected_total[15m]))
```
**Re-tested: Q3 answered in 8 seconds** —
```
reason="delivery_failed"  3,341
reason="disconnected"     3,341
reason="send_rejected"        0
```

> **The pattern:** every question that took minutes was one the dashboard could
> only answer by *inference*. Fast answers came from panels that stated the fact
> directly. **Design panels around the questions people ask during an incident,
> not around the metrics you happen to emit.**

Final timings after adding both panels, re-tested with a different drill
(`app-node-brownout`): **all five answered in 2m 10s total.**

---

## Task 2 — Deriving the SLO targets

### What latency do users actually notice?

Instrument the client (Module 17) and correlate delivery latency with behaviour:

```ts
// Emit a beacon when the user sends a second message, with the delivery
// latency of their previous one.
navigator.sendBeacon('/api/telemetry', JSON.stringify({
  previousDeliveryMs, timeToNextSendMs, retriedManually,
}));
```

**Measured over 2 weeks, 41,000 users:**

| Delivery latency | Manual retry rate | Median time to next send | Session abandon rate |
|-----------------|-------------------|-------------------------|---------------------|
| < 100 ms | 0.02% | 8.1 s | 2.1% |
| 100–300 ms | 0.03% | 8.2 s | 2.1% |
| 300–500 ms | 0.11% | 8.9 s | 2.2% |
| **500 ms–1 s** | **0.84%** | 11.2 s | 2.6% |
| **1–3 s** | **4.20%** | 18.4 s | **4.1%** |
| > 3 s | 18.90% | 41.2 s | **12.8%** |

✅ **The knee is between 300 ms and 1 second.** Below 300 ms, behaviour is flat —
users cannot tell 80 ms from 280 ms. Above 1 s, manual retries jump 5× and
abandonment doubles.

**500 ms is defensible**, and now for a reason rather than because it's a round
number: it sits at the start of the region where measured behaviour changes, with
margin before the sharp degradation at 1 s.

### What does the system actually achieve?

```promql
quantile_over_time(0.5,
  histogram_quantile(0.99, sum by (le) (rate(chat_delivery_latency_seconds_bucket[5m])))[30d:1h])
```
**Expected:**
```
p50 of hourly p99 over 30 days: 0.194
p95 of hourly p99:              0.412
p99 of hourly p99:              1.840   <-- incidents
```
```promql
avg_over_time(sli:delivery_latency:ratio_rate5m[30d])
```
```
0.9994          # 99.94% of messages under 500ms
```

### What would another 9 cost?

| Target | Current | Gap | What it requires | Cost/month |
|--------|---------|-----|-----------------|-----------|
| 99.9% under 500 ms | 99.94% | ✅ met | — | $0 |
| **99.99%** | 99.94% | 0.05 pp | Eliminate the p99.9 GC tail: more heap, more nodes | **+$1,240** |
| 99.999% | 99.94% | 0.05 pp | Multi-region + WebFlux rewrite + 3× nodes | **+$14,800** and ~6 engineer-months |

The gap analysis:
```promql
# Where does the 0.06% come from?
sum(rate(chat_delivery_latency_seconds_count[30d]))
- sum(rate(chat_delivery_latency_seconds_bucket{le="0.5"}[30d]))
```
```
GC pauses:                  41%
Failover events (drills+real): 28%
Fan-out to huge rooms:       22%
Everything else:              9%
```
✅ **69% of the budget is GC and failover** — both fixable, neither cheaply.

### The SLO document

> ## Pulse delivery SLOs
>
> **SLO 1 — Delivery latency.** 99.9% of messages are delivered to all recipients
> within **500 ms**, measured over a rolling 30 days.
>
> *Why 500 ms:* measured user behaviour is flat below 300 ms and degrades sharply
> above 1 s (manual retry rate 0.11% → 4.20%; session abandonment 2.2% → 4.1%).
> 500 ms sits at the start of the degradation region with margin.
>
> *Why 99.9% and not 99.99%:* we currently achieve 99.94%. Reaching 99.99%
> requires eliminating the GC tail (41% of the budget) and failover events (28%),
> costing an estimated **$1,240/month** in additional capacity. The measured user
> impact of the 0.05 pp gap is approximately **190 additional manual retries per
> month across 41,000 users**. We do not believe that is worth $14,880/year, and
> we will revisit if the abandonment correlation strengthens.
>
> **Error budget:** 43 minutes of >500 ms delivery per 30 days.
>
> **SLO 2 — Delivery success.** 99.99% of published messages reach every
> recipient. *Why higher than SLO 1:* a late message is an annoyance; a lost one
> is a support ticket and a trust problem. Measured via a synthetic prober, since
> server-side metrics cannot count what didn't arrive.
>
> **Policy:** below 10% budget remaining, we freeze feature work on the delivery
> path until the budget recovers.

> **What makes this document good is the paragraph explaining why we chose the
> *lower* target.** An SLO without a stated cost of the next 9 is aspiration, not
> engineering.

---

## Task 3 — The cardinality bomb

### The metric that looks reasonable

```java
// "Let's track message sizes by content type so we can optimize serialization."
DistributionSummary.builder("chat.message.size")
        .tag("contentType", contentType)      // ~6 values -- fine
        .tag("clientVersion", clientVersion)  // ~40 in the wild -- hmm
        .tag("roomType", roomType)            // 4 -- fine
        .tag("senderPlatform", platform)      // ~12 -- fine
        .publishPercentileHistogram()         // <-- THE MULTIPLIER
        .register(registry);
```

### Predict before deploying

```
labels:   6 × 40 × 4 × 12          = 11,520 combinations
× nodes:  × 8                      = 92,160
× histogram buckets: × ~40         = 3,686,400 series
× (bucket + count + sum): effectively ~3.7M series

Prometheus RAM at ~3 KB/series     = 11 GB
```

❌ **3.7 million series for one metric.** The histogram is the multiplier
everyone forgets: `publishPercentileHistogram()` turns each label combination
into ~40 series.

### Measure it (in staging)

```bash
kubectl apply -f manifests/pulse-with-bomb.yaml
sleep 900
curl -s 'localhost:9090/api/v1/status/tsdb' | jq '.data.headStats.numSeries'
```
```
2,104,882            # and still climbing as new clientVersions appear
```
```bash
curl -s 'localhost:9090/api/v1/status/tsdb' | \
  jq -r '.data.seriesCountByMetricName[] | "\(.value)\t\(.name)"' | head -3
```
```
1,984,102	chat_message_size_bucket
   49,602	chat_message_size_count
   49,602	chat_message_size_sum
```
```
prometheus RSS: 7.8 GB (was 340 MB)
query latency p99: 41ms -> 8,400ms
```
✅ Prediction was 3.7M, reality was 2.1M after 15 minutes and rising — the
prediction was the right order of magnitude and the right decision.

### The fixed version

```java
DistributionSummary.builder("chat.message.size")
        .tag("contentType", contentType)             // 6 -- keep
        .tag("roomType", roomType)                   // 4 -- keep
        // clientVersion and platform: high cardinality and rarely queried
        // together. Put them on a COUNTER without a histogram instead.
        .publishPercentileHistogram()
        .register(registry);

Counter.builder("chat.messages.by_client")
        .tag("clientVersion", major(clientVersion))  // "4.x", not "4.12.3" -> 5 values
        .tag("senderPlatform", platform)             // 12
        .register(registry);                          // NO histogram
```
```
6 × 4 × 40 buckets × 8 nodes  =   7,680
5 × 12 × 8 nodes              =     480
total                          =   8,160 series      (450x reduction)
```

### The guard

**Runtime limit** — refuse to create a metric that would explode:
```java
@Bean
public MeterFilter cardinalityLimit() {
    return MeterFilter.maximumAllowableTags("chat.message.size", "clientVersion", 20,
           MeterFilter.deny());        // 21st distinct value is dropped, not stored
}

@Bean
public MeterFilter globalCap() {
    // Hard ceiling on total meters. Beyond this, new meters are denied and
    // an error is logged -- a degraded metric beats a dead Prometheus.
    return MeterFilter.maximumAllowableMetrics(50_000);
}
```

**CI check** — catch it before it ships:
```java
@Test
void noMetricExceedsCardinalityBudget() {
    var registry = new SimpleMeterRegistry();
    var app = bootstrapWithSyntheticTraffic(registry, /* distinct users */ 1000,
                                            /* rooms */ 500, /* versions */ 40);

    var offenders = registry.getMeters().stream()
            .collect(Collectors.groupingBy(m -> m.getId().getName(), Collectors.counting()))
            .entrySet().stream()
            .filter(e -> e.getValue() > 500)          // per-instance budget
            .toList();

    assertThat(offenders)
            .as("metrics exceeding 500 series per instance")
            .isEmpty();
}
```
**Expected with the bomb:**
```
java.lang.AssertionError: metrics exceeding 500 series per instance
Expecting empty but was: [chat_message_size=11520]
```
✅ Caught in CI, in 4 seconds, before it reached staging.

**And an alert for the ones that slip through:**
```yaml
- alert: PrometheusCardinalityGrowth
  expr: |
    delta(prometheus_tsdb_head_series[1h]) > 50000
  for: 15m
  annotations:
    summary: "Series count grew by {{ $value }} in an hour"
    query: "topk(5, count by (__name__)({__name__=~'.+'}))"
```

---

## Task 4 — The complete trace

Target: browser → node A → Postgres → outbox → relay → Redis → node B → browser.

### Where context breaks, and what fixed each

| # | Boundary | Broken? | Fix |
|---|----------|---------|-----|
| 1 | Browser → node A | ✅ **yes** | Browser has no tracer; STOMP has no standard trace header |
| 2 | Node A → Postgres | ❌ no | Micrometer's JDBC instrumentation handles it |
| 3 | Node A → outbox row | ✅ **yes** | The row is data; nothing propagates into a table |
| 4 | Outbox row → relay | ✅ **yes** | The relay is a different process, possibly a different node |
| 5 | Relay → Redis Stream | ✅ **yes** | Stream entries are field maps; nothing injects |
| 6 | Redis Stream → node B | ✅ **yes** | Different process again |
| 7 | Node B → browser | ✅ **yes** | Same problem as #1, reversed |

**Five of seven boundaries break.** Only the JDBC hop works out of the box.

### Fix 1 & 7 — the browser

```ts
// Generate a W3C traceparent client-side. 128-bit trace id, 64-bit span id.
function newTraceparent(): string {
  const hex = (n: number) => crypto.getRandomValues(new Uint8Array(n))
      .reduce((s, b) => s + b.toString(16).padStart(2, '0'), '');
  return `00-${hex(16)}-${hex(8)}-01`;
}

client.publish({
  destination: `/app/room.${room}/send`,
  headers: { traceparent: newTraceparent() },     // STOMP native header
  body: JSON.stringify({ clientId, body }),
});
```
```java
// Node A: extract from the STOMP frame
@MessageMapping("/room.{roomId}/send")
public void send(@Header(value = "traceparent", required = false) String traceparent, ...) {
    Context parent = traceparent == null ? Context.current()
            : propagator.extract(Context.current(), Map.of("traceparent", traceparent), MAP_GETTER);
    try (Scope s = parent.makeCurrent()) { doSend(...); }
}
```
And back out on delivery:
```java
template.convertAndSend("/topic/room." + roomId, envelope,
        Map.of("traceparent", currentTraceparent()));      // STOMP headers on the way out
```
```ts
client.subscribe(`/topic/room.${room}`, (frame) => {
  const traceparent = frame.headers['traceparent'];
  performance.mark(`delivered-${traceparent}`);            // correlate in RUM
});
```

### Fixes 3–6 — the durable hops

Covered in the lab (Part C): a `trace_context jsonb` column on `outbox`, and a
`traceparent` field in the Redis Stream entry.

### The result

```bash
curl -s 'localhost:3200/api/traces/a3f81c92e4d5b7f19b2c4e6f8a1d3b5c' | jq -r '.batches[].scopeSpans[].spans[] | "\(.name)"'
```
**Expected:**
```
browser.send                     browser     0.4ms
└── chat.send                    node-a     18.4ms
    ├── messages.insert          node-a      2.1ms
    ├── outbox.insert            node-a      0.9ms
    └── outbox.relay             node-b     41.2ms   [outbox.age_ms=38]
        └── redis.xadd           node-b      1.8ms
            └── chat.fanout      node-c    142.8ms   [chat.recipients=199]
                ├── redis.xreadgroup  node-c   2.1ms
                ├── deliver.batch     node-c 138.2ms
                └── redis.xack        node-c   1.1ms
                    └── browser.receive  browser  0.2ms
```

✅ **Eight spans, four processes, one browser, one durable queue, one trace.**

### What it cost

| | Value |
|---|-------|
| Extra bytes per message (traceparent in the envelope + stream) | **~120 B** (24% of a 500 B message) |
| `outbox.trace_context` column | 180 B/row, dropped with the row |
| CPU overhead (inject + extract × 5 boundaries) | **+2.1%** |
| p50 latency | +0.4 ms |
| Storage at 0.1% tail sampling | 41 GB/month |

**The 24% payload increase is the notable one.** Mitigation: only propagate for
sampled traces —
```java
if (Span.current().getSpanContext().isSampled()) {
    propagator.inject(Context.current(), fields, Map::put);
}
```
**120 B → 0.12 B amortized**, and unsampled messages carry nothing. The cost of
tracing should be paid by the 0.1% you trace.

---

## Task 5 — Alerting on the signal-less

### (a) A room with a permanent sequence gap — a **derived** metric

No event fires when a sequence number is allocated and never used. Detect it by
comparing what should exist against what does:

```java
@Scheduled(cron = "0 */5 * * * *")
public void detectPermanentGaps() {
    // For active rooms, compare the max seq against the row count. They should
    // differ only by KNOWN gaps.
    var suspect = jdbc.sql("""
            SELECT m.room_id,
                   max(m.seq)                                     AS max_seq,
                   count(*)                                       AS actual,
                   coalesce((SELECT count(*) FROM sequence_gaps g
                             WHERE g.room_id = m.room_id), 0)     AS known_gaps
            FROM messages m
            WHERE m.created_at > now() - interval '1 hour'
            GROUP BY m.room_id
            HAVING max(m.seq) - count(*) > coalesce(
                     (SELECT count(*) FROM sequence_gaps g WHERE g.room_id = m.room_id), 0)
            """).query(GapSuspect.class).list();

    registry.gauge("chat.rooms.with_unexplained_gaps", suspect.size());
    suspect.forEach(s -> log.error("UNEXPLAINED GAP room={} max_seq={} actual={} known={}",
            s.roomId(), s.maxSeq(), s.actual(), s.knownGaps()));
}
```
```yaml
- alert: UnexplainedSequenceGaps
  expr: chat_rooms_with_unexplained_gaps > 0
  for: 10m
  labels: { severity: page }
  annotations:
    summary: "{{ $value }} rooms have sequence gaps we did not record"
```

✅ **This is the alert that catches a class of silent data loss** — a message that
was sequenced and then never persisted. Nothing else in the system would notice.

Validated by injecting the failure:
```bash
curl -X POST localhost:8080/debug/drop-after-sequence -d '{"count":3}'
```
```
ERROR UNEXPLAINED GAP room=room.42 max_seq=48216 actual=48213 known=0
chat_rooms_with_unexplained_gaps 1
```

### (b) A user whose messages consistently fail — a **derived** metric

Aggregate error rates hide a single user with a poisoned state (a corrupt
`clientId`, a permissions edge case, a message body that trips a bug).

```java
private final Cache<String, AtomicInteger> failuresByUser = Caffeine.newBuilder()
        .expireAfterWrite(Duration.ofMinutes(15))
        .maximumSize(100_000)
        .build();

public void recordSendFailure(String userId, String reason) {
    int n = failuresByUser.get(userId, k -> new AtomicInteger()).incrementAndGet();
    if (n == 10) {
        // Cardinality-safe: a COUNTER of affected users, not a per-user gauge.
        persistentlyFailingUsers.increment(Tags.of("reason", reason));
        log.error("USER PERSISTENTLY FAILING user={} reason={} count={}", userId, reason, n);
    }
}
```
```yaml
- alert: UsersPersistentlyFailing
  expr: increase(chat_users_persistently_failing_total[15m]) > 5
  for: 5m
```

✅ Catches "it works for everyone except these six people," which is invisible in
a 99.99% success rate.

### (c) A slow leak in the dedup cache — a **probe**

A cache whose eviction stops working degrades silently: memory climbs over days,
and the only symptom is an OOM three weeks later.

```java
@Component
public class DedupCacheProbe {

    /** Write a known key, verify it's gone after the TTL. */
    @Scheduled(fixedRate = 60_000)
    public void probe() {
        String probeKey = "probe-" + Instant.now().getEpochSecond();
        dedupCache.put(probeKey, SENTINEL);

        scheduler.schedule(() -> {
            boolean stillPresent = dedupCache.getIfPresent(probeKey) != null;
            registry.gauge("chat.dedup.eviction_working", stillPresent ? 0 : 1);
            if (stillPresent) log.error("DEDUP CACHE NOT EVICTING: {} survived its TTL", probeKey);
        }, dedupWindow.plusSeconds(30).toSeconds(), TimeUnit.SECONDS);

        // And the growth signal
        registry.gauge("chat.dedup.size", dedupCache.estimatedSize());
        registry.gauge("chat.dedup.hit_rate", dedupCache.stats().hitRate());
    }
}
```
```yaml
- alert: DedupCacheNotEvicting
  expr: chat_dedup_eviction_working == 0
  for: 5m
  labels: { severity: page }

# The slow leak, caught by trend rather than threshold
- alert: DedupCacheGrowthUnbounded
  expr: predict_linear(chat_dedup_size[6h], 7*24*3600) > 500000
  for: 1h
  annotations:
    summary: "Dedup cache will exceed its bound within 7 days at current growth"
```

✅ **`predict_linear` is the pattern for every slow leak.** A threshold alert
fires when it's already a problem; a trend alert fires while there's still a week
to fix it. Module 18's blind test found exactly this gap for disk.

---

## Task 6 (stretch) — Cost, and halving it

### Measured

| | Volume | Storage/month | Cost/month |
|---|--------|--------------|-----------|
| **Metrics** (41k series, 15 s scrape, 15 d retention) | 2.4 GB | 2.4 GB | $18 |
| **Traces** (0.1% tail sampling, 30 d) | 41 GB | 41 GB | $310 |
| **Logs** (all INFO+, structured JSON) | **892 GB** | 892 GB | **$1,240** |
| Prometheus compute | — | — | $86 |
| Tempo compute | — | — | $104 |
| Loki compute | — | — | $240 |
| **Total** | | **935 GB** | **$1,998** |

**Application overhead:**
```bash
# with and without instrumentation
./code/head_to_head.sh --instrumented / --bare
```
| | Bare | Instrumented | Delta |
|---|------|-------------|-------|
| p50 delivery | 189 ms | 194 ms | **+2.6%** |
| p99 | 402 ms | 418 ms | +4.0% |
| CPU | 41% | **46%** | +12% |
| Heap | 3.1 GB | 3.3 GB | +6% |
| Throughput (knee) | 812k/s | 790k/s | **−2.7%** |

### Halving it: logs are 62% of the bill

```bash
# What is actually in 892 GB?
logcli query '{service="pulse"}' --limit=0 --stats --since=24h
```
```
Total bytes:  29.7 GB/day
By level:   INFO  27.1 GB (91%)
            WARN   2.1 GB
            ERROR  0.5 GB
Top messages by volume:
  1. "delivering to session {}"        18.4 GB (62%)     <-- per-recipient log
  2. "message persisted seq={}"         5.2 GB
  3. "stream entry acked {}"            2.9 GB
```

❌ **One log line per recipient.** At 400,000 outbound messages/second that's
400,000 log lines/second, for information the metrics already have.

**Cut 1 — delete per-recipient logging.**
```java
// BEFORE: 400,000 lines/sec
targets.forEach(sid -> { log.debug("delivering to session {}", sid); send(sid, envelope); });

// AFTER: 1 line per message, and only when something is wrong
if (failures > 0) log.warn("delivered {}/{} for room {}", targets.size() - failures,
                           targets.size(), roomId);
```
**29.7 GB/day → 6.1 GB/day (−79%).**

**Cut 2 — sample the remaining INFO.**
```xml
<turboFilter class="ch.qos.logback.classic.turbo.DuplicateMessageFilter">
  <allowedRepetitions>5</allowedRepetitions>
  <cacheSize>500</cacheSize>
</turboFilter>
```
Plus trace-aware sampling — log everything for sampled traces, sample the rest:
```java
if (Span.current().getSpanContext().isSampled() || level >= WARN) {
    log.info(...);        // full detail for traced requests
}
```
**6.1 GB/day → 2.8 GB/day.**

**Cut 3 — shorter retention on traces.**
```yaml
# Tempo: 30d -> 7d. Nobody investigates a trace from three weeks ago.
retention: 168h
```
**41 GB → 9.6 GB.**

### Result

| | Before | After | Change |
|---|--------|-------|--------|
| Logs | $1,240 | **$117** | −91% |
| Traces | $310 | **$73** | −76% |
| Metrics | $18 | $18 | — |
| Compute | $430 | **$268** | −38% |
| **Total** | **$1,998** | **$476** | **−76%** |
| App CPU overhead | +12% | **+4%** | (less logging work) |
| Throughput | 790k/s | **806k/s** | +2% |

✅ **76% cheaper and 2% faster**, because emitting 400,000 log lines/second was
itself a meaningful cost.

### Can it still answer Task 1's five questions?

Re-run the blind drill:

| Question | Before | After | Notes |
|----------|--------|-------|-------|
| What broke? | 14 s | **14 s** | Dependency matrix is a metric, unaffected |
| When? | 20 s | **20 s** | Metric |
| How many affected? | 8 s | **8 s** | Metric |
| Was data lost? | 15 s | **15 s** | Prober metric |
| Is it fixed? | 30 s | **30 s** | Metric |
| *Bonus: which session failed and why?* | 40 s | **55 s** | Needed the trace, then Loki filtered by traceId |

✅ **All five unchanged**, because every incident question is answered by
**metrics**, not logs. The 892 GB of logs were answering a question nobody asked.

The one regression is the sixth, deeper question — and 15 extra seconds to go
metric → trace → log is a fine price for $1,522/month.

> **The general finding:** observability cost is almost always dominated by logs
> nobody reads, and the biggest single cause is logging inside a fan-out loop.
> **Metrics answer "what and how bad." Traces answer "where." Logs answer "why,"
> and you only need them for the small fraction of requests you're actually
> investigating.** Budget accordingly.
