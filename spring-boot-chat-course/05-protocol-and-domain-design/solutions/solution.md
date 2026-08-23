# Solutions — Module 05

---

## Task 1 — The sequence-hole bug

### Prove it

```java
@Test
void sequencesAreContiguousUnderConcurrentRetries() throws Exception {
    var create = new MessageCreate("c-hole", "x", null);
    int attempts = 64;
    var barrier = new CyclicBarrier(attempts);

    try (var ex = Executors.newVirtualThreadPerTaskExecutor()) {
        IntStream.range(0, attempts).forEach(i -> ex.submit(() -> {
            barrier.await();
            service.send("room.hole", "alice", create);
            return null;
        }));
    }
    // one more, distinct message
    service.send("room.hole", "alice", new MessageCreate("c-after", "y", null));

    List<Long> seqs = jdbc.sql("SELECT seq FROM messages WHERE room_id='room.hole' ORDER BY seq")
                          .query(Long.class).list();
    Long lastAllocated = jdbc.sql("SELECT last_seq FROM room_sequences WHERE room_id='room.hole'")
                             .query(Long.class).single();

    assertEquals(List.of(1L, 2L), seqs);
    assertEquals(2L, lastAllocated, "sequences were burned by losing racers");
}
```

**Expected failure:**
```
org.opentest4j.AssertionFailedError: sequences were burned by losing racers
  ==> expected: <2> but was: <41>
```

✅ Thirty-nine sequence numbers allocated and never used. The `messages` table
has `seq` 1 and 41; a client sees a gap of 39 messages that never existed and
will request a resume for them forever.

### The fix — let the insert allocate the sequence

The bug is ordering: `nextSeq()` commits its increment whether or not the insert
succeeds. Do both in **one statement**, so they succeed or fail together:

```java
@Transactional
public InsertResult insertIdempotent(long id, String roomId, String sender,
                                     String clientId, String body, Long replyTo) {

    // Single statement: the sequence is allocated by the same CTE that inserts.
    // If ON CONFLICT DO NOTHING fires, the sequence CTE's effect is discarded
    // along with it, because data-modifying CTEs in one statement share a fate.
    Optional<MessageNew> inserted = jdbc.sql("""
            WITH next AS (
                INSERT INTO room_sequences (room_id, last_seq) VALUES (:room, 1)
                ON CONFLICT (room_id) DO UPDATE SET last_seq = room_sequences.last_seq + 1
                RETURNING last_seq
            ), ins AS (
                INSERT INTO messages (id, room_id, seq, sender, client_id, body, reply_to)
                SELECT :id, :room, next.last_seq, :sender, :clientId, :body, :replyTo
                FROM next
                ON CONFLICT (room_id, client_id) DO NOTHING
                RETURNING id, client_id, seq, room_id, sender, body,
                          extract(epoch from created_at)*1000 AS ts, reply_to
            )
            SELECT * FROM ins
            """)
            .param("id", id).param("room", roomId).param("sender", sender)
            .param("clientId", clientId).param("body", body).param("replyTo", replyTo)
            .query(MessageNew.class)
            .optional();

    if (inserted.isPresent()) return new InsertResult(inserted.get(), false);
    return new InsertResult(findByClientId(roomId, clientId).orElseThrow(), true);
}
```

**Expected after the fix:**
```
SequenceContiguityTest > sequencesAreContiguousUnderConcurrentRetries() PASSED
  seqs = [1, 2], last_seq = 2
```

### Wait — does this actually work?

**Almost, and the caveat matters.** In Postgres, data-modifying CTEs all see the
same snapshot and all execute, but here the `ins` CTE's `SELECT ... FROM next`
means the sequence CTE only runs when the insert row is produced. If
`ON CONFLICT DO NOTHING` suppresses the insert, the `room_sequences` upsert
**has still executed** — CTEs are not conditionally skipped.

So this reduces the hole but doesn't eliminate it. The genuinely correct
approaches, in order of preference:

**(a) Check-then-insert, with the check as the fast path (what Pulse ships):**
```java
var existing = findByClientId(roomId, clientId);
if (existing.isPresent()) return new InsertResult(existing.get(), true);
// only now allocate — races are rare, and a rare hole is repaired below
```
Combined with **(c)**, this is what production systems actually do.

**(b) Advisory lock per room** — correct, and serializes every send in a room:
```sql
SELECT pg_advisory_xact_lock(hashtext(:room));
```
Correct but it's a per-room write lock; at Pulse's rates that's the bottleneck.

**(c) Make gaps repairable instead of impossible.** This is the real answer.
A client that sees a gap issues a `resume` (Module 10); the server responds with
what it has, plus `"gaps": [41]` marking sequences that are permanently absent.
The client stops asking.

