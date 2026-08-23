# Lab 05 — Implement the Protocol

**You'll:** build the envelope, Snowflake IDs, per-room sequences, idempotent
send with a dedup cache, the ack ladder, and gap detection — then write tests
that prove a retry doesn't duplicate and a gap is detectable.

⏱️ ~90 min. Work in `spring-boot-chat-course/apps/pulse`.

---

## Part A — The envelope

`src/main/java/com/pulse/protocol/Envelope.java`:

```java
package com.pulse.protocol;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import com.fasterxml.jackson.databind.JsonNode;

/**
 * Every frame on the wire, in both directions, is one of these.
 *
 * ignoreUnknown = true is a PROTOCOL DECISION, not a convenience: it is what
 * lets a v1 client survive a server that adds fields.
 */
@JsonIgnoreProperties(ignoreUnknown = true)
public record Envelope(
        int v,
        String type,
        long ts,
        String room,
        JsonNode data) {

    public static final int VERSION = 1;

    public static Envelope of(String type, String room, JsonNode data) {
        return new Envelope(VERSION, type, System.currentTimeMillis(), room, data);
    }
}
```

`src/main/java/com/pulse/protocol/Payloads.java`:

```java
package com.pulse.protocol;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import jakarta.validation.constraints.*;

public final class Payloads {

    @JsonIgnoreProperties(ignoreUnknown = true)
    public record MessageCreate(
            @NotBlank @Size(max = 40) String clientId,
            @NotBlank @Size(max = 4000) String body,
            String replyTo) {}

    public record MessageAck(String clientId, String id, long seq, long ts) {}

    public record MessageNew(
            String id, String clientId, long seq, String room,
            String sender, String body, long ts, String replyTo) {}

    public record ReadUpto(@Positive long seq) {}

    public record Control(String action, String reason, Long retryAfterMs) {}

    public record Error(String code, String message, String clientId) {}

    private Payloads() {}
}
```

---

## Part B — Snowflake IDs

`src/main/java/com/pulse/protocol/SnowflakeIdGenerator.java`:

```java
package com.pulse.protocol;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

/**
 * 64-bit time-sortable IDs, generated without coordination.
 *
 *  ┌─┬──────────────────────────────────┬──────────┬────────────┐
 *  │0│      timestamp ms (41 bits)      │worker(10)│  seq (12)  │
 *  └─┴──────────────────────────────────┴──────────┴────────────┘
 *
 * 41 bits of ms = ~69 years from the epoch below.
 * 10 bits of worker = 1024 nodes.
 * 12 bits of sequence = 4096 IDs per node per millisecond.
 */
@Component
public class SnowflakeIdGenerator {

    /** 2024-01-01T00:00:00Z. Choosing a recent epoch buys back years of range. */
    private static final long EPOCH = 1_704_067_200_000L;

    private static final int WORKER_BITS = 10;
    private static final int SEQ_BITS = 12;
    private static final long MAX_WORKER = (1L << WORKER_BITS) - 1;
    private static final long SEQ_MASK = (1L << SEQ_BITS) - 1;

    private final long workerId;
    private long lastMillis = -1L;
    private long sequence = 0L;

    public SnowflakeIdGenerator(@Value("${pulse.worker-id:0}") long workerId) {
        if (workerId < 0 || workerId > MAX_WORKER)
            throw new IllegalArgumentException("worker-id must be 0.." + MAX_WORKER);
        this.workerId = workerId;
    }

    /**
     * synchronized is acceptable here despite Module 01's rule: this method never
     * blocks on I/O, so a pinned carrier is released within nanoseconds. The
     * alternative (a CAS loop over a packed long) is measurably faster under
     * extreme contention — see the challenge.
     */
    public synchronized long nextId() {
        long now = System.currentTimeMillis();

        if (now < lastMillis) {
            // Clock went backwards (NTP step). Refusing is better than issuing
            // duplicate IDs: a brief 503 beats permanently corrupted history.
            throw new IllegalStateException(
                    "clock moved backwards by " + (lastMillis - now) + "ms");
        }

        if (now == lastMillis) {
            sequence = (sequence + 1) & SEQ_MASK;
            if (sequence == 0) now = waitNextMillis(lastMillis);   // 4096 exhausted
        } else {
            sequence = 0L;
        }

        lastMillis = now;
        return ((now - EPOCH) << (WORKER_BITS + SEQ_BITS))
             | (workerId << SEQ_BITS)
             | sequence;
    }

    private long waitNextMillis(long last) {
        long now = System.currentTimeMillis();
        while (now <= last) now = System.currentTimeMillis();
        return now;
    }

    public static long timestampOf(long id) {
        return (id >>> (WORKER_BITS + SEQ_BITS)) + EPOCH;
    }

    public static long workerOf(long id) {
        return (id >>> SEQ_BITS) & MAX_WORKER;
    }
}
```

