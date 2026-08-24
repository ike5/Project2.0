# Challenge 11 — Make Presence Cheap and Limits Unbypassable

Solutions in [`solutions/`](./solutions/). Try first.

## Tasks

1. **Find the presence design's remaining lie, and fix it.**
   The lab's presence is per `(room, username)`. Alice has three devices and two
   browser tabs. Work out precisely what happens when she closes one tab, and
   what the other four connections observe.

   Then fix it so that presence is correct for multi-connection users, and state
   the new Redis memory cost per online user. Prove the fix with a test that
   opens three connections for one user and closes one.

2. **Build the "away" state, and defend the extra cardinality.**
   Presence today is binary: in the sorted set or not. Add a third state — `away`
   — driven by client-reported idleness (no keystroke or focus event for 5
   minutes), and make sure it survives a worker restart.

   Then measure what it costs: frames/s during the Part C storm, Redis memory,
   and the additional state transitions per user per hour. Decide, with numbers,
   whether Pulse should ship it.

3. **Make the limiter unbypassable across the dimensions it currently misses.**
   The six tiers still have holes. Find at least two and close them. Consider:
   - a botnet with 5,000 distinct IPs, 1 message/s each, into one room;
   - one user opening 200 WebSocket connections (each within the connection tier)
     and sending 1 message/s on each;
   - `typing.start` and `read.upto`, which currently bypass the message tiers
     entirely;
   - a client that never honours `retry_after_ms`.

   For each hole: the attack, the tier that closes it, the limit you chose, and
   the legitimate traffic your limit would break.

4. **Decide whether to shed presence under load, and implement it.**
   During the Part C storm, presence competed with chat for the same fan-out
   budget and chat lost. Build **load shedding**: when a worker's outbound queue
   depth or event-loop lag crosses a threshold, degrade presence (longer sweep
   interval, then suppress entirely) while leaving message delivery untouched.

   Measure the p99 message delivery latency during the storm, with and without
   shedding. State the signal you shed on and why you rejected the others.

5. **Stretch — replace the per-worker sweep with something better, or prove you
   can't.**
   Eight workers each read every room's roster every second. That is eight
   identical reads. Design an alternative (one sweeper per room by consistent
   hash, publishing deltas over the channel layer) and measure it against the
   naive-but-robust version on: Redis ops/s, presence frames/s, worst-case
   staleness after a worker dies, and lines of code.

   Then argue for one. A defensible "the naive version wins" is a full-credit
   answer if the numbers support it.

## Success criteria

- [ ] Multi-connection presence is correct, tested with three connections for one
      user, with the new per-user memory cost stated
- [ ] An `away` state exists, survives a worker restart, and there is a numbers-
      backed ship/no-ship decision for it
- [ ] At least two limiter bypasses found and closed, each with the attack, the
      new tier, the chosen limit, and the legitimate traffic it breaks
- [ ] Presence load shedding implemented, with before/after p99 message delivery
      latency during a storm and a justified choice of shed signal
- [ ] Stretch: the sweep alternative is implemented and measured on all four axes,
      with a defended recommendation either way
