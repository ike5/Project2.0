# Challenge 07 — Reference Solution

Runnable manifests: [`xnetwork-nat.yaml`](./xnetwork-nat.yaml),
[`xnetwork-import.yaml`](./xnetwork-import.yaml),
[`broken-network.yaml`](./broken-network.yaml).

---

### 1. NAT gateways

See [`xnetwork-nat.yaml`](./xnetwork-nat.yaml). The structure, per AZ:

```gotemplate
{{- if $xr.spec.enableNatGateway }}
{{- range $i, $az := $azs }}
---
apiVersion: ec2.aws.upbound.io/v1beta1
kind: EIP
metadata:
  annotations:
    {{ setResourceNameAnnotation (printf "nat-eip-%s" $az) }}
spec:
  forProvider:
    region: {{ $region }}
    domain: vpc
  providerConfigRef: { name: default }
---
apiVersion: ec2.aws.upbound.io/v1beta1
kind: NATGateway
metadata:
  annotations:
    {{ setResourceNameAnnotation (printf "nat-%s" $az) }}
  labels: { az: {{ $az }} }
spec:
  forProvider:
    region: {{ $region }}
    # THE NAT GATEWAY GOES IN A **PUBLIC** SUBNET. It needs a route to the
    # internet gateway itself in order to forward traffic outward. Putting it
    # in a private subnet is the classic mistake and produces a NAT that is
    # itself unreachable.
    subnetIdSelector:
      matchControllerRef: true
      matchLabels: { tier: public, az: {{ $az }} }
    allocationIdSelector:
      matchControllerRef: true
      matchLabels: { az: {{ $az }} }
  providerConfigRef: { name: default }
---
# One private route table PER AZ, so traffic uses the NAT in its own AZ.
apiVersion: ec2.aws.upbound.io/v1beta1
kind: RouteTable
metadata:
  annotations:
    {{ setResourceNameAnnotation (printf "private-rt-%s" $az) }}
  labels: { tier: private, az: {{ $az }} }
spec:
  forProvider:
    region: {{ $region }}
    vpcIdSelector: { matchControllerRef: true }
  providerConfigRef: { name: default }
---
apiVersion: ec2.aws.upbound.io/v1beta1
kind: Route
metadata:
  annotations:
    {{ setResourceNameAnnotation (printf "private-route-%s" $az) }}
spec:
  forProvider:
    region: {{ $region }}
    routeTableIdSelector:
      matchControllerRef: true
      matchLabels: { tier: private, az: {{ $az }} }
    destinationCidrBlock: 0.0.0.0/0
    natGatewayIdSelector:
      matchControllerRef: true
      matchLabels: { az: {{ $az }} }
  providerConfigRef: { name: default }
---
apiVersion: ec2.aws.upbound.io/v1beta1
kind: RouteTableAssociation
metadata:
  annotations:
    {{ setResourceNameAnnotation (printf "private-assoc-%s" $az) }}
spec:
  forProvider:
    region: {{ $region }}
    subnetIdSelector:
      matchControllerRef: true
      matchLabels: { tier: private, az: {{ $az }} }
    routeTableIdSelector:
      matchControllerRef: true
      matchLabels: { tier: private, az: {{ $az }} }
  providerConfigRef: { name: default }
{{- end }}
{{- end }}
```

**One NAT gateway or one per AZ?**

*The availability argument for one-per-AZ:* if the single NAT lives in AZ `a` and AZ
`a` fails, private subnets in AZ `b` lose all outbound internet — even though `b` is
perfectly healthy. You have paid for multi-AZ and still have a single-AZ failure
domain. Worse, cross-AZ NAT traffic incurs data-transfer charges *and* higher latency
even when everything is working.

*The cost argument for one:* a NAT gateway is roughly **$32/month** in hourly charges
before a byte moves, plus about **$0.045/GB** processed. Three AZs is ~$1,150/year in
fixed cost per VPC. Multiply by dev, staging, and prod, and by every team with its own
VPC, and NAT becomes a genuinely significant line item — it is one of the most common
sources of surprise AWS bills.

*What I'd pick:*
- **Startup:** one NAT gateway, in one AZ, and accept the risk. At that stage a
  30-minute outage from an AZ failure is survivable and $700/year is not nothing. Make
  it a documented, deliberate decision rather than an accident — and set
  `enableNatGateway: false` entirely for environments that don't need outbound
  internet at all.
- **Bank:** one per AZ, without discussion. The regulatory and reputational cost of an
  avoidable outage dwarfs $1,150/year, and "we saved $70/month" is not a defensible
  answer in an incident review.

