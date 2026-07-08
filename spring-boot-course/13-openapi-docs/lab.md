# Lab 13 — Live API Docs with Swagger UI

**You'll:** add `springdoc-openapi`, customize the OpenAPI bean, document a
couple of endpoints, and explore the spec.

⏱️ ~30 min. Run from `spring-boot-course/apps/taskforge`.

---

## Part A — Add the dependency

`pom.xml`:
```xml
<dependency>
  <groupId>org.springdoc</groupId>
  <artifactId>springdoc-openapi-starter-webmvc-ui</artifactId>
  <version>2.6.0</version>
</dependency>
```

Add the public paths to `SecurityConfig`:
```java
.requestMatchers("/v3/api-docs/**", "/swagger-ui/**", "/swagger-ui.html").permitAll()
```

---

## Part B — Customize the OpenAPI bean

Create `src/main/java/com/taskforge/config/OpenApiConfig.java` from the
README §4.

Run:
```bash
mvn -q spring-boot:run
open http://localhost:8080/swagger-ui.html
```

✅ The title says "taskforge API", the version is "v1", and there's a
padlock icon for the "bearer-jwt" security scheme.

---

## Part C — Document the controllers

Add to `TaskController`:
```java
@Tag(name = "Tasks", description = "CRUD operations on tasks")
@RestController
@RequestMapping("/api/tasks")
public class TaskController { ... }
```

Add to the `create` method:
```java
@Operation(
    summary = "Create a task",
    description = "Creates a new task owned by the authenticated user."
)
@ApiResponses({
    @ApiResponse(responseCode = "201", description = "Task created",
                 content = @Content(schema = @Schema(implementation = TaskResponse.class))),
    @ApiResponse(responseCode = "400", description = "Validation failed",
                 content = @Content(mediaType = "application/problem+json",
                                    schema = @Schema(implementation = ProblemDetail.class))),
    @ApiResponse(responseCode = "401", description = "Missing or invalid token")
})
@SecurityRequirement(name = "bearer-jwt")
@PostMapping
public ResponseEntity<TaskResponse> create(...) { ... }
```

Add to the request DTOs:
```java
public record CreateTaskRequest(
    @Schema(description = "Short title", example = "Buy milk", maxLength = 200)
    @NotBlank @Size(max = 200) String title,

    @Schema(description = "Optional longer description", example = "2% organic")
    @Size(max = 2000) String description,

    @Schema(description = "Priority", allowableValues = {"low", "medium", "high"})
    @Pattern(regexp = "low|medium|high") String priority
) {}
```

Reload the UI: the `Tasks` section now has rich descriptions, examples,
and a "Try it out" button that sends the request for real.

---

## Part D — Authorize and try it

1. Click **Authorize** at the top.
2. Paste a token from `POST /api/auth/login` (use curl, copy from the
   response).
3. Open `POST /api/tasks`, click **Try it out**, edit the JSON, click
   **Execute**.

The UI sends the request with the bearer token and shows the actual
response.

---

## What you learned

- `springdoc-openapi` generates the OpenAPI spec from your controllers;
  no separate spec file to maintain.
- A `OpenAPI` bean sets the title, version, contact, servers, and auth
  scheme.
- `@Operation`, `@ApiResponse`, `@Schema`, `@Tag`, `@SecurityRequirement`
  enrich the spec with descriptions, examples, and the right error
  shapes.
- The Swagger UI is a live API explorer: "Try it out" issues real
  requests with your bearer token.

➡️ Now try the **[challenge](./challenge.md)**, then move to
[Module 14](../14-docker-compose/).
