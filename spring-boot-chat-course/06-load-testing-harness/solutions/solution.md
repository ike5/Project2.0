# Solutions — Module 06

Reference machine: 8-core / 16 GB, Ubuntu 24.04, JDK 21.0.5, ZGC, 6 GB heap.

---

## Task 1 — Coordinated omission, quantified

### The two scenarios

```js
// closed-loop.js — the WRONG way
export const options = { scenarios: { closed: {
  executor: 'constant-vus', vus: 500, duration: '3m' } } };

export default function () {
  ws.connect(url, {}, function (socket) {
    socket.on('open', () => sendOne(socket));
    socket.on('message', () => {                 // <-- next send waits for this
      record(Date.now() - sentAt);
      sendOne(socket);
    });
  });
}
```
```js
// open-loop.js — the RIGHT way
export const options = { scenarios: { open: {
  executor: 'constant-arrival-rate',
  rate: 500, timeUnit: '1s', duration: '3m',
  preAllocatedVUs: 800, maxVUs: 2000 } } };
```

### Inducing the stall

```java
@MessageMapping("/debug/stall")
public void stall(@Payload StallRequest r) throws InterruptedException {
    stallUntil = System.currentTimeMillis() + r.millis();
}
// in the send path:
long remaining = stallUntil - System.currentTimeMillis();
if (remaining > 0) Thread.sleep(remaining);
```

### Results — 3-minute run, 5-second stall injected at t=90s

| | Closed loop | Open loop |
|---|-------------|-----------|
| Requests attempted | 89,412 | **90,000** (500/s × 180 s) |
| Requests completed | 89,412 | 88,247 |
| `dropped_iterations` | n/a | 1,753 |
| p50 | 8 ms | 9 ms |
| p95 | 31 ms | 44 ms |
| **p99** | **112 ms** | **4,780 ms** |
| p99.9 | 890 ms | 4,996 ms |
| max | 5,020 ms | 5,031 ms |

### The explanation

During the 5-second stall the two generators behaved completely differently:

**Closed loop:** all 500 VUs were blocked in `awaitResponse()`. They sent
**500 requests total** across the whole 5-second window (one each, already
in flight). When the server recovered, those 500 recorded ~5,000 ms — and 500
samples out of 89,412 is **0.56%**, which lands at the p99.4 mark. It barely
moves p99.

**Open loop:** k6 kept arriving at 500/s regardless. In 5 seconds that's
**2,500 requests** that queued behind the stall, each recording between 0 and
5,000 ms. Those 2,500 samples are **2.8%** of the total, so they dominate
everything above p97.2.

```
                 requests that experienced the stall
closed loop:     500  / 89,412  = 0.56%   -> p99 unaffected (112ms)
open loop:     2,500  / 90,000  = 2.78%   -> p99 = 4,780ms
```

**The closed-loop generator responded to overload by reducing load.** That's the
definition of coordinated omission: the samples that would have been slowest were
never taken, because the generator was too polite to take them.

> **Note `dropped_iterations: 1,753`.** k6 is telling you it couldn't start
> iterations on schedule — it ran out of VUs while they were stuck in the stall.
> That's an honest signal you must check every run; a large value means your
> open-loop test partially degenerated into a closed-loop one.

**Real users are an open loop.** They keep pressing send whether or not you're
having a good day.

---

## Task 2 — The 157 KB breakdown

Method: measure at 5,000 and 20,000 connections, subtract, divide by 15,000.

```bash
jcmd <pid> GC.run && sleep 2
jcmd <pid> GC.heap_info
jcmd <pid> VM.native_memory summary
jcmd <pid> GC.class_histogram | head -30
cat /proc/net/sockstat
```

### Results

| Component | Bytes/conn | How measured |
|-----------|-----------|--------------|
| **TCP socket buffers (kernel)** | **~62,000** | `/proc/net/sockstat` TCP `mem` pages × 4096 ÷ conns |
| Tomcat `NioChannel` + read/write ByteBuffers | ~34,000 | NMT "Other" delta; 16 KB read + 16 KB write buffers |
| `WsSession` + `ConcurrentWebSocketSessionDecorator` | ~21,000 | class histogram delta |
| STOMP subscription registry entries (2 subs/conn) | ~11,000 | `DefaultSubscriptionRegistry` retained size |
| `SimpSession` + principal + session attributes map | ~14,000 | histogram |
| Our `SessionRegistry` entries (3 maps) | ~9,000 | histogram, `ConcurrentHashMap$Node` |
| Micrometer per-connection tags | ~4,000 | histogram |
| Misc / fragmentation | ~2,000 | remainder |
| **Total** | **~157,000** | matches the aggregate |

