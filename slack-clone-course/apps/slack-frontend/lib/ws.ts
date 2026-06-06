// Builds the WebSocket URL for a channel, passing the JWT as a query param (browsers
// can't set Authorization headers on a WebSocket — see Module 05).
import { getAccess } from "./auth";

const WS = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000";

export function channelSocketUrl(channelId: number): string {
  const token = getAccess() ?? "";
  return `${WS}/ws/channels/${channelId}/?token=${encodeURIComponent(token)}`;
}
