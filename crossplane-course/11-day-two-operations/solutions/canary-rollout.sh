#!/usr/bin/env bash
# Challenge 11 Task 5 — automated canary rollout with abort-and-rollback.
#
# Usage:
#   ./canary-rollout.sh <xr-kind> <target-revision> \
#       --canary <ns/name> [--batch-size 5] [--wait 300] [--settle 900]
#
# NOTE: this automates the MECHANICS, not the JUDGEMENT. It can tell you
# Synced=True; it cannot tell you the application is serving correctly. Keep a
# human on the gates that matter.
set -uo pipefail

KIND="${1:-}"; TARGET_REV="${2:-}"
shift 2 2>/dev/null || true
CANARY=""; BATCH=5; WAIT=300; SETTLE=900

while [ "$#" -gt 0 ]; do
  case "$1" in
    --canary)     CANARY="$2"; shift 2 ;;
    --batch-size) BATCH="$2";  shift 2 ;;
    --wait)       WAIT="$2";   shift 2 ;;
    --settle)     SETTLE="$2"; shift 2 ;;
    *) echo "unknown option: $1" >&2; exit 2 ;;
  esac
done

if [ -z "${KIND}" ] || [ -z "${TARGET_REV}" ] || [ -z "${CANARY}" ]; then
  echo "usage: $0 <xr-kind> <target-revision> --canary <ns/name>" >&2
  echo "          [--batch-size N] [--wait SECONDS] [--settle SECONDS]" >&2
  exit 2
fi

CANARY_NS="${CANARY%%/*}"; CANARY_NAME="${CANARY##*/}"

log() { printf '\n\033[1m▶ %s\033[0m\n' "$*"; }
fail() { printf '\n\033[31m✗ %s\033[0m\n' "$*" >&2; }

unhealthy_count() {
  kubectl get managed --no-headers 2>/dev/null \
    | awk '$2 != "True" || $3 != "True"' | wc -l | tr -d ' '
}

# ---- 0. Refuse to start on a broken system ------------------------------
log "Pre-flight"
N=$(unhealthy_count)
if [ "${N}" -ne 0 ]; then
  fail "${N} managed resources are already unhealthy. Fix them first --"
  fail "you will not be able to attribute a later failure to this rollout."
  kubectl get managed --no-headers | awk '$2 != "True" || $3 != "True"'
  exit 1
fi
echo "  ✅ everything healthy"

# Record the CURRENT revision now, so rollback never depends on querying a
# cluster that may by then be in a strange state.
PREV_REV=$(kubectl get "${KIND}" "${CANARY_NAME}" -n "${CANARY_NS}" \
  -o jsonpath='{.spec.crossplane.compositionRevisionRef.name}' 2>/dev/null)
echo "  ℹ️  canary is currently on: ${PREV_REV:-<automatic>}"
echo "  ℹ️  rolling forward to:     ${TARGET_REV}"

move_to() {  # move_to <ns> <name> <revision>
  kubectl patch "${KIND}" "$2" -n "$1" --type=merge \
    -p "{\"spec\":{\"crossplane\":{\"compositionUpdatePolicy\":\"Manual\",\"compositionRevisionRef\":{\"name\":\"$3\"}}}}" \
    >/dev/null
}

rollback_canary() {
  if [ -n "${PREV_REV}" ]; then
    fail "Rolling the canary back to ${PREV_REV}"
    move_to "${CANARY_NS}" "${CANARY_NAME}" "${PREV_REV}"
    fail "NOTE: a rollback restores the composition's SHAPE. It does NOT undo"
    fail "anything the new revision already did. If a resource was recreated,"
    fail "declare an incident and restore from backup."
  fi
}

# ---- 1. Pin everything -------------------------------------------------
log "Pinning all ${KIND} so nothing moves on its own"
kubectl get "${KIND}" -A -o json | jq -r '.items[]
  | "\(.metadata.namespace) \(.metadata.name)"' | while read -r ns name; do
  kubectl patch "${KIND}" "${name}" -n "${ns}" --type=merge \
    -p '{"spec":{"crossplane":{"compositionUpdatePolicy":"Manual"}}}' >/dev/null
