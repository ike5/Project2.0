# Module 19 — Kubernetes HA & Multi-Region

**Goal:** Move the Module 18 stack onto Kubernetes without losing anything it
bought you, learn the four places Kubernetes quietly assumes your workload is
stateless HTTP, and understand honestly what a second region costs a chat system.

⏱️ ~6 hours · **Prerequisites:** Modules 00–18. Kubernetes basics help but aren't
assumed — this module cross-references
[`kubernetes-course`](../../kubernetes-course/) throughout.

> This is the Django/ASGI twin of
> [`spring-boot-chat-course/19-kubernetes-ha-and-multiregion`](../../spring-boot-chat-course/19-kubernetes-ha-and-multiregion/).
> The Kubernetes objects are identical — a PodDisruptionBudget does not care what
> language your pods run. Three things are genuinely different, and they are the
> reason this module is not a copy: **signal delivery to a Python process tree**,
> **a liveness probe that cannot see a blocked worker**, and **an HPA whose
> ceiling is set by Module 07's channel-layer amplification rather than by CPU.**

---

## Kubernetes adds automation, not availability

Module 18 already had HA. Every failover in that module was performed by Sentinel,
by Patroni, or by an etcd quorum — none of which Kubernetes replaces. What
Kubernetes adds is that the things you were doing by hand become objects the API
server enforces.

| Module 18, in Compose | Module 19, in Kubernetes |
|---|---|
| `docker compose up -d --scale pulse=3` | `Deployment.replicas: 3`, self-healing |
| `docker start pulse-ha-pulse-1-1` after a kill | kubelet restarts, controller replaces |
| `stop_grace_period: 60s` | `terminationGracePeriodSeconds` + `preStop` |
| `depends_on: { condition: service_healthy }` | readiness gates, init containers |
| `rolling_deploy.sh`, a bash loop | `RollingUpdate` with `maxUnavailable: 0` |
| "don't drain two of three etcd nodes" — a wiki page | **PodDisruptionBudget**, enforced |
| nginx `upstream` block, edited by hand | Service endpoints, updated by a controller |

**The PodDisruptionBudget is the one genuinely new capability.** In Compose,
"never take the second etcd node down during maintenance" is a convention someone
can violate at 2 a.m. In Kubernetes it is an object, and `kubectl drain` refuses.

Everything else on that list is convenience. Convenience matters — Module 18's
`rolling_deploy.sh` was 6 lines and had no idea what readiness meant — but do not
arrive expecting Kubernetes to make your system available. **Kubernetes
reschedules; your quorum protocol fails over.** Part G measures exactly how far
apart those two things are.

---

## Deployment or StatefulSet for a socket server?

This is where most Kubernetes tutorials for "stateful WebSocket workloads" go
wrong, and the wrong answer is the intuitive one.

| | Deployment | StatefulSet |
|---|---|---|
| Pod names | random (`pulse-7d4f8c9b4-x8k2`) | ordinal, stable (`redis-0`) |
| Storage | shared or none | one PVC per pod, follows the pod |
| Start / stop order | parallel | ordered (0, then 1, then 2) |
| DNS | one Service | **per-pod DNS** (`redis-0.redis.default.svc`) |
| Scale-down | arbitrary pod | **always the highest ordinal** |

Pulse's app tier holds an enormous amount of state: 10,000 live sockets, each
with a consumer instance, a `scope`, a group subscription and a per-connection
sequence cursor. It is obviously stateful. So a StatefulSet, right?

**No. Use a Deployment.**

The question a StatefulSet answers is *"when this pod comes back, must it be the
same pod?"* — same name, same disk, same position in a replication topology.
Redis-1 must come back as redis-1 because redis-2 is configured to replicate from
`redis-1.redis`. Patroni member 3 must reclaim its own PGDATA.

Pulse's app pod answers **no** to every part of that:

