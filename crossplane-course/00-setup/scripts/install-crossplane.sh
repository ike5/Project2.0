#!/usr/bin/env bash
# Install Crossplane v2 into the course cluster via its official Helm chart.
# Idempotent: re-running upgrades in place.
set -euo pipefail

NAMESPACE="crossplane-system"
# Pinned so the course is reproducible. Bump deliberately, not accidentally.
CHART_VERSION="${CROSSPLANE_CHART_VERSION:-2.3.0}"

if ! command -v helm >/dev/null 2>&1; then
  echo "❌ 'helm' is not installed. Run: brew install helm" >&2
  exit 1
fi

if ! kubectl cluster-info >/dev/null 2>&1; then
  echo "❌ No reachable cluster. Run ./scripts/create-cluster.sh first." >&2
  exit 1
fi

echo "📦 Adding the Crossplane Helm repo..."
helm repo add crossplane-stable https://charts.crossplane.io/stable >/dev/null
helm repo update crossplane-stable >/dev/null

echo "🚀 Installing Crossplane ${CHART_VERSION} into '${NAMESPACE}'..."
helm upgrade --install crossplane crossplane-stable/crossplane \
  --namespace "${NAMESPACE}" \
  --create-namespace \
  --version "${CHART_VERSION}" \
  --wait \
  --timeout 5m

echo
echo "⏳ Waiting for the Crossplane pods to be Ready..."
kubectl wait --for=condition=Available deployment --all \
  --namespace "${NAMESPACE}" --timeout=300s

echo
echo "✅ Crossplane is running:"
kubectl get pods -n "${NAMESPACE}"
echo
echo "✅ It installed these core APIs:"
kubectl api-resources --api-group=apiextensions.crossplane.io
echo
echo "Next: ./scripts/install-aws-emulator.sh"
