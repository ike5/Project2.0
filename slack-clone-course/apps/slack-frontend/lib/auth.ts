// Token storage + auth helpers for the SimpleJWT backend.
//
// Access/refresh tokens are kept in localStorage so a page refresh keeps you logged
// in. (For stricter XSS posture you'd use httpOnly cookies + a same-site backend;
// localStorage is the common, simpler choice for a separate SPA and is fine for the
// course — we discuss the trade-off in Module 16.)

const ACCESS_KEY = "sc.access";
const REFRESH_KEY = "sc.refresh";

export type User = {
  id: number;
  username: string;
  email: string;
  display_name?: string;
  avatar_url?: string;
};

export function getAccess(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(ACCESS_KEY);
}

export function getRefresh(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(REFRESH_KEY);
}

export function setTokens(access: string, refresh?: string) {
  localStorage.setItem(ACCESS_KEY, access);
  if (refresh) localStorage.setItem(REFRESH_KEY, refresh);
}

export function clearTokens() {
  localStorage.removeItem(ACCESS_KEY);
  localStorage.removeItem(REFRESH_KEY);
}

export function isAuthenticated(): boolean {
  return !!getAccess();
}
