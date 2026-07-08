# Module 09 — Logging, Configuration & Profiles

**Goal:** ship logs that a human can read **and** a machine can parse, with a
trace id that follows a request through every layer. Make your configuration
**typed and externalized** so the same JAR runs in dev, test, and prod.
By the end of this module, "where did this error come from?" is a 5-second
question to answer.

⏱️ ~2 hours · 🎯 Prereq: Modules 02–08 complete (a working tested app).

> Logging and configuration are the difference between a project and a
> service. This module is short on code and long on conventions — exactly
> what real production codebases insist on.

---

## 1. SLF4J + Logback — Spring Boot's logging story

Spring Boot uses **SLF4J** as the API and **Logback** as the implementation.

```java
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

@Service
public class TaskService {
    private static final Logger log = LoggerFactory.getLogger(TaskService.class);

    public Task create(String title, String description, Long ownerId) {
        log.info("creating task title='{}' ownerId={}", title, ownerId);
        // ...
    }
}
```

**Log levels (low → high severity):** `TRACE`, `DEBUG`, `INFO`, `WARN`, `ERROR`.

**MDC (Mapped Diagnostic Context)** — per-thread key/value pairs attached
to every log line. Module 06's trace-id filter is the canonical example.

---

## 2. Configure log levels — `application.yml`

```yaml
logging:
  level:
    root: INFO
    com.taskforge: DEBUG
    org.hibernate.SQL: INFO
    org.springframework.security: INFO
```

`logging.level.<package>` sets the threshold for every logger in that
package. `root` is the fallback.

> **Pro tip:** at `DEBUG`, Hibernate logs every SQL statement and binds every
> parameter. It's invaluable in development; it's noise in production. Use
> profiles to flip this.

---

## 3. Structured (JSON) logs for production

Plain text is great for humans. JSON is great for
**Elasticsearch / Loki / Splunk / CloudWatch**:

```json
{
  "timestamp": "2024-01-15T10:30:00.123Z",
  "level": "INFO",
  "logger": "com.taskforge.task.TaskService",
  "message": "creating task title='buy milk' ownerId=42",
  "traceId": "a1b2c3d4-...",
  "service": "taskforge"
}
```

Add `logstash-logback-encoder`:
```xml
<dependency>
  <groupId>net.logstash.logback</groupId>
  <artifactId>logstash-logback-encoder</artifactId>
  <version>7.4</version>
</dependency>
```

`src/main/resources/logback-spring.xml`:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<configuration>
  <springProperty scope="context" name="appName" source="spring.application.name"/>
  <appender name="JSON" class="ch.qos.logback.core.ConsoleAppender">
    <encoder class="net.logstash.logback.encoder.LogstashEncoder">
      <customFields>{"service":"${appName}"}</customFields>
    </encoder>
  </appender>

  <appender name="TEXT" class="ch.qos.logback.core.ConsoleAppender">
    <encoder>
      <pattern>%d{HH:mm:ss.SSS} %-5level [%X{traceId}] %logger{20} - %msg%n</pattern>
    </encoder>
  </appender>

  <root level="INFO">
    <!-- dev: pretty; prod: structured -->
    <if condition='isDefined("SPRING_PROFILES_ACTIVE") &amp;&amp; "prod".equals(property("SPRING_PROFILES_ACTIVE"))'>
      <then><appender-ref ref="JSON"/></then>
      <else><appender-ref ref="TEXT"/></else>
    </if>
  </root>
</configuration>
```

> Spring's `<springProfile>` element is simpler for profile-based switches —
> see the README's example.

---

## 4. Putting the trace id everywhere

Module 06's `TraceIdFilter` puts a `traceId` in the MDC. The
`logback-spring.xml` pattern above includes it. To put it in your service
logs, MDC is read with:

```java
import org.slf4j.MDC;

log.info("creating task traceId={} userId={}", MDC.get("traceId"), ownerId);
```

A request id header convention:
- Client sends `X-Trace-Id` (or you generate one).
- Server echoes `X-Trace-Id` on the response.
- Every log line includes it.
- Every outbound HTTP call sends it.
- Every Kafka message key includes it.

Module 14 reuses this when the app runs in Docker; Module 11 reuses it in
Kafka headers.

---

## 5. `@ConfigurationProperties` — typed, validated configuration

`application.yml`:
```yaml
taskforge:
  security:
    jwt:
      secret: ${JWT_SECRET}
      expiration: PT1H
  pagination:
    default-page-size: 20
    max-page-size: 200
  email:
    enabled: true
    from: noreply@taskforge.com
```

`TaskforgeProperties.java`:
```java
@ConfigurationProperties(prefix = "taskforge")
@Validated
public record TaskforgeProperties(
    @NotNull Security security,
    @NotNull Pagination pagination,
    @NotNull Email email
) {
    public record Security(@NotNull Jwt jwt) {
        public record Jwt(@NotBlank String secret, @NotNull Duration expiration) {}
    }
    public record Pagination(@Min(1) int defaultPageSize, @Min(1) int maxPageSize) {}
    public record Email(boolean enabled, @Email String from) {}
}
```

> `@Validated` + Jakarta Validation annotations on the record make Spring
> refuse to start if the config is missing or malformed. **Fail fast is the
> only safe mode.**

Enable scanning: `@ConfigurationPropertiesScan` on the main class
(already added in Module 03).

---

## 6. Profiles — dev, test, prod

Three files, three environments:

```
src/main/resources/
├── application.yml           ← shared config
├── application-dev.yml       ← dev overrides
├── application-test.yml      ← test overrides
└── application-prod.yml      ← prod overrides
```

Spring picks them by `spring.profiles.active`. Activate with:
- env: `SPRING_PROFILES_ACTIVE=prod`
- CLI: `--spring.profiles.active=prod`
- YAML: `spring.profiles.active: dev`

`application-dev.yml`:
```yaml
logging:
  level:
    com.taskforge: DEBUG
    org.hibernate.SQL: DEBUG