> **The lesson generalizes:** in a distributed system, "make this invariant
> impossible to violate" is often more expensive than "make violations
> detectable and repairable." Sequence contiguity is worth ~99.99%, not a
> per-room lock. Module 10 builds the repair path, and Module 09 moves the
> counter to Redis `INCR` where the allocation is atomic and free.

---

## Task 2 — Typing indicators done right

```java
@Service
public class TypingService {

    private record Typer(String user, long expiresAt) {}

    // room -> user -> expiry
    private final Map<String, Map<String, Long>> typers = new ConcurrentHashMap<>();
    private final Set<String> dirty = ConcurrentHashMap.newKeySet();
    private final SimpMessagingTemplate template;

    private static final long TTL_MS = 5_000;

    public void startTyping(String roomId, String user) {
        typers.computeIfAbsent(roomId, k -> new ConcurrentHashMap<>())
              .put(user, System.currentTimeMillis() + TTL_MS);
        dirty.add(roomId);                      // mark, don't broadcast
    }

    public void stopTyping(String roomId, String user) {
        var room = typers.get(roomId);
        if (room != null && room.remove(user) != null) dirty.add(roomId);
    }

    /** ONE broadcast per room per second, and only for rooms that changed. */
    @Scheduled(fixedRate = 1000)
    public void flush() {
        long now = System.currentTimeMillis();

        // expire first — an expiry is a change worth broadcasting
        typers.forEach((roomId, room) -> {
            if (room.entrySet().removeIf(e -> e.getValue() < now)) dirty.add(roomId);
            if (room.isEmpty()) typers.remove(roomId, room);
        });

        var toFlush = Set.copyOf(dirty);
        dirty.removeAll(toFlush);

        for (String roomId : toFlush) {
            var users = typers.getOrDefault(roomId, Map.of()).keySet();
            template.convertAndSend("/topic/room." + roomId + ".typing",
                    Envelope.of("typing.update", roomId,
                            json.valueToTree(Map.of("users", List.copyOf(users)))));
        }
    }
}
```

Client debounce:
```js
let lastTypingSent = 0;
input.addEventListener('input', () => {
  const now = Date.now();
  if (now - lastTypingSent < 3000) return;      // at most once per 3s
  lastTypingSent = now;
  client.publish({ destination: `/app/${room}/typing`, body: '{}' });
});
```

### Measured, 200-member room, 20 simultaneous typers over 60 s

| Design | Client→server | Server→client | Total |
|--------|--------------|---------------|-------|
| Naive (every keystroke, broadcast each) | 20 × 300 keystrokes = **6,000** | 6,000 × 199 = **1,194,000** | 1,200,000 |
| Debounced only (3 s, broadcast each) | 20 × 20 = **400** | 400 × 199 = **79,600** | 80,000 |
| **Debounced + aggregated (1 Hz)** | **400** | 60 × 199 = **11,940** | **12,340** |

**Reduction: 97× vs naive, 6.5× vs debouncing alone.**

The aggregation win is the interesting one: it makes outbound traffic depend on
*time*, not on the number of typers. Twenty typers or two hundred, it's still one
frame per room per second. That's a **hard bound on the worst case**, which is
worth more than the average-case saving.

> ⚠️ **Aggregation is only safe because typing is at-most-once and
> state-latest.** You cannot do this to messages — dropping the intermediate
> states of a message stream loses data. Knowing which traffic tolerates this is
> the reusable insight, and Module 07 acts on it by routing typing through
> Pub/Sub and messages through Streams.

---

## Task 3 — A defensible dedup window

### How long can a client retry?

Exponential backoff with a 30 s cap, starting at 1 s, over a 10-attempt budget:
```
1 + 2 + 4 + 8 + 16 + 30 + 30 + 30 + 30 + 30 = 181 s  ≈ 3 minutes
```
A phone in a tunnel with an offline queue is the real worst case: messages queued
while offline flush on reconnect, and "offline" can be **hours**. But those aren't
*retries* of an in-flight send — they're first attempts with old `clientId`s,
which the database index handles regardless of cache window.

**So: the cache needs to cover the in-flight retry window (~3 minutes); the
database covers everything else, forever.**

### Cost per entry

```java
// measured with JOL
new MessageNew("136099384856576000", "01H8XGJQ4V2K9NPZ0Y3RTBWMDC", 48213L,
               "room.7", "alice", "sounds good to me", 1735689600123L, null)
```
```
Object header + 8 refs           :   80 bytes
id String (18 chars)             :   64 bytes
clientId String (26 chars)       :   80 bytes
room, sender, body Strings       :  168 bytes
Caffeine node + key String       :  152 bytes
                                   ---------
                            total:  544 bytes
```

