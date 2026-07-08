# Challenge 11 — Make Events Reliable

No step-by-step this time. Use what you learned. Reference solutions are in
[`solutions/`](./solutions/) — try first!

## Tasks

1. **Add `@RetryableTopic`.** Wrap the listener with `@RetryableTopic` so
   failed messages are retried 4 times with exponential backoff and land in
   a DLT on final failure. Inject a `RecordInterceptor` or use
   `DefaultErrorHandler` with a `DeadLetterPublishingRecoverer` if you
   prefer manual control.

2. **The outbox pattern.** Add an `outbox_event` table
   `(id, type, payload, created_at, published_at)`. Write to it in the
   same transaction as the task create/update. A scheduled poller
   (`@Scheduled`) reads unpublished rows every second, sends them to
   Kafka, and marks them `published_at = now()`. Add a migration for the
   table.

3. **Idempotency.** Add a `processed_event (event_id, consumer, processed_at)`
   table with a unique constraint. The consumer checks
   `existsByEventIdAndConsumer` before doing work; saves the row after.

4. **Multiple consumers.** Add a second `@KafkaListener` in a *different*
   consumer group (`groupId = "taskforge-analytics"`) that logs
   "analytics: received ...". Confirm with `kafka-consumer-groups.sh`
   that two groups exist for the same topic.

5. **Headers for tracing.** On the producer, add the trace id as a Kafka
   header. On the consumer, read it via `@Header(KafkaHeaders.RECEIVED_HEADERS)`
   and put it in the MDC.

6. **Stretch:** Add a separate Spring Boot **worker** module
   (`taskforge-worker`) that contains **only** the `NotificationWorker`.
   Run it as `java -jar worker.jar` alongside the API. Same Kafka, same
   topic, separate processes.

## Success criteria

- [ ] Failed messages retry 4× with backoff, then land in a DLT.
- [ ] The outbox pattern guarantees no lost events on Kafka failure.
- [ ] The same event processed twice is a no-op.
- [ ] Two consumer groups read the same topic independently.
- [ ] Trace id flows producer → consumer via Kafka headers.
- [ ] Stretch: the worker runs in a separate process.
