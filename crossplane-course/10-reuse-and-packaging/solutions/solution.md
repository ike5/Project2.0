# Challenge 10 — Reference Solution

Runnable files: [`platform-package/`](./platform-package/),
[`namespace-environment.yaml`](./namespace-environment.yaml).

---

### 1. Packaging the whole platform

See [`platform-package/`](./platform-package/). Layout:

```
platform-package/
├── crossplane.yaml
├── apis/
│   ├── xnetwork.yaml
│   ├── xappidentity.yaml
│   └── xdatabase.yaml
└── compositions/
    ├── xnetwork-aws.yaml
    ├── xappidentity-aws.yaml
    └── xdatabase-aws.yaml
```

The `dependsOn` list must cover every provider **and** function any composition
references:

```yaml
dependsOn:
  - provider: xpkg.upbound.io/upbound/provider-aws-s3
    version: ">=v1.21.0"
  - provider: xpkg.upbound.io/upbound/provider-aws-ec2
    version: ">=v1.21.0"
  - provider: xpkg.upbound.io/upbound/provider-aws-rds
    version: ">=v1.21.0"
  - provider: xpkg.upbound.io/upbound/provider-aws-iam
    version: ">=v1.21.0"
  - function: xpkg.upbound.io/crossplane-contrib/function-go-templating
    version: ">=v0.9.0"
  - function: xpkg.upbound.io/crossplane-contrib/function-patch-and-transform
    version: ">=v0.8.0"
  - function: xpkg.upbound.io/crossplane-contrib/function-auto-ready
    version: ">=v0.4.0"
  - function: xpkg.upbound.io/crossplane-contrib/function-environment-configs
    version: ">=v0.4.0"
```

The clean-cluster test:
```bash
00-setup/scripts/delete-cluster.sh && 00-setup/scripts/create-cluster.sh
00-setup/scripts/install-crossplane.sh
00-setup/scripts/install-aws-emulator.sh

kubectl apply -f - <<'YAML'
apiVersion: pkg.crossplane.io/v1
kind: Configuration
metadata:
  name: acme-platform
spec:
  package: ghcr.io/acme/platform:v1.0.0
YAML

kubectl get configurations,providers,functions -w
```

**Two things the package does not carry, and cannot:**

1. **ProviderConfigs.** They contain credentials and endpoints specific to a cluster.
   Consumers create their own — which is right, and it's why Module 08's real-AWS
   ProviderConfig is a separate file.
2. **EnvironmentConfigs.** Same reason: they hold *this* installation's account IDs.

So a consumer's bootstrap is: install the Configuration, then apply their own
ProviderConfig and EnvironmentConfigs. Document those two steps in your package's
README — they're the whole of "getting started" for a new team.

### 2. Two versions

**v1.1.0 — the safe change.** Add an optional field with a default:
```yaml
storageClass:
  type: string
  enum: [standard, infrequent-access]
  default: standard
```

```bash
kubectl patch configuration acme-platform --type=merge \
  -p '{"spec":{"package":"ghcr.io/acme/platform:v1.1.0"}}'
sleep 60
kubectl get buckets -o custom-columns=NAME:.metadata.name,AGE:.metadata.creationTimestamp
```
Creation timestamps are **unchanged** — existing XRs got the default, the rendered
resources are identical, and nothing was touched.

**v2.0.0 — the rename.** After upgrading, every bucket has a new name and a new
creation timestamp. Resources were deleted and recreated.

**The release notes I'd publish:**

> ## v2.0.0 — BREAKING
>
> **⚠️ This release recreates every bucket managed by `XBucket`. Do not upgrade a
> production installation without reading this.**
>
> ### What breaks
> The composed resource previously named `bucket` is now named `s3-bucket`. Crossplane
> identifies composed resources by that name, so on upgrade it will **delete the
> existing bucket and create a new one** for every `XBucket` in your cluster.
>
> Buckets in `prod` environments have `deletionPolicy: Orphan`, so the underlying S3
> bucket survives — but it becomes **unmanaged**, and a new empty bucket is created
> alongside it. Buckets in `dev` and `staging` are **destroyed, including their
> objects**.
>
> ### Why we did it
> [If you cannot answer this convincingly, do not ship the change.]
>
> ### Migration
> 1. Set `deletionPolicy: Orphan` on all `XBucket`s before upgrading.
> 2. Upgrade, and let the new resources be created.
> 3. For each orphaned bucket, copy the data across, or re-adopt it by setting the new
>    resource's external-name annotation (Module 03).
> 4. Delete the orphaned buckets once you've verified the new ones.
>
> ### If you cannot take downtime
> Stay on v1.1.0. It remains supported until 2026-12-31.

**The honest lesson:** those release notes are so ugly that the right decision is
usually **don't make the change**. A resource name in a composition is a permanent
commitment. Pick names carefully the first time, because the cost of changing one is
out of all proportion to how trivial the diff looks.

### 3. Un-spoofable environments

The attack:
```bash
kubectl apply -f - <<'YAML'
apiVersion: platform.acme.io/v1alpha1
kind: XAppIdentity
metadata: { name: sneaky, namespace: team-payments }   # a DEV namespace
spec:
  serviceAccountName: sneaky
  environment: prod                                     # ...asking for PROD
YAML
```
Today this succeeds and yields a role in account `333333333333`.

