# Challenge 20 — Make the Dashboard Answer Questions

Solutions in [`solutions/`](./solutions/). Try first.

A dashboard is not judged by how many panels it has. It is judged by how long it
takes someone who did not build the system to answer the five questions every
incident asks. This challenge measures that, with a stopwatch, and then makes the
numbers on it defensible to someone who has to pay for them.

## Tasks

1. **Answer five incident questions from the dashboard alone, timed.**
   Have someone inject one of Module 18's drills without telling you which.
   Using only Grafana — no `docker logs`, no `kubectl`, no `redis-cli` — answer:
   what broke, when, how many users were affected, was data lost, and is it
   fixed.

   Record how long each answer took. **Any question that took minutes is a
   missing panel, not a slow person.** Add the panels, then re-test with a
   different drill and report the new times.

2. **Set the SLO targets from data instead of from round numbers.**
   500 ms and 99.99% were asserted in the lab. Derive defensible targets: what
   latency users actually notice, what the system achieves over 30 days, where
   the budget is being spent, and what one more nine would cost.

   Then write the SLO document you would put in front of a product owner —
   including the paragraph explaining why you chose the *lower* target.

3. **Find and fix a cardinality bomb before it fires.**
   The lab showed the obvious one (a `room` label). Find a **Python-specific**
   one that a label audit would not catch — something about the runtime rather
   than the metric definitions.

   Predict its cost before deploying, measure it, then build a guard that stops
   the next one: a CI check, a runtime limit, or both.

4. **Trace a message end to end, including the browser.**
   Produce one trace covering client → node A → Postgres → outbox → Celery relay
   → Redis Stream → node B → client. Report every place context was lost and
   what it took to reconnect it.

   Then answer the harder question: what does the browser half cost, and is it
   worth shipping to every user?

5. **Alert on the failures that have no natural signal.**
   Some failures produce no error, no latency spike and no metric: a room whose
   sequence has a permanent gap, a socket made deaf by `group_expiry`
   (Module 11), a Celery outbox relay that is running and doing nothing.

   Pick three. Design detection for each. At least one must be a **derived**
   metric and at least one must be a **probe**. State each one's false-positive
   rate.

## Stretch

6. **Cost the observability stack, then halve it.**
   Measure what your instrumentation costs: Prometheus memory and disk, trace
   storage, log volume, and the CPU and latency overhead on the application
   itself — measured, not assumed.

   Then halve the total **without losing the ability to answer Task 1's five
   questions**, and prove it by re-running Task 1.

## Success criteria

- [ ] Five incident questions answered from the dashboard alone and timed, with
      every slow answer traced to a missing panel that is then added and
      re-tested
- [ ] SLO targets derived from measured user tolerance and achieved performance,
      with a budget breakdown and a priced next nine, written as a document
- [ ] A Python-specific cardinality or exposition bomb predicted, measured, and
      prevented by an automated guard
- [ ] A complete end-to-end trace including the browser, with every context
      break documented and the browser half's cost stated
- [ ] Three signal-less failures given detection — at least one derived metric,
      at least one probe — each with a measured false-positive rate
- [ ] Stretch: observability cost measured and halved, with Task 1 re-run to
      prove the capability survived
