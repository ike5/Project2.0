# Lab 03 — Import, Protect, and Unstick

**You'll:** adopt a hand-built bucket without recreating it, protect a resource from
deletion, make one read-only, and deliberately wedge a deletion so you can practise
unwedging it. ⏱️ ~70 min.

> Prereqs: Module 02 complete. Providers, MRAP, Secret, and ProviderConfig installed.
> Make sure your `awslocal` shell function from Lab 01 is defined.

---

## Part A — Create "legacy" infrastructure

Simulate a bucket someone made by hand in 2019, long before your team existed:

```bash
awslocal s3 mb s3://legacy-data-2019
awslocal s3api put-bucket-tagging --bucket legacy-data-2019 \
  --tagging 'TagSet=[{Key=created-by,Value=someone-who-left},{Key=year,Value=2019}]'
awslocal s3 ls
```
✅ Expected: `legacy-data-2019` exists.

Crossplane knows nothing about it:
```bash
kubectl get buckets
```
✅ Expected: `No resources found`.

**Your task: bring this under management without touching the data.**

## Part B — The wrong way (understand the failure first)

Before doing it correctly, see why the naive approach fails. Apply a bucket manifest
with no external-name:

```bash
kubectl apply -f - <<'YAML'
apiVersion: s3.aws.upbound.io/v1beta1
kind: Bucket
metadata:
  name: legacy-data-2019
spec:
  forProvider:
    region: us-east-1
  providerConfigRef:
    name: default
YAML
sleep 30
awslocal s3 ls
```
✅ Expected: **still one bucket**, but check *why*:
```bash
kubectl get bucket legacy-data-2019 \
  -o jsonpath='{.metadata.annotations.crossplane\.io/external-name}'; echo
```
✅ Expected: `legacy-data-2019` — Crossplane defaulted the external name to the object
name and, finding a bucket already there, adopted it *by accident*.

**That accident is the danger.** It worked here only because the Kubernetes name
happened to equal the S3 name. Had you named the object `legacy` instead, Crossplane
would have created a *second* bucket called `legacy` and left the real one unmanaged.

Clean up before doing it properly — and note this uses `Orphan` so the real bucket
survives:
```bash
kubectl patch bucket legacy-data-2019 --type=merge \
  -p '{"spec":{"deletionPolicy":"Orphan"}}'
kubectl delete bucket legacy-data-2019
awslocal s3 ls
```
✅ Expected: the bucket is **still there**. You just used `Orphan` for real.

## Part C — Import, step 1: observe only

```bash
cd 03-managed-resource-lifecycle
cat manifests/observe-only.yaml
kubectl apply -f manifests/observe-only.yaml
sleep 20
kubectl get bucket legacy-bucket
```
✅ Expected:
```
NAME            SYNCED   READY   EXTERNAL-NAME      AGE
legacy-bucket   True     True    legacy-data-2019   20s
```

Notice: the Kubernetes object is called `legacy-bucket`, but it points at the AWS
bucket `legacy-data-2019`. The external-name annotation is the bridge.

**Now look at what Crossplane discovered:**
```bash
kubectl get bucket legacy-bucket -o jsonpath='{.status.atProvider}' | jq
```
✅ Expected: real state, including the tags you set in Part A:
```json
{
  "arn": "arn:aws:s3:::legacy-data-2019",
  "id": "legacy-data-2019",
  "region": "us-east-1",
  "tags": { "created-by": "someone-who-left", "year": "2019" }
}
```

**Prove it's read-only.** Try to change something through Crossplane:
```bash
kubectl patch bucket legacy-bucket --type=merge \
  -p '{"spec":{"forProvider":{"tags":{"owner":"platform-team"}}}}'
sleep 40
awslocal s3api get-bucket-tagging --bucket legacy-data-2019
```
✅ Expected: the tags are **unchanged** — still `created-by` and `year`. Crossplane
read your request and declined to act, because `Update` isn't in its policy list.

> **This is the safety property that makes import viable.** You can point Crossplane
> at production infrastructure and be certain it will not touch it. Explore freely.

## Part D — Import, step 2: take control

Now that you've *seen* the real state, adopt it fully. Note the manifest carries the
real tags forward, plus `deletionPolicy: Orphan`:

```bash
cat manifests/imported-full.yaml
kubectl apply -f manifests/imported-full.yaml
sleep 40
awslocal s3api get-bucket-tagging --bucket legacy-data-2019
```
✅ Expected: the tags are now **what your manifest says**:
```json
{"TagSet": [{"Key": "imported-by", "Value": "crossplane"},
            {"Key": "original-owner", "Value": "unknown"}]}
```

The old tags are gone — Crossplane reconciled the real bucket to match your
declaration. **This is exactly the moment that would have been dangerous** if you'd
skipped the Observe step and your spec had disagreed with reality in a way that
mattered.

```bash
kubectl get bucket legacy-bucket
```
✅ Expected: `SYNCED=True READY=True`, fully managed, no data lost, no bucket
recreated.

🎉 **You imported production infrastructure with zero downtime.** This exact procedure
is how teams migrate off Terraform incrementally.

## Part E — Protection: deletionPolicy Orphan

```bash
kubectl apply -f manifests/orphan-on-delete.yaml
kubectl wait --for=condition=Ready bucket/precious-data --timeout=2m
awslocal s3 ls | grep precious
```
✅ Expected: `precious-data` exists.

