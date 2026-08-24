# Solutions — Module 22 (Capstone)

This is the reference capstone. It contains worked answers to the six challenge
tasks and points at the two required documents,
[`ARCHITECTURE_REVIEW.md`](./ARCHITECTURE_REVIEW.md) and
[`PRODUCTION_READINESS.md`](./PRODUCTION_READINESS.md).

**The point of the reference is not to be copied.** It is to show what
"defensible" looks like — including the three decisions it concedes, the
production gap it created, and the improvement it rejected for being an
improvement to the wrong thing.

Reference machine throughout: **8-core / 16 GB, Ubuntu 24.04, Python 3.12,
Uvicorn + uvloop, Django 5.1 / Channels 4.1, Redis 7.2, Postgres 16.** Where a
number came from an earlier module, the module is named; where it came from the
capstone run, it says so.

---

## Task 1 — Your knee, and a 1,000,000-connection plan

### Finding the knee

```bash
for target in 100000 120000 150000 172000 200000; do
  k6 run -e TARGET=$target code/acceptance.js | tee /tmp/knee-$target.txt
done
```

**Expected — 4 pods x 4 workers, 4 channel-layer shards, `capacity: 6000`:**

| Connections | burst out msg/s | % of the 956,000 ceiling | run p99 | burst p99 | % delivered < 500 ms | Verdict |
|---|---|---|---|---|---|---|
| 100,000 | 530,400 | 55% | 296 ms | 438 ms | 99.97% | ✅ all green |
| 120,000 | 636,500 | 67% | 318 ms | 549 ms | 99.96% | ✅ all green |
| 150,000 | 795,600 | 83% | 402 ms | 1,240 ms | 99.91% | ⚠️ SLO 2 at the line |
| **172,000** | **912,300** | **95%** | **1,110 ms** | **3,140 ms** | **99.81%** | ❌ **SLO 2 breach** |
| 200,000 | 1,060,800 | 111% | 6,240 ms | 14,900 ms | 96.4% | ❌ collapse |

✅ **The knee is 172,000 connections, and SLO 2 (delivery latency) breaks first** —
during the burst window, not the steady one.

Part A's arithmetic predicted 180,000 (`956,000 ÷ 5.304 outbound msg/s per connection`).
**Measured 172,000, so the model was 4.5% optimistic** — the expected direction,
because the model charges Redis nothing for the `XADD`s, the presence sweeps and the
ticket traffic that share the same shards.

At 172,000, SLO 1 goes with it: mailbox depth pins at 6,000 and
`chat_layer_over_capacity_total` climbs to 1,204, dropping `delivery_success` to
99.987%.

### Which resource was binding — check it, don't assume it

```bash
./code/binding-resource.sh 172000
```
**Expected:**
```
Redis, worst channel-layer shard    CPU  96%    <-- BINDING
uvicorn worker, worst pod           CPU  79%
memory per worker   10,750 conns x 45 KB = 484 MB of the ~1.8 GB ceiling   (27%)
event-loop lag p99                       11 ms
sync_to_async threadpool                 22/32 threads
Postgres primary                    CPU  31%
PgBouncer client waits                   0
NIC, worst shard                    31 MB/s of ~87 MB/s usable
```

✅ **Redis's single thread, at 96%, with 73% of the per-worker memory ceiling
unused.** [Module 07](../../07-scale-out-redis-channel-layer/) predicted this
precisely: the CPU wall arrives about 15× earlier than the bandwidth wall, and
buying a bigger Redis box does nothing because Redis executes commands on one
thread regardless of core count.

> **Contrast with the JVM twin.** Its capstone knee is **memory**: 46,000
> connections per node at 7.4 Gi of an 8 Gi heap. Ours is **one Redis thread being
> told about each message sixteen times**, with a quarter of our memory used. Same
> architecture, same target, entirely different binding resource — because the JVM
> twin's unit of subscription is an *instance* and ours is a *worker process*.
> **Every conclusion about "just add a node" inverts across that line.**

### The safe design point, stated so someone can check it

```
Module 06's rule: operate at <= 65% of the knee.
0.65 x 956,000 = 621,400 out msg/s burst
621,400 / 5.304 out per connection  = 117,100 connections
```

