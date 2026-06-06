# Challenge 09 — Harden the Client

No step-by-step this time. Use what you learned. Reference solutions are in
[`solutions/`](./solutions/) — try first!

## Tasks

1. **Avoid the refresh stampede.** If ten requests `401` at once, `apiFetch` could
   fire ten refreshes. Make it dedupe: while a refresh is in flight, queued callers
   await the *same* refresh promise. Implement it.

2. **A `useUser` hook.** Create a hook that fetches `/api/auth/me/` once, caches it,
   and exposes `{ user, loading }` so any component can show the current user without
   refetching.

3. **Friendly errors.** When login fails, show the backend's actual error message
   (e.g. throttled → "Too many attempts, try later") by reading `ApiError.body`
   instead of a generic string.

4. **Workspace switcher.** Add a small dropdown in the sidebar header listing the
   user's workspaces (`GET /api/workspaces/`) that navigates to `/w/:id` on select.

5. **Stretch:** Explain what breaks if you store the access token in a normal
   (non-httpOnly) cookie versus localStorage, with respect to CSRF and XSS — and why
   neither is a silver bullet.

## Success criteria
- [ ] Concurrent 401s trigger exactly one refresh.
- [ ] `useUser` returns the cached current user.
- [ ] Login surfaces the real backend error.
- [ ] A workspace switcher navigates between workspaces.
- [ ] You can compare cookie vs localStorage token storage.
