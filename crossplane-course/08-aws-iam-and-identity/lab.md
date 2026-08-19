# Lab 08 — Least Privilege, Generated

**You'll:** build the two-policy structure by hand, generate scoped policies from a
composition, read a complete IRSA setup, and audit a dangerous policy.
⏱️ ~80 min.

> Prereqs: Modules 06–07.
>
> ⚠️ **The emulator does not evaluate IAM policies.** Everything here will apply
> cleanly whether your policy is correct or catastrophic. That's why Part F is about
> *auditing* rather than testing, and why §8 of the README matters.

---

## Part A — Add the IAM provider

```bash
cd 08-aws-iam-and-identity
kubectl apply -f - <<'YAML'
apiVersion: pkg.crossplane.io/v1
kind: Provider
metadata:
  name: provider-aws-iam
spec:
  package: xpkg.upbound.io/upbound/provider-aws-iam:v1.21.0
---
apiVersion: apiextensions.crossplane.io/v1alpha1
kind: ManagedResourceActivationPolicy
metadata:
  name: course-resources
spec:
  activate:
    - "*.s3.aws.upbound.io"
    - "*.ec2.aws.upbound.io"
    - "*.rds.aws.upbound.io"
    - "*.iam.aws.upbound.io"
YAML
kubectl wait provider/provider-aws-iam --for=condition=Healthy --timeout=10m
```
✅ Expected: `provider.pkg.crossplane.io/provider-aws-iam condition met`.

## Part B — The two-policy structure

```bash
cat manifests/role-basic.yaml
kubectl apply -f manifests/role-basic.yaml
sleep 20
kubectl get roles.iam.aws.upbound.io,policies.iam.aws.upbound.io,rolepolicyattachments.iam.aws.upbound.io
```
✅ Expected: three resources, all `SYNCED=True READY=True`.

Read the trust policy — **who may become this role**:
```bash
awslocal iam get-role --role-name report-generator \
  --query 'Role.AssumeRolePolicyDocument'
```
✅ Expected: a document naming `ec2.amazonaws.com` as the principal. Note it says
**nothing** about S3.

Now the permission policy — **what the role may do**:
```bash
awslocal iam list-attached-role-policies --role-name report-generator
```
✅ Expected: `report-read-policy` attached.

**Prove the attachment matters.** Delete just the join:
```bash
kubectl delete rolepolicyattachment report-generator-read
sleep 15
awslocal iam list-attached-role-policies --role-name report-generator
```
✅ Expected: an empty list. The role still exists. The policy still exists. They are
now completely unrelated, and anything assuming this role can do nothing.

```bash
kubectl apply -f manifests/role-basic.yaml
```

> **Three objects, all required.** A role with no attached policy is a common and
> silent misconfiguration — the role looks fine in the console.

## Part C — Generate least privilege from a composition

```bash
kubectl apply -f manifests/xrd.yaml
kubectl apply -f manifests/composition.yaml
cat manifests/xr-identity.yaml
kubectl apply -f manifests/xr-identity.yaml
sleep 45
kubectl get xappidentities -n team-payments
```
✅ Expected: `READY=True`, with a role ARN in the `ROLE` column.

