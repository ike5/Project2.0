# Module 13 — API Documentation with OpenAPI

**Goal:** generate a live, browsable API spec from your code, and use it as
the contract between your backend and any client. By the end of this
module, `<http://localhost:8080/swagger-ui.html>` documents every endpoint
in your app, with schemas, status codes, and an executable request runner.

⏱️ ~1.5 hours · 🎯 Prereq: Modules 02–12 complete (full app, mostly documented).

> Documentation that lives in code **can't drift** from the code. That's
> the value of `springdoc-openapi` over a hand-maintained wiki.

---

## 1. OpenAPI in one paragraph

**OpenAPI** (formerly Swagger) is a YAML/JSON specification of a REST API:
endpoints, request bodies, response shapes, status codes, auth schemes.
Tools generate docs, client SDKs, server stubs, and tests from it.

**Swagger UI** is the most popular tool for browsing the spec in a browser.
**springdoc-openapi** generates the spec from Spring controllers and serves
the UI at `/swagger-ui.html`.

---

## 2. Add the dependency

`pom.xml`:
```xml
<dependency>
  <groupId>org.springdoc</groupId>
  <artifactId>springdoc-openapi-starter-webmvc-ui</artifactId>
  <version>2.6.0</version>
</dependency>
```

That's it. Spring Boot auto-configures the rest:
- `/v3/api-docs` — the raw spec as JSON.
- `/v3/api-docs.yaml` — same, as YAML.
- `/swagger-ui.html` — the UI.

> **Spring Security gotcha:** the security filter chain (Module 07) blocks
> these by default. Add them to the permit-all list:
> ```java
> .requestMatchers("/v3/api-docs/**", "/swagger-ui/**", "/swagger-ui.html").permitAll()
> ```

---

## 3. The default output

```bash
mvn -q spring-boot:run
open http://localhost:8080/swagger-ui.html
```

You should see every controller in your app: `TaskController`, `AuthController`,
`AttachmentController`, and the actuator endpoints. Click into one to see
its operations, parameters, and response shapes.

The schema for `TaskResponse` is generated from the record's components.

---

## 4. The `OpenAPI` bean — title, version, contact

`src/main/java/com/taskforge/config/OpenApiConfig.java`:
```java
package com.taskforge.config;

import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.info.Contact;
import io.swagger.v3.oas.models.info.Info;
import io.swagger.v3.oas.models.info.License;
import io.swagger.v3.oas.models.servers.Server;
import io.swagger.v3.oas.models.security.SecurityScheme;
import io.swagger.v3.oas.models.Components;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import java.util.List;

@Configuration
public class OpenApiConfig {

    @Bean
    public OpenAPI taskforgeOpenApi() {
        return new OpenAPI()
            .info(new Info()
                .title("taskforge API")
                .version("v1")
                .description("Task tracker backend — auth, tasks, attachments, events.")
                .contact(new Contact().name("taskforge team").email("dev@taskforge.com"))
                .license(new License().name("MIT")))
            .servers(List.of(
                new Server().url("http://localhost:8080").description("local dev"),
                new Server().url("https://api.taskforge.com").description("prod")))
            .components(new Components()
                .addSecuritySchemes("bearer-jwt",
                    new SecurityScheme()
                        .type(SecurityScheme.Type.HTTP)
                        .scheme("bearer")
                        .bearerFormat("JWT")));
    }
}
```

Reload the UI — the title, version, servers, and a "bearer-jwt" auth
scheme appear at the top.

---

## 5. Documenting endpoints

The UI is already usable without annotations — the spec is generated from
the controller method signatures. Annotations make it **better**.

### 5.1 Class-level

```java
@Tag(name = "Tasks", description = "CRUD operations on tasks")
@RestController
@RequestMapping("/api/tasks")
public class TaskController { ... }
```

### 5.2 Method-level

```java
@Operation(
    summary = "Create a task",
    description = "Creates a new task owned by the authenticated user."
)
@ApiResponses({
    @ApiResponse(responseCode = "201", description = "Task created",
                 content = @Content(schema = @Schema(implementation = TaskResponse.class))),
    @ApiResponse(responseCode = "400", description = "Validation failed",
                 content = @Content(schema = @Schema(implementation = ProblemDetail.class))),
    @ApiResponse(responseCode = "401", description = "Missing or invalid token")
})
@PostMapping
public ResponseEntity<TaskResponse> create(
    @Parameter(description = "Task to create") @RequestBody @Valid CreateTaskRequest req,
    Authentication auth) { ... }
```

### 5.3 Fields

```java
public record CreateTaskRequest(
    @Schema(description = "Short title of the task", example = "Buy milk", maxLength = 200)
    @NotBlank @Size(max = 200) String title,

    @Schema(description = "Optional longer description", example = "2% organic")
    @Size(max = 2000) String description,

    @Schema(description = "Priority level", allowableValues = {"low", "medium", "high"})
    @Pattern(regexp = "low|medium|high") String priority
) {}
```

### 5.4 Errors

