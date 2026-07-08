# Module 11 — Async Messaging with Kafka

**Goal:** publish **events** when interesting things happen ("task created",
"task completed") and consume them in a notification worker. By the end of
this module, "send the user an email when a task is assigned" no longer
blocks the API request — it's a background concern handled by a separate
consumer.

⏱️ ~3 hours · 🎯 Prereq: Modules 02–10 complete (cached, secure, tested app).

> Async messaging is the "decouple things that don't need to be in the
> same request" pattern. Used well, it turns tightly-coupled code into
> independent services that can fail and scale on their own.

---

## 1. Why async messaging?

**Synchronous (REST):**
```
HTTP POST /api/tasks
  ▼
TaskService.create(...)
  ▼
DB INSERT
  ▼
EmailSender.send(...)         ← slow, may fail, blocks the response
  ▼
SlackNotifier.post(...)        ← slow, may fail
  ▼
HTTP 201
```
If any of these is slow or down, the user is waiting or seeing an error.

**Asynchronous (events):**
```
HTTP POST /api/tasks
  ▼
TaskService.create(...)
  ▼
DB INSERT
  ▼
KafkaTemplate.send("task.events", TaskCreated)  ~2 ms
  ▼
HTTP 201                            ← user is happy

  ... later, in a different process ...

NotificationWorker
  ▼
@KafkaListener receives TaskCreated
  ▼
EmailSender.send(...)
  ▼
SlackNotifier.post(...)
```

The notification failures don't impact the API. The notification worker
scales independently. **The trade-off:** eventual consistency.

---

## 2. Kafka in 90 seconds

Kafka is a **distributed commit log**. Producers write events to **topics**;
consumers read them at their own pace.

```
Producer                Topic "task.events"          Consumer
   │                          │                         │
   │──send("task.created", {…})──▶  [partition 0]        │
   │                          │     msg 1 ───────────────│
   │                          │     msg 2                │
   │                          │     msg 3 ───────────────│── handle
   │                          │                          │
```

**Key concepts:**

| Term | What it is |
|------|-----------|
| **Topic** | A named stream of events |
| **Partition** | A topic is split into ordered partitions. Each partition is owned by one consumer in a group at a time. |
| **Offset** | The position of a message in a partition. Consumers track their own offset. |
| **Consumer group** | A set of consumers that share the work of a topic |
| **Broker** | A Kafka server. A cluster is 3+ brokers. |
| **Producer** | Anything that sends messages |
| **Consumer** | Anything that reads messages |
| **Replication factor** | How many brokers store each partition. 3 is the production standard. |

For this course you have **one broker** (the dev container). In Module 16+
the same code runs against a 3-broker cluster — no app changes.

---

## 3. The `spring-kafka` starter

`pom.xml`:
```xml
<dependency>
  <groupId>org.springframework.kafka</groupId>
  <artifactId>spring-kafka</artifactId>
</dependency>
```

`application.yml`:
```yaml
spring:
  kafka:
    bootstrap-servers: localhost:9092
    producer:
      key-serializer:   org.apache.kafka.common.serialization.StringSerializer
      value-serializer: org.springframework.kafka.support.serializer.JsonSerializer
      acks: all
      properties:
        enable.idempotence: true
    consumer:
      group-id: taskforge
      key-deserializer:   org.apache.kafka.common.serialization.StringDeserializer
      value-deserializer: org.springframework.kafka.support.serializer.JsonDeserializer
      auto-offset-reset: earliest
      properties:
        spring.json.trusted.packages: com.taskforge.*
```

> **Why `enable.idempotence: true`?** Prevents the producer from
> accidentally writing the same message twice on retry.
> **Why `JsonSerializer`?** You publish objects, not bytes. The
> deserializer needs the same trust list.

---

## 4. The event

`src/main/java/com/taskforge/events/TaskEvent.java`:
```java
package com.taskforge.events;

import java.time.Instant;

public record TaskEvent(
    String type,        // "task.created", "task.updated", "task.completed"
    Long taskId,
    String title,
    Long ownerId,
    String traceId,
    Instant occurredAt
) {
    public static TaskEvent created(Task t, String traceId) {
        return new TaskEvent("task.created", t.getId(), t.getTitle(), t.getOwnerId(), traceId, Instant.now());
    }
    public static TaskEvent completed(Task t, String traceId) {
        return new TaskEvent("task.completed", t.getId(), t.getTitle(), t.getOwnerId(), traceId, Instant.now());
    }
}
```

