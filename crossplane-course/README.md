# Crossplane: Orchestrate Applications *and* Infrastructure 🛰️

A hands-on, local-first course that takes you from **"I can deploy a Pod"** to
**"I designed and shipped my company's platform API"** — building real AWS
infrastructure and the applications that use it, from a single control plane,
entirely on your laptop, for free.

> **Who this is for:** You know Kubernetes basics (Pods, Deployments, Services,
> CRDs) and you want to build **platforms**, not just consume them. Maybe you've
> written Terraform and wondered why it drifts, why it needs a CI pipeline to run,
> and why your app deploy and your database deploy live in two different worlds.
> This course answers that.

> **Prerequisite course:** [`../kubernetes-course/`](../kubernetes-course/) —
> Modules 00–12. If you can explain what a controller reconcile loop does and
> write a Deployment from memory, you're ready.

---

## Why this course is different

- **You build a platform, not a demo.** Every module adds to one running control
  plane. By Module 15 you ship a self-service API where a developer writes 12 lines
  of YAML and gets a VPC-attached Postgres, an S3 bucket, a scoped IAM role, and a
  running app — with credentials wired in automatically.
- **Real AWS APIs, no AWS bill.** We run [LocalStack](https://localstack.cloud/)
  *inside* your kind cluster. The provider makes genuine AWS API calls to
  `s3.amazonaws.com`-shaped endpoints — you just point them somewhere free. Every
  manifest you write is the same YAML you'd apply against a real account, and
  Module 08 shows you exactly what changes when you do.
- **Crossplane v2, not v1 muscle memory.** Namespaced composite resources,
  composition **functions** (the only mode there is now), Managed Resource
  Activation Policies, and Operations. Most tutorials online still teach the v1
  claim/XR split that v2 deleted. We teach what ships today.
- **Applications *and* infrastructure.** This is the v2 superpower and the reason
  this course exists: one composite resource can create an RDS instance **and** the
  Deployment that connects to it. No more "Terraform provisions it, Helm consumes
  it, and a human copies the password between them."
- **Break things on purpose.** You'll delete a bucket behind Crossplane's back and
  watch it heal, wedge a composition on a bad patch, strand a resource by deleting
  its provider config, and debug all of it with `crossplane trace`.

---

## The arc

```
   ┌───────────────────────────────────────────────────────────────────┐
   │  PHASE 0 — Orientation                                            │
   │  00 Setup  →  01 Control-plane thinking (vs. Terraform/IaC)       │
   └───────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
   ┌───────────────────────────────────────────────────────────────────┐
   │  PHASE 1 — Consume infrastructure as Kubernetes objects           │
   │  02 Providers & Managed Resources  →  03 Lifecycle, drift, import │
   │        "kubectl apply an S3 bucket"                               │
   └───────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
   ┌───────────────────────────────────────────────────────────────────┐
   │  PHASE 2 — Build your own APIs                                    │
   │  04 XRDs & Compositions  →  05 Composition Functions              │
   │                          →  06 Apps + Infra in one XR             │
   │        "kubectl apply a Database, get 9 resources"                │
   └───────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
   ┌───────────────────────────────────────────────────────────────────┐
   │  PHASE 3 — Serious AWS                                            │
   │  07 Networking (VPC)  →  08 IAM & identity  →  09 Data services   │
   │        "a real, private, credentialed stack"                      │
   └───────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
   ┌───────────────────────────────────────────────────────────────────┐
   │  PHASE 4 — Run it like a platform team                            │
   │  10 Reuse & packaging  →  11 Day-2 Operations                     │
   │  12 Observability      →  13 Security & multi-tenancy             │
   │                        →  14 GitOps & CI/CD                       │
   └───────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
   ┌───────────────────────────────────────────────────────────────────┐
   │  15 CAPSTONE — Ship a self-service platform API end to end        │
   └───────────────────────────────────────────────────────────────────┘
```

---

## Prerequisites

- A Mac (Apple Silicon or Intel) or Linux box with **~10 GB RAM free** and ~30 GB disk.
  Crossplane plus a provider plus LocalStack is heavier than the Kubernetes course.
- **Kubernetes fundamentals.** You should be comfortable with `kubectl`, Deployments,
  Services, Secrets, and — importantly — **CRDs and controllers**. Module 01 refreshes
  the controller mental model but does not teach Kubernetes from scratch.
- Docker + `kind` + `kubectl` + `helm` installed (the Kubernetes course's Module 00
  installs all of these; Module 00 here adds the `crossplane` CLI).
- **No AWS account required.** Module 08 explains what to change if you want to run
  against a real one, and how to do it without leaking credentials.

---

## The learning path

Work through the modules **in order** — each builds on the last, and the control
plane you build accumulates.

| # | Module | You'll learn to… | Est. time |
|---|--------|------------------|-----------|
| 00 | [Setup & Orientation](./00-setup/) | Install Crossplane + LocalStack on a kind cluster | 1 h |
| 01 | [Control-Plane Thinking](./01-control-plane-thinking/) | Explain *why* a control plane beats a `terraform apply` pipeline | 1.5 h |
| 02 | [Providers & Managed Resources](./02-providers-and-managed-resources/) | Install a provider, configure it, `kubectl apply` an S3 bucket | 2.5 h |
| 03 | [Managed Resource Lifecycle](./03-managed-resource-lifecycle/) | Drift correction, management/deletion policies, importing existing infra | 2.5 h |
| 04 | [XRDs & Compositions](./04-xrds-and-compositions/) | Define your own API and implement it with a Composition | 3 h |
| 05 | [Composition Functions](./05-composition-functions/) | Patch-and-transform, Go templating, pipelines, `crossplane render` | 3 h |
| 06 | [Composing Applications](./06-composing-applications/) | Ship app **and** infra from one XR — the v2 superpower | 3 h |
| 07 | [AWS Networking](./07-aws-networking/) | Compose a VPC, subnets, routing, and security groups | 3 h |
| 08 | [AWS IAM & Identity](./08-aws-iam-and-identity/) | IAM roles/policies, least privilege, and how to authenticate for real | 3 h |
| 09 | [AWS Data Services](./09-aws-data-services/) | RDS, DynamoDB, and wiring connection secrets into apps | 3 h |
| 10 | [Reuse & Packaging](./10-reuse-and-packaging/) | EnvironmentConfigs, `Usage` ordering, and shipping a Configuration package | 3 h |
| 11 | [Day-2 Operations](./11-day-two-operations/) | Composition revisions, safe upgrades, `Operation`/`CronOperation` | 2.5 h |
| 12 | [Observability & Debugging](./12-observability-and-debugging/) | `crossplane trace`, conditions, events, metrics — and 5 broken stacks | 3 h |
| 13 | [Security & Multi-Tenancy](./13-security-and-multitenancy/) | RBAC, namespace isolation, credential blast radius, policy | 3 h |
| 14 | [GitOps & CI/CD](./14-gitops-and-cicd/) | Argo CD + Crossplane, and testing compositions in CI | 3 h |
| 15 | [Capstone](./15-capstone/) | Ship a complete, documented, self-service platform API | 4+ h |

**Total: a realistic ~45 hours of focused, hands-on work.**

---

## What you'll be able to do at the end

These are the course's learning goals. Check yourself against them when you finish —
each one is exercised by a specific challenge, and all of them by the capstone.

**Fundamentals**
1. Explain the difference between a *control plane* and a *provisioning tool*, and
   argue when each is the right choice.
2. Describe the reconcile loop, and predict what Crossplane does when reality and
   desired state diverge.
3. Read any Crossplane resource's `status.conditions` and say what's wrong.

**Consuming infrastructure**
4. Install and configure a provider family, and activate only the managed resources
   you need with a `ManagedResourceActivationPolicy`.
5. Provision AWS resources declaratively and predict their reconcile behavior.
6. Import existing, hand-built cloud infrastructure into Crossplane without
   recreating or destroying it.
7. Choose the right `managementPolicies` and `deletionPolicy` for a given risk profile.

**Building platform APIs**
8. Design a composite resource API (XRD) that a developer can use without knowing AWS.
9. Implement it with a composition function pipeline, using patch-and-transform and
   Go templating where each is appropriate.
10. Compose applications and infrastructure together in one XR, wiring connection
    details from a database into a Deployment automatically.
11. Test compositions locally with `crossplane render` and `crossplane validate`, with
    no cluster running.

**AWS depth**
12. Compose a working VPC: subnets, internet gateway, route tables, security groups.
13. Write least-privilege IAM policies and roles, and explain IRSA well enough to
    configure it.
14. Authenticate a provider four ways (static keys, IRSA, web identity, and
    cross-account role assumption) and pick the right one.
15. Provision RDS and surface its credentials to an application as a Kubernetes Secret
    without ever printing the password.

**Operating a platform**
16. Package a platform API as a Configuration and version it for consumers.
17. Roll out a breaking composition change safely using composition revisions.
18. Diagnose a stuck stack in under five minutes using `crossplane trace` and events.
19. Scope RBAC and credentials so one tenant cannot provision into another's account.
20. Run the whole thing through GitOps with Argo CD, with composition tests in CI.

---

## How each module is structured

```
NN-topic/
├── README.md      ← Concepts in plain language. Read this first.
├── lab.md         ← Step-by-step guided lab with expected output. Do this second.
├── manifests/     ← The YAML files the lab applies.
├── challenge.md   ← An unguided task to prove you understood it. Do this third.
└── solutions/     ← Reference answers — peek only after you've tried.
```

**The rhythm for every module:** read `README.md` → follow `lab.md` hands-on →
attempt `challenge.md` solo → check `solutions/`.

---

## Reference material (keep these open)

- **[cheatsheets/crossplane-cli.md](./cheatsheets/crossplane-cli.md)** — every `crossplane` and `kubectl` command you'll need
- **[cheatsheets/composition-functions.md](./cheatsheets/composition-functions.md)** — patch types, transforms, and function inputs
- **[cheatsheets/aws-resources.md](./cheatsheets/aws-resources.md)** — the AWS managed resources used in this course, with their gotchas
- **[cheatsheets/troubleshooting.md](./cheatsheets/troubleshooting.md)** — "my XR is stuck" decision tree
- **[GLOSSARY.md](./GLOSSARY.md)** — every term defined in plain English
- **[VERIFY.md](./VERIFY.md)** — end-to-end smoke test to confirm your setup works

---

## Quick start

```bash
# 1. Install the toolchain and create the cluster (Module 00 explains each step)
cd crossplane-course/00-setup
./scripts/create-cluster.sh        # kind cluster: xp-course

# 2. Install Crossplane + LocalStack + the AWS provider
./scripts/install-crossplane.sh
./scripts/install-localstack.sh

# 3. Confirm everything is healthy
./scripts/verify-setup.sh

# 4. Start learning
cd ../01-control-plane-thinking && cat README.md
```

When you're done for the day, free up your laptop's resources:

```bash
crossplane-course/00-setup/scripts/delete-cluster.sh
```

---

## Where this fits in the curriculum

```
linux-course ──► ansible-course ──┐
                                  ├──► kubernetes-course ──► crossplane-course ──► slack-clone-course
docker (in kubernetes-course) ────┘                             (you are here)
```

- **[kubernetes-course](../kubernetes-course/)** is a hard prerequisite — Crossplane
  *is* a Kubernetes controller, and every debugging skill transfers directly.
- **[ansible-course](../ansible-course/)** teaches push-based, imperative-ish
  automation. Module 01 compares it head-to-head with the control-plane model so you
  can articulate when each wins.
- **[slack-clone-course](../slack-clone-course/)** deploys a real multi-tier app on
  Kubernetes. After this course, try re-platforming its Postgres onto an XR.

---

## Philosophy

- **Learn by doing.** 80% of your time is in a terminal, not reading.
- **Production patterns, not toys.** Least-privilege IAM, connection secrets, RBAC,
  composition revisions, GitOps — the things that bite you at 3 a.m.
- **Deliberate failure.** You cannot operate a platform you've never seen break.
- **Local-first and free.** No AWS account, no Upbound subscription, no paid tiers.
- **Modern only.** Crossplane v2.x. If a pattern was removed in v2, we tell you it
  existed and then move on.

---

Ready? **→ [Start with Module 00: Setup & Orientation](./00-setup/)**
