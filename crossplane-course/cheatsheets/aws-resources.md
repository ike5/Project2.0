# AWS Managed Resources Cheatsheet

Every AWS resource used in this course, with the fields that matter and the gotchas
that will bite you.

**Provider family:** `xpkg.upbound.io/upbound/provider-aws-*`. Install only the
service packages you need — `provider-aws-s3`, not the whole of AWS.

---

## Finding fields for any resource

The provider's CRDs are the authoritative reference and they're already in your
cluster:

```bash
kubectl explain bucket.spec.forProvider
kubectl explain instance.spec.forProvider.engine
kubectl get crd buckets.s3.aws.upbound.io -o yaml | less
```

Naming pattern: `<service>.aws.upbound.io/v1beta1`, e.g. `s3.aws.upbound.io`,
`ec2.aws.upbound.io`, `rds.aws.upbound.io`, `iam.aws.upbound.io`.

---

## The universal shape

Every AWS managed resource looks like this:

```yaml
apiVersion: <service>.aws.upbound.io/v1beta1
kind: <Kind>
metadata:
  name: my-resource                        # the Kubernetes name
  annotations:
    crossplane.io/external-name: real-name # the AWS name/ID (see below)
spec:
  forProvider:
    region: us-east-1                      # required on nearly everything
    # ...service-specific fields
  providerConfigRef:
    name: default
  deletionPolicy: Delete                   # or Orphan
  managementPolicies: ["*"]                # or a subset
  writeConnectionSecretToRef:              # where credentials land
    namespace: default
    name: my-conn
```

> **`crossplane.io/external-name` is the most important annotation in Crossplane.**
> If unset, Crossplane creates a resource and writes the resulting name/ID back into
> it. If you set it yourself, Crossplane *looks for that resource* instead of
> creating one — which is exactly how you import existing infrastructure.

---

## Referencing one resource from another

Three ways, in order of preference:

```yaml
# 1. By Kubernetes object name — the resolver fills in the AWS ID for you
subnetIdRef:
  name: my-subnet

# 2. By label selector — resolves to a matching resource
subnetIdSelector:
  matchLabels:
    network: private

# 3. By literal AWS ID — only for resources Crossplane doesn't manage
subnetId: subnet-0abc123def456
```

The `...Ref`/`...Selector` forms are what make compositions composable: you don't
know the VPC's ID at authoring time, so you reference the *object* and let Crossplane
resolve it once it exists.

---

## S3

```yaml
apiVersion: s3.aws.upbound.io/v1beta1
kind: Bucket
metadata:
  name: my-app-data
spec:
  forProvider:
    region: us-east-1
```

Related resources — S3 configuration is split across many objects:

| Kind | Purpose |
|------|---------|
| `Bucket` | The bucket itself |
| `BucketVersioning` | Enable versioning |
| `BucketServerSideEncryptionConfiguration` | Encryption at rest |
| `BucketPublicAccessBlock` | Block public access (**always set this**) |
| `BucketPolicy` | Resource policy JSON |
| `BucketLifecycleConfiguration` | Expiry/transition rules |
| `BucketOwnershipControls` | ACL behaviour |

> **Gotchas**
> - Bucket names are **globally unique across all of AWS**. Always append a suffix in
>   compositions. LocalStack doesn't enforce this — real AWS does, loudly.
> - A non-empty bucket **refuses to delete**. Expect stuck finalizers if you wrote
>   objects into it.
> - `BucketVersioning` and friends reference the bucket via `bucketRef.name`.

---

## EC2 / VPC networking

```yaml
apiVersion: ec2.aws.upbound.io/v1beta1
kind: VPC
spec:
  forProvider:
    region: us-east-1
    cidrBlock: 10.0.0.0/16
    enableDnsSupport: true
    enableDnsHostnames: true        # required for RDS DNS names to resolve
```

| Kind | Key fields | Notes |
|------|-----------|-------|
| `VPC` | `cidrBlock`, `enableDnsHostnames` | The root of everything |
| `Subnet` | `cidrBlock`, `availabilityZone`, `vpcIdRef` | One AZ each; needs ≥2 for RDS |
| `InternetGateway` | `vpcIdRef` | Public internet access |
| `RouteTable` | `vpcIdRef` | |
| `Route` | `routeTableIdRef`, `destinationCidrBlock`, `gatewayIdRef` | `0.0.0.0/0` → IGW = public |
| `RouteTableAssociation` | `subnetIdRef`, `routeTableIdRef` | Ties a subnet to a table |
| `SecurityGroup` | `vpcIdRef`, `name`, `description` | `description` is **required** by AWS |
| `SecurityGroupRule` | `type`, `fromPort`, `toPort`, `protocol`, `securityGroupIdRef` | `type` is `ingress`/`egress` |
| `NATGateway` | `subnetIdRef`, `allocationIdRef` | Costs real money on real AWS |

> **Gotchas**
> - A subnet is **public** only if its route table has a `0.0.0.0/0` route to an IGW
>   *and* a `RouteTableAssociation` links them. Forgetting the association is the
>   classic silent failure.
> - `SecurityGroup.spec.forProvider.description` is mandatory; AWS rejects an empty one.
> - Availability zones are region-specific. `us-east-1a` doesn't exist in `eu-west-1`.
> - Deleting a VPC with anything inside fails with `DependencyViolation`. Use `Usage`
>   objects (Module 10) to order the teardown.

---

## IAM

```yaml
apiVersion: iam.aws.upbound.io/v1beta1
kind: Role
spec:
  forProvider:
    assumeRolePolicy: |          # WHO may assume this role
      {
        "Version": "2012-10-17",
        "Statement": [{
          "Effect": "Allow",
          "Principal": {"Service": "ec2.amazonaws.com"},
          "Action": "sts:AssumeRole"
        }]
      }
```

