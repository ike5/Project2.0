# Module 10 — Real-time UI & CSS

**Goal:** turn the skeleton into a live chat experience — a WebSocket hook, message
list, composer with optimistic send, typing and presence indicators, and a styled,
responsive layout.

⏱️ ~3.5 hours · 🎯 Prereq: Modules 05–06 (real-time backend) and 09 (frontend foundations).

> This is the payoff module. By the end, two browsers talk to each other instantly,
> messages feel immediate, and the app actually looks like Slack.

---

## 1. The WebSocket hook

`hooks/useChannelSocket.ts` encapsulates everything tricky about a live connection:

- opens `ws://…/ws/channels/<id>/?token=<access>` (token in the query — Module 05),
- calls your `onEvent` for each server event,
- **reconnects with exponential backoff** if the socket drops,
- sends a **heartbeat** every 15 s so presence stays fresh (Module 06),
- exposes `sendMessage` and `sendTyping`,
- cleans everything up when you leave the channel.

Components just call the hook and react to events — no raw WebSocket wrangling.

## 2. Load history, then go live

The channel page does both halves of Module 01's "two paths":
1. **REST** loads the recent history (`listMessages`) — newest-first, reversed for display.
2. **WebSocket** streams new messages on top.

It also `markRead`s the latest message so the unread badge clears (Module 06).

## 3. Optimistic send (why it feels instant)

When you hit Enter, we **don't** wait for the server. We append the message
immediately with a temporary negative id and a `pending` flag (rendered faded), then
send it over the socket. When the server broadcasts the authoritative copy (real id +
timestamp), we **replace** the optimistic one by matching author + body.

```
type ───► [optimistic, faded] ──server broadcast──► [confirmed, solid]
```

If the send failed, you'd mark the pending message with an error and offer a retry
(challenge). This pattern is what makes chat feel zero-latency.

## 4. Typing & presence

- **Typing:** the composer throttles `typing` pings to one per second; the page shows
  "X is typing…" and clears it after 3 s of silence. Ephemeral — never stored.
- **Presence:** the header dot reflects the socket's connected state; `presence`
  events (Module 06) drive who's online in the member list.

## 5. CSS architecture

- **Design tokens** (colors, radius, font) are CSS custom properties in
  `globals.css` — change the theme in one place.
- **Component styles** are **CSS modules** (`Sidebar.module.css`, etc.): class names
  are locally scoped, so `.item` in one component never clashes with another.
- The shell is a CSS **grid** (`260px 1fr`); the channel view is a flex column with a
  scrollable message list and a pinned composer. Make it responsive in the challenge.

---

## 6. Do the lab

Open two browsers, chat between them live, watch optimistic messages confirm, trigger
typing indicators and presence, and theme the app by changing a few tokens.

👉 **[lab.md](./lab.md)**

Then test yourself: 👉 **[challenge.md](./challenge.md)**

---

## Key terms (see [GLOSSARY](../GLOSSARY.md))

WebSocket hook · optimistic update · reconnect backoff · heartbeat · CSS module · design token

**Next →** [Module 11: Uploads & Search](../11-uploads-search/)
