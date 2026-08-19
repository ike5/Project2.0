# Challenge 04 — Reference Solution

Runnable manifests accompany this file:
[`xstaticsite-xrd.yaml`](./xstaticsite-xrd.yaml),
[`xstaticsite-composition.yaml`](./xstaticsite-composition.yaml),
[`xbucket-v2-xrd.yaml`](./xbucket-v2-xrd.yaml).

---

### 1. XStaticSite

See [`xstaticsite-xrd.yaml`](./xstaticsite-xrd.yaml) and
[`xstaticsite-composition.yaml`](./xstaticsite-composition.yaml).

The interesting mechanic is making one boolean drive two coordinated changes. A `map`
transform can't be used directly — its keys are strings — so convert first:

```yaml
- type: FromCompositeFieldPath
  fromFieldPath: spec.public
  toFieldPath: spec.forProvider.blockPublicPolicy
  transforms:
    - type: convert
      convert: { toType: string }      # true -> "true"
    - type: map
      map: { "true": false, "false": true }   # public means DON'T block
```

Note the inversion: `public: true` must set `blockPublicPolicy: false`. Getting this
backwards produces a site that returns 403 while looking correctly configured, which
is a genuinely annoying bug to chase.

The bucket policy is only wanted when public, and patch-and-transform has no "skip
this resource" mechanism — so it always renders, and we make it harmless when
private by templating the policy's `Effect`:

```yaml
- type: FromCompositeFieldPath
  fromFieldPath: spec.public
  toFieldPath: spec.forProvider.policy
  transforms:
    - type: convert
      convert: { toType: string }
    - type: map
      map:
        "true": |
          {"Version":"2012-10-17","Statement":[{"Sid":"PublicRead","Effect":"Allow",
           "Principal":"*","Action":"s3:GetObject","Resource":"arn:aws:s3:::*/*"}]}
        "false": |
          {"Version":"2012-10-17","Statement":[{"Sid":"NoPublicRead","Effect":"Deny",
           "Principal":"*","Action":"s3:GetObject","Resource":"arn:aws:s3:::*/*"}]}
```

> This works but it's ugly — a JSON document embedded in a YAML map value, and a
> resource that exists even when unwanted. **This is precisely the pain that motivates
> Module 05.** With `function-go-templating` you write `{{ if .spec.public }}` and the
> resource simply isn't rendered. Feel the pain here so the fix lands.

Verify:
```bash
kubectl apply -f xstaticsite-xrd.yaml -f xstaticsite-composition.yaml
kubectl apply -f - <<'YAML'
apiVersion: platform.acme.io/v1alpha1
kind: XStaticSite
metadata: { name: marketing-site, namespace: team-web }
spec: { indexDocument: index.html, public: true }
YAML
kubectl get xstaticsite marketing-site -n team-web -o jsonpath='{.status.url}'
awslocal s3api get-public-access-block --bucket team-web-marketing-site
```

### 2. sizeCategory → retention

In the XRD:
```yaml
sizeCategory:
  type: string
  enum: [small, medium, large]
  default: small
```
Remove `retentionDays` entirely — if the developer can't set it, they can't set it
wrong.

In the composition:
```yaml
- type: FromCompositeFieldPath
  fromFieldPath: spec.sizeCategory
  toFieldPath: spec.forProvider.rule[0].expiration[0].days
  transforms:
    - type: map
      map: { small: 30, medium: 90, large: 365 }
  policy:
    fromFieldPath: Required
```

> **`map` values keep their YAML type.** `30` here is an integer, which is what the
> `days` field needs. Writing `"30"` would produce a type error at apply time —
> a common and confusing failure.

### 3. Guarding retention on prod, two ways

**a) In the XRD schema, with CEL validation:**
```yaml
schema:
  openAPIV3Schema:
    type: object
    properties:
      spec:
        type: object
        properties:
          environment: { type: string, enum: [dev, staging, prod] }
          retentionDays: { type: integer, minimum: 1, maximum: 3650 }
        required: [environment]
        x-kubernetes-validations:
          - rule: "self.environment != 'prod' || !has(self.retentionDays) || self.retentionDays >= 30"
            message: "prod buckets must retain data for at least 30 days"
```

```bash
kubectl apply -f - <<'YAML'
apiVersion: platform.acme.io/v1alpha1
kind: XBucket
metadata: { name: risky, namespace: team-payments }
spec: { environment: prod, retentionDays: 1 }
YAML
# Error: prod buckets must retain data for at least 30 days
```

**b) In the composition, by clamping:**
```yaml
- type: FromCompositeFieldPath
  fromFieldPath: spec.retentionDays
  toFieldPath: spec.forProvider.rule[0].expiration[0].days
  transforms:
    - type: math
      math: { type: ClampMin, clampMin: 30 }
```

**The trade-off:**

