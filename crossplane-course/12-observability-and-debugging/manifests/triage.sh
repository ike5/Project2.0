#!/usr/bin/env bash
# The debugging order, scripted.
#
#   1. crossplane trace      -> which layer?
#   2. condition messages    -> the raw cloud error
#   3. events                -> history
#   4. component logs        -> only when 1-3 are not enough
#
# Usage: ./triage.sh <xr-kind> <name> [-n namespace]
set -uo pipefail

KIND="${1:-}"; NAME="${2:-}"; NS="${4:-default}"
if [ -z "${KIND}" ] || [ -z "${NAME}" ]; then
  echo "usage: $0 <xr-kind> <name> [-n namespace]" >&2
  echo "   eg: $0 xbrokenone stack-one -n debug" >&2
  exit 2
fi

hdr() { printf '\n\033[1m════ %s ════\033[0m\n' "$*"; }

hdr "1. The tree — which layer is broken?"
if command -v crossplane >/dev/null 2>&1; then
  crossplane trace "${KIND}" "${NAME}" -n "${NS}" 2>&1 || \
    echo "  (trace failed — the XR may not exist, or its kind is wrong)"
else
  echo "  crossplane CLI not found; falling back to kubectl"
  kubectl get "${KIND}" "${NAME}" -n "${NS}" 2>&1
fi

hdr "2. Conditions on the XR"
kubectl get "${KIND}" "${NAME}" -n "${NS}" -o json 2>/dev/null \
  | jq -r '.status.conditions[]? |
      "  \(.type)=\(.status)\n    reason:  \(.reason // "-")\n    message: \(.message // "-")"' \
  || echo "  (no conditions — nothing is reconciling this XR)"

hdr "3. Any managed resource that is not fully healthy"
UNHEALTHY=$(kubectl get managed --no-headers 2>/dev/null \
  | awk '$2 != "True" || $3 != "True"' || true)
if [ -z "${UNHEALTHY}" ]; then
  echo "  ✅ every managed resource is Synced and Ready."
  echo
  echo "  ⚠️  If the system is still broken, the fault is NOT in Crossplane."
  echo "     A green control plane and a broken system means YOU DECLARED THE"
  echo "     WRONG THING. Stop reading these logs and compare what the"
  echo "     composition produced against what you actually intended:"
  echo
  echo "       crossplane render <xr> <composition> <functions>"
  echo "       awslocal s3 ls   # or the equivalent for your resource"
else
  echo "${UNHEALTHY}"
  echo
  echo "── The Synced message for each (this is where the cloud error lives) ──"
  echo "${UNHEALTHY}" | awk '{print $1}' | while read -r res; do
    MSG=$(kubectl get "${res}" -o jsonpath='{.status.conditions[?(@.type=="Synced")].message}' 2>/dev/null)
    printf '  %s\n    %s\n' "${res}" "${MSG:-<no message>}"
  done
fi

hdr "4. Recent events for this XR"
kubectl get events -n "${NS}" \
  --field-selector "involvedObject.name=${NAME}" \
  --sort-by='.lastTimestamp' 2>/dev/null | tail -12 \
  || echo "  (none — note that events expire after about an hour)"

hdr "5. Composition engine log (last 20 lines mentioning this XR)"
kubectl logs -n crossplane-system deploy/crossplane --tail=400 2>/dev/null \
  | grep -i "${NAME}" | tail -20 \
  || echo "  (nothing — which itself suggests the XR is not being reconciled)"

hdr "Next steps"
cat <<'EOF'
  If the tree showed NO composed resources at all
    -> compositeTypeRef mismatch, or no Composition selected.
       kubectl get compositions
       kubectl describe <kind> <name> -n <ns> | tail

  If ONE resource is unsynced with "cannot resolve references"
    -> normal for the first minute. A bug only if it persists.

  If EVERYTHING is unsynced at once
    -> credentials, endpoint, or a provider upgrade.
       kubectl get providerconfigs
       kubectl logs -n crossplane-system -l pkg.crossplane.io/provider=<provider>

  If everything is GREEN and the system is broken
    -> you declared the wrong thing. crossplane render and compare.
EOF
