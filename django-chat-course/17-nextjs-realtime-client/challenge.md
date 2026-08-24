# Challenge 17 — Make the Client Trustworthy

Solutions in [`solutions/`](./solutions/). Try first.

## Tasks

1. **Break the guarantee from the client side, four ways.**
   Find four distinct client bugs that cause message loss or duplication despite
   a completely correct server. For each: reproduce it, show the user-visible
   symptom, and fix it.

   At least one must only appear **with two tabs open**, and at least one must
   only appear **under latency**. State, for each, which line of
   [`pulse-protocol-v1.md`](../05-protocol-and-domain-design/code/pulse-protocol-v1.md)
   the client was violating.

2. **Handle ticket expiry on a long-lived socket.**
   A ws ticket is single-use and short-lived; the socket stays open for eight
   hours. Implement in-band re-authentication driven by
   `control{action:"reauth"}` (§3.6): the server warns before expiry, the client
   refreshes and re-authenticates **without dropping the connection**.

   Prove no messages are lost across the refresh. Then test what happens when the
   refresh itself fails, and make that path correct too.

3. **Make the virtualized list survive edits and deletes.**
   `message.update` may change a message's height; `message.removed` makes it
   disappear. Both invalidate the virtualizer's measurement cache and can jump
   the user's scroll position.

   Fix both. Measure the scroll displacement in pixels before and after.

4. **Add read receipts driven by visibility, correctly debounced.**
   Implement read tracking with `IntersectionObserver` — a message is read when
   it has been visible for 500 ms. Debounce to at most one `read.upto` per 2
   seconds per room (§3.3).

   Measure the receipt rate with and without, and prove the server's
   `last_read_seq` still ends up correct — including when the user scrolls
   backwards.

5. **Measure and bound the client's memory.**
   Load a room, scroll through 100,000 messages, and measure heap growth. Find
   what is retained that should not be.

   Then implement a bounded in-memory window — keep N messages, drop the rest,
   re-fetch on scroll-back — and measure the difference. State what the bound
   costs in extra requests.

6. **Prove the SharedWorker's state split is right.**
   The lab asserted a split: the delivery cursor belongs in the worker, the
   scroll position and virtualizer cache belong per tab.

   Design a two-tab test that **fails** if the split is wrong in either
   direction — a piece of tab state wrongly shared, and a piece of shared state
   wrongly per-tab. Then run it against both the correct and the broken versions.

7. **Stretch — survive a server that is lying to you.**
   Assume the server is buggy, not malicious: it sends a `seq` that goes
   backwards, a `resume.batch` whose `to_seq` is *below* `from_seq`, a
   `message.new` for a room you never subscribed to, and a `ts` from 1970.

   Make the client degrade gracefully on all four — no crash, no silent
   corruption, and a signal an engineer can act on. Then say which of the four
   the protocol should have made impossible, and how.

## Success criteria

- [ ] Four client-side loss/duplication bugs reproduced and fixed, including one
      multi-tab and one latency-only, each mapped to the protocol clause it broke
- [ ] In-band `reauth` works without dropping the socket, with zero messages lost
      across the refresh, and the refresh-failure path handled
- [ ] Edits and deletes do not displace scroll position; displacement measured in
      pixels before and after
- [ ] Read receipts are `IntersectionObserver`-driven and debounced, with the
      rate reduction measured and `last_read_seq` proven correct under backward
      scrolling
- [ ] Client heap measured over 100k messages, a bounded window implemented, and
      its request cost stated
- [ ] A two-tab test that fails on a wrong split in **both** directions, run
      against a correct and a broken build
- [ ] Stretch: four server-lie scenarios handled with no crash and no silent
      corruption, with a protocol-level fix proposed for at least one
