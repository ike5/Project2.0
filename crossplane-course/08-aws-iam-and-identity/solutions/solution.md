# Challenge 08 — Reference Solution

Runnable manifests: [`boundary.yaml`](./boundary.yaml),
[`xappidentity-irsa.yaml`](./xappidentity-irsa.yaml),
[`policy-lint.sh`](./policy-lint.sh).

---

### 1. The permissions boundary

The boundary policy — note it is an **allow-list ceiling**, not a grant:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "MaxAllowedServices",
      "Effect": "Allow",
      "Action": ["s3:*", "dynamodb:*", "sqs:*", "logs:*"],
      "Resource": "*"
    },
    {
      "Sid": "NeverIam",
      "Effect": "Deny",
      "Action": ["iam:*", "organizations:*", "account:*"],
      "Resource": "*"
    },
    {
      "Sid": "NeverEscapeTheBoundary",
      "Effect": "Deny",
      "Action": ["iam:DeleteRolePermissionsBoundary", "iam:PutRolePermissionsBoundary"],
      "Resource": "*"
    }
  ]
}
```

Applied in the composition:
```gotemplate
spec:
  forProvider:
    permissionsBoundary: arn:aws:iam::{{ $accountId }}:policy/AppIdentityBoundary
    assumeRolePolicy: | ...
```

**Effective permissions = attached policies ∩ boundary.** The boundary grants nothing
by itself; it caps.

**What a developer could do before, and can't after:**

Before: the composition's policy generator takes `spec.buckets[].name` as an arbitrary
string. A developer could write:
```yaml
spec:
  serviceAccountName: innocent
  buckets:
    - name: "*"                      # every bucket in the account
      access: readwrite
```
producing `"Resource": "arn:aws:s3:::*/*"` — read/write/delete on **every bucket in
the account**, including other teams' data and the Terraform state bucket.

After: the boundary still allows `s3:*`, so this specific attack isn't fully blocked
by the boundary alone — which is the honest answer, and the reason the *complete* fix
is two changes:

1. **The boundary** stops the worse case: a developer can never obtain `iam:*`, so
   they cannot escalate beyond their bucket access into account takeover.
2. **Schema validation** stops the wildcard:
   ```yaml
   name:
     type: string
     pattern: '^[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]$'
   ```
   plus a CEL rule pinning bucket names to the requesting namespace's prefix:
   ```yaml
   x-kubernetes-validations:
     - rule: "self.buckets.all(b, b.name.startsWith('acme-'))"
       message: "bucket names must start with acme-"
   ```

> **The general lesson:** a boundary limits *blast radius*, and input validation
> limits *reach*. You need both. A boundary alone still lets someone do the worst
> thing the boundary permits.

### 2. Cross-account provisioning

One ProviderConfig per target account:
```yaml
apiVersion: aws.upbound.io/v1beta1
kind: ProviderConfig
metadata: { name: account-prod }
spec:
  credentials: { source: IRSA }
  assumeRoleChain:
    - roleARN: arn:aws:iam::333333333333:role/CrossplaneProvisioner
      externalID: prod-external-id
---
apiVersion: aws.upbound.io/v1beta1
kind: ProviderConfig
metadata: { name: account-dev }
spec:
  credentials: { source: IRSA }
  assumeRoleChain:
    - roleARN: arn:aws:iam::111111111111:role/CrossplaneProvisioner
```

In the composition:
```gotemplate
{{- $account := $xr.spec.account | default "dev" -}}
providerConfigRef:
  name: {{ printf "account-%s" $account }}
```

**What stops a dev-namespace developer targeting prod?** Not the composition — a
developer can set `account: prod` in their YAML. Three layers actually stop them:

1. **The XRD schema doesn't decide it; a policy does.** A `ValidatingAdmissionPolicy`
   binding namespace to account:
   ```yaml
   validations:
     - expression: |
         (object.metadata.namespace.startsWith('prod-') && object.spec.account == 'prod') ||
         (!object.metadata.namespace.startsWith('prod-') && object.spec.account != 'prod')
       message: "only prod-* namespaces may target the prod account"
   ```
2. **AWS-side trust.** `CrossplaneProvisioner` in account 333 trusts only the control
   plane's role — and if dev and prod run on **separate control planes**, a dev
   cluster physically cannot assume it. This is the strongest control, because it does
   not depend on your cluster's configuration being correct.
3. **RBAC on ProviderConfigs.** Developers shouldn't be able to read or reference
   arbitrary ProviderConfigs. Module 13 covers this.

**The strongest answer is (2): separate control planes per environment.** Everything
enforced inside one cluster is one misconfiguration away from failing. An IAM trust
relationship that simply doesn't include your dev cluster fails safe.

### 3. The `iam:PassRole` escalation path

**Your colleague is wrong, and the escalation is complete account takeover.**

The path:
1. `ec2:RunInstances` lets them launch an EC2 instance.
2. `iam:PassRole` on `*` lets them attach **any role in the account** to that instance
   — including one with `AdministratorAccess`.
3. They launch an instance with that admin role and a user-data script.
4. The instance boots, the script queries the instance metadata service, receives
   admin credentials, and does whatever it likes.

They never needed permission to do any of it directly. `PassRole` on `*` is
equivalent to "assume any role in the account", and it is one of the most commonly
overlooked escalation paths in AWS.

**The corrected version** — constrain which roles may be passed, and to which service:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "LaunchInstances",
      "Effect": "Allow",
      "Action": ["ec2:RunInstances"],
      "Resource": "*"
    },
    {
      "Sid": "PassOnlyTheAppRole",
      "Effect": "Allow",
      "Action": ["iam:PassRole"],
      "Resource": "arn:aws:iam::123456789012:role/app-instance-role",
      "Condition": {
        "StringEquals": { "iam:PassedToService": "ec2.amazonaws.com" }
      }
    }
  ]
}
```

