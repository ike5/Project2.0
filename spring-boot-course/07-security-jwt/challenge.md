# Challenge 07 — Lock It Down

No step-by-step this time. Use what you learned. Reference solutions are in
[`solutions/`](./solutions/) — try first!

## Tasks

1. **Refresh tokens.** Issue a refresh token alongside the access token. Add
   `POST /api/auth/refresh` that accepts the refresh token and returns a new
   access token (and a rotated refresh token). Store refresh tokens hashed
   in a new `refresh_token` table with `(user_id, token_hash, expires_at)`.

2. **Logout.** `POST /api/auth/logout` — accept the access token, add its
   `jti` to a Redis denylist with TTL = remaining lifetime, and reject it
   in the filter. (Module 10 sets up Redis; for now, just stub the storage.)

3. **Role-based endpoint.** Add `DELETE /api/admin/users/{id}` that's only
   accessible to users with `role = ADMIN`. Annotate with
   `@PreAuthorize("hasRole('ADMIN')")`. Manually promote a user to `ADMIN`
   in psql and verify the endpoint works for them and `403`s for others.

4. **Method-level security on a service.** Use `@PreAuthorize` on a service
   method to require `hasRole('ADMIN')` for "delete any task." Wire it into
   the controller.

5. **Audit field from the security context.** Wire `AuditorAware<String>`
   so `@CreatedBy` is filled in with the current user's email. Verify in
   psql that a created task has the right `created_by`.

6. **Stretch:** Add a `PermissionEvaluator` that checks
   `hasPermission(#id, 'Task', 'delete')` — i.e. only the owner can delete
   a task. Use it in `@PreAuthorize("hasPermission(#id, 'Task', 'delete')")`.

## Success criteria

- [ ] `POST /api/auth/refresh` issues a new access token.
- [ ] `POST /api/auth/logout` revokes the token until expiry.
- [ ] `DELETE /api/admin/users/{id}` works for ADMIN, 403s for USER.
- [ ] `@PreAuthorize` on a service method is honored.
- [ ] `@CreatedBy` is set from the security context.
- [ ] Stretch: a custom `PermissionEvaluator` enforces ownership.
