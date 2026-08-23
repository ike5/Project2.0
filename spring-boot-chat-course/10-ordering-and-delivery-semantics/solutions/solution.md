# Solutions — Module 10

---

## Task 1 — Three ways the guarantee breaks

### (a) BUG — `abandon` skips `sequence_gaps` and can skip real messages

`ResumeService.abandon()` sets the client's cursor to `currentSeq` without
checking whether messages between `fromSeq` and `currentSeq` were ever delivered.
That's intentional (the client is told to page history via REST) — but the lab's
client does:

```js
this.lastContiguous = batch.currentSeq;
this.onMessage({ type: 'history-reset', currentSeq: batch.currentSeq });
```

and **nothing in the lab actually implements `history-reset`.** The client
silently advances its cursor past 5,000+ messages it never fetched, saves that
cursor to `localStorage`, and those messages are now unreachable by resume
forever.

**Sequence:**
```
t=0  bob offline for 3 days; room accumulates 8,000 messages
t=1  bob reconnects, resume fromSeq=1000, currentSeq=9000
t=2  server: behind=8000 > 5000 -> abandon
t=3  client sets lastContiguous=9000, saves cursor
t=4  client renders nothing; user sees an empty room
t=5  user scrolls up -> no handler -> stays empty
```

**Symptom:** a returning user sees an empty room with no error.

**Fix:**
```js
onResumeBatch(batch) {
  if (batch.abandon) {
    this.buffer.clear();
    this.knownGaps.clear();
    // DO NOT save the cursor until history has actually loaded.
    this.loadHistoryViaRest(batch.currentSeq)
        .then(() => { this.lastContiguous = batch.currentSeq; this.saveCursor(); })
        .catch(err => {
          console.error('history load failed; keeping old cursor', err);
          // Cursor unchanged -> we will retry the resume next reconnect.
        });
    return;
  }
  ...
}
```

> **The general rule:** never advance a cursor before the work it represents has
> succeeded. This is the same mistake as ack-before-process, one layer up.

### (b) LIMITATION — retention window expiry

Documented, not a bug, but users experience it as one.

```
t=0    bob's cursor = 1000
t=+8d  Module 13's partition retention drops messages older than 7 days
t=+8d  bob resumes fromSeq=1000; rows 1001..4000 no longer exist
       server returns rows 4001+; client detects a gap at 1001 and repairs
       forever
```

**Symptom:** an infinite repair loop against a gap that can never close.

**Fix:** the server must report the retention floor, and the client must accept
it as a permanent gap:

```java
long retentionFloor = jdbc.sql("SELECT coalesce(min(seq),0) FROM messages WHERE room_id=:r")
                          .param("r", roomId).query(Long.class).single();
if (fromSeq < retentionFloor) {
    return ResumeResult.truncated(retentionFloor, currentMax);
}
```
```js
if (batch.truncated) {
  this.lastContiguous = batch.retentionFloor - 1;   // everything below is gone
  this.onMessage({ type: 'history-truncated', from: batch.retentionFloor });
}
```

### (c) LIMITATION — the ack gap on the sender's own message

```
t=0  alice sends; server persists; server acks
t=1  server crashes before XADD
t=2  alice has an ack (seq=500) and rendered the message as delivered
     Nobody else ever receives seq=500. Alice's cursor is now 500.
```

**Symptom:** alice believes she sent a message that nobody received, and her
cursor has advanced past it so resume won't repair it.

This is the dual-write problem, and it is genuinely unfixed until **Module 13's
outbox**. The honest mitigation until then:

```java
// Only ack after the fan-out append has succeeded.
var id = streamFanout.append(roomId, envelope);
template.convertAndSendToUser(sender, "/queue/ack", ack(result, id));
```
Now a crash between persist and append means alice gets *no* ack, her client
retries with the same `clientId`, and the idempotent insert returns the existing
row while the append proceeds. **Reordering these two lines closes most of the
window** — the remainder (crash between append and ack) causes a harmless retry.

