# Module 02 — Spring Boot Fast-Track

**Goal:** Get productive in Spring Boot fast, by building Pulse's skeleton — and
understand the two or three pieces of Spring's machinery that actually matter
when you're holding 50,000 sockets, rather than the forty that don't.

⏱️ ~4 hours · **Prerequisites:** Modules 00–01.

> **If you already know Spring Boot**, skim the README, skip to Part E of the
> lab (virtual threads + Actuator wiring), and move on. Nothing here is secret.

---

## Spring in one page, for people who already know a framework

Spring is a **dependency injection container** with a very large ecosystem
bolted on. If you know Django, Rails, NestJS, or ASP.NET Core, the mapping is:

| Concept | Spring | Django | NestJS | ASP.NET Core |
|---------|--------|--------|--------|--------------|
| DI container | `ApplicationContext` | (none — modules) | Nest IoC | `IServiceProvider` |
| Component | `@Component`/`@Service` | — | `@Injectable()` | registered service |
| Route handler | `@RestController` | view | `@Controller()` | Controller |
| ORM entity | `@Entity` | Model | Entity | Entity |
| Repo layer | `JpaRepository<T,ID>` | Manager/QuerySet | Repository | `DbSet<T>` |
| Config | `application.yml` + `@ConfigurationProperties` | `settings.py` | `ConfigModule` | `appsettings.json` |
| Middleware | Filter / Interceptor | Middleware | Middleware/Guard | Middleware |
| Migrations | Flyway / Liquibase | `manage.py migrate` | TypeORM migrations | EF migrations |

The one genuinely distinctive thing is **auto-configuration**, so let's be
precise about it, because "magic" is exactly the wrong mental model for a course
about understanding things deeply.

### Auto-configuration is not magic — it's conditional bean definitions

When you add `spring-boot-starter-data-redis`, Spring Boot does *not* scan your
code and guess. It does this:

1. Every starter jar ships a file listing auto-configuration classes
   (`META-INF/spring/org.springframework.boot.autoconfigure.AutoConfiguration.imports`).
2. Each of those classes is annotated with **conditions**:

```java
@AutoConfiguration
@ConditionalOnClass(RedisOperations.class)              // is Lettuce/Jedis on the classpath?
@EnableConfigurationProperties(RedisProperties.class)
public class RedisAutoConfiguration {

    @Bean
    @ConditionalOnMissingBean(name = "redisTemplate")   // did the USER define one?
    public RedisTemplate<Object, Object> redisTemplate(RedisConnectionFactory cf) { ... }
}
```

3. At startup, Spring evaluates every condition and registers the beans that
   survive.

That's the whole mechanism. `@ConditionalOnMissingBean` is why **defining your
own bean silently replaces the default** — the single most useful thing to know
about Spring Boot.

And you can *see* the evaluation, which removes the mystery entirely:

```bash
java -jar pulse.jar --debug            # prints the full condition report
curl localhost:8080/actuator/conditions | jq
```

The lab makes you read that report. Once you've seen "Redis auto-config matched
because `RedisOperations` was on the classpath and no `redisTemplate` bean was
defined," Spring stops being magic permanently.

---

## Beans and injection — the 20% you need

```java
@Service                                   // "this is a bean; component-scan finds it"
public class MessageService {

    private final MessageRepository repo;  // final = required, immutable
    private final SessionRegistry registry;

    // No @Autowired needed: a single constructor is implicitly injected.
    public MessageService(MessageRepository repo, SessionRegistry registry) {
        this.repo = repo;
        this.registry = registry;
    }
}
```

**Always constructor injection.** Field injection (`@Autowired` on a field) is
legal, ubiquitous in old tutorials, and wrong: it hides dependencies, prevents
`final`, and makes the class untestable without a container.

Stereotypes are all `@Component` with different semantics:

| Annotation | Means | Extra behaviour |
|------------|-------|-----------------|
| `@Component` | Generic bean | — |
| `@Service` | Business logic | None (purely documentary) |
| `@Repository` | Data access | Translates persistence exceptions |
| `@RestController` | HTTP endpoint | `@Controller` + `@ResponseBody` |
| `@Configuration` | Bean definitions | `@Bean` methods; proxied for singleton semantics |

### Scopes, and the one that will bite you

Beans are **singletons by default** — one instance for the whole application.
That's why:

```java
@Service
public class BrokenCounter {
    private int count;                       // SHARED ACROSS ALL 50,000 CONNECTIONS
    public void increment() { count++; }     // and this is a data race
}
```

For a chat server this matters more than for a CRUD app: singleton beans are
touched by thousands of virtual threads simultaneously. **Every field on a
singleton bean must be immutable or thread-safe.** No exceptions.

---

## Configuration

```yaml
# application.yml
pulse:
  fanout:
    max-in-flight: 100
    dedup-window: 5m
  limits:
    max-room-size: 5000
```

```java
@ConfigurationProperties(prefix = "pulse")
@Validated
public record PulseProperties(
        @NotNull Fanout fanout,
        @NotNull Limits limits) {

    public record Fanout(@Positive int maxInFlight, @NotNull Duration dedupWindow) {}
    public record Limits(@Positive int maxRoomSize) {}
}
```

Typed, validated at startup, and a `record` so it's immutable. Compare to
`@Value("${pulse.fanout.max-in-flight}")` scattered across ten classes — which
fails at *runtime*, on the unlucky request, with a stack trace nobody reads.

