#!/usr/bin/env bash
# Challenge 14 Task 3 — distinguish late-initialization noise from real drift.
#
# ignoreDifferences on /spec/forProvider is a blunt instrument: it suppresses
# Crossplane's own late-init writes AND a human's console edit, because Argo CD
# cannot tell them apart from a JSON diff.
#
# This compares THREE sources instead of two:
#   1. What git says      (crossplane render of the committed composition)
#   2. What the cluster's spec says
#   3. What the cloud actually is (status.atProvider)
#
# READ THE LIMITS SECTION AT THE BOTTOM. This is a partial control.
set -uo pipefail

KIND="${1:-}"; NAME="${2:-}"; NS="${3:-default}"
COMPOSITION="${4:-}"; FUNCTIONS="${5:-}"

if [ -z "${KIND}" ] || [ -z "${NAME}" ]; then
  echo "usage: $0 <xr-kind> <xr-name> [namespace] [composition.yaml] [functions.yaml]" >&2
  exit 2
fi

echo "Drift check: ${KIND}/${NAME} in ${NS}"

# Source 1: what git would produce.
if [ -n "${COMPOSITION}" ] && [ -n "${FUNCTIONS}" ]; then
  kubectl get "${KIND}" "${NAME}" -n "${NS}" -o yaml > /tmp/live-xr.yaml 2>/dev/null
  crossplane render /tmp/live-xr.yaml "${COMPOSITION}" "${FUNCTIONS}" > /tmp/from-git.yaml 2>/dev/null \
    || echo "⚠️  could not render from git; skipping source 1"
fi

# Sources 2 and 3: the live spec and the observed cloud state.
kubectl get managed -o json > /tmp/live-managed.json 2>/dev/null

python3 - <<'PY'
import json
import os

import yaml

live = json.load(open("/tmp/live-managed.json"))["items"]

from_git = {}
if os.path.exists("/tmp/from-git.yaml"):
    for d in yaml.safe_load_all(open("/tmp/from-git.yaml")):
        if isinstance(d, dict):
            ann = (d.get("metadata") or {}).get("annotations") or {}
            n = ann.get("crossplane.io/composition-resource-name")
            if n:
                from_git[n] = (d.get("spec") or {}).get("forProvider") or {}

benign = real = cannot_converge = 0

for mr in live:
    ann = (mr["metadata"].get("annotations") or {})
    rname = ann.get("crossplane.io/composition-resource-name")
    ident = f"{mr['kind']}/{mr['metadata']['name']}"
    spec_fp = (mr.get("spec") or {}).get("forProvider") or {}
    at_provider = (mr.get("status") or {}).get("atProvider") or {}
    git_fp = from_git.get(rname)

    if git_fp is None:
        continue

    for key, spec_val in spec_fp.items():
        git_val = git_fp.get(key)
        cloud_val = at_provider.get(key)

        if git_val is None:
            # Not in git. Benign IF it matches reality -- that is exactly what
            # late initialization does.
            if cloud_val is not None and cloud_val == spec_val:
                benign += 1
            else:
                real += 1
                print(f"  🚨 {ident}.{key} is set in the cluster, absent from git,")
                print(f"     and does not match the cloud. Someone edited this directly.")
                print(f"     spec={spec_val!r} cloud={cloud_val!r}")
        elif git_val != spec_val:
            # In BOTH and disagreeing: the live declaration was edited.
            real += 1
            print(f"  🚨 {ident}.{key} differs from git.")
            print(f"     git={git_val!r} cluster={spec_val!r}")
        elif cloud_val is not None and cloud_val != spec_val:
            # Declaration matches git, but the cloud does not match the
            # declaration -- the provider cannot converge (Module 12).
            cannot_converge += 1
            print(f"  ⚠️  {ident}.{key}: the cloud does not match the declaration.")
            print(f"     declared={spec_val!r} cloud={cloud_val!r}")
            print(f"     If this persists past a reconcile interval, the provider")
            print(f"     cannot apply it. Read the Synced condition.")

print()
print(f"  {benign} benign late-init field(s)")
print(f"  {real} genuine drift finding(s)")
print(f"  {cannot_converge} field(s) the provider cannot converge")

if real:
    raise SystemExit(1)
PY

cat <<'LIMITS'

── What this check CANNOT tell apart (be honest about this) ──

1. A new provider version's late-init defaults look identical to a console
   edit: both are "a field appeared that git lacks, and it matches reality".
   Expect a burst of false positives after any deliberate provider upgrade,
   and re-baseline afterwards.

2. A console change Crossplane has ALREADY corrected is invisible here. By the
   time this runs, reality matches the declaration again. Catching that needs
   CloudTrail, not Kubernetes.

3. It cannot see changes to fields the composition never declared. Crossplane
   only reconciles what you declared (Module 01's challenge), so a rogue tag on
   an undeclared field is drift no Kubernetes-side check will find.

For genuine "who changed what in our cloud account", you need CloudTrail with
alerting on console-originated writes, and ideally an SCP denying console
writes to production. This check is worth having; it is not a substitute.
LIMITS
