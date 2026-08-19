#!/usr/bin/env bash
# Challenge 11 Task 2 — preflight.sh plus three more destructive-change checks.
#
# The dangerous composition changes are the ones with NO VISIBLE API SURFACE.
# A linter that only diffs the XRD schema catches none of these.
#
# Usage:
#   ./preflight-plus.sh <old-composition> <new-composition> <sample-xr> <functions>
set -uo pipefail

if [ "$#" -ne 4 ]; then
  echo "usage: $0 <old.yaml> <new.yaml> <sample-xr.yaml> <functions.yaml>" >&2
  exit 2
fi
OLD="$1"; NEW="$2"; XR="$3"; FUNCS="$4"

command -v crossplane >/dev/null 2>&1 || { echo "❌ crossplane CLI not found" >&2; exit 1; }

OLD_OUT="$(mktemp)"; NEW_OUT="$(mktemp)"
trap 'rm -f "${OLD_OUT}" "${NEW_OUT}"' EXIT

crossplane render "${XR}" "${OLD}"  "${FUNCS}" > "${OLD_OUT}" 2>/dev/null
crossplane render "${XR}" "${NEW}"  "${FUNCS}" > "${NEW_OUT}" 2>/dev/null

OLD_OUT="${OLD_OUT}" NEW_OUT="${NEW_OUT}" python3 - <<'PY'
import os
import sys

import yaml

NAME_ANNOTATION = "crossplane.io/composition-resource-name"
EXTERNAL_NAME = "crossplane.io/external-name"


def index(path):
    """resource-name -> the rendered document."""
    out = {}
    with open(path) as fh:
        for doc in yaml.safe_load_all(fh):
            if not isinstance(doc, dict):
                continue
            ann = (doc.get("metadata") or {}).get("annotations") or {}
            name = ann.get(NAME_ANNOTATION)
            if name:
                out[name] = doc
    return out


old = index(os.environ["OLD_OUT"])
new = index(os.environ["NEW_OUT"])
problems = 0

print("── 1. Renamed resources (delete + recreate) ──")
renamed = set(old) ^ set(new)
added, removed = set(new) - set(old), set(old) - set(new)
# A rename looks like one removal plus one addition, so report them separately
# and let the reader judge -- guessing which addition pairs with which removal
# would be worse than saying nothing.
if not renamed:
    print("✅ Composed resource names are unchanged.")
else:
    if removed:
        problems += 1
        print("🚨 A COMPOSED RESOURCE WAS REMOVED: " + ", ".join(sorted(removed)))
        print("   Crossplane garbage-collects composed resources that are no")
        print("   longer desired. This DELETES that resource for every existing XR.")
        print("   If you meant to RENAME it, that is the same thing: the old name")
        print("   is deleted and the new one created.")
    if added:
        print(f"ℹ️  New composed resource(s): {', '.join(sorted(added))}")
        print("   Adding a resource is safe on its own -- but if this is half of")
        print("   a rename, see the removal above.")

print("\n── 2. Changed external names (orphan + recreate) ──")
ext_changed = []
for name in sorted(set(old) & set(new)):
    o = ((old[name].get("metadata") or {}).get("annotations") or {}).get(EXTERNAL_NAME)
    n = ((new[name].get("metadata") or {}).get("annotations") or {}).get(EXTERNAL_NAME)
    if o != n:
        ext_changed.append((name, o, n))
if not ext_changed:
    print("✅ External names are unchanged.")
else:
    problems += 1
    for name, o, n in ext_changed:
        print(f'🚨 EXTERNAL NAME CHANGED for resource "{name}":')
        print(f"     old: {o}")
        print(f"     new: {n}")
    print("   A changed external name does NOT rename anything in the cloud.")
    print("   It points Crossplane at a DIFFERENT resource: the existing one is")
    print("   ORPHANED (still running, unmanaged, still billed) and a new one is")
    print("   created. On a database, the old data becomes invisible to the")
    print("   platform while an empty instance takes its place.")

print("\n── 3. Weakened deletion protection ──")
weakened = []
for name in sorted(set(old) & set(new)):
    o = (old[name].get("spec") or {}).get("deletionPolicy")
    n = (new[name].get("spec") or {}).get("deletionPolicy")
    if o != n:
        weakened.append((name, o, n))
if not weakened:
    print("✅ deletionPolicy is unchanged.")
else:
    for name, o, n in weakened:
        if o == "Orphan" and n in (None, "Delete"):
            problems += 1
            print(f'⚠️  deletionPolicy changed Orphan -> {n or "Delete (default)"} '
                  f'for resource "{name}".')
            print("   Deleting the XR will now DESTROY the cloud resource.")
            print("   Confirm this is intended.")
        else:
            print(f'ℹ️  deletionPolicy changed {o} -> {n} for resource "{name}".')

print()
if problems:
    print(f"⚠️  {problems} destructive change(s) detected. Do not roll this out")
    print("   without a canary on something you can afford to lose.")
    sys.exit(1)
print("🎉 No destructive changes detected.")
PY
