# Glossary

Plain-English definitions of every term used in this course. Skim it now; come
back whenever a word trips you up.

## Java basics

- **JVM (Java Virtual Machine)** — The runtime that executes compiled Java
  bytecode. "Write once, run anywhere" — the same `.class` files run on Linux,
  macOS, and Windows.
- **JDK (Java Development Kit)** — The toolchain you need to *build* Java apps:
  the compiler (`javac`), the runtime (`java`), and standard libraries. Module 00
  installs JDK 21.
- **JAR (Java ARchive)** — A zip file containing compiled classes and resources,
  packaged for distribution.
- **Class** — A blueprint for an object. Java is class-based: every piece of
  state and behavior lives inside a class.
- **Record** — A compact, immutable data class introduced in Java 16. We use
  them for DTOs in Spring controllers.
- **Interface** — A contract: a list of method signatures a class promises to
  implement. Spring uses interfaces heavily to decouple layers.
- **Lambda** — An anonymous function. Java 8 added them. `x -> x + 1` is a
  function that adds one.
- **Stream API** — A functional way to transform collections: `list.stream()
  .filter(...).map(...).toList()`. Used everywhere in modern Java + Spring.
- **Optional** — A container that may or may not hold a value. Replaces `null`
  checks in many places. `Optional.ofNullable(x).orElse(default)`.
- **Generics** — Type parameters on classes/methods. `List<String>` is a list
  of strings — the type is checked at compile time.
- **Checked exception** — An exception the compiler *forces* you to handle
  (`try`/`catch` or `throws`). Unchecked exceptions (like `NullPointerException`)
  don't require this.

## Spring & Spring Boot

- **Spring** — A huge ecosystem of libraries for building Java applications.
  "Spring Framework" is the core container; "Spring Boot" is the opinionated
  starting point.
- **Spring Boot** — A fast way to stand up a production-grade Spring app:
  embedded server, sensible defaults, starter dependencies, auto-configuration.
- **Starter** — A curated set of dependencies that work together. Adding
  `spring-boot-starter-web` brings in Spring MVC, Jackson, Tomcat, and
  Validation in one go.
- **Auto-configuration** — Spring Boot's "we'll guess what you need" magic.
  Detects libraries on the classpath and configures them with sensible defaults.
  Override any default with your own bean.
- **`@SpringBootApplication`** — The meta-annotation on your main class.
  Combines `@Configuration`, `@EnableAutoConfiguration`, and
  `@ComponentScan`.
- **IoC (Inversion of Control)** — A design principle: you don't `new` your
  dependencies — the framework hands them to you. The Hollywood Principle:
  "don't call us, we'll call you."
- **Bean** — An object managed by the Spring container. You declare beans via
  annotations (`@Component`, `@Service`, …) or `@Bean` methods; Spring handles
  creation, wiring, and lifecycle.
- **ApplicationContext** — The IoC container. Holds every bean, resolves
  dependencies, and fires lifecycle events.
- **Dependency Injection (DI)** — How Spring achieves IoC: the container
  *injects* a bean's collaborators (constructor args or setters) instead of the
  bean constructing them itself.
- **`@Autowired`** — Marks a constructor, field, or setter for injection.
  Prefer constructor injection — it's testable, immutable, and required.
- **Component scanning** — Spring's mechanism for finding beans: it scans
  packages under your main app class and registers everything annotated with
  `@Component` (or its specializations).

## Spring annotations you'll see

- **`@Component`** — Generic stereotype for any Spring-managed bean.
- **`@Service`** — Stereotype for the business-logic layer.
- **`@Repository`** — Stereotype for the data-access layer; also enables
  JPA exception translation.
- **`@Controller`** — Spring MVC controller returning views.
- **`@RestController`** — `@Controller` + `@ResponseBody` — returns JSON.
- **`@Configuration`** — A class containing `@Bean` methods.
- **`@Bean`** — A method that produces a Spring-managed object.
- **`@Value("${...}")`** — Inject a property value.
- **`@ConfigurationProperties`** — Bind a group of properties to a typed class.
- **`@Profile`** — Activate a bean only in specific environments.
- **`@Transactional`** — Wrap a method in a database transaction.