- **The state cannot be recovered.** A TCP connection is held by a process. Kill
  the process and the socket is gone; there is no disk to reattach and no name to
  reclaim. A "restarted" `pulse-0` shares nothing with the old one but a label.
- **The state is not on disk.** It is in the event loop, and Module 18 established
  the whole drain protocol precisely because you *cannot* migrate it — you can
  only close it politely and let the client come back.
- **Ordered rollout is actively wrong.** A StatefulSet's default
  `podManagementPolicy: OrderedReady` updates one pod at a time and waits for
  Ready. For 10 replicas each taking 45 seconds to drain, that is a 7½-minute
  deploy with a reconnect wave at every step. A Deployment with `maxSurge: 1`
  gives you the same one-at-a-time safety without the ordering constraint.
- **Ordinal scale-down is the wrong pod.** A StatefulSet always removes the
  highest ordinal. That pod might be holding 9,800 connections while `pulse-2`
  holds 40. The challenge measures what picking the right pod is worth.

> **The rule:** StatefulSet is for **identity you must reclaim**. Connection state
> is identity you *cannot* reclaim. Deployment for the app tier; StatefulSet for
> Redis, Postgres and etcd, which have all three of the properties above.

The one thing you lose is stable per-pod DNS, which you will want in
[Module 20](../20-observability-and-slos/) for per-worker metrics. A **headless
Service alongside the Deployment** gives you per-pod DNS records without the rest
of the StatefulSet semantics — that is the whole trick, and the lab uses it.

---

## Probes: a socket server needs different ones

Kubernetes has three probes, and all three of their defaults were designed for a
stateless HTTP server that can be killed cheaply. Pulse can't.

```
startupProbe    "has it finished booting?"      → suppresses the other two
readinessProbe  "should traffic go here?"       → Service endpoint in/out
livenessProbe   "should I kill it?"             → RESTART. Very expensive here.
```

### Readiness does not drain anything

The single most misunderstood fact in this module:

> **A readiness probe going false removes the pod from the Service endpoints. It
> does nothing to the connections the pod already holds.**

For an HTTP service that is a complete drain — requests are short, so within a
second every in-flight request has finished and no new one arrives. For a socket
server it changes *nothing about the 10,000 people currently connected*. They
stay connected, they keep sending, and they keep expecting delivery.

That is why Module 18's `readiness.set("draining")` was only *phase one* of the
drain. Readiness stops the bleeding; the control frame and `close(1001)` are what
actually end the connections. Kubernetes gives you no help with the second half.

Module 18 already built the readiness endpoint, and it carries the capacity signal
that turned the brownout drill from RPO 4,102 into RPO 0:

```python
async def readyz(request):
    if not readiness.ready:
        return JsonResponse({"status": "draining"}, status=503)
    queued, p99 = outbound_queue_depth(), fanout_p99_ms()
    if queued > 5000 or p99 > 2000:                      # shed BEFORE you're the problem
        return JsonResponse({"status": "capacity", ...}, status=503)
    return JsonResponse({"status": "up", ...}, status=200)
```

That endpoint is exactly right for Kubernetes too — with one addition the lab
makes: a readiness probe that returns 503 for *capacity* reasons will, under a
cluster-wide load spike, take **every** pod out of the endpoints at once. An empty
endpoint list means the Service blackholes traffic. The lab caps it.

### Liveness on a multi-worker pod is nearly blind

Here is the Python-specific problem, and it is a good one.

Each `pulse` pod runs Uvicorn with **4 worker processes** (Module 07's measured
sweet spot — more on that below). All four share one listening socket; the kernel
hands each new connection to whichever worker calls `accept()` first.

```
   kubelet ──HTTP GET /healthz──▶ :8000 ──kernel──▶ worker 1 │ 2 │ 3 │ 4
                                                      ▲
                                        whichever one is free answers
```

