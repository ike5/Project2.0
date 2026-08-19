# Challenge 01 — Reference Solution

### 1. Measuring the reconcile loop

```bash
for i in 1 2 3; do
  kubectl apply -f manifests/bucket.yaml >/dev/null
  kubectl wait --for=condition=Ready bucket/declared-bucket --timeout=2m >/dev/null
  awslocal s3 rb s3://declared-bucket >/dev/null 2>&1
  START=$(date +%s)
  until awslocal s3 ls 2>/dev/null | grep -q declared-bucket; do sleep 2; done
  echo "run $i: $(( $(date +%s) - START ))s"
done
```

Typical output — note the wide spread:
```
run 1: 43s
run 2: 8s
run 3: 61s
```

**Why the range?** The provider polls each resource on a fixed interval (default
`--poll-interval=1m`), but each resource's timer started when *it* was last
reconciled. Delete a bucket right before its tick and recovery is near-instant;
delete it right after and you wait almost the full interval. So expected recovery is
uniformly distributed between 0 and the poll interval — **the mean is about half the
interval, and the worst case is the whole thing.**

**Tuning it.** The interval is a provider flag, set via a `DeploymentRuntimeConfig`:

```yaml
apiVersion: pkg.crossplane.io/v1beta1
kind: DeploymentRuntimeConfig
metadata:
  name: fast-poll
spec:
  deploymentTemplate:
    spec:
      selector: {}
      template:
        spec:
          containers:
            - name: package-runtime
              args:
                - --poll-interval=10s
---
apiVersion: pkg.crossplane.io/v1
kind: Provider
metadata:
  name: provider-aws-s3
spec:
  package: xpkg.upbound.io/upbound/provider-aws-s3:v1.21.0
  runtimeConfigRef:
    name: fast-poll
```

**The trade-off:** every poll is an AWS API call, *per managed resource*. At 10s with
2,000 managed resources that's 200 calls/second against your account — you will hit
API rate limits, and throttling degrades everything including genuine changes. AWS
rate limits are per-account, so one aggressive control plane can break unrelated
services.

The right answer in production is usually to **leave the interval at 1–10 minutes**
and accept that drift correction is measured in minutes. If you need faster, the
answer isn't polling harder — it's event-driven reconciliation (EventBridge →
webhook), which some providers support.

### 2. A change Crossplane will not correct

Add a tag to the bucket directly in AWS:

```bash
kubectl apply -f manifests/bucket.yaml
kubectl wait --for=condition=Ready bucket/declared-bucket --timeout=2m

awslocal s3api put-bucket-tagging --bucket declared-bucket \
  --tagging 'TagSet=[{Key=rogue,Value=added-by-hand}]'

sleep 90
awslocal s3api get-bucket-tagging --bucket declared-bucket
```
The `rogue` tag is **still there**. Crossplane never removes it.

Other examples that also survive: enabling versioning by hand, adding a lifecycle
rule, uploading objects.

**The rule:** Crossplane reconciles the fields present in `spec.forProvider`, plus
whatever the provider's resource schema explicitly covers. A field you never set is
generally treated as "don't care" rather than "must be empty" — and separate concerns
like versioning live in *entirely different* managed resources
(`BucketVersioning`, `BucketLifecycleConfiguration`), which Crossplane doesn't manage
unless you create them.

**Why this matters:** "Crossplane corrects drift" is true but narrower than it
sounds. It corrects drift *in what you declared*. Anything you didn't declare is
unmanaged, and someone can change it freely. If you need a property enforced, you
must declare it — and if you need to prevent all out-of-band change, you need IAM
policy or SCPs denying console writes, not just Crossplane.

If you *do* want tags reconciled exactly, declare them:
```yaml
spec:
  forProvider:
    region: us-east-1
    tags:
      owner: platform
```
Now the rogue tag is removed on the next reconcile, because `tags` is a managed field.

### 3. The decision memo

