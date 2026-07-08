# Challenge 13 — Reference Solution

### 1. Grouped APIs
```java
@Bean public GroupedOpenApi publicApi()  { return GroupedOpenApi.builder().group("public").pathsToMatch("/api/auth/**", "/actuator/health").build(); }
@Bean public GroupedOpenApi privateApi() { return GroupedOpenApi.builder().group("private").pathsToMatch("/api/tasks/**", "/api/attachments/**").build(); }
```

### 2. TypeScript client
```bash
npm i -g @openapitools/openapi-generator-cli
openapi-generator-cli generate -i http://localhost:8080/v3/api-docs \
  -g typescript-axios -o /tmp/ts-client
```
```ts
// /tmp/ts-client/example.ts
import { Configuration, TasksApi } from "./api";
const cfg = new Configuration({ basePath: "http://localhost:8080",
    accessToken: process.env.TOKEN });
const api = new TasksApi(cfg);
const res = await api.createTask({ createTaskRequest: { title: "from ts" } });
console.log(res.data);
```

### 3. Pin the spec
```java
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
class OpenApiSnapshotIT {
    @LocalServerPort int port;

    @Test
    void specMatchesBaseline() throws Exception {
        var live   = new ObjectMapper().readTree(new URL("http://localhost:" + port + "/v3/api-docs"));
        var base   = new ObjectMapper().readTree(new ClassPathResource("openapi.json").getFile());
        // naive compare; in CI, ignore timestamps + version-only fields
        // Assertions.assertEquals(live, base);
    }
}
```

### 4. Security on controllers
```java
@SecurityRequirement(name = "bearer-jwt")
@RestController
@RequestMapping("/api/tasks")
public class TaskController { ... }

@SecurityRequirements       // empty
@RestController
@RequestMapping("/api/auth")
public class AuthController { ... }
```

### 5. ProblemDetail schema
```java
@Bean
public OpenAPI customize(OpenAPI openApi) {
    openApi.getComponents().addSchemas("ProblemDetail", new Schema<>()
        .type("object")
        .addProperty("type", new StringSchema())
        .addProperty("title", new StringSchema())
        .addProperty("status", new IntegerSchema())
        .addProperty("detail", new StringSchema())
        .addProperty("instance", new StringSchema())
        .addProperty("errors", new ArraySchema().items(new ObjectSchema())));
    return openApi;
}
```
Reference it:
```java
@Schema(implementation = ProblemDetail.class)
```

### 6. Generated server (stretch)
```bash
openapi-generator-cli generate -i http://localhost:8080/v3/api-docs \
  -g spring -o /tmp/server --library=spring-boot
cd /tmp/server && mvn spring-boot:run
```
The stub server starts on `:8080` and implements the same contract — but
with no business logic. Useful for "is this API implementable?" smoke
tests.

> In a real org, the frontend team generates a client from this spec and
> the backend team tests the spec against a generated stub. Mismatches
> surface as build failures, not bug reports.
