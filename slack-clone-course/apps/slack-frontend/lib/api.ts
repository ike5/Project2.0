// A small fetch wrapper that attaches the JWT and transparently refreshes it once
// on a 401 — so callers never deal with token plumbing.
import { clearTokens, getAccess, getRefresh, setTokens, User } from "./auth";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

class ApiError extends Error {
  constructor(public status: number, public body: unknown) {
    super(`API ${status}`);
  }
}

async function refreshAccess(): Promise<boolean> {
  const refresh = getRefresh();
  if (!refresh) return false;
  const res = await fetch(`${API}/api/auth/refresh/`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ refresh }),
  });
  if (!res.ok) {
    clearTokens();
    return false;
  }
  const data = await res.json();
  setTokens(data.access, data.refresh); // rotation: store the new refresh too
  return true;
}

export async function apiFetch<T = unknown>(
  path: string,
  options: RequestInit = {},
  _retried = false,
): Promise<T> {
  const access = getAccess();
  const headers = new Headers(options.headers);
  headers.set("content-type", "application/json");
  if (access) headers.set("Authorization", `Bearer ${access}`);

  const res = await fetch(`${API}${path}`, { ...options, headers });

  if (res.status === 401 && !_retried && (await refreshAccess())) {
    return apiFetch<T>(path, options, true); // retry once with a fresh token
  }
  if (!res.ok) {
    throw new ApiError(res.status, await res.json().catch(() => null));
  }
  return res.status === 204 ? (undefined as T) : res.json();
}

// ── Auth calls ────────────────────────────────────────────────────────────────
export async function login(email: string, password: string) {
  const res = await fetch(`${API}/api/auth/login/`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) throw new ApiError(res.status, await res.json().catch(() => null));
  const data = await res.json();
  setTokens(data.access, data.refresh);
  return data.user as User;
}

export async function register(email: string, username: string, password: string) {
  return apiFetch("/api/auth/register/", {
    method: "POST",
    body: JSON.stringify({ email, username, password }),
  });
}

export async function logout() {
  const refresh = getRefresh();
  try {
    await apiFetch("/api/auth/logout/", {
      method: "POST",
      body: JSON.stringify({ refresh }),
    });
  } finally {
    clearTokens();
  }
}

// ── Domain calls ──────────────────────────────────────────────────────────────
export const getMe = () => apiFetch<User>("/api/auth/me/");
export const listWorkspaces = () => apiFetch<any[]>("/api/workspaces/");
export const listChannels = (workspaceId: number) =>
  apiFetch<any>(`/api/channels/?workspace=${workspaceId}`);
export const listMessages = (channelId: number) =>
  apiFetch<any>(`/api/messages/?channel=${channelId}`);
export const markRead = (channelId: number, messageId: number) =>
  apiFetch(`/api/channels/${channelId}/read/`, {
    method: "POST",
    body: JSON.stringify({ message_id: messageId }),
  });

export { ApiError };
