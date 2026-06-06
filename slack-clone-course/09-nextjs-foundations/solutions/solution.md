# Challenge 09 — Reference Solution

### 1. Dedupe concurrent refreshes
```ts
// lib/api.ts
let refreshing: Promise<boolean> | null = null;

async function refreshAccess(): Promise<boolean> {
  if (refreshing) return refreshing;       // reuse the in-flight refresh
  refreshing = (async () => {
    const refresh = getRefresh();
    if (!refresh) return false;
    const res = await fetch(`${API}/api/auth/refresh/`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ refresh }),
    });
    if (!res.ok) { clearTokens(); return false; }
    const data = await res.json();
    setTokens(data.access, data.refresh);
    return true;
  })();
  try { return await refreshing; } finally { refreshing = null; }
}
```

### 2. `useUser` hook
```ts
// hooks/useUser.ts
"use client";
import { useEffect, useState } from "react";
import { getMe } from "@/lib/api";
import type { User } from "@/lib/auth";

let cache: User | null = null;
export function useUser() {
  const [user, setUser] = useState<User | null>(cache);
  const [loading, setLoading] = useState(!cache);
  useEffect(() => {
    if (cache) return;
    getMe().then((u) => { cache = u; setUser(u); }).finally(() => setLoading(false));
  }, []);
  return { user, loading };
}
```

### 3. Friendly errors
```ts
import { ApiError } from "@/lib/api";
try { await login(email, password); }
catch (e) {
  const body = e instanceof ApiError ? e.body as any : null;
  setError(body?.detail || "Invalid email or password.");
}
```

### 4. Workspace switcher
```tsx
// in Sidebar header
const [workspaces, setWorkspaces] = useState<any[]>([]);
useEffect(() => { listWorkspaces().then(setWorkspaces); }, []);
<select value={workspaceId} onChange={(e) => router.push(`/w/${e.target.value}`)}>
  {workspaces.map((w) => <option key={w.id} value={w.id}>{w.name}</option>)}
</select>
```

### 5. Cookie vs localStorage
> **localStorage** is readable by any JS on the page, so an **XSS** flaw can exfiltrate
> the token — but it's immune to **CSRF** because the browser never attaches it
> automatically. A **non-httpOnly cookie** has the *same* XSS exposure *and* is sent
> automatically, opening **CSRF** unless you add same-site/anti-CSRF tokens. An
> **httpOnly** cookie defeats XSS theft (JS can't read it) but is auto-sent, so it
> needs CSRF defenses. There's no silver bullet: you trade which attack you must
> mitigate, which is why Module 16 layers CSP, same-site, and short token lifetimes.