**Fix (a): derive the environment from a namespace label the developer cannot set.**

```yaml
# Platform-managed, applied by an admin
apiVersion: v1
kind: Namespace
metadata:
  name: team-payments
  labels:
    acme.io/environment: dev
```

Read it with `function-extra-resources`:
```yaml
- step: load-namespace
  functionRef:
    name: function-extra-resources
  input:
    apiVersion: extra-resources.fn.crossplane.io/v1beta1
    kind: Input
    spec:
      extraResources:
        - apiVersion: v1
          kind: Namespace
          into: ns
          type: Reference
          ref:
            name: ""            # resolved from the XR's namespace via a patch
```
Then in the template, ignore `spec.environment` entirely:
```gotemplate
{{- $nsObj := index .context "apiextensions.crossplane.io/extra-resources" "ns" 0 -}}
{{- $env := index $nsObj.resource.metadata.labels "acme.io/environment" -}}
```
And remove `environment` from the XRD schema, so it cannot be set at all.

**Fix (b): an admission policy** binding namespace to environment:
```yaml
apiVersion: admissionregistration.k8s.io/v1
kind: ValidatingAdmissionPolicy
metadata: { name: env-matches-namespace }
spec:
  matchConstraints:
    resourceRules:
      - apiGroups: ["platform.acme.io"]
        operations: ["CREATE", "UPDATE"]
        resources: ["xappidentities"]
  paramKind: { apiVersion: v1, kind: Namespace }
  validations:
    - expression: "object.spec.environment == params.metadata.labels['acme.io/environment']"
      message: "environment must match the namespace's acme.io/environment label"
```

**Which to use?** (a) is better, because it removes the field entirely — there is
nothing to spoof and nothing to validate. (b) is easier to retrofit onto an API that
already ships `environment`.

**And the answer that beats both: separate control planes per environment.** If the
dev cluster's ProviderConfig has no path to the prod account, the entire class of
attack is gone regardless of what any composition does. Everything enforced inside one
cluster is one misconfiguration from failing; an IAM trust relationship that simply
doesn't include your dev cluster fails safe.

### 4. Automating `Usage`

Add to the `XNetwork` template, inside the AZ loop:
```gotemplate
---
apiVersion: apiextensions.crossplane.io/v1beta1
kind: Usage
metadata:
  annotations:
    {{ setResourceNameAnnotation (printf "usage-subnet-vpc-%s" $az) }}
spec:
  of:
    apiVersion: ec2.aws.upbound.io/v1beta1
    kind: VPC
    resourceSelector:
      matchControllerRef: true
  by:
    apiVersion: ec2.aws.upbound.io/v1beta1
    kind: Subnet
    resourceSelector:
      matchControllerRef: true
      matchLabels:
        tier: public
        az: {{ $az }}
  reason: "Subnet lives inside this VPC"
```
`resourceSelector` rather than `resourceRef`, because the composition doesn't know the
generated resource names at authoring time.

**Measured teardown** (two AZs, ~14 resources):
```bash
time (kubectl delete xnetwork payments-net -n team-payments && \
      until [ "$(kubectl get managed --no-headers 2>/dev/null | wc -l)" -eq 0 ]; do sleep 5; done)
```
```
without Usage:  2m48s   (VPC delete rejected 4 times before converging)
with Usage:     1m12s   (each delete issued once, in order)
```

The saving is real but modest. **The bigger win is determinism**: without `Usage` the
teardown *usually* converges and occasionally strands a resource in `Terminating`
until someone investigates. With it, every delete is issued once, in a valid order.

**The cost, stated honestly:** roughly 6 extra objects per network, an admission
webhook call on every delete, and a new failure mode — if a `Usage` object is
orphaned (its `by` resource gone but the `Usage` remaining), it blocks deletion
forever and the error message doesn't obviously say why. Add `Usage` where teardown
ordering has actually bitten you, not everywhere by default.

### 5. Stretch — dependency conflict

```yaml
# package-a: dependsOn provider-aws-s3 >=v1.21.0
# package-b: dependsOn provider-aws-s3 <v1.20.0
```

Installing both:
```bash
kubectl get configurations
# NAME        INSTALLED   HEALTHY
# package-a   True        True
# package-b   True        False

kubectl describe configuration package-b | tail -10
# ...incompatible dependency version: existing provider-aws-s3 v1.21.0
#    does not satisfy constraint <v1.20.0
```

Crossplane installs the first, then refuses the second because no single provider
version satisfies both constraints. The second Configuration reports
`Healthy=False` — **it does not downgrade the provider**, which would break the
first package.

**Resolving it:** there is no clever fix. One of the packages must widen its
constraint. In practice you contact the owner, or fork.

**Why ranges rather than exact pins:** an exact pin
(`version: "v1.21.0"`) means your package conflicts with **every other package** that
pins a different patch version of the same provider. Since a cluster runs one instance
of each provider, exact pins make packages mutually exclusive — and the more popular
your package, the more collisions it causes.

Use `>=` for the minimum version whose features you need. Add an upper bound only for
a version you have actually verified is incompatible (`>=v1.21.0,<v2.0.0` is
reasonable if v2 is a known breaking release).

> This is the same reasoning as library dependency ranges in any package manager,
> with one difference that raises the stakes: a Crossplane provider is a **singleton
> in the cluster**, so there is no equivalent of vendoring two versions side by side.
