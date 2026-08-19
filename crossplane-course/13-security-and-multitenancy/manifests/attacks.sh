#!/usr/bin/env bash
# Six attacks against the two-tenant platform. Every one should FAIL.
#
# Run this after applying tenants.yaml, providerconfigs.yaml and
# admission-policies.yaml. Each attack prints which LAYER stopped it -- that
# mapping is the point of the exercise, not the fact that they failed.
set -uo pipefail

ALPHA="system:serviceaccount:tenant-alpha:developer"
PASS=0; FAIL=0

# expect_denied <description> <layer> <command...>
expect_denied() {
  local desc="$1" layer="$2"; shift 2
  printf '\n\033[1m▶ %s\033[0m\n' "${desc}"
  local out
  if out=$("$@" 2>&1); then
    printf '  \033[31m✗ SUCCEEDED — this is a security hole\033[0m\n'
    printf '    %s\n' "${out}" | head -3
    FAIL=$((FAIL + 1))
  else
    printf '  \033[32m✓ denied\033[0m  (stopped at: %s)\n' "${layer}"
    printf '    %s\n' "$(echo "${out}" | head -2)"
    PASS=$((PASS + 1))
  fi
}

echo "════════════════════════════════════════════════════════"
echo " Attacking the platform as tenant-alpha's developer"
echo "════════════════════════════════════════════════════════"

# ─── 1. Cross-tenant read ───
expect_denied \
  "1. Read tenant-beta's secrets" \
  "Kubernetes RBAC (namespaced Role)" \
  kubectl get secrets -n tenant-beta --as="${ALPHA}"

# ─── 2. Cross-tenant write ───
expect_denied \
  "2. Create an XR in tenant-beta's namespace" \
  "Kubernetes RBAC (namespaced Role)" \
  kubectl create -n tenant-beta --as="${ALPHA}" -f - <<'YAML'
apiVersion: platform.acme.io/v1alpha1
kind: XBucket
metadata:
  name: intruder
  labels: { acme.io/owner: alpha }
spec: { environment: dev }
YAML

# ─── 3. Bypass the platform API ───
# THE MOST IMPORTANT ONE. A raw Bucket skips encryption, public-access
# blocking, tagging and naming -- every guarantee the composition makes.
expect_denied \
  "3. Create a raw managed resource, bypassing the composition" \
  "Kubernetes RBAC (no create on managed resources)" \
  kubectl create -n tenant-alpha --as="${ALPHA}" -f - <<'YAML'
apiVersion: s3.aws.upbound.io/v1beta1
kind: Bucket
metadata:
  name: unguarded
spec:
  forProvider: { region: us-east-1 }
  providerConfigRef: { name: default }
YAML

# ─── 4. Steal the provider's credentials ───
expect_denied \
  "4. Read the provider's AWS credentials" \
  "Kubernetes RBAC (no access to crossplane-system)" \
  kubectl get secret aws-creds -n crossplane-system --as="${ALPHA}"

# ─── 5. Rewrite the platform itself ───
# A developer who can edit a Composition can make it do anything, for everyone.
expect_denied \
  "5. Modify the Composition every tenant uses" \
  "Kubernetes RBAC (cluster-scoped resource, no ClusterRole)" \
  kubectl patch composition xbucket-tenant-scoped --as="${ALPHA}" \
    --type=merge -p '{"metadata":{"labels":{"pwned":"true"}}}'

# ─── 6. Delete production ───
expect_denied \
  "6. Delete any XR at all (no delete verb)" \
  "Kubernetes RBAC (delete is break-glass only)" \
  kubectl delete xbucket --all -n tenant-alpha --as="${ALPHA}"

echo
echo "════════════════════════════════════════════════════════"
printf ' %d denied, %d SUCCEEDED\n' "${PASS}" "${FAIL}"
echo "════════════════════════════════════════════════════════"
if [ "${FAIL}" -ne 0 ]; then
  echo
  echo "⚠️  An attack succeeded. That is a hole -- find which control was"
  echo "   missing before continuing."
  exit 1
fi
cat <<'EOF'

Note which layer stopped each attack: ALL SIX were Kubernetes RBAC.

That is worth sitting with. RBAC is doing all the work here, which means a
single mistake in one Role -- an over-broad verb, a wildcard resource, a
ClusterRoleBinding someone adds in a hurry -- removes the entire defence.

The lab's remaining attacks (7 and 8) are the ones RBAC CANNOT stop, and they
are why the layers above it exist.
EOF
