# Module 14 — GitOps & CI/CD

**Goal:** make git the only way anything reaches your control plane, and catch
destructive composition changes in a pull request rather than in production.

⏱️ ~3 hours · 🎯 Prereq: Modules 11–13.

---

## 1. Why GitOps matters more for Crossplane

For applications, GitOps is a nice-to-have: it gives you review, history, and easy
rollback. For a control plane it is closer to essential, because of something you've
now seen repeatedly:

**A composition change applies itself immediately, to all existing XRs, with no
approval step.** Module 11's rename destroyed every bucket. Module 04's selector
change deleted a whole stack. Module 07's one-word edit removed live subnets.

Every one of those would have been a **pull request** under GitOps — reviewable,
diffable, and testable before it ever reached a cluster.

Combined with Module 13's RBAC, GitOps gives you the property that matters:
**nobody has write access to the cluster, so `kubectl delete` isn't a thing anyone
can do.**

## 2. The layers of a Crossplane GitOps repo

Not everything belongs in one place or moves at one speed:

```
platform-repo/
├── bootstrap/          ← Crossplane itself, providers, functions
│   └── (rarely changes; a human applies these)
├── apis/               ← XRDs — YOUR PUBLIC CONTRACT. Review hardest.
├── compositions/       ← implementations. Review carefully.
├── config/             ← EnvironmentConfigs, ProviderConfigs (no secrets!)
└── tenants/            ← namespaces, RBAC, quotas
```

And separately, per team:
```
team-payments-repo/
└── infrastructure/     ← XRs. The team owns these.
```

**Why split?** The platform repo changes rarely and affects everyone; a team's XRs
change often and affect one team. Different review rules, different owners, different
blast radius.

## 3. Argo CD and Crossplane

Argo CD works with Crossplane, with three adjustments worth knowing.

**a) Order matters at bootstrap.** XRDs must exist before Compositions reference them,
and providers must be healthy before their CRDs exist. Use sync waves:
```yaml
metadata:
  annotations:
    argocd.argoproj.io/sync-wave: "1"      # providers
    # "2" for XRDs, "3" for compositions
```

**b) Health checks need teaching.** Argo CD doesn't natively know what a healthy XR
looks like. Give it a Lua health check reading Crossplane's conditions — otherwise
every XR shows as `Progressing` forever and your sync never completes.

**c) Late initialization causes permanent diffs.** Crossplane writes cloud-chosen
defaults back into `spec.forProvider` (Module 02). Argo CD sees fields the git
manifest doesn't have and reports `OutOfSync` forever. Fix with `ignoreDifferences`:
```yaml
ignoreDifferences:
  - group: "*.aws.upbound.io"
    kind: "*"
    jsonPointers:
      - /spec/forProvider
```
(Or turn late initialization off — Module 03.)

> **This third one bites everybody.** A permanently-`OutOfSync` application trains
> your team to ignore sync status, which defeats the purpose of running Argo CD.

## 4. Testing compositions in CI

You have the tools already; this module assembles them into a pipeline.

| Check | Tool | Catches |
|-------|------|---------|
| Does it render? | `crossplane render` | Template errors |
| Is the output valid? | `crossplane validate` | Schema violations |
| Right resources? | render + assertions (Module 05) | Missing or extra resources |
| Internally consistent? | `consistency-check.sh` (Module 12) | The "green but wrong" class |
| Destructive change? | `preflight.sh` (Module 11) | Renames that recreate infrastructure |
| Safe IAM? | `policy-lint.sh` (Module 08) | Wildcards, escalation paths |

**All of these run without a cluster**, in seconds, on every pull request. That is the
single highest-leverage thing you can build for a Crossplane platform.

```bash
crossplane render xr.yaml composition.yaml functions.yaml \
  | crossplane validate crds/ -
```

## 5. The check that matters most

Of everything above, one deserves special emphasis:

```bash
./preflight.sh <kind> old-composition.yaml new-composition.yaml xr.yaml functions.yaml
```

**A renamed composed resource is invisible in an API diff and destroys infrastructure
for every existing XR.** It is the only change in Crossplane where a three-character
edit reviewed by two competent engineers can delete a production database.

Make CI fail on it. Require an explicit label (`breaking-change-approved`) to merge
anyway.

## 6. Secrets in a GitOps repo

**Never commit:** provider credentials, database passwords, API tokens.

**Safe to commit:** XRDs, Compositions, XRs, EnvironmentConfigs (account IDs and VPC
IDs are not secrets), ProviderConfigs that use IRSA.

For anything genuinely secret, use External Secrets Operator or Sealed Secrets — or
better, arrange not to have one: **IRSA means there is no credential to store**
(Module 08), and `autoGeneratePassword` means no human ever handles the database
password (Module 09).

> The best secret management is not needing the secret.

## 7. Promotion between environments

```
dev cluster  ──►  staging cluster  ──►  prod cluster
     ▲                  ▲                    ▲
     └── same Configuration package, different tag
```

Promotion is **bumping a version tag** in the environment's repo directory:

```yaml
# environments/prod/configuration.yaml
spec:
  package: ghcr.io/acme/platform:v1.4.2      # dev is already on v1.5.0
```

This is why Module 10's packaging matters: an environment pins a **version**, not a
git branch. Branch-based promotion means prod is running whatever `main` looked like
at an unpredictable moment.

---

## Do the lab
Install Argo CD, put your platform under GitOps, fix the permanent-diff problem, and
build a CI pipeline that rejects a destructive composition change.
👉 **[lab.md](./lab.md)**

Then: 👉 **[challenge.md](./challenge.md)**

## Manifests
- [`argocd/`](./manifests/argocd/) — Applications, sync waves, health checks
- [`repo-layout/`](./manifests/repo-layout/) — a complete example repo structure
- [`ci/`](./manifests/ci/) — a GitHub Actions workflow and the test script it runs

## Key terms
GitOps · Argo CD · Application · sync wave · health check · `ignoreDifferences` ·
drift (Argo's sense vs. Crossplane's) · promotion · pinned version · pull-request gate

**Next →** [Module 15: Capstone](../15-capstone/)
