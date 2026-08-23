# Module 06 — The Load-Testing Harness

**Goal:** Build a measurement rig you'll use for the rest of the course, then use
it to break your single-node chat server — and know precisely *what* broke,
*why*, and at what number.

⏱️ ~5 hours · **Prerequisites:** Modules 00–05.

---

## Why this module exists here

Everything after this point is a claim about scale. "Redis Streams cost more than
Pub/Sub." "WebFlux holds more connections than virtual threads." "Sharding
subscriptions reduces fan-out cost."

Those claims are worthless to you unless you can check them. So before you build
any of it, you build the thing that tells you whether it worked.

And you establish the **baseline** — the number every later module is measured
against. Without it, "Module 07 made it faster" is a feeling.

---

## The one rule

> **Measure the client's experience, not the server's throughput.**

A server logging 200,000 messages/second while p99 fan-out latency is 8 seconds
is a broken chat server that looks great on a dashboard. The metric that matters:

```
From the instant sender S calls send(),
how long until receiver R's socket has the bytes?

Reported at p50, p95, p99, p99.9.
```

Note it's an **end-to-end, cross-connection** measurement: sender's clock to
receiver's clock, through the whole system. That's harder to instrument than
"time in my handler," and it's the only number that corresponds to a human being
noticing something.

---

## Coordinated omission — the trap that invalidates most load tests

This is the single most important idea in this module.

```java
// The obvious load generator. Also wrong.
while (running) {
    long start = now();
    send(message);
    awaitResponse();          // <-- blocks here
    record(now() - start);
}
```

Here's what happens when the server gets slow: `awaitResponse()` blocks longer,
so the loop iterates **less often**, so you send **fewer** messages. The server
is overloaded and you responded by reducing the load.

Worse, the latencies you recorded are all from requests that *did* get through.
Every request you *didn't send* because you were blocked — the ones that would
have been slowest — is simply absent from your data.

```
Intended: 1000 req/s for 10s = 10,000 requests
Server stalls for 5s at t=2

Closed-loop reality:  ~5,000 requests sent, p99 = 40ms   ← "looks fine!"
Open-loop reality:   10,000 requests sent, p99 = 4,800ms ← the truth
```

**The fix: an open model.** Send at a fixed rate regardless of responses.

```js
// k6: an OPEN model — arrivals don't depend on completions
scenarios: {
  steady: {
    executor: 'constant-arrival-rate',
    rate: 2000, timeUnit: '1s',
    preAllocatedVUs: 500, maxVUs: 5000,
  }
}
```

If k6 can't keep up, it *tells you* (`dropped_iterations`), rather than silently
lying. Watch that metric — a non-zero value means your generator, not your
server, is the bottleneck.

---

## Your generator will lie to you before your server breaks

Prove the rig isn't the limit before you believe any number.

| Limit | Symptom | Fix |
|-------|---------|-----|
| **Ephemeral ports** | Plateau at ~28,000 connections, exactly | `ip_local_port_range="10000 65535"` → ~55k; beyond that, more source IPs or more hosts |
| **File descriptors** | `too many open files` | `ulimit -n 200000` on **both** ends |
| **TIME_WAIT** | Connect failures *after* a run | `ss -s`; wait 60 s, or `tcp_tw_reuse=1` |
| **Generator CPU** | Latency climbs, server CPU flat | Record generator CPU **every run**; over ~70% and the number is garbage |
| **Same-host contention** | Everything is slow, nothing is saturated | Separate hosts, or `taskset` to pin them apart |

The ephemeral port one deserves emphasis because it produces such a convincing
false result. A connection is `(src_ip, src_port, dst_ip, dst_port)`. Your
generator has one source IP and ~28,000 usable ports toward `server:8080`. At
28,000 connections it stops — and it looks *exactly* like a server ceiling.

```bash
ss -s
cat /proc/sys/net/ipv4/ip_local_port_range
```

---

## What breaks first, and in what order

Single-node chat servers fail in a predictable sequence. Knowing it means you can
predict what your graph will look like before you run the test.

