# Solutions — Module 06

Reference machine for every number: **8-core / 16 GB, Ubuntu 24.04, Python
3.12, Django 5.1, Channels 4.1, Uvicorn + uvloop, `--workers 1`,
`InMemoryChannelLayer`.** Scale factor 1×.

---

## Task 1 — Coordinated omission, in k6

### The two scenarios

`code/co-closed.js` — the wrong way, written the way people actually write it:

```js
import ws from 'k6/ws';
import { Trend } from 'k6/metrics';

const rt = new Trend('roundtrip_ms', true);

export const options = {
  scenarios: {
    closed: { executor: 'constant-vus', vus: 500, duration: '3m' },
  },
  summaryTrendStats: ['med', 'p(95)', 'p(99)', 'p(99.9)', 'max', 'count'],
};

export default function () {
  ws.connect(`ws://localhost:8000/ws/room/0/?as=c${__VU}`, {}, function (socket) {
    let sentAt = 0;
    const fire = () => {
      sentAt = Date.now();
      socket.send(JSON.stringify({v: 1, type: 'message.create', data: {
        client_id: `c-${__VU}-${sentAt}`, body: `t=${sentAt} pad` }}));
    };
    socket.on('open', fire);
    socket.on('message', (raw) => {
      const env = JSON.parse(raw);
      if (env.type !== 'message.new') return;
      rt.add(Date.now() - sentAt);       // record...
      fire();                            // ...then, and only then, send again
    });
    socket.setTimeout(() => socket.close(), 3 * 60 * 1000);
  });
}
```

`code/co-open.js` — the same work, arriving on a schedule:

```js
export const options = {
  scenarios: {
    open: {
      executor: 'constant-arrival-rate',
      rate: 500, timeUnit: '1s', duration: '3m',
      preAllocatedVUs: 800, maxVUs: 3000,
    },
  },
};
```

The stall is the lab's `?ms=5000` debug endpoint, fired at t = 90 s.

### Results — 3-minute run, one 5-second stall

| | `constant-vus` (closed) | `constant-arrival-rate` (open) |
|---|------------------------|-------------------------------|
| Iterations the model intended | n/a (VU-paced) | **90,000** = 500/s × 180 s |
| Iterations started | 86,912 | 88,102 |
| `dropped_iterations` | n/a | **1,898** |
| p50 | 9 ms | 10 ms |
| p95 | 33 ms | 46 ms |
| **p99** | **141 ms** | **4,712 ms** |
| p99.9 | 918 ms | 4,988 ms |
| max | 5,022 ms | 5,041 ms |

**33× disagreement at p99, on one server, during one outage.**

### Why, arithmetically

```
During the 5 seconds the loop was blocked:

closed:  all 500 VUs were parked inside socket.on('message'). Between them
         they had exactly 500 sends in flight. 500 / 86,912 = 0.58% of the
         samples -> the stall lands at p99.42 -> p99 barely moves.

open:    k6 kept starting iterations at 500/s regardless. 500 x 5 = 2,500
         messages entered the stall. 2,500 / 88,102 = 2.84% of the samples
         -> the stall owns everything above p97.16 -> p99 = 4,712 ms.
```

The closed-loop generator **responded to overload by offering less load.** The
samples that would have been slowest were never taken.

### What `dropped_iterations: 1,898` means

k6 is telling you it could not start 1,898 of the 90,000 iterations on schedule
— it ran out of VUs because 500 of them were stuck in the stall and `maxVUs`
capped how many replacements it could spawn.

**A non-zero `dropped_iterations` means your open-loop test partially
degenerated into a closed-loop one**, and every number in that run is biased in
the optimistic direction by exactly the amount you dropped.

```
1,898 / 90,000 = 2.1% of the intended arrivals never happened
```

**Throw-away threshold: 1% of intended iterations.** Below that, the bias is
smaller than the run-to-run spread you measured in Part K (5%) and you can
report the number with a footnote. Above it, raise `maxVUs`, add generator
processes, or move the generator to its own host — and re-run.

> **The trap inside the trap:** raising `maxVUs` to 10,000 makes
> `dropped_iterations` go to zero *and* makes the generator's own CPU the
> bottleneck, at which point the run is garbage for a different reason. There is
> no setting that removes the need to check both numbers. Check both, every run.

> **Why this matters more in Python than on the JVM.** The JVM twin's server had
> eight cores to absorb a burst of arrivals. Yours has one. An open-loop
> generator therefore drives your server past its knee *faster* and with *less*
> offered load than the same test drives a JVM — so a closed-loop test flatters
> a Python server by more, not less. Never quote a closed-loop tail for this
> architecture.

---

## Task 2 — Where 63 KB goes, and how to get it back

### Method

Measure at 5,000 and 20,000 connections and subtract, so that the interpreter,
Django's app registry, the ORM's model cache and every import are cancelled out.
Aggregate first, then attribute:

```bash
# aggregate
grep VmRSS /proc/$PID/status              # at 5,000 and again at 20,000
grep TCP: /proc/net/sockstat

