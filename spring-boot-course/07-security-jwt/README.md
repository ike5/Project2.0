# Module 07 — Security with Spring Security & JWT

**Goal:** secure the API with **stateless JWT auth** — register, log in, get
a signed token, send it on every request. By the end of this module, every
endpoint is either public (register, login, health) or requires a valid
bearer token, and tasks are scoped to the logged-in user.

⏱️ ~3.5 hours · 🎯 Prereq: Modules 02–06 complete (REST + JPA + validation).

> This is the biggest single module. Take it in two sittings if you need to —
> the security vocabulary alone is dense, and it's worth understanding **why**
> each annotation is there.

---

## 1. The two halves of "security"

- **Authentication** — "who are you?" (login with email + password; prove it
  with a token).
- **Authorization** — "what are you allowed to do?" (only owners can delete
  their tasks; only admins can invite users).

Spring Security handles both via a **filter chain** that runs before your
controllers.

---

## 2. Spring Security 6 — the modern configuration

The pre-Spring-Security-6 style (`WebSecurityConfigurerAdapter`) is **gone**.
The new style uses a bean of type `SecurityFilterChain`:

```java
@Configuration
@EnableWebSecurity
public class SecurityConfig {

    @Bean
    public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        return http
            .csrf(csrf -> csrf.disable())             // stateless JWT APIs
            .sessionManagement(s -> s.sessionCreationPolicy(SessionCreationPolicy.STATELESS))
            .authorizeHttpRequests(auth -> auth
                .requestMatchers("/api/auth/**").permitAll()
                .requestMatchers("/actuator/health").permitAll()
                .anyRequest().authenticated()
            )
            .build();
    }
}
```

> **Why disable CSRF for a JWT API?** CSRF guards against cookie-based
> session attacks. JWTs are sent in the `Authorization` header, not as
> cookies, so CSRF doesn't apply. If you do use cookies, leave CSRF on.

---

## 3. The data model — `AppUser` and `Role`

`V4__create_app_user.sql`:
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

`AppUser.java`:
```java
@Entity @Table(name = "app_user")
public class AppUser {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(unique = true, nullable = false) private String email;
    @Column(unique = true, nullable = false) private String username;
    @Column(name = "password_hash", nullable = false) private String passwordHash;
    @Enumerated(EnumType.STRING)
    @Column(nullable = false) private Role role;
    @Column(name = "created_at", nullable = false, updatable = false) private Instant createdAt;

    protected AppUser() { }
    public AppUser(String email, String username, String passwordHash, Role role) {
        this.email = email; this.username = username; this.passwordHash = passwordHash;
        this.role = role; this.createdAt = Instant.now();
    }
    // getters/setters
}

public enum Role { USER, ADMIN }
```

`AppUserRepository.java`:
```java
public interface AppUserRepository extends JpaRepository<AppUser, Long> {
    Optional<AppUser> findByEmail(String email);
    boolean existsByEmail(String email);
    boolean existsByUsername(String username);
}
```

---

## 4. The password encoder

**Never store passwords in plain text.** Spring Security ships with
`BCryptPasswordEncoder`, the standard choice:

```java
@Bean
public PasswordEncoder passwordEncoder() {
    return new BCryptPasswordEncoder();
}
```

Register a user:
```java
String hash = passwordEncoder.encode(rawPassword);
repo.save(new AppUser(email, username, hash, Role.USER));
```

Verify a login:
```java
if (!passwordEncoder.matches(rawPassword, user.getPasswordHash()))
    throw new BadCredentialsException("invalid credentials");
```

> `BCrypt` is **slow on purpose** — that's the cost an attacker pays to
> brute-force hashes. Always use it; never use `MessageDigest` (SHA-256)
> for passwords.

---

## 5. JWT — JSON Web Tokens

A JWT is a **signed, self-contained** token. The server signs claims
(`sub`, `exp`, `roles`); the client sends it on every request. The server
verifies the signature and reads the claims. **No session needed.**

A JWT has three parts (header, payload, signature) base64-encoded and
dot-separated: `eyJhbGciOi...eyJzdWIiOi...SflKxw...`

```json
// header
{ "alg": "HS256", "typ": "JWT" }
// payload
{ "sub": "42", "email": "ann@example.com", "roles": ["USER"],
  "iat": 1700000000, "exp": 1700003600 }
```

We use **HMAC-SHA256** for the signature: the server holds a secret; the
token is valid only if the signature was made with that secret. For
multi-service setups, use **RSA** or a JWKS endpoint — out of scope here.

---

## 6. The `JwtService` — issue and validate tokens

Add the dependency:
```xml
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

`application.yml`:
```yaml
taskforge:
  security:
    jwt:
      secret: ${JWT_SECRET:dev-only-secret-please-change-me-32-bytes-minimum}
      expiration: PT1H                 # ISO 8601 duration — 1 hour
