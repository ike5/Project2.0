# Module 05 — Data Access with Spring Data JPA & PostgreSQL

**Goal:** replace the in-memory `TaskRepository` with a real Postgres-backed
one. You'll learn **Spring Data JPA** — the abstraction that turns a
repository *interface* into a fully working data layer — and **Flyway**, the
tool that versions your schema the way Git versions your code.

⏱️ ~3.5 hours · 🎯 Prereq: Modules 02–04 complete (REST API works with in-memory data).

> The most important module for the **data layer**. After this, your tasks
> survive an app restart — and your schema is reproducible across every
> environment.

---

## 1. The JPA / Hibernate stack

| Layer | What it does |
|-------|--------------|
| **JDBC** | Java Database Connectivity — the low-level API. `Connection`, `PreparedStatement`, `ResultSet`. |
| **JPA** | Jakarta Persistence API — the spec. Defines `@Entity`, `EntityManager`, JPQL. |
| **Hibernate** | The most popular JPA implementation. Does the actual SQL generation and execution. |
| **Spring Data JPA** | Spring's wrapper. You define a repository *interface*; Spring generates the implementation. |
| **Flyway** | Schema migration tool. Versioned SQL files, applied in order. |

**You mostly write interface methods.** Spring generates the implementation
at startup. The result is less boilerplate than JDBC and more productivity
than raw Hibernate.

---

## 2. Add the dependencies

`pom.xml`:
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

What each one gives you:

- **`spring-boot-starter-data-jpa`** — Hibernate, Spring Data, HikariCP (the
  connection pool).
- **`postgresql`** — the JDBC driver.
- **`flyway-core`** + **`flyway-database-postgresql`** — schema migrations.

---

## 3. Configure the datasource

`application.yml`:
```yaml
spring:
  datasource:
    url: jdbc:postgresql://localhost:5432/taskforge
    username: taskforge
    password: taskforge
  jpa:
    hibernate:
      ddl-auto: validate          # Hibernate checks the schema matches; never auto-alter
    open-in-view: false           # disable OSIV (anti-pattern, see GLOSSARY)
    properties:
      hibernate.format_sql: true
      hibernate.jdbc.time_zone: UTC
  flyway:
    enabled: true
    locations: classpath:db/migration
```

> **`ddl-auto: validate`** is the safe choice. Hibernate will refuse to start
> if the entity and the database schema disagree. `update` is dangerous
> (silently mutates prod) and `create` is for throwaway experiments only.
> We own our schema with Flyway, so Hibernate just verifies.

---

## 4. The first migration

SQL files in `src/main/resources/db/migration/` are applied in alphabetical
order on startup. The naming convention is `V<version>__<description>.sql`
(two underscores between version and description).

`V1__create_task_table.sql`:
```sql
CREATE TABLE task (
    id          BIGSERIAL PRIMARY KEY,
    title       VARCHAR(200)  NOT NULL,
    description VARCHAR(2000),
    done        BOOLEAN       NOT NULL DEFAULT FALSE,
    created_at  TIMESTAMPTZ   NOT NULL DEFAULT now()
);

CREATE INDEX idx_task_done ON task(done);
```

> `BIGSERIAL` is Postgres's auto-incrementing 8-byte integer. The JPA
> `@GeneratedValue(strategy = IDENTITY)` maps to it.

Flyway writes a `flyway_schema_history` table that records which migrations
have run. Restart-safe and reversible only by writing a new migration.

---

## 5. The `Task` entity

