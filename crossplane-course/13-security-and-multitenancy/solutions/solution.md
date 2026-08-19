# Challenge 13 — Reference Solution

Runnable files: [`tenant-gamma.yaml`](./tenant-gamma.yaml),
[`audit-cronjob.yaml`](./audit-cronjob.yaml).

---

### 1. The hole: `update` is as powerful as `create`

The developer role grants `update` and `patch` on XRs but not `delete`. That looks
conservative. It isn't.

**Attack A — take over the composition selection:**
```bash
kubectl patch xbucket reports -n tenant-alpha \
  --as=system:serviceaccount:tenant-alpha:developer --type=merge \
  -p '{"spec":{"crossplane":{"compositionRef":{"name":"xbucket-aws"}}}}'
```
This **succeeds**. The developer just moved their XR onto a *different composition* —
one that may use the `default` ProviderConfig instead of their tenant-scoped one, and
may omit the public access block entirely. **Every guarantee the tenant-scoped
composition made is gone**, and they never needed `create` on a managed resource.

Worse, as Module 04's challenge showed, changing the composition selector deletes and
recreates the composed resources. So `update` is also a **delete** in disguise:

**Attack B — deletion without the delete verb:**
```bash
# Move to a composition that composes nothing
kubectl patch xbucket reports -n tenant-alpha \
  --as=system:serviceaccount:tenant-alpha:developer --type=merge \
  -p '{"spec":{"crossplane":{"compositionRef":{"name":"xbucket-empty"}}}}'
```
Crossplane garbage-collects composed resources that are no longer desired. The bucket
is destroyed. The break-glass control for deletion has been bypassed entirely.

**The fix — make `spec.crossplane` immutable to developers:**

```yaml
apiVersion: admissionregistration.k8s.io/v1
kind: ValidatingAdmissionPolicy
metadata:
  name: no-composition-hijack
spec:
  failurePolicy: Fail
  matchConstraints:
    resourceRules:
      - apiGroups: ["platform.acme.io"]
        operations: ["UPDATE"]
        resources: ["*"]
  validations:
    - expression: >-
        !has(object.spec.crossplane) ||
        !has(oldObject.spec.crossplane) ||
        object.spec.crossplane == oldObject.spec.crossplane
      message: >-
        spec.crossplane is managed by the platform and cannot be changed.
        Changing the composition would bypass the guarantees your platform API
        makes, and can destroy the resources this XR owns.
```

Plus, at the XRD level, defence in depth:
```yaml
x-kubernetes-validations:
  - rule: "!has(self.environment) || self.environment == oldSelf.environment"
    message: "environment is immutable"
```

**The general lesson, which generalises well beyond Crossplane:** in a control plane,
**`update` is not a lesser permission than `create`.** Any field that changes *which
code runs* — a composition reference, a selector, a policy name — is as powerful as
the code itself. Audit your APIs for fields like that and pin them.

**A second, smaller hole:** the developer role grants `get`/`list` on **all** Secrets
in their namespace, not just their own connection secrets. If another team's XR ever
writes a Secret into that namespace, they can read it. Scope it with
`resourceNames`, or use a label selector via an admission policy.

### 2. The threat model

| # | Threat | Likelihood | Impact | Control | Enforcing layer |
|---|--------|-----------|--------|---------|-----------------|
| 1 | Dev reads another tenant's secrets | Medium | High | Namespaced RBAC | Kubernetes |
| 2 | Dev bypasses composition guarantees | **High** | High | No `create` on managed resources | Kubernetes |
| 3 | Dev hijacks composition via `update` | Medium | High | Admission policy on `spec.crossplane` | Kubernetes |
| 4 | Dev provisions into prod from dev | Medium | High | Namespace-label admission policy | Kubernetes |
| 5 | Dev escalates via IAM | Low | **Critical** | Permissions boundary + no-wildcard policy | **AWS** + Kubernetes |
| 6 | Cross-tenant cloud access | Low | **Critical** | ProviderConfig per tenant, separate accounts | **AWS** |
| 7 | Provider credentials stolen | Low | **Critical** | IRSA (no secret exists) + etcd encryption | **AWS** |
| 8 | One tenant exhausts API quota | Medium | Medium | ResourceQuota | Kubernetes |
| 9 | Accidental prod deletion | **High** | **Critical** | Break-glass + admission + `Usage` + Orphan | Kubernetes ×3 |
| 10 | RBAC drift (stray cluster-admin) | Medium | **Critical** | Scheduled audit | **Process** |

