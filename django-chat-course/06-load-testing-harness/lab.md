# Lab 06 — Find the Ceiling

**You'll:** instrument the server with `prometheus_client` and an event-loop-lag
probe; build the k6 harness and prove your *generator* isn't the bottleneck;
watch the Module 05 code collapse at 20,000 connections; **tune the fan-out path
from 5,900 to 151,000 outbound messages/second in five measured steps**; record
the baseline every later module is compared against; run the same workload
through Locust and watch coordinated omission lie to you by 34×; then break the
single worker **three different ways** — file descriptors, event-loop
saturation, and one client that refuses to read.

⏱️ ~110 min. Work in `django-chat-course/apps/pulse` and
`06-load-testing-harness/code/`.

```bash
cd django-chat-course/apps/pulse
source ../../.venv/bin/activate
set -a; source env.dev; set +a
docker compose -p pulse-dev -f ../../infra/compose.dev.yml up -d
pip install --quiet prometheus-client orjson locust websocket-client
k6 version && locust --version
```

Reference machine for every number below: **8-core / 16 GB, Ubuntu 24.04,
Python 3.12, Django 5.1, Channels 4.1, Uvicorn + uvloop, `--workers 1`.**

> **One worker. On purpose.** Module 04 proved the `InMemoryChannelLayer` does
> not span worker processes, so until Module 07 a node *is* a worker: one
> process, one core. Every number in this lab is a one-core number, and saying
> so is the sharpest possible statement of the Python scaling story.

> **Low-memory path:** under 12 GB, divide every connection target by four
> (5,000 instead of 20,000) and multiply `SEND_EVERY` by four. Every curve keeps
> its shape; only the absolute numbers move. Write the scale factor at the top
> of `results-06.md` and never quote a scaled number without it.

---

## Part A — Instrument the server

Copy the reference instrumentation into the app. Read it before you copy it —
the comments are the lesson:

```bash
cp ../../06-load-testing-harness/code/metrics.py chat/metrics.py
python chat/metrics.py
```

**Expected — the probe seeing a blocked loop, which is the whole point:**
```
idle loop lag      : 0.0004 s
after a 0.8 s block: 0.7986 s
```

✅ 0.4 ms when the loop is free, 799 ms when someone blocked it for 800 ms.
`chat_event_loop_lag_seconds` is not a proxy for load; it *is* the queueing
delay of the one callback queue your worker has.

Now wire it into the consumer. In `chat/consumers.py`, add the imports and four
call sites:

```python
import time

from chat.metrics import (CONNS, GROUP_SEND, MESSAGES_IN, MESSAGES_OUT,
                          WORKER, start_lag_probe)


class RoomConsumer(AsyncJsonWebsocketConsumer):

    def _group_size(self) -> int:
        """How many channels this fan-out will actually reach.

        On the InMemoryChannelLayer that's a dict lookup. Module 07 replaces
        the body with a Redis ZCARD on the group key; the call site does not
        change, which is the reason this is a method and not an expression.
        """
        groups = getattr(self.channel_layer, "groups", {})
        return len(groups.get(self.group, ()))

    async def connect(self):
        # ... unchanged auth + group_add + accept from Modules 04/05 ...
        start_lag_probe()                      # idempotent; first caller wins
        CONNS.labels(worker=WORKER).inc()

    async def disconnect(self, code):
        if hasattr(self, "group"):
            CONNS.labels(worker=WORKER).dec()
        # ... unchanged group_discard + presence from Module 04 ...

    async def _on_message_create(self, data):
        MESSAGES_IN.inc()
        result = await send_message(...)       # unchanged from Module 05
        await self.send_json(envelope("message.ack", ...))
        if result.duplicate:
            return

        recipients = self._group_size()
        t0 = time.perf_counter()
        await self.channel_layer.group_send(self.group, {...})
        GROUP_SEND.observe(time.perf_counter() - t0)
        MESSAGES_OUT.inc(recipients)
```

> ⚠️ **`GROUP_SEND` measures the enqueue half, not delivery.** `group_send`
> returns once the message is in the layer, not once 199 sockets have the
> bytes. Both numbers are useful; confusing them is how people report 2 ms
> latency on a system users find sluggish. The end-to-end number comes from the
> generator, because **only a receiver knows when it received.**

Expose it. In `chat/views.py`:

```python
from django.http import HttpResponse
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from chat import metrics


def metrics_view(request):
    # metrics.registry() returns the process-local registry, or a merged
    # multiprocess one when PROMETHEUS_MULTIPROC_DIR is set (Module 07).
    return HttpResponse(generate_latest(metrics.registry()),
                        content_type=CONTENT_TYPE_LATEST)
```
```python
# pulse/urls.py
    path("metrics", views.metrics_view),
```

```bash
uvicorn pulse.asgi:application --port 8000 --loop uvloop --workers 1 &
sleep 3
curl -s localhost:8000/metrics | grep -E '^chat_' | head
```

**Expected:**
```
chat_messages_inbound_total 0.0
chat_messages_outbound_total 0.0
chat_group_send_seconds_bucket{le="0.001"} 0.0
chat_connections_active{worker="pid-58112"} 0.0
chat_event_loop_lag_seconds{worker="pid-58112"} 0.0004372
```

✅ Note `chat_group_send_seconds_bucket` — **explicit buckets, not a
client-computed percentile.** The p99 of eight workers is not the mean of eight
p99s, and from Module 07 onward you will have eight workers. Buckets add;
percentiles do not.

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

Confirm they took:
```bash
ulimit -n; cat /proc/sys/net/ipv4/ip_local_port_range; python -c "
import resource; print(resource.getrlimit(resource.RLIMIT_NOFILE))"
```
**Expected:**
```
200000
10000	65535
(200000, 200000)
```