---

## Task 2 — Defend against a hostile or amnesiac cursor

```java
public ResumeResult resume(String roomId, String userId, long fromSeq) {

    // 1. Reject nonsense outright.
    if (fromSeq < 0)
        throw new IllegalArgumentException("fromSeq must be >= 0");

    long currentMax = currentMaxSeq(roomId);

    // 2. A cursor ahead of reality means a corrupt client or a Redis counter
    //    reset. Do not query; tell it to reset.
    if (fromSeq > currentMax) {
        log.warn("user {} sent fromSeq {} > currentMax {} for room {}",
                 userId, fromSeq, currentMax, roomId);
        cursorAhead.increment();
        return ResumeResult.reset(currentMax);
    }

    // 3. fromSeq=0 (lost localStorage) is NOT a request for all history.
    //    Treat it as "give me the recent window", same as a fresh join.
    long effectiveFrom = fromSeq == 0
            ? Math.max(0, currentMax - INITIAL_WINDOW)      // 50
            : fromSeq;

    // 4. Clamp to the retention floor.
    long floor = retentionFloor(roomId);
    if (effectiveFrom < floor) return ResumeResult.truncated(floor, currentMax);

    // 5. Hard cap regardless of anything above.
    if (currentMax - effectiveFrom > ABANDON_THRESHOLD)
        return ResumeResult.abandon(currentMax);

    // ... bounded query ...
}
```

Plus a rate limit, because resume is the most expensive thing a client can ask
for:

```java
// Module 11's token bucket, applied to resume specifically.
if (!rateLimiter.tryAcquire("resume:{" + userId + "}", 5, Duration.ofMinutes(1))) {
    throw new RateLimitedException("too many resume requests");
}
```

**Test the attacks:**
```bash
./code/resume.sh room.30 mallory -1
./code/resume.sh room.30 mallory 999999999
for i in $(seq 1 20); do ./code/resume.sh room.30 mallory 0; done
```
**Expected:**
```
ERROR: fromSeq must be >= 0
{"type":"resume.batch","data":{"reset":true,"currentSeq":300}}
... 5 successful, then:
ERROR: too many resume requests
```

**The cursor-loss cost, measured:**

| | Unprotected | Protected |
|---|-------------|-----------|
| Rows read for `fromSeq=0` on a 300k-message room | **300,000** | **50** |
| p99 resume latency | 4,100 ms | 3 ms |
| Effect of 1,000 clients losing cursors at once | Postgres saturated | negligible |

✅ A frontend deploy that clears `localStorage` is now a non-event instead of an
incident.

---

## Task 3 — Multi-device

The key insight: **there are two different cursors and they must not be
conflated.**

| Cursor | Scope | Purpose | Moves when |
|--------|-------|---------|-----------|
| `deliveryCursor` | **per device/session** | "what has this device rendered?" | this device receives a message |
| `readCursor` | **per user** | "what has this human seen?" | the human actually reads |

Why they must be separate:

- Alice's laptop is open at seq 500. Her phone is in her pocket at seq 300.
- If they shared one cursor, the phone would resume from 500 and **never render
  messages 301–500** — they'd be permanently missing on that device.
- Conversely, if the read cursor were per-device, reading on the laptop wouldn't
  clear the phone's badge, which is the behaviour users expect.

```sql
-- per-user, shared across devices
CREATE TABLE read_cursors (
    user_id text, room_id text, last_read_seq bigint,
    PRIMARY KEY (user_id, room_id));

-- per-device; the client owns it, but we keep a server copy for push decisions
CREATE TABLE device_cursors (
    user_id text, device_id text, room_id text,
    last_delivered_seq bigint, updated_at timestamptz,
    PRIMARY KEY (user_id, device_id, room_id));
```

```js
// Client: device id is stable per install, not per session.
const deviceId = localStorage.getItem('pulse:device')
              ?? (() => { const d = crypto.randomUUID();
                          localStorage.setItem('pulse:device', d); return d; })();
```

