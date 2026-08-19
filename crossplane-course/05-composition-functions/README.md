# Module 05 — Composition Functions

**Goal:** move beyond static patching to compositions that loop, branch, and compute —
and get a 3-second feedback loop instead of a 3-minute one.

⏱️ ~3 hours · 🎯 Prereq: Module 04.

---

## 1. Where Module 04 hurt

Your `XBucket` composition worked, but if you did the challenge you hit walls:

- **You can't loop.** "One subnet per availability zone" is impossible — you'd have to
  write out three near-identical resource blocks and patch each individually.
- **You can't branch.** Patch-and-transform has no way to say "only create this
  resource if `spec.public` is true." The challenge solution had to render a bucket
  policy *always* and flip it between Allow and Deny.
- **You can't compute.** Anything beyond map/format/math means chaining transforms
  into something unreadable — like that regexp doing a template's job.

These aren't gaps in your knowledge. They're the boundary of what patch-and-transform
is *for*. Crossplane's answer is to let you plug in a different function.

## 2. What a function actually is

A composition function is **a program that takes desired state and returns desired
state.**

```
                 RunFunctionRequest (gRPC)
                 ┌──────────────────────┐
Crossplane ─────►│ observed: what exists │─────► Function pod
                 │ desired:  what prior  │
                 │           steps want  │
                 │ input:    your config │
                 └──────────────────────┘
                                                        │
                 ┌──────────────────────┐               │
Crossplane ◄─────│ desired: the resources│◄──────────────┘
                 │          that should  │
                 │          exist        │
                 └──────────────────────┘
                 RunFunctionResponse
```

Because it's a gRPC contract rather than a config format, a function can be written in
any language. `function-patch-and-transform` is just one implementation — one that
happens to interpret a declarative config. Others run Go templates, KCL, Python, or
arbitrary Go code you wrote yourself.

## 3. The pipeline

Steps run in order, each receiving the previous step's desired state:

```yaml
pipeline:
  - step: load-environment      # 1. pull in shared config
    functionRef: { name: function-environment-configs }
  - step: render-dynamic        # 2. loops and conditionals
    functionRef: { name: function-go-templating }
  - step: patch-common          # 3. apply consistent tags to everything
    functionRef: { name: function-patch-and-transform }
  - step: ready                 # 4. decide when the XR is Ready
    functionRef: { name: function-auto-ready }
```

**Mixing functions in one pipeline is normal and idiomatic.** Template the parts that
vary; patch the parts that are uniform. You don't pick one function for a composition
— you compose them.

Two ordering rules worth memorising:
- `function-environment-configs` goes **first** (later steps read its context).
- `function-auto-ready` goes **last** (it must see every resource).

> **Step order is not creation order.** Composed resources are created in parallel
> regardless of which step produced them. If a cloud API genuinely requires ordering,
> use `function-sequencer` or a `Usage` object (Module 10).

## 4. function-go-templating

The workhorse for anything dynamic. You write a Go template that emits YAML:

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
        {{- range $i, $az := $xr.spec.availabilityZones }}
        ---
        apiVersion: ec2.aws.upbound.io/v1beta1
        kind: Subnet
        metadata:
          annotations:
            {{ setResourceNameAnnotation (printf "subnet-%d" $i) }}
        spec:
          forProvider:
            region: {{ $xr.spec.region }}
            availabilityZone: {{ $az }}
        {{- end }}
```

Three subnets, or seven, from one block. That's the unlock.

### The context you can read

| Path | Contains |
|------|----------|
| `.observed.composite.resource` | The XR as applied — its `spec`, `metadata` |
| `.observed.resources` | Composed resources as they currently exist, by name |
| `.observed.resources.<n>.resource.status.atProvider` | **Live cloud state** — ARNs, IDs |
| `.desired.composite.resource` | The XR as earlier steps left it |
| `.context` | Data passed between steps |

### Two rules that will save you hours

**Every resource needs a stable name annotation:**
```gotemplate
{{ setResourceNameAnnotation "bucket" }}
```
This is how Crossplane tracks which rendered resource corresponds to which existing
one. **If the name changes between renders, Crossplane deletes the old resource and
creates a new one.** Derive it from something stable — an index, a fixed string — never
from a timestamp, a random value, or a field the user can edit.

**Guard every cross-resource read:**
```gotemplate
{{- $vpc := index .observed.resources "vpc" -}}
{{- if $vpc }}
vpcId: {{ $vpc.resource.status.atProvider.id }}
{{- end }}
```
On the first reconcile the VPC doesn't exist yet, so the lookup is nil. An unguarded
read fails the whole render, and nothing gets created — including the VPC that would
have unblocked it. This deadlock is a rite of passage; skip it by guarding.

## 5. `crossplane render` — the fastest loop available

You do not need a cluster to develop a composition:

```bash
crossplane render xr.yaml composition.yaml functions.yaml
```

It runs the real functions in Docker and prints exactly what would be created.

| Loop | Time per iteration |
|------|-------------------|
| Edit → apply → wait for AWS → `kubectl describe` | ~3 minutes |
| Edit → `crossplane render` | ~3 seconds |

**Write your compositions with `render`, then apply once it's right.** This single
habit is the difference between composition development being pleasant and being
miserable.

Validate the output against real schemas:
```bash
crossplane render xr.yaml composition.yaml functions.yaml \
  | crossplane validate crds/ -
```

## 6. Choosing a function

| Need | Function |
|------|----------|
| Fixed resources, values copied in | `function-patch-and-transform` |
| Loops, conditionals, computed values | `function-go-templating` |
| Complex logic with real types | `function-kcl` or `function-python` |
| Shared config (account IDs, VPCs) | `function-environment-configs` |
| Read other cluster resources | `function-extra-resources` |
| Force creation ordering | `function-sequencer` |
| Decide XR readiness | `function-auto-ready` |

**Start with patch-and-transform. Switch to templating the moment you want a loop or
an `if`.** Don't reach for templating first — a template that could have been three
patches is harder to read, not easier.

## 7. Readiness

By default `function-auto-ready` marks the XR `Ready` when all composed resources are
`Ready`. Override per-resource when that's wrong:

```yaml
readiness:
  policy: MatchCondition
  matchCondition: { type: Ready, status: "True" }
```

Policies: `MatchCondition` (default), `NonEmpty` (a status field is populated),
`MatchString`, `MatchInteger`, `MatchTrue`/`MatchFalse`, and `None` (never blocks
readiness — for resources whose readiness you don't care about).

---

## Do the lab
Rewrite the Module 04 composition with Go templating, add loops and conditionals,
develop entirely offline with `crossplane render`, and cause the nil-lookup deadlock
on purpose.
👉 **[lab.md](./lab.md)**

Then: 👉 **[challenge.md](./challenge.md)**

## Manifests
- [`functions.yaml`](./manifests/functions.yaml) — all functions this module needs
- [`xrd.yaml`](./manifests/xrd.yaml) — an `XDataLake` API with variable-length inputs
- [`composition-templated.yaml`](./manifests/composition-templated.yaml) — loops and conditionals
- [`composition-hybrid.yaml`](./manifests/composition-hybrid.yaml) — templating + patching together
- [`xr-small.yaml`](./manifests/xr-small.yaml) / [`xr-large.yaml`](./manifests/xr-large.yaml) — instances
- [`render/`](./manifests/render/) — files for offline `crossplane render`

## Key terms
composition function · pipeline · step · gRPC · `function-go-templating` ·
`setResourceNameAnnotation` · `crossplane render` · observed vs desired · readiness policy

**Next →** [Module 06: Composing Applications](../06-composing-applications/)