| | XRD (CEL) | Composition (clamp) |
|---|---|---|
| **When it fires** | At `kubectl apply` — instant | On reconcile, after acceptance |
| **Error quality** | Excellent: names the rule, rejects the object | None — silently changes the value |
| **What it catches** | Only what the expression covers | Every path to that field |
| **Developer experience** | Clear, actionable | Confusing: "I asked for 1, I got 30" |

**Use the XRD for anything a human types.** Rejecting bad input with a clear message
is always better than silently correcting it — a developer who asked for 1 day and got
30 will file a bug, and they'd be right to.

**Use the composition clamp as a backstop**, for values that arrive from somewhere
other than a human (another XR, an EnvironmentConfig, a default) where no useful error
message could be shown anyway. Defence in depth: do both, and make the schema the one
that talks to people.

### 4. Versioning the API

```yaml
versions:
  - name: v1alpha1
    served: true
    referenceable: true          # only ONE version may be referenceable
    schema: { ... retentionDays: {type: integer} ... }
  - name: v1beta1
    served: true
    referenceable: false
    schema: { ... retention: {type: object, properties: {days: {type: integer}}} ... }
```

```bash
kubectl apply -f xbucket-v2-xrd.yaml
kubectl get xbucket scratch-data -n team-payments -o yaml | grep apiVersion
kubectl get xbucket.v1beta1.platform.acme.io scratch-data -n team-payments -o yaml
```

**What you observe:** existing XRs still work and are readable as `v1beta1` — but the
`retention.days` field is **empty**. The stored object has `retentionDays: 7`, and
nothing translates it.

**Why:** Kubernetes serves multiple CRD versions from one stored representation, and
converting between them requires a **conversion webhook**. Without one, the API server
does a no-op conversion: it relabels the `apiVersion` and hands you the same fields.
Renamed or restructured fields simply vanish.

To do this properly you need `spec.conversion.strategy: Webhook` on the generated CRD,
plus a webhook server implementing the translation — a real Go service you build,
deploy, and give a TLS certificate.

**Why Crossplane versioning is harder than CRD versioning:**

1. **`referenceable: true` may only be set on one version.** That's the version
   Compositions bind to via `compositeTypeRef`. So even with two served versions, every
   Composition targets one of them.
2. **Compositions are versioned independently** of the XRD, so a v1beta1 XR and a
   v1alpha1-targeting Composition must still be reconciled together.
3. **Existing XRs are live infrastructure.** A breaking API change on a Deployment is
   annoying; on an XRD it can mean recomposing resources under a running database.

**What teams actually do:** avoid breaking changes. Add optional fields with
defaults, never rename, and if you truly must break, ship a *new kind*
(`XBucketV2`) and migrate consumers deliberately. It's less elegant and far safer.

### 5. Stretch — the migration, and why selection is dangerous

```yaml
apiVersion: apiextensions.crossplane.io/v1
kind: Composition
metadata:
  name: xstaticsite-gcp
  labels: { provider: gcp }
spec:
  compositeTypeRef:
    apiVersion: platform.acme.io/v1alpha1
    kind: XStaticSite
  mode: Pipeline
  pipeline:
    - step: render
      functionRef: { name: function-patch-and-transform }
      input:
        apiVersion: pt.fn.crossplane.io/v1beta1
        kind: Resources
        resources: []           # composes nothing
    - step: ready
      functionRef: { name: function-auto-ready }
```

```bash
kubectl patch xstaticsite marketing-site -n team-web --type=merge \
  -p '{"spec":{"crossplane":{"compositionSelector":{"matchLabels":{"provider":"gcp"}}}}}'
sleep 60
crossplane trace xstaticsite marketing-site -n team-web
awslocal s3 ls
```
The AWS resources are **deleted**. The new composition says they shouldn't exist, and
Crossplane garbage-collects composed resources that are no longer desired.

**Why this makes composition selection dangerous in GitOps:**

Composition selection looks like configuration — a label, a string, the kind of thing
a Helm value or Kustomize patch naturally templatizes. But **changing it is a
destroy-and-recreate of everything the XR owns.** A typo in a values file, a bad
`kustomize` overlay, or a well-meaning "let's parameterise the provider" refactor can
silently delete production infrastructure, and the git diff will look like a one-word
change.

**What to do about it:**

1. **Pin, don't select, in production.** Use `compositionUpdatePolicy: Manual` and an
   explicit `compositionRevisionRef` (Module 11), so nothing moves without a
   deliberate act.
2. **Never templatize the selector.** Hardcode it per environment; if it must vary,
   vary the whole XR file, so the diff is visible.
3. **Set `deletionPolicy: Orphan`** on stateful composed resources, so even a
   mis-selection can't destroy data.
4. **Admission policy** rejecting changes to `spec.crossplane.compositionSelector` on
   XRs labelled production, so the guardrail is enforced rather than documented.

The general principle, which recurs throughout this course: **in a control plane, a
config change is an action.** Fields that would be harmless settings in a
provisioning tool are live commands here, and they need to be treated as such.
