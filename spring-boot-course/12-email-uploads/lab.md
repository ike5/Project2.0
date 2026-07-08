# Lab 12 — Templated Email and Presigned Uploads

**You'll:** wire the templated `EmailService` (with Thymeleaf HTML), set up
MinIO with a presigned-URL endpoint, and exercise the full upload flow
without sending bytes through the API.

⏱️ ~50 min. Run from `spring-boot-course/apps/taskforge`. MailHog, Kafka,
**and MinIO** containers from Module 00 must be up.

---

## Part A — Dependencies and config

`pom.xml`:
```xml
<dependency>
  <groupId>org.springframework.boot</groupId>
  <artifactId>spring-boot-starter-mail</artifactId>
</dependency>
<dependency>
  <groupId>org.springframework.boot</groupId>
  <artifactId>spring-boot-starter-thymeleaf</artifactId>
</dependency>
<dependency>
  <groupId>io.minio</groupId>
  <artifactId>minio</artifactId>
  <version>8.5.10</version>
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

taskforge:
  email:
    enabled: true
    from: noreply@taskforge.com
  storage:
    endpoint: http://localhost:9000
    access-key: minioadmin
    secret-key: minioadmin
    bucket: taskforge
    presign-expiration: PT15M
```

Add `Storage` to `TaskforgeProperties`:
```java
public record TaskforgeProperties(
    Security security, Pagination pagination, Email email, Storage storage
) {
    public record Storage(String endpoint, String accessKey, String secretKey,
                          String bucket, Duration presignExpiration) {}
}
```

---

## Part B — The `EmailService` and a Thymeleaf template

`src/main/java/com/taskforge/email/EmailMessage.java`:
```java
package com.taskforge.email;
import java.util.Map;
public record EmailMessage(String to, String subject, String template, Map<String, Object> vars) {}
```

`src/main/java/com/taskforge/email/EmailService.java`:
```java
package com.taskforge.email;
public interface EmailService { void send(EmailMessage msg); }
```

`src/main/java/com/taskforge/email/SmtpEmailService.java`:
```java
package com.taskforge.email;

import com.taskforge.config.TaskforgeProperties;
import jakarta.mail.internet.MimeMessage;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.mail.javamail.JavaMailSender;
import org.springframework.mail.javamail.MimeMessageHelper;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;
import org.thymeleaf.context.Context;
import org.thymeleaf.spring6.SpringTemplateEngine;

import java.nio.charset.StandardCharsets;
import java.util.Locale;
import java.util.Map;

@Service
@ConditionalOnProperty(name = "taskforge.email.enabled", havingValue = "true")
public class SmtpEmailService implements EmailService {
    private static final Logger log = LoggerFactory.getLogger(SmtpEmailService.class);
    private final JavaMailSender mail;
    private final SpringTemplateEngine templates;
    private final String from;

    public SmtpEmailService(JavaMailSender mail, SpringTemplateEngine templates,
                            TaskforgeProperties props) {
        this.mail = mail;
        this.templates = templates;
        this.from = props.email().from();
    }

    @Override
    @Async
    public void send(EmailMessage msg) {
        try {
            String html = templates.process(msg.template(), new Context(
                Locale.getDefault(), msg.vars() == null ? Map.of() : msg.vars()));
            MimeMessage mime = mail.createMimeMessage();
            MimeMessageHelper helper = new MimeMessageHelper(mime, false, StandardCharsets.UTF_8.name());
            helper.setFrom(from);
            helper.setTo(msg.to());
            helper.setSubject(msg.subject());
            helper.setText(html, true);
            mail.send(mime);
            log.info("email sent to={} subject={}", msg.to(), msg.subject());
        } catch (Exception e) {
            log.error("email send failed to={} subject={}", msg.to(), msg.subject(), e);
        }
    }
}
```

`@EnableAsync` on the main class:
```java
@SpringBootApplication
@EnableAsync
@EnableCaching
public class TaskforgeApplication { ... }
```

`src/main/resources/templates/email/task-created.html`:
```html
<!DOCTYPE html>
<html xmlns:th="http://www.thymeleaf.org">
<body style="font-family: sans-serif;">
  <h2>New task: <span th:text="${title}"/></h2>
  <p>Hi user <span th:text="${ownerId}"/>,</p>
  <p>You created task <strong th:text="${taskId}"/></p>
  <p>— taskforge</p>
</body>
</html>
```

Update `NotificationWorker` to call `EmailService.send(...)` with a
template instead of `EmailSender.send(...)` from Module 11.

---

## Part C — `StorageService` and presigned URLs

