#!/usr/bin/env bash
# Who can do what to your platform?
#
# Run this periodically. RBAC drifts: a ClusterRoleBinding added during an
# incident and never removed is the most common way platform isolation quietly
# stops existing.
set -uo pipefail

hdr() { printf '\n\033[1m════ %s ════\033[0m\n' "$*"; }

hdr "1. Who can read the provider's credentials?"
echo "   (the crown jewels -- these can create and destroy everything)"
for sa in $(kubectl get sa -A -o jsonpath='{range .items[*]}{.metadata.namespace}:{.metadata.name}{"\n"}{end}' 2>/dev/null); do
  ns="${sa%%:*}"; name="${sa##*:}"
  if kubectl auth can-i get secrets -n crossplane-system \
       --as="system:serviceaccount:${ns}:${name}" 2>/dev/null | grep -q yes; then
    echo "   ⚠️  system:serviceaccount:${ns}:${name}"
  fi
done
echo "   (only Crossplane's own service accounts should appear above)"

hdr "2. Who can create MANAGED RESOURCES directly?"
echo "   (bypassing every guarantee your compositions make)"
kubectl get clusterrolebindings -o json 2>/dev/null | jq -r '
  .items[]
  | select(.roleRef.name | test("admin|edit|cluster-admin"))
  | "   ⚠️  \(.metadata.name) -> \(.roleRef.name)\n       subjects: \([.subjects[]?.name] | join(", "))"'

hdr "3. Who holds cluster-admin?"
kubectl get clusterrolebindings -o json 2>/dev/null | jq -r '
  .items[] | select(.roleRef.name == "cluster-admin")
  | "   \(.metadata.name): \([.subjects[]? | "\(.kind)/\(.name)"] | join(", "))"'

hdr "4. Break-glass bindings still active"
echo "   (a break-glass grant that was never revoked is just a permanent"
echo "    permission with extra steps)"
STALE=$(kubectl get clusterrolebindings -o json 2>/dev/null | jq -r --argjson now "$(date +%s)" '
  .items[]
  | select(.metadata.name | startswith("break-glass"))
  | select(($now - (.metadata.creationTimestamp | fromdateiso8601)) > 3600)
  | "   🚨 \(.metadata.name) — active for \((($now - (.metadata.creationTimestamp | fromdateiso8601)) / 3600) | floor)h"')
if [ -n "${STALE}" ]; then echo "${STALE}"; else echo "   ✅ none older than an hour"; fi

hdr "5. ProviderConfigs and who uses them"
kubectl get providerconfigs -o custom-columns=NAME:.metadata.name 2>/dev/null
echo
echo "   Resources per ProviderConfig:"
kubectl get managed -o json 2>/dev/null | jq -r '
  [.items[] | .spec.providerConfigRef.name // "default"]
  | group_by(.) | map({config: .[0], count: length})
  | .[] | "     \(.config): \(.count)"'

hdr "6. Admission policies in force"
kubectl get validatingadmissionpolicy -o custom-columns=\
NAME:.metadata.name,ACTIONS:.spec.validations[*].message 2>/dev/null \
  | head -20 || echo "   ⚠️  NONE — the guardrails RBAC cannot express are absent"

hdr "7. Namespaces without a quota"
echo "   (one tenant can exhaust the cloud API rate limit for everyone)"
for ns in $(kubectl get ns -l acme.io/tenant -o jsonpath='{.items[*].metadata.name}' 2>/dev/null); do
  if [ "$(kubectl get resourcequota -n "${ns}" --no-headers 2>/dev/null | wc -l)" -eq 0 ]; then
    echo "   ⚠️  ${ns} has no ResourceQuota"
  fi
done
echo "   (done)"
