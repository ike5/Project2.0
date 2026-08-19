# Module 15 — Capstone: Ship a Self-Service Platform

**Goal:** build, secure, package, and operate a complete platform API that a developer
can use without knowing anything about AWS — and defend your design decisions.

⏱️ 4+ hours · 🎯 Prereq: every previous module.

---

## The brief

You are the platform team at ACME. Today, a product engineer who needs a new service
files a ticket, waits three days, and receives a database endpoint and a password in a
Slack message.

**Your job: replace that with this.**

```yaml
apiVersion: platform.acme.io/v1alpha1
kind: Service
metadata:
  name: checkout
  namespace: team-payments
  labels:
    acme.io/owner: team-payments
spec:
  image: acme/checkout:2.1.0
  size: medium
  database: true
  storage: true
  host: checkout.acme.example
```

Twelve lines, applied by the developer into their own namespace. Out of it comes a
private network, a Postgres database, an S3 bucket, a scoped IAM role, a running
Deployment with credentials already wired in, a Service, and an Ingress.

**The developer never sees a password, an ARN, a subnet, or an IAM policy.**

---

## Requirements

### Must have — the platform API

- [ ] **One API** (`Service`) that composes everything a service needs.
- [ ] **T-shirt sizing** (`small`/`medium`/`large`) mapped to instance classes and
      replica counts by the platform, never exposed as raw AWS values.
- [ ] **Optional components**: `database` and `storage` genuinely absent when `false`
      — not merely configured differently.
- [ ] **Connection details** flowing from the database into the Deployment
      automatically, with **your platform's key names**, not the provider's.
- [ ] **Status** surfacing what a developer needs: the URL, the bucket name, and the
      database host. Never the password.

### Must have — safety

- [ ] **Immutable fields** enforced in the XRD: anything whose change would destroy
      data is rejected at `kubectl apply` with a clear message.
- [ ] **Environment-driven protection**: production gets `deletionProtection`,
      `deletionPolicy: Orphan`, backups, and multi-AZ. Development does not.
- [ ] **Least-privilege IAM**, generated from what the service actually asked for.
      No wildcards.
- [ ] **No secrets in git.** Passwords generated, never typed.

### Must have — multi-tenancy

- [ ] **Two tenants**, isolated: RBAC, quotas, and a per-tenant `ProviderConfig`.
- [ ] Developers **cannot** create managed resources directly.
- [ ] Developers **cannot** delete production resources.
- [ ] An **admission policy** enforcing at least one rule RBAC cannot express.

### Must have — operations

- [ ] **Packaged** as a versioned Configuration with correct `dependsOn`.
- [ ] **CI** that renders, validates, and rejects a destructive composition change.
- [ ] A **runbook** for rolling out a composition change to live services.
- [ ] **Documentation** a developer could use without asking you anything.

### Stretch

- [ ] Read replicas, with a `DATABASE_READ_HOST` that is correct at zero replicas.
- [ ] A second Composition (a `minimal` tier) selected by label.
- [ ] `Usage` objects for deterministic teardown.
- [ ] An end-to-end test that uses the XR's published output.
- [ ] Argo CD, with health checks and `ignoreDifferences` configured.

---

## Suggested build order

Don't build it all at once. Each stage should work before you start the next.

```
Stage 1  The API              → XRD only. kubectl explain works, validation rejects bad input.
Stage 2  Infrastructure       → network + database + bucket. crossplane trace is green.
Stage 3  The application      → Deployment + Service + Ingress, credentials wired in.
Stage 4  Identity             → IAM role, IRSA-shaped, least privilege.
Stage 5  Safety               → immutability rules, prod protections.
Stage 6  Tenancy              → namespaces, RBAC, quotas, admission policy.
Stage 7  Packaging + CI       → xpkg, tests, the destructive-change gate.
Stage 8  Documentation        → the developer guide and the runbook.
```

**Use `crossplane render` throughout.** Stages 1–5 are almost entirely offline work;
you shouldn't be waiting on a cloud API to find out your template has a typo.

---

## What "done" looks like

Run these and they all pass:

```bash
# A developer, with a developer's permissions, can ship a service
kubectl apply -f examples/service.yaml \
  --as=system:serviceaccount:team-payments:developer
kubectl wait service.platform.acme.io/checkout -n team-payments \
  --for=condition=Ready --timeout=10m

# It actually works, end to end
curl -s http://localhost/ | jq          # via the Ingress
kubectl logs -n team-payments deploy/checkout | grep "database is up"

# The developer cannot subvert it
./tests/attacks.sh                      # every attack denied

# CI catches the dangerous change
./ci/check-destructive.sh --base-ref main

# It ships as a versioned artifact
crossplane xpkg build --package-root=. --package-file=platform.xpkg
```

---

## The write-up

Alongside the code, produce a short design document. **This is not padding** — it's
the part that distinguishes an engineer who built a thing from one who can be trusted
to own a platform.

Answer these:

1. **What did you deliberately NOT let developers configure, and why?** Name at least
   three, with the failure each omission prevents.
2. **Where is your platform's security boundary**, and what happens if someone gets
   past it?
3. **Which of your controls are enforced by Kubernetes and which by AWS?** Which would
   survive a serious misconfiguration of your cluster?
4. **What breaks if you rename a composed resource?** Show that your CI catches it.
5. **What did you choose NOT to build**, and what would make you reconsider?

That last one matters most. A platform that tries to do everything does nothing well,
and an engineer who can't name their scope boundary hasn't chosen one.

---

## Grading yourself

The rubric in [`solutions/RUBRIC.md`](./solutions/RUBRIC.md) is the honest one — it
weights judgement over feature count. Score yourself before looking at the reference
implementation in [`solutions/`](./solutions/).

> **Peek only after you've built yours.** The reference solution is one set of
> defensible choices, not the answer. Where yours differs, be able to say why.

---

## Reference material

- [`starter/`](./starter/) — scaffolding to build on, with `TODO` markers
- [`solutions/`](./solutions/) — a complete reference implementation
- [`solutions/RUBRIC.md`](./solutions/RUBRIC.md) — the scoring rubric
- Every previous module's `manifests/` — you wrote most of these pieces already

## What you'll be able to say afterwards

You designed a platform API, implemented it with composition functions, secured it for
multiple tenants, packaged it for distribution, and built the automation that stops it
destroying production. That's the job.

Check yourself against the **20 learning goals** in the
[course README](../README.md#what-youll-be-able-to-do-at-the-end). The capstone
exercises all of them.

---

**← Back to [the course README](../README.md)**
