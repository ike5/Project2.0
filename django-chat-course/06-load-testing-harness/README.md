# Module 06 — The Load-Testing Harness

**Goal:** Build the measurement rig you'll use for the rest of the course, then
use it to break your single-node Channels server — and know precisely *what*
broke, *why*, and at what number.

⏱️ ~5 hours · **Prerequisites:** Modules 00–05.

---

## Why this module exists here

Everything after this point is a claim about scale. "The Redis channel layer
costs one network hop." "Redis Streams cost more than Pub/Sub but lose nothing."
"An async consumer holds more connections than a sync one." "Sharding
subscriptions reduces fan-out cost."

Those claims are worthless to you unless you can check them. So before you build
any of it, you build the thing that tells you whether it worked.

And you establish the **baseline** — the number every later module is measured
against. Without it, "Module 07 made it faster" is a feeling, not an engineering
result. This is the same discipline the JVM twin builds in its
[`06-load-testing-harness`](../../spring-boot-chat-course/06-load-testing-harness/);
the rig is different (raw WebSocket + JSON instead of STOMP, `prometheus_client`
instead of Micrometer), the thesis is identical.

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
receiver's clock, through the whole system — the ASGI server, the consumer, the
channel layer's `group_send`, and back out to a different socket. That's harder
to instrument than "time in my handler," and it's the only number that
corresponds to a human being noticing something.

The server-side timers you'll also build (`chat_group_send_seconds`) measure the
*enqueue* half — how long `group_send` took to hand the message to the channel
layer. Both are useful. Confusing them is how people report 2 ms latency on a
system users find sluggish.

---

## The worker model for this course (read this once, carefully)

This paragraph pins a fact that Modules 06–15 all depend on. Everything in
Module 01 was building to it.

A **node** is one 8-core machine. The honest way to use 8 cores in Python is
**8 worker processes — one per core** — because a single async worker process
runs the event loop on exactly **one** core (the GIL serialises Python bytecode;
`asyncio` gives you cheap concurrency for *I/O* on one core, not parallel CPU).

But Module 04 proved something sharper than the JVM twin ever had to confront:
**the `InMemoryChannelLayer` does not span worker processes even on the same
machine.** Two `uvicorn` workers behind one socket cannot deliver a message from
worker 3's connection to worker 6's connection in the same room. The group
registry is a plain dict in each process's heap, and there is no code that could
join them, because there is no shared memory between processes.

The consequence for *this* module:

> Until Redis arrives (Module 07), a single node's fan-out capacity **is a single
> worker's capacity**: one process, one core. Every number in this module is a
> **one-worker, one-core** number, and that is the sharpest possible statement of
> the Python scaling story.

The single-node fan-out knee we measure here — **≈150,000 outbound msg/s** — is
what one tuned `uvicorn + uvloop` worker sustains before p99 hockey-sticks.
Getting the other seven cores is **not a config flag**; it is a network hop to
Redis, and it is the entire subject of Module 07. When the rest of the course
says "8 workers per node," that is the *post-Redis* deployment. Here, pre-Redis,
**the node is one worker.**

```
   The JVM twin (Module 06):          This course (Module 06):

   one JVM ── 20,000 virtual          one worker ── 20,000 asyncio Tasks
   threads across a SHARED heap,      on ONE event loop, ONE core.
   using ALL 8 cores.
                                      The other 7 cores are unreachable
   knee ≈ 450,000 out msg/s           without a cross-process layer.

                                      knee ≈ 150,000 out msg/s
```

That ~3× gap is not an embarrassment. It is the runtime difference the whole
course exists to make legible: virtual threads share a heap and scale across
cores for free; Python processes do not, so Redis is needed *sooner and more
fundamentally* here than on the JVM. We'll measure the gap, not hand-wave it.

---

## Coordinated omission — the trap that invalidates most load tests

This is the single most important idea in this module.

```python
# The obvious load generator. Also wrong.
while running:
    start = now()
    ws.send(message)
    ws.recv()              # <-- blocks here
    record(now() - start)
```

Here's what happens when the server gets slow: `ws.recv()` blocks longer, so the
loop iterates **less often**, so you send **fewer** messages. The server is
overloaded and you responded by reducing the load.

Worse, the latencies you recorded are all from requests that *did* get through.
Every request you *didn't send* because you were blocked — the ones that would
have been slowest — is simply absent from your data.