Try it:

```java
// SnowflakeDemo.java
var gen = new SnowflakeIdGenerator(7);
for (int i = 0; i < 3; i++) {
    long id = gen.nextId();
    System.out.printf("%d  ts=%d  worker=%d%n",
        id, SnowflakeIdGenerator.timestampOf(id), SnowflakeIdGenerator.workerOf(id));
}
```

**Expected:**
```
136099384856576000  ts=1735689600123  worker=7
136099384856576001  ts=1735689600123  worker=7
136099384860770304  ts=1735689600124  worker=7
```

✅ Three things to notice: the IDs are **increasing**, the timestamp is
**recoverable**, and the first two differ only in the sequence bits because they
were generated in the same millisecond.

Compare sizes:
```java
System.out.println(Long.toString(136099384856576000L).length());  // 18 chars, 8 bytes
System.out.println(UUID.randomUUID().toString().length());        // 36 chars, 16 bytes
```

---

## Part C — Per-room sequences

Sequences must be monotonic per room and survive restarts. Postgres for now;
Module 09 moves the hot path to Redis.

`src/main/resources/db/migration/V2__messages.sql`:

```sql
CREATE TABLE messages (
    id         bigint      NOT NULL,
    room_id    text        NOT NULL,
    seq        bigint      NOT NULL,
    sender     text        NOT NULL,
    client_id  text        NOT NULL,
    body       text        NOT NULL,
    reply_to   bigint,
    created_at timestamptz NOT NULL DEFAULT now(),
    edited_at  timestamptz,
    deleted_at timestamptz,
    PRIMARY KEY (room_id, seq)
);

-- Scrollback: "last N in this room". Equality column first, range column second.
CREATE INDEX idx_messages_room_id_desc ON messages (room_id, id DESC);

-- THE idempotency guarantee. Without this unique index, ON CONFLICT has nothing
-- to conflict on and retries create duplicates.
CREATE UNIQUE INDEX idx_messages_dedup ON messages (room_id, client_id);

CREATE TABLE room_sequences (
    room_id  text   PRIMARY KEY,
    last_seq bigint NOT NULL DEFAULT 0
);
```

`src/main/java/com/pulse/chat/MessageRepository.java`:

```java
package com.pulse.chat;

import com.pulse.protocol.Payloads.MessageNew;
import org.springframework.jdbc.core.simple.JdbcClient;
import org.springframework.stereotype.Repository;
import org.springframework.transaction.annotation.Transactional;

import java.util.Optional;

@Repository
public class MessageRepository {

    private final JdbcClient jdbc;

    public MessageRepository(JdbcClient jdbc) { this.jdbc = jdbc; }

    /**
     * Allocate the next sequence for a room, atomically.
     *
     * INSERT ... ON CONFLICT DO UPDATE is an atomic upsert-and-increment: the
     * row lock is held only for the duration of this statement, and concurrent
     * callers serialize on it. That serialization is exactly why Module 09 moves
     * this to Redis INCR for the hot path.
     */
    private long nextSeq(String roomId) {
        return jdbc.sql("""
                INSERT INTO room_sequences (room_id, last_seq) VALUES (:room, 1)
                ON CONFLICT (room_id) DO UPDATE SET last_seq = room_sequences.last_seq + 1
                RETURNING last_seq
                """)
                .param("room", roomId)
                .query(Long.class)
                .single();
    }

    /**
     * Idempotent insert. Returns the message that now exists — whether we just
     * created it or a previous attempt did.
     */
    @Transactional
    public InsertResult insertIdempotent(long id, String roomId, String sender,
                                         String clientId, String body, Long replyTo) {

        Optional<MessageNew> existing = findByClientId(roomId, clientId);
        if (existing.isPresent()) {
            return new InsertResult(existing.get(), true);       // it's a retry
        }

        long seq = nextSeq(roomId);

        int inserted = jdbc.sql("""
                INSERT INTO messages (id, room_id, seq, sender, client_id, body, reply_to)
                VALUES (:id, :room, :seq, :sender, :clientId, :body, :replyTo)
                ON CONFLICT (room_id, client_id) DO NOTHING
                """)
                .param("id", id).param("room", roomId).param("seq", seq)
                .param("sender", sender).param("clientId", clientId)
                .param("body", body).param("replyTo", replyTo)
                .update();

        if (inserted == 0) {
            // Lost a race with a concurrent retry of the same clientId.
            // The seq we burned is skipped — see the note below.
            return new InsertResult(findByClientId(roomId, clientId).orElseThrow(), true);
        }

        return new InsertResult(new MessageNew(String.valueOf(id), clientId, seq,
                roomId, sender, body, System.currentTimeMillis(),
                replyTo == null ? null : String.valueOf(replyTo)), false);
    }

    public Optional<MessageNew> findByClientId(String roomId, String clientId) {
        return jdbc.sql("""
                SELECT id, client_id, seq, room_id, sender, body,
                       extract(epoch from created_at)*1000 AS ts, reply_to
                FROM messages WHERE room_id = :room AND client_id = :clientId
                """)
                .param("room", roomId).param("clientId", clientId)
                .query(MessageNew.class)
                .optional();
    }

    public record InsertResult(MessageNew message, boolean wasRetry) {}
}
```

