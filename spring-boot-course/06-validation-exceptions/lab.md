# Lab 06 — Build a Clean Error Contract

**You'll:** wire Bean Validation, add a global `@RestControllerAdvice`,
define a domain `NotFoundException`, and prove that every error response
follows the same RFC 7807 shape.

⏱️ ~50 min. Run from `spring-boot-course/apps/taskforge`.

---

## Part A — Validate the request DTOs

Open `src/main/java/com/taskforge/task/api/CreateTaskRequest.java` and make
sure the constraints are explicit:

```java
package com.taskforge.task.api;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;

public record CreateTaskRequest(
    @NotBlank(message = "title is required")
    @Size(max = 200, message = "title must be 200 chars or fewer")
    String title,

    @Size(max = 2000, message = "description must be 2000 chars or fewer")
    String description,

    @Pattern(regexp = "low|medium|high", message = "priority must be low, medium, or high")
    String priority
) {}
```

> The `@Valid` on the controller method (already added in Module 04) is what
> actually triggers the validation. Re-confirm it's there:
> ```java
> @PostMapping
> public ResponseEntity<TaskResponse> create(@RequestBody @Valid CreateTaskRequest req) { ... }
> ```

---

## Part B — A domain `NotFoundException`

`src/main/java/com/taskforge/common/NotFoundException.java`:
```java
package com.taskforge.common;

public class NotFoundException extends RuntimeException {
    public NotFoundException(String message) { super(message); }
}
```

`src/main/java/com/taskforge/common/ConflictException.java`:
```java
package com.taskforge.common;

public class ConflictException extends RuntimeException {
    public ConflictException(String message) { super(message); }
}
```

Update `TaskService` to throw these:
```java
public Task get(Long id) {
    return repo.findById(id)
        .orElseThrow(() -> new NotFoundException("Task " + id + " not found"));
}

public void delete(Long id) {
    if (!repo.existsById(id)) throw new NotFoundException("Task " + id + " not found");
    repo.deleteById(id);
}
```

> **Remove** the old `NoSuchElementException` imports — we're standardizing
> on `NotFoundException`.

---

## Part C — The global exception handler

`src/main/java/com/taskforge/api/ApiExceptionHandler.java`:
```java
package com.taskforge.api;

import com.taskforge.common.ConflictException;
import com.taskforge.common.NotFoundException;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpStatus;
import org.springframework.http.ProblemDetail;
import org.springframework.http.converter.HttpMessageNotReadableException;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

import java.net.URI;
import java.util.Map;
import java.util.NoSuchElementException;

@RestControllerAdvice
public class ApiExceptionHandler {

    private static final Logger log = LoggerFactory.getLogger(ApiExceptionHandler.class);

    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ProblemDetail handleValidation(MethodArgumentNotValidException ex) {
        ProblemDetail pd = ProblemDetail.forStatus(HttpStatus.BAD_REQUEST);
        pd.setType(URI.create("https://api.taskforge.com/errors/validation"));
        pd.setTitle("Validation failed");
        pd.setDetail("One or more fields are invalid.");
        pd.setProperty("errors", ex.getBindingResult().getFieldErrors().stream()
            .map(fe -> Map.of(
                "field", fe.getField(),
                "message", fe.getDefaultMessage() == null ? "invalid" : fe.getDefaultMessage()))
            .toList());
        return pd;
    }

    @ExceptionHandler({NotFoundException.class, NoSuchElementException.class})
    public ProblemDetail handleNotFound(RuntimeException ex) {
        ProblemDetail pd = ProblemDetail.forStatus(HttpStatus.NOT_FOUND);
        pd.setType(URI.create("https://api.taskforge.com/errors/not-found"));
        pd.setTitle("Not found");
        pd.setDetail(ex.getMessage());
        return pd;
    }

    @ExceptionHandler(ConflictException.class)
    public ProblemDetail handleConflict(ConflictException ex) {
        ProblemDetail pd = ProblemDetail.forStatus(HttpStatus.CONFLICT);
        pd.setType(URI.create("https://api.taskforge.com/errors/conflict"));
        pd.setTitle("Conflict");
        pd.setDetail(ex.getMessage());
        return pd;
    }

    @ExceptionHandler(IllegalArgumentException.class)
    public ProblemDetail handleBadInput(IllegalArgumentException ex) {
        ProblemDetail pd = ProblemDetail.forStatus(HttpStatus.BAD_REQUEST);
        pd.setType(URI.create("https://api.taskforge.com/errors/bad-input"));
        pd.setTitle("Bad request");
        pd.setDetail(ex.getMessage());
        return pd;
    }

    @ExceptionHandler(HttpMessageNotReadableException.class)
    public ProblemDetail handleUnreadable(HttpMessageNotReadableException ex) {
        ProblemDetail pd = ProblemDetail.forStatus(HttpStatus.BAD_REQUEST);
        pd.setType(URI.create("https://api.taskforge.com/errors/malformed"));
        pd.setTitle("Malformed request body");
        pd.setDetail("Request body is missing or not valid JSON.");
        return pd;
    }

    @ExceptionHandler(Exception.class)
    public ProblemDetail handleAny(Exception ex) {
        log.error("unhandled exception", ex);
        ProblemDetail pd = ProblemDetail.forStatus(HttpStatus.INTERNAL_SERVER_ERROR);
        pd.setType(URI.create("https://api.taskforge.com/errors/internal"));
        pd.setTitle("Internal server error");
        pd.setDetail("An unexpected error occurred. Try again later.");
        return pd;
    }
}
```

---

## Part D — Run and verify the error contract

```bash
mvn -q spring-boot:run
```

In another terminal:

**1. Validation error (400):**
```bash
curl -s -i -X POST localhost:8080/api/tasks \
  -H 'content-type: application/json' \
  -d '{"title":"","description":"too long","priority":"urgent"}'
# → 400 application/problem+json
# body includes "errors": [{"field":"title","message":"title is required"}, ...]
```

**2. Not found (404):**
```bash
curl -s -i localhost:8080/api/tasks/9999
# → 404 application/problem+json
# body: {"type":"https://api.taskforge.com/errors/not-found","title":"Not found","status":404,"detail":"Task 9999 not found"}
```

**3. Malformed JSON (400):**
```bash
curl -s -i -X POST localhost:8080/api/tasks \
  -H 'content-type: application/json' \
  -d 'not json'
# → 400 with type "https://api.taskforge.com/errors/malformed"
```

**4. Happy path (201):**
```bash
curl -s -i -X POST localhost:8080/api/tasks \
  -H 'content-type: application/json' \
  -d '{"title":"Buy milk","priority":"medium"}'
# → 201
```

✅ **Checkpoint:** every error response uses `application/problem+json` and
the same `ProblemDetail` shape. Clients can code against the contract.

---

## What you learned

- Bean Validation is enforced at the boundary when you put `@Valid` on the
  `@RequestBody`.
- A `@RestControllerAdvice` centralizes exception → response translation.
- `ProblemDetail` is Spring 6's RFC 7807 type; the framework serializes it
  with the right `application/problem+json` content type.
- Domain exceptions (`NotFoundException`, `ConflictException`) are clearer
  than reusing `NoSuchElementException` from the JDK.
- The `Exception.class` fallback is your safety net: log server-side, return
  a sanitized message client-side, never a stack trace.

➡️ Now try the **[challenge](./challenge.md)**, then move to
[Module 07](../07-security-jwt/).
