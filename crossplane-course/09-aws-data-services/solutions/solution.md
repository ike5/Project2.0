# Challenge 09 — Reference Solution

Runnable manifest: [`xdatabase-full.yaml`](./xdatabase-full.yaml).

---

### 1. Read replicas

Schema:
```yaml
readReplicas:
  type: integer
  default: 0
  minimum: 0
  maximum: 5
```

Template:
```gotemplate
{{- $replicas := $xr.spec.readReplicas | default 0 }}
{{- range $i := until $replicas }}
---
apiVersion: rds.aws.upbound.io/v1beta1
kind: Instance
metadata:
  annotations:
    {{ setResourceNameAnnotation (printf "replica-%d" $i) }}
    crossplane.io/external-name: {{ printf "%s-replica-%d" $dbName $i }}
spec:
  forProvider:
    region: us-east-1
    instanceClass: {{ $class }}
    # A replica inherits engine, version, storage and credentials from its
    # source. Setting them here is an error, not merely redundant.
    replicateSourceDb: {{ $dbName }}
    publiclyAccessible: false
    skipFinalSnapshot: true
  providerConfigRef: { name: default }
{{- end }}
```

The read host, with a fallback:
```gotemplate
{{- $readHost := "" }}
{{- $primary := index .observed.resources "instance" }}
{{- if $primary }}
  {{- $readHost = dig "status" "atProvider" "address" "" $primary.resource }}
{{- end }}
{{- if gt $replicas 0 }}
  {{- $r0 := index .observed.resources "replica-0" }}
  {{- if $r0 }}
    {{- $addr := dig "status" "atProvider" "address" "" $r0.resource }}
    {{- if $addr }}{{ $readHost = $addr }}{{ end }}
  {{- end }}
{{- end }}
```

**Why replicas must come after the primary, and why no sequencer is needed:**

`replicateSourceDb` names a database that must already **exist and be available** —
AWS rejects the create call otherwise. But Crossplane's convergence handles this for
free: the replica's create fails, it reports `Synced=False`, and it retries. Once the
primary is available, the next retry succeeds.

The composition just has to *tolerate* the failure window rather than prevent it,
which is the same lesson as Module 07's reference resolution. Using
`function-sequencer` here would make things worse: if the primary never became ready,
the replica would never be *created*, so you couldn't inspect it to find out why.

The one thing you must handle is the **status** read — hence the guards above. An
unguarded `.resource.status.atProvider.address` on a replica that doesn't exist yet
fails the whole render, including the primary.

### 2. `DATABASE_URL`

The trap: `connectionDetails` can only copy a value from somewhere. It cannot
concatenate, and it cannot URL-encode. So the string must be **assembled where you
have a real programming language** — inside the templating function.

But there's a second trap: the **password is not available to the template**.
`.observed.resources.instance.resource` contains the instance's spec and status;
connection secret contents are deliberately not exposed to functions.

So `DATABASE_URL` cannot be built in the composition at all from the generated
password. Three honest options:

**a) Build it in the app.** The application composes the URL from the five variables
it already has. This is what most teams do, it costs three lines of code, and it is
the correct answer for most cases.

**b) Publish a URL template with a placeholder**, and have the app substitute:
```gotemplate
- type: FromValue
  name: DATABASE_URL_TEMPLATE
  value: "postgres://appuser:%s@{{ $host }}:5432/postgres?sslmode=require"
```
Honest about what it is, but pushes work to the app anyway.

**c) Generate the password yourself** rather than using `autoGeneratePassword`, so
the composition knows it:
```gotemplate
{{- $pw := randAlphaNum 32 }}
```
**Do not do this.** `randAlphaNum` produces a *different* value on every render, so
every reconcile would try to reset the database password. You'd need to generate it
once into a Secret and read it back — at which point you've rebuilt
`autoGeneratePassword` badly.

**Recommendation: (a).** Publish the components; let the application assemble the
URL. If you must publish a URL, use a **sidecar or init container** that reads the
mounted Secret and writes the assembled string — the assembly happens where the
password legitimately lives.

> The general lesson: **Crossplane deliberately keeps generated secrets away from
> composition functions.** A function is a rendering step whose inputs get logged and
> cached; putting passwords through it would undermine the whole point of generating
> them in the first place.

### 3. Password rotation

**What Crossplane does handle:** if you delete the password Secret referenced by
`passwordSecretRef`, the provider generates a new password on the next reconcile and
updates the database via `ModifyDBInstance`. The new value propagates to the
connection secret.

```bash
kubectl delete secret payments-db-password -n crossplane-system
# next reconcile: new password generated, applied to RDS, connection secret updated
```

**What Crossplane does NOT handle, and this is the important half:**

1. **Running pods keep the old password.** As Module 06's challenge established,
   `secretKeyRef` env vars are resolved once at container start. The app holds the old
   value in memory and will keep using it — and start failing authentication the
   moment it opens a new connection.
2. **In-flight connections.** Existing TCP connections authenticated with the old
   password stay open and working. The failure appears later, unpredictably, when the
   pool opens a new connection.
3. **Nothing restarts the app.** Crossplane updates the Secret and stops there.

**A workable procedure:**

```
1. Mount the secret as a VOLUME, not env vars, so the kubelet updates it in place.
2. Make the app re-read credentials on connection failure (most pool libraries
   support a credential provider callback).
3. Trigger rotation: kubectl delete secret <db>-password -n crossplane-system
4. Wait for the connection secret to change:
     kubectl get secret payments-db-conn -o jsonpath='{.data.DATABASE_PASSWORD}'
5. Roll the Deployment as a belt-and-braces step:
     kubectl rollout restart deploy/payments
```

