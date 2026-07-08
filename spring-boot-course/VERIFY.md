# VERIFY — End-to-End Smoke Test

Use this to confirm your environment and the app actually work. Early modules
only exercise the first few checks; by the capstone you should pass them all.
Run it whenever something feels broken to localize the problem.

---

## 0. Toolchain (after Module 00)

```bash
java --version         # 21.x (LTS)
mvn --version          # 3.9.x or newer
docker version         # Client AND Server sections present
docker compose version # v2.x
```

✅ All commands print a version with no errors.

## 1. Local data services (after Module 00)

```bash
cd spring-boot-course/00-setup
docker compose -f compose.dev.yml up -d
docker compose -f compose.dev.yml ps     # postgres, redis, kafka, mailhog, minio = "running"/healthy
```

✅ Every container is `running`/`healthy`. Postgres on `5432`, Redis on `6379`,
Kafka on `9092`, MailHog UI on `8025`, MinIO console on `9001`.

## 2. App boots (after Module 02+)

```bash
cd ../apps/taskforge
mvn spring-boot:run
curl -s localhost:8080/actuator/health   # {"status":"UP"}
```

✅ Health endpoint returns `UP`; the app starts on port `8080`.

## 3. Persistence round-trip (after Module 05+)

```bash
# create
curl -s -X POST localhost:8080/api/tasks \
  -H 'content-type: application/json' \
  -d '{"title":"first task","description":"hello"}'
# → 201, with an id

# list
curl -s localhost:8080/api/tasks   # → JSON array including the task
```

✅ A task created via POST is visible via GET, and the row is in Postgres
(`docker compose exec postgres psql -U taskforge -d taskforge -c 'select * from task;'`).

## 4. Validation & error contract (after Module 06)

```bash
curl -s -X POST localhost:8080/api/tasks \
  -H 'content-type: application/json' \
  -d '{"title":""}'    # empty title violates @NotBlank
# → 400 with an RFC 7807 problem-details body
```

✅ A bad request returns `400` and a structured error body explaining the
violations.

## 5. Auth round-trip (after Module 07)

```bash
# register
curl -s -X POST localhost:8080/api/auth/register \
  -H 'content-type: application/json' \
  -d '{"email":"a@example.com","username":"ann","password":"password123"}'

# log in to get tokens
curl -s -X POST localhost:8080/api/auth/login \
  -H 'content-type: application/json' \
  -d '{"email":"a@example.com","password":"password123"}'
# → {"accessToken":"...","refreshToken":"..."}
```

✅ You receive `accessToken` and `refreshToken`; a protected endpoint accepts
the access token (`Authorization: Bearer ...`) and rejects a missing/expired one.

## 6. Tests pass (after Module 08)

```bash
mvn test
```

✅ All unit, slice, and Testcontainer tests pass; coverage report shows the
service + controller + repository layers are exercised.

## 7. Caching works (after Module 10)

```bash
# Look in logs the first time
curl -s localhost:8080/api/tasks/1
# Look in logs the second time — should be a cache hit (no SQL query)
curl -s localhost:8080/api/tasks/1
```

✅ The second call is served from Redis; the SQL log only fires on the first.

## 8. Kafka round-trip (after Module 11)

```bash
# create a task; the producer publishes "task.created" to Kafka
curl -s -X POST localhost:8080/api/tasks -H 'content-type: application/json' \
  -d '{"title":"via kafka","description":"..."}'

# the consumer logs the event
docker compose -f ../../00-setup/compose.dev.yml logs -f kafka | head
```

✅ The "task.created" event appears in the Kafka topic, the consumer logs
receipt, and (if the email module is up) a notification email lands in MailHog.

## 9. OpenAPI docs (after Module 13)

Open <http://localhost:8080/swagger-ui.html> → every endpoint is documented;
`/v3/api-docs` returns the raw OpenAPI JSON.

✅ Swagger UI loads and the spec covers all your controllers.

## 10. Containerized stack (after Module 14)

```bash
cd spring-boot-course
docker compose up --build
```

✅ Postgres, Redis, Kafka, MailHog, MinIO, and the app come up; the app
responds at `http://localhost:8080/actuator/health` with `UP`.

## 11. Observability (after Module 15)

```bash
curl -s localhost:8080/actuator/health          # {"status":"UP"}
curl -s localhost:8080/actuator/metrics         # list of available metrics
curl -s localhost:8080/actuator/prometheus | head
```

✅ Custom `taskforge_tasks_created_total` counter appears in the Prometheus
output.

## 12. Capstone (after Module 16)

A single `docker compose up` brings up:

- Postgres (Flyway-applied schema, seeded data)
- Redis (cache + rate limiter)
- Kafka (event bus)
- MailHog (dev SMTP)
- MinIO (object storage)
- The app (JWT-secured, observability-instrumented)

End-to-end:

- A user registers, logs in, gets a JWT.
- They create a task → row in Postgres, event in Kafka, email in MailHog.
- They upload an attachment → file in MinIO.
- They hit `/actuator/prometheus` → task metrics are visible.
- All structured logs include a correlation id.
