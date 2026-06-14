# Module 09 — Next.js Frontend Foundations

**Goal:** build the web client's skeleton — App Router structure, a JWT-aware API
client with automatic token refresh, login/register flows, and protected routes.

⏱️ ~3 hours · 🎯 Prereq: Modules 03–04 (auth + REST API). Backend running.

> Now we give the API a face. This module is all the plumbing — auth, routing, the
> fetch layer — so Module 10 can focus purely on the live chat experience.

---

## 1. App Router in one minute

Next.js maps the `app/` folder to routes:

```
app/
├── layout.tsx                     the root HTML shell (wraps everything)
├── page.tsx                       "/"  → redirects to login or first workspace
├── login/page.tsx                 "/login"
├── register/page.tsx              "/register"
└── w/[workspace]/                 "/w/:workspace"
    ├── layout.tsx                 protected shell: sidebar + content
    ├── page.tsx                   picks the first channel
    └── [channel]/page.tsx         "/w/:workspace/:channel" — the chat view
```

`[workspace]` and `[channel]` are **dynamic segments** — the URL carries the ids, so
the UI is deep-linkable and the browser back button just works.

`"use client"` at the top of a file makes it a **client component** (it can use
state, effects, the browser, WebSockets). Our interactive pages are all client
components; a real app mixes in server components for static/SEO content.

## 2. The API client (`lib/api.ts`)

Every call goes through `apiFetch`, which:
1. attaches `Authorization: Bearer <access>`,
2. on a `401`, calls `/api/auth/refresh/` **once**, stores the rotated tokens, and
   retries the original request,
3. throws a typed `ApiError` otherwise.

So components call `listChannels(id)` and never think about tokens or refresh. This
mirrors the backend's rotation (Module 03): the new refresh token returned each time
is saved, so the old one's blacklisting is harmless.

## 3. Token storage and the trade-off

`lib/auth.ts` keeps the access + refresh tokens in `localStorage` so a page reload
stays logged in. That's the common, simple choice for a separate SPA — but it's
readable by JavaScript, so an XSS bug could steal it. The stricter alternative is
httpOnly cookies. We use localStorage for the course and revisit hardening in Module
16. Everything touches `window` behind a `typeof window` guard so server-rendering
doesn't crash.

## 4. Auth flows

- **Register** → `POST /register/`, then auto-login, then route to `/`.
- **Login** → `POST /login/`, store tokens, route to `/` (which forwards to the first
  workspace).
- **Logout** → blacklist the refresh token server-side, clear local tokens, go to `/login`.

## 5. Protecting routes

`app/w/[workspace]/layout.tsx` is a client guard: if there's no token it
`router.replace("/login")`; otherwise it renders the sidebar + content shell. Because
every workspace route is nested under this layout, they're all protected by one
check. (This is client-side UX protection — the *real* security is the backend, which
rejects every unauthenticated request regardless of the UI.)

---

## 6. Do the lab

Run the frontend, register and log in through the UI, watch tokens land in
localStorage, see a protected route bounce you when logged out, and confirm the API
client transparently refreshes an expired access token.

👉 **[lab.md](./lab.md)**

Then test yourself: 👉 **[challenge.md](./challenge.md)**

---

## Key terms (see [GLOSSARY](../GLOSSARY.md))

React · Next.js · App Router · client component · dynamic segment · hook · token refresh

**Next →** [Module 10: Real-time UI & CSS](../10-realtime-ui-css/)
