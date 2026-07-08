# Module 14 — Containerizing with Docker & Docker Compose

**Goal:** package the entire `taskforge` app and its dependencies into
**containers** that run identically on a laptop, a CI box, and a
production server. By the end of this module, `docker compose up` brings up
the whole stack: app + Postgres + Redis + Kafka + MailHog + MinIO.

⏱️ ~2.5 hours · 🎯 Prereq: Modules 02–13 complete (full app, fully tested).

> The image is the artifact. From here on, you ship the image, not the
> source.

---

## 1. What "containerizing" means for a Spring Boot app

A Spring Boot app already produces a **fat JAR** that runs anywhere with
Java. Why containerize?

- **Identical environment** — JDK version, locale, time zone, libstdc++,
  curl — all baked in.
- **Layered image** — base image, dependencies, your code in separate
  layers. Re-builds are fast.
- **Same deploy unit** — `docker compose up` in dev, Kubernetes in prod.

The trade-off: more moving parts. Mitigated by the multi-stage build
below.

---

## 2. The multi-stage Dockerfile

A single Dockerfile that:
1. **Builds** with the full JDK + Maven.
2. **Packages** your code into a fat JAR.
3. **Runs** the JAR in a slim JRE-only image.

`apps/taskforge/Dockerfile`:
```dockerfile
# syntax=docker/dockerfile:1.7

# ── 1. Build ────────────────────────────────────────────────────────────────
FROM eclipse-temurin:21-jdk-jammy AS builder
WORKDIR /workspace

# Cache dependencies first
COPY pom.xml ./
COPY .mvn .mvn
COPY mvnw ./
RUN ./mvnw -B -e -ntp dependency:go-offline

# Build the JAR
COPY src ./src
RUN ./mvnw -B -e -ntp -DskipTests package

# ── 2. Runtime ──────────────────────────────────────────────────────────────
FROM eclipse-temurin:21-jre-jammy
RUN useradd -ms /bin/bash app
WORKDIR /app

# Copy the fat JAR
COPY --from=builder /workspace/target/*.jar /app/app.jar
RUN chown -R app:app /app
USER app

EXPOSE 8080
HEALTHCHECK --interval=15s --timeout=3s --start-period=30s --retries=3 \
  CMD curl -fsS http://localhost:8080/actuator/health | grep -q '"status":"UP"' || exit 1

ENV JAVA_OPTS="-XX:MaxRAMPercentage=75 -XX:+ExitOnOutOfMemoryError"
ENTRYPOINT ["sh", "-c", "exec java $JAVA_OPTS -jar /app/app.jar \"$@\"", "--"]
```

> **Why `temurin:21-jre-jammy`?** The JRE is much smaller than the JDK
> (~200 MB vs ~500 MB). You don't need the compiler in production.
> **Why `HEALTHCHECK`?** Docker calls it; the `unhealthy` state is visible
> in `docker ps`. Module 15's Actuator endpoint is what it probes.

Build:
```bash
cd apps/taskforge
docker build -t taskforge:1.0.0 .
docker run --rm -p 8080:8080 \
  -e SPRING_PROFILES_ACTIVE=prod \
  -e DATABASE_URL=jdbc:postgresql://host.docker.internal:5432/taskforge \
  -e DATABASE_USER=taskforge \
  -e DATABASE_PASSWORD=taskforge \
  -e JWT_SECRET=change-me-change-me-change-me-change-me \
  taskforge:1.0.0
```

---

## 3. The `.dockerignore`

`apps/taskforge/.dockerignore`:
```
target
.git
.gitignore
.idea
.vscode
*.iml
.mvn/wrapper/maven-wrapper.jar.bak
README.md
```

> Without this, every `docker build` copies your entire repo into the
> build context, slowing the build and potentially leaking `.git/` and
> secrets.

---

## 4. The `docker-compose.yml` — the whole stack

`spring-boot-course/docker-compose.yml`:
```yaml
version: "3.9"

services:
  postgres:
    image: postgres:16
    environment:
      POSTGRES_USER: taskforge
      POSTGRES_PASSWORD: taskforge
      POSTGRES_DB: taskforge
    volumes:
      - pgdata:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U taskforge"]
      interval: 5s
      timeout: 3s
      retries: 10

  redis:
    image: redis:7
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      retries: 10

  kafka:
    image: bitnami/kafka:3.7
    environment:
      KAFKA_CFG_NODE_ID: 1
      KAFKA_CFG_PROCESS_ROLES: controller,broker
      KAFKA_CFG_CONTROLLER_QUORUM_VOTERS: 1@kafka:9093
      KAFKA_CFG_LISTENERS: PLAINTEXT://:9092,CONTROLLER://:9093
      KAFKA_CFG_ADVERTISED_LISTENERS: PLAINTEXT://kafka:9092
      KAFKA_CFG_CONTROLLER_LISTENER_NAMES: CONTROLLER
      KAFKA_CFG_LISTENER_SECURITY_PROTOCOL_MAP: CONTROLLER:PLAINTEXT,PLAINTEXT:PLAINTEXT
      KAFKA_CFG_INTER_BROKER_LISTENER_NAME: PLAINTEXT
      ALLOW_PLAINTEXT_LISTENER: "yes"
    ports:
      - "9092:9092"

  mailhog:
    image: mailhog/mailhog:v1.0.1
    ports:
      - "1025:1025"
      - "8025:8025"

  minio:
    image: minio/minio:latest
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin
    ports:
      - "9000:9000"
      - "9001:9001"
    volumes:
      - miniodata:/data

  app:
    build: ./apps/taskforge
    image: taskforge:1.0.0
    depends_on:
      postgres: { condition: service_healthy }
      redis:    { condition: service_healthy }
      kafka:    { condition: service_started }
      mailhog:  { condition: service_started }
      minio:    { condition: service_started }
    environment:
      SPRING_PROFILES_ACTIVE: prod
      DATABASE_URL: jdbc:postgresql://postgres:5432/taskforge
      DATABASE_USER: taskforge
      DATABASE_PASSWORD: taskforge
      SPRING_DATA_REDIS_HOST: redis
      SPRING_KAFKA_BOOTSTRAP_SERVERS: kafka:9092
      SPRING_MAIL_HOST: mailhog
      SPRING_MAIL_PORT: 1025
      TASKFORGE_STORAGE_ENDPOINT: http://minio:9000
      JWT_SECRET: please-change-me-32-bytes-minimum-1234567890
      EMAIL_FROM: noreply@taskforge.com
    ports:
      - "8080:8080"

volumes:
  pgdata:
  miniodata:
```

