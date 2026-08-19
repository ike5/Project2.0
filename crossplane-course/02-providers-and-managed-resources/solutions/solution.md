# Challenge 02 — Reference Solution

### 1. A second ProviderConfig

```yaml
# sandbox-config.yaml
apiVersion: aws.upbound.io/v1beta1
kind: ProviderConfig
metadata:
  name: sandbox
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
---
apiVersion: s3.aws.upbound.io/v1beta1
kind: Bucket
metadata: { name: prod-bucket }
spec:
  forProvider: { region: us-east-1 }
  providerConfigRef: { name: default }
---
apiVersion: s3.aws.upbound.io/v1beta1
kind: Bucket
metadata: { name: sandbox-bucket }
spec:
  forProvider: { region: us-east-1 }
  providerConfigRef: { name: sandbox }
```

Prove which config each used:
```bash
kubectl get buckets -o custom-columns=\
NAME:.metadata.name,CONFIG:.spec.providerConfigRef.name,SYNCED:.status.conditions[0].status
```
```
NAME             CONFIG    SYNCED
prod-bucket      default   True
sandbox-bucket   sandbox   True
```

Crossplane also tracks usage from the config's side:
```bash
kubectl get providerconfigusages
```
Each shows which resource is bound to which config. This is what stops you deleting a
ProviderConfig that resources still depend on.

**A missing config:**
```bash
kubectl patch bucket sandbox-bucket --type=merge \
  -p '{"spec":{"providerConfigRef":{"name":"nonexistent"}}}'
kubectl get bucket sandbox-bucket -o jsonpath='{.status.conditions[?(@.type=="Synced")].message}'
```
```
cannot resolve provider config: providerconfigs.aws.upbound.io "nonexistent" not found
```
The resource goes `Synced=False` and **stops being reconciled** — but the bucket in
AWS is untouched. Crossplane can't manage what it can't authenticate to, so it stops
and reports. It does not delete anything, which is the safe behaviour.

### 2. Discovering BucketLifecycleConfiguration

```bash
# Full apiVersion
kubectl api-resources --api-group=s3.aws.upbound.io | grep -i lifecycle
# bucketlifecycleconfigurations   s3.aws.upbound.io/v1beta1   true   BucketLifecycleConfiguration

# Required fields
kubectl explain bucketlifecycleconfiguration.spec.forProvider | grep -i -B2 required
kubectl explain bucketlifecycleconfiguration.spec.forProvider.rule

# How it references its bucket
kubectl explain bucketlifecycleconfiguration.spec.forProvider.bucketRef
```

Answers: `s3.aws.upbound.io/v1beta1`; `region` and `rule` are required; it references
its bucket via `bucketRef.name` (a Kubernetes object name), `bucketSelector`
(labels), or `bucket` (a literal S3 name).

```yaml
apiVersion: s3.aws.upbound.io/v1beta1
kind: BucketLifecycleConfiguration
metadata: { name: app-data-lifecycle }
spec:
  forProvider:
    region: us-east-1
    bucketRef: { name: app-data }
    rule:
      - id: expire-tmp
        status: Enabled
        filter:
          - prefix: tmp/
        expiration:
          - days: 7
  providerConfigRef: { name: default }
```
```bash
awslocal s3api get-bucket-lifecycle-configuration --bucket app-data
```

> **`kubectl explain` is the right reflex.** It reflects the exact provider version
> installed, so it can't drift from reality the way a docs page can.

### 3. A tighter activation policy

```yaml
apiVersion: apiextensions.crossplane.io/v1alpha1
kind: ManagedResourceActivationPolicy
metadata: { name: course-resources }
spec:
  activate:
    - buckets.s3.aws.upbound.io
    - bucketversionings.s3.aws.upbound.io
```

```bash
kubectl apply -f tight-mrap.yaml
kubectl get crd bucketpublicaccessblocks.s3.aws.upbound.io
# Error from server (NotFound)
```

**What happens to existing instances?** This is the important part, and the answer
surprises people: **deactivating a type removes its CRD, and deleting a CRD deletes
every object of that kind.** The Kubernetes objects vanish.

