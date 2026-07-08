# Cheatsheet — Spring Data JPA & Hibernate

Quick reference for the data layer. Keep it open while you build.

## Entity skeleton

```java
@Entity
@Table(name = "task")
public class Task {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false, length = 200)
    private String title;

    @Column(name = "created_at", nullable = false, updatable = false)
    private Instant createdAt;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 16)
    private Priority priority = Priority.MEDIUM;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "owner_id")
    private User owner;

    @OneToMany(mappedBy = "task", cascade = CascadeType.ALL, orphanRemoval = true)
    private List<Comment> comments = new ArrayList<>();

    protected Task() { }                       // JPA needs it
    public Task(String title) { this.title = title; this.createdAt = Instant.now(); }
    // getters / setters
}
```

## Repository

```java
public interface TaskRepository extends JpaRepository<Task, Long> {

    // Derived queries — name them in a pattern Spring parses
    List<Task> findByDone(boolean done);
    List<Task> findByTitleContainingIgnoreCase(String fragment);
    Optional<Task> findByOwnerIdAndId(Long ownerId, Long id);
    long countByOwnerIdAndDone(Long ownerId, boolean done);
    boolean existsByTitle(String title);

    // Custom JPQL
    @Query("SELECT t FROM Task t WHERE t.done = false ORDER BY t.createdAt DESC")
    List<Task> findOpen(Pageable pageable);

    // Native SQL
    @Query(value = "SELECT * FROM task WHERE done = false ORDER BY created_at DESC LIMIT :n",
           nativeQuery = true)
    List<Task> findRecentOpen(@Param("n") int n);

    // Modifying — must be in a transaction
    @Modifying
    @Query("UPDATE Task t SET t.done = true WHERE t.id = :id")
    int markDone(@Param("id") Long id);

    // Specifications (dynamic filters)
    // public interface TaskRepository extends JpaRepository<Task, Long>, JpaSpecificationExecutor<Task> {}
}
```

## Migrations (Flyway)

```
src/main/resources/db/migration/
├── V1__create_task_table.sql
├── V2__add_priority.sql
├── V3__create_app_user.sql
└── V4__add_owner_id.sql
```

```sql
-- V1__create_task_table.sql
CREATE TABLE task (
    id          BIGSERIAL    PRIMARY KEY,
    title       VARCHAR(200) NOT NULL,
    description VARCHAR(2000),
    done        BOOLEAN      NOT NULL DEFAULT FALSE,
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT now()
);
CREATE INDEX idx_task_done ON task(done);
```

> **Never edit a migration after it's been applied.** Add a new one.

## `@Transactional`

```java
@Service
@Transactional                                  // all methods
public class TaskService {

    @Transactional(readOnly = true)              // explicit on reads
    public Task get(Long id) { ... }

    @Transactional(propagation = Propagation.REQUIRES_NEW)
    public void audit(String msg) { ... }        // new tx, suspends outer
}
```

| Propagation | Effect |
|-------------|--------|
| `REQUIRED` (default) | Use existing tx; create if none |
| `REQUIRES_NEW` | Always new; suspends any existing |
| `MANDATORY` | Must be in a tx; throw if not |
| `NEVER` | Must NOT be in a tx |
| `NESTED` | Savepoint inside an existing tx |

| Isolation | Effect |
|-----------|--------|
| `DEFAULT` | DB default |
| `READ_COMMITTED` | No dirty reads |
| `REPEATABLE_READ` | + no non-repeatable reads |
| `SERIALIZABLE` | + no phantoms |

## N+1 — the most common performance bug

```java
// Bad — N+1
List<Task> tasks = repo.findAll();
for (Task t : tasks) System.out.println(t.getOwner().getName());

// Good — JOIN FETCH
@Query("SELECT t FROM Task t JOIN FETCH t.owner")
List<Task> findAllWithOwner();

// Or
@Query("SELECT t FROM Task t WHERE t.id = :id")
@EntityGraph(attributePaths = "owner")
Optional<Task> findByIdWithOwner(@Param("id") Long id);
```

## Pagination

```java
@GetMapping
public Page<TaskResponse> list(
    @RequestParam(defaultValue = "0")  int page,
    @RequestParam(defaultValue = "20") int size
) {
    return service.list(PageRequest.of(page, size, Sort.by("createdAt").descending()))
                  .map(TaskResponse::from);
}
```

`Page` carries `content`, `totalElements`, `totalPages`, `number`, `size`.

## Auditing

```java
@EntityListeners(AuditingEntityListener.class)
@MappedSuperclass
public abstract class Auditable {
    @CreatedDate  @Column(updatable = false) private Instant createdAt;
    @LastModifiedDate                            private Instant updatedAt;
    @CreatedBy                                   private String createdBy;
    @LastModifiedBy                              private String updatedBy;
}
@EnableJpaAuditing
@SpringBootApplication
public class MyAppApplication { ... }

// optional: set the auditor from the security context
@Component
class SpringSecurityAuditorAware implements AuditorAware<String> {
    public Optional<String> getCurrentAuditor() {
        var auth = SecurityContextHolder.getContext().getAuthentication();
        return Optional.ofNullable(auth == null ? null : (String) auth.getDetails());
    }
}
```

## `ddl-auto` cheat

| Value | Use it when |
|-------|-------------|
| `none` | Flyway is the source of truth (default for this course) |
| `validate` | Hibernate checks entity ↔ DB; refuses to start on mismatch |
| `update` | **Local dev only** — silently mutates the DB |
| `create` | Throwaway experiments |
| `create-drop` | Tests with H2 |

## Common pitfalls

- **`LazyInitializationException`** — touched a `@OneToMany` outside a
  tx. Either wrap the call in `@Transactional` or use `JOIN FETCH`.
- **`Detached entity passed to persist`** — you used a previous ID
  accidentally. Refresh the entity.
- **`Schema-validation: missing column [xxx]`** — your entity changed;
  write a migration.
- **N+1** — see above. The fastest way to find it: turn on
  `hibernate.generate_statistics=true` and check the query count.

## Application properties (the JPA section)

```yaml
spring:
  jpa:
    hibernate:
      ddl-auto: validate
    open-in-view: false                # discipline: no lazy loads in controllers
    show-sql: true                     # dev only
    properties:
      hibernate.format_sql: true
      hibernate.jdbc.time_zone: UTC
      hibernate.generate_statistics: true  # dev only
  flyway:
    enabled: true
    locations: classpath:db/migration
    baseline-on-migrate: true          # allow migrating an existing schema
```