done
STILL_AUTO=$(kubectl get "${KIND}" -A -o json | jq '[.items[]
  | select((.spec.crossplane.compositionUpdatePolicy // "Automatic") == "Automatic")] | length')
if [ "${STILL_AUTO}" -ne 0 ]; then
  fail "${STILL_AUTO} ${KIND} are still on Automatic. Aborting."
  exit 1
fi
echo "  ✅ all pinned"

# ---- 2. Canary ---------------------------------------------------------
log "Moving canary ${CANARY} to ${TARGET_REV}"
move_to "${CANARY_NS}" "${CANARY_NAME}" "${TARGET_REV}"

log "Waiting ${SETTLE}s for the canary to be SUSTAINED healthy"
echo "  (a single healthy check is not enough -- a resource can be briefly"
echo "   Ready in the middle of a replacement)"
DEADLINE=$(( $(date +%s) + SETTLE ))
CONSECUTIVE=0
while [ "$(date +%s)" -lt "${DEADLINE}" ]; do
  sleep 30
  if [ "$(unhealthy_count)" -eq 0 ]; then
    CONSECUTIVE=$(( CONSECUTIVE + 1 ))
    printf '  ✓ healthy check %d\n' "${CONSECUTIVE}"
  else
    fail "Canary went unhealthy."
    kubectl get managed --no-headers | awk '$2 != "True" || $3 != "True"'
    rollback_canary
    exit 1
  fi
done
echo "  ✅ canary sustained healthy for ${SETTLE}s"

echo
echo "  ⚠️  This script has verified Synced/Ready ONLY. Before continuing,"
echo "      confirm by hand that the application using the canary is serving"
echo "      correctly, and that nothing was recreated:"
echo "        kubectl get managed -o custom-columns=NAME:.metadata.name,CREATED:.metadata.creationTimestamp"
echo

# ---- 3. Batches --------------------------------------------------------
mapfile -t REMAINING < <(kubectl get "${KIND}" -A -o json | jq -r --arg ns "${CANARY_NS}" \
  --arg n "${CANARY_NAME}" --arg rev "${TARGET_REV}" '.items[]
  | select(.spec.crossplane.compositionRevisionRef.name != $rev)
  | "\(.metadata.namespace)/\(.metadata.name)"')

log "${#REMAINING[@]} remaining, in batches of ${BATCH}"
i=0
for entry in "${REMAINING[@]}"; do
  ns="${entry%%/*}"; name="${entry##*/}"
  move_to "${ns}" "${name}" "${TARGET_REV}"
  echo "  → ${entry}"
  i=$(( i + 1 ))
  if [ $(( i % BATCH )) -eq 0 ]; then
    echo "  ...batch complete, waiting ${WAIT}s"
    sleep "${WAIT}"
    if [ "$(unhealthy_count)" -ne 0 ]; then
      fail "A batch went unhealthy. ABORTING -- the remaining XRs stay on the"
      fail "old revision. Investigate before continuing."
      kubectl get managed --no-headers | awk '$2 != "True" || $3 != "True"'
      exit 1
    fi
    echo "  ✅ healthy"
  fi
done

log "Rollout complete"
echo "  All ${KIND} are on ${TARGET_REV}."
echo
echo "  ⚠️  They are still PINNED (compositionUpdatePolicy: Manual)."
echo "      Unpinning is a deliberate human decision after verification, so"
echo "      this script does not do it. When you are satisfied:"
echo
echo "        kubectl get ${KIND} -A -o name | xargs -I{} kubectl patch {} \\"
echo "          --type=merge -p '{\"spec\":{\"crossplane\":{\"compositionUpdatePolicy\":\"Automatic\",\"compositionRevisionRef\":null}}}'"