```

> **The secret must be ≥ 32 bytes for HS256.** In prod, load it from a
> secret manager, not a config file.

`JwtService.java`:
```java
@Service
public class JwtService {

    private final SecretKey key;
    private final Duration expiration;

    public JwtService(TaskforgeProperties props) {
        byte[] secretBytes = props.security().jwt().secret().getBytes(StandardCharsets.UTF_8);
        this.key = Keys.hmacShaKeyFor(secretBytes);
        this.expiration = props.security().jwt().expiration();
    }

    public String issue(AppUser user) {
        Instant now = Instant.now();
        return Jwts.builder()
            .subject(String.valueOf(user.getId()))
            .claim("email", user.getEmail())
            .claim("username", user.getUsername())
            .claim("roles", user.getRole().name())
            .issuedAt(Date.from(now))
            .expiration(Date.from(now.plus(expiration)))
            .signWith(key)
            .compact();
    }

    public Jws<Claims> parse(String token) {
        return Jwts.parser().verifyWith(key).build().parseSignedClaims(token);
    }
}
```

---

## 7. The `AuthController` and `AuthService`

```java
@RestController
@RequestMapping("/api/auth")
public class AuthController {

    private final AuthService auth;
    public AuthController(AuthService auth) { this.auth = auth; }

    @PostMapping("/register")
    @ResponseStatus(HttpStatus.CREATED)
    public AuthResponse register(@RequestBody @Valid RegisterRequest req) {
        return auth.register(req);
    }

    @PostMapping("/login")
    public AuthResponse login(@RequestBody @Valid LoginRequest req) {
        return auth.login(req);
    }
}
```

`AuthResponse`:
```java
public record AuthResponse(String accessToken, String tokenType, long expiresIn, UserResponse user) {
    public static AuthResponse of(String token, Duration exp, AppUser u) {
        return new AuthResponse(token, "Bearer", exp.toSeconds(),
            new UserResponse(u.getId(), u.getEmail(), u.getUsername(), u.getRole().name()));
    }
}
```

`AuthService`:
```java
@Service
public class AuthService {
    private final AppUserRepository users;
    private final PasswordEncoder encoder;
    private final JwtService jwt;

    public AuthService(AppUserRepository users, PasswordEncoder encoder, JwtService jwt) {
        this.users = users; this.encoder = encoder; this.jwt = jwt;
    }

    @Transactional
    public AuthResponse register(RegisterRequest req) {
        if (users.existsByEmail(req.email()))  throw new ConflictException("email already in use");
        if (users.existsByUsername(req.username())) throw new ConflictException("username already in use");
        AppUser u = new AppUser(req.email(), req.username(), encoder.encode(req.password()), Role.USER);
        return AuthResponse.of(jwt.issue(users.save(u)), jwt.expiration(), u);
    }

    @Transactional(readOnly = true)
    public AuthResponse login(LoginRequest req) {
        AppUser u = users.findByEmail(req.email())
            .orElseThrow(() -> new BadCredentialsException("invalid credentials"));
        if (!encoder.matches(req.password(), u.getPasswordHash()))
            throw new BadCredentialsException("invalid credentials");
        return AuthResponse.of(jwt.issue(u), jwt.expiration(), u);
    }
}
```

---

## 8. The JWT filter — every request gets a user

```java
@Component
public class JwtAuthenticationFilter extends OncePerRequestFilter {

    private final JwtService jwt;
    public JwtAuthenticationFilter(JwtService jwt) { this.jwt = jwt; }

    @Override
    protected void doFilterInternal(HttpServletRequest req, HttpServletResponse res,
                                    FilterChain chain) throws ServletException, IOException {
        String header = req.getHeader(HttpHeaders.AUTHORIZATION);
        if (header != null && header.startsWith("Bearer ")) {
            String token = header.substring(7);
            try {
                Claims claims = jwt.parse(token).getPayload();
                Long userId = Long.parseLong(claims.getSubject());
                String email = claims.get("email", String.class);
                String role  = claims.get("roles", String.class);

                var authorities = List.of(new SimpleGrantedAuthority("ROLE_" + role));
                var auth = new UsernamePasswordAuthenticationToken(userId, null, authorities);
                auth.setDetails(email);
                SecurityContextHolder.getContext().setAuthentication(auth);
            } catch (JwtException ex) {
                // invalid token; leave context unauthenticated
            }
        }
        chain.doFilter(req, res);
    }
}
```

Register the filter in the chain:
```java
http.addFilterBefore(jwtFilter, UsernamePasswordAuthenticationFilter.class)
    .exceptionHandling(eh -> eh
        .authenticationEntryPoint((req, res, ex) -> {
            res.setStatus(401);
            res.setContentType("application/problem+json");
            res.getWriter().write("""
                {"type":"https://api.taskforge.com/errors/unauthorized",
                 "title":"Unauthorized","status":401,
                 "detail":"Missing or invalid bearer token"}""");
        })
    );
