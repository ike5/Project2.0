# Challenge 10 — Break the Guarantee, Then Defend It

Solutions in [`solutions/`](./solutions/). Try first.

## Tasks

1. **Break the README's guarantee three ways, and document each.**
   The guarantee is: *every message the server acknowledged to its sender will be
   delivered to every room member at least once, in per-room `seq` order, and a
   client can detect and repair any gap — provided the client returns within the
   retention window and correctly persists its cursor.*

   Find three concrete scenarios where it fails. For each, write the exact
   sequence of events, the observable symptom, and whether it is a **bug** or a
   **documented limitation**.

   At least one must be a genuine bug in the lab's implementation. Hints: what
   happens when the same user has two devices in the same room? What does the
   `abandon` path do to a client that was only 5,001 messages behind? What does
   `MAX_BUFFER` do when a client is buffering ahead and the repair fails?

2. **Make the cursor survive a hostile or broken client.**
   The guarantee depends on the client persisting `from_seq` correctly. Assume it
   does not: `localStorage` is disabled, the client always sends `from_seq: 0`, or
   an attacker opens 500 sockets each requesting `from_seq: 0` on your busiest
   room.

   Add server-side protection so that (a) no client can force an unbounded query,
   (b) a client that genuinely lost its cursor recovers cheaply rather than
   downloading the room, and (c) a client that requests resume in a loop is
   throttled rather than served. Measure the cost of the attack before and after.

3. **Handle multi-device correctly.**
   Alice is on her phone and her laptop, in the same room. Design and implement:
   - **per-device resume** — each device catches up independently;
   - **a shared read cursor** — reading on the laptop clears the phone's badge;
   - and explain in writing why those two must be *different* values, and what
     breaks if you use one for both.

   Prove it with a test that runs two simultaneous sessions for one user.

4. **Measure and then fix the mass-reconnect resume cost.**
   Simulate a deploy: disconnect 10,000 clients across 100 rooms at once, then let
   them all reconnect and resume. Measure peak database queries per second, p99
   resume latency, and total rows read.

   Then optimize it and re-measure. Hint: 10,000 clients in 100 rooms are asking
   **100 distinct questions**, not 10,000 — and most of them are asking for the
   same tail of the same room.

5. **Distinguish "one bad network" from "this worker is dropping messages."**
   The client detects gaps. The server should too. A gap that appears for one
   client is a network blip; the same gap appearing for many clients on the same
   worker process at the same time is a fan-out failure.

   Implement a metric that separates the two, and define the alert you would page
   on. State the false-positive rate you would accept and why.

6. **Stretch — causal delivery for replies only.**
   Per-room total ordering is broken by exactly one thing users notice: a reply
   rendering before the message it replies to, which is possible when the parent
   is still in the client's out-of-order buffer.

   Implement causal delivery for replies: hold a `reply_to` message until its
   parent has been delivered, with a timeout. Then write the argument for why you
   would **not** extend this to all messages.

## Success criteria

- [ ] Three guarantee-breaking scenarios documented, with at least one genuine
      implementation bug found, explained and fixed
- [ ] A client cannot force an unbounded resume query; cursor loss recovers
      cheaply; resume-loop abuse is throttled, with before/after numbers
- [ ] Per-device resume and a shared read cursor both work, the distinction is
      argued in writing, and a two-session test proves it
- [ ] Mass-reconnect resume cost measured, optimized, and re-measured — with the
      before and after numbers in your results file
- [ ] Server-side gap detection distinguishes per-client from per-worker failure,
      with a stated alert threshold and an accepted false-positive rate
- [ ] Stretch: replies are causally ordered with a bounded wait, plus a reasoned
      argument against generalizing it
