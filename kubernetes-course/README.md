# Kubernetes: From Scratch to Mastery 🚀

A hands-on, local-first course that takes you from **zero container knowledge**
to **confidently running real applications on Kubernetes** — entirely on your Mac,
for free, with no cloud account required.

> **Who this is for:** You're new to containers and Kubernetes and want practical,
> real-world skills (not exam cramming). Every lesson is paired with a runnable lab
> on a real multi-node cluster running on your laptop.

---

## Why this course is different

- **Learn by doing.** Every module = short concepts + a guided lab + a challenge you solve yourself.
- **Real multi-node cluster, locally.** We use [kind](https://kind.sigs.k8s.io/)
  (Kubernetes IN Docker) so you get a genuine 3-node cluster on your Mac — perfect
  for actually *seeing* scheduling, networking, and high-availability behavior that
  a single-node setup hides.
- **Break things on purpose.** You'll learn to debug `CrashLoopBackOff`,
  `ImagePullBackOff`, `Pending`, and friends — because that's the job.
- **Production patterns, not toys.** Helm, Kustomize, RBAC, NetworkPolicies, HPA,
  GitOps with Argo CD, and a full multi-tier capstone.

---

## Prerequisites

- A Mac (Apple Silicon or Intel) with **~8 GB RAM free** and ~20 GB disk.
- Comfort with a terminal (`cd`, `ls`, editing files). **No prior Docker or
  Kubernetes knowledge needed** — Module 01 starts at containers.
- [Homebrew](https://brew.sh/) installed (the course uses it to install tools).

---

## The learning path

Work through the modules **in order** — each builds on the last.

| # | Module | You'll learn to… | Est. time |
|---|--------|------------------|-----------|
| 00 | [Setup & Orientation](./00-setup/) | Install the toolchain and spin up your 3-node cluster | 45 min |
| 01 | [Containers & Docker Primer](./01-containers-docker/) | Build & run container images; understand *why* orchestration | 1.5 h |
| 02 | [Kubernetes Fundamentals](./02-k8s-fundamentals/) | Understand the architecture and drive `kubectl` | 1.5 h |
| 03 | [Pods & Core Workloads](./03-pods-and-workloads/) | Deploy, scale, roll out, and roll back apps | 2 h |
| 04 | [Configuration & Lifecycle](./04-configuration/) | Externalize config, add health probes, set resources | 2 h |
| 05 | [Networking: Services & Ingress](./05-networking-services-ingress/) | Expose apps, service discovery, routing with Ingress | 2 h |
| 06 | [Storage](./06-storage/) | Persist data with PVs, PVCs, and StorageClasses | 1.5 h |
| 07 | [Controllers: Jobs & StatefulSets](./07-controllers-jobs-statefulsets/) | DaemonSets, Jobs, CronJobs, StatefulSets | 2 h |
| 08 | [Scheduling & Scaling](./08-scheduling-and-scaling/) | Control pod placement; autoscale with HPA | 2 h |
| 09 | [Observability & Debugging](./09-observability-and-debugging/) | Diagnose failures; install Prometheus + Grafana | 2.5 h |
| 10 | [Packaging: Helm & Kustomize](./10-packaging-helm-kustomize/) | Template and manage apps across environments | 2.5 h |
| 11 | [Security: RBAC & Policies](./11-security-rbac-policies/) | Least-privilege access, NetworkPolicies, Pod Security | 2.5 h |
| 12 | [Production & GitOps](./12-production-and-gitops/) | Quotas, zero-downtime, GitOps with Argo CD | 2.5 h |
| 13 | [Capstone Project](./13-capstone/) | Ship a full multi-tier app end-to-end | 3+ h |

**Total: a realistic ~30 hours of focused, hands-on work.** Take it at your own pace.

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

- **[cheatsheets/kubectl.md](./cheatsheets/kubectl.md)** — the commands you'll use 100x a day
- **[cheatsheets/yaml-anatomy.md](./cheatsheets/yaml-anatomy.md)** — how to read any manifest
- **[cheatsheets/troubleshooting.md](./cheatsheets/troubleshooting.md)** — "my pod won't start" decision tree
- **[GLOSSARY.md](./GLOSSARY.md)** — every term defined in plain English
- **[VERIFY.md](./VERIFY.md)** — end-to-end smoke test to confirm your setup works

---

## Shared sample apps

- **[apps/web-api/](./apps/web-api/)** — a tiny Flask API used in most labs (fast to build).
- **[apps/guestbook/](./apps/guestbook/)** — the multi-tier app you'll ship in the capstone.

---

## Quick start

```bash
# 1. Install everything (Module 00 explains each tool)
cd kubernetes-course/00-setup
cat README.md            # follow the install steps

# 2. Create your cluster
./scripts/create-cluster.sh

# 3. Confirm it's healthy (should show 3 Ready nodes)
./scripts/verify-setup.sh

# 4. Start learning
cd ../01-containers-docker && cat README.md
```

When you're done for the day, free up your laptop's resources:

```bash
kubernetes-course/00-setup/scripts/delete-cluster.sh
```

---

Ready? **→ [Start with Module 00: Setup & Orientation](./00-setup/)**
