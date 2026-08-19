# Lab 10 — Shared Facts, Ordered Deletes, Shipped Packages

**You'll:** lift hardcoded values into EnvironmentConfigs, prove `Usage` blocks a
deletion that would otherwise fail messily, and build and install a real Configuration
package. ⏱️ ~80 min.

> Prereqs: Modules 08–09. The `XAppIdentity` XRD from Module 08 installed.

---

## Part A — Install the EnvironmentConfigs function

```bash
cd 10-reuse-and-packaging
kubectl apply -f - <<'YAML'
apiVersion: pkg.crossplane.io/v1
kind: Function
metadata:
  name: function-environment-configs
spec:
  package: xpkg.upbound.io/crossplane-contrib/function-environment-configs:v0.4.0
YAML
kubectl wait function/function-environment-configs --for=condition=Healthy --timeout=5m
```

## Part B — See the problem first

```bash
grep -n 'accountId :=\|oidcHost :=' ../08-aws-iam-and-identity/manifests/composition.yaml
```
✅ Expected:
```
{{- $accountId := "123456789012" -}}
{{- $oidcHost := "oidc.eks.us-east-1.amazonaws.com/id/EXAMPLED..." -}}
```

**That composition works in exactly one AWS account.** To use it in dev and prod
you'd copy it, change two lines, and now maintain two files that will drift.

## Part C — Lift the facts out

```bash
cat manifests/environmentconfigs.yaml
kubectl apply -f manifests/environmentconfigs.yaml
kubectl get environmentconfigs
```
✅ Expected: `aws-dev` and `aws-prod`, labelled by environment.

```bash
kubectl apply -f manifests/composition-envconfig.yaml
```

Add an `environment` field to the XRD so the selector has something to match on:
```bash
kubectl patch xrd xappidentities.platform.acme.io --type=json -p='[
  {"op":"add","path":"/spec/versions/0/schema/openAPIV3Schema/properties/spec/properties/environment",
   "value":{"type":"string","enum":["dev","prod"],"default":"dev"}}
]'
```

Now create the **same XR** twice, differing only by environment:
```bash
kubectl create ns team-payments 2>/dev/null || true
kubectl create ns team-payments-prod 2>/dev/null || true

for pair in "team-payments dev" "team-payments-prod prod"; do
  set -- $pair
  kubectl apply -f - <<YAML
apiVersion: platform.acme.io/v1alpha1
kind: XAppIdentity
metadata:
  name: billing
  namespace: $1
spec:
  serviceAccountName: billing
  environment: $2
  crossplane:
    compositionRef:
      name: xappidentity-envconfig
YAML
done
sleep 45
kubectl get xappidentities -A
```
✅ Expected: both `READY=True`, with **different account IDs** in their role ARNs:
```
NAMESPACE            NAME      SERVICEACCOUNT   ROLE
team-payments        billing   billing          arn:aws:iam::111111111111:role/team-payments-billing
team-payments-prod   billing   billing          arn:aws:iam::333333333333:role/team-payments-prod-billing
```

**One composition, two accounts.** The composition contains no account IDs at all:
```bash
grep -c '111111111111\|333333333333' manifests/composition-envconfig.yaml
```
✅ Expected: `0`.

Confirm the environment-specific tags landed too:
```bash
awslocal iam list-role-tags --role-name team-payments-prod-billing \
  --query 'Tags[?Key==`costCenter`]'
```
✅ Expected: `platform-production` — a fact that came from the EnvironmentConfig, not
the composition.

## Part D — What happens when the selector matches nothing

```bash
kubectl apply -f - <<'YAML'
apiVersion: platform.acme.io/v1alpha1
kind: XAppIdentity
metadata:
  name: no-env
  namespace: team-payments
spec:
  serviceAccountName: no-env
  environment: dev
  crossplane:
    compositionRef:
      name: xappidentity-envconfig
YAML
kubectl label environmentconfig aws-dev environment-
sleep 30
kubectl describe xappidentity no-env -n team-payments | tail -8
```
✅ Expected: an error — no EnvironmentConfig matched.