# attribution — run inside the worker via a DEBUG-only view
python - <<'EOF'
import gc, sys
from collections import Counter
sizes = Counter()
for obj in gc.get_objects():
    sizes[type(obj).__qualname__] += sys.getsizeof(obj)
for name, total in sizes.most_common(15):
    print(f"{total/1048576:8.1f} MB  {name}")
EOF
```

`sys.getsizeof` is shallow, so walk the interesting objects explicitly
(`tracemalloc.take_snapshot().compare_to()` between the two connection counts is
the higher-fidelity version and agrees to within 6%).

### The application half — 46.2 KB

| Component | Bytes/conn | How measured |
|-----------|-----------|--------------|
| ASGI `scope` dict (headers as a list of byte-tuples, `url_route`, `client`, `server`, `subprotocols`, `session`) | **9,400** | `sys.getsizeof` walk of `consumer.scope` |
| `websockets` protocol object + reader/writer buffers + frame `deque` | 11,800 | `tracemalloc` delta, `websockets.legacy.protocol` |
| `RoomConsumer` instance + `__dict__` (`self.room` Room, `self.user` User, `self.group`, base_send closure) | 7,600 | object walk |
| The asyncio `Task` driving the consumer, plus its live coroutine frames (three: `__call__`, `await_many_dispatch`, `receive`) | 5,200 | `len(asyncio.all_tasks())` × frame walk |
| Channel-layer bookkeeping: `groups[group][channel]` entry, the per-channel `asyncio.Queue`, the channel-name `str` | 4,900 | `layer.groups` / `layer.channels` walk |
| `AuthMiddlewareStack` residue: session dict, `LazyObject` wrapper | 2,300 | object walk |
| Python object headers, dict over-allocation, pymalloc arena slack | 5,000 | remainder |
| **Total** | **46,200** | matches the aggregate |

**The largest single contributor is the ASGI `scope` — 9,400 bytes, 20% — and
almost none of it is ever read after `connect()` returns.**

Look at what is in there:

```python
# DEBUG-only view
{'type': 'websocket', 'path': '/ws/room/0/', 'raw_path': b'/ws/room/0/',
 'headers': [(b'host', b'localhost:8000'), (b'user-agent', b'k6/0.54.0 ...'),
             (b'accept-encoding', b'gzip'), (b'sec-websocket-key', b'...'),
             (b'sec-websocket-version', b'13'), (b'connection', b'Upgrade'),
             (b'upgrade', b'websocket'), (b'sec-websocket-protocol', b'pulse.v1'),
             (b'cookie', b'sessionid=...; csrftoken=...')],
 'query_string': b'as=u4711', 'client': ['127.0.0.1', 51422],
 'server': ['127.0.0.1', 8000], 'subprotocols': ['pulse.v1'],
 'url_route': {'args': (), 'kwargs': {'slug': '0'}},
 'user': <User: u4711>, 'session': <LazyObject: ...>, 'cookies': {...}}
