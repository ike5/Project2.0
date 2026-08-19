# Challenge 14 — Reference Solution

Runnable files: [`gitops-rbac.yaml`](./gitops-rbac.yaml),
[`environments/`](./environments/), [`drift-check.sh`](./drift-check.sh),
[`e2e-test.sh`](./e2e-test.sh).

---

### 1. Closing the last door

See [`gitops-rbac.yaml`](./gitops-rbac.yaml).

```yaml
# Argo CD's controller may manage platform objects.
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata: { name: platform-writer }
rules:
  - apiGroups: ["apiextensions.crossplane.io", "pkg.crossplane.io"]
    resources: ["*"]
    verbs: ["*"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata: { name: argocd-platform-writer }
roleRef: { apiGroup: rbac.authorization.k8s.io, kind: ClusterRole, name: platform-writer }
subjects:
  - kind: ServiceAccount
    name: argocd-application-controller
    namespace: argocd
```
and **humans get a read-only ClusterRole** with `get/list/watch` only.

The critical part is auditing that nothing else has the access:
```bash
kubectl auth can-i update compositions --as=alice@acme.example       # no
kubectl auth can-i update compositions \
  --as=system:serviceaccount:argocd:argocd-application-controller    # yes
```

**The emergency path when Argo CD is broken.**

The naive answer — "give someone cluster-admin" — is wrong, because that permission
persists after the emergency and nobody removes it (Module 13's audit exists for
exactly this).

The right shape is Module 13's **break-glass** pattern applied here:

```bash
# 1. Announce in #incident. Record the ticket.
# 2. Bind yourself, with a timestamp in the name so the audit can age it:
kubectl create clusterrolebinding "break-glass-platform-$USER-$(date +%s)" \
  --clusterrole=platform-writer --user="$USER"
# 3. Make the minimum change.
# 4. UNBIND immediately.
# 5. Reconcile git with what you did, before Argo CD recovers.
```

**Why this is safe:**
- It's **time-bounded and named**, so Module 13's audit job pages if a binding
  outlives an hour.
- It's **auditable** — every action carries a human identity, not a shared account.
- Step 5 is the one people skip and the one that matters: if git doesn't match what
  you did, Argo CD's `selfHeal` will revert your emergency fix the moment it recovers,
  usually at the worst possible time.

**The deeper point:** an emergency path that doesn't exist gets invented under
pressure, badly. Design it in advance, make it noisy, and make it expire.

### 2. Promotion by pinned version

See [`environments/`](./environments/).

```
environments/
├── dev/configuration.yaml       package: ghcr.io/acme/platform:v1.1.0
├── staging/configuration.yaml   package: ghcr.io/acme/platform:v1.1.0
└── prod/configuration.yaml      package: ghcr.io/acme/platform:v1.0.0
```

Promotion is a one-line pull request:
```bash
sed -i 's|platform:v1.0.0|platform:v1.1.0|' environments/prod/configuration.yaml
git commit -am "Promote platform v1.1.0 to prod"
```

**Why a pinned version beats a branch:**

1. **A branch is a moving target.** "Prod tracks `release`" means prod runs whatever
   `release` pointed at when Argo CD last synced. Two clusters syncing minutes apart
   can run different code, and neither can tell you which.
2. **Rollback is exact.** Reverting to `v1.0.0` restores a specific, immutable
   artifact. Reverting a branch restores "whatever that branch looked like then",
   which requires archaeology.
3. **The diff between environments is legible.** `git diff environments/prod
   environments/staging` shows `v1.0.0` vs `v1.1.0` — one line, obviously meaningful.
   Comparing two branches shows every commit between them.
4. **It survives a force-push.** A branch can be rewritten; a pushed OCI tag is
   content-addressed and immutable.
5. **It records intent.** The commit "Promote v1.1.0 to prod" is a decision with an
   author, a timestamp, and a reviewer. A branch merge is a side effect.

> This is why Module 10's packaging matters. Without a versioned artifact, "promotion"
> can only mean pointing at a branch, and you inherit all five problems.

### 3. Detecting real drift, honestly

**The problem with `ignoreDifferences` on `/spec/forProvider`:** it's a blunt
instrument. It suppresses late-initialization noise *and* genuine unauthorized change,
because Argo CD can't tell them apart from a JSON diff.

**A better check** — see [`drift-check.sh`](./drift-check.sh). It compares three
sources rather than two:

1. **What git says** (`crossplane render` of the committed composition).
2. **What the cluster's spec says** (`kubectl get -o yaml`).
3. **What the cloud actually is** (`status.atProvider`, and direct AWS queries).

