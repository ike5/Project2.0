# Lab 11 — Change a Live Platform Without Breaking It

**You'll:** pin XRs to composition revisions, canary a change, roll it back, discover
the limit of what a rollback can undo, and upgrade a provider. ⏱️ ~70 min.

> Prereqs: Module 10. The `XBucket` XRD from Module 10's package installed.

---

## Part A — Establish a baseline

```bash
cd 11-day-two-operations
kubectl apply -f ../10-reuse-and-packaging/manifests/package/apis/xbucket.yaml
kubectl apply -f manifests/composition-v1.yaml
kubectl get compositionrevisions
```
✅ Expected: **one** revision.
```
NAME                 REVISION   XR-KIND    AGE
xbucket-rev-7f9c2a1  1          XBucket    5s
```

Create three XRs — two "production", one canary:
```bash
kubectl create ns team-payments 2>/dev/null || true
for n in prod-a prod-b canary; do
  kubectl apply -f - <<YAML
apiVersion: platform.acme.io/v1alpha1
kind: XBucket
metadata:
  name: $n
  namespace: team-payments
spec:
  environment: dev
  retentionDays: 7
  crossplane:
    compositionRef:
      name: xbucket-rev
YAML
done
sleep 45
kubectl get xbuckets -n team-payments
```
✅ Expected: three, all `READY=True`.

Record what exists, so you can prove later what survived:
```bash
kubectl get buckets -o custom-columns=\
NAME:.metadata.name,EXTERNAL:.metadata.annotations.crossplane\\.io/external-name,CREATED:.metadata.creationTimestamp \
  | tee /tmp/before.txt
```

## Part B — Watch `Automatic` do its thing

By default nothing is pinned, so a composition change reaches everything instantly.

```bash
kubectl get xbuckets -n team-payments -o custom-columns=\
NAME:.metadata.name,POLICY:.spec.crossplane.compositionUpdatePolicy,REV:.spec.crossplane.compositionRevisionRef.name
```
✅ Expected: `POLICY` is empty (meaning `Automatic`) and each has a revision ref.

Apply v2 and watch all three move together:
```bash
kubectl apply -f manifests/composition-v2.yaml
sleep 45
kubectl get compositionrevisions
kubectl get xbuckets -n team-payments -o custom-columns=\
NAME:.metadata.name,REV:.spec.crossplane.compositionRevisionRef.name
```
✅ Expected: **two** revisions now, and **all three XRs on revision 2**.

```bash
kubectl get managed | grep -c BucketPublicAccessBlock
```
✅ Expected: `3` — every XR gained the new resource, immediately, with no approval.

> **This is the default, and it's usually right** — it's how a security fix reaches
> every team at once. It's also how a mistake does.

## Part C — Pin everything, then roll out deliberately

```bash
kubectl get xbuckets -n team-payments -o name | xargs -I{} kubectl patch {} \
  -n team-payments --type=merge \
  -p '{"spec":{"crossplane":{"compositionUpdatePolicy":"Manual"}}}'

kubectl get xbuckets -n team-payments -o custom-columns=\
NAME:.metadata.name,POLICY:.spec.crossplane.compositionUpdatePolicy,REV:.spec.crossplane.compositionRevisionRef.name
```
✅ Expected: all three `Manual`, all on revision 2.

Run the pre-flight check before changing anything:
```bash
./manifests/preflight.sh xbuckets
```
✅ Expected: all green — everything healthy, nothing on `Automatic`.

## Part D — The canary catches a destructive change

Now apply v3, which changes only the resource **name** annotation:

```bash
diff manifests/composition-v2.yaml manifests/composition-v3-destructive.yaml | head -20
```
✅ Expected: the difference is `setResourceNameAnnotation "bucket"` →
`"s3-bucket"`, plus a tag. **No API field changed.**

```bash
kubectl apply -f manifests/composition-v3-destructive.yaml
kubectl get compositionrevisions
```
✅ Expected: **three** revisions — and because everything is pinned, **no XR moved**.

