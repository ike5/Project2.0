# Spring Boot: From Zero to Production-Ready ☕🚀

A hands-on, local-first course that takes you from **an empty repo** to a
**production-ready, containerized, observable web application** built with Spring
Boot 3, Java 21, PostgreSQL, Redis, Kafka, and the full set of dependencies you
need to ship a real backend.

> **Who this is for:** You can write some code in *any* language and you're
> comfortable in a terminal. You want to build a *real* product — REST APIs,
> persistence, auth, async messaging, file uploads, observability, Docker — and
> learn the production patterns (12-factor config, layered architecture, JWT
> auth, caching, integration testing) that hobby tutorials skip.

> **Web only.** This course builds the **backend**. A frontend (React/Angular/Vue)
> is out of scope — but the API you build here is exactly what any SPA would consume.

---

## Why this course is different

- **Learn by building one real app.** Every module grows the *same* task tracker
  — `apps/taskforge` — from a `HelloController` to a multi-module, JWT-secured,
  Redis-cached, Kafka-backed, observability-instrumented service. No throwaway toys.
- **The full dependency story.** Most courses show you `spring-boot-starter-web`
  and stop. This course walks through the **whole web-app dependency graph**:
  web, validation, security, data JPA, security JWT, OAuth2 resource server, mail,
  Redis, Kafka, OpenAPI, Actuator, Micrometer, Testcontainers, Docker.
- **Production patterns, not demos.** Layered architecture (controller → service
  → repository), DTOs vs entities, global exception handling, structured logging
  with Logback, externalized configuration with profiles, Flyway migrations,
  health checks, Prometheus metrics — what real Spring Boot services look like.
- **Run it on your machine.** Postgres, Redis, Kafka, and MailHog all run in
  Docker via `docker compose`. You build, run, test, and break the app yourself.

---

## Prerequisites

- A Mac or Linux machine with **~8 GB RAM free** and ~15 GB disk.
- **Java 21 (LTS)** and **Maven 3.9+** (or Gradle 8+). Module 00 installs these.
- **Docker** and **Docker Compose** for the data services. Module 00 confirms them.
- Comfort with a terminal, basic Git, and HTTP. You do **not** need prior Java or
  Spring experience — each is introduced from the ground up.
- **No prior Java knowledge needed.** Module 01 is a focused Java fast-track that
  gets you productive in the language features Spring actually uses.

---

## The learning path

Work through the modules **in order** — each one adds to the app you're building.

| # | Module | You'll build / learn | Est. time |
|---|--------|----------------------|-----------|
| 00 | [Setup & Orientation](./00-setup/) | Install JDK, Maven, IDE; start Postgres/Redis/Kafka/MailHog in Docker | 1 h |
| 01 | [Java Fast-Track for Spring](./01-java-fast-track/) | Types, records, streams, lambdas, exceptions, generics — the Java you actually need | 2.5 h |
| 02 | [Spring Boot Fundamentals](./02-spring-boot-fundamentals/) | `start.spring.io`, project structure, starters, auto-configuration, the main app | 2 h |
| 03 | [Dependency Injection & Beans](./03-dependency-injection-beans/) | The IoC container, `@Component`/`@Service`/`@Repository`, constructor injection, bean scopes | 2.5 h |
| 04 | [REST APIs with Spring MVC](./04-rest-apis-spring-mvc/) | `@RestController`, `@RequestMapping`, DTOs, response status, content negotiation | 3 h |
| 05 | [Data Access with Spring Data JPA](./05-data-jpa-postgres/) | Entities, repositories, relationships, Flyway migrations, query methods | 3.5 h |
| 06 | [Validation & Exception Handling](./06-validation-exceptions/) | Bean Validation, `@ControllerAdvice`, RFC 7807 problem details, error contracts | 2 h |
| 07 | [Security with Spring Security & JWT](./07-security-jwt/) | SecurityFilterChain, authentication/authorization, JWT issuance & validation | 3.5 h |
| 08 | [Testing (Unit, Slice, Integration)](./08-testing/) | JUnit 5, Mockito, `@WebMvcTest`, `@DataJpaTest`, Testcontainers, coverage | 3 h |
| 09 | [Logging, Configuration & Profiles](./09-logging-config-profiles/) | Logback, structured JSON logs, `@ConfigurationProperties`, dev/prod profiles | 2 h |
| 10 | [Caching with Redis & Spring Cache](./10-caching-redis/) | `@Cacheable`/`@CacheEvict`, Redis as cache backend, TTL, cache aside pattern | 2 h |
| 11 | [Async Messaging with Kafka](./11-async-messaging/) | `spring-kafka`, producers/consumers, topics, error handling, dead letter queues | 3 h |
| 12 | [Email & File Uploads](./12-email-uploads/) | `spring-boot-starter-mail` (MailHog), MinIO/S3 presigned URLs for uploads | 2.5 h |
| 13 | [OpenAPI / Swagger](./13-openapi-docs/) | `springdoc-openapi`, Swagger UI, documenting endpoints, generating clients | 1.5 h |
| 14 | [Containerizing with Docker](./14-docker-compose/) | Multi-stage Dockerfile, `docker-compose` for the whole stack, images that actually run | 2.5 h |
| 15 | [Observability with Actuator](./15-observability/) | Health checks, Prometheus metrics, custom metrics, distributed tracing basics | 2 h |
| 16 | [Capstone — Production-Ready App](./16-capstone/) | Wire everything together: tested, containerized, observable, secure | 4+ h |

