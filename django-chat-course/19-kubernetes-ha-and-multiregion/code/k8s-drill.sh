#!/usr/bin/env bash
# code/k8s-drill.sh — Module 18's drill.sh, ported to Kubernetes.
#
#   ./code/k8s-drill.sh <name> <inject-command> [recovery-command]
#
# The output format is DELIBERATELY IDENTICAL to Module 18's:
#
#   <name>   RTO=  9.40s  RPO=0 msgs (28,104 sent, 28,104 received)  p99=1,840ms
#
# so the Kubernetes numbers can be put next to the Compose numbers in one table
# without anyone having to normalise them. That comparison is the entire point
# of Part G: the same failure, the same load, two orchestrators.
#
# Every drill runs WITH A LOAD TEST ON. A drill without one tells you the
# cluster reconfigured; a drill with one tells you how many users noticed.
set -euo pipefail

NAME="${1:?usage: k8s-drill.sh <name> <inject> [recover]}"
INJECT="$2"
RECOVER="${3:-}"

NS="${PULSE_NS:-default}"
HOST="${PULSE_HOST:-localhost:8090}"
VUS="${PULSE_VUS:-10000}"
ROOMS="${PULSE_ROOMS:-100}"
BASELINE_S="${PULSE_BASELINE_S:-120}"
OUT="/tmp/drill-$NAME"

mkdir -p "$OUT"
echo "=== drill: $NAME  (ns=$NS host=$HOST vus=$VUS) ==="

# ---------------------------------------------------------------------------
# 0. Record the cluster's opinion of itself before we start, so the post-mortem
#    has a "before" to diff against. `kubectl get events` is the single most
#    useful artefact when a drill produces a surprise.
# ---------------------------------------------------------------------------
kubectl -n "$NS" get pods -o wide            > "$OUT/pods.before"
kubectl -n "$NS" get endpointslices -o yaml  > "$OUT/endpoints.before"
kubectl -n "$NS" get pdb                     > "$OUT/pdb.before"

# ---------------------------------------------------------------------------
# 1. Steady state. Same harness, same parameters as Module 06 and Module 18.
# ---------------------------------------------------------------------------
k6 run -e "HOST=$HOST" -e "ROOMS=$ROOMS" -e SEND_EVERY=5000 \
       --vus "$VUS" --duration 6m \
       --summary-export="$OUT/k6.json" \
       ../../06-load-testing-harness/code/pulse-load.js > "$OUT/k6.log" 2>&1 &
K6=$!

python3 ../../06-load-testing-harness/code/collect.py \
        --out "$OUT/seq.txt" --host "$HOST" &
PROBE=$!

# Follow cluster events for the whole drill. This is the Kubernetes-specific
# addition to Module 18's harness: half of what happens during a k8s drill is a
# controller making a decision, and that decision only exists as an Event.
kubectl -n "$NS" get events --watch-only \
        -o custom-columns='TS:.lastTimestamp,REASON:.reason,OBJ:.involvedObject.name,MSG:.message' \
        > "$OUT/events.log" 2>&1 &
EVENTS=$!

trap 'kill "$K6" "$PROBE" "$EVENTS" 2>/dev/null || true' EXIT

sleep "$BASELINE_S"                                # establish a baseline

# ---------------------------------------------------------------------------
# 2. Inject.
# ---------------------------------------------------------------------------
INJECT_AT=$(date +%s.%N)
echo ">>> $INJECT_AT INJECT: $INJECT"
eval "$INJECT"

# ---------------------------------------------------------------------------
# 3. Wait for recovery: the first successful send AFTER the failure.
#
#    NOT "the pod is Ready" and NOT "the rollout completed". Module 18's whole
#    argument is that configuration is a hypothesis and behaviour is the
#    experiment; a Ready pod that cannot deliver a message has recovered
#    nothing. This is also why the Kubernetes numbers are comparable to the
#    Compose ones -- both measure the same user-visible event.
# ---------------------------------------------------------------------------
RECOVERED_AT=$(python3 ../../06-load-testing-harness/code/collect.py --await-recovery --host "$HOST")
echo ">>> $RECOVERED_AT RECOVERED"

[ -n "$RECOVER" ] && { echo ">>> RECOVER: $RECOVER"; eval "$RECOVER"; }

wait "$K6"  || true
kill "$PROBE" "$EVENTS" 2>/dev/null || true

# ---------------------------------------------------------------------------
# 4. Score it.
# ---------------------------------------------------------------------------
RTO=$(echo "$RECOVERED_AT - $INJECT_AT" | bc)
SENT=$(grep -c '^sent ' "$OUT/seq.txt" || echo 0)
GOT=$(grep -c '^recv ' "$OUT/seq.txt" || echo 0)
P99=$(jq -r '.metrics.fanout_latency_ms["p(99)"] // "n/a"' "$OUT/k6.json")

# Kubernetes-only columns. These are the ones that explain a surprising RTO:
#   - restarts:   a liveness probe fired and cost you a pod you did not intend
#   - evictions:  the kubelet or a PDB-ignoring controller took a pod
#   - pending:    a topology constraint refused to place the replacement
RESTARTS=$(kubectl -n "$NS" get pods -l app=pulse \
             -o jsonpath='{range .items[*]}{.status.containerStatuses[0].restartCount}{"\n"}{end}' \
           | awk '{s+=$1} END {print s+0}')
EVICTED=$(grep -c 'Evicted\|Preempt\|OOMKilling' "$OUT/events.log" || echo 0)
PENDING=$(kubectl -n "$NS" get pods --field-selector=status.phase=Pending --no-headers 2>/dev/null | wc -l)

printf '%-28s RTO=%6.2fs  RPO=%d msgs (%d sent, %d received)  p99=%sms  restarts=%d evicted=%d pending=%d\n' \
  "$NAME" "$RTO" "$((SENT - GOT))" "$SENT" "$GOT" "$P99" "$RESTARTS" "$EVICTED" "$PENDING" \
  | tee "$OUT.summary"

kubectl -n "$NS" get pods -o wide > "$OUT/pods.after"
echo "artefacts in $OUT/  (events.log is usually the interesting one)"
