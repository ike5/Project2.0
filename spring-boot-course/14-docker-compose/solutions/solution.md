# Challenge 14 — Reference Solution

### 1. Smaller image
```dockerfile
FROM eclipse-temurin:21-jre-alpine
RUN apk add --no-cache curl
# ... rest of the runtime stage
```
Size: ~250 MB vs ~430 MB for the jammy variant. Alpine uses musl libc
instead of glibc — fine for the JVM, but some native libraries (e.g.
`librdkafka` in some setups) prefer glibc.

### 2. Non-root
```bash
$ docker compose exec app id
uid=1000(app) gid=1000(app) groups=1000(app)
```

### 3. Healthchecks
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
    mailhog:  { condition: service_started }
    minio:    { condition: service_started }
```

### 4. `.env`
```bash
# .env (do not commit)
POSTGRES_PASSWORD=...
JWT_SECRET=...
MINIO_ROOT_PASSWORD=...
```
```yaml
# docker-compose.yml
postgres:
  environment:
    POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
app:
  environment:
    JWT_SECRET: ${JWT_SECRET}
```
Add `.env` to `.gitignore`.

### 5. Resource limits
```yaml
app:
  mem_limit: 512m
  cpus: "1.0"
```
```bash
$ docker stats taskforge-app-1
NAME              CPU %   MEM USAGE / LIMIT
taskforge-app-1   5.32%   240MiB / 512MiB
```

### 6. Multi-arch
```bash
docker buildx create --use
docker buildx build --platform linux/amd64,linux/arm64 \
  -t taskforge:1.0.0 --push ./apps/taskforge
```

### 7. Makefile (stretch)
```makefile
.PHONY: up down logs build test
up:
	docker compose up -d --build
down:
	docker compose down
logs:
	docker compose logs -f
build:
	docker compose build
test:
	cd apps/taskforge && mvn -q test
```
`make up && make logs` is a satisfying two-liner.

> **Take it further:** replace `make` with `task` (go-task), or write a
> small `bin/dev` shell script. The point is: one command for the common
> workflows.
