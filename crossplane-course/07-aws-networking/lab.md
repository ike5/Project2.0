# Lab 07 — Build a VPC, Twice

**You'll:** build a network the hard way with raw managed resources, watch reference
resolution converge, then hide all of it behind a four-line API — and prove which
subnets can actually reach the internet. ⏱️ ~80 min.

> Prereqs: Modules 04–06. The EC2 provider from Module 02 must be installed and its
> types activated in your MRAP.

---

## Part A — The hard way

Apply a working VPC as raw managed resources so you feel the volume:

```bash
cd 07-aws-networking
grep -c '^kind:' manifests/raw-vpc.yaml
kubectl apply -f manifests/raw-vpc.yaml
```
✅ Expected: `7` resources for the *smallest useful* network — and that's with no
private subnets at all.

**Immediately** check status, before waiting:
```bash
kubectl get managed
```
✅ Expected: most resources `SYNCED=False`:
```
NAME                              SYNCED   READY
vpc.ec2.../raw-vpc                False
subnet.ec2.../raw-subnet-a        False
internetgateway.ec2.../raw-igw    False
...
```

**This looks broken. It isn't.** Read why:
```bash
kubectl get subnet raw-subnet-a \
  -o jsonpath='{.status.conditions[?(@.type=="Synced")].message}'; echo
```
✅ Expected: something like `cannot resolve references: ... referenced resource is not
yet ready`.

The subnet references a VPC that doesn't exist yet. Resolution failed. It will retry.

Wait and watch it converge:
```bash
sleep 60
kubectl get managed
```
✅ Expected: everything `SYNCED=True READY=True`.

> **This convergence pattern is the heart of Crossplane.** Resources are created in
> parallel, dependent ones fail, and the loop retries until the graph resolves. You
> almost never need explicit ordering — you need patience for the first 60 seconds.

Verify from AWS's side:
```bash
awslocal ec2 describe-vpcs --query 'Vpcs[].{Id:VpcId,Cidr:CidrBlock}' --output table
awslocal ec2 describe-subnets --query 'Subnets[].{Id:SubnetId,Az:AvailabilityZone,Cidr:CidrBlock}' --output table
```
✅ Expected: one VPC (`10.99.0.0/16`) and two subnets in different AZs.

## Part B — Prove what "public" means

The route table association is the step people forget. Prove it matters.

```bash
RT=$(kubectl get routetable raw-public-rt \
  -o jsonpath='{.metadata.annotations.crossplane\.io/external-name}')
awslocal ec2 describe-route-tables --route-table-ids "$RT" \
  --query 'RouteTables[0].{Routes:Routes,Assocs:Associations[].SubnetId}'
```
✅ Expected: a `0.0.0.0/0` route pointing at an `igw-…`, and **two associated subnet
IDs**.

Now delete one association and observe:
```bash
kubectl delete routetableassociation raw-assoc-b
sleep 20
awslocal ec2 describe-route-tables --route-table-ids "$RT" \
  --query 'RouteTables[0].Associations[].SubnetId'
```
✅ Expected: only **one** subnet listed. `raw-subnet-b` still exists, still has an IP
range, still looks fine in `describe-subnets` — and now routes nowhere.

**There is no field on the subnet that tells you this.** "Public" is an emergent
property of three resources agreeing. This is why networking is composed, not
configured.

Restore it:
```bash
kubectl apply -f manifests/raw-vpc.yaml
```

## Part C — Tear it down and see DependencyViolation

```bash
kubectl delete -f manifests/raw-vpc.yaml --wait=false
sleep 15
kubectl get managed
kubectl get vpc raw-vpc -o jsonpath='{.status.conditions[?(@.type=="Synced")].message}'; echo
```
✅ Expected: the VPC reports a `DependencyViolation` — AWS refuses to delete a VPC
that still contains subnets.

Wait for it to sort itself out:
```bash
sleep 90
kubectl get managed
```
✅ Expected: everything gone. The subnets deleted first, then the VPC's next retry
succeeded.

> Deletion converges the same way creation does. It's noisy, and when it *doesn't*
> converge you get resources stuck `Terminating` — Module 10's `Usage` object fixes
> the ordering explicitly.

## Part D — Now the good way

```bash
kubectl apply -f manifests/xrd.yaml
kubectl apply -f manifests/composition.yaml
kubectl apply -f manifests/xr-network.yaml
kubectl get xnetworks -n team-payments -w    # Ctrl-C when READY is True
```
✅ Expected, after 1–2 minutes:
```
NAME           SIZE    CIDR            VPC              READY
payments-net   small   10.101.0.0/20   vpc-0a1b2c3d4e   True
```

```bash
crossplane trace xnetwork payments-net -n team-payments
```
✅ Expected: **~14 resources** — VPC, IGW, route table, route, 2 public subnets, 2
associations, 2 private subnets, 2 security groups, 2 rules.

**From four lines of developer YAML.** Compare with the 7-resource, less capable
version you hand-wrote in Part A.

