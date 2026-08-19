# Capstone — reference walkthrough

**Read this after building yours.** It is one set of defensible choices, not the
answer. Where yours differs, be able to say why.

---

## Deploy the reference implementation

```bash
cd 15-capstone/solutions

# 1. Platform prerequisites (from earlier modules)
kubectl apply -f ../../06-composing-applications/manifests/providers.yaml
kubectl apply -f ../../05-composition-functions/manifests/functions.yaml
kubectl apply -f - <<'YAML'
apiVersion: pkg.crossplane.io/v1
kind: Function
metadata: { name: function-environment-configs }
spec:
  package: xpkg.upbound.io/crossplane-contrib/function-environment-configs:v0.4.0
---
apiVersion: pkg.crossplane.io/v1
kind: Function
metadata: { name: function-extra-resources }
spec:
  package: xpkg.upbound.io/crossplane-contrib/function-extra-resources:v0.1.4
YAML
kubectl wait provider,function --all --for=condition=Healthy --timeout=10m

# 2. The platform
kubectl apply -f tenants/tenants.yaml
kubectl apply -f config/
kubectl apply -f apis/
sleep 5
kubectl apply -f compositions/
kubectl apply -f tenants/policies.yaml

# 3. Build the sample app if you haven't
cd ../../06-composing-applications/manifests/app
docker build -t xp-course/sample-app:1.0 .
kind load docker-image xp-course/sample-app:1.0 --name xp-course
cd ../../../15-capstone/solutions
```

## Ship a service, as a developer

```bash
kubectl apply -f examples/service.yaml \
  --as=system:serviceaccount:team-payments:developer
kubectl get services.platform.acme.io -n team-payments -w
```
✅ Expected, in 2–4 minutes:
```
NAME       IMAGE                      SIZE     DB     ENV   URL                        READY
checkout   xp-course/sample-app:1.0   medium   true   dev   http://checkout.localhost  True
worker     xp-course/sample-app:1.0   small    false  dev                              True
```

```bash
crossplane trace service.platform.acme.io checkout -n team-payments
```
✅ Expected: ~12 resources — subnet group, RDS instance, bucket, public access block,
encryption, IAM role, policy, attachment, ServiceAccount, Deployment, Service, Ingress.

**From twelve lines.**

## Verify every claim the platform makes

```bash
# The developer never sees the password, but the app has it
kubectl port-forward -n team-payments svc/checkout 8080:80 &
sleep 3; curl -s localhost:8080/ | jq '.database'; kill %1
```
✅ Expected: `"password_present": true` with the value never shown.

```bash
# The password is NOT readable from the XR
kubectl get service.platform.acme.io checkout -n team-payments -o yaml | grep -i password
```
✅ Expected: no output.

```bash
# The bucket is private, and IAM is scoped to exactly it
BUCKET=$(kubectl get service.platform.acme.io checkout -n team-payments -o jsonpath='{.status.bucketName}')
awslocal s3api get-public-access-block --bucket "$BUCKET"
awslocal iam get-policy-version \
  --policy-arn "$(awslocal iam list-policies --scope Local \
    --query 'Policies[?contains(PolicyName,`checkout`)].Arn' --output text)" \
  --version-id v1 --query 'PolicyVersion.Document'
```
✅ Expected: all four blocks true; the policy names **only** this bucket, in two
statements.

```bash
# The optional components are genuinely absent
crossplane trace service.platform.acme.io worker -n team-payments
```
✅ Expected: 3 resources. No database, no bucket, no IAM, no Ingress.

## Verify the safety properties

```bash
D=--as=system:serviceaccount:team-payments:developer

# Data-destroying change: REJECTED
kubectl patch service.platform.acme.io checkout -n team-payments $D \
  --type=merge -p '{"spec":{"database":false}}'
#   `database` cannot be changed after creation...

# Downsizing: REJECTED
kubectl patch service.platform.acme.io checkout -n team-payments $D \
  --type=merge -p '{"spec":{"size":"small"}}'
#   `size` can only be increased...

# Composition hijack (Module 13's discovered hole): REJECTED
kubectl patch service.platform.acme.io checkout -n team-payments $D \
  --type=merge -p '{"spec":{"crossplane":{"compositionRef":{"name":"anything"}}}}'
#   spec.crossplane is managed by the platform...

# Bypassing the platform API: REJECTED
kubectl create -n team-payments $D -f - <<'YAML'
apiVersion: s3.aws.upbound.io/v1beta1
kind: Bucket
metadata: { name: unguarded }
spec:
  forProvider: { region: us-east-1 }
  providerConfigRef: { name: team-payments }
YAML
#   Forbidden

# Missing owner label: REJECTED
kubectl create -n team-payments $D -f - <<'YAML'
apiVersion: platform.acme.io/v1alpha1
kind: Service
metadata: { name: unowned }
spec: { image: nginx:1.27 }
YAML
#   Every Service must carry an acme.io/owner label...

# A SAFE change: accepted, in place
kubectl patch service.platform.acme.io checkout -n team-payments $D \
  --type=merge -p '{"spec":{"size":"large"}}'
```

