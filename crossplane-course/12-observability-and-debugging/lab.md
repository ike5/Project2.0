# Lab 12 — Five Broken Stacks

**You'll:** diagnose five failures, each with a different root cause, using only the
debugging order — then install Prometheus and write an alert that doesn't cry wolf.
⏱️ ~90 min.

> Prereqs: Modules 04–11.
>
> **Diagnose each stack before opening `solutions/`.** The whole value of this module
> is in the diagnosis, not the answer. Give each one a genuine ten minutes.

---

## Part A — Setup

```bash
cd 12-observability-and-debugging
kubectl create ns debug
```

For each stack: apply it, diagnose it, write down your conclusion, **then** check
`solutions/solution.md`.

---

## Stack 1 — "Nothing happens"

```bash
kubectl apply -f manifests/broken/01-no-composition.yaml
sleep 30
kubectl get xbrokenone -n debug
```
✅ Expected: the XR exists and is not ready.

**Diagnose it:**
```bash
./manifests/triage.sh xbrokenone stack-one -n debug
```

Questions to answer before moving on:
- Which of the four layers is broken?
- How many composed resources exist?
- What does the XR's condition message say?

<details><summary>Hint (try for ten minutes first)</summary>

Compare the XRD's `versions[0].name` with the Composition's
`compositeTypeRef.apiVersion`. Look very carefully.
</details>

---

## Stack 2 — "Green, but the tag is missing"

```bash
kubectl apply -f manifests/broken/02-silent-empty-field.yaml
sleep 40
kubectl get xbrokentwo -n debug
crossplane trace xbrokentwo stack-two -n debug
```
✅ Expected: **everything is `True`**. The stack is entirely healthy.

But:
```bash
kubectl get bucket -o json | jq -r '.items[]
  | select(.metadata.name | startswith("stack-two"))
  | {name: .metadata.name, tags: .spec.forProvider.tags}'
```
✅ Expected: `tags` is `null`. The XR asked for `environment: staging`.

**Diagnose it.** There is no error anywhere — that's the point.

<details><summary>Hint</summary>

Read the patch's `fromFieldPath` and compare it with the XRD's actual schema.
Then look up what a patch does when `fromFieldPath` doesn't exist, and what
`policy.fromFieldPath: Required` would have done.
</details>

---

## Stack 3 — "Nothing is created at all"

```bash
kubectl apply -f manifests/broken/03-deadlock.yaml
sleep 30
kubectl get xbrokenthree -n debug
crossplane trace xbrokenthree stack-three -n debug
```
✅ Expected: **zero composed resources** — not even the one with no dependencies.

```bash
kubectl describe xbrokenthree stack-three -n debug | tail -12
```

**Diagnose it.** Why is the *independent* resource missing too?

<details><summary>Hint</summary>

A composition renders as a unit. If the render fails, how much of it gets applied?
Now ask what `.observed.resources.primary` contains on the very first reconcile.
</details>

---

## Stack 4 — "Everything unsynced"

```bash
kubectl apply -f manifests/broken/04-bad-provider-config.yaml
sleep 40
crossplane trace xbrokenfour stack-four -n debug
```
✅ Expected: the resource **exists** as a Kubernetes object but is `SYNCED=False`.

**Diagnose it** — and note this signature is different from Stack 3: the composition
rendered fine, so the fault is *below* it.

```bash
./manifests/triage.sh xbrokenfour stack-four -n debug
```

<details><summary>Hint</summary>

Read the `Synced` message, then find which ProviderConfig this resource uses and
compare its endpoint with your working one.
</details>

---

## Stack 5 — "Everything is green and nothing works"

This is the hardest and most realistic one.

```bash
kubectl apply -f manifests/broken/05-green-but-wrong.yaml
sleep 40
crossplane trace xbrokenfive stack-five -n debug
```
✅ Expected: **completely healthy.** Every resource `Synced=True Ready=True`.

Now check whether it actually did the job:
```bash
# What was the app told to use?
kubectl get xbrokenfive stack-five -n debug -o jsonpath='{.status.bucketName}'; echo

# What buckets exist?
awslocal s3 ls | grep broken-five

# Is the "private" bucket actually private?
awslocal s3api get-public-access-block --bucket broken-five-stack-five 2>&1 | head -3
```
✅ Expected: three separate problems, none of which Crossplane reports.

