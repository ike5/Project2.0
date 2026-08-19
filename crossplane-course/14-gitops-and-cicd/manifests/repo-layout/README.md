# Platform repository layout

A working structure for a Crossplane platform repo. The point of the split is that
**different things change at different speeds, affect different people, and deserve
different review rules.**

```
platform/
├── VERSION                 ← the version CI publishes (e.g. 1.4.2)
├── crossplane.yaml         ← package metadata + dependsOn (Module 10)
├── bootstrap/              ← Crossplane, providers, functions
│   ├── providers.yaml
│   ├── functions.yaml
│   └── mrap.yaml
├── apis/                   ← XRDs — YOUR PUBLIC CONTRACT
│   ├── xnetwork.yaml
│   ├── xdatabase.yaml
│   └── xbucket.yaml
├── compositions/           ← implementations
│   ├── xnetwork-aws.yaml
│   ├── xdatabase-aws.yaml
│   └── xbucket-aws.yaml
├── config/                 ← EnvironmentConfigs, ProviderConfigs (NO SECRETS)
│   ├── environments.yaml
│   └── providerconfigs.yaml
├── tenants/                ← namespaces, RBAC, quotas (Module 13)
│   ├── tenant-alpha.yaml
│   └── policies.yaml
├── tests/                  ← sample XRs that CI renders
│   ├── functions.yaml
│   ├── xr-xdatabase.yaml
│   └── xr-xbucket.yaml
└── ci/
    ├── test-compositions.sh
    ├── check-destructive.sh
    ├── consistency-check.sh    (from Module 12)
    └── policy-lint.sh          (from Module 08)
```

## Review rules per directory

| Directory | Reviewers | Why |
|-----------|-----------|-----|
| `apis/` | 2 platform engineers | It is your public contract. A change here affects every consumer, and some changes cannot be undone. |
| `compositions/` | 2 platform engineers | A change applies to every existing XR immediately. |
| `bootstrap/` | 2 + a scheduled window | Provider upgrades can trigger cluster-wide drift (Module 11). |
| `config/` | 1 platform engineer | Environment facts. Wrong values break one environment. |
| `tenants/` | 1 platform engineer + the tenant | Their isolation, their quota. |
| `tests/` | 1 anyone | Adding a test case should be frictionless. |

Encode this in `CODEOWNERS`:
```
/apis/          @acme/platform-leads
/compositions/  @acme/platform-leads
/bootstrap/     @acme/platform-leads
/config/        @acme/platform
/tenants/       @acme/platform
/tests/         @acme/engineering
```

## What must never be committed

- Provider credentials, database passwords, API tokens.
- Anything under `crossplane-system` that contains a `Secret`.

**Safe to commit:** XRDs, Compositions, XRs, EnvironmentConfigs (account IDs and VPC
IDs are not secrets), and ProviderConfigs that use `source: IRSA`.

> The best secret management is not needing the secret. IRSA (Module 08) means no
> credential exists to store; `autoGeneratePassword` (Module 09) means no human ever
> handles the database password.

## Team repos are separate

```
team-payments/
└── infrastructure/
    ├── database.yaml       ← an XDatabase
    └── buckets.yaml        ← XBuckets
```

A team changing their own database size should not need a platform engineer. A
platform engineer changing the composition behind it should be reviewed by someone
who understands all 40 consumers. Different repos make that distinction structural
rather than a matter of discipline.
