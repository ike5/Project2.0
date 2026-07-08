# Module 06 — Validation & Exception Handling

**Goal:** turn bad input into structured `400` responses and turn unhandled
exceptions into predictable, documented error contracts. By the end of this
module, **no exception ever leaks a stack trace to the client** — every
failure is a clean JSON body with a status, a message, and a machine-readable
code.

⏱️ ~2 hours · 🎯 Prereq: Modules 02–05 complete (REST + JPA working).

> A real API is defined as much by **how it fails** as by how it succeeds.
> This module establishes the error contract clients can code against.

---

## 1. Two layers of validation

| Layer | When | What it checks |
|-------|------|----------------|
| **Bean Validation (jakarta.validation)** | Before the controller method runs | Field-level rules: `@NotBlank`, `@Size`, `@Email`, … |
| **Service-layer checks** | Inside the business logic | Cross-field rules, "owner cannot be the same as assignee," "title is unique" |

Bean Validation catches the easy stuff at the boundary; the service layer
catches the rest. **Both layers should be tested.**

---

## 2. The starter you already have

`@NotBlank` worked in Module 04 because `spring-boot-starter-validation` is
a transitive dependency of `spring-boot-starter-web`. The annotations live in
`jakarta.validation.constraints.*`:

```java
public record CreateTaskRequest(
    @NotBlank(message = "title is required")
    @Size(max = 200, message = "title must be 200 chars or fewer")
    String title,

    @Size(max = 2000) String description,

    @Pattern(regexp = "low|medium|high") String priority
) {}
```

**Common annotations:**

| Annotation | Validates |
|-----------|-----------|
| `@NotNull` | value is not `null` |
| `@NotBlank` | string is not `null`, empty, or whitespace |
| `@NotEmpty` | string/collection/map is not `null` and not empty |
| `@Size(min, max)` | size of string/collection is in range |
| `@Min`, `@Max` | numeric value |
| `@Email` | well-formed email |
| `@Pattern(regexp = "...")` | matches a regex |
| `@Past`, `@Future` | date in past / future |
| `@Positive`, `@Negative` | sign of a number |
| `@AssertTrue`, `@AssertFalse` | boolean is true / false |

To make them fire, annotate the `@RequestBody` parameter with `@Valid`:
```java
@PostMapping
public TaskResponse create(@RequestBody @Valid CreateTaskRequest req) { ... }
```

---

## 3. The problem — Spring's default error response is ugly

`POST /api/tasks` with `{"title":""}`:
```json
{
  "timestamp": "2024-01-15T10:30:00.000+00:00",
  "status": 400,
  "error": "Bad Request",
  "path": "/api/tasks"
}
```

The "title is required" message is *gone*. That's a poor API contract.
Clients can't tell which field failed, and they have to string-match the
error.

---

## 4. RFC 7807 — Problem Details for HTTP APIs

The IETF standard for error responses. Spring 6 / Boot 3 has first-class
support:

```json
{
  "type": "https://api.taskforge.com/errors/validation",
  "title": "Validation failed",
  "status": 400,
  "detail": "One or more fields are invalid.",
  "instance": "/api/tasks",
  "errors": [
    { "field": "title", "message": "title is required" },
    { "field": "priority", "message": "must match \"low|medium|high\"" }
  ]
}
```

`type` is a URI identifying the problem class. `title` is a short summary.
`status` mirrors the HTTP status. `errors[]` is the custom array of field
errors. **RFC 7807 is the contract; you decide which extra fields to add.**

---

## 5. The global exception handler — `@RestControllerAdvice`

A class annotated with `@RestControllerAdvice` is consulted **for every
exception thrown by every controller**. Define `@ExceptionHandler` methods
to translate exceptions into the response you want.

```java
package com.taskforge.api;

import org.springframework.http.HttpStatus;
import org.springframework.http.ProblemDetail;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

import java.net.URI;
import java.util.List;
import java.util.Map;
import java.util.NoSuchElementException;

@RestControllerAdvice
public class ApiExceptionHandler {

    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ProblemDetail handleValidation(MethodArgumentNotValidException ex) {
        ProblemDetail pd = ProblemDetail.forStatus(HttpStatus.BAD_REQUEST);
        pd.setType(URI.create("https://api.taskforge.com/errors/validation"));
        pd.setTitle("Validation failed");
        pd.setDetail("One or more fields are invalid.");
        pd.setProperty("errors", ex.getBindingResult().getFieldErrors().stream()
            .map(fe -> Map.of("field", fe.getField(),
                              "message", fe.getDefaultMessage() == null ? "invalid" : fe.getDefaultMessage()))
            .toList());
        return pd;
    }

    @ExceptionHandler(NoSuchElementException.class)
    public ProblemDetail handleNotFound(NoSuchElementException ex) {
        ProblemDetail pd = ProblemDetail.forStatus(HttpStatus.NOT_FOUND);
        pd.setType(URI.create("https://api.taskforge.com/errors/not-found"));
        pd.setTitle("Not found");
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
}
```

> `ProblemDetail` is Spring 6's built-in RFC 7807 type. Returning one from
> a controller or advice is automatically serialized to the right
> `application/problem+json` content type.

---

## 6. A dedicated `NotFoundException`

`NoSuchElementException` is a JDK class — it's used in many places, and
catching it generically can hide other bugs. Define a domain exception:

```java
package com.taskforge.common;

public class NotFoundException extends RuntimeException {
    public NotFoundException(String message) { super(message); }
}
```

Use it in services:
```java
public Task get(Long id) {
    return repo.findById(id).orElseThrow(() -> new NotFoundException("Task " + id + " not found"));
}
```

…and handle it in the advice:
```java
@ExceptionHandler(NotFoundException.class)
public ProblemDetail handleNotFound(NotFoundException ex) {
    ProblemDetail pd = ProblemDetail.forStatus(HttpStatus.NOT_FOUND);
    pd.setType(URI.create("https://api.taskforge.com/errors/not-found"));
    pd.setTitle("Not found");
    pd.setDetail(ex.getMessage());
    return pd;
}
```

> **Pattern:** `NotFoundException`, `ConflictException`,
> `ForbiddenException`, … — one exception per HTTP status you need.

---

## 7. Catching the unknown — the fallback handler

The last line of defense. Anything that escapes the typed handlers turns
into a `500 Internal Server Error` with a generic message — **never a stack
trace**:

```java
@ExceptionHandler(Exception.class)
public ProblemDetail handleAny(Exception ex) {
    log.error("unhandled exception", ex);   // server-side log
    ProblemDetail pd = ProblemDetail.forStatus(HttpStatus.INTERNAL_SERVER_ERROR);
    pd.setType(URI.create("https://api.taskforge.com/errors/internal"));
    pd.setTitle("Internal server error");
    pd.setDetail("An unexpected error occurred. Try again later.");
    return pd;
}
```

> **Log the full exception server-side; return a sanitized message to the
> client.** Stack traces can leak file paths, code structure, and library
> versions to attackers.

---

## 8. Service-layer validation patterns

A few patterns you'll use all the time:

```java
// "Owner cannot be the assignee"
if (Objects.equals(task.getOwnerId(), task.getAssigneeId()))
    throw new IllegalArgumentException("owner and assignee must differ");

// "Title must be unique"
if (repo.existsByTitleAndOwnerId(title, ownerId))
    throw new ConflictException("title already exists for this owner");

// "Cannot delete a task with children"
if (task.getSubtasks() != null && !task.getSubtasks().isEmpty())
    throw new ConflictException("task has subtasks");
```

These belong in the service, **not** the controller, because:

1. The service is the boundary of business truth.
2. Tests for the service cover them; you don't need to spin up the web layer.

---

## 9. Custom validation annotations

When a constraint is reused or has a non-trivial implementation, write a
custom annotation:

```java
@Target({ElementType.FIELD, ElementType.PARAMETER})
@Retention(RetentionPolicy.RUNTIME)
@Constraint(validatedBy = NoProfanityValidator.class)
public @interface NoProfanity {
    String message() default "must not contain profanity";
    Class<?>[] groups() default {};
    Class<? extends Payload>[] payload() default {};
}

public class NoProfanityValidator implements ConstraintValidator<NoProfanity, String> {
    private static final Set<String> BANNED = Set.of("darn", "shoot");
    public boolean isValid(String value, ConstraintValidatorContext ctx) {
        return value == null || Arrays.stream(value.split("\\s+"))
            .noneMatch(w -> BANNED.contains(w.toLowerCase()));
    }
}
```

Use it like any other constraint:
```java
public record CreateTaskRequest(
    @NotBlank @NoProfanity String title,
    ...
) {}
```

---

## 10. Validation in service tests

Use a `Validator` directly to test constraints without Spring:

```java
class CreateTaskRequestTest {
    private static final Validator VALIDATOR =
        Validation.buildDefaultValidatorFactory().getValidator();

    @Test
    void blankTitleFails() {
        var violations = VALIDATOR.validate(new CreateTaskRequest("", "desc", "low"));
        assertThat(violations).extracting("propertyPath").extracting(Object::toString)
            .containsExactly("title");
    }
}
```

> The Spring test starter wires a `LocalValidatorFactoryBean` for you, so
> `@Valid` in controllers and the standalone `Validator` are the same
> implementation.

---

## 11. Common pitfalls

| Symptom | Cause | Fix |
|---------|-------|-----|
| Validation never fires | Missing `@Valid` on the `@RequestBody` | Add `@Valid` |
| `ConstraintViolationException` instead of `MethodArgumentNotValidException` | Validation on a `@RequestParam` or path variable | Add `@Validated` to the controller class |
| `ProblemDetail` returns `null` fields | Set wrong type — used `setDetail` for `setTitle` | Use the right setter |
| `415` instead of `400` for malformed JSON | Spring is rejecting the body before validation | Add `HttpMessageNotReadableException` handler |
| Stack trace in the response | You forgot the `Exception.class` fallback | Add a fallback `@ExceptionHandler(Exception.class)` |

---

## 12. Do the lab

Wire Bean Validation, a global exception handler, and the domain
`NotFoundException`. Confirm the error contract with a few `curl` calls that
trigger each error type.

👉 **[lab.md](./lab.md)**

Then test yourself: 👉 **[challenge.md](./challenge.md)**

---

## Key terms (see [GLOSSARY](../GLOSSARY.md))

Bean Validation · `@NotBlank` / `@Size` / `@Email` / `@Pattern` · `@Valid` · RFC 7807 · `ProblemDetail` · `@RestControllerAdvice` · `@ExceptionHandler` · service-layer validation · custom constraint

**Next →** [Module 07: Security with Spring Security & JWT](../07-security-jwt/)
