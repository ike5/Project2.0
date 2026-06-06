# Challenge 05 — Make Real-time Richer

No step-by-step this time. Use what you learned. Reference solutions are in
[`solutions/`](./solutions/) — try first!

## Tasks

1. **Edit & delete, live.** Handle two new client events in the consumer:
   `message.edit` (`{type, id, body}`) and `message.delete` (`{type, id}`). Update
   Postgres (author-only) and broadcast `message.updated` / `message.deleted` so all
   clients reflect the change instantly.

2. **Reactions, live.** Handle a `reaction.add` event that creates the `Reaction` and
   broadcasts `reaction.added` with the message id, emoji, and username.

3. **Reject posting to a private channel you're not in.** Confirm that connecting to a
   `private` channel you're not a `ChannelMember` of closes the socket — and add a
   test that proves it.

4. **Limit message size.** Reject any `message.new` with a body longer than 4000
   characters by sending the client an `{type:"error","detail":...}` event instead of
   storing it.

5. **Stretch:** A user has the same channel open in two browser tabs. Explain what
   happens on the channel layer when they post a message, and why they (correctly)
   see it appear in *both* tabs.

## Success criteria
- [ ] Edit/delete propagate live and are author-enforced.
- [ ] Adding a reaction broadcasts to everyone in the channel.
- [ ] Connecting to a private channel you're not in is rejected (with a test).
- [ ] Oversized messages are rejected with an error event, not stored.
- [ ] You can explain multi-tab behavior in terms of groups/connections.
