# Challenge 02 — Provider Fluency

Solutions in [`solutions/`](./solutions/). Try first.

## Tasks

1. **A second account.** Real platforms manage more than one AWS account. Create a
   *second* `ProviderConfig` named `sandbox` (point it at the same emulator — the
   mechanism is what matters, not the isolation). Then provision two buckets, one
   through each config, and prove from the objects themselves which config each used.
   Finally, explain what happens to a resource whose `providerConfigRef` names a
   config that doesn't exist — try it and read the error.

2. **Discover an API you've never seen.** Without searching the web, use only
   `kubectl` to answer these about the `BucketLifecycleConfiguration` resource:
   - What is its full `apiVersion`?
   - Which fields under `spec.forProvider` are required?
   - How does it reference its bucket?

   Then write and apply one that expires objects under a `tmp/` prefix after 7 days.
   Verify with `awslocal s3api get-bucket-lifecycle-configuration`.

3. **Tighten the activation policy.** The provided MRAP activates more than this
   module strictly needs. Write your own that activates *only* `buckets` and
   `bucketversionings`, apply it, and determine what happens to the
   `BucketPublicAccessBlock` resource type. Then answer: if a bucket of a
   now-deactivated type still exists in the cluster, what happens to it? Test your
   prediction before you look.

4. **Predict, then verify.** For each of these, write down what you expect *before*
   running it:
   - a) You delete the `aws-creds` Secret while a healthy bucket exists. What happens
     to the bucket over the next 5 minutes?
   - b) You change a bucket's `crossplane.io/external-name` annotation to a name that
     doesn't exist in AWS.
   - c) You `kubectl delete` the `provider-aws-s3` Provider while buckets exist.

   Run each, record what actually happened, and explain any surprises. **(c) is
   destructive to your lab state — do it last, and be ready to reinstall.**

5. **Stretch — measure MRAP's real cost saving.** Install `metrics-server` on your
   kind cluster, then measure the EC2 provider's memory footprint with the default
   catch-all activation policy versus your narrow one from Task 3. Report both
   numbers and the percentage saved. (Restarting the provider pod between
   measurements gives you a fair comparison.)

## Success criteria
- [ ] Two ProviderConfigs exist, and you can show from a resource which one it used.
- [ ] You answered all three discovery questions with `kubectl` alone and applied a
      working lifecycle rule.
- [ ] You wrote a narrower MRAP and correctly predicted the fate of both the
      *type* and any *existing instances* of a deactivated resource.
- [ ] You made written predictions for 4a–c before testing, and explained every
      surprise.
- [ ] You can state the debugging order for a `Synced=False` resource from memory.