**Accepted risks — not mitigated, and why:**

> **A platform engineer with legitimate cluster-admin does something catastrophic.**
>
> We have not mitigated this and we do not intend to. Any control we could add (dual
> approval on every composition change, no standing admin, a separate approval
> cluster) would be circumventable by the same people and would slow every legitimate
> change by hours. We accept it and rely on: GitOps so changes are reviewed before
> they apply (Module 14), audit logging so actions are attributable, and hiring.
>
> **We revisit this if** the team grows past ~15 people, at which point "everyone
> knows everyone" stops being a control.

> **A compromised provider image.** We install providers from `xpkg.upbound.io` and
> trust them. Mitigating properly means mirroring, scanning, and signature
> verification for every package. We accept this risk today, pin every tag (never
> `:latest`), and have it on the roadmap for when we mirror packages internally.

**Why include accepted risks:** a threat model with no accepted risks is one where
somebody wrote down every control they could think of and claimed it was complete.
The accepted ones are where the real thinking is, and they're what a reviewer should
argue with.

**Note the layer column.** Seven of ten controls are enforced by Kubernetes, which is
the honest weakness of this design: a single cluster misconfiguration degrades most of
it at once. The three AWS-enforced controls (5, 6, 7) are the ones that survive your
own mistakes, which is why the recommendation is always to push controls down to AWS
where you can.

### 3. Tenant gamma

See [`tenant-gamma.yaml`](./tenant-gamma.yaml). Four restrictions, four mechanisms:

| Restriction | Mechanism |
|-------------|-----------|
| No `XDatabase` | RBAC: `resources: ["xbuckets"]` only |
| Max 2 buckets | `ResourceQuota` |
| Must have `contract-end-date` | `ValidatingAdmissionPolicy` |
| No connection secrets | RBAC: no `secrets` rule at all |

Demonstrating each:
```bash
GAMMA="system:serviceaccount:tenant-gamma:contractor"

kubectl auth can-i create xdatabases -n tenant-gamma --as="$GAMMA"   # no
kubectl auth can-i get secrets       -n tenant-gamma --as="$GAMMA"   # no

# Missing label -> rejected by admission
kubectl apply -n tenant-gamma --as="$GAMMA" -f - <<'YAML'
apiVersion: platform.acme.io/v1alpha1
kind: XBucket
metadata: { name: no-date, labels: { acme.io/owner: contractors } }
spec: { environment: dev }
YAML
# Error: contractor resources must carry a contract-end-date label

# Third bucket -> rejected by quota
```

**The interesting one is the date label.** It gives you a query for offboarding:
```bash
kubectl get xbuckets -A -o json | jq -r --arg today "$(date +%F)" '
  .items[] | select(.metadata.labels["contract-end-date"] != null)
  | select(.metadata.labels["contract-end-date"] < $today)
  | "\(.metadata.namespace)/\(.metadata.name) expired \(.metadata.labels["contract-end-date"])"'
```
Contractor infrastructure that outlives the contract is a common and boring source of
both cost and risk. Make it queryable and it stops being invisible.

### 4. The audit CronJob

See [`audit-cronjob.yaml`](./audit-cronjob.yaml). RBAC is read-only on RBAC objects
and provider configs, plus write on one named ConfigMap.

**Page at 3 a.m.:**
- A new `cluster-admin` binding that wasn't there yesterday. This is either a
  compromise or an incident someone is handling without telling you; both warrant
  waking someone.
