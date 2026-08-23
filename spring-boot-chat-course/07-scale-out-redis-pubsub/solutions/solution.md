# Solutions — Module 07

---

## Task 1 — Subscription amplification

```bash
for N in 1 2 4 8; do
  ./code/run-instances.sh "$N"
  k6 run -e ROOMS=1000 -e SEND_EVERY=10000 --vus 8000 --duration 3m code/pulse-load.js &
  sleep 120
  echo "=== $N instances ==="
  docker exec pulse-redis redis-cli PUBSUB CHANNELS 'pulse.room.*' | wc -l
  for p in $(seq 8080 $((8079+N))); do
    curl -s "localhost:$p/actuator/metrics/fanout.subscribed.rooms" | jq '.measurements[0].value'
  done
  docker exec pulse-redis redis-cli INFO stats | grep -E 'total_net_(in|out)put_bytes'
  wait
done
```

### Results — 1,000 rooms, 8,000 users, 800 inbound msg/s

| Instances | Distinct channels | Channels **per instance** | Redis out/in ratio | Redis out (Mbit/s) |
|-----------|-------------------|---------------------------|--------------------|--------------------|
| 1 | 1,000 | 1,000 | 1.0× | 3.1 |
| 2 | 1,000 | 998 | **2.0×** | 6.2 |
| 4 | 1,000 | 1,000 | **4.0×** | 12.4 |
| 8 | 1,000 | 1,000 | **8.0×** | 24.8 |

```
Redis outbound
   Mbit/s │                                          ●  (8)
      25  │                                       ╱
      20  │                                    ╱
      15  │                              ● (4)
      10  │                      ╱
       5  │      ● (2)     ╱
         ●(1)  ╱
          └────┬────┬────┬────┬────┬────┬────┬────  instances
               1    2    4    8   16   32   64
```

**Perfectly linear, and that's the problem.** Note the third column: with 8,000
users spread randomly over 1,000 rooms, *every* instance has a subscriber in
*every* room. Adding instances doesn't divide the work — it multiplies Redis's.

### Extrapolation to 1 Gbit/s

```
per-instance outbound = 3.1 Mbit/s
1000 Mbit/s / 3.1 Mbit/s = 322 instances     (naive)
```

But that ignores payload growth and assumes perfect efficiency. With a practical
70% ceiling on a 1 GbE link:

```
700 Mbit/s / 3.1 = ~225 instances
```

**In practice you hit trouble far earlier**, around 30–50 instances, because:
- Redis is single-threaded for command execution. `PUBLISH` to 50 subscribers is
  50 socket writes on one thread. At 800 msg/s × 50 = 40,000 writes/s it's fine;
  at 8,000 msg/s × 50 = 400,000 writes/s it is not.
- `INFO commandstats` shows `usec_per_call` for `publish` climbing with
  subscriber count — measure it.

```bash
docker exec pulse-redis redis-cli INFO commandstats | grep publish
```
```
cmdstat_publish:calls=144000,usec=2016000,usec_per_call=14.00     # 8 instances
cmdstat_publish:calls=144000,usec=252000,usec_per_call=1.75       # 1 instance
```

**8× the subscribers, 8× the per-call cost.** Redis's single thread is the wall,
not the network.

### The fixes (Module 13)

1. **Sharded Pub/Sub** (`SSUBSCRIBE`/`SPUBLISH`) — routes by hash slot so in a
   cluster only the node owning that slot does the fan-out. Turns one thread's
   problem into N threads' problem.
2. **Room affinity** — assign each room to a subset of instances by consistent
   hash, so a room's message goes to 3 instances, not 30. Requires the LB (or a
   routing layer) to place users accordingly, or an internal forward.
3. **Fan-out on read** for large rooms — stop pushing entirely.

---

## Task 2 — The split-view hazard

### Reproduce it

```java
// Debug hook
@MessageMapping("/debug/break-fanout")
public void breakFanout(@Payload BreakRequest r) { fanout.failNextN(r.count()); }
```
```java
public void publish(String roomId, Envelope envelope) {
    if (failCounter.getAndDecrement() > 0)
        throw new FanoutException("simulated redis failure", null);
    // ...
}
```

```bash
# alice on node-a, bob on node-b, both in room.7
curl -X POST localhost:8080/debug/break-fanout -d '{"count":5}'
# alice sends 5 messages
```

**Expected:**
```
alice (node-a): sees all 5
bob   (node-b): sees 0
node-a log: FanoutException x5, and the SEND still returned successfully
```

Permanent divergence. Bob's history has a hole; alice has no idea.

### The fix: publish first, deliver locally from the subscription

Invert the order and remove the special-casing:

```java
public void send(...) {
    var result = messages.send(roomId, principal.getName(), create);
    var envelope = Envelope.of("message.new", roomId, json.valueToTree(result.message()));

    template.convertAndSendToUser(principal.getName(), "/queue/ack", ackEnvelope(result));
    if (result.wasRetry()) return;

    // Publish ONLY. Do not deliver locally here.
    fanout.publish(roomId, envelope);       // throws -> the client gets an error
}
```
```java
@Override
public void onMessage(Message message, byte[] pattern) {
    var wrapper = json.readValue(message.getBody(), Wrapper.class);
    // Deliver locally REGARDLESS of origin — including our own publishes.
    broker.convertAndSend("/topic/room." + wrapper.envelope().room(), wrapper.envelope());
}
```

Now Redis is the **single source of ordering and delivery**. Either the publish
succeeds and everyone (including local subscribers) gets it via the subscription,
or it fails and nobody does — and the sender gets an error frame they can retry
with the same `clientId`.

**Expected after the fix:**
```
alice: sees 0, receives 5 error frames
bob:   sees 0
```
Consistent. Alice retries; the `clientId` makes it safe.

### What you traded away

| | Before (local-first) | After (publish-only) |
|---|---------------------|---------------------|
| Same-node p50 latency | **0.2 ms** | 3.1 ms |
| Consistency on publish failure | ❌ split view | ✅ all-or-nothing |
| Ordering | per-node, can differ | **single order for everyone** |
| Redis outbound | inbound × (instances−1) | inbound × instances |

**You traded ~3 ms of same-node latency and one extra Redis delivery for
consistency and a global order.** For chat that's clearly correct — a hole in
someone's history is a bug users report, 3 ms is not.

The ordering benefit is the underrated one: with local-first, a same-node
recipient can see message B before message A while a remote recipient sees the
reverse. With publish-only, Redis's arrival order is *the* order for everybody.

**What this still doesn't fix:** the message is already in Postgres when the
publish fails. Persisted but not delivered. Only the **transactional outbox**
(Module 13) closes that, and it's a real remaining gap — note it.

---

## Task 3 — The listener pool

Add the gauge first:

```java
Gauge.builder("fanout.listener.queued", executor,
              e -> e.getThreadPoolExecutor().getQueue().size()).register(registry);
Gauge.builder("fanout.listener.active", executor,
              ThreadPoolTaskExecutor::getActiveCount).register(registry);
```

### Saturation point — 8 core threads, 500-byte messages

| Inbound fan-out msg/s | `listener.queued` | `listener.active` | p99 |
|----------------------|-------------------|-------------------|-----|
| 20,000 | 0 | 2 | 18 ms |
| 60,000 | 0 (spikes 30) | 6 | 41 ms |
| 100,000 | **sustained 400–2,000** | 8 (pinned) | 380 ms |
| 140,000 | climbing to capacity | 8 | 2,100 ms |

**Saturation: ~85,000 inbound fan-out messages/second** with 8 core threads.

### What happens when the queue fills

```
org.springframework.core.task.TaskRejectedException: Executor
[ThreadPoolExecutor@1a2b[Running, pool size = 32, active threads = 32,
queued tasks = 10000, completed tasks = 4821993]] did not accept task
```

The message is **dropped**, and `RedisMessageListenerContainer` catches the
rejection, logs it, and continues.

### Is this better or worse than the outbound channel's failure?

**Strictly worse, for two reasons.**

| | `clientOutboundChannel` rejection | Listener pool rejection |
|---|----------------------------------|------------------------|
| Blast radius | **One recipient** misses one message | **Every local subscriber of that room** misses it |
| Redelivery possible? | No | No (Pub/Sub) |
| Visible to sender? | No | No |
| Correlates with load on | This node's fan-out | Cluster-wide message rate |

The outbound channel drops a *delivery*. The listener pool drops a *message* —
before it ever reaches the local broker. One rejection there costs you N
deliveries, where N is the local subscriber count for that room.

**So it must be sized more generously than the outbound channel, not less.**
The lab's `corePoolSize(8)` is too small; 32 is a better default, since these
threads are doing deserialization plus a broker handoff, not blocking I/O.

**Better still: don't queue, apply backpressure.**

```java
executor.setRejectedExecutionHandler(new ThreadPoolExecutor.CallerRunsPolicy());
```

With `CallerRunsPolicy`, the rejection is absorbed by the **Redis listener
thread** doing the work itself. That thread stops reading from the Redis socket,
Redis's `client-output-buffer-limit pubsub` starts filling, and eventually Redis
disconnects the subscriber — which is loud, visible, and recoverable, instead of
silently dropping messages.

```
Redis log: "Client id=42 scheduled to be closed ASAP for overcoming of output buffer limits"
```

That log line is infinitely more useful than a silent drop.

---

## Task 4 — Poison messages, bounded

### The catch is necessary

