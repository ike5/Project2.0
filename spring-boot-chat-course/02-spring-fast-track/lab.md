# Lab 02 — Build the Pulse Skeleton

**You'll:** generate the Pulse project, wire virtual threads and Actuator, read
the auto-configuration report until Spring stops being magic, add typed config,
and confirm graceful shutdown works.

⏱️ ~70 min. Work in `spring-boot-chat-course/apps/`.

---

## Part A — Generate the project

Use `start.spring.io` from the command line so the whole thing is reproducible:

```bash
cd spring-boot-chat-course/apps

curl https://start.spring.io/starter.zip \
  -d type=maven-project \
  -d language=java \
  -d bootVersion=3.4.1 \
  -d javaVersion=21 \
  -d groupId=com.pulse \
  -d artifactId=pulse \
  -d name=pulse \
  -d packageName=com.pulse \
  -d dependencies=web,websocket,actuator,validation,data-jpa,postgresql,flyway,data-redis,testcontainers \
  -o pulse.zip

unzip -q pulse.zip -d pulse && rm pulse.zip
cd pulse
```

**Expected:**
```bash
ls
```
```
HELP.md  mvnw  mvnw.cmd  pom.xml  src
```

> **No network?** `spring-boot-chat-course/02-spring-fast-track/code/pom.xml`
> has the equivalent POM; create the directory structure by hand and copy it in.

Confirm it builds:

```bash
./mvnw -q -DskipTests package
```

**Expected:** silence, then:
```bash
ls target/*.jar
```
```
target/pulse-0.0.1-SNAPSHOT.jar
```

### What those dependencies are for

| Dependency | Why Pulse needs it | First used |
|------------|-------------------|------------|
| `web` | Embedded Tomcat, REST endpoints for room/history APIs | 04 |
| `websocket` | The STOMP-over-WebSocket support — the whole point | 04 |
| `actuator` | Metrics, health, thread dumps. You'll live here. | 02 |
| `validation` | Bean Validation on inbound message payloads | 05 |
| `data-jpa` + `postgresql` | Room/user metadata | 12 |
| `flyway` | Schema migrations, including the partitioning DDL | 12 |
| `data-redis` | Pub/Sub, Streams, presence | 07 |
| `testcontainers` | Integration tests against real Redis and Postgres | 05 |

---

## Part B — Configuration

Replace `src/main/resources/application.properties` with `application.yml`
(delete the `.properties` file):

```bash
rm src/main/resources/application.properties
cat > src/main/resources/application.yml <<'EOF'
spring:
  application:
    name: pulse

  # Module 01's headline feature. Read the warning in this module's README
  # before you assume this makes everything faster.
  threads:
    virtual:
      enabled: true

  datasource:
    url: jdbc:postgresql://localhost:5432/pulse
    username: pulse
    password: pulse
    hikari:
      maximum-pool-size: 20          # deliberately small — Module 06 makes this hurt
      pool-name: pulse-pool

  jpa:
    hibernate:
      ddl-auto: validate             # never 'update' — Flyway owns the schema
    open-in-view: false              # see the note below
    properties:
      hibernate.jdbc.batch_size: 50

  flyway:
    enabled: true
    baseline-on-migrate: true

  data:
    redis:
      host: localhost
      port: 6379
      timeout: 2s

server:
  port: 8080
  shutdown: graceful

spring.lifecycle:
  timeout-per-shutdown-phase: 45s

management:
  endpoints:
    web:
      exposure:
        include: health,info,metrics,prometheus,conditions,threaddump,heapdump,loggers,configprops,env
  endpoint:
    health:
      show-details: always
      probes:
        enabled: true
  metrics:
    tags:
      application: pulse

pulse:
  fanout:
    max-in-flight: 100
    dedup-window: 5m
  limits:
    max-room-size: 5000
    max-message-bytes: 4096

logging:
  level:
    com.pulse: DEBUG
EOF
```

> **`open-in-view: false` matters.** The default (`true`) keeps a JPA session —
> *and therefore a database connection* — open for the entire request, including
> while you're serializing JSON. On a 20-connection pool with thousands of
> concurrent virtual threads, that's a self-inflicted outage. Spring Boot warns
> about this at startup for a reason.

---

## Part C — Typed configuration properties

`src/main/java/com/pulse/config/PulseProperties.java`:

