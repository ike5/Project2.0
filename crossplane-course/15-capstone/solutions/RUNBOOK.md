# Runbook: rolling out a Service composition change

For platform engineers. A composition change **applies itself to every existing
Service immediately** unless you pin first. This is the procedure that puts a human
back in the loop.

---

## 1. Pre-flight

```bash
./ci/test-compositions.sh --base-ref origin/main
../../11-day-two-operations/manifests/preflight.sh services.platform.acme.io \
  compositions/service-aws.yaml compositions/service-aws-new.yaml \
  examples/service.yaml tests/functions.yaml
```

**All four must hold. If any fails, STOP:**
- [ ] Zero managed resources currently unhealthy.
      *A broken system cannot tell you which problem your change caused.*
- [ ] `✅ Composed resource names are unchanged.`
      *If this fails, the change recreates every database. Escalate.*
- [ ] The rendered diff contains only what you intended.
- [ ] No `deletionPolicy` weakened from `Orphan` to `Delete`.

## 2. Announce

> Rolling out a Service composition change (<what>) starting now, expected complete by
> HH:MM. Services stay up; you may see a brief `Synced=False` on your Service. Reply
> here if you see anything else.

## 3. Pin everything

```bash
kubectl get services.platform.acme.io -A -o json | jq -r '.items[]
  | "\(.metadata.namespace) \(.metadata.name)"' | while read -r ns name; do
  kubectl patch services.platform.acme.io "$name" -n "$ns" --type=merge \
    -p '{"spec":{"crossplane":{"compositionUpdatePolicy":"Manual"}}}'
done

# GATE: must print 0
kubectl get services.platform.acme.io -A -o json | jq '[.items[]
  | select((.spec.crossplane.compositionUpdatePolicy // "Automatic") == "Automatic")] | length'
```

## 4. Apply (nothing should move)

```bash
kubectl apply -f compositions/service-aws.yaml
kubectl get compositionrevisions
```
**GATE:** a new revision exists and **no Service is on it.** If one moved, it wasn't
pinned — go to §6.

## 5. Canary

**Pick, in priority order:** a dev Service → your own team's Service. **Never** the
largest, the busiest, or another team's.

```bash
REV=$(kubectl get compositionrevisions -o json | jq -r '[.items[]
  | select(.spec.compositeTypeRef.kind=="Service")] | max_by(.spec.revision) | .metadata.name')
kubectl patch services.platform.acme.io "$CANARY" -n "$CANARY_NS" --type=merge \
  -p "{\"spec\":{\"crossplane\":{\"compositionRevisionRef\":{\"name\":\"$REV\"}}}}"
```

**GATE — wait 15 minutes, then all four:**
- [ ] `crossplane trace` — every resource `Synced=True Ready=True`.
- [ ] **The RDS instance's `creationTimestamp` is unchanged.** A new one means it was
      recreated: go to §6 and declare an incident.
- [ ] The application is serving (check its dashboard).
- [ ] The change did what it was meant to do.

## 6. Rollback

```bash
PREV=$(kubectl get compositionrevisions -o json | jq -r '[.items[]
  | select(.spec.compositeTypeRef.kind=="Service")] | sort_by(.spec.revision) | .[-2].metadata.name')
kubectl patch services.platform.acme.io "$CANARY" -n "$CANARY_NS" --type=merge \
  -p "{\"spec\":{\"crossplane\":{\"compositionRevisionRef\":{\"name\":\"$PREV\"}}}}"
```

**⚠️ KNOWN LIMIT.** Rollback restores the composition's *shape*. **It does not undo
what the new revision already did.** If a database was recreated, rolling back gives
you the old configuration pointed at a new, empty instance.

**If an instance was recreated: stop, declare an incident, restore from the most
recent snapshot.** Do not continue the rollout.

## 7. Full rollout

Batches of 5, five minutes apart. **Abort on the first failure** — a partial rollout
across 40 services with an unknown fault is worse than a clean revert.

```bash
../../11-day-two-operations/solutions/canary-rollout.sh \
  services.platform.acme.io "$REV" --canary "$CANARY_NS/$CANARY" \
  --batch-size 5 --wait 300 --settle 900
```

## 8. Unpin

```bash
kubectl get services.platform.acme.io -A -o json | jq -r '.items[]
  | "\(.metadata.namespace) \(.metadata.name)"' | while read -r ns name; do
  kubectl patch services.platform.acme.io "$name" -n "$ns" --type=merge \
    -p '{"spec":{"crossplane":{"compositionUpdatePolicy":"Automatic","compositionRevisionRef":null}}}'
done
```

**Do not skip this.** Pinned Services stop receiving fixes, and a year of forgotten
pins produces Services on eleven revisions that nobody dares touch.

## 9. Close out

Post completion. Record: revision number, start/end time, canary used, any gate that
failed.

---

## Break-glass: deleting a production Service

Deletion is blocked by an admission policy, `deletionPolicy: Orphan`, and AWS's
`deletionProtection` — three independent layers, because losing a production database
is unrecoverable.

1. Get approval in `#platform-approvals`. Record the ticket.
2. Confirm what will be destroyed:
   `crossplane trace service.platform.acme.io <name> -n <ns>`
3. Note which resources are `Orphan` — **they will survive and become unmanaged.**
   You must clean them up separately or they become unowned cloud spend.
4. Bind, with a timestamp so the audit can age it:
   ```bash
   kubectl create clusterrolebinding "break-glass-$USER-$(date +%s)" \
     --clusterrole=platform-break-glass --user="$USER"
   ```
5. Delete.
6. **Unbind immediately.**
7. Record in the change log.
