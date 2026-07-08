# Cheatsheet — Docker & Docker Compose

Quick reference for containerizing your Spring Boot app. Keep it open
while you build.

## The minimum viable Dockerfile (Spring Boot)

```dockerfile
# syntax=docker/dockerfile:1.7

FROM eclipse-temurin:21-jdk-jammy AS builder
WORKDIR /workspace
COPY pom.xml mvnw ./
COPY .mvn .mvn
RUN ./mvnw -B -e -ntp dependency:go-offline
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

## `.dockerignore`

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

## The minimum viable `docker-compose.yml`

```yaml
services:
  postgres:
    image: postgres:16
    environment:
      POSTGRES_USER: taskforge
      POSTGRES_PASSWORD: taskforge
      POSTGRES_DB: taskforge
    volumes:
      - pgdata:/var/lib/postgresql/data
    ports: ["5432:5432"]
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U taskforge"]
      interval: 5s
      timeout: 3s
      retries: 10

  app:
    build: .
    depends_on:
      postgres: { condition: service_healthy }
    environment:
      SPRING_PROFILES_ACTIVE: prod
      DATABASE_URL: jdbc:postgresql://postgres:5432/taskforge
      DATABASE_USER: taskforge
      DATABASE_PASSWORD: taskforge
    ports: ["8080:8080"]

volumes:
  pgdata:
```

## The commands you'll use

```bash
docker build -t taskforge:1.0.0 .           # build an image
docker images                                # list images
docker run --rm -p 8080:8080 taskforge:1.0.0 # run interactively
docker ps                                    # running containers
docker ps -a                                 # all containers (including stopped)
docker logs -f <id>                          # tail logs
docker exec -it <id> sh                      # shell in
docker stop <id>                             # stop
docker rm <id>                               # remove
docker image rm <id>                         # remove image

docker compose up -d --build                 # start (build first)
docker compose up -d                         # start (no rebuild)
docker compose down                          # stop + remove
docker compose down -v                       # + volumes
docker compose ps                            # status
docker compose logs -f app                   # logs (one service)
docker compose exec postgres psql -U taskforge -d taskforge   # shell
docker compose restart app                   # restart one
```

## Healthchecks

```yaml
postgres:
  healthcheck:
    test: ["CMD-SHELL", "pg_isready -U taskforge"]
    interval: 5s
    timeout: 3s
    retries: 10

redis:
  healthcheck:
    test: ["CMD", "redis-cli", "ping"]
    interval: 5s
    retries: 10

kafka:
  healthcheck:
    test: ["CMD-SHELL", "kafka-topics.sh --bootstrap-server localhost:9092 --list >/dev/null 2>&1"]
    interval: 10s
    retries: 20

app:
  depends_on:
    postgres: { condition: service_healthy }
    redis:    { condition: service_healthy }
    kafka:    { condition: service_healthy }
```

> `service_healthy` waits for the healthcheck to pass. `service_started`
> (the default) only waits for the container to start — not the service
> inside it.

## Volumes

```yaml
services:
  postgres:
    volumes:
      - pgdata:/var/lib/postgresql/data      # named volume (managed)
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql:ro  # bind mount (file)
volumes:
  pgdata:
```

> **Named volumes** survive `docker compose down`. **`-v` removes them.**
> **Bind mounts** are paths on the host — useful for config files.

## Networks (the implicit one)

Inside `docker compose`, every service can reach every other by **service
name** as the hostname:

```yaml
app:
  environment:
    DATABASE_URL: jdbc:postgresql://postgres:5432/taskforge
    SPRING_KAFKA_BOOTSTRAP_SERVERS: kafka:9092
```

Outside the network (your laptop, or another compose project), use
`localhost:5432` against the `ports: "5432:5432"` mapping.

## Resource limits

```yaml
app:
  mem_limit: 512m
  cpus: "1.0"
  pids_limit: 200
```

Confirm with `docker stats <name>`.

## Multi-arch builds

```bash
docker buildx create --use
docker buildx build --platform linux/amd64,linux/arm64 \
  -t ghcr.io/yourorg/taskforge:1.0.0 --push .
```

## Image size cheats

| Image | Size | Notes |
|-------|------|-------|
| `eclipse-temurin:21-jdk-jammy` | ~500 MB | Build stage only |
| `eclipse-temurin:21-jre-jammy` | ~430 MB | Runtime — fine for most |
| `eclipse-temurin:21-jre-alpine` | ~250 MB | musl libc; sometimes tricky |
| `eclipse-temurin:21-jre-jammy-noble` | ~360 MB | Ubuntu 24 base |
| GraalVM native image | ~80 MB | Sub-100ms startup, AOT compiled |

## Common pitfalls

- **`localhost` in `application.yml`** — points at the container, not
  Postgres. Use env vars; compose service names are the hostnames.
- **`Connection refused` between services** — the receiving service
  isn't using `0.0.0.0`, or the `EXPOSE`d port isn't actually listening.
  Check with `docker compose exec app curl postgres:5432`.
- **Image is 800 MB** — used `jdk` as the runtime. Switch to `jre`.
- **Build is slow** — no layer caching. Copy `pom.xml` and run
  `dependency:go-offline` *before* copying `src/`.
- **Volume permission errors** — the data dir is owned by `root` and
  the container runs as `app`. `chown` it in the Dockerfile or run as
  root (less safe).
- **Secret leaked in image** — `ARG` or `ENV` with a real secret at
  build time. Use `docker build --secret` or runtime env vars instead.
- **Healthcheck says "unhealthy"** — the probe path is wrong, or the
  app hasn't started yet. Use `--start-period=30s` to give it time.

## Healthchecks for every common service

| Service | Probe |
|---------|-------|
| Postgres | `pg_isready -U $USER` |
| MySQL | `mysqladmin ping -h 127.0.0.1` |
| Redis | `redis-cli ping` |
| Kafka | `kafka-topics.sh --bootstrap-server localhost:9092 --list` |
| MinIO | `curl -f http://localhost:9000/minio/health/live` |
| MailHog | `curl -f http://localhost:8025/` |
| RabbitMQ | `rabbitmq-diagnostics ping` |