> ⚠️ **The skipped-sequence subtlety.** When two concurrent retries race, one
> allocates a `seq` it then can't use. That leaves a **hole in the sequence** —
> and a client doing gap detection will report a missing message that never
> existed. Module 10 fixes this properly (allocate the sequence only after the
> insert wins). Note it now; the challenge asks you to find it.

---

## Part D — The service, with dedup cache

Hitting Postgres on every send just to check for a retry is wasteful. Put a
bounded in-memory cache in front.

Add Caffeine:
```xml
<dependency>
  <groupId>com.github.ben-manes.caffeine</groupId>
  <artifactId>caffeine</artifactId>
</dependency>
```

`src/main/java/com/pulse/chat/MessageService.java`:

```java
package com.pulse.chat;

import com.github.benmanes.caffeine.cache.Cache;
import com.github.benmanes.caffeine.cache.Caffeine;
import com.pulse.config.PulseProperties;
import com.pulse.protocol.*;
import com.pulse.protocol.Payloads.*;
import io.micrometer.core.instrument.Counter;
import io.micrometer.core.instrument.MeterRegistry;
import org.springframework.stereotype.Service;

@Service
public class MessageService {

    private final MessageRepository repository;
    private final SnowflakeIdGenerator ids;
    private final Cache<String, MessageNew> dedup;
    private final Counter retriesDetected;

    public MessageService(MessageRepository repository, SnowflakeIdGenerator ids,
                          PulseProperties props, MeterRegistry metrics) {
        this.repository = repository;
        this.ids = ids;
        // BOUNDED. An unbounded dedup cache is a memory leak with a nice name.
        this.dedup = Caffeine.newBuilder()
                .maximumSize(200_000)
                .expireAfterWrite(props.fanout().dedupWindow())
                .recordStats()
                .build();
        this.retriesDetected = Counter.builder("chat.send.retry.detected")
                .description("sends recognized as duplicates via clientId")
                .register(metrics);
    }

    public SendResult send(String roomId, String sender, MessageCreate create) {
        String dedupKey = roomId + "|" + create.clientId();

        MessageNew cached = dedup.getIfPresent(dedupKey);
        if (cached != null) {
            retriesDetected.increment();
            return new SendResult(cached, true);          // no DB round trip at all
        }

        var result = repository.insertIdempotent(
                ids.nextId(), roomId, sender, create.clientId(),
                create.body(), parseReplyTo(create.replyTo()));

        dedup.put(dedupKey, result.message());
        if (result.wasRetry()) retriesDetected.increment();
        return new SendResult(result.message(), result.wasRetry());
    }

    private Long parseReplyTo(String s) { return s == null ? null : Long.parseLong(s); }

    public record SendResult(MessageNew message, boolean wasRetry) {}
}
```

> The cache is a **fast path, not the guarantee**. The unique index in Postgres
> is the guarantee. A cache miss (eviction, restart, a different instance) falls
> through to the database and is still correct — just slower. Never invert that:
> a system whose correctness depends on a cache is a system that breaks on
> restart.

---

## Part E — Wire it into the controller with the ack ladder

Replace `ChatController`:

```java
package com.pulse.chat;

import com.pulse.protocol.*;
import com.pulse.protocol.Payloads.*;
import com.fasterxml.jackson.databind.ObjectMapper;
import jakarta.validation.Valid;
import org.springframework.messaging.handler.annotation.*;
import org.springframework.messaging.simp.SimpMessagingTemplate;
import org.springframework.stereotype.Controller;

import java.security.Principal;

@Controller
public class ChatController {

    private final MessageService messages;
    private final SimpMessagingTemplate template;
    private final ObjectMapper json;

    public ChatController(MessageService messages, SimpMessagingTemplate template,
                          ObjectMapper json) {
        this.messages = messages;
        this.template = template;
        this.json = json;
    }

    @MessageMapping("/room.{roomId}/send")
    public void send(@DestinationVariable String roomId,
                     @Payload @Valid MessageCreate create,
                     Principal principal) {

        var result = messages.send(roomId, principal.getName(), create);
        var message = result.message();

        // RUNG 2 of the ack ladder: "queued" — persisted, here's your id and seq.
        // Sent to the sender ONLY, and sent even for a retry so the client's
        // pending bubble resolves either way.
        template.convertAndSendToUser(principal.getName(), "/queue/ack",
                Envelope.of("message.ack", roomId,
                        json.valueToTree(new MessageAck(
                                message.clientId(), message.id(), message.seq(), message.ts()))));

        // A retry must NOT re-broadcast — everyone already has it.
        if (result.wasRetry()) return;

        template.convertAndSend("/topic/room." + roomId,
                Envelope.of("message.new", roomId, json.valueToTree(message)));
    }

    @MessageMapping("/room.{roomId}/read")
    public void read(@DestinationVariable String roomId,
                     @Payload @Valid ReadUpto readUpto,
                     Principal principal) {
        template.convertAndSend("/topic/room." + roomId + ".read",
                Envelope.of("read.update", roomId,
                        json.valueToTree(new ReadUpdate(principal.getName(), readUpto.seq()))));
    }

    public record ReadUpdate(String user, long seq) {}
}
```

Add validation error handling so a bad payload doesn't kill the socket:

```java
@MessageExceptionHandler(MethodArgumentNotValidException.class)
@SendToUser("/queue/errors")
public Envelope onInvalid(MethodArgumentNotValidException e) {
    return Envelope.of("error", null, json.valueToTree(
            new Payloads.Error("invalid_payload", e.getMessage(), null)));
}
```

---

## Part F — Prove idempotency

`src/test/java/com/pulse/chat/IdempotencyTest.java`:

```java
package com.pulse.chat;

import com.pulse.protocol.Payloads.MessageCreate;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.testcontainers.service.connection.ServiceConnection;
import org.springframework.jdbc.core.simple.JdbcClient;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.testcontainers.containers.PostgreSQLContainer;
import org.testcontainers.junit.jupiter.*;

import java.util.concurrent.*;
import java.util.stream.IntStream;

import static org.junit.jupiter.api.Assertions.*;

@SpringBootTest
@Testcontainers
class IdempotencyTest {

    @Container @ServiceConnection
    static PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>("postgres:16-alpine");

    @Autowired MessageService service;
    @Autowired JdbcClient jdbc;

    @Test
    void retryDoesNotDuplicate() {
        var create = new MessageCreate("c-fixed-1", "hello", null);

        var first  = service.send("room.1", "alice", create);
        var second = service.send("room.1", "alice", create);
        var third  = service.send("room.1", "alice", create);

        assertFalse(first.wasRetry());
        assertTrue(second.wasRetry());
        assertTrue(third.wasRetry());

        assertEquals(first.message().id(),  second.message().id(),  "id changed on retry");
        assertEquals(first.message().seq(), second.message().seq(), "seq changed on retry");

        Long count = jdbc.sql("SELECT count(*) FROM messages WHERE room_id='room.1' AND client_id='c-fixed-1'")
                         .query(Long.class).single();
        assertEquals(1L, count, "duplicate row created");
    }

    @Test
    void concurrentRetriesStillProduceOneRow() throws Exception {
        var create = new MessageCreate("c-race-1", "concurrent", null);
        int attempts = 64;
        var barrier = new CyclicBarrier(attempts);
        var results = new ConcurrentLinkedQueue<MessageService.SendResult>();

        try (var ex = Executors.newVirtualThreadPerTaskExecutor()) {
            IntStream.range(0, attempts).forEach(i -> ex.submit(() -> {
                barrier.await();                       // fire simultaneously
                results.add(service.send("room.2", "alice", create));
                return null;
            }));
        }

        Long rows = jdbc.sql("SELECT count(*) FROM messages WHERE room_id='room.2' AND client_id='c-race-1'")
                        .query(Long.class).single();
        assertEquals(1L, rows, "concurrent retries created duplicates");

        long distinctIds = results.stream().map(r -> r.message().id()).distinct().count();
        assertEquals(1L, distinctIds, "callers saw different ids for the same message");
    }
}
```

```bash
./mvnw test -Dtest=IdempotencyTest
```

**Expected:**
```
IdempotencyTest > retryDoesNotDuplicate() PASSED
IdempotencyTest > concurrentRetriesStillProduceOneRow() PASSED

Tests run: 2, Failures: 0
```

