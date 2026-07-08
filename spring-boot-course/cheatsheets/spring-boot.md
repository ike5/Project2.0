# Cheatsheet — Spring Boot

Quick reference for the framework. Keep it open while you build.

## Project layout (the standard)

```
my-app/
├── pom.xml
├── mvnw, mvnw.cmd
├── src/
│   ├── main/
│   │   ├── java/com/example/myapp/
│   │   │   ├── MyAppApplication.java
│   │   │   ├── config/             ← @Configuration, @ConfigurationProperties
│   │   │   ├── web/                ← @RestController, @ControllerAdvice
│   │   │   ├── service/            ← @Service, business logic
│   │   │   ├── repository/         ← @Repository, JPA interfaces
│   │   │   ├── domain/             ← @Entity, records for domain
│   │   │   └── api/                ← DTOs (request/response records)
│   │   └── resources/
│   │       ├── application.yml
│   │       ├── application-dev.yml
│   │       ├── application-prod.yml
│   │       ├── logback-spring.xml
│   │       ├── db/migration/       ← Flyway SQL files
│   │       └── templates/          ← Thymeleaf
│   └── test/
│       └── java/com/example/myapp/
└── target/                          ← build output (gitignored)
```

## The main class

```java
@SpringBootApplication
@EnableCaching
@EnableAsync
@ConfigurationPropertiesScan
public class MyAppApplication {
    public static void main(String[] args) {
        SpringApplication.run(MyAppApplication.class, args);
    }
}
```

## Maven essentials

```bash
mvn spring-boot:run              # dev (recompiles + restarts)
mvn -q compile                   # compile
mvn -q test                      # compile + tests (unit only by default)
mvn -q verify                    # compile + unit + integration tests
mvn -q -DskipTests package       # build the JAR
mvn -q -DskipTests -Pprod package # with a profile

java -jar target/myapp-0.0.1-SNAPSHOT.jar
```

## Dependency starter cheatsheet

```xml
<dependency><groupId>org.springframework.boot</groupId><artifactId>spring-boot-starter-web</artifactId></dependency>
<dependency><groupId>org.springframework.boot</groupId><artifactId>spring-boot-starter-data-jpa</artifactId></dependency>
<dependency><groupId>org.springframework.boot</groupId><artifactId>spring-boot-starter-security</artifactId></dependency>
<dependency><groupId>org.springframework.boot</groupId><artifactId>spring-boot-starter-data-redis</artifactId></dependency>
<dependency><groupId>org.springframework.boot</groupId><artifactId>spring-boot-starter-cache</artifactId></dependency>
<dependency><groupId>org.springframework.boot</groupId><artifactId>spring-boot-starter-validation</artifactId></dependency>
<dependency><groupId>org.springframework.boot</groupId><artifactId>spring-boot-starter-actuator</artifactId></dependency>
<dependency><groupId>org.springframework.boot</groupId><artifactId>spring-boot-starter-mail</artifactId></dependency>
<dependency><groupId>org.springframework.kafka</groupId><artifactId>spring-kafka</artifactId></dependency>
<dependency><groupId>org.flywaydb</groupId><artifactId>flyway-core</artifactId></dependency>
<dependency><groupId>org.flywaydb</groupId><artifactId>flyway-database-postgresql</artifactId></dependency>
<dependency><groupId>io.jsonwebtoken</groupId><artifactId>jjwt-api</artifactId><version>0.12.6</version></dependency>
<dependency><groupId>io.jsonwebtoken</groupId><artifactId>jjwt-impl</artifactId><version>0.12.6</version><scope>runtime</scope></dependency>
<dependency><groupId>io.jsonwebtoken</groupId><artifactId>jjwt-jackson</artifactId><version>0.12.6</version><scope>runtime</scope></dependency>
<dependency><groupId>io.minio</groupId><artifactId>minio</artifactId><version>8.5.10</version></dependency>
<dependency><groupId>org.springdoc</groupId><artifactId>springdoc-openapi-starter-webmvc-ui</artifactId><version>2.6.0</version></dependency>
<dependency><groupId>net.logstash.logback</groupId><artifactId>logstash-logback-encoder</artifactId><version>7.4</version></dependency>
<dependency><groupId>io.micrometer</groupId><artifactId>micrometer-registry-prometheus</artifactId></dependency>
<dependency><groupId>io.micrometer</groupId><artifactId>micrometer-tracing-bridge-otel</artifactId></dependency>

<dependency><groupId>org.testcontainers</groupId><artifactId>postgresql</artifactId><scope>test</scope></dependency>
<dependency><groupId>org.testcontainers</groupId><artifactId>junit-jupiter</artifactId><scope>test</scope></dependency>
```

