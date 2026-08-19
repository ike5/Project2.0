# Challenge 11 — Reference Solution

Runnable files: [`preflight-plus.sh`](./preflight-plus.sh),
[`revision-report.sh`](./revision-report.sh),
[`canary-rollout.sh`](./canary-rollout.sh),
[`drift-alert.yaml`](./drift-alert.yaml).

---

### 1. The rollout runbook

> # RUNBOOK: XDatabase composition change — add automated backups
>
> **Change:** adds `backupRetentionPeriod` and `preferredBackupWindow` to the RDS
> instance produced by `xdatabase-aws`.
> **Blast radius:** 40 XDatabase XRs, 12 teams, all production.
> **Expected duration:** 90 minutes.
> **Roll back at any point** by following §6.
>
> ---
> ## 1. Pre-flight (do not skip)
>
> ```bash
> ./preflight.sh xdatabases \
>   compositions/xdatabase-aws.yaml \
>   compositions/xdatabase-aws-v2.yaml \
>   test/sample-xr.yaml test/functions.yaml
> ```
>
> **PASS criteria — all four must hold:**
> - [ ] Zero managed resources currently `Synced=False` or `Ready=False`.
>       *If anything is already broken, STOP.* You will not be able to attribute a
>       later failure.
> - [ ] `✅ Composed resource names are unchanged.`
>       *If this fails, STOP and escalate.* The change will recreate 40 databases.
> - [ ] The rendered diff contains **only** the two backup fields.
> - [ ] No `deletionPolicy` change appears in the diff.
>
> ## 2. Announce
>
> Post in `#platform-announcements` before starting:
> > Rolling out an XDatabase composition change (adds automated backups) starting
> > now. Expected complete by HH:MM. Databases stay up throughout; you may see a
> > brief `Synced=False` on your XDatabase as it applies. Reply here if you see
> > anything else.
>
> ## 3. Pin everything
>
> ```bash
> kubectl get xdatabases -A -o name | while read -r xr; do
>   ns=$(kubectl get "$xr" -A -o jsonpath='{.metadata.namespace}')
>   kubectl patch "$xr" -n "$ns" --type=merge \
>     -p '{"spec":{"crossplane":{"compositionUpdatePolicy":"Manual"}}}'
> done
>
> # VERIFY -- must print 0
> kubectl get xdatabases -A -o json | jq '[.items[]
>   | select((.spec.crossplane.compositionUpdatePolicy // "Automatic") == "Automatic")] | length'
> ```
> **GATE:** the count above must be `0`. If not, do not proceed — an unpinned XR will
> move the instant you apply in step 4.
>
> ## 4. Apply (nothing should change yet)
>
> ```bash
> kubectl apply -f compositions/xdatabase-aws-v2.yaml
> kubectl get compositionrevisions | grep xdatabase
> ```
> **GATE:** a new revision exists, and
> `kubectl get xdatabases -A` shows **no** XR on it.
> If any XR moved, one was not pinned — go to §6 immediately.
>
> ## 5. Canary
>
> **Canary selection, in priority order:**
> 1. A **non-production** XDatabase if one exists (`environment: dev`).
> 2. Otherwise: the production database owned by **your own team** — you can
>    assess its health directly and you own the consequences.
> 3. **Never** pick the largest, the busiest, or another team's.
>
> ```bash
> REV=$(kubectl get compositionrevisions -o json \
>   | jq -r '[.items[] | select(.spec.compositeTypeRef.kind=="XDatabase")]
>            | max_by(.spec.revision) | .metadata.name')
> kubectl patch xdatabase "$CANARY" -n "$CANARY_NS" --type=merge \
>   -p "{\"spec\":{\"crossplane\":{\"compositionRevisionRef\":{\"name\":\"$REV\"}}}}"
> ```
>
> **GATE — wait 15 minutes, then all four must hold:**
> - [ ] `crossplane trace xdatabase $CANARY -n $CANARY_NS` — every resource
>       `Synced=True Ready=True`.
> - [ ] `kubectl get instance.rds.aws.upbound.io -o jsonpath='{...creationTimestamp}'`
>       — **unchanged from before the rollout**. A new timestamp means the instance
>       was recreated: go to §6 and declare an incident.
> - [ ] The application using it is still serving (check its dashboards).
> - [ ] `aws rds describe-db-instances` shows `BackupRetentionPeriod: 7` — the change
>       actually did what it was meant to.
>
> **If any gate fails → §6.**
>
> ## 6. Rollback
>
> ```bash
> PREV=$(kubectl get compositionrevisions -o json \
>   | jq -r '[.items[] | select(.spec.compositeTypeRef.kind=="XDatabase")]
>            | sort_by(.spec.revision) | .[-2].metadata.name')
> kubectl patch xdatabase "$CANARY" -n "$CANARY_NS" --type=merge \
>   -p "{\"spec\":{\"crossplane\":{\"compositionRevisionRef\":{\"name\":\"$PREV\"}}}}"
> ```
>
> **⚠️ KNOWN LIMIT — read this before relying on rollback.**
> Rolling back restores the composition's *shape*. **It does not undo anything the
> new revision already did.** If the new revision deleted and recreated the RDS
> instance, rolling back gives you the old configuration pointed at the new, empty
> database. The data is not recovered by this procedure.
>
> If an instance was recreated: **stop, declare an incident, and restore from the
> most recent snapshot.** Do not attempt further rollout steps.
>
> ## 7. Full rollout
>
> Batches of 5, waiting 5 minutes between them:
> ```bash
> ./canary-rollout.sh xdatabases "$REV" --batch-size 5 --wait 300
> ```
> **GATE between each batch:** zero XDatabases `Synced=False`. Abort on the first
> failure.
>
> ## 8. Unpin
>
> ```bash
> kubectl get xdatabases -A -o name | while read -r xr; do
>   ns=$(kubectl get "$xr" -A -o jsonpath='{.metadata.namespace}')
>   kubectl patch "$xr" -n "$ns" --type=merge \
>     -p '{"spec":{"crossplane":{"compositionUpdatePolicy":"Automatic","compositionRevisionRef":null}}}'
> done
> ```
> **Do not skip this.** Pinned XRs stop receiving future fixes, and a year of
> forgotten pins produces XRs on eleven revisions that nobody dares touch.
>
> ## 9. Close out
>
> Post completion in `#platform-announcements`. Record in the change log: revision
> number, start/end time, canary used, any gate that failed.

