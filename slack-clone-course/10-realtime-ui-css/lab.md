# Lab 10 — Two Browsers, One Conversation

**You'll:** chat live between two browser sessions, watch optimistic messages confirm,
trigger typing and presence, exercise reconnection, and re-theme the app.

⏱️ ~60 min. Backend (ASGI) + frontend (`npm run dev`) running. Redis up.

---

## Part A — Two sessions

Open the app in a normal window (as **ann**) and an incognito window (as **bob**,
added to the same channel). Put them side by side on the same channel.

Type in ann's window and hit Enter.
✅ Expected: the message appears **instantly** in ann's window (faded for a beat),
then **also** in bob's window — pushed over the WebSocket.

---

## Part B — See the optimistic → confirmed swap

In DevTools, throttle ann's network (Slow 3G). Send a message.
✅ Expected: it shows immediately **faded** (`pending`), then turns solid a moment
later when the server's broadcast arrives and replaces it. Remove the throttle.

---

## Part C — Typing indicator

Start typing in bob's composer (don't send).
✅ Expected: ann sees "**bob is typing…**", which disappears ~3 s after bob stops.
Confirm in DevTools that `typing` frames are sent at most ~once per second.

---

## Part D — Presence

Watch the header connection dot: green when connected, grey while reconnecting.
Kill the backend briefly (`Ctrl+C`), watch the dot go grey and the hook retry; bring
the backend back and watch it reconnect automatically (backoff).
✅ **Checkpoint:** the client survives a backend restart without a page reload.

---

## Part E — Unread clears

As bob, open a different channel, then have ann post to the first one. Switch bob back
— the unread badge (Module 06) was set, and opening the channel `markRead`s it to zero.
✅ Confirm via `GET /api/channels/<id>/unread/`.

---

## Part F — Re-theme in 30 seconds

Edit the design tokens at the top of `app/globals.css` — e.g.:
```css
--bg: #f8f8f8; --bg-elevated: #fff; --text: #1d1c1d; --text-strong: #111;
--sidebar: #3f0e40; --accent: #007a5a;
```
✅ Expected: the whole app restyles (a light theme with an aubergine sidebar) because
every component reads these variables. No component CSS needed.

---

## What you learned
- The WebSocket hook delivers live messages; the UI reacts to events.
- Optimistic send makes posting feel instant, then reconciles with the server copy.
- Typing/presence are ephemeral signals layered on the same socket.
- Reconnection with backoff makes the client resilient.
- Design tokens make theming a one-file change.

➡️ Now try the **[challenge](./challenge.md)**, then move to
[Module 11](../11-uploads-search/).
