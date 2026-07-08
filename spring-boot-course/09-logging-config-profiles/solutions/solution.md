# Challenge 09 — Reference Solution

### 1. MDC for the user
```java
// JwtAuthenticationFilter, after setting the Authentication
Claims claims = jwt.parse(token).getPayload();
MDC.put("userId", claims.getSubject());
MDC.put("userEmail", claims.get("email", String.class));
try { chain.doFilter(req, res); }
finally { MDC.remove("userId"); MDC.remove("userEmail"); }
```
`logback-spring.xml`:
```xml
<pattern>%d{HH:mm:ss.SSS} %-5level [%X{traceId:-} u=%X{userId:-}] %logger{20} - %msg%n</pattern>
```

### 2. Conditional email bean
```java
public interface EmailSender { void send(String to, String subject, String body); }

@Component
@ConditionalOnProperty(name = "taskforge.email.enabled", havingValue = "true")
class SmtpEmailSender implements EmailSender {
    public void send(String to, String s, String b) { /* ... */ }
}

@Component
@ConditionalOnMissingBean(EmailSender.class)
class NoOpEmailSender implements EmailSender {
    public void send(String to, String s, String b) { /* no-op */ }
}
```

### 3. Fail fast
Set `taskforge.security.jwt.secret: ""` → startup fails with:
```
***************************
APPLICATION FAILED TO START
***************************
Description: ...must not be blank
Action: Update your application configuration
```

### 4. CI profile
`application-ci.yml`:
```yaml
spring:
  datasource:
    url: jdbc:tc:postgresql:16:///taskforge   # Testcontainers JDBC URL
    username: taskforge
    password: taskforge
  flyway:
    clean-disabled: false
```
Or just set `SPRING_PROFILES_ACTIVE=ci` and use Testcontainers in a base
test class. Spring's `JdbcDatabaseContainer` integrates with
`spring.datasource.url` via the `jdbc:tc:...` URL.

### 5. Custom property source
```java
public class YamlPropertySourceFactory extends DefaultPropertySourceFactory {
    @Override
    protected PropertySource<?> createPropertySource(String name, EncodedResource resource) throws IOException {
        return new YamlPropertySourceLoader().load(resource.getResource().getFilename(), resource.getResource()).get(0);
    }
}

@Configuration
@PropertySource(value = "classpath:branding.yml", factory = YamlPropertySourceFactory.class)
public class BrandingConfig { /* @Value("${branding.tagline}") */ }
```

### 6. `@Observed` (stretch)
```java
@Service
public class TaskService {
    @Observed(name = "task.create", contextualName = "createTask")
    public Task create(String title, String description, Long ownerId) { ... }
}
```
```yaml
management:
  observations:
    annotations:
      enabled: true
```
Confirm:
```bash
curl -s localhost:8080/actuator/metrics/task.create
# → {"name":"task.create","measurements":[...],"availableTags":["outcome",...]}
```

> Module 15 promotes these to Prometheus metrics.