```java
package com.pulse.config;

import jakarta.validation.Valid;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Positive;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.validation.annotation.Validated;

import java.time.Duration;

@ConfigurationProperties(prefix = "pulse")
@Validated
public record PulseProperties(
        @Valid @NotNull Fanout fanout,
        @Valid @NotNull Limits limits) {

    public record Fanout(
            @Positive int maxInFlight,
            @NotNull Duration dedupWindow) {}

    public record Limits(
            @Positive int maxRoomSize,
            @Positive int maxMessageBytes) {}
}
```

Enable scanning in `PulseApplication.java`:

```java
package com.pulse;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.context.properties.ConfigurationPropertiesScan;

@SpringBootApplication
@ConfigurationPropertiesScan
public class PulseApplication {
    public static void main(String[] args) {
        SpringApplication.run(PulseApplication.class, args);
    }
}
```

**Prove the validation is real.** Temporarily set `max-in-flight: -5` in
`application.yml` and start the app:

```bash
./mvnw spring-boot:run
```

**Expected — startup failure, not a runtime surprise:**
```
***************************
APPLICATION FAILED TO START
***************************

Description:

Binding to target ... failed:

    Property: pulse.fanout.max-in-flight
    Value: "-5"
    Reason: must be greater than 0
```

✅ Put it back to `100`. That fail-fast behaviour is the entire argument for
`@ConfigurationProperties` over `@Value`.

---

## Part D — First run

Start the data tier if it isn't up:

```bash
docker compose -f ../../infra/compose.dev.yml up -d
```

Create the Flyway baseline so JPA validation passes —
`src/main/resources/db/migration/V1__init.sql`:

```sql
CREATE TABLE rooms (
    id          bigserial PRIMARY KEY,
    name        text        NOT NULL UNIQUE,
    created_at  timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE users (
    id           bigserial PRIMARY KEY,
    username     text        NOT NULL UNIQUE,
    display_name text        NOT NULL,
    created_at   timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE room_members (
    room_id   bigint NOT NULL REFERENCES rooms(id) ON DELETE CASCADE,
    user_id   bigint NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    joined_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (room_id, user_id)
);

-- "which rooms is this user in" — the reverse lookup needs its own index
CREATE INDEX idx_room_members_user ON room_members (user_id, room_id);
```

Run it:

```bash
./mvnw spring-boot:run
```

**Expected** — the lines worth reading:
```
Flyway Community Edition 10.20.1 by Redgate
Successfully validated 1 migration
Creating Schema History table "public"."flyway_schema_history"
Migrating schema "public" to version "1 - init"
Successfully applied 1 migration to schema "public"
Tomcat started on port 8080 (http) with context path '/'
Started PulseApplication in 2.184 seconds (process running for 2.41)
```

Confirm:

```bash
curl -s localhost:8080/actuator/health | jq
```

**Expected:**
```json
{
  "status": "UP",
  "components": {
    "db":    { "status": "UP", "details": { "database": "PostgreSQL", "validationQuery": "isValid()" } },
    "diskSpace": { "status": "UP" },
    "ping":  { "status": "UP" },
    "redis": { "status": "UP", "details": { "version": "7.4.1" } }
  }
}
```

✅ Note you never wrote a health check for Postgres or Redis. Auto-configuration
saw the beans on the classpath and registered `DataSourceHealthIndicator` and
`RedisHealthIndicator`. That's the mechanism from the README, doing something
useful.

---

## Part E — Prove virtual threads are actually on

```bash
curl -s localhost:8080/actuator/health > /dev/null
curl -s localhost:8080/actuator/threaddump | jq -r '.threads[].threadName' | grep -c 'VirtualThread'
```

Better — look at what handled your request. Add a temporary controller,
`src/main/java/com/pulse/WhoAmIController.java`:

```java
package com.pulse;

import org.springframework.web.bind.annotation.*;

@RestController
public class WhoAmIController {
    @GetMapping("/whoami")
    public String whoami() {
        Thread t = Thread.currentThread();
        return "thread=" + t + "\nvirtual=" + t.isVirtual() + "\n";
    }
}
```

```bash
curl -s localhost:8080/whoami
```

**Expected with `spring.threads.virtual.enabled: true`:**
```
thread=VirtualThread[#62,tomcat-handler-0]/runnable@ForkJoinPool-1-worker-3
virtual=true
```

Now flip it off and restart:
```bash
SPRING_THREADS_VIRTUAL_ENABLED=false ./mvnw spring-boot:run
curl -s localhost:8080/whoami
```

**Expected:**
```
thread=Thread[#54,http-nio-8080-exec-1,5,main]
virtual=false
```

