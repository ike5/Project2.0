# Lab 07 — Lock Down the API with JWT

**You'll:** add `AppUser`, register/login endpoints, a `JwtAuthenticationFilter`,
and ownership-scoped task access. By the end, `/api/tasks/**` requires a
valid bearer token and users only see their own tasks.

⏱️ ~80 min. Run from `spring-boot-course/apps/taskforge`.

---

## Part A — Dependencies and config

Add to `pom.xml`:
```xml
<dependency>
  <groupId>org.springframework.boot</groupId>
  <artifactId>spring-boot-starter-security</artifactId>
</dependency>
<dependency>
  <groupId>io.jsonwebtoken</groupId>
  <artifactId>jjwt-api</artifactId>
  <version>0.12.6</version>
</dependency>
<dependency>
  <groupId>io.jsonwebtoken</groupId>
  <artifactId>jjwt-impl</artifactId>
  <version>0.12.6</version>
  <scope>runtime</scope>
</dependency>
<dependency>
  <groupId>io.jsonwebtoken</groupId>
  <artifactId>jjwt-jackson</artifactId>
  <version>0.12.6</version>
  <scope>runtime</scope>
</dependency>
```

Extend `TaskforgeProperties`:
```java
public record TaskforgeProperties(Security security, Pagination pagination) {
    public record Security(Jwt jwt) {
        public record Jwt(String secret, Duration expiration) {}
    }
    public record Pagination(int defaultPageSize, int maxPageSize) {}
}
```

`application.yml`:
```yaml
taskforge:
  security:
    jwt:
      secret: dev-only-secret-please-change-me-32-bytes-minimum-secret
      expiration: PT1H
  pagination:
    default-page-size: 20
    max-page-size: 200
```

---

## Part B — Flyway: create `app_user`

`src/main/resources/db/migration/V4__create_app_user.sql`:
```sql
CREATE TABLE app_user (
    id            BIGSERIAL PRIMARY KEY,
    email         VARCHAR(254) UNIQUE NOT NULL,
    username      VARCHAR(50)  UNIQUE NOT NULL,
    password_hash VARCHAR(100) NOT NULL,
    role          VARCHAR(20)  NOT NULL DEFAULT 'USER',
    created_at    TIMESTAMPTZ  NOT NULL DEFAULT now()
);
```

Create the entity, enum, and repository (see README §3). The
`AppUserRepository` has `findByEmail`, `existsByEmail`, `existsByUsername`.

---

## Part C — `JwtService`, `PasswordEncoder`, `AuthService`

Create all three classes from the README (§§4, 6, 7). The `JwtService`
takes a `TaskforgeProperties` and exposes:

```java
public String issue(AppUser user);
public Jws<Claims> parse(String token);
public Duration expiration();   // for the response
```

---

## Part D — `SecurityConfig` and the JWT filter

`src/main/java/com/taskforge/security/SecurityConfig.java`:
```java
@Configuration
@EnableWebSecurity
@EnableMethodSecurity
public class SecurityConfig {

    private final JwtAuthenticationFilter jwtFilter;

    public SecurityConfig(JwtAuthenticationFilter jwtFilter) { this.jwtFilter = jwtFilter; }

    @Bean
    public PasswordEncoder passwordEncoder() { return new BCryptPasswordEncoder(); }

    @Bean
    public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        return http
            .csrf(csrf -> csrf.disable())
            .cors(cors -> {})   // accept default config for now
            .sessionManagement(s -> s.sessionCreationPolicy(SessionCreationPolicy.STATELESS))
            .authorizeHttpRequests(auth -> auth
                .requestMatchers("/api/auth/**").permitAll()
                .requestMatchers("/actuator/health", "/actuator/info").permitAll()
                .anyRequest().authenticated()
            )
            .addFilterBefore(jwtFilter, UsernamePasswordAuthenticationFilter.class)
            .exceptionHandling(eh -> eh.authenticationEntryPoint((req, res, ex) -> {
                res.setStatus(401);
                res.setContentType("application/problem+json");
                res.getWriter().write("""
                    {"type":"https://api.taskforge.com/errors/unauthorized",
                     "title":"Unauthorized","status":401,
                     "detail":"Missing or invalid bearer token"}""");
            }))
            .build();
    }
}
```

`src/main/java/com/taskforge/security/JwtAuthenticationFilter.java`:
(see README §8)

---

## Part E — Auth controller

`src/main/java/com/taskforge/auth/AuthController.java`:
```java
@RestController
@RequestMapping("/api/auth")
public class AuthController {

    private final AuthService auth;
    public AuthController(AuthService auth) { this.auth = auth; }

    @PostMapping("/register")
    @ResponseStatus(HttpStatus.CREATED)
    public AuthResponse register(@RequestBody @Valid RegisterRequest req) { return auth.register(req); }

    @PostMapping("/login")
    public AuthResponse login(@RequestBody @Valid LoginRequest req) { return auth.login(req); }
}
```

