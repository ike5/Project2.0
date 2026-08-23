# Challenge 10 — Break the Guarantee, Then Fix It

Solutions in [`solutions/`](./solutions/). Try first.

## Tasks

1. **Break the guarantee three ways, and document each.**
   Find three concrete scenarios where the guarantee stated in the README fails.
   For each, write the sequence of events, the observable symptom, and whether it
   is a bug or a documented limitation.

   At least one must be a genuine bug in the lab's implementation. (Hint:
   consider what happens when the same user has two devices, or what
   `abandon` does to `sequence_gaps`.)

2. **Make the cursor survive a hostile client.**
   The guarantee depends on the client persisting `lastSeq` correctly. Assume it
   doesn't: `localStorage` is disabled, or the client sends a `fromSeq` of 0, or
   a malicious client sends `fromSeq: -1`.

   Implement server-side protection so that no client can force an unbounded
   query, and so a client that loses its cursor recovers cheaply rather than
   downloading everything.

3. **Handle multi-device correctly.**
   Alice is on her phone and her laptop. Each has its own cursor. Design and
   implement:
   - per-device resume (each device catches up independently),
   - a shared read cursor (reading on the laptop clears the phone's badge),
   - and explain why those two must be separate values.

   Prove it with a test using two simultaneous sessions for one user.

4. **Measure the resume cost under a mass reconnect.**
   Simulate a deploy: disconnect 10,000 clients at once, then let them all
   reconnect and resume. Measure:
   - peak database queries per second,
   - p99 resume latency,
   - total rows read.

   Then optimize it. (Hint: 10,000 clients in 100 rooms are asking 100 distinct
   questions, not 10,000.)

5. **Add server-side gap detection.**
   The client detects gaps. The server should too — a gap that appears for many
   clients simultaneously indicates a real fan-out failure, not a network blip.

   Implement a metric that distinguishes "one client is on a bad network" from
   "this node is dropping messages," and alert only on the second.

6. **Stretch — implement causal ordering for a specific case.**
   Total per-room ordering is broken by exactly one thing users notice: a reply
   arriving before the message it replies to (possible if the parent is still in
   the client's buffer during a gap).

   Implement causal delivery for replies: hold a reply until its parent has been
   delivered. Then explain why you would *not* extend this to all messages.

## Success criteria

- [ ] Three guarantee-breaking scenarios documented, with at least one genuine
      implementation bug found and fixed
- [ ] A client cannot force an unbounded resume query, and cursor loss recovers
      cheaply
- [ ] Multi-device resume and shared read cursors work, with the distinction
      explained and proven by a two-session test
- [ ] Mass-reconnect resume cost is measured and then optimized, with before and
      after numbers
- [ ] Server-side gap detection distinguishes per-client from per-node failures
- [ ] Stretch: replies are causally ordered, with a reasoned argument against
      generalizing it
