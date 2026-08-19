#!/usr/bin/env bash
# Challenge 12 Task 3 — catch the "green but wrong" class.
#
# Renders a composition and asserts that its resources are INTERNALLY
# CONSISTENT: every cross-resource reference names something the same render
# produces, and every status value matches a real external name.
#
# This is the check that would have caught Stack 5, in CI, with no cluster.
# See solution.md for what it still misses.
#
# Usage:
#   ./consistency-check.sh <xr.yaml> <composition.yaml> <functions.yaml>
#   ./consistency-check.sh --stdin < rendered.yaml
set -uo pipefail

CHECKER="$(mktemp)"
trap 'rm -f "${CHECKER}"' EXIT

# Written to a temp file rather than fed via heredoc, because a heredoc would
# occupy stdin and swallow the YAML we are trying to check.
cat > "${CHECKER}" <<'PY'
import sys

import yaml

NAME_ANN = "crossplane.io/composition-resource-name"
EXT_ANN = "crossplane.io/external-name"

# Fields that reference another resource by its cloud name.
REF_FIELDS = ("bucket", "dbInstanceIdentifier", "tableName", "replicateSourceDb")

docs = [d for d in yaml.safe_load_all(sys.stdin) if isinstance(d, dict)]

# Every external name this composition actually creates.
created = {}
for d in docs:
    ann = (d.get("metadata") or {}).get("annotations") or {}
    ext = ann.get(EXT_ANN)
    if ext:
        created[ext] = ann.get(NAME_ANN, "<unnamed>")

problems = []

# 1. Cross-resource references must name something this render creates.
for d in docs:
    ann = (d.get("metadata") or {}).get("annotations") or {}
    rname = ann.get(NAME_ANN, "<unnamed>")
    fp = (d.get("spec") or {}).get("forProvider") or {}
    for field in REF_FIELDS:
        val = fp.get(field)
        if isinstance(val, str) and val and val not in created:
            names = ", ".join(sorted(created)) or "none"
            problems.append(
                'resource "{r}" references {f} "{v}", which no resource in this '
                "composition creates.\n"
                "      Rendered external names: {n}".format(
                    r=rname, f=field, v=val, n=names))

# 2. status.*Name values must match something real. An application handed a
#    name that does not exist fails at runtime, long after everything went green.
for d in docs:
    st = d.get("status") or {}
    if not isinstance(st, dict):
        continue
    for key, val in st.items():
        if key.lower().endswith("name") and isinstance(val, str) and val:
            if val not in created:
                problems.append(
                    'status.{k} = "{v}" does not match any rendered external '
                    "name.\n      An application given this value will fail at "
                    "runtime.".format(k=key, v=val))

# 3. Two resources of the same kind must not claim one external name.
seen = {}
for d in docs:
    ann = (d.get("metadata") or {}).get("annotations") or {}
    ext, rname = ann.get(EXT_ANN), ann.get(NAME_ANN)
    kind = d.get("kind")
    if ext and kind:
        key = (kind, ext)
        if key in seen:
            problems.append(
                'two resources claim the same external name "{e}" ({a} and {b}). '
                "One will overwrite the other.".format(e=ext, a=seen[key], b=rname))
        seen[key] = rname

if problems:
    for p in problems:
        print("    x " + p)
    print("\n{n} consistency error(s)".format(n=len(problems)))
    sys.exit(1)

print("    OK internally consistent ({n} named resources)".format(n=len(created)))
PY

if [ "${1:-}" = "--stdin" ]; then
  python3 "${CHECKER}"
else
  if [ "$#" -ne 3 ]; then
    echo "usage: $0 <xr.yaml> <composition.yaml> <functions.yaml>" >&2
    echo "       $0 --stdin < rendered.yaml" >&2
    exit 2
  fi
  command -v crossplane >/dev/null 2>&1 || {
    echo "crossplane CLI not found - see 00-setup/README.md" >&2; exit 1; }
  crossplane render "$1" "$2" "$3" 2>/dev/null | python3 "${CHECKER}"
fi