> **Events are facts, not commands.** Past tense ("task was created"),
> immutable, named after the thing that happened. No "create task" or
> "send email" verbs.

---

## 5. The publisher

```java
@Service
public class TaskEventPublisher {
    private static final Logger log = LoggerFactory.getLogger(TaskEventPublisher.class);
    private final KafkaTemplate<String, TaskEvent> kafka;

    public TaskEventPublisher(KafkaTemplate<String, TaskEvent> kafka) { this.kafka = kafka; }

    public void publish(TaskEvent event) {
        // partition key = ownerId so all events for one user land in order
        kafka.send("task.events", String.valueOf(event.ownerId()), event)
            .whenComplete((result, ex) -> {
                if (ex != null) log.error("kafka send failed for {}", event, ex);
                else log.info("kafka sent {} offset={} traceId={}",
                    event.type(), result.getRecordMetadata().offset(), event.traceId());
            });
    }
}
```

`TaskService`:
```java
public Task create(String title, String description, Long ownerId) {
    if (title == null || title.isBlank()) throw new IllegalArgumentException("title is required");
    Task t = new Task(title.trim(), description);
    t.setOwnerId(ownerId);
    Task saved = repo.save(t);
    events.publish(TaskEvent.created(saved, MDC.get("traceId")));
    return saved;
}

public Task update(Long id, ..., Long requesterId) {
    // ...
    Task saved = repo.save(t);
    String type = saved.isDone() ? "task.completed" : "task.updated";
    events.publish(new TaskEvent(type, saved.getId(), saved.getTitle(), saved.getOwnerId(), MDC.get("traceId"), Instant.now()));
    return saved;
}
```

---

## 6. The consumer

`src/main/java/com/taskforge/notifications/NotificationWorker.java`:
```java
@Component
public class NotificationWorker {

    private static final Logger log = LoggerFactory.getLogger(NotificationWorker.class);
    private final EmailSender email;

    public NotificationWorker(EmailSender email) { this.email = email; }

    @KafkaListener(topics = "task.events", groupId = "taskforge-notifier")
    public void onTaskEvent(TaskEvent event) {
        try {
            MDC.put("traceId", event.traceId() == null ? "n/a" : event.traceId());
            log.info("received {} for task {}", event.type(), event.taskId());
            switch (event.type()) {
                case "task.created"   -> handleCreated(event);
                case "task.completed" -> handleCompleted(event);
                default               -> log.debug("ignored {}", event.type());
            }
        } finally {
            MDC.remove("traceId");
        }
    }

    private void handleCreated(TaskEvent e) {
        // look up the owner's email, send a "new task" notification
        email.send("user-" + e.ownerId() + "@taskforge.com",
                   "New task: " + e.title(),
                   "Task " + e.taskId() + " was created");
    }

    private void handleCompleted(TaskEvent e) {
        // send a "task done" notification
    }
}
```

> The consumer runs in the **same JVM** as the API by default. For real
> isolation, run it in a separate Spring Boot app pointing at the same
> Kafka. That's a deployment detail; the code is identical.

---

## 7. Error handling — retries and the DLQ

A consumer that throws will keep getting the same message forever
(by default). The right pattern:

```java
@KafkaListener(topics = "task.events", groupId = "taskforge-notifier")
@RetryableTopic(
    attempts = "4",
    backoff = @Backoff(delay = 1000, multiplier = 2.0),
    dltStrategy = DltStrategy.FAIL_ON_ERROR
)
public void onTaskEvent(TaskEvent event) { ... }
```

Spring Kafka auto-creates:
- `task.events-retry-0`, `-retry-1`, … (delayed retries)
- `task.events-dlt` (the **dead letter topic** — messages that exhausted
  retries)

> Manually inspect the DLT for poison messages, fix the bug, and replay.

If you prefer manual control:
```java
@KafkaListener(topics = "task.events", groupId = "taskforge-notifier")
public void onTaskEvent(TaskEvent event, @Header(KafkaHeaders.DELIVERY_ATTEMPT) int attempt) {
    try {
        handle(event);
    } catch (Exception e) {
        if (attempt >= 3) {
            kafka.send("task.events-dlt", event.ownerId().toString(), event);
            return;
        }
        throw e;     // Kafka will redeliver
    }
}
```

