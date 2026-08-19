# Challenge 03 — Reference Solution

### 1. Audit before you touch

```yaml
# audit.yaml — three read-only imports
apiVersion: s3.aws.upbound.io/v1beta1
kind: Bucket
metadata:
  name: prod-uploads
  annotations: { crossplane.io/external-name: acme-prod-uploads }
spec:
  managementPolicies: ["Observe"]
  forProvider: { region: us-east-1 }
  providerConfigRef: { name: default }
---
apiVersion: s3.aws.upbound.io/v1beta1
kind: Bucket
metadata:
  name: prod-backups
  annotations: { crossplane.io/external-name: acme-prod-backups }
spec:
  managementPolicies: ["Observe"]
  forProvider: { region: us-east-1 }
  providerConfigRef: { name: default }
---
apiVersion: s3.aws.upbound.io/v1beta1
kind: Bucket
metadata:
  name: staging-uploads
  annotations: { crossplane.io/external-name: acme-staging-uploads }
spec:
  managementPolicies: ["Observe"]
  forProvider: { region: us-east-1 }
  providerConfigRef: { name: default }
```

```bash
kubectl apply -f audit.yaml
sleep 30
kubectl get buckets
for b in prod-uploads prod-backups staging-uploads; do
  echo "=== $b ==="
  kubectl get bucket $b -o jsonpath='{.status.atProvider}' | jq '{arn, tags}'
done
```

Versioning is a *separate* resource, so import it separately to inspect it:
```yaml
apiVersion: s3.aws.upbound.io/v1beta1
kind: BucketVersioning
metadata:
  name: prod-backups-versioning
  annotations: { crossplane.io/external-name: acme-prod-backups }
spec:
  managementPolicies: ["Observe"]
  forProvider:
    region: us-east-1
    bucketRef: { name: prod-backups }
  providerConfigRef: { name: default }
```

**Inventory:**

| Bucket | Tags | Versioning | Holds data |
|--------|------|-----------|-----------|
| `acme-prod-uploads` | `env=prod`, `team=payments` | No | No |
| `acme-prod-backups` | none | **Enabled** | **Yes** (`jan.bak`) |
| `acme-staging-uploads` | none | No | No |

> Note what the audit surfaced that a naive import would have destroyed:
> `acme-prod-uploads` has tags a bare manifest would wipe, and `acme-prod-backups`
> has versioning that lives in a resource you'd otherwise never have created.

### 2. Adopt with the right posture

```yaml
# adopt.yaml
apiVersion: s3.aws.upbound.io/v1beta1
kind: Bucket
metadata:
  name: prod-uploads
  annotations: { crossplane.io/external-name: acme-prod-uploads }
spec:
  managementPolicies: ["*"]
  forProvider:
    region: us-east-1
    tags:                          # copied verbatim from status.atProvider
      env: prod
      team: payments
  providerConfigRef: { name: default }
  deletionPolicy: Orphan
---
apiVersion: s3.aws.upbound.io/v1beta1
kind: Bucket
metadata:
  name: prod-backups
  annotations: { crossplane.io/external-name: acme-prod-backups }
spec:
  # Holds data: manage it, but never let Crossplane delete it. Belt AND braces —
  # Delete removed from the policy list, and Orphan on top.
  managementPolicies: ["Observe", "Create", "Update", "LateInitialize"]
  forProvider: { region: us-east-1 }
  providerConfigRef: { name: default }
  deletionPolicy: Orphan
---
apiVersion: s3.aws.upbound.io/v1beta1
kind: BucketVersioning
metadata:
  name: prod-backups-versioning
  annotations: { crossplane.io/external-name: acme-prod-backups }
spec:
  managementPolicies: ["Observe", "Create", "Update", "LateInitialize"]
  forProvider:
    region: us-east-1
    bucketRef: { name: prod-backups }
    versioningConfiguration:
      status: Enabled              # matches reality — does not change it
  providerConfigRef: { name: default }
---
apiVersion: s3.aws.upbound.io/v1beta1
kind: Bucket
metadata:
  name: staging-uploads
  annotations: { crossplane.io/external-name: acme-staging-uploads }
spec:
  managementPolicies: ["*"]
  forProvider: { region: us-east-1 }
  providerConfigRef: { name: default }
  deletionPolicy: Delete
```

**Prove nothing changed:**
```bash
# BEFORE
awslocal s3api get-bucket-tagging --bucket acme-prod-uploads > /tmp/before-tags.json
awslocal s3api get-bucket-versioning --bucket acme-prod-backups > /tmp/before-ver.json

kubectl apply -f adopt.yaml
sleep 60

# AFTER — must be identical
awslocal s3api get-bucket-tagging --bucket acme-prod-uploads > /tmp/after-tags.json
awslocal s3api get-bucket-versioning --bucket acme-prod-backups > /tmp/after-ver.json
diff /tmp/before-tags.json /tmp/after-tags.json && echo "✅ tags unchanged"
diff /tmp/before-ver.json  /tmp/after-ver.json  && echo "✅ versioning unchanged"

# Data still present
awslocal s3 ls s3://acme-prod-backups/
```

**A successful import produces no diff.** If `diff` shows anything, your spec
disagreed with reality and Crossplane "fixed" the wrong side.

