# Challenge 12 — Reference Solution

Includes the answers to the five lab stacks. **Diagnose them before reading.**

Runnable files: [`status-report.sh`](./status-report.sh),
[`06-broken-mrap.yaml`](./06-broken-mrap.yaml),
[`consistency-check.sh`](./consistency-check.sh).

---

## The five lab stacks

### Stack 1 — no Composition selected

**Root cause:** the XRD serves `v1alpha1`; the Composition's `compositeTypeRef`
says `v1beta1`.

```bash
kubectl get xrd xbrokenones.debug.acme.io -o jsonpath='{.spec.versions[0].name}'
# v1alpha1
kubectl get composition xbrokenone-aws -o jsonpath='{.spec.compositeTypeRef.apiVersion}'
# debug.acme.io/v1beta1     ← mismatch
```

No Composition matches the XR's type, so Crossplane selects nothing and creates
nothing. **Layer 1.**

**The signature:** an XR with **zero** composed resources and no dramatic error. When
you see that, check `compositeTypeRef` against the XRD's group, version, *and* kind
before anything else. `kubectl describe` on the XR says
`no composition selected` — but it's easy to miss because everything else looks fine.

**Fix:** change the Composition to `debug.acme.io/v1alpha1`.

### Stack 2 — a silently skipped patch

**Root cause:** the patch reads `spec.parameters.environment`; the XRD schema defines
`spec.environment`. There is no `parameters` level.

```yaml
- type: FromCompositeFieldPath
  fromFieldPath: spec.parameters.environment   # does not exist
  toFieldPath: spec.forProvider.tags.environment
```

**Patches default to `policy.fromFieldPath: Optional`**, which means a missing source
path is *silently skipped*. No error, no warning, no event — the tag simply never
gets set, and everything reports healthy.

**Layer 2**, and the nastiest kind: a green system that quietly does less than you
asked.

**Fix — and the habit worth forming:**
```yaml
  policy:
    fromFieldPath: Required
```
Now a missing path fails the render loudly. **Set `Required` on every patch whose
value genuinely matters.** It costs three lines and prevents an entire category of
silent bug. (`spec.parameters.*` is itself a v1 muscle memory — old claim-based
examples nested user input under `parameters`.)

### Stack 3 — the render deadlock

**Root cause:** the template reads
`(index .observed.resources "primary").resource.status.atProvider.id` with no guard.
On the first reconcile `primary` doesn't exist, the lookup is nil, and the template
execution fails.

**Why nothing at all is created:** a composition renders as a **unit**. If the
function returns an error, Crossplane gets no desired state and applies nothing —
including the primary bucket, which had no dependencies and would have succeeded.

So the primary is never created → the lookup never succeeds → **the composition can
never make progress.** It is a genuine deadlock, not a slow convergence.

**Fix:**
```gotemplate
{{- $primary := index .observed.resources "primary" -}}
{{- if $primary }}
bucket: {{ $primary.resource.status.atProvider.id }}
{{- end }}
```
First reconcile: block skipped, primary created. Second: lookup succeeds.

**The principle:** compositions converge over several reconciles. **Write them to
tolerate partial state**, because partial state is the normal case, not an edge case.

### Stack 4 — an unreachable endpoint

**Root cause:** the resource uses a ProviderConfig whose endpoint points at
`moto.wrong-namespace.svc.cluster.local`, which doesn't resolve.

```bash
kubectl get bucket -o json | jq -r '.items[]
  | select(.metadata.name | startswith("stack-four"))
  | .status.conditions[] | select(.type=="Synced") | .message'
# ...dial tcp: lookup moto.wrong-namespace.svc.cluster.local: no such host
```

**Layer 3.** The composition rendered perfectly — the Kubernetes object exists with
exactly the right spec. The provider could not reach the cloud API.

**The signature that distinguishes it from Stack 3:** here the composed resources
**exist**. Stack 3 produced nothing. Resources existing but unsynced always means the
fault is *below* the composition.

**Fix:** point `providerConfigRef` at the working config, or correct the endpoint.

**In production this signature usually means:** an expired credential, a rotated
secret, a NetworkPolicy blocking egress, or a VPC endpoint change. If it hits
*everything at once*, check the credential first.

