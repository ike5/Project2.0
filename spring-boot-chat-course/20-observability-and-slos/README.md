# Module 20 — Observability & SLOs

**Goal:** Instrument a system whose defining characteristic is that **nothing is
a request** — no request ID, no response, no status code — and define SLOs that
correspond to what a user actually notices.

⏱️ ~5 hours · **Prerequisites:** Modules 00–19.

---

## Why chat breaks normal observability

Every observability default assumes a request/response cycle:

| Standard assumption | Chat reality |
|--------------------|--------------|
| A request has a response | A message has **N deliveries**, to different connections, at different times |
| Latency = response time − request time | Latency spans **two connections** and possibly two processes |
| Errors are status codes | A message that silently never arrives has no status code |
| A trace follows one thread | Fan-out crosses a Redis Stream, a thread pool, and N sockets |
| Traffic = requests/second | Inbound rate is a **lie**; `inbound × room size` is the load |

The consequence: you can have a dashboard that is entirely green while users
cannot chat. Module 06 measured a case exactly like that — 200,000 messages/second
with an 8-second p99.

---

## RED and USE, adapted

**RED** (service level): Rate, Errors, Duration.

| | Standard | Chat |
|---|---------|------|
| **Rate** | requests/sec | **inbound msg/s AND outbound msg/s** — report both, always |
| **Errors** | 5xx rate | send rejections + **undelivered messages** + sequence gaps |
| **Duration** | response time | **send → last recipient delivery** |

**USE** (resource level): Utilization, Saturation, Errors.

Saturation is the one people skip and the one that predicts outages:

| Resource | Utilization | **Saturation** ← the leading indicator |
|----------|-------------|--------------------------------------|
| App node | CPU % | **`stomp.channel.queued{outbound}`** |
| Redis | ops/sec | **`XPENDING` depth, `stream.lag`** |
| Postgres | active connections | **`cl_waiting` in PgBouncer, `hikaricp.pending`** |
| Outbox relay | rows/sec | **`outbox.backlog`** |
| Connections | count | **connections / measured ceiling** |

Every one of those saturation metrics was built in an earlier module because it
was the thing that broke first. This module puts them on one dashboard.

---

## Histograms, not summaries

```java
Timer.builder("chat.fanout.latency")
     .publishPercentileHistogram()      // buckets, aggregatable
     .register(registry);
```

⚠️ **Client-side percentiles cannot be averaged.** The p99 of three servers is
*not* the mean of their three p99s. `publishPercentiles()` alone computes
quantiles in-process and ships numbers; `publishPercentileHistogram()` ships
buckets, which Prometheus can sum correctly across instances.

Get this wrong and every multi-instance dashboard from Module 07 onward is
quietly, confidently wrong.

## Cardinality will take down your monitoring

```java
// This creates one time series PER USER. At 1M users, your Prometheus dies.
Counter.builder("chat.messages").tag("userId", userId).register(registry);
```

```
series = product of all label cardinalities
  room_id (100,000) × node (8) × type (6) = 4,800,000 series
```

Prometheus needs roughly **3 KB of RAM per active series**. 4.8M series is 14 GB,
for one metric.

| Label | Cardinality | Safe? |
|-------|-------------|-------|
| `node` | ~10 | ✅ |
| `type` (`message.new`, …) | ~10 | ✅ |
| `outcome` (ok/rejected/dropped) | ~5 | ✅ |
| `room_size_bucket` (small/medium/large) | 3 | ✅ **bucket, don't label** |
| `room_id` | 100,000+ | ❌ |
| `user_id` | 1,000,000+ | ❌❌ |
| `client_id` | unbounded | ❌❌❌ |

**Per-entity detail belongs in logs and traces, not metrics.** If you need "which
room is slow," use exemplars — a histogram bucket can carry a sample trace ID
without creating a series.

---

## Tracing across an async fan-out

A trace normally follows a thread. Pulse's message crosses:

```
client → node A (thread 1) → Postgres → outbox → relay (thread 2)
       → Redis Stream → node B (thread 3) → 200 sockets
```

Three processes, three thread pools, one durable queue. Context does not
propagate itself across any of them.

You must **inject and extract manually**:

```java
// Producing side — put the W3C traceparent in the stream entry
var fields = new HashMap<String, String>();
fields.put("payload", json.writeValueAsString(envelope));
propagator.inject(Context.current(), fields, Map::put);      // adds "traceparent"

// Consuming side — restore it before doing work
Context extracted = propagator.extract(Context.current(), record.getValue(), GETTER);
try (Scope scope = extracted.makeCurrent()) {
    deliver(roomId, record);
}
```

**And sample aggressively.** At 400,000 outbound messages/second, 1% sampling is
4,000 spans/second, which is already a lot of storage. Use:

- **Tail sampling** — keep 100% of traces that were slow or errored, 0.1% of the
  rest. This is what you actually want and it needs a collector that buffers.
- **Span the fan-out as one span with an attribute**, not 200 spans. A span per
  recipient is 200× your trace volume for information a histogram already gives
  you.

```java
span.setAttribute("chat.recipients", recipients);
span.setAttribute("chat.room_size_bucket", bucket(recipients));
```

---

## SLIs that correspond to something

An SLI must be something a user would complain about.

| Candidate SLI | Good? | Why |
|---------------|-------|-----|
| CPU under 80% | ❌ | Nobody has ever noticed CPU |
| p99 fan-out latency | ⚠️ | Close — but a *delivered late* message and a *never delivered* one are different complaints |
| **Delivery success rate** | ✅ | "My message didn't arrive" |
| **Delivery latency p99** | ✅ | "Messages are slow" |
| **Connection success rate** | ✅ | "I can't connect" |
| **Reconnect gap duration** | ✅ | "It keeps dropping" |
| Sequence gap rate | ✅ | "Messages are missing from history" |

Pulse's four:

```
SLI 1  Delivery success:   delivered / (published × recipients)     >= 99.99%
SLI 2  Delivery latency:   p99(send → last delivery)                <  500 ms
SLI 3  Connection success: successful handshakes / attempts          >= 99.9%
SLI 4  Sequence integrity: rooms with a permanent gap / rooms       <  0.01%
```

**SLI 1 is the hard one to measure**, because you can't count what didn't happen.
The lab measures it two ways: server-side (deliveries attempted versus
recipients) and client-side (a synthetic prober that verifies receipt).

---

## Error budgets

An SLO of 99.9% over 30 days is **43 minutes** of allowed failure.

```
budget_remaining = 1 - (observed_failures / allowed_failures)
```

The point isn't the number; it's the decision rule:

| Budget remaining | Policy |
|-----------------|--------|
| > 50% | Ship freely |
| 10–50% | Ship, prioritize reliability work |
| **< 10%** | **Feature freeze; reliability only** |
| Exhausted | Freeze, incident review |

**Burn-rate alerting** is what makes this operational. Alerting on "SLO
violated" is too late; alert on the *rate* of consumption:

```
14.4× burn over 1 hour  → you'll exhaust a 30-day budget in ~2 days → page
6×    burn over 6 hours → exhausted in ~5 days                      → page
1×    burn over 3 days  → on track to exhaust exactly                → ticket
```

The multi-window, multi-burn-rate approach (from Google's SRE workbook) catches
both a sudden severe failure and a slow leak, without paging on a brief blip.

---

## Alert on symptoms, not causes

| Bad alert | Why | Better |
|-----------|-----|--------|
| `redis_cpu > 80%` | Users don't experience CPU | `chat_delivery_latency_p99 > 500ms` |
| `pod_restarts > 0` | Restarts can be routine | `chat_connection_success < 99.9%` |
| `disk_usage > 80%` | Not yet a problem | `predict_linear(disk_avail[6h], 24*3600) < 0` |

**Cause-based alerts fire constantly and get muted. Symptom-based alerts fire
when something is actually wrong.** Keep cause metrics on dashboards for
diagnosis; alert on symptoms.

The exception is **runway alerts** — anything that can be exhausted (disk,
partitions, error budget, connection capacity) deserves a *predictive* alert,
because by the time it's a symptom it's an outage. Module 18's blind test found
exactly this gap.

---

## What's next

The lab builds the full stack — Prometheus, Grafana, Tempo, structured logs with
trace correlation — instruments true end-to-end delivery, propagates trace
context across the outbox and the Redis Stream, defines the four SLOs with
burn-rate alerts, and then runs Module 18's drills to see whether the dashboard
tells you what happened.

See you in [`lab.md`](./lab.md).
