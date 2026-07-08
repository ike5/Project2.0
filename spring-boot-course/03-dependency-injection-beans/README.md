# Module 03 — Dependency Injection & Beans

**Goal:** understand the IoC container — Spring's core mechanism for managing
objects, wiring them together, and giving you a place to put cross-cutting
configuration. By the end you'll be fluent in the annotation vocabulary every
later module uses.

⏱️ ~2.5 hours · 🎯 Prereq: Module 02 complete (project runs, `HelloController` works).

> The IoC container is what makes Spring "Spring." Master it now and the
> annotations in later modules (`@Service`, `@Repository`, `@Configuration`,
> `@Transactional`) are just names attached to behaviors you already
> understand.

---

## 1. The problem Spring solves

Without a framework, your code is full of `new`:

```java
public class TaskService {
    private final TaskRepository repo = new TaskRepository();   // hard-coded
    private final EmailSender    mail = new SmtpEmailSender();   // hard-coded
    public Task create(String title) { ... }
}
```

Three problems:

1. **Hard to test** — you can't substitute a fake `TaskRepository` in a test.
2. **Hard to change** — swapping to `SesEmailSender` means editing source.
3. **Hidden coupling** — every collaborator is constructed in the consumer.

The fix: **don't construct collaborators — declare them, and let the framework
hand them to you.** That's Inversion of Control (IoC) and Dependency
Injection (DI).

```java
@Service
public class TaskService {
    private final TaskRepository repo;   // injected, not constructed
    private final EmailSender    mail;   // injected, not constructed

    public TaskService(TaskRepository repo, EmailSender mail) {  // constructor
        this.repo = repo; this.mail = mail;
    }
    // ...
}
```

---

## 2. The IoC container — the `ApplicationContext`

When `SpringApplication.run(...)` starts, it builds an **`ApplicationContext`**:
a registry of objects ("beans") and the wiring between them.

The container is responsible for:

- **Creating** beans (calling constructors).
- **Wiring** beans into each other (resolving dependencies).
- **Managing** their lifecycle (`@PostConstruct`, `@PreDestroy`, `InitializingBean`).
- **Scoping** them (singleton, request, session, prototype, …).
- **Proxies** for cross-cutting concerns (transactions, security, caching) —
  Module 06 and 07.

You almost never interact with the context directly. You declare beans, and
the container does the rest.

---

## 3. How a bean gets into the container

Three ways:

### 3.1 Component scanning (the common case)

Annotate a class; Spring finds it on the classpath and instantiates it.

```java
@Component                                    // generic stereotype
@Service                                      // business logic
@Repository                                   // data access (also enables JPA exception translation)
@Controller  /  @RestController               // web layer
@Configuration                                // contains @Bean methods
```

`@Service`, `@Repository`, `@Controller` are all `@Component` under the hood.
They exist to **express intent** — a service-layer bean should be marked
`@Service` so a reader (and tooling) knows where it lives.

Component scanning starts at the package of `@SpringBootApplication` and
goes deeper. If you put `TaskforgeApplication` in `com.taskforge`, every
bean must be in `com.taskforge` or a sub-package.

### 3.2 `@Bean` methods (the precise case)

When you need to construct a bean whose class you don't own (a third-party
library), declare a `@Bean` method in a `@Configuration` class:

```java
@Configuration
public class HttpClientConfig {

    @Bean
    public RestClient restClient() {
        return RestClient.builder()
            .baseUrl("https://api.example.com")
            .build();
    }
}
```

The method's return type is the bean's type; the method name is its id.

### 3.3 Explicit registration (rare)

```java
@SpringBootApplication
public class TaskforgeApplication {
    public static void main(String[] args) {
        SpringApplication.run(TaskforgeApplication.class, args);
    }

    @Bean
    public Clock systemClock() { return Clock.systemUTC(); }
}
```

> **Rule of thumb:** own the class → annotate it. Don't own the class → declare
> a `@Bean` method. You'll mostly do the former in this course.

---

## 4. Constructor injection — the only kind you should use

Spring supports three injection styles:

```java
// ✅ Constructor injection — the modern recommendation
@Service
public class TaskService {
    private final TaskRepository repo;
    private final EmailSender    mail;
    public TaskService(TaskRepository repo, EmailSender mail) {
        this.repo = repo; this.mail = mail;
    }
}

// ⚠️ Field injection — discouraged
@Service
public class TaskService {
    @Autowired private TaskRepository repo;       // hidden dependency
    @Autowired private EmailSender    mail;       // can't make final
}

// ⚠️ Setter injection — for optional dependencies only
@Service
public class TaskService {
    private TaskRepository repo;
    @Autowired(required = false) public void setRepo(TaskRepository r) { this.repo = r; }
}
```

**Why constructor injection wins:**

1. **Immutability** — fields are `final`.
2. **Testability** — you can call the constructor directly with mocks; no
   need for a Spring context in unit tests.
3. **Required dependencies are obvious** — you can't construct without them.
4. **No reflection** — the JVM verifies the constructor at compile time.

> **Spring 4.3+** auto-wires any class with a single constructor; you don't
> need `@Autowired` on it. Use `@Autowired` only when you have multiple
> constructors and need to disambiguate.

---

## 5. Bean scopes