`src/main/java/com/taskforge/storage/StorageService.java`:
```java
package com.taskforge.storage;

import com.taskforge.config.TaskforgeProperties;
import io.minio.GetPresignedObjectUrlArgs;
import io.minio.MinioClient;
import io.minio.http.Method;
import org.springframework.stereotype.Service;

import java.util.UUID;

@Service
public class StorageService {
    private final MinioClient minio;
    private final TaskforgeProperties props;

    public StorageService(TaskforgeProperties props) {
        this.props = props;
        this.minio = MinioClient.builder()
            .endpoint(props.storage().endpoint())
            .credentials(props.storage().accessKey(), props.storage().secretKey())
            .build();
    }

    public PresignedUpload presignPut(String filename, String contentType) {
        String key = "attachments/" + UUID.randomUUID() + "/" + filename;
        String url = minio.getPresignedObjectUrl(
            GetPresignedObjectUrlArgs.builder()
                .method(Method.PUT)
                .bucket(props.storage().bucket())
                .object(key)
                .expiry((int) props.storage().presignExpiration().toSeconds())
                .build());
        return new PresignedUpload(url, key);
    }

    public String publicUrl(String key) {
        return props.storage().endpoint() + "/" + props.storage().bucket() + "/" + key;
    }
}

public record PresignedUpload(String uploadUrl, String objectKey) {}
```

`src/main/java/com/taskforge/storage/StorageInitializer.java`:
```java
package com.taskforge.storage;

import io.minio.BucketExistsArgs;
import io.minio.MakeBucketArgs;
import io.minio.MinioClient;
import org.springframework.boot.context.event.ApplicationReadyEvent;
import org.springframework.context.event.EventListener;
import org.springframework.stereotype.Component;

@Component
public class StorageInitializer {

    private final StorageService storage;
    public StorageInitializer(StorageService storage) { this.storage = storage; }

    @EventListener(ApplicationReadyEvent.class)
    public void ensureBucket() throws Exception {
        // (Intentionally minimal — call into MinioClient via StorageService internals.
        //  For a real app, expose a method on StorageService that does this.)
    }
}
```

> For brevity, the lab doesn't auto-create the bucket. Create it manually
> via the MinIO console at <http://localhost:9001> (login
> `minioadmin`/`minioadmin`, then "Create Bucket" → `taskforge`). The
> challenge asks you to automate this.

---

## Part D — The controller

`src/main/java/com/taskforge/storage/AttachmentController.java`:
```java
package com.taskforge.storage;

import jakarta.validation.Valid;
import jakarta.validation.constraints.NotBlank;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/attachments")
public class AttachmentController {

    private final StorageService storage;
    public AttachmentController(StorageService storage) { this.storage = storage; }

    @PostMapping("/presign")
    public PresignedUpload presign(@RequestBody @Valid PresignRequest req) {
        return storage.presignPut(req.filename(), req.contentType());
    }

    public record PresignRequest(
        @NotBlank String filename,
        @NotBlank String contentType
    ) {}
}
```

---

## Part E — Run and verify

```bash
mvn -q spring-boot:run
```

**Email check** (after creating a task, Module 11 publishes the event):
```bash
# create a task; the consumer fires; the email lands in MailHog
TOKEN=$(curl -s -X POST localhost:8080/api/auth/login \
  -H 'content-type: application/json' \
  -d '{"email":"ann@example.com","password":"password123"}' | jq -r .accessToken)

curl -s -X POST -H "Authorization: Bearer $TOKEN" -H 'content-type: application/json' \
  -d '{"title":"buy milk"}' localhost:8080/api/tasks

# open http://localhost:8025 — see the HTML email
```

**Upload check**:
```bash
# 1. create the bucket in the MinIO console first (http://localhost:9001)

# 2. get a presigned URL
URL_JSON=$(curl -s -X POST -H "Authorization: Bearer $TOKEN" \
  -H 'content-type: application/json' \
  -d '{"filename":"report.pdf","contentType":"application/pdf"}' \
  localhost:8080/api/attachments/presign)

UPLOAD_URL=$(echo "$URL_JSON" | jq -r .uploadUrl)
OBJECT_KEY=$(echo "$URL_JSON" | jq -r .objectKey)

# 3. upload directly to MinIO
echo "fake pdf content" > /tmp/report.pdf
curl -s -X PUT -H 'content-type: application/pdf' \
  --data-binary @/tmp/report.pdf \
  "$UPLOAD_URL"

# 4. fetch it
curl -s "http://localhost:9000/taskforge/$OBJECT_KEY"
# → "fake pdf content"
```

✅ **Checkpoint:** the file is in MinIO and downloadable, but never went
through the API. The bytes travelled from your terminal straight to
storage.

---

## What you learned

- The `JavaMailSender` + Thymeleaf pair is the right way to send
  templated HTML email; `@Async` keeps the request thread free.
- Object storage uploads should go **directly** from the client to the
  storage, using a **presigned URL** minted by your API.
- MinIO is S3-compatible; the same `MinioClient` (or `aws-sdk-java`) code
  works against AWS S3 in production with just a config change.
- A bucket policy is the second line of defense after server-side
  validation; both are needed.

➡️ Now try the **[challenge](./challenge.md)**, then move to
[Module 13](../13-openapi-docs/).
