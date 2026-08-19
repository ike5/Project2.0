# Lab 05 — Loops, Conditionals, and a 3-Second Feedback Loop

**You'll:** develop a composition entirely offline, use loops and conditionals, mix
two functions in one pipeline, and cause the nil-lookup deadlock on purpose.
⏱️ ~80 min.

> Prereqs: Module 04. Docker must be running — `crossplane render` executes functions
> as local containers.

---

## Part A — Install the functions

```bash
cd 05-composition-functions
kubectl apply -f manifests/functions.yaml
kubectl get functions -w        # Ctrl-C when all three are HEALTHY
```
✅ Expected: three functions, all `INSTALLED=True HEALTHY=True`.

## Part B — Render offline, before touching the cluster

This is the habit worth building. Develop first, apply later.

```bash
cd manifests/render
crossplane render xr.yaml ../composition-templated.yaml functions.yaml
```
✅ Expected (after a first-run image pull): a stream of YAML documents — 3 buckets, 3
lifecycle configurations, an audit bucket, and audit versioning.

```bash
crossplane render xr.yaml ../composition-templated.yaml functions.yaml \
  | grep -c '^kind:'
```
✅ Expected: `8`.

**Now feel the loop.** Edit `xr.yaml` and remove one zone:
```bash
sed -i.bak '/us-east-1c/d' xr.yaml
crossplane render xr.yaml ../composition-templated.yaml functions.yaml | grep -c '^kind:'
```
✅ Expected: `6` — two fewer resources, computed in about three seconds.

Turn the audit bucket off:
```bash
sed -i.bak 's/enableAudit: true/enableAudit: false/' xr.yaml
crossplane render xr.yaml ../composition-templated.yaml functions.yaml | grep -c '^kind:'
```
✅ Expected: `4` — the conditional resources are **gone entirely**, not merely
configured differently. That's the thing patch-and-transform could not do.

Restore the file:
```bash
mv xr.yaml.bak xr.yaml 2>/dev/null; sed -i 's/enableAudit: false/enableAudit: true/' xr.yaml
crossplane render xr.yaml ../composition-templated.yaml functions.yaml | grep -c '^kind:'
```
✅ Expected: back to `8`.

> **Compare the timings.** Applying to a cluster and waiting for AWS is ~3 minutes per
> iteration. That was ~3 seconds. Over an afternoon of composition development this is
> the difference between finishing and giving up.

## Part C — Read the template

```bash
cd ..
sed -n '/render-buckets/,/ready/p' composition-templated.yaml | head -60
```

Find these three mechanics:

1. **The loop** — `{{- range $i, $zone := $xr.spec.zones }}` … `{{- end }}`
2. **The conditional** — `{{- if $xr.spec.enableAudit }}` … `{{- end }}`
3. **The computed status** — `bucketCount: {{ len $xr.spec.zones }}`

And read the long comment about `setResourceNameAnnotation`. It explains why the name
is keyed to `$zone` and not to the loop index `$i`. **That comment describes a real
data-loss bug**, and Part F makes you reproduce it.

## Part D — Apply it for real

```bash
kubectl create ns team-data
kubectl apply -f xrd.yaml
kubectl apply -f composition-templated.yaml
kubectl apply -f xr-small.yaml
sleep 45
kubectl get xdatalakes -n team-data
```
✅ Expected:
```
NAME        ZONES                        AUDIT   BUCKETS   READY
analytics   ["us-east-1a","us-east-1b"]  false   2         True
```

```bash
crossplane trace xdatalake analytics -n team-data
```
✅ Expected: 4 composed resources — two buckets, two lifecycle configurations.

Now the large one, from the **same composition**:
```bash
kubectl apply -f xr-large.yaml
sleep 60
crossplane trace xdatalake warehouse -n team-data
```
✅ Expected: **10** composed resources.

```bash
awslocal s3 ls
```
✅ Expected: 7 buckets total across both data lakes.

**One composition, two very different outcomes, driven entirely by the developer's
input.** That is what you could not do in Module 04.

Check the computed status:
```bash
kubectl get xdatalake warehouse -n team-data -o jsonpath='{.status}' | jq
```
✅ Expected: `bucketCount: 4`, a `zoneBuckets` array of four names, and `auditBucket`
populated. All computed, none copied.

## Part E — Scale it live

Add a zone to a running data lake:
```bash
kubectl patch xdatalake analytics -n team-data --type=merge \
  -p '{"spec":{"zones":["us-east-1a","us-east-1b","us-east-1c"]}}'
sleep 45
crossplane trace xdatalake analytics -n team-data
```
✅ Expected: 6 resources now. The two existing buckets were **untouched**; only the new
zone's resources were created.

Verify nothing was recreated:
```bash
kubectl get buckets -n team-data -o custom-columns=NAME:.metadata.name,AGE:.metadata.creationTimestamp
```
✅ Expected: the original two buckets have older timestamps than the new one.

## Part F — Break it: the unstable name bug

Now reproduce the bug the template comment warns about. Make a copy keyed to the loop
**index** instead of the zone name:

```bash
sed 's/bucket-%s" $zone/bucket-%d" $i/; s/lifecycle-%s" $zone/lifecycle-%d" $i/; s/name: xdatalake-templated/name: xdatalake-unstable/' \
  composition-templated.yaml > /tmp/unstable.yaml
grep -n 'setResourceNameAnnotation' /tmp/unstable.yaml
```
✅ Expected: names now use `%d` and `$i`.

