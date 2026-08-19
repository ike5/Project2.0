# Glossary

Plain-English definitions of every term used in this course. Skim it now; come back
whenever a word trips you up.

Terms marked **(v1 only)** were removed or demoted in Crossplane v2. They're listed
because you *will* hit them in older blog posts and Stack Overflow answers, and you
need to recognise them as out of date.

---

## The big picture

- **Control plane** — Software that continuously drives the real world toward a
  declared desired state. Kubernetes is a control plane for containers; Crossplane
  turns it into a control plane for *anything with an API*.
- **Reconciliation** — The never-ending loop: observe reality → compare to desired
  state → act on the difference → repeat. The single most important idea in this
  course.
- **Drift** — When reality stops matching desired state (someone clicked something in
  the AWS console). A control plane *corrects* drift; a provisioning tool only
  *reports* it on the next run.
- **Declarative** — You describe the end state you want. Contrast with **imperative**,
  where you describe the steps to get there.
- **Platform API** — An interface your platform team designs for its developers, that
  hides infrastructure detail. "Give me a Postgres" instead of 40 lines of RDS config.
  Building one is the point of this course.
- **Infrastructure as Code (IaC)** — The general practice of defining infrastructure
  in version-controlled files. Crossplane is IaC; so is Terraform. They differ in
  *what runs the code* (a persistent controller vs. a CLI in a pipeline).

## Crossplane core objects

- **Provider** — An installable package that teaches Crossplane to manage one
  external API (AWS, Azure, GitHub, Datadog…). Ships as a pod plus a set of CRDs.
- **Provider family** — Modern providers are split by service (`provider-aws-s3`,
  `provider-aws-ec2`) rather than one giant `provider-aws`. Family members share a
  common `provider-family-aws` that owns the `ProviderConfig` type.
- **ProviderConfig** — Tells a provider *how to authenticate* and *which endpoint to
  call*. Separate from the resources themselves, so one provider can manage several
  accounts.
- **Managed Resource (MR)** — One external resource represented as a Kubernetes
  object. An S3 `Bucket`, an EC2 `VPC`, an RDS `Instance`. The atoms of Crossplane.
- **`spec.forProvider`** — The part of an MR that maps to the cloud API's own fields.
  If AWS calls it `BucketName`, it lives here as `bucketName`.
- **`status.atProvider`** — What the cloud API says the resource *actually* looks
  like right now. Read-only, written by the provider.
- **External name** — The resource's real identity in the cloud (the actual bucket
  name, the `vpc-0abc123` ID). Stored in the
  `crossplane.io/external-name` annotation. **This is the field that makes importing
  existing infrastructure possible.**

## Composition — building your own APIs

- **CompositeResourceDefinition (XRD)** — Defines *your* API: its group, kind, and
  the schema of fields users can set. Creates a new CRD in the cluster. Think of it
  as the interface.
- **Composite Resource (XR)** — An instance of the API an XRD defines. When a user
  creates one, Crossplane creates the underlying resources. Think of it as the object.
- **Composition** — The implementation behind an XRD: given an XR, what resources
  should exist? One XRD can have several Compositions (e.g. dev vs. prod).
- **Composed resource** — Any resource an XR creates. In v2 this can be a managed
  resource, another XR, *or* a plain Kubernetes object like a Deployment.
- **Scope** — An XRD field controlling where XRs live:
  - `Namespaced` — the v2 default. XRs live in a namespace and compose resources in
    that namespace. Best for multi-tenancy.
  - `Cluster` — XRs are cluster-scoped and can compose anywhere.
  - `LegacyCluster` — v1 compatibility mode; the only scope that still supports claims.
- **Claim (XRC)** **(v1 only)** — The old namespaced front-end to a cluster-scoped XR.
  v2 made XRs themselves namespaced, so claims are no longer needed. If a tutorial
  tells you to write a `kind: PostgreSQLInstance` claim alongside an
  `XPostgreSQLInstance`, it predates v2.
- **`spec.crossplane`** — Where a v2 XR keeps its Crossplane machinery
  (`compositionRef`, `compositionRevisionRef`, `resourceRefs`), keeping it out of the
  way of your own API fields.
- **CompositionRevision** — An immutable snapshot of a Composition, created on every
  change. Lets existing XRs pin to the version they were created with while you roll
  out a new one.
- **`compositionUpdatePolicy`** — `Automatic` (default: follow the latest revision) or
  `Manual` (stay pinned until a human moves you). The main safety valve for risky
  composition changes.

## Composition functions

- **Composition function** — A program Crossplane calls to decide what an XR should
  produce. Runs as a pod, speaks gRPC. **In v2 this is the only way compositions
  work.**
- **Pipeline** — An ordered list of function steps. Each receives the previous step's
  output, so you can layer generic templating, then patching, then validation.
- **`function-patch-and-transform`** — The function that reproduces classic
  patch-and-transform behaviour: templates of resources plus patches that copy fields
  from the XR into them.
- **`function-go-templating`** — Renders resources from Go templates. Better than
  patch-and-transform when you need loops or conditionals ("one subnet per AZ").
- **`function-auto-ready`** — Marks the XR `Ready` once its composed resources are
  ready. Almost every pipeline ends with this.
- **`function-sequencer`** — Forces resources to be created in a set order, for the
  cases where a cloud API genuinely can't tolerate parallel creation.
- **Patch** — A rule copying a value between the XR and a composed resource.
  `FromCompositeFieldPath` (XR → resource) and `ToCompositeFieldPath` (resource → XR
  status) are the two you'll use most.