Worker 3 has blocked its event loop on a synchronous ORM call
([Module 15](../15-async-sync-and-raw-asgi/): p99 61 ms → 9,340 ms for all 5,000
of its connections). Worker 3 is, from every user's point of view, dead.

**The liveness probe will almost never notice.** A blocked worker doesn't call
`accept()`, so the kernel gives the probe to a healthy worker, which answers 200
instantly. With `failureThreshold: 3` and `periodSeconds: 10` you would need three
consecutive probes to land on the same blocked worker — at 1-in-4 odds that is
`0.25³ = 1.6%` per cycle. The pod stays Ready, holding a quarter of its
connections hostage, indefinitely.

Three responses, and you want all three:

1. **Do not try to fix this with liveness.** Restarting the pod kills 3 healthy
   workers to punish 1. A restart is the most expensive action available for a
   socket server; reserve it for a pod that is genuinely, wholly dead.
2. **Make the probe worker-aware.** `/healthz` returns the responding worker's
   PID and its event-loop lag. The kubelet can't aggregate that, but Prometheus
   can — which is why [Module 20](../20-observability-and-slos/) scrapes
   `chat_event_loop_lag_seconds` with a `worker` label and alerts on
   `max by (pod) (...)`, not the average.
3. **Have the worker take itself out.** A worker whose loop lag exceeds a
   threshold closes its own connections with a `control{reconnect}` frame — the
   Module 18 drain, self-inflicted, on one process. The clients land on healthy
   workers within their jittered retry window. The challenge builds this.

> **The general shape:** Kubernetes probes are *pod*-granular and your failure
> domain is *process*-granular. Anything smaller than a pod, Kubernetes cannot
> see. On the JVM one instance is one process and this problem does not exist —
> it is a direct consequence of the GIL forcing you to run several processes per
> box ([Module 01](../01-python-async-concurrency/)).

### Probe settings that survive contact with a socket server

```yaml
startupProbe:                          # Django + Channels boot: migrations check,
  httpGet: { path: /healthz, port: 8000 }   # app registry, channel-layer connect
  failureThreshold: 30
  periodSeconds: 2                     # 60s of budget, then liveness takes over
readinessProbe:
  httpGet: { path: /readyz, port: 8000 }
  periodSeconds: 3
  failureThreshold: 2                  # react fast: 6s to leave the endpoints
  successThreshold: 1
livenessProbe:
  httpGet: { path: /healthz, port: 8000 }
  periodSeconds: 10
  failureThreshold: 6                  # DELIBERATELY SLOW: 60s before a restart
  timeoutSeconds: 5
```

Readiness is twitchy on purpose (leaving the load balancer is cheap and
reversible). Liveness is sluggish on purpose (a restart costs 10,000 reconnects).
**Those two knobs point in opposite directions, and defaults get both wrong.**

---

## Graceful drain: `preStop`, and the two ways Python breaks it

Module 18 built the drain out of three pieces — a per-process connection registry,
the ASGI `lifespan.shutdown` hook, and a two-phase SIGTERM handler that flips
readiness *before* Uvicorn stops accepting. All three port unchanged. Kubernetes
adds one requirement and Python adds two traps.

### The Kubernetes requirement: `preStop` sleep

```
kubelet decides to terminate a pod
   ├──▶ removes it from the EndpointSlice   ┐
   └──▶ runs preStop, then sends SIGTERM    ├─ THESE ARE CONCURRENT
                                            ┘
```

Endpoint removal propagates asynchronously: endpoints controller → every
kube-proxy → every node's iptables/IPVS rules → the ingress controller's upstream
list. That takes **hundreds of milliseconds** (the lab measures ~620 ms in `kind`).
Meanwhile SIGTERM has already arrived and Uvicorn has already stopped calling
`accept()`.

For HTTP that's a handful of connection-refused errors and a retry. For a
**WebSocket handshake** it is a connection routed to a pod that will never
complete it, and the client sees a failed upgrade rather than a retryable 503.

