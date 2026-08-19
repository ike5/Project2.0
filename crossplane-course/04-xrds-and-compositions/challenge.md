# Challenge 04 — Design an API Someone Would Want

Solutions in [`solutions/`](./solutions/). Try first.

## Tasks

1. **Design `XStaticSite`.** Your company hosts static marketing sites. Design and
   build a complete platform API for one. The developer should write no more than:

   ```yaml
   apiVersion: platform.acme.io/v1alpha1
   kind: XStaticSite
   metadata:
     name: marketing-site
     namespace: team-web
   spec:
     indexDocument: index.html
     public: true
   ```

   Behind it, compose: a bucket, a website configuration, a public access block whose
   settings *depend on* `spec.public`, and an appropriate ownership control. Surface
   the website endpoint in `status.url` so the developer can find it.

   The interesting part is `public: true` — it must relax the public access block
   **and** attach a bucket policy allowing reads. When `public: false`, everything
   stays locked down. One boolean, two coordinated changes.

2. **Add a computed field.** Extend `XBucket` so the developer can request
   `sizeCategory: small | medium | large`, and the composition maps that to a
   lifecycle transition: `small` → expire at 30 days, `medium` → 90, `large` → 365.
   The developer must not be able to set a raw day count. Use a `map` transform.

3. **Guard against a real mistake.** Your `XBucket` API lets a developer set
   `retentionDays: 1` on a **prod** bucket, which would delete customer data daily.
   Fix this so it's impossible. Implement it **two different ways** and explain the
   trade-off:
   - a) Purely in the XRD's OpenAPI schema.
   - b) In the composition.

   One of these gives a better error message; the other catches more cases. Say which
   is which and when you'd use each.

4. **Version your API.** Add a `v1beta1` version to the `XBucket` XRD that renames
   `retentionDays` to `retention.days` (a nested object). Serve both versions. Then
   answer, with evidence from your cluster: what happens to an existing `v1alpha1` XR?
   Can a developer read it as `v1beta1`? What would you need to add to make that work
   properly, and why is API versioning in Crossplane harder than it first looks?

5. **Stretch — the migration.** Write a second Composition for `XStaticSite` that
   labels itself `provider: gcp` and composes *nothing* (an empty resource list is
   valid). Show that flipping an existing XR's `compositionSelector` from `aws` to
   `gcp` causes Crossplane to delete the AWS resources. Then explain why this makes
   composition selection a genuinely dangerous field to templatize in a GitOps repo,
   and what you'd do about it.

## Success criteria
- [ ] `XStaticSite` works end-to-end; `public: true` and `public: false` produce
      demonstrably different, coherent AWS configurations.
- [ ] `sizeCategory` maps to retention via a transform, with no raw day count
      exposed to the developer.
- [ ] Both guard implementations work, and you explained the trade-off between them.
- [ ] You added `v1beta1`, tested what happens to existing XRs, and explained why
      Crossplane API versioning is harder than CRD versioning alone.
- [ ] You can explain why `matchControllerRef: true` is preferable to patching
      resource names by hand.