A JPA entity is a class mapped to a table. Annotations describe the mapping.

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

    protected Task() { }                            // JPA needs a no-arg constructor

    public Task(String title, String description) {
        this.title = title;
        this.description = description;
        this.done = false;
        this.createdAt = Instant.now();
    }

    public Long    getId()          { return id; }
    public String  getTitle()       { return title; }
    public String  getDescription() { return description; }
    public boolean isDone()         { return done; }
    public Instant getCreatedAt()   { return createdAt; }

    public void setTitle(String t)            { this.title = t; }
    public void setDescription(String d)       { this.description = d; }
    public void setDone(boolean d)             { this.done = d; }
}
```

> **Why a class and not a record?** JPA needs a no-arg constructor and
> typically uses field-based reflection. Records work in Hibernate 6.2+,
> but the classic class with getters/setters is the more common pattern
> you'll see in real codebases. Module 05 sticks to the classic style.

**Mapping details worth knowing:**

- `@Id` + `@GeneratedValue(IDENTITY)` → DB-generated id.
- `@Column(name = "created_at", nullable = false, updatable = false)` → maps
  the camelCase field to a snake_case column and makes it read-only after
  insert.
- `protected` no-arg constructor → JPA uses it; you don't.
- No setter for `id` or `createdAt` → they shouldn't change.

---

## 6. The repository — interface only

```java
package com.taskforge.task;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import java.util.List;

public interface TaskRepository extends JpaRepository<Task, Long> {

    List<Task> findByDone(boolean done);

    List<Task> findByTitleContainingIgnoreCase(String fragment);

    @Query("SELECT t FROM Task t WHERE t.done = false ORDER BY t.createdAt DESC")
    List<Task> findOpenOrderByCreated();

    @Query(value = "SELECT * FROM task WHERE done = false ORDER BY created_at DESC LIMIT :limit",
           nativeQuery = true)
    List<Task> findRecentOpen(@Param("limit") int limit);
}
```

**What you get for free from `JpaRepository`:**
- `findAll()`, `findById(id)`, `save(entity)`, `deleteById(id)`,
  `count()`, `existsById(id)`, `flush()`, …

**Derived query methods** — name them in a pattern Spring parses:
- `findByDone` → `WHERE done = ?`
- `findByTitleContainingIgnoreCase` → `WHERE LOWER(title) LIKE LOWER('%' || ? || '%')`
- `countByDone` → `SELECT COUNT(*) WHERE done = ?`

**`@Query` for things that don't fit the naming pattern** — write JPQL
(`Task` not `task`, fields not columns) or native SQL.

---

## 7. Wiring — kill the in-memory repo, use the JPA one

Delete `InMemoryTaskRepository.java`. The `TaskRepository` interface is now
implemented automatically by Spring Data — you don't write the
implementation.

`TaskService` was already written against the interface, so the only change
is the **constructor**: it no longer needs the explicit `Clock` injection
unless you want to use it for the entity (the entity itself sets
`createdAt`).

> **Decision point:** who owns `createdAt`? In this module the entity sets
> it in the constructor. In Module 06 we'll move that to the service so
> auditing is centralized.

Run the app:
```bash
mvn -q spring-boot:run
```

Watch the logs:
```
Flyway Community Edition 10.x by Redgate
Successfully validated 1 migration (running V1__create_task_table)
Migrating schema "taskforge" to version "1 - create task table"
Successfully applied 1 migration to schema "taskforge"
...
Hibernate ORM core version 6.5.x.Final
Started TaskforgeApplication in 2.3 seconds
```

✅ **Checkpoint:** Flyway created the `task` table; Hibernate validated
the entity matches; the app is up. Create a task via curl; `docker exec
postgres psql ... -c 'select * from task;'` shows the row.

---

## 8. `@Transactional` — the magic that makes it all atomic

The `@Transactional` annotation wraps a method in a database transaction.
All SQL inside runs as one unit: if anything throws, the whole thing rolls
back.

```java
@Service
public class TaskService {
    private final TaskRepository repo;

    public TaskService(TaskRepository repo) { this.repo = repo; }

    @Transactional
    public Task create(String title, String description) {
        return repo.save(new Task(title, description));
    }

    @Transactional(readOnly = true)
    public List<Task> list() { return repo.findAll(); }

