# Cheatsheet — Spring Security + JWT

Quick reference for the security layer. Keep it open while you build.

## Modern `SecurityFilterChain` (Spring Security 6+)

```java
@Bean
public SecurityFilterChain filterChain(HttpSecurity http, JwtAuthFilter jwt) throws Exception {
    return http
        .csrf(csrf -> csrf.disable())                          // stateless JWT APIs
        .cors(cors -> {})                                       // CORS config (see below)
        .sessionManagement(s -> s.sessionCreationPolicy(SessionCreationPolicy.STATELESS))
        .authorizeHttpRequests(auth -> auth
            .requestMatchers("/api/auth/**").permitAll()
            .requestMatchers("/actuator/health", "/actuator/info",
                             "/v3/api-docs/**", "/swagger-ui/**").permitAll()
            .anyRequest().authenticated())
        .addFilterBefore(jwt, UsernamePasswordAuthenticationFilter.class)
        .exceptionHandling(eh -> eh.authenticationEntryPoint((req, res, ex) -> {
            res.setStatus(401);
            res.setContentType("application/problem+json");
            res.getWriter().write("""
                {"type":".../unauthorized","title":"Unauthorized","status":401,
                 "detail":"Missing or invalid bearer token"}""");
        }))
        .build();
}
```

## Password encoding

```java
@Bean
public PasswordEncoder passwordEncoder() { return new BCryptPasswordEncoder(); }

String hash = encoder.encode(raw);
boolean ok = encoder.matches(raw, hash);
```

## JWT issue + parse (jjwt 0.12.x)

```java
@Service
public class JwtService {
    private final SecretKey key;
    private final Duration expiration;

    public JwtService(TaskforgeProperties props) {
        byte[] bytes = props.security().jwt().secret().getBytes(StandardCharsets.UTF_8);
        this.key = Keys.hmacShaKeyFor(bytes);     // HS256 needs ≥ 32 bytes
        this.expiration = props.security().jwt().expiration();
    }

    public String issue(AppUser u) {
        Instant now = Instant.now();
        return Jwts.builder()
            .subject(String.valueOf(u.getId()))
            .claim("email", u.getEmail())
            .claim("roles", u.getRole().name())
            .issuedAt(Date.from(now))
            .expiration(Date.from(now.plus(expiration)))
            .signWith(key)
            .compact();
    }

    public Claims parse(String token) {
        return Jwts.parser().verifyWith(key).build()
            .parseSignedClaims(token).getPayload();
    }
}
```

## JWT filter

```java
@Component
public class JwtAuthFilter extends OncePerRequestFilter {
    private final JwtService jwt;
    public JwtAuthFilter(JwtService jwt) { this.jwt = jwt; }

    @Override
    protected void doFilterInternal(HttpServletRequest req, HttpServletResponse res, FilterChain chain)
            throws ServletException, IOException {
        String header = req.getHeader(HttpHeaders.AUTHORIZATION);
        if (header != null && header.startsWith("Bearer ")) {
            try {
                Claims c = jwt.parse(header.substring(7));
                Long userId = Long.parseLong(c.getSubject());
                String role = c.get("roles", String.class);
                var auth = new UsernamePasswordAuthenticationToken(
                    userId, null, List.of(new SimpleGrantedAuthority("ROLE_" + role)));
                auth.setDetails(c.get("email", String.class));
                SecurityContextHolder.getContext().setAuthentication(auth);
            } catch (JwtException ex) { /* leave unauthenticated */ }
        }
        chain.doFilter(req, res);
    }
}
```

## CORS

```java
@Bean
public CorsConfigurationSource cors() {
    var cfg = new CorsConfiguration();
    cfg.setAllowedOrigins(List.of("http://localhost:3000"));
    cfg.setAllowedMethods(List.of("GET","POST","PUT","PATCH","DELETE"));
    cfg.setAllowedHeaders(List.of("*"));
    cfg.setAllowCredentials(true);
    var src = new UrlBasedCorsConfigurationSource();
    src.registerCorsConfiguration("/api/**", cfg);
    return src;
}
```

## Method security

```java
@EnableMethodSecurity
@Configuration
public class MethodSecurityConfig {}

@PreAuthorize("hasRole('ADMIN')")
@DeleteMapping("/api/admin/users/{id}")
public void deleteUser(@PathVariable Long id) { ... }

@PreAuthorize("hasRole('ADMIN') or @taskSecurity.isOwner(#id, principal)")
public void delete(Long id) { ... }
```

## `@AuthenticationPrincipal` / `Authentication` in controllers

```java
@GetMapping("/api/tasks/mine")
public List<TaskResponse> mine(Authentication auth) {
    Long userId = (Long) auth.getPrincipal();
    return service.listForUser(userId).stream().map(TaskResponse::from).toList();
}
```

## Application properties

```yaml
spring:
  security:
    user: { name: admin, password: changeme }   # only if you DON'T override

taskforge:
  security:
    jwt:
      secret: ${JWT_SECRET:dev-only-secret-please-change-me-32-bytes-min}
      expiration: PT1H
```

## Authorization cheat sheet

| Expression | Meaning |
|-----------|---------|
| `hasRole('ADMIN')` | User has authority `ROLE_ADMIN` |
| `hasAnyRole('ADMIN','USER')` | Either |
| `hasAuthority('SCOPE_read')` | OAuth2 scope |
| `isAuthenticated()` | Logged in (any way) |
| `isAnonymous()` | Not logged in |
| `permitAll` / `denyAll` | Always / never |
| `@bean.method(args)` | Custom bean (SpEL) |

## Common pitfalls

- **CSRF on a JWT API** — leave it disabled (no cookies).
- **Forgetting `STATELESS` session policy** — Spring will create an
  HTTP session by default. The JWT filter will set the context, but the
  session is wasted.
- **`hasRole` vs `hasAuthority`** — `hasRole('ADMIN')` checks for the
  authority `ROLE_ADMIN`; `hasAuthority('ADMIN')` checks for the
  authority `ADMIN`. Match the right one.
- **JWT secret < 32 bytes** — `Keys.hmacShaKeyFor` throws at startup.
- **Clock skew** — if the issuer and verifier are on different machines
  with skewed clocks, set `Jwts.parser().clockSkewSeconds(60)`.
- **Returning a stack trace** — add a fallback `@ExceptionHandler(Exception.class)`
  in your advice that logs server-side and returns a sanitized
  problem detail.