✅ `http-nio-8080-exec-1` is a member of Tomcat's classic 200-thread pool. That
one env var is the difference between a 200-request ceiling and a
virtual-thread-per-request model.

> Note the env-var spelling: `SPRING_THREADS_VIRTUAL_ENABLED` maps to
> `spring.threads.virtual.enabled`. That's **relaxed binding**, and it's how all
> config gets overridden in Docker and Kubernetes later.

Turn it back on before continuing.

---

## Part F — Read the auto-configuration report

This is the part that makes Spring stop being magic. Do not skip it.

```bash
curl -s localhost:8080/actuator/conditions | jq '.contexts.pulse.positiveMatches | keys | length'
curl -s localhost:8080/actuator/conditions | jq '.contexts.pulse.negativeMatches | keys | length'
```

**Expected** (numbers will vary by Boot version):
```
118
542
```

118 auto-configurations matched; 542 were evaluated and rejected. Look at a
specific one:

```bash
curl -s localhost:8080/actuator/conditions \
  | jq '.contexts.pulse.positiveMatches | with_entries(select(.key | test("Redis")))'
```

**Expected:**
```json
{
  "RedisAutoConfiguration#redisTemplate": [
    {
      "condition": "OnBeanCondition",
      "message": "@ConditionalOnMissingBean (names: redisTemplate; types: org.springframework.data.redis.core.RedisTemplate) did not find any beans"
    }
  ],
  "RedisAutoConfiguration": [
    {
      "condition": "OnClassCondition",
      "message": "@ConditionalOnClass found required class 'org.springframework.data.redis.core.RedisOperations'"
    }
  ]
}
```

✅ Read that message literally: *"did not find any beans"*. Spring registered a
`RedisTemplate` **because you didn't**. In Module 07 you will define your own,
and this auto-configuration will silently step aside. That's `@ConditionalOnMissingBean`,
and it's the most important five words in Spring Boot.

Now look at something that *didn't* match:

```bash
curl -s localhost:8080/actuator/conditions \
  | jq -r '.contexts.pulse.negativeMatches | with_entries(select(.key | test("Kafka"))) | keys[]'
```

**Expected:**
```
KafkaAutoConfiguration
```

Because `spring-kafka` isn't on the classpath. In Module 16 you'll add it and
watch this move from `negativeMatches` to `positiveMatches` without writing a
line of configuration.

---

## Part G — Graceful shutdown

This matters more for WebSocket than for HTTP, so let's confirm it works now.

Start the app, then in another terminal:

```bash
curl -s "localhost:8080/actuator/health/readiness" | jq
```
**Expected:**
```json
{ "status": "UP", "components": { "readinessState": { "status": "UP" } } }
```

Now send `SIGTERM` and watch the logs:

```bash
kill -TERM $(pgrep -f 'pulse.*jar\|PulseApplication')
```

**Expected in the app log:**
```
Commencing graceful shutdown. Waiting for active requests to complete
Graceful shutdown complete
```

✅ In Module 18 you'll add a shutdown hook that also sends a STOMP close frame
with a "reconnect after jittered backoff" hint, so 30,000 clients don't come
back simultaneously. The plumbing starts here.

---

## Part H — Baseline metrics

```bash
curl -s localhost:8080/actuator/metrics | jq -r '.names[]' | head -20
curl -s localhost:8080/actuator/metrics/jvm.threads.live | jq
curl -s localhost:8080/actuator/prometheus | grep -E '^(jvm_memory_used|hikaricp)' | head
```

**Expected** (excerpt):
```json
{
  "name": "jvm.threads.live",
  "measurements": [ { "statistic": "VALUE", "value": 24 } ]
}
```

✅ **24 live threads** for a running Spring Boot app with Postgres and Redis
connected. Note this number — in Module 06 you'll hold 20,000 WebSocket
connections and it will barely move. That's the whole story of this course in
one metric.

Record it in `results.md`.

---

## What you did

- Generated Pulse with exactly the dependencies the course needs, and can say
  what each is for.
- Wired typed, validated configuration that fails at startup, not at 3 a.m.
- Turned on virtual threads and **proved** it with `/whoami`, then proved the
  difference by turning it off.
- Read the auto-configuration report and saw `@ConditionalOnMissingBean` decide
  something real.
- Confirmed graceful shutdown, health probes, and baseline metrics.

Now do [`challenge.md`](./challenge.md).

Then: [Module 03 — Real-Time Transports on the Wire](../03-realtime-transports/).