✅ **This topology is sized for ~117,000 connections, not 172,000.** We run at
100,000, which is **17% connection headroom** — a number the review's decision #7
states, and the trigger for buying a fifth shard.

### The 1,000,000-connection plan

```
1,000,000 connections
  4,800 rooms x 200   = 960,000   1 msg/user/180 s
     10 rooms x 4,000 =  40,000   announcements
inbound  steady  5,333 msg/s
outbound steady  1,061,400 msg/s
burst 5x         5,307,000 msg/s      -> required ceiling at 65% = 8,164,600
```

**Workers.** At a conservative 25,000 connections/worker (62% of the ~40,000
memory ceiling, leaving room for the 6,000-entry mailbox and the resume batches),
1,000,000 connections is **40 worker processes = 10 pods**.

**And that is where it falls apart:**

```
W = 40  ->  per group_send = 55 + 46 x 40 = 1,895 µs
            97% of Redis's work is now the per-worker term
            one shard = 950,000 / 1,895 x 199 = 99,699 out msg/s
            shards needed = 8,164,600 / 99,699 = 82
```

❌ **Eighty-two channel-layer Redis primaries** — 164 nodes with replicas, 246
processes with Sentinels — to fan out for ten application pods. That is not an
architecture; it is a symptom, and the symptom's name is on the second line above:
**you are paying Redis to tell forty processes about a message, once each.**

**Breaking point 1 — the per-worker subscription term.** It is super-linear in
disguise: more connections need more workers, more workers make each `group_send`
more expensive, and the shard count you need grows faster than your traffic. The
JVM twin does not have this, because it counts instances.

Two escapes, both already named in the course:

| Approach | `W` per room | Ceiling per shard | Shards for 1M | Cost |
|---|---|---|---|---|
| Nothing (today's design) | 40 | 99,699 | **82** | — |
| **Room affinity** ([Module 14](../../14-sharding-and-wide-column/)) | 4 | 790,826 | **11** | 3–4 engineer-weeks; breaks the one-socket client unless done server-side |
| **A Go/Rust edge tier** ([Module 15](../../15-async-sync-and-raw-asgi/)) | 4 | 790,826 | **11** | a second language, a second on-call surface, a network hop |

Room affinity and an edge tier land on the *same* shard count, which is the useful
observation: they are the same fix — reduce the number of processes subscribed per
room — arrived at from opposite ends. The edge tier is the better one at this
scale for a reason that has nothing to do with speed: **it keeps
[Module 17](../../17-nextjs-realtime-client/)'s one-socket-many-rooms
`SharedWorker` client intact**, because an edge node holds a user's single socket
and subscribes to whatever rooms that user is in. Client-visible room affinity does
not.

**Breaking point 2 — a single hot room.** A 50,000-member room where everyone
talks is `50,000/180 = 278` inbound msg/s × 49,999 recipients = **13.9 million
outbound msg/s from one room** — 60% above the 8.7 million ceiling that eleven
shards buy you at 1M.
Module 14 proved a hot partition cannot be split by adding hardware, and the
sequencer makes it worse: `seq` allocation is one Lua `INCR`+`XADD` on one slot,
measured at **31,900 sends/s per room** ([Module 10](../../10-ordering-and-delivery-semantics/))
— fine for writes, irrelevant to the fan-out. The mitigations are a hard room-size
cap ([Module 21](../../21-security-and-abuse-at-scale/) sets 50,000) and
**fan-out-on-read** for rooms above a threshold. Neither is automated. See the
readiness doc.

**The plan:**

| Tier | 100k (today) | 1M |
|---|---|---|
| Socket layer | 4 pods × 4 uvicorn workers | **4 Go/Rust edge nodes** + 6 Django pods for logic |
| Subscribed processes `W` | 16 | **4** (was 40 without the edge) |
| Channel layer | 4 shards | **11 shards** (82 without the edge) |
| State Redis | 3 primaries + 3 replicas | Cluster, 12 primaries + 12 replicas |
| Postgres | 4096 logical → 4 physical | 4096 logical → **16 physical**, 16 replicas |
| Monthly, list-price arithmetic | ≈ **$2,400** | ≈ **$26,000** (≈$71,000 without the edge tier) |
| Team to operate | 1–2 engineers | a platform team |

> **The honest conclusion.** This architecture is comfortable to ~117,000
> connections and stretches to ~172,000 before an SLO breaks. Past roughly 400,000
> — the crossover where 82 shards becomes unavoidable — **the socket edge stops
> being a Django problem**, and Module 15's "should you even use Django for this?"
> section stops being a thought experiment and becomes the quarter's roadmap.
> **Knowing where your architecture stops is worth more than claiming it doesn't**,
> and knowing it *in units of the thing that binds* — subscribed processes, not
> machines — is the Python-specific version of that skill.

---

## Task 2 — Two novel failures

### The one it survives: a shard failover *during* a rolling deploy

Not on the drill list, because the list runs drills three minutes apart. Real
incidents overlap.

```bash
./code/drill.sh "failover-during-rolling-deploy" \
  "./code/rolling_deploy.sh & sleep 12; docker kill pulse-capstone-cl-2-1" \
  "docker start pulse-capstone-cl-2-1"
```
**Expected:**
```
failover-during-rolling-deploy   RTO=  9.40s  RPO=0 msgs  p99=1,840ms
  pulse-3 readiness 503 at t=0.2s, nginx removed it at t=2.9s
  sentinel-c promoted cl-2-replica at t=17.1s (kill was t=12.0s)
  connections during the overlap: 100,000 held across 3 pods
  channel-layer ceiling DURING the drain: 1,245,000 out/s   (W dropped 16 -> 12)
```

✅ **Survived, RPO 0** — and note the last line, which is genuinely
counterintuitive: **draining a pod *raises* the fan-out ceiling**, from 956,000 to
1,245,000 outbound msg/s, because `W` fell from 16 to 12 and the `46 µs × W` term
fell with it. The system is *more* capable of fan-out mid-deploy than at rest. That
is not a happy accident; it is the same equation from Part A read in the other
direction, and it is the reason a rolling deploy costs 344 ms of p99 rather than
seconds.

The reason it composes at all is that the graceful drain flips readiness *before*
Uvicorn stops accepting ([Module 18](../../18-compose-ha-and-chaos/)'s `DRAIN_DELAY`),
so nginx had already removed pulse-3 by the time Sentinel started arbitrating.
Two independent recovery mechanisms, no shared state, no interaction.

### The one it doesn't: DNS starved by the ORM threadpool during a failover

This is the Python-specific failure, and it exists because of one line added for a
good reason.

```python
# apps/pulse/pulse/asgi.py — added in Module 15's Task 2, while sizing the pool
loop.set_default_executor(SyncToAsync.executor)   # one bounded pool, not two
```

Reproduce it by making the ORM pool hot and *then* forcing a Redis re-resolve:

```bash
./code/drill.sh "failover-during-resume-storm" \
  "docker kill pulse-capstone-pulse-3-1 && sleep 2 && docker kill pulse-capstone-cl-2-1" \
  "docker start pulse-capstone-pulse-3-1 pulse-capstone-cl-2-1"
```
**Expected:**
```
failover-during-resume-storm   RTO= 47.30s  RPO=1,918 msgs  p99=9,410ms

  chat_event_loop_lag_seconds p99 ....... 0.009 s   <-- GREEN. The loop is not blocked.
  sync_to_async threads busy ............ 32/32 for 38 s
  getaddrinfo p99 ....................... 1,914 ms  (baseline 0.4 ms)
  channel-layer receive loop ............ no BZPOPMIN return for 22 s on 7 of 16 workers
  connections closed by the 20 s ping timeout .... 3,142
  delivery_success ...................... 99.94%    <-- SLO 1 BREACH
```

❌ **Failed, and failed with every dashboard green.**

**The chain, step by step:**

1. Killing pulse-3 sends 25,000 clients to reconnect and `resume`. Each resume is a
   keyset query against Postgres through `database_sync_to_async`. The ORM pool
   goes to 32/32.
2. Two seconds later Sentinel promotes `cl-2`'s replica. `redis-py`'s asyncio
   client reconnects **by hostname**.
3. `asyncio`'s `loop.getaddrinfo()` is not async. It runs the blocking C
   `socket.getaddrinfo` on the loop's **default executor**.
4. Line 41 of `asgi.py` made the default executor *the ORM pool*. DNS resolution
   now queues behind 25,000 resume queries.
5. Each resolve takes 1.9 s instead of 0.4 ms. The channel layer's receive loop is
   `await`ing that connection, so it pops nothing — **for twenty-two seconds, on
   seven of sixteen workers.**
6. Clients on those workers miss their app-level pong and close at 20 s. 3,142 of
   them. The messages in flight for those seven workers' mailboxes expire.

**Why every alert stayed green** is the part worth internalising.
`chat_event_loop_lag_seconds` is [Module 20](../../20-observability-and-slos/)'s
leading indicator for exactly this class of failure, and it read **9 ms**. The
loop was not blocked. It was **starved** — perfectly healthy, spinning, with every
coroutine that mattered awaiting a future that could not resolve until a thread
freed up. *Blocked* and *starved* look identical to a user and opposite to a
metric.

**The fix, in scope, three lines:**

```python
# apps/pulse/pulse/asgi.py
from concurrent.futures import ThreadPoolExecutor
from asgiref.sync import SyncToAsync

SyncToAsync.executor = ThreadPoolExecutor(max_workers=32, thread_name_prefix="pulse-orm")
loop.set_default_executor(ThreadPoolExecutor(max_workers=8, thread_name_prefix="pulse-io"))
```

Plus belt and braces: resolve Sentinel-advertised addresses once in a Sentinel
callback and hand `redis-py` an IP, so the reconnect path performs no DNS at all.

Plus the metric that did not exist:

```python
# chat/metrics.py — starvation, as distinct from blocking
LAYER_STALL = Gauge("chat_channel_layer_receive_stalled_seconds",
                    "seconds since this worker's channel-layer receive loop last returned",
                    ["worker"])
```
```yaml
- alert: ChannelLayerReceiveStalled
  expr: max(chat_channel_layer_receive_stalled_seconds) > 5
  for: 0m
  severity: page
  annotations:
    summary: "A worker has not popped from the channel layer in >5s (loop may be STARVED, not blocked)"
```

**Re-run after the fix:**
```
failover-during-resume-storm   RTO= 11.80s  RPO=0 msgs  p99=2,410ms
  getaddrinfo p99 ....................... 0.4 ms
  chat_channel_layer_receive_stalled_seconds max ..... 1.2 s
```
✅ **RTO 47.3 → 11.8 s, RPO 1,918 → 0.**

> **The generalisation, and it is the capstone's sharpest lesson.** Module 15
> taught "never block the event loop." That is only half the rule. The other half
> is **"never let two unrelated workloads share one bounded pool"** — which Module
> 21's challenge already found once, when forty compliant users exhausted the same
> 32-thread ORM pool and took p99 to 6,120 ms. The capstone is where the two halves
> collide: a bounded pool shared between the ORM and the *DNS resolver*, welded
> together by one line added as an optimisation. **A fixed drill list proves you
> survive the failures you thought of. This is what you find when you go looking
> for the ones you didn't.**

Release-blocker verdict: the fix ships, but **nothing tests executor isolation**,
so the next well-meaning refactor re-welds them. A CI assertion is a named gap in
[`PRODUCTION_READINESS.md`](./PRODUCTION_READINESS.md).

---

## Task 3 — One measured improvement, and the ones rejected

### The candidates, with the number that decided each

| Candidate | What it moves | Cost | Verdict |
|---|---|---|---|
| **Pre-serialize the fan-out envelope once per channel-layer event (`orjson`)** | p99 296 → 251 ms; burst p99 438 → 349; worker CPU 84% → 61% | 34 lines | ✅ **shipped** |
| Larger socket buffers / `--ws-max-queue` | connection density +19% | 2 lines | ❌ **wrong resource.** We use 16% of the memory ceiling. Zero effect on p99, zero on the knee. |
| nginx `hash $room consistent` | ceiling 956,000 → 3,164,000 (3.3×) | **6 lines** | ❌ **blocked.** Breaks Module 17's one-socket-many-rooms `SharedWorker` — a user in 12 rooms would need 12 sockets. |
| A fifth channel-layer shard | ceiling +25% | 3 containers + $ | ⏸ buy it at 117,000 connections, not before |
| Server-side room affinity (Module 14) | ceiling 3.3× | 3–4 engineer-weeks | ⏸ the 1M plan needs it; this quarter does not |
| Go/Rust edge tier (Module 15) | conns/node 40k → 250k, `W` 16 → 4 | a second language, a second on-call | ⏸ crossover ≈ 400,000 connections |

Two of those rejections are worth more than the acceptance.

**The `--ws-max-queue` line is the trap the challenge warned about.** It is two
lines, it delivers a real 19% improvement, and it improves a resource that is at
16% utilisation. It changes nothing a user or an SLO can observe. *Benefit per line
is not a ranking function; benefit per line **on the binding resource** is.*

**The nginx room-hash is the more painful one.** Six lines of load-balancer config
for 3.3× the fan-out ceiling is the best ratio in the entire course — and it is
unavailable, because [Module 17](../../17-nextjs-realtime-client/) decided that one
user gets one socket across all rooms and all tabs. Client-visible room affinity
and a multiplexed client are mutually exclusive. **A decision made in the client
module, for good reasons, priced the cheapest server-side improvement out of
existence**, and neither module could have seen it alone.

### The shipped change

`AsyncJsonWebsocketConsumer.send_json` calls `json.dumps` per socket. At 199
recipients spread over 16 workers, each worker encodes the *same* dict roughly 12
times per message. Encode once when the channel-layer event arrives; send bytes.

```python
class RoomConsumer(AsyncJsonWebsocketConsumer):
    async def chat_message(self, event):
        payload = event.get("_wire")            # pre-encoded by the fan-out worker
        if payload is None:                     # own-message path still needs client_id
            payload = orjson.dumps(self.personalize(event["envelope"]))
        await self.send(text_data=payload.decode())
```

**Before / after, full acceptance test, 100,000 connections:**

```
                       before      after     delta
p50 delivery            27 ms      23 ms     -15%
p95                    121 ms     101 ms     -17%
p99                    296 ms     251 ms     -15%
p99.9                  910 ms     690 ms     -24%
burst p99              438 ms     349 ms     -20%
worker CPU at burst     84%        61%       -27 pts
Python ceiling      1,950,000  2,690,000     +38%
measured knee        172,000    174,000      +1.2%   (within noise)
```

✅ **The knee did not move, and it was never going to.** Redis's single thread
still binds at 956,000 outbound msg/s. What moved is **the number SLO 2 measures**:
p99 at the operating point fell 15%, and the burst window gained 89 ms of headroom
against the 500 ms target.

**The justification, stated as a distinction worth keeping:** the *knee* is a
throughput ceiling set by the binding resource; the *latency at a given load* is
set by whatever does per-delivery work. They are different resources and you fix
them with different changes. This one is the change that improves the number the
SLO measures, and the ceiling can only be moved by sharding or affinity, which cost
money or weeks.

⚠️ **And it creates a gap.** Bypassing `send_json` means a Channels release that
changes the consumer's send path breaks Pulse silently. That goes in the readiness
document as a named upgrade risk with a required contract test — an improvement
that ships a liability is still an improvement, but only if you write the liability
down.

---

## Task 4 — The runbook, blind-tested

Full runbook in `RUNBOOK.md`; the structure per SLO is: **alert (with both burn
windows) → three diagnostic steps → causes ranked by probability → remediation.**

Excerpt, SLO 1:

```markdown
### SLO 1 — Delivery success < 99.99%

ALERT   burn > 14.4x over 1h AND 5m   -> page      (budget gone in ~2 days)
        burn > 6x over 6h AND 30m     -> page
        chat_layer_over_capacity_total increase > 0 for 0m -> page  (ANY drop is loss)

DIAGNOSE (in order, ~90 seconds)
  1. increase(chat_layer_over_capacity_total[5m])  -- are we dropping at the mailbox?
  2. max(chat_channel_layer_receive_stalled_seconds) -- is a worker STARVED?
  3. XPENDING per room stream on the busiest shard  -- is a consumer dead?

CAUSES, ranked
  1. Burst above the mailbox's time budget      -> raise capacity, re-derive from rate
  2. A worker starved on a shared bounded pool  -> Task 2's executor split
  3. A dead consumer holding its PEL            -> XAUTOCLAIM idle threshold too high
  4. A shard at 95% CPU                         -> add a shard; do NOT add pods
REMEDIATE ... (per cause)
```

**Blind test — three drills injected without warning:**

| Injected | Path followed | Time to diagnosis | Result |
|---|---|---|---|
| App pod brownout | SLO 3 burn alert → readiness-503 panel → pod CPU | **4 min 10 s** | ✅ |
| Task 2's starvation failure | SLO 1 burn alert → loop-lag panel (green) → chased Redis | **19 min** | ❌ no entry existed |
| Celery relay split-brain | `chat_stream_duplicate_xadd_total` derived metric | **2 min 40 s** | ✅ |

Two findings, one of which repeats Module 18's:

1. **The gap without an alert is worse than the gap without a fix.** The starvation
   failure had a *fix* (shipped in Task 2) and no *alert*, so the on-call engineer
   spent 19 minutes proving Redis was healthy — which it was. Added
   `ChannelLayerReceiveStalled` and a runbook entry that names the symptom.
2. **Name alerts after symptoms, not conclusions.** The draft alert was called
   `RedisChannelLayerDown`. Redis was up; a worker was starved. An engineer who
   trusts the alert name spends their first five minutes in the wrong system.
   Renamed to `ChannelLayerReceiveStalled`, and every other alert audited for the
   same defect. (Module 18's blind test found this once already, which is the
   argument for blind-testing runbooks more than once.)

---

## Task 5 — Three objections, answered

### Objection 1 — "Your entire fan-out ceiling is one Redis thread. Use Kafka."

**Rebut with the number, then concede the trigger.** Kafka genuinely handles this
shape better: [Module 16](../../16-kafka-comparison/) measured why — the data is on
disk, twenty-four consumers reading the same recent offsets hit the same page-cache
pages, and `sendfile` serves them with no per-read CPU on a single thread. Redis
pays one thread for every read, which is precisely our binding resource.

**But** Module 16's own scorecard puts Pulse at **five of five** on the
Redis-Streams column: we already run Redis for `seq`, presence, buckets and
tickets; we need a log *per room* and a million keys is free where a million
partitions is impossible; our replay window is minutes by design; our latency
budget is 500 ms end to end; and we are a small team. Adding Kafka is a second
stateful system, a second upgrade path, a second on-call surface, and 64 partitions
that must be sized before the first message.

**Concede the trigger, precisely:** Kafka becomes correct the moment **a second
consumer appears** (search, analytics, moderation, ML) or **subscribed worker
count passes ~24**. The 1M plan crosses the second within one growth step, and Task
6 shows the first one arriving with the next feature anyone asks for. Decision #3
in the review says so, with those two numbers in its "would change if."

### Objection 2 — "You are holding 100,000 sockets in CPython. That is the wrong tool."

**Partially concede, and rebut the part that is wrong today.** This is the
strongest objection to the *architecture* and it is wrong about the *present*: at
6,250 connections per worker we use **16%** of the memory ceiling, our worker CPU
peaks at 61% at burst after Task 3, and the resource that actually breaks at
172,000 connections is Redis's single thread — which a Go rewrite would not touch
by one message per second. Rewriting the socket edge in Go today buys nothing an
SLO can see.

**Concede the future, with the crossover.** Module 15 named the condition and the
1M plan crosses it: past roughly **400,000 connections**, `W` grows past the point
where any affordable shard count keeps up, and the fix that works — reduce
subscribed processes per room — is exactly what an edge tier gives you for free.
At that point the answer is not "rewrite Pulse in Go"; it is "put a dumb Go/Rust
socket terminator in front of Pulse and keep every line of business logic in
Django," which is the architecture Module 15 sketched and the 1M plan adopts.

**So decision #2 in the review is labelled provisional** — the only runtime choice
in either course that carries an expiry date, and the JVM twin never has to write
it down.

### Objection 3 — "You run your own Postgres and Redis HA. Just use managed services."

**Concede almost entirely.** Module 19 said it outright: managed is *less*
operational work, and self-managing "should be a decision with a reason." Our
reason is **pedagogical** — the course builds Sentinel and Patroni so you know what
the operator does when it does it for you.

The honest production answer is: **managed by default.** RDS/Aurora and a managed
Redis unless there is a specific reason — cost at your scale, a feature the managed
product lacks, or existing deep expertise. Module 18's challenge already priced our
posture: HA costs 8.4× the money, +52% p99, −8% knee, and the honest way to halve
it is to *reduce the ambition* (keep Redis HA, drop Patroni/etcd/HAProxy, promote
Postgres by hand: $1,180 → $390/month, PG RTO 11.8 s → ~5 minutes) rather than to
keep the diagram and delete the margin.

Decision #8 is labelled provisional, and the readiness doc lists "either managed
Postgres or a funded on-call rotation" as a release blocker.

> **Two of three objections are substantially conceded, and one of the concessions
> is the runtime the course is named after.** That is what an architecture review
> looks like when it is doing its job: not a defence of every choice, but a map of
> which choices are firm, which are provisional, and what would move each one.
>
> A fourth objection is worth naming even though the challenge asked for three:
> *"three of your ten decisions are provisional — is that an architecture or a
> bet?"* The answer is that every architecture is a bet, and the useful distinction
> is whether you wrote down the odds. We did, with thresholds someone can go and
> measure.

---

## Task 6 (stretch) — What I'd build next: message search

The most-requested chat capability the course deliberately skipped
([Module 12](../../12-postgres-message-store/): "no full-text search in the message
store; search goes elsewhere").

**Architecture:**

```
  chat.Message ──▶ outbox (M13) ──┬──▶ Redis Stream (delivery, unchanged)
                                  └──▶ Kafka ──▶ indexer ──▶ OpenSearch
                                                  (its OWN process class,
                                                   not a Channels worker)
```

Three things about this sketch are Django-specific and none of them are the
indexer:

1. **The indexer cannot live in a Channels worker.** Tokenising and normalising
   message bodies is CPU-bound Python, and CPU-bound Python on a worker process is
   the GIL taking the event loop's core away from 6,250 sockets. It needs a
   separate process class with its own scaling — [Module 01](../../01-python-async-concurrency/)'s
   lesson arriving at the very end of the course, in the one place nobody expects
   it.
2. **Authz moves to query time and loses its cache.** Module 21's delivery-time
   authz works because each worker caches room membership with a 10-second
   staleness budget. A search query spans *every* room the user has ever been in;
   there is no per-worker cache shaped like that. And Module 21's challenge finding
   #1 applies with full force: `history_visible_from` must be enforced **inside the
   index**, or search returns messages from before a user joined. That is the bug
   that gets written about.
3. **E2EE rooms are unsearchable server-side.** Module 21's tradeoff, arriving as a
   product problem: the UI has to say "this room's messages aren't in results"
   without making it feel broken.

**Most disrupted: decision #3 (Redis Streams over Kafka).** Module 16 named "the
moment a second consumer appears" as the trigger that flips it, and search *is* the
second consumer. So **shipping search probably means shipping Kafka**, and the
review's single most-cited conclusion — Redis Streams over Kafka — is conditional
on there being exactly one consumer. Search removes the condition.

**Effort: ~5 engineer-weeks.** The indexer is one. The other four are query-time
authz, `history_visible_from` in the index, reindexing on edit and delete (which
Module 12's edit path does not currently fan out), and the Kafka adoption that
decision #3 has been deferring.

> The instructive part: **the feature that looks like "just add OpenSearch" is the
> feature that re-opens the biggest architectural decision in the course.** Seeing
> that before you commit the quarter is the second-order thinking the whole course
> was training.

---

## The two required documents

- **[`ARCHITECTURE_REVIEW.md`](./ARCHITECTURE_REVIEW.md)** — ten decisions, each
  with decision / evidence / rejected alternative / falsifying condition. Three are
  labelled provisional: the fan-out backbone, the self-managed data tier, and the
  runtime itself.
- **[`PRODUCTION_READINESS.md`](./PRODUCTION_READINESS.md)** — nine gaps, five
  release blockers, one of which this capstone created in Task 3.

---

## Scoring this capstone against the rubric

| Axis | Score | Why |
|---|---|---|
| **Correctness** | Excellent | RPO 0 on 8/8 drills under full load; every SLI measured, none asserted; found two real defects (the mailbox time budget, the welded executor) that no module's tests covered |
| **Performance** | Excellent | All four SLOs green at 100,000; knee measured at 172,000 and the model's 4.5% error reported; operates at 55% of the fan-out ceiling on purpose |
| **Resilience** | Strong | RTO ≤ 13.2 s / RPO 0 everywhere; the 25,000-reconnect wart named with the three mechanisms that keep it survivable; the compound-failure drill run rather than assumed |
| **Observability** | Strong | Five incident questions in under a minute; blind test found a 19-minute dead end and closed it with a new metric and a renamed alert |
| **Judgment** | Excellent | Every decision carries its rejected alternative; 3 of 10 conceded provisional including the runtime; the best-ratio improvement rejected because a Module 17 decision priced it out; 5 release blockers named, one self-inflicted |

The judgment axis is excellent **because of** the concessions, not despite them. A
capstone that defended all ten decisions and declared itself production-ready would
fail the one axis the entire course exists to teach: knowing what you built, what
you didn't, what binds, and what would change your mind.

---

## Record it

```markdown
## Module 22 — capstone

Topology DERIVED, not chosen: 4 pods x 4 workers = 16 subscribed processes,
  and therefore FOUR channel-layer shards (3 puts the burst at 74% of ceiling).
  Nothing in modules 00-21 said "four"; Module 07's 55+46W, Module 19's shard
  math and Module 06's 65% rule said it together.
Acceptance FAILED first run: capacity 3000 was 2 s at Module 07's steady rate
  and 1.13 s at the capstone's burst rate -> 2,847 drops, 61 gaps.
  Re-derived from the ACTUAL arrival rate -> 6000 (25 MB). All four SLOs green:
  p50/p99/p99.9 = 27/296/910 ms, success 99.993%, gaps 3.
Chaos: RPO 0 on 8/8 under 100k load. Worst RTO 13.2 s. Eight deliberate
  catastrophes = 6.2% of SLO 2's 43-minute monthly budget.
Knee 172,000 conns; SLO 2 breaks first; BINDING RESOURCE = one Redis thread at
  96% with 73% of per-worker memory unused. The JVM twin is memory-bound at
  46k/node. Same design, different wall, because our unit is a PROCESS.
Novel failure found: loop.set_default_executor(SyncToAsync.executor) welds DNS
  to the ORM pool; a failover during a resume storm starves 7 of 16 workers for
  22 s with EVERY dashboard green (starved != blocked). 3-line fix + a new
  starvation metric. "Never block the loop" is only half the rule.
Improvement: pre-serialized fan-out (34 lines) -> p99 296->251 ms and burst p99
  438->349. Did NOT move the knee and was never going to. Rejected: socket
  buffers (+19% on a resource at 16%); nginx room-hash (6 lines, 3.3x ceiling,
  BLOCKED by Module 17's one-socket client).
1M plan: 82 channel-layer shards without room affinity, 11 with -- or with a
  Go/Rust edge tier, which gets affinity's W=4 while KEEPING the one-socket
  client. Crossover ~400,000 connections.
Review: 10 decisions, 3 provisional (backbone, self-managed data tier, and the
  RUNTIME). Readiness: 9 gaps, 5 blockers, 1 created by this capstone.
```

---

That is the course. You built a real-time system from the wire up, measured every
claim on your own machine, found the wall, learned which resource it is made of,
and can now defend the whole thing — including the three places where the honest
answer is "provisionally, and here is the number that would change my mind."

If you have not yet worked
[`spring-boot-chat-course`](../../../spring-boot-chat-course/22-capstone/), read its
capstone solution next to this one. Two runtimes, one architecture, four SLOs, and
completely different walls. That comparison is the most transferable thing either
course has to give.