> **Note the hostnames:** inside the compose network, the app reaches
> Postgres as `postgres:5432`, not `localhost`. Spring's `application.yml`
> reads them from env vars.

---

## 5. Bring it all up

```bash
# from the course root
docker compose up -d --build

# watch
docker compose ps
docker compose logs -f app

# smoke
curl -s localhost:8080/actuator/health
# → {"status":"UP"}

# in MailHog
open http://localhost:8025

# in MinIO
open http://localhost:9001
```

Tear down:
```bash
docker compose down            # containers only
docker compose down -v         # + volumes (data gone)
```

> **`-v` is destructive.** Don't run it in prod. In dev it's how you reset
> state.

---

## 6. Production-flavored adjustments

For a real production deploy, a few changes:

- **Externalize secrets** to a real secret manager (AWS Secrets Manager,
  HashiCorp Vault), not env vars on the compose file.
- **Use a registry** — `docker build -t ghcr.io/yourorg/taskforge:1.0.0 .`
  and `docker push`.
- **Multi-stage the data services** — Postgres and Kafka have their own
  containers in real life. Module 16's capstone keeps them here for
  simplicity but acknowledges the trade-off.
- **Read-only filesystem** — `read_only: true` + tmpfs mounts for
  `/tmp` (Hikari wants to write the JDBC driver there).
- **Run as non-root** — the Dockerfile already does this with `USER app`.
- **Resource limits** — `mem_limit: 512m`, `cpus: 1.0` per service.

---

## 7. The Spring Boot Maven plugin's `build-image` goal

Spring Boot's plugin can build a **native image** or a **Buildpacks image**
without a Dockerfile:

```bash
mvn -Pnative native:compile          # GraalVM native image (fast start, low memory)
# OR
mvn spring-boot:build-image          # Buildpacks image (no Docker required locally)
```

`build-image` produces an image named after the artifact (`docker.io/library/taskforge:0.0.1-SNAPSHOT`)
that you can run with `docker run -p 8080:8080 ...`.

> For this course we use the multi-stage Dockerfile because it teaches the
> pattern. In real projects, `build-image` is often the easier path.

---

## 8. Docker Compose for tests

You can reuse the data services in tests:

`src/test/resources/docker-compose.yml` (subset of services):
```yaml
services:
  postgres:
    image: postgres:16
    environment: { POSTGRES_USER: taskforge, POSTGRES_PASSWORD: taskforge, POSTGRES_DB: taskforge }
    ports: ["5432"]
```

> Testcontainers (Module 08) is usually a better choice — the
> container's lifecycle is tied to the test, not your laptop.

---

## 9. Common pitfalls

| Symptom | Cause | Fix |
|---------|-------|-----|
| App can't reach Postgres | `localhost` in `application.yml` instead of the compose service name | Use env vars / `depends_on` for service discovery |
| `Connection refused` between services | The receiving container's `EXPOSE`d port isn't published to the host | Inside the compose network, services reach each other on the **container** port (e.g. `5432`), not the host port (`5432:5432`) |
| Image is 800 MB | You used `temurin:21-jdk` as the runtime | Use `temurin:21-jre` (or `-alpine` for an even smaller image) |
| `HEALTHCHECK` says "unhealthy" but the app is fine | Probe path is wrong or returns non-200 | Verify with `curl localhost:8080/actuator/health` from inside the container |
| Build is slow | No layer caching for deps | Copy `pom.xml` and run `dependency:go-offline` *before* copying `src/` |
| Image rebuilds every change | You copy `src/` before the dependency layer | Order matters: deps first, then sources |
| Secret leaked in image | `ARG` or `ENV` contains a real secret | Use `--secret` mounts at build time; never bake secrets in |

---

## 10. Do the lab

Write the Dockerfile, `.dockerignore`, and a `docker-compose.yml` that
brings up the whole stack. Confirm `curl localhost:8080/actuator/health`
returns `UP` from inside the container.

👉 **[lab.md](./lab.md)**

Then test yourself: 👉 **[challenge.md](./challenge.md)**

---

## Key terms (see [GLOSSARY](../GLOSSARY.md))

Docker · image · container · multi-stage build · base image · `USER` · `HEALTHCHECK` · `ENTRYPOINT` · `.dockerignore` · `docker compose` · service · `depends_on` · `condition: service_healthy` · `volumes` · `ports` · `build-image` · Buildpacks

**Next →** [Module 15: Observability with Actuator, Metrics, and Health](../15-observability/)
