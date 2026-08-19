#!/usr/bin/env bash
# Challenge 14 Task 4 — the test static analysis cannot replace.
#
# Every other check in this course verifies that a composition is INTERNALLY
# COHERENT. This one verifies that it DOES THE THING ANYONE WANTED, by taking
# the XR's output and using it exactly as an application would.
#
# It is the only thing that catches the Module 12 Stack 5 class: a stack where
# every resource is Synced=True Ready=True and the bucket the application was
# told to use does not exist.
set -euo pipefail

CLUSTER="${CLUSTER:-xp-e2e}"
KEEP="${KEEP:-false}"
NS="ci"
EMULATOR="http://moto.aws-local.svc.cluster.local:5000"

step() { printf '\n\033[1m═══ %s ═══\033[0m\n' "$*"; }
ok()   { printf '  \033[32m✓\033[0m %s\n' "$*"; }
die()  { printf '  \033[31m✗ %s\033[0m\n' "$*" >&2; exit 1; }

cleanup() {
  if [ "${KEEP}" = "true" ]; then
    echo "KEEP=true — leaving cluster ${CLUSTER} for inspection"
  else
    kind delete cluster --name "${CLUSTER}" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT

awslocal() {
  kubectl run "awscli-$RANDOM" --rm -i --restart=Never -q \
    --image=amazon/aws-cli:2.18.9 \
    --env=AWS_ACCESS_KEY_ID=test --env=AWS_SECRET_ACCESS_KEY=test \
    --env=AWS_DEFAULT_REGION=us-east-1 \
    -- --endpoint-url="${EMULATOR}" "$@"
}

# ─────────────────────────────────────────────────────────────
step "1. Ephemeral cluster"
kind delete cluster --name "${CLUSTER}" >/dev/null 2>&1 || true
kind create cluster --name "${CLUSTER}" --wait 3m >/dev/null
ok "cluster ${CLUSTER} up"

step "2. Crossplane and the AWS emulator"
helm repo add crossplane-stable https://charts.crossplane.io/stable >/dev/null 2>&1 || true
helm repo update crossplane-stable >/dev/null
helm install crossplane crossplane-stable/crossplane \
  -n crossplane-system --create-namespace --version 2.3.0 --wait --timeout 5m >/dev/null
ok "Crossplane installed"

kubectl apply -f "${EMULATOR_MANIFEST:-../../00-setup/manifests/aws-emulator.yaml}" >/dev/null
kubectl wait --for=condition=Available deploy/moto -n aws-local --timeout=5m >/dev/null
ok "emulator ready"

step "3. Platform"
kubectl apply -f "${BOOTSTRAP:-bootstrap/}" >/dev/null
kubectl wait provider --all --for=condition=Healthy --timeout=10m >/dev/null
kubectl wait function --all --for=condition=Healthy --timeout=10m >/dev/null
ok "providers and functions healthy"

kubectl create secret generic aws-creds -n crossplane-system \
  --from-literal=creds='[default]
aws_access_key_id = test
aws_secret_access_key = test' >/dev/null
kubectl apply -f "${PROVIDERCONFIG:-config/providerconfig.yaml}" >/dev/null
kubectl apply -f "${APIS:-apis/}" >/dev/null
sleep 5
kubectl apply -f "${COMPOSITIONS:-compositions/}" >/dev/null
ok "XRDs and compositions applied"

# ─────────────────────────────────────────────────────────────
step "4. Provision through the platform API"
kubectl create ns "${NS}" >/dev/null
kubectl apply -n "${NS}" -f - >/dev/null <<'YAML'
apiVersion: platform.acme.io/v1alpha1
kind: XBucket
metadata:
  name: e2e
  labels:
    acme.io/owner: ci
spec:
  environment: dev
  retentionDays: 7
YAML

if ! kubectl wait xbucket/e2e -n "${NS}" --for=condition=Ready --timeout=5m >/dev/null; then
  echo
  crossplane trace xbucket e2e -n "${NS}" || true
  die "the XR never became Ready"
fi
ok "XR is Ready"

# ─────────────────────────────────────────────────────────────
step "5. USE the output the way an application would"
#
# THIS IS THE WHOLE POINT. Everything above only proves Crossplane thinks it
# succeeded. Module 12's Stack 5 passed every one of those checks while handing
# the application a bucket name that did not exist.

BUCKET="$(kubectl get xbucket e2e -n "${NS}" -o jsonpath='{.status.bucketName}')"
[ -n "${BUCKET}" ] || die "status.bucketName is empty — an application would have nothing to use"
ok "the platform published bucket name: ${BUCKET}"

# Write, then read back. A NoSuchBucket here is exactly the error the
# application would have hit in production.
if ! echo "e2e probe $(date -u +%s)" | awslocal s3 cp - "s3://${BUCKET}/probe.txt" >/dev/null 2>&1; then
  die "could not write to ${BUCKET} — the name the platform published is not usable"
fi
ok "wrote an object using the published name"

if ! awslocal s3 cp "s3://${BUCKET}/probe.txt" - >/dev/null 2>&1; then
  die "could not read back from ${BUCKET}"
fi
ok "read the object back"

# ─────────────────────────────────────────────────────────────
step "6. Verify the guarantees the platform PROMISED"
#
# A developer never asked for these. The platform said they would be true, so
# the platform's tests must prove they are.

PAB="$(awslocal s3api get-public-access-block --bucket "${BUCKET}" 2>/dev/null || echo '{}')"
echo "${PAB}" | grep -q '"BlockPublicAcls": true' \
  || die "public access is NOT blocked — the platform's core guarantee is broken"
ok "public access is blocked"

LIFECYCLE="$(awslocal s3api get-bucket-lifecycle-configuration --bucket "${BUCKET}" 2>/dev/null || echo '{}')"
echo "${LIFECYCLE}" | grep -q '"Days": 7' \
  || die "the 7-day retention rule the XR requested is not applied"
ok "retention is 7 days, as requested"

# ─────────────────────────────────────────────────────────────
step "7. Teardown actually removes the cloud resource"
kubectl delete xbucket e2e -n "${NS}" --timeout=3m >/dev/null
sleep 20
if awslocal s3 ls 2>/dev/null | grep -q "${BUCKET}"; then
  die "the bucket survived deletion of the XR — check deletionPolicy"
fi
ok "cloud resource removed"

echo
echo "🎉 End-to-end test passed."
echo
echo "   Note what this caught that no static check could: it USED the value"
echo "   the platform published. A composition can be internally consistent and"
echo "   still hand an application a name for something that does not exist."
