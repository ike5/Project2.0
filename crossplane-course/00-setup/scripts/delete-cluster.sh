#!/usr/bin/env bash
# Delete the course cluster and free your laptop's RAM.
#
# Everything in this course is declarative YAML in git, so throwing the cluster away
# costs you nothing but the ~5 minutes it takes to rebuild. Do it at the end of every
# session.
set -euo pipefail

CLUSTER_NAME="xp-course"

if ! kind get clusters 2>/dev/null | grep -qx "${CLUSTER_NAME}"; then
  echo "✅ Cluster '${CLUSTER_NAME}' doesn't exist. Nothing to do."
  exit 0
fi

echo "🧹 Deleting kind cluster '${CLUSTER_NAME}'..."
kind delete cluster --name "${CLUSTER_NAME}"
echo "✅ Gone. Rebuild any time with ./scripts/create-cluster.sh"
