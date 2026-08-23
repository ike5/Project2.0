# Challenge 05 — Harden the Protocol

Solutions in [`solutions/`](./solutions/). Try first.

## Tasks

1. **Fix the skipped-sequence bug.**
   `send_message` allocates a sequence *before* the idempotent insert, so a lost
   race burns a sequence number and leaves a permanent hole. The lab's 64-way
   retry test burned **63** of them in one burst. A client doing gap detection
   will report those missing forever, and Module 10's `resume` will re-query for
   them on every reconnect.

   First **prove the bug**: write a test that fires 64 concurrent retries of one
   `client_id` and asserts the room's sequences are contiguous, and watch it
   fail. Then fix it so a sequence is allocated only by the winning insert.
   Verify under the same concurrency, and also verify that **64 concurrent
   *distinct* messages** still get 64 contiguous sequences with no duplicates —
   the fix must not trade one bug for the other.

   Report the throughput cost of your fix in messages/second into one room.

2. **Design and implement `typing.*` properly.**
   Typing indicators are the highest-volume, lowest-value traffic in chat.
   Implement all three layers:

   - client-side debounce: at most one `typing.start` per 3 s while typing,
   - server-side aggregation: one `typing.update` per room per second listing
     all current typers, not one frame per typer,
   - automatic expiry: a typer who goes silent disappears after 5 s with no
     explicit stop.

   Measure the outbound frame rate for a 200-member room in which 20 people type
   simultaneously, with and without aggregation. Report the ratio, and state how
   it scales with room size.

3. **Make the dedup window a defensible number.**
   The unique index on `(room_id, client_id)` grows forever. Decide how long
   idempotency actually needs to hold, with measurements:

   - What is the longest realistic client retry window? (Consider a phone in a
     tunnel with full-jitter exponential backoff, and Module 17's offline
     outbox.)
   - What does each index entry cost in bytes? Measure it, do not estimate.
   - At 10,000 messages/second, what does a 5-minute / 1-hour / 7-day / forever
     window cost in index size?

   Then implement a **two-tier** scheme: a bounded in-process cache for the hot
   window backed by the database constraint for everything older. Prove
   correctness survives eviction by evicting the cache mid-test.

4. **Break compatibility on purpose, three ways.**
   Starting from a working v1 browser client, make each of these changes
   server-side and document the **exact symptom** the old client shows:

   - add a required field to `message.create`,
   - change `seq` from a number to a string,
   - change the meaning of `ts` from milliseconds to seconds.

   Rank them by how hard each is to detect in production, and explain why the
   third is the most dangerous *class* of protocol change. Then, for each, state
   the mechanism that would have caught it before deploy.

5. **Stretch — make `resume` real, and find its cost.**
   Implement `resume` / `resume.batch` from the protocol spec: a client sends
   `from_seq`, the server returns everything after it in ascending order,
   capped at 500 messages with `has_more`.

   Then answer the question that decides Module 10's design: a client
   disconnected for **two minutes** in a room doing 1 message/second reconnects
   and resumes. Measure the query, the frame size, and the server CPU. Now scale
   it: **5,000 clients** reconnect simultaneously after a deploy (Module 18's
   scenario). What breaks first, and at what number? Propose a mitigation and
   measure it.

## Success criteria

- [ ] The sequence-hole bug is reproduced by a failing test, fixed, and
      re-verified under 64-way retry **and** 64-way distinct-message concurrency,
      with the throughput cost reported
- [ ] Typing indicators are debounced, aggregated and auto-expiring, with the
      frame-rate reduction measured and its scaling with room size stated
- [ ] The dedup window is chosen from measured byte costs at three horizons,
      with a two-tier implementation proven correct across a cache eviction
- [ ] All three breaking changes are documented with observed symptoms, ranked by
      detectability, each with a named pre-deploy detection mechanism
- [ ] Stretch: `resume` works, its single-client cost is measured, and the
      5,000-simultaneous-reconnect failure mode is identified with a number and
      a measured mitigation
