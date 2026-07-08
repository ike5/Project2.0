# Module 12 — Email & File Uploads

**Goal:** send real emails through a transactional email service (MailHog in
dev), and accept file uploads without streaming bytes through the API.
You'll learn the **`spring-boot-starter-mail`** integration, the **presigned
URL** pattern for object storage, and MinIO as a dev-time S3.

⏱️ ~2.5 hours · 🎯 Prereq: Modules 02–11 complete (Kafka + email + security wired).

> Email and uploads are two of the "real product" features that distinguish
> a toy from a service. Both have a few sharp edges — this module walks
> through the right patterns.

---

## 1. The email story so far

Module 11 sent emails through `JavaMailSender` + MailHog. This module
formalizes it: a proper `EmailService` with **templates**, **HTML bodies**,
and **async sending** so the request never blocks on SMTP.

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
```

> **Thymeleaf?** Yes — for email templates. Thymeleaf works for both web
> and email. We use the same template engine for both.

---

## 2. The configuration

`application.yml`:
```yaml
spring:
  mail:
    host: ${SMTP_HOST:localhost}
    port: ${SMTP_PORT:1025}
    username: ${SMTP_USER:}
    password: ${SMTP_PASSWORD:}
    properties:
      mail.smtp.auth: ${SMTP_AUTH:false}
      mail.smtp.starttls.enable: ${SMTP_TLS:false}
taskforge:
  email:
    enabled: ${TASKFORGE_EMAIL_ENABLED:true}
    from: ${EMAIL_FROM:noreply@taskforge.com}
```

---

## 3. The `EmailService`

```java
public interface EmailService {
    void send(EmailMessage msg);
}

public record EmailMessage(String to, String subject, String template, Map<String, Object> vars) {}
```

```java
@Service
@ConditionalOnProperty(name = "taskforge.email.enabled", havingValue = "true")
public class SmtpEmailService implements EmailService {

    private final JavaMailSender mail;
    private final SpringTemplateEngine templates;
    private final String from;