## Web / REST

- **HTTP** — The protocol browsers and APIs speak. Methods: `GET` (read),
  `POST` (create), `PUT` (replace), `PATCH` (partial update), `DELETE` (remove).
- **REST (Representational State Transfer)** — A style of HTTP API: resources
  at URLs, JSON bodies, standard status codes, stateless.
- **Spring MVC** — The web framework inside Spring. DispatcherServlet routes
  requests to controllers, serializes responses to JSON.
- **`@RequestMapping`** / `@GetMapping` / `@PostMapping` — Map HTTP methods to
  controller methods.
- **Path variable** — A value in the URL path: `/tasks/{id}` → method
  parameter annotated with `@PathVariable`.
- **Request body** — The JSON payload. `@RequestBody` binds it to a DTO.
- **DTO (Data Transfer Object)** — A simple object used at the API boundary.
  Decouples your wire format from your database entities.
- **ResponseEntity** — A wrapper around the response with status code, headers,
  and body.
- **Content negotiation** — The server choosing a response format (JSON, XML)
  based on the `Accept` header.
- **HATEOAS** — A REST style where responses include links to related
  resources. Not required, but Spring supports it.
- **Swagger / OpenAPI** — A specification for describing REST APIs. Tools
  generate docs, client SDKs, and server stubs from it.
- **Swagger UI** — A web page that renders OpenAPI as browsable documentation.
  `springdoc-openapi` provides it automatically.

## Data & JPA

- **JPA (Jakarta Persistence API)** — The standard ORM specification in Java.
  Defines `@Entity`, `EntityManager`, JPQL.
- **Hibernate** — The most popular JPA implementation. The actual ORM under the
  hood.
- **Spring Data JPA** — Spring's abstraction over JPA. You define a repository
  interface; Spring generates the implementation.
- **Entity** — A class mapped to a database table. Annotated with `@Entity`;
  fields map to columns.
- **Id** — The primary key. `@Id` + `@GeneratedValue(strategy =
  GenerationType.IDENTITY)` is the most common pattern.
- **Repository** — A Spring Data interface that gives you CRUD and query
  methods for free. `JpaRepository<T, ID>` is the workhorse.
- **Derived query** — A method name like `findByEmailAndActive` that Spring
  translates to a JPA query at startup.
- **`@Query`** — Write a JPQL or native SQL query directly on a repository
  method.
- **N+1 problem** — A performance bug where fetching N entities causes N extra
  queries for their relationships. Fixed with `JOIN FETCH` or `@EntityGraph`.
- **Lazy vs eager loading** — Lazy: relationships aren't loaded until you
  access them. Eager: they're loaded with the parent. Lazy is the default and
  usually what you want.
- **Flyway** — A schema migration tool. SQL files in `db/migration` are
  versioned and applied in order — your schema's version control.
- **`@Transactional`** — Marks a method (or class) as transactional. All DB
  work inside runs in one transaction; any exception rolls it back.
- **Connection pool** — A cache of database connections. HikariCP is Spring
  Boot's default and is fast.

## Security

- **Spring Security** — The de-facto security framework. Filter chain,
  authentication (who are you?), authorization (what can you do?).
- **Authentication** — Verifying identity. Username + password, JWT, OAuth2,
  API key, etc.
- **Authorization** — Determining what an authenticated user is allowed to do.
- **SecurityFilterChain** — The chain of HTTP filters that handles security.
  The modern (post-`WebSecurityConfigurerAdapter`) way to configure Spring
  Security.
- **JWT (JSON Web Token)** — A signed, self-contained token. The server signs
  claims (`sub`, `exp`, `roles`) and the client sends it on every request.
  Stateless — no server session.
- **Access token** — Short-lived JWT used to authenticate API calls.
- **Refresh token** — Longer-lived token used only to mint new access tokens.
- **BCrypt** — A password hashing algorithm. Spring Security's default.
- **`PasswordEncoder`** — Spring's interface for hashing and verifying
  passwords. `BCryptPasswordEncoder` is the implementation you wire in.
