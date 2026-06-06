# Module 17 — Capstone: Ship the Whole Thing

**Goal:** bring everything together — deploy the complete Slack clone to the HA
cluster, run it under load, and prove it survives real failures. This is your
end-to-end, résumé-worthy artifact.

⏱️ ~4+ hours · 🎯 Prereq: Modules 00–16.

> No new concepts here. The capstone is about **integration and proof**: the app, the
> async pipeline, the real-time layer, the HA data tier, and the production hardening
> all working as one system you can stand behind.

---

## 1. What "done" looks like

A user can, on the deployed app over HTTPS:
- register, log in, and join a workspace;
- chat **live** across channels and DMs (messages, threads, reactions, typing, presence);
- get an **email** when @-mentioned while away, and see in-app notifications;
- **upload** a file and **search** history;
- have an external tool post via an **incoming webhook**, and an outgoing webhook fire
  on new messages;

…all while running **highly available**: multiple web/worker replicas spread across
nodes, an HA Postgres and Redis, autoscaling, and self-healing through failures.

## 2. The feature checklist (your acceptance test)

Tie each item back to the module that built it:

| ✓ | Capability | Module |
|---|------------|--------|
| ☐ | Email-based auth, JWT refresh rotation, logout | 03 |
| ☐ | Workspaces/channels/messages REST, cursor pagination | 04 |
| ☐ | Live messaging over WebSockets across replicas | 05, 15 |
| ☐ | Presence, unread counts, rate limiting | 06 |
| ☐ | @mention/DM notifications + email, digest | 07 |
| ☐ | Incoming + signed outgoing webhooks | 08 |
| ☐ | Next.js UI: optimistic send, typing, presence, theming | 09, 10 |
| ☐ | File uploads (presigned) + full-text search | 11 |
| ☐ | Containerized, one image / three roles | 12 |
| ☐ | Deployed on k8s: Deployments, Ingress, migration Job | 13 |
| ☐ | HA Postgres (CNPG) + HA Redis (operator) | 14 |
| ☐ | HPA, PDB, anti-affinity, zero-downtime rollouts | 15 |
| ☐ | TLS, NetworkPolicies, metrics, logs, Sentry | 16 |

## 3. Load test

Drive realistic traffic — many concurrent WebSocket clients posting messages — and
watch the system respond: web autoscales, latency stays bounded, the channel layer
fans out across replicas, workers keep the notification queue drained. Record p95
latency and the replica count at peak.

## 4. The failure drills (the real grade)

Run these **while the app is in use** and confirm it stays available or recovers fast:

1. **Kill a web pod** → traffic never stops; a replacement schedules.
2. **Kill a worker** mid-task → the task finishes (warm shutdown) or re-queues; no lost emails.
3. **Kill the Postgres primary** → operator promotes a replica; `-rw` repoints; app reconnects.
4. **Kill the Redis master** → Sentinel promotes a new master; real-time resumes.
5. **Drain a node** → PDBs + anti-affinity keep every service serving; pods reschedule.
6. **Roll out a new version** under load → zero failed requests.

## 5. Write it up

Produce a short **runbook + architecture doc**: the diagram, how to deploy, how to roll
back, what each failure drill proved, and known limitations / next steps. This is what
makes the project legible to others (and to interviewers).

---

## 6. Do the lab

Deploy the full stack to the HA cluster via Kustomize, run the acceptance checklist,
load-test, execute all six failure drills, and complete the verification in
[../VERIFY.md](../VERIFY.md).

👉 **[lab.md](./lab.md)**

Then the final challenge — make it *yours*: 👉 **[challenge.md](./challenge.md)**

---

## Key terms (see [GLOSSARY](../GLOSSARY.md))

acceptance test · load test · failure drill · runbook · SLO

**🎉 Finish →** You've built and shipped a production-ready Slack clone. The phone app
is a separate course — and it consumes the exact API and WebSocket layer you built here.
