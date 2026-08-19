# Module 02 — Providers & Managed Resources

**Goal:** understand how Crossplane learns to talk to a cloud, and become fluent with
the managed resource — the atom every later module is built from.

⏱️ ~2.5 hours · 🎯 Prereq: Module 01.

---

## 1. A provider is a controller in a box

You already know how Kubernetes controllers work: watch objects of some kind, compare
them to reality, act. A **provider** is exactly that, packaged so you can install it
with one YAML file.

Installing `provider-aws-s3` does three things:

1. **Installs CRDs** — `Bucket`, `BucketPolicy`, `BucketVersioning`, and friends
   become real Kubernetes kinds.
2. **Runs a Deployment** — a pod in `crossplane-system` that watches those kinds.
3. **Creates RBAC** — so that pod may read and update the objects it manages.

```yaml
apiVersion: pkg.crossplane.io/v1
kind: Provider
metadata:
  name: provider-aws-s3
spec:
  package: xpkg.upbound.io/upbound/provider-aws-s3:v1.21.0
```

That `package` is an **OCI image** — the same format as a container image. Crossplane
extensions ship through ordinary container registries, which means your existing
registry, mirroring, and scanning all work unchanged.

> **Always pin the tag.** `:v1.21.0`, never `:latest`. A provider that silently
> upgrades itself is a provider that silently changes how your infrastructure is
> reconciled, at a time you didn't choose. Module 11 covers upgrades properly.

## 2. Provider families

Older Crossplane had one enormous `provider-aws` with **~1,000 CRDs**. Installing it
to manage three buckets meant loading a thousand schemas into your API server, which
measurably degraded whole clusters.

Modern providers are split into **families**, one package per AWS service:

```
provider-family-aws        ← owns the shared ProviderConfig type
├── provider-aws-s3        ← Bucket, BucketPolicy, ...
├── provider-aws-ec2       ← VPC, Subnet, SecurityGroup, ...
├── provider-aws-rds       ← Instance, SubnetGroup, ...
└── provider-aws-iam       ← Role, Policy, ...
```

Install a family member and Crossplane pulls `provider-family-aws` automatically as a
dependency. **You install only the services you actually use.**

## 3. MRDs and MRAP — the v2 answer to CRD bloat

Splitting into families helped, but `provider-aws-ec2` alone still has ~300 resource
types, and you probably want six of them.

Crossplane v2 adds two objects:

- **ManagedResourceDefinition (MRD)** — a resource's schema, *installed but inert*.
  It costs nothing until activated.
- **ManagedResourceActivationPolicy (MRAP)** — pattern rules choosing which MRDs
  become real, live CRDs.

```yaml
apiVersion: apiextensions.crossplane.io/v1alpha1
kind: ManagedResourceActivationPolicy
metadata:
  name: activated
spec:
  activate:
    - buckets.s3.aws.upbound.io
    - "*.ec2.aws.upbound.io"        # wildcards work
```

The default policy activates everything (`*`), which keeps the getting-started
experience simple. On a real platform, narrowing this is one of the highest-value
tuning changes available — teams routinely cut provider memory by 80%+.

You'll measure that yourself in the lab.

## 4. ProviderConfig — credentials and endpoint

A provider knows *how* to call S3. A **ProviderConfig** tells it *which account* and
*which endpoint*:

```yaml
apiVersion: aws.upbound.io/v1beta1
kind: ProviderConfig
metadata:
  name: default
spec:
  credentials:
    source: Secret
    secretRef:
      namespace: crossplane-system
      name: aws-creds
      key: creds
```

Keeping this separate from the resources is what lets one Crossplane manage **many
accounts**: a `prod-us` config, a `prod-eu` config, a `sandbox` config, each pointing
at different credentials. Every resource names the one it wants:

```yaml
spec:
  providerConfigRef:
    name: prod-us
```

If you omit `providerConfigRef`, Crossplane uses the one named `default`. Convenient
in a lab; a footgun in production, where an unlabelled resource quietly landing in the
wrong account is a real incident. Module 13 covers locking this down.

## 5. Anatomy of a managed resource

Every managed resource, in every provider, has this shape. Learn it once:

```yaml
apiVersion: s3.aws.upbound.io/v1beta1
kind: Bucket
metadata:
  name: my-bucket                             # the KUBERNETES name
  annotations:
    crossplane.io/external-name: real-name    # the AWS name (see §6)
spec:
  forProvider:                                # ← what YOU want
    region: us-east-1
  providerConfigRef:
    name: default                             # ← which account
  deletionPolicy: Delete                      # ← what happens on delete
  managementPolicies: ["*"]                   # ← which verbs are allowed
status:
  atProvider:                                 # ← what AWS SAYS IT IS
    arn: arn:aws:s3:::real-name
  conditions:                                 # ← health
    - type: Synced
      status: "True"
    - type: Ready
      status: "True"
```

The split that matters:

- **`spec.forProvider` is yours.** Crossplane never writes here (except late
  initialization — §7). It's your declaration.
- **`status.atProvider` is AWS's.** The provider writes it every reconcile. Read it
  to discover generated values: ARNs, IDs, endpoints.

**`Synced` vs `Ready`** is the distinction you'll use every day:

| Condition | Question it answers |
|-----------|--------------------|
| `Synced` | Did my last API call to AWS succeed? |
| `Ready` | Does the resource exist and is it usable? |

`Synced=False` is a **Crossplane/AWS communication problem** — bad credentials,
invalid parameters, no network. `Synced=True, Ready=False` is normal and means "AWS
accepted it, it's still being built."

## 6. The external name — the most important annotation

`metadata.name` is a Kubernetes identifier. It is **not** the resource's name in AWS.
The bridge between them is:

```yaml
metadata:
  annotations:
    crossplane.io/external-name: my-actual-bucket-name
```

Two behaviours follow:

- **Not set:** Crossplane creates a new resource and writes the resulting name/ID back
  into this annotation.
- **Set:** Crossplane looks for a resource with that name/ID and **adopts** it instead
  of creating one.

That second behaviour is how you import existing infrastructure without recreating it
— the subject of Module 03.

> **Never edit this annotation on a live resource.** Changing it doesn't rename
> anything in AWS; it points Crossplane at a *different* resource, orphaning the old
> one. On an RDS instance that means your database is suddenly unmanaged and a new
> empty one appears.

## 7. Late initialization

Cloud APIs fill in defaults you didn't specify. Create a bucket without saying
anything about ACLs and AWS picks one.

If Crossplane ignored those, it would see a difference on every reconcile and try
forever to "fix" it. Instead it **late-initializes**: it copies cloud-chosen defaults
back into your `spec.forProvider`.

So `kubectl get bucket -o yaml` after a while shows more fields than you applied.
That's not corruption — it's the provider recording what the cloud decided, so it can
tell a *real* future change from a default.

You can turn it off by removing `LateInitialize` from `managementPolicies` (Module 03).

## 8. Reading a provider's API

You don't need documentation for field names — the CRDs are in your cluster:

```bash
kubectl explain bucket.spec.forProvider
kubectl explain instance.spec.forProvider.engine
kubectl api-resources --api-group=s3.aws.upbound.io
```

`kubectl explain` is the fastest reference available and it always matches the exact
provider version you have installed.

---

## Do the lab
Install providers, measure what MRAP saves you, configure credentials, and provision
your first resources — including one that fails, on purpose.
👉 **[lab.md](./lab.md)**

Then: 👉 **[challenge.md](./challenge.md)**

## Manifests
- [`provider-s3.yaml`](./manifests/provider-s3.yaml) — the S3 provider
- [`provider-ec2.yaml`](./manifests/provider-ec2.yaml) — the EC2 provider
- [`mrap.yaml`](./manifests/mrap.yaml) — a narrow activation policy
- [`providerconfig.yaml`](./manifests/providerconfig.yaml) — emulator credentials and endpoint
- [`bucket-full.yaml`](./manifests/bucket-full.yaml) — a bucket with versioning and encryption
- [`bucket-broken.yaml`](./manifests/bucket-broken.yaml) — deliberately invalid

## Key terms
Provider · provider family · package (xpkg) · ProviderConfig · Managed Resource ·
`forProvider` · `atProvider` · external name · late initialization · MRD · MRAP ·
`Synced` · `Ready`

**Next →** [Module 03: Managed Resource Lifecycle](../03-managed-resource-lifecycle/)