```

---

## 9. The principal — who is making the request?

Controllers need to know **who** is logged in. Inject the `Authentication`
or use `@AuthenticationPrincipal`:

```java
@GetMapping("/api/tasks/mine")
public List<TaskResponse> mine(Authentication auth) {
    Long userId = (Long) auth.getPrincipal();
    return service.listForUser(userId).stream().map(TaskResponse::from).toList();
}
```

Add to `TaskService`:
```java
@Transactional(readOnly = true)
public List<Task> listForUser(Long userId) {
    return repo.findByOwnerId(userId);    // add this method to the repository
}
```

And to `Task`:
```java
@Column(name = "owner_id") private Long ownerId;
public Long getOwnerId() { return ownerId; }
public void setOwnerId(Long id) { this.ownerId = id; }
```

In `TaskService.create(...)`:
```java
public Task create(String title, String description, Long ownerId) { ... }
    Task t = new Task(title, description);
    t.setOwnerId(ownerId);
    return repo.save(t);
```

---

## 10. Authorization — only the owner can edit

A clean place to enforce "only the owner can edit" is **in the service**:

```java
public Task update(Long id, String title, String description, boolean done, Long requesterId) {
    Task t = get(id);
    if (!Objects.equals(t.getOwnerId(), requesterId))
        throw new ForbiddenException("not your task");
    // ...
}
```

Define `ForbiddenException`:
```java
public class ForbiddenException extends RuntimeException { ... }
```

Handle it in the advice:
```java
@ExceptionHandler(ForbiddenException.class)
public ProblemDetail handleForbidden(ForbiddenException ex) {
    ProblemDetail pd = ProblemDetail.forStatus(HttpStatus.FORBIDDEN);
    pd.setType(URI.create("https://api.taskforge.com/errors/forbidden"));
    pd.setTitle("Forbidden");
    pd.setDetail(ex.getMessage());
    return pd;
}
```

For role-based checks ("only ADMIN can …"), use Spring's expression-based
access control:
```java
@PreAuthorize("hasRole('ADMIN')")
@DeleteMapping("/api/admin/users/{id}")
public void deleteUser(@PathVariable Long id) { ... }
```

Enable with `@EnableMethodSecurity` on the security config.

---

## 11. Refresh tokens (a brief note)

Short-lived access tokens are great for security. Long-lived **refresh
tokens** are how you keep users logged in without re-entering their
password. The flow:

```
POST /api/auth/login   {email,password} → {accessToken, refreshToken}
POST /api/auth/refresh {refreshToken}    → {accessToken, refreshToken}
```

The refresh token is **opaque** (random bytes), stored server-side
(hashed in the DB), and rotated on every use. A stolen refresh token's
useful life is short.

This course uses **access-only** tokens for simplicity; the refresh flow
is a 30-line addition you can make in the challenge.

---

## 12. Common pitfalls

| Symptom | Cause | Fix |
|---------|-------|-----|
| 403 on every authenticated request | Your role is `"USER"` but you're checking `hasRole("user")` | `@PreAuthorize` is case-sensitive on the value; `hasRole("USER")` checks for authority `ROLE_USER` |
| 401 with no `WWW-Authenticate` header | You didn't set an `authenticationEntryPoint` | Add the entry point in the chain |
| `JwtException: signature mismatch` | The secret changed between issuing and verifying | Use the same secret everywhere; rotate via re-issue |
| `ExpiredJwtException` for tokens you just made | Server clock skew between issuer and verifier | `allowedClockSkewSeconds(60)` on the parser |
| `Cannot convert Long to String` in the principal | You set `userId` as a `String` in the JWT but cast to `Long` | Match the types: `.subject(String.valueOf(userId))` ↔ `Long.parseLong(...)` |

---

## 13. Do the lab

Add `AppUser`, JWT issuance/validation, the `JwtAuthenticationFilter`,
register + login endpoints, and ownership-scoped task access. Confirm
unauthenticated requests are rejected and the right user sees their own
tasks.

👉 **[lab.md](./lab.md)**

Then test yourself: 👉 **[challenge.md](./challenge.md)**

---

## Key terms (see [GLOSSARY](../GLOSSARY.md))

Spring Security · `SecurityFilterChain` · authentication · authorization · `Authentication` · `GrantedAuthority` · `PasswordEncoder` · `BCrypt` · JWT · `Jwts.builder()` · `Bearer` token · `SecurityContextHolder` · `OncePerRequestFilter` · `@AuthenticationPrincipal` · `@PreAuthorize` · `hasRole` · refresh token · CSRF · CORS

**Next →** [Module 08: Testing](../08-testing/)