```yaml
lifecycle:
  preStop:
    exec:
      command: ["/bin/sh", "-c", "sleep 6"]
```

Six seconds looks like superstition. It is the documented, standard fix, and Part
E measures what it is worth: **118 rejected handshakes without it, 0 with it.**

### Python trap 1 — set `PULSE_DRAIN_DELAY=0` in Kubernetes

Module 18's SIGTERM handler already waits `DRAIN_DELAY=6` seconds before deferring
to Uvicorn, for exactly the same reason — to let nginx's healthcheck notice.

In Kubernetes, `preStop` has **already done that wait**, before SIGTERM was even
sent. Leaving `PULSE_DRAIN_DELAY=6` set makes you wait twice: 6 s of `preStop` plus
6 s of handler, then 2 s of frame flush, then the close loop. That is 14 seconds
of a `terminationGracePeriodSeconds` budget spent on one wait done twice, and it
is the kind of thing nobody notices until a deploy of 30 pods takes 20 minutes.

```yaml
env:
  - name: PULSE_DRAIN_DELAY
    value: "0"          # preStop already waited; do not wait twice
```

> Two mechanisms that solve the same problem, one from each platform, silently
> composing into double the delay. Look for this pattern whenever you port a
> Compose stack — timeouts and retries stack the same way.

### Python trap 2 — PID 1 must be Uvicorn

This one silently deletes the whole drain, and it is the single most common way
Python graceful shutdown fails in containers.

```dockerfile
# BROKEN. /bin/sh is PID 1. It does not forward SIGTERM to its child.
CMD uvicorn pulse.asgi:application --host 0.0.0.0 --port 8000 --workers 4
```

Docker's shell form wraps the command in `/bin/sh -c`. The shell becomes PID 1,
receives SIGTERM, and — unless it is `exec`-ing — **does not pass it on**. Uvicorn
never learns it is shutting down. `lifespan.shutdown` never fires. Your registry
is never drained. Then `terminationGracePeriodSeconds` expires and the kubelet
SIGKILLs everything, and 10,000 clients get a bare TCP close (code 1006) exactly
as if you had never written the drain.

The tell is that it *looks like it works*: the pod terminates, the rollout
completes, the deploy is green. Only the close-code distribution in the client
tells you, which is why Part E counts close codes rather than trusting the
rollout status.

```dockerfile
# CORRECT — exec form, Uvicorn is PID 1 and gets the signal directly.
CMD ["uvicorn", "pulse.asgi:application", "--host", "0.0.0.0", "--port", "8000", \
     "--workers", "4", "--timeout-graceful-shutdown", "45"]
```

Uvicorn's master then forwards SIGTERM to each worker, and **each worker drains
its own registry** — the registry is process-local because the connections are.
Same GIL/process boundary that forced Redis on you in
[Module 04](../04-channels-chat-single-node/), showing up at shutdown.

### The grace period is a sum, and it must be bigger than its parts

```
terminationGracePeriodSeconds  >=  preStop (6)
                                 + drain flush (2)
                                 + close loop (~1s per 10k sockets)
                                 + Uvicorn --timeout-graceful-shutdown headroom
```

Pulse uses **90 s** with `--timeout-graceful-shutdown 45`. The measured drain of a
pod holding 3,300 sockets takes about 9 seconds; the headroom exists because
`terminationGracePeriodSeconds` is a hard SIGKILL deadline and there is no partial
credit. Note that `preStop`'s duration is **inside** the grace period, not extra —
a 6-second `preStop` with a 10-second grace period leaves you 4 seconds to drain.

---

## Rolling updates that don't cause a reconnect storm

```yaml
strategy:
  type: RollingUpdate
  rollingUpdate:
    maxUnavailable: 0     # never drop below `replicas` of *capacity*
    maxSurge: 1           # add one, then remove one
```

