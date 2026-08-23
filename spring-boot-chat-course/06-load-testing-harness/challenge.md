# Challenge 06 — Prove Your Numbers

Solutions in [`solutions/`](./solutions/). Try first.

## Tasks

1. **Demonstrate coordinated omission, quantitatively.**
   Write two k6 scenarios against the same server under the same offered load:
   one closed-loop (send, await reply, repeat) and one open-loop
   (`constant-arrival-rate`). Then induce a 5-second stall in the server
   (a `Thread.sleep` behind a debug endpoint, or `docker pause` on Redis later).

   Report both p99s and the request counts. Explain the discrepancy in terms of
   what each generator did during the stall.

2. **Find the bytes-per-connection breakdown.**
   You measured 157 KB/connection in aggregate. Break it down: how much is the
   WebSocket session object, the STOMP subscription registry, the outbound
   buffer, your `SessionRegistry` entry, and the TCP socket buffers?

   Use `jcmd VM.native_memory summary` and a heap histogram at two connection
   counts, then subtract. Identify the single largest contributor and propose a
   concrete change that would halve it.

3. **Prove the outbound queue is the bottleneck — don't just believe it.**
   Design an experiment that distinguishes "outbound channel saturation" from
   "CPU saturation" and "GC pressure" as the cause of the knee. You will need to
   vary one at a time.

   Hints: what happens if you raise `maxPoolSize` alone? If you shrink the
   payload to 5 bytes? If you switch to a collector with different pause
   characteristics? Report which intervention moves the knee and which doesn't.

4. **Build a regression gate.**
   Write a CI-runnable k6 script (5 minutes max) with thresholds derived from
   your baseline, that exits non-zero on regression. It must be stable enough not
   to fail spuriously — run it 10 times and report the false-positive rate.

   Then deliberately introduce a regression (add a `synchronized` block to the
   send path, per Module 01) and prove the gate catches it.

5. **Model the capacity plan.**
   Given your measured knee, produce a table answering: how many nodes do you
   need for 100,000 concurrent users, at average room sizes of 10, 50, 200, and
   1,000, with each user sending 1 message per 5 minutes?

   State every assumption. Then identify the room size at which your answer
   becomes "this architecture doesn't work" and explain what would have to change.

6. **Stretch — measure with the generator on a separate machine.**
   Everything so far ran the generator and server on one host, which means they
   competed for CPU and used loopback (no real network stack, no real MTU, no
   packet loss). Re-run the ceiling test with the generator on a second machine
   (or a `kind`/VM guest).

   Report how much the numbers moved and in which direction. Explain the two
   competing effects — freed CPU vs real network cost — and which dominated.

## Success criteria

- [ ] Closed vs open loop p99s are reported side by side, with the request-count
      difference explaining the gap
- [ ] The 157 KB/connection is broken into named components summing to roughly
      the total, with the largest identified
- [ ] An experiment isolates outbound-queue saturation from CPU and GC, with
      results for each intervention
- [ ] A CI gate exists, has a measured false-positive rate under 10%, and catches
      an injected regression
- [ ] A capacity table covers 4 room sizes with stated assumptions and a named
      breaking point
- [ ] Stretch: two-host numbers are compared to single-host, with the direction
      of the change explained
