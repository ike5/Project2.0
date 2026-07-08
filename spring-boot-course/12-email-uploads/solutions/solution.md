# Challenge 12 — Reference Solution

### 1. Auto-create bucket
```java
public void ensureBucket() throws Exception {
    boolean exists = minio.bucketExists(BucketExistsArgs.builder().bucket(bucket).build());
    if (!exists) minio.makeBucket(MakeBucketArgs.builder().bucket(bucket).build());
}
```
Call from `ApplicationReadyEvent`:
```java
@EventListener(ApplicationReadyEvent.class)
public void init() throws Exception { storage.ensureBucket(); }
```

### 2. Per-user scoping
```java
public PresignedUpload presignPut(String filename, String contentType, Long userId) {
    String key = "attachments/" + userId + "/" + UUID.randomUUID() + "/" + filename;
    // ...
}
```
Controller:
```java
@PostMapping("/presign")
public PresignedUpload presign(@RequestBody @Valid PresignRequest req, Authentication auth) {
    Long userId = Long.valueOf(auth.getName());
    return storage.presignPut(req.filename(), req.contentType(), userId);
}
```

### 3. Size and content-type enforcement
```java
private static final Set<String> ALLOWED = Set.of(
    "application/pdf", "image/png", "image/jpeg", "text/plain");
private static final long MAX_BYTES = 10L * 1024 * 1024;

public PresignedUpload presignPut(String filename, String contentType, long sizeBytes, Long userId) {
    if (!ALLOWED.contains(contentType))
        throw new IllegalArgumentException("content type not allowed: " + contentType);
    if (sizeBytes > MAX_BYTES)
        throw new IllegalArgumentException("file too large; max " + MAX_BYTES + " bytes");
    // ...
}
```

### 4. Attachments on a task
```sql
-- V8__create_attachment.sql
CREATE TABLE attachment (
    id           BIGSERIAL PRIMARY KEY,
    task_id      BIGINT NOT NULL REFERENCES task(id),
    object_key   VARCHAR(500) NOT NULL,
    filename     VARCHAR(200) NOT NULL,
    content_type VARCHAR(100) NOT NULL,
    size_bytes   BIGINT,
    uploaded_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
```
```java
@Entity @Table(name = "attachment")
public class Attachment { /* ... */ }
```
```java
@PostMapping
public AttachmentResponse attach(@PathVariable Long id, @RequestBody @Valid AttachRequest req, Authentication auth) {
    Long userId = Long.valueOf(auth.getName());
    service.assertOwner(id, userId);
    return service.attach(id, req);
}
```

### 5. Email retry
```java
@Async
public void send(EmailMessage msg) {
    var retry = RetryTemplate.builder()
        .maxAttempts(3)
        .exponentialBackoff(500, 2.0, 5000)
        .retryOn(MailException.class)
        .build();
    try {
        retry.execute(ctx -> doSend(msg));
    } catch (Exception e) {
        log.error("email permanently failed to={}", msg.to(), e);
        failedEmailRepo.save(new FailedEmail(msg, e.getMessage()));
    }
}
```

### 6. AWS SDK S3Presigner (stretch)
```xml
<dependency>
  <groupId>software.amazon.awssdk</groupId>
  <artifactId>s3</artifactId>
  <version>2.27.0</version>
</dependency>
```
```java
@Bean
public S3Presigner s3Presigner(TaskforgeProperties props) {
    return S3Presigner.builder()
        .endpointOverride(URI.create(props.storage().endpoint()))
        .credentialsProvider(StaticCredentialsProvider.create(
            AwsBasicCredentials.create(props.storage().accessKey(), props.storage().secretKey())))
        .region(Region.US_EAST_1)              // required, even for MinIO
        .build();
}
```
> The same presigned URL mechanism works against AWS S3 — only the
> endpoint and credentials differ.
