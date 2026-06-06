# Module 03 — Authentication with SimpleJWT

**Goal:** let users register and log in, issue short-lived access tokens + rotating
refresh tokens, and enforce workspace-scoped permissions on every request.

⏱️ ~2.5 hours · 🎯 Prereq: Module 02 (backend boots, migrations applied).

> Auth is where security lives or dies. We use JSON Web Tokens because the API is
> consumed by a separate Next.js app (and, one day, a phone app) — stateless tokens
> beat server-side sessions for that.

---

## 1. Why JWT here (and the trade-offs)

A **JWT** is a signed token the client sends on every request (`Authorization:
Bearer <token>`). The server verifies the signature — no database lookup — so it
scales across many backend Pods without shared session storage.

The catch: you can't instantly "log out" a signed token. We mitigate that with the
**access/refresh split**.

## 2. Access vs refresh tokens

```
 login ──► access  (15 min, sent on every request)
       └─► refresh (7 days, used ONLY to get a new access token)
```

- The **access token** is short-lived, so a leaked one expires fast.
- The **refresh token** is long-lived but used rarely (only at `/api/auth/refresh/`),
  so it's exposed less.

## 3. Rotation + blacklist (the important part)

We set `ROTATE_REFRESH_TOKENS` and `BLACKLIST_AFTER_ROTATION`. Each time a client
refreshes, it gets a **brand-new** refresh token and the old one is **blacklisted**.
Consequences:

- A stolen refresh token is useful only until the real user next refreshes (then it's
  dead).
- **Logout** = blacklist the current refresh token (`/api/auth/logout/`).
- This requires the `token_blacklist` app and its tables (already in `INSTALLED_APPS`).

## 4. Email-based login

Because `AUTH_USER_MODEL` uses `email` as the `USERNAME_FIELD`, SimpleJWT's login
serializer authenticates by **email + password** out of the box. Our
`EmailTokenObtainSerializer` also returns the user object so the frontend can render
the avatar/name immediately after login.

## 5. The endpoints

| Method & path | Purpose | Auth |
|---------------|---------|------|
| `POST /api/auth/register/` | Create an account | public |
| `POST /api/auth/login/` | Get access + refresh | public |
| `POST /api/auth/refresh/` | Rotate → new access (+ refresh) | refresh token |
| `POST /api/auth/logout/` | Blacklist a refresh token | access token |
| `GET/PATCH /api/auth/me/` | Read/update own profile | access token |

Globally, DRF defaults to `IsAuthenticated` (`config/settings.py`), so *every* other
endpoint requires a valid access token unless it opts out with `AllowAny`.

## 6. Workspace-scoped permissions

Authentication answers "who are you?"; **authorization** answers "may you touch
*this*?". `workspaces/permissions.py` provides `IsWorkspaceMember` and
`IsWorkspaceAdmin`: a user may only act on data in workspaces they belong to. Module
04's viewsets both **filter querysets** by membership (so non-members can't even see
rows) *and* apply these object-level checks (defense in depth).

## 7. Throttling

`config/settings.py` sets DRF throttles (`1000/hour` per user, `30/hour` anon) so
login/registration can't be brute-forced or abused. Redis backs the cache the
throttle counters live in.

---

## 8. Do the lab

Register a user, log in, call a protected endpoint with and without a token, refresh
to rotate, and prove logout actually invalidates the old refresh token.

👉 **[lab.md](./lab.md)**

Then test yourself: 👉 **[challenge.md](./challenge.md)**

---

## Key terms (see [GLOSSARY](../GLOSSARY.md))

SimpleJWT · access token · refresh token · rotation · blacklist · permission class · throttling

**Next →** [Module 04: REST API with DRF](../04-rest-api-drf/)
