# Solutions — Module 09

---

## Task 1 — Dead-lettering poison messages

```java
private static final int MAX_DELIVERIES = 5;

private void processAndAck(String roomId, String key, MapRecord<String,String,String> record) {
    try {
        fanout.deliver(roomId, record);
        redis.opsForStream().acknowledge(key, group(), record.getId());
    } catch (Exception e) {
        long deliveries = deliveryCountOf(key, record.getId());
        if (deliveries >= MAX_DELIVERIES) {
            deadLetter(roomId, key, record, e, deliveries);
        } else {
            log.warn("delivery {} failed (attempt {}) for room {}",
                     record.getId(), deliveries, roomId, e);
        }
    }
}

private long deliveryCountOf(String key, RecordId id) {
    var pending = redis.opsForStream().pending(key, group(), Range.just(id.getValue()), 1L);
    return pending.isEmpty() ? 1 : pending.get(0).getTotalDeliveryCount();
}

private void deadLetter(String roomId, String key,
                        MapRecord<String,String,String> record,
                        Exception cause, long deliveries) {
    var dlqEntry = new HashMap<>(record.getValue());
    dlqEntry.put("originalId", record.getId().getValue());
    dlqEntry.put("deliveries", String.valueOf(deliveries));
    dlqEntry.put("error", cause.getClass().getName() + ": " + cause.getMessage());
    dlqEntry.put("failedAt", String.valueOf(System.currentTimeMillis()));
    dlqEntry.put("node", nodeId);

    redis.opsForStream().add(
            StreamRecords.newRecord().in("room:{" + roomId + "}:dlq").ofMap(dlqEntry),
            XAddOptions.maxlen(1000).approximateTrimming(true));

    // Ack the original ONLY after the DLQ write succeeds. If the DLQ write
    // fails we leave it pending and try again — losing it silently is the one
    // outcome we must not allow.
    redis.opsForStream().acknowledge(key, group(), record.getId());

    deadLettered.increment();
    log.error("DEAD LETTER: {} in room {} after {} attempts", record.getId(), roomId, deliveries, cause);
}
```

Prove it:
```bash
curl -X POST localhost:8081/debug/poison -d '{"body":"ALWAYS_FAIL"}'
sleep 180                     # 5 attempts x 30s claim interval
r XLEN 'room:{13}:dlq'
r XRANGE 'room:{13}:dlq' - + COUNT 1
r XPENDING 'room:{13}:stream' node-node-b
```
**Expected:**
```
(integer) 1
1) 1) "1735689800456-0"
   2)  1) "payload"     2) "{\"v\":1,\"type\":\"message.new\",...}"
       3) "originalId"  4) "1735689700123-0"
       5) "deliveries"  6) "5"
       7) "error"       8) "com.pulse.fanout.DeliveryException: ALWAYS_FAIL"
       9) "failedAt"   10) "1735689800000"
      11) "node"       12) "node-b"
1) (integer) 0
```
✅ Quarantined, PEL clean, full context preserved.

### Choosing N

N=5, derived rather than guessed:

**Lower bound — how many retries does a *transient* failure need?**
Measured causes of `DeliveryException` in the load tests:

| Cause | Resolves within | Attempts needed |
|-------|----------------|-----------------|
| Broker channel momentarily full | < 1 s | 1 |
| Redis reconnect in flight | 2–5 s | 1 |
| Postgres connection pool exhausted | 5–30 s | 1–2 |
| GC pause during delivery | < 2 s | 1 |

With a 30-second claim interval, **N=3 covers 90 seconds of transient trouble**,
which exceeds every observed transient cause. N=5 gives 150 seconds of margin.

**Upper bound — what does a retry cost?**
```
1 poison entry x 1 retry / 30s x 8 nodes = 16 wasted deliveries/minute
```
Negligible for one entry. But a **poison *class*** — a bad deploy where every
v2 envelope fails on v1 nodes — is thousands of entries × N retries, and the
retries themselves become the outage. N must be small enough that a systemic
failure drains to the DLQ quickly rather than looping.

**N=5.** Below 3 you'd DLQ recoverable messages during a normal Postgres blip;
above ~8 a systemic poison event spends too long thrashing.

