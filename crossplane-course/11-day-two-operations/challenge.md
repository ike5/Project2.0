# Challenge 11 — Operate It

Solutions in [`solutions/`](./solutions/). Try first.

## Tasks

1. **Write the rollout runbook.** Your team is about to change the `XDatabase`
   composition to add automated backups. There are 40 `XDatabase` XRs in production
   across 12 teams. Write the runbook an on-call engineer would follow, including:
   - Pre-flight checks and their pass criteria
   - The canary selection criteria (which XR, and why that one)
   - Explicit go/no-go gates with observable conditions
   - The rollback procedure and its known limits
   - Who to notify and when

   Write it so someone who has never used Crossplane could execute it at 3 a.m.

2. **Automate the safety.** Extend `preflight.sh` to also detect:
   - A composed resource being **removed** from a composition (which deletes it)
   - A change to an `external-name` annotation template (which orphans and recreates)
   - A `deletionPolicy` changing from `Orphan` to `Delete` (which removes protection)

   Each should print a distinct, actionable warning.

3. **Find the pinning problem.** Pin ten XRs across three different revisions, then
   write a script that reports: which revisions are in use, how many XRs on each, how
   old each revision is, and which XRs are more than one revision behind. This is the
   report a platform team actually needs to avoid revision sprawl.

4. **Build a real scheduled job.** Using the CronJob pattern rather than the alpha
   Operation, build a job that runs nightly and: finds every managed resource that has
   been `Synced=False` for more than an hour, and posts a summary somewhere
   (a ConfigMap is fine). Scope its RBAC to the minimum.

   Then explain why "Synced=False for more than an hour" is a better alert than
   "Synced=False".

5. **Stretch — automate the canary.** Write a script that performs a full canary
   rollout: pins all XRs, applies the new composition, moves one canary, waits for it
   to be healthy for N minutes, then moves the rest in batches of five with a health
   check between each — and aborts, rolling back, on the first failure.

## Success criteria
- [ ] A runbook a Crossplane novice could execute under pressure, with observable
      go/no-go gates.
- [ ] `preflight.sh` detects all three additional destructive patterns with distinct
      messages.
- [ ] Your revision report shows usage counts, ages, and which XRs are behind.
- [ ] A working nightly job with minimal RBAC, and a justification for the one-hour
      threshold.
- [ ] You can explain why a composition rollback doesn't undo a destructive change.
