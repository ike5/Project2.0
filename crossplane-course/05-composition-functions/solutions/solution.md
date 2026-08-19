# Challenge 05 — Reference Solution

Runnable manifests: [`xstaticsite-templated.yaml`](./xstaticsite-templated.yaml),
[`xdatalake-tiered.yaml`](./xdatalake-tiered.yaml),
[`render-test.sh`](./render-test.sh).

---

### 1. XStaticSite, rewritten

See [`xstaticsite-templated.yaml`](./xstaticsite-templated.yaml). The core of it:

```gotemplate
{{- $xr := .observed.composite.resource -}}
{{- $bucket := printf "%s-%s" $xr.metadata.namespace $xr.metadata.name -}}

{{- if $xr.spec.public }}
---
apiVersion: s3.aws.upbound.io/v1beta1
kind: BucketPolicy
metadata:
  annotations:
    {{ setResourceNameAnnotation "policy" }}
spec:
  forProvider:
    region: {{ $xr.spec.region | default "us-east-1" }}
    bucket: {{ $bucket }}
    policy: |
      {
        "Version": "2012-10-17",
        "Statement": [{
          "Sid": "PublicRead",
          "Effect": "Allow",
          "Principal": "*",
          "Action": "s3:GetObject",
          "Resource": "arn:aws:s3:::{{ $bucket }}/*"
        }]
      }
  providerConfigRef:
    name: default
{{- end }}
```

And the access block, readable at a glance:
```gotemplate
blockPublicPolicy: {{ not $xr.spec.public }}
restrictPublicBuckets: {{ not $xr.spec.public }}
blockPublicAcls: true
ignorePublicAcls: true
```

Verify the resource genuinely disappears:
```bash
crossplane render xr-private.yaml xstaticsite-templated.yaml functions.yaml \
  | grep -c 'kind: BucketPolicy'      # 0
crossplane render xr-public.yaml xstaticsite-templated.yaml functions.yaml \
  | grep -c 'kind: BucketPolicy'      # 1
```

**Which would I rather maintain?** The templated one, without hesitation. The
patch-and-transform version required a regexp transform to smuggle a conditional past a
system with no conditionals, and it left a `Deny` policy attached to every private
bucket — a resource that exists for no reason and that a future reader will
misinterpret. The template says `{{ if .spec.public }}` and means exactly that.

> The general rule: when you find yourself using a `map` transform keyed on
> `"true"`/`"false"`, you wanted an `if`. Switch functions.

### 2. Tiered zones

XRD change — zones become objects:
```yaml
zones:
  type: array
  minItems: 1
  maxItems: 10
  items:
    type: object
    properties:
      name: { type: string }
      tier: { type: string, enum: [hot, cold], default: hot }
    required: [name]
```

Template — iterate objects, branch inside the loop:
```gotemplate
{{- range $zone := $xr.spec.zones }}
{{- $retention := 365 }}
{{- if eq $zone.tier "hot" }}{{ $retention = 7 }}{{ end }}
---
apiVersion: s3.aws.upbound.io/v1beta1
kind: Bucket
metadata:
  annotations:
    {{ setResourceNameAnnotation (printf "bucket-%s" $zone.name) }}
    crossplane.io/external-name: {{ printf "%s-%s-%s" $ns $name $zone.name }}
spec:
  forProvider:
    region: {{ $region }}
    tags:
      tier: {{ $zone.tier }}
  providerConfigRef: { name: default }
---
apiVersion: s3.aws.upbound.io/v1beta1
kind: BucketLifecycleConfiguration
metadata:
  annotations:
    {{ setResourceNameAnnotation (printf "lifecycle-%s" $zone.name) }}
spec:
  forProvider:
    region: {{ $region }}
    bucket: {{ printf "%s-%s-%s" $ns $name $zone.name }}
    rule:
      - id: retention
        status: Enabled
        expiration:
          - days: {{ $retention }}
  providerConfigRef: { name: default }
{{- if eq $zone.tier "hot" }}
---
apiVersion: s3.aws.upbound.io/v1beta1
kind: BucketVersioning
metadata:
  annotations:
    {{ setResourceNameAnnotation (printf "versioning-%s" $zone.name) }}
spec:
  forProvider:
    region: {{ $region }}
    bucket: {{ printf "%s-%s-%s" $ns $name $zone.name }}
    versioningConfiguration: { status: Enabled }
  providerConfigRef: { name: default }
{{- end }}
{{- end }}
```

