# Module 11 — Security: RBAC, NetworkPolicies & Pod Security

**Goal:** apply least-privilege access (RBAC + ServiceAccounts), restrict Pod-to-Pod
traffic (NetworkPolicies), and enforce baseline Pod hardening (Pod Security Standards).

⏱️ ~2.5 hours · 🎯 Prereq: Modules 00–10.

> ⚠️ **Heads-up on NetworkPolicies:** the default kind CNI (**kindnet**) does **not
> enforce** NetworkPolicies — it will *accept* the objects but silently allow all
> traffic. That's itself a critical real-world lesson: *a NetworkPolicy is a no-op
> without a CNI that enforces it.* The lab includes an **optional** Calico-backed
> cluster so you can see real enforcement. RBAC and Pod Security work on your normal
> cluster.

---

## 1. AuthN vs AuthZ

- **Authentication (who are you?)** — certs, tokens, OIDC. The api-server verifies identity.
- **Authorization (what may you do?)** — **RBAC** decides if an authenticated identity
  can perform a verb on a resource.
- **Admission control (is this allowed/mutated?)** — webhooks/policies that validate
  or modify objects *after* authz (Pod Security Standards live here).

## 2. RBAC

Four objects, two pairs:

| Object | Scope | Says |
|--------|-------|------|
| **Role** | one namespace | "these verbs on these resources" |
| **ClusterRole** | whole cluster | same, but cluster-wide (or for cluster-scoped resources) |
| **RoleBinding** | one namespace | "grant this Role/ClusterRole to these subjects" |
| **ClusterRoleBinding** | whole cluster | grant a ClusterRole cluster-wide |

A **Role** is a set of permission rules:
```yaml
rules:
  - apiGroups: [""]            # "" = core API group (pods, services, configmaps)
    resources: ["pods"]
    verbs: ["get", "list", "watch"]
```
A **binding** attaches it to **subjects**: a `User`, a `Group`, or a
**ServiceAccount**.

Test what an identity can do with `kubectl auth can-i`:
```bash
kubectl auth can-i list pods
kubectl auth can-i delete nodes --as=system:serviceaccount:default:reader
```

## 3. ServiceAccounts

A **ServiceAccount (SA)** is an identity for *processes running in Pods* (as opposed
to humans). Every Pod runs as an SA (`default` if unspecified). To let an app talk to
the Kubernetes API with least privilege:

1. Create an SA.
2. Bind a Role granting only what it needs.
3. Set `spec.serviceAccountName` on the Pod.

The SA's token is auto-mounted into the Pod; client libraries use it automatically.
**Least privilege matters:** the over-permissioned `default` SA is a classic attack
escalation path.

## 4. NetworkPolicies

By default, **all Pods can talk to all Pods**. A **NetworkPolicy** is a Pod-level
firewall: it selects Pods and defines allowed **ingress** (incoming) and **egress**
(outgoing) traffic. Key rules of thumb:

- Policies are **additive** and **default-allow until a policy selects a Pod** — once
  *any* policy selects a Pod for a direction, only explicitly-allowed traffic is
  permitted (default-deny for that direction).
- A common pattern: a **default-deny** policy, then narrow **allow** policies.

```yaml
# deny all ingress to pods in this namespace
spec:
  podSelector: {}          # all pods
  policyTypes: ["Ingress"] # with no ingress rules -> deny all incoming
```

**Requires an enforcing CNI** (Calico, Cilium, etc.). See the heads-up above.

## 5. Pod Security Standards (PSS)

PSS are three baseline profiles enforced by the built-in **Pod Security admission**
controller, applied via **namespace labels**:

- **privileged** — no restrictions.
- **baseline** — blocks known privilege escalations (hostNetwork, privileged, etc.).
- **restricted** — hardened: non-root, no privilege escalation, seccomp, drop caps.

```bash
kubectl label namespace prod \
  pod-security.kubernetes.io/enforce=restricted
```
After that, Pods violating `restricted` are **rejected at creation**. You'll see this
live in the lab.

## 6. Secret hygiene (recap + more)

- Secrets are base64, not encrypted at rest by default — enable etcd encryption.
- Lock down who can `get secrets` via RBAC.
- Prefer file mounts over env for sensitive values.
- For production, consider External Secrets Operator / Vault / cloud KMS.

---

## Do the lab
Create a least-privilege ServiceAccount + Role and test it with `auth can-i`,
enforce `restricted` Pod Security on a namespace, and (optionally, on a Calico
cluster) prove a default-deny NetworkPolicy blocks traffic. 👉 **[lab.md](./lab.md)**

Then: 👉 **[challenge.md](./challenge.md)**

## Manifests
- RBAC: [`serviceaccount.yaml`](./manifests/serviceaccount.yaml),
  [`role.yaml`](./manifests/role.yaml), [`rolebinding.yaml`](./manifests/rolebinding.yaml)
- NetworkPolicy: [`netpol-deny-all.yaml`](./manifests/netpol-deny-all.yaml),
  [`netpol-allow-from-client.yaml`](./manifests/netpol-allow-from-client.yaml),
  [`netpol-test-apps.yaml`](./manifests/netpol-test-apps.yaml)
- Pod Security: [`restricted-ns.yaml`](./manifests/restricted-ns.yaml),
  [`violating-pod.yaml`](./manifests/violating-pod.yaml),
  [`compliant-pod.yaml`](./manifests/compliant-pod.yaml)
- Optional Calico cluster: [`kind-calico.yaml`](./manifests/kind-calico.yaml)

## Key terms
authN/authZ · RBAC · Role/ClusterRole · RoleBinding · subject · ServiceAccount ·
`auth can-i` · NetworkPolicy · ingress/egress · default-deny · Pod Security Standards

**Next →** [Module 12: Production & GitOps](../12-production-and-gitops/)
