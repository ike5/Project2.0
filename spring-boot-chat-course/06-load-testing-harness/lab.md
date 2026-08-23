# Lab 06 — Find the Ceiling

**You'll:** build the k6 and Gatling harnesses, prove your generator isn't the
bottleneck, then break your server three ways — connection exhaustion, fan-out
saturation, and the slow-consumer heap attack.

⏱️ ~100 min. Work in `spring-boot-chat-course/apps/pulse` and
`06-load-testing-harness/code/`.

> **Low-memory path:** if you have under 12 GB, scale every target down 4× (5,000
> connections instead of 20,000). The *shape* of every curve is identical; only
> the absolute numbers move. Note the scale factor in `results.md`.

---

## Part A — Instrument the server

`src/main/java/com/pulse/metrics/ChatMetrics.java`:

```java
package com.pulse.metrics;

import com.pulse.registry.SessionRegistry;
import io.micrometer.core.instrument.*;
import org.springframework.stereotype.Component;

import java.util.concurrent.TimeUnit;

@Component
public class ChatMetrics {

    private final Timer fanoutLatency;
    private final Counter messagesIn;
    private final Counter messagesOut;
    private final DistributionSummary roomSize;

    public ChatMetrics(MeterRegistry registry, SessionRegistry sessions) {

        this.fanoutLatency = Timer.builder("chat.fanout.latency")
                .description("send() to last recipient delivery")
                .publishPercentileHistogram()      // AGGREGATABLE — see the README
                .minimumExpectedValue(java.time.Duration.ofMillis(1))
                .maximumExpectedValue(java.time.Duration.ofSeconds(30))
                .register(registry);

        this.messagesIn  = Counter.builder("chat.messages.inbound").register(registry);
        this.messagesOut = Counter.builder("chat.messages.outbound").register(registry);
        this.roomSize    = DistributionSummary.builder("chat.room.size")
                .publishPercentileHistogram().register(registry);

        Gauge.builder("chat.connections.active", sessions, SessionRegistry::activeConnections)
             .register(registry);
    }

    public void recordFanout(long nanos, int recipients) {
        fanoutLatency.record(nanos, TimeUnit.NANOSECONDS);
        messagesIn.increment();
        messagesOut.increment(recipients);
        roomSize.record(recipients);
    }
}
```

Wire it into `ChatController.send()`:

```java
long t0 = System.nanoTime();
template.convertAndSend("/topic/room." + roomId, envelope);
metrics.recordFanout(System.nanoTime() - t0, sessions.sessionsInRoom(roomId).size());
```

> **This measures enqueue time, not delivery.** `convertAndSend` returns as soon
> as the message is on `brokerChannel`. True end-to-end latency has to be
> measured at the receiving client — which is what the k6 harness does, by
> putting a timestamp in the payload. Both numbers are useful; confusing them is
> how people report 2 ms latency on a system users find sluggish.

---

## Part B — Prepare the machine

```bash
# --- both ends ---
ulimit -n 200000

# --- generator side: the false ceiling ---
sudo sysctl -w net.ipv4.ip_local_port_range="10000 65535"
sudo sysctl -w net.ipv4.tcp_tw_reuse=1

# --- server side: accept backlog ---
sudo sysctl -w net.core.somaxconn=65535
sudo sysctl -w net.ipv4.tcp_max_syn_backlog=65535
```

Give the JVM room and a low-pause collector:

```bash
export JAVA_TOOL_OPTIONS="-Xmx6g -XX:+UseZGC -XX:+ZGenerational \
  -XX:+HeapDumpOnOutOfMemoryError -XX:HeapDumpPath=/tmp \
  -XX:NativeMemoryTracking=summary -Djdk.tracePinnedThreads=full"
./mvnw spring-boot:run
```

Confirm the limits took:
```bash
ulimit -n
cat /proc/sys/net/ipv4/ip_local_port_range
curl -s localhost:8080/actuator/metrics/jvm.memory.max | jq '.measurements[0].value'
```
**Expected:**
```
200000
10000	65535
6442450944
```