**This is the good outcome.** The composition set `fromFieldPathPolicy: Required`, so
a missing environment fails loudly. Without it, `$env.accountId` would be empty and
you'd get an IAM role with `arn:aws:iam:::oidc-provider/` — a malformed trust policy
that AWS might accept and that would never work.

Restore it:
```bash
kubectl label environmentconfig aws-dev environment=dev
kubectl delete xappidentity no-env -n team-payments
```

## Part E — `Usage` for deletion ordering

Recreate the raw network from Module 07:
```bash
kubectl apply -f ../07-aws-networking/manifests/raw-vpc.yaml
sleep 75
kubectl get managed | grep raw
```
✅ Expected: everything `SYNCED=True READY=True`.

**First, see the messy version.** Try deleting the VPC while its subnets exist:
```bash
kubectl delete vpc raw-vpc --wait=false
sleep 20
kubectl get vpc raw-vpc -o jsonpath='{.status.conditions[?(@.type=="Synced")].message}'; echo
```
✅ Expected: a `DependencyViolation` — the delete was **attempted and failed**, and
the VPC is now stuck `Terminating` while it retries.

```bash
kubectl get vpc raw-vpc
```
✅ Expected: `Terminating`.

Let it recover by removing the subnets:
```bash
kubectl delete subnet raw-subnet-a raw-subnet-b
kubectl delete routetableassociation --all 2>/dev/null
sleep 60
kubectl get vpc 2>/dev/null || echo "VPC eventually deleted"
```

**Now the clean version.** Rebuild, and declare the dependency:
```bash
kubectl apply -f ../07-aws-networking/manifests/raw-vpc.yaml
sleep 75
kubectl apply -f manifests/usage-ordering.yaml
kubectl get usages
```
✅ Expected: two `Usage` objects.

```bash
kubectl delete vpc raw-vpc
```
✅ Expected: **rejected immediately**, not attempted:
```
Error from server (Forbidden): admission webhook "nousages.apiextensions.crossplane.io"
denied the request: cannot delete resource in use by another resource
```

**The difference matters.** Before, the delete was issued, AWS rejected it, and the
object sat `Terminating` — a state you have to notice and understand. Now the request
is refused at the API server with a message naming the cause, and **nothing changed
state at all**.

Delete in the right order and it works:
```bash
kubectl delete subnet raw-subnet-a
kubectl delete internetgateway raw-igw
sleep 20
kubectl delete vpc raw-vpc      # now permitted
```

## Part F — `Usage` as a lock

```bash
kubectl apply -f - <<'YAML'
apiVersion: s3.aws.upbound.io/v1beta1
kind: Bucket
metadata:
  name: production-data
spec:
  forProvider: { region: us-east-1 }
  providerConfigRef: { name: default }
YAML
kubectl wait --for=condition=Ready bucket/production-data --timeout=2m
kubectl apply -f manifests/usage-protection.yaml

kubectl delete bucket production-data
```
✅ Expected: **rejected**, with your `reason` text visible in the error.

```bash
kubectl get usage protect-production-data -o jsonpath='{.spec.reason}'; echo
```
✅ Expected: the retention-requirement explanation.

**Removing protection is a separate, auditable act:**
```bash
kubectl delete usage protect-production-data
kubectl delete bucket production-data     # now permitted
```

> **Compare the three protections you now know:**
> - `deletionPolicy: Orphan` — object goes, cloud resource stays.
> - `deletionProtection: true` (Module 09) — **AWS** refuses.
> - `Usage` — the **Kubernetes object cannot be deleted at all**.
>
> They're independent and complementary. Production data deserves all three.

## Part G — Build a real package

```bash
cd manifests/package
cat crossplane.yaml
crossplane xpkg build --package-root=. --package-file=acme-platform.xpkg
ls -lh acme-platform.xpkg
```
✅ Expected: a `.xpkg` file of a few KB. It's an OCI image tarball.

