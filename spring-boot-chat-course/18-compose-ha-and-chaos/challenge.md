# Challenge 18 — Find the Failure You Didn't Test

Solutions in [`solutions/`](./solutions/). Try first.

## Tasks

1. **Migrate from Sentinel to Redis Cluster, live.**
   Move the fan-out from a Sentinel-managed single dataset to a 3-primary
   Cluster, with traffic running. Then verify every Lua script and multi-key
   operation still works.

   You will find at least one `CROSSSLOT` error. Fix it, and explain why the hash
   tags from Modules 08 and 11 were placed where they were.

2. **Design and run three drills the lab didn't.**
   The lab covers kill, pause, partition and brownout. Find three failure modes
   it misses — think about disk, clocks, DNS, and slow dependencies — and run
   them with the same harness.

   At least one should reveal a real weakness. Fix it.

3. **Measure the cost of HA.**
   Compare the full HA stack against the single-node dev stack on: latency,
   throughput, resource usage, and dollar cost (use real cloud pricing).

   Then answer: what would you give up to halve the cost, and what does that do
   to your RTO and RPO?

4. **Make the drills run in CI.**
   Turn the drill harness into an automated suite that runs on every merge to
   main, with pass/fail thresholds on RTO and RPO.

   It must complete in under 15 minutes and have a false-positive rate below 5%
   over 20 runs. Report both.

5. **Find the split-brain you haven't prevented.**
   The lab proved fencing works for Redis and Patroni. Find a component in the
   stack where a partition can still cause divergence or duplicate work.

   (Hint: consider the outbox relay, the presence sweeper, and the shard
   assignment map.) Prove it, then fix it.

6. **Stretch — write the runbook.**
   Produce an on-call runbook for this stack: for each of the eleven drills, the
   alert that fires, the first three diagnostic commands, the remediation, and
   the escalation criterion.

   Then have someone who didn't build the system follow it during a drill you
   inject without telling them which one. Report where they got stuck.

## Success criteria

- [ ] Live Sentinel-to-Cluster migration completes with measured downtime, and
      every `CROSSSLOT` issue is found and fixed
- [ ] Three new drills designed and run; at least one reveals and fixes a real
      weakness
- [ ] HA cost measured on four dimensions with a costed halving option and its
      RTO/RPO consequence
- [ ] A CI drill suite runs under 15 minutes with a measured false-positive rate
- [ ] A remaining split-brain or duplicate-work window is found, proven, and
      fixed
- [ ] Stretch: a runbook exists and survives a blind test by someone else
