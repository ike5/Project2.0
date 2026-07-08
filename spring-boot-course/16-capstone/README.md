# Module 16 — Capstone: A Production-Ready App

**Goal:** bring it all together. You should now be able to:
- Stand up the full stack with `docker compose up`.
- Run a real, JWT-secured, multi-user workflow end-to-end.
- Read structured logs, custom metrics, and traces from the app.
- Pass the smoke tests in [VERIFY.md](../VERIFY.md).
- Confidently say "I built a Spring Boot backend that's ready to ship."

⏱️ ~4+ hours · 🎯 Prereq: Modules 00–15 complete.

> This is the **graduation** module. There's no new content — only the
> integration of everything you've learned. Treat it as a final exam.

---

## 1. The full app

By the end of the course, `taskforge` has:

| Layer | What's there |
|-------|--------------|
| **Build** | Multi-stage Dockerfile, `docker-compose.yml`, `Makefile` |
| **Web** | REST API with proper status codes, DTOs, `application/problem+json` errors |
| **Auth** | JWT issuance + validation, ownership-scoped resources, `@PreAuthorize` |
| **Data** | JPA + Flyway, indexes, constraints, auditing |
| **Cache** | Redis-backed `@Cacheable` / `@CacheEvict` |
| **Async** | Kafka events, `@RetryableTopic`, DLT |
| **Storage** | Presigned-URL uploads to MinIO |
| **Mail** | Async templated email via MailHog |
| **Config** | `@ConfigurationProperties` + `@Validated`, dev/prod profiles |
| **Logs** | JSON, MDC, trace id, request id |
| **Metrics** | Micrometer → Prometheus → Grafana |
| **Traces** | Micrometer → OpenTelemetry → Zipkin |
| **Docs** | OpenAPI / Swagger UI |
| **Tests** | Unit + slice + Testcontainer integration, JaCoCo coverage |

---

## 2. The capstone exercises

Pick at least three. Each is graded against the success criteria; a
screenshot or a log line in your PR is enough to prove it.

### Exercise A — Deploy the full stack

```bash
cd spring-boot-course
docker compose up -d --build
curl -s localhost:8080/actuator/health
# → {"status":"UP"}
```

✅ All services healthy: app, postgres, redis, kafka, mailhog, minio,
prometheus, grafana, zipkin.

### Exercise B — Run the smoke test

Walk through [VERIFY.md §0–11](../VERIFY.md). Every check should pass.

### Exercise C — A real workflow

1. Register two users.
2. As user A, create a task.
3. Confirm MailHog shows the "new task" email.
4. As user B, try to `PUT` A's task — get `403`.
5. As A, complete the task — confirm a `task.completed` event.
6. Upload an attachment; the presigned URL works directly against MinIO.
7. Confirm `taskforge_tasks_created_total` is now ≥ 2 in Prometheus.

### Exercise D — Failure drill

Stop Postgres: `docker compose stop postgres`.
- `/actuator/health` → `DOWN`.
- Readiness → `DOWN`; liveness → `UP`.
- New requests fail with `500`.
Restart Postgres: `docker compose start postgres`.
- Within ~10 s, `/actuator/health` → `UP` again.
- New requests succeed.

### Exercise E — Trace a slow request

Send 100 requests to `GET /api/tasks/{id}` (a cached read).
In Zipkin, find the slowest one.
- Show the spans: HTTP → controller → service → cache.
- Note that the cached request has *one* span (no DB); the first has two.

### Exercise F — Capacity test (lightweight)

```bash
# install hey or ab
hey -n 5000 -c 50 -H "Authorization: Bearer $TOKEN" \
  http://localhost:8080/api/tasks
```

In Grafana:
- p99 latency under load.
- Request rate per second.
- Hikari active connections (no higher than pool max).
- JVM heap used.

> Don't optimize yet. **First, measure.**

### Exercise G — A new feature

Add **`comments`** on a task:
- Migration: `V9__create_comment.sql`.
- Entity: `Comment { id, task_id, author_id, body, created_at }`.
- `CommentRepository`.
- `CommentService` with ownership checks.
- `CommentController` with `POST /api/tasks/{id}/comments`,
  `GET /api/tasks/{id}/comments`, `DELETE /comments/{id}`.