```

Nine header tuples, each a `bytes` object with a 33-byte header, plus the list,
plus a `cookies` dict that duplicates the cookie header, plus a `session` that
was consumed during the handshake. **Retained for the entire lifetime of the
connection because the scope dict is.**

### Reduction (a) — trim the scope

```python
    async def connect(self):
        self.slug = self.scope["url_route"]["kwargs"]["slug"]
        self.group = f"room.{self.slug}"

        # Resolve the lazy user BEFORE trimming: touching .pk forces the
        # session read. Do this in the wrong order and every connection
        # raises "Session object has no attribute".
        self.user = self.scope.get("user")
        if self.user is None or self.user.is_anonymous:
            await self.close(code=4401)
            return
        _ = self.user.pk

        # Keep the two things later modules genuinely need, as plain strings.
        self.client_ip = _client_ip(self.scope)      # Module 21: abuse scoring
        self.origin = _header(self.scope, b"origin") # Module 21: CSWSH audit

        # Then drop the rest. The scope dict is retained for the life of the
        # connection; nothing below is read again.
        for key in ("headers", "cookies", "session", "query_string", "raw_path"):
            self.scope.pop(key, None)
```

**Measured:**

| | Before | After |
|---|--------|-------|
| `scope` bytes/conn | 9,400 | **1,120** |
| Application bytes/conn | 46,200 | **38,120** (−17.5%) |
| p99 fan-out | 138 ms | 136 ms (no change) |
| Connections per 2.5 GB worker | 40,000 | 48,000 (+20%) |

**What it breaks, precisely:**

1. **Anything that reads a header after the handshake.** Module 21's re-auth
   flow, `X-Forwarded-For` extraction, and any future feature that wants the
   user agent. The mitigation is above: hoist what you need into a scalar
   attribute *before* popping, and treat `self.scope["headers"]` as unavailable
   from `connect()` onward. Write that in a comment or someone will re-add a
   header read in six months and it will fail only behind a proxy.
2. **`channels.auth.login()` / `logout()`** need `scope["session"]`. Pulse
   authenticates at handshake and never re-logs-in on the socket, so this is
   free — but it is a real capability you are giving up.
3. **Django Debug Toolbar and some third-party middleware** introspect the
   scope. Trim only outside `DEBUG`, or accept losing them.

> **Why this is worth 8 KB and the alternative isn't.** The obvious alternative
> is `__slots__` on `RoomConsumer` — Channels' generic consumers do not support
> it (they set attributes dynamically) and it would save ~400 bytes. The scope
> is 23× the payoff for 8 lines. **Measure before you optimise the thing that
> looks optimisable.**

### The kernel half — 16.8 KB idle, 95.9 KB at the knee

```bash
grep TCP: /proc/net/sockstat
sysctl net.ipv4.tcp_rmem net.ipv4.tcp_wmem
```
```
TCP: inuse 20044 orphan 0 tw 12 alloc 20051 mem 82013         # idle
TCP: inuse 20051 orphan 0 tw 19 alloc 20058 mem 468221        # at the knee
net.ipv4.tcp_rmem = 4096	131072	6291456
net.ipv4.tcp_wmem = 4096	16384	4194304
```

```
idle:      82,013 pages x 4,096 / 20,000  =  16.8 KB/conn
at knee:  468,221 pages x 4,096 / 20,000  =  95.9 KB/conn
```

**This is the number people miss.** Linux charges pages *as it uses them*, so an
idle socket is cheap and a socket with a backlog is not. During fan-out the
write queue grows toward `tcp_wmem`'s maximum of 4 MB, and at 20,000 connections
the kernel is holding **1.9 GB** that never appears in `VmRSS`, never appears in
`jvm_memory_used`'s Python equivalent, and is charged to your container's cgroup.

**That is why a container sized on `VmRSS` gets OOM-killed at exactly the moment
it gets busy**, and it is why Module 19 sizes limits from `memory.current`, not
from the process.

### Reduction (b) — size the buffers for chat, not for bulk transfer

```bash
sudo sysctl -w net.ipv4.tcp_rmem="4096 16384 1048576"
sudo sysctl -w net.ipv4.tcp_wmem="4096 16384 262144"
```

**Measured:**

| | Before | After |
|---|--------|-------|
| Kernel bytes/conn, idle | 16.8 KB | **14.2 KB** |
| Kernel bytes/conn, at the knee | **95.9 KB** | **22.2 KB** (−77%) |
| Total bytes/conn, idle | 63.0 KB | **52.3 KB** |
| Kernel memory at 20,000 conns, at the knee | 1.87 GB | **433 MB** |
| p99 fan-out | 138 ms | 141 ms (+2%, inside noise) |
| Slow-consumer time-to-detection | ~40 s | **~4 s** |

**What it breaks:** a genuinely large burst to one client now needs more round
trips, because the send window cannot open as far. For 200-byte chat frames that
is unmeasurable. **It would matter the day you put file transfer or image
thumbnails on the same socket** — and the honest note is that you would then
want two socket classes with different `SO_SNDBUF`, not one global sysctl.

The unexpected benefit is the last row: a smaller write queue means a
non-draining client hits the wall in four seconds instead of forty, so your
`4008` close fires while the room is still healthy. **Bounding a buffer improves
observability, not just memory.**

### Combined result

```
before:  46.2 KB app + 16.8 KB kernel = 63.0 KB/conn  ->  ~40,000 conns/worker
after :  38.1 KB app + 14.2 KB kernel = 52.3 KB/conn  ->  ~48,000 conns/worker
```

**+20% connections per worker for eight lines of Python and two sysctls, with no
latency cost.** And note what did *not* move: the knee. Memory was never the
binding constraint — Part I proved that — so this buys density, not throughput.
Say so when you report it, or someone will expect the knee to move.

---

## Task 3 — A regression gate a team will keep

`code/ci-gate.js`:

```js
import ws from 'k6/ws';
import { Trend, Rate, Counter } from 'k6/metrics';