Check what the platform computed:
```bash
kubectl get xnetwork payments-net -n team-payments -o jsonpath='{.status}' | jq
```
✅ Expected:
```json
{
  "cidrBlock": "10.101.0.0/20",
  "vpcId": "vpc-0a1b2c3d4e",
  "publicSubnetIds": ["subnet-...", "subnet-..."],
  "privateSubnetIds": ["subnet-...", "subnet-..."]
}
```

The developer never chose a CIDR. `netIndex: 1` selected slot 1 in the platform's
address plan and the composition derived everything else.

## Part E — Verify the invariants the platform promised

**Two availability zones** (required for RDS):
```bash
awslocal ec2 describe-subnets \
  --filters "Name=tag:tier,Values=private" \
  --query 'Subnets[].{Az:AvailabilityZone,Cidr:CidrBlock}' --output table
```
✅ Expected: two rows, different AZs.

**Private subnets have no route to the internet:**
```bash
PRIV=$(awslocal ec2 describe-subnets --filters "Name=tag:tier,Values=private" \
  --query 'Subnets[0].SubnetId' --output text)
awslocal ec2 describe-route-tables \
  --filters "Name=association.subnet-id,Values=$PRIV" \
  --query 'RouteTables[].Routes[].DestinationCidrBlock'
```
✅ Expected: empty or no route table — the private subnets were never associated with
the public route table, so they use the VPC's default (local-only) routing. **They
cannot reach the internet, by construction.**

**The database is reachable only from the app tier:**
```bash
DBSG=$(kubectl get securitygroup -l role=db \
  -o jsonpath='{.items[0].metadata.annotations.crossplane\.io/external-name}')
awslocal ec2 describe-security-groups --group-ids "$DBSG" \
  --query 'SecurityGroups[0].IpPermissions'
```
✅ Expected: one rule, port 5432, whose source is **another security group ID** — not
a CIDR block.

> That's the pattern to internalise. `sourceSecurityGroupId` stays correct forever;
> a hardcoded CIDR is correct until the first time anything moves.

## Part F — Change intent, watch the network adapt

```bash
kubectl patch xnetwork payments-net -n team-payments --type=merge \
  -p '{"spec":{"highAvailability":false}}'
sleep 45
crossplane trace xnetwork payments-net -n team-payments | head -20
```
✅ Expected: the `us-east-1b` subnets and their association are **gone**. Fewer
resources, same composition.

**Now think about what you just did.** In a real account that deleted a subnet.
Anything running in it would have lost its network. Restore it:
```bash
kubectl patch xnetwork payments-net -n team-payments --type=merge \
  -p '{"spec":{"highAvailability":true}}'
sleep 45
```

> **A one-word change destroyed and rebuilt real infrastructure.** This is the
> control-plane trade-off from Module 01 made concrete: no plan step, no approval —
> the loop simply reconciled to the new declaration. Module 11's composition
> revisions and Module 13's admission policies exist for exactly this.

## Part G — Break reference resolution

```bash
kubectl apply -f - <<'YAML'
apiVersion: ec2.aws.upbound.io/v1beta1
kind: Subnet
metadata:
  name: orphan-subnet
spec:
  forProvider:
    region: us-east-1
    cidrBlock: 10.200.0.0/24
    availabilityZone: us-east-1a
    vpcIdRef:
      name: a-vpc-that-does-not-exist
  providerConfigRef:
    name: default
YAML
sleep 30
kubectl get subnet orphan-subnet
kubectl get subnet orphan-subnet -o jsonpath='{.status.conditions[?(@.type=="Synced")].message}'; echo
```
✅ Expected: permanently `SYNCED=False`, with a message about being unable to resolve
references.

**It will retry forever and never succeed.** Note the failure mode: not an error at
apply time, not a crash — a resource that sits there quietly failing. This is exactly
why `crossplane trace` matters, and why Module 12 covers alerting on unsynced
resources.

```bash
kubectl delete subnet orphan-subnet
```

## Part H — Clean up

```bash
kubectl delete xnetwork --all -n team-payments
sleep 120
kubectl get managed
awslocal ec2 describe-vpcs --query 'Vpcs[].VpcId'
```
✅ Expected: eventually empty. Teardown takes longer than creation because of the
dependency retries — be patient, and re-run if resources are still `Terminating`.

**Leave the XRD and composition installed** — Module 09 builds a database inside this
network.

---

## What you learned
- A working VPC is ~12 interdependent resources; "public" is an emergent property of
  a route, a route table, and an **association**, not a field.
- **Reference resolution converges**: resources are created in parallel, dependent
  ones fail and retry. Early `SYNCED=False` is normal, not broken.
- `matchControllerRef: true` scopes a reference to "composed by my XR".
- Security groups should reference **other security groups**, not CIDRs.
- Teardown hits `DependencyViolation` and converges too — usually.
- A good network API exposes **intent** (`size`, `highAvailability`) and keeps CIDR
  allocation in the platform's hands.

➡️ **[challenge.md](./challenge.md)** then [Module 08](../08-aws-iam-and-identity/).
