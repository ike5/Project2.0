# Lab 11 — Publish and Consume Task Events

**You'll:** publish `TaskEvent` from `TaskService` and consume them in a
`NotificationWorker` that uses the MailHog fake SMTP. Confirm by watching
MailHog's inbox.

⏱️ ~60 min. Run from `spring-boot-course/apps/taskforge`. Postgres, Redis,
**and Kafka** containers from Module 00 must be up.

---

## Part A — Add the dependency

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

---

## Part B — The event

`src/main/java/com/taskforge/events/TaskEvent.java`:
```java
package com.taskforge.events;
import java.time.Instant;

public record TaskEvent(
    String type, Long taskId, String title, Long ownerId, String traceId, Instant occurredAt
) {
    public static TaskEvent created(Task t, String traceId) {
        return new TaskEvent("task.created", t.getId(), t.getTitle(), t.getOwnerId(), traceId, Instant.now());
    }
    public static TaskEvent completed(Task t, String traceId) {
        return new TaskEvent("task.completed", t.getId(), t.getTitle(), t.getOwnerId(), traceId, Instant.now());
    }
}
```

---

## Part C — The publisher

`src/main/java/com/taskforge/events/TaskEventPublisher.java`:
```java
package com.taskforge.events;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.stereotype.Service;

@Service
public class TaskEventPublisher {
    private static final Logger log = LoggerFactory.getLogger(TaskEventPublisher.class);
    private final KafkaTemplate<String, TaskEvent> kafka;

    public TaskEventPublisher(KafkaTemplate<String, TaskEvent> kafka) { this.kafka = kafka; }

    public void publish(TaskEvent event) {
        kafka.send("task.events", String.valueOf(event.ownerId()), event)
            .whenComplete((r, ex) -> {
                if (ex != null) log.error("kafka send failed {}", event, ex);
                else log.info("kafka sent {} offset={}", event.type(),
                    r.getRecordMetadata().offset());
            });
    }
}
```

Inject into `TaskService` and call from `create(...)` and `update(...)`:
```java
public Task create(String title, String description, Long ownerId) {
    if (title == null || title.isBlank()) throw new IllegalArgumentException("title is required");
    Task t = new Task(title.trim(), description);
    t.setOwnerId(ownerId);
    Task saved = repo.save(t);
    events.publish(TaskEvent.created(saved, MDC.get("traceId")));
    return saved;
}
```

---

## Part D — A MailHog-backed `EmailSender`

> We'll add a real `EmailSender` in Module 12. For now, a simple
> `JavaMailSender` wired to MailHog will do.

`pom.xml`:
```xml
<dependency>
  <groupId>org.springframework.boot</groupId>
  <artifactId>spring-boot-starter-mail</artifactId>
</dependency>
```

`application.yml`:
```yaml
spring:
  mail:
    host: localhost
    port: 1025
    properties:
      mail.smtp.auth: false
      mail.smtp.starttls.enable: false
```

`src/main/java/com/taskforge/email/EmailSender.java` (interface):
```java
package com.taskforge.email;
public interface EmailSender {
    void send(String to, String subject, String body);
}
```

`src/main/java/com/taskforge/email/SmtpEmailSender.java`:
```java
package com.taskforge.email;

import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.mail.SimpleMailMessage;
import org.springframework.mail.javamail.JavaMailSender;
import org.springframework.stereotype.Component;

@Component
@ConditionalOnProperty(name = "taskforge.email.enabled", havingValue = "true")
public class SmtpEmailSender implements EmailSender {
    private final JavaMailSender mail;
    public SmtpEmailSender(JavaMailSender mail) { this.mail = mail; }
    public void send(String to, String subject, String body) {
        var msg = new SimpleMailMessage();
        msg.setFrom("noreply@taskforge.com");
        msg.setTo(to); msg.setSubject(subject); msg.setText(body);
        mail.send(msg);
    }
}
```

Set `taskforge.email.enabled: true` in `application.yml`.

---

## Part E — The consumer

`src/main/java/com/taskforge/notifications/NotificationWorker.java`:
```java
package com.taskforge.notifications;

import com.taskforge.email.EmailSender;
import com.taskforge.events.TaskEvent;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.slf4j.MDC;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.stereotype.Component;

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
                case "task.created"   -> email.send("user@example.com", "New task: " + event.title(), "Task " + event.taskId() + " was created.");
                case "task.completed" -> email.send("user@example.com", "Task done: " + event.title(), "Task " + event.taskId() + " is done.");
                default -> log.debug("ignored {}", event.type());
            }
        } finally {
            MDC.remove("traceId");
        }
    }
}
```

---

## Part F — Run and verify

```bash
mvn -q spring-boot:run
```

In another terminal:
```bash
# get a token and create a task
TOKEN=$(curl -s -X POST localhost:8080/api/auth/login \
  -H 'content-type: application/json' \
  -d '{"email":"ann@example.com","password":"password123"}' | jq -r .accessToken)

TID=$(curl -s -X POST -H "Authorization: Bearer $TOKEN" \
  -H 'content-type: application/json' \
  -d '{"title":"buy milk"}' localhost:8080/api/tasks | jq -r .id)

# mark it done
curl -s -X PUT -H "Authorization: Bearer $TOKEN" \
  -H 'content-type: application/json' \
  -d '{"done":true}' localhost:8080/api/tasks/$TID
```

Open <http://localhost:8025> — MailHog shows two emails:
- "New task: buy milk"
- "Task done: buy milk"

✅ **Checkpoint:** a synchronous `POST /api/tasks` triggered an async email
through Kafka.

> The API never blocks on the email. If MailHog were down, the
> `TaskEventPublisher` would log the failure and the API would still
> return `201`.

---

## What you learned

- `KafkaTemplate.send(topic, key, value)` publishes events; the **key**
  decides the partition (so all events for one user land in order).
- `@KafkaListener` registers a consumer in a **consumer group** — multiple
  instances share the partitions.
- `acks=all` + `enable.idempotence=true` make the producer safe under
  retries.
- Putting the trace id in the event and reading it in the consumer
  stitches logs together across processes.
- Errors in the consumer don't affect the producer; the **DLT** catches
  poison messages.

➡️ Now try the **[challenge](./challenge.md)**, then move to
[Module 12](../12-email-uploads/).
