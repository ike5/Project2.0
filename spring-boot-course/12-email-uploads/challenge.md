# Challenge 12 — Email and Uploads in Production

No step-by-step this time. Use what you learned. Reference solutions are in
[`solutions/`](./solutions/) — try first!

## Tasks

1. **Auto-create the bucket.** Make `StorageService` call
   `MakeBucketArgs` if the bucket doesn't exist (use `BucketExistsArgs`).
   Remove the manual step in the MinIO console.

2. **Per-user scoping.** Put uploads under `attachments/{userId}/{uuid}/{filename}`.
   Add a `userId` parameter to `presignPut` and pass the authenticated
   user's id from the controller.

3. **Size and content-type enforcement.** Reject uploads over 10 MB or
   outside the allowlist (`application/pdf`, `image/png`, `image/jpeg`,
   `text/plain`) at the API. Return `400` with a problem detail.

4. **Real attachment on a task.** Add `POST /api/tasks/{id}/attachments`
   that records `(taskId, objectKey, filename, contentType, sizeBytes,
   uploadedAt)` in a new `attachment` table. `GET /api/tasks/{id}/attachments`
   returns the list.

5. **Async email with retry.** Add a `RetryTemplate` to `SmtpEmailService`
   so transient SMTP failures retry 3× with backoff. Log final failures
   to a `failed_email` table for manual replay.

6. **Stretch:** Generate an **S3-compatible** `S3Presigner` (AWS SDK v2)
   in addition to the MinIO client, so the same code can target either
   by changing `taskforge.storage.endpoint`. (Useful if you ever migrate
   from MinIO to S3.)

## Success criteria

- [ ] The bucket is created on startup; no manual step.
- [ ] Upload keys are scoped per user.
- [ ] Oversized / disallowed uploads return 400.
- [ ] Attachments are stored against a task and listable.
- [ ] Email retries on transient failures; final failures are recorded.
- [ ] Stretch: AWS SDK `S3Presigner` works against an alternate endpoint.