**Honestly: steps 1 and 2 are application work that Crossplane cannot do for you.**
A platform that promises "rotation" without them is promising an outage on a schedule.

**The better answer for anything serious:** use **AWS Secrets Manager with RDS managed
rotation**, and have the app read from Secrets Manager via IRSA. AWS rotates using a
two-user scheme (rotate the inactive user, swap, rotate the other) that gives genuinely
zero-downtime rotation. Crossplane provisions the rotation configuration; AWS runs it.
Use the cloud's mechanism rather than reimplementing it in a reconcile loop.

### 4. Surviving the outage

**a) What state is the AWS resource in?**

Because the composition sets prod defaults, the database **still exists**:
- `deletionPolicy: Orphan` — Crossplane never issued a delete call.
- `deletionProtection: true` — AWS would have refused even if it had.

```bash
awslocal rds describe-db-instances \
  --query 'DBInstances[].{Id:DBInstanceIdentifier,Status:DBInstanceStatus}'
# team-payments-payments-db is still there, "available"
```

What was actually lost: the Kubernetes objects, the connection Secret, and therefore
the app's ability to get credentials on its next pod restart. **The data is fine; the
plumbing is gone.** Running pods keep working, which is why this can go unnoticed for
hours.

**b) Recovery:**

```bash
# 1. Confirm the database is alive and note its exact identifier
awslocal rds describe-db-instances --db-instance-identifier team-payments-payments-db

# 2. Re-create the XR with the SAME name and namespace, so the composition
#    computes the same external names. This is why deterministic naming matters.
kubectl apply -f manifests/xr-database.yaml

# 3. Crossplane finds the existing instance by external name and ADOPTS it.
kubectl get xdatabase payments-db -n team-payments -w
```

**The critical detail:** the composition derives the external name from
`namespace + name`, so recreating the XR with the same identity produces the same
external name, and Crossplane adopts rather than creates. Had the composition used a
random suffix, this recovery would be impossible without manual annotation.

**c) Bringing it back under management safely:**

Do **not** just re-apply and hope. Follow Module 03's import discipline:
```bash
# Adopt observe-only first
kubectl patch xdatabase payments-db -n team-payments --type=merge \
  -p '{"spec":{"crossplane":{"compositionRef":{"name":"xdatabase-observe"}}}}'
# Compare the real instance against what the composition WOULD apply
crossplane render manifests/xr-database.yaml manifests/composition.yaml functions.yaml \
  | grep -A20 'kind: Instance'
awslocal rds describe-db-instances --db-instance-identifier team-payments-payments-db
# Only when they match, switch back to the full composition
```
If the spec disagrees with reality — say the instance was manually resized during the
incident — a full-management reconcile will "correct" it back, causing a second
outage during your recovery.

The connection secret regenerates automatically once the instance is adopted, and
`kubectl rollout restart` gets the app onto it.

**d) Preventing it:**

The root cause is not the deletion — it's that deleting was *possible and easy*. In
order of value:

1. **Separate clusters per environment.** "The wrong context" stops being a category
   of accident when prod is a different cluster with different credentials, and this
   is the only fix that addresses the actual cause.
2. **RBAC:** nobody should hold `delete` on `xdatabases` in prod. Deletion is a
   break-glass operation via a separate, audited role.
3. **A validating admission policy** rejecting deletion of XRs labelled
   `criticality: high`.
4. **GitOps only** (Module 14): if the cluster only accepts changes from a reviewed
   repo, `kubectl delete` isn't a thing anyone can do.

Note that `deletionPolicy: Orphan` **worked exactly as designed** and is why this was
an inconvenience rather than a company-ending event. It saved you; it just doesn't
prevent the incident.

### 5. Stretch — multi-engine

The mechanics are straightforward:
```gotemplate
{{- $engine := $xr.spec.engine | default "postgres" }}
{{- $version := "16.3" }}{{- $port := 5432 }}{{- $scheme := "postgres" }}
{{- if eq $engine "mysql" }}
  {{- $version = "8.0" }}{{ $port = 3306 }}{{ $scheme = "mysql" }}
{{- end }}
```

**Is one composition for two engines a good idea?** Mostly **no**, and the reasoning
generalises:

*Arguments for one composition:* a single API for consumers, shared logic for
networking and deletion protection, one place to fix a bug.

*Arguments for two, which win:*
1. **The differences compound.** Port, version, and scheme are trivial. Parameter
   groups, backup semantics, replica behaviour, connection limits, and TLS
   configuration all differ. Every one adds another `if`, and after six of them the
   template is unreadable.
2. **Testing doubles.** Every change must be verified against both engines, and
   `crossplane render` only proves it *renders*.
3. **A bug in the shared path breaks both.** Two compositions fail independently.
4. **They diverge over time.** MySQL gets a feature Postgres doesn't; the conditionals
   metastasise.

**The better shape: one XRD, two Compositions, selected by label.**
```yaml
# The developer still writes one kind
spec:
  engine: postgres
  crossplane:
    compositionSelector:
      matchLabels: { engine: postgres }
```
Consumers get a single API; implementations stay separate and independently testable.
This is exactly the pattern Module 04 introduced with `xbucket-aws` and
`xbucket-aws-minimal`, and it is the right answer whenever two implementations of one
API differ by more than a few values.

**The heuristic:** if the conditionals in your template outnumber the shared lines,
you have two compositions wearing a trenchcoat.
