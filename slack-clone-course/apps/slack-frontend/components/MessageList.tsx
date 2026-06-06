"use client";
import { useEffect, useRef } from "react";
import styles from "./MessageList.module.css";

export type Message = {
  id: number; // negative ids are optimistic (not yet confirmed by the server)
  body: string;
  author: { username: string };
  created_at: string;
  pending?: boolean;
};

export default function MessageList({ messages }: { messages: Message[] }) {
  const bottomRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to the newest message whenever the list grows.
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages.length]);

  return (
    <div className={styles.list}>
      {messages.map((m) => (
        <div key={m.id} className={`${styles.row} ${m.pending ? styles.pending : ""}`}>
          <div className={styles.avatar}>{m.author.username[0]?.toUpperCase()}</div>
          <div>
            <div className={styles.meta}>
              <span className={styles.author}>{m.author.username}</span>
              <span className={styles.time}>
                {new Date(m.created_at).toLocaleTimeString([], {
                  hour: "2-digit",
                  minute: "2-digit",
                })}
              </span>
            </div>
            <div className={styles.body}>{m.body}</div>
          </div>
        </div>
      ))}
      <div ref={bottomRef} />
    </div>
  );
}