By default every bean is a **singleton** — one instance for the whole
context. Spring also defines:

| Scope | When to use it |
|-------|----------------|
| `singleton` (default) | Stateless services, repositories, config |
| `prototype` | A new instance every time it's requested |
| `request` | One per HTTP request (web scopes) |
| `session` | One per HTTP session |
| `application` | One per `ServletContext` |

```java
@Component
@Scope("prototype")
public class RequestContext { ... }
```

> **99% of the beans you'll write are singletons.** Scopes are mostly for web-
> stateful concerns, and even then Spring Security, `@SessionScope`, and JWT
> tokens usually remove the need for them.

---

## 6. Bean lifecycle

The container calls these hooks on every bean (when present):

```
new           ← constructor
   ↓
@PostConstruct  ← "this is ready, do init work"
   ↓
in use
   ↓
@PreDestroy    ← "about to be destroyed, clean up"
```

```java
@Component
public class CacheWarmer {
    @PostConstruct
    void warm() { /* preload caches */ }

    @PreDestroy
    void flush() { /* persist outstanding writes */ }
}
```

> **Spring Boot does this for you too:** the embedded server is started by
> a `SmartLifecycle` bean that fires during context refresh.

---

## 7. Profiles — beans that exist only in some environments

A **profile** is a named environment (e.g. `dev`, `prod`). You can mark
beans to be created only in specific profiles:

```java
@Configuration
@Profile("dev")
public class DevConfig {
    @Bean
    public CommandLineRunner seedData(TaskRepository repo) {
        return args -> { /* load fake data */ };
    }
}
```

Activate a profile in `application.yml`:
```yaml
spring:
  profiles:
    active: dev
```

…or on the command line:
```bash
java -jar app.jar --spring.profiles.active=prod
```

Module 09 covers this in depth.

---

## 8. `@ConfigurationProperties` — typed configuration

`@Value("${...}")` is fine for one-off properties. For groups, bind them to
a typed class:

```yaml
# application.yml
taskforge:
  pagination:
    default-page-size: 20
    max-page-size: 100
  features:
    email-notifications: true
```

```java
@ConfigurationProperties(prefix = "taskforge")
public record TaskforgeProperties(Pagination pagination, Features features) {
    public record Pagination(int defaultPageSize, int maxPageSize) {}
    public record Features(boolean emailNotifications) {}
}
```

Enable scanning with `@ConfigurationPropertiesScan` on the main class:
```java
@SpringBootApplication
@ConfigurationPropertiesScan
public class TaskforgeApplication { ... }
```

Now you can `@Autowired` `TaskforgeProperties` anywhere and read typed config.

> **Why this matters:** it catches typos at startup. `@Value("${taskforge.pagaination...}")`
> fails silently (empty string); `@ConfigurationProperties` fails loudly with
> a clear error pointing at the missing property.

---

## 9. Conditional beans — `@ConditionalOn...`

Sometimes a bean should only exist if a class, property, or bean is present.
Spring Boot's `@ConditionalOn*` family is what auto-configuration is built on:

```java
@Bean
@ConditionalOnProperty(name = "taskforge.email.enabled", havingValue = "true")
public EmailSender emailSender() { return new SmtpEmailSender(); }
```

You'll see these annotations when you read the auto-config report in Module 02.

---

## 10. Testing beans — the `ApplicationContext` for tests

Two main ways to test beans in a Spring context:

```java
@SpringBootTest                          // loads the full context
class TaskServiceIT { ... }

@ExtendWith(MockitoExtension.class)     // no Spring at all — just Mockito
class TaskServiceTest {
    @Mock TaskRepository repo;
    @InjectMocks TaskService service;
}
```

**Use unit tests with Mockito** for service logic; use `@SpringBootTest` only
when you need the full context (e.g. testing wiring itself). Module 08 goes
deep on testing.

---

## 11. Common pitfalls

| Symptom | Cause |
|---------|-------|
| `NoSuchBeanDefinitionException` | Forgot the annotation, or class is in a package *above* the main class |
| `NoUniqueBeanDefinitionException` | Two beans of the same type; qualify with `@Qualifier` or `@Primary` |
| `BeanCreationException: ... circular reference` | Bean A needs B needs A; refactor |
| Field is `null` in a unit test | You forgot `@InjectMocks` or the constructor |
| `LazyInitializationException` | Tried to access a session-scoped bean outside a session |

Most of these have a single fix: **add a constructor and let Spring inject.**

---

## 12. Do the lab

Build a small service layer for `taskforge`: a `TaskService` with a fake
`TaskRepository`, wired with constructor injection, and a `CommandLineRunner`
that runs at startup. Add a `@ConfigurationProperties` class for the
app's settings.

👉 **[lab.md](./lab.md)**

Then test yourself: 👉 **[challenge.md](./challenge.md)**

---

## Key terms (see [GLOSSARY](../GLOSSARY.md))

IoC · DI · bean · `ApplicationContext` · component scanning · `@Component` / `@Service` / `@Repository` / `@Controller` / `@Configuration` · `@Bean` · constructor injection · scope · lifecycle · `@PostConstruct` · `@PreDestroy` · profile · `@ConfigurationProperties`

**Next →** [Module 04: REST APIs with Spring MVC](../04-rest-apis-spring-mvc/)