```
Intended: 1000 req/s for 10s = 10,000 requests
Server stalls for 5s at t=2

Closed-loop reality:  ~5,000 requests sent, p99 = 40ms   ← "looks fine!"
Open-loop reality:   10,000 requests sent, p99 = 4,800ms ← the truth
```

**The fix: an open model.** Arrivals happen at a fixed rate regardless of
completions. In k6 that's the `constant-arrival-rate` executor:

```js
scenarios: {
  steady: {
    executor: 'constant-arrival-rate',
    rate: 2000, timeUnit: '1s',
    preAllocatedVUs: 500, maxVUs: 5000,
  }
}
```

If k6 can't keep up, it *tells you* (`dropped_iterations`), rather than silently
lying. A non-zero value means your generator, not your server, is the
bottleneck — check it every run.

### Locust and coordinated omission — an honest warning

Because this is a Python course, you'll also run [Locust](https://locust.io),
which is Python top to bottom and is worth knowing. But **Locust's default model
is closed-loop and coordinated-omission-prone**, and you must understand exactly
how before you trust a number it gives you.

A Locust `User` runs a task, then sleeps `wait_time`, then runs the next task.
When the server slows down, the task takes longer — so the *next* task starts
later — so Locust sends fewer requests, and it records response times **only for
requests that completed**. That is textbook coordinated omission. Locust's own
statistics (the median/p95/p99 in its UI) are computed over completed requests
and will *under-report* tail latency under overload, in exactly the way the
closed loop above does.

You can push Locust toward an open model — fire on a fixed timer with
`constant_throughput` / `constant_pacing` and a `LoadTestShape`, or use
`FastHttpUser`-style pacing — but even then Locust measures per-request response
time from *its* send to *its* receive, which for a WebSocket fan-out test is not
the cross-connection number we care about. So in this course:

- **k6 is the ceiling tool.** Open-loop, cross-connection latency, honest
  `dropped_iterations`. Trust it for capacity numbers.
- **Locust is the Python-native tool** you'll reach for when you want to script
  complex user *behaviour* in Python (join rooms, send, react, leave) and when
  the team already knows Python. Use it for behavioural realism and developer
  ergonomics, and read its latency numbers knowing they omit the tail under
  overload.

The lab runs both against the same server so you can *see* the discrepancy rather
than take my word for it.

---

## Your generator will lie to you before your server breaks

Prove the rig isn't the limit before you believe any number.

| Limit | Symptom | Fix |
|-------|---------|-----|
| **Ephemeral ports** | Plateau at ~28,000 connections, exactly | `ip_local_port_range="10000 65535"` → ~55k; beyond that, more source IPs or hosts |
| **File descriptors** | `too many open files` (`OSError: [Errno 24]`) | `ulimit -n 200000` on **both** ends |
| **TIME_WAIT** | Connect failures *after* a run | `ss -s`; wait 60 s, or `tcp_tw_reuse=1` |
| **Generator CPU** | Latency climbs, server CPU flat | Record generator CPU **every run**; over ~70% and the number is garbage |
| **Same-host contention** | Everything is slow, nothing is saturated | Separate hosts, or `taskset` to pin them apart |

The ephemeral-port one deserves emphasis because it produces such a convincing
false result. A connection is a 4-tuple `(src_ip, src_port, dst_ip, dst_port)`.
Your generator has one source IP and ~28,000 usable ports toward
`server:8000`. At 28,000 connections it stops — and it looks *exactly* like a
server ceiling.

```bash
ss -s
cat /proc/sys/net/ipv4/ip_local_port_range
```

**This trap bites Python especially hard** on the same host, because k6/Locust
and `uvicorn` are then fighting for the same cores. On the JVM you had one
process using all cores; here your server is *also* one core per worker, so a
CPU-hungry generator steals from the exact resource you're trying to measure.
Pin them apart with `taskset` and watch both CPUs.

---

## What breaks first, and in what order

Single-node async chat servers fail in a predictable sequence. Knowing it means
you can predict what your graph looks like before you run the test.

```
      ┌──────────────────────────────────────────────┐
  1.  │  File descriptors        ~1,024 (default)    │  instant, obvious
      ├──────────────────────────────────────────────┤
  2.  │  Ephemeral ports (client) ~28,000            │  looks like #4, isn't
      ├──────────────────────────────────────────────┤
  3.  │  RSS: per-connection Python objects          │  gradual, then OOM
      ├──────────────────────────────────────────────┤
  4.  │  Event-loop saturation: one core at 100%     │  ← usually the real one
      │  fan-out serialises; loop lag climbs         │
      ├──────────────────────────────────────────────┤
  5.  │  Slow-consumer write buffers (unbounded)     │  one bad client, whole worker
      ├──────────────────────────────────────────────┤
  6.  │  GC / allocator pauses in the p99.9 tail     │
      └──────────────────────────────────────────────┘
```