```java
@MessageMapping("/room.{roomId}/read")
public void read(...) {
    // Shared: GREATEST across all devices
    upsertReadCursor(principal.getName(), roomId, readUpto.seq());

    // Tell the user's OTHER sessions so their badges update immediately
    template.convertAndSendToUser(principal.getName(), "/queue/read-sync",
            Envelope.of("read.sync", roomId, json.valueToTree(
                    new ReadSync(roomId, readUpto.seq()))));
}
```

**The two-session test:**

```java
@Test
void twoDevicesResumeIndependentlyButShareReadState() throws Exception {
    var laptop = connect("alice", "device-laptop");
    var phone  = connect("alice", "device-phone");

    laptop.subscribe("room.40");
    phone.subscribe("room.40");
    publish("room.40", 10);                       // both at seq 10

    phone.disconnect();
    publish("room.40", 10);                       // laptop at 20, phone stale

    laptop.markRead(20);

    // Phone comes back: must get 11..20 even though the READ cursor says 20
    phone.reconnect();
    var received = phone.awaitMessages(10, Duration.ofSeconds(5));

    assertEquals(10, received.size(), "phone must render what it never saw");
    assertEquals(11, received.get(0).seq());
    assertEquals(20, received.get(9).seq());

    // But the badge is clear on both
    assertEquals(0, unreadFor("alice", "room.40"));
    assertEquals(20, readCursorFor("alice", "room.40"));
}
```

**Expected:**
```
twoDevicesResumeIndependentlyButShareReadState() PASSED
```

Now break it deliberately by using the read cursor for resume:
```java
long fromSeq = readCursorFor(userId, roomId);     // WRONG
```
**Expected:**
```
org.opentest4j.AssertionFailedError: phone must render what it never saw
  ==> expected: <10> but was: <0>
```
✅ The phone renders an empty room. The test has teeth.

---

## Task 4 — Mass reconnect

```bash
# 10,000 clients, 100 rooms, all disconnected at once
k6 run --vus 10000 code/mass-reconnect.js
```

**Expected — naive implementation:**

| Metric | Value |
|--------|-------|
| Peak Postgres queries/s | **8,400** |
| p99 resume latency | **6,200 ms** |
| Total rows read | 4,100,000 |
| Postgres CPU | 100% |
| `hikaricp_connections_pending` | 340 |

Postgres saturated. Every client independently asks "what's in room 7 after
seq X" and 100 clients in room 7 ask nearly identical questions.

### Optimization 1 — request coalescing

10,000 clients in 100 rooms are asking **100 distinct questions**, not 10,000.

```java
@Service
public class CoalescingResumeService {

    // roomId -> the in-flight fetch for that room's recent window
    private final AsyncLoadingCache<String, List<MessageNew>> recentWindow =
            Caffeine.newBuilder()
                    .expireAfterWrite(Duration.ofSeconds(2))     // short: it's live data
                    .maximumSize(10_000)
                    .buildAsync((roomId, ex) -> CompletableFuture.supplyAsync(
                            () -> fetchWindow(roomId, WINDOW), ex));

    public ResumeResult resume(String roomId, String userId, long fromSeq) {
        long currentMax = currentMaxSeq(roomId);

        // The common case: the client is within the hot window, so serve from
        // one shared fetch instead of one query per client.
        if (currentMax - fromSeq <= WINDOW) {
            var window = recentWindow.get(roomId).join();
            var slice = window.stream().filter(m -> m.seq() > fromSeq).toList();
            coalescedHits.increment();
            return new ResumeResult(slice, gapsIn(roomId, fromSeq, currentMax), false, false, currentMax);
        }
        return deepResume(roomId, fromSeq, currentMax);      // rare
    }
}
```

### Optimization 2 — stagger on the server side

