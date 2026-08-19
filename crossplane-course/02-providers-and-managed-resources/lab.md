# Lab 02 — Providers, Activation Policies, and Your First Resources

**You'll:** install two providers, measure the cost of CRD bloat, narrow it with
MRAP, configure credentials, build a production-shaped bucket, and debug a broken
one. ⏱️ ~75 min.

> Prereqs: Module 01 complete. The S3 provider from `VERIFY.md` may still be
> installed — that's fine, Part A is idempotent.

---

## Part A — Install a provider and watch what it does

```bash
cd 02-providers-and-managed-resources
kubectl apply -f manifests/provider-s3.yaml
kubectl get providers -w        # Ctrl-C when HEALTHY is True
```
✅ Expected (this can take 2–5 minutes on first pull):
```
NAME              INSTALLED   HEALTHY   PACKAGE                                              AGE
provider-aws-s3   True        True      xpkg.upbound.io/upbound/provider-aws-s3:v1.21.0      2m
```

Now look at what the installation actually created:

```bash
# 1. A controller pod
kubectl get pods -n crossplane-system

# 2. A dependency it pulled in automatically
kubectl get providers
```
✅ Expected: **two** providers. You asked for `provider-aws-s3`; Crossplane also
installed `upbound-provider-family-aws`, because the S3 package declares it as a
dependency. The family package is what owns the `ProviderConfig` type.

```bash
# 3. New API kinds
kubectl api-resources --api-group=s3.aws.upbound.io
```
✅ Expected: a list including `buckets`, `bucketpolicies`, `bucketversionings`…

```bash
# 4. The package's own record of every version installed
kubectl get providerrevisions
```
✅ Expected: one revision, `ACTIVE=True`. Upgrading a provider adds another revision
rather than replacing this one — which is what makes rollback possible (Module 11).

## Part B — Measure the cost of CRDs

Install a much bigger provider and watch the API server's object count grow:

```bash
kubectl get crds | wc -l                      # baseline
kubectl apply -f manifests/provider-ec2.yaml
kubectl wait provider/provider-aws-ec2 --for=condition=Healthy --timeout=10m
kubectl get crds | wc -l                      # after
```
✅ Expected: the count jumps by **several hundred**. Exact numbers vary by provider
version; the order of magnitude is the point.

Check the memory the EC2 provider is using:
```bash
kubectl top pod -n crossplane-system 2>/dev/null || \
  echo "(metrics-server not installed — that's fine, read the note below)"
```

> Every activated CRD means: a schema the API server keeps in memory, an entry in
> the OpenAPI document sent to every `kubectl` client, and a watch the provider
> maintains. Multiply by five clouds and you have a genuinely degraded cluster. On
> large installations this is not a micro-optimisation — teams have seen API-server
> memory drop by gigabytes.

## Part C — Narrow it with an activation policy

```bash
cat manifests/mrap.yaml
kubectl apply -f manifests/mrap.yaml
kubectl get managedresourceactivationpolicies
```
✅ Expected: `course-resources` listed.

Inspect what's now installed-but-inert versus active:
```bash
kubectl get managedresourcedefinitions | head -20
kubectl get managedresourcedefinitions | wc -l
```
✅ Expected: many MRDs, most with `ESTABLISHED=False` — schemas present, no CRD
created, no cost.

Confirm the types you *did* activate still work:
```bash
kubectl explain vpc.spec.forProvider --api-version=ec2.aws.upbound.io/v1beta1 | head -15
```
✅ Expected: field documentation prints.

And that an unlisted one doesn't:
```bash
kubectl get flowlogs.ec2.aws.upbound.io 2>&1 | head -2
```
✅ Expected: an error about the resource not being found — it's inert, exactly as
intended. Adding it to the MRAP's `activate` list would bring it to life.

> **Design point:** you now have an explicit, reviewable list of every cloud resource
> type your platform is allowed to create. That list is a security artifact as much
> as a performance one.

## Part D — Configure credentials

If you completed `VERIFY.md`, the Secret already exists and this will error
harmlessly — skip to the ProviderConfig.

```bash
kubectl create secret generic aws-creds \
  -n crossplane-system \
  --from-literal=creds='[default]
aws_access_key_id = test
aws_secret_access_key = test'
```

The `creds` key must be **AWS INI format**, including the `[default]` header — that's
what the AWS SDK's credential file parser expects. A common failure is passing just
the key ID, which produces a confusing `InvalidClientTokenId` later.

```bash
kubectl apply -f manifests/providerconfig.yaml
kubectl get providerconfigs
```
✅ Expected: `default` listed.

Read the file and note what's emulator-specific:
```bash
cat manifests/providerconfig.yaml
```
The `endpoint` block and the four `skip_*` fields are the *only* things separating
this course from real AWS. Everything else you write is production YAML.

## Part E — A production-shaped bucket

