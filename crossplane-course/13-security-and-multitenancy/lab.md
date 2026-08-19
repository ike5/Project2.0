# Lab 13 — Build a Multi-Tenant Platform, Then Attack It

**You'll:** stand up two isolated tenants, run eight attacks against them, and see
exactly which layer stops each one — including two that RBAC cannot stop.
⏱️ ~80 min.

> Prereqs: Modules 08, 10, 12. The `XBucket` XRD installed.

---

## Part A — Build the tenants

```bash
cd 13-security-and-multitenancy
kubectl apply -f manifests/tenants.yaml
kubectl apply -f manifests/providerconfigs.yaml
kubectl apply -f manifests/break-glass.yaml
kubectl apply -f ../10-reuse-and-packaging/manifests/package/apis/xbucket.yaml
kubectl apply -f manifests/composition-tenant-scoped.yaml
kubectl get ns -l acme.io/tenant
kubectl get resourcequota -A
```
✅ Expected: two tenant namespaces, each with a quota.

Read what the developer role **omits** — the omissions are the security:
```bash
sed -n '/WHAT IS DELIBERATELY ABSENT/,/break-glass.yaml/p' manifests/tenants.yaml
```

## Part B — Prove normal use works

```bash
kubectl apply -n tenant-alpha --as=system:serviceaccount:tenant-alpha:developer -f - <<'YAML'
apiVersion: platform.acme.io/v1alpha1
kind: XBucket
metadata:
  name: reports
  labels:
    acme.io/owner: team-alpha
spec:
  environment: dev
  crossplane:
    compositionRef:
      name: xbucket-tenant-scoped
YAML
sleep 45
kubectl get xbuckets -n tenant-alpha
```
✅ Expected: `READY=True`.

Confirm the composition chose the tenant's own ProviderConfig:
```bash
kubectl get buckets -o custom-columns=\
NAME:.metadata.name,EXTERNAL:.metadata.annotations.crossplane\\.io/external-name,CONFIG:.spec.providerConfigRef.name
```
✅ Expected: external name `tenant-alpha-reports`, config `tenant-alpha`.

**The developer never chose that config, and could not have.** It's derived from
their namespace, which they cannot change from inside their own XR.

## Part C — Run the attacks

```bash
./manifests/attacks.sh
```
✅ Expected: **six attacks, all denied.**

```
▶ 1. Read tenant-beta's secrets
  ✓ denied  (stopped at: Kubernetes RBAC (namespaced Role))
▶ 2. Create an XR in tenant-beta's namespace
  ✓ denied  (stopped at: Kubernetes RBAC (namespaced Role))
▶ 3. Create a raw managed resource, bypassing the composition
  ✓ denied  (stopped at: Kubernetes RBAC (no create on managed resources))
...
 6 denied, 0 SUCCEEDED
```

**Read the note the script prints at the end.** All six were stopped by RBAC — which
means a single over-broad Role removes the entire defence. The next two attacks are
the ones RBAC *cannot* stop.

> **Attack 3 is the most important.** If a developer can create a raw `Bucket`, they
> get a bucket with no encryption, no public access block, no tags, and any name they
> like. Every guarantee your composition makes is bypassed. **The platform API is the
> security boundary; direct managed-resource access is a hole straight through it.**

## Part D — Attack 7: the environment RBAC can't check

RBAC can say "you may create XBuckets". It cannot say "but not production ones".

```bash
kubectl apply -n tenant-alpha --as=system:serviceaccount:tenant-alpha:developer -f - <<'YAML'
apiVersion: platform.acme.io/v1alpha1
kind: XBucket
metadata:
  name: sneaky-prod
  labels:
    acme.io/owner: team-alpha
spec:
  environment: prod
  crossplane:
    compositionRef:
      name: xbucket-tenant-scoped
YAML
```
✅ Expected: **it succeeds.** A dev-namespace developer just created a production
resource. RBAC allowed it because RBAC only sees the verb and the kind.

```bash
kubectl delete xbucket sneaky-prod -n tenant-alpha
```

**Now add the guardrail:**
```bash
kubectl apply -f manifests/admission-policies.yaml
kubectl get validatingadmissionpolicy
```

Retry the attack:
```bash
kubectl apply -n tenant-alpha --as=system:serviceaccount:tenant-alpha:developer -f - <<'YAML'
apiVersion: platform.acme.io/v1alpha1
kind: XBucket
metadata:
  name: sneaky-prod
  labels:
    acme.io/owner: team-alpha
spec:
  environment: prod
YAML
```
✅ Expected: **rejected**:
```
spec.environment must match your namespace's acme.io/environment label.
You cannot provision into an environment your namespace is not part of.
```

> **This is the layer above RBAC.** The namespace label is platform-managed and the
> developer cannot patch it, so `environment` is now pinned to something they cannot
> forge.

Test the owner-label requirement too:
```bash
kubectl apply -n tenant-alpha --as=system:serviceaccount:tenant-alpha:developer -f - <<'YAML'
apiVersion: platform.acme.io/v1alpha1
kind: XBucket
metadata:
  name: unowned
spec:
  environment: dev
YAML
```
✅ Expected: rejected — every platform resource must name an owner. Unattributable
infrastructure is how cloud accounts fill with resources nobody will admit to.

## Part E — Attack 8: the quota

Nothing so far stops one tenant exhausting your AWS API rate limit for everyone.

