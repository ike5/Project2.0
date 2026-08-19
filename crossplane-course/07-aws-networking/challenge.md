# Challenge 07 — Networking That Survives Contact With Reality

Solutions in [`solutions/`](./solutions/). Try first.

## Tasks

1. **Add NAT gateways.** `spec.enableNatGateway` exists in the XRD and does nothing.
   Implement it: when true, create an Elastic IP and a NAT Gateway **in a public
   subnet**, a private route table per AZ, a `0.0.0.0/0` route to the NAT gateway, and
   associations for the private subnets.

   Then answer: should there be one NAT gateway or one per AZ? Give the availability
   argument *and* the cost argument, and say which you'd pick for a startup and for a
   bank.

2. **Fix the CIDR allocation problem.** `netIndex` is a footgun — two developers
   picking index 1 create overlapping networks that can never be peered, and nothing
   stops them. Design a better mechanism and implement it.

   (Hints: `function-extra-resources` can read existing `XNetwork` objects during
   rendering; an admission policy could reject duplicates; a central allocation
   registry could hand out indexes. Each has real drawbacks — pick one, implement it,
   and be explicit about what it doesn't solve.)

3. **Make the network importable.** Your company already has a production VPC built
   by Terraform. Write an `XNetwork` that **adopts** it rather than creating a new
   one, using what you learned in Module 03. Explain what `managementPolicies` you'd
   start with and what specifically could go wrong if you skipped straight to `["*"]`.

4. **Diagnose a broken network.** Apply [`solutions/broken-network.yaml`](./solutions/broken-network.yaml)
   (read it only *after* you've diagnosed it). It creates a VPC where an EC2 instance
   in the "public" subnet cannot reach the internet. Find the fault using only
   `kubectl`, `crossplane trace`, and `awslocal`. Write down your diagnostic steps in
   order — the process matters more than the answer.

5. **Stretch — VPC peering.** Create two `XNetwork`s with different `netIndex` values
   and peer them: a `VPCPeeringConnection` plus routes on both sides. Then explain why
   a full mesh of peered VPCs doesn't scale, and what AWS offers instead.

## Success criteria
- [ ] `enableNatGateway: true` produces a working NAT path for private subnets, and
      you argued the one-vs-per-AZ trade-off with both availability and cost.
- [ ] You implemented a CIDR allocation mechanism better than `netIndex` and stated
      its remaining weakness.
- [ ] An `XNetwork` adopts a pre-existing VPC without recreating it.
- [ ] You diagnosed the broken network and recorded your steps in order.
- [ ] You can explain, from memory, the three resources that must agree for a subnet
      to be public.