---

## Part C — The k6 harness

`code/pulse-load.js`:

```js
import ws from 'k6/ws';
import { check } from 'k6';
import { Trend, Counter, Rate, Gauge } from 'k6/metrics';

const fanout   = new Trend('fanout_latency_ms', true);
const received = new Counter('msgs_received');
const sent     = new Counter('msgs_sent');
const gaps     = new Counter('sequence_gaps');
const errors   = new Rate('ws_errors');
const conns    = new Gauge('open_connections');

const NUL = String.fromCharCode(0);          // STOMP frames are NUL-terminated

const ROOMS      = Number(__ENV.ROOMS      || 100);
const SEND_EVERY = Number(__ENV.SEND_EVERY || 60000);   // ms per user
const HOST       = __ENV.HOST || 'localhost:8080';

export const options = {
  scenarios: {
    ramp: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '1m', target: 2000 },
        { duration: '2m', target: 5000 },
        { duration: '2m', target: 10000 },
        { duration: '2m', target: 20000 },
        { duration: '3m', target: 20000 },     // steady state — MEASURE HERE
      ],
      gracefulRampDown: '30s',
    },
  },
  thresholds: {
    'fanout_latency_ms': ['p(50)<50', 'p(95)<200', 'p(99)<500'],
    'ws_errors':         ['rate<0.01'],
    'sequence_gaps':     ['count<10'],
  },
  summaryTrendStats: ['min', 'med', 'p(95)', 'p(99)', 'p(99.9)', 'max'],
};

export default function () {
  const room = `room.${__VU % ROOMS}`;
  const user = `u${__VU}`;
  let lastSeq = 0;

  const res = ws.connect(`ws://${HOST}/ws`, {}, function (socket) {
    socket.on('open', () => {
      conns.add(1);
      socket.send(`CONNECT\naccept-version:1.2\nheart-beat:10000,10000\nAuthorization:user:${user}\n\n${NUL}`);
      socket.send(`SUBSCRIBE\nid:s0\ndestination:/topic/${room}\n\n${NUL}`);
      socket.send(`SUBSCRIBE\nid:s1\ndestination:/user/queue/ack\n\n${NUL}`);

      // OPEN MODEL: fire on a timer, never waiting for a reply.
      // Jitter the start so 20,000 VUs don't all send on the same tick.
      socket.setTimeout(() => {
        socket.setInterval(() => {
          const payload = JSON.stringify({
            clientId: `c-${__VU}-${Date.now()}`,
            body: `t=${Date.now()}`,          // sender timestamp travels in the body
          });
          socket.send(`SEND\ndestination:/app/${room}/send\ncontent-type:application/json\n\n${payload}${NUL}`);
          sent.add(1);
        }, SEND_EVERY);
      }, Math.random() * SEND_EVERY);
    });

    socket.on('message', (raw) => {
      const split = raw.indexOf('\n\n');
      if (split < 0) return;                             // heartbeat newline
      const body = raw.slice(split + 2).replace(/\x00$/, '');
      if (!body.startsWith('{')) return;                 // CONNECTED frame

      let env;
      try { env = JSON.parse(body); } catch (e) { return; }
      if (env.type !== 'message.new') return;

      const m = env.data;
      const match = /t=(\d+)/.exec(m.body);
      if (match) fanout.add(Date.now() - Number(match[1]));
      received.add(1);

      if (lastSeq && m.seq > lastSeq + 1) gaps.add(m.seq - lastSeq - 1);
      lastSeq = Math.max(lastSeq, m.seq);
    });

    socket.on('error', () => errors.add(true));
    socket.on('close', () => conns.add(-1));
    socket.setTimeout(() => socket.close(), 11 * 60 * 1000);
  });

  check(res, { 'handshake 101': (r) => r && r.status === 101 });
}
```

> **The timestamp-in-the-body trick** is how you measure true end-to-end latency
> across two different connections. The sender writes `Date.now()` into the
> payload; the receiver subtracts. Both are the same k6 process, so the clocks
> agree — which is exactly why you can't do this trivially with two real
> machines.

---

## Part D — Prove the generator isn't the bottleneck

**Do this first, every time. It takes two minutes and prevents wrong conclusions.**

```bash
# Connections only — no messages at all. If THIS plateaus, it's the rig.
k6 run --vus 30000 --duration 2m \
       -e SEND_EVERY=999999999 code/pulse-load.js
