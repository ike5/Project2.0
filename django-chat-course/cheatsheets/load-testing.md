# Cheatsheet — Load Testing Real-Time Systems with Locust

The Python-native half of the Module 06 harness. Locust is the tool whose *user
classes read like the code you already write* — you model a chat user joining
rooms, sending, reacting and leaving in ordinary Python, and you reuse your own
envelope helpers. That is worth a lot.

It is also the tool most likely to lie to you about tail latency, and this
cheatsheet spends more space on *why* than on syntax, because the syntax is
easy and the lie is expensive.

> **Division of labour in this course** (pinned in
> [`../06-load-testing-harness/`](../06-load-testing-harness/)): **k6** is the
> ceiling tool — open-loop, cheap per socket, honest about dropped iterations —
> so capacity numbers come from it. **Locust** is the behaviour tool. Everything
> below is about making Locust give you numbers you can defend.

---

## The one rule

> **Measure the client's experience, not the server's throughput.**

A chat server reporting 200,000 messages/second while p99 fan-out latency is
8 seconds is a broken chat server. The metric that matters is:

```
From the instant sender S calls send(),
how long until RECEIVER R's socket has the bytes?

Reported at p50, p95, p99, p99.9.
```

Note **receiver**, not sender. This is a cross-connection measurement — sender's
clock, through the ASGI server, the consumer, the channel layer's `group_send`,
back out to a *different* socket. Locust's built-in stats measure per-request
"my send → my receive", which is a different and much friendlier number. You have
to fire the real one yourself; the recipe is below.

---

## Locust's concurrency model (and why it matters here)

Locust runs on **gevent**. Every `User` is a greenlet, and `gevent.monkey.patch_all()`
runs at import, so blocking socket calls in `websocket-client` become
cooperative yields instead of real blocks.

Two consequences you must internalize:

1. **This is Module 01's "Answer B" via monkey-patching** — the thing the course
   told you Python doesn't really have. It works, and it's why Locust can hold
   thousands of sockets per process. It is also why an un-patched C extension in
   your `User` code (a synchronous crypto call, a native JSON parser doing a long
   parse) blocks *every other user in that process*, exactly like blocking an
   event loop.
2. **One Locust process is one core.** Same GIL, same story as your server. A
   single Locust process saturates around **3,000–5,000 WebSocket users** on the
   reference machine before its own CPU becomes the bottleneck. Use
   `--processes` (Locust 2.19+) to fork one worker per core:

```bash
locust -f locustfile.py --processes 8 --headless -u 20000 -r 500 -t 6m
```

Anything less and you will "discover" a server ceiling that is really your
generator's ceiling. **Check generator CPU every single run.**

---

## Load-generator ceilings (false bottlenecks)

Before you believe any number, prove the *generator* isn't the limit.

| Limit | Symptom | Fix |
|-------|---------|-----|
| Ephemeral ports | Plateaus at almost exactly ~28,000 conns | `sysctl -w net.ipv4.ip_local_port_range="10000 65535"` (~55k), or add source IPs |
| File descriptors | `OSError: [Errno 24] Too many open files` | `ulimit -n 200000` on **both** ends |
| TIME_WAIT buildup | Connect failures *after* a run | `ss -s`; wait 60 s, or `net.ipv4.tcp_tw_reuse=1` |
| Locust process CPU | Latency climbs, server CPU flat | `--processes N`; keep each worker under ~70% |
| Coordinated omission | Suspiciously good p99 under overload | see the next section — the big one |
| Same-host contention | Everything slow, nothing saturated | `taskset` the generator and server apart, or two machines |

```bash
ss -s                                       # socket summary by state
ss -tan state established | wc -l
watch -n1 'ss -s; uptime'
cat /proc/sys/net/ipv4/ip_local_port_range
```

> **The ephemeral-port trap deserves emphasis** because it produces such a
> convincing false result. A connection is a 4-tuple `(src_ip, src_port, dst_ip,
> dst_port)`. Your generator has one source IP and ~28,000 usable ports toward
> `server:8000`. At 28,000 it stops — and it looks *exactly* like a server
> ceiling. It bites this course harder than the JVM twin because Locust and
> Uvicorn are both one-core-per-process, so co-locating them means they fight for
> the exact resource you're measuring.

---

## Coordinated omission — the reason to read this file

```python
# The obvious Locust task. Also wrong.
@task
def send_message(self):
    self.ws.send(envelope)
    self.ws.recv()               # <-- blocks here
```