*The third option nobody considers:* many workloads only need outbound access to reach
**AWS services** (S3, ECR, Secrets Manager). **VPC endpoints** provide that with no
NAT gateway at all — a Gateway endpoint for S3 is free. Reaching for a NAT when you
only needed an S3 endpoint is a common and expensive mistake.

### 2. Fixing CIDR allocation

`netIndex` fails because nothing prevents two people choosing the same value. Three
mechanisms, in increasing robustness:

**a) Validating admission policy — cheap and effective:**
```yaml
apiVersion: admissionregistration.k8s.io/v1
kind: ValidatingAdmissionPolicy
metadata: { name: unique-net-index }
spec:
  matchConstraints:
    resourceRules:
      - apiGroups: ["platform.acme.io"]
        apiVersions: ["v1alpha1"]
        operations: ["CREATE", "UPDATE"]
        resources: ["xnetworks"]
  variables:
    - name: others
      expression: "params.items.filter(x, x.metadata.name != object.metadata.name)"
  validations:
    - expression: "!variables.others.exists(x, x.spec.netIndex == object.spec.netIndex)"
      message: "netIndex is already in use by another XNetwork"
```
*Doesn't solve:* races between two simultaneous applies, and it can't see networks
created outside this cluster (the Terraform-built ones, for instance).

**b) `function-extra-resources` — allocate during rendering:**
```yaml
- step: load-existing
  functionRef: { name: function-extra-resources }
  input:
    apiVersion: extra-resources.fn.crossplane.io/v1beta1
    kind: Input
    spec:
      extraResources:
        - kind: XNetwork
          into: existing
          type: Selector
          selector:
            maxMatch: 100
            matchLabels: []
```
Then compute the lowest unused index in the template.
*Doesn't solve:* it's still racy — two XRs rendering simultaneously both see the same
"lowest unused" value. And a re-render after another network is deleted could
*reallocate* an index, which would rewrite a live VPC's CIDR. **This one is actively
dangerous** unless you also pin the allocation into status on first render and never
recompute it.

**c) A real allocation registry — the correct answer:**
Keep the allocation in a single object that is updated transactively:
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: cidr-allocations
  namespace: crossplane-system
data:
  "10.101.0.0/20": "team-payments/payments-net"
  "10.102.0.0/20": "team-search/search-net"
```
A small controller (or an `Operation`, Module 11) claims a free block using an
optimistic-concurrency update, and the XR reads its assigned block from status. The
Kubernetes API server's `resourceVersion` check makes the claim atomic, which is
exactly the primitive the other two approaches lack.

*Doesn't solve:* networks created outside the system still need to be registered
manually. In practice most organisations reserve ranges per environment and per region
up front in an IPAM tool (AWS has a managed one), and the platform allocates within
its assigned range.

**Recommendation:** ship (a) today because it takes ten minutes and catches the common
case, and plan for (c). Avoid (b) — a mechanism that can silently reassign a live
network's address space is worse than the footgun it replaces.

### 3. Importing an existing VPC

See [`xnetwork-import.yaml`](./xnetwork-import.yaml). The mechanism is Module 03's,
applied to a composition: set external names on the composed resources to the real
AWS IDs.

```gotemplate
apiVersion: ec2.aws.upbound.io/v1beta1
kind: VPC
metadata:
  annotations:
    {{ setResourceNameAnnotation "vpc" }}
    crossplane.io/external-name: {{ $xr.spec.existingVpcId }}
spec:
  managementPolicies: ["Observe"]
  forProvider:
    region: {{ $region }}
  providerConfigRef: { name: default }
```

**Start with `managementPolicies: ["Observe"]` on every composed resource.**

**What goes wrong if you skip to `["*"]`:** your composition declares
`cidrBlock: 10.101.0.0/20` because that's what `netIndex: 1` computes. The real VPC is
`10.0.0.0/16`. On the first reconcile Crossplane tries to make reality match — and
since a VPC's CIDR **cannot be changed in place**, the provider's only route to
convergence is to *delete and recreate the VPC*. That destroys every subnet, every
route, and every resource inside it, in production, within about sixty seconds of your
`kubectl apply`.

This is the single most destructive mistake available in Crossplane, and Observe-first
prevents it entirely: you see the real values, copy them into your spec, confirm the
render matches, *then* widen.

Practical import sequence:
1. Compose everything with `["Observe"]`.
2. `kubectl get xnetwork ... -o jsonpath='{.status}'` and compare with the real VPC.
3. Adjust the composition so its computed values **match reality exactly**.
4. `crossplane render` and diff against `awslocal ec2 describe-*` output.
5. Widen to `["Observe","Create","Update"]` — note, still no `Delete`.
6. Add `Delete` only once you're confident, and set `deletionPolicy: Orphan` on the
   VPC regardless.

### 4. Diagnosing the broken network

**The fault: there is no `RouteTableAssociation`.** The route table exists, the
`0.0.0.0/0` route to the internet gateway exists — but nothing binds that table to the
subnet, so the subnet falls back to the VPC's main route table, which has only the
local route.

**A good diagnostic sequence:**

```bash
# 1. Is anything failing at the Crossplane layer?
kubectl get managed
#    Everything is SYNCED=True READY=True. So this is NOT a Crossplane problem --
#    every resource we asked for exists. That immediately tells you the fault is
#    in what we DECLARED, not in how it was applied.

