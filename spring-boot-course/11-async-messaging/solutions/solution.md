# Challenge 11 — Reference Solution

### 1. `@RetryableTopic`
```java
@RetryableTopic(
    attempts = "4",
    backoff = @Backoff(delay = 1000, multiplier = 2.0),
    dltStrategy = DltStrategy.FAIL_ON_ERROR
)
@KafkaListener(topics = "task.events", groupId = "taskforge-notifier")
public void onTaskEvent(TaskEvent event) { ... }
```
Auto-creates `task.events-retry-0..3` and `task.events-dlt`.

### 2. Outbox pattern
```sql
-- V7__create_outbox_event.sql
CREATE TABLE outbox_event (
    id           BIGSERIAL PRIMARY KEY,
    type         VARCHAR(50) NOT NULL,
    payload      JSONB       NOT NULL,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    published_at TIMESTAMPTZ
);
CREATE INDEX idx_outbox_unpublished ON outbox_event(id) WHERE published_at IS NULL;
```
```java
@Component
public class OutboxPoller {
    private final OutboxRepository outbox;
    private final KafkaTemplate<String, TaskEvent> kafka;

    @Scheduled(fixedDelay = 1000)
    @Transactional
    public void publish() {
        var batch = outbox.findTop100ByPublishedAtIsNullOrderById();
        for (var e : batch) {
            kafka.send("task.events", e.getAggregateId(), e.toEvent());
            e.setPublishedAt(Instant.now());
        }
    }
}
```

### 3. Idempotency
```java
@Entity @Table(name = "processed_event",
    uniqueConstraints = @UniqueConstraint(columnNames = {"event_id", "consumer"}))
public class ProcessedEvent {
    @Id @GeneratedValue private Long id;
    private String eventId; private String consumer;
    private Instant processedAt;
    // ...
}
```
```java
@KafkaListener(...)
public void onTaskEvent(TaskEvent event) {
    if (processed.existsByEventIdAndConsumer(event.eventId(), "notifier")) return;
    handle(event);
    processed.save(new ProcessedEvent(event.eventId(), "notifier"));
}
```

### 4. Multiple consumer groups
```java
@KafkaListener(topics = "task.events", groupId = "taskforge-notifier")
public void onTaskEventNotify(TaskEvent e) { /* email */ }

@KafkaListener(topics = "task.events", groupId = "taskforge-analytics")
public void onTaskEventAnalytics(TaskEvent e) { log.info("analytics: received {}", e); }
```
Inspect with:
```bash
docker compose exec kafka kafka-consumer-groups.sh \
  --bootstrap-server localhost:9092 --list
# → taskforge-notifier, taskforge-analytics
```

### 5. Trace id headers
```java
// producer
kafka.send(new ProducerRecord<>("task.events", null, key, value) {{
    headers().add("X-Trace-Id", event.traceId().getBytes());
}});

// consumer
@KafkaListener(...)
public void onTaskEvent(TaskEvent e, @Header(name = "X-Trace-Id", required = false) byte[] traceId) {
    MDC.put("traceId", traceId == null ? "n/a" : new String(traceId));
    // ...
}
```

### 6. Separate worker module (stretch)
```xml
<!-- taskforge-worker/pom.xml inherits from taskforge/pom.xml -->
<dependencies>
  <dependency><groupId>com.taskforge</groupId><artifactId>taskforge-events</artifactId></dependency>
  <dependency><groupId>org.springframework.boot</groupId><artifactId>spring-boot-starter</artifactId></dependency>
  <dependency><groupId>org.springframework.kafka</groupId><artifactId>spring-kafka</artifactId></dependency>
</dependencies>
```
The worker is a Spring Boot app with `@SpringBootApplication` and
`@EnableKafka`. Run with `mvn -pl taskforge-worker spring-boot:run`.

> This is the architecture of every microservice platform you've used:
> one database per service, events between them, separate deployable
> JARs. Module 16's capstone deploys the API and the worker as separate
> containers.