taskforge:
  email:
    enabled: false
spring:
  jpa:
    show-sql: true
```

`application-prod.yml`:
```yaml
logging:
  level:
    root: INFO
spring:
  datasource:
    url: ${DATABASE_URL}
    username: ${DATABASE_USER}
    password: ${DATABASE_PASSWORD}
  jpa:
    hibernate:
      ddl-auto: validate
taskforge:
  email:
    enabled: true
    from: ${EMAIL_FROM}
```

> **Rule of thumb:** `application.yml` holds shared defaults; environment-
> specific files override them. Never put secrets in `application.yml` —
> only env-var references (`${...}`).

---

## 7. `@Profile` — beans that exist only in some environments

```java
@Configuration
@Profile("dev")
public class DevDataConfig {
    @Bean
    public CommandLineRunner seedData(TaskRepository repo) {
        return args -> repo.save(new Task("welcome", "first task!"));
    }
}

@Configuration
@Profile("prod")
public class ProdDataConfig {
    // empty — production has real data
}
```

---

## 8. `@ConditionalOnProperty` — toggle features with a flag

```java
@Bean
@ConditionalOnProperty(name = "taskforge.email.enabled", havingValue = "true")
public EmailSender emailSender() {
    return new SmtpEmailSender();
}

@Bean
@ConditionalOnMissingBean(EmailSender.class)
public EmailSender noOpEmailSender() {
    return new NoOpEmailSender();
}
```

This is the **"default off, opt in"** pattern. Off-by-default features are
safer than on-by-default ones.

---

## 9. Externalize **everything** env-specific

The 12-factor rule: **the same artifact runs in every environment**; only
the environment changes. The contract:

| Thing | Lives in | Override via |
|-------|----------|-------------|
| DB URL | env var | `DATABASE_URL` |
| DB credentials | env var | `DATABASE_USER`, `DATABASE_PASSWORD` |
| JWT secret | env var / secret manager | `JWT_SECRET` |
| Feature flags | env var | `TASKFORGE_EMAIL_ENABLED=true` |
| Log level | env var | `LOGGING_LEVEL_ROOT=DEBUG` |
| Port | env var | `SERVER_PORT=8080` |
| Spring profile | env var | `SPRING_PROFILES_ACTIVE=prod` |

> In Docker, set them in `docker-compose.yml`. In Kubernetes, set them in a
> `ConfigMap` or `Secret`. In a CI test, set them as environment
> variables in the pipeline.

---

## 10. A "right" `application.yml` for `taskforge`

```yaml
spring:
  application:
    name: taskforge
  profiles:
    active: dev
  jpa:
    open-in-view: false
  flyway:
    locations: classpath:db/migration

server:
  port: ${SERVER_PORT:8080}

management:
  endpoints:
    web:
      exposure:
        include: health,info,metrics,prometheus

taskforge:
  security:
    jwt:
      secret: ${JWT_SECRET:dev-only-secret-please-change-me-32-bytes-min}
      expiration: ${JWT_EXPIRATION:PT1H}
  pagination:
    default-page-size: 20
    max-page-size: 200
  email:
    enabled: ${TASKFORGE_EMAIL_ENABLED:false}
    from: ${EMAIL_FROM:noreply@taskforge.com}

logging:
  level:
    root: INFO
    com.taskforge: DEBUG
```

> The `${VAR:default}` syntax is Spring's "use this env var, or fall back to
> the default." The defaults are dev-friendly; in prod you set the env vars.

---

## 11. Common pitfalls

| Symptom | Cause | Fix |
|---------|-------|-----|
| Secret shows up in plaintext in startup logs | You logged it (or the auto-config did) | Set `logging.level.org.springframework.boot.autoconfigure.condition=ERROR` and avoid `log.info("config={}", props)` |
| Tests can't see the prod profile | `@ActiveProfiles("test")` not set on the test class | Add `@ActiveProfiles("test")` |
| `@ConfigurationProperties` record won't bind | Snake-case in YAML vs camelCase in the record | Spring is smart enough — but a missing getter or a primitive default that can't be null won't work. Use boxed types or `Duration`/`Size` types |
| `IllegalStateException: Failed to bind properties` | Validation failed on a `@ConfigurationProperties` record | Read the message; the field that's missing is named in the error |
| `logback-spring.xml` changes ignored | You named it `logback.xml` | Use `logback-spring.xml` for Spring-aware features |

---

## 12. Do the lab

Wire the trace-id filter, structured logs, `@ConfigurationProperties` with
validation, and `dev`/`prod` profiles. Confirm the same JAR runs against
different config.

👉 **[lab.md](./lab.md)**

Then test yourself: 👉 **[challenge.md](./challenge.md)**

---

## Key terms (see [GLOSSARY](../GLOSSARY.md))

SLF4J · Logback · log level · MDC · structured logging · `logstash-logback-encoder` · `@ConfigurationProperties` · `@Validated` · `@Profile` · `@ConditionalOnProperty` · 12-factor config · `${VAR:default}` · `application-{profile}.yml`

**Next →** [Module 10: Caching with Redis & Spring Cache](../10-caching-redis/)
