# Challenge 13 — Threat-Model Your Own Platform

Solutions in [`solutions/`](./solutions/). Try first.

## Tasks

1. **Find the hole.** The lab's tenancy model has at least one real weakness that
   none of the eight attacks exercised. Find it, demonstrate it working as an attack,
   and fix it.

   (Hints to consider: what can a developer do with `update` that they can't with
   `create`? What does the composition trust that it shouldn't? What happens to a
   connection Secret when an XR moves?)

2. **Write the threat model.** Produce a table for your platform: threat, likelihood,
   impact, control, and **which layer** enforces it. Include at least one threat you
   have decided **not** to mitigate, with the reasoning — a threat model that mitigates
   everything is a threat model nobody believed.

3. **Add a third tenant with different rules.** `tenant-gamma` is a contractor team:
   they may create `XBucket` but never `XDatabase`, they are capped at 2 buckets, all
   their resources must carry a `contract-end-date` label, and they cannot read
   connection secrets at all. Implement it.

4. **Automate the audit.** Turn `audit.sh` into a CronJob that runs daily and writes
   its findings to a ConfigMap, with its own minimal RBAC. Then define which findings
   should page someone at 3 a.m. versus wait for the morning — and justify the split.

5. **Stretch — the escape.** Assume an attacker has compromised one developer's
   ServiceAccount token in `tenant-alpha`. Write the incident response: what can they
   reach, what do you do in the first 10 minutes, how do you determine what they did,
   and what would have limited the blast radius further?

## Success criteria
- [ ] You found a genuine weakness, demonstrated it as a working attack, and fixed it.
- [ ] Your threat model names the enforcing layer for each control and includes an
      accepted risk with reasoning.
- [ ] `tenant-gamma` has all four restrictions working, demonstrated by attacks that
      fail.
- [ ] The audit CronJob runs with minimal RBAC, and you justified the page-now vs
      wait-until-morning split.
- [ ] You can explain why a control enforced by AWS beats one enforced by your
      cluster.