const fanout = new Trend('fanout_latency_ms', true);
const errors = new Rate('ws_errors');
const gaps   = new Counter('sequence_gaps');

export const options = {
  scenarios: {
    gate: {
      executor: 'constant-arrival-rate',
      rate: 200, timeUnit: '1s', duration: '3m',
      preAllocatedVUs: 2000, maxVUs: 4000,
      gracefulStop: '15s',
    },
  },
  thresholds: {
    // Baseline: p50 11 ms, p99 138 ms. Gate at ~3x, with an explicit comment
    // saying why -- a threshold nobody can justify is a threshold that gets
    // bumped the first time it fails.
    'fanout_latency_ms':  ['p(50)<40', 'p(99)<400'],
    'ws_errors':          ['rate<0.005'],
    'sequence_gaps':      ['count<5'],
    // Guard against the generator lying. Without this the gate can pass
    // because k6 gave up, which is the worst possible green build.
    'dropped_iterations': ['count<360'],   // 1% of 200/s x 180 s
  },
};
```

```yaml
# .github/workflows/perf-gate.yml
- name: Performance gate
  run: |
    docker compose -p pulse-dev -f infra/compose.dev.yml up -d --wait
    python manage.py migrate --noinput
    uvicorn pulse.asgi:application --port 8000 --workers 1 --loop uvloop \
            --ws-per-message-deflate false --ws-max-queue 64 &
    timeout 60 bash -c 'until curl -sf localhost:8000/healthz; do sleep 1; done'
    sleep 20            # let the connection pool and the import graph settle
    k6 run --quiet 06-load-testing-harness/code/ci-gate.js \
      || k6 run --quiet 06-load-testing-harness/code/ci-gate.js
