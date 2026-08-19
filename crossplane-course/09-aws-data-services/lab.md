# Lab 09 — Databases and the Credentials Nobody Sees

**You'll:** provision Postgres in a private network, curate a connection secret that
becomes your platform's contract, watch a data-destroying change get rejected, and
compare with DynamoDB. ⏱️ ~80 min.

> Prereqs: Modules 06–08. Module 07's `XNetwork` XRD and composition installed.

---

## Part A — Add the DynamoDB provider

RDS is already installed from Module 06. Add DynamoDB for Part G:

```bash
cd 09-aws-data-services
kubectl apply -f - <<'YAML'
apiVersion: pkg.crossplane.io/v1
kind: Provider
metadata:
  name: provider-aws-dynamodb
spec:
  package: xpkg.upbound.io/upbound/provider-aws-dynamodb:v1.21.0
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
    - "*.dynamodb.aws.upbound.io"
YAML
kubectl wait provider/provider-aws-dynamodb --for=condition=Healthy --timeout=10m
```

## Part B — Build the network the database will live in

```bash
kubectl create ns team-payments 2>/dev/null || true
kubectl apply -f ../07-aws-networking/manifests/xrd.yaml
kubectl apply -f ../07-aws-networking/manifests/composition.yaml
kubectl apply -f ../07-aws-networking/manifests/xr-network.yaml
kubectl wait xnetwork/payments-net -n team-payments --for=condition=Ready --timeout=5m
```
✅ Expected: the network becomes `Ready`.

Label the private subnets so the database's subnet group can find them:
```bash
kubectl label subnet -l tier=private network=payments-net --overwrite
kubectl get subnets -l tier=private --show-labels | head
```
✅ Expected: two private subnets, in **two different AZs**.

> In a full platform the composition would apply this label itself. It's manual here
> so you can see exactly which selector the subnet group uses.

## Part C — The hard way, and the two-AZ rule

```bash
kubectl apply -f manifests/raw-rds.yaml
sleep 45
kubectl get subnetgroup,instance.rds.aws.upbound.io
```
✅ Expected: both `SYNCED=True READY=True`.

Confirm the subnet group really spans two AZs:
```bash
awslocal rds describe-db-subnet-groups \
  --query 'DBSubnetGroups[0].Subnets[].SubnetAvailabilityZone.Name'
```
✅ Expected: two **different** zones.

**Now break it deliberately** — the single most common RDS composition failure:
```bash
kubectl apply -f - <<'YAML'
apiVersion: rds.aws.upbound.io/v1beta1
kind: SubnetGroup
metadata:
  name: one-az-group
spec:
  forProvider:
    region: us-east-1
    description: Deliberately broken - only one availability zone
    subnetIdSelector:
      matchLabels:
        tier: private
        az: us-east-1a
  providerConfigRef: { name: default }
YAML
sleep 25
kubectl get subnetgroup one-az-group \
  -o jsonpath='{.status.conditions[?(@.type=="Synced")].message}'; echo
```
✅ Expected: an error about needing subnets in at least two availability zones.

**On real AWS this is a hard failure**, and the error appears only when you try to
create the *database*, not the subnet group — which is why it's so confusing. Remember
the shape of it.

```bash
kubectl delete subnetgroup one-az-group
```

## Part D — The password nobody typed

```bash
kubectl get secret raw-postgres-password -n crossplane-system -o jsonpath='{.data}' | jq 'keys'
```
✅ Expected: `["password"]`. The provider generated it.

Look at the connection secret it produced:
```bash
kubectl get secret raw-postgres-conn -n team-payments -o jsonpath='{.data}' | jq 'keys'
```
✅ Expected:
```json
["attribute.address", "endpoint", "password", "port", "username"]
```

**Those key names come from the provider, not from you.** If every app in your company
consumes `endpoint`, you've coupled all of them to the RDS provider's vocabulary. Part
E fixes that.

```bash
kubectl delete -f manifests/raw-rds.yaml
```

## Part E — The good way, with a curated contract

```bash
kubectl apply -f manifests/xrd.yaml
kubectl apply -f manifests/composition.yaml
kubectl apply -f manifests/xr-database.yaml
kubectl get xdatabases -n team-payments -w      # Ctrl-C when READY is True
```
✅ Expected:
```
NAME          ENGINE     SIZE    ENV   HOST                         READY
payments-db   postgres   small   dev   payments-db.xxxx.rds.ama...  True
```

Now compare the two secrets side by side:
```bash
echo "--- Level 1: what RDS wrote (provider's names) ---"
kubectl get secret payments-db-rds-conn -n team-payments -o jsonpath='{.data}' | jq 'keys'

echo "--- Level 2: what YOUR PLATFORM publishes ---"
kubectl get secret payments-db-conn -n team-payments -o jsonpath='{.data}' | jq 'keys'
```
✅ Expected:
```
--- Level 1 ---
["attribute.address","endpoint","password","port","username"]
--- Level 2 ---
["DATABASE_HOST","DATABASE_PASSWORD","DATABASE_PORT","DATABASE_SSLMODE","DATABASE_USER"]
```

**Level 2 is your API contract.** Note it includes `DATABASE_SSLMODE=require`, which no
managed resource produced — it came from `FromValue`. You can add platform-wide
defaults that the underlying service knows nothing about.

## Part F — Consume it

```bash
kubectl apply -f manifests/consumer.yaml
sleep 20
kubectl logs -n team-payments deploy/payments-consumer --tail=5
```
✅ Expected:
```
connecting to payments-db.xxxx.rds.amazonaws.com:5432 as appuser
password length: 20
```

**The full chain, with no human in it:** the provider generated a password → wrote it
to a Secret → the composition republished it under your platform's key names → the
kubelet mounted it into the Pod. Nobody saw the value at any point.