```bash
kubectl get buckets -o custom-columns=NAME:.metadata.name,CREATED:.metadata.creationTimestamp
diff <(cut -d' ' -f1 /tmp/before.txt) <(kubectl get buckets -o name | cut -d/ -f2) >/dev/null \
  && echo "✅ nothing changed yet"
```

**Move only the canary:**
```bash
REV3=$(kubectl get compositionrevisions -o json \
  | jq -r '.items[] | select(.spec.revision==3) | .metadata.name')
echo "revision 3 is $REV3"

kubectl patch xbucket canary -n team-payments --type=merge \
  -p "{\"spec\":{\"crossplane\":{\"compositionRevisionRef\":{\"name\":\"$REV3\"}}}}"
sleep 45
crossplane trace xbucket canary -n team-payments
```
✅ Expected: the canary's bucket now has a **new object name and a new creation
timestamp** — it was deleted and recreated. `prod-a` and `prod-b` are untouched.

```bash
kubectl get buckets -o custom-columns=\
NAME:.metadata.name,EXTERNAL:.metadata.annotations.crossplane\\.io/external-name,CREATED:.metadata.creationTimestamp
```

🎉 **The canary did its job.** In production this would have been one team's bucket
instead of every team's.

## Part E — Roll back, and find the limit

```bash
REV2=$(kubectl get compositionrevisions -o json \
  | jq -r '.items[] | select(.spec.revision==2) | .metadata.name')
kubectl patch xbucket canary -n team-payments --type=merge \
  -p "{\"spec\":{\"crossplane\":{\"compositionRevisionRef\":{\"name\":\"$REV2\"}}}}"
sleep 45
kubectl get buckets -o custom-columns=NAME:.metadata.name,CREATED:.metadata.creationTimestamp
```
✅ Expected: the canary is back on the v2 shape — the resource is named `bucket`
again.

**Now the important observation.** Look at the creation timestamp:

The rollback created *another* new bucket object. The original one from Part A is gone
forever, and so is anything that was in it.

> **Rolling back a composition does not roll back what it did.** Revisions protect
> you from *propagating* a bad change to the other 99 XRs. They do not undo a
> destructive action that already ran on the canary. That is precisely why you canary
> on something you can afford to lose.

Confirm production was never affected:
```bash
grep -E 'prod-a|prod-b' /tmp/before.txt
kubectl get buckets -o custom-columns=NAME:.metadata.name,CREATED:.metadata.creationTimestamp | grep prod
```
✅ Expected: identical creation timestamps. **Untouched throughout.**

## Part F — The pre-flight check catches it before the canary does

Better still: catch it before applying anything at all.

```bash
cat > /tmp/sample-xr.yaml <<'YAML'
apiVersion: platform.acme.io/v1alpha1
kind: XBucket
metadata: { name: sample, namespace: team-payments }
spec: { environment: dev, retentionDays: 7 }
YAML

./manifests/preflight.sh xbuckets \
  manifests/composition-v2.yaml \
  manifests/composition-v3-destructive.yaml \
  /tmp/sample-xr.yaml \
  ../06-composing-applications/manifests/render/functions.yaml
```
✅ Expected: a rendered diff, then:
```
── Resource-name check (the destructive one) ──
🚨 COMPOSED RESOURCE NAMES CHANGED.
   Applying this WILL DELETE AND RECREATE infrastructure for every
   existing XR. On a database, that is your data.
```

**That check takes three seconds and needs no cluster.** Put it in CI (Module 14) and
this class of mistake never reaches a review, let alone production.

Compare with a safe change:
```bash
./manifests/preflight.sh xbuckets \
  manifests/composition-v1.yaml \
  manifests/composition-v2.yaml \
  /tmp/sample-xr.yaml \
  ../06-composing-applications/manifests/render/functions.yaml
```
✅ Expected: a diff showing the added resource, and
`✅ Composed resource names are unchanged.`

## Part G — Finish the rollout