`maxUnavailable: 0` guarantees capacity. It does not guarantee that the clients on
the drained pod come back gently — that is the client's jitter and the server's
`retry_after_ms`, both from Module 18 and
[Module 11](../11-presence-and-rate-limiting/).

Two Kubernetes-specific storm sources Module 18 didn't have:

**1. `minReadySeconds` is the pacing knob.** By default a pod counts as available
the instant readiness passes, so the next pod starts draining immediately. Its
clients arrive at a pod that has been serving for one second and has cold caches
and a cold connection pool. `minReadySeconds: 30` forces a settle window between
steps. Module 18's `rolling_deploy.sh` had `sleep 45` for this reason; here it is
a field.

**2. Every drained pod's clients return through the ingress at once.** The
`retry_after_ms` jitter (1–30 s, per client) spreads them, but with `maxSurge: 1`
and 10 replicas you get 10 waves 45 seconds apart. If your jitter window is 30 s
and your step interval is 45 s, the waves don't overlap. If someone "speeds up the
deploy" by dropping `minReadySeconds` to 5, they do. **The relationship between
the jitter cap and the rollout step interval is a real constraint that nothing
enforces** — the challenge writes the check.

### `group_expiry` and rollouts

[Module 11](../11-presence-and-rate-limiting/) set `group_expiry: 43_200` (12 h)
and had every heartbeat re-`group_add` to refresh the membership timestamp. A
rolling update is where the second half earns its keep: during the rollout a room
briefly has group memberships from both the draining pod's workers and the new
pod's workers. The draining pod's entries are discarded on `group_discard` during
`close()` — but a pod SIGKILLed at the end of its grace period leaves them behind,
and they sit in `asgi:group:room.7` as ghost members receiving `group_send` traffic
that goes nowhere, until `group_expiry` reaps them. **Twelve hours of ghosts is the
price of one ungraceful pod termination**, and it is another reason the PID-1 trap
above matters more than it looks.

---

## PodDisruptionBudgets

```yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata: { name: etcd }
spec:
  minAvailable: 2                  # of 3 — the quorum must survive
  selector: { matchLabels: { app: etcd } }
```

This blocks **voluntary** disruptions — `kubectl drain`, node upgrades, cluster
autoscaler scale-down — from taking the second etcd pod. It does nothing about a
node crash; nothing can.

Module 18's etcd quorum-loss drill (RTO 45.2 s, **all writes rejected**) is the
failure a PDB exists to prevent, and its conclusion there was "run etcd on
separate failure domains" — which in Kubernetes is a `topologySpreadConstraint`
plus this PDB.

⚠️ **`minAvailable == replicas` makes your cluster un-upgradeable.** A
`minAvailable: 3` on a 3-replica set means no node can ever be drained, the
eviction API retries forever, and the error message does not say "your PDB is
impossible." Always `minAvailable = replicas - 1`, or `maxUnavailable: 1`.

For the **app** tier the PDB is `maxUnavailable: 1` — not because of quorum, but
because two simultaneously drained pods double the reconnect wave onto the
survivors, which is precisely the Module 18 herd that turned a 4.2 s RTO into
41.8 s.

---

## Topology spread: a quorum in one zone is not a quorum

```yaml
topologySpreadConstraints:
  - maxSkew: 1
    topologyKey: topology.kubernetes.io/zone
    whenUnsatisfiable: DoNotSchedule      # quorum members: a RULE
    labelSelector: { matchLabels: { app: etcd } }
```

`DoNotSchedule` means a pod stays `Pending` rather than violating the spread. For a
quorum member that is what you want: a `Pending` pod is a visible problem, and
three etcd pods on one node is an invisible one that becomes visible during the
outage.

For the **app** tier use `whenUnsatisfiable: ScheduleAnyway`. A Pulse pod that
can't be placed evenly should still be placed — capacity beats balance when the
failure mode of imbalance is "slightly worse blast radius" rather than "lost
quorum."

