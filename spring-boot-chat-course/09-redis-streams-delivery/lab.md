# Lab 09 — Stop Losing Messages

**You'll:** convert the backplane to Streams with per-node consumer groups,
re-run Module 07's loss test and lose nothing, kill a consumer mid-flight and
watch `XAUTOCLAIM` recover it, prove idempotency handles the duplicate, and
measure what durability costs.

⏱️ ~100 min. Work in `spring-boot-chat-course/apps/pulse`.

```bash
alias r='docker exec -i pulse-redis redis-cli'
```

---

## Part A — Streams by hand first

Before writing Java, drive the whole protocol from `redis-cli`. Ten minutes here
saves an hour of debugging later.

```bash
r DEL 'room:{7}:stream'
r XADD 'room:{7}:stream' '*' body 'first'  sender alice
r XADD 'room:{7}:stream' '*' body 'second' sender bob
r XLEN 'room:{7}:stream'
```
**Expected:**
```
"1735689600123-0"
"1735689600456-0"
(integer) 2
```

Create two groups — one per simulated node:

```bash
r XGROUP CREATE 'room:{7}:stream' node-a 0 MKSTREAM
r XGROUP CREATE 'room:{7}:stream' node-b 0 MKSTREAM
r XINFO GROUPS 'room:{7}:stream'
```
**Expected:**
```
1)  1) "name"              2) "node-a"
    3) "consumers"         4) (integer) 0
    5) "pending"           6) (integer) 0
    7) "last-delivered-id" 8) "0-0"
2)  1) "name"              2) "node-b"
    ...
```

> `0` as the start ID means "from the beginning." `$` means "only new entries."
> For a node joining an existing room you want `$` — otherwise it replays the
> entire history on startup. The lab uses `0` here so you can see both entries.

Now read as node-a. **Both groups get everything** — that's the replication
property:

```bash
r XREADGROUP GROUP node-a consumer-1 COUNT 10 STREAMS 'room:{7}:stream' '>'
r XREADGROUP GROUP node-b consumer-1 COUNT 10 STREAMS 'room:{7}:stream' '>'
```
**Expected — identical output from both:**
```
1) 1) "room:{7}:stream"
   2) 1) 1) "1735689600123-0"
         2) 1) "body"   2) "first"   3) "sender" 4) "alice"
      2) 1) "1735689600456-0"
         2) 1) "body"   2) "second"  3) "sender" 4) "bob"
```

Now look at the PEL — nothing has been acked:

```bash
r XPENDING 'room:{7}:stream' node-a
```
**Expected:**
```
1) (integer) 2
2) "1735689600123-0"
3) "1735689600456-0"
4) 1) 1) "consumer-1"
      2) "2"
```

Read `>` again — **nothing new**, because these entries were already delivered:

```bash
r XREADGROUP GROUP node-a consumer-1 COUNT 10 STREAMS 'room:{7}:stream' '>'
```
**Expected:**
```
(nil)
```

But read `0` and you get **your own pending entries back**:

```bash
r XREADGROUP GROUP node-a consumer-1 COUNT 10 STREAMS 'room:{7}:stream' 0
```
**Expected:** both entries again.

✅ **That is crash recovery.** A restarted consumer reads `0` first to recover
what it was mid-processing.

Acknowledge one and watch the PEL shrink:

```bash
r XACK 'room:{7}:stream' node-a 1735689600123-0
r XPENDING 'room:{7}:stream' node-a
```
**Expected:**
```
(integer) 1
1) (integer) 1
2) "1735689600456-0"
3) "1735689600456-0"
```

### Simulate a dead consumer

```bash
# consumer-1 "dies" holding one entry. consumer-2 claims it after 5s idle.
sleep 6
r XAUTOCLAIM 'room:{7}:stream' node-a consumer-2 5000 0 COUNT 10
```
**Expected:**
```
1) "0-0"                                   # next cursor
2) 1) 1) "1735689600456-0"
      2) 1) "body" 2) "second" 3) "sender" 4) "bob"
3) (empty array)                           # entries that no longer exist
```
```bash
r XPENDING 'room:{7}:stream' node-a - + 10
```
**Expected — ownership transferred:**
```
1) 1) "1735689600456-0"
   2) "consumer-2"
   3) (integer) 142
   4) (integer) 2                          # delivery count is now 2
```

