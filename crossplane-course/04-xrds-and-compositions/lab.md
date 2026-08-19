# Lab 04 — Build Your First Platform API

**You'll:** define an API, implement it, use it as a developer would, add a second
implementation, and break the `compositeTypeRef` on purpose to learn its failure
signature. ⏱️ ~80 min.

> Prereqs: Modules 02–03. Providers, MRAP, Secret, and ProviderConfig installed.

---

## Part A — Install the composition functions

Compositions can't do anything without functions. Install them like providers:

```bash
cd 04-xrds-and-compositions
kubectl apply -f manifests/functions.yaml
kubectl get functions -w        # Ctrl-C when both are HEALTHY
```
✅ Expected (2–4 minutes for the first pull):
```
NAME                           INSTALLED   HEALTHY   PACKAGE                                    AGE
function-auto-ready            True        True      .../function-auto-ready:v0.4.1             2m
function-patch-and-transform   True        True      .../function-patch-and-transform:v0.8.2    2m
```

```bash
kubectl get pods -n crossplane-system | grep function
```
✅ Expected: a pod per function. They're gRPC servers Crossplane calls during
reconciliation.

## Part B — Define your API

```bash
cat manifests/xrd.yaml
kubectl apply -f manifests/xrd.yaml
kubectl get xrd
```
✅ Expected:
```
NAME                          ESTABLISHED   OFFERED   AGE
xbuckets.platform.acme.io     True                    10s
```

