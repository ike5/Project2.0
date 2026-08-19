#!/usr/bin/env bash
# The CI gate for a Crossplane platform repo.
#
# Every check here runs WITHOUT A CLUSTER, in seconds, on every pull request.
# That is the single highest-leverage thing you can build for a Crossplane
# platform: the alternative is discovering a destructive composition change
# when it has already destroyed something.
#
# Usage (from the repo root):
#   ./ci/test-compositions.sh
#   ./ci/test-compositions.sh --base-ref origin/main   # also diff-check
set -uo pipefail

BASE_REF=""
[ "${1:-}" = "--base-ref" ] && BASE_REF="${2:-}"

TESTS_DIR="${TESTS_DIR:-tests}"
COMPOSITIONS_DIR="${COMPOSITIONS_DIR:-compositions}"
APIS_DIR="${APIS_DIR:-apis}"
FUNCTIONS="${FUNCTIONS:-tests/functions.yaml}"

FAILED=0
step() { printf '\n\033[1m═══ %s ═══\033[0m\n' "$*"; }
ok()   { printf '  \033[32m✓\033[0m %s\n' "$*"; }
bad()  { printf '  \033[31m✗\033[0m %s\n' "$*"; FAILED=$((FAILED + 1)); }

command -v crossplane >/dev/null 2>&1 || {
  echo "crossplane CLI not found" >&2; exit 1; }

# ─────────────────────────────────────────────────────────────
step "1. YAML is parseable"
# The cheapest check there is. Run it first so a typo does not produce a
# confusing failure three steps later.
while IFS= read -r f; do
  if python3 -c "import yaml,sys; list(yaml.safe_load_all(open(sys.argv[1])))" "$f" 2>/dev/null; then
    ok "$f"
  else
    bad "$f is not valid YAML"
  fi
done < <(find "${APIS_DIR}" "${COMPOSITIONS_DIR}" -name '*.yaml' 2>/dev/null)

# ─────────────────────────────────────────────────────────────
step "2. Every composition renders"
# A composition that does not render produces NOTHING at all -- not even the
# resources with no dependencies (Module 12, stack 3).
for xr in "${TESTS_DIR}"/xr-*.yaml; do
  [ -e "$xr" ] || continue
  name="$(basename "$xr" .yaml)"
  comp="${COMPOSITIONS_DIR}/$(basename "$xr" .yaml | sed 's/^xr-//').yaml"
  [ -e "$comp" ] || comp="$(ls "${COMPOSITIONS_DIR}"/*.yaml 2>/dev/null | head -1)"
  if crossplane render "$xr" "$comp" "${FUNCTIONS}" > "/tmp/${name}.rendered" 2>/tmp/render.err; then
    count=$(grep -c '^kind:' "/tmp/${name}.rendered" || echo 0)
    ok "$name renders ($count resources)"
  else
    bad "$name FAILED to render"
    sed 's/^/      /' /tmp/render.err | head -5
  fi
done

# ─────────────────────────────────────────────────────────────
step "3. Rendered output validates against real schemas"
for rendered in /tmp/xr-*.rendered; do
  [ -e "$rendered" ] || continue
  name="$(basename "$rendered" .rendered)"
  if crossplane validate "${APIS_DIR}" "$rendered" >/tmp/validate.err 2>&1; then
    ok "$name validates"
  else
    bad "$name failed schema validation"
    sed 's/^/      /' /tmp/validate.err | head -5
  fi
done

# ─────────────────────────────────────────────────────────────
step "4. Compositions are internally consistent"
# Catches the "everything green and nothing works" class from Module 12:
# a resource referencing a bucket no other resource creates, or a status field
# handing an application a name that does not exist.
if [ -x ./ci/consistency-check.sh ]; then
  for rendered in /tmp/xr-*.rendered; do
    [ -e "$rendered" ] || continue
    name="$(basename "$rendered" .rendered)"
    if ./ci/consistency-check.sh --stdin < "$rendered" >/tmp/cons.err 2>&1; then
      ok "$name is internally consistent"
    else
      bad "$name has consistency errors"
      sed 's/^/      /' /tmp/cons.err | head -8
    fi
  done
else
  echo "  (skipped: ci/consistency-check.sh not present)"
fi

# ─────────────────────────────────────────────────────────────
step "5. IAM policies are safe"
if [ -x ./ci/policy-lint.sh ]; then
  for rendered in /tmp/xr-*.rendered; do
    [ -e "$rendered" ] || continue
    name="$(basename "$rendered" .rendered)"
    if ./ci/policy-lint.sh --stdin < "$rendered" >/tmp/iam.err 2>&1; then
      ok "$name IAM policies pass"
    else
      bad "$name has unsafe IAM"
      sed 's/^/      /' /tmp/iam.err | head -8
    fi
  done
else
  echo "  (skipped: ci/policy-lint.sh not present)"
fi

# ─────────────────────────────────────────────────────────────
step "6. No destructive composition changes"
# THE MOST IMPORTANT CHECK IN THIS FILE.
#
# A renamed composed resource is INVISIBLE in an API diff and DESTROYS
# infrastructure for every existing XR. It is the only change in Crossplane
# where a three-character edit, reviewed by two competent engineers, can delete
# a production database.
if [ -z "${BASE_REF}" ]; then
  echo "  (skipped: pass --base-ref origin/main to enable)"
else
  WORKTREE="$(mktemp -d)"
  if git worktree add -q --detach "${WORKTREE}" "${BASE_REF}" 2>/dev/null; then
    for xr in "${TESTS_DIR}"/xr-*.yaml; do
      [ -e "$xr" ] || continue
      name="$(basename "$xr" .yaml)"
      comp="${COMPOSITIONS_DIR}/$(basename "$xr" .yaml | sed 's/^xr-//').yaml"
      old_comp="${WORKTREE}/${comp}"
      [ -e "$old_comp" ] || { ok "$name is new (no baseline to compare)"; continue; }

      crossplane render "$xr" "$old_comp" "${FUNCTIONS}" > /tmp/old.rendered 2>/dev/null
      OLD=$(grep -o 'crossplane.io/composition-resource-name: .*' /tmp/old.rendered | sort || true)
      NEW=$(grep -o 'crossplane.io/composition-resource-name: .*' "/tmp/${name}.rendered" | sort || true)

      if [ "$OLD" = "$NEW" ]; then
        ok "$name: composed resource names unchanged"
      else
        bad "$name: COMPOSED RESOURCE NAMES CHANGED"
        echo "      This will DELETE AND RECREATE infrastructure for every"
        echo "      existing XR. On a database, that is your data."
        diff <(echo "$OLD") <(echo "$NEW") | sed 's/^/      /' || true
        echo "      If this is intended, add the 'breaking-change-approved'"
        echo "      label to the pull request and write the migration in the"
        echo "      release notes."
      fi
    done
    git worktree remove --force "${WORKTREE}" 2>/dev/null
  else
    echo "  (skipped: could not check out ${BASE_REF})"
  fi
fi

# ─────────────────────────────────────────────────────────────
echo
if [ "${FAILED}" -eq 0 ]; then
  echo "🎉 All checks passed."
else
  echo "❌ ${FAILED} check(s) failed."
  exit 1
fi