**Diagnose all three.** Then answer the question that matters:

> **Why did no monitoring catch this, and what kind of check would have?**

<details><summary>Hint</summary>

Compare three strings: the bucket's external name, the name in the public access
block's `bucket` field, and the name in `status.bucketName`. They should all be the
same string. Count how many distinct values you find.
</details>

---

## Part B — Debrief: the signatures

You've now seen all five signatures from the README table. Match them up:

| Stack | Signature | Layer |
|-------|-----------|-------|
| 1 | XR exists, no composed resources | 1 — the XR |
| 2 | Green, but a field is silently empty | 2 — the composition |
| 3 | Render error, **nothing** created | 2 — the composition |
| 4 | Resources exist, all `SYNCED=False` | 3 — the provider |
| 5 | **Everything green, system broken** | 4 — reality vs. intent |

**The most valuable one is 5.** A green control plane and a broken system means you
declared the wrong thing, and no amount of `kubectl describe` will show you what you
failed to write.

## Part C — Install Prometheus

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update prometheus-community
helm upgrade --install prometheus prometheus-community/kube-prometheus-stack \
  -n monitoring --create-namespace \
  -f manifests/prometheus-values.yaml --wait --timeout 10m
```
✅ Expected: pods running in `monitoring`. This takes a few minutes on kind.

```bash
kubectl apply -f manifests/servicemonitor.yaml
kubectl apply -f manifests/alerts.yaml
```

Check Crossplane's metrics directly:
```bash
kubectl port-forward -n crossplane-system deploy/crossplane 8080:8080 &
sleep 3
curl -s localhost:8080/metrics | grep -E '^crossplane_' | head -10
kill %1
```
✅ Expected: `crossplane_managed_resource_*` metrics.

## Part D — Write an alert that doesn't cry wolf

Open Prometheus:
```bash
kubectl port-forward -n monitoring svc/prometheus-kube-prometheus-prometheus 9090:9090 &
```
Visit <http://localhost:9090>.

**First, the bad alert.** Run this query:
```promql
crossplane_managed_resource_ready == 0
```
✅ Expected: it matches resources — including ones that are simply still being
created.

Prove it fires on healthy behaviour:
```bash
kubectl apply -f - <<'YAML'
apiVersion: s3.aws.upbound.io/v1beta1
kind: Bucket
metadata: { name: perfectly-normal }
spec:
  forProvider: { region: us-east-1 }
  providerConfigRef: { name: default }
YAML
```
Refresh the query immediately. The brand-new, perfectly healthy bucket **matches**.

> **An alert on this fires every time anyone creates anything.** Within a week it's
> muted, and then it never helps anyone again. This is how monitoring dies.

**Now the good alert:**
```promql
min_over_time(crossplane_managed_resource_ready[1h]) == 0
```
✅ Expected: the new bucket does **not** match — it was ready within the hour.

But the genuinely broken Stack 4 resource does, once an hour has passed.

```bash
kubectl delete bucket perfectly-normal
kill %1
```

> **Alert on failure to converge, not on not-yet-converged.** The system is *designed*
> to spend time in the unsynced state. Duration is the only thing that distinguishes
> a slow convergence from a stuck one, and picking that threshold is the whole design.
> Choose one longer than your slowest legitimate operation.

## Part E — Clean up

```bash
kubectl delete -f manifests/broken/ --ignore-not-found
kubectl delete ns debug
sleep 30
kubectl get managed
# Optional — frees a lot of laptop RAM:
# helm uninstall prometheus -n monitoring
```

---

## What you learned
- **`crossplane trace` first**, then the condition message, then events, then logs.
- Five signatures, each pointing at a different layer.
- A patch with a wrong `fromFieldPath` fails **silently**. `policy: Required` turns
  that into a loud error — use it while developing.
- A failed render creates **nothing**, including resources with no dependencies.
- `SYNCED=False` on everything at once means credentials, endpoint, or a provider
  change.
- **Green control plane + broken system = you declared the wrong thing.** Stop
  reading logs and compare rendered output against intent.
- **Alert on duration, not state.** An alert that fires on healthy behaviour gets
  muted and then protects nothing.

➡️ **[challenge.md](./challenge.md)** then [Module 13](../13-security-and-multitenancy/).
