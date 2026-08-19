# Module 13 — Security & Multi-Tenancy

**Goal:** let many teams share one control plane without any of them being able to
reach another's infrastructure, take down the platform, or escalate into your cloud
account.

⏱️ ~3 hours · 🎯 Prereq: Modules 08, 10, 12.

---

## 1. What you're actually defending against

A Crossplane control plane holds credentials that can create and destroy cloud
infrastructure. That makes it one of the most valuable targets in your estate. Be
specific about the threats:

| Threat | Example |
|--------|---------|
| **Cross-tenant access** | Team A creates an XR that reads team B's database |
| **Privilege escalation** | A developer creates an IAM role with `AdministratorAccess` |
| **Account escape** | A dev-cluster XR provisions into the production account |
| **Credential theft** | Someone reads the provider's AWS keys out of a Secret |
| **Destructive action** | `kubectl delete` removes production data |
| **Denial of service** | One team creates 10,000 XRs and exhausts API quota |

Each needs a different control, and **most of them are not solved by RBAC**.

## 2. The layers, and which threat each stops

```
┌──────────────────────────────────────────────────────────┐
│ AWS: separate accounts, IAM trust, permissions boundaries│  ← strongest
├──────────────────────────────────────────────────────────┤
│ Crossplane: ProviderConfig scoping, Usage locks          │
├──────────────────────────────────────────────────────────┤
│ Kubernetes: RBAC, namespaces, admission policy, quotas   │
├──────────────────────────────────────────────────────────┤
│ Process: GitOps, code review, no direct cluster access   │  ← weakest alone
└──────────────────────────────────────────────────────────┘
```

**The single most important idea in this module:** everything enforced *inside* your
cluster is one misconfiguration away from failing. A control enforced by **AWS** —
an IAM trust relationship that simply doesn't include your dev cluster — fails safe.

Prefer the highest layer you can afford.

## 3. RBAC for a platform

Three distinct roles, and developers should have the narrowest:

**Developers** create XRs in their own namespace. Nothing else:
```yaml
kind: Role
metadata:
  namespace: team-payments
rules:
  - apiGroups: ["platform.acme.io"]
    resources: ["xdatabases", "xbuckets"]
    verbs: ["get", "list", "watch", "create", "update", "patch"]
    # NOTE: no "delete". Deletion is a break-glass operation.
```

**Developers must not** get access to managed resources directly:
```yaml
# ❌ Never grant this to a developer
- apiGroups: ["s3.aws.upbound.io"]
  resources: ["buckets"]
  verbs: ["create"]
```
Why: a raw `Bucket` bypasses every guarantee your composition makes — encryption,
public access blocking, tagging, naming. **The platform API is the security boundary.
Direct managed-resource access is a hole straight through it.**

**Platform engineers** manage XRDs, Compositions, and providers. **Nobody** routinely
holds delete on production XRs.

## 4. Namespace isolation, and its limits

Namespaced XRs (the v2 default) give you real isolation for the Kubernetes half:

- An XR in `team-a` composes resources in `team-a`.
- Its connection Secrets land in `team-a`.
- Standard namespace RBAC applies.

**But namespaces do not isolate the cloud.** Both teams' XRs go through the same
provider, using the same `ProviderConfig`, into the same AWS account. Namespace
isolation controls **who can ask**; it does nothing about what AWS itself permits.

For cloud isolation you need §5 and §6.

## 5. ProviderConfig scoping — the cloud boundary

The real boundary is which credentials an XR's resources use.

```yaml
apiVersion: aws.upbound.io/v1beta1
kind: ProviderConfig
metadata:
  name: team-payments
spec:
  credentials:
    source: IRSA
  assumeRoleChain:
    - roleARN: arn:aws:iam::444444444444:role/TeamPaymentsProvisioner
```

Now a composition selects the config from the XR's namespace:
```gotemplate
providerConfigRef:
  name: {{ $xr.metadata.namespace }}
```

