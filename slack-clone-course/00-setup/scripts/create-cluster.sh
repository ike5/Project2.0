#!/usr/bin/env bash
# Create the local kind cluster. Idempotent: re-running is a no-op if it exists.
set -euo pipefail
cd "$(dirname "$0")/.."

CLUSTER=slack

if kind get clusters | grep -qx "$CLUSTER"; then
  echo "✓ Cluster '$CLUSTER' already exists. Nothing to do."
else
  echo "Creating cluster '$CLUSTER' (1 control-plane + 2 workers)…"
  kind create cluster --name "$CLUSTER" --config manifests/kind-cluster.yaml
fi

kubectl config use-context "kind-$CLUSTER" >/dev/null
echo "✓ kubectl context set to kind-$CLUSTER"
