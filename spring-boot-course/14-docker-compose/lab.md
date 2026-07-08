# Lab 14 — Containerize taskforge

**You'll:** write the multi-stage Dockerfile, the `.dockerignore`, and the
`docker-compose.yml`. Confirm `docker compose up` brings up the whole
stack.

⏱️ ~50 min. Run from `spring-boot-course/`. Docker must be running.

---

## Part A — The Dockerfile

`apps/taskforge/Dockerfile`:
```dockerfile
# syntax=docker/dockerfile:1.7

FROM eclipse-temurin:21-jdk-jammy AS builder
WORKDIR /workspace

# Pre-fetch dependencies (cached layer)
COPY pom.xml ./
COPY .mvn .mvn
COPY mvnw ./
RUN ./mvnw -B -e -ntp dependency:go-offline

# Build the JAR
COPY src ./src
RUN ./mvnw -B -e -ntp -DskipTests package

FROM eclipse-temurin:21-jre-jammy
RUN useradd -ms /bin/bash app
WORKDIR /app
COPY --from=builder /workspace/target/*.jar /app/app.jar
RUN chown -R app:app /app
USER app

EXPOSE 8080
HEALTHCHECK --interval=15s --timeout=3s --start-period=30s --retries=3 \
  CMD curl -fsS http://localhost:8080/actuator/health | grep -q '"status":"UP"' || exit 1

ENV JAVA_OPTS="-XX:MaxRAMPercentage=75 -XX:+ExitOnOutOfMemoryError"
ENTRYPOINT ["sh", "-c", "exec java $JAVA_OPTS -jar /app/app.jar \"$@\"", "--"]
```

> If you don't have a `mvnw` wrapper, drop the `.mvn` and `mvnw` lines
> and use `mvn` directly.

---

## Part B — The `.dockerignore`

`apps/taskforge/.dockerignore`:
```
target
.git
.gitignore
.idea
.vscode
*.iml
README.md
docker-compose.yml
Dockerfile
```

---

## Part C — The `docker-compose.yml`

Create `docker-compose.yml` at the **course root** (see README §4 for
the full file). Bring it up:

```bash
cd spring-boot-course
docker compose up -d --build
docker compose ps
```

✅ Expected:
```
NAME             STATUS              PORTS
postgres         running (healthy)   5432
redis            running (healthy)   6379
kafka            running              9092
mailhog          running              1025, 8025
minio            running              9000, 9001
taskforge-app-1  running (healthy)    8080
```

---

## Part D — Verify the app inside the container

```bash
curl -s localhost:8080/actuator/health
# → {"status":"UP"}

# Swagger UI works
open http://localhost:8080/swagger-ui.html

# MailHog still receives emails
open http://localhost:8025

# MinIO still works
open http://localhost:9001
```

Stop everything:
```bash
docker compose down            # keep data
docker compose down -v         # wipe data
```

---

## Part E — A small optimization

Watch the build:
```bash
docker compose build app
# Look for the "CACHED" markers on the dependency layer.
# Edit a single .java file → only the second stage rebuilds.
```

---

## What you learned

- A multi-stage Dockerfile produces a small, secure image.
- Layer caching is the build's performance: deps first, sources second.
- `docker compose` orchestrates a multi-service local environment with
  healthchecks and dependencies.
- Inside the compose network, services reach each other by **service
  name** (e.g. `postgres:5432`), not `localhost`.
- The Spring Boot Actuator endpoint + `HEALTHCHECK` makes the container
  status reportable to orchestrators.

➡️ Now try the **[challenge](./challenge.md)**, then move to
[Module 15](../15-observability/).
