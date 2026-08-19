#!/usr/bin/env bash
# Challenge 05 Task 5 — structural assertions over `crossplane render` output.
#
# Runs entirely offline (no cluster, no AWS) so it is fast enough for CI on
# every pull request. Module 14 builds on this.
set -uo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FUNCS="${HERE}/../manifests/render/functions.yaml"
FAILED=0
WORK="$(mktemp -d)"
trap 'rm -rf "${WORK}"' EXIT

# assert <description> <expected> <actual>
assert() {
  local desc="$1" expected="$2" actual="$3"
  printf '▶ %-50s' "$desc"
  if [ "$expected" = "$actual" ]; then
    echo "✅"
  else
    echo "❌"
    echo "    expected: ${expected}"
    echo "    actual:   ${actual}"
    FAILED=$((FAILED + 1))
  fi
}

render() {  # render <xr-file> <composition-file>
  crossplane render "$1" "$2" "${FUNCS}" 2>/dev/null
}

if ! command -v crossplane >/dev/null 2>&1; then
  echo "❌ crossplane CLI not found — see 00-setup/README.md" >&2
  exit 1
fi
if ! docker info >/dev/null 2>&1; then
  echo "❌ Docker is not running — crossplane render executes functions locally" >&2
  exit 1
fi

# ---- fixtures -------------------------------------------------------------
cat > "${WORK}/site-private.yaml" <<'YAML'
apiVersion: platform.acme.io/v1alpha1
kind: XStaticSite
metadata: { name: t, namespace: test }
spec: { indexDocument: index.html, public: false }
YAML

cat > "${WORK}/site-public.yaml" <<'YAML'
apiVersion: platform.acme.io/v1alpha1
kind: XStaticSite
metadata: { name: t, namespace: test }
spec: { indexDocument: index.html, public: true }
YAML

cat > "${WORK}/lake-3zone.yaml" <<'YAML'
apiVersion: platform.acme.io/v1alpha1
kind: XDataLake
metadata: { name: t, namespace: test }
spec:
  region: us-east-1
  zones: [us-east-1a, us-east-1b, us-east-1c]
  enableAudit: false
  retentionDays: 30
YAML

SITE_COMP="${HERE}/xstaticsite-templated.yaml"
LAKE_COMP="${HERE}/../manifests/composition-templated.yaml"

# ---- tests ----------------------------------------------------------------
echo "Running composition render tests..."
echo

# A private site must not produce a bucket policy AT ALL.
assert "private site produces no BucketPolicy" "0" \
  "$(render "${WORK}/site-private.yaml" "${SITE_COMP}" | grep -c '^kind: BucketPolicy')"

assert "public site produces exactly one BucketPolicy" "1" \
  "$(render "${WORK}/site-public.yaml" "${SITE_COMP}" | grep -c '^kind: BucketPolicy')"

# 3 zones -> 3 buckets + 3 lifecycle configurations.
assert "3-zone lake produces 6 resources" "6" \
  "$(render "${WORK}/lake-3zone.yaml" "${LAKE_COMP}" | grep -c '^kind:')"

# Every S3 Bucket needs a deterministic external name; a missing one means
# Crossplane would generate a random bucket name we cannot predict or reference.
LAKE_OUT="$(render "${WORK}/lake-3zone.yaml" "${LAKE_COMP}")"
BUCKETS="$(echo "${LAKE_OUT}" | grep -c '^kind: Bucket$')"
NAMED="$(echo "${LAKE_OUT}" | grep -c 'crossplane.io/external-name')"
assert "every Bucket has an external-name" "${BUCKETS}" "${NAMED}"

# Resource names must be stable when a zone is REMOVED from the middle of the
# list. This is the delete-and-recreate bug from Lab 05 Part F.
cat > "${WORK}/lake-2zone.yaml" <<'YAML'
apiVersion: platform.acme.io/v1alpha1
kind: XDataLake
metadata: { name: t, namespace: test }
spec:
  region: us-east-1
  zones: [us-east-1a, us-east-1c]
  enableAudit: false
  retentionDays: 30
YAML
BEFORE="$(render "${WORK}/lake-3zone.yaml" "${LAKE_COMP}" \
  | grep 'crossplane.io/external-name' | grep 'us-east-1c' | tr -d ' ')"
AFTER="$(render "${WORK}/lake-2zone.yaml" "${LAKE_COMP}" \
  | grep 'crossplane.io/external-name' | grep 'us-east-1c' | tr -d ' ')"
assert "removing a middle zone keeps other names stable" "${BEFORE}" "${AFTER}"

echo
if [ "${FAILED}" -eq 0 ]; then
  echo "🎉 All tests passed."
else
  echo "${FAILED} test(s) failed."
  exit 1
fi