When the server gets slow, `recv()` blocks longer → the task iterates less often
→ **you send fewer messages**. The server is overloaded and you responded by
*reducing the load*. Worse, every request you didn't send — the ones that would
have been slowest — is simply absent from your data.

```
Intended: 1000 req/s for 10s = 10,000 requests
Server stalls for 5s at t=2

Closed-loop reality:  ~5,000 sent, p99 =    40 ms   ← "looks fine!"
Open-loop reality:   10,000 sent, p99 = 4,800 ms   ← the truth
```

**Locust's default model is closed-loop.** A `User` runs a task, sleeps
`wait_time`, runs the next. Its median/p95/p99 are computed over *completed*
requests and will under-report tail latency under overload, by design.

### The three things that get Locust closer to honest

**1. `constant_throughput` / `constant_pacing`, not `between`.**

```python
from locust import User, task, constant_throughput

class ChatUser(User):
    # "run this task at most N times per second, regardless of how long it took"
    wait_time = constant_throughput(1)      # 1 task/s per user
```

`constant_throughput(1)` targets one iteration per second per user; if an
iteration takes 900 ms it waits 100 ms, and if it takes 1.4 s it waits 0. That
last case is the honest signal — **arrival rate you failed to achieve**. Locust
reports it as a shortfall in RPS versus `users × rate`, and you must look at it.
`constant_pacing(1)` is the same idea expressed as a fixed period.

**2. Decouple sending from receiving.** In a fan-out test, the reply doesn't come
back on the sending socket anyway — it arrives on *other* users' sockets. So run
a receiver greenlet per user and never block the send task on a recv.

**3. Record latency from the message's own timestamp**, not from the local
send/recv pair. The envelope carries `ts`; the receiver subtracts. This turns
Locust's stats into the cross-connection number you actually want.

With all three, Locust is *usably* honest. It still cannot do what k6's
`constant-arrival-rate` executor does — spawn work regardless of whether the
previous iteration finished — so past the knee, trust k6.

---

## The WebSocket user — the reference recipe

Locust has no built-in WebSocket user. The course drives one with
`websocket-client` (installed in Module 00, verified in `VERIFY.md`).

`code/locustfile.py`:

```python
import json, os, random, time, uuid
import gevent
import websocket
from locust import User, task, events, constant_throughput
from locust.runners import MasterRunner

HOST     = os.getenv("PULSE_HOST", "localhost:8000")
ROOMS    = int(os.getenv("ROOMS", "100"))
ROOM_SIZE_HINT = int(os.getenv("ROOM_SIZE", "200"))


class WebSocketUser(User):
    """One chat user: one socket, one receiver greenlet, paced sends.

    The receiver greenlet is what makes this open-ish: the send task never
    waits for a reply, so a slow server does NOT slow down our send rate.
    """
    abstract = True

    def on_start(self):
        self.cid_prefix = uuid.uuid4().hex[:8]
        self.room = f"room.{random.randrange(ROOMS)}"
        self.ws = websocket.create_connection(
            f"ws://{HOST}/ws/{self.room}/?ticket={self._ticket()}",
            timeout=10,
            # gevent has monkey-patched this socket; the timeout is cooperative.
        )
        self.ws.send(json.dumps({"type": "hello", "token": self._token()}))
        self.ws.recv()                                   # hello_ok
        self.connected_at = time.time()
        self._stop = False
        self._pump = gevent.spawn(self._receive_loop)    # <-- the important line

    def on_stop(self):
        self._stop = True
        try:
            self.ws.close()
        finally:
            self._pump.kill(block=False)

    def _receive_loop(self):
        """Every inbound frame is a DELIVERY. Time it from the sender's clock."""
        while not self._stop:
            try:
                raw = self.ws.recv()
            except (websocket.WebSocketConnectionClosedException, OSError) as e:
                self._fire("ws_recv", 0, exc=e)
                return
            if not raw:
                return
            now = time.time()
            try:
                msg = json.loads(raw)
            except ValueError:
                continue
            if msg.get("type") != "message.new":
                continue                                  # acks, presence, control
            sent_at = msg["data"].get("ts")
            if sent_at is None:
                continue
            # THE NUMBER: sender's send() -> this receiver's socket.
            self._fire("fanout", (now - sent_at) * 1000, length=len(raw))

    @task
    def send_message(self):
        payload = json.dumps({
            "type": "message.create",
            "room": self.room,
            "clientId": f"{self.cid_prefix}-{time.time_ns()}",
            "ts": time.time(),                            # the sender's clock
            "body": "x" * 40,
        })
        t0 = time.time()
        try:
            self.ws.send(payload)
        except Exception as e:
            self._fire("ws_send", (time.time() - t0) * 1000, exc=e)
            return
        # Record the SEND cost only. Do NOT recv() here — that's the trap.
        self._fire("ws_send", (time.time() - t0) * 1000, length=len(payload))

    # ---- plumbing -----------------------------------------------------------
    def _fire(self, name, ms, length=0, exc=None):
        events.request.fire(
            request_type="WS", name=name, response_time=ms,
            response_length=length, exception=exc, context={"room": self.room},
        )

    def _ticket(self):   # Module 21's single-use ticket; stubbed in early modules
        return os.getenv("PULSE_TICKET", "dev")

    def _token(self):
        return os.getenv("PULSE_TOKEN", "dev")


class ChatUser(WebSocketUser):
    wait_time = constant_throughput(1 / 60)      # 1 message per user per 60s
    weight = 1
```