```

### Stability — ten consecutive runs, unchanged code

```
run  1: p50=12 p99=163  PASS
run  2: p50=11 p99=171  PASS
run  3: p50=12 p99=158  PASS
run  4: p50=14 p99=402  FAIL   <-- the runner's other job started a build
run  5: p50=11 p99=169  PASS
run  6: p50=12 p99=155  PASS
run  7: p50=11 p99=181  PASS
run  8: p50=13 p99=166  PASS
run  9: p50=12 p99=174  PASS
run 10: p50=11 p99=160  PASS
```

**False-positive rate: 1/10 = 10%.** Too high. A gate that fails one build in
ten is disabled within two sprints, and then you have no gate at all.

### Two ways to fix it, and what each costs

**Option A — loosen the threshold to `p(99)<600`.**
All ten runs pass. You have bought trust with sensitivity: a real 3× regression
from 138 ms to 420 ms now ships silently. For a system whose SLO is 200 ms
that is giving away the thing you were trying to protect.

**Option B — change the decision rule: retry once, fail on two consecutive
failures.** ✅ **Chosen.**

```
P(false positive) = 0.10 x 0.10 = 1%
```
Measured over 20 runs with the retry: **0 false positives**, with the tighter
400 ms threshold intact.

The cost is real and worth naming: a genuine regression that only manifests 50%
of the time now escapes 25% of the time, and each failing build takes twice as
long. For a *performance* gate — where the failure mode you fear is a systematic
slowdown, not a flaky one — that is the right trade. For a correctness test it
would not be, and "retry until green" on a correctness suite is how teams learn
to ignore red.

> **The rule generalises:** when a check is noisy, prefer changing the
> *decision rule* over changing the *threshold*. Loosening the threshold
> destroys information permanently; a retry rule spends time instead.

### Catching the injected regression

Revert Part E Step 3 — go back to encoding the envelope once per recipient:

```
     fanout_latency_ms..............: med=1180ms p(95)=6209ms p(99)=9240ms

     ✗ fanout_latency_ms  p(50)<40   FAILED
     ✗ fanout_latency_ms  p(99)<400  FAILED
     ✗ ws_errors          rate<0.005 FAILED (0.081)

ERRO[0195] thresholds on metrics have been crossed
exit status 99
```

The retry also failed, so it is not a flake. **Both** thresholds tripped, and
which ones trip tells you what kind of regression you have:

| Failing threshold | What it means |
|-------------------|---------------|
| **p50 only** | *Systemic* — everything got slower by a constant. A new per-message cost: an extra encode, a new middleware, a synchronous call on the hot path. |
| **p99 only** | *Tail* — most requests are fine and some stall. A lock, a GC-like pause, an unbounded queue, a slow neighbour. |
| **both** | The system is past its knee at the gate's offered load. The per-message cost went up enough to move `rho` across the hockey stick. |

Here: **both**, which is the correct diagnosis. Re-encoding per recipient added
~180 µs of CPU per delivery; at 200 members that is 36 ms of core time per
inbound message, and at 200 msg/s the offered load exceeded one core. The gate
did not just say "slower" — it said "you crossed the knee", which is the
sentence that gets a revert instead of a "we'll look at it next sprint".

Confirm the mechanism rather than assuming it:

```bash
sudo py-spy top --pid $PID --duration 10 --nonblocking | head -6
```
```
 41.50%  41.50%    4.15s     4.15s   dumps (orjson)
 12.00%  58.00%    1.20s     5.80s   send_json (channels/generic/websocket.py)
```

---

## Task 4 — The capacity plan

**Assumptions, stated so they can be attacked:**

1. Measured knee **150,000 outbound msg/s per worker process**; operate at 65%
   = **100,000**.
2. Measured **52.3 KB per connection** (post-Task-2), against a 2.5 GB budget
   per worker ⇒ **48,000 connections per worker**.
3. **250,000 concurrent users**, each sending **1 message per 5 minutes** ⇒
   **833 inbound msg/s in total, regardless of room size.**
4. `outbound = inbound × (room_size − 1)`.
5. A worker process is one core; a node is eight workers, post-Module-07.
6. **Protocol v1 opens one socket per room** (`pulse-protocol-v1.md` §Transport).
   Assumption 3 says nothing about how many rooms a user is *in*. Held at 1 for
   the first table; corrected below, where it changes the answer completely.

### Table A — one room per user

| Avg room size | Outbound msg/s | Workers for fan-out | Workers for connections | **Workers needed** | Bound by |
|---------------|----------------|--------------------|------------------------|-------------------|----------|
| 10 | 7,497 | 1 | 6 | **6** | connections |
| 50 | 40,817 | 1 | 6 | **6** | connections |
| 200 | 165,767 | 2 | 6 | **6** | connections |
| **841** | **700,000** | **7** | **6** | **7** | ← **crossover** |
| 1,000 | 832,167 | 9 | 6 | **9** | fan-out |
| 5,000 | 4,164,167 | **42** | 6 | **42** | fan-out |

**The crossover from connection-bound to fan-out-bound is at ~840 members.**
Below it you buy cores to hold sockets; above it you buy cores to copy bytes,
and cost grows linearly with room size while revenue does not.

### The correction that matters more than the table

Real users are in more than one room, and **v1 gives each room its own socket.**
At a conservative 8 rooms per user:

```
connections = 250,000 users x 8 rooms = 2,000,000 sockets
            = 2,000,000 / 48,000      = 42 worker processes
