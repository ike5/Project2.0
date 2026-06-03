#!/usr/bin/env bash
# Verify the toolchain is installed and the cluster is healthy (3 Ready nodes).
set -uo pipefail

CLUSTER_NAME="k8s-course"
fail=0

check() {
  local name="$1"; shift
  if command -v "$name" >/dev/null 2>&1; then
    printf "  ✅ %-10s %s\n" "$name" "$("$@" 2>/dev/null | head -1)"
  else
    printf "  ❌ %-10s NOT INSTALLED (brew install %s)\n" "$name" "$name"
    fail=1
  fi
}

echo "🔧 Checking tools..."
check docker  docker --version
check kind    kind version
check kubectl kubectl version --client
check helm    helm version --short
check k9s     k9s version --short
check kubectx kubectx --help >/dev/null; true

echo
echo "🐳 Checking Docker daemon..."
if docker info >/dev/null 2>&1; then
  echo "  ✅ Docker is running"
else
  echo "  ❌ Docker is NOT running — start Docker Desktop"
  fail=1
fi

echo
echo "☸️  Checking cluster '${CLUSTER_NAME}'..."
if kind get clusters 2>/dev/null | grep -qx "${CLUSTER_NAME}"; then
  echo "  ✅ Cluster exists"
  ready=$(kubectl get nodes --no-headers 2>/dev/null | grep -c " Ready ")
  total=$(kubectl get nodes --no-headers 2>/dev/null | wc -l | tr -d ' ')
  echo "  ℹ️  Nodes Ready: ${ready}/${total} (expecting 3)"
  kubectl get nodes 2>/dev/null
  if [ "${ready}" -lt 3 ]; then
    echo "  ⚠️  Fewer than 3 nodes Ready. Wait a moment and re-run, or recreate the cluster."
    fail=1
  fi
else
  echo "  ❌ Cluster not found. Run ./scripts/create-cluster.sh"
  fail=1
fi

echo
if [ "${fail}" -eq 0 ]; then
  echo "🎉 All good! Proceed to ../VERIFY.md for the full smoke test, then Module 01."
else
  echo "❗ Some checks failed — see messages above. Setup help: 00-setup/README.md"
  exit 1
fi
