# Composition Functions Cheatsheet

In Crossplane v2, **functions are the only way compositions work**. Every Composition
has `mode: Pipeline` and a list of steps.

---

## The skeleton every composition has

```yaml
apiVersion: apiextensions.crossplane.io/v1
kind: Composition
metadata:
  name: xdatabase-aws
spec:
  compositeTypeRef:                     # MUST match your XRD exactly
    apiVersion: platform.example.org/v1alpha1
    kind: XDatabase
  mode: Pipeline
  pipeline:
    - step: render-resources
      functionRef:
        name: function-patch-and-transform
      input:
        apiVersion: pt.fn.crossplane.io/v1beta1
        kind: Resources
        resources: [...]
    - step: ready
      functionRef:
        name: function-auto-ready       # nearly always the last step
```

## The functions worth knowing

| Function | Use it when | Package |
|----------|-------------|---------|
| `function-patch-and-transform` | A fixed set of resources with values copied in | `crossplane-contrib/function-patch-and-transform` |
| `function-go-templating` | You need loops or conditionals | `crossplane-contrib/function-go-templating` |
| `function-auto-ready` | Always — as the final step | `crossplane-contrib/function-auto-ready` |
| `function-environment-configs` | Pulling shared values (account IDs, VPC IDs) into context | `crossplane-contrib/function-environment-configs` |
| `function-extra-resources` | The composition must read other cluster objects | `crossplane-contrib/function-extra-resources` |
| `function-sequencer` | A cloud API can't tolerate parallel creation | `crossplane-contrib/function-sequencer` |
| `function-cel-filter` | Conditionally drop resources using CEL | `crossplane-contrib/function-cel-filter` |

**Rule of thumb:** reach for patch-and-transform first. Switch to Go templating the
moment you catch yourself wanting a `for` loop. Mixing both in one pipeline is normal
and idiomatic — template the variable parts, then patch the fixed ones.

---

## function-patch-and-transform

```yaml
input:
  apiVersion: pt.fn.crossplane.io/v1beta1
  kind: Resources
  resources:
    - name: bucket                       # unique within the composition
      base:
        apiVersion: s3.aws.upbound.io/v1beta1
        kind: Bucket
        spec:
          forProvider:
            region: us-east-1
      patches:
        - type: FromCompositeFieldPath
          fromFieldPath: spec.region
          toFieldPath: spec.forProvider.region
        - type: ToCompositeFieldPath
          fromFieldPath: status.atProvider.arn
          toFieldPath: status.bucketArn
```

### Patch types

| Type | Direction | Use |
|------|-----------|-----|
| `FromCompositeFieldPath` | XR → composed | The workhorse. User input into a resource. |
| `ToCompositeFieldPath` | composed → XR | Surface results (ARNs, endpoints) on the XR status. |
| `CombineFromComposite` | several XR fields → one | Build a name from region + env. |
| `PatchSet` | reusable | Define once under `patchSets`, reference by name. |

### Transforms

```yaml
patches:
  - type: FromCompositeFieldPath
    fromFieldPath: spec.name
    toFieldPath: spec.forProvider.bucketName
    transforms:
      # string: format, upper, lower, trimPrefix, trimSuffix, replace, regexp
      - type: string
        string: { type: Format, fmt: "%s-data-bucket" }

      # map: look up a value
      - type: map
        map: { dev: t3.micro, staging: t3.small, prod: db.r6g.large }

      # match: like map, but with a fallback and regex support
      - type: match
        match:
          patterns:
            - type: literal
              literal: prod
              result: 100
          fallbackValue: 20

      # math: multiply / clampMin / clampMax
      - type: math
        math: { type: Multiply, multiply: 2 }

      # convert: change type
      - type: convert
        convert: { toType: string }
```

### The policy field — turn silent bugs loud

```yaml
- type: FromCompositeFieldPath
  fromFieldPath: spec.parameters.size
  toFieldPath: spec.forProvider.instanceClass
  policy:
    fromFieldPath: Required      # error instead of silently skipping
```

> **Default behaviour is `Optional`:** if `fromFieldPath` doesn't exist, the patch is
> silently skipped and you get an empty field with no error. Set `Required` on
> anything that genuinely must be present. This single line prevents more debugging
> pain than any other in this cheatsheet.

### Connection details