```

| Rooms/user | Sockets | Workers for connections | Workers for fan-out (200-member rooms) | Needed |
|-----------|---------|------------------------|---------------------------------------|--------|
| 1 | 250,000 | 6 | 2 | 6 |
| 4 | 1,000,000 | 21 | 2 | 21 |
| **8** | **2,000,000** | **42** | 2 | **42** |
| 20 | 5,000,000 | 105 | 2 | **105** |

**At 8 rooms per user, Pulse is connection-bound by 21× and the fan-out capacity
you spent this whole module measuring is irrelevant.** Five and a quarter nodes
of eight cores, to hold sockets that are 99.7% idle.

That is not a capacity finding, it is a **protocol** finding, and it is why
[`17-nextjs-realtime-client`](../../17-nextjs-realtime-client/) multiplexes many
rooms over one socket (and one socket across browser tabs with a
`SharedWorker`). Multiplexing collapses the 42 back to 6.

> **Notice what the harness did here.** It did not find a slow function. It
> found that a decision made in Module 05 for protocol-simplicity reasons —
> "one socket per room in v1" — is the dominant term in the hardware bill at
> 250,000 users. **You could not have found that by reading the code.**

### Where the architecture stops working, and the three fixes

**At ~5,000-member rooms.** 42 workers of pure fan-out for 250,000 users is
already hard to justify, and it gets worse than linear: once you have 42 worker
processes, **every worker holding a subscriber in a room must receive every
message for that room** (Module 07's subscription amplification), so Redis
delivers each message up to 42 times *on top of* the 4,999× room amplification.

Three things would have to change, in the order you would do them:

1. **Multiplex rooms onto one socket** (Module 17). Removes the 8× connection
   multiplier — the largest and cheapest win, and it is a client change.
2. **Fan-out on read above a threshold.** Above a few thousand members, stop
   pushing: clients poll a per-room cursor. Turns O(members) writes into
   O(active viewers) reads, and the active viewers of a 20,000-person channel is
   perhaps 200. This is what every large chat product does.
3. **Room affinity / sharded subscriptions** so a room lives on a known subset
   of workers rather than all of them (Module 14's shape, Module 18's
   `SSUBSCRIBE`). Kills the worker-count amplification.

A fourth, honest one: **move fan-out off Python entirely** — a dedicated edge
tier whose only job is holding sockets and copying bytes.
[`15-async-sync-and-raw-asgi`](../../15-async-sync-and-raw-asgi/) measures the
raw-ASGI version of this and asks the uncomfortable question directly.

### Comparison with the JVM twin

The JVM twin's [`06-load-testing-harness`](../../../spring-boot-chat-course/06-load-testing-harness/)
measured a **450,000 outbound msg/s** knee per node using all eight cores, and
~50,000 connections per node.

| | This course (per core) | JVM twin (per 8-core node) |
|---|----------------------|---------------------------|
| Fan-out knee | 150,000 | 450,000 |
| Safe operating point | 100,000 | 292,500 |
| Connections | 48,000 | 50,000 |
| Nodes for 250,000 users, 200-member rooms, 1 room each | 6 cores = **0.75 node** | **5 nodes** |
| Connection→fan-out crossover | **841 members** | **1,756 members** |

**The shape of the conclusion is identical; only the numbers move.** Both
architectures are connection-bound at small room sizes and fan-out-bound at
large ones; both break somewhere in the low thousands of members; both need
fan-out-on-read at the top end. The crossover arrives at roughly half the room
size here because one Python core does roughly a third of the fan-out work of
eight JVM cores while holding about the same number of sockets.

The one structural difference is the *unit*: the JVM twin plans in **nodes** and
gets all eight cores for free inside one heap. You plan in **worker processes**,
and eight of them on one box cannot see each other until Module 07 gives them a
shared channel layer. **The GIL turned a capacity-planning unit into an
architecture decision.** That is the sentence to bring to the review.

---

## Task 5 (stretch) — The generator on its own machine

Setup: server on the 8-core host, k6 on a second machine, 1 GbE, same switch.

| Metric | Single host (loopback) | Two hosts (1 GbE) | Change |
|--------|----------------------|-------------------|--------|
| Max connections | 20,000 | 20,000 | — |
| p50 fan-out | 11 ms | 12 ms | **+9%** |
| p95 | 52 ms | 58 ms | +12% |
| **p99** | **138 ms** | **108 ms** | **−22%** |
| p99.9 | 640 ms | 478 ms | −25% |
| **Knee** | **150,000** | **178,000** | **+19%** |
| Server CPU at the knee | 100% of 1 core | 100% of 1 core | — |
| Generator CPU at the knee | 61% (shared box) | 44% (own box) | — |
| Bandwidth at the knee | n/a (loopback) | 313 Mbit/s | 31% of the link |

### The two competing effects

**Effect 1 — freed CPU (helps, and less than you would guess).** On one host,
k6 was taking 61% of eight cores at the knee. Moving it off returns roughly five
cores to a server that **wants exactly one**. So the direct gain is small; the
real gain is second-order — the scheduler stops migrating the worker between
cores, softirq processing for k6's 20,000 sockets stops landing on the CPU
running the event loop, and the L2 cache stops being trashed by a foreign
process. That is worth **19% on the knee** and **22% at p99**.

**Effect 2 — real network cost (hurts, at the median).** Loopback has no MTU, no
NIC interrupts, no driver, and ~5 µs RTT. Gigabit ethernet adds ~140 µs RTT and
softirq CPU for packet processing. That is the **+9% at p50**.

**Effect 1 wins at the tail; Effect 2 wins at the median**, because the median is
dominated by transit time (which got worse) and the tail is dominated by
scheduling and queueing (which got much better).

### Compare this to the JVM twin, because the difference is the point

The JVM twin measured **+36% on the knee** from the same change. You measured
+19%. **The Python single-host penalty is smaller** — precisely because a
one-core server has less to lose to a greedy co-tenant. The JVM twin's server
genuinely wanted all eight cores and was being robbed of three; yours wanted one
and got it either way.

That cuts both ways as advice:

- **Your single-host numbers are less wrong than the JVM twin's**, so the
  numbers in this course are more trustworthy than they would be on the JVM.
- **But they are still 19% conservative**, which is enough to buy 19% more
  hardware than you need. Quote single-host numbers as a floor, never as a
  capacity plan.

### The confounder the two-host setup introduces — and it is a bad one

**Clock skew.** The entire latency measurement rests on

```
latency = receiver_clock_now  -  sender_clock_at_send
```

which is only valid while sender and receiver share a clock. With one k6 process
they do, trivially. The moment you scale the generator to **two** machines to get
past 30,000 connections, half your "latency" samples are
`clock_B_now − clock_A_then`, and NTP on a LAN is accurate to roughly **±1–10 ms**
— the same order as your p50 of 11 ms.

You would not see an error. You would see a p50 that drifts between runs, or a
small negative minimum:

```
     fanout_latency_ms..............: min=-4  med=9  p(95)=51  p(99)=140
```

**`min` below zero is the tell.** Add it to your check list; a negative minimum
latency means your clocks, not your server.

Three ways out, in increasing order of effort:

1. **Keep one clock domain.** One generator host, more source IPs
   (`ip addr add`) to get past the ephemeral-port ceiling. Simplest, and enough
   to reach ~200,000 connections.
2. **PTP (`ptp4l`/`phc2sys`)** between generator hosts — sub-microsecond on a
   LAN with hardware timestamping, and 100× better than NTP without it.
3. **Measure a round trip instead of a one-way trip.** Have the *sender* also be
   a subscriber and record `send → own message.new` — one clock by construction,
   and the protocol already delivers a sender its own message (Module 04 Part B)
   specifically so this works. You lose the ability to measure asymmetric paths,
   which for a fan-out system is a real loss.

> **There is no setup with no confounders; there are only confounders you have
> identified.** State the one you are most worried about next to every number
> you publish. For the single-host results in this course, that sentence is:
> *"the generator shared eight cores with the server, which makes the knee
> approximately 19% conservative."*