Note `{{ $retention = 7 }}` (assignment to an existing variable) rather than
`{{ $retention := 7 }}` (which would declare a new one scoped to the `if` block and
silently have no effect outside it). That's a genuine Go template gotcha.

Still keyed to `$zone.name`, so reordering the list is safe.

### 3. Computed cost

```gotemplate
{{- $hot := 0 }}{{- $cold := 0 }}
{{- range $z := $xr.spec.zones }}
  {{- if eq $z.tier "hot" }}{{ $hot = add1 $hot }}{{ else }}{{ $cold = add1 $cold }}{{ end }}
{{- end }}
{{- $cost := add (mul $hot 5) $cold }}
{{- if $xr.spec.enableAudit }}{{ $cost = add $cost 10 }}{{ end }}
---
apiVersion: platform.acme.io/v1alpha1
kind: XDataLake
status:
  estimatedMonthlyCost: {{ printf "$%.2f" (float64 $cost) | quote }}
```

**Why this is questionable in production:**

1. **The numbers are hardcoded and will be wrong.** AWS pricing changes, varies by
   region, and depends on actual usage — S3 bills on storage and requests, not per
   bucket. A number that looks authoritative and is wrong is worse than no number.
2. **It's untestable in isolation.** Business logic embedded in a YAML string inside a
   Composition has no unit tests, no type checking, and no code review affordances.
3. **It doesn't belong in a control loop.** This value is recomputed on every
   reconcile, forever, to produce something nobody acts on programmatically.

**Where it should live:** a cost API queried by a dashboard, or AWS Cost Explorer
tags — this composition already tags every bucket with `team` and `datalake`, which is
the *right* mechanism. Tag for attribution; let a cost system do costing.

**The general principle:** templates should shape resources, not encode business
rules. When a template starts doing arithmetic on domain concepts, that's a signal the
logic wants to be a real function (`function-python`, `function-kcl`, or a custom Go
function) where it can be tested — or somewhere else entirely.

### 4. Readiness excluding the audit bucket

Add a patch-and-transform step after the template, setting a readiness policy on the
audit resources:

```yaml
- step: readiness-overrides
  functionRef:
    name: function-patch-and-transform
  input:
    apiVersion: pt.fn.crossplane.io/v1beta1
    kind: Resources
    resources:
      - name: bucket-audit
        readiness:
          policy: None          # never blocks the XR's readiness
      - name: versioning-audit
        readiness:
          policy: None
- step: ready
  functionRef:
    name: function-auto-ready
```

```bash
kubectl get xdatalake warehouse -n team-data
# READY=True even while the audit bucket is still provisioning
```

**When this is a good idea:** the audit bucket is genuinely non-blocking — the data
lake is usable without it, and a slow audit bucket shouldn't hold up an application
waiting on the XR. Same reasoning applies to monitoring dashboards, backup
configurations, and DNS records that aren't on the critical path.

**When it's dangerous:** anything a consumer of the XR actually depends on. If a
Deployment waits for the XR to be `Ready` before starting, and `Ready` doesn't include
the database, the app starts and immediately crashes. Worse, `policy: None` hides
*failures* too — a permanently broken audit bucket will never surface in the XR's
status, so nobody notices for months.

**The rule:** `policy: None` means "I accept that I will never be told if this
breaks." Use it only where that's genuinely true, and add separate monitoring for
those resources (Module 12).

### 5. Stretch — the render test harness

See [`render-test.sh`](./render-test.sh). Usage:

```bash
./render-test.sh
```
```
▶ private site produces no BucketPolicy          ✅
▶ public site produces exactly one BucketPolicy  ✅
▶ 3-zone lake produces 6 resources               ✅
▶ every resource has an external-name             ❌
    3 resources missing crossplane.io/external-name
1 test failed
```

The design points that make this useful in CI:
- **It needs no cluster**, so it runs on a PR in seconds.
- **It asserts on structure**, not exact YAML, so cosmetic changes don't cause false
  failures.
- **It exits non-zero**, so CI fails.

This is genuinely how composition testing works in practice — Module 14 formalises it
with `crossplane validate` for schema conformance alongside these structural
assertions.
