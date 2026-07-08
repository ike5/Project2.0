# Challenge 07 — Reference Solution

### 1. Refresh tokens
```sql
-- V6__create_refresh_token.sql
CREATE TABLE refresh_token (
    id         BIGSERIAL PRIMARY KEY,
    user_id    BIGINT NOT NULL REFERENCES app_user(id),
    token_hash VARCHAR(128) UNIQUE NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```
```java
@Entity @Table(name = "refresh_token")
public class RefreshToken {
    @Id @GeneratedValue private Long id;
    @Column(name = "user_id") private Long userId;
    @Column(name = "token_hash") private String tokenHash;
    @Column(name = "expires_at") private Instant expiresAt;
    // ...
}
```
```java
// AuthService
public AuthResponse register(RegisterRequest req) {
    AppUser u = /* ... save ... */;
    return AuthResponse.of(jwt.issue(u), issueRefresh(u), jwt.expiration(), u);
}

private String issueRefresh(AppUser u) {
    String raw = UUID.randomUUID().toString();
    String hash = Hashing.sha256().hashString(raw, StandardCharsets.UTF_8).toString();
    refreshRepo.save(new RefreshToken(u.getId(), hash, Instant.now().plus(Duration.ofDays(30))));
    return raw;
}

public AuthResponse refresh(String raw) {
    String hash = Hashing.sha256().hashString(raw, StandardCharsets.UTF_8).toString();
    RefreshToken rt = refreshRepo.findByTokenHash(hash)
        .orElseThrow(() -> new BadCredentialsException("invalid refresh token"));
    if (rt.getExpiresAt().isBefore(Instant.now()))
        throw new BadCredentialsException("refresh token expired");
    refreshRepo.delete(rt);                     // rotate
    AppUser u = users.findById(rt.getUserId()).orElseThrow();
    return AuthResponse.of(jwt.issue(u), issueRefresh(u), jwt.expiration(), u);
}
```

### 2. Logout (denylist stub)
```java
// AuthService
public void logout(String token) {
    var claims = jwt.parse(token).getPayload();
    Instant exp = claims.getExpiration().toInstant();
    denylist.add(token, exp);   // stub: a Map<String, Instant> in memory
}

// JwtAuthenticationFilter — at the top of doFilterInternal:
if (denylist.contains(header.substring(7))) {
    chain.doFilter(req, res);
    return;
}
```

### 3. Role-based admin endpoint
```java
@PreAuthorize("hasRole('ADMIN')")
@DeleteMapping("/api/admin/users/{id}")
@ResponseStatus(HttpStatus.NO_CONTENT)
public void deleteUser(@PathVariable Long id) { /* ... */ }
```
Promote: `UPDATE app_user SET role = 'ADMIN' WHERE username = 'ann';`

### 4. Service-level security
```java
@Service
public class TaskService {
    @PreAuthorize("hasRole('ADMIN') or @taskSecurity.isOwner(#id, principal)")
    public void adminOrOwnerDelete(Long id) { repo.deleteById(id); }
}
```

### 5. Auditor from security context
```java
@Component
public class SpringSecurityAuditorAware implements AuditorAware<String> {
    public Optional<String> getCurrentAuditor() {
        var auth = SecurityContextHolder.getContext().getAuthentication();
        return auth == null ? Optional.empty() : Optional.ofNullable((String) auth.getDetails());
    }
}
```

### 6. Custom `PermissionEvaluator` (stretch)
```java
@Component
public class TaskPermissionEvaluator implements PermissionEvaluator {
    private final TaskRepository repo;
    public TaskPermissionEvaluator(TaskRepository repo) { this.repo = repo; }

    public boolean hasPermission(Authentication auth, Object id, Object targetType, Object permission) {
        if (!"Task".equals(targetType)) return false;
        Long userId = (Long) auth.getPrincipal();
        return repo.findById((Long) id).map(t -> Objects.equals(t.getOwnerId(), userId)).orElse(false);
    }
    public boolean hasPermission(Authentication auth, Serializable id, String type, Object perm) {
        return hasPermission(auth, (Object) id, type, perm);
    }
}
```
```java
@PreAuthorize("hasPermission(#id, 'Task', 'delete')")
@DeleteMapping("/api/tasks/{id}")
public void delete(@PathVariable Long id) { service.delete(id); }
```

> This is the **resource-ownership** pattern used in mature Spring codebases
> — the policy lives in one class, the controllers stay clean.
