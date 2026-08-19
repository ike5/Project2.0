# Challenge 01 — Argue Both Sides

Solutions in [`solutions/`](./solutions/). Try first.

This module's challenge is unusual: it's mostly **writing and reasoning**, not YAML.
That's deliberate. The technical modules start in Module 02, but an engineer who
can't explain *why* a control plane is the right choice will build the wrong one.

## Tasks

1. **Measure the reconcile loop.** Find out empirically how long Crossplane takes to
   notice and correct drift. Delete a Crossplane-managed bucket in AWS and time how
   long until it returns. Run it three times and report the range. Then find the
   setting that controls it (hint: it's a flag on the provider, configured through a
   `DeploymentRuntimeConfig`) and explain the trade-off in tuning it down to 10s.

2. **Break it in a way that doesn't heal.** Part D showed drift being corrected.
   Construct a change to a bucket that Crossplane will **not** correct, and explain
   why. (Hint: think about the difference between the fields in `spec.forProvider`
   and everything else about a bucket that AWS tracks.) This is a real and important
   limitation — Crossplane only reconciles what it's been told to manage.

3. **Write the decision memo.** Your company runs 40 microservices on EKS. Each needs
   an S3 bucket, sometimes a Postgres, sometimes an SQS queue. Today this is ~4,000
   lines of Terraform in one repo, applied by a Jenkins job that only the two-person
   platform team can trigger. Lead time for a new database: 3 days.

   Write a **one-page memo** to your VP of Engineering recommending whether to adopt
   Crossplane. It must include:
   - A recommendation, stated in the first sentence.
   - Three concrete benefits tied to *this* situation, not generic marketing.
   - **Three honest risks or costs**, including at least one that might change your
     mind.
   - What you'd do in the first 90 days.

   Write it for an executive: no jargon without definition, and no more than a page.

4. **Stretch — find the seam.** In the workflow described in §1 of the README, step 5
   is "someone copies the password by hand into a Kubernetes Secret." Sketch (in
   words or YAML pseudocode — you don't have the tools yet) how Crossplane removes
   that step entirely. You'll build this for real in Module 09; the point is to
   predict the mechanism now.

## Success criteria
- [ ] You measured drift-correction time across three runs and named the setting
      that controls it, with a stated trade-off.
- [ ] You produced a change Crossplane does **not** correct, and explained the rule
      that determines what it does and doesn't watch.
- [ ] Your memo has a recommendation, three situation-specific benefits, three honest
      risks, and a 90-day plan — on one page.
- [ ] You can explain the difference between a provisioning tool and a control plane
      to someone who has never heard of either.