⚠️ `ulimit -n` applies to the **shell that launches the process**, not to
already-running ones. Restart uvicorn after raising it, or the server keeps the
old limit and you will "discover" a ceiling at 1,024 connections.

Start the server the way every measurement in this course expects:

```bash
kill %1 2>/dev/null
uvicorn pulse.asgi:application --port 8000 --workers 1 \
        --loop uvloop --http httptools --ws websockets \
        --ws-ping-interval 20 --ws-ping-timeout 20 \
        --log-level warning &
sleep 3
PID=$(pgrep -f 'uvicorn pulse.asgi' | head -1)
grep VmRSS /proc/$PID/status
```

**Expected — Django + DRF + Channels + prometheus_client, zero connections:**
```
VmRSS:	  104180 kB
```

Write that number down. Every per-connection memory figure in this lab is a
delta from it.

---

## Part C — The harness, and proving it isn't the bottleneck

The k6 script is [`code/pulse-load.js`](./code/pulse-load.js). Read it; two
lines carry the whole design.

**Line one — the timestamp inside the body:**

```js
body: `t=${Date.now()} ${PAD}`,
```

The v1 protocol's allowlist rejects any field on `message.create` other than
`client_id`, `body` and `reply_to` — deliberately, because a client sending a
field you do not honour is a client whose author believes it works. So there is
nowhere to put a sender timestamp *except* the body. The receiver parses it back
out and subtracts. Both ends are the same k6 process, so the clocks agree —
which is precisely why you cannot do this trivially across two machines.

**Line two — the send timer:**

```js
socket.setInterval(() => { socket.send(...); sent.add(1); }, SEND_EVERY);
```

An interval, not a request/response loop. The VU never waits for anything before
its next send. That is the open model, and Part G shows you what it buys.

### Prove the generator isn't the limit — do this first, every time

Two minutes, and it prevents a whole category of wrong conclusions.

```bash
# Connections only, no messages at all. If THIS plateaus, it is the rig.
k6 run --vus 30000 --duration 2m -e SEND_EVERY=999999999 \
       ../../06-load-testing-harness/code/pulse-load.js
```

In another terminal:
```bash
watch -n1 'ss -s | head -3; echo ---; ss -tan state established | wc -l; \
  echo "--- generator cpu ---"; ps -o %cpu= -p $(pgrep -x k6)'
```

**Expected — a healthy rig:**
```
Total: 30184
TCP:   30052 (estab 30011, closed 88, orphaned 0, timewait 71)
---
30011
--- generator cpu ---
44.8
```

**Expected — a broken rig, the false ceiling:**
```
TCP:   28233 (estab 28180, ...)
```
```
WARN[0074] Request Failed  error="dial tcp: connect: cannot assign requested address"
```

`cannot assign requested address` is **ephemeral-port exhaustion**, not a server
limit, and it stops at almost exactly your port-range size. Widen the range
(Part B) and re-run.

**Record in `results-06.md`:**
```
Generator ceiling (connections only): 30,011 @ 45% generator CPU — not limiting
```

> **This trap bites Python harder than the JVM twin.** There, one JVM used all
> eight cores and the generator competed for slack. Here your server is *one
> core by construction*, so a k6 process at 45% is eating three and a half cores
> the server cannot use anyway — but at 70%+ it starts stealing scheduler time
> from the one core that matters. Check `gen_cpu_pct` on every run;
> `code/collect.py` prints it.

---

## Part D — The first honest run, and the collapse

Start the collector, then the real workload:

```bash
../../06-load-testing-harness/code/collect.py /tmp/run-untuned.csv \
    --baseline-mb 101.7 &
k6 run -e ROOMS=100 -e SEND_EVERY=60000 \
       ../../06-load-testing-harness/code/pulse-load.js
kill %2
```

**Expected — and it is a disaster:**
```
     checks.........................:  61.20% 12240 out of 20000
     fanout_latency_ms..............: min=3 med=8420 p(95)=41209 p(99)=58900 p(99.9)=71204 max=79118
     msgs_received..................: 421884   716/s
     msgs_sent......................: 19984    33.9/s
     sequence_gaps..................: 214
     ws_errors......................: 12.10%

     ✗ fanout_latency_ms  p(50)<40   FAIL
     ✗ ws_errors          rate<0.01  FAIL
```

And in the collector's live output, the reason:

```
conns= 11840  lag=  4210.7 ms  out/s=    5880  amp=  199  cpu=100.0%  gen= 39.1%
conns= 11902  lag=  6104.2 ms  out/s=    5910  amp=  199  cpu=100.0%  gen= 39.4%
conns= 11844  lag=  8890.1 ms  out/s=    5902  amp=  199  cpu=100.0%  gen= 38.8%
```

Read those three columns together and the diagnosis is already complete:

- **`out/s` is pinned at ~5,900.** The workload *offers* 66,300 (333 inbound ×
  199 members). The worker delivers 5,900 and the rest queues.
