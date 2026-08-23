# Challenge 18 — Find the Failure You Didn't Test

Solutions in [`solutions/`](./solutions/). Try first.

The lab ran eleven drills and every one of them passed. That is the least
interesting possible outcome of a chaos exercise: you tested the failures you
already imagined, using the mechanism you built to survive them. Real chaos
engineering starts here — with the failures nobody wrote a drill for, and with
the parts of the system that *aren't* the datastore.

> **Authorized testing only**: everything below runs against your own laptop.
> **Every drill runs with a load test on.** A drill without one tells you the
> cluster reconfigured; a drill with one tells you how many users noticed.

## Tasks

1. **Move the Redis tier off a single Sentinel-managed dataset, live.**
   Traffic running, zero downtime. Then verify every Lua script, every
   multi-key operation and the channel layer itself still work.

   You will hit at least one `CROSSSLOT` error and one thing that is *worse*
   than an error — a `channels_redis` behaviour that silently gives you
   something other than what you asked for. Find both. Explain why the hash tags
   you placed in Modules 08 and 11 were placed where they were, and name the one
   place they were placed wrong.

2. **Design and run three drills the lab didn't.**
   The lab covered kill, pause, partition, brownout and deploy — all of them
   *whole-container* failures of *datastores*. Find three failure modes it
   misses. Think about disk, clocks, DNS, and slow dependencies — and think
   about the fact that each app container runs **several Uvicorn worker
   processes** that can fail independently of it.

   At least one drill must reveal a real weakness. Fix it, and re-run to prove
   the fix.

3. **Find the split-brain you haven't prevented.**
   The lab proved fencing works for Redis (Sentinel demoted the returning
   primary) and Postgres (Patroni's leader-lock TTL). Both are datastores with
   a consensus protocol. **Your application has components with neither.**

   Find a component where a partition causes divergence, duplicate work, or a
   destructive mass action. (Hint: the Celery outbox relay, the presence
   sweeper, Module 21's reconciliation loop, and Module 14's shard-assignment
   map are four different answers, and at least two are exploitable today.)
   Prove it with a drill, then fix it — and prefer a fix that reuses something
   already fenced over adding a new lock.

4. **Make the drills run in CI.**
   Turn `drill.sh` into an automated suite that runs on every merge to `main`,
   with pass/fail thresholds on RTO, RPO and p99.

   It must complete in **under 15 minutes** and have a **false-positive rate
   below 5%**. Report both — and report honestly how many runs it takes to
   *demonstrate* a rate below 5%, rather than to merely observe zero failures.

5. **Price the HA stack, then halve it.**
   Compare the full HA stack against `compose.dev.yml` on four dimensions:
   latency, throughput, host resources, and monthly cost (use published cloud
   list prices — this is a cost model, not a deployment).

   Then answer the question a founder will actually ask: **what would you give
   up to halve the cost, and what does that do to RTO and RPO?** The good answer
   is probably not "fewer replicas."

## Stretch

6. **Write the runbook, then have someone else use it.**
   For each drill: the alert that fires, the first three diagnostic commands,
   the remediation, and the escalation criterion.

   Then have someone who did not build the system follow it while you inject a
   failure without telling them which one. Record where they got stuck. The
   places they got stuck are your real findings.

## Success criteria

- [ ] The Redis tier migrated live with measured downtime, every `CROSSSLOT`
      found and fixed, and the silent `channels_redis` behaviour identified and
      explained
- [ ] Three new drills designed and run under load; at least one reveals a real
      weakness that is then fixed and re-proven
- [ ] A partition-induced divergence or destructive mass action found in an
      *application* component, proven with a drill, and fixed
- [ ] A CI drill suite that runs in under 15 minutes, with thresholds, a
      measured false-positive rate, and an honest statement of the confidence
      interval on that measurement
- [ ] HA costed on four dimensions, with a halving option whose RTO/RPO
      consequences are stated in terms a non-engineer can decide on
- [ ] Stretch: a runbook that survives a blind test by someone else, with the
      sticking points recorded and fixed
