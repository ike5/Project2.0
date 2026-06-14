# Lab 03 — Register, Login, Refresh, Logout

**You'll:** exercise the whole auth lifecycle with `curl`, see how a missing/expired
token is rejected, and confirm refresh-token rotation and blacklisting work.

⏱️ ~45 min. Server running (`python manage.py runserver`) from
`apps/slack-backend`. Use a second terminal for `curl`.

> Tip: install `jq` for readable JSON, or pipe through `python -m json.tool`.

---

## Part A — Register

```bash
curl -s -X POST localhost:8000/api/auth/register/ \
  -H 'content-type: application/json' \
  -d '{"email":"ann@example.com","username":"ann","password":"slackpass123"}' | jq
```
✅ Expected: `201`-style body with `id`, `email`, `username` (no password echoed).

Try registering the same email again → `400` with a uniqueness error. Try a weak
password (`"123"`) → `400` from the validators.

---

## Part B — Login → tokens

```bash
curl -s -X POST localhost:8000/api/auth/login/ \
  -H 'content-type: application/json' \
  -d '{"email":"ann@example.com","password":"slackpass123"}' | jq
```
✅ Expected: `access`, `refresh`, and a `user` object.

Capture the tokens into shell variables for the next steps:
```bash
ACCESS=$(curl -s -X POST localhost:8000/api/auth/login/ -H 'content-type: application/json' \
  -d '{"email":"ann@example.com","password":"slackpass123"}' | jq -r .access)
REFRESH=$(curl -s -X POST localhost:8000/api/auth/login/ -H 'content-type: application/json' \
  -d '{"email":"ann@example.com","password":"slackpass123"}' | jq -r .refresh)
```

---

## Part C — Protected endpoint, with and without a token

```bash
# No token → 401
curl -s -o /dev/null -w "%{http_code}\n" localhost:8000/api/auth/me/

# With the access token → 200 + your profile
curl -s localhost:8000/api/auth/me/ -H "Authorization: Bearer $ACCESS" | jq
```
✅ Expected: `401` then `200`. This is DRF's global `IsAuthenticated` at work.

Update your display name:
```bash
curl -s -X PATCH localhost:8000/api/auth/me/ \
  -H "Authorization: Bearer $ACCESS" -H 'content-type: application/json' \
  -d '{"display_name":"Ann from Acme"}' | jq
```

---

## Part D — Refresh (rotation in action)

```bash
curl -s -X POST localhost:8000/api/auth/refresh/ \
  -H 'content-type: application/json' \
  -d "{\"refresh\":\"$REFRESH\"}" | jq
```
✅ Expected: a **new** `access` *and* a **new** `refresh` (rotation is on). Save the
new refresh as `REFRESH2`.

Now reuse the **old** refresh again:
```bash
curl -s -X POST localhost:8000/api/auth/refresh/ \
  -H 'content-type: application/json' \
  -d "{\"refresh\":\"$REFRESH\"}"
```
✅ Expected: `401` — the old refresh was **blacklisted** the moment it was rotated.

---

## Part E — Logout

```bash
curl -s -o /dev/null -w "%{http_code}\n" -X POST localhost:8000/api/auth/logout/ \
  -H "Authorization: Bearer $ACCESS" -H 'content-type: application/json' \
  -d "{\"refresh\":\"$REFRESH2\"}"
# → 205
# now REFRESH2 is dead:
curl -s -o /dev/null -w "%{http_code}\n" -X POST localhost:8000/api/auth/refresh/ \
  -H 'content-type: application/json' -d "{\"refresh\":\"$REFRESH2\"}"
# → 401
```
✅ **Checkpoint:** logout blacklisted the refresh token; it can no longer mint access tokens.

---

## What you learned
- Register/login issue an access + refresh pair; access guards every request.
- Missing/expired access tokens are rejected with `401` by the global permission.
- Rotation hands out a fresh refresh each time and blacklists the old one.
- Logout = blacklisting the refresh token.

➡️ Now try the **[challenge](./challenge.md)**, then move to
[Module 04](../04-rest-api-drf/).
