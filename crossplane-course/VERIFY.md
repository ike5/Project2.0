# End-to-End Verification

Run this **once after Module 00**, and any time something feels broken. It goes
further than `verify-setup.sh`: it installs a real provider and provisions a real
S3 bucket through Crossplane. If every step here passes, the rest of the course
will work.

⏱️ ~10 minutes (most of it waiting for an image pull).

---

## 0. Tools respond

```bash
docker version          # client + server both answer
kind version
kubectl version --client
helm version
crossplane version --client
```
✅ Expected: each prints a version; `crossplane` reports **v2.x**.

## 1. Cluster is up with 3 nodes

```bash
cd 00-setup
./scripts/create-cluster.sh      # idempotent
kubectl get nodes
```
✅ Expected: **3 nodes**, all `Ready`.

## 2. Crossplane core is healthy

```bash
kubectl get pods -n crossplane-system
kubectl api-resources --api-group=apiextensions.crossplane.io
```
✅ Expected: pods `Running`, and these API kinds exist:
```
compositeresourcedefinitions   xrd,xrds   apiextensions.crossplane.io/v2   false   CompositeResourceDefinition
compositionrevisions           comprev    apiextensions.crossplane.io/v1   false   CompositionRevision
compositions                   comp       apiextensions.crossplane.io/v1   false   Composition
```

## 3. The emulator answers from inside the cluster

This matters because **the provider pod** makes the AWS calls, not your laptop.
Testing from your laptop would prove nothing.

```bash
kubectl run curl-test --rm -it --restart=Never --image=curlimages/curl:8.10.1 -- \
  -s http://moto.aws-local.svc.cluster.local:5000/moto-api/
```
✅ Expected: a JSON blob listing services, each `"available"` or `"running"`:
```json
{"services": {"s3": "available", "iam": "available", "sts": "available", ...}}
```

> ❌ If this times out, the emulator isn't ready. `kubectl get pods -n aws-local`
> and wait for `1/1 Running`.

## 4. Install the AWS S3 provider

```bash
kubectl apply -f - <<'YAML'
apiVersion: pkg.crossplane.io/v1
kind: Provider
metadata:
  name: provider-aws-s3
spec:
  package: xpkg.upbound.io/upbound/provider-aws-s3:v1.21.0
YAML

kubectl wait provider.pkg.crossplane.io/provider-aws-s3 \
  --for=condition=Healthy --timeout=10m
```
✅ Expected: `provider.pkg.crossplane.io/provider-aws-s3 condition met`.

This pulls a large image and installs CRDs, so the first run genuinely can take
several minutes. Watch it if you're impatient:
```bash
kubectl get providers -w
```

Confirm the `Bucket` API now exists in your cluster:
```bash
kubectl api-resources --api-group=s3.aws.upbound.io | head
```
✅ Expected: `buckets  s3.aws.upbound.io/v1beta1  ...  Bucket` among the rows.

> **This is the moment worth pausing on.** You just added a cloud service to the
> Kubernetes API. `kubectl get buckets` is now a valid command on your cluster.

## 5. Give the provider credentials and an endpoint

moto accepts any credentials, so these are deliberately fake.

```bash
kubectl create secret generic aws-creds \
  -n crossplane-system \
  --from-literal=creds='[default]
aws_access_key_id = test
aws_secret_access_key = test'

kubectl apply -f - <<'YAML'
apiVersion: aws.upbound.io/v1beta1
kind: ProviderConfig
metadata:
  name: default
spec:
  credentials:
    source: Secret
    secretRef:
      namespace: crossplane-system
      name: aws-creds
      key: creds
  # Point the AWS SDK at the local emulator instead of amazonaws.com.
  endpoint:
    hostnameImmutable: true
    url:
      type: Static
      static: http://moto.aws-local.svc.cluster.local:5000
  # The emulator doesn't implement these checks; skip them.
  skip_credentials_validation: true
  skip_metadata_api_check: true
  skip_requesting_account_id: true
  skip_region_validation: true
  s3_use_path_style: true
YAML
```
✅ Expected: `secret/aws-creds created` and `providerconfig.aws.upbound.io/default created`.

> `s3_use_path_style: true` is the emulator-specific bit. Real S3 uses
> virtual-host addressing (`my-bucket.s3.amazonaws.com`); The emulator serves
> everything from one hostname, so buckets must appear in the *path*
> (`moto:5000/my-bucket`). Get this wrong and buckets fail with DNS errors.

## 6. Provision a bucket — the real test

```bash
kubectl apply -f - <<'YAML'
apiVersion: s3.aws.upbound.io/v1beta1
kind: Bucket
metadata:
  name: xp-course-smoke-test
spec:
  forProvider:
    region: us-east-1
  providerConfigRef:
    name: default
YAML

kubectl wait bucket.s3.aws.upbound.io/xp-course-smoke-test \
  --for=condition=Ready --timeout=3m
```
✅ Expected: `bucket.s3.aws.upbound.io/xp-course-smoke-test condition met`.

```bash
kubectl get buckets
```
✅ Expected:
```
NAME                   SYNCED   READY   EXTERNAL-NAME          AGE
xp-course-smoke-test   True     True    xp-course-smoke-test   40s
```

**`SYNCED=True`** means Crossplane successfully talked to the AWS API.
**`READY=True`** means the bucket actually exists out there. Both true = your whole
pipeline works.

## 7. Confirm it exists on the "AWS" side

Don't take Crossplane's word for it — ask AWS directly:

```bash
kubectl run awscli --rm -it --restart=Never \
  --image=amazon/aws-cli:2.18.9 \
  --env=AWS_ACCESS_KEY_ID=test \
  --env=AWS_SECRET_ACCESS_KEY=test \
  --env=AWS_DEFAULT_REGION=us-east-1 \
  -- --endpoint-url=http://moto.aws-local.svc.cluster.local:5000 s3 ls
```
✅ Expected: your bucket, listed by the actual AWS CLI:
```
2026-01-15 10:32:11 xp-course-smoke-test
```

> Keep this `awscli` one-liner handy — it's how you verify **every** AWS lab in this
> course from the outside. The cheatsheet has it too.

## 8. Clean up the smoke test

```bash
kubectl delete bucket xp-course-smoke-test
kubectl wait --for=delete bucket/xp-course-smoke-test --timeout=2m
```
✅ Expected: the object is gone, and re-running the `aws s3 ls` command above shows
no buckets. Crossplane deleted the real resource, not just the Kubernetes object.

**Leave the provider, the Secret, and the ProviderConfig installed** — Module 02
picks up exactly here.

---

## If a step failed

| Symptom | Cause | Fix |
|---------|-------|-----|
| Provider never goes `Healthy` | Image pull is slow or blocked | `kubectl describe provider provider-aws-s3` → read Events |
| Bucket `SYNCED=False` | Provider can't reach the emulator | Re-run step 3; check the endpoint URL in your ProviderConfig for typos |
| Bucket `SYNCED=True`, `READY=False` | AWS accepted the call but the resource isn't ready | `kubectl describe bucket <name>` → read Events and Conditions |
| `no matches for kind "Bucket"` | Provider CRDs aren't installed yet | Wait for the provider to be `Healthy`, then retry |
| `InvalidClientTokenId` / signature errors | Credential Secret is malformed | The `creds` key must be INI format, including the `[default]` line |

The full decision tree lives in
[cheatsheets/troubleshooting.md](./cheatsheets/troubleshooting.md).

---

🎉 **All green?** Your control plane is real and it provisions cloud resources.
Head to **[Module 01: Control-Plane Thinking](./01-control-plane-thinking/)**.
