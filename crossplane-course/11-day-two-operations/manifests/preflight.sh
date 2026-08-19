#!/usr/bin/env bash
# The pre-change checklist, scripted.
#
# Run this BEFORE applying a composition change to a cluster with live XRs.
# It answers three questions:
#   1. Is everything currently healthy? (never change a broken system)
#   2. Which revision is each XR pinned to?
#   3. What would the new composition actually produce, versus the old one?
#
# Usage:
#   ./preflight.sh <xr-kind> [old-composition.yaml new-composition.yaml \
#                             sample-xr.yaml functions.yaml]
set -uo pipefail

KIND="${1:-}"
if [ -z "${KIND}" ]; then
  echo "usage: $0 <xr-kind> [old.yaml new.yaml sample-xr.yaml functions.yaml]" >&2
  echo "   eg: $0 xbuckets" >&2
  exit 2
fi

WARN=0

echo "════════════════════════════════════════════════════════════"
echo " 1. Is anything unhealthy right now?"
echo "════════════════════════════════════════════════════════════"
UNHEALTHY=$(kubectl get managed --no-headers 2>/dev/null \
  | awk '$2 != "True" || $3 != "True"' || true)
if [ -n "${UNHEALTHY}" ]; then
  echo "⚠️  Some managed resources are NOT healthy:"
  echo "${UNHEALTHY}"
  echo
  echo "   Do not roll out a change on top of an existing failure -- you will"
  echo "   not be able to tell which problem your change caused."
  WARN=1
else
  echo "✅ All managed resources are Synced and Ready."
fi

echo
echo "════════════════════════════════════════════════════════════"
echo " 2. Which revision is each ${KIND} pinned to?"
echo "════════════════════════════════════════════════════════════"
kubectl get "${KIND}" -A -o custom-columns=\
NAMESPACE:.metadata.namespace,\
NAME:.metadata.name,\
POLICY:.spec.crossplane.compositionUpdatePolicy,\
REVISION:.spec.crossplane.compositionRevisionRef.name 2>/dev/null \
  || echo "   (no ${KIND} found)"

AUTO=$(kubectl get "${KIND}" -A -o json 2>/dev/null \
  | jq -r '[.items[] | select((.spec.crossplane.compositionUpdatePolicy // "Automatic") == "Automatic")] | length' \
  2>/dev/null || echo "?")
echo
if [ "${AUTO}" != "0" ] && [ "${AUTO}" != "?" ]; then
  echo "⚠️  ${AUTO} ${KIND} are on compositionUpdatePolicy: Automatic."
  echo "   They will adopt your new composition THE MOMENT you apply it,"
  echo "   with no canary and no approval. Pin them first:"
  echo
  echo "     kubectl get ${KIND} -A -o name | xargs -I{} kubectl patch {} \\"
  echo "       --type=merge -p '{\"spec\":{\"crossplane\":{\"compositionUpdatePolicy\":\"Manual\"}}}'"
  WARN=1
else
  echo "✅ No ${KIND} will move automatically."
fi

echo
echo "════════════════════════════════════════════════════════════"
echo " 3. Existing composition revisions"
echo "════════════════════════════════════════════════════════════"
kubectl get compositionrevisions 2>/dev/null || echo "   (none)"

if [ "$#" -eq 5 ]; then
  OLD="$2"; NEW="$3"; XR="$4"; FUNCS="$5"
  echo
  echo "════════════════════════════════════════════════════════════"
  echo " 4. What actually changes (the closest thing to a plan)"
  echo "════════════════════════════════════════════════════════════"
  OLD_OUT="$(mktemp)"; NEW_OUT="$(mktemp)"
  trap 'rm -f "${OLD_OUT}" "${NEW_OUT}"' EXIT
  crossplane render "${XR}" "${OLD}" "${FUNCS}" > "${OLD_OUT}" 2>/dev/null
  crossplane render "${XR}" "${NEW}" "${FUNCS}" > "${NEW_OUT}" 2>/dev/null

  if diff -u "${OLD_OUT}" "${NEW_OUT}"; then
    echo "✅ No rendered difference."
  fi

  echo
  echo "── Resource-name check (the destructive one) ──"
  # A changed resource-name annotation means DELETE AND RECREATE, with no
  # visible API change. This is the single most dangerous composition edit.
  OLD_NAMES="$(grep -o 'crossplane.io/composition-resource-name: .*' "${OLD_OUT}" | sort || true)"
  NEW_NAMES="$(grep -o 'crossplane.io/composition-resource-name: .*' "${NEW_OUT}" | sort || true)"
  if [ "${OLD_NAMES}" = "${NEW_NAMES}" ]; then
    echo "✅ Composed resource names are unchanged."
  else
    echo "🚨 COMPOSED RESOURCE NAMES CHANGED."
    echo "   Crossplane identifies composed resources by these names."
    echo "   Applying this WILL DELETE AND RECREATE infrastructure for every"
    echo "   existing XR. On a database, that is your data."
    echo
    diff <(echo "${OLD_NAMES}") <(echo "${NEW_NAMES}") || true
    WARN=1
  fi
fi

echo
if [ "${WARN}" -eq 0 ]; then
  echo "🎉 Pre-flight clean. Proceed with the canary rollout."
else
  echo "⚠️  Pre-flight raised warnings above. Read them before proceeding."
  exit 1
fi
