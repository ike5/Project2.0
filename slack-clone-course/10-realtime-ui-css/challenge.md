# Challenge 10 — Polish the Experience

No step-by-step this time. Use what you learned. Reference solutions are in
[`solutions/`](./solutions/) — try first!

## Tasks

1. **Failed-send retry.** If the socket is closed when sending, mark the optimistic
   message with an error state and render a "retry" affordance that re-sends it.

2. **Infinite scroll up.** When the user scrolls to the top of the message list, load
   the previous page using the cursor `next`/`previous` from the messages API and
   prepend the older messages without jumping the scroll position.

3. **Member list with presence.** Add a right-hand panel listing channel members,
   each with an online/away/offline dot driven by `presence` events and the
   `GET /api/workspaces/{id}/presence/` endpoint.

4. **Responsive layout.** Below 768px, collapse the sidebar behind a hamburger toggle
   so the chat view is full-width on mobile. Use a CSS media query only.

5. **Stretch:** Your optimistic-replace matches on `author + body`. Describe a case
   where that misidentifies messages (e.g. the same text sent twice quickly) and
   propose a more robust correlation (hint: a client-generated `nonce` echoed by the
   server).

## Success criteria
- [ ] A failed send can be retried from the UI.
- [ ] Scrolling up loads older history seamlessly.
- [ ] A member panel shows live presence.
- [ ] The layout is usable on a phone-width screen.
- [ ] You can describe a robust optimistic-correlation scheme.