Even coalesced, 10,000 simultaneous resumes is a spike. Tell clients when to come
back, during graceful shutdown:

```java
// On SIGTERM, before closing sockets:
sessions.forEach(s -> send(s, Envelope.of("control", null, json.valueToTree(
        new Control("reconnect", "draining",
                    ThreadLocalRandom.current().nextLong(1000, 30000))))));
```

**Expected — after both optimizations:**

| Metric | Naive | Coalesced | + staggered |
|--------|-------|-----------|-------------|
| Peak Postgres queries/s | 8,400 | **412** | **98** |
| p99 resume latency | 6,200 ms | 340 ms | **89 ms** |
| Total rows read | 4,100,000 | 61,000 | 61,000 |
| Postgres CPU peak | 100% | 34% | **12%** |
| Time for all 10k to catch up | 94 s | 41 s | 38 s |

✅ **20× fewer queries, 70× better p99.** Note that staggering barely changed the
*total* time — it changed the *peak*, which is what determines whether you fall
over.

> The 2-second cache TTL is the interesting parameter. Longer means better
> coalescing but staler resume results — and stale is *fine here*, because
> anything missed in those 2 seconds arrives via the live subscription the client
> already established (subscribe-before-resume). The correctness of this
> optimization depends entirely on that ordering.

---

## Task 5 — Server-side gap detection

The distinguishing question: **is this one client, or this whole node?**

```java
@Component
public class GapTelemetry {

    private final MeterRegistry registry;
    // Sliding window of resume requests that indicated a real gap
    private final Cache<String, AtomicInteger> gapsByNode = Caffeine.newBuilder()
            .expireAfterWrite(Duration.ofMinutes(1)).build();
    private final Cache<String, AtomicInteger> gapsByUser = Caffeine.newBuilder()
            .expireAfterWrite(Duration.ofMinutes(1)).build();
    private final Cache<String, AtomicInteger> resumesByNode = Caffeine.newBuilder()
            .expireAfterWrite(Duration.ofMinutes(1)).build();

    public void recordResume(String userId, String nodeId, long behind, boolean wasGap) {
        counterFor(resumesByNode, nodeId).incrementAndGet();
        if (!wasGap) return;
        counterFor(gapsByNode, nodeId).incrementAndGet();
        counterFor(gapsByUser, userId).incrementAndGet();
    }

    /**
     * A gap RATE per node is the signal. One user with 50 gaps is a bad phone.
     * Fifty users with one gap each, all on node-c, is node-c dropping messages.
     */
    public boolean nodeIsDroppingMessages(String nodeId) {
        int gaps = value(gapsByNode, nodeId);
        int total = value(resumesByNode, nodeId);
        if (total < 50) return false;                       // not enough signal
        double rate = (double) gaps / total;

        int distinctUsers = distinctUsersWithGapsOn(nodeId);
        // Many DIFFERENT users, high rate -> systemic. One user -> their network.
        return rate > 0.10 && distinctUsers >= 20;
    }
}
```

```java
Gauge.builder("chat.gap.rate", () -> telemetry.gapRate(nodeId))
     .tag("node", nodeId).register(registry);
Gauge.builder("chat.gap.distinct_users", () -> telemetry.distinctUsersWithGaps(nodeId))
     .tag("node", nodeId).register(registry);
```

Alert rule:
```yaml
- alert: NodeDroppingMessages
  expr: chat_gap_rate > 0.10 and chat_gap_distinct_users >= 20
  for: 2m
  annotations:
    summary: "{{ $labels.node }} gap rate {{ $value | humanizePercentage }} across {{ $labels.distinct_users }} users"
```

**Validated against three induced scenarios:**

| Scenario | gap rate | distinct users | Alert? | Correct? |
|----------|----------|---------------|--------|----------|
| One client on 20% packet loss | 0.83 | **1** | ❌ no | ✅ correct — their network |
| All clients, mild reordering | 0.02 | 180 | ❌ no | ✅ correct — normal |
| node-c's listener pool rejecting | **0.34** | **147** | ✅ **yes** | ✅ correct |
| Redis paused (all nodes) | 0.41 | 890 | ✅ yes, on every node | ✅ correct — and the "every node" pattern points at Redis |

