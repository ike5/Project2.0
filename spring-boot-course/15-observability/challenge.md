# Challenge 15 — The Full Observability Stack

No step-by-step this time. Use what you learned. Reference solutions are in
[`solutions/`](./solutions/) — try first!

## Tasks

1. **Liveness vs readiness.** Confirm both endpoints work and return
   different JSON shapes. Stop Redis (`docker compose stop redis`) and
   confirm readiness goes `DOWN` while liveness stays `UP`. (Restart
   Redis after.)

2. **Tag with `result`.** Add a tag to your custom counter:
   `taskforge.tasks.created{result="success"|"error"}`. Increment with
   the right tag in both branches.

3. **HTTP request metrics.** Use the built-in `http.server.requests`
   timer to build a Grafana panel: p50, p95, p99 of `POST /api/tasks`
   latency over the last 5 minutes.

4. **A custom health indicator for the connection pool.** Add the
   `ConnectionPoolHealthIndicator` from the README. Stop Postgres and
   confirm the indicator reports `DOWN` with a clear message.

5. **Trace propagation to Kafka.** When the API publishes a `TaskEvent`,
   the trace id is in the payload. When the consumer handles it, it
   creates a *new* span. Use `KafkaTemplate` with Micrometer's
   `KafkaSenderContext` so the trace id flows through Kafka headers
   automatically. (In `spring-kafka` 3.x, this is on by default with the
   Micrometer bridge.)

6. **Stretch:** Add an SLO (Service Level Objective) dashboard in
   Grafana: error rate, latency p99, and request rate. Alert in
   Prometheus when error rate > 1% for 5 min.

## Success criteria

- [ ] Liveness ≠ readiness (different statuses when a dependency is down).
- [ ] The custom counter has a `result` tag.
- [ ] A Grafana panel shows p50/p95/p99 of `POST /api/tasks`.
- [ ] The connection pool health indicator reports `DOWN` when needed.
- [ ] Trace ids propagate through Kafka to the consumer.
- [ ] Stretch: a Prometheus alert is configured.
