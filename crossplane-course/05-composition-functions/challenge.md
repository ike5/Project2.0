# Challenge 05 — Make the Template Do the Work

Solutions in [`solutions/`](./solutions/). Try first.

## Tasks

1. **Rewrite the ugly one.** The Module 04 challenge solution had a `BucketPolicy`
   that always existed and flipped between `Allow` and `Deny`, plus a regexp transform
   doing a template's job. Rewrite `XStaticSite` with `function-go-templating` so that:
   - when `public: false`, the `BucketPolicy` resource **does not exist at all**;
   - the policy JSON is built with a template, not a regexp;
   - the public access block settings are derived from the boolean readably.

   Develop it entirely with `crossplane render` — do not apply until the output is
   right. Then compare the two compositions and write two sentences on which you'd
   rather maintain.

2. **Per-environment sizing without a map explosion.** Extend `XDataLake` so each zone
   can be declared as an object rather than a bare string:

   ```yaml
   zones:
     - name: us-east-1a
       tier: hot
     - name: us-east-1b
       tier: cold
   ```

   `hot` zones get 7-day retention and versioning; `cold` zones get 365-day retention
   and no versioning. Update the XRD schema and the template. This requires iterating
   over a list of objects and branching inside the loop.

3. **Compute something real.** Add a `status.estimatedMonthlyCost` to `XDataLake`,
   calculated in the template as `$5 per hot zone + $1 per cold zone + $10 if audit is
   enabled`. Return it as a formatted string like `"$26.00"`. You'll need Sprig's
   arithmetic and formatting functions.

   Then explain: why is computing this in a template a *questionable* idea in
   production, and where should this logic really live?

4. **Readiness that means something.** By default the XR is `Ready` when all composed
   resources are ready. Change your `XDataLake` composition so the XR is `Ready` as
   soon as the **zone buckets** are ready, without waiting for the audit bucket.
   Justify when this is a good idea and when it's dangerous.

5. **Stretch — build a render test harness.** Write a script that runs
   `crossplane render` over a directory of test XRs and asserts properties of the
   output: that a `public: false` site produces no `BucketPolicy`, that a 3-zone lake
   produces exactly 6 resources, that every rendered resource has a
   `crossplane.io/external-name`. Make it exit non-zero on failure so it can run in
   CI. This is the seed of what you'll formalise in Module 14.

## Success criteria
- [ ] `XStaticSite` renders **no** `BucketPolicy` when `public: false`, verified with
      `crossplane render`.
- [ ] Zones accept objects with tiers, and hot/cold produce demonstrably different
      resources.
- [ ] `status.estimatedMonthlyCost` computes correctly, and you explained why this
      logic is questionable in a template.
- [ ] The XR reaches `Ready` without waiting for the audit bucket, and you justified
      the trade-off.
- [ ] You can state from memory why `setResourceNameAnnotation` must never be keyed to
      a list index.
