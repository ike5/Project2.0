# Module 04 — REST APIs with Spring MVC

**Goal:** expose the `TaskService` over HTTP — proper request mapping, JSON
serialization, status codes, validation hooks, and a layered architecture
that scales beyond "controller calls repo."

⏱️ ~3 hours · 🎯 Prereq: Modules 02–03 complete (project runs, `TaskService` works).

> This is the module where the app becomes an **API**. From here on, every
> module either adds a new layer (security, persistence, caching) or enriches
> the API (errors, docs, metrics).

---

## 1. The HTTP vocabulary Spring gives you

| Annotation | What it does |
|-----------|--------------|
| `@RestController` | `@Controller` + `@ResponseBody` — return value is serialized to JSON |
| `@RequestMapping("/tasks")` | Class-level URL prefix + common config |
| `@GetMapping`, `@PostMapping`, `@PutMapping`, `@PatchMapping`, `@DeleteMapping` | HTTP method routing |
| `@PathVariable` | A value from the URL path: `/tasks/{id}` |
| `@RequestParam` | A value from the query string: `?done=true` |
| `@RequestBody` | The JSON body, deserialized into a DTO |
| `@RequestHeader` | A value from a header |
| `@ResponseStatus` | Set the HTTP status code of the response |
| `ResponseEntity<T>` | Wrapper with status, headers, and body |

> **Naming tip:** use plural nouns for collections (`/tasks`, `/users`).
> Use the HTTP method to express intent: `GET` reads, `POST` creates,
> `PUT`/`PATCH` updates, `DELETE` removes.

---

## 2. DTOs vs entities

**Critical concept:** the JSON you accept and return is *not* the database
entity. Use **DTOs** (Data Transfer Objects) at the API boundary.

```java
// DTO — what the API sees
public record CreateTaskRequest(String title, String description) {}
public record TaskResponse(Long id, String title, String description, boolean done, Instant createdAt) {}

// Entity — what's stored (Module 05)
@Entity class Task { ... }
```

Why:

1. **Stable API.** You can rename or restructure the entity without
   breaking clients.
2. **Hide internals.** Don't expose password hashes, internal flags, etc.
3. **Validation lives on the DTO** (Module 06).
4. **Different shapes for different calls.** A `CreateTaskRequest` doesn't
   need `id`; a `TaskResponse` doesn't need `password`.

> Records make great DTOs. The Spring/Jackson default constructor + accessor
> naming is record-friendly out of the box.

---

## 3. The full controller — `TaskController`

```java
@RestController
@RequestMapping("/api/tasks")
public class TaskController {

    private final TaskService service;

    public TaskController(TaskService service) {     // constructor injection
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
    public TaskResponse create(@RequestBody @Valid CreateTaskRequest req) {  // @Valid in Module 06
        Task t = service.create(req.title(), req.description());
        return TaskResponse.from(t);
    }

    @PutMapping("/{id}")
    public TaskResponse update(@PathVariable Long id, @RequestBody UpdateTaskRequest req) {
        return TaskResponse.from(service.update(id, req.title(), req.description(), req.done()));
    }

    @DeleteMapping("/{id}")
    @ResponseStatus(HttpStatus.NO_CONTENT)
    public void delete(@PathVariable Long id) {
        service.delete(id);
    }
}
```

**URL → method map:**

| Method | URL | Action |
|--------|-----|--------|
| `GET` | `/api/tasks` | List all tasks |
| `GET` | `/api/tasks/1` | Get task 1 |
| `POST` | `/api/tasks` | Create a task |
| `PUT` | `/api/tasks/1` | Replace task 1 |
| `DELETE` | `/api/tasks/1` | Delete task 1 |

---

## 4. The full service — `TaskService` extensions

The service grows two methods: `update(...)` and the ability to "complete" a
task without losing its id/createdAt.

```java
public Task update(Long id, String title, String description, boolean done) {
    Task existing = get(id);
    return repo.save(new Task(
        existing.id(),
        title != null ? title : existing.title(),
        description != null ? description : existing.description(),
        done,
        existing.createdAt()
    ));
}
```

> **PATCH vs PUT:** `PUT` is "replace the whole resource" (clients send
> every field); `PATCH` is "apply this delta" (clients send only changed
> fields). The code above behaves more like PATCH. That's a common
> simplification; for true PATCH support use JSON Patch or JSON Merge Patch
> (out of scope here).

---

## 5. `ResponseEntity` — when you need more control

`@ResponseStatus` is fine for static codes. For dynamic responses
(different codes, headers, body), use `ResponseEntity`:

```java
@GetMapping("/{id}")
public ResponseEntity<TaskResponse> get(@PathVariable Long id) {
    return service.find(id)                                     // returns Optional
        .map(t -> ResponseEntity.ok(TaskResponse.from(t)))
        .orElseGet(() -> ResponseEntity.notFound().build());
}
```