## The design write-up

### 1. What developers deliberately cannot configure

**`region`.** We run in `us-east-1`. Exposing it would let someone deploy a service
into a region with no network, no monitoring, and no on-call coverage — and the
failure appears as an unrelated networking error weeks later. *Prevents:* orphaned
infrastructure in regions nobody watches.

**`instanceClass`, `engineVersion`, `allocatedStorage`.** These are cost and
compatibility decisions with blast radius beyond the requesting team. `size` maps to
them, so we can retune the mapping — or migrate to Graviton — without a single
consumer change. *Prevents:* a `db.r6g.16xlarge` in a dev namespace, and a fleet
pinned to an EOL engine version.

**`environment`.** The most important omission. If a developer can set it, a dev
namespace can request production behaviour and, with the per-tenant ProviderConfig,
production credentials. We derive it from a namespace label they have no RBAC to
patch. *Prevents:* Module 13's attack 7 — privilege escalation by YAML.

**Encryption, public access blocking, backups, deletion protection.** Not fields at
all. A developer cannot forget what they were never asked. *Prevents:* the audit
finding that starts "a bucket containing customer data was world-readable".

### 2. Where the security boundary is

**The `Service` API itself.** Everything a developer can do goes through it, and it
is the only thing they can create. RBAC denying `create` on managed resources is what
makes that true — without it, the API is a suggestion.

**If someone gets past it** (a stray `ClusterRoleBinding`, a compromised token) they
reach whatever the tenant's `ProviderConfig` can reach. On this course cluster, that
is everything, because both tenants share one credential. On real AWS with
per-tenant accounts, they reach **one tenant's account** — the blast radius is bounded
by AWS rather than by our RBAC being correct.

### 3. Which controls are enforced by Kubernetes, which by AWS

| Control | Layer | Survives a cluster misconfiguration? |
|---------|-------|--------------------------------------|
| Developers can't create managed resources | Kubernetes | ❌ |
| Immutability rules | Kubernetes | ❌ |
| Admission policies | Kubernetes | ❌ |
| Quotas | Kubernetes | ❌ |
| `deletionPolicy: Orphan` | Crossplane | ❌ |
| **`deletionProtection`** | **AWS** | ✅ |
| **Permissions boundary** | **AWS** | ✅ |
| **Per-tenant account + IAM trust** | **AWS** | ✅ |

**Eight controls, three of which survive us being wrong.** That is the honest
assessment, and it is why the single highest-value change to this platform is
**separate AWS accounts per tenant** — it converts the tenancy boundary from "our
RBAC is correct" to "AWS refuses".

### 4. What breaks if you rename a composed resource

Crossplane identifies composed resources by their name annotation. Renaming `database`
to `db` makes Crossplane see one resource removed and another added: it **deletes the
RDS instance and creates a new, empty one**, for every existing Service, within about
a minute of apply.

`deletionPolicy: Orphan` on production saves the *data* — the old instance survives,
unmanaged — but production is now pointed at an empty database. It is an outage either
way.

CI catches it:
```bash
./ci/check-destructive.sh --base-ref main
#   ✗ service-aws: COMPOSED RESOURCE NAMES CHANGED
#     < crossplane.io/composition-resource-name: database
#     > crossplane.io/composition-resource-name: db
```
Two seconds, no cluster. Overriding it requires a `breaking-change-approved` label.

### 5. What we chose not to build

**Multi-cloud.** One `Service` API with an AWS composition and a GCP composition is
technically easy and strategically expensive: every feature must then exist in both,
tested in both, on two clouds' release schedules. We would reconsider **only** if the
business committed to a second cloud for a named reason — not for optionality, which
is the reason people usually give and which never survives contact with the roadmap.

**Autoscaling.** `size` is static. An HPA is easy to add and hard to tune, and a
badly-tuned one is worse than a fixed replica count. We would add it once we have
per-service latency SLOs to scale against — scaling on CPU without them is guessing.

**A self-service network.** `XNetwork` exists (Module 07) but is **not** part of
`Service`. A VPC outlives every service in it, and AWS defaults to five per region —
40 services each owning one would exhaust the quota at service six. Services
*reference* the shared network; they don't own it. **Ownership follows lifecycle.**

**Cost reporting in the composition.** We tag every resource with `team`, `service`
and `environment`, and let Cost Explorer do costing. A template computing dollar
amounts is untestable, wrong within a quarter, and authoritative-looking — the worst
combination.

---

## What this demonstrates

Every learning goal from the [course README](../../README.md#what-youll-be-able-to-do-at-the-end):
an API a developer can use without AWS knowledge, implemented with a function
pipeline, composing applications and infrastructure together, secured for multiple
tenants, packaged for distribution, and defended by automation that stops it
destroying production.

**That's the job.**