```

Watch, in another terminal:
```bash
watch -n1 'ss -s | head -3; echo "---"; \
  ss -tan state established | wc -l; echo "--- generator cpu ---"; \
  ps -o %cpu= -p $(pgrep -x k6)'
```

**Expected (healthy rig):**
```
Total: 30184
TCP:   30052 (estab 30012, closed 88, orphaned 0, timewait 71)
---
30012
--- generator cpu ---
41.2
```

**Expected (broken rig — the false ceiling):**
```
TCP:   28233 (estab 28180, ...)
28180
```
plus in the k6 output:
```
WARN[0074] Request Failed  error="dial: connect: cannot assign requested address"
```

`cannot assign requested address` is **ephemeral port exhaustion**, not a server
limit. If you see it, widen the range (Part B) and re-run. The number it stops at
should be very close to your port-range size.

**Record in `results.md`:**
```
Generator ceiling (connections only): 30,012 @ 41% generator CPU — not limiting
```

---

## Part E — Break #1: connection exhaustion

Start with FDs deliberately low, so you see failure mode #1 in isolation:

```bash
# in the server's shell
ulimit -n 4096
./mvnw spring-boot:run
```
```bash
k6 run -e SEND_EVERY=999999999 --vus 6000 --duration 3m code/pulse-load.js
```

**Expected in the server log**, at just under 4,096 connections:
```
java.io.IOException: Too many open files
	at java.base/sun.nio.ch.Net.accept(Native Method)
WARN o.a.t.u.n.NioEndpoint : Socket accept failed
```

And in k6:
```
checks.........................: 68.01% 4081 out of 6000
```

It stopped at **4,081** — your FD limit minus the ~15 the JVM already held.
Perfectly predictable: **one connection is one file descriptor**. Raise it and
move on:

```bash
ulimit -n 200000
```

**Record:** `FD ceiling: 4,081 with ulimit -n 4096 (confirms 1 FD per connection)`

---

## Part F — Break #2: measure the real ceiling

```bash
k6 run -e ROOMS=100 -e SEND_EVERY=60000 code/pulse-load.js
```

While it runs, collect server-side metrics. `code/collect.sh`:

```bash
#!/usr/bin/env bash
# Sample the metrics that predict failure, once a second, to a CSV.
OUT="${1:-/tmp/pulse-metrics.csv}"
echo "ts,conns,queued_out,queued_in,heap_mb,gc_pause_max_ms,threads,cpu" > "$OUT"
while true; do
  P=$(curl -s localhost:8080/actuator/prometheus)
  ts=$(date +%s)
  conns=$(grep  '^chat_connections_active'            <<<"$P" | awk '{print $2}')
  qout=$(grep   'stomp_channel_queued.*outbound'      <<<"$P" | awk '{print $2}')
  qin=$(grep    'stomp_channel_queued.*inbound'       <<<"$P" | awk '{print $2}')
  heap=$(grep   '^jvm_memory_used_bytes.*area="heap"' <<<"$P" | awk '{s+=$2} END {print s/1048576}')
  gc=$(grep     '^jvm_gc_pause_seconds_max'           <<<"$P" | awk '{if($2>m)m=$2} END {print m*1000}')
  thr=$(grep    '^jvm_threads_live_threads'           <<<"$P" | awk '{print $2}')
  cpu=$(grep    '^system_cpu_usage'                   <<<"$P" | awk '{print $2}')
  echo "$ts,$conns,$qout,$qin,$heap,$gc,$thr,$cpu" >> "$OUT"
  sleep 1
