# Lab 04 — Expose the Service over HTTP

**You'll:** wire `TaskService` to a real REST API with proper DTOs, all five
CRUD endpoints, correct status codes, and a curl-based smoke test.

⏱️ ~50 min. Run from `spring-boot-course/apps/taskforge`. The data services
from Module 00 should be running (you don't need Postgres yet — the in-memory
repo still works).

---

## Part A — Add the DTO records

`src/main/java/com/taskforge/task/api/CreateTaskRequest.java`:
```java
package com.taskforge.task.api;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

public record CreateTaskRequest(
    @NotBlank @Size(max = 200) String title,
    @Size(max = 2000) String description
) {}
```

> The `@NotBlank` and `@Size` annotations are from **Jakarta Bean
> Validation** (included with `spring-boot-starter-validation`, which the
> web starter transitively pulls in). Module 06 turns them into 400
> responses.

`src/main/java/com/taskforge/task/api/UpdateTaskRequest.java`:
```java
package com.taskforge.task.api;

public record UpdateTaskRequest(String title, String description, Boolean done) {}
```

`src/main/java/com/taskforge/task/api/TaskResponse.java`:
```java
package com.taskforge.task.api;
import com.taskforge.task.Task;
import java.time.Instant;

public record TaskResponse(
    Long id, String title, String description, boolean done, Instant createdAt
) {
    public static TaskResponse from(Task t) {
        return new TaskResponse(t.id(), t.title(), t.description(), t.done(), t.createdAt());
    }
}
```

---

## Part B — The full `TaskController`

`src/main/java/com/taskforge/task/api/TaskController.java`:
```java
package com.taskforge.task.api;

import com.taskforge.task.Task;
import com.taskforge.task.TaskService;
import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/tasks")
public class TaskController {

    private final TaskService service;

    public TaskController(TaskService service) {
        this.service = service;
    }

    @GetMapping
    public List<TaskResponse> list() {
        return service.list().stream().map(TaskResponse::from).toList();
    }

    @GetMapping("/{id}")
    public TaskResponse get(@PathVariable Long id) {
        return TaskResponse.from(service.get(id));
    }

    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    public TaskResponse create(@RequestBody @Valid CreateTaskRequest req) {
        Task t = service.create(req.title(), req.description());
        return TaskResponse.from(t);
    }

    @PutMapping("/{id}")
    public TaskResponse update(@PathVariable Long id, @RequestBody UpdateTaskRequest req) {
        return TaskResponse.from(service.update(
            id, req.title(), req.description(), req.done() != null && req.done()));
    }

    @DeleteMapping("/{id}")
    @ResponseStatus(HttpStatus.NO_CONTENT)
    public void delete(@PathVariable Long id) {
        service.delete(id);
    }
}
```

---

## Part C — Add the `update(...)` method to `TaskService`

Open `TaskService.java` and add:
```java
public Task update(Long id, String title, String description, boolean done) {
    Task existing = get(id);
    return repo.save(new Task(
        existing.id(),
        title  != null ? title  : existing.title(),
        description != null ? description : existing.description(),
        done,
        existing.createdAt()
    ));
}
```

Remove the `TaskForgeRunner` (or comment it out) — we want a clean slate for
the smoke test.

---

## Part D — Run and smoke-test

```bash
mvn -q spring-boot:run
```

In another terminal:
```bash
# create
curl -s -i -X POST localhost:8080/api/tasks \
  -H 'content-type: application/json' \
  -d '{"title":"Buy milk","description":"2% organic"}'
# → HTTP/1.1 201
#   Content-Type: application/json
#   {"id":1,"title":"Buy milk","description":"2% organic","done":false,"createdAt":"..."}

# list
curl -s localhost:8080/api/tasks
# → [{"id":1,...},{"id":2,...}]

# get one
curl -s localhost:8080/api/tasks/1

# update
curl -s -X PUT localhost:8080/api/tasks/1 \
  -H 'content-type: application/json' \
  -d '{"title":"Buy oat milk","description":"","done":true}'

# delete
curl -s -i -X DELETE localhost:8080/api/tasks/2
# → HTTP/1.1 204
```

✅ **Checkpoint:** every endpoint returns the expected status and body. The
in-memory `TaskRepository` is the data layer; the data is gone when the app
restarts (Module 05 swaps it for Postgres).

---

## Part E — Add a `Location` header on create (use `ResponseEntity`)

Replace the `create` method with:
```java
@PostMapping
public ResponseEntity<TaskResponse> create(@RequestBody @Valid CreateTaskRequest req) {
    Task t = service.create(req.title(), req.description());
    return ResponseEntity
        .created(URI.create("/api/tasks/" + t.id()))
        .body(TaskResponse.from(t));
}
```

`curl -i -X POST ... -d '...'` now shows:
```
HTTP/1.1 201
Location: /api/tasks/3
```

---

## What you learned

- `@RestController` + `@RequestMapping` + method-specific annotations are the
  routing vocabulary.
- DTOs at the API boundary keep your wire format decoupled from your domain.
- `@PathVariable` binds URL segments, `@RequestParam` binds query params,
  `@RequestBody` binds JSON bodies.
- `@ResponseStatus` is the simple way to set a status; `ResponseEntity` is
  the powerful way (status + headers + body).
- Records are a perfect match for DTOs: Jackson serializes them with
  zero configuration.

➡️ Now try the **[challenge](./challenge.md)**, then move to
[Module 05](../05-data-jpa-postgres/).
