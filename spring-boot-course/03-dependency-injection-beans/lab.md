# Lab 03 — Wire a Service Layer with Constructor Injection

**You'll:** build the **service layer** of `taskforge` from scratch — a
`TaskService` and an in-memory `TaskRepository` — and prove that Spring wires
them together. You'll also add a `@ConfigurationProperties` class for the
app's settings.

⏱️ ~50 min. Run from `spring-boot-course/apps/taskforge`.

---

## Part A — Define the `Task` record (and a `TaskRepository` interface)

Create `src/main/java/com/taskforge/task/Task.java`:
```java
package com.taskforge.task;
import java.time.Instant;

public record Task(Long id, String title, String description, boolean done, Instant createdAt) {}
```

> We use a record for now. In Module 05, when we persist with JPA, this
> becomes a `@Entity` class (a record *can* be an entity in Hibernate 6.2+,
> but classic JPA classes are still the more common pattern you'll see).

Create `src/main/java/com/taskforge/task/TaskRepository.java`:
```java
package com.taskforge.task;
import java.util.List;
import java.util.Optional;

public interface TaskRepository {
    Task save(Task task);
    Optional<Task> findById(Long id);
    List<Task> findAll();
    void deleteById(Long id);
}
```

> The interface is the **boundary** between the service and the data layer.
> Module 05 implements it with Spring Data; Module 03 implements it with
> an in-memory list to keep this lab dependency-free.

---

## Part B — The in-memory implementation as a Spring bean

Create `src/main/java/com/taskforge/task/InMemoryTaskRepository.java`:
```java
package com.taskforge.task;

import org.springframework.stereotype.Repository;

import java.util.*;
import java.util.concurrent.atomic.AtomicLong;

@Repository
public class InMemoryTaskRepository implements TaskRepository {

    private final Map<Long, Task> byId = new LinkedHashMap<>();
    private final AtomicLong nextId = new AtomicLong(1);

    @Override
    public Task save(Task task) {
        Long id = (task.id() == null) ? nextId.getAndIncrement() : task.id();
        Task saved = new Task(id, task.title(), task.description(), task.done(), task.createdAt());
        byId.put(id, saved);
        return saved;
    }

    @Override
    public Optional<Task> findById(Long id) {
        return Optional.ofNullable(byId.get(id));
    }

    @Override
    public List<Task> findAll() {
        return List.copyOf(byId.values());
    }

    @Override
    public void deleteById(Long id) {
        byId.remove(id);
    }
}
```

✅ **Checkpoint:** the class is annotated `@Repository`. When the app starts,
Spring will instantiate it (calling the no-arg constructor) and register it
as a bean of type `TaskRepository`.

---

## Part C — The service with constructor injection

Create `src/main/java/com/taskforge/task/TaskService.java`:
```java
package com.taskforge.task;

import org.springframework.stereotype.Service;

import java.time.Clock;
import java.time.Instant;
import java.util.List;
import java.util.NoSuchElementException;

@Service
public class TaskService {

    private final TaskRepository repo;
    private final Clock clock;

    public TaskService(TaskRepository repo, Clock clock) {
        this.repo = repo;
        this.clock = clock;
    }

    public Task create(String title, String description) {
        if (title == null || title.isBlank())
            throw new IllegalArgumentException("title is required");
        return repo.save(new Task(null, title.trim(), description, false, Instant.now(clock)));
    }

    public List<Task> list() { return repo.findAll(); }

    public Task get(Long id) {
        return repo.findById(id).orElseThrow(() -> new NoSuchElementException("no task " + id));
    }

    public Task markDone(Long id) {
        Task t = get(id);
        return repo.save(new Task(t.id(), t.title(), t.description(), true, t.createdAt()));
    }

    public void delete(Long id) { repo.deleteById(id); }
}
```

> **Why inject `Clock`?** A `Clock` lets tests pin time. You don't want your
> unit tests asserting "created at 2024-01-01" to flake because the clock
> moved. (Module 08 does this for real.)

---

## Part D — Provide a `Clock` bean

Create `src/main/java/com/taskforge/config/ClockConfig.java`:
```java
package com.taskforge.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import java.time.Clock;

@Configuration
public class ClockConfig {

    @Bean
    public Clock clock() {
        return Clock.systemUTC();
    }
}
```

A `@Bean` method is a recipe the container follows to make a bean. The
returned `Clock` is what `TaskService` receives.

---

## Part E — Prove wiring with a `CommandLineRunner`

Create `src/main/java/com/taskforge/task/TaskForgeRunner.java`:
```java
package com.taskforge.task;

import org.springframework.boot.CommandLineRunner;
import org.springframework.stereotype.Component;

@Component
public class TaskForgeRunner implements CommandLineRunner {

    private final TaskService service;

    public TaskForgeRunner(TaskService service) {
        this.service = service;
    }

    @Override
    public void run(String... args) {
        service.create("Buy milk", "2% organic");
        service.create("Fix login bug", "null check on email");
        service.list().forEach(t -> System.out.println("seeded: " + t));
    }
}
```

`CommandLineRunner` is a Spring Boot interface — the container calls `run(...)`
on every `CommandLineRunner` bean **after** startup completes and **before**
`SpringApplication.run(...)` returns. Perfect for "do this once at boot."

Run it:
```bash
mvn -q spring-boot:run
```

You should see (before "Started TaskforgeApplication"):
```
seeded: Task[1, Buy milk, 2% organic, false, ...]
seeded: Task[2, Fix login bug, null check on email, false, ...]
```

✅ **Checkpoint:** Spring created `InMemoryTaskRepository`, `Clock`, and
`TaskService`, wired them together, and your `TaskForgeRunner` got the
fully-wired `TaskService` injected.

---

## Part F — Add typed config with `@ConfigurationProperties`

Create `src/main/java/com/taskforge/config/TaskforgeProperties.java`:
```java
package com.taskforge.config;

import org.springframework.boot.context.properties.ConfigurationProperties;

@ConfigurationProperties(prefix = "taskforge")
public record TaskforgeProperties(Pagination pagination) {
    public TaskforgeProperties {
        if (pagination == null) pagination = new Pagination(20, 100);
    }
    public record Pagination(int defaultPageSize, int maxPageSize) {}
}
```

Enable scanning on the main class:
```java
@SpringBootApplication
@ConfigurationPropertiesScan
public class TaskforgeApplication { ... }
```

Add to `application.yml`:
```yaml
taskforge:
  pagination:
    default-page-size: 25
    max-page-size: 200
```

Inject it into `TaskService`:
```java
public TaskService(TaskRepository repo, Clock clock, TaskforgeProperties props) {
    this.repo = repo;
    this.clock = clock;
    System.out.println("default page size = " + props.pagination().defaultPageSize());
}
```

Run again — you'll see `default page size = 25` in the logs.

✅ **Checkpoint:** Spring bound `taskforge.pagination.*` from `application.yml`
into a record. You can `@Autowired` it anywhere.

---

## What you learned

- The IoC container creates beans, wires them, and manages their lifecycle.
- Component scanning finds `@Component` / `@Service` / `@Repository` /
  `@Controller` classes under your main class's package.
- `@Bean` methods are how you register objects you don't own.
- Constructor injection is the only kind you should use.
- `@ConfigurationProperties` binds a YAML tree to a typed class — typos
  fail at startup, not at runtime.

➡️ Now try the **[challenge](./challenge.md)**, then move to
[Module 04](../04-rest-apis-spring-mvc/).