> Same object, opposite setting, and the reason is the failure mode. Copying the
> Redis stanza onto the app tier is how you get `Pending` app pods during a
> traffic spike.

---

## Session affinity: still an optimization, still awkward

[Module 07](../07-scale-out-redis-channel-layer/) established that with a Redis
backplane, sticky sessions are an *optimization*, not a correctness requirement —
any worker can serve any user. Kubernetes offers two mechanisms and neither is
good:

| Mechanism | How | Problem |
|---|---|---|
| `Service.sessionAffinity: ClientIP` | kube-proxy hashes the source IP | **Breaks behind NAT** (thousands of users, one IP) and is invalidated whenever the endpoint set changes |
| Ingress cookie affinity | `nginx.ingress.kubernetes.io/affinity: cookie` | Works, but the affinity table lives in the ingress controller's memory |

The nginx-ingress annotations are the practical answer, and note the last two:

```yaml
annotations:
  nginx.ingress.kubernetes.io/affinity: "cookie"
  nginx.ingress.kubernetes.io/session-cookie-name: "pulse-node"
  nginx.ingress.kubernetes.io/affinity-mode: "persistent"
  nginx.ingress.kubernetes.io/proxy-read-timeout: "3600"
  nginx.ingress.kubernetes.io/proxy-send-timeout: "3600"
```

⚠️ **The ingress `proxy-read-timeout` default is 60 seconds and it kills idle
WebSockets.** This is the same lesson as
[Module 03](../03-realtime-transports/) and the same one Module 18 applied to its
own nginx — and this is where people rediscover it, because the ingress controller
is a *different* nginx with *different* defaults that nobody remembers configuring.

---

## Autoscaling: the metric is not CPU, and the ceiling is not your cores

### Why CPU is wrong

A pod holding 10,000 idle connections uses very little CPU and has essentially no
capacity left. At the pinned **≈45 KB per idle connection** plus kernel socket
buffers, memory and the event loop's callback queue bind long before CPU does. An
HPA targeting 70% CPU would sit at 18% and never scale up — and would scale
*down*, evicting a pod whose 10,000 connections then land on pods that cannot hold
them.

**Scale on a signal that reflects capacity:**

```
chat_connections_active / MAX_CONNECTIONS_PER_POD     # the denominator is measured
chat_event_loop_lag_seconds                           # the leading indicator
chat_group_send_seconds p99                           # the enqueue half of latency
```

All three already exist — `chat/metrics.py` from
[Module 06](../06-load-testing-harness/) defines them, and Module 20 is where they
get a dashboard.

### Why more pods stop helping — and this is the Python part

Here is the constraint the JVM twin does not have, and it is the reason this
module's autoscaling section is longer than its sibling's.

Module 07 measured the channel layer's cost model precisely:

```
fixed per group_send      55 µs   (read the group membership, set up the EVAL)
per subscribed worker     46 µs   (one more key in the EVAL, one more BZPOPMIN wake)
```

That per-worker term is charged against **Redis's single thread**, and it is per
*worker process*, not per pod. Module 07's headline finding — **eight workers were
slower than four** (441,000 vs 521,000 outbound msg/s) — is that term becoming the
ceiling.

A Pulse pod runs 4 workers, so **each replica adds 4 to that multiplier.** With
Module 18's three Sentinel-managed channel-layer shards, each shard sees a third of
the `group_send` traffic, and the ceiling for `W` total subscribed workers is:

```
group_sends/s  =  3 shards × 0.95 × 1,000,000 µs  ÷  (55 + 46·W) µs
outbound/s     =  group_sends/s × 199 recipients
```

| Replicas | Workers | Redis-thread ceiling | Python ceiling | Which binds |
|---|---|---|---|---|
| 1 | 4 | 2,373,000 out/s | ~521,000 | Python ✅ |
| 2 | 8 | 1,341,000 out/s | ~1,010,000 | Python ✅ |
| **3** | **12** | **934,000 out/s** | ~1,490,000 | **Redis ❌** |
| 4 | 16 | 717,000 out/s | ~1,950,000 | Redis ❌❌ |