| Kind | Purpose |
|------|---------|
| `Role` | An assumable identity |
| `Policy` | A standalone permission document |
| `RolePolicyAttachment` | Attaches a `Policy` to a `Role` |
| `User`, `AccessKey` | Long-lived identities — **avoid**; prefer roles |
| `OpenIDConnectProvider` | The trust anchor for IRSA |
| `InstanceProfile` | Wraps a role for EC2 instances |

> **Gotchas**
> - Two different policy fields do two different jobs. `assumeRolePolicy` on a `Role`
>   says **who can become it**. A `Policy` attached via `RolePolicyAttachment` says
>   **what it can do**. Mixing them up is the most common IAM error in Crossplane.
> - Policy documents are **JSON strings**, not YAML objects. Use a YAML block scalar
>   (`|`) and keep valid JSON inside.
> - IAM is eventually consistent. A role can exist but not yet be usable for a few
>   seconds — expect brief `Ready=False` flapping on first creation.
> - LocalStack accepts nearly any policy without evaluating it. **Real AWS enforces
>   them.** Don't assume a policy is correct because a lab passed.

---

## RDS

```yaml
apiVersion: rds.aws.upbound.io/v1beta1
kind: Instance
spec:
  forProvider:
    region: us-east-1
    engine: postgres
    engineVersion: "16.3"
    instanceClass: db.t3.micro
    allocatedStorage: 20
    username: postgres
    autoGeneratePassword: true               # never hardcode a password
    passwordSecretRef:
      namespace: crossplane-system
      name: db-password
      key: password
    dbSubnetGroupNameRef:
      name: my-subnet-group
    vpcSecurityGroupIdRefs:
      - name: my-db-sg
    skipFinalSnapshot: true                  # false in production!
    publiclyAccessible: false
  writeConnectionSecretToRef:
    namespace: default
    name: db-conn
```

| Kind | Purpose |
|------|---------|
| `Instance` | A database instance |
| `SubnetGroup` | The subnets RDS may place it in (**needs ≥2 AZs**) |
| `ParameterGroup` | Engine tuning |
| `Cluster` | Aurora clusters |

**Connection secret keys** written by `Instance`:
`endpoint`, `port`, `username`, `password`, `attribute.address`.

> **Gotchas**
> - `SubnetGroup` requires subnets in **at least two availability zones**, even for a
>   single-AZ instance. This is the #1 RDS composition failure.
> - Real RDS takes **5–15 minutes** to become available. Don't assume your composition
>   is broken because `Ready=False` after two minutes. LocalStack fakes it instantly,
>   which is convenient but sets a false expectation.
> - `skipFinalSnapshot: true` is fine for labs and dangerous in production — it means
>   deletion destroys the data with no backup.
> - Never put a password in `forProvider`. Use `autoGeneratePassword` +
>   `passwordSecretRef`, so the value exists only in a Secret.

---

## DynamoDB

```yaml
apiVersion: dynamodb.aws.upbound.io/v1beta1
kind: Table
spec:
  forProvider:
    region: us-east-1
    billingMode: PAY_PER_REQUEST      # no capacity planning
    hashKey: id
    attribute:
      - name: id
        type: S                       # S | N | B
```

> **Gotcha:** you only declare attributes used as keys or index keys — not every
> field you plan to store. Declaring extra ones is an error.

---

## Provider authentication, four ways

| Source | Use when | Security |
|--------|----------|----------|
| `Secret` | Local dev, LocalStack | ⚠️ Static long-lived keys |
| `IRSA` | Crossplane runs on EKS | ✅ Best on EKS — no stored keys |
| `WebIdentity` | Any OIDC-capable cluster | ✅ No stored keys |
| `Upbound` / `InjectedIdentity` | Managed control planes / node role | ✅ Depends on setup |

```yaml
# Local dev (this course)
spec:
  credentials:
    source: Secret
    secretRef: { namespace: crossplane-system, name: aws-creds, key: creds }

# Production on EKS
spec:
  credentials:
    source: IRSA
```

Cross-account access — one ProviderConfig per target account:
```yaml
spec:
  assumeRoleChain:
    - roleARN: arn:aws:iam::222222222222:role/CrossplaneProvisioner
  credentials:
    source: IRSA
```

---

## The LocalStack ProviderConfig (this course)

```yaml
apiVersion: aws.upbound.io/v1beta1
kind: ProviderConfig
metadata:
  name: default
spec:
  credentials:
    source: Secret
    secretRef: { namespace: crossplane-system, name: aws-creds, key: creds }
  endpoint:
    hostnameImmutable: true
    url:
      type: Static
      static: http://localstack.localstack.svc.cluster.local:4566
  skip_credentials_validation: true
  skip_metadata_api_check: true
  skip_requesting_account_id: true
  skip_region_validation: true
  s3_use_path_style: true
```

**To switch to real AWS:** delete the `endpoint` block and every `skip_*` field,
change `credentials.source` to `IRSA`, and put real credentials behind it. Nothing
else in any manifest changes. That's the whole point.

---

## Where LocalStack differs from real AWS

Know these so you don't learn the wrong lesson:

| Behaviour | LocalStack | Real AWS |
|-----------|-----------|----------|
| IAM policy enforcement | Mostly ignored | Strictly enforced |
| S3 global name uniqueness | Not enforced | Enforced |
| RDS provisioning time | Instant | 5–15 minutes |
| Eventual consistency | Rare | Common — expect retries |
| Service quotas | None | Real, and you will hit them |
| Cost | $0 | Not $0 — NAT Gateways especially |

Everything the course teaches transfers. These are the places to double-check before
running a composition against a real account for the first time.
