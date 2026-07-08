# Lab 09 — Logs You Can Search, Config You Can Trust

**You'll:** add the trace-id filter, structured logging, validated
`@ConfigurationProperties`, and dev/prod profiles. Confirm the same JAR
runs against different config and produces different output.

⏱️ ~45 min. Run from `spring-boot-course/apps/taskforge`.

---

## Part A — The trace-id filter

`src/main/java/com/taskforge/observability/TraceIdFilter.java`:
```java
package com.taskforge.observability;

import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.slf4j.MDC;
import org.springframework.core.Ordered;
import org.springframework.core.annotation.Order;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;
import java.util.Optional;
import java.util.UUID;

@Component
@Order(Ordered.HIGHEST_PRECEDENCE)
public class TraceIdFilter extends OncePerRequestFilter {

    public static final String HEADER = "X-Trace-Id";
    public static final String MDC_KEY = "traceId";

    @Override
    protected void doFilterInternal(HttpServletRequest req, HttpServletResponse res,
                                    FilterChain chain) throws ServletException, IOException {
        String traceId = Optional.ofNullable(req.getHeader(HEADER))
                                 .filter(s -> !s.isBlank())
                                 .orElseGet(() -> UUID.randomUUID().toString());
        MDC.put(MDC_KEY, traceId);
        res.setHeader(HEADER, traceId);
        try {
            chain.doFilter(req, res);
        } finally {
            MDC.remove(MDC_KEY);
        }
    }
}
```

---

## Part B — Structured logging config

`src/main/resources/logback-spring.xml`:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<configuration>
  <springProperty scope="context" name="appName" source="spring.application.name"/>

  <appender name="TEXT" class="ch.qos.logback.core.ConsoleAppender">
    <encoder>
      <pattern>%d{HH:mm:ss.SSS} %-5level [%X{traceId:-}] %logger{20} - %msg%n</pattern>
    </encoder>
  </appender>

  <appender name="JSON" class="ch.qos.logback.core.ConsoleAppender">
    <encoder class="net.logstash.logback.encoder.LogstashEncoder">
      <customFields>{"service":"${appName}"}</customFields>
      <includeMdcKeyName>traceId</includeMdcKeyName>
    </encoder>
  </appender>

  <springProfile name="prod">
    <root level="INFO">
      <appender-ref ref="JSON"/>
    </root>
  </springProfile>

  <springProfile name="!prod">
    <root level="INFO">
      <appender-ref ref="TEXT"/>
    </root>
    <logger name="com.taskforge" level="DEBUG"/>
  </springProfile>
</configuration>
```

Add the dependency:
```xml
<dependency>
  <groupId>net.logstash.logback</groupId>
  <artifactId>logstash-logback-encoder</artifactId>
  <version>7.4</version>
</dependency>
```

---

## Part C — Validated `@ConfigurationProperties`

Replace `TaskforgeProperties`:
```java
package com.taskforge.config;

import jakarta.validation.Valid;
import jakarta.validation.constraints.*;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.validation.annotation.Validated;

import java.time.Duration;

@Validated
@ConfigurationProperties(prefix = "taskforge")
public record TaskforgeProperties(
    @NotNull @Valid Security security,
    @NotNull @Valid Pagination pagination,
    @NotNull @Valid Email email
) {
    public record Security(@NotNull @Valid Jwt jwt) {
        public record Jwt(@NotBlank String secret, @NotNull Duration expiration) {}
    }
    public record Pagination(@Min(1) int defaultPageSize, @Min(1) int maxPageSize) {}
    public record Email(boolean enabled, @Email String from) {}
}
```

> **Tip:** if Spring complains that validation annotations don't work on
> record components, add a `@Validated` to the class (already there) and
> ensure your main class has `@ConfigurationPropertiesScan`.

---

## Part D — Profiles

`application.yml` (shared, dev-friendly defaults):
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
        include: health,info,metrics

taskforge:
  security:
    jwt:
      secret: ${JWT_SECRET:dev-only-secret-please-change-me-32-bytes-min}
      expiration: PT1H
  pagination:
    default-page-size: 20
    max-page-size: 200
  email:
    enabled: false
    from: noreply@taskforge.com
```

`application-dev.yml`:
```yaml
logging:
  level:
    com.taskforge: DEBUG
taskforge:
  email:
    enabled: false
```

`application-prod.yml`:
```yaml
spring:
  datasource:
    url: ${DATABASE_URL}
    username: ${DATABASE_USER}
    password: ${DATABASE_PASSWORD}
logging:
  level:
    root: INFO
taskforge:
  email:
    enabled: true
    from: ${EMAIL_FROM}
```

---

## Part E — Run and verify

**Dev profile (default):**
```bash
mvn -q spring-boot:run
# Logs are human-readable; DEBUG enabled for com.taskforge.
# Test: curl -H "X-Trace-Id: my-trace" -H "Authorization: Bearer $TOKEN" ...
# Every log line shows [my-trace]. The response carries the same header.
```

**Prod profile:**
```bash
SPRING_PROFILES_ACTIVE=prod \
DATABASE_URL=jdbc:postgresql://localhost:5432/taskforge \
DATABASE_USER=taskforge \
DATABASE_PASSWORD=taskforge \
EMAIL_FROM=noreply@taskforge.com \
mvn -q spring-boot:run
```
Logs are JSON. `taskforge.email.enabled` is `true`.

✅ **Checkpoint:** the same JAR, two different outputs, two different
config values. Spring Boot's externalized config is working.

---

## What you learned

- A `TraceIdFilter` (or a Spring Boot 3.3 `MicrometerObservation`-based
  alternative) puts a request id on the MDC, and Logback prints it on
  every line.
- `logback-spring.xml` is the Spring-aware variant of Logback's config
  file. Use `<springProfile>` to switch appenders per environment.
- `logstash-logback-encoder` gives you JSON logs with one dependency.
- `@ConfigurationProperties` + `@Validated` = typed config that fails fast.
- Profiles + `${VAR:default}` + `application-{profile}.yml` = the 12-factor
  pattern in Spring.

➡️ Now try the **[challenge](./challenge.md)**, then move to
[Module 10](../10-caching-redis/).