```bash
docker exec pulse-redis redis-cli PUBLISH pulse.room.7 'not json at all'
```

**Without the catch:**
```
com.fasterxml.jackson.core.JsonParseException: Unrecognized token 'not'
	at ...RedisMessageListenerContainer$DispatchMessageListener.onMessage
```
The task dies. With `CallerRunsPolicy` or a small pool, repeated poison can kill
listener threads faster than they're replaced — and **all fan-out on that node
silently stops** while the node stays "healthy."

**With the catch:** logged, dropped, listener survives. Prove it by publishing a
valid message immediately after — it arrives.

### The catch is insufficient

Three ways it fails:

1. **`OutOfMemoryError` is an `Error`, not an `Exception`** — `catch (Exception)`
   doesn't catch it, and the thread dies anyway. A 500 MB payload published to a
   room does this.
2. **Every message is poison.** If a bad deploy publishes a v2 envelope that v1
   nodes can't parse, you log at ERROR 100,000 times per second. The logging
   itself becomes the outage — disk fills, log shipper backs up, and the real
   errors are unfindable.
3. **No signal.** A node dropping 100% of fan-out reports `UP`. The load balancer
   keeps sending it clients who then receive nothing.

### The bounded policy

```java
@Component
public class FanoutFailurePolicy {

    private final Map<String, AtomicInteger> consecutiveFailures = new ConcurrentHashMap<>();
    private final Set<String> circuitOpen = ConcurrentHashMap.newKeySet();
    private final RateLimiter errorLog = RateLimiter.create(1.0);   // 1 log/sec
    private final AtomicLong totalFailures = new AtomicLong();
    private final AtomicLong totalMessages = new AtomicLong();

    private static final int THRESHOLD = 20;

    public boolean shouldProcess(String roomId) {
        return !circuitOpen.contains(roomId);
    }

    public void recordSuccess(String roomId) {
        totalMessages.incrementAndGet();
        consecutiveFailures.remove(roomId);
        circuitOpen.remove(roomId);
    }

    public void recordFailure(String roomId, Throwable t) {
        totalMessages.incrementAndGet();
        totalFailures.incrementAndGet();

        int n = consecutiveFailures.computeIfAbsent(roomId, k -> new AtomicInteger())
                                   .incrementAndGet();
        if (errorLog.tryAcquire()) {                     // <-- bounded logging
            log.error("fanout failure {} for room {} ({} consecutive)",
                      t.getClass().getSimpleName(), roomId, n, t);
        }
        if (n >= THRESHOLD) {
            circuitOpen.add(roomId);
            log.error("CIRCUIT OPEN for room {} after {} consecutive failures", roomId, n);
        }
    }

    /** Fraction of ALL fanout messages that failed, over the recent window. */
    public double failureRate() {
        long total = totalMessages.get();
        return total == 0 ? 0.0 : (double) totalFailures.get() / total;
    }

    public int openCircuits() { return circuitOpen.size(); }
}
```