Now delete the Kubernetes object:
```bash
kubectl delete bucket precious-data
kubectl get buckets
awslocal s3 ls | grep precious
```
✅ Expected: the Kubernetes object is **gone**, the S3 bucket is **still there**.

```
(kubectl get buckets shows no precious-data)
2026-01-15 11:04:22 precious-data
```

Compare with the default. Apply the same bucket with `deletionPolicy: Delete`:
```bash
kubectl apply -f - <<'YAML'
apiVersion: s3.aws.upbound.io/v1beta1
kind: Bucket
metadata:
  name: disposable
spec:
  forProvider: { region: us-east-1 }
  providerConfigRef: { name: default }
  deletionPolicy: Delete
YAML
kubectl wait --for=condition=Ready bucket/disposable --timeout=2m
kubectl delete bucket disposable
awslocal s3 ls | grep disposable
```
✅ Expected: no output — the bucket is genuinely destroyed.

**One field, and the difference is whether your data still exists.**

## Part F — Get a deletion stuck, on purpose

The most common Crossplane support question is "my resource won't delete." Cause it
deliberately so you recognise it instantly.

```bash
kubectl apply -f - <<'YAML'
apiVersion: s3.aws.upbound.io/v1beta1
kind: Bucket
metadata:
  name: stuck-bucket
spec:
  forProvider: { region: us-east-1 }
  providerConfigRef: { name: default }
YAML
kubectl wait --for=condition=Ready bucket/stuck-bucket --timeout=2m

# Put an object in it — S3 refuses to delete a non-empty bucket
echo "important data" > /tmp/data.txt
awslocal s3 cp /tmp/data.txt s3://stuck-bucket/data.txt 2>/dev/null || \
  kubectl run s3put --rm -i --restart=Never -q --image=amazon/aws-cli:2.18.9 \
    --env=AWS_ACCESS_KEY_ID=test --env=AWS_SECRET_ACCESS_KEY=test \
    --env=AWS_DEFAULT_REGION=us-east-1 \
    --command -- sh -c 'echo important | aws --endpoint-url=http://localstack.localstack.svc.cluster.local:4566 s3 cp - s3://stuck-bucket/data.txt'
```

Now try to delete it:
```bash
kubectl delete bucket stuck-bucket --timeout=30s
```
✅ Expected: the command times out. Investigate:

```bash
kubectl get bucket stuck-bucket
```
✅ Expected: it's `Terminating` and staying there.

```bash
kubectl get bucket stuck-bucket -o jsonpath='{.metadata.finalizers}'; echo
kubectl describe bucket stuck-bucket | tail -12
```
✅ Expected: a `finalizer.managedresource.crossplane.io` finalizer, and Events
containing `BucketNotEmpty` or similar.

**The correct fix — address the real cause:**
```bash
kubectl run s3rm --rm -i --restart=Never -q --image=amazon/aws-cli:2.18.9 \
  --env=AWS_ACCESS_KEY_ID=test --env=AWS_SECRET_ACCESS_KEY=test \
  --env=AWS_DEFAULT_REGION=us-east-1 \
  -- --endpoint-url=http://localstack.localstack.svc.cluster.local:4566 \
     s3 rm s3://stuck-bucket --recursive
sleep 60
kubectl get buckets
```
✅ Expected: `stuck-bucket` is gone. The finalizer cleared itself as soon as the real
deletion succeeded. **No force was needed.**

> **The lesson:** a stuck finalizer is a *message*, not a bug. It means "the cloud
> won't let me do what you asked." Force-removing it (`--type=merge -p
> '{"metadata":{"finalizers":[]}}'`) makes the symptom disappear and silently orphans
> the resource. Fix the cause instead.

## Part G — Late initialization on and off

```bash
kubectl apply -f manifests/no-late-init.yaml
kubectl wait --for=condition=Ready bucket/minimal-spec --timeout=2m
kubectl get bucket minimal-spec -o jsonpath='{.spec.forProvider}' | jq
```
✅ Expected: essentially just `{"region": "us-east-1"}` — what you wrote, nothing more.

Compare with a late-initialized one:
```bash
kubectl get bucket legacy-bucket -o jsonpath='{.spec.forProvider}' | jq
```
✅ Expected: noticeably more fields, filled in by AWS's defaults.

Pick based on whether you diff your manifests against the cluster. If you do, turn
late initialization off and keep the noise down.

## Part H — Clean up

```bash
kubectl delete bucket legacy-bucket minimal-spec --ignore-not-found
# legacy-bucket is Orphan, so remove the real bucket by hand:
awslocal s3 rb s3://legacy-data-2019 --force
awslocal s3 rb s3://precious-data --force
awslocal s3 ls
```
✅ Expected: no buckets. (Note you had to clean up the orphaned ones yourself —
that's the trade-off `Orphan` makes.)

---

## What you learned
- **Import** = external-name annotation + `managementPolicies: ["Observe"]`, then
  widen once you've seen the real state. Never skip the Observe step.
- **`deletionPolicy: Orphan`** keeps cloud resources alive when the object is deleted
  — and makes cleanup your job.
- **`managementPolicies`** scopes Crossplane's authority verb by verb;
  `["Observe"]` is a genuinely read-only mode you can point at production.
- A **stuck finalizer** means the cloud is refusing. Read the error and fix the cause;
  forcing it orphans resources silently.
- Omitting `LateInitialize` keeps your spec identical to what you wrote.

➡️ **[challenge.md](./challenge.md)** then [Module 04](../04-xrds-and-compositions/).