✅ Now **break it on purpose**. Drop the unique index:

```sql
DROP INDEX idx_messages_dedup;
```
and disable the cache (`maximumSize(0)`). Re-run:

**Expected:**
```
IdempotencyTest > concurrentRetriesStillProduceOneRow() FAILED
  org.opentest4j.AssertionFailedError:
    concurrent retries created duplicates ==> expected: <1> but was: <7>
```

✅ Seven duplicates from 64 concurrent retries. **The unique index is the
guarantee; the cache is only speed.** Restore both.

---

## Part G — Gap detection on the client

Add to `static/index.html`, inside the `message.new` subscription:

```js
const lastSeq = {};          // room -> highest contiguous seq seen
const pending = {};          // room -> Map(seq -> message) held out of order

client.subscribe('/topic/' + room, frame => {
  const env = JSON.parse(frame.body);
  if (env.type !== 'message.new') return;
  const m = env.data;

  const expected = (lastSeq[env.room] ?? m.seq - 1) + 1;

  if (m.seq < expected) return;                    // duplicate — already have it

  if (m.seq > expected) {
    log(`⚠ GAP: expected seq ${expected}, got ${m.seq} — missing ${m.seq - expected}`, 'sys');
    (pending[env.room] ??= new Map()).set(m.seq, m);
    // Module 10 sends a resume request here. For now, just render it.
  }

  render(m);
  lastSeq[env.room] = m.seq;

  // Drain anything that's now contiguous
  const held = pending[env.room];
  while (held?.has(lastSeq[env.room] + 1)) {
    const next = held.get(++lastSeq[env.room]);
    held.delete(lastSeq[env.room]);
    render(next);
  }
});
```

**Force a gap to prove it works.** Add a debug endpoint that skips a sequence:

```java
@MessageMapping("/room.{roomId}/skip")
public void skipASequence(@DestinationVariable String roomId) {
    messages.burnSequence(roomId);       // allocate a seq and never use it
}
```

```bash
# in the browser console, with the client connected:
client.publish({destination: '/app/room.7/skip', body: '{}'});
# then send a normal message
```

**Expected in the browser log:**
```
⚠ GAP: expected seq 5, got 6 — missing 1
alice: after the gap
```

✅ **The client detected a hole it could not otherwise have known about.** That
is what the sequence number bought you, and it's the foundation of Module 10's
resume.

---

## Part H — Optimistic send and reconciliation

```js
const pendingByClientId = new Map();

function sendMessage(body) {
  const clientId = 'c-' + crypto.randomUUID();
  const bubble = render({ clientId, sender: user, body, ts: Date.now() }, 'pending');
  pendingByClientId.set(clientId, bubble);

  client.publish({
    destination: '/app/' + room + '/send',
    body: JSON.stringify({ clientId, body }),
  });
}

client.subscribe('/user/queue/ack', frame => {
  const ack = JSON.parse(frame.body).data;
  const bubble = pendingByClientId.get(ack.clientId);
  if (bubble) {
    bubble.dataset.state = 'queued';
    bubble.dataset.seq = ack.seq;
    bubble.querySelector('.tick').textContent = '✓';
  }
});

// The broadcast comes back too — do NOT render a second bubble
function render(m, state) {
  if (m.clientId && pendingByClientId.has(m.clientId)) {
    const existing = pendingByClientId.get(m.clientId);
    existing.dataset.state = 'confirmed';
    pendingByClientId.delete(m.clientId);
    return existing;                                 // reuse, don't duplicate
  }
  // ... create a new bubble ...
}
```

Test it under latency:

```bash
sudo tc qdisc add dev lo root netem delay 800ms
```

**Expected:** the message appears **instantly** in grey with no tick, then gets a
`✓` about 1.6 s later, and never appears twice.

```bash
sudo tc qdisc del dev lo root
```

✅ Without the `clientId` match in `render()`, you'd see every message twice.
Try it — comment out the reconciliation block and watch.

---

## What you built

- A versioned, self-describing envelope with forward-compatible parsing.
- Snowflake IDs: time-sortable, coordination-free, 8 bytes.
- Per-room sequences that make gaps **detectable**.
- Idempotent send: a retry is free, proven by a concurrency test that fails
  without the unique index.
- The ack ladder, with the sender's optimistic bubble reconciling on `clientId`.
- Client-side gap detection, demonstrated with a deliberately burned sequence.

Now do [`challenge.md`](./challenge.md).

Then: [Module 06 — The Load-Testing Harness](../06-load-testing-harness/).
