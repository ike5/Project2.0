# Challenge 17 — Make the Client Trustworthy

Solutions in [`solutions/`](./solutions/). Try first.

## Tasks

1. **Break the guarantee from the client side, four ways.**
   Find four distinct client bugs that cause message loss or duplication despite
   a correct server. For each: reproduce it, show the user-visible symptom, and
   fix it.

   At least one must be a bug that only appears with two tabs open, and at least
   one must only appear under latency.

2. **Handle token expiry on a long-lived socket.**
   A JWT expires in 15 minutes; the socket stays open for 8 hours. Implement
   in-band re-authentication: the server sends a warning before expiry, the
   client refreshes and re-authenticates **without dropping the connection**.

   Prove no messages are lost across the refresh. Then test what happens when the
   refresh itself fails.

3. **Make the virtualized list survive edits and deletes.**
   An edited message may change height; a deleted one disappears. Both invalidate
   the virtualizer's measurement cache and can jump the user's scroll position.

   Fix both. Measure the scroll displacement before and after.

4. **Add optimistic read receipts with correct debouncing.**
   Implement read tracking driven by `IntersectionObserver` — a message is read
   when it's been visible for 500 ms. Debounce to at most one receipt per 2
   seconds per room.

   Measure the receipt rate with and without, and prove the server's
   `last_read_seq` still ends up correct.

5. **Measure and reduce the client's memory footprint.**
   Load a room, scroll through 100,000 messages, and measure heap growth. Find
   what's retained that shouldn't be.

   Implement a bounded in-memory window (keep N messages, drop the rest, re-fetch
   on scroll-back) and measure the difference.

6. **Stretch — make it work with two tabs and one SharedWorker, correctly.**
   The lab's SharedWorker shares a connection but each tab has its own
   `RoomStore` and its own cursor. Two tabs will fight over `localStorage`.

   Design and implement the correct split: what state belongs in the worker, what
   belongs per tab, and how do they stay consistent? Prove it with a two-tab test.

## Success criteria

- [ ] Four client-side loss/duplication bugs reproduced and fixed, including one
      multi-tab and one latency-only
- [ ] In-band token refresh works without dropping the socket; the refresh-failure
      path is handled
- [ ] Edits and deletes don't displace scroll position; displacement measured
- [ ] Read receipts are `IntersectionObserver`-driven and debounced, with the
      rate reduction measured and server state proven correct
- [ ] Client heap measured over 100k messages, with a bounded window implemented
      and the difference reported
- [ ] Stretch: worker/tab state split designed and proven with a two-tab test