Register `ProblemDetail` (Module 06) globally so every error response
references it:
```java
@Bean
public OpenAPI customize(OpenAPI openApi) {
    return openApi.components(new Components()
        .addSchemas("ProblemDetail", new io.swagger.v3.oas.models.media.Schema<>()
            .type("object")
            .addProperty("type", new StringSchema().example("https://api.taskforge.com/errors/validation"))
            .addProperty("title", new StringSchema().example("Validation failed"))
            .addProperty("status", new IntegerSchema().example(400))
            .addProperty("detail", new StringSchema().example("One or more fields are invalid."))
            .addProperty("instance", new StringSchema().example("/api/tasks"))
            .addProperty("errors", new ArraySchema().items(new ObjectSchema()))));
}
```

> Or use `@Schema(name = "ProblemDetail")` on a record that mirrors the
> Spring type, and reference it from `@ApiResponse`.

---

## 6. The "Authorize" button — JWT in the UI

Click "Authorize" at the top of Swagger UI. The bearer scheme prompts for
a token. Paste your access token; the UI sends it on every "Try it out"
request.

```
Authorize
  bearer-jwt  [ ____________________ ] [Authorize]
              eyJhbGciOiJIUzI1NiJ9....
```

This is wired automatically by the `addSecuritySchemes("bearer-jwt", ...)`
in §4.

---

## 7. Grouping endpoints — `@Tag` and group configurations

```java
@Bean
public GroupedOpenApi publicApi() {
    return GroupedOpenApi.builder()
        .group("public")
        .pathsToMatch("/api/auth/**", "/actuator/health")
        .build();
}

@Bean
public GroupedOpenApi privateApi() {
    return GroupedOpenApi.builder()
        .group("private")
        .pathsToMatch("/api/tasks/**", "/api/attachments/**")
        .build();
}
```

The UI gets a dropdown to switch between groups. Useful for large APIs.

---

## 8. Generating clients

The raw spec at `/v3/api-docs` is the contract. From it, generate clients
in any language:

```bash
# TypeScript
npx @openapitools/openapi-generator-cli generate \
  -i http://localhost:8080/v3/api-docs \
  -g typescript-axios \
  -o src/api/client

# Python
openapi-generator-cli generate \
  -i http://localhost:8080/v3/api-docs \
  -g python \
  -o ./sdk

# Java
openapi-generator-cli generate \
  -i http://localhost:8080/v3/api-docs \
  -g java \
  -o ./sdk --library=webclient
```

The generated SDK is a typed client — the compiler enforces that you pass
the right types. **This is how large orgs keep frontend and backend in
sync without manual coordination.**

---

## 9. Documenting security — the right way

```java
@SecurityRequirement(name = "bearer-jwt")    // class or method level
@RestController
@RequestMapping("/api/tasks")
public class TaskController { ... }
```

Now every operation in `TaskController` shows a padlock and the "Bearer"
auth requirement. The "Authorize" button in the UI sends the token.

For public endpoints:
```java
@SecurityRequirements       // clears the inherited security
@PostMapping("/api/auth/login")
public AuthResponse login(...) { ... }
```

---

## 10. The spec is a test

Pin the spec in CI:

```bash
# Save today's spec
curl -s localhost:8080/v3/api-docs > expected.json

# Tomorrow, diff
curl -s localhost:8080/v3/api-docs > actual.json
diff expected.json actual.json
```

Any change to the API shows up in the diff. **The CI job fails on
unintended changes; the PR review forces you to acknowledge them.**

For real enforcement, generate client code in CI and run its tests
against the live server.

---

## 11. Common pitfalls

| Symptom | Cause | Fix |
|---------|-------|-----|
| `404` on `/swagger-ui.html` | springdoc not on the classpath | Add the dependency |
| `401` on `/v3/api-docs` | Spring Security blocks it | Add to `permitAll()` |
| Schemas are missing fields | Records: springdoc may not see records on older versions | Upgrade to 2.x; records are supported |
| `Try it out` sends no token | You didn't set the security scheme | Add `bearer-jwt` to `components.securitySchemes` and `@SecurityRequirement` |
| Generated client has wrong types | DTOs lack `@Schema` hints | Add `@Schema(example = "...")` for string formats and example values |
| Spec is enormous | No grouping | Add `GroupedOpenApi` beans |

---

## 12. Do the lab

Add the dependency, customize the OpenAPI bean, document a couple of
endpoints, and explore the Swagger UI.

👉 **[lab.md](./lab.md)**

Then test yourself: 👉 **[challenge.md](./challenge.md)**

---

## Key terms (see [GLOSSARY](../GLOSSARY.md))

OpenAPI · Swagger UI · springdoc-openapi · `OpenAPI` bean · `@Tag` · `@Operation` · `@ApiResponse` · `@Schema` · `@SecurityRequirement` · `GroupedOpenApi` · `bearer-jwt` security scheme · `/v3/api-docs`

**Next →** [Module 14: Containerizing with Docker & Docker Compose](../14-docker-compose/)
