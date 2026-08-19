# Module 10 — Reuse & Packaging

**Goal:** stop copy-pasting values between compositions, order deletions correctly,
and ship your platform API as a versioned artifact other teams can install.

⏱️ ~3 hours · 🎯 Prereq: Modules 04–09.

---

## 1. Three problems you now have

By Module 09 you have a working platform. You also have three problems that only
appear at scale:

1. **Hardcoded environment values.** Your `XAppIdentity` composition contains
   `$accountId := "123456789012"` and an OIDC host. Those differ per cluster, per
   environment, per account — and they're baked into the composition.
2. **Deletion ordering.** Module 07's teardown produced `DependencyViolation` errors
   that *usually* resolved. "Usually" is not a strategy.
3. **Distribution.** Your XRDs and Compositions live in a directory. How does another
   team install them? How do they get version 1.2 rather than whatever is on `main`
   today?

This module fixes all three.

## 2. EnvironmentConfig — shared values, out of the composition

An `EnvironmentConfig` is a cluster-scoped bag of data a composition can read while
rendering:

```yaml
apiVersion: apiextensions.crossplane.io/v1beta1
kind: EnvironmentConfig
metadata:
  name: aws-account-prod
data:
  accountId: "333333333333"
  region: us-east-1
  oidcHost: oidc.eks.us-east-1.amazonaws.com/id/EXAMPLE
  vpcId: vpc-0abc123
  privateSubnetIds:
    - subnet-01
    - subnet-02
```

Load it as a pipeline step, then read it from context:

```yaml
- step: environment
  functionRef:
    name: function-environment-configs
  input:
    apiVersion: environmentconfigs.fn.crossplane.io/v1beta1
    kind: Input
    spec:
      environmentConfigs:
        - type: Reference
          ref:
            name: aws-account-prod
```

```gotemplate
{{- $env := index .context "apiextensions.crossplane.io/environment" -}}
accountId: {{ $env.accountId }}
```

**Why this matters more than it looks:** it's what makes one composition work across
dev, staging, and prod. The composition describes *shape*; the EnvironmentConfig
supplies *facts*. Without it you need a composition per environment, and they drift.

You can also select one dynamically, so an XR's own fields choose its environment:
```yaml
- type: Selector
  selector:
    matchLabels:
      - key: environment
        type: FromCompositeFieldPath
        valueFromFieldPath: spec.environment
```

> **EnvironmentConfigs are not secrets.** They're readable by anything that can read
> the cluster and they end up in function inputs, which get logged. Account IDs and
> VPC IDs are fine; credentials are not.

## 3. `Usage` — deletion ordering that actually works

Module 07's teardown relied on retries converging. `Usage` makes the dependency
explicit:

```yaml
apiVersion: apiextensions.crossplane.io/v1beta1
kind: Usage
metadata:
  name: subnet-uses-vpc
spec:
  of:                       # the thing being used
    apiVersion: ec2.aws.upbound.io/v1beta1
    kind: VPC
    resourceRef:
      name: my-vpc
  by:                       # the thing using it
    apiVersion: ec2.aws.upbound.io/v1beta1
    kind: Subnet
    resourceRef:
      name: my-subnet
```

Crossplane now **refuses to delete the VPC** while the subnet exists — enforced by an
admission webhook, so the deletion is rejected rather than attempted and failed.

Two distinct uses:

**Ordering deletion**, as above. And **protecting a resource** by omitting `by`:
```yaml
spec:
  of:
    apiVersion: rds.aws.upbound.io/v1beta1
    kind: Instance
    resourceRef:
      name: prod-database
  reason: "Protected: holds production customer data"
```
Nothing can delete that instance until the `Usage` is removed — a deliberate,
auditable two-step.

> **`Usage` vs `deletionPolicy: Orphan`.** `Orphan` says "don't delete the cloud
> resource." `Usage` says "don't delete this object at all." Use `Usage` when the
> *order* matters or when you want deletion **blocked**; use `Orphan` when you're
> happy for the object to go and the cloud resource to stay.