Two constraints, both necessary: the `Resource` pins *which* role, and
`iam:PassedToService` pins *what* it may be passed to. Without the condition, the
role could be passed to Lambda, CodeBuild, or anything else that accepts one.

**The general rule: `iam:PassRole` must always name specific role ARNs.** Treat
`PassRole` on `*` as equivalent to `AdministratorAccess` in any review.

### 4. Migrating off IAM users

See [`xappidentity-irsa.yaml`](./xappidentity-irsa.yaml). The composition drops
`User`, `UserPolicy`, and `AccessKey`, and produces a `Role` plus an annotated
`ServiceAccount` instead. The Deployment loses its `AWS_ACCESS_KEY_ID` and
`AWS_SECRET_ACCESS_KEY` env vars entirely and gains `serviceAccountName`.

**The no-downtime migration order:**

1. **Create the role alongside the existing user.** Both work; nothing changes yet.
2. **Attach the same permissions** to the new role that the user has. Verify with
   `simulate-principal-policy` that the role can do everything the user can.
3. **Annotate the ServiceAccount** and set `serviceAccountName` on the Deployment,
   **but leave the static key env vars in place.**
   > At this point both credential sources are present. **The AWS SDK credential chain
   > prefers explicit environment variables over web identity**, so the app is still
   > using the old key. This is deliberate: it means the rollout itself is a no-op and
   > cannot break anything.
4. **Remove the env vars** and roll the Deployment. Now the SDK falls through to the
   web identity token. This is the only step that changes behaviour, and it's a
   normal rolling update — roll back by re-adding the env vars.
5. **Verify the old key is genuinely unused** before deleting it. This is the step
   people skip:
   ```bash
   aws iam get-access-key-last-used --access-key-id AKIA...
   ```
   Check `LastUsedDate`. **Wait at least as long as your longest infrequent job** —
   if a monthly billing batch uses that key, a week of silence proves nothing. For
   anything important, wait a full cycle plus margin.
   Cross-check in CloudTrail:
   ```bash
   aws cloudtrail lookup-events \
     --lookup-attributes AttributeKey=AccessKeyId,AttributeValue=AKIA... \
     --start-time 2026-01-01
   ```
6. **Deactivate before deleting.** `aws iam update-access-key --status Inactive` is
   instantly reversible; deletion is not. Leave it inactive for a week — if something
   breaks, reactivating takes seconds.
7. **Delete the key and the user.**

**The principle:** every step before 4 is additive and reversible, step 4 is a normal
rollback-able deploy, and steps 5–6 make the irreversible step safe. Migrations fail
when someone deletes the old thing before proving it was unused.

### 5. Stretch — policy linting in CI

See [`policy-lint.sh`](./policy-lint.sh). It renders each composition, extracts every
`assumeRolePolicy` and `policy` field, parses them as JSON, and checks:

- `"Action": "*"` anywhere with `Effect: Allow`
- `"Resource": "*"` with `Effect: Allow` on a sensitive service prefix
- `iam:PassRole` without a `Condition` or with `Resource: "*"`
- `s3:ListBucket` paired with a `/*` resource ARN (the silent no-op)
- Any `iam:*` action in an Allow statement

```
▶ team-payments-payments-identity-access                   ✅
▶ dangerous-policy
    ✗ statement 0: Action "*" with Effect Allow
    ✗ statement 1: iam:* actions in an Allow statement
    ✗ statement 2: s3:ListBucket on an object ARN (grants nothing)
2 policies checked, 1 failed
```

Running it on rendered output rather than on the composition source matters: the
policy is *generated*, so bugs live in the template logic and only appear after
rendering. Pair it with `aws accessanalyzer validate-policy` in a job that has AWS
credentials — that catches AWS-specific grammar this script can't know about.