**#4 is almost always where a single Channels worker actually dies**, and it's
the least obvious. One message into a 200-member room becomes 200 `send_json`
coroutines the *one* event loop must run, each doing a JSON encode and a socket
write. When the arrival rate of fan-out work exceeds the rate one core can drain
it, the event loop falls behind: scheduled callbacks fire late, `await`s take
longer, and every connection on that worker gets slower at once. There is no
separate broker thread to blame — the loop *is* the bottleneck, and **event-loop
lag** is the gauge that sees it coming.

This is subtly different from the JVM twin, where an unbounded
`clientOutboundChannel` *queue* grew and ate the heap. In asyncio the failure is
CPU/latency first (the loop can't keep up), and memory second (undrained
`transport.write()` buffers, failure mode #5). You'll watch both.

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
At 99% it's 99×. For a single-threaded event loop, `ρ` is simply *the fraction of
wall-clock time the one core spends running Python* — and when it approaches 1.0,
latency explodes.

**Practical consequence:** your safe operating point is **60–70% of the knee**,
not 95%. For our knee of ≈150,000 outbound msg/s, that's **≈100,000 out msg/s**.
The 30% you're "wasting" is what absorbs bursts, failovers, and the extra load
from a node that just died.

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
500,000 outbound messages/second, which is a completely different machine — and,
for one Python core, a machine that doesn't exist. That is why amplification is
the number that forces you to Redis in Module 07.

---

## What to instrument on the server

Django's HTTP metrics come from `django-prometheus`, but the WebSocket / channel
path is invisible to it — WSGI-era middleware never runs on an ASGI WebSocket
scope. So you build a tiny amount yourself with `prometheus_client`, and you get
the histogram bucketing right:

```python
from prometheus_client import Histogram, Counter, Gauge

# publishPercentileHistogram()'s analog: explicit buckets ship to Prometheus and
# aggregate correctly across workers/nodes. Client-side percentiles DO NOT —
# the p99 of three workers is NOT the mean of three p99s.
GROUP_SEND = Histogram(
    "chat_group_send_seconds",
    "Time for group_send() to enqueue a fan-out",
    buckets=(.001, .002, .005, .01, .025, .05, .1, .25, .5, 1, 2.5, 5),
)
MESSAGES_IN  = Counter("chat_messages_inbound_total",  "messages received from clients")
MESSAGES_OUT = Counter("chat_messages_outbound_total", "messages fanned out to sockets")
CONNS        = Gauge("chat_connections_active", "open websocket connections", ["worker"])
LOOP_LAG     = Gauge("chat_event_loop_lag_seconds", "scheduler lateness", ["worker"])
```

⚠️ **Use `Histogram` (buckets), not client-computed percentiles.** Getting this
wrong makes every multi-worker/multi-node dashboard from Module 07 onward quietly
wrong. This is the exact same warning the JVM twin gives about
`publishPercentileHistogram()`, for the exact same reason.

The gauges that predict failure, in priority order:

| Metric | Why it matters |
|--------|---------------|
| `chat_event_loop_lag_seconds` | **The leading indicator.** The one core is falling behind; sustained lag = past the knee |
| `chat_connections_active` | Denominator for everything |
| `process_resident_memory_bytes` | Divide by connections → bytes/connection |
| `chat_group_send_seconds` p99 | The enqueue half of latency; rises as the loop saturates |
| `chat_messages_outbound_total` rate | The number amplification actually produces |
| write-buffer high-water (per socket) | Failure mode #5, the slow consumer |

Because one worker is one core, you also just watch **CPU of that one process**.
When it pins at 100% of a single core, you are at the wall, and no amount of
tuning inside Python moves it — only fewer messages or more processes (Redis)
will.

---

## What's next

The lab builds the k6 harness (open model, cross-connection latency, gap
detection), the Locust equivalent (so you can see coordinated omission with your
own eyes), a `prometheus_client` instrumentation layer and an event-loop-lag
probe, and a metrics collector — then ramps until your single worker falls over,
**three different ways**: file-descriptor exhaustion, event-loop / fan-out
saturation, and the slow-consumer memory attack.

You will record a number that Modules 07, 09, 13, 15, 16 and 22 all compare
against. Take it seriously.

See you in [`lab.md`](./lab.md).
</content>
</invoke>
