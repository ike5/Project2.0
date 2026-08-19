# Module 07 — AWS Networking

**Goal:** compose a real VPC — subnets, gateways, routing, security groups — and
understand why this is the hardest thing to get right in cloud infrastructure.

⏱️ ~3 hours · 🎯 Prereq: Modules 04–06.

---

## 1. Why networking first

Every AWS resource that isn't S3 or IAM lives inside a VPC. RDS needs subnets. EKS
needs subnets. Load balancers need subnets. **You cannot build anything substantial
without networking**, which is why it's the first of the three AWS-depth modules.

It's also where Crossplane's reference-resolution machinery gets a proper workout: a
working VPC is about a dozen resources that must all point at each other, in an order
nobody explicitly specifies.

## 2. The anatomy of a working VPC

```
┌─────────────────────────────────────────────────────────────┐
│ VPC  10.0.0.0/16                                            │
│                                                             │
│  ┌──────────────────────┐   ┌──────────────────────┐        │
│  │ Public subnet        │   │ Public subnet        │        │
│  │ 10.0.0.0/24  (AZ a)  │   │ 10.0.1.0/24  (AZ b)  │        │
│  │      │               │   │      │               │        │
│  └──────┼───────────────┘   └──────┼───────────────┘        │
│         │  route 0.0.0.0/0 ────────┴──────► ┌─────┐         │
│         │                                   │ IGW │◄────────┼─── internet
│         │                                   └─────┘         │
│  ┌──────┴───────────────┐   ┌──────────────────────┐        │
│  │ Private subnet       │   │ Private subnet       │        │
│  │ 10.0.10.0/24 (AZ a)  │   │ 10.0.11.0/24 (AZ b)  │        │
│  │   (no 0.0.0.0/0      │   │                      │        │
│  │    route to IGW)     │   │   RDS lives here     │        │
│  └──────────────────────┘   └──────────────────────┘        │
└─────────────────────────────────────────────────────────────┘
```

| Resource | Job |
|----------|-----|
| `VPC` | The network. A CIDR block and some DNS settings. |
| `Subnet` | An IP range **in one availability zone**. |
| `InternetGateway` | Attaches to the VPC; the door to the internet. |
| `RouteTable` | A set of routing rules. |
| `Route` | One rule: "traffic for X goes to Y". |
| `RouteTableAssociation` | **Binds a subnet to a route table.** |
| `SecurityGroup` | A stateful firewall attached to resources. |
| `NATGateway` | Lets private subnets reach out without being reachable. |

### The three things that trip everyone up

**1. "Public" is not a property of a subnet.** There is no `public: true` field. A
subnet is public *if and only if* its route table has a `0.0.0.0/0` route pointing at
an internet gateway, **and** a `RouteTableAssociation` links that table to that
subnet. Miss the association and you have a subnet that looks configured and silently
routes nowhere.

**2. Availability zones are region-specific, and two are usually the minimum.**
`us-east-1a` doesn't exist in `eu-west-1`. And RDS requires a subnet group spanning
**at least two AZs** even for a single-AZ database — this is the single most common
RDS composition failure.

**3. NAT Gateways cost real money.** Roughly $32/month each plus data processing
charges, and the textbook "one per AZ" design triples that. On the emulator they're
free, which makes it easy to build a habit your finance team will dislike.

## 3. Reference resolution — how the pieces find each other

You don't know the VPC's ID when you write the composition; AWS assigns it at
creation. Crossplane solves this with **references**:

```yaml
# By Kubernetes object name — the usual choice
vpcIdRef:
  name: my-vpc

# By label selector — flexible, works well in compositions
vpcIdSelector:
  matchControllerRef: true      # "the VPC composed by this same XR"

# By literal ID — only for resources Crossplane doesn't manage
vpcId: vpc-0abc123def456
```

**How it works:** the provider sees `vpcIdRef`, looks up that object, reads its
external name (the real `vpc-…` ID), and writes it into `spec.forProvider.vpcId`. If
the VPC doesn't exist yet, resolution fails, the resource reports
`cannot resolve references`, and it retries next reconcile.