```bash
for i in $(seq 1 8); do
  kubectl apply -n tenant-alpha --as=system:serviceaccount:tenant-alpha:developer -f - <<YAML 2>&1 | tail -1
apiVersion: platform.acme.io/v1alpha1
kind: XBucket
metadata:
  name: flood-$i
  labels: { acme.io/owner: team-alpha }
spec: { environment: dev }
YAML
done
```
✅ Expected: the first few succeed, then:
```
Error ... exceeded quota: platform-quota, requested: count/xbuckets.platform.acme.io=1,
used: count/xbuckets.platform.acme.io=5, limited: count/xbuckets.platform.acme.io=5
```

**One team's mistake became one team's error message**, instead of a platform-wide
outage.

```bash
kubectl delete xbucket -n tenant-alpha --all --ignore-not-found
```

## Part F — Break-glass deletion

Developers cannot delete. Watch the procedure:

```bash
kubectl apply -n tenant-alpha --as=system:serviceaccount:tenant-alpha:developer -f - <<'YAML'
apiVersion: platform.acme.io/v1alpha1
kind: XBucket
metadata:
  name: to-delete
  labels: { acme.io/owner: team-alpha }
spec: { environment: dev }
YAML
sleep 30

# The developer cannot remove it
kubectl delete xbucket to-delete -n tenant-alpha \
  --as=system:serviceaccount:tenant-alpha:developer
```
✅ Expected: forbidden.

```bash
kubectl get cm break-glass-procedure -n crossplane-system -o jsonpath='{.data.RUNBOOK\.md}'

# Step 4: bind
kubectl create clusterrolebinding "break-glass-demo" \
  --clusterrole=platform-break-glass \
  --serviceaccount=tenant-alpha:developer

kubectl delete xbucket to-delete -n tenant-alpha \
  --as=system:serviceaccount:tenant-alpha:developer

# Step 6: UNBIND IMMEDIATELY
kubectl delete clusterrolebinding break-glass-demo
```
✅ Expected: the deletion succeeds while bound, and the binding is then removed.

> **The point isn't that deletion is impossible** — it's that it cannot happen
> *absentmindedly*, which is how nearly every accidental deletion happens. Every step
> is in the audit log with a name attached.

## Part G — Audit

```bash
./manifests/audit.sh
```

Read each section. Deliberately create a problem and see it caught:
```bash
kubectl create clusterrolebinding oops-admin \
  --clusterrole=cluster-admin --serviceaccount=tenant-alpha:developer
./manifests/audit.sh 2>/dev/null | sed -n '/Who can read/,/^$/p'
```
✅ Expected: `tenant-alpha:developer` now appears as able to read the provider's
credentials.

Re-run the attacks with that binding in place:
```bash
./manifests/attacks.sh
```
✅ Expected: **every attack now succeeds.** One line of YAML removed the entire
defence.

```bash
kubectl delete clusterrolebinding oops-admin
./manifests/attacks.sh
```
✅ Expected: back to all denied.

> **This is why the audit script exists and why it should run on a schedule.** RBAC
> drifts. A `ClusterRoleBinding` added during an incident and never removed is the
> most common way platform isolation quietly stops existing — and nothing alerts on
> it, because nothing broke.

## Part H — Where the real boundary is

Everything you've built lives inside one cluster. Consider the failure mode:

```bash
kubectl get providerconfigs
kubectl get providerconfig tenant-alpha -o jsonpath='{.spec.credentials.secretRef.name}'; echo
kubectl get providerconfig tenant-beta  -o jsonpath='{.spec.credentials.secretRef.name}'; echo
```
✅ Expected: **the same Secret.** In this lab both tenants ultimately use the same
credentials — the isolation is entirely a matter of your cluster's configuration
being correct.

On real AWS you would change this to:
```yaml
spec:
  credentials:
    source: IRSA
  assumeRoleChain:
    - roleARN: arn:aws:iam::444444444444:role/TenantAlphaProvisioner
```
with tenant beta in a **different account**. Then a mistake in your RBAC, your
admission policies, or your composition cannot grant cross-tenant access, **because
AWS refuses** — and AWS doesn't care what your cluster believes.

> **Prefer the highest layer you can afford.** Everything enforced inside your
> cluster is one misconfiguration from failing. An IAM trust relationship that simply
> doesn't include your dev cluster fails safe.

## Part I — Clean up

```bash
kubectl delete xbucket --all -n tenant-alpha
kubectl delete xbucket --all -n tenant-beta
kubectl delete ns tenant-alpha tenant-beta
kubectl delete -f manifests/admission-policies.yaml
sleep 30
```

---

## What you learned
- **Developers must never hold create on managed resources.** The platform API is the
  security boundary; a raw resource bypasses every guarantee.
- Namespaced XRs isolate the **Kubernetes** half. They do nothing about the cloud.
- **ProviderConfig per tenant, backed by separate AWS accounts**, is the boundary that
  survives your own mistakes.
- **Admission policies express what RBAC cannot**: environment matching, required
  labels, no-wildcard IAM, no deleting production.
- **ResourceQuota** turns a platform-wide outage into one team's error message.
- **Break-glass deletion** makes destruction deliberate and audited.
- One `cluster-admin` binding removes every RBAC control at once — **audit on a
  schedule.**

➡️ **[challenge.md](./challenge.md)** then [Module 14](../14-gitops-and-cicd/).