- **CSRF (Cross-Site Request Forgery)** — An attack where a malicious site
  submits a request using your cookies. Disabled by default in JWT-only APIs
  (since you don't use cookies).
- **CORS (Cross-Origin Resource Sharing)** — Browser mechanism for allowing
  your API to be called from a frontend on a different domain. Configured in
  Spring Security with `cors()`.
- **OAuth2 Resource Server** — Spring's built-in JWT validation. Point it at a
  JWKS URL and it validates every request's bearer token.

## Caching & messaging

- **Cache** — A fast in-memory store (Redis) for repeated reads. `@Cacheable`
  results, `@CacheEvict` on write, `@CachePut` to update.
- **TTL (time to live)** — An expiry on a cache key. After the TTL, the key is
  gone and the next read hits the database.
- **Cache aside** — The common pattern: app reads from cache, on miss reads
  from DB and writes to cache.
- **Kafka** — A distributed event log (a "message broker"). Producers write
  events to topics; consumers subscribe to topics and process events at their
  own pace.
- **Topic** — A named stream of events in Kafka. Producers write to it;
  consumers read from it.
- **Partition** — A topic is split into ordered partitions. Each partition is
  processed by one consumer in a group at a time, in order.
- **Consumer group** — A set of consumers that share the work of a topic.
  Each partition is owned by one consumer in the group.
- **Dead Letter Queue (DLQ)** — A topic where messages go after exhausting
  retries. You inspect and replay them manually.
- **Idempotency** — A producer sending the same message twice should not
  cause duplicate work. Often implemented with a message key + dedup table.

## Observability

- **Actuator** — Spring Boot's built-in ops endpoints: `/actuator/health`,
  `/actuator/info`, `/actuator/metrics`, `/actuator/prometheus`.
- **Health check** — A liveness/readiness probe: "is this instance OK to
  receive traffic?"
- **Liveness probe** — "Is the process alive?" Failure → restart the pod.
- **Readiness probe** — "Is the process ready to serve?" Failure → remove from
  the load balancer.
- **Metrics** — Numeric time series: counters (requests served), gauges
  (queue depth), histograms (request duration).
- **Prometheus** — An open-source metrics collection system. Spring Boot
  exposes metrics in Prometheus format on `/actuator/prometheus`.
- **Structured logging** — Logs as JSON (or key/value pairs) instead of plain
  text. Easy to parse, query, and aggregate.
- **Logback** — Spring Boot's default logging library. Configured in
  `logback-spring.xml`.
- **Correlation ID / trace ID** — A unique ID attached to a request and
  passed through every log line and downstream call, so you can follow it.

## Build, test, deploy

- **Maven** — A build tool and dependency manager. `pom.xml` declares
  dependencies; `mvn package` builds a JAR; `mvn test` runs tests.
- **Gradle** — A Groovy/Kotlin DSL build tool. Faster than Maven for big
  builds, but Maven is more common in Spring Boot tutorials.
- **JUnit 5** — The standard Java testing framework. Tests are methods on a
  class annotated with `@Test`.
- **Mockito** — A mocking library. `when(repo.findById(1)).thenReturn(task)`.
- **AssertJ** — A fluent assertion library: `assertThat(task.getTitle()).isEqualTo("hi")`.
- **`@SpringBootTest`** — Loads the full application context for an
  integration test. Slow but realistic.
- **`@WebMvcTest`** — Loads only the web layer (controllers, filters) for fast
  slice tests. No DB, no services.
- **`@DataJpaTest`** — Loads only JPA + repositories against an in-memory or
  Testcontainer DB. Fast data-layer tests.
- **Testcontainers** — A library that spins up real Docker containers
  (Postgres, Redis, Kafka) for tests. You get a real DB without polluting your
  machine.
- **Multi-stage Dockerfile** — A Dockerfile with a `builder` stage (compiles
  the JAR with full JDK + Maven) and a slim `runtime` stage (JRE + the JAR
  only). Produces small, secure images.
- **Docker Compose** — A declarative way to run multi-container apps locally.
  `docker compose up -d` brings up your service, its DB, its cache, etc.
- **12-factor config** — Read configuration (DB URL, secrets, feature flags)
  from environment variables. The same JAR runs in dev, staging, and prod —
  only the env changes.