### Stack 5 — green and wrong (three faults)

Nothing is wrong with Crossplane. The composition faithfully created exactly what it
was told to create. **What it was told was wrong.**

Three distinct name strings where there should be one:

| Where | Value |
|-------|-------|
| The bucket's external name | `broken-five-stack-five` |
| The public access block's `bucket` field | `broken-five-wrong-name` (hardcoded) |
| `status.bucketName`, given to the app | `broken-five-stack-five-data` |

Consequences:
1. **The public access block protects a bucket that doesn't exist.** It applied
   successfully — the emulator doesn't require the bucket to exist — so the real
   bucket has **no public access block at all**. The "private" bucket is not private.
2. **The application is told to use `...-data`**, which doesn't exist. Every call
   fails with `NoSuchBucket`.
3. Everything reports `Synced=True Ready=True`, because each resource individually
   did what it was asked.

**Why no monitoring caught it:** every metric in Module 12's alert set measures
*whether Crossplane succeeded*. Crossplane succeeded completely. There is no metric
for "the thing you asked for was not the thing you wanted."

**What would have caught it:**

1. **A consistency check** asserting that every cross-resource reference names a
   resource the same composition creates — see
   [`consistency-check.sh`](./consistency-check.sh). It runs on `crossplane render`
   output, needs no cluster, and catches this in CI.
2. **An end-to-end smoke test.** After provisioning, actually write and read an object
   using the name in `status.bucketName`. This catches *all three* faults at once and
   is the highest-value test you can write.
3. **`crossplane render` review.** A human reading the rendered output would see three
   different bucket names side by side.

**What still misses it:** any amount of unit testing the composition in isolation.
The composition is internally consistent — it just doesn't describe the system anyone
wanted. **Only a test that uses the output the way an application would will catch
this class.**

---

## 1. A sixth broken stack

See [`06-broken-mrap.yaml`](./06-broken-mrap.yaml).

**Symptom card (give the reader only this):**
> A composition that worked yesterday now fails for new XRs. Existing XRs are fine.
> The XR reports an error mentioning a kind you're certain exists — you can see the
> provider is healthy, and a colleague insists they used that resource type last week.

**Root cause:** someone narrowed the `ManagedResourceActivationPolicy`, deactivating
the resource type this composition uses. The provider is healthy, the CRD is simply
gone, so the composition's rendered resource can't be applied.

It's a good sixth case because the evidence is in a place none of the other five point
to — `kubectl get managedresourcedefinitions` — and because "it worked last week" sends
people hunting through composition history instead.

## 2. The dashboard

Panels, each with its justification:

| Panel | "I look at this when…" |
|-------|----------------------|
| Unsynced resources by age (table) | …a team reports something isn't provisioning. It tells me instantly whether it's stuck or just slow. |
| Provider health + restart count | …**many** things break at once. A restarting provider explains everything downstream. |
| XRs not ready, by namespace | …I need to know **who** is affected, before they tell me. |
| Reconcile error rate by controller | …I suspect throttling or an expired credential. A step change here dates the incident. |
| Composition revision spread | …weekly, to catch pinning sprawl before a fix fails to reach someone. |

**Panels I deleted, and why:**
- *Total managed resources* — a number that only goes up. I never act on it.
- *CPU/memory of Crossplane pods* — real, but it belongs on the cluster dashboard.
  Duplicating it here means two places to look and neither is authoritative.
- *Reconciles per second* — impressive-looking and I could not complete the sentence.

> **Finish the sentence or delete the panel.** A dashboard nobody reads during an
> incident is worse than no dashboard, because it creates the impression of coverage.

## 3. Catching the invisible failure

See [`consistency-check.sh`](./consistency-check.sh). It renders a composition and
asserts:

- every `bucket:` / `bucketRef.name:` value names a resource the same render produces;
- every `status.*Name` value matches a real rendered external name;
- no two resources claim the same external name.

```
▶ xbrokenfive-aws
    ✗ resource "pab": references bucket "broken-five-wrong-name",
      which no resource in this composition creates.
      Rendered bucket names: broken-five-stack-five
    ✗ status.bucketName = "broken-five-stack-five-data" does not match any
      rendered external name.
2 consistency errors
```