### The largest contributor: kernel socket buffers (62 KB, 39%)

This is **not heap** — it's why `docker stats` shows more memory than
`jvm_memory_used` and why people are confused by OOM kills with a healthy heap.

```bash
sysctl net.ipv4.tcp_rmem net.ipv4.tcp_wmem
```
```
net.ipv4.tcp_rmem = 4096	131072	6291456
net.ipv4.tcp_wmem = 4096	16384	4194304
```

Linux starts each socket at the *default* (131 KB read, 16 KB write) and grows to
the max under load. For chat — tiny, infrequent messages — that default read
buffer is enormously oversized.

**The concrete change that halves it:**

```bash
sudo sysctl -w net.ipv4.tcp_rmem="4096 16384 1048576"
sudo sysctl -w net.ipv4.tcp_wmem="4096 16384 1048576"
```

Measured effect:

| | Before | After |
|---|--------|-------|
| Kernel bytes/conn | 62,000 | **19,000** |
| Total bytes/conn | 157,000 | **114,000** (−27%) |
| Connections in 6 GB heap + 8 GB RSS budget | ~51,000 | **~70,000** |
| p99 latency | 147 ms | 151 ms (no meaningful change) |

**27% more connections per box for one sysctl.** The tradeoff is that a genuinely
large burst to one client now needs more round trips — irrelevant for 500-byte
chat messages, and something you'd revisit if you added file transfer to the same
socket.

**The runner-up:** Tomcat's 16 KB read + 16 KB write ByteBuffers per connection.
Configurable via `server.tomcat.max-http-form-post-size` and the
`socket.appReadBufSize` / `appWriteBufSize` properties, but be careful — shrinking
them below your max frame size causes fragmentation and more syscalls. Measure.

> **The general point:** most "per-connection memory" on a socket server is not
> your application's. Before optimizing your session object, check the kernel.

---

## Task 3 — Isolate the bottleneck

Four interventions, one variable each, all at `SEND_EVERY=5000` (past the knee,
p99 = 1,840 ms baseline):

| Intervention | Hypothesis tested | p99 after | Verdict |
|--------------|-------------------|-----------|---------|
| `maxPoolSize` 64 → 256 | Thread starvation on outbound | **1,780 ms** | ❌ No effect |
| Payload 500 B → 5 B | CPU in serialization | **1,610 ms** | ⚠️ Small effect |
| ZGC → Parallel GC | GC pauses own the tail | 2,940 ms (worse) | ❌ Not the cause |
| **Rooms 200 → 20 members** (same total conns, same inbound) | **Fan-out amplification** | **34 ms** | ✅ **This is it** |
| `-XX:ActiveProcessorCount=16` (fake more cores) | CPU count | 1,795 ms | ❌ No effect |

### Reading this

**Raising `maxPoolSize` did nothing.** More threads don't help when the threads
are already CPU-bound — you added contention, not capacity. The pool was never
starved; it was saturated. (Check: `stomp.channel.active` was pinned at 64 before
*and* 256 after, but system CPU was 100% in both cases.)

**Shrinking the payload helped 12%.** So serialization is real but minor —
it's ~12% of the cost, not the bottleneck.

**Changing the collector made it worse.** ZGC was already doing its job; Parallel
GC added 1.1 s of stop-the-world to the tail. This rules out GC *as the cause*
while confirming it *contributes to the tail* (p99.9 was 890 ms under ZGC).

**Cutting room size 10× improved p99 by 54×.** Same connections, same inbound
rate, same payload, same everything — only the amplification factor changed, from
199× to 19×.

### The conclusion

The bottleneck is **outbound message volume**, and the outbound channel queue is
where it manifests. Not threads, not CPU per message, not GC.

**Which means the fix is architectural, not a tuning knob.** You cannot configure
your way out of 800,000 outbound messages/second on one JVM. You need either
fewer outbound messages (smaller rooms, aggregation, client-side pull) or more
JVMs — which is Phase 2.

> **This is the most valuable experiment in the module.** Three of the five
> interventions are the ones a team would try first, and all three are wrong.
> Being able to rule them out with data — rather than trying them in production
> one sprint at a time — is the whole reason to build a harness.

---

## Task 4 — The regression gate

`code/ci-gate.js`:

```js
import ws from 'k6/ws';
import { Trend, Rate } from 'k6/metrics';

const fanout = new Trend('fanout_latency_ms', true);
const errors = new Rate('ws_errors');
const NUL = String.fromCharCode(0);

export const options = {
  scenarios: {
    gate: {
      executor: 'constant-arrival-rate',
      rate: 200, timeUnit: '1s',
      duration: '3m',
      preAllocatedVUs: 400, maxVUs: 1000,
      gracefulStop: '15s',
    },
  },
  thresholds: {
    // Baseline p99 = 147ms. Gate at 2x baseline + headroom for CI noise.
    // Deliberately loose: a gate that cries wolf gets disabled by the team.
    'fanout_latency_ms': ['p(50)<40', 'p(99)<400'],
    'ws_errors':         ['rate<0.005'],
    'dropped_iterations': ['count<100'],     // guard against generator-side lies
  },
  // 45s of warm-up excluded: JIT compilation dominates the first 30s.
  discardResponseBodies: true,
};
```

```yaml
# .github/workflows/perf-gate.yml
- name: Performance gate
  run: |
    docker compose -f infra/compose.dev.yml up -d --wait
    java -jar target/pulse.jar &
    timeout 60 bash -c 'until curl -sf localhost:8080/actuator/health/readiness; do sleep 2; done'
    sleep 45                                   # JVM warm-up
    k6 run --quiet code/ci-gate.js
```

### Stability — 10 consecutive runs

```
run  1: p99=163ms  PASS
run  2: p99=171ms  PASS
run  3: p99=158ms  PASS
run  4: p99=402ms  FAIL   <-- noisy neighbour on the CI runner
run  5: p99=169ms  PASS
run  6: p99=155ms  PASS
run  7: p99=181ms  PASS
run  8: p99=166ms  PASS
run  9: p99=174ms  PASS
run 10: p99=160ms  PASS
```

**False-positive rate: 1/10 = 10%.** Too high — a gate that fails 10% of the time
gets ignored within two weeks.

Two fixes, both applied:

1. **Raise the threshold to `p(99)<500`.** Reruns 1–10 all pass. Costs
   sensitivity, buys trust.
2. **Better: retry once on failure, fail only on two consecutive failures.**
   Independent 10% failures give a 1% combined rate, while keeping the tighter
   400 ms threshold and catching real regressions on the second run.

```yaml
    k6 run --quiet code/ci-gate.js || k6 run --quiet code/ci-gate.js
```

Final measured false-positive rate over 20 runs with the retry: **0/20**.

### Catching an injected regression

```java
// The Module 01 sin: a synchronized block on the send path.
private final Object lock = new Object();

@MessageMapping("/room.{roomId}/send")
public void send(...) {
    synchronized (lock) {                       // <-- injected regression
        var result = messages.send(roomId, principal.getName(), create);
        template.convertAndSend(...);
    }
}
```

**Expected:**
```
     fanout_latency_ms..............: p(50)=1,204ms  p(99)=8,940ms

     threshold on fanout_latency_ms p(50)<40  FAILED
     threshold on fanout_latency_ms p(99)<400 FAILED

ERRO[0195] thresholds on metrics have been crossed
exit status 99
```

Caught on both thresholds, and by a wide margin — 8,940 ms against a 400 ms gate.
The retry also failed, so it isn't a flake.

Confirm the mechanism:
```bash
java -Djdk.tracePinnedThreads=full -jar target/pulse.jar 2>&1 | grep -c 'monitors:1'
```
```
28471
```
28,471 pinning events. The virtual threads couldn't unmount while holding the
monitor across the database call inside `messages.send()`.

> **Why `p(50)` is in the gate and not just `p(99)`:** a p50 threshold catches
> *systemic* regressions (everything got slower) while p99 catches *tail*
> regressions (something occasionally stalls). They fail for different reasons
> and you want to know which.

---

## Task 5 — The capacity plan

**Assumptions, stated explicitly:**
- Measured knee: **450,000 outbound msg/s per node**; operate at 65% = **292,500**.
- 100,000 concurrent users, each sending **1 message / 5 minutes** = 333 msg/s
  inbound, total, regardless of room size.
- Connection ceiling per node: **50,000** (from the 157 KB/conn measurement
  against an 8 GB budget), or 70,000 with the tuned socket buffers.
- Users belong to exactly one active room. (Real users are in several; see below.)
- No message batching, no client-side pull, no read-time assembly.

| Avg room size | Outbound msg/s | Nodes for fan-out | Nodes for connections | **Nodes needed** |
|---------------|----------------|-------------------|----------------------|------------------|
| 10 | 3,330 | 1 | 2 | **2** (connection-bound) |
| 50 | 16,650 | 1 | 2 | **2** (connection-bound) |
| 200 | 66,600 | 1 | 2 | **2** (connection-bound) |
| 1,000 | 333,000 | **2** | 2 | **2** (both binding) |
| 5,000 | 1,665,000 | **6** | 2 | **6** (fan-out-bound) |
| 20,000 | 6,660,000 | **23** | 2 | **23** |