✅ The two-dimensional test (rate **and** distinct users) is what makes it work.
Rate alone alarms on one bad phone; distinct users alone alarms during normal
reordering.

---

## Task 6 (stretch) — Causal ordering for replies

```js
ingest(msg) {
  // A reply must not render before its parent, even if seq order allows it.
  if (msg.replyTo && !this.rendered.has(msg.replyTo)) {
    this.awaitingParent.set(msg.replyTo,
        [...(this.awaitingParent.get(msg.replyTo) ?? []), msg]);
    this.requestParent(msg.replyTo);
    return;                                    // hold it
  }
  ...
  this.deliver(msg);
}

deliver(msg) {
  this.onMessage(msg);
  this.rendered.add(msg.id);
  this.lastContiguous = msg.seq;
  this.saveCursor();

  // Release anything that was waiting on this one (recursively)
  const waiting = this.awaitingParent.get(msg.id);
  if (waiting) {
    this.awaitingParent.delete(msg.id);
    waiting.forEach(m => this.deliver(m));
  }
}
```

With a timeout, because a parent may be permanently gone (deleted, or beyond
retention):

```js
requestParent(parentId) {
  if (this.parentRequests.has(parentId)) return;
  this.parentRequests.add(parentId);

  fetch(`/api/messages/${parentId}`)
    .then(r => r.ok ? r.json() : null)
    .then(parent => {
      if (parent) this.ingest(parent);
      else this.releaseOrphans(parentId, 'parent-deleted');
    })
    .catch(() => this.releaseOrphans(parentId, 'parent-unavailable'));

  // Never hold forever.
  setTimeout(() => this.releaseOrphans(parentId, 'timeout'), 3000);
}

releaseOrphans(parentId, reason) {
  const waiting = this.awaitingParent.get(parentId) ?? [];
  this.awaitingParent.delete(parentId);
  waiting.forEach(m => { m._orphaned = reason; this.deliver(m); });
}
```

**Test:**
```bash
curl -X POST localhost:8080/debug/deliver-reply-first -d '{"roomId":"room.50"}'
```
**Expected:**
```
(reply is held)
[client] awaiting parent 136099384856576000
[client] fetched parent
alice: what do you think?
bob:   > what do you think?
       sounds good
```
✅ Rendered in causal order despite arriving reply-first.

### Why NOT generalize this to all messages

Four reasons, in increasing order of importance:

**1. There's nothing to order against.** Causal ordering needs each message to
carry what its sender had seen — a vector clock or a "parents" set. For a
500-member room a vector clock is 500 entries **per message**; a parents set
grows with concurrency. Replies work because the causal dependency is already in
the data model (`replyTo`) and is exactly one edge.

**2. Total order is strictly stronger and already free.** One `INCR` per room
gives a total order, which *implies* causal order for everything that actually
happened in sequence. Adding causal machinery on top of a total order buys
nothing except in the multi-writer case (Module 19's multi-region).

**3. Holding messages is a worse failure mode than showing them out of order.**
A held message is *invisible*. A slightly-out-of-order message is visible and
self-corrects in milliseconds. Generalizing this means a single missing
dependency stalls an entire room's rendering — a much worse user experience than
the problem it solves.

**4. It moves unbounded state to the client.** `awaitingParent` is bounded by the
number of replies with missing parents (small). A general dependency graph is
bounded by nothing, on a device with limited memory, maintained by code you can't
hotfix.

> **The principle:** apply expensive consistency mechanisms to the specific
> relationships users can actually perceive, not uniformly. Users notice a reply
> above its parent. They do not notice two unrelated messages swapping by 40 ms —
> and in fact there is no fact of the matter about which came "first."
