# Challenge 05 — Harden the Protocol

Solutions in [`solutions/`](./solutions/). Try first.

## Tasks

1. **Fix the skipped-sequence bug.**
   The lab's `insertIdempotent` allocates a sequence *before* the insert, so a
   lost race burns a sequence number and leaves a permanent hole. A client doing
   gap detection will forever report a missing message that never existed.

   First **prove the bug**: write a test with 64 concurrent retries of the same
   `clientId` that asserts the room's sequences are contiguous, and watch it fail.
   Then fix it so sequences are allocated only by the winning insert. Verify the
   fix under the same concurrency.

2. **Design and implement `typing.*` correctly.**
   Typing indicators are the highest-volume, lowest-value traffic in chat.
   Implement:
   - client-side debounce (send `typing.start` at most once per 3 s while typing),
   - server-side aggregation (one `typing.update` per room per second listing all
     current typers, not one frame per typer),
   - automatic expiry (a typer who goes silent disappears after 5 s without an
     explicit `typing.stop`).

   Measure the outbound message rate for a 200-member room where 20 people type
   simultaneously, with and without aggregation. Report the ratio.

3. **Make the dedup window a defensible number.**
   The lab hardcodes 5 minutes. Determine the right value by answering, with
   measurements:
   - What is the longest realistic client retry window? (Consider a phone in a
     tunnel with exponential backoff.)
   - What does each cached entry cost in bytes?
   - At your target of 50,000 messages/minute, what heap does a 5 / 30 / 120
     minute window need?

   Then implement a **two-tier** scheme: a bounded in-memory cache for the hot
   window, backed by the database unique index for everything older. Prove
   correctness survives eviction by evicting the cache mid-test.

4. **Add protocol version negotiation.**
   Have the client send its protocol version in the STOMP `CONNECT` frame. The
   server should:
   - accept versions it supports,
   - reject unsupported ones with a `control` frame naming the minimum version,
   - record a metric tagged by client version so you can *measure* how many old
     clients exist before deprecating.

   Then simulate a breaking change: add a `v2` envelope where `room` moves into
   `data`, and show a `v1` client still works while a `v2` client uses the new
   shape.

5. **Break compatibility on purpose, three ways.**
   Starting from a working v1 client, make each of these changes server-side and
   document the exact symptom the old client shows:
   - add a required field to `MessageCreate`,
   - change `seq` from a number to a string,
   - change the meaning of `ts` from milliseconds to seconds.

   Rank them by how hard each is to detect in production, and explain why the
   third is the most dangerous class of protocol change.

6. **Stretch — replace Snowflake's `synchronized` with a lock-free version.**
   The lab's generator uses `synchronized`, which Module 01 told you pins virtual
   threads. Implement a CAS-based version that packs `(lastMillis, sequence)` into
   a single `AtomicLong` and updates it with `compareAndSet`.

   Benchmark both at 1, 8, and 64 concurrent virtual threads. Then argue whether
   the change is actually worth making — the honest answer may be no, and
   defending that is the point.

## Success criteria

- [ ] The sequence-hole bug is reproduced by a failing test, then fixed and
      re-verified under 64-way concurrency
- [ ] Typing indicators are debounced, aggregated and auto-expiring, with the
      message-rate reduction measured
- [ ] The dedup window is chosen from measured byte costs, with a two-tier
      implementation proven correct across an eviction
- [ ] Version negotiation works, rejects old clients cleanly, and emits a metric
      tagged by version
- [ ] All three breaking changes are documented with their observed symptoms and
      ranked by detectability
- [ ] Stretch: a lock-free generator is benchmarked against the synchronized one,
      with a defended recommendation