```bash
kubectl apply -f manifests/bucket-full.yaml
kubectl get managed
```
✅ Expected, after ~30 seconds, four resources all `SYNCED=True READY=True`:
```
NAME                                                              SYNCED   READY   EXTERNAL-NAME   AGE
bucket.s3.aws.upbound.io/app-data                                 True     True    app-data        30s
bucketversioning.s3.aws.upbound.io/app-data-versioning            True     True    app-data        28s
bucketserversideencryptionconfiguration.../app-data-encryption    True     True    app-data        28s
bucketpublicaccessblock.s3.aws.upbound.io/app-data-pab            True     True    app-data        28s
```

> `kubectl get managed` lists **every** managed resource from **every** provider.
> It's the single most useful status command in Crossplane.

Verify from AWS's side:
```bash
awslocal s3api get-bucket-versioning --bucket app-data
```
✅ Expected: `{"Status": "Enabled"}`

**Four resources for one bucket.** That's the AWS API's shape, not Crossplane's
choice — and it's precisely the tedium you'll hide behind a single `Bucket` API of
your own design in Module 04.

## Part F — Explore the anatomy

```bash
kubectl get bucket app-data -o yaml
```

Find each part from the README:

```bash
# What you asked for
kubectl get bucket app-data -o jsonpath='{.spec.forProvider}' | jq

# What AWS says it is
kubectl get bucket app-data -o jsonpath='{.status.atProvider}' | jq

# Its real identity in AWS
kubectl get bucket app-data -o jsonpath='{.metadata.annotations.crossplane\.io/external-name}'

# Health
kubectl get bucket app-data -o jsonpath='{range .status.conditions[*]}{.type}={.status} {.reason}{"\n"}{end}'
```
✅ Expected external name: `app-data`. ✅ Expected conditions: `Ready=True Available`
and `Synced=True ReconcileSuccess`.

**Notice the late initialization.** Compare what you applied with what exists:
```bash
diff <(yq '.spec.forProvider' manifests/bucket-full.yaml 2>/dev/null | head -20) \
     <(kubectl get bucket app-data -o yaml | yq '.spec.forProvider') || true
```
✅ Expected: the live object has **more** fields than you wrote. AWS chose defaults;
Crossplane recorded them so it can distinguish a default from a real future change.
(No `yq`? Just eyeball the two outputs.)

## Part G — Break it on purpose

Now the skill that actually matters. Apply a bucket with an invalid region:

```bash
kubectl apply -f manifests/bucket-broken.yaml
sleep 20
kubectl get bucket broken-bucket
```
✅ Expected: it is **not** healthy.
```
NAME            SYNCED   READY   EXTERNAL-NAME   AGE
broken-bucket   False            broken-bucket   20s
```

`SYNCED=False` means the API call failed. Now find out why — **always in this order**:

```bash
# 1. The condition message (fastest, usually enough)
kubectl get bucket broken-bucket \
  -o jsonpath='{.status.conditions[?(@.type=="Synced")].message}'; echo

# 2. Events
kubectl describe bucket broken-bucket | tail -15

# 3. The provider's logs, if the above are unclear
kubectl logs -n crossplane-system -l pkg.crossplane.io/provider=provider-aws-s3 --tail=30
```
✅ Expected: an error naming the region as invalid — something like
`failed to resolve endpoint` or `invalid region`.

Fix it in place and watch it recover:
```bash
kubectl patch bucket broken-bucket --type=merge \
  -p '{"spec":{"forProvider":{"region":"us-east-1"}}}'
sleep 20
kubectl get bucket broken-bucket
```
✅ Expected: `SYNCED=True READY=True`. **No re-apply, no pipeline, no restart** — the
reconcile loop simply picked up the corrected spec on its next pass.

> This debugging order — **condition message → events → provider logs** — resolves
> the large majority of Crossplane problems. Internalise it now; Module 12 builds on
> it.

## Part H — Clean up

```bash
kubectl delete -f manifests/bucket-broken.yaml
kubectl delete -f manifests/bucket-full.yaml
kubectl wait --for=delete bucket/app-data --timeout=2m
awslocal s3 ls
```
✅ Expected: no buckets remain.

**Leave the providers, MRAP, Secret, and ProviderConfig installed** — every later
module builds on them.

---

## What you learned
- A provider = CRDs + a controller pod + RBAC, shipped as an OCI image.
- Provider **families** split a cloud by service; **MRAP** narrows it further to the
  resource types you actually use.
- **ProviderConfig** separates credentials from resources, so one control plane can
  manage many accounts.
- Every managed resource has `spec.forProvider` (yours) and `status.atProvider`
  (the cloud's), joined by the **external-name** annotation.
- `Synced` = "did the API call work"; `Ready` = "does the resource work".
- Debug in order: **condition message → events → provider logs.**

➡️ **[challenge.md](./challenge.md)** then [Module 03](../03-managed-resource-lifecycle/).
