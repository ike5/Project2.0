#!/usr/bin/env bash
# Confirm the whole toolchain is healthy. Safe to run any time.
set -uo pipefail

fail=0
check() {
  local label="$1"; shift
  if "$@" >/dev/null 2>&1; then
    echo "  ✅ ${label}"
  else
    echo "  ❌ ${label}"
    fail=1
  fi
}

echo "🔧 Tool versions"
for tool in docker kind kubectl helm crossplane; do
  if command -v "$tool" >/dev/null 2>&1; then
    printf '  ✅ %-11s %s\n' "$tool" "$("$tool" version --short 2>/dev/null | head -1 || "$tool" version 2>/dev/null | head -1)"
  else
    echo "  ❌ ${tool} is not installed"
    fail=1
  fi
done

echo
echo "☸️  Cluster"
check "api-server reachable" kubectl cluster-info
NODES=$(kubectl get nodes --no-headers 2>/dev/null | grep -c ' Ready ')
if [ "${NODES:-0}" -ge 3 ]; then
  echo "  ✅ ${NODES} nodes Ready"
else
  echo "  ❌ expected 3 Ready nodes, found ${NODES:-0}"
  fail=1
fi

echo
echo "🛰️  Crossplane"
check "crossplane-system namespace exists" kubectl get ns crossplane-system
check "crossplane deployment Available" \
  kubectl wait --for=condition=Available deployment/crossplane -n crossplane-system --timeout=10s
check "CompositeResourceDefinition CRD installed" \
  kubectl get crd compositeresourcedefinitions.apiextensions.crossplane.io
check "Composition CRD installed" \
  kubectl get crd compositions.apiextensions.crossplane.io

echo
echo "☁️  LocalStack"
check "localstack deployment Available" \
  kubectl wait --for=condition=Available deployment/localstack -n localstack --timeout=10s
if kubectl run xp-verify-curl --rm -i --restart=Never --image=curlimages/curl:8.10.1 --quiet -- \
     -sf http://localstack.localstack.svc.cluster.local:4566/_localstack/health >/dev/null 2>&1; then
  echo "  ✅ LocalStack health endpoint answers from inside the cluster"
else
  echo "  ❌ LocalStack health endpoint unreachable from inside the cluster"
  fail=1
fi

echo
if [ "$fail" -eq 0 ]; then
  echo "🎉 All green. Head to ../01-control-plane-thinking/"
else
  echo "⚠️  Something above failed. See 00-setup/README.md → Troubleshooting,"
  echo "   or ../cheatsheets/troubleshooting.md"
  exit 1
fi