### 3. Prove the protection

```bash
kubectl delete bucket prod-uploads prod-backups staging-uploads
kubectl delete bucketversioning prod-backups-versioning
sleep 30
awslocal s3 ls
awslocal s3 ls s3://acme-prod-backups/
```

Result:
```
2026-01-15 11:20:03 acme-prod-uploads     ← survived
2026-01-15 11:20:05 acme-prod-backups     ← survived, data intact
                                          ← acme-staging-uploads is GONE
2026-01-15 11:20:11 jan.bak
```

- `acme-prod-backups` and `acme-prod-uploads` survived because of
  **`deletionPolicy: Orphan`** (and, for backups, because `Delete` was additionally
  absent from `managementPolicies`).
- `acme-staging-uploads` was destroyed because it had the default
  **`deletionPolicy: Delete`**.

### 4. The dangerous scenario

```bash
kubectl get buckets -o name | xargs kubectl delete
```

**What happens in this estate:** all three Kubernetes objects are deleted. Then:
- `acme-prod-uploads` — **survives** (Orphan), now unmanaged.
- `acme-prod-backups` — **survives** (Orphan + no Delete verb), now unmanaged.
- `acme-staging-uploads` — **destroyed**, permanently.

So the estate survives *this time* — but only because someone remembered to set
`Orphan` on the right two buckets. **That's a convention, not a control.** The next
bucket someone adds without it is unprotected, and the command gives no warning.

**Guardrails, in increasing strength:**

1. **RBAC — the real answer (Module 13).** Almost nobody should hold `delete` on
   managed resources in a production cluster:
   ```yaml
   apiVersion: rbac.authorization.k8s.io/v1
   kind: ClusterRole
   metadata: { name: crossplane-viewer }
   rules:
     - apiGroups: ["s3.aws.upbound.io"]
       resources: ["*"]
       verbs: ["get", "list", "watch"]     # no delete, no patch
   ```

2. **A validating admission policy** that rejects deletion of anything labelled
   `criticality: high`, so protection is enforced centrally rather than per-resource:
   ```yaml
   apiVersion: admissionregistration.k8s.io/v1
   kind: ValidatingAdmissionPolicy
   metadata: { name: protect-critical }
   spec:
     matchConstraints:
       resourceRules:
         - apiGroups: ["s3.aws.upbound.io"]
           operations: ["DELETE"]
           resources: ["buckets"]
     validations:
       - expression: "oldObject.metadata.?labels['criticality'].orValue('') != 'high'"
         message: "Buckets labelled criticality=high cannot be deleted directly."
   ```

3. **Defaulting policy** — a mutating policy that sets `deletionPolicy: Orphan` on
   anything in a production namespace, so protection is the default rather than
   something to remember.

4. **GitOps with no direct cluster access (Module 14).** If deletions can only happen
   through a reviewed pull request, `xargs kubectl delete` isn't a command anyone can
   run in the first place.

**The principle:** `deletionPolicy` protects a resource from *the reconcile loop*. It
does not protect it from *a human with credentials*. Those need different controls.

### 5. Stretch — the import script

```bash
#!/usr/bin/env bash
# import-bucket.sh <aws-bucket-name> [k8s-object-name]
set -euo pipefail

BUCKET="${1:?usage: import-bucket.sh <aws-bucket-name> [k8s-name]}"
NAME="${2:-$(echo "$BUCKET" | tr '.' '-')}"
REGION="${REGION:-us-east-1}"

echo "🔍 Importing '${BUCKET}' as Bucket/${NAME} (observe-only)..."

kubectl apply -f - <<YAML
apiVersion: s3.aws.upbound.io/v1beta1
kind: Bucket
metadata:
  name: ${NAME}
  annotations:
    crossplane.io/external-name: ${BUCKET}
spec:
  managementPolicies: ["Observe"]
  forProvider:
    region: ${REGION}
  providerConfigRef:
    name: default
YAML

echo "⏳ Waiting for Crossplane to observe it..."
if ! kubectl wait --for=condition=Ready "bucket/${NAME}" --timeout=120s; then
  echo "❌ Never became Ready. The bucket may not exist, or the name is wrong:" >&2
  kubectl get "bucket/${NAME}" \
    -o jsonpath='{.status.conditions[?(@.type=="Synced")].message}' >&2
  exit 1
fi

echo
echo "✅ Observed. Discovered state:"
kubectl get "bucket/${NAME}" -o jsonpath='{.status.atProvider}' | jq

echo
echo "📋 Suggested spec.forProvider for full management:"
kubectl get "bucket/${NAME}" -o json \
  | jq '{region: .status.atProvider.region, tags: .status.atProvider.tags}
        | with_entries(select(.value != null))'

echo
echo "⚠️  Review the above, merge it into your manifest, THEN widen"
echo "    managementPolicies to [\"*\"]. Do not skip the review — an incorrect"
echo "    spec will be applied to the real resource on the next reconcile."
```

```bash
chmod +x import-bucket.sh
./import-bucket.sh acme-prod-uploads
```

The deliberate design choice here: the script **stops** at the suggestion and makes a
human merge it. Auto-generating and auto-applying a full-management manifest would
reintroduce exactly the risk the Observe step exists to eliminate.