Look at the policy the composition generated:
```bash
awslocal iam list-policies --scope Local --query 'Policies[].PolicyName'
POLICY_ARN=$(awslocal iam list-policies --scope Local \
  --query 'Policies[?PolicyName==`team-payments-payments-identity-access`].Arn' --output text)
VERSION=$(awslocal iam get-policy --policy-arn "$POLICY_ARN" \
  --query 'Policy.DefaultVersionId' --output text)
awslocal iam get-policy-version --policy-arn "$POLICY_ARN" --version-id "$VERSION" \
  --query 'PolicyVersion.Document'
```
✅ Expected: **six statements** — two per bucket (objects and list) plus one for
DynamoDB:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {"Sid":"Objectsteampaymentspaymentsdata","Effect":"Allow",
     "Action":["s3:GetObject","s3:PutObject","s3:DeleteObject"],
     "Resource":"arn:aws:s3:::team-payments-payments-data/*"},
    {"Sid":"Listteampaymentspaymentsdata","Effect":"Allow",
     "Action":["s3:ListBucket"],
     "Resource":"arn:aws:s3:::team-payments-payments-data"},
    {"Sid":"Objectssharedreferencedata","Effect":"Allow",
     "Action":["s3:GetObject"],
     "Resource":"arn:aws:s3:::shared-reference-data/*"},
    ...
  ]
}
```

**Notice three things the developer got for free:**
1. The **two-statement structure** — object actions on `bucket/*`, `ListBucket` on
   `bucket`. Nearly everyone gets this wrong by hand.
2. `access: read` produced only `GetObject`; `readwrite` added `PutObject` and
   `DeleteObject`. No way to accidentally request more.
3. Resources are pinned to **named buckets**, never `*`.

> This is the argument for platform APIs, stated as precisely as it can be:
> hand-writing this is tedious, so people write `s3:*` instead. A composition makes
> the correct thing the *default* thing.

## Part D — The Kubernetes half of IRSA

```bash
kubectl get sa payments -n team-payments -o yaml | grep -A3 annotations
```
✅ Expected: the ServiceAccount carries the role ARN:
```yaml
annotations:
  eks.amazonaws.com/role-arn: arn:aws:iam::123456789012:role/team-payments-payments-identity
```

On a real EKS cluster, the pod identity webhook sees that annotation and injects a
projected token plus `AWS_ROLE_ARN` and `AWS_WEB_IDENTITY_TOKEN_FILE` into every pod
using this ServiceAccount. The AWS SDK finds them automatically. **The application
needs no code changes and holds no credentials.**

Now inspect the trust policy the composition wrote:
```bash
awslocal iam get-role --role-name team-payments-payments-identity \
  --query 'Role.AssumeRolePolicyDocument' | jq '.Statement[0].Condition'
```
✅ Expected:
```json
{
  "StringEquals": {
    "oidc.eks...:sub": "system:serviceaccount:team-payments:payments",
    "oidc.eks...:aud": "sts.amazonaws.com"
  }
}
```

**That `sub` condition is the entire security model.** It pins the role to exactly one
ServiceAccount in exactly one namespace. Remove it and any pod in the cluster —
including one in another team's namespace — could assume this role.

## Part E — Read the full IRSA setup

```bash
cat manifests/irsa.yaml
```

You can't apply this (kind has no AWS-registered OIDC issuer), but read all five
pieces and make sure you can say what each does:

1. **`OpenIDConnectProvider`** — tells AWS to trust your cluster's token issuer.
2. **`Role`** — trusts that issuer, for one ServiceAccount, with a permissions
   boundary capping what it can ever do.
3. **`Policy` + attachment** — what the provider may manage. Note the explicit
   `Deny` on IAM escalation actions.
4. **`DeploymentRuntimeConfig`** — pins the provider pod's ServiceAccount **name**, so
   it matches the `sub` claim in the trust policy. **These two strings must agree
   exactly or STS silently refuses.**
5. **`ProviderConfig` with `source: IRSA`** — no `secretRef`, because no secret exists.

Then compare your course config with the production one:
```bash
diff <(grep -v '^\s*#' ../02-providers-and-managed-resources/manifests/providerconfig.yaml | grep -v '^$') \
     <(sed -n '/name: production$/,/source: IRSA/p' manifests/providerconfig-real-aws.yaml)
```
The difference is the `endpoint` block, four `skip_*` fields, and the credential
source. **Nothing else in this entire course changes when you go to real AWS.**

## Part F — Audit a dangerous policy

```bash
cat manifests/bad-policy.yaml
kubectl apply -f manifests/bad-policy.yaml
sleep 15
kubectl get policy dangerous-policy
```
✅ Expected: `SYNCED=True READY=True`. **The emulator accepted it without complaint.**

Find the three faults yourself before reading on:
```bash
BAD=$(awslocal iam list-policies --scope Local \
  --query 'Policies[?PolicyName==`dangerous-policy`].Arn' --output text)
V=$(awslocal iam get-policy --policy-arn "$BAD" --query 'Policy.DefaultVersionId' --output text)
awslocal iam get-policy-version --policy-arn "$BAD" --version-id "$V" \
  --query 'PolicyVersion.Document' | jq
```

<details>
<summary>The three faults</summary>

1. **`"Action": "*", "Resource": "*"`** — this is `AdministratorAccess`. It can delete
   the account's resources, including the control plane managing them.
2. **`iam:CreatePolicyVersion` + `iam:AttachRolePolicy` on `*`** — a **privilege
   escalation path**. Even without statement 1, this role could write itself a new
   policy granting anything and attach it. Any policy allowing an identity to modify
   IAM is effectively an administrator policy.
3. **`s3:ListBucket` on `arn:aws:s3:::my-bucket/*`** — silently grants **nothing**.
   `ListBucket` acts on the bucket, not its objects. The app can fetch a key it
   already knows and cannot list anything, and no error explains why.
</details>

**Catch these automatically.** On a real account:
```bash
aws accessanalyzer validate-policy \
  --policy-document file://policy.json --policy-type IDENTITY_POLICY
```
It flags over-broad permissions and mismatched resource ARNs. It's free, runs offline,
and belongs in CI — Module 14 wires it in.

```bash
kubectl delete -f manifests/bad-policy.yaml
```

## Part G — Clean up

```bash
kubectl delete xappidentity --all -n team-payments
kubectl delete -f manifests/role-basic.yaml
sleep 30
kubectl get managed
```

**Leave the IAM provider and the `XAppIdentity` XRD installed** — the capstone uses
them.

---

## What you learned
- A **trust policy** says who may assume a role; a **permission policy** says what it
  may do. They are different objects joined by a `RolePolicyAttachment`.
- S3 needs **two statements**: object actions on `bucket/*`, `ListBucket` on `bucket`.
- Compositions make least privilege practical by generating the correct narrow policy
  automatically.
- **IRSA** gives pods short-lived, auto-rotating credentials with no stored key. The
  `sub` **condition** in the trust policy is what makes it per-workload.
- Going to real AWS changes **one object**: the `ProviderConfig`.
- The emulator accepts any policy, so audit with `validate-policy` and
  `simulate-principal-policy` against a real account.

➡️ **[challenge.md](./challenge.md)** then [Module 09](../09-aws-data-services/).
