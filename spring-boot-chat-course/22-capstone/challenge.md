# Challenge 22 — Prove It, and Extend It

Solutions in [`solutions/`](./solutions/). Try first.

The capstone lab built and measured the system. These tasks push past the target
into the decisions and extensions that separate a passing capstone from a design
you'd stake your name on.

## Tasks

1. **Find your own knee, then plan capacity for 1,000,000 users.**
   Push the acceptance test past 100k until an SLO breaks. Record exactly what
   broke first and at what number.

   Then produce a capacity plan for 1,000,000 concurrent users: node count,
   Redis topology, Postgres sharding, cost, and the two things that break before
   you get there.

2. **Break your own system in a way the drills didn't.**
   The chaos suite is a fixed list. Design one failure it doesn't cover that you
   believe your system handles, and one you believe it doesn't. Run both.

   Fix the one that fails, or — if the fix is out of scope — document it as a
   named production gap with a proposed remediation.

3. **Make one measured improvement.**
   Pick the single change with the best cost/benefit from everything you've
   measured across the course. Implement it, measure the before and after against
   the acceptance test, and justify why this one over the alternatives.

4. **Write the on-call runbook.**
   For each of the four SLOs, write the alert, the first three diagnostic steps,
   the likely causes ranked by probability, and the remediation. Then have
   someone follow it during a drill you inject blind (Module 18's method).

5. **Defend the design against three real objections.**
   Take the three strongest objections a senior engineer would raise to your
   architecture. For each, either concede and revise, or rebut with a
   measurement. "It depends" is not an answer; a number is.

6. **Stretch — the thing you'd build next.**
   Identify the single most valuable feature or capability not in the course
   (message search at scale, threads, voice, a bot platform, federation). Sketch
   its architecture, name the module it would most disrupt, and estimate the
   effort.

## Success criteria

- [ ] Your own knee found and characterized; a 1M-user capacity plan with a cost
      and two named breaking points
- [ ] A novel failure your system survives and one it doesn't, both run; the
      failure fixed or documented as a gap
- [ ] One measured improvement with before/after acceptance numbers and a
      justification over alternatives
- [ ] A four-SLO runbook that survives a blind test by someone else
- [ ] Three strong objections each conceded-and-revised or rebutted with a number
- [ ] Stretch: a next-feature sketch with its architecture, blast radius, and
      effort estimate