### 2. `preflight-plus.sh`

See [`preflight-plus.sh`](./preflight-plus.sh). The three added detections:

**Removed resource** — compare the resource-name sets and report names present in old
but absent in new:
```
🚨 A COMPOSED RESOURCE WAS REMOVED: lifecycle
   Crossplane garbage-collects composed resources that are no longer desired.
   This will DELETE that resource for every existing XR.
```

**Changed external-name template** — a changed external name doesn't rename anything
in the cloud; it points Crossplane at a *different* resource, orphaning the old one:
```
🚨 EXTERNAL NAME CHANGED for resource "bucket":
     old: team-payments-prod-a
     new: acme-team-payments-prod-a
   Crossplane will ORPHAN the existing cloud resource and CREATE a new one.
   The old resource keeps running, unmanaged and unbilled to anyone.
```

**Weakened deletionPolicy:**
```
⚠️  deletionPolicy changed Orphan -> Delete for resource "database".
   Deleting the XR will now DESTROY the cloud resource. Confirm this is intended.
```

The general principle: **the dangerous composition changes are the ones with no
visible API surface.** A linter that only diffs the XRD schema catches none of them.

### 3. Revision report

See [`revision-report.sh`](./revision-report.sh).

```
Composition: xdatabase-aws
  REVISION  AGE    XRs   XRs BEHIND LATEST
  1         84d    2     ← 3 behind  ⚠️
  3         31d    6     ← 1 behind
  4         2d     32    (latest)

  40 XRs total across 3 revisions.
  ⚠️  2 XRs are more than one revision behind:
        team-legacy/billing-db      (revision 1, pinned 84d ago)
        team-legacy/reporting-db    (revision 1, pinned 84d ago)
```

**Why this report matters:** revision sprawl is silent. Nobody notices that two XRs
have been pinned since a rollout eleven weeks ago — until a security fix goes out and
those two don't get it. Run this weekly and treat "pinned more than 30 days" as a
bug to be closed.

### 4. The drift alert job

See [`drift-alert.yaml`](./drift-alert.yaml). RBAC is read-only on managed resources
plus write on one ConfigMap in its own namespace.

**Why "unsynced for more than an hour" beats "unsynced":**

`Synced=False` is a **completely normal transient state**, and you saw it constantly:
- Module 07: every subnet was `Synced=False` until its VPC existed.
- Module 09: replicas are `Synced=False` until the primary is available.
- Any resource is briefly unsynced during an update.

Alerting on `Synced=False` means paging on every normal creation. Within a week
everyone mutes the alert, and then it never fires usefully again.

**An hour is chosen because it is longer than every legitimate convergence.** The
slowest thing in this course is real RDS at 5–15 minutes; an hour gives 4× headroom
over the worst legitimate case while still catching a genuinely stuck resource the
same working day.

> The general rule for control-plane alerting: **alert on failure to converge, not on
> not-yet-converged.** The system is *designed* to spend time in the second state.
> Duration is what distinguishes them, and picking the threshold is the whole design.

### 5. Automated canary rollout

See [`canary-rollout.sh`](./canary-rollout.sh):

```bash
./canary-rollout.sh xdatabases xdatabase-aws-4f8a2c1 \
  --canary team-platform/test-db --batch-size 5 --wait 300 --settle 900
```

The design decisions worth noting:

- **It aborts on the first failure and rolls back**, rather than continuing. A partial
  rollout across 40 databases with an unknown failure is worse than a clean revert.
- **It waits for a *sustained* healthy period** (`--settle`), not a single check. A
  resource can be briefly `Ready` mid-replacement.
- **It records the previous revision before starting**, so rollback doesn't depend on
  querying a cluster that may be in a strange state.
- **It refuses to run if anything is unhealthy beforehand**, for the reason in the
  runbook.
- **It does not unpin at the end.** That's a deliberate human decision after
  verification, not something a script should do while nobody's watching.

**The honest caveat, which the script prints:** automating the rollout does not
automate the *judgement*. The script can tell you `Synced=True`; it cannot tell you
the application is serving correctly. Keep a human on the gates that matter.