Wire it to **readiness, not liveness** (Module 02's lesson):

```java
@Component("fanoutHealth")
public class FanoutHealthIndicator implements HealthIndicator {
    @Override
    public Health health() {
        double rate = policy.failureRate();
        var b = (rate > 0.05 || policy.openCircuits() > 10) ? Health.down() : Health.up();
        return b.withDetail("failureRate", rate)
                .withDetail("openCircuits", policy.openCircuits())
                .build();
    }
}
```
```yaml
management.endpoint.health.group.readiness.include: readinessState,db,redis,fanoutHealth
```

And catch `Throwable`, not `Exception`, at the listener boundary — while
**rethrowing the ones you must not swallow**:

```java
} catch (VirtualMachineError e) {
    throw e;                                  // OOM, StackOverflow: do not pretend
} catch (Throwable t) {
    policy.recordFailure(roomId, t);
}
```

**Expected under a 100%-poison flood:**
```
ERROR fanout failure JsonParseException for room 7 (1 consecutive)
ERROR fanout failure JsonParseException for room 7 (18 consecutive)     [1/sec]
ERROR CIRCUIT OPEN for room 7 after 20 consecutive failures
```
```bash
curl -s localhost:8080/actuator/health/readiness | jq -r .status
```
```
DOWN
```
✅ nginx removes the node from rotation, one log line per second instead of
100,000, and the circuit stops burning CPU on messages that will never parse.

---

## Task 5 — What stickiness costs

Measured with 10,000 connected clients, then changing the upstream list:

| Strategy | Clients moved on **add** 3rd node | Clients moved on **remove** 1 node | Even distribution? |
|----------|----------------------------------|-----------------------------------|--------------------|
| No stickiness (round robin) | n/a (already arbitrary) | 3,333 (the dead node's) | ✅ perfect |
| `ip_hash` | **6,712 (67%)** | 5,104 (51%) | ❌ NAT clumping: 3 IPs held 41% of clients |
| `hash $cookie consistent` | **3,401 (34%)** | 3,333 (33%) | ✅ within 4% |

### Reading this

**`ip_hash` remaps far more than necessary** because nginx's `ip_hash` is a
modulo scheme, not consistent hashing: changing the server count changes almost
every mapping. It also clumps badly — in the test, three carrier-NAT source IPs
accounted for 41% of clients, all pinned to one node.

**Consistent hashing moves ~1/n**, which is the theoretical minimum. The 3,333 on
removal is unavoidable: those clients' node is gone.

### Is stickiness worth it for Pulse?

**Yes, but weakly — and it's worth being precise about why.**

What actually breaks without it:

1. **Nothing about message delivery.** The backplane makes any node able to serve
   any user. This is the important finding: stickiness is *not* a correctness
   requirement once you have a backplane.
2. **Reconnect cost.** A client landing on a new node re-authenticates,
   re-subscribes, and warms a cold dedup cache. Measured: **+180 ms** on
   reconnect vs +40 ms to the same node.
3. **Per-node caches lose their value.** Room membership and permission caches
   are per-node; without affinity every node caches everything.
4. **Debuggability.** "Which node has this user?" becomes "all of them, over
   time."

What stickiness costs:

1. **Rolling deploys disconnect everyone on the drained node** — you can't move a
   socket. (Module 18.)
2. **Uneven load.** A node that happens to get chatty users stays hot; you can't
   rebalance without disconnecting.
3. **Failure amplification.** Losing a node means 1/n of users reconnect
   simultaneously — the thundering herd.

**Recommendation: cookie-based consistent hashing, and treat it as an
optimization rather than a requirement.** Design every code path to work without
it. That way, when Module 19's rolling deploy needs to move clients, nothing
breaks except latency.

---

## Task 6 (stretch) — Redis backplane vs RabbitMQ relay

Identical k6 workload: 20,000 connections, 100 rooms, 200 members, `SEND_EVERY=10000`.

| | Redis backplane | RabbitMQ STOMP relay |
|---|-----------------|---------------------|
| p50 fan-out | **17 ms** | 24 ms |
| p95 | **68 ms** | 91 ms |
| p99 | **161 ms** | 214 ms |
| Broker CPU at 400k out msg/s | **58%** (1 core, pinned) | 190% (2 cores) |
| Broker RSS | **410 MB** | 1.8 GB |
| Messages lost, 1.5 s `docker pause` | **29 / 200** | **0 / 200** |
| Messages lost, broker killed + restarted | 200 / 200 (during downtime) | 0 / 200 (durable queues) |
| Application code required | ~180 lines | ~10 lines of config |
| Extra hops per message | 1 | 2 |

### The ADR paragraph

> **Decision: use Redis Pub/Sub + Streams as the fan-out backplane, not the
> RabbitMQ STOMP relay.**
>
> RabbitMQ measurably wins on the thing that matters most — **zero message loss
> across a broker pause, versus 14.5% for Pub/Sub** — and requires roughly ten
> lines of configuration against our ~180 lines of relay code. That is a serious
> argument and we are not dismissing it. We are choosing Redis for three
> reasons. First, **Pulse already operates Redis** for presence, rate limiting,
> unread counts and dedup; RabbitMQ would be an additional stateful system with
> its own clustering model, its own partition-handling policy, and its own
> on-call runbook, and it must earn that cost by doing something Redis cannot.
> Second, **Redis Streams close the durability gap** (Module 09) while keeping
> the delivery mechanics explicit and inspectable — consumer groups, a visible
> pending-entries list, and `XAUTOCLAIM` recovery are all things we can reason
> about with `redis-cli`, where the relay's guarantees are inside the broker.
> Third, Redis costs us **less than half the broker CPU and a quarter of the
> memory** at our target rate, and one fewer network hop, worth 7 ms at p50 and
> 53 ms at p99.
>
> **We would switch to RabbitMQ (or a managed equivalent) if:** we needed durable
> per-user queues for offline delivery at a scale where Streams' memory cost
> became prohibitive; if we needed real STOMP `ACK`/`NACK` semantics end to end
> rather than application-level acks; or if the team's operational familiarity
> with RabbitMQ meaningfully exceeded its familiarity with Redis. The first is
> the most likely trigger and we should revisit at 10× current volume.

> **A note on the fairness of this comparison:** the "0 / 200 lost" for RabbitMQ
> is with durable queues and publisher confirms enabled, which costs it
> throughput — some of the p99 gap is us paying for durability on one side and
> not the other. Comparing Redis **Streams** (Module 09) against RabbitMQ would
> be the honest like-for-like, and the gap narrows considerably. Redo this
> measurement after Module 09.
