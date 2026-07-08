# Challenge 05 — Reference Solution

### 1. Add `priority`
`V2__add_task_priority.sql`:
```sql
ALTER TABLE task ADD COLUMN priority VARCHAR(10) NOT NULL DEFAULT 'medium';
```
Entity:
```java
@Column(nullable = false, length = 10) private String priority = "medium";
public String getPriority() { return priority; }
public void setPriority(String p) { this.priority = p; }
```
DTO `TaskResponse`: add `String priority` to the record and to `from(...)`.

Confirm in psql:
```sql
select version, description, success from flyway_schema_history order by installed_rank;
```

### 2. Derived query
```java
List<Task> findByDoneAndPriority(boolean done, String priority);
```
```java
// TaskService
@Transactional(readOnly = true)
public List<Task> list(boolean done, String priority) {
    return repo.findByDoneAndPriority(done, priority);
}
```

### 3. JPQL recent
```java
@Query("SELECT t FROM Task t WHERE t.done = false ORDER BY t.createdAt DESC")
List<Task> findRecentOpen(Pageable pageable);
```
```java
// controller
@GetMapping("/recent")
public List<TaskResponse> recent() {
    return service.findRecentOpen(10).stream().map(TaskResponse::from).toList();
}
```

### 4. Auditing
Add to the entity (or an `Auditable` superclass):
```java
@LastModifiedDate
@Column(name = "updated_at")
private Instant updatedAt;
```
Enable auditing:
```java
@EnableJpaAuditing
@SpringBootApplication
public class TaskforgeApplication { ... }
```
Update a task:
```sql
select title, created_at, updated_at from task;
```
The `updated_at` advances.

### 5. Unique constraint
`V3__create_app_user.sql`:
```sql
CREATE TABLE app_user (
    id    BIGSERIAL PRIMARY KEY,
    email VARCHAR(254) UNIQUE NOT NULL
);
```
Two inserts with the same email:
```
ERROR: duplicate key value violates unique constraint "app_user_email_key"
```

### 6. Specification (stretch)
```java
public interface TaskRepository extends JpaRepository<Task, Long>, JpaSpecificationExecutor<Task> {}
```
```java
public static Specification<Task> filter(Boolean done, String priority) {
    return (root, q, cb) -> {
        var preds = new ArrayList<Predicate>();
        if (done != null)     preds.add(cb.equal(root.get("done"), done));
        if (priority != null) preds.add(cb.equal(root.get("priority"), priority));
        return cb.and(preds.toArray(new Predicate[0]));
    };
}
```
```java
// controller
@GetMapping
public List<TaskResponse> list(@RequestParam(required = false) Boolean done,
                                @RequestParam(required = false) String priority) {
    return repo.findAll(Specifications.filter(done, priority))
               .stream().map(TaskResponse::from).toList();
}
```

> Specifications are how you build the dynamic "filter sidebar" in admin
> panels — Spring Data writes the SQL, you write the conditions.