done
```

```bash
chmod +x code/collect.sh
./code/collect.sh /tmp/run1.csv &
k6 run code/pulse-load.js
kill %1
```

**Expected k6 summary** (reference: 8-core / 16 GB, ZGC, 6 GB heap):

```
     checks.........................: 100.00% 20000 out of 20000
     fanout_latency_ms..............: min=2   med=14   p(95)=61   p(99)=147  p(99.9)=890  max=4218
     msgs_received..................: 3891204  6485/s
     msgs_sent......................: 19604    32.6/s
     open_connections...............: 20000
     sequence_gaps..................: 0
     ws_errors......................: 0.00%
     ws_connecting..................: p(95)=284ms

     threshold on fanout_latency_ms p(50)<50  PASS
     threshold on fanout_latency_ms p(95)<200 PASS
     threshold on fanout_latency_ms p(99)<500 PASS
```

**20,000 connections held, 6,485 outbound msg/s, p99 = 147 ms.** All thresholds
pass — a healthy operating point, but not the ceiling.

Find the ceiling by raising the **message rate**, not the connection count:

```bash
k6 run -e SEND_EVERY=10000 code/pulse-load.js      # 6x the message rate
k6 run -e SEND_EVERY=5000  code/pulse-load.js      # 12x
k6 run -e SEND_EVERY=3000  code/pulse-load.js      # 20x
```

**Expected — the knee appears:**

| `SEND_EVERY` | inbound msg/s | outbound msg/s | p50 | p99 | `queued_out` |
|--------------|---------------|----------------|-----|-----|--------------|
| 60000 | 333 | 66,300 | 14 ms | 147 ms | 0 |
| 10000 | 2,000 | 398,000 | 22 ms | 310 ms | spikes to 400 |
| 5000 | 4,000 | 796,000 | 89 ms | **1,840 ms** | **sustained 3,000+** |
| 3000 | 6,666 | 1,326,000 | 410 ms | **9,200 ms** | climbing, never drains |

At `SEND_EVERY=3000` the collector shows the failure in progress:

```bash
tail -3 /tmp/run4.csv
```
```
1735689900,20000,48211,12,5820.4,412.0,71,0.99
1735689901,20000,61044,18,5910.1,398.0,71,0.99
1735689902,20000,77982,22,5988.7,1204.0,71,1.00
```

**`queued_out` climbing monotonically, heap tracking it, CPU pinned at 100%.**
The outbound channel queue is the bottleneck — exactly failure mode #4 from the
README. Note that `queued_in` stays at ~20: inbound is fine. It's amplification
that kills you.

**The knee is between `SEND_EVERY=10000` and `5000`** — roughly **400,000–500,000
outbound messages/second**. Safe operating point: 60–70% of that, so **~300,000
outbound msg/s**.

Record everything:

```markdown
## Module 06 — Single-node ceiling  (8-core/16GB, ZGC, 6GB heap, JDK 21.0.5)

Workload: 20,000 conns, 100 rooms, 200 members/room, amplification 199x
Generator: same host, ulimit 200000, ports 10000-65535, CPU 41% (not limiting)

- Max stable connections:         20,000 (not the limit — untested above)
- KNEE:                           ~450,000 outbound msg/s
- Safe operating point:           ~300,000 outbound msg/s (65% of knee)
- p50/p95/p99 at safe point:      14 / 61 / 147 ms
- Heap after GC at 20k conns:     3,140 MB  ->  157 KB/connection
- Live JVM threads at 20k conns:  71
- What broke first:               clientOutboundChannel queue depth
- Second:                         GC pause (p99.9 890ms -> 4.2s at the knee)
```

> **157 KB per connection** and **71 threads for 20,000 connections.** Compare
> that second number to Module 01's platform-thread run, which needed 20,014
> threads for the same job.

---

## Part G — Break #3: the slow consumer

`code/slow_consumer.py`:

```python
#!/usr/bin/env python3
"""Connect, subscribe, then never read. The heap attack from Module 04."""
import socket, sys, time
sys.path.insert(0, '../../03-realtime-transports/code')
from ws_raw import handshake, encode          # from Module 03's challenge