Team A's resources use team A's role, which AWS scopes to team A's resources. **A
misconfiguration in your cluster can no longer grant team A access to team B's data,
because AWS is the one saying no.**

> **The strongest version: separate AWS accounts per team or per environment.** IAM
> boundaries within one account are permeable in subtle ways; account boundaries are
> not.

## 6. Protecting the provider's credentials

The provider's credentials are the crown jewels — they can create and destroy
everything.

```bash
# Who can read the credential Secret?
kubectl auth can-i get secrets -n crossplane-system --as=system:serviceaccount:team-payments:default
```

Rules:
1. **Nobody but Crossplane reads `crossplane-system`.** No developer RBAC should
   touch that namespace.
2. **Use IRSA, so there is no Secret at all** (Module 08). You cannot steal a
   credential that doesn't exist.
3. **Encrypt etcd at rest.** Kubernetes Secrets are base64, not encrypted, by default.
4. **Scope the provider's own IAM role.** If it holds `AdministratorAccess`, then so
   does anyone who compromises the control plane.

## 7. Admission policy — the guardrails RBAC can't express

RBAC answers "may this identity perform this verb on this kind?" It cannot say "only
if the field is under 100" or "not on Fridays". `ValidatingAdmissionPolicy` can:

```yaml
apiVersion: admissionregistration.k8s.io/v1
kind: ValidatingAdmissionPolicy
metadata:
  name: protect-production
spec:
  matchConstraints:
    resourceRules:
      - apiGroups: ["platform.acme.io"]
        operations: ["DELETE"]
        resources: ["xdatabases"]
  validations:
    - expression: "oldObject.spec.environment != 'prod'"
      message: "Production databases cannot be deleted directly. See RUNBOOK-114."
```

This is where you enforce: no deleting production, environment must match namespace,
sizes within limits, required labels present.

## 8. Quotas — the denial-of-service control

Nothing so far stops a team creating 10,000 XRs and exhausting your AWS API quota,
which would degrade *every* team.

```yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: platform-quota
  namespace: team-payments
spec:
  hard:
    count/xdatabases.platform.acme.io: "5"
    count/xbuckets.platform.acme.io: "20"
```

Standard `ResourceQuota` counts custom resources. Cheap, and it turns a
platform-wide outage into one team getting a clear error.

## 9. A concrete tenancy model

For a platform serving many teams:

| Concern | Control |
|---------|---------|
| Who can create XRs | RBAC, namespaced |
| Which XRs they can create | RBAC per kind |
| What those XRs may do | The Composition — developers never touch managed resources |
| Which cloud account | ProviderConfig per namespace + IAM trust |
| How much they can create | ResourceQuota |
| What they cannot delete | Admission policy + `Usage` + `deletionPolicy: Orphan` |
| What the platform itself can do | The provider's IAM role + permissions boundary |

**And above all of it:** separate clusters per environment. It is the only control
that makes "wrong context" impossible rather than merely unlikely.

---

## Do the lab
Build a two-tenant platform, then attack it: try to reach the other tenant's data,
escalate privileges, and delete production. Watch each attempt fail, and at which
layer.
👉 **[lab.md](./lab.md)**

Then: 👉 **[challenge.md](./challenge.md)**

## Manifests
- [`tenants.yaml`](./manifests/tenants.yaml) — two namespaces, quotas, RBAC
- [`providerconfigs.yaml`](./manifests/providerconfigs.yaml) — per-tenant cloud identity
- [`admission-policies.yaml`](./manifests/admission-policies.yaml) — the guardrails
- [`attacks.sh`](./manifests/attacks.sh) — six attacks, scripted
- [`audit.sh`](./manifests/audit.sh) — who can do what

## Key terms
tenant · namespace isolation · RBAC · ProviderConfig scoping · `assumeRoleChain` ·
permissions boundary · `ValidatingAdmissionPolicy` · CEL · `ResourceQuota` ·
break-glass · defence in depth

**Next →** [Module 14: GitOps & CI/CD](../14-gitops-and-cicd/)