**The third replica is the new eighth worker.** Part F measures it and the numbers
land within a few percent of that arithmetic. An HPA that scales on connections
alone will happily walk you past replica 2 and make fan-out *slower*.

Three consequences, all of which the lab implements:

1. **`maxReplicas` is a measured constant, not a big round number.** Pulse caps at
   the point where the Redis-thread ceiling crosses the Python ceiling, and the
   HPA carries a comment explaining the arithmetic so the next person doesn't
   raise it.
2. **The escape is sharding, not scaling.** More channel-layer shards move the
   ceiling linearly; room affinity ([Module 14](../14-sharding-and-wide-column/))
   reduces `W` per room, which moves it much faster. Neither is an HPA setting.
3. **Scale-down must be far more reluctant than scale-up.** Scaling up is cheap;
   scaling down disconnects everyone on a pod. The `behavior` block encodes that
   asymmetry, and the challenge measures what it saves.

---

## Redis and Postgres in Kubernetes — or deliberately not

### Postgres: use the operator, and know what it's doing

[CloudNativePG](https://cloudnative-pg.io/) replaces the Patroni + etcd + HAProxy
tier from Module 18 with one CRD. It does the same three jobs: leader election
(via the Kubernetes API instead of etcd), fencing, and endpoint steering — and it
gives you `pulse-pg-rw` and `pulse-pg-ro` Services, which is exactly what Module
18's HAProxy `:5000`/`:5001` were doing by hand.

Two Django-specific things do **not** change:

```python
DATABASES["default"]["OPTIONS"] = {"prepare_threshold": None}   # PgBouncer, again
DATABASES["default"]["CONN_MAX_AGE"] = 0                        # let the pooler own it
```

CloudNativePG's `Pooler` CRD is PgBouncer in transaction mode, so
[Module 13](../13-partitioning-replication-pooling/)'s psycopg gotcha is identical.
The `-ro` Service is what the Module 13 database router's `replica` alias points
at.

> **Should you run Postgres in Kubernetes at all?** Genuinely contested. Operators
> have made it far safer than it was, and the lab uses one so you understand what
> it does for you. A managed database is less operational work, and "we run our
> own Postgres in Kubernetes" should be a decision with a reason.

### Redis: two topologies, two answers

Module 18's honest conclusion was **two Redis topologies for two jobs**, because
`channels_redis` shards by group name and has no idea about cluster slots — a plain
`PUBLISH` on a Redis Cluster is broadcast to every node, giving you the right
answer at roughly triple the cost, forever.

| Data | Client | Topology | In Kubernetes |
|---|---|---|---|
| **Channel layer** (groups, `group_send`) | `channels_redis` | 3 independent Sentinel-managed instances | 3 small StatefulSets, `emptyDir`, PDB `maxUnavailable: 1` |
| **State** (Streams, `seq`, presence, buckets, tickets) | `redis.asyncio.RedisCluster` | Redis Cluster, 3 primaries + 3 replicas | StatefulSet with PVCs, `DoNotSchedule` spread, PDB `minAvailable: 5` |

**The channel-layer Redis is the one you should consider *not* persisting at all.**
It is pure transport. Losing it costs every client a reconnect and nothing else —
Module 09 moved durable delivery onto Streams precisely so this tier could be
disposable. Give it `emptyDir`, no AOF, and a fast restart.

**The state Redis is a correctness surface** and gets the opposite treatment:
PVCs, `noeviction` (the reason is argued in [`../infra/README.md`](../infra/)),
anti-affinity, and a PDB that protects the cluster quorum. Losing a slot here
loses sequence counters, presence, and the Streams replay window.

> **Same technology, opposite operational posture, because the data has opposite
> value.** If you take one thing from this section: decide per-dataset, not per-
> technology.

---

## Multi-region: what actually breaks

The honest section, because most multi-region chat designs are wrong.

### The latency floor is physics, and you should compute it

New York to London is **5,570 km** great-circle. Real fibre routes are roughly
1.4× the great-circle distance, so call it **7,800 km** of glass. Light in
single-mode fibre travels at `c/n` with `n ≈ 1.468`:

```
299,792 km/s ÷ 1.468        = 204,218 km/s
7,800 km ÷ 204,218 km/s     = 38.2 ms one way
                            = 76 ms round trip, FLOOR
```

Measured NYC↔London RTT on a good path is 70–80 ms. There is no CDN, no protocol
and no amount of money that gets below that number, and the lab simulates 90 ms
with `tc netem` to include realistic router hops.

**Why this matters for Pulse specifically:** Module 05's ordering guarantee comes
from **one sequencer per room** — a single `INCR room:{7}:seq`. A counter lives in
exactly one place. Cross-region, that place is 76+ ms away for half your users, and
no architecture removes the 76 ms; it only decides *who pays it and for what*.

### What breaks first: the sequencer

```
region A: alice sends → seq 501
region B: bob sends   → seq 501       (different message, same number)
```

Two regions with independent sequencers means the sequence number stops
identifying a message. Every client's gap detection
([Module 10](../10-ordering-and-delivery-semantics/)) breaks — permanently,
because a client that saw 501 will never accept the other 501. **Your entire
delivery guarantee assumed a single writer per room.**

### The three viable architectures

**1. Room affinity — recommended.** Each room has a **home region**, derived from
`Room.slug` by a hash so there is no lookup and no coordination. Writes to that
room are forwarded there; reads are served from a local replica.

```
alice (EU) sends to room.7 (home: US)
  → EU pod forwards the write to US over HTTP
  → US sequences (INCR room:{7}:seq) and publishes
  → replicated back to EU
  → alice's own message is confirmed ~204 ms later
```

Every guarantee survives. The cost is cross-region latency **on writes to
non-local rooms** — bearable for chat because sends are infrequent and rendered
optimistically ([Module 17](../17-nextjs-realtime-client/)), so the user's own
message appears instantly and the tick arrives later.

**2. Region-scoped rooms.** A room simply exists in one region and users connect
there. Simplest and correct; a globally distributed team has a bad experience.

**3. Active/active with CRDTs.** Replace total ordering with **causal** ordering —
Lamport timestamps or vector clocks in every message, conflicts resolved by a merge
function. Genuinely correct and genuinely expensive: you rewrite the protocol, the
client's ordering logic, and the storage model. That is what you build when
concurrent editing *is* the product. **For chat it is almost always
over-engineering.**

### What multi-region does not fix

- **Latency to the sequencer** for cross-region rooms. Unavoidable in options 1
  and 2; it is the 76 ms floor.
- **Cross-region data transfer cost.** Replicating every message to every region
  is real money, and it is the line item that dominates the model in the solution.
- **Split-brain during a partition.** Two regions that can't see each other and
  both accept writes to one room will diverge. Option 1 handles this by making the
  non-home region **read-only** for that room — a deliberate availability
  sacrifice, and the lab proves the sequences don't diverge after healing.

> **The honest recommendation:** most chat products do not need multi-region
> *write* capability. They need **edge-terminated sockets and local reads** —
> users connect to a nearby pod which holds the socket and forwards to a single
> home region. That is most of the latency benefit for a small fraction of the
> complexity, and the solution prices both.

---

## What's next

The lab ports the whole stack to `kind`, builds up a genuinely zero-drop rolling
deploy in three attempts so you can see what each piece contributes, proves a PDB
blocks a quorum-breaking drain, measures the replica-count knee against Module 07's
cost model, and then builds edge-terminated multi-region with room affinity —
including the partition drill that proves sequences don't diverge.

See you in [`lab.md`](./lab.md).