What happens to the *cloud* resources depends on timing and on whether the provider
gets to process the finalizers before its CRD disappears. In practice this is
**unsafe and can orphan real infrastructure**.

**The operational rule:** treat MRAP like a firewall rule. Only ever *widen* it
casually. Before removing a type, confirm nothing uses it:
```bash
kubectl get bucketpublicaccessblocks -A
```
and if anything does, delete those objects deliberately first.

### 4. Predictions and results

**a) Delete the credentials Secret.**

*Prediction:* the bucket goes `Synced=False`; the real bucket is unaffected.

*Actual:* correct. Within a reconcile interval:
```
NAME       SYNCED   READY
app-data   False    True
```
with a message about being unable to get credentials. `READY` stays `True` because it
reflects the last *known* state — Crossplane can't observe the resource any more, so
it reports the last thing it knew rather than guessing.

**The lesson:** losing credentials is a *safe* failure. Crossplane stops and
complains; it never interprets "I can't see it" as "it must be deleted."

Restore with `kubectl create secret ...` and it recovers on its own.

**b) Change the external name to something nonexistent.**

*Prediction (most people):* Crossplane renames the bucket, or errors.

*Actual:* **Crossplane creates a brand new bucket with the new name, and the original
is orphaned** — still in AWS, no longer managed by anything.

```bash
kubectl annotate bucket app-data crossplane.io/external-name=totally-different --overwrite
sleep 60
awslocal s3 ls     # BOTH buckets now exist
```

This is why the README says never to edit this annotation on a live resource. The
annotation isn't a name *setting* — it's the pointer Crossplane uses to find the
resource it manages. Repoint it and you've told Crossplane "manage that other thing
instead." On an RDS instance this means your production database becomes unmanaged
while an empty new one is provisioned alongside it.

**c) Delete the provider while buckets exist.**

*Prediction:* the buckets are deleted, or nothing happens.

*Actual:* the **buckets get stuck in `Terminating` forever** — or, if you don't delete
them, they simply stop reconciling.

Deleting the Provider removes its controller pod and eventually its CRDs. If a Bucket
object has a finalizer and no controller is left running, nothing can process that
finalizer, so deletion hangs indefinitely.

**Recovery:** reinstall the provider. The controller comes back, processes the pending
finalizers, and deletion completes normally.

```bash
kubectl apply -f manifests/provider-s3.yaml
kubectl wait provider/provider-aws-s3 --for=condition=Healthy --timeout=10m
```

**The lesson:** always delete managed resources *before* the provider that manages
them. Removing the controller first strands everything it owned. This generalises —
it's the same reason you don't uninstall a CRD's operator before its custom resources.

### 5. Stretch — measuring MRAP's saving

```bash
# metrics-server on kind needs --kubelet-insecure-tls
helm repo add metrics-server https://kubernetes-sigs.github.io/metrics-server/
helm upgrade --install metrics-server metrics-server/metrics-server \
  -n kube-system --set 'args={--kubelet-insecure-tls}'
sleep 60

# Baseline: activate everything
kubectl apply -f - <<'YAML'
apiVersion: apiextensions.crossplane.io/v1alpha1
kind: ManagedResourceActivationPolicy
metadata: { name: course-resources }
spec:
  activate: ["*"]
YAML
kubectl rollout restart deploy -n crossplane-system \
  -l pkg.crossplane.io/provider=provider-aws-ec2
sleep 120
kubectl top pod -n crossplane-system | grep ec2

# Narrow, then re-measure
kubectl apply -f manifests/mrap.yaml
kubectl rollout restart deploy -n crossplane-system \
  -l pkg.crossplane.io/provider=provider-aws-ec2
sleep 120
kubectl top pod -n crossplane-system | grep ec2
```

Representative numbers (yours will differ by provider version and machine):
```
all resources active:      ~640Mi
8 resources active:        ~180Mi      → ~72% saved
```

The saving comes from watches and informer caches: each activated type means one more
watch on the API server and one more in-memory cache in the provider. It scales with
the number of *types*, not the number of *resources* — so a platform managing ten
buckets pays the same bloat cost as one managing ten thousand, unless it narrows the
activation policy.