Run it:

```bash
locust -f code/locustfile.py --processes 8 --headless \
       -u 20000 -r 500 -t 6m \
       --csv=/tmp/pulse-locust --html=/tmp/pulse-locust.html
```

**Expected (moderate-load baseline — 20,000 conns, 100 rooms, 200 members,
1 msg/user/60 s; 8-core/16 GB, Python 3.12, Uvicorn+uvloop, Django 5.1 /
Channels 4.1):**

```
Type  Name      # reqs   # fails |    Avg     Min     Max    Med |   req/s
------|---------|--------|--------|-------|-------|-------|------|--------
WS    fanout   3,978,412      0  |     19       2   1,940     11 | 66,307
WS    ws_send     19,984      0  |      0       0      12      0 |    333

Percentiles (approximated) — fanout
  50%    11
  95%    52
  99%   138
  99.9% 640
```

✅ **p50 11 ms, p95 52 ms, p99 138 ms, p99.9 640 ms** — the pinned Module 06
baseline. Note `fanout` req/s = 66,307 ≈ 333 × 199: the amplification, visible in
the output.

---

## Fan-out amplification — state it or the number means nothing

```
inbound_rate × (average_room_size − 1) = outbound_rate
```

```
20,000 connections, 100 rooms, 200 members each, 1 msg/user/60s

  inbound:  20,000 / 60   =     333 msg/s   ← what naive dashboards show
  outbound: 333 × 199     =  66,267 msg/s   ← the actual work
  amplification:               199×
```

"Can it handle 1,000 messages a second?" is unanswerable. "Can it handle 1,000
messages a second into 500-member rooms?" is a capacity plan for 500,000
outbound msg/s — which, for one Python core, is a machine that does not exist.
Amplification is the number that forces you to Redis in Module 07.

---

## Shaping the load: ramps, steps, and finding the knee

Locust's `LoadTestShape` replaces `-u/-r` with a programmatic schedule. Use a
**step** shape to find the knee, not a smooth ramp — a smooth ramp smears the
knee across the whole run and you can't point at it.

```python
from locust import LoadTestShape

class StepToKnee(LoadTestShape):
    """Hold each step long enough for the queue to reach steady state.
    60s is too short: you measure the transient, not the equilibrium."""
    steps = [
        # (users, spawn_rate, hold_seconds)
        ( 5_000, 250, 180),
        (10_000, 250, 180),
        (15_000, 250, 180),
        (20_000, 250, 180),
        (25_000, 250, 180),
        (30_000, 250, 180),
    ]

    def tick(self):
        run_time = self.get_run_time()
        elapsed = 0
        for users, rate, hold in self.steps:
            elapsed += hold
            if run_time < elapsed:
                return (users, rate)
        return None          # stop the test
```

```bash
locust -f code/locustfile.py --processes 8 --headless -t 20m --csv=/tmp/knee
```

Then read the knee out of the per-step percentiles:

```
users    out msg/s   p50    p99      generator CPU
 5,000      16,500    9 ms    41 ms       18%
10,000      33,000   10 ms    58 ms       33%
15,000      49,500   11 ms    94 ms       49%
20,000      66,300   11 ms   138 ms       61%
25,000      82,900   14 ms   287 ms       69%
30,000      99,500   21 ms   612 ms       74%   ← generator getting hot; add processes
```

Latency versus load is a **hockey stick**, not a line:

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

Queueing theory: waiting time grows roughly as `1/(1−ρ)`. At 50% utilization
queue delay is 1× service time; at 90% it's 9×; at 99% it's 99×. For a
single-threaded event loop `ρ` is simply the fraction of wall-clock time the one
core spends running Python.