- `CommentEvent` published to Kafka.
- Email notification when someone comments on your task.
- Tests at three levels.
- Documented in Swagger.
- Custom metric `taskforge.comments.created`.

This is the **capstone's capstone**: a feature that touches every layer
in the course.

---

## 3. The "definition of done"

A `taskforge` is **done** when:

- [ ] `docker compose up --build` brings up the whole stack.
- [ ] `mvn verify` passes; coverage ≥ 70% on services, ≥ 80% on controllers.
- [ ] The OpenAPI spec is checked into the repo and a CI step diffs it on
      every PR.
- [ ] `/actuator/health` is `UP` and exposes dependency statuses.
- [ ] `/actuator/prometheus` shows your custom metrics.
- [ ] A trace from a real request shows in Zipkin and includes the Kafka
      producer/consumer spans.
- [ ] A JSON log line from any service can be searched by trace id.
- [ ] The `README.md` has install, run, test, and a short architecture
      diagram.

---

## 4. What to read next

You've finished the course. These are the natural next steps in real
Spring Boot work:

| Topic | Where to learn |
|-------|----------------|
| **Spring Cloud Gateway** | API gateway / routing / rate limiting |
| **Spring Cloud Config** | Externalized config server |
| **Resilience4j** | Circuit breakers, retries, bulkheads |
| **Spring Authorization Server** | OAuth2 provider (not just resource server) |
| **Spring Modulith** | Modular monoliths with Spring's eventing |
| **Spring AI** | LLM integration for the same Spring patterns |
| **GraalVM native image** | Sub-second startup, much lower memory |
| **Kubernetes Operators** | Deploy, scale, and operate at the platform layer |
| **Postgres deep dive** | Indexes, query plans, partitioning, replication |
| **Kafka deep dive** | Schemas (Avro/Protobuf), exactly-once, ksqlDB |

> **The patterns you learned in this course — IoC, layered architecture,
> DTOs, validation, exception handling, transactions, testing,
> observability, containerization — apply to every one of them.**

---

## 5. A note on the course itself

This course is intentionally opinionated:

- **Maven over Gradle.** Maven is more common in Spring Boot tutorials
  and is what `start.spring.io` defaults to.
- **JPA over jOOQ or JDBC.** JPA is the default Spring Boot story.
- **JWT (HS256) over OAuth2.** Easier to teach; OAuth2 with JWKS is the
  follow-up.
- **Single-tenant.** Multi-tenancy is a deep topic on its own.
- **Java 21 records as DTOs.** Modern and concise.
- **`docker compose` over Kubernetes for the capstone.** K8s is its own
  course.

Every one of these choices has reasonable alternatives. The patterns are
what matter; the tools are interchangeable.

---

## 6. Final checklist

Before you move on, you should be able to answer **yes** to each:

- [ ] Can you scaffold a Spring Boot 3 app from scratch and run it?
- [ ] Can you write a `@RestController` with DTOs, validation, and
      `ProblemDetail` errors?
- [ ] Can you wire a `JpaRepository` with Flyway migrations and
      `@Transactional` services?
- [ ] Can you secure endpoints with Spring Security and JWT, including
      resource-ownership checks?
- [ ] Can you write unit, slice, and Testcontainer tests?
- [ ] Can you externalize config with `@ConfigurationProperties` and
      profiles?
- [ ] Can you cache method results with Redis and invalidate on writes?
- [ ] Can you publish and consume Kafka events with retry and DLT?
- [ ] Can you send templated email and accept presigned-URL uploads?
- [ ] Can you document the API with OpenAPI and serve Swagger UI?
- [ ] Can you write a multi-stage Dockerfile and a `docker-compose.yml`
      that brings up the whole stack?
- [ ] Can you read `/actuator/health`, `/actuator/prometheus`, and Zipkin
      traces?

If you answered "yes" to all of them, **you're ready to ship a Spring Boot
service**. Welcome to the backend.