You can also build a response with a header (e.g. for `Location` after a POST):
```java
@PostMapping
public ResponseEntity<TaskResponse> create(@RequestBody CreateTaskRequest req) {
    Task t = service.create(req.title(), req.description());
    URI location = URI.create("/api/tasks/" + t.id());
    return ResponseEntity.created(location).body(TaskResponse.from(t));
}
```

---

## 6. Request/response bodies — Jackson and the records

Spring Boot includes Jackson. By default it:

- Serializes records to JSON using the accessor names.
- Deserializes JSON into records using the canonical constructor.
- Handles `Instant`, `LocalDate`, `LocalDateTime`, `UUID` with the JDK 8+ module.
- Wraps any deserialization failure in `HttpMessageNotReadableException`.

```json
// request
{ "title": "Buy milk", "description": "2% organic" }
```

```json
// response
{
  "id": 1,
  "title": "Buy milk",
  "description": "2% organic",
  "done": false,
  "createdAt": "2024-01-15T10:30:00Z"
}
```

> **Troubleshooting:** If you see `Java 8 date/time type java.time.Instant
> not supported by default`, add `jackson-datatype-jsr310` (it's included by
> `spring-boot-starter-json`, so this shouldn't happen — if it does, check
> your exclusions).

---

## 7. Content negotiation and produces/consumes

By default Spring serves `application/json` and accepts `application/json`.
You can be explicit:

```java
@RestController
@RequestMapping(value = "/api/tasks", produces = MediaType.APPLICATION_JSON_VALUE)
public class TaskController {

    @PostMapping(consumes = MediaType.APPLICATION_JSON_VALUE)
    public TaskResponse create(@RequestBody CreateTaskRequest req) { ... }
}
```

> **Real APIs are JSON-only.** Don't spend time on XML; every modern client
> expects JSON.

---

## 8. CORS — letting browsers from other origins call you

If a browser at `https://app.example.com` calls `https://api.example.com`,
the browser blocks the request unless you opt in via **CORS headers**:

```java
@Configuration
public class WebConfig implements WebMvcConfigurer {

    @Override
    public void addCorsMappings(CorsRegistry registry) {
        registry.addMapping("/api/**")
            .allowedOrigins("http://localhost:3000")  // dev frontend
            .allowedMethods("GET", "POST", "PUT", "DELETE", "PATCH")
            .allowedHeaders("*")
            .allowCredentials(true);
    }
}
```

For production with Spring Security, configure CORS in the
`SecurityFilterChain` (Module 07) — not in `WebMvcConfigurer`.

---

## 9. The right shape for a real `taskforge` controller

Putting it all together, your `taskforge` API will look like:

```
GET    /api/tasks                    → 200 [TaskResponse, ...]
POST   /api/tasks                    → 201 TaskResponse   (with Location header)
GET    /api/tasks/{id}               → 200 TaskResponse | 404
PUT    /api/tasks/{id}               → 200 TaskResponse | 404
DELETE /api/tasks/{id}               → 204
GET    /api/tasks?done=false         → 200 [...]
```

A request:
```bash
curl -i -X POST localhost:8080/api/tasks \
  -H 'content-type: application/json' \
  -d '{"title":"Buy milk","description":"2%"}'
# → HTTP/1.1 201
#   Location: /api/tasks/1
#   {"id":1,"title":"Buy milk","description":"2%","done":false,"createdAt":"..."}
```

---

## 10. Common pitfalls

| Symptom | Cause | Fix |
|---------|-------|-----|
| `415 Unsupported Media Type` | Missing `Content-Type: application/json` on the request | Add the header |
| `400 Bad Request: Required request body is missing` | The controller expects `@RequestBody` but no body was sent | Send a JSON body, or make it `Optional<>` |
| JSON field is `null` on read but the field is set in code | Jackson can't find a matching property | Use `@JsonProperty` or rename to match |
| `MismatchedInputException: Cannot deserialize` | Type mismatch (e.g. `"abc"` for a `Long`) | Validate input upstream; return 400 (Module 06) |
| Date printed as a timestamp number, not ISO 8601 | Missing `jackson-datatype-jsr310` | Add the dependency (it should be transitively present) |

---

## 11. Do the lab

Build the `TaskController` end-to-end: DTOs, all five CRUD endpoints, proper
status codes, and a quick `curl` smoke test.

👉 **[lab.md](./lab.md)**

Then test yourself: 👉 **[challenge.md](./challenge.md)**

---

## Key terms (see [GLOSSARY](../GLOSSARY.md))

`@RestController` · `@RequestMapping` · `@GetMapping` / `@PostMapping` · `@PathVariable` · `@RequestParam` · `@RequestBody` · `@ResponseStatus` · `ResponseEntity` · DTO · Jackson · content negotiation · CORS

**Next →** [Module 05: Data Access with Spring Data JPA](../05-data-jpa-postgres/)