- A break-glass binding active for more than an hour. Either it was forgotten (fix it
  now, it's a standing privilege) or someone is doing something at 3 a.m. that you
  want to know about.
- Any service account outside `crossplane-system` that can read the provider
  credentials. This is a direct route to the cloud account.

**Wait until morning:**
- A namespace missing a `ResourceQuota`. Real, but the damage is gradual and bounded.
- An admission policy absent. It should have been caught at deploy time; fixing it at
  3 a.m. changes nothing that wasn't already true yesterday.
- Drift in ProviderConfig usage counts. Interesting, not urgent.

**The principle for the split:** page when **a control that was present has
disappeared**, because that's either an attack or an unmanaged change. Wait when **a
control was never there**, because the exposure already existed all day and waking
someone doesn't reduce it. The first is a delta; the second is a backlog item.

> Corollary: this means the audit must **compare against yesterday's result**, not
> just report today's state. An absolute report can't tell you what changed, and
> "what changed" is the whole signal.

### 5. Stretch — the compromised token

**What the attacker can reach**, given the lab's controls:
- Create and update `XBucket`/`XDatabase` in `tenant-alpha` only.
- Read all Secrets in `tenant-alpha`, including connection secrets → **database
  credentials for tenant-alpha's databases**.
- Read managed resources (reconnaissance: bucket names, ARNs, endpoints).
- **Cannot** delete, touch another namespace, read provider credentials, or edit
  compositions.
- **But** (from Task 1) if `spec.crossplane` is not pinned, they can hijack the
  composition — which means they *can* effectively delete, and can move resources onto
  a composition with weaker guarantees.

**First 10 minutes:**
```bash
# 1. Revoke the token. Deleting the ServiceAccount invalidates its tokens.
kubectl delete sa developer -n tenant-alpha

# 2. Freeze the blast radius WITHOUT deleting evidence.
kubectl annotate xbucket,xdatabase -n tenant-alpha --all crossplane.io/paused=true
#    Pausing stops Crossplane acting on anything the attacker changed, while
#    leaving every object intact for investigation. Do NOT delete anything yet.

# 3. Rotate any credential they could have read.
kubectl get secrets -n tenant-alpha
#    Every connection secret in that namespace is compromised. For each database,
#    delete its password secret so the provider regenerates it (Module 09).
```

**Determining what they did** — audit logs are the only real answer, which is why
enabling them matters before you need them:
```bash
# Everything that identity did
kubectl get events -n tenant-alpha --sort-by='.lastTimestamp'

# The authoritative record, if API audit logging is on
grep 'system:serviceaccount:tenant-alpha:developer' /var/log/kubernetes/audit.log \
  | jq 'select(.verb != "get" and .verb != "list")'

# What exists now that shouldn't
kubectl get xbuckets,xdatabases -n tenant-alpha -o json \
  | jq -r '.items[] | "\(.metadata.name) created \(.metadata.creationTimestamp)"'

# Cloud-side truth
awslocal s3 ls | grep tenant-alpha
```

**Note what you cannot reconstruct without audit logs:** Kubernetes Events expire
after an hour (Module 12), and `creationTimestamp` tells you when something appeared
but not who made it or what they changed. **If audit logging is off, you cannot answer
"what did they do" at all** — you can only enumerate current state and guess.

**What would have limited the blast radius:**

1. **Short-lived tokens.** Bound ServiceAccount tokens (the default since 1.24) expire
   and are audience-scoped. A long-lived Secret-based token is a permanent credential;
   avoid creating them.
2. **No blanket Secret read.** Scope the developer's Secret access by
   `resourceNames` to their own connection secrets, so a compromise doesn't yield
   every credential in the namespace.
3. **Pin `spec.crossplane`** (Task 1), removing the composition-hijack route.
4. **Separate AWS accounts per tenant.** Even with full control of tenant-alpha's
   namespace, the attacker reaches only tenant-alpha's account. **This is the control
   that bounds the damage rather than merely reducing it.**
5. **Audit logging enabled and shipped off-cluster**, so the record survives an
   attacker with cluster access.

**The recurring theme, one last time:** controls 1–3 are Kubernetes controls, and a
sufficiently determined attacker with cluster access erodes them. Control 4 is
enforced by AWS and holds regardless of what happens inside your cluster. **Push the
boundary down to the cloud wherever you can afford to.**
