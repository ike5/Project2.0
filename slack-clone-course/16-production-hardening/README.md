# Module 16 — Production Hardening & Observability

**Goal:** make the deployment trustworthy — structured logs, metrics + dashboards,
error tracking, TLS, network policies, resource governance, and a CI/CD outline.

⏱️ ~3 hours · 🎯 Prereq: Module 15 (HA app). A working cluster.

> "It runs" isn't "it's production-ready." This module adds the things you only miss
> at 3am during an incident: visibility, security boundaries, and safe delivery.

---

## 1. Observability: logs, metrics, traces

- **Structured logging.** Switch Django/Celery to **JSON logs** so a log aggregator
  (Loki, ELK, CloudWatch) can index fields — request id, user, status — instead of
  grepping prose. Include a request id you can follow across services.
- **Metrics.** Expose Prometheus metrics (`django-prometheus`) — request latency,
  error rate, DB query time, plus a custom **active WebSocket connections** gauge — and
  view them in **Grafana**. The four "golden signals" (latency, traffic, errors,
  saturation) are your dashboard.
- **Error tracking.** Wire **Sentry** so unhandled exceptions (web *and* Celery) page
  you with a stack trace, release, and breadcrumbs — far better than tailing logs.

## 2. Security boundaries

- **TLS everywhere.** `k8s/hardening/tls.yaml` uses **cert-manager** to issue a
  certificate and serve HTTPS at the ingress (self-signed locally; Let's Encrypt in
  prod). WebSockets become `wss://`.
- **NetworkPolicies.** `k8s/hardening/networkpolicy.yaml` is **default-deny**, then
  allows only needed flows: only backend pods may reach Postgres; only the ingress may
  reach web. A compromised pod can't freely pivot. (Needs a policy-enforcing CNI like
  Calico.)
- **Least privilege.** Run as non-root (already in the Dockerfile), drop Linux
  capabilities, mount a read-only root filesystem where possible, and scope RBAC tightly.

## 3. Secrets, for real

The committed Secret is a placeholder. In production, secrets come from a manager —
**Sealed Secrets**, **External Secrets Operator** (pulling from Vault/AWS Secrets
Manager), or your cloud's CSI driver — so plaintext never touches git. Rotate
`SECRET_KEY` and DB credentials on a schedule.

## 4. Resource governance

Every container already sets **requests/limits** (Module 13) so the scheduler can pack
nodes and one pod can't starve others. Add a namespace **ResourceQuota** and
**LimitRange** so the `slack` namespace can't exceed its share and every pod gets sane
defaults.

## 5. CI/CD outline

A safe pipeline for this repo:

```
push → CI: ruff + pytest (backend), tsc + next build (frontend), build images, scan
     → push images to a registry by immutable digest
     → CD: apply migrate Job, wait for success
          → kubectl set image / Argo CD sync (GitOps)
          → rolling update with readiness gating; auto-rollback on failed health
```

GitOps (Argo CD) makes the cluster's desired state a git repo — every change is a
reviewed commit, and drift self-heals. (The Kubernetes course covers Argo CD in depth.)

## 6. The hardening checklist

- [ ] JSON logs with a request id; shipped to an aggregator.
- [ ] Prometheus metrics + Grafana golden-signals dashboard.
- [ ] Sentry on web and Celery.
- [ ] HTTPS at the ingress; `wss://` for sockets; HSTS.
- [ ] Default-deny NetworkPolicies; non-root, least-privilege pods.
- [ ] Secrets from a manager, not git; rotation plan.
- [ ] Requests/limits + ResourceQuota/LimitRange.
- [ ] CI (test+scan) and CD (migrate→rollout→auto-rollback).

---

## 7. Do the lab

Turn on JSON logging and Sentry, install Prometheus + Grafana and view the dashboard,
enable TLS with cert-manager, and apply the NetworkPolicies (then prove a denied flow).

👉 **[lab.md](./lab.md)**

Then test yourself: 👉 **[challenge.md](./challenge.md)**

---

## Key terms (see [GLOSSARY](../GLOSSARY.md))

structured logging · golden signals · Prometheus/Grafana · Sentry · cert-manager · NetworkPolicy · ResourceQuota · GitOps

**Next →** [Module 17: Capstone](../17-capstone/)
