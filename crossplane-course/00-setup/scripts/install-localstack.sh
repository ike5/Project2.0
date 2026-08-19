#!/usr/bin/env bash
# Deploy LocalStack (the free AWS API emulator) into the cluster.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MANIFEST="${SCRIPT_DIR}/../manifests/localstack.yaml"

if ! kubectl cluster-info >/dev/null 2>&1; then
  echo "❌ No reachable cluster. Run ./scripts/create-cluster.sh first." >&2
  exit 1
fi

echo "🚀 Deploying LocalStack..."
kubectl apply -f "${MANIFEST}"

echo
echo "⏳ Waiting for LocalStack to become Ready (first pull can take a few minutes)..."
kubectl wait --for=condition=Available deployment/localstack \
  --namespace localstack --timeout=600s

echo
echo "✅ LocalStack is up. In-cluster endpoint:"
echo "   http://localstack.localstack.svc.cluster.local:4566"
echo
kubectl get pods,svc -n localstack
echo
echo "Next: ./scripts/verify-setup.sh"