    @Transactional
    public void delete(Long id) { repo.deleteById(id); }
}
```

> **Why mark `readOnly = true` on reads?** It tells Hibernate not to flush
> the session, which is a small performance win and a safety net against
> accidental writes.

Spring's transaction manager is auto-configured when JPA is on the
classpath. `@Transactional` works on any bean.

---

## 9. Relationships — `@OneToMany`, `@ManyToOne`, `@ManyToMany`

You'll rarely have a single table. The most common relationships:

```java
// One user has many tasks
@Entity
public class User {
    @Id @GeneratedValue private Long id;
    @Column(unique = true, nullable = false) private String email;
    @OneToMany(mappedBy = "owner") private List<Task> tasks = new ArrayList<>();
}

@Entity
public class Task {
    @Id @GeneratedValue private Long id;
    @ManyToOne(fetch = FetchType.LAZY) @JoinColumn(name = "owner_id")
    private User owner;
}
```

> **Defaults and gotchas:**
> - `@ManyToOne` and `@OneToOne` default to **eager** loading — usually wrong.
> - `@OneToMany` and `@ManyToMany` default to **lazy** loading — usually right.
> - The **`mappedBy`** attribute points to the field on the *owning* side.
> - Lazy collections throw `LazyInitializationException` outside a
>   transaction. We disabled `open-in-view` to force service-layer access.

The N+1 problem and `JOIN FETCH` are covered in Module 08.

---

## 10. Auditing — `@CreatedDate`, `@LastModifiedDate`, `@CreatedBy`

For "who created this" and "when was it last updated":

```java
@EntityListeners(AuditingEntityListener.class)
@MappedSuperclass
public abstract class Auditable {
    @CreatedDate  @Column(updatable = false) private Instant createdAt;
    @LastModifiedDate private Instant updatedAt;
    @CreatedBy  private String createdBy;
    @LastModifiedBy private String updatedBy;
}

@EnableJpaAuditing
@SpringBootApplication
@ConfigurationPropertiesScan
public class TaskforgeApplication { ... }

@Entity
public class Task extends Auditable { ... }
```

> Module 09 sets the auditor from the security context, so the "who" is
> filled in automatically.

---

## 11. The "right" service layer for `taskforge`

Combining JPA, transactions, and the controller layer:

```
TaskController (Module 04)
    │
    ▼
TaskService          ← @Service, @Transactional
    │
    ▼
TaskRepository       ← interface; Spring Data generates the impl
    │
    ▼
Hibernate  ──►  HikariCP  ──►  Postgres
```

By Module 16, this is exactly the shape `taskforge` has.

---

## 12. Common pitfalls

| Symptom | Cause | Fix |
|---------|-------|-----|
| `SchemaManagementException: Schema-validation` | Entity and DB disagree | Update the migration; never `ddl-auto=update` |
| `LazyInitializationException` | Touched a `@OneToMany` outside a transaction | Wrap the call in `@Transactional`; or `JOIN FETCH` |
| `JpaSystemException: could not extract ResultSet` | Native query returns columns the entity doesn't have | Match the SELECT list to the entity fields |
| Data inserted but id is `null` in the response | Forgot `@GeneratedValue` or set `id` manually | Let the DB assign ids |
| Dates off by hours | Server time zone ≠ Postgres time zone | Set `hibernate.jdbc.time_zone: UTC` and store `timestamptz` |

---

## 13. Do the lab

Replace the in-memory repository with a JPA + Postgres one. Add Flyway,
define the entity, derive a few queries, and prove the data survives a
restart.

👉 **[lab.md](./lab.md)**

Then test yourself: 👉 **[challenge.md](./challenge.md)**

---

## Key terms (see [GLOSSARY](../GLOSSARY.md))

JDBC · JPA · Hibernate · Spring Data JPA · `JpaRepository` · derived query · JPQL · native query · entity · `@Id` · `@GeneratedValue` · `@Column` · `@OneToMany` · `@ManyToOne` · `mappedBy` · lazy vs eager · `@Transactional` · Flyway · migration · `ddl-auto` · OSIV

**Next →** [Module 06: Validation & Exception Handling](../06-validation-exceptions/)