- **`cpu` is 100.0% — of one core.** Not of the machine. There are seven idle
  cores you cannot reach (Module 04's wall).
- **`lag` is climbing without bound.** The loop is not just busy, it is falling
  further behind every second. That is `1/(1-rho)` with `rho >= 1`.
- **Connections are being dropped** (`checks 61.2%`) because the loop is too
  late to answer WebSocket pings.

✅ **Module 04 predicted this exactly**: 200 receivers at 10 msg/s cost 34% of a
core, which extrapolates to 100% at ~5,900 outbound msg/s. The prediction held.

Now find out *where* the core goes before you change anything:

```bash
pip install --quiet py-spy
sudo py-spy top --pid $PID --duration 20 --nonblocking
```

**Expected:**
```
Total Samples 2000
GIL: 99.00%, Active: 99.00%, Threads: 2

  %Own   %Total  OwnTime  TotalTime  Function (filename)
 38.00%  38.00%    7.61s     7.61s   deflate (zlib)
 19.50%  22.00%    3.90s     4.40s   dumps (json/encoder.py)
 14.50%  15.00%    2.90s     3.00s   iterencode (json/encoder.py)
  8.50%  61.00%    1.70s    12.20s   send_json (channels/generic/websocket.py)
  5.00%   5.00%    1.00s     1.00s   deepcopy (copy.py)
  4.50%   4.50%    0.90s     0.90s   write (asyncio/selector_events.py)
```

**53% of your one core is JSON encoding, and 38% is compressing 180-byte
frames.** Both are per-recipient work, done 199 times for one inbound message.
Neither is Channels' fault, Django's fault, or Python's fault — it is *your fan
out path* doing the same work 199 times.

---

## Part E — Tune the fan-out path

Five changes. Measure after each one, because three of them are worth far more
than you would guess and one is worth almost nothing.

The measurement procedure for each step: hold 20,000 connections and lower
`SEND_EVERY` until `loop_lag_ms` stays above 50 ms for 30 consecutive seconds.
The `out_rate` just below that point is the step's ceiling.

```bash
# code/step.sh — same ladder for every step
for every in 60000 30000 20000 10000 6000 4000 3000; do
  k6 run -q -e ROOMS=100 -e SEND_EVERY=$every --duration 90s \
         --summary-export=/tmp/step-$every.json \
         ../../06-load-testing-harness/code/pulse-load.js
  sleep 45              # let TIME_WAIT drain between runs
done
```

### Step 1 — turn off per-message compression

```bash
uvicorn pulse.asgi:application --port 8000 --workers 1 --loop uvloop \
        --ws websockets --ws-per-message-deflate false ... &
```

**Expected:** `5,900 → 21,400 outbound msg/s` (**3.6×**)

Uvicorn enables `permessage-deflate` by default. For 500 KB HTTP responses that
is free bandwidth; for a 180-byte chat frame you are paying a full zlib
compression cycle **per recipient** to save perhaps 60 bytes, and zlib keeps a
32 KB sliding window **per connection**. At 20,000 connections that window alone
is 640 MB.

> **The condition that would flip this:** mobile clients on metered data, where
> 60 bytes × 199 recipients × millions of messages is a real bill. The fix then
> is not per-frame deflate but a smaller envelope (Module 05 Part J) or
> MessagePack — compress the *format*, not each frame.

### Step 2 — `orjson` instead of the stdlib encoder

`chat/consumers.py`:

```python
import orjson


class RoomConsumer(AsyncJsonWebsocketConsumer):

    @classmethod
    async def encode_json(cls, content):
        # Module 05 measured 4.2x on the reference machine. This is the one
        # line that swap was designed to be.
        return orjson.dumps(content).decode()

    @classmethod
    async def decode_json(cls, text_data):
        return orjson.loads(text_data)
```

**Expected:** `21,400 → 33,800 outbound msg/s` (**1.58×**)

Less than the 4.2× the microbenchmark promised, because encoding is now only
part of the work. **This is normal and worth internalizing**: a 4.2× improvement
to a component that is 45% of your cost yields 1.6× overall. Amdahl, measured.

### Step 3 — encode once, fan out the same bytes

The big one. Right now `chat_message()` runs once per recipient and each run
encodes the *identical* envelope. Encode it once, in the sender's coroutine,
and put the finished string on the channel layer:

```python
    async def _on_message_create(self, data):
        MESSAGES_IN.inc()
        result = await send_message(...)
        await self.send_json(envelope("message.ack", ...))
        if result.duplicate:
            return

        # Encode ONCE. Every member of the room gets byte-identical bytes.
        payload = dumps(envelope(
            "message.new", self.group, result.ts,
            id=result.id, seq=result.seq, client_id=data["client_id"],
            sender=self.user.username, body=data["body"].strip(),
            reply_to=data.get("reply_to")))

        recipients = self._group_size()
        t0 = time.perf_counter()
        await self.channel_layer.group_send(
            self.group, {"type": "chat.message", "payload": payload})
        GROUP_SEND.observe(time.perf_counter() - t0)
        MESSAGES_OUT.inc(recipients)

    async def chat_message(self, event):
        # No dict construction, no encode. One socket write.
        await self.send(text_data=event["payload"])
```

**Expected:** `33,800 → 118,000 outbound msg/s` (**3.49×**)

> ⚠️ **What you just gave up, and it is not nothing.** Every recipient now
> receives byte-identical bytes, so you can never personalise a broadcast — no
> per-recipient `unread` count, no per-recipient `you_were_mentioned` flag, no
> per-viewer redaction. Pulse accepts that because those belong in separate
> per-user frames anyway (Module 10 builds them). If your product needs
> per-recipient content in the broadcast, this optimisation is unavailable and
> your fan-out ceiling is Step 2's, not Step 5's. **State the constraint out
> loud; do not let a future feature discover it during an incident.**

### Step 4 — stop paying for `send_json`'s ceremony

`AsyncJsonWebsocketConsumer.send_json` calls `encode_json`, builds a dict for
the ASGI message, and dispatches. `self.send(text_data=...)` skips the first
two. Step 3 already switched `chat_message` to `send`; do the same for the
frames on the sender's own path (`message.ack`, `pong`, `error`) by encoding
them with `dumps()` from `chat/protocol.py`.

**Expected:** `118,000 → 132,000 outbound msg/s` (**1.12×**)

Small, but free, and it removes the last stdlib-`json` call from the hot path.

### Step 5 — accept backlog and socket write buffers

```bash
uvicorn pulse.asgi:application ... --backlog 8192 --ws-max-queue 64 &
sudo sysctl -w net.ipv4.tcp_wmem="4096 32768 4194304"
```

**Expected:** `132,000 → 151,000 outbound msg/s` (**1.14×**)

Most of that is the write buffer: a 32 KB default send buffer means fewer
`EAGAIN`-and-reschedule cycles per frame, and each avoided cycle is an event-loop
callback you did not pay for.

`--ws-max-queue 64` is in that command line for a different reason and it is
worth being precise, because the name misleads: it bounds the **incoming**
frame queue per connection in `websockets`, so a client that floods you cannot
make your worker buffer its frames without limit. It does **not** bound the
outbound direction. Outbound backpressure in `websockets` comes from
`write_limit` and `drain()`, and the thing that actually protects your worker
from a non-reading client is the **channel layer's `capacity`** — which is Part
J's subject.

### The ladder, together

| Step | Change | Outbound msg/s at 100% of one core | Factor |
|------|--------|-----------------------------------|--------|
| 0 | Module 05 code as written | **5,900** | — |
| 1 | `--ws-per-message-deflate false` | 21,400 | 3.63× |
| 2 | `orjson` encode/decode | 33,800 | 1.58× |
| 3 | **encode once, fan out bytes** | **118,000** | **3.49×** |
| 4 | `send(text_data=)` everywhere | 132,000 | 1.12× |
| 5 | socket buffers, bounded ws queue | **151,000** | 1.14× |
| | **total** | | **25.6×** |

✅ **25.6× from five changes, none of which touched Django, Channels, or the
event loop.** All five removed *per-recipient work*. That is the shape of every
fan-out optimisation you will ever do: the inbound path is never the problem;
the multiplier is.

Re-run `py-spy` and confirm the profile has changed shape:

```bash
sudo py-spy top --pid $PID --duration 20 --nonblocking
```
**Expected:**
```
 21.00%  21.00%    4.20s     4.20s   write (asyncio/selector_events.py)
 14.00%  18.50%    2.80s     3.70s   send (websockets/legacy/protocol.py)
 11.50%  11.50%    2.30s     2.30s   deepcopy (copy.py)
  9.00%  62.00%    1.80s    12.40s   group_send (channels/layers.py)
  5.50%   5.50%    1.10s     1.10s   loads (orjson)
```

Now the top cost is `write()` — an actual socket syscall, which is irreducible
work — and `deepcopy` from the in-memory layer's per-recipient copy. **That
`deepcopy` is 11.5% of your core and it disappears in Module 07**, because the
Redis layer serialises once instead of copying N times. A rare case where adding
a network hop removes CPU.

---

## Part F — The baseline

This is the number Modules 07, 09, 13, 15, 16 and 22 all compare against. Take
it seriously: restart everything, run it clean, run it three times.

```bash
kill %1; sleep 5
uvicorn pulse.asgi:application --port 8000 --workers 1 --loop uvloop \
        --ws websockets --ws-per-message-deflate false --backlog 8192 \
        --ws-max-queue 64 --log-level warning &
sleep 3; PID=$(pgrep -f 'uvicorn pulse.asgi' | head -1)

../../06-load-testing-harness/code/collect.py /tmp/baseline.csv \
    --baseline-mb 101.7 --pid $PID &
k6 run -e ROOMS=100 -e SEND_EVERY=60000 \
       --summary-export=/tmp/baseline.json \
       ../../06-load-testing-harness/code/pulse-load.js
kill %2
```

**Expected:**

```
     checks.........................: 100.00% 20000 out of 20000
     acks_received..................: 19987
     error_frames...................: 0
     fanout_latency_ms..............: min=2 med=11 p(95)=52 p(99)=138 p(99.9)=640 max=2104
     msgs_received..................: 3978412  66307/s
     msgs_sent......................: 19984    333/s
     open_connections...............: 20000
     sequence_gaps..................: 0
     ws_errors......................: 0.00%
     ws_connecting..................: p(95)=291ms

     ✓ fanout_latency_ms  p(50)<40
     ✓ fanout_latency_ms  p(95)<200
     ✓ fanout_latency_ms  p(99)<400
     ✓ ws_errors          rate<0.01
     ✓ sequence_gaps      count<10
```

✅ **p50 11 ms · p95 52 ms · p99 138 ms · p99.9 640 ms at 20,000 connections and
66,307 outbound messages/second.** Every threshold green, zero gaps, zero
errors. **This is the pinned Module 06 baseline.**

State the amplification alongside it or the number means nothing:

```
20,000 connections / 100 rooms / 200 members each / 1 msg per user per 60 s

  inbound   20,000 / 60      =     333 msg/s    <- what a naive dashboard shows
  outbound  333 x 199        =  66,267 msg/s    <- the actual work
  amplification                    199x
```

The generator reported 66,307/s against a predicted 66,267/s — 0.06% apart. When
your measured amplification matches your arithmetic, your rig is telling the
truth.

### Per-connection memory, from two directions

```bash
grep VmRSS /proc/$PID/status
grep TCP: /proc/net/sockstat
curl -s localhost:8000/metrics | grep chat_connections_active
```

**Expected, at steady state:**
```
VmRSS:	 1028412 kB
TCP: inuse 20044 orphan 0 tw 12 alloc 20051 mem 82013
chat_connections_active{worker="pid-58112"} 20000.0
```

```
application:  (1,028,412 - 104,180) kB / 20,000  =  46.2 KB per connection
kernel:       82,013 pages x 4,096 B / 20,000    =  16.8 KB per connection
                                                    ------
total                                               63.0 KB per connection
```

✅ **46.2 KB of application memory against the pinned ≈45 KB, plus 16.8 KB of
kernel socket buffers your Python process never sees.**

Two things follow, and both matter later:

1. **`docker stats` and `VmRSS` disagree with each other, and both are right.**
   The kernel's 16.8 KB per connection is charged to the container's cgroup but
   is invisible to Python. A container sized on `VmRSS` will get OOM-killed at
   20,000 connections. Module 19's `resources.limits` uses the 63 KB figure.
2. **The pinned ≈40,000 connections per worker** costs `40,000 × 63 KB ≈ 2.5 GB`
   — comfortable for one of eight workers on a 16 GB box. Memory is *not* what
   binds you. The next section shows what does.

Compare against Module 01: 20,000 OS threads died at ~32,000 threads and roughly
8 MB of virtual address space each. Here 20,000 connections live on **one
thread**:

```bash
ls /proc/$PID/task | wc -l
```
**Expected:** `14` — the loop, plus Django's `database_sync_to_async` threadpool.

---

## Part G — Locust, and coordinated omission with your own eyes

Same server, same workload, the Python-native generator:
[`code/locustfile.py`](./code/locustfile.py).

```bash
locust -f ../../06-load-testing-harness/code/locustfile.py ChatUser \
       --processes 8 --headless -u 20000 -r 500 -t 6m \
       --csv=/tmp/pulse-locust --html=/tmp/pulse-locust.html
```

**Expected:**
```
Type  Name       # reqs   # fails |    Avg     Min     Max    Med |   req/s
------|----------|--------|--------|-------|-------|-------|------|--------
WS    fanout    3,978,412      0  |     19       2   1,940     11 | 66,307
WS    ws_send      19,984      0  |      0       0      12      0 |    333

--- fan-out latency, raw samples ------------------------------
  samples : 3,978,412
  mean    :     19.4 ms
  p50     :     11.0 ms
  p95     :     52.0 ms
  p99     :    138.0 ms
  p99.9   :    640.0 ms
  max     :   1940.0 ms
---------------------------------------------------------------
```

✅ **Locust agrees with k6 to within a millisecond at every percentile** —
because `ChatUser` was built to: paced sends, a dedicated receiver greenlet, and
latency taken from the sender's clock in the body. A well-built Locust user is
not a worse instrument; it is the same instrument in Python.

Now break it on purpose. Add a debug stall to the server — this is Module 04's
cardinal sin, weaponised:

```python
# chat/views.py
import time as _time

STALL_UNTIL = 0.0


def debug_stall(request):
    """DEBUG-only. Block the event loop for N ms, once, on the next fan-out."""
    global STALL_UNTIL
    STALL_UNTIL = _time.time() + float(request.GET.get("ms", 5000)) / 1000
    return HttpResponse("ok")
```
```python
# chat/consumers.py, at the top of _on_message_create
        from chat import views
        remaining = views.STALL_UNTIL - time.time()
        if remaining > 0:
            time.sleep(remaining)              # blocks the loop. Every socket.
            views.STALL_UNTIL = 0.0
```

Run both Locust user classes against the same server, same offered load
(500 users, 1 msg/s each), with a 5-second stall injected at t=90 s:

```bash
for cls in ChatUser ClosedLoopUser; do
  SEND_EVERY=1000 locust -f ../../06-load-testing-harness/code/locustfile.py $cls \
      --processes 4 --headless -u 500 -r 100 -t 3m --csv=/tmp/co-$cls &
  sleep 90 && curl -s "localhost:8000/debug/stall?ms=5000"
  wait
done
```

**Expected:**

| | `ClosedLoopUser` | `ChatUser` (open) |
|---|-----------------|-------------------|
| Messages the model intended | 90,000 | 90,000 |
| Messages actually sent | **86,412** | **89,940** |
| p50 | 9 ms | 10 ms |
| p95 | 34 ms | 47 ms |
| **p99** | **138 ms** | **4,690 ms** |
| p99.9 | 902 ms | 4,981 ms |
| max | 5,020 ms | 5,032 ms |

✅ **34× disagreement at p99, on the same server, during the same outage.**

The arithmetic that explains it exactly:

```
During the 5-second stall:

closed loop:  all 500 users are blocked in recv(). Between them they had
              500 requests in flight. 500 / 86,412 = 0.58% of samples
              -> lands at p99.4 -> p99 barely moves.

open loop:    the send task never waited, so 500 users x 5 s = 2,500 messages
              were sent INTO the stall. 2,500 / 89,940 = 2.78% of samples
              -> dominates everything above p97.2 -> p99 = 4,690 ms.
```

**The closed-loop generator responded to overload by reducing the load.** That
is the definition of coordinated omission: the samples that would have been
slowest were never taken, because the generator was too polite to take them.

**Real users are an open loop.** They keep pressing send whether or not you are
having a good day.

> **What Locust still cannot do, honestly stated.** `constant_throughput` paces
> a user's *next* iteration; it does not start an iteration while the previous
> one is still running. k6's `constant-arrival-rate` executor does, and reports
> `dropped_iterations` when it cannot keep up. So past the knee — where
> iterations overrun their period — even a well-built Locust user degrades
> toward closed-loop. **Ceilings come from k6. Behaviour, protocol realism and
> anything you want to write in Python come from Locust.** Say which you used
> whenever you quote a number.

---

## Part H — Break #1: file descriptors

Start with the limit deliberately low, so you see failure mode #1 in isolation:

```bash
kill %1
bash -c 'ulimit -n 4096; exec uvicorn pulse.asgi:application --port 8000 \
        --workers 1 --loop uvloop --log-level info' &
sleep 3
k6 run -e SEND_EVERY=999999999 --vus 6000 --duration 2m \
       ../../06-load-testing-harness/code/pulse-load.js
```

**Expected — in the server log, just under 4,096:**
```
ERROR:    Exception in callback _SelectorSocketTransport._accept_connection
OSError: [Errno 24] Too many open files
WARNING:  Could not accept connection
```

And in k6:
```
     checks.........................: 67.98% 4079 out of 6000
     ws_errors......................: 32.02%
```

It stopped at **4,079** — your FD limit minus the ~17 the process already held
(stdin/stdout/stderr, the Postgres pool, the epoll fd, the listening socket).
**One connection is one file descriptor**, exactly and always.

```bash
ls /proc/$PID/fd | wc -l
```
**Expected:** `4096`

Raise it and move on:
```bash
kill %1; ulimit -n 200000
uvicorn pulse.asgi:application --port 8000 --workers 1 --loop uvloop \
        --ws-per-message-deflate false --ws-max-queue 64 --log-level warning &
```

**Record:** `FD ceiling: 4,079 with ulimit -n 4096 (confirms 1 FD per connection)`

---

## Part I — Break #2: find the knee

Not the maximum. The **knee** — the offered load past which p99 stops being a
line and becomes a hockey stick.

Raise the *message rate*, not the connection count. Connections are cheap
(63 KB); amplification is not.

```bash
for every in 60000 40000 30000 26000 20000; do
  echo "=== SEND_EVERY=$every ==="
  ../../06-load-testing-harness/code/collect.py /tmp/knee-$every.csv --pid $PID &
  k6 run -q -e ROOMS=100 -e SEND_EVERY=$every --duration 4m \
         --summary-export=/tmp/knee-$every.json \
         ../../06-load-testing-harness/code/pulse-load.js
  kill %2; sleep 60
done

for f in /tmp/knee-*.json; do
  jq -r "\"$f  p50=\(.metrics.fanout_latency_ms.med)  \
p99=\(.metrics.fanout_latency_ms[\"p(99)\"])\"" "$f"
done
```

**Expected — the knee appears:**

| `SEND_EVERY` | inbound msg/s | outbound msg/s | p50 | p99 | loop lag | worker CPU |
|--------------|---------------|----------------|-----|-----|----------|------------|
| 60000 | 333 | 66,300 | 11 ms | 138 ms | 1.2 ms | 44% |
| 40000 | 500 | 99,500 | 13 ms | 211 ms | 4.1 ms | 66% |
| 30000 | 667 | 132,700 | 18 ms | 342 ms | 18 ms | 88% |
| **26000** | **769** | **153,000** | **41 ms** | **1,180 ms** | **142 ms** | **99%** |
| 20000 | 1,000 | 199,000 | 380 ms | **4,910 ms** | 1,404 ms | 100% |

```
p99 │                                        ╱
 ms │                                      ╱
    │                                   ╱   <- 26000
    │                              ╱
    │  ─────────────────────╱
    └───────────────────────┬───────────────── offered outbound msg/s
                   150,000 knee
       operate at 100,000 ←┤
```

✅ **The knee is ≈150,000 outbound messages/second.** Safe operating point at
65% of it: **≈100,000 outbound msg/s**, which is exactly the `SEND_EVERY=40000`
row — p99 211 ms, loop lag 4 ms, 66% of one core, and 34% of headroom left to
absorb a burst or a neighbour's failure.

### Read the leading indicator

```bash
head -1 /tmp/knee-30000.csv; sed -n '95,99p' /tmp/knee-30000.csv
```
**Expected:**
```
ts,conns,loop_lag_ms,in_rate,out_rate,amp,gs_p99_ms,rss_mb,kb_per_conn,cpu_pct,gen_cpu_pct
1735689812,20000,16.40,666.9,132698.1,199.0,3.10,1004.2,46.2,87.9,51.2
1735689813,20000,18.10,667.2,132745.0,199.0,3.40,1004.3,46.2,88.4,51.0
1735689814,20000,21.90,666.4,132610.4,199.0,4.20,1004.6,46.2,89.1,50.8
```

**`loop_lag_ms` moved from 4 ms to 18 ms while p99 was still an acceptable
342 ms.** The lag gauge saw the knee coming while the latency SLO was still
green — which is exactly what a leading indicator is for, and why Module 20
pages on loop lag and not on p99.

Note also `gs_p99_ms` (the *enqueue* half) is **3.4 ms** while end-to-end p99 is
**342 ms**. A dashboard built on the server-side timer alone would say this
system is healthy at 100× the truth. **That is the trap the README's "one rule"
exists to prevent.**

### Prove which resource is actually binding

Three interventions, one variable each, all at `SEND_EVERY=26000`:

```bash
# a. more memory                (does 46 KB/conn matter?)
# b. smaller payload            (is it serialization?)
# c. rooms 200 -> 20 members    (is it amplification?)
k6 run -e SEND_EVERY=26000 -e BODY_PAD=2   --duration 3m ...
k6 run -e SEND_EVERY=26000 -e ROOMS=1000   --duration 3m ...   # 20 members each
```

**Expected:**

| Intervention | Hypothesis | p99 after | Verdict |
|--------------|-----------|-----------|---------|
| Payload 42 B → 4 B | serialization cost | 1,090 ms | ❌ 8% — real, minor |
| RSS headroom doubled (8 GB free) | memory pressure | 1,175 ms | ❌ no effect |
| `CHANNEL_CAPACITY` 100 → 5,000 | mailbox depth | 1,204 ms | ❌ slightly worse |
| **Rooms 100 → 1,000 (200 → 20 members)** | **amplification** | **31 ms** | ✅ **this is it** |

**Same connections, same inbound rate, same payload, same everything — only the
multiplier changed, from 199× to 19×, and p99 improved 38×.**

The conclusion is architectural, not a tuning knob: **you cannot configure your
way out of 150,000 outbound messages per second on one Python core.** You need
either fewer outbound messages (smaller rooms, aggregation, fan-out on read) or
more processes — and more processes needs a channel layer that crosses
processes, which is Module 07.

---

## Part J — Break #3: the slow consumer

One phone on a bad train connection. Module 04 showed `ChannelFull` firing at
100 queued events; that bound is the only thing standing between you and the
worker's heap, so take it away and find out what it was worth.

Module 04 made the bound configurable for exactly this moment:

```python
CHANNEL_LAYERS = {"default": {
    "BACKEND": "channels.layers.InMemoryChannelLayer",
    "CONFIG": {"capacity": env("CHANNEL_CAPACITY", "100", cast=int), "expiry": 60}}}
```

```bash
kill %1
CHANNEL_CAPACITY=1000000 uvicorn pulse.asgi:application --port 8000 \
        --workers 1 --loop uvloop --ws-per-message-deflate false \
        --log-level warning &
sleep 3; PID=$(pgrep -f 'uvicorn pulse.asgi' | head -1)

python ../../04-channels-chat-single-node/code/wsprobe.py deadbeat \
       --room 0 --user slowpoke &
sleep 2
k6 run -e ROOMS=1 -e SEND_EVERY=300 -e BODY_PAD=2000 --vus 200 --duration 5m \
       ../../06-load-testing-harness/code/pulse-load.js &
watch -n5 'grep VmRSS /proc/'$PID'/status'
```

**Expected — 667 inbound/s into one 200-member room, 2 KB bodies:**
```
VmRSS:	  148204 kB       t=0
VmRSS:	  278912 kB       t=1m
VmRSS:	  412044 kB       t=2m
VmRSS:	  540788 kB       t=3m
VmRSS:	  668932 kB       t=5m
```

✅ **One client that never reads costs 1.7 MB/second, forever.** Do the
extrapolation, because it is the point:

```
1.7 MB/s               ->  16 GB in 2.6 hours from ONE bad connection
10 such clients        ->  16 GB in 16 minutes
```

**It does not kill you during your test. It kills you at 04:00**, which is
strictly worse: nothing correlates, nothing in the application log, and the
graph is a straight line that started when a user boarded a train.

The mechanism, precisely:

1. Your consumer `await self.send(text_data=event["payload"])`.
2. `websockets` writes to the transport and `drain()`s. Because the client is
   not reading, the socket's send window closes, the transport buffer passes
   `write_limit`, and **the `await` does not return.**
3. That consumer's task is now parked. It stops draining its channel mailbox.
4. Every `group_send` into the room keeps appending to that mailbox, and with
   `capacity` effectively removed, **nothing stops it.** Each queued event holds
   a copy of the 2 KB payload.

Confirm the diagnosis rather than believing it:

```bash
curl -s localhost:8000/api/layer-debug/ | python -c "
import sys, json
from channels.layers import get_channel_layer
"   # or, in a DEBUG shell inside the worker:
python - <<'EOF'
from channels.layers import get_channel_layer
layer = get_channel_layer()
for name, q in sorted(layer.channels.items(), key=lambda kv: -kv[1].qsize())[:3]:
    print(f"{q.qsize():>8}  {name}")
EOF
```
**Expected — one channel holding everything:**
```
  198431  specific.a3f1c9e2!Lw9xRt
       0  specific.a3f1c9e2!QK7pZm
       0  specific.a3f1c9e2!Bn4vHy
```

Now restore the bound and re-run:

```bash
kill %1
CHANNEL_CAPACITY=100 uvicorn pulse.asgi:application ... &
```
**Expected:**
```
VmRSS stays flat at ~152 MB
```
```
ERROR    Exception inside application: specific.a3f1c9e2!Lw9xRt
channels.exceptions.ChannelFull: specific.a3f1c9e2!Lw9xRt
```

The heap is safe — and Module 04 already showed you the cost: on the in-memory
layer that exception surfaces out of the **sender's** `group_send`, so one stuck
consumer makes a send fail for the whole room. **A bound alone is not a
solution; it just chooses a different victim.**

Handle it deliberately. The protocol reserves a close code for exactly this
(`4008`, "slow consumer"; `pulse-protocol-v1.md` §4):

```python
# chat/metrics.py
OVERFLOW = Counter("chat_slow_consumer_closed_total",
                   "Connections closed for not draining", ["worker"])
```
```python
# chat/consumers.py
from channels.exceptions import ChannelFull

    async def _on_message_create(self, data):
        ...
        try:
            await self.channel_layer.group_send(self.group, {...})
        except ChannelFull:
            # Do NOT fail the sender. Find the channel that is stuck and drop
            # it, then let the room carry on. Losing one bad connection beats
            # degrading the room to the speed of its slowest member.
            OVERFLOW.labels(worker=WORKER).inc()
            await self._evict_stuck_channels()
```
```python
    async def _evict_stuck_channels(self):
        layer = self.channel_layer
        for name, q in list(getattr(layer, "channels", {}).items()):
            if q.qsize() >= layer.capacity * 0.9:
                logger.warning("evicting slow consumer %s (%d queued)",
                               name, q.qsize())
                await layer.send(name, {"type": "chat.overflow"})  # best effort
                await layer.group_discard(self.group, name)
```
```python
    async def chat_overflow(self, event):
        await self.close(code=4008)
```

**Expected on re-run with the eviction in place:**
```
WARNING  evicting slow consumer specific.a3f1c9e2!Lw9xRt (90 queued)
```
```
$ python ../../04-channels-chat-single-node/code/wsprobe.py deadbeat ...
closed by server: 4008
```
```
     fanout_latency_ms..............: med=12 p(95)=54 p(99)=141      # unaffected
     ws_errors......................: 0.00%
```

✅ **The deadbeat is gone, the other 200 users never noticed, the heap is flat,
and a counter says it happened.** That close is the safety valve reporting
success, not a bug to suppress.

> `chat.overflow` is on `pulse-protocol-v1.md`'s reserved internal-event list
> (§5) precisely so this path exists without inventing a wire type. The protocol
> anticipated this failure two modules ago.

**Record:** `Slow consumer, capacity 1,000,000: +1.7 MB/s, OOM projected in
2.6 h. capacity 100: flat, ChannelFull aborts the whole group_send.
capacity 100 + eviction: flat, one client closed 4008, room unaffected.`

---

## Part K — Three runs, or it is an anecdote

```bash
for i in 1 2 3; do
  echo "=== run $i ==="
  ../../06-load-testing-harness/code/collect.py /tmp/run-$i.csv --pid $PID &
  k6 run -q --summary-export=/tmp/summary-$i.json \
         -e ROOMS=100 -e SEND_EVERY=60000 \
         ../../06-load-testing-harness/code/pulse-load.js
  kill %2
  sleep 60                                   # let TIME_WAIT drain
done

jq -r '.metrics.fanout_latency_ms | "p50=\(.med) p99=\(."p(99)")"' /tmp/summary-*.json
```

**Expected:**
```
p50=11 p99=138
p50=11 p99=144
p50=12 p99=131
```

A ~5% spread at p99. **If your three runs differ by more than ~15%, something
uncontrolled is happening** — a background process, thermal throttling, or a
generator closer to its own limit than you thought. Find it before you trust any
later comparison, because Module 07 is about to claim a 4 ms difference and 4 ms
inside 15% noise is not a measurement.

---

## What you measured

Record in `apps/pulse/results-06.md`:

```markdown
## Module 06 — single-worker ceiling
Reference: 8-core/16GB, Ubuntu 24.04, Python 3.12, Django 5.1, Channels 4.1,
Uvicorn+uvloop, --workers 1, InMemoryChannelLayer. Scale factor: 1x.

Workload: 20,000 conns / 100 rooms / 200 members / 1 msg per user per 60 s
          inbound 333/s, outbound 66,307/s, amplification 199x
Generator: same host, k6, 45% CPU (not limiting), ports 10000-65535

- BASELINE  p50 11 ms | p95 52 ms | p99 138 ms | p99.9 640 ms
- KNEE                          ~150,000 outbound msg/s
- Safe operating point (65%)    ~100,000 outbound msg/s
- Per connection                46.2 KB app + 16.8 KB kernel = 63.0 KB
- Threads for 20,000 conns      14
- Tuning ladder                 5,900 -> 151,000 out msg/s (25.6x, 5 steps)
- FD ceiling                    4,079 at ulimit -n 4096 (1 FD per connection)
- Binding resource              fan-out amplification (rooms 200->20: p99 /38)
- Slow consumer, capacity 1e6   +1.7 MB/s, OOM projected in 2.6 h
- Slow consumer, capacity 100   flat, but ChannelFull aborts the whole group_send
- Slow consumer, + eviction     flat, one client closed 4008, room unaffected
- Coordinated omission          closed-loop p99 138 ms vs open-loop 4,690 ms (34x)
- Run-to-run spread (p99)       138 / 144 / 131 ms  (5%)
```

| Measurement | Reference | Yours |
|-------------|-----------|-------|
| Generator ceiling, connections only | 30,011 @ 45% CPU | |
| Untuned outbound ceiling | 5,900 msg/s | |
| Tuned outbound ceiling | 151,000 msg/s | |
| Baseline p50 / p95 / p99 / p99.9 | 11 / 52 / 138 / 640 ms | |
| Application bytes per connection | 46.2 KB | |
| Kernel bytes per connection | 16.8 KB | |
| Knee | ~150,000 out msg/s | |
| Safe operating point | ~100,000 out msg/s | |
| Loop lag at the knee | 142 ms | |
| `group_send` p99 vs end-to-end p99 at 132k | 3.4 ms vs 342 ms | |
| Closed vs open loop p99 under a 5 s stall | 138 ms vs 4,690 ms | |

---

## What you built

```
apps/pulse/chat/
├── metrics.py       ← 6 metrics, histogram buckets, the event-loop lag probe
├── consumers.py     ← encode-once fan-out, 4008 on overflow, instrumented
└── views.py         ← /metrics, and a DEBUG-only stall injector
06-load-testing-harness/code/
├── pulse-load.js    ← k6, open model, cross-connection latency, gap detection
├── locustfile.py    ← ChatUser (honest) + ClosedLoopUser (the trap)
├── metrics.py       ← the reference copy of chat/metrics.py
└── collect.py       ← 1 Hz CSV of the columns that predict failure
```

And you established the facts Phase 2 exists to move:

- **A baseline with a stated workload and a stated amplification.** p50 11 ms at
  66,307 outbound msg/s, 199×. Without the amplification, the latency is a
  number without units.
- **A knee at ≈150,000 outbound msg/s on one core**, versus the JVM twin's
  ≈450,000 across eight. Not an embarrassment — the measured price of the GIL,
  and the reason Redis arrives sooner here.
- **25.6× of tuning that never touched the framework**, all of it removing
  per-recipient work, with one optimisation (encode-once) whose cost is a
  product constraint you must state out loud.
- **Three deliberate failures**, each understood: FD exhaustion at exactly
  `ulimit - 17`, event-loop saturation as the real ceiling, and one non-reading
  client leaking 1.7 MB/s into a worker's heap until you bound the mailbox
  AND choose a victim.
- **A 34× measurement of coordinated omission**, on your own server, using two
  generators you wrote.

You now have a number. Everything in Phase 2 has to beat it — or explain why it
doesn't.

Now do [`challenge.md`](./challenge.md).

Then: [Module 07 — Scaling Out with the Redis Channel Layer](../07-scale-out-redis-channel-layer/),
which swaps one settings dict, gets you your other seven cores, measures what
the Redis hop costs (**+4 ms p50 for 1.9× the knee**), and then pauses Redis
under load and counts what Pub/Sub loses.