Prove the app is decoupled from the implementation:
```bash
kubectl get deploy payments-consumer -n team-payments \
  -o jsonpath='{.spec.template.spec.containers[0].env[*].name}'; echo
```
✅ Expected: `DATABASE_HOST DATABASE_PORT DATABASE_USER DATABASE_PASSWORD` — not one
mention of RDS, AWS, or Postgres. **Swap the composition for Aurora or Cloud SQL and
this Deployment is unchanged.**

## Part G — Reject a change that would destroy the data

This is the most important part of the module.

```bash
kubectl patch xdatabase payments-db -n team-payments --type=merge \
  -p '{"spec":{"engine":"mysql"}}'
```
✅ Expected: **rejected immediately**:
```
The XDatabase "payments-db" is invalid: spec: Invalid value: "object":
engine is immutable: changing it would destroy all data
```

Without that rule, Crossplane would have accepted it, seen that `engine` cannot be
changed in place, and **deleted and recreated the database** — total data loss, within
about a minute, with no confirmation prompt.

Try shrinking storage:
```bash
kubectl patch xdatabase payments-db -n team-payments --type=merge \
  -p '{"spec":{"storageGB":10}}'
```
✅ Expected: rejected — `storageGB can only be increased`.

And an unsafe production configuration:
```bash
kubectl apply -f - <<'YAML'
apiVersion: platform.acme.io/v1alpha1
kind: XDatabase
metadata: { name: prod-tiny, namespace: team-payments }
spec:
  environment: prod
  size: small
  networkRef: payments-net
YAML
```
✅ Expected: rejected — `prod databases may not use the small size`.

Now confirm a **safe** change still works:
```bash
kubectl patch xdatabase payments-db -n team-payments --type=merge \
  -p '{"spec":{"storageGB":40}}'
sleep 30
kubectl get instance.rds.aws.upbound.io \
  -o custom-columns=NAME:.metadata.name,STORAGE:.spec.forProvider.allocatedStorage
```
✅ Expected: accepted, storage now 40. In-place, no replacement.

> **Encode "this would destroy data" as a schema rule.** It fails at `kubectl apply`
> with a message a human can act on, instead of succeeding and quietly doing the right
> thing according to a wrong declaration. This is the single highest-value use of
> `x-kubernetes-validations` in Crossplane.

## Part H — Production settings, for contrast

Render (don't apply) a prod database and compare:
```bash
sed 's/environment: dev/environment: prod/; s/size: small/size: medium/; s/name: payments-db/name: prod-db/' \
  manifests/xr-database.yaml > /tmp/prod-db.yaml
crossplane render /tmp/prod-db.yaml manifests/composition.yaml \
  ../06-composing-applications/manifests/render/functions.yaml \
  | grep -E 'deletionProtection|skipFinalSnapshot|multiAz|backupRetention|deletionPolicy'
```
✅ Expected:
```
      deletionProtection: true
      skipFinalSnapshot: false
      backupRetentionPeriod: 30
      multiAz: true
  deletionPolicy: Orphan
```

**One word — `prod` — turned on four independent protections.** The developer didn't
request any of them and cannot turn them off.

## Part I — DynamoDB, for contrast

```bash
kubectl apply -f - <<'YAML'
apiVersion: dynamodb.aws.upbound.io/v1beta1
kind: Table
metadata:
  name: payments-idempotency
spec:
  forProvider:
    region: us-east-1
    billingMode: PAY_PER_REQUEST
    hashKey: requestId
    attribute:
      - name: requestId
        type: S
  providerConfigRef: { name: default }
YAML
sleep 25
kubectl get table.dynamodb.aws.upbound.io
```
✅ Expected: `SYNCED=True READY=True`.

**No subnet group, no security group, no password, no connection secret.** Access is
entirely through IAM (Module 08), which is why `XAppIdentity` had a `dynamoTables`
field.

Now the classic mistake:
```bash
kubectl patch table.dynamodb.aws.upbound.io payments-idempotency --type=merge \
  -p '{"spec":{"forProvider":{"attribute":[{"name":"requestId","type":"S"},{"name":"payload","type":"S"}]}}}'
sleep 20
kubectl get table.dynamodb.aws.upbound.io payments-idempotency \
  -o jsonpath='{.status.conditions[?(@.type=="Synced")].message}'; echo
```
✅ Expected: an error. **DynamoDB is schemaless apart from its keys** — you declare
only attributes used as a hash key, range key, or index key. Declaring a data field is
an error.

```bash
kubectl delete table.dynamodb.aws.upbound.io payments-idempotency
```

## Part J — Clean up

```bash
kubectl delete -f manifests/consumer.yaml
kubectl delete xdatabase --all -n team-payments
sleep 60
kubectl delete xnetwork --all -n team-payments
sleep 120
kubectl get managed
```

**Leave the `XDatabase` XRD and composition installed** — the capstone uses them.

---

## What you learned
- RDS needs a **subnet group spanning ≥2 AZs**, even for a single-AZ instance.
- `autoGeneratePassword` means **no human ever knows the password**.
- Connection details flow at **two levels**: what the resource writes, and the curated
  contract your composition publishes. Applications must consume the second.
- `FromValue` lets you add platform-wide settings no cloud resource produced.
- **Encode destructive changes as immutability rules** in the XRD — a rejected apply
  beats a silent replacement.
- Production protection is three independent layers: `deletionProtection` (AWS),
  `deletionPolicy: Orphan` (Crossplane), and a final snapshot.
- DynamoDB declares only **key** attributes, never data fields.

➡️ **[challenge.md](./challenge.md)** then [Module 10](../10-reuse-and-packaging/).