```yaml
- name: db
  base: { ... }
  connectionDetails:
    - type: FromConnectionSecretKey
      name: password
      fromConnectionSecretKey: attribute.password
    - type: FromFieldPath
      name: host
      fromFieldPath: status.atProvider.endpoint
    - type: FromValue
      name: port
      value: "5432"
```

### Readiness

```yaml
- name: bucket
  base: { ... }
  readiness:
    policy: MatchCondition          # default: MatchCondition on Ready
    matchCondition:
      type: Ready
      status: "True"
    # other policies: NonEmpty, MatchString, MatchInteger, MatchTrue, MatchFalse, None
```

---

## function-go-templating

Use it for loops, conditionals, and computed values.

```yaml
- step: render
  functionRef:
    name: function-go-templating
  input:
    apiVersion: gotemplating.fn.crossplane.io/v1beta1
    kind: GoTemplate
    source: Inline
    inline:
      template: |
        {{- $xr := .observed.composite.resource -}}
        {{- range $i, $cidr := $xr.spec.subnetCidrs }}
        ---
        apiVersion: ec2.aws.upbound.io/v1beta1
        kind: Subnet
        metadata:
          annotations:
            {{ setResourceNameAnnotation (printf "subnet-%d" $i) }}
        spec:
          forProvider:
            region: {{ $xr.spec.region }}
            cidrBlock: {{ $cidr }}
        {{- end }}
```

### Context you can read

| Path | Contains |
|------|----------|
| `.observed.composite.resource` | The XR as applied (its `spec`, `metadata`) |
| `.observed.resources` | Composed resources as they currently exist, keyed by name |
| `.observed.resources.<name>.resource.status.atProvider` | Live cloud state — ARNs, IDs |
| `.desired.composite.resource` | The XR as previous pipeline steps left it |
| `.context` | Data passed between steps (EnvironmentConfigs land here) |

### Essential helpers

```gotemplate
{{ setResourceNameAnnotation "my-name" }}   {{/* REQUIRED on every resource */}}
{{ toYaml .observed.composite.resource.spec | nindent 4 }}
{{ getResourceCondition "Ready" .observed.resources.vpc }}
{{ include "template-name" . }}
```
Sprig functions are available too: `default`, `required`, `b64enc`, `sha256sum`,
`randAlphaNum`, `dig`.

> **Gotcha:** every rendered resource needs
> `{{ setResourceNameAnnotation "..." }}` in its metadata annotations, and the name
> must be unique and *stable*. If it changes between renders, Crossplane deletes the
> old resource and creates a new one — which on an RDS instance means destroying your
> database. Never derive it from something that varies.

### Reading a value another resource produced

```gotemplate
{{- $vpc := index .observed.resources "vpc" -}}
{{- if $vpc }}
vpcId: {{ $vpc.resource.status.atProvider.id }}
{{- end }}
```
The `if` matters: on the first reconcile the VPC doesn't exist yet and the lookup is
nil. Guard every cross-resource read.

---

## EnvironmentConfigs

```yaml
- step: environment
  functionRef:
    name: function-environment-configs
  input:
    apiVersion: environmentconfigs.fn.crossplane.io/v1beta1
    kind: Input
    spec:
      environmentConfigs:
        - type: Reference
          ref:
            name: aws-account-prod
```
Then read it in later steps at `.context["apiextensions.crossplane.io/environment"]`.

---

## Testing locally — the fastest loop in Crossplane

```bash
crossplane render xr.yaml composition.yaml functions.yaml
```

`functions.yaml`:
```yaml
apiVersion: pkg.crossplane.io/v1
kind: Function
metadata:
  name: function-patch-and-transform
  annotations:
    render.crossplane.io/runtime: Docker
spec:
  package: xpkg.upbound.io/crossplane-contrib/function-patch-and-transform:v0.8.2
```

Validate the result against real schemas:
```bash
crossplane render xr.yaml composition.yaml functions.yaml \
  | crossplane validate crds/ -
```

**Write your compositions this way.** Editing YAML, applying it to a cluster, and
waiting for a cloud API is a 3-minute feedback loop. `crossplane render` is a
3-second one.

---

## Pipeline ordering rules

1. Steps run **in order**, each seeing the previous step's desired state.
2. A later step can modify or delete what an earlier one produced.
3. `function-auto-ready` goes **last** — it needs to see every resource.
4. `function-environment-configs` goes **first** — later steps read its context.
5. Composed resources are created **in parallel** regardless of step order. If you
   need creation ordering, use `function-sequencer` or a `Usage` object.