- **Transform** — A modification applied to a value in transit: string formatting,
  a lookup map, arithmetic, a regex match.
- **Native patch-and-transform (`mode: Resources`)** **(v1 only)** — Compositions used
  to list resources and patches directly. Removed in v2; the identical functionality
  now comes from `function-patch-and-transform`.

## Managed resource lifecycle

- **`managementPolicies`** — Which verbs Crossplane may use on a resource:
  `Create`, `Observe`, `Update`, `Delete`, `LateInitialize`, or `*` for all.
  Setting only `["Observe"]` gives you a read-only, safe way to adopt existing infra.
- **`deletionPolicy`** — What happens to the *cloud* resource when you delete the
  Kubernetes object: `Delete` (default) or `Orphan` (leave it running).
- **Late initialization** — Crossplane writing cloud-chosen defaults back into your
  spec, so it doesn't repeatedly try to "fix" values you never set.
- **`crossplane.io/paused` annotation** — Set to `"true"` to stop reconciling one
  resource. The emergency brake: it stops Crossplane fighting you while you
  investigate, without deleting anything.
- **ManagedResourceDefinition (MRD)** — A v2 wrapper over a CRD that lets a managed
  resource's schema be *installed* without being *activated*.
- **ManagedResourceActivationPolicy (MRAP)** — Pattern-matching rules choosing which
  MRDs actually become live CRDs. Providers ship hundreds of resource types; MRAP
  lets you activate the four you use, saving significant API-server memory and CPU.

## Packaging and distribution

- **Package (xpkg)** — An OCI image containing Crossplane extensions. Providers,
  functions, and configurations all ship this way, so any container registry works.
- **Configuration** — A package containing XRDs and Compositions: your platform API,
  versioned and shareable. What a platform team publishes for its developers.
- **`crossplane.yaml`** — The metadata file at the root of a package: its name,
  version, and dependencies.
- **Dependency** — A package another package needs. Installing a Configuration
  automatically pulls the providers and functions it declares.

## Operations (day two)

- **Operation** — A one-shot function pipeline that runs to completion, like a
  Kubernetes Job. For tasks that *do* something rather than *maintain* something —
  a backup, a rotation, a migration.
- **CronOperation** — Creates Operations on a cron schedule.
- **WatchOperation** — Creates Operations in response to resource changes.
- **Concurrency policy** — `Allow` (default), `Forbid`, or `Replace` — what to do when
  a scheduled Operation is still running as the next one comes due.

## Connection and configuration plumbing

- **Connection details / connection secret** — Credentials and endpoints a resource
  produces (a DB password, an RDS hostname). Crossplane writes them to a Kubernetes
  Secret so applications can consume them without a human ever seeing the value.
- **`writeConnectionSecretToRef`** — Where a resource should write its connection
  Secret.
- **EnvironmentConfig** — A cluster-scoped bag of values a composition can read at
  render time: account IDs, VPC IDs, region maps. Keeps per-environment data out of
  your compositions.
- **`Usage`** — An object declaring "resource A is used by resource B", so Crossplane
  refuses to delete A while B exists. Prevents the classic "deleted the VPC before the
  subnets" failure.
- **Extra resources** — Arbitrary existing cluster resources a function can request
  and read while rendering, via `function-extra-resources`.

## AWS terms used in this course

- **VPC** — Your own private network in AWS. Everything else lives inside one.
- **Subnet** — An IP range inside a VPC, tied to one Availability Zone. **Public**
  subnets route to an internet gateway; **private** ones don't.
- **Availability Zone (AZ)** — An isolated datacentre within a region. Spreading
  across AZs is how you survive one failing.
- **Internet Gateway (IGW)** — Attaches to a VPC to give it internet access.
- **NAT Gateway** — Lets private subnets reach *out* to the internet without being
  reachable *from* it.
- **Route table** — Rules for where traffic leaves a subnet.
- **Security group** — A stateful virtual firewall attached to resources.
- **IAM** — AWS's identity and permission system.
- **IAM policy** — A JSON document listing allowed/denied actions on resources.
- **IAM role** — An identity that can be *assumed*, rather than one with a permanent
  password. How services get permissions safely.
- **Trust policy (assume-role policy)** — The policy on a role saying *who* may assume
  it. Distinct from the permission policies saying *what* the role can do.
- **IRSA (IAM Roles for Service Accounts)** — The EKS mechanism that lets a Kubernetes
  ServiceAccount assume an IAM role, so pods get AWS permissions with no static keys.
  The right way to authenticate a provider on EKS.
- **STS** — AWS's token service; the thing that actually hands out temporary
  credentials when a role is assumed.
- **RDS** — AWS's managed relational database service.
- **DynamoDB** — AWS's managed NoSQL key-value database.
- **ARN (Amazon Resource Name)** — The globally unique ID of any AWS resource.
  `arn:aws:s3:::my-bucket`.

## Kubernetes terms worth re-stating

You know these from the Kubernetes course, but they mean something specific here:

- **CRD (CustomResourceDefinition)** — How you add a new object type to the Kubernetes
  API. Providers install them; XRDs generate them.
- **Controller** — A loop that watches objects and acts on them. Every provider is
  one; so is Crossplane's own composition engine.
- **Conditions** — The `status.conditions` list on an object, reporting health. In
  Crossplane the two you read constantly are **`Synced`** (did the API call succeed?)
  and **`Ready`** (does the resource actually exist and work?).
- **Finalizer** — A marker preventing deletion until cleanup finishes. When a
  Crossplane object won't delete, a stuck finalizer is usually why.
- **Owner reference** — The link from a composed resource back to its XR, which is how
  garbage collection cascades.
