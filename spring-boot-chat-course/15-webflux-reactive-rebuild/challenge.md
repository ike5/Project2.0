# Challenge 15 — Close the Gap From Both Sides

Solutions in [`solutions/`](./solutions/). Try first.

## Tasks

1. **Close the memory gap on the blocking side.**
   WebFlux used 59 KB/connection; virtual threads used 157 KB. Find where the
   difference actually goes (it is not thread stacks — measure, don't assume) and
   reduce the blocking stack's per-connection cost.

   Target: under 100 KB/connection without changing runtime. Report what you
   changed and what it cost.

2. **Add real backpressure to the blocking stack.**
   Implement the four Reactor overflow strategies (`BUFFER`, `DROP_OLDEST`,
   `DROP_LATEST`, `ERROR`) for the blocking fan-out path, as a configurable
   policy.

   Then re-run the past-the-knee benchmark and see how close you get to WebFlux's
   2,140 ms p99 and 3-second recovery.

3. **Find the crossover point.**
   At what connection count, message rate and room size does WebFlux's advantage
   become decisive? Map it as a surface, not a single number.

   Then state, for Pulse's actual projected growth, when (if ever) you cross it.

4. **Measure the debugging tax.**
   Inject the same three bugs into both stacks: a NullPointerException deep in
   fan-out, a connection leak, and an off-by-one in the resume cursor.

   Time yourself finding each. Report the times and what specifically made the
   difference. (Be honest — this is the number that decides most adoptions.)

5. **Prove context propagation works, then break it.**
   Wire MDC logging and a security context through the reactive stack so a trace
   ID appears in every log line for a request. Then find an operator that loses
   it, and show the log line without the ID.

   Explain the mechanism, and what would have caught it in CI.

6. **Stretch — build the hybrid.**
   Keep MVC + virtual threads for the connection layer (where STOMP earns its
   keep) but run the fan-out consumer as a reactive `Flux` with backpressure.

   Measure it against both pure stacks. Is the combination better than either, or
   worse than both?

## Success criteria

- [ ] The per-connection memory difference is attributed to named components,
      and the blocking stack gets under 100 KB/conn
- [ ] Four overflow strategies implemented for the blocking path, with
      past-the-knee numbers compared to WebFlux
- [ ] A crossover surface over three variables, with Pulse's position on it
- [ ] Three bugs timed in both stacks with an honest account of the difference
- [ ] MDC/trace context works reactively, then is broken by a named operator with
      an explanation and a CI check
- [ ] Stretch: the hybrid is measured against both pure stacks with a verdict
