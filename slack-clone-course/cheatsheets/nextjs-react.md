# Cheatsheet — Next.js & React

## App Router routing

```
app/layout.tsx              root shell (html/body)
app/page.tsx                "/"
app/login/page.tsx          "/login"
app/w/[workspace]/layout.tsx     nested layout (protect here)
app/w/[workspace]/[channel]/page.tsx   dynamic segments
```

```tsx
"use client";                       // needed for state/effects/browser/WebSockets
import { useParams, useRouter } from "next/navigation";
const { workspace, channel } = useParams();
useRouter().replace("/login");
```

## Hooks you'll use

```tsx
const [v, setV] = useState("");
useEffect(() => { /* run on mount / when deps change */ }, [deps]);
const ref = useRef<WebSocket|null>(null);     // mutable, no re-render
const fn = useCallback(() => {...}, [deps]);  // stable function identity
```

## Data fetching with the API client

```ts
import { apiFetch } from "@/lib/api";
const channels = await apiFetch("/api/channels/?workspace=1");
// apiFetch attaches the JWT and refreshes once on 401 automatically
```

## WebSocket hook pattern

```tsx
const { connected, sendMessage, sendTyping } = useChannelSocket(channelId, (e) => {
  if (e.type === "message.new") setMessages(m => [...m, e]);
});
```
- Keep the latest event handler in a ref so the socket doesn't reopen each render.
- Reconnect with backoff in `onclose`; heartbeat on an interval.

## Optimistic update

```tsx
setMessages(m => [...m, { id: tmp--, body, pending: true, author }]);
sendMessage(body);   // when the server broadcast arrives, replace the pending one
```

## CSS

- Global tokens in `app/globals.css` (`:root { --accent: … }`).
- Per-component **CSS modules**: `import s from "./X.module.css"` → `className={s.row}`.
- Theme by changing tokens in one place.

## Env

```
NEXT_PUBLIC_API_URL=…      # baked at BUILD time; exposed to the browser
```
Server-only secrets: plain env (no `NEXT_PUBLIC_`), read in server components/route handlers.

## Commands

```bash
npm run dev          # http://localhost:3000
npm run build        # production build (standalone output for Docker)
npm run start
npx tsc --noEmit     # typecheck
```

## Gotchas
- `localStorage`/`window` only exist in the browser — guard with `typeof window !== "undefined"`.
- `NEXT_PUBLIC_*` is inlined at build → one image is env-locked (see Module 12 challenge).
- Mark interactive components `"use client"`, or hooks won't work.