```
      ┌──────────────────────────────────────────────┐
  1.  │  File descriptors        ~1,024 (default)    │  instant, obvious
      ├──────────────────────────────────────────────┤
  2.  │  Ephemeral ports (client) ~28,000            │  looks like #4, isn't
      ├──────────────────────────────────────────────┤
  3.  │  Heap: per-connection state                  │  gradual, then OOM
      ├──────────────────────────────────────────────┤
  4.  │  clientOutboundChannel queue depth           │  ← usually the real one
      ├──────────────────────────────────────────────┤
  5.  │  CPU: JSON serialization × fan-out           │
      ├──────────────────────────────────────────────┤
  6.  │  GC pause time in the p99.9 tail             │
      └──────────────────────────────────────────────┘
```

**#4 is almost always where a Spring STOMP server actually dies**, and it's the
least obvious. One message into a 500-member room becomes 500 tasks on the
outbound channel. When arrival exceeds drain rate, the queue grows without bound
(that's the default) and your heap disappears into it.

This is why Module 04 had you bound that queue and export a gauge for it. In this
module you watch the gauge climb and correlate it with the latency knee.

---

## The knee

Latency versus load is not a line. It's a hockey stick.

```
p99 │                                        ╱
 ms │                                      ╱
    │                                   ╱
    │                              ╱
    │  ─────────────────────╱
    └───────────────────────┬───────────────── offered load
                          knee
              operate HERE ←┤
```

Queueing theory says waiting time grows as roughly `1/(1−ρ)` where `ρ` is
utilization. At 50% utilization, queue delay is 1× service time. At 90% it's 9×.
At 99% it's 99×.

**Practical consequence:** your safe operating point is **60–70% of the knee**,
not 95%. The 30% you're "wasting" is what absorbs bursts, failovers, and the
extra load from a node that just died.

Finding the knee — not the maximum — is the goal of every capacity test in this
course.

---

## Fan-out amplification, stated properly

Every benchmark result in this course must state this, or it means nothing:

```
inbound_rate × average_room_size = outbound_rate
```

```
20,000 connections, 100 rooms, 200 members each, 1 msg/user/60s

  inbound:  20,000 / 60          =     333 msg/s   ← what naive dashboards show
  outbound: 333 × 199            =  66,267 msg/s   ← the actual work
  amplification:                      199×
```

"Can it handle 1,000 messages a second?" is an unanswerable question. "Can it
handle 1,000 messages a second into 500-member rooms?" is a capacity plan for
500,000 outbound messages/second, which is a completely different machine.

---

## What to instrument on the server

```java
Timer.builder("chat.fanout.latency")
     .publishPercentileHistogram()      // AGGREGATABLE across instances
     .register(registry);
```

⚠️ **Use `publishPercentileHistogram()`, not just `publishPercentiles()`.**
Client-side percentiles cannot be averaged: the p99 of three servers is *not* the
mean of three p99s. Histograms ship buckets, which Prometheus can sum correctly.
Getting this wrong makes every multi-instance dashboard from Module 07 onward
quietly wrong.

The gauges that predict failure, in priority order:

| Metric | Why it matters |
|--------|---------------|
| `stomp.channel.queued{channel="outbound"}` | **The leading indicator.** Non-zero and sustained = you're past the knee |
| `chat.connections.active` | Denominator for everything |
| `jvm.memory.used` after GC | Divide by connections → bytes/connection |
| `jvm.gc.pause` max | Owns your p99.9 |
| `hikaricp.connections.pending` | Module 01's unbounded-concurrency trap, visible |
| `chat.send.retry.detected` | Clients retrying = they think you're slow |

---

## What's next

The lab builds the k6 harness, the Gatling harness for detailed reports, and a
metrics collection script — then ramps until your server falls over, three
different ways.

You will record a number that Modules 07, 09, 13, 15, 16 and 22 all compare
against. Take it seriously.

See you in [`lab.md`](./lab.md).