    public SmtpEmailService(JavaMailSender mail,
                            SpringTemplateEngine templates,
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
            var mime = mailSender.createMimeMessage();
            var helper = new MimeMessageHelper(mime, false, "UTF-8");
            helper.setFrom(from);
            helper.setTo(msg.to());
            helper.setSubject(msg.subject());
            helper.setText(html, true);
            mail.send(mime);
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

> **Why `@Async`?** A slow SMTP server shouldn't block the API request.
> With `@Async`, the call returns immediately and the email sends on a
> background thread.

---

## 4. The email template

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

Send it from the consumer (Module 11):
```java
@KafkaListener(topics = "task.events", groupId = "taskforge-notifier")
public void onTaskEvent(TaskEvent event) {
    if (!"task.created".equals(event.type())) return;
    email.send(new EmailMessage(
        "user@example.com",
        "New task: " + event.title(),
        "email/task-created",
        Map.of("title", event.title(),
               "ownerId", event.ownerId(),
               "taskId",  event.taskId())));
}
```

---

## 5. File uploads — the right way

The wrong way: `multipart/form-data` POSTs the file **through your API**.
This blocks a request thread, doubles your bandwidth, and forces the API
to handle binary data it's not good at.

The right way: the API **mints a presigned URL**, the browser uploads
**directly** to object storage. The API never sees the bytes.

```
1. Client → API:  POST /api/attachments/presign
                   { filename: "report.pdf", contentType: "application/pdf" }
   API   → Client: { uploadUrl: "https://minio.../report.pdf?X-Amz-...",
                     publicUrl: "https://minio.../report.pdf" }

2. Client → MinIO: PUT <uploadUrl>  (binary upload, no API in the path)

3. Client → API:   POST /api/tasks/{id}/attachments
                    { url: "https://minio.../report.pdf", filename: "report.pdf" }
```

The API is small and fast. Storage does what storage is good at.

---

## 6. The MinIO client

`pom.xml`:
```xml
<dependency>
  <groupId>io.minio</groupId>
  <artifactId>minio</artifactId>
  <version>8.5.10</version>
</dependency>
```

`application.yml`:
```yaml
taskforge:
  storage:
    endpoint: http://localhost:9000
    access-key: minioadmin
    secret-key: minioadmin
    bucket: taskforge
    presign-expiration: PT15M
```

`StorageProperties`:
```java
public record Storage(String endpoint, String accessKey, String secretKey,
                      String bucket, Duration presignExpiration) {}
```

`StorageService`:
```java
@Service
public class StorageService {
    private final MinioClient minio;
    private final StorageProperties props;

    public StorageService(StorageProperties props) {
        this.props = props;
        this.minio = MinioClient.builder()
            .endpoint(props.endpoint())
            .credentials(props.accessKey(), props.secretKey())
            .build();
    }

    public PresignedUpload presignPut(String filename, String contentType) {
        String key = "attachments/" + UUID.randomUUID() + "/" + filename;
        String url = minio.getPresignedObjectUrl(
            GetPresignedObjectUrlArgs.builder()
                .method(io.minio.http.Method.PUT)
                .bucket(props.bucket())
                .object(key)
                .expiry((int) props.presignExpiration().toSeconds())
                .build());
        return new PresignedUpload(url, key);
    }

    public String publicUrl(String key) {
        return props.endpoint() + "/" + props.bucket() + "/" + key;
    }
}

public record PresignedUpload(String uploadUrl, String objectKey) {}
```

Bootstrap the bucket on startup:
```java
@Component
public class MinioBucketInitializer {
    public MinioBucketInitializer(StorageService storage) {
        // call storage.ensureBucket() in a @PostConstruct
    }
}
```

---

## 7. The controller

`AttachmentController`:
```java
@RestController
@RequestMapping("/api/attachments")
public class AttachmentController {

    private final StorageService storage;
    public AttachmentController(StorageService storage) { this.storage = storage; }

    @PostMapping("/presign")
    public PresignedUpload presign(@RequestBody @Valid PresignRequest req) {
        return storage.presignPut(req.filename(), req.contentType());
    }
}

public record PresignRequest(
    @NotBlank String filename,
    @NotBlank String contentType
) {}
```

> A real version scopes the key to a user/workspace and enforces a max
> size. Add those in the challenge.

---

## 8. The full client flow (curl)

```bash
# 1. Get a presigned URL
URL_JSON=$(curl -s -X POST -H "Authorization: Bearer $TOKEN" \
  -H 'content-type: application/json' \
  -d '{"filename":"report.pdf","contentType":"application/pdf"}' \
  localhost:8080/api/attachments/presign)

UPLOAD_URL=$(echo "$URL_JSON" | jq -r .uploadUrl)
OBJECT_KEY=$(echo "$URL_JSON" | jq -r .objectKey)

# 2. Upload directly to MinIO
echo "fake pdf content" > /tmp/report.pdf
curl -s -X PUT -H 'content-type: application/pdf' \
  --data-binary @/tmp/report.pdf \
  "$UPLOAD_URL"

# 3. The file is at http://localhost:9000/taskforge/$OBJECT_KEY
curl -s "http://localhost:9000/taskforge/$OBJECT_KEY"
# → "fake pdf content"
```

✅ The API never touched the bytes.

---

## 9. Serving downloads — presigned GETs

For private buckets, generate a presigned **GET** URL on demand:

```java
public String presignGet(String objectKey) {
    return minio.getPresignedObjectUrl(
        GetPresignedObjectUrlArgs.builder()
            .method(io.minio.http.Method.GET)
            .bucket(props.bucket())
            .object(objectKey)
            .expiry(3600)
            .build());
}
```

For public files, you can serve directly from MinIO through a CDN. Module
14's `docker-compose` exposes MinIO on `localhost:9000` for dev.

---

## 10. Validating uploads

Two layers:

1. **At presign time:** enforce a max filename length, a content-type
   allowlist, a per-user quota.
2. **At upload time:** MinIO's bucket policy can enforce a max object
   size and an allowlist of content types.

A reasonable policy:
```java
private static final Set<String> ALLOWED_TYPES = Set.of(
    "application/pdf", "image/png", "image/jpeg", "text/plain");
private static final long MAX_BYTES = 10L * 1024 * 1024;   // 10 MB

public PresignedUpload presignPut(String filename, String contentType, long sizeBytes) {
    if (!ALLOWED_TYPES.contains(contentType))
        throw new IllegalArgumentException("disallowed content type");
    if (sizeBytes > MAX_BYTES)
        throw new IllegalArgumentException("file too large");
    // ...
}
```

> **Server-side validation only goes so far.** The presigned URL gives the
> uploader the ability to PUT *something*; bucket policy and post-upload
> scanning are the second line of defense. (Antivirus is out of scope
> here.)

---

## 11. Testing uploads

A slice test for the presign endpoint:
```java
@WebMvcTest(AttachmentController.class)
class AttachmentControllerTest {
    @Autowired MockMvc mvc;
    @MockBean StorageService storage;

    @Test
    void presign_returnsUrlAndKey() throws Exception {
        when(storage.presignPut(eq("a.pdf"), eq("application/pdf")))
            .thenReturn(new PresignedUpload("https://minio/x", "attachments/uuid/a.pdf"));

        mvc.perform(post("/api/attachments/presign")
                .with(jwt())
                .contentType(MediaType.APPLICATION_JSON)
                .content("{\"filename\":\"a.pdf\",\"contentType\":\"application/pdf\"}"))
           .andExpect(status().isOk())
           .andExpect(jsonPath("$.uploadUrl").value("https://minio/x"));
    }
}
```

An integration test with a Testcontainer MinIO is more thorough; out of
scope for the lab, but a good exercise.

---

## 12. Common pitfalls

| Symptom | Cause | Fix |
|---------|-------|-----|
| `535 Authentication failed` | MailHog doesn't need auth but your prod provider does | Set `mail.smtp.auth: true` and provide credentials |
| Email never sent but no error | `@Async` swallowed the exception | Add an `AsyncUncaughtExceptionHandler` or wrap with try/catch |
| `MalformedURLException` from MinIO | Wrong endpoint format — `http://host:port`, no trailing slash | Match exactly |
| `AccessDenied` from MinIO | Bucket policy or credentials are wrong | In dev: `minioadmin`/`minioadmin`. In prod: a per-app IAM user with `s3:PutObject` only. |
| Presigned URL expired | Default is 7 days; you set it shorter | Match `presign-expiration` to how long you expect uploads to take |
| Browser shows CORS error uploading | MinIO isn't configured to accept your origin | Set `MINIO_API_CORS_ALLOW_ORIGIN=*` in dev, or a specific origin in prod |

---

## 13. Do the lab

Wire the templated email service, set up MinIO + presigned URLs, and prove
the full client flow with curl.

👉 **[lab.md](./lab.md)**

Then test yourself: 👉 **[challenge.md](./challenge.md)**

---

## Key terms (see [GLOSSARY](../GLOSSARY.md))

`JavaMailSender` · `MimeMessageHelper` · Thymeleaf · `EmailService` · `@Async` · presigned URL · object storage · MinIO · `GetPresignedObjectUrlArgs` · `Method.PUT/GET` · `Content-Type` allowlist · bucket policy

**Next →** [Module 13: API Documentation with OpenAPI](../13-openapi-docs/)
