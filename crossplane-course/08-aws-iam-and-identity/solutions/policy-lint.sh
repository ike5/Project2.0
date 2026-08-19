#!/usr/bin/env bash
# Challenge 08 Task 5 — lint IAM policy documents produced by compositions.
#
# Runs against RENDERED output, not composition source: the policies are
# generated, so bugs live in template logic and only appear after rendering.
#
# Usage:
#   ./policy-lint.sh <xr.yaml> <composition.yaml> <functions.yaml>
#   ./policy-lint.sh --stdin < rendered.yaml
#   crossplane render ... | ./policy-lint.sh --stdin
set -uo pipefail

LINTER="$(mktemp)"
trap 'rm -f "${LINTER}"' EXIT

# The checker is written to a temp file rather than fed via heredoc, because a
# heredoc would occupy stdin and swallow the YAML we are trying to lint.
cat > "${LINTER}" <<'PY'
import json
import sys

import yaml

# Actions that mean "can grant itself anything".
IAM_ESCALATION = {
    "iam:*", "iam:CreatePolicyVersion", "iam:AttachRolePolicy",
    "iam:AttachUserPolicy", "iam:PutRolePolicy", "iam:CreateAccessKey",
    "iam:UpdateAssumeRolePolicy", "iam:DeleteRolePermissionsBoundary",
}


def as_list(v):
    if v is None:
        return []
    return v if isinstance(v, list) else [v]


def check(doc):
    """Return a list of problem strings for one policy document."""
    problems = []
    for i, st in enumerate(as_list(doc.get("Statement"))):
        if not isinstance(st, dict):
            continue
        # Deny statements are constraints, not grants -- breadth is fine there.
        if st.get("Effect", "Allow") != "Allow":
            continue

        actions = as_list(st.get("Action"))
        resources = as_list(st.get("Resource"))
        has_condition = bool(st.get("Condition"))

        if "*" in actions:
            problems.append(f'statement {i}: Action "*" with Effect Allow')

        if "*" in resources and any(a.endswith(":*") for a in actions):
            problems.append(f'statement {i}: service-wide Action on Resource "*"')

        for a in actions:
            if a in IAM_ESCALATION or (a.startswith("iam:") and a.endswith("*")):
                problems.append(
                    f"statement {i}: {a} in an Allow statement "
                    "(privilege escalation path)")
                break

        # PassRole on * is equivalent to "assume any role in the account".
        if "iam:PassRole" in actions:
            if "*" in resources:
                problems.append(
                    f'statement {i}: iam:PassRole on Resource "*" '
                    "(equivalent to AdministratorAccess)")
            elif not has_condition:
                problems.append(
                    f"statement {i}: iam:PassRole without an "
                    "iam:PassedToService condition")

        # The silent no-op: ListBucket acts on the bucket, not on its objects.
        if "s3:ListBucket" in actions:
            for r in resources:
                if r.endswith("/*"):
                    problems.append(
                        f"statement {i}: s3:ListBucket on an object ARN "
                        f"({r}) -- grants nothing")
    return problems


checked = failed = skipped = 0
for d in yaml.safe_load_all(sys.stdin):
    if not isinstance(d, dict):
        continue
    fp = (d.get("spec") or {}).get("forProvider") or {}
    meta = d.get("metadata") or {}
    name = meta.get("name") or fp.get("name") or "<unnamed>"

    # A PERMISSIONS BOUNDARY IS A CEILING, NOT A GRANT. Its breadth is the
    # point: it caps what attached policies can achieve and grants nothing on
    # its own. Flagging it for wildcards would be a false positive, so a
    # boundary must opt out explicitly -- and reviewers should check that the
    # opt-out is honest.
    if (meta.get("annotations") or {}).get("policy-lint/kind") == "boundary":
        skipped += 1
        print(f"▶ {name:<55} ⏭  boundary (breadth checks skipped)")
        continue

    for key in ("policy", "assumeRolePolicy"):
        raw = fp.get(key)
        if not isinstance(raw, str) or not raw.strip().startswith("{"):
            continue
        checked += 1
        label = f"{name} .{key}"
        try:
            doc = json.loads(raw)
        except json.JSONDecodeError as e:
            failed += 1
            print(f"▶ {label}\n    ✗ invalid JSON: {e}")
            continue
        problems = check(doc)
        if problems:
            failed += 1
            print(f"▶ {label}")
            for p in problems:
                print(f"    ✗ {p}")
        else:
            print(f"▶ {label:<55} ✅")

print()
summary = f"{checked} policy document(s) checked, {failed} failed"
if skipped:
    summary += f", {skipped} boundary policy(ies) skipped"
print(summary)
sys.exit(1 if failed else 0)
PY

if [ "${1:-}" = "--stdin" ]; then
  python3 "${LINTER}"
else
  if [ "$#" -ne 3 ]; then
    echo "usage: $0 <xr.yaml> <composition.yaml> <functions.yaml>" >&2
    echo "       $0 --stdin < rendered.yaml" >&2
    exit 2
  fi
  command -v crossplane >/dev/null 2>&1 || {
    echo "❌ crossplane CLI not found — see 00-setup/README.md" >&2; exit 1; }
  crossplane render "$1" "$2" "$3" | python3 "${LINTER}"
fi
