# Challenge 12 — Know Before They Tell You

Solutions in [`solutions/`](./solutions/). Try first.

## Tasks

1. **Break one yourself.** Write a *sixth* broken stack with a root cause not covered
   by the five in the lab, plus a short "symptom card" describing only what a user
   would observe. Swap with a colleague (or set it aside for a week and try your own).

   Your stack must be genuinely diagnosable — the evidence has to be reachable through
   `kubectl` and `crossplane trace`.

2. **A dashboard someone would actually use.** Build a Grafana dashboard with the five
   panels from README §7. Then justify each: for every panel, write the sentence
   "I look at this when ___". If you can't finish the sentence, delete the panel.

3. **Alert on the invisible failure.** Stack 5 was completely green and completely
   broken. Design a check that would have caught it.

   (Hints: compare `status` fields against actual cloud state; assert that every
   composed resource's `bucket` reference names a bucket that exists; run
   `crossplane render` in CI and check for name mismatches.)

   Implement at least one, and be honest about what it still misses.

4. **Measure your own recovery.** Have someone apply one of the five broken stacks
   without telling you which. Time yourself from "something is wrong" to correct root
   cause. Do this for all five, record the times, and write down which step in the
   debugging order was slowest and why.

   The goal is under five minutes for all five.

5. **Stretch — a status aggregator.** Write a tool that reports, for every XR in the
   cluster: its readiness, how long it has been in that state, which composed resource
   is blocking it (if any), and the raw cloud error (if any) — in one table.

   This is the "what is broken right now" view a platform on-call actually needs, and
   no built-in command provides it.

## Success criteria
- [ ] Your sixth broken stack has a distinct root cause and is genuinely diagnosable
      from its symptom card.
- [ ] Every dashboard panel has a completed "I look at this when ___" sentence.
- [ ] You implemented a check that catches the Stack 5 class, and stated its limits.
- [ ] You diagnosed all five stacks in under five minutes each, with recorded times.
- [ ] You can recite the debugging order from memory.