✅ **The entry moved to a live consumer and its delivery count incremented.**
That delivery count is how you detect poison messages — an entry delivered 10
times is one nobody can process.

---

## Part B — The stream fan-out

`src/main/java/com/pulse/fanout/StreamFanout.java`:

```java
package com.pulse.fanout;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.pulse.protocol.Envelope;
import io.micrometer.core.instrument.*;
import org.springframework.data.redis.connection.stream.*;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.messaging.simp.SimpMessagingTemplate;
import org.springframework.stereotype.Component;

import java.time.Duration;
import java.util.Map;

@Component
public class StreamFanout {

    private final StringRedisTemplate redis;
    private final SimpMessagingTemplate broker;
    private final ObjectMapper json;
    private final String nodeId;
    private final long maxLen;

    private final Counter appended, delivered, duplicates, claimed;
    private final Timer appendTimer;

    public StreamFanout(StringRedisTemplate redis, SimpMessagingTemplate broker,
                        ObjectMapper json, MeterRegistry metrics,
                        @Value("${pulse.node-id}") String nodeId,
                        @Value("${pulse.stream.max-len:10000}") long maxLen) {
        this.redis = redis; this.broker = broker; this.json = json;
        this.nodeId = nodeId; this.maxLen = maxLen;

        this.appended   = Counter.builder("stream.appended").register(metrics);
        this.delivered  = Counter.builder("stream.delivered").register(metrics);
        this.duplicates = Counter.builder("stream.duplicates").register(metrics);
        this.claimed    = Counter.builder("stream.claimed").register(metrics);
        this.appendTimer = Timer.builder("stream.append.latency")
                .publishPercentileHistogram().register(metrics);
    }

    /** Hash tag {roomId} keeps the stream and its seq counter in the same slot. */
    public static String streamKey(String roomId) { return "room:{" + roomId + "}:stream"; }
    private  String group()                       { return "node-" + nodeId; }

    public RecordId append(String roomId, Envelope envelope) {
        return appendTimer.record(() -> {
            try {
                var record = StreamRecords.newRecord()
                        .in(streamKey(roomId))
                        .ofMap(Map.of("payload", json.writeValueAsString(envelope)));

                // MAXLEN ~ : approximate trim, whole macro-nodes only. The ~ is
                // not a nicety — exact trimming is O(n) on every single XADD.
                RecordId id = redis.opsForStream().add(record,
                        XAddOptions.maxlen(maxLen).approximateTrimming(true));

                appended.increment();
                return id;
            } catch (Exception e) {
                throw new FanoutException("XADD failed for room " + roomId, e);
            }
        });
    }

    /** Called by the consumer loop for every entry read. */
    void deliver(String roomId, MapRecord<String, String, String> record) {
        try {
            var envelope = json.readValue(record.getValue().get("payload"), Envelope.class);
            broker.convertAndSend("/topic/room." + roomId, envelope);
            delivered.increment();
        } catch (Exception e) {
            throw new DeliveryException(record.getId().getValue(), e);
        }
    }
}
```

---

## Part C — The consumer loop

The three-phase loop from the README: recover mine, read new, claim the dead.

`src/main/java/com/pulse/fanout/StreamConsumer.java`:

```java
package com.pulse.fanout;

import org.springframework.data.redis.connection.stream.*;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Component;

import java.time.Duration;
import java.util.*;
import java.util.concurrent.*;

@Component
public class StreamConsumer {

    private final StringRedisTemplate redis;
    private final StreamFanout fanout;
    private final String nodeId;

    private final Map<String, Future<?>> loops = new ConcurrentHashMap<>();
    private final ExecutorService executor =
            Executors.newThreadPerTaskExecutor(Thread.ofVirtual().factory());
    private volatile boolean running = true;

    /** Called when this node gains its first local subscriber for a room. */
    public void startConsuming(String roomId) {
        loops.computeIfAbsent(roomId, id -> {
            ensureGroup(id);
            return executor.submit(() -> consumeLoop(id));
        });
    }

    public void stopConsuming(String roomId) {
        var future = loops.remove(roomId);
        if (future != null) future.cancel(true);
    }

    private void ensureGroup(String roomId) {
        try {
            // '$' = only new entries. Starting at 0 would replay the whole room
            // history to a node that just gained one subscriber.
            redis.opsForStream().createGroup(StreamFanout.streamKey(roomId),
                    ReadOffset.latest(), group());
        } catch (Exception e) {
            if (!e.getMessage().contains("BUSYGROUP")) throw e;   // already exists: fine
        }
    }

    private void consumeLoop(String roomId) {
        String key = StreamFanout.streamKey(roomId);

        // PHASE 1 — recover entries THIS consumer had in flight when it died.
        // Read '0' repeatedly until it comes back empty.
        recoverOwnPending(roomId, key);

        long lastClaimSweep = System.currentTimeMillis();

        while (running && !Thread.currentThread().isInterrupted()) {
            try {
                // PHASE 2 — new entries. BLOCK so we're not polling.
                List<MapRecord<String, String, String>> records =
                        redis.opsForStream().read(
                                Consumer.from(group(), nodeId),
                                StreamReadOptions.empty().count(100).block(Duration.ofSeconds(2)),
                                StreamOffset.create(key, ReadOffset.lastConsumed()));

                if (records != null) {
                    for (var record : records) processAndAck(roomId, key, record);
                }

                // PHASE 3 — periodically claim work abandoned by dead consumers.
                if (System.currentTimeMillis() - lastClaimSweep > 30_000) {
                    claimAbandoned(roomId, key);
                    lastClaimSweep = System.currentTimeMillis();
                }

            } catch (Exception e) {
                if (!running) return;
                log.warn("consume loop error for room {}, backing off", roomId, e);
                sleepQuietly(1000);          // don't hot-spin against a dead Redis
            }
        }
    }

    private void recoverOwnPending(String roomId, String key) {
        while (true) {
            var records = redis.opsForStream().read(
                    Consumer.from(group(), nodeId),
                    StreamReadOptions.empty().count(100),
                    StreamOffset.create(key, ReadOffset.from("0")));   // '0' = MY pending
            if (records == null || records.isEmpty()) return;
            log.info("recovering {} pending entries for room {}", records.size(), roomId);
            for (var record : records) processAndAck(roomId, key, record);
        }
    }

    private void claimAbandoned(String roomId, String key) {
        var claimed = redis.opsForStream().claim(key, group(), nodeId,
                RedisStreamCommands.XClaimOptions.minIdle(Duration.ofSeconds(30))
                        .ids(pendingIdsFromDeadConsumers(key)));
        for (var record : claimed) processAndAck(roomId, key, record);
    }

    /**
     * ACK AFTER processing. This is the at-least-once choice: a crash between
     * deliver() and acknowledge() causes a redelivery, which the idempotent
     * insert in MessageService absorbs. Acking first would be at-most-once.
     */
    private void processAndAck(String roomId, String key,
                               MapRecord<String, String, String> record) {
        try {
            fanout.deliver(roomId, record);
            redis.opsForStream().acknowledge(key, group(), record.getId());
        } catch (Exception e) {
            // Do NOT ack. The entry stays in the PEL and will be redelivered
            // or claimed. If it's poison, the delivery count will reveal it.
            log.error("delivery failed for {} in room {}", record.getId(), roomId, e);
        }
    }

    @PreDestroy
    public void shutdown() {
        running = false;
        loops.values().forEach(f -> f.cancel(true));
        executor.shutdownNow();
    }
}
```