**Profiles** switch config sets:
```yaml
spring:
  config:
    activate:
      on-profile: ha
pulse:
  redis:
    mode: cluster
```
```bash
java -jar pulse.jar --spring.profiles.active=ha
SPRING_PROFILES_ACTIVE=ha docker compose up
```

You'll use `dev`, `bench`, `ha`, and `prod` in this course. Note the env-var
form: **`PULSE_FANOUT_MAX_IN_FLIGHT` overrides `pulse.fanout.max-in-flight`** —
relaxed binding, and the reason 12-factor config works cleanly in containers.

---

## The three things that actually matter for a socket server

Everything above is generic Spring. These three are why this module exists.

### 1. Turn on virtual threads

```yaml
spring:
  threads:
    virtual:
      enabled: true
```

One line. It replaces Tomcat's request thread pool with a virtual-thread
executor, and makes `@Async` and Spring's task scheduler use them too.

**But read Module 01 again before you celebrate:** this removes the accidental
rate limiting the 200-thread pool was providing. If your service calls a
database with a 20-connection Hikari pool, you have just moved your queueing to
a place with no backpressure. The lab makes you add explicit limits.

**And it does not affect WebSocket message handling** — those flow through
Spring's `clientInboundChannel` executor, which is configured separately. Module
04 covers that. A lot of people set this flag and assume their whole app is
virtual-threaded; it isn't.

### 2. Actuator, from day one

```yaml
management:
  endpoints.web.exposure.include: health,info,metrics,prometheus,conditions,threaddump,heapdump,loggers
  endpoint.health.show-details: always
  metrics.tags.application: pulse
```

You will be staring at `/actuator/metrics` and `/actuator/prometheus` for the
rest of this course. Wiring it now costs nothing.

**Liveness vs readiness** — get this right now, it matters in Modules 18–19:

```yaml
management.endpoint.health.probes.enabled: true
```
- `/actuator/health/liveness` → "am I broken? restart me." Should almost never
  fail. A liveness probe that fails under load causes a **restart storm**, which
  is how a slow service becomes an outage.
- `/actuator/health/readiness` → "should I get traffic?" This is what your load
  balancer reads, and it's what goes false during graceful shutdown so the LB
  stops sending you new connections while you drain.

### 3. Graceful shutdown

```yaml
server:
  shutdown: graceful
spring:
  lifecycle:
    timeout-per-shutdown-phase: 45s
```

For a REST service this is a nicety. For a WebSocket server it's the difference
between a deploy nobody notices and 30,000 clients simultaneously reconnecting
(Module 18's thundering herd).

---

## Data access, briefly

You'll use JPA for room/user metadata and **plain JDBC for the message hot
path**. That split is deliberate and worth stating now:

```java
@Entity
public class Room {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    private String name;
    // ...
}

public interface RoomRepository extends JpaRepository<Room, Long> {
    Optional<Room> findByName(String name);          // derived query
}
```

That's great for rooms — a few thousand rows, rich object graph, low write rate.

For messages at 10,000 inserts/second, JPA's per-entity overhead (dirty
checking, the persistence context, `@Version` optimistic locking) is cost you
pay for features you don't use. Module 12 replaces it with `JdbcClient`:

```java
jdbcClient.sql("INSERT INTO messages (id, room_id, sender_id, client_id, body) VALUES (?,?,?,?,?)")
          .params(id, roomId, senderId, clientId, body)
          .update();
```

> **The principle:** use the ORM where the object graph earns its cost, and drop
> to SQL on the path that runs ten thousand times a second. "Always use the ORM"
> and "never use the ORM" are both positions held by people who haven't
> profiled.

**Flyway** handles migrations — versioned SQL files in
`src/main/resources/db/migration/V1__init.sql`, applied on startup, tracked in a
`flyway_schema_history` table. Module 13 leans on this heavily for partitioning.

---

## Why not Quarkus / Micronaut / Helidon / plain Netty?

Honest comparison, since this course is about defending choices:

- **Quarkus / Micronaut** do dependency injection at **build time** rather than
  runtime. Result: ~10× faster startup, much lower memory, native-image
  friendly. Genuinely better for serverless and for dense container packing.
  Spring's counter-argument is ecosystem depth and that Spring Boot 3 + AOT
  narrows the gap.
- **Plain Netty** is what Spring's WebSocket support runs on anyway (via
  Tomcat/Undertow/Reactor Netty). Writing directly against it gets you maximum
  control and maximum connections per gigabyte — at the cost of implementing
  STOMP, sessions, auth, metrics, and lifecycle yourself. Module 15's benchmark
  quantifies what that control is worth.
- **Vert.x** is a strong middle ground: event-loop based, less ceremony than
  Netty, good WebSocket support.

**Why Spring here:** the ecosystem for the *other* four problems (Redis, JPA,
Kafka, Security, Micrometer, Testcontainers) is unmatched, and this course
spends most of its time on those, not on the HTTP layer. If your constraint were
"maximum sockets per dollar" the answer might well be Vert.x or raw Netty — and
by Module 15 you'll have the numbers to make that call.

---

## What's next

The lab generates the Pulse project, wires virtual threads and Actuator, reads
the auto-configuration report, and adds a health endpoint you'll use for the
rest of the course.

See you in [`lab.md`](./lab.md).
