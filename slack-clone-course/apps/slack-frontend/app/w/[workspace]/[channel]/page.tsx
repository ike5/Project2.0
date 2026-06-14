"use client";
import { useCallback, useEffect, useRef, useState } from "react";
import { useParams } from "next/navigation";
import { getMe, listMessages, markRead } from "@/lib/api";
import { useChannelSocket, WsEvent } from "@/hooks/useChannelSocket";
import MessageList, { Message } from "@/components/MessageList";
import Composer from "@/components/Composer";
import styles from "./channel.module.css";

export default function ChannelPage() {
  const params = useParams();
  const channelId = Number(params.channel);

  const [messages, setMessages] = useState<Message[]>([]);
  const [typing, setTyping] = useState<string[]>([]);
  const meRef = useRef<string>("");
  const tmpId = useRef(-1);
  const typingTimers = useRef<Record<string, ReturnType<typeof setTimeout>>>({});

  // Load identity + history when the channel changes.
  useEffect(() => {
    getMe().then((u) => (meRef.current = u.username));
    listMessages(channelId).then((data) => {
      const rows: Message[] = (data.results ?? data).slice().reverse(); // oldest→newest
      setMessages(rows);
      if (rows.length) markRead(channelId, rows[rows.length - 1].id).catch(() => {});
    });
  }, [channelId]);

  const onEvent = useCallback((e: WsEvent) => {
    if (e.type === "message.new") {
      setMessages((prev) => {
        // Replace an optimistic message from me with the authoritative server copy.
        const idx = prev.findIndex(
          (m) => m.pending && m.author.username === e.author.username && m.body === e.body,
        );
        const real: Message = {
          id: e.id,
          body: e.body,
          author: e.author,
          created_at: e.created_at,
        };
        if (idx >= 0) {
          const next = prev.slice();
          next[idx] = real;
          return next;
        }
        if (prev.some((m) => m.id === e.id)) return prev; // dedupe
        return [...prev, real];
      });
      markRead(channelId, e.id).catch(() => {});
    } else if (e.type === "typing") {
      showTyping(e.user);
    }
  }, [channelId]);

  const { connected, sendMessage, sendTyping } = useChannelSocket(channelId, onEvent);

  function showTyping(user: string) {
    if (user === meRef.current) return;
    setTyping((t) => (t.includes(user) ? t : [...t, user]));
    clearTimeout(typingTimers.current[user]);
    typingTimers.current[user] = setTimeout(
      () => setTyping((t) => t.filter((u) => u !== user)),
      3000,
    );
  }

  function send(body: string) {
    // Optimistic: show immediately with a temporary negative id.
    const optimistic: Message = {
      id: tmpId.current--,
      body,
      author: { username: meRef.current },
      created_at: new Date().toISOString(),
      pending: true,
    };
    setMessages((prev) => [...prev, optimistic]);
    sendMessage(body); // server will broadcast the real copy → replaces this one
  }

  return (
    <div className={styles.channel}>
      <header className={styles.head}>
        <span className={styles.title}># channel {channelId}</span>
        <span className={connected ? styles.dotOn : styles.dotOff} title={connected ? "connected" : "reconnecting"} />
      </header>
      <MessageList messages={messages} />
      <div className={styles.typing}>
        {typing.length > 0 && `${typing.join(", ")} ${typing.length === 1 ? "is" : "are"} typing…`}
      </div>
      <Composer onSend={send} onTyping={sendTyping} />
    </div>
  );
}