> **`ReadOffset.lastConsumed()` maps to `>`**, and `ReadOffset.from("0")` maps to
> `0`. Getting these backwards is the most common Streams bug: reading `0` in the
> main loop means you re-process your entire PEL forever and never see new
> entries.

Wire the lifecycle:
```java
// RoomSubscriptionManager
public void roomJoined(String roomId) {
    localSubscribers.compute(roomId, (id, count) -> {
        if (count == null) { streamConsumer.startConsuming(id); return new AtomicInteger(1); }
        count.incrementAndGet(); return count;
    });
}
```

And the controller:
```java
// replace fanout.publish(...) with:
streamFanout.append(roomId, envelope);
```

---

## Part D — Re-run the loss test

**The moment of truth.** Same script as Module 07, unchanged.

```bash
./code/loss_test.sh
```

**Expected — Module 07 with Pub/Sub:**
```
published: 200   received: 171   LOST: 29
```

**Expected — now, with Streams:**
```
publishing 1..200 via node-a, pausing redis at message 80
>>> docker pause pulse-redis
>>> docker unpause pulse-redis
published: 200   received: 200   LOST: 0
```

✅ **Zero lost.**

Watch what happened during the pause:

```bash
r XINFO GROUPS 'room:{9}:stream'
```
**Expected right after the unpause:**
```
1) 1) "name"              2) "node-node-b"
   3) "consumers"         4) (integer) 1
   5) "pending"           6) (integer) 27          <-- the backlog
   7) "last-delivered-id" 8) "1735689612891-0"
   9) "entries-read"     10) (integer) 200
  11) "lag"              12) (integer) 0
```

And a few seconds later:
```
   5) "pending"           6) (integer) 0
```

The 27 entries that node-b couldn't receive during the pause were **still in the
stream**. When it reconnected, `XREADGROUP >` delivered them in order. Nothing
retried, nothing was cleverly recovered — they were simply *stored*.

Now the harder variant. Kill Redis entirely with persistence off:

```bash
docker kill pulse-redis && docker start pulse-redis
./code/loss_test.sh
```
**Expected:**
```
published: 200   received: 143   LOST: 57
```

⚠️ **Streams do not survive a Redis restart without persistence.** The stream is
in memory. This is the gap Module 13's outbox closes — Postgres holds the
message and can republish.

Note it honestly in `results.md`:
```markdown
- Streams, Redis PAUSED 1.5s:    0/200 lost   (was 29/200 with Pub/Sub)
- Streams, Redis KILLED+restart: 57/200 lost  (needs the outbox — Module 13)
```

---

## Part E — Kill a consumer mid-processing

```bash
# Make delivery slow so we can kill it in the middle
curl -X POST localhost:8081/debug/slow-delivery -d '{"millis":3000}'

# publish 20 messages
for i in $(seq 1 20); do ./code/publish.sh room.11 "kill-test-$i"; done

# node-b is now processing, one every 3s. Kill it.
sleep 5
kill -9 $(pgrep -f 'PULSE_NODE_ID=node-b')

r XPENDING 'room:{11}:stream' node-node-b
```
**Expected:**
```
1) (integer) 18
2) "1735689700123-0"
3) "1735689700890-0"
4) 1) 1) "node-b"
      2) "18"
```

18 entries stranded in a dead consumer's PEL. Now start a third node in the same
group name to claim them — or just restart node-b:

```bash
SERVER_PORT=8081 PULSE_NODE_ID=node-b ./mvnw spring-boot:run
```

**Expected in the log:**
```
INFO c.p.fanout.StreamConsumer : recovering 18 pending entries for room 11
```
```bash
r XPENDING 'room:{11}:stream' node-node-b
```
**Expected:**
```
1) (integer) 0
```

✅ **Phase 1 of the consumer loop recovered every stranded entry**, because they
were still in the PEL.

Now test recovery by a *different* consumer — the case where the node never
comes back:

```bash
kill -9 $(pgrep -f 'PULSE_NODE_ID=node-b')
# start node-c, but with the SAME group name (edit group() to use a shared name
# for this experiment, or run the XAUTOCLAIM by hand):
sleep 35
r XAUTOCLAIM 'room:{11}:stream' node-node-b node-c 30000 0 COUNT 100
```
**Expected:**
```
1) "0-0"
2) 1) 1) "1735689700123-0"
      2) 1) "payload" 2) "{\"v\":1,...}"
   ... 17 more
3) (empty array)
```

✅ Ownership transferred to `node-c`, which will process and ack them.

> **The 30-second `min-idle-time` is a real design parameter.** Too short and you
> steal work from a consumer that's merely slow, causing duplicates. Too long and
> recovery from a genuine crash is slow. It should be comfortably longer than
> your p99.9 processing time.

---

## Part F — Prove the duplicate is harmless

Force a redelivery and confirm nothing bad happens.

```bash
# process a message but crash before the XACK
curl -X POST localhost:8081/debug/skip-ack -d '{"count":5}'
for i in $(seq 1 5); do ./code/publish.sh room.12 "dup-test-$i"; done

r XPENDING 'room:{12}:stream' node-node-b
```
**Expected:**
```
1) (integer) 5
```

Restart node-b; the 5 entries are redelivered:

**Expected in the log:**
```
INFO  c.p.fanout.StreamConsumer : recovering 5 pending entries for room 12
DEBUG c.p.chat.MessageService  : retry detected for clientId c-dup-1
DEBUG c.p.chat.MessageService  : retry detected for clientId c-dup-2
...
```

```bash
docker exec pulse-postgres psql -U pulse -d pulse -c \
  "SELECT client_id, count(*) FROM messages WHERE room_id='room.12' GROUP BY 1 ORDER BY 1;"
```
**Expected:**
```
  client_id  | count
-------------+-------
 c-dup-test-1|     1
 c-dup-test-2|     1
 c-dup-test-3|     1
 c-dup-test-4|     1
 c-dup-test-5|     1
```

✅ **Delivered twice, stored once.** The `clientId` from Module 05 plus the unique
index absorbed it. That's the exactly-once illusion, working.

Check the client didn't see doubles either:
```bash
curl -s localhost:8080/actuator/metrics/stream.duplicates | jq '.measurements[0].value'
```
```
5
```

---

## Part G — Measure what durability costs

Same k6 workload as Modules 06 and 07.

```bash
k6 run -e ROOMS=100 -e SEND_EVERY=60000 ../../06-load-testing-harness/code/pulse-load.js
```

**Expected:**

| | Module 06 (1 node) | Module 07 (Pub/Sub) | Module 09 (Streams) |
|---|-------------------|---------------------|---------------------|
| p50 | 14 ms | 17 ms | **21 ms** |
| p95 | 61 ms | 68 ms | **79 ms** |
| p99 | 147 ms | 161 ms | **192 ms** |
| Knee (outbound msg/s) | 450,000 | 870,000 | **790,000** |
| Redis CPU at 400k out/s | n/a | 24% | **51%** |
| Redis memory | n/a | ~40 MB | **1.9 GB** |
| Messages lost (Redis pause) | n/a | **29/200** | **0/200** |

### Reading the tradeoff

**+4 ms p50, +31 ms p99, 9% less throughput, and 47× the Redis memory — for
zero message loss.**

Where the extra latency goes:
```bash
r INFO commandstats | grep -E 'cmdstat_(xadd|xreadgroup|xack)'
```
```
cmdstat_xadd:calls=284119,usec=511414,usec_per_call=1.80
cmdstat_xreadgroup:calls=91204,usec=2189896,usec_per_call=24.01
cmdstat_xack:calls=284119,usec=340943,usec_per_call=1.20
```

`XADD` and `XACK` are ~1.5 µs. `XREADGROUP` is 24 µs — it does more work
(updating the PEL, tracking last-delivered) and returns batches. Three commands
per message instead of one, plus PEL bookkeeping. Redis CPU doubling from 24% to
51% is the real cost, and it's what will push you to Cluster.

