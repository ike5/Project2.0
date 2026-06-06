#!/usr/bin/env bash
# Delete the local kind cluster to free RAM. Recreate any time with create-cluster.sh.
set -euo pipefail
kind delete cluster --name slack
echo "✓ Cluster 'slack' deleted."
