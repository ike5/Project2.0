#!/usr/bin/env bash
# Confirm the cluster is healthy: 3 nodes, all Ready.
set -euo pipefail

echo "== Tool versions =="
kind version
kubectl version --client | head -n1

echo
echo "== Nodes (expect 3 Ready) =="
kubectl get nodes

ready=$(kubectl get nodes --no-headers | grep -c " Ready ") || true
if [ "$ready" -ge 3 ]; then
  echo "✓ $ready nodes Ready."
else
  echo "✗ Only $ready nodes Ready — wait 30–60s for the CNI and re-run."
  exit 1
fi
