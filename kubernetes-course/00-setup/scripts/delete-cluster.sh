#!/usr/bin/env bash
# Delete the course's kind cluster to free up your Mac's CPU/RAM.
set -euo pipefail

CLUSTER_NAME="k8s-course"

if kind get clusters 2>/dev/null | grep -qx "${CLUSTER_NAME}"; then
  echo "🧹 Deleting kind cluster '${CLUSTER_NAME}'..."
  kind delete cluster --name "${CLUSTER_NAME}"
  echo "✅ Gone. Recreate any time with ./scripts/create-cluster.sh"
else
  echo "ℹ️  No cluster named '${CLUSTER_NAME}' found. Nothing to delete."
fi