Render with three zones, then with the **middle one removed**:
```bash
cd render
crossplane render xr.yaml /tmp/unstable.yaml functions.yaml \
  | grep 'crossplane.io/external-name' > /tmp/before.txt
sed -i.bak '/us-east-1b/d' xr.yaml
crossplane render xr.yaml /tmp/unstable.yaml functions.yaml \
  | grep 'crossplane.io/external-name' > /tmp/after.txt
diff /tmp/before.txt /tmp/after.txt
```

Look at what happened to the resource **named** `bucket-1`: before the edit it pointed
at the `us-east-1b` bucket; after, the same name points at `us-east-1c`.

**Crossplane would interpret that as "the resource called `bucket-1` should now be a
different bucket"** — so it deletes the `us-east-1b` bucket and creates a new one.
Removing one zone from the middle of the list destroys every bucket after it.

Now confirm the correct version is safe:
```bash
crossplane render xr.yaml ../composition-templated.yaml functions.yaml \
  | grep 'crossplane.io/external-name'
mv xr.yaml.bak xr.yaml
```
✅ Expected: each remaining bucket keeps the name it had. Only the removed zone's
resources disappear.

> **This is the single most dangerous mistake in Go-templated compositions.** The
> resource name annotation is an *identity*, not a label. Key it to something
> intrinsic to the resource — never to a position in a list.

## Part G — Mix two functions

```bash
cd ..
kubectl apply -f composition-hybrid.yaml
kubectl patch xdatalake analytics -n team-data --type=merge \
  -p '{"spec":{"crossplane":{"compositionRef":{"name":"xdatalake-hybrid"}}}}'
sleep 45
kubectl get buckets -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.spec.forProvider.tags}{"\n"}{end}'
```
✅ Expected: buckets carry both the `zone` tag (from the **template** step) and the
`team`/`datalake` tags (from the **patch** step).

Two functions, one pipeline: the template built the variable structure, the patch step
applied a uniform concern across it. **This is the shape most production compositions
end up with.**

## Part H — The nil-lookup deadlock

Guarding cross-resource reads is a rule you'll only remember after breaking it.

```bash
cat > /tmp/deadlock.yaml <<'YAML'
apiVersion: apiextensions.crossplane.io/v1
kind: Composition
metadata:
  name: xdatalake-deadlock
spec:
  compositeTypeRef:
    apiVersion: platform.acme.io/v1alpha1
    kind: XDataLake
  mode: Pipeline
  pipeline:
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
            ---
            apiVersion: s3.aws.upbound.io/v1beta1
            kind: Bucket
            metadata:
              annotations:
                {{ setResourceNameAnnotation "primary" }}
                crossplane.io/external-name: {{ $xr.metadata.name }}-primary
            spec:
              forProvider:
                region: us-east-1
              providerConfigRef:
                name: default
            ---
            apiVersion: s3.aws.upbound.io/v1beta1
            kind: BucketVersioning
            metadata:
              annotations:
                {{ setResourceNameAnnotation "versioning" }}
            spec:
              forProvider:
                region: us-east-1
                # UNGUARDED read of a sibling that does not exist yet:
                bucket: {{ (index .observed.resources "primary").resource.status.atProvider.id }}
                versioningConfiguration:
                  status: Enabled
              providerConfigRef:
                name: default
    - step: ready
      functionRef:
        name: function-auto-ready
YAML
kubectl apply -f /tmp/deadlock.yaml
kubectl apply -f - <<'YAML'
apiVersion: platform.acme.io/v1alpha1
kind: XDataLake
metadata:
  name: deadlocked
  namespace: team-data
spec:
  zones: ["us-east-1a"]
  crossplane:
    compositionRef:
      name: xdatalake-deadlock
YAML
sleep 30
kubectl describe xdatalake deadlocked -n team-data | tail -12
```
✅ Expected: a template execution error — a nil pointer on `.resource`.

**And critically:** `crossplane trace xdatalake deadlocked -n team-data` shows **zero**
composed resources. The render failed entirely, so *nothing* was created — including
the primary bucket that would have made the lookup succeed. **The composition can
never make progress.**

The fix is the guard from the README:
```gotemplate
{{- $primary := index .observed.resources "primary" -}}
{{- if $primary }}
bucket: {{ $primary.resource.status.atProvider.id }}
{{- end }}
```
First reconcile: the block is skipped, the primary bucket is created. Second reconcile:
the primary exists, the lookup succeeds, versioning is configured. **Compositions
converge over several reconciles — write them to tolerate partial state.**

```bash
kubectl delete xdatalake deadlocked -n team-data
kubectl delete composition xdatalake-deadlock
```

## Part I — Clean up

```bash
kubectl delete xdatalake --all -n team-data
sleep 30
awslocal s3 ls
```
✅ Expected: no buckets.

**Leave the XRD, compositions, and functions installed.**

---

## What you learned
- Functions are gRPC programs; the **pipeline** chains them, each seeing the last
  one's output.
- `function-go-templating` provides **loops, conditionals, and computed values** —
  everything patch-and-transform cannot express.
- **`crossplane render` is a 3-second feedback loop** with no cluster. Develop this
  way.
- `setResourceNameAnnotation` is an **identity**. Keying it to a list index causes
  delete-and-recreate when the list changes.
- **Guard every cross-resource read** — an unguarded nil lookup deadlocks the whole
  composition.
- Mixing templating and patching in one pipeline is the normal production shape.

➡️ **[challenge.md](./challenge.md)** then [Module 06](../06-composing-applications/).
