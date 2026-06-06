# Challenge 01 — Think Like a Schema Designer

No step-by-step this time. Use the `explore` schema (reload `code/seed.sql` if you
dropped it). Reference solutions are in [`solutions/`](./solutions/) — try first!

## Tasks

1. **The membership question.** Write one query listing every member of the `Acme`
   workspace with their role, sorted owners → admins → members.

2. **DM participants.** The DM is channel 4. Write a query that returns the
   usernames of everyone in it. (Remember DMs have no `name`, so you must use
   `channel_member`.)

3. **Busiest channel.** Which channel has the most messages? Return the channel
   name (or `'(dm)'` when name is null) and the count, highest first.

4. **Design a reaction.** The seed schema has no reactions table. On paper (or as a
   comment), write the `CREATE TABLE reaction` DDL: it links a user and a message
   with an emoji, and the *same user can't react with the same emoji twice* on one
   message. State which column(s) form the uniqueness constraint.

5. **Stretch:** Explain in two sentences why modeling a DM as a `channel` (rather
   than a separate `conversation` table) simplifies the message-sending code you'll
   write in Module 05.

## Success criteria
- [ ] You listed workspace members ordered by role.
- [ ] You returned the DM's participant usernames.
- [ ] You found the busiest channel and its message count.
- [ ] You wrote a `reaction` table with the correct uniqueness constraint.
- [ ] You can justify the "DMs are channels" design decision.
