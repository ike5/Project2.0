# Challenge 06 — Prove Your Numbers

Solutions in [`solutions/`](./solutions/). Try first.

Every task below produces a number you will be asked to defend in Module 22's
architecture review. Write them into `apps/pulse/results-06.md` as you go, with
the reference machine and the scale factor attached — a measurement without its
conditions is an opinion.

## Tasks

1. **Quantify coordinated omission a second time, in k6.**
   The lab demonstrated it with Locust's two user classes. Now do it with k6's
   two executors against the same server and the same 5-second stall: one
   scenario using `constant-vus` with a send-then-await-reply loop, one using
   `constant-arrival-rate`.

   Report both p99s, both request counts, and — the part Locust cannot give you
   — `dropped_iterations`. Then explain what a non-zero `dropped_iterations`
   means about the number you just measured, and at what value you would throw
   the run away.

2. **Break the 63 KB per connection into named components.**
   You measured 46.2 KB of application memory and 16.8 KB of kernel socket
   buffers in aggregate. Decompose both halves: the consumer instance, the
   asyncio Task, the `websockets` protocol object and its buffers, the ASGI
   `scope` dict, the channel-layer group entry and mailbox, and the kernel's
   `tcp_rmem`/`tcp_wmem`.

   Use `tracemalloc`, `pympler` or `sys.getsizeof` walks at two connection
   counts and subtract; use `/proc/net/sockstat` and `sysctl net.ipv4.tcp_rmem`
   for the kernel half.

   Then implement **two** reductions and measure each: (a) trim `scope` —
   Module 04 flagged that every request header is retained for the whole
   connection lifetime, and most of them are never read again; (b) size the
   kernel socket buffers for 200-byte messages instead of for bulk transfer.
   Report the new bytes-per-connection and the new connections-per-worker
   ceiling, and state what each reduction would break.

3. **Build a regression gate that a team would not disable.**
   Write a CI-runnable k6 script (5 minutes maximum) with thresholds derived
   from your baseline that exits non-zero on regression. Run it **ten times
   unchanged** and report the false-positive rate. If it is above 10%, fix it —
   and say whether you fixed it by loosening the threshold or by changing the
   decision rule, and what each choice costs.

   Then inject a regression the gate must catch: revert the encode-once change
   from Part E Step 3 (or add a `time.sleep(0.05)` to `_on_message_create`).
   Show the gate failing, and show *which* threshold failed — p50 and p99 fail
   for different reasons and you should be able to say which one you tripped.

4. **Model the capacity plan.**
   From your measured knee, produce a table answering: how many worker
   processes do you need for 250,000 concurrent users at average room sizes of
   10, 50, 200, 1,000 and 5,000, with each user sending one message per five
   minutes?

   State every assumption explicitly — including the two the lab handed you
   (63 KB per connection, 150,000 outbound msg/s per core) and the one it did
   not (users are in more than one room).

   Then identify the room size at which your answer becomes "this architecture
   does not work", and name the three things that would have to change. Compare
   your crossover point to the JVM twin's
   [`06-load-testing-harness`](../../spring-boot-chat-course/06-load-testing-harness/):
   it measured the same crossover on a runtime with 3× the per-node knee. Does
   the *shape* of the conclusion change, or only the numbers?

5. **Stretch — move the generator to a second machine.**
   Everything so far ran the generator and the server on one host, sharing
   eight cores and talking over loopback: no MTU, no NIC interrupts, no driver,
   ~5 µs RTT. Re-run the baseline and the knee hunt with k6 on a second machine
   (or a `kind` node, or a VM guest).

   Report how far every number moved and in which direction, then explain the
   two competing effects — freed CPU versus real network cost — and which one
   dominated at the median and which at the tail. Finally: name the confounder
   your two-host setup has that the single-host setup did not, and how you
   would detect it.

## Success criteria

- [ ] Closed and open k6 p99s are reported side by side with request counts,
      `dropped_iterations`, and a stated throw-away threshold
- [ ] 63 KB is decomposed into named components summing to roughly the total,
      split across application and kernel
- [ ] Two memory reductions are implemented and measured, each with the thing
      it would break named
- [ ] A CI gate exists, has a measured false-positive rate under 10% over ten
      runs, and catches an injected regression on a named threshold
- [ ] A capacity table covers five room sizes with every assumption stated, a
      named breaking point, and a comparison to the JVM twin's conclusion
- [ ] Stretch: two-host numbers are compared to single-host with the direction
      of each change explained and one remaining confounder named