### Heap at 50,000 msg/min

| Window | Entries | Heap |
|--------|---------|------|
| 5 min | 250,000 | **136 MB** |
| 30 min | 1,500,000 | 816 MB |
| 120 min | 6,000,000 | **3.3 GB** ❌ |

**5 minutes is right**: ~1.7× the measured worst-case retry window, at a heap
cost you can afford. 30 minutes buys nothing (retries don't last that long) and
costs 6×.

### Two-tier, proven across eviction

Store only what's needed to answer a retry — not the whole message:

```java
// Tier 1: bounded, hot. Stores 24 bytes instead of 544.
private record DedupEntry(long id, long seq) {}
private final Cache<String, DedupEntry> hot = Caffeine.newBuilder()
        .maximumSize(300_000)
        .expireAfterWrite(Duration.ofMinutes(5))
        .recordStats()
        .build();
```
```
new entry cost: 24 (record) + 96 (key String) + 40 (node) = 160 bytes
250,000 entries = 40 MB     ← 3.4x better than caching the full message
```

Test that eviction doesn't break correctness:

```java
@Test
void correctnessSurvivesCacheEviction() {
    var create = new MessageCreate("c-evict", "hello", null);
    var first = service.send("room.e", "alice", create);

    service.invalidateDedupCache();               // simulate eviction/restart/other instance

    var second = service.send("room.e", "alice", create);

    assertTrue(second.wasRetry(), "fell through to DB and still detected the retry");
    assertEquals(first.message().id(),  second.message().id());
    assertEquals(first.message().seq(), second.message().seq());

    Long rows = jdbc.sql("SELECT count(*) FROM messages WHERE client_id='c-evict'")
                    .query(Long.class).single();
    assertEquals(1L, rows);
}
```
**Expected:** `PASSED` — slower (one DB round trip), still correct.

Watch the hit rate in production:
```bash
curl -s localhost:8080/actuator/metrics/cache.gets | jq
```
A hit rate below ~95% means your window is too short or your cache too small —
you're paying database round trips for retries. Above 99.9% with a large cache
means you're over-provisioned.

---

## Task 4 — Version negotiation

```java
// In AuthChannelInterceptor, on CONNECT:
String clientVersion = accessor.getFirstNativeHeader("pulse-version");
int v = clientVersion == null ? 1 : Integer.parseInt(clientVersion);

if (v < MIN_SUPPORTED_VERSION) {
    throw new UnsupportedProtocolException(
            "client version " + v + " is no longer supported; minimum is " + MIN_SUPPORTED_VERSION);
}
accessor.getSessionAttributes().put("protocolVersion", v);

meterRegistry.counter("chat.connect", "protocol_version", String.valueOf(v)).increment();
```

The metric is the point:
```bash
curl -s localhost:8080/actuator/prometheus | grep chat_connect_total
```
```
chat_connect_total{protocol_version="1",} 84213.0
chat_connect_total{protocol_version="2",} 1902847.0
```

✅ **4.2% of connections are still v1.** Now the deprecation decision is a
business call with a number attached, not a guess. Deprecating without this
metric is how you find out from support tickets.

### v1/v2 coexistence

```java
public Envelope toWire(MessageNew m, int version) {
    return version >= 2
        ? new Envelope(2, "message.new", m.ts(), null,
              json.valueToTree(new V2Data(m.room(), m.id(), m.seq(), m.sender(), m.body())))
        : new Envelope(1, "message.new", m.ts(), m.room(),
              json.valueToTree(m));
}
```

Per-session version means fan-out must serialize **twice** for mixed rooms. That
cost is real (Module 06 will show it), which is an argument for short deprecation
windows — and another reason the metric matters.

---

## Task 5 — Three breaking changes, ranked

| # | Change | Old-client symptom | Detectability |
|---|--------|-------------------|---------------|
| 1 | Add required field to `MessageCreate` | Server rejects with `MethodArgumentNotValidException`; client gets an `error` frame; **every send fails, loudly** | ⭐⭐⭐⭐⭐ Trivial. Error rate goes to 100% and alerts in seconds. |
| 2 | `seq` number → string | JS: `48213 > "48214"` is `false`; gap detection silently stops working; resume never fires. **No error anywhere.** | ⭐⭐ Hard. Nothing throws. Users report "missing messages" days later. |
| 3 | `ts` ms → seconds | Every message displays as **1970-01-21**. Sorting by ts inverts. Retention jobs compute ages 1000× wrong and may **delete recent data**. | ⭐ Nearly invisible to monitoring. |

### Why the third class is the most dangerous

Changes 1 and 2 alter the **shape** of data; change 3 alters its **meaning** while
leaving the shape identical. That difference is everything:

- **No validator can catch it.** `1735689600` and `1735689600123` are both valid
  `long`s. Schema validation, JSON Schema, Protobuf, and type systems all pass.
- **No test catches it** unless a test asserts on a *semantic* property (a
  timestamp is within a plausible range of now) rather than a structural one.
- **It corrupts data at rest.** Shape errors fail at the boundary and nothing is
  written. A meaning error writes plausible-looking wrong values into your
  database, and every downstream consumer — analytics, retention, billing,
  moderation — inherits them. By the time you notice, you cannot distinguish
  correct old rows from incorrect new ones.
- **The failure is delayed and displaced.** The retention job that deletes recent
  messages runs at 3 a.m. three weeks later, and the incident looks like a
  retention bug, not a protocol change.

**Defences:**
- Put units in the field name: `tsMillis`, `expiresAtSeconds`, `sizeBytes`. Ugly;
  prevents an entire bug class.
- Add semantic assertions to contract tests: "a fresh message's `ts` is within
  60 s of `now()`."
- **Never reuse a field name with new semantics.** Add `tsSeconds`, deprecate
  `ts`, delete it a version later. The cost is one field; the alternative is
  unbounded.

---

## Task 6 (stretch) — Lock-free Snowflake

```java
@Component
public class LockFreeSnowflakeIdGenerator {

    private static final long EPOCH = 1_704_067_200_000L;
    private static final int WORKER_BITS = 10, SEQ_BITS = 12;
    private static final long SEQ_MASK = (1L << SEQ_BITS) - 1;

    private final long workerId;
    /** Packs (millis << SEQ_BITS) | sequence into one atomically-updated long. */
    private final AtomicLong state = new AtomicLong();

    public long nextId() {
        long now, prev, next;
        do {
            prev = state.get();
            long prevMillis = prev >>> SEQ_BITS;
            long prevSeq = prev & SEQ_MASK;
            now = System.currentTimeMillis();

            if (now < prevMillis) {
                // Clock went backwards: keep issuing from prevMillis rather than
                // duplicating. Monotonicity beats accuracy for an identifier.
                now = prevMillis;
            }
            long seq = (now == prevMillis) ? (prevSeq + 1) & SEQ_MASK : 0L;
            if (now == prevMillis && seq == 0L) { now = prevMillis + 1; }   // spill forward
            next = (now << SEQ_BITS) | seq;
        } while (!state.compareAndSet(prev, next));

        return ((next >>> SEQ_BITS) - EPOCH) << (WORKER_BITS + SEQ_BITS)
             | (workerId << SEQ_BITS)
             | (next & SEQ_MASK);
    }
}
```

Benchmark (JMH, 8-core, ops/sec):

| Threads | `synchronized` | CAS | Ratio |
|---------|---------------|-----|-------|
| 1 | 84,200,000 | 91,400,000 | 1.09× |
| 8 | 12,800,000 | 41,200,000 | **3.2×** |
| 64 | 9,100,000 | 38,900,000 | **4.3×** |

Pinning check under 10,000 virtual threads:
```bash
java -Djdk.tracePinnedThreads=full -jar pulse.jar
```
```
synchronized version: 4,182 pinning events in 60s
CAS version:              0 pinning events
```

### Is it worth making? An honest answer: **no, not for Pulse.**

The CAS version is 4× faster under contention and eliminates pinning entirely.
And it doesn't matter, because:

1. **The generator is not the bottleneck.** Even the slow version does 9.1M
   IDs/sec. Pulse's target is ~10,000 messages/sec — **three orders of magnitude
   of headroom.** Optimizing this is optimizing 0.1% of a 0.1%.
2. **The pinning is nanoseconds long.** Module 01's warning is about pinning
   across *blocking I/O*, where a carrier is held for milliseconds. Holding one
   for ~40 ns to increment a counter is not a scalability problem — the 4,182
   "pinning events" are real but each lasted about as long as the CAS retry loop
   would have.
3. **The CAS version is meaningfully harder to reason about.** The clock-backwards
   branch and the sequence-spill are subtle, and getting either wrong produces
   duplicate IDs — silently, and permanently, in your message history. The
   `synchronized` version's failure mode is an exception you can see.

**When it *would* be worth it:** if the generator moved into the fan-out path
(an ID per *delivery* rather than per message), 500× amplification would put you
at 5M IDs/sec and the 4× would start mattering.

> **The meta-lesson, and the reason this task exists:** "faster" and "eliminates
> a known anti-pattern" are not sufficient justification. The question is always
> *what is scarce, and does this change it?* A 4× improvement on something with
> 1000× headroom is a rounding error you paid for in review time and risk. Being
> able to say that in an architecture review — with the benchmark in hand — is
> worth more than the optimization.
