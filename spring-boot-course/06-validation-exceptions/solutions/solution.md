# Challenge 06 — Reference Solution

### 1. `@NoHtml` annotation
```java
@Target({ElementType.FIELD, ElementType.PARAMETER})
@Retention(RetentionPolicy.RUNTIME)
@Constraint(validatedBy = NoHtmlValidator.class)
public @interface NoHtml {
    String message() default "must not contain HTML";
    Class<?>[] groups() default {};
    Class<? extends Payload>[] payload() default {};
}

public class NoHtmlValidator implements ConstraintValidator<NoHtml, String> {
    public boolean isValid(String v, ConstraintValidatorContext ctx) {
        return v == null || (v.indexOf('<') < 0 && v.indexOf('>') < 0);
    }
}
```
DTO:
```java
public record CreateTaskRequest(
    @NotBlank @Size(max = 200) String title,
    @Size(max = 2000) @NoHtml String description,
    @Pattern(regexp = "low|medium|high") String priority
) {}
```

### 2. Cannot reopen
```java
// TaskService
public Task update(Long id, String title, String description, boolean done) {
    Task t = get(id);
    if (t.isDone() && !done)
        throw new ConflictException("Task " + id + " is already completed and cannot be reopened");
    if (title != null) t.setTitle(title);
    if (description != null) t.setDescription(description);
    t.setDone(done);
    return repo.save(t);
}
```

### 3. Bad credentials handler (preview)
```java
@ExceptionHandler(BadCredentialsException.class)
public ProblemDetail handleBadCreds(BadCredentialsException ex) {
    ProblemDetail pd = ProblemDetail.forStatus(HttpStatus.UNAUTHORIZED);
    pd.setType(URI.create("https://api.taskforge.com/errors/unauthorized"));
    pd.setTitle("Unauthorized");
    pd.setDetail("Invalid credentials");
    return pd;
}
```
Wired in Module 07.

### 4. Pagination validation
```java
@RestController
@RequestMapping("/api/tasks")
@Validated
public class TaskController {

    @GetMapping
    public List<TaskResponse> list(
        @RequestParam(defaultValue = "0") @Min(0) int page,
        @RequestParam(defaultValue = "20") @Min(1) @Max(200) int size) {
        return service.list(PageRequest.of(page, size, Sort.by("createdAt").descending()))
                      .stream().map(TaskResponse::from).toList();
    }
}
```
A `ConstraintViolationException` is thrown when violated. Handle it in the
advice:
```java
@ExceptionHandler(ConstraintViolationException.class)
public ProblemDetail handleConstraintViolation(ConstraintViolationException ex) {
    var errors = ex.getConstraintViolations().stream()
        .map(v -> Map.of("field", v.getPropertyPath().toString(),
                         "message", v.getMessage())).toList();
    ProblemDetail pd = ProblemDetail.forStatus(HttpStatus.BAD_REQUEST);
    pd.setType(URI.create("https://api.taskforge.com/errors/validation"));
    pd.setTitle("Validation failed");
    pd.setProperty("errors", errors);
    return pd;
}
```

### 5. Localized messages
`src/main/resources/ValidationMessages.properties`:
```
custom.title.required=Please provide a non-empty title
```
DTO:
```java
@NotBlank(message = "{custom.title.required}") String title
```
Restart — the response now says `"message":"Please provide a non-empty title"`.

### 6. Trace-id filter (stretch)
```java
@Component
public class TraceIdFilter extends OncePerRequestFilter {
    @Override
    protected void doFilterInternal(HttpServletRequest req, HttpServletResponse res,
                                    FilterChain chain) throws ServletException, IOException {
        String traceId = Optional.ofNullable(req.getHeader("X-Trace-Id"))
            .orElseGet(() -> java.util.UUID.randomUUID().toString());
        MDC.put("traceId", traceId);
        res.setHeader("X-Trace-Id", traceId);
        try { chain.doFilter(req, res); }
        finally { MDC.remove("traceId"); }
    }
}
```
Every response now carries `X-Trace-Id: <uuid>`, and every log line includes
the same id (configured in Module 09).