> **To:** VP Engineering
> **From:** Platform Engineering
> **Re:** Adopting Crossplane for application infrastructure
>
> **Recommendation: adopt Crossplane for new application infrastructure over the next
> two quarters, while leaving our foundational network and account setup in
> Terraform.** This is a targeted change, not a migration.
>
> **Why this helps us specifically**
>
> 1. **Removes the platform team from the critical path.** Our 3-day lead time for a
>    database is almost entirely queueing — the Jenkins job takes 11 minutes. With
>    Crossplane, a service team applies a 10-line file into their own namespace and
>    gets a database in minutes. We stop being a ticket queue for 40 teams.
> 2. **Drift stops being invisible.** Our Terraform runs on merge, so between
>    merges we have no idea whether production matches the repo. A control plane
>    re-checks every resource continuously and repairs it. Our last two incidents
>    both involved a console change nobody noticed for weeks.
> 3. **Credentials stop being copied by hand.** Today a human moves each database
>    password from Terraform state into a Kubernetes Secret. Crossplane writes it
>    directly into the namespace, so no person ever sees a production password. This
>    closes an audit finding we already have open.
>
> **Honest risks**
>
> 1. **We take on operating a control plane.** Crossplane is a system with an uptime
>    requirement. If it's down, nobody provisions. We'd need it on a dedicated
>    cluster with monitoring and a tested restore path — real work we must staff.
> 2. **There is no `terraform plan` for live changes.** Our engineers rely on
>    reviewing a plan before apply. Crossplane acts on merge. A bad composition can
>    affect many services at once, which is a genuinely larger blast radius than a
>    bad module. Mitigation exists (pinned composition revisions, staged rollout),
>    but it is a real change in how we work and it needs discipline we don't yet have.
> 3. **Composition is a new skill, and the team is two people.** Writing good
>    platform APIs is harder than writing Terraform modules. If both engineers who
>    learn it leave, we own a system nobody understands. **This is the risk that
>    would change my recommendation:** if we can't fund training for at least four
>    engineers, we should not do this.
>
> **First 90 days**
>
> - *Weeks 1–4:* Two engineers train. Stand up Crossplane on a non-production cluster.
>   No production traffic.
> - *Weeks 5–8:* Ship exactly one API — `Bucket` — to two willing teams. It is the
>   lowest-risk resource we have. Measure lead time against the current baseline.
> - *Weeks 9–12:* If lead time drops and nothing broke, add `Database`. Write the
>   runbook. Decide at the end of the quarter whether to continue, with data.
>
> We keep Terraform for VPCs, accounts, and IAM boundaries. Those change rarely,
> benefit from an explicit plan step, and are exactly where a control plane's
> autonomy is a liability rather than a feature.

**What makes this a good memo:** the recommendation is scoped (not "replace
Terraform"), the benefits cite *our* numbers, one risk is labelled as decision-changing,
and the plan has a go/no-go gate with a metric.

### 4. Stretch — closing the password seam

The mechanism has three parts, and you'll build it in Module 09:

1. The RDS managed resource generates its own password and writes it, plus the
   endpoint and port, into a Kubernetes Secret:
   ```yaml
   kind: Instance
   spec:
     forProvider:
       autoGeneratePassword: true
       passwordSecretRef: { namespace: crossplane-system, name: db-pw, key: password }
     writeConnectionSecretToRef: { namespace: team-a, name: db-conn }
   ```
2. The composition surfaces those as the **XR's** connection details, so the whole
   composite has one Secret describing how to reach it.
3. The same composition creates the Deployment, referencing that Secret:
   ```yaml
   env:
     - name: DATABASE_PASSWORD
       valueFrom:
         secretKeyRef: { name: db-conn, key: password }
   ```

The password is generated inside the cluster, stored only in a Secret, and injected
into the Pod. **No human is ever in the loop, so there is no step for a human to get
wrong.** That is what "removing the seam" means in practice — not automating the
copy, but deleting the need for it.