DTOs:
```java
public record RegisterRequest(
    @NotBlank @Email String email,
    @NotBlank @Size(min = 3, max = 50) String username,
    @NotBlank @Size(min = 8, max = 100) String password
) {}

public record LoginRequest(
    @NotBlank @Email String email,
    @NotBlank String password
) {}
```

---

## Part F — Add `ownerId` to `Task` and ownership-scoped endpoints

`V5__add_task_owner.sql`:
```sql
ALTER TABLE task ADD COLUMN owner_id BIGINT REFERENCES app_user(id);
CREATE INDEX idx_task_owner ON task(owner_id);
```

`Task`:
```java
@Column(name = "owner_id") private Long ownerId;
public Long getOwnerId() { return ownerId; }
public void setOwnerId(Long id) { this.ownerId = id; }
```

`TaskRepository`:
```java
List<Task> findByOwnerId(Long ownerId);
```

`TaskService`:
```java
public Task create(String title, String description, Long ownerId) {
    if (title == null || title.isBlank()) throw new IllegalArgumentException("title is required");
    Task t = new Task(title.trim(), description);
    t.setOwnerId(ownerId);
    return repo.save(t);
}

public List<Task> listForUser(Long ownerId) { return repo.findByOwnerId(ownerId); }

public Task update(Long id, String title, String description, boolean done, Long requesterId) {
    Task t = get(id);
    if (!Objects.equals(t.getOwnerId(), requesterId))
        throw new ForbiddenException("not your task");
    if (title != null) t.setTitle(title);
    if (description != null) t.setDescription(description);
    t.setDone(done);
    return repo.save(t);
}
```

`TaskController`:
```java
private final TaskService service;
public TaskController(TaskService service) { this.service = service; }

@PostMapping
public ResponseEntity<TaskResponse> create(@RequestBody @Valid CreateTaskRequest req,
                                            Authentication auth) {
    Long userId = (Long) auth.getPrincipal();
    Task t = service.create(req.title(), req.description(), userId);
    return ResponseEntity.created(URI.create("/api/tasks/" + t.getId()))
                          .body(TaskResponse.from(t));
}

@GetMapping
public List<TaskResponse> list(Authentication auth) {
    Long userId = (Long) auth.getPrincipal();
    return service.listForUser(userId).stream().map(TaskResponse::from).toList();
}

@PutMapping("/{id}")
public TaskResponse update(@PathVariable Long id, @RequestBody UpdateTaskRequest req,
                           Authentication auth) {
    Long userId = (Long) auth.getPrincipal();
    return TaskResponse.from(service.update(id, req.title(), req.description(),
        req.done() != null && req.done(), userId));
}
```

Define `ForbiddenException` and add the handler in `ApiExceptionHandler`.

---

## Part G — Run and verify

```bash
mvn -q spring-boot:run
```

**1. Register:**
```bash
curl -s -X POST localhost:8080/api/auth/register \
  -H 'content-type: application/json' \
  -d '{"email":"ann@example.com","username":"ann","password":"password123"}'
# → {"accessToken":"eyJhbGci...","tokenType":"Bearer","expiresIn":3600,"user":{...}}
```

**2. Use the token:**
```bash
TOKEN=$(curl -s -X POST localhost:8080/api/auth/login \
  -H 'content-type: application/json' \
  -d '{"email":"ann@example.com","password":"password123"}' | jq -r .accessToken)

curl -s -H "Authorization: Bearer $TOKEN" -X POST localhost:8080/api/tasks \
  -H 'content-type: application/json' \
  -d '{"title":"my first task"}'

curl -s -H "Authorization: Bearer $TOKEN" localhost:8080/api/tasks
# → only the tasks owned by ann
```

**3. Unauthenticated request:**
```bash
curl -s -i localhost:8080/api/tasks
# → HTTP/1.1 401
#   Content-Type: application/problem+json
#   {"type":".../unauthorized", ...}
```

**4. Cross-user edit:**
```bash
# Register a second user
TOKEN2=$(curl -s -X POST localhost:8080/api/auth/register \
  -H 'content-type: application/json' \
  -d '{"email":"bob@example.com","username":"bob","password":"password123"}' | jq -r .accessToken)

# Bob tries to edit ann's task 1
curl -s -i -H "Authorization: Bearer $TOKEN2" -X PUT localhost:8080/api/tasks/1 \
  -H 'content-type: application/json' -d '{"title":"hacked"}'
# → HTTP/1.1 403
```

✅ **Checkpoint:** the API is locked down, users see only their data, and the
error contract is consistent for `401` and `403`.

---

## What you learned

- `SecurityFilterChain` is the modern way to configure Spring Security.
- BCrypt is the right password encoder — never SHA-256.
- JWTs are signed, self-contained, and stateless — no server session.
- A `OncePerRequestFilter` reads the `Authorization: Bearer …` header and
  sets the `SecurityContext` for downstream code.
- Service-layer authorization ("is this the owner?") is simpler and more
  testable than annotation-based checks for resource ownership.
- `ProblemDetail` covers `401` and `403` cleanly via the entry point and
  the advice.

➡️ Now try the **[challenge](./challenge.md)**, then move to
[Module 08](../08-testing/).
