# Lab 14 — Git Is the Only Way In

**You'll:** put your platform under Argo CD, fix the permanent-diff problem that
makes everyone ignore sync status, and build a CI gate that rejects a destructive
composition change. ⏱️ ~80 min.

> Prereqs: Modules 11–13.
>
> Argo CD is heavy on a kind cluster. **Parts D–F are the highest-value part of this
> lab and need no Argo CD at all** — if your laptop struggles, skip to Part D.

---

## Part A — Install Argo CD

```bash
cd 14-gitops-and-cicd
cat manifests/argocd/install.md
kubectl create namespace argocd
kubectl apply -n argocd \
  -f https://raw.githubusercontent.com/argoproj/argo-cd/v2.13.2/manifests/install.yaml
kubectl wait --for=condition=Available deploy --all -n argocd --timeout=10m
```
✅ Expected: several deployments available. This takes a few minutes.

```bash
kubectl -n argocd get secret argocd-initial-admin-secret \
  -o jsonpath='{.data.password}' | base64 -d; echo
kubectl port-forward svc/argocd-server -n argocd 8080:443 &
```
Open <https://localhost:8080> (user `admin`, accept the self-signed certificate).

## Part B — Teach Argo CD what "healthy" means

**Before** applying the health checks, create an XR and watch the problem:

```bash
kubectl create ns gitops-demo
kubectl apply -f ../10-reuse-and-packaging/manifests/package/apis/xbucket.yaml
kubectl apply -f ../10-reuse-and-packaging/manifests/package/compositions/xbucket-aws.yaml
kubectl apply -f - <<'YAML'
apiVersion: platform.acme.io/v1alpha1
kind: XBucket
metadata: { name: demo, namespace: gitops-demo }
spec: { environment: dev, retentionDays: 7 }
YAML
```

Without a health check, Argo CD has no idea how to read an XR's status, so it would
report `Progressing` forever. Apply the checks:

```bash
kubectl apply -f manifests/argocd/health-check.yaml
kubectl rollout restart deploy/argocd-server -n argocd
kubectl rollout status deploy/argocd-server -n argocd
```

Read the Lua — it reads exactly the conditions you've been reading by hand since
Module 02:
```bash
sed -n '/Synced=False means/,/Progressing/p' manifests/argocd/health-check.yaml
```

> **Note the deliberate choice:** `Synced=False` reports **Degraded**, not
> Progressing, because it means a cloud API call *failed* — that's an error, not a
> slow start. `Synced=True, Ready=False` reports Progressing, because that's normal
> provisioning.

## Part C — The permanent-diff problem

This is the one that bites everybody.

```bash
kubectl get bucket -n gitops-demo -o yaml 2>/dev/null | head -40 || \
  kubectl get bucket -o yaml | head -40
```

Compare `spec.forProvider` with what the composition actually specified. The live
object has **more fields** — Crossplane late-initialized cloud-chosen defaults into
it (Module 02, §7).

**Argo CD sees those extra fields as drift from git, and reports `OutOfSync` forever.**

The fix:
```bash
grep -A8 'ignoreDifferences' manifests/argocd/applications.yaml
```
```yaml
ignoreDifferences:
  - group: "*.aws.upbound.io"
    kind: "*"
    jsonPointers:
      - /spec/forProvider
```

> **Why this matters more than it sounds:** a permanently-yellow application trains
> your team to ignore sync status. Once that happens, Argo CD is decoration — a real
> drift alert is indistinguishable from the noise everyone has learned to skip.
>
> The alternative is disabling late initialization entirely (Module 03) by omitting
> `LateInitialize` from `managementPolicies`. Pick one; don't leave it broken.

Read the sync waves and the deliberate `prune: false` choices:
```bash
grep -B2 -A4 'prune:' manifests/argocd/applications.yaml
```
✅ Expected: `prune: false` on providers and XRDs, `prune: true` on compositions.
The comments explain why — pruning a provider strands every resource it owned, and
pruning an XRD deletes its CRD, which deletes every XR of that kind.

## Part D — Build the CI pipeline

**This is the part that pays for itself.** Set up a realistic repo:

```bash
# Point this at your checkout of the course
CS="$(cd "$(git rev-parse --show-toplevel 2>/dev/null || echo /home/user/Project2.0)" && pwd)/crossplane-course"
WORK="$(mktemp -d)/platform"
mkdir -p "$WORK"/{apis,compositions,tests,ci}
cd "$WORK"
git init -q -b main

cp "$CS"/10-reuse-and-packaging/manifests/package/apis/xbucket.yaml            apis/
cp "$CS"/10-reuse-and-packaging/manifests/package/compositions/xbucket-aws.yaml compositions/
cp "$CS"/14-gitops-and-cicd/manifests/repo-layout/tests/functions.yaml          tests/
cp "$CS"/14-gitops-and-cicd/manifests/repo-layout/tests/xr-xbucket-aws.yaml     tests/
cp "$CS"/14-gitops-and-cicd/manifests/ci/test-compositions.sh                   ci/
cp "$CS"/14-gitops-and-cicd/manifests/ci/check-destructive.sh                   ci/
cp "$CS"/12-observability-and-debugging/solutions/consistency-check.sh          ci/
cp "$CS"/08-aws-iam-and-identity/solutions/policy-lint.sh                       ci/
chmod +x ci/*.sh

git add -A && git commit -qm "Initial platform"
echo "repo at $WORK"
```