**What it still misses**, stated honestly:
- References to buckets that legitimately exist **outside** this composition (a shared
  bucket from an EnvironmentConfig) look identical to a typo. It needs an allow-list,
  and an allow-list is a place for a mistake to hide.
- It cannot know whether the *intent* was right, only that the composition is
  internally consistent. A composition that consistently creates the wrong thing
  passes.
- It only checks the string patterns it knows about; a new resource kind with a
  different reference field is invisible to it until someone adds a rule.

**Which is why the end-to-end smoke test matters more.** Static checks catch typos;
only using the output the way an application would catches "this isn't what we
wanted."

## 4. Timing yourself

Representative times after practice, and where the time actually goes:

| Stack | Time | Slowest step |
|-------|------|-------------|
| 1 | 1m10s | Realising to compare two apiVersions character by character |
| 2 | 4m30s | **Believing there is a problem at all** — everything is green |
| 3 | 2m00s | Understanding why the *independent* resource is missing too |
| 4 | 0m50s | None — the condition message names the host |
| 5 | 8m00s | **Accepting that Crossplane is fine and the fault is upstream of it** |

**The pattern:** the slowest step is almost never technical. Stacks 4 and 1 are fast
because a message tells you the answer. Stacks 2 and 5 are slow because the system
*insists everything is fine*, and you have to override that signal with your own
judgement.

**The habit worth building:** when everything is green and the system is broken, spend
your first minute confirming that — `kubectl get managed`, all `True` — and then
**deliberately stop looking at Crossplane.** The evidence you need is in the diff
between rendered output and intent, not in any log.

## 5. Stretch — the status aggregator

See [`status-report.sh`](./status-report.sh):

```
XR                              READY  FOR      BLOCKED BY              ERROR
team-payments/payments-db       True   3d4h     -                       -
team-payments/payments-net      False  00:02:11 Subnet/payments-net-x7k  cannot resolve references
team-search/search-cache        False  04:31:02 Instance/search-cache    InvalidParameterValue: db.t3.nano
debug/stack-four                False  00:44:18 Bucket/stack-four-9mn4q  no such host: moto.wrong-...
```

The design decisions that make it useful on-call:

- **"FOR" is the most important column.** `00:02:11` is a healthy creation;
  `04:31:02` is an incident. Readiness alone can't distinguish them, and that's the
  same insight the alerting threshold rests on.
- **It names the *blocking* resource**, not just the XR. That's the difference between
  "something in payments-net is wrong" and "go look at this subnet".
- **It shows the raw cloud error inline.** In practice this is the answer about 70% of
  the time, and it saves a `describe` round-trip per resource.
- **Sorted by duration descending**, so the worst problem is the first line.

This is the view no built-in command gives you, and it's the one a platform on-call
opens first.

---

## Diagnosing stack 6 (the answer)

```bash
# 1. The XR names a kind that "does not exist"
kubectl describe xbrokensix stack-six -n debug | tail -6
#   ...no matches for kind "BucketVersioning" in version "s3.aws.upbound.io/v1beta1"

# 2. But the provider is fine
kubectl get providers
#   provider-aws-s3   True   True

# 3. And the schema IS installed -- just not activated
kubectl get managedresourcedefinitions | grep bucketversioning
#   bucketversionings.s3.aws.upbound.io   ...   ESTABLISHED=False

# 4. THE ANSWER
kubectl get managedresourceactivationpolicy course-resources -o yaml
#   spec.activate: [buckets.s3.aws.upbound.io]      <- BucketVersioning missing
```

**Fix:** add the type back to the activation policy.

**Why this is worth practising:** MRAP is a *cluster-wide* setting that a platform
engineer changes for performance reasons (Module 02), and it breaks compositions owned
by someone else, later, silently. The person who narrowed the policy and the person
who hits the failure are usually different people on different days.

**The operational rule from Module 02's challenge, restated:** treat MRAP like a
firewall rule. Widening is safe; narrowing needs a check that nothing uses the type
you're removing:
```bash
kubectl get bucketversionings.s3.aws.upbound.io -A
```