The rules it applies:
- A field in (2) but not (1), where (2) matches (3) → **late initialization.** Benign.
- A field in (1) and (2) that *disagrees* → **real drift in the declaration**. Someone
  edited the cluster directly. Alert.
- (3) disagreeing with (2), persisting past a reconcile interval → **the provider
  cannot converge.** This is Module 12's `Synced=False` territory.
- A resource in (3) with no counterpart in (1) or (2) → **unmanaged infrastructure**,
  possibly created out-of-band.

**What it genuinely cannot tell apart, stated plainly:**

- **A new provider version's late-init defaults look identical to a console edit.**
  Both are "a field appeared in the spec that git doesn't have, and it matches
  reality". Upgrading a provider will produce a burst of false positives, and the only
  honest mitigation is to re-baseline after a deliberate upgrade.
- **A console change that Crossplane has already corrected is invisible.** By the time
  the check runs, reality matches the declaration again. Catching that needs
  **CloudTrail**, not Kubernetes.
- **It can't see changes to fields the composition never declared.** Module 01's
  challenge showed Crossplane only reconciles what you declared; a rogue tag on an
  undeclared field is drift no Kubernetes-side check will find.

**The conclusion worth stating:** Kubernetes-side drift detection is a partial
control. For genuine "who changed what in our cloud account" you need **CloudTrail
with alerting on console-originated writes**, and ideally an SCP denying console
writes to production entirely. The check above is worth having; it is not a substitute
for the cloud's own audit trail.

### 4. The end-to-end test

See [`e2e-test.sh`](./e2e-test.sh). It runs in CI against a kind cluster: creates a
cluster, installs Crossplane and the emulator, applies the platform, creates an XR,
waits for readiness, **then uses the output**:

```bash
BUCKET=$(kubectl get xbucket ci-test -n ci -o jsonpath='{.status.bucketName}')

# THE CRITICAL STEP: use the value the way an application would.
awslocal s3 cp /tmp/probe.txt "s3://${BUCKET}/probe.txt"
awslocal s3 cp "s3://${BUCKET}/probe.txt" /tmp/probe-back.txt
diff /tmp/probe.txt /tmp/probe-back.txt

# And verify the guarantees the platform PROMISED
awslocal s3api get-public-access-block --bucket "$BUCKET" \
  | jq -e '.PublicAccessBlockConfiguration.BlockPublicAcls == true'
```

**Why this is the only thing that catches the Stack 5 class:**

Module 12's Stack 5 was internally consistent from Crossplane's point of view — every
resource was `Synced=True Ready=True`, because each one did exactly what it was told.
The faults were:
- the public access block protected a bucket that didn't exist;
- `status.bucketName` handed the application a name that didn't exist.

**No static check on the composition can catch the second one in general**, because
"is this string the name of something that will exist" depends on what the cloud
actually does. The consistency checker from Module 12 catches the common case (a
reference to a name nothing in the same render produces) and would miss a name that's
valid-looking but wrong for an external reason.

Only a test that **takes the output and uses it** exercises the actual contract. The
probe upload fails with `NoSuchBucket`, which is precisely the error the application
would have hit in production — discovered in CI instead.

**The general principle:** static checks verify that the composition is *internally
coherent*. Only an e2e test verifies that it *does the thing anyone wanted*. You need
both, and the e2e test is slower and more valuable.

### 5. Stretch — the whole pipeline

The assembled repo runs, on every pull request:

| Stage | Runtime | Catches |
|-------|---------|---------|
| YAML parse | ~1s | Typos |
| `crossplane render` | ~5s | Template errors |
| `crossplane validate` | ~5s | Schema violations |
| Consistency check | ~2s | Green-but-wrong references |
| IAM policy lint | ~2s | Wildcards, escalation paths |
| **Destructive-change gate** | ~5s | **Renames that destroy infrastructure** |
| e2e against kind | ~6min | Everything else |

**Total: ~20 seconds for the static gate, ~6 minutes with e2e.**

Run the static checks on **every push** and the e2e on **pull requests and main
only**. Six minutes on every commit trains people to push less often, which is the
opposite of what you want.

**If you could keep only one check**, keep the **destructive-change gate**. Every
other failure it might miss is recoverable: a bad render fails loudly, a schema
violation is rejected at apply, a wildcard IAM policy is a latent risk you can fix
tomorrow. A renamed composed resource **silently destroys production data**, looks
like a trivial diff in review, and is unrecoverable once it runs.

It's five seconds of CI against the one mistake in Crossplane that you cannot undo.