NUL = b"\x00"

s = socket.create_connection(("localhost", 8080))
s.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 2048)   # tiny receive window
handshake(s, "localhost:8080", "/ws")
s.sendall(encode(b"CONNECT\naccept-version:1.2\nAuthorization:user:slowpoke\n\n" + NUL))
time.sleep(0.3)
s.sendall(encode(b"SUBSCRIBE\nid:s0\ndestination:/topic/room.0\n\n" + NUL))
print("subscribed. now sleeping forever WITHOUT reading.")
time.sleep(1e9)
```

With `setSendBufferSizeLimit` **removed** from `WebSocketConfig`:

```bash
python3 code/slow_consumer.py &
k6 run -e ROOMS=1 -e SEND_EVERY=100 --vus 200 --duration 3m code/pulse-load.js
watch -n1 'curl -s localhost:8080/actuator/metrics/jvm.memory.used | jq ".measurements[0].value/1048576|floor"'
```

**Expected:**
```
heap:  412 MB
heap: 1840 MB
heap: 3910 MB
heap: 5620 MB
java.lang.OutOfMemoryError: Java heap space
Dumping heap to /tmp/java_pid4821.hprof ...
```

**One client killed the server for all 200 others.**

Inspect the dump to confirm the culprit:
```bash
jhat -port 7000 /tmp/java_pid4821.hprof      # or open in VisualVM / Eclipse MAT
```
**Expected** — the dominator tree is one session's buffer:
```
org.springframework.web.socket.handler.ConcurrentWebSocketSessionDecorator
  -> buffer: LinkedList<WebSocketMessage>  size=1,204,881   retained 5.1 GB
```

Now restore the limits:
```java
registration.setSendBufferSizeLimit(512 * 1024).setSendTimeLimit(20 * 1000);
```

**Expected on re-run:**
```
heap stays flat at ~380 MB
```
```
WARN o.s.w.s.m.SubProtocolWebSocketHandler : Closing session ...
org.springframework.web.socket.handler.SessionLimitExceededException:
  Buffer size 524891 exceeded the allowed limit 524288
```

Session closed at ~1,100 buffered messages. **Everyone else unaffected.** That
exception is the safety valve reporting success, not a bug to suppress.

---

## Part H — Gatling, for the report

k6 finds ceilings; Gatling produces the distribution graphs you put in a
document. Add to `pom.xml`:

```xml
<dependency>
  <groupId>io.gatling.highcharts</groupId>
  <artifactId>gatling-charts-highcharts</artifactId>
  <version>3.11.5</version>
  <scope>test</scope>
</dependency>
```

`src/test/java/com/pulse/load/ChatSimulation.java`:

```java
package com.pulse.load;

import io.gatling.javaapi.core.*;
import io.gatling.javaapi.http.*;
import java.time.Duration;

import static io.gatling.javaapi.core.CoreDsl.*;
import static io.gatling.javaapi.http.HttpDsl.*;

public class ChatSimulation extends Simulation {

    /** STOMP's NUL terminator. Gatling trims trailing NULs, so we send a space. */
    private static final String NUL = " ";

    HttpProtocolBuilder httpProtocol = http
            .baseUrl("http://localhost:8080")
            .wsBaseUrl("ws://localhost:8080")
            .wsReconnect()
            .wsMaxReconnects(3);

