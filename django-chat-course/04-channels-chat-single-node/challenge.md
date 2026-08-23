# Challenge 04 — Make the Channel Layer Show You Its Limits

Solutions in [`solutions/`](./solutions/). Try first.

The lab showed you the wall. These tasks make you *characterize* it — turn "two
workers don't talk" into numbers, failure modes, and a defensible position on
what to do before Module 07 arrives.

## Tasks

1. **Close the forgery hole in your own protocol.**
   Right now any connected client can send `{"type":"chat.message", ...}` — no
   wait, it cannot, because `receive_json` only handles `message.create`. Good.
   So find the hole that *does* exist: a client can set any `body` it likes, but
   what about `sender`?

   Trace the path from `receive_json` to `chat_message` and prove, from
   `websocat`, whether a client can impersonate another user. Then do the same
   for the **room**: can a client authenticated for `general` cause a
   `group_send` to `room.random`?

   Write down the general rule your consumer must follow about which parts of a
   client frame are ever allowed to reach a `group_send`, and enforce it with a
   single explicit allowlist rather than by hoping.

2. **Find the revocation gap in connect-time authorization.**
   `_load_room_if_member` authorizes at CONNECT time. Show, with two terminals
   and a `Membership.objects.filter(...).delete()` in a Django shell, that a
   removed user keeps receiving messages for as long as the socket stays open.

   Then close it. There are at least three designs — delivery-time checks, a
   revocation broadcast to the room group, and a per-user control channel — and
   they differ in cost per message. Implement one, measure what it adds to the
   Part F fan-out p99, and explain in writing why you rejected the other two.

3. **Characterize the wall as a curve, not an anecdote.**
   Run `crosstalk` at `--workers` 1, 2, 3, 4, 6 and 8, with `--pairs 200` at
   each, and plot delivery rate against worker count.

   - Does it match `1/workers`? Derive the expected value and explain any gap.
   - Now re-run with **four different rooms** and 200 pairs spread across them.
     Does the curve change? Why or why not?
   - Finally, answer the question a tech lead will actually ask: *at what worker
     count does this become a production incident rather than a rare
     complaint?* Justify with the delivery rate a user would perceive.

4. **Build a working, honest, cross-process channel layer — and then reject it.**
   Write a `FileChannelLayer` that implements `group_add`, `group_discard` and
   `group_send` by putting events in a directory on disk (or a SQLite file, or a
   Unix socket — your choice), so that two Uvicorn workers *can* deliver to each
   other. Get `crosstalk --pairs 50` to 100% at `--workers 4`.

   Then measure it against the in-memory layer on Part F's fan-out test and
   write the honest verdict: latency added, CPU added, and — most importantly —
   the list of things you did not implement (liveness, cleanup of dead channels,
   backpressure, ordering, cross-machine). That list is the argument for Redis,
   written by you rather than asserted by this course.

5. **Stretch — make the failure visible.**
   The lab's most alarming finding was not that delivery broke; it was that
   *nothing reported it*. Design and implement a detector that would have paged
   you.

   Ideas worth considering: a periodic self-test connection pair, a metric of
   `len(layer.groups[g])` compared against the room's true member count, or an
   end-to-end synthetic prober. Whatever you build, it must (a) run inside the
   app, (b) produce a single number a dashboard can alert on, and (c) fire
   within 60 seconds of someone starting a second worker.

   Then state its false-positive conditions. A detector nobody trusts is worse
   than none.

## Success criteria

- [ ] Impersonation and cross-room injection are each tested from `websocat`,
      and the consumer enforces an explicit allowlist of client-controlled fields
- [ ] The revocation gap is demonstrated live, one fix is implemented and
      measured against the fan-out p99, and two alternatives are rejected in
      writing
- [ ] A delivery-rate-vs-worker-count curve exists for 6 worker counts, compared
      against `1/workers`, with a stated incident threshold
- [ ] A cross-process channel layer works at 100% with 4 workers, is benchmarked
      against the in-memory layer, and comes with a written list of what it does
      not do
- [ ] Stretch: a detector emits one alertable number, fires within 60 s of a
      second worker starting, and its false positives are named