## `application.yml` (the standard sections)

```yaml
spring:
  application: { name: myapp }
  profiles: { active: dev }
  datasource: { url, username, password }
  jpa: { hibernate: { ddl-auto: validate }, open-in-view: false }
  flyway: { locations: classpath:db/migration }
  data: { redis: { host, port } }
  cache: { type: redis }
  mail: { host, port, ... }
  kafka: { bootstrap-servers, producer, consumer }
  security: { user: { name, password } }  # only if you don't override

server: { port: 8080 }

management:
  endpoints: { web: { exposure: { include: health,info,metrics,prometheus } } }
  endpoint: { health: { probes: { enabled: true } } }

myapp:
  anything: ...
```

## Annotations you'll use 100×

```java
// stereotypes
@Component, @Service, @Repository, @Controller, @RestController, @Configuration

// web
@RestController @RequestMapping("/api/x")
@GetMapping @PostMapping @PutMapping @DeleteMapping @PatchMapping
@PathVariable @RequestParam @RequestBody @RequestHeader
@ResponseStatus(HttpStatus.CREATED) ResponseEntity<T>

// validation
@Valid @NotNull @NotBlank @NotEmpty @Size @Min @Max @Email @Pattern

// persistence
@Entity @Table @Id @GeneratedValue @Column
@OneToMany @ManyToOne @OneToOne @ManyToMany
@JoinColumn @MappedBy @Transactional(readOnly=true)

// cross-cutting
@Cacheable @CacheEvict @CachePut
@Async @Scheduled @EventListener
@Retryable @RetryableTopic
@PreAuthorize @Secured @RolesAllowed
@ConfigurationProperties(prefix = "x")
@ConditionalOnProperty, @ConditionalOnClass, @ConditionalOnMissingBean
@Profile("dev")
```

## Constructor injection (the only kind you should use)

```java
@Service
public class MyService {
    private final MyRepository repo;
    private final Clock clock;
    public MyService(MyRepository repo, Clock clock) {  // no @Autowired needed
        this.repo = repo;
        this.clock = clock;
    }
}
```

## Global exception handler

```java
@RestControllerAdvice
public class ApiExceptionHandler {

    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ProblemDetail handleValidation(MethodArgumentNotValidException ex) {
        ProblemDetail pd = ProblemDetail.forStatus(HttpStatus.BAD_REQUEST);
        pd.setTitle("Validation failed");
        pd.setProperty("errors", ex.getBindingResult().getFieldErrors().stream()
            .map(fe -> Map.of("field", fe.getField(), "message", fe.getDefaultMessage()))
            .toList());
        return pd;
    }

    @ExceptionHandler(NotFoundException.class)
    public ProblemDetail handleNotFound(NotFoundException ex) {
        return ProblemDetail.forStatusAndDetail(HttpStatus.NOT_FOUND, ex.getMessage());
    }
}
```

## Actuator endpoints

```
/actuator/health            (aggregate)
/actuator/health/liveness
/actuator/health/readiness
/actuator/info
/actuator/metrics           (list)
/actuator/metrics/{name}    (one metric)
/actuator/prometheus        (Prometheus format)
```

## Quick debugging

```bash
mvn spring-boot:run -Dspring-boot.run.arguments="--debug"     # auto-config report
mvn spring-boot:run -Dspring-boot.run.profiles=dev            # pick a profile
curl -s localhost:8080/actuator/health | jq
curl -s localhost:8080/actuator/metrics | jq
```

## Common pitfalls

- **Field injection** (`@Autowired private Foo foo;`) — prefer constructor.
- **`open-in-view: true`** (default in older Boot) — turn it off.
- **`ddl-auto: update`** in prod — never; use Flyway.
- **Logging secrets** — `log.info("config={}", props)` leaks the whole object.
- **Catching `Exception` and swallowing it** — the worst bug in the JVM.
