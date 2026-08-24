# Challenge 22 — Prove It, Break It, Defend It

Solutions in [`solutions/`](./solutions/). Try first.

The lab built the system, hit the target and passed the drills. That is the
*passing* capstone. These tasks are the difference between a system that works and
a design you would put your name on: find your own ceiling, break yourself in a way
the drill list never imagined, spend your one improvement on the right thing, and
survive three people who think you are wrong.

## Tasks

1. **Find your own knee, then plan for 1,000,000 connections.**
   Push the acceptance test past 100,000 until an SLO breaks. Record *exactly*
   which one broke first, at what number, and which resource was binding — then
   check that resource against Part A's arithmetic and report how wrong the model
   was.

   Then produce a capacity plan for 1,000,000 concurrent connections: worker
   count, channel-layer shard count, Redis and Postgres topology, monthly cost, and
   **the two things that break before you get there**. At least one of them must be
   something the JVM twin does not have.

2. **Break your system in a way the drills didn't.**
   The chaos suite is a fixed list, which means it proves you handle the failures
   you already thought of. Design one failure it does not cover that you believe
   your system survives, and one you believe it does not. Run both.

   At least one must be **Python-specific** — a failure that exists because of the
   GIL, the event loop, the threadpool, or the sync/async boundary, and that would
   not exist on the JVM. Fix it, or document it as a named production gap with a
   proposed remediation and a release-blocker verdict.

3. **Spend your one improvement correctly.**
   Pick the single change with the best cost/benefit from everything you measured
   across 22 modules. Implement it, measure before and after against the full
   acceptance test, and justify it over the alternatives.

   The trap is real and you should expect to fall into it: **the change with the
   best benefit-per-line may improve a resource that is not binding.** Show the
   candidate you rejected for exactly that reason, with both numbers.

4. **Write the on-call runbook, then have it blind-tested.**
   For each of the four SLOs: the alert (with its burn-rate windows), the first
   three diagnostic steps, the likely causes ranked by probability, and the
   remediation. Then have someone inject a drill *without telling you which* and
   follow the runbook — Module 18's method.

   Report the time to diagnosis for each, and every place the runbook sent you
   somewhere useless. A failure with no runbook entry is a finding; a failure with
   no *alert* is a worse one.

5. **Defend the design against three real objections.**
   Take the three strongest objections a senior engineer would raise. For each,
   either concede and revise the review, or rebut with a measurement.

   One of the three must attack your **runtime** — the choice to hold 100,000
   sockets in CPython at all. "It depends" is not an answer; a number is.

## Stretch

6. **The thing you'd build next.**
   Identify the single most valuable capability not in the course — search at
   scale, threads, voice, federation, a bot platform. Sketch its architecture,
   name the module it most disrupts, and estimate the effort.

   Then answer the harder question: **which of your ten architecture-review
   decisions does it re-open?** The instructive feature is the one that looks like
   "just add a service" and turns out to invalidate a decision you already made.

## Success criteria

- [ ] Your own knee measured, the first-breaking SLO and binding resource named,
      and the arithmetic's error reported as a percentage
- [ ] A 1,000,000-connection capacity plan with shard count, cost, and two named
      breaking points, one of which is specific to the Python process model
- [ ] Two novel failures run — one survived, one not — with at least one that
      could only happen on this runtime; the failure fixed or documented as a gap
      with an explicit release-blocker verdict
- [ ] One measured improvement with before/after acceptance numbers, plus a
      rejected candidate whose benefit landed on a non-binding resource
- [ ] A four-SLO runbook that survives a blind test, with time-to-diagnosis per
      drill and every dead end recorded
- [ ] Three strong objections — including one against the runtime — each conceded
      and revised, or rebutted with a number
- [ ] Stretch: a next-capability sketch naming the architecture-review decision it
      re-opens, with an effort estimate