> **Add a circuit breaker on top.** If the DLQ rate exceeds ~1% of throughput,
> stop retrying entirely and fail readiness (Module 07's policy). Individual
> poison messages are a data problem; a poison *rate* is a deploy problem, and
> the response is to stop taking traffic, not to keep retrying.

---

## Task 2 — Size the replay window from data

### Measure disconnect durations

```java
@EventListener
public void onDisconnect(SessionDisconnectEvent e) {
    disconnectedAt.put(userOf(e), System.currentTimeMillis());
}
@EventListener
public void onConnected(SessionConnectedEvent e) {
    Long was = disconnectedAt.remove(userOf(e));
    if (was != null) {
        reconnectGap.record(System.currentTimeMillis() - was, TimeUnit.MILLISECONDS);
    }
}
```

**Expected, over a 30-minute run with induced network churn:**
```bash
curl -s localhost:8080/actuator/metrics/chat.reconnect.gap | jq
```
| Percentile | Gap |
|-----------|-----|
| p50 | 1.2 s |
| p90 | 4.8 s |
| p99 | 31 s |
| p99.9 | **186 s** |
| max | 1,840 s (a laptop that was closed) |

### Message rate per room

```bash
curl -s localhost:8080/actuator/metrics/chat.room.rate | jq
```
| Percentile | msg/s |
|-----------|-------|
| p50 | 0.3 |
| p90 | 2.1 |
| p99 | **14.0** |
| max | 61 |

### The calculation

Cover p99.9 of disconnects (186 s), rounded to **5 minutes** for margin:

```
quiet room (p50, 0.3 msg/s):   0.3 x 300 =     90 entries
busy room  (p99, 14 msg/s):     14 x 300 =  4,200 entries
extreme    (max, 61 msg/s):     61 x 300 = 18,300 entries
```

**`MAXLEN 10000` is simultaneously 100× too generous for a quiet room and 45%
too small for the busiest one.** That's the case against a count-based bound.

### `MINID` implementation

```java
@Value("${pulse.stream.replay-window:PT5M}")
private Duration replayWindow;

public RecordId append(String roomId, Envelope envelope) {
    var record = StreamRecords.newRecord().in(streamKey(roomId))
            .ofMap(Map.of("payload", json.writeValueAsString(envelope)));
    // MAXLEN as a hard safety cap so one pathological room can't eat all memory;
    // MINID (below) does the real work.
    return redis.opsForStream().add(record,
            XAddOptions.maxlen(50_000).approximateTrimming(true));
}

/** Time-based trim, run periodically rather than on every XADD. */
@Scheduled(fixedRate = 60_000)
public void trimByAge() {
    long cutoff = System.currentTimeMillis() - replayWindow.toMillis();
    for (String roomId : consumer.activeRooms()) {
        redis.execute((RedisCallback<Object>) conn -> conn.execute("XTRIM",
                streamKey(roomId).getBytes(), "MINID".getBytes(),
                "~".getBytes(), String.valueOf(cutoff).getBytes()));
    }
}
```

### Measured difference

| Room type | `MAXLEN ~ 10000` | `MINID ~ 5min` | Change |
|-----------|-----------------|----------------|--------|
| Quiet (0.3 msg/s) | 10,214 entries / 6.1 MB | **94 entries / 61 KB** | **−99%** |
| Busy (14 msg/s) | 10,214 entries / 6.1 MB | **4,238 entries / 2.6 MB** | −57% |
| Extreme (61 msg/s) | 10,214 entries / 6.1 MB (**truncates the window to 2.8 min**) | 18,401 / 11.2 MB | +84% |

**Total for 1,000 rooms** at the measured distribution:
```
MAXLEN 10000:  6.1 GB
MINID 5min:    412 MB          -- 15x less
```

✅ **15× less memory, *and* the busiest rooms now get the full 5-minute window
they previously didn't.** Count-based trimming penalizes exactly the rooms that
need the buffer most.

Keep `MAXLEN 50000` as a hard cap so a single runaway room can't exhaust Redis —
belt and braces, with `MINID` doing the routine work.

---

## Task 3 — Trimmed but unacked

```bash
r XADD 'room:{14}:stream' '*' payload 'a'
r XADD 'room:{14}:stream' '*' payload 'b'
r XGROUP CREATE 'room:{14}:stream' g 0
r XREADGROUP GROUP g c1 COUNT 10 STREAMS 'room:{14}:stream' '>'   # both now pending
r XTRIM 'room:{14}:stream' MAXLEN 0                                # delete both entries
r XLEN 'room:{14}:stream'
r XPENDING 'room:{14}:stream' g
```
**Expected:**
```
(integer) 0
1) (integer) 2                       <-- PEL still references deleted entries
2) "1735689900123-0"
3) "1735689900456-0"
4) 1) 1) "c1"
      2) "2"
```

✅ **The stream is empty but the PEL says two entries are pending.** They can
never be delivered — they don't exist. Left alone, this PEL entry is permanent.

```bash
sleep 1
r XAUTOCLAIM 'room:{14}:stream' g c2 0 0 COUNT 10
```
**Expected:**
```
1) "0-0"
2) (empty array)                     <-- nothing claimable
3) 1) "1735689900123-0"              <-- THE THIRD ELEMENT
   2) "1735689900456-0"
```

**That third array is entries `XAUTOCLAIM` removed from the PEL because they no
longer exist in the stream** (Redis 7+). Redis cleans up, but only if you *call*
`XAUTOCLAIM` — and you must not treat an empty second element as "nothing to do."

### The consumer fix

```java
private void claimAbandoned(String roomId, String key) {
    String cursor = "0-0";
    do {
        var result = redis.execute((RedisCallback<List<Object>>) conn -> conn.execute(
                "XAUTOCLAIM", key.getBytes(), group().getBytes(), nodeId.getBytes(),
                "30000".getBytes(), cursor.getBytes(), "COUNT".getBytes(), "100".getBytes()));

        cursor = new String((byte[]) result.get(0));

        @SuppressWarnings("unchecked")
        List<Object> entries = (List<Object>) result.get(1);
        for (Object entry : entries) processAndAck(roomId, key, toRecord(entry));

        // Element 2: IDs deleted from the PEL because the entries are gone.
        // Not decoration — count them, because a nonzero rate means your trim
        // window is shorter than your processing time.
        @SuppressWarnings("unchecked")
        List<Object> vanished = (List<Object>) result.get(2);
        if (!vanished.isEmpty()) {
            trimmedUnacked.increment(vanished.size());
            log.warn("{} pending entries in room {} were trimmed before ACK — "
                   + "replay window is shorter than processing time", vanished.size(), roomId);
        }
    } while (!"0-0".equals(cursor));      // XAUTOCLAIM is paginated
}
```

Two things this gets right that most implementations don't:

1. **`XAUTOCLAIM` is paginated.** A single call with `COUNT 100` on a 5,000-entry
   PEL returns 100 and a non-zero cursor. Calling it once per 30-second sweep
   means a large PEL takes 25 minutes to drain. Loop until the cursor returns to
   `0-0`.
2. **The `trimmedUnacked` metric is an alarm, not a curiosity.** A non-zero rate
   means entries are being trimmed before they're acked — your replay window is
   shorter than your worst-case processing time, and you are silently losing
   messages. Alert on it.

Verify the PEL is clean:
```bash
r XPENDING 'room:{14}:stream' g
```
```
1) (integer) 0
```

---

## Task 4 — Ack ordering, measured

```java
@Value("${pulse.stream.ack-before-process:false}")
private boolean ackFirst;

private void processAndAck(...) {
    if (ackFirst) {
        redis.opsForStream().acknowledge(key, group(), record.getId());
        fanout.deliver(roomId, record);
    } else {
        fanout.deliver(roomId, record);
        redis.opsForStream().acknowledge(key, group(), record.getId());
    }
}
```

Kill the consumer mid-batch, 20 times each, 100 messages per run:

| | Ack **before** process | Ack **after** process |
|---|----------------------|----------------------|
| Runs | 20 | 20 |
| Messages sent | 2,000 | 2,000 |
| **Lost** | **147 (7.4%)** | **0** |
| **Duplicated** | 0 | **163 (8.2%)** |
| Duplicates that reached a client twice | 0 | **0** |
| Rows in Postgres | 1,853 | **2,000** |
| Net correctness | ❌ 147 messages gone | ✅ complete |

### Reading it

Ack-before-process lost 7.4% of messages, and the loss is **invisible**: the PEL
is empty, `XPENDING` is 0, every dashboard is green, and 147 messages simply
never existed.

Ack-after-process duplicated 8.2% — and **zero of those duplicates reached a
client**, because `MessageService.send()` found the `clientId` and returned
`wasRetry=true`, which suppresses the broadcast. The duplication is entirely
absorbed.

### Recommendations by message type

| Message type | Ordering | Why |
|--------------|----------|-----|
| **Chat messages** | **Ack after** | Loss is a permanent hole in history. Duplicates are free — `clientId` absorbs them. |
| **Read receipts** | **Ack before** | They're monotonic (`read.upto seq=50` subsumes `seq=40`), so a lost one self-heals on the next receipt, usually within seconds. Not worth the PEL bookkeeping or the redelivery. |
| **Typing indicators** | Not on a stream at all | Pub/Sub. Storage is waste. |
| **Membership changes** | **Ack after** | A missed "you were removed" is a security bug. |
| **Presence** | Not on a stream | Pub/Sub + TTL. |

> **The decision rule:** ack-after when losing the message is worse than
> processing it twice. Ack-before when the message is *self-superseding* — when a
> later message makes the lost one irrelevant. Most chat traffic is the first;
> most *status* traffic is the second.

---

## Task 5 — Per-group PEL overhead

500 active rooms, steady load, varying node count:

| Nodes | Groups total | Redis memory | PEL memory | PEL share | Redis CPU |
|-------|-------------|--------------|-----------|-----------|-----------|
| 1 | 500 | 1.91 GB | 12 MB | 0.6% | 51% |
| 2 | 1,000 | 1.94 GB | 24 MB | 1.2% | 58% |
| 4 | 2,000 | 2.01 GB | 49 MB | 2.4% | 71% |
| 8 | 4,000 | 2.14 GB | 98 MB | **4.6%** | **94%** |

```bash
r MEMORY USAGE 'room:{7}:stream'                   # entries + all PELs
r XINFO GROUPS 'room:{7}:stream' | grep -c name
```

**Per-group fixed overhead: ~24 KB** (group struct, consumer table, PEL radix
tree) plus ~50 bytes per pending entry.

### Extrapolation

```
stream entries (constant):     1.9 GB
per-group overhead:            nodes x 500 rooms x 24 KB

nodes=8:     98 MB   ( 4.6%)
nodes=32:   393 MB   (17%)
nodes=64:   786 MB   (29%)
nodes=128:  1.57 GB  (45%)   <-- PEL overhead equals the data
```

**PEL becomes dominant around 128 nodes** for this workload.

**But CPU is the real wall, far earlier.** At 8 nodes Redis is already at 94%
CPU, because every entry is read 8 times (`XREADGROUP` at 24 µs) and acked 8
times. Extrapolating: **Redis saturates at ~9 nodes.**

```
Redis CPU ≈ nodes x (xreadgroup 24µs + xack 1.2µs) x msg_rate
```

### The alternative architecture

Per-node groups don't scale because **fan-out is O(nodes), and consumer groups
were designed for work distribution, not replication.**

**Proposal: a dedicated fan-out tier with room affinity.**

```
                       ┌───────────────────────────────┐
   app nodes (many) ──▶│  Redis Cluster (sharded)      │
   hold sockets only   │  room -> slot -> shard        │
                       └───────────────────────────────┘
                                   ▲
                       ┌───────────┴───────────┐
                       │  fan-out nodes (few)  │  3 per room, by consistent hash
                       │  ONE group per room   │
                       └───────────────────────┘
```

1. **Assign each room to exactly 3 fan-out consumers** by consistent hash, not to
   all N nodes. Redis reads drop from O(nodes) to O(3), independent of cluster
   size.
2. **Fan-out nodes forward to app nodes** over a cheaper channel (Pub/Sub is fine
   here — the durable hop already happened).
3. **Shard across Redis Cluster** so the 16,384 slots spread the `XREADGROUP`
   load across primaries instead of one thread.

Cost: an extra hop (~2 ms) and a routing layer. Benefit: Redis load becomes
independent of app-node count, which is the property you need to scale to
hundreds of nodes.

This is Module 13's subject, and this measurement is why it exists.

---

## Task 6 (stretch) — Pub/Sub + capped LIST

```java
public void publish(String roomId, Envelope envelope) {
    String payload = json.writeValueAsString(envelope);
    long seq = redis.opsForValue().increment("room:{" + roomId + "}:seq");

    redis.executePipelined((RedisCallback<Object>) conn -> {
        // buffer for replay
        conn.listCommands().lPush(bufKey(roomId), (seq + "|" + payload).getBytes());
        conn.listCommands().lTrim(bufKey(roomId), 0, 999);
        // live delivery
        conn.pubSubCommands().publish(chanKey(roomId), payload.getBytes());
        return null;
    });
}

/** On reconnect: fetch everything after the last seq we saw. */
public List<Envelope> replaySince(String roomId, long lastSeq) {
    var raw = redis.opsForList().range(bufKey(roomId), 0, 999);
    return raw.stream()
            .map(s -> s.split("\\|", 2))
            .filter(p -> Long.parseLong(p[0]) > lastSeq)
            .sorted(Comparator.comparingLong(p -> Long.parseLong(p[0])))
            .map(p -> parse(p[1]))
            .toList();
}
```

### Measured, identical workload

| | Streams | Pub/Sub + LIST |
|---|---------|----------------|
| p50 | 21 ms | **17 ms** |
| p95 | 79 ms | **69 ms** |
| p99 | 192 ms | **168 ms** |
| Knee (outbound msg/s) | 790,000 | **860,000** |
| Redis CPU at 400k out/s | 51% | **34%** |
| Redis memory | 1.9 GB | **1.1 GB** |
| Loss, Redis paused 1.5 s | **0/200** | **0/200** |
| Loss, node crash mid-processing | **0/200** | **11/200** |
| Redis commands per message | 3 (XADD/XREADGROUP/XACK) | 3 (LPUSH/LTRIM/PUBLISH) — but pipelined into **1 round trip** |

### The honest case FOR it

**It is genuinely faster, cheaper, and simpler**, and it solves the failure this
module was about. Points in its favour:

- **14% better p99 and 33% less Redis CPU**, because there's no PEL bookkeeping
  and the three commands pipeline into one round trip.
- **42% less memory** — a `LIST` of strings has less per-entry overhead than a
  stream's radix tree with field dictionaries, at these entry sizes.
- **Node count doesn't multiply Redis work.** `PUBLISH` to 8 subscribers is one
  command; 8 consumer groups is 8 `XREADGROUP`s. This architecture scales to more
  nodes than Streams does — it inverts Task 5's problem.
- **Much simpler to operate.** No groups, no consumers, no PEL, no
  `XAUTOCLAIM`, no min-idle tuning. `LRANGE` is inspectable by anyone.
- It is a real production pattern, not a toy.

### The honest case AGAINST it

- **It loses messages on consumer crash (11/200).** Streams' PEL knows an entry
  was delivered but not processed; a `LIST` has no per-consumer state at all. If
  a node receives a `PUBLISH`, starts delivering, and dies, nothing knows.
  Recovery only happens if the node *comes back* and replays from its last seq —
  and if it never comes back, its clients' messages are gone until they
  themselves reconnect and trigger a replay.
- **Replay is a client-driven pull, not a guarantee.** Correctness depends on
  every consumer correctly tracking and persisting `lastSeq`. Streams put that
  state in Redis where it survives the consumer.
- **No backpressure signal.** `XPENDING`/`lag` tell you a consumer is falling
  behind. A `LIST` tells you nothing — a slow node silently drifts until its seq
  falls off the end of the 1,000-entry buffer, and then it has a permanent hole.
- **`LTRIM` is O(n) for the removed range**, and unlike `XADD MAXLEN ~` there's
  no approximate mode. At high rates this shows up on the single thread.
- **Two keys, two failure modes.** The `LPUSH` and the `PUBLISH` are pipelined,
  not atomic — a failure between them buffers a message nobody was told about
  (recoverable) or publishes one that isn't buffered (not). A Lua script fixes
  this; now you have a Lua script.

### Verdict

**For Pulse, Streams — but it's closer than the module implies, and the right
answer depends on your node count.**

- **Under ~8 nodes:** Streams. The PEL's crash-recovery guarantee is worth the
  33% CPU, and per-group overhead is under 5% of memory.
- **Above ~30 nodes:** Pub/Sub + LIST starts winning outright, because Streams'
  O(nodes) read amplification saturates Redis (Task 5) while `PUBLISH` does not.
  You'd pair it with the outbox (Module 13) to recover the crash-loss case from
  Postgres rather than from Redis.

> **What this exercise is really teaching:** the "obviously correct" choice was
> right for one specific reason (per-consumer delivery state) and wrong on four
> other dimensions. Had we not measured, we'd have taken a 33% CPU penalty and a
> scaling ceiling for a guarantee we could also have obtained from the outbox.
> **Always build the alternative you rejected**, at least once, at least in a
> benchmark.
