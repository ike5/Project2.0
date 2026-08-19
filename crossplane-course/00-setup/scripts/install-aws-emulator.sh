#!/usr/bin/env bash
# Deploy the local AWS API emulator (moto) into the cluster.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MANIFEST="${SCRIPT_DIR}/../manifests/aws-emulator.yaml"

if ! kubectl cluster-info >/dev/null 2>&1; then
  echo "❌ No reachable cluster. Run ./scripts/create-cluster.sh first." >&2
  exit 1
fi

echo "🚀 Deploying the AWS API emulator (moto)..."
kubectl apply -f "${MANIFEST}"

echo
echo "⏳ Waiting for it to become Ready..."
kubectl wait --for=condition=Available deployment/moto \
  --namespace aws-local --timeout=300s

echo
echo "✅ Emulator is up. In-cluster endpoint:"
echo "   http://moto.aws-local.svc.cluster.local:5000"
echo
kubectl get pods,svc -n aws-local
echo
echo "Next: ./scripts/verify-setup.sh"
