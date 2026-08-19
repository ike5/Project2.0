# Capstone starter

Scaffolding with `TODO` markers. Fill them in, in the build order from the module
README — each stage should work before you start the next.

```
starter/
├── apis/service.yaml            ← Stage 1: the API (TODOs)
├── compositions/service-aws.yaml← Stages 2-5: the implementation (TODOs)
├── config/                      ← ProviderConfigs, EnvironmentConfigs
├── tenants/                     ← Stage 6: namespaces, RBAC, quotas
├── tests/                       ← render fixtures and attack tests
├── ci/                          ← copy your checks from Modules 08, 11, 12
└── examples/service.yaml        ← what a developer writes
```

## Work offline

Stages 1–5 are almost entirely `crossplane render` work:

```bash
crossplane render examples/service.yaml compositions/service-aws.yaml tests/functions.yaml
```

Three seconds per iteration instead of three minutes. Don't wait on a cloud API to
discover a template typo.

## Assemble your CI from what you already wrote

```bash
CS=../..            # the course root
cp "$CS"/12-observability-and-debugging/solutions/consistency-check.sh ci/
cp "$CS"/08-aws-iam-and-identity/solutions/policy-lint.sh              ci/
cp "$CS"/14-gitops-and-cicd/manifests/ci/check-destructive.sh          ci/
cp "$CS"/14-gitops-and-cicd/manifests/ci/test-compositions.sh          ci/
cp "$CS"/13-security-and-multitenancy/manifests/attacks.sh             tests/
chmod +x ci/*.sh tests/*.sh
```

Nothing in the capstone's CI is new. You wrote all of it.