    ScenarioBuilder chat = scenario("pulse-chat")
        .exec(session -> session.set("user", "g" + session.userId())
                                .set("room", "room." + (session.userId() % 100)))
        .exec(ws("open").connect("/ws"))
        .exec(ws("stomp-connect")
                .sendText(session -> "CONNECT\naccept-version:1.2\nheart-beat:10000,10000\n"
                        + "Authorization:user:" + session.getString("user") + "\n\n" + NUL)
                .await(10).on(ws.checkTextMessage("connected")
                        .check(regex("CONNECTED").exists())))
        .exec(ws("subscribe").sendText(session ->
                "SUBSCRIBE\nid:s0\ndestination:/topic/" + session.getString("room") + "\n\n" + NUL))
        .during(Duration.ofMinutes(5)).on(
            exec(ws("send").sendText(session ->
                    "SEND\ndestination:/app/" + session.getString("room") + "/send\n"
                  + "content-type:application/json\n\n"
                  + "{\"clientId\":\"g-" + session.userId() + "-" + System.nanoTime() + "\","
                  + "\"body\":\"load\"}" + NUL)
                .await(3).on(ws.checkTextMessage("delivered")
                        .check(regex("message.new").exists())))
            .pause(Duration.ofSeconds(1)))
        .exec(ws("close").close());

    {
        setUp(chat.injectOpen(
                rampUsers(5000).during(Duration.ofMinutes(2)),
                constantUsersPerSec(50).during(Duration.ofMinutes(5))
        )).protocols(httpProtocol)
          .assertions(
                global().responseTime().percentile3().lt(500),   // p99
                global().failedRequests().percent().lt(1.0));
    }
}
```

```bash
./mvnw gatling:test -Dgatling.simulationClass=com.pulse.load.ChatSimulation
```

**Expected:**
```
================================================================================
---- Global Information --------------------------------------------------------
> request count                                    1284933 (OK=1284211 KO=722   )
> min response time                                      1 (OK=1      KO=3001   )
> mean response time                                    28 (OK=28     KO=3001   )
> response time 95th percentile                        118 (OK=117    KO=3002   )
> response time 99th percentile                        341 (OK=338    KO=3004   )
> mean requests/sec                                 3572.0
---- Response Time Distribution ------------------------------------------------
> t < 800 ms                                       1284211 ( 99%)
> failed                                                722 (  0%)
================================================================================

Reports generated in target/gatling/pulsechat-20260823141205/index.html
```

Open the HTML report. The **percentiles-over-time** chart is the one worth
keeping — it shows the knee arriving as a curve rather than a single number.

> Note Gatling's `.await(3).on(...)` makes this a **closed model** — coordinated
> omission territory. That's acceptable here because we want distribution shape,
> not absolute ceilings. Use k6 for ceilings, Gatling for pictures, and say which
> you used when you present numbers.

---

## Part I — Run it three times

One run is an anecdote.

```bash
for i in 1 2 3; do
  echo "=== run $i ==="
  ./code/collect.sh /tmp/run-$i.csv &
  k6 run --summary-export=/tmp/summary-$i.json code/pulse-load.js
  kill %1
  sleep 60                     # let TIME_WAIT drain
done

jq -r '.metrics.fanout_latency_ms["p(99)"]' /tmp/summary-*.json
```

**Expected:**
```
147.2
151.8
144.9
```

A ~5% spread. If your three runs differ by more than ~15%, something
uncontrolled is happening — background processes, thermal throttling, or a
generator closer to its limit than you thought. Find it before trusting any
later comparison.

**Record the median and the spread.** Every later module compares against this.

---

## What you built and measured

- A k6 harness with an **open model**, end-to-end latency measurement, and gap
  detection.
- A Gatling simulation for distribution reports.
- A metrics collector that captures the leading indicator (`queued_out`).
- Proof that your generator isn't the bottleneck.
- **Three deliberate failures**, each understood: FD exhaustion, outbound-queue
  saturation, and the slow-consumer heap attack.
- A baseline: **~450,000 outbound msg/s knee, 157 KB/connection, 71 threads for
  20,000 connections.**

You now have a number. Everything in Phase 2 has to beat it — or explain why it
doesn't.

Now do [`challenge.md`](./challenge.md).

Then: [Module 07 — Scaling Out: Pub/Sub Fan-Out](../07-scale-out-redis-pubsub/).