**`ESTABLISHED=True` means the CRD was created.** (`OFFERED` is blank because that
column is about v1 claims, which `scope: Namespaced` doesn't use.)

Your API now exists as a first-class part of Kubernetes:
```bash
kubectl api-resources --api-group=platform.acme.io
kubectl explain xbucket.spec
```
✅ Expected: `kubectl explain` prints **your** field documentation — the descriptions
you wrote in the XRD.

Test the schema validation you got for free:
```bash
kubectl create ns team-payments
kubectl apply -f - <<'YAML'
apiVersion: platform.acme.io/v1alpha1
kind: XBucket
metadata:
  name: bad
  namespace: team-payments
spec:
  environment: production
YAML
```
✅ Expected: **rejected before it's ever stored**:
```
The XBucket "bad" is invalid: spec.environment: Unsupported value: "production":
supported values: "dev", "staging", "prod"
```

> The developer typed `production` instead of `prod` and got an instant, precise
> error. You wrote zero validation code — the `enum` in your XRD did it. **Push as
> much validation into the schema as you possibly can.**

## Part C — Implement it

```bash
cat manifests/composition.yaml
kubectl apply -f manifests/composition.yaml
kubectl get compositions
```
✅ Expected: `xbucket-aws` listed.

Nothing has happened yet — a Composition is inert until an XR selects it.

## Part D — Be a developer

```bash
cat manifests/xr-dev.yaml       # five lines of spec
kubectl apply -f manifests/xr-dev.yaml
kubectl get xbuckets -n team-payments
```
✅ Expected, within ~60 seconds:
```
NAME           ENVIRONMENT   BUCKET                      SYNCED   READY   AGE
scratch-data   dev           team-payments-scratch-data  True     True    45s
```

(Those columns come from the `additionalPrinterColumns` you defined in the XRD.)

**Now look at what those five lines actually built:**
```bash
crossplane trace xbucket scratch-data -n team-payments
```
✅ Expected — a tree of four managed resources:
```
NAME                                            SYNCED   READY   STATUS
XBucket/scratch-data (team-payments)            True     True    Available
├─ Bucket/scratch-data-x7k2p                    True     True    Available
├─ BucketPublicAccessBlock/scratch-data-9mn4q   True     True    Available
├─ BucketServerSideEncryptionConfiguration/...  True     True    Available
└─ BucketLifecycleConfiguration/scratch-data-.. True     True    Available
```

> **`crossplane trace` is the command you'll use most in this course.** It shows the
> whole tree and where it's broken. Learn it now.

Verify from AWS's side:
```bash
awslocal s3 ls
awslocal s3api get-bucket-encryption --bucket team-payments-scratch-data
awslocal s3api get-public-access-block --bucket team-payments-scratch-data
```
✅ Expected: the bucket exists, is encrypted with AES256, and blocks all public
access — **none of which the developer asked for or could have forgotten.**

## Part E — Environment-driven behaviour

```bash
kubectl apply -f manifests/xr-prod.yaml
sleep 45
kubectl get xbuckets -n team-payments
```

Compare the `deletionPolicy` the composition chose for each:
```bash
kubectl get buckets -o custom-columns=\
NAME:.metadata.name,EXTERNAL:.metadata.annotations.crossplane\\.io/external-name,DELETION:.spec.deletionPolicy
```
✅ Expected:
```
NAME                  EXTERNAL                          DELETION
scratch-data-x7k2p    team-payments-scratch-data        Delete
customer-uploads-...  team-payments-customer-uploads    Orphan
```

**One word in the developer's YAML (`dev` → `prod`) produced a different safety
posture.** The developer doesn't know `deletionPolicy` exists. That's the abstraction
doing its job: the platform encodes the policy, the developer states the intent.

Confirm the retention differs too:
```bash
awslocal s3api get-bucket-lifecycle-configuration --bucket team-payments-scratch-data \
  | grep -i days
awslocal s3api get-bucket-lifecycle-configuration --bucket team-payments-customer-uploads \
  | grep -i days
```
✅ Expected: `7` and `365`.

## Part F — Two implementations, one API

```bash
kubectl apply -f manifests/composition-cheap.yaml
kubectl get compositions
```
✅ Expected: two compositions, both for `XBucket`.

Now there's ambiguity. Create an XR with no selector:
```bash
kubectl apply -f - <<'YAML'
apiVersion: platform.acme.io/v1alpha1
kind: XBucket
metadata:
  name: ambiguous
  namespace: team-payments
spec:
  environment: dev
YAML
sleep 15
kubectl describe xbucket ambiguous -n team-payments | tail -8
```
✅ Expected: an error about composition selection — Crossplane won't guess.

Fix it by selecting on labels:
```bash
kubectl apply -f manifests/xr-selected.yaml
sleep 45
crossplane trace xbucket cheap-bucket -n team-payments
```
✅ Expected: **only one** composed resource (just the Bucket) — this XR used the
minimal composition.

```bash
kubectl delete xbucket ambiguous -n team-payments
```

> **This is how you offer variants.** Same API, different implementations, selected by
> label. It's also how a migration works: write a GCP composition for the same XRD,
> flip the selector, and the developer's manifest never changes.

## Part G — Break the compositeTypeRef

This failure is so common, and so silent, that it's worth causing deliberately.

```bash
kubectl patch composition xbucket-aws --type=merge \
  -p '{"spec":{"compositeTypeRef":{"apiVersion":"platform.acme.io/v1beta1","kind":"XBucket"}}}'

kubectl apply -f - <<'YAML'
apiVersion: platform.acme.io/v1alpha1
kind: XBucket
metadata:
  name: orphan-xr
  namespace: team-payments
spec:
  environment: dev
  crossplane:
    compositionRef:
      name: xbucket-aws
YAML
sleep 20
kubectl get xbucket orphan-xr -n team-payments
```
✅ Expected: it sits there, **not ready, with no obvious error**:
```
NAME        ENVIRONMENT   BUCKET   SYNCED   READY   AGE
orphan-xr   dev                    False            20s
```

Find the real message:
```bash
kubectl describe xbucket orphan-xr -n team-payments | tail -10
```
✅ Expected: a message about the referenced composition not being compatible — the
version `v1beta1` doesn't match the XR's `v1alpha1`.

Fix and watch it recover:
```bash
kubectl patch composition xbucket-aws --type=merge \
  -p '{"spec":{"compositeTypeRef":{"apiVersion":"platform.acme.io/v1alpha1","kind":"XBucket"}}}'
sleep 45
kubectl get xbucket orphan-xr -n team-payments
```
✅ Expected: `SYNCED=True READY=True`.

> **Remember this signature: an XR that sits idle with nothing underneath it.**
> Check `compositeTypeRef` against your XRD's group, version, *and* kind before
> anything else.

## Part H — Clean up

```bash
kubectl delete xbucket --all -n team-payments
sleep 30
kubectl get managed
awslocal s3 ls
```
✅ Expected: the dev buckets are gone. **The prod one (`customer-uploads`) remains in
AWS** — `deletionPolicy: Orphan`, exactly as designed. Remove it by hand:
```bash
awslocal s3 rb s3://team-payments-customer-uploads --force
```

**Leave the XRD, Compositions, and functions installed** — Module 05 extends them.

---

## What you learned
- An **XRD** defines your API and creates a real CRD; its OpenAPI schema gives you
  free, instant validation.
- A **Composition** implements that API through a function **pipeline** (the only
  mode in v2).
- One XRD can have **many Compositions**, selected by label — the developer's YAML
  never changes.
- Patches move values **in** (`FromCompositeFieldPath`) and results **out**
  (`ToCompositeFieldPath`).
- `matchControllerRef: true` is how one composed resource references a sibling.
- A mismatched **`compositeTypeRef`** produces an XR that silently does nothing.
  Check it first.
- Security settings the developer never sees are settings they can never forget.

➡️ **[challenge.md](./challenge.md)** then [Module 05](../05-composition-functions/).