---

## 8. Idempotency

A consumer may receive the same message twice (a producer retry, a
rebalance). The handler should be **idempotent** — running it twice has
the same effect as once.

For "send email" the right pattern is a **dedup table**:

```java
@KafkaListener(...)
public void onTaskEvent(TaskEvent event) {
    if (processedRepo.existsByEventIdAndConsumer(event.eventId(), "notifier")) return;
    try {
        email.send(...);
        processedRepo.save(new ProcessedEvent(event.eventId(), "notifier"));
    } catch (Exception e) { /* retry */ }
}
```

`eventId` should be unique per event (UUID or `taskId + type`).

---

## 9. Outbox pattern — for exactly-once-feel

If you write to Postgres *and* publish to Kafka in the same code path,
they can disagree: DB succeeded, Kafka failed (or vice versa). The
**transactional outbox** fixes this:

```
TaskService.create(...)
   ▼ (one transaction)
  ├── INSERT task
  └── INSERT INTO outbox(type, payload, created_at)
  ▼
A scheduled poller reads OUTBOX and publishes to Kafka
  ▼
After publish success: DELETE FROM outbox
```

The DB is the source of truth. Kafka is eventually consistent. This is
how every "exactly-once" messaging system works under the hood.

For this course, the simpler "publish after save" is fine — accept the
rare case where the publish fails and the event is lost. The outbox
pattern is a 30-line addition in the challenge.

---

## 10. Testing async code

```java
@SpringBootTest
@Testcontainers
class NotificationWorkerIT {
    @Container static KafkaContainer kafka = new KafkaContainer(
        DockerImageName.parse("confluentinc/cp-kafka:7.6.0"));

    @DynamicPropertySource static void p(DynamicPropertyRegistry r) {
        r.add("spring.kafka.bootstrap-servers", kafka::getBootstrapServers);
    }

    @Autowired KafkaTemplate<String, TaskEvent> kafka;
    @MockBean EmailSender email;

    @Test
    void receivesTaskCreatedEvent() throws Exception {
        var event = new TaskEvent("task.created", 1L, "buy milk", 42L, "trace-1", Instant.now());
        kafka.send("task.events", "42", event).get();

        await().atMost(Duration.ofSeconds(5)).untilAsserted(() -> {
            verify(email).send(any(), any(), any());
        });
    }
}
```

`awaitility` makes waiting for async work readable.

---

## 11. Common pitfalls

| Symptom | Cause | Fix |
|---------|-------|-----|
| Consumer never sees the message | `auto-offset-reset: latest` and the producer wrote before the consumer started | `earliest`, or send a message after the consumer is up |
| `JsonDeserializer` can't read the message | Class isn't in the trusted packages list | Add to `spring.json.trusted.packages` |
| Message processed twice | At-least-once delivery + non-idempotent handler | Add a dedup table |
| `ClassCastException` on the consumer | The producer serialized a different class | Keep event schemas in one module shared between publisher and consumer |
| `UnknownTopicException` | The topic doesn't exist and auto-create is off | Set `auto.create.topics.enable=true` in dev; create topics in prod |
| Producer blocks forever | Kafka is down and `max.block.ms` is the default 60s | Lower it: `spring.kafka.producer.properties.max.block.ms=5000` |

---

## 12. Do the lab

Publish `TaskEvent` from `TaskService.create(...)` and `update(...)`, and
consume them in a `NotificationWorker` that uses MailHog.

👉 **[lab.md](./lab.md)**

Then test yourself: 👉 **[challenge.md](./challenge.md)**

---

## Key terms (see [GLOSSARY](../GLOSSARY.md))

Kafka · topic · partition · offset · consumer group · broker · producer · consumer · `KafkaTemplate` · `@KafkaListener` · `@RetryableTopic` · dead letter topic (DLT) · idempotency · outbox pattern · `JsonSerializer` / `JsonDeserializer` · `enable.idempotence` · `acks=all` · `MDC` · trace id

**Next →** [Module 12: Email & File Uploads](../12-email-uploads/)