Note what just happened: the CI pipeline is assembled from checks you wrote in
**Modules 08, 11, and 12**. Nothing here is new — this module only wires them into a
gate.

Run the pipeline on a clean repo:
```bash
./ci/test-compositions.sh
```
✅ Expected: all checks pass.
```
═══ 1. YAML is parseable ═══
  ✓ apis/xbucket.yaml
  ✓ compositions/xbucket-aws.yaml
═══ 2. Every composition renders ═══
  ✓ xr-xbucket-aws renders (3 resources)
...
🎉 All checks passed.
```

## Part E — CI catches the destructive change

Make the Module 11 change — rename a composed resource:

```bash
git checkout -q -b rename-resource
sed -i 's/setResourceNameAnnotation "bucket"/setResourceNameAnnotation "s3-bucket"/' \
  compositions/xbucket-aws.yaml
git diff --stat
```
✅ Expected: **one file, one line changed.** In a pull request this looks utterly
trivial.

```bash
git commit -aqm "Rename bucket resource for clarity"
./ci/check-destructive.sh --base-ref main
```
✅ Expected: **rejected**:
```
  ✗ xbucket-aws: COMPOSED RESOURCE NAMES CHANGED
      < crossplane.io/composition-resource-name: bucket
      > crossplane.io/composition-resource-name: s3-bucket

❌ This change renames one or more composed resources.
...On an S3 bucket that loses your objects. On an RDS instance that is your database.
```

🎉 **A three-character edit that would have destroyed every bucket in production,
caught in a pull request, in about two seconds, with no cluster.**

Confirm a *safe* change passes:
```bash
git checkout -q main && git checkout -q -b safe-change
sed -i 's/environment: {{ \$xr.spec.environment }}/environment: {{ $xr.spec.environment }}\n                  managed-by: crossplane/' \
  compositions/xbucket-aws.yaml 2>/dev/null || \
  python3 - <<'PY'
import pathlib
p = pathlib.Path('compositions/xbucket-aws.yaml'); s = p.read_text()
s = s.replace("                  team: {{ $ns }}",
              "                  team: {{ $ns }}\n                  managed-by: crossplane")
p.write_text(s)
PY
git commit -aqm "Add a managed-by tag"
./ci/check-destructive.sh --base-ref main
```
✅ Expected: `✅ No destructive composition changes.`

> **This is the highest-leverage automation in the whole course.** It is the one
> change where three characters, reviewed by two competent engineers, deletes a
> production database — and it takes a two-second check to make that impossible.

## Part F — The full gate

```bash
./ci/test-compositions.sh --base-ref main
cat "$CS"/14-gitops-and-cicd/manifests/ci/github-actions.yaml
```

Note the workflow's structure:
- The destructive check is a **separate job**, so a breaking change doesn't also mask
  ordinary test failures.
- It can be overridden by a `breaking-change-approved` **label** — a deliberate,
  visible, auditable act rather than a bypass.
- `publish` runs only on `main`, only after both jobs pass, and pushes a **real
  version** read from a `VERSION` file, never `:latest`.

Read the repo layout and its review rules:
```bash
cat "$CS"/14-gitops-and-cicd/manifests/repo-layout/README.md
```

> **The `CODEOWNERS` table is the real content there.** `apis/` needs two platform
> engineers because it's your public contract; `tests/` needs one of anyone because
> adding a test case should be frictionless. Friction in the wrong place is how
> people stop writing tests.

## Part G — Clean up

```bash
cd /home/user/Project2.0/crossplane-course
kubectl delete xbucket --all -n gitops-demo
kubectl delete ns gitops-demo
kill %1 2>/dev/null
# Optional — frees significant laptop RAM:
# kubectl delete namespace argocd
```

---

## What you learned
- GitOps matters more for a control plane than for apps, because **a composition
  change applies itself immediately to every existing XR**.
- Argo CD needs three adjustments: **sync waves** for ordering, **health checks** so
  XRs don't sit at Progressing forever, and **`ignoreDifferences`** so late
  initialization doesn't make everything permanently `OutOfSync`.
- **`prune: false` on providers and XRDs.** Pruning a provider strands its resources;
  pruning an XRD deletes every XR of that kind.
- Every composition check runs **without a cluster**, in seconds, on every PR.
- **The destructive-rename check is the one that pays for the whole pipeline.**
- Split the repo by **change rate and blast radius**, and encode that in `CODEOWNERS`.
- Promote by **pinned version**, never by branch.

➡️ **[challenge.md](./challenge.md)** then [Module 15: the Capstone](../15-capstone/).
