"use client";
import { KeyboardEvent, useRef, useState } from "react";
import styles from "./Composer.module.css";

export default function Composer({
  onSend,
  onTyping,
}: {
  onSend: (body: string) => void;
  onTyping: () => void;
}) {
  const [value, setValue] = useState("");
  const lastTyping = useRef(0);

  function submit() {
    const body = value.trim();
    if (!body) return;
    onSend(body);
    setValue("");
  }

  function onKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    // Enter sends; Shift+Enter inserts a newline.
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      submit();
    } else {
      // Throttle typing pings to at most one per second.
      const now = Date.now();
      if (now - lastTyping.current > 1000) {
        lastTyping.current = now;
        onTyping();
      }
    }
  }

  return (
    <div className={styles.wrap}>
      <textarea
        className={styles.input}
        rows={1}
        placeholder="Message"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={onKeyDown}
      />
      <button className={styles.send} onClick={submit} disabled={!value.trim()}>
        Send
      </button>
    </div>
  );
}
