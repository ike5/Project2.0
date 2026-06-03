#!/usr/bin/env bash
# One-shot deploy of the capstone reference solution.
# Prereqs: kind cluster up; ingress-nginx installed (Module 05); metrics-server
# installed (Module 08); guestbook:1.0 built and loaded into kind.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "==> Ensuring guestbook:1.0 is loaded into kind..."
if ! docker image inspect guestbook:1.0 >/dev/null 2>&1; then
  echo "Building guestbook:1.0..."
  ( cd "${SCRIPT_DIR}/../../apps/guestbook" && docker build -t guestbook:1.0 . )
fi
kind load docker-image guestbook:1.0 --name k8s-course

echo "==> Applying manifests (ordered)..."
kubectl apply -f "${SCRIPT_DIR}/00-namespace.yaml"
kubectl apply -f "${SCRIPT_DIR}/10-secret.yaml"
kubectl apply -f "${SCRIPT_DIR}/11-configmap.yaml"
kubectl apply -f "${SCRIPT_DIR}/20-redis.yaml"
echo "==> Waiting for Redis..."
kubectl rollout status statefulset/redis -n guestbook --timeout=120s

kubectl apply -f "${SCRIPT_DIR}/30-guestbook.yaml"
kubectl apply -f "${SCRIPT_DIR}/31-ingress.yaml"
kubectl apply -f "${SCRIPT_DIR}/32-hpa.yaml"
kubectl apply -f "${SCRIPT_DIR}/40-networkpolicy.yaml"

echo "==> Waiting for guestbook..."
kubectl rollout status deployment/guestbook -n guestbook --timeout=120s

echo
echo "✅ Deployed. Open http://localhost/ to use the guestbook."
echo "   Try: curl -s http://localhost/api/messages"
