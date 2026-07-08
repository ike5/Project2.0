# Challenge 04 — Reference Solution

### 1. Filter by `done`
```java
@GetMapping
public List<TaskResponse> list(@RequestParam(defaultValue = "false") boolean done) {
    return service.list(done).stream().map(TaskResponse::from).toList();
}
```
```java
// TaskService
public List<Task> list(boolean done) {
    return repo.findAll().stream().filter(t -> t.done() == done).toList();
}
```

### 2. Complete endpoint
```java
@PostMapping("/{id}/done")
public TaskResponse complete(@PathVariable Long id) {
    return TaskResponse.from(service.complete(id));
}
```
```java
// TaskService
public Task complete(Long id) { return markDone(id); }
```

### 3. Bulk create
```java
@PostMapping("/bulk")
@ResponseStatus(HttpStatus.CREATED)
public List<TaskResponse> bulkCreate(@RequestBody List<@Valid CreateTaskRequest> reqs) {
    return reqs.stream()
        .map(r -> service.create(r.title(), r.description()))
        .map(TaskResponse::from)
        .toList();
}
```

### 4. Search
```java
@GetMapping("/search")
public List<TaskResponse> search(@RequestParam String q) {
    return service.search(q).stream().map(TaskResponse::from).toList();
}
```
```java
// TaskService
public List<Task> search(String q) {
    String f = q.toLowerCase();
    return repo.findAll().stream()
        .filter(t -> t.title().toLowerCase().contains(f))
        .toList();
}
```

### 5. Custom header — via a `HandlerInterceptor`
```java
@Component
public class AppHeaderInterceptor implements HandlerInterceptor {
    @Override
    public void postHandle(HttpServletRequest req, HttpServletResponse res,
                           Object handler, ModelAndView mav) {
        res.setHeader("X-App-Name", "taskforge");
    }
}

@Configuration
public class WebConfig implements WebMvcConfigurer {
    @Override
    public void addInterceptors(InterceptorRegistry registry) {
        registry.addInterceptor(new AppHeaderInterceptor());
    }
}
```

### 6. Validation handler (stretch)
```java
@RestControllerAdvice
public class ApiExceptionHandler {
    @ExceptionHandler(MethodArgumentNotValidException.class)
    @ResponseStatus(HttpStatus.BAD_REQUEST)
    public Map<String, Object> handle(MethodArgumentNotValidException ex) {
        var errors = ex.getBindingResult().getFieldErrors().stream()
            .map(e -> e.getField() + ": " + e.getDefaultMessage()).toList();
        return Map.of("errors", errors);
    }
}
```
`POST /api/tasks` with `{"title":""}` →
```json
{"errors": ["title: must not be blank"]}
```

> Module 06 turns this into full RFC 7807 problem details. The pattern is
> the same.
