#!/usr/bin/env bash
# Create the course's kind cluster. Idempotent: if it already exists, do nothing.
set -euo pipefail

CLUSTER_NAME="k8s-course"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG="${SCRIPT_DIR}/../manifests/kind-cluster.yaml"

if ! command -v kind >/dev/null 2>&1; then
  echo "❌ 'kind' is not installed. Run: brew install kind" >&2
  exit 1
fi

if ! docker info >/dev/null 2>&1; then
  echo "❌ Docker doesn't seem to be running. Start Docker Desktop and try again." >&2
  exit 1
fi

if kind get clusters 2>/dev/null | grep -qx "${CLUSTER_NAME}"; then
  echo "✅ Cluster '${CLUSTER_NAME}' already exists. Nothing to do."
  echo "   (To recreate it: ./scripts/delete-cluster.sh && ./scripts/create-cluster.sh)"
  exit 0
fi

echo "🚀 Creating kind cluster '${CLUSTER_NAME}' (1 control-plane + 2 workers)..."
kind create cluster --name "${CLUSTER_NAME}" --config "${CONFIG}"

echo
echo "⏳ Waiting for all nodes to become Ready..."
kubectl wait --for=condition=Ready nodes --all --timeout=120s

echo
echo "✅ Done. Your cluster:"
kubectl get nodes
echo
echo "Next: ./scripts/verify-setup.sh"
