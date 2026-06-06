# Challenge 03 — Lock It Down

No step-by-step this time. Use what you learned. Reference solutions are in
[`solutions/`](./solutions/) — try first!

## Tasks

1. **Shorten the access lifetime.** Change the access token to live **2 minutes**,
   log in, wait it out, and confirm a call to `/api/auth/me/` then returns `401`
   while a refresh still mints a working new access token.

2. **Add a write permission class.** Create a permission `IsSelf` so that
   `PATCH /api/auth/me/` can only ever edit the requesting user (it already does via
   `get_object`, but prove it by attempting to change another field like `id` and
   seeing it ignored as read-only).

3. **Protect a throwaway endpoint by role.** Add a temporary view
   `GET /api/auth/admin-ping/` that returns `{"pong": true}` **only** to staff users
   (`is_staff`), and `403` otherwise. Use a DRF permission to enforce it.

4. **Brute-force defense.** Lower the anon throttle to `5/min`, then hit the login
   endpoint 6 times quickly with a wrong password and observe the `429 Too Many
   Requests` response.

5. **Stretch:** In two sentences, explain why we store the refresh token's
   *blacklist* in the database but verify access tokens with *only* a signature
   check — and what that means for "instant logout" of an access token.

## Success criteria
- [ ] A 2-minute access token expires and is refused; refresh still works.
- [ ] `PATCH /me/` cannot change read-only fields.
- [ ] A staff-only endpoint returns `200` for staff, `403` for others.
- [ ] Repeated bad logins trigger `429`.
- [ ] You can explain the signature-vs-blacklist trade-off.
