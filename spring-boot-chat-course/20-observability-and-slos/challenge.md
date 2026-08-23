# Challenge 20 — Make the Dashboard Answer Questions

Solutions in [`solutions/`](./solutions/). Try first.

## Tasks

1. **Answer five incident questions from the dashboard alone.**
   Have someone inject one of Module 18's drills without telling you which. Using
   only Grafana, answer: what broke, when, how many users were affected, was data
   lost, and is it fixed.

   Record how long each answer took. Any question you cannot answer is a missing
   panel — add it.

2. **Set the SLO targets from data, not from round numbers.**
   99.99% and 500 ms were asserted. Derive defensible targets by measuring: what
   latency users actually notice, what your system achieves at p50 over 30 days,
   and what a 9 of additional reliability would cost.

   Then write the SLO document you'd put in front of a product owner.

3. **Find and fix a cardinality bomb before it fires.**
   Add a metric that looks reasonable and explodes cardinality under real usage.
   Predict the series count before deploying, then measure it.

   Then build a guard: a CI check or a runtime limit that prevents the next one.

4. **Trace a message end to end across every hop.**
   Produce a single trace covering client → node A → Postgres → outbox → relay →
   Redis Stream → node B → client, including the browser side.

   Report where context is lost and what it took to fix each break.

5. **Alert on the thing that has no metric.**
   Some failures have no natural signal: a room whose sequence has a permanent
   gap, a user whose messages consistently fail, a slow leak in the dedup cache.

   Pick three and design detection for each. At least one must be a derived
   metric, and at least one must be a probe.

6. **Stretch — cost the observability stack.**
   Measure what your instrumentation costs: metric storage, trace storage, log
   volume, and the CPU/latency overhead on the application.

   Then halve it without losing the ability to answer Task 1's five questions.

## Success criteria

- [ ] Five incident questions answered from the dashboard, timed, with missing
      panels identified and added
- [ ] SLO targets derived from measured user tolerance and achieved performance,
      written as a document with costs
- [ ] A cardinality bomb predicted, measured, and a preventive guard implemented
- [ ] A complete end-to-end trace including the browser, with every context break
      documented
- [ ] Three signal-less failures given detection, including one derived metric and
      one probe
- [ ] Stretch: observability cost measured and halved with capability preserved