**This is why you don't need `function-sequencer` for most dependency ordering.**
Resources are created in parallel, the dependent ones fail to resolve, and they
succeed on a later pass. The system converges. It looks alarming in the first 30
seconds — a lot of `Synced=False` — and then it's fine.

> `matchControllerRef: true` is the form you want inside compositions. It means "the
> resource composed by the same XR as me", so two `XNetwork` instances in the same
> cluster never cross-wire.

## 4. Security groups

A security group is a **stateful** firewall: allow traffic in, and the response is
automatically allowed out. You write rules for the direction the *connection* is
initiated, not for individual packets.

```yaml
apiVersion: ec2.aws.upbound.io/v1beta1
kind: SecurityGroupRule
spec:
  forProvider:
    type: ingress
    fromPort: 5432
    toPort: 5432
    protocol: tcp
    securityGroupIdRef: { name: db-sg }
    # Reference ANOTHER security group rather than a CIDR:
    sourceSecurityGroupIdRef: { name: app-sg }
```

**Referencing another security group instead of a CIDR is the pattern worth
learning.** `sourceSecurityGroupIdRef: app-sg` means "anything in the app security
group may connect", which stays correct as IPs change, instances are replaced, and
the app scales. A hardcoded CIDR does not.

> `SecurityGroup.spec.forProvider.description` is **required** by AWS. An empty
> description is rejected, with an error that doesn't obviously say so.

## 5. Deletion order

Networking is where deletion gets genuinely hard. AWS refuses to delete a VPC that
still contains subnets, an internet gateway that's still attached, or a security group
that's still referenced — all with `DependencyViolation`.

Crossplane deletes composed resources in parallel, so teardown produces a burst of
failures that mostly resolve themselves as dependencies clear. Mostly. When it
doesn't, you have resources stuck `Terminating` and a VPC that won't go away.

Module 10 introduces the `Usage` object, which declares dependencies explicitly so
Crossplane orders deletion correctly. For now, expect messy teardowns and know why.

## 6. Designing the network API

The interesting design question: **what should a developer be allowed to choose?**

A tempting API:
```yaml
spec:
  cidrBlock: 10.0.0.0/16
  publicSubnets: ["10.0.0.0/24", "10.0.1.0/24"]
  privateSubnets: ["10.0.10.0/24", "10.0.11.0/24"]
  availabilityZones: ["us-east-1a", "us-east-1b"]
```
This is flexible and **wrong for most organisations**. It lets a developer pick a CIDR
that overlaps another VPC, choose one AZ and lose availability, or forget private
subnets entirely.

A better API:
```yaml
spec:
  size: small        # small=/20, medium=/18, large=/16
  region: us-east-1
  highAvailability: true
```
The platform computes CIDRs from an allocation scheme it controls, picks AZs, and
guarantees the private subnets exist. **The developer states intent; the platform
holds the invariants.**

This is the Module 04 API-design lesson applied to the hardest domain — and the lab
builds the second version.

---

## Do the lab
Compose a complete VPC with public and private subnets across two AZs, watch
reference resolution converge, and prove which subnets can actually reach the
internet.
👉 **[lab.md](./lab.md)**

Then: 👉 **[challenge.md](./challenge.md)**

## Manifests
- [`xrd.yaml`](./manifests/xrd.yaml) — the `XNetwork` API (intent, not CIDRs)
- [`composition.yaml`](./manifests/composition.yaml) — the full VPC build
- [`xr-network.yaml`](./manifests/xr-network.yaml) — a developer's request
- [`raw-vpc.yaml`](./manifests/raw-vpc.yaml) — the same thing as raw managed resources, for contrast

## Key terms
VPC · CIDR · subnet · availability zone · internet gateway · NAT gateway ·
route table · route table association · security group · reference resolution ·
`matchControllerRef` · `DependencyViolation`

**Next →** [Module 08: AWS IAM & Identity](../08-aws-iam-and-identity/)