## 4. Packages — shipping your platform

You've installed providers and functions as packages all course. Your own APIs ship
the same way, as a **Configuration**.

```
my-platform/
├── crossplane.yaml          ← metadata and dependencies
├── xrds/
│   ├── xdatabase.yaml
│   └── xnetwork.yaml
└── compositions/
    ├── xdatabase-aws.yaml
    └── xnetwork-aws.yaml
```

```yaml
# crossplane.yaml
apiVersion: meta.pkg.crossplane.io/v1
kind: Configuration
metadata:
  name: acme-platform
spec:
  crossplane:
    version: ">=v2.0.0"
  dependsOn:
    - provider: xpkg.upbound.io/upbound/provider-aws-rds
      version: ">=v1.21.0"
    - function: xpkg.upbound.io/crossplane-contrib/function-go-templating
      version: ">=v0.9.0"
```

```bash
crossplane xpkg build --package-root=. --package-file=platform.xpkg
crossplane xpkg push --package-files=platform.xpkg ghcr.io/acme/platform:v1.0.0
```

A consumer installs it with one object:
```yaml
apiVersion: pkg.crossplane.io/v1
kind: Configuration
metadata:
  name: acme-platform
spec:
  package: ghcr.io/acme/platform:v1.0.0
```

**Crossplane resolves and installs the dependencies automatically.** The consumer
doesn't need to know which providers or functions your compositions use.

## 5. Versioning your platform API

Packages are OCI images, so they use semver tags. The discipline that matters:

| Change | Version bump | Safe? |
|--------|-------------|-------|
| Add an optional field with a default | patch/minor | ✅ |
| Add a new Composition | minor | ✅ |
| Change what an existing field does | **major** | ⚠️ Existing XRs change behaviour |
| Remove a field | **major** | ❌ Breaks consumers |
| Change a composed resource's name annotation | **major** | ❌ **Deletes and recreates** |

That last row is the one that catches people. Renaming a resource in a composition is
invisible in the API — no field changed — but it destroys and recreates infrastructure
for every existing XR. **Treat resource names in compositions as part of your public
API**, even though consumers never see them.

**Never publish `:latest`.** A consumer pinned to `:latest` gets your next commit
applied to their production infrastructure, at a time they didn't choose.

## 6. What belongs in one Configuration?

Same lifecycle test as Module 06's XR boundaries, one level up:

- ✅ **One Configuration per platform team's coherent API set.** All the APIs a team
  owns and versions together.
- ❌ **One Configuration for the whole company.** Every team blocked on one release.
- ❌ **One Configuration per XRD.** Dependency management becomes a full-time job.

A useful test: **could you write release notes for this package that one audience
cares about?** If half the notes are irrelevant to any given reader, split it.

---

## Do the lab
Extract hardcoded values into EnvironmentConfigs, use `Usage` to make deletion
deterministic and to block a deletion outright, then build and install a real
Configuration package.
👉 **[lab.md](./lab.md)**

Then: 👉 **[challenge.md](./challenge.md)**

## Manifests
- [`environmentconfigs.yaml`](./manifests/environmentconfigs.yaml) — dev and prod facts
- [`composition-envconfig.yaml`](./manifests/composition-envconfig.yaml) — reads them
- [`usage-ordering.yaml`](./manifests/usage-ordering.yaml) — deletion ordering
- [`usage-protection.yaml`](./manifests/usage-protection.yaml) — deletion blocking
- [`package/`](./manifests/package/) — a complete, buildable Configuration

## Key terms
EnvironmentConfig · `function-environment-configs` · context · `Usage` ·
Configuration package · `crossplane.yaml` · `dependsOn` · xpkg · semver ·
breaking change

**Next →** [Module 11: Day-2 Operations](../11-day-two-operations/)