### Where it breaks

**The crossover from connection-bound to fan-out-bound is at ~1,000 members.**
Below that, you're buying nodes to hold sockets. Above it, you're buying nodes to
push bytes — and cost grows **linearly with room size** while revenue does not.

**The architecture stops working around 20,000-member rooms.** At 23 nodes for
100,000 users you're spending more on fan-out than the product can plausibly
justify, and — critically — **every node must receive every message for every
room it has a subscriber in.** With 23 nodes and users spread randomly, nearly
every node has a subscriber in nearly every large room, so the Redis backbone
must deliver each message to all 23. That's a 23× amplification *on top of* the
room amplification, and it's the wall Module 13 attacks.

**What would have to change:**

1. **Fan-out on read for large rooms.** Above a threshold (Slack's is reportedly
   in the low thousands), stop pushing. Clients poll or long-poll a per-room
   cursor. Turns O(members) writes into O(active viewers) reads, and active
   viewers of a 20,000-person channel is maybe 200.
2. **Shard subscriptions by room** so a given room lives on a known subset of
   nodes rather than all of them (Module 13). Kills the 23× node amplification.
3. **Batch and coalesce.** Deliver up to N messages or 50 ms of accumulation in
   one frame. At 6,660,000 msg/s with 10× batching that's 666,000 frames — a
   different problem.
4. **Move fan-out off the JVM entirely** — a dedicated edge tier in Rust/Go/C++
   whose only job is holding sockets and copying bytes. This is what the largest
   systems do, and it's the honest answer at the top end.

> **A correction to my own assumption:** users are in several rooms, not one. A
> user in 8 rooms receives messages from all 8, so the real outbound number is
> higher than this table by roughly the average room count — but the *inbound*
> number stays at 333/s. Rerun the table with `outbound = inbound × avg_room_size
> × avg_rooms_per_user` for a real plan. The shape of the conclusion doesn't
> change; the crossover just arrives sooner.

---

## Task 6 (stretch) — Two hosts

Setup: server on the 8-core host, generator on a second machine over gigabit
ethernet, same switch.

| Metric | Single host (loopback) | Two hosts (1 GbE) | Change |
|--------|----------------------|-------------------|--------|
| Max connections | 20,000 | 20,000 | — |
| p50 fanout | 14 ms | 15 ms | +7% |
| p95 fanout | 61 ms | 68 ms | +11% |
| **p99 fanout** | **147 ms** | **119 ms** | **−19%** |
| p99.9 | 890 ms | 720 ms | −19% |
| **Knee (outbound msg/s)** | **~450,000** | **~610,000** | **+36%** |
| Server CPU at knee | 100% | 100% | — |
| Generator CPU at knee | 71% (same box!) | 58% (own box) | — |

### The two competing effects

**Effect 1 — freed CPU (dominant, helps).** On a single host, k6 was consuming
~40–70% of the same 8 cores the JVM needed. The server was never actually getting
8 cores. Moving the generator off returned roughly 3 cores to the JVM, which is
why the **knee moved up 36%**.

**Effect 2 — real network cost (secondary, hurts).** Loopback has no MTU
fragmentation, no NIC interrupt handling, no driver, and ~5 µs RTT. Real
gigabit ethernet adds ~150 µs RTT, 1500-byte MTU fragmentation for larger
frames, and softirq CPU for packet processing. This is why **p50 got 7% worse**.

**Effect 1 wins decisively at the tail; Effect 2 wins slightly at the median.**
The median is dominated by network RTT (which got worse); the tail is dominated
by CPU contention and queueing (which got much better).

### The takeaway

**Single-host numbers understate your server's capacity, sometimes badly.**
A 36% error on the ceiling is enough to make a wrong capacity decision — you'd
buy 36% more nodes than you need.

But it's *conservative* in the direction that matters, which is why the
single-host numbers in this course are still useful: if your server meets its SLO
on a contended single host, it will meet it on a real one.

**What single-host numbers cannot show you at all:**
- Behaviour under packet loss and jitter (loopback has none) — this is why
  Module 03 used `tc netem` explicitly.
- NIC or bandwidth saturation. At 610,000 outbound msg/s × 500 bytes = **2.4
  Gbit/s**, gigabit ethernet was in fact the binding constraint in the two-host
  run above 610k. The "knee" measured there is partly a *network* knee, not a
  server one — which is itself a useful discovery, and the reason the run should
  be repeated on 10 GbE before treating 610,000 as the server's number.

> Note that last point carefully: **the two-host test found a new false ceiling
> of its own.** There is no setup with no confounders; there are only confounders
> you have identified. Always state the one you're most worried about.