Inspect what went in:
```bash
tar -tf acme-platform.xpkg 2>/dev/null | head || \
  echo "(it's an OCI layout — 'crossplane xpkg' tooling reads it)"
```

**Install it from the local file** (no registry needed):
```bash
kind load image-archive acme-platform.xpkg --name xp-course 2>/dev/null || \
  echo "note: if this fails, push to a registry instead — see the package README"
```

In a real workflow you'd push and install:
```bash
# crossplane xpkg push --package-files=acme-platform.xpkg ghcr.io/acme/platform:v1.0.0
#
# then, on any cluster:
# kubectl apply -f - <<'YAML'
# apiVersion: pkg.crossplane.io/v1
# kind: Configuration
# metadata:
#   name: acme-platform
# spec:
#   package: ghcr.io/acme/platform:v1.0.0
# YAML
```

**The point to internalise:** that one `Configuration` object installs the XRDs, the
Compositions, **and** the two providers and three functions listed in `dependsOn`. A
consuming team runs one command and has a working platform API.

```bash
cd ../..
```

## Part H — The breaking change that looks harmless

This is the most valuable five minutes in the module.

```bash
kubectl apply -f manifests/package/apis/xbucket.yaml
kubectl apply -f manifests/package/compositions/xbucket-aws.yaml
kubectl apply -f - <<'YAML'
apiVersion: platform.acme.io/v1alpha1
kind: XBucket
metadata: { name: versioned, namespace: team-payments }
spec: { environment: dev, retentionDays: 7 }
YAML
sleep 45
kubectl get bucket -o custom-columns=NAME:.metadata.name,EXTERNAL:.metadata.annotations.crossplane\\.io/external-name,AGE:.metadata.creationTimestamp
```
✅ Expected: a bucket, note its name and creation timestamp.

Now make a change that looks purely cosmetic — rename the resource in the composition:
```bash
sed 's/setResourceNameAnnotation "bucket"/setResourceNameAnnotation "s3-bucket"/' \
  manifests/package/compositions/xbucket-aws.yaml | kubectl apply -f -
sleep 60
kubectl get bucket -o custom-columns=NAME:.metadata.name,EXTERNAL:.metadata.annotations.crossplane\\.io/external-name,AGE:.metadata.creationTimestamp
```
✅ Expected: **a different bucket object, with a new creation timestamp.** The old one
was deleted and a new one created.

**No API field changed. The XR is byte-for-byte identical. And every existing
consumer's bucket was destroyed and recreated.** On an RDS instance this is your
database.

> **Resource name annotations are part of your package's public API**, even though
> consumers never see them. A rename is a **major** version bump. This is the single
> most important versioning rule in Crossplane, and the one least likely to be caught
> in review.

Restore it:
```bash
kubectl apply -f manifests/package/compositions/xbucket-aws.yaml
```

## Part I — Clean up

```bash
kubectl delete xbucket --all -n team-payments
kubectl delete xappidentity --all -A
kubectl delete usage --all
sleep 45
kubectl get managed
rm -f manifests/package/acme-platform.xpkg
```

**Leave the EnvironmentConfigs installed** — the capstone uses them.

---

## What you learned
- **EnvironmentConfigs** hold per-environment facts so one composition serves every
  environment. Set `fromFieldPathPolicy: Required` so a missing match fails loudly.
- They are **not secrets** — their contents flow into function inputs.
- **`Usage` with `by`** orders deletion by *rejecting* the request, rather than
  attempting and failing it.
- **`Usage` without `by`** locks a resource against deletion entirely.
- A **Configuration package** ships your XRDs, Compositions, and their dependencies as
  one versioned OCI artifact.
- **Renaming a composed resource destroys and recreates infrastructure** for every
  existing XR, with no visible API change. Treat it as a major version bump.

➡️ **[challenge.md](./challenge.md)** then [Module 11](../11-day-two-operations/).
