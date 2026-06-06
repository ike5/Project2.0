# Lab 09 — Run the Client, Wire Up Auth

**You'll:** start the Next.js app, register and log in through the UI, inspect the
stored tokens, confirm route protection, and watch the API client auto-refresh an
expired access token.

⏱️ ~50 min. Backend running (`apps/slack-backend`). Work in `apps/slack-frontend`.

---

## Part A — Start the frontend

```bash
cd apps/slack-frontend
npm install
cp .env.example .env.local        # points at http://localhost:8000
npm run dev                       # http://localhost:3000
```
✅ Expected: the dev server starts; visiting <http://localhost:3000> bounces you to
`/login` (no token yet).

---

## Part B — Register through the UI

Go to `/register`, create an account, and submit. You should be auto-logged-in and
routed to `/` → your first workspace (create one in the Django admin first if you
have none).

Open **DevTools → Application → Local Storage → localhost:3000**:
✅ Expected: `sc.access` and `sc.refresh` keys hold JWTs.

---

## Part C — Protected routes

With the app open on a workspace, clear the two localStorage keys and reload.
✅ Expected: you're redirected to `/login` — the `w/[workspace]/layout.tsx` guard
fired. Log back in.

---

## Part D — Watch a real API call

Open **DevTools → Network**. Click a channel. You'll see:
- `GET /api/channels/?workspace=…` and `GET /api/messages/?channel=…`
- each carrying an `Authorization: Bearer …` header (added by `apiFetch`).

✅ **Checkpoint:** the UI never sets tokens by hand — `apiFetch` does it.

---

## Part E — Force a token refresh

Temporarily shorten the backend access lifetime (Module 03 challenge) to ~1 minute
and restart the API. In the frontend, log in, wait it out, then click around.

In **Network** you'll see a request return `401`, immediately followed by a
`POST /api/auth/refresh/`, then the original request **retried** and succeeding —
all without you noticing.
✅ Expected: `sc.access` (and `sc.refresh`, due to rotation) update in localStorage.

Restore the longer access lifetime when done.

---

## Part F — Logout

Click **Sign out** in the sidebar.
✅ Expected: a `POST /api/auth/logout/` fires (blacklisting the refresh token),
localStorage clears, and you land on `/login`. The old refresh token now fails if reused.

---

## What you learned
- The App Router maps folders to routes; dynamic segments carry workspace/channel ids.
- `apiFetch` centralizes auth, refresh-on-401, and errors.
- Tokens live in localStorage (with a documented XSS trade-off).
- A layout-level guard protects every nested route with one check.

➡️ Now try the **[challenge](./challenge.md)**, then move to
[Module 10](../10-realtime-ui-css/).