The memory is the number to plan around:
```bash
r MEMORY USAGE 'room:{7}:stream'
r XLEN 'room:{7}:stream'
```
```
6144912
10214
```
**~600 bytes per entry** at `MAXLEN ~ 10000` = ~6 MB per room. **1,000 rooms =
6 GB.** That is a capacity plan, and it's why `MAXLEN` is not optional.

Try `MINID` instead — bound by time, not count:
```java
redis.opsForStream().trim(key, ...);   // XTRIM key MINID ~ <now - 10min>
```
```bash
r XTRIM 'room:{7}:stream' MINID '~' $(( ($(date +%s) - 600) * 1000 ))
r XLEN 'room:{7}:stream'
```
For a quiet room this keeps far fewer entries; for a busy one it keeps more.
**It bounds your replay *window*, which is what a reconnecting client actually
needs** (Module 10), rather than an arbitrary count.

---

## Part H — PEL monitoring

The PEL is your backlog gauge. Wire it up now; Module 20 alerts on it.

```java
@Component
public class StreamHealthMetrics {

    @Scheduled(fixedRate = 10_000)
    public void sample() {
        for (String roomId : consumer.activeRooms()) {
            String key = StreamFanout.streamKey(roomId);
            var info = redis.opsForStream().groups(key).stream()
                    .filter(g -> g.groupName().equals(group()))
                    .findFirst().orElse(null);
            if (info == null) continue;

            registry.gauge("stream.pending", Tags.of("room", roomId), info.pending());
            // 'lag' = entries added but not yet delivered to this group.
            // This is the leading indicator: pending means slow ACKs,
            // lag means slow READS.
            registry.gauge("stream.lag", Tags.of("room", roomId),
                           info.getRaw().get("lag") instanceof Number n ? n.longValue() : 0);
        }
    }
}
```

```bash
watch -n2 'curl -s localhost:8080/actuator/prometheus | grep -E "stream_(pending|lag)" | head'
```
**Expected at healthy load:**
```
stream_pending{room="7",} 0.0
stream_lag{room="7",} 0.0
```
**Expected when a node is struggling:**
```
stream_pending{room="7",} 4821.0
stream_lag{room="7",} 18402.0
```

✅ **`pending` and `lag` mean different things and you need both.** A high
`pending` means you're reading fast but processing/acking slowly. A high `lag`
means you're not reading fast enough. The fixes are different — more processing
concurrency versus a bigger `COUNT`/more consumers.

Record it:
```markdown
## Module 09 — Streams

- Pub/Sub loss (redis pause 1.5s): 29/200  ->  Streams: 0/200
- Streams, redis KILLED (no persistence): 57/200 lost (outbox needed, Module 13)
- Latency cost: +4ms p50, +31ms p99 vs Pub/Sub
- Throughput cost: 870k -> 790k outbound msg/s (-9%)
- Redis CPU: 24% -> 51% (3 commands/msg + PEL bookkeeping)
- Redis memory: 40MB -> 1.9GB (~600 bytes/entry at MAXLEN ~10000)
- Duplicate delivery on redelivery: absorbed by clientId unique index
- XAUTOCLAIM min-idle: 30s (must exceed p99.9 processing time)
```

---

## What you built

- Per-node consumer groups giving **replication plus acknowledgement**.
- A three-phase consumer loop: recover own pending, read new, claim abandoned.
- **Zero message loss** across a Redis pause, verified with the same script that
  lost 29 messages in Module 07.
- Crash recovery proven twice: same consumer restarting, and a different
  consumer claiming.
- Duplicate delivery proven harmless via Module 05's idempotency.
- The measured price of durability, and the memory model to budget for it.
- PEL and lag gauges — the two numbers that tell you a node is falling behind.

**Remaining gap:** the last hop. A *client* that disconnects still misses
messages, and still can't tell. That's Module 10.

Now do [`challenge.md`](./challenge.md).

Then: [Module 10 — Ordering & Delivery Semantics](../10-ordering-and-delivery-semantics/).
