# Module 12 — Observability & Debugging

**Goal:** diagnose any broken Crossplane stack in under five minutes, and know before
your users do.

⏱️ ~3 hours · 🎯 Prereq: Modules 04–11.

---

## 1. The four layers

Every Crossplane problem lives in one of four places. Identifying which one, first,
is most of the work:

```
Layer 1  Your XR            → is the composition even rendering?
Layer 2  Composed resources → did it produce what you expected?
Layer 3  The provider       → did the cloud API accept the call?
Layer 4  The cloud          → does the resource actually work?
```

**The single command that spans all four:**
```bash
crossplane trace <kind> <name> -n <namespace>
```

Read it top-down and stop at the first thing that isn't `True`. That's your layer.

## 2. Conditions: the two you read constantly

| Condition | Question |
|-----------|----------|
| `Synced` | Did my last API call to the cloud succeed? |
| `Ready` | Does the resource exist and work? |

| `SYNCED` | `READY` | Meaning | Where to look |
|----------|---------|---------|---------------|
| `True` | `True` | Working | — |
| `True` | `False` | Accepted; still building | Normal for minutes. If stuck, `describe` it |
| `False` | `False` | **The API call failed** | The `Synced` message — it has the raw cloud error |
| `False` | `True` | Was working; an update was rejected | The `Synced` message. Your spec change is invalid |
| *(none)* | | Nothing is reconciling it | Provider healthy? Resource paused? |

The message is where the answer lives:
```bash
kubectl get bucket my-bucket \
  -o jsonpath='{.status.conditions[?(@.type=="Synced")].message}'
```

## 3. The debugging order

Follow this every time. It resolves the large majority of problems, and it's the same
order Module 02 introduced:

```
1. crossplane trace         → which layer?
2. The condition message    → the raw cloud error, usually enough
3. kubectl describe         → Events, at the bottom
4. Component logs           → only when 1-3 aren't enough
```

**Which log?**
```bash
# XRD/Composition/XR problems — the composition engine
kubectl logs -n crossplane-system deploy/crossplane -f

# Cloud API problems — auth, quota, invalid parameters
kubectl logs -n crossplane-system -l pkg.crossplane.io/provider=provider-aws-s3 -f

# Rendering problems — the function itself failed
kubectl logs -n crossplane-system -l pkg.crossplane.io/function=function-go-templating -f
```

## 4. Signatures worth memorising

Each of these has a distinctive shape. Recognising it skips straight to the cause.

| Signature | Cause |
|-----------|-------|
| XR exists, **no composed resources**, no obvious error | `compositeTypeRef` mismatch, or no Composition selected |
| XR exists, resources exist, XR never `Ready` | A composed resource isn't ready; `trace` shows which |
| One resource `SYNCED=False`, `cannot resolve references` | A dependency doesn't exist yet — **normal for a minute**, a bug if permanent |
| Everything `SYNCED=True` but the system doesn't work | **You declared the wrong thing.** Stop reading Crossplane logs |
| Resource stuck `Terminating` | The cloud refuses to delete it; read the Events |
| A field is silently empty | A patch's `fromFieldPath` doesn't exist — set `policy: Required` |
| Everything went unsynced at once | Credentials, endpoint, or a provider upgrade |

> **The fourth row is the important one.** A green control plane and a broken system
> means the fault is in *what you asked for*, not in how it was applied. No amount of
> `kubectl describe` will show you what you failed to write — go and compare reality
> against your intent.

## 5. Metrics and alerting

Crossplane and its providers expose Prometheus metrics on `:8080/metrics`.

The ones worth alerting on:

| Metric | Alert when |
|--------|-----------|
| `crossplane_managed_resource_ready` | A resource is not ready for > 1 hour |
| `controller_runtime_reconcile_errors_total` | The error rate rises sharply |
| `controller_runtime_reconcile_time_seconds` | p99 climbs — usually cloud API throttling |
| `up` on provider pods | A provider is down |

**The rule that matters more than the metric list:**

> **Alert on failure to converge, not on not-yet-converged.**

`Synced=False` is a completely normal transient state — every subnet in Module 07 was
unsynced until its VPC existed. Alerting on the raw condition means paging on every
normal creation, and within a week the alert is muted forever.

**Duration is what distinguishes a slow convergence from a stuck one.** Pick a
threshold longer than your slowest legitimate operation (real RDS is 5–15 minutes, so
an hour gives good headroom) and alert on *that*.

```promql
# Good: stuck for an hour
min_over_time(crossplane_managed_resource_ready[1h]) == 0

# Bad: fires constantly on healthy creations
crossplane_managed_resource_ready == 0
```

## 6. Events

Crossplane emits Kubernetes Events, which is how you get history rather than just
current state:

```bash
kubectl get events --field-selector involvedObject.name=my-bucket
kubectl get events -A --sort-by='.lastTimestamp' | grep -i crossplane
```

> **Events expire** (default one hour). For anything you'll want during a post-mortem,
> ship them to your logging system. "It was working yesterday and I can't see why it
> changed" is unanswerable without event history.

## 7. Knowing before your users do

A short, high-value dashboard:

1. **Unsynced resources by age** — anything over an hour is a real problem.
2. **Provider health** — `Healthy=False` or a restarting pod.
3. **XRs not ready, by namespace** — tells you which team is affected.
4. **Reconcile error rate by provider** — a spike usually means throttling or an
   expired credential.
5. **Composition revision spread** — from Module 11; sprawl is silent.

---

## Do the lab
Diagnose five broken stacks, each with a different root cause, using only the
debugging order. Then install Prometheus and write an alert that doesn't cry wolf.
👉 **[lab.md](./lab.md)**

Then: 👉 **[challenge.md](./challenge.md)**

## Manifests
- [`broken/`](./manifests/broken/) — five stacks, each broken differently
- [`prometheus-values.yaml`](./manifests/prometheus-values.yaml) — scraping Crossplane
- [`alerts.yaml`](./manifests/alerts.yaml) — alerts that fire on real problems only
- [`triage.sh`](./manifests/triage.sh) — the debugging order, scripted

## Key terms
`crossplane trace` · conditions · `Synced` · `Ready` · Events · reconcile error rate ·
failure to converge · alert threshold · four layers

**Next →** [Module 13: Security & Multi-Tenancy](../13-security-and-multitenancy/)