**Total: a realistic ~45 hours of focused, hands-on work.** Take it at your own pace.

---

## How each module is structured

```
NN-topic/
├── README.md      ← Concepts in plain language. Read this first.
├── lab.md         ← Step-by-step guided build with expected output. Do this second.
├── code/          ← Reference files the lab adds to the app (when applicable).
├── challenge.md   ← An unguided task to prove you understood it. Do this third.
└── solutions/     ← Reference answers — peek only after you've tried.
```

**The rhythm for every module:** read `README.md` → follow `lab.md` hands-on →
attempt `challenge.md` solo → check `solutions/`.

---

## The app you're building

One app under [`apps/taskforge/`](./apps/taskforge/) grows with you across the
whole course. It starts as "a `Task` entity with CRUD endpoints" and ends as a
JWT-secured, Redis-cached, Kafka-aware, observability-instrumented service
ready to deploy.

By the capstone you can:

- Hit a versioned, documented REST API.
- Sign up, log in, and get a JWT.
- Create / list / update / delete tasks scoped to your user.
- Receive an email (via MailHog) when a task is assigned to you.
- Publish "task created" events to Kafka and consume them in a notification worker.
- Upload attachments to MinIO via presigned URLs.
- See Prometheus metrics, health checks, and structured logs.

---

## The dependency story (what the course covers)

Spring Boot's strength is its **starter** model — one dependency pulls in a
coherent set of libraries, pre-configured to work together. This course walks
through every starter you need to build a real web app:

| Starter | What it gives you | Module |
|---------|------------------|--------|
| `spring-boot-starter-web` | Spring MVC, embedded Tomcat, Jackson JSON | 02, 04 |
| `spring-boot-starter-validation` | Bean Validation (Hibernate Validator) | 06 |
| `spring-boot-starter-security` | Authentication, authorization, filter chain | 07 |
| `spring-boot-starter-data-jpa` | JPA, Hibernate, Spring Data repositories | 05 |
| `spring-boot-starter-data-redis` | Redis client, `RedisTemplate`, cache integration | 10 |
| `spring-boot-starter-cache` | `@Cacheable` abstraction over Redis | 10 |
| `spring-kafka` | Producer/consumer APIs, listener container | 11 |
| `spring-boot-starter-mail` | JavaMailSender for transactional email | 12 |
| `spring-boot-starter-actuator` | Health, info, metrics, Prometheus endpoint | 15 |
| `spring-boot-starter-test` | JUnit 5, Mockito, AssertJ, Spring Test | 08 |
| `springdoc-openapi-starter-webmvc-ui` | Swagger UI and OpenAPI spec | 13 |
| `flyway-core` + `flyway-database-postgresql` | Versioned SQL migrations | 05 |
| `io.minio:minio-java` | S3-compatible object storage client | 12 |
| `org.testcontainers:{postgresql,redis,kafka}` | Throwaway containers in tests | 08 |
| `io.micrometer:micrometer-registry-prometheus` | Prometheus metrics format | 15 |

You'll understand **what each one does, why you'd add it, and what the
trade-offs are** — not just the `pom.xml` line.

---

## Reference material (keep these open)

- **[cheatsheets/spring-boot.md](./cheatsheets/spring-boot.md)** — annotations, app structure, configuration.
- **[cheatsheets/jpa-hibernate.md](./cheatsheets/jpa-hibernate.md)** — entities, repositories, query methods.
- **[cheatsheets/security-jwt.md](./cheatsheets/security-jwt.md)** — SecurityFilterChain, JWT issuance/validation.
- **[cheatsheets/maven.md](./cheatsheets/maven.md)** — `pom.xml`, goals, plugins, dependency management.
- **[cheatsheets/docker-compose.md](./cheatsheets/docker-compose.md)** — multi-service local dev, healthchecks.
- **[GLOSSARY.md](./GLOSSARY.md)** — every term defined in plain English.
- **[VERIFY.md](./VERIFY.md)** — end-to-end smoke test to confirm your stack works.

---

## Quick start

```bash
# 1. Install the toolchain (Module 00 explains each tool)
cd spring-boot-course/00-setup
cat README.md

# 2. Bring up Postgres + Redis + Kafka + MailHog for local dev
docker compose -f compose.dev.yml up -d

# 3. Start learning
cd ../01-java-fast-track && cat README.md
```

---

Ready? **→ [Start with Module 00: Setup & Orientation](./00-setup/)**