Move production to v2 in batches, then return to `Automatic`:
```bash
for n in prod-a prod-b; do
  kubectl patch xbucket $n -n team-payments --type=merge \
    -p "{\"spec\":{\"crossplane\":{\"compositionRevisionRef\":{\"name\":\"$REV2\"}}}}"
  sleep 20
  kubectl get xbucket $n -n team-payments
done

kubectl get xbuckets -n team-payments -o name | xargs -I{} kubectl patch {} \
  -n team-payments --type=merge \
  -p '{"spec":{"crossplane":{"compositionUpdatePolicy":"Automatic","compositionRevisionRef":null}}}'
```

> **Don't leave everything pinned forever.** Pinned XRs stop receiving fixes, and a
> year later you have XRs on eleven different revisions and no idea which are safe.
> Pin for a rollout; unpin when you're done.

## Part H — Upgrade a provider

```bash
kubectl get providerrevisions
kubectl patch provider provider-aws-s3 --type=merge \
  -p '{"spec":{"package":"xpkg.upbound.io/upbound/provider-aws-s3:v1.22.0"}}'
kubectl get providerrevisions -w      # Ctrl-C when the new one is ACTIVE
```
✅ Expected: **two** provider revisions, the new one `ACTIVE=True`, the old one
`ACTIVE=False` but still present.

**Immediately check for a drift wave** — the thing to fear from a provider upgrade:
```bash
kubectl get managed | grep -v "True *True" || echo "✅ nothing went unsynced"
```

Roll back with the same patch in reverse:
```bash
kubectl patch provider provider-aws-s3 --type=merge \
  -p '{"spec":{"package":"xpkg.upbound.io/upbound/provider-aws-s3:v1.21.0"}}'
```

> **The provider upgrade failure mode:** a new version changes how a field is
> compared, so every existing resource suddenly looks drifted and gets updated. On
> buckets that's noise. On RDS instances it's an unscheduled maintenance window.
> Always upgrade in a non-production cluster first and watch `kubectl get managed`.

## Part I — Operations (read, mostly)

```bash
cat manifests/cronoperation.yaml
kubectl apply -f manifests/cronoperation.yaml 2>&1 | head -3
```
Likely: `no matches for kind "CronOperation"`. **That's expected** — Operations are
alpha and off by default.

To try them:
```bash
kubectl -n crossplane-system patch deploy crossplane --type=json -p='[
  {"op":"add","path":"/spec/template/spec/containers/0/args/-","value":"--enable-operations"}
]'
kubectl -n crossplane-system rollout status deploy/crossplane
sleep 20
kubectl apply -f manifests/cronoperation.yaml
kubectl get cronoperations,operations
```

Now read the boring alternative:
```bash
cat manifests/cronjob-alternative.yaml
```

> **Use the CronJob today.** Operations are genuinely promising — running day-2 work
> through the same function pipelines as your compositions is elegant — but alpha APIs
> change, and a backup job is the worst possible place to discover that. A CronJob
> with a tightly scoped ServiceAccount is unexciting and dependable.

## Part J — Clean up

```bash
kubectl delete xbucket --all -n team-payments
kubectl delete cronoperation,operation --all 2>/dev/null
sleep 45
kubectl get managed
```

---

## What you learned
- Every Composition edit creates an immutable **CompositionRevision**.
- `compositionUpdatePolicy: Automatic` (the default) applies changes to every XR
  instantly. `Manual` + `compositionRevisionRef` puts a human in the loop.
- **Canary one XR**, verify, then roll out in batches. Rollback is a one-line patch.
- **A rollback does not undo what already ran.** Revisions stop propagation, not
  destruction.
- The **pre-flight resource-name check** catches the destructive-rename class of bug
  in three seconds, with no cluster.
- Provider upgrades create revisions too, and the failure mode to watch for is a wave
  of unexpected drift.
- `Operation`/`CronOperation` are alpha; use a `CronJob` for real scheduled work.

➡️ **[challenge.md](./challenge.md)** then [Module 12](../12-observability-and-debugging/).