# 2. Does the internet gateway exist and is it attached?
awslocal ec2 describe-internet-gateways \
  --query 'InternetGateways[].{Id:InternetGatewayId,Attached:Attachments[].VpcId}'
#    Yes, attached to the VPC. Not the fault.

# 3. Does a route to it exist?
awslocal ec2 describe-route-tables \
  --query 'RouteTables[].{Id:RouteTableId,Routes:Routes[].DestinationCidrBlock}'
#    Yes, a 0.0.0.0/0 route exists. Not the fault.

# 4. WHICH route table does the subnet actually use?
SUBNET=$(awslocal ec2 describe-subnets --filters "Name=tag:tier,Values=public" \
  --query 'Subnets[0].SubnetId' --output text)
awslocal ec2 describe-route-tables \
  --filters "Name=association.subnet-id,Values=$SUBNET" \
  --query 'RouteTables[].RouteTableId'
#    EMPTY. Nothing is associated with this subnet.  <-- THE FAULT

# 5. Confirm by listing associations on the route table we built
awslocal ec2 describe-route-tables --route-table-ids <rt-id> \
  --query 'RouteTables[0].Associations'
#    Empty.
```

**The fix:**
```yaml
apiVersion: ec2.aws.upbound.io/v1beta1
kind: RouteTableAssociation
metadata:
  name: broken-assoc
spec:
  forProvider:
    region: us-east-1
    subnetIdRef: { name: broken-public-subnet }
    routeTableIdRef: { name: broken-rt }
  providerConfigRef: { name: default }
```

**The lesson about method, which matters more than the answer:** step 1 was the
important one. Confirming that *every Crossplane resource was healthy* immediately
ruled out half the possible causes and told you to stop reading Crossplane logs and
start reading AWS state. A green control plane and a broken system means **you
declared the wrong thing** — and no amount of `kubectl describe` will show you what
you failed to write.

### 5. Stretch — peering, and why it doesn't scale

```yaml
apiVersion: ec2.aws.upbound.io/v1beta1
kind: VPCPeeringConnection
metadata: { name: net1-net2 }
spec:
  forProvider:
    region: us-east-1
    vpcIdRef: { name: net1-vpc }
    peerVpcIdRef: { name: net2-vpc }
    autoAccept: true
  providerConfigRef: { name: default }
---
# Routes are needed on BOTH sides -- peering alone carries no traffic.
apiVersion: ec2.aws.upbound.io/v1beta1
kind: Route
metadata: { name: net1-to-net2 }
spec:
  forProvider:
    region: us-east-1
    routeTableIdRef: { name: net1-rt }
    destinationCidrBlock: 10.102.0.0/20
    vpcPeeringConnectionIdRef: { name: net1-net2 }
  providerConfigRef: { name: default }
```

**Why a full mesh doesn't scale:**

1. **O(n²) connections.** 10 VPCs need 45 peering connections; 20 need 190. Each needs
   routes on both sides, so you're maintaining hundreds of route entries.
2. **Peering is not transitive.** A↔B and B↔C does *not* give A↔C. You cannot route
   through an intermediate VPC, so the mesh must genuinely be full.
3. **Route table entry limits.** A route table caps at 50 routes by default (raisable
   to 1000, at a performance cost). A large mesh exhausts it.
4. **CIDRs must never overlap.** Any two VPCs you might *ever* want to peer must have
   disjoint ranges — which is precisely why Task 2's allocation problem matters so
   much, and why getting it wrong is unrecoverable without renumbering.

**What AWS offers instead: Transit Gateway.** A hub-and-spoke router: each VPC
attaches once, and the gateway handles transitive routing between all of them. That's
O(n) attachments instead of O(n²) peerings, with centralised route tables and
segmentation. It costs more per hour and adds a data-processing charge, so peering
remains correct for two or three VPCs — but past roughly five, Transit Gateway is the
answer.