**Your safe operating point is 60–70% of the knee, not 95%.** For the pinned
single-node knee of **≈150,000 outbound msg/s**, that is **≈100,000 out msg/s**.
The 30% you're "wasting" absorbs bursts, failovers, and the extra load from a
node that just died.

---

## Making percentiles trustworthy

Locust's console shows approximated percentiles built from rounded response-time
buckets. That's fine for p50/p95 and increasingly wrong at p99.9. Two fixes:

**1. Use the CSV, which reports finer percentiles:**
```bash
locust ... --csv=/tmp/pulse --csv-full-history
column -s, -t /tmp/pulse_stats.csv
```

**2. For anything you'll quote in an architecture review, keep your own
histogram** and compute percentiles from raw samples:

```python
from locust import events
import numpy as np

SAMPLES = []

@events.request.add_listener
def _collect(name, response_time, exception, **kw):
    if name == "fanout" and exception is None:
        SAMPLES.append(response_time)

@events.quitting.add_listener
def _report(environment, **kw):
    a = np.array(SAMPLES)
    for q in (50, 95, 99, 99.9):
        print(f"  p{q:<5} {np.percentile(a, q):8.1f} ms   (n={a.size:,})")
```

> ⚠️ **Percentiles do not average.** The p99 of three Locust workers is *not*
> the mean of three p99s, and neither is the p99 of three app nodes. If you need
> aggregated percentiles across processes, aggregate the raw samples (or use
> Prometheus histogram buckets on the server side — Module 06 makes this point
> about `prometheus_client.Histogram` for the same reason).

---

## Detecting loss and gaps, not just latency

Latency is half the story. Module 07's `docker pause` loses ~15% of messages
while p99 looks *fine*, because a lost message has no latency at all. Track
sequence gaps:

```python
class GapDetectingUser(ChatUser):
    def on_start(self):
        super().on_start()
        self.last_seq = {}

    def _fire_delivery(self, msg):
        room, seq = msg["data"]["room"], msg["data"]["seq"]
        prev = self.last_seq.get(room)
        if prev is not None and seq > prev + 1:
            events.request.fire(request_type="WS", name="gap",
                                response_time=0, response_length=seq - prev - 1,
                                exception=None)
        self.last_seq[room] = max(seq, prev or 0)
```

**Expected (Module 07 `docker pause redis`, 30 s, at-most-once Pub/Sub layer):**
```
WS   gap        412 events   14.9% of expected deliveries missing
```
**Expected (Module 09, the same drill on the Streams-backed layer):**
```
WS   gap          0 events
```

That contrast — same latency shape, 15% loss versus 0% — is the entire argument
of Phase 2, and Locust's numbers alone would never have shown it.

---

## Locust vs k6 — an honest table

| | Locust | k6 |
|---|--------|-----|
| Language | **Python** — same as your app, reuse envelope code | JavaScript |
| Concurrency | gevent greenlets, **1 core/process** | Go goroutines, all cores |
| Sockets per process (reference machine) | ~3,000–5,000 | ~30,000 |
| Load model | closed-loop by default; `constant_throughput` gets close | true open model (`constant-arrival-rate`) |
| Tells you when it can't keep up | only indirectly (RPS shortfall) | explicitly (`dropped_iterations`) |
| WebSocket support | none built in — `websocket-client` + a greenlet | first-class (`k6/ws`) |
| Modelling complex behaviour | **excellent** — it's just Python | awkward |
| Live UI | **yes**, and it's genuinely good for exploration | terminal summary |
| Trust for capacity ceilings | ⚠️ verify against k6 | ✅ |

**Use Locust when:** you're modelling *behaviour* (join 4 rooms, scroll history,
react, go idle, reconnect), when the team is Python and will actually maintain
the script, when you want the live UI while poking at the system, and for
regression tests well below the knee.

**Use k6 when:** the output is a capacity number someone will plan against.

The lab in Module 06 runs both against the same server *specifically so you can
watch the discrepancy appear past the knee* rather than take anyone's word for it.

---

## Distributed Locust

```bash
# master (aggregates, serves the UI)
locust -f code/locustfile.py --master --expect-workers 4

# workers, one per machine (each forks --processes across its cores)
locust -f code/locustfile.py --worker --master-host 10.0.0.5 --processes 8
```

`--processes N` on a single host is the shorthand for a local master plus N
workers, and it's what you want on a laptop. Go multi-host when you need more
than ~40,000 sockets or more source IPs than one NIC's ephemeral range provides.

⚠️ **Every worker runs the whole `locustfile`.** Module-level state (a shared
counter, a pre-built room list) is per-process, not global. Use
`@events.test_start` and the master/worker message API if you need coordination:

```python
from locust import events
from locust.runners import MasterRunner, WorkerRunner

@events.test_start.add_listener
def _(environment, **kw):
    if isinstance(environment.runner, WorkerRunner):
        environment.runner.send_message("ready", {"pid": os.getpid()})
```

---

## What to measure, per module

| Module | Question | Primary metric |
|--------|----------|----------------|
| 06 | How many sockets on one worker? | Max stable users before p99 breaks or errors appear |
| 06 | Where's the memory going? | RSS ÷ connections → **bytes/connection** (pinned ≈45 KB) |
| 06 | Where's the knee? | Outbound msg/s where p99 goes superlinear (pinned ≈150k) |
| 07 | Cost of the Redis hop? | p50 delta (pinned ≈ +4 ms) and 1-node vs 2-node knee (≈1.9×) |
| 07 | Does Pub/Sub lose messages? | **gap count during `docker pause`** (≈15%) |
| 09 | Streams vs Pub/Sub? | +5 ms p50, ~2× Redis CPU, **0 gaps** on the same drill |
| 10 | Resume after a 2-min disconnect | Messages missed: 98 without resume, 0 with |
| 11 | Presence storm | Redis ops/s when 10,000 users connect at once |
| 13 | Replica lag under write load | `replay_lag` vs msg/s |
| 15 | Sync vs async vs raw ASGI | KB/conn and p99 at equal load (120 / 45 / 28 KB) |
| 16 | Redis vs Kafka | p99 plus CPU/RAM of the broker tier |
| 18 | Failover cost | **Messages lost and seconds unavailable during a drill** |
| 22 | Does it hit target? | All of the above, at once |

---

## Watching the server while the test runs

```bash
# per-worker CPU — for one async worker, 100% of ONE core IS the wall
top -H -p $(pgrep -d, -f 'uvicorn pulse.asgi')
pidstat -p $(pgrep -f 'uvicorn pulse.asgi' | head -1) 1

# the leading indicator: event-loop lag
curl -s localhost:8000/metrics | grep -E 'chat_event_loop_lag|chat_connections_active'

# bytes per connection
curl -s localhost:8000/metrics | grep -E 'process_resident_memory_bytes|chat_connections_active'

# Redis, during Phase 2 runs
redis-cli --stat
redis-cli INFO stats | grep -E 'instantaneous_ops_per_sec|evicted_keys'
redis-cli SLOWLOG GET 10
```

**`chat_event_loop_lag_seconds` is the leading indicator.** It rises before p99
does, because the loop falling behind is *why* p99 rises. If you graph one thing
during a Locust run, graph that.

---

## Reporting the number

A number without this context is not a result:

```
Server:     8-core / 16 GB, Ubuntu 24.04, Python 3.12, Django 5.1 / Channels 4.1
            Uvicorn 0.30 + uvloop, 8 workers, RedisChannelLayer (channels_redis 4.2)
Generator:  Locust 2.32, --processes 8, separate host,
            ulimit -n 200000, ip_local_port_range 10000-65535, CPU peak 61%
Workload:   20,000 connections, 100 rooms, 200 members/room, 1 msg/user/60s
            = 333 msg/s in, 66,267 msg/s out (199x fan-out amplification)
Duration:   10 min steady state after a 3 min ramp; first 3 min excluded
Result:     p50 11ms  p95 52ms  p99 138ms  p99.9 640ms   0 errors, 0 gaps
            RSS 900 MB / 20,000 conns -> 45 KB per connection
Runs:       3; reported median. Spread on p99: 131-149 ms.
```

The **fan-out amplification** line is the one people forget. Inbound rate is not
the load.

---

## Run checklist

- [ ] Generator and server on separate hosts, or `taskset`-pinned apart
- [ ] `ulimit -n` raised on **both** ends
- [ ] Ephemeral port range widened on the generator
- [ ] `--processes` ≥ cores; generator CPU recorded and under ~70%
- [ ] `constant_throughput`/`constant_pacing`, never `between()` for a capacity run
- [ ] Sends and receives decoupled (receiver greenlet), latency taken from the
      envelope's `ts`, not from a local send/recv pair
- [ ] Gap/loss detection on, not just latency
- [ ] Ramp excluded from the reported window; each step held ≥ 3 min
- [ ] Percentiles computed from raw samples for anything you'll quote
- [ ] Fan-out amplification stated next to the inbound rate
- [ ] Run ≥ 3×; report the median **and the spread**, not the best run
- [ ] Cross-checked against k6 if the number is a capacity ceiling
