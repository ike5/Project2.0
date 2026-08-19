# Capstone rubric

Score yourself **before** reading the reference implementation.

This rubric deliberately weights **judgement over feature count**. A platform with
three well-chosen fields and correct safety properties beats one with twenty fields
that recreates a database when someone changes a tag.

---

## 1. API design (25 points)

| | Points |
|---|---|
| A developer can ship a service in ≤15 lines with no AWS knowledge | 5 |
| Fields express **intent** (`size: medium`), never implementation (`db.t3.small`) | 5 |
| Optional components are genuinely **absent** when false, not reconfigured | 5 |
| Schema validation rejects bad input at `kubectl apply` with a useful message | 5 |
| `status` gives developers what they need — and **never the password** | 5 |

**Deduct 5** for every field that exists because it was easy to add rather than
because a developer needs it. `region` is the usual offender: if you only run in one
region, it is not a choice, it is a footgun.

## 2. Safety (25 points) — *the section that matters most*

| | Points |
|---|---|
| Data-destroying changes are **rejected at apply** via `x-kubernetes-validations` | 8 |
| Production gets `deletionProtection` + `Orphan` + final snapshot + backups | 6 |
| External names are **deterministic**, so a deleted XR can be re-adopted | 5 |
| Every cross-resource read in the template is **guarded** | 3 |
| No secret is ever typed, committed, or printed | 3 |

**Automatic zero for this section** if changing any field silently deletes and
recreates a database. That is the failure this whole course exists to prevent.

## 3. Security & tenancy (20 points)

| | Points |
|---|---|
| Developers **cannot** create managed resources directly | 6 |
| Per-tenant `ProviderConfig`, selected by namespace not by user input | 5 |
| IAM is least-privilege and generated — no wildcards, correct two-statement S3 | 4 |
| An admission policy enforces something RBAC cannot express | 3 |
| Quotas exist | 2 |

**Deduct 6** if a developer can set `environment` directly. That is Module 13's
attack 7, and it means a dev namespace can request production behaviour.

## 4. Operations (15 points)

| | Points |
|---|---|
| Packaged as a versioned Configuration with correct `dependsOn` | 4 |
| CI renders and validates every composition, with no cluster | 4 |
| **CI rejects a destructive composition rename** | 5 |
| A rollout runbook with observable go/no-go gates | 2 |

The 5 points for the rename check are deliberately the largest single line item in
this section. It is the only change in Crossplane where three characters, reviewed by
two competent engineers, deletes a production database.

## 5. Documentation (15 points)

| | Points |
|---|---|
| A developer guide someone could follow without asking you anything | 5 |
| The design write-up answers all five questions | 5 |
| You named something you chose **not** to build, and what would change your mind | 5 |

That last one is not a formality. An engineer who cannot state their scope boundary
has not chosen one, and a platform that tries to do everything does nothing well.

---

## Scoring

| Score | Meaning |
|-------|---------|
| **90–100** | You could own this platform in production. |
| **75–89** | Solid. Find your weakest section and fix it — it's usually Safety. |
| **60–74** | It works. It would hurt someone within a quarter. |
| **< 60** | Re-read Modules 09, 11, and 13, and try the Safety section again. |

## The one question that overrides the score

> **If a colleague changed one line of your composition and applied it, could they
> destroy customer data?**

If the answer is yes, the score doesn't matter. Fix that first.
