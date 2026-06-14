"use client";
// The heart of the real-time UI (Module 10): open a WebSocket to a channel, expose
// the live event stream, and provide senders for messages/typing. Reconnects with
// backoff if the socket drops.
import { useCallback, useEffect, useRef, useState } from "react";
import { channelSocketUrl } from "@/lib/ws";

export type WsEvent =
  | { type: "message.new"; id: number; channel: number; parent: number | null; body: string; author: { id: number; username: string }; created_at: string }
  | { type: "typing"; channel: number; user: string }
  | { type: "presence"; user: string; online: boolean }
  | { type: "error"; detail: string };

export function useChannelSocket(
  channelId: number,
  onEvent: (e: WsEvent) => void,
) {
  const socketRef = useRef<WebSocket | null>(null);
  const [connected, setConnected] = useState(false);
  // Keep the latest handler without re-opening the socket on every render.
  const handlerRef = useRef(onEvent);
  handlerRef.current = onEvent;

  useEffect(() => {
    let closedByUs = false;
    let retry = 0;
    let timer: ReturnType<typeof setTimeout>;

    function open() {
      const ws = new WebSocket(channelSocketUrl(channelId));
      socketRef.current = ws;

      ws.onopen = () => {
        setConnected(true);
        retry = 0;
      };
      ws.onmessage = (ev) => handlerRef.current(JSON.parse(ev.data));
      ws.onclose = () => {
        setConnected(false);
        if (!closedByUs) {
          // Exponential backoff, capped at 10s.
          retry += 1;
          timer = setTimeout(open, Math.min(1000 * 2 ** retry, 10000));
        }
      };
    }

    open();
    // Heartbeat keeps presence fresh (Module 06).
    const hb = setInterval(() => {
      socketRef.current?.readyState === WebSocket.OPEN &&
        socketRef.current.send(JSON.stringify({ type: "heartbeat" }));
    }, 15000);

    return () => {
      closedByUs = true;
      clearTimeout(timer);
      clearInterval(hb);
      socketRef.current?.close();
    };
  }, [channelId]);

  const sendMessage = useCallback((body: string, parent?: number) => {
    socketRef.current?.send(JSON.stringify({ type: "message.new", body, parent }));
  }, []);

  const sendTyping = useCallback(() => {
    socketRef.current?.send(JSON.stringify({ type: "typing" }));
  }, []);

  return { connected, sendMessage, sendTyping };
}
