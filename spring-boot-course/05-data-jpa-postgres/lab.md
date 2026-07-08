# Lab 05 — Persist to Postgres with Spring Data JPA

**You'll:** add JPA + Flyway + Postgres, define a `Task` entity, swap out the
in-memory repository, and prove tasks survive an app restart.

⏱️ ~60 min. Run from `spring-boot-course/apps/taskforge`. The Postgres
container from Module 00 must be up.

---

## Part A — Add the dependencies

Add to `pom.xml` inside `<dependencies>`:
```xml
<dependency>
  <groupId>org.springframework.boot</groupId>
  <artifactId>spring-boot-starter-data-jpa</artifactId>
</dependency>
<dependency>
  <groupId>org.postgresql</groupId>
  <artifactId>postgresql</artifactId>
  <scope>runtime</scope>
</dependency>
<dependency>
  <groupId>org.flywaydb</groupId>
  <artifactId>flyway-core</artifactId>
</dependency>
<dependency>
  <groupId>org.flywaydb</groupId>
  <artifactId>flyway-database-postgresql</artifactId>
</dependency>
```

Reload Maven: the IDE picks this up automatically; on the CLI:
```bash
mvn -q dependency:resolve
```

---

## Part B — Configure the datasource

Replace `application.yml`:
```yaml
spring:
  application:
    name: taskforge
  datasource:
    url: jdbc:postgresql://localhost:5432/taskforge
    username: taskforge
    password: taskforge
  jpa:
    hibernate:
      ddl-auto: validate
    open-in-view: false
    properties:
      hibernate.format_sql: true
      hibernate.jdbc.time_zone: UTC
  flyway:
    enabled: true
    locations: classpath:db/migration

server:
  port: 8080

management:
  endpoints:
    web:
      exposure:
        include: health,info
```

---

## Part C — First Flyway migration

Create the migration directory and the first file:
```bash
mkdir -p src/main/resources/db/migration
```

`src/main/resources/db/migration/V1__create_task_table.sql`:
```sql
CREATE TABLE task (
    id          BIGSERIAL    PRIMARY KEY,
    title       VARCHAR(200) NOT NULL,
    description VARCHAR(2000),
    done        BOOLEAN      NOT NULL DEFAULT FALSE,
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT now()
);

CREATE INDEX idx_task_done ON task(done);
```

> **Why `TIMESTAMPTZ` and not `TIMESTAMP`?** `TIMESTAMPTZ` stores the instant;
> `TIMESTAMP` stores a wall-clock value with no zone awareness. Always use
> `TIMESTAMPTZ` for new code.

---

## Part D — The `Task` entity

Replace `src/main/java/com/taskforge/task/Task.java` (the old record) with
the classic entity version:

`src/main/java/com/taskforge/task/Task.java`:
```java
package com.taskforge.task;

import jakarta.persistence.*;
import java.time.Instant;

@Entity
@Table(name = "task")
public class Task {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false, length = 200)
    private String title;

    @Column(length = 2000)
    private String description;

    @Column(nullable = false)
    private boolean done;

    @Column(name = "created_at", nullable = false, updatable = false)
    private Instant createdAt;

    protected Task() { }

    public Task(String title, String description) {
        this.title = title;
        this.description = description;
        this.done = false;
        this.createdAt = Instant.now();
    }

    public Long getId() { return id; }
    public String getTitle() { return title; }
    public String getDescription() { return description; }
    public boolean isDone() { return done; }
    public Instant getCreatedAt() { return createdAt; }

    public void setTitle(String t) { this.title = t; }
    public void setDescription(String d) { this.description = d; }
    public void setDone(boolean d) { this.done = d; }
}
```

---

## Part E — The `TaskRepository`

Replace `src/main/java/com/taskforge/task/TaskRepository.java`:
```java
package com.taskforge.task;

import org.springframework.data.jpa.repository.JpaRepository;
import java.util.List;

public interface TaskRepository extends JpaRepository<Task, Long> {
    List<Task> findByDone(boolean done);
    List<Task> findByTitleContainingIgnoreCase(String fragment);
}
```

> **No implementation file.** Spring Data generates a proxy at startup. The
> methods you wrote are derived queries — Spring parses the name and emits
> the SQL.

---

## Part F — Update `TaskService` and delete the in-memory repo

Open `TaskService.java`:
```java
package com.taskforge.task;

import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.NoSuchElementException;

@Service
@Transactional
public class TaskService {

    private final TaskRepository repo;

    public TaskService(TaskRepository repo) { this.repo = repo; }

    public Task create(String title, String description) {
        if (title == null || title.isBlank())
            throw new IllegalArgumentException("title is required");
        return repo.save(new Task(title.trim(), description));
    }

    @Transactional(readOnly = true)
    public List<Task> list() { return repo.findAll(); }

    @Transactional(readOnly = true)
    public Task get(Long id) {
        return repo.findById(id).orElseThrow(() -> new NoSuchElementException("no task " + id));
    }

    public Task markDone(Long id) {
        Task t = get(id);
        t.setDone(true);
        return repo.save(t);
    }

    public Task update(Long id, String title, String description, boolean done) {
        Task t = get(id);
        if (title != null) t.setTitle(title);
        if (description != null) t.setDescription(description);
        t.setDone(done);
        return repo.save(t);
    }

    public void delete(Long id) {
        if (!repo.existsById(id)) throw new NoSuchElementException("no task " + id);
        repo.deleteById(id);
    }
}
```

**Delete** `InMemoryTaskRepository.java`. The interface is implemented by
Spring Data now.

---

## Part G — Update the controller's mapper

`TaskResponse.from(Task)` no longer works with the new entity (no `id()`
accessor). Replace it:

```java
public record TaskResponse(
    Long id, String title, String description, boolean done, Instant createdAt
) {
    public static TaskResponse from(Task t) {
        return new TaskResponse(t.getId(), t.getTitle(), t.getDescription(), t.isDone(), t.getCreatedAt());
    }
}
```

---

## Part H — Run and verify

```bash
mvn -q spring-boot:run
```

In the logs look for:
```
Flyway Community Edition ...
Successfully applied 1 migration ...
Hibernate: ...
Started TaskforgeApplication in 2.3 seconds
```

Create a task:
```bash
curl -s -X POST localhost:8080/api/tasks \
  -H 'content-type: application/json' \
  -d '{"title":"Buy milk","description":"2% organic"}'
```

Read it back:
```bash
curl -s localhost:8080/api/tasks/1
```

Verify the row in Postgres:
```bash
docker compose -f ../../00-setup/compose.dev.yml exec postgres \
  psql -U taskforge -d taskforge -c 'select * from task;'
```

✅ **Checkpoint:** the row is in Postgres.

**The killer test:** stop the app (`Ctrl-C`), restart it
(`mvn -q spring-boot:run`), and `curl localhost:8080/api/tasks/1` again. The
data is still there.

---

## What you learned

- Spring Data JPA turns a repository *interface* into a working data layer
  with zero implementation code.
- Flyway versions your schema with plain SQL files; migrations are replayed
  identically in dev, CI, and prod.
- `ddl-auto: validate` lets Hibernate enforce "entity matches DB" without
  ever mutating the schema.
- `@Transactional` wraps a method in a database transaction; `readOnly = true`
  is a small optimization for queries.
- Disabling `open-in-view` forces all DB access through the service layer
  — a discipline that prevents `LazyInitializationException` and N+1 bugs.

➡️ Now try the **[challenge](./challenge.md)**, then move to
[Module 06](../06-validation-exceptions/).
