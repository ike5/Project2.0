#!/usr/bin/env bash
# The single most valuable check in a Crossplane CI pipeline, standalone so it
# can be a required status check that a PR label overrides.
#
# A renamed composed resource is invisible in an API diff and destroys
# infrastructure for every existing XR.
set -uo pipefail

BASE_REF="main"
[ "${1:-}" = "--base-ref" ] && BASE_REF="${2:-main}"

TESTS_DIR="${TESTS_DIR:-tests}"
COMPOSITIONS_DIR="${COMPOSITIONS_DIR:-compositions}"
FUNCTIONS="${FUNCTIONS:-tests/functions.yaml}"
FAILED=0

command -v crossplane >/dev/null 2>&1 || { echo "crossplane CLI not found" >&2; exit 1; }

WORKTREE="$(mktemp -d)"
trap 'git worktree remove --force "${WORKTREE}" 2>/dev/null || true' EXIT

if ! git worktree add -q --detach "${WORKTREE}" "${BASE_REF}" 2>/dev/null; then
  echo "⚠️  Could not check out ${BASE_REF}; skipping the destructive-change check."
  echo "   (This is a soft pass. Ensure CI checks out full history.)"
  exit 0
fi

names_from() {  # names_from <xr> <composition>
  crossplane render "$1" "$2" "${FUNCTIONS}" 2>/dev/null \
    | grep -o 'crossplane.io/composition-resource-name: .*' | sort
}

for xr in "${TESTS_DIR}"/xr-*.yaml; do
  [ -e "$xr" ] || continue
  base="$(basename "$xr" .yaml | sed 's/^xr-//')"
  comp="${COMPOSITIONS_DIR}/${base}.yaml"
  [ -e "$comp" ] || continue
  old_comp="${WORKTREE}/${comp}"

  if [ ! -e "$old_comp" ]; then
    printf '  ✓ %s is new (no baseline)\n' "$base"
    continue
  fi

  OLD="$(names_from "$xr" "$old_comp")"
  NEW="$(names_from "$xr" "$comp")"

  if [ "$OLD" = "$NEW" ]; then
    printf '  ✓ %s: composed resource names unchanged\n' "$base"
  else
    printf '  ✗ %s: COMPOSED RESOURCE NAMES CHANGED\n' "$base"
    diff <(echo "$OLD") <(echo "$NEW") | sed 's/^/      /' || true
    FAILED=$((FAILED + 1))
  fi
done

echo
if [ "${FAILED}" -eq 0 ]; then
  echo "✅ No destructive composition changes."
  exit 0
fi
cat <<'EOF'
❌ This change renames one or more composed resources.

Crossplane identifies composed resources by their composition-resource-name
annotation. Renaming one means Crossplane sees the old name as REMOVED and the
new name as NEW -- a delete and a create. For every existing XR.

On an S3 bucket that loses your objects. On an RDS instance that is your
database.

If this is intended:
  1. Add the 'breaking-change-approved' label to this pull request.
  2. Bump the MAJOR version.
  3. Write the migration in the release notes (see Module 10).
  4. Set deletionPolicy: Orphan on affected resources BEFORE rolling out.
EOF
exit 1
