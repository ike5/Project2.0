#!/usr/bin/env bash
# Challenge 11 Task 3 — report on composition revision usage.
#
# Revision sprawl is silent: nobody notices two XRs pinned since a rollout
# eleven weeks ago until a security fix goes out and they do not get it.
# Run this weekly; treat "pinned more than 30 days" as a bug to close.
#
# Usage: ./revision-report.sh <xr-kind> [stale-days]
set -uo pipefail

KIND="${1:-}"
STALE_DAYS="${2:-30}"
if [ -z "${KIND}" ]; then
  echo "usage: $0 <xr-kind> [stale-days]   eg: $0 xdatabases 30" >&2
  exit 2
fi

kubectl get "${KIND}" -A -o json > /tmp/xrs.json 2>/dev/null || {
  echo "❌ no ${KIND} found" >&2; exit 1; }
kubectl get compositionrevisions -o json > /tmp/revs.json 2>/dev/null

STALE_DAYS="${STALE_DAYS}" python3 - <<'PY'
import json
import os
from collections import defaultdict
from datetime import datetime, timezone

stale_days = int(os.environ["STALE_DAYS"])
xrs = json.load(open("/tmp/xrs.json"))["items"]
revs = json.load(open("/tmp/revs.json"))["items"]

now = datetime.now(timezone.utc)


def age_days(ts):
    return (now - datetime.fromisoformat(ts.replace("Z", "+00:00"))).days


# revision name -> (composition name, revision number, age)
info = {}
latest = defaultdict(int)
for r in revs:
    comp = r["metadata"].get("labels", {}).get(
        "crossplane.io/composition-name", r["metadata"]["name"])
    num = r.get("spec", {}).get("revision", 0)
    info[r["metadata"]["name"]] = (
        comp, num, age_days(r["metadata"]["creationTimestamp"]))
    latest[comp] = max(latest[comp], num)

# Group the XRs by the revision they are actually on.
usage = defaultdict(list)
unpinned = []
for xr in xrs:
    cp = xr.get("spec", {}).get("crossplane", {}) or {}
    ref = (cp.get("compositionRevisionRef") or {}).get("name")
    policy = cp.get("compositionUpdatePolicy", "Automatic")
    ident = f"{xr['metadata'].get('namespace','-')}/{xr['metadata']['name']}"
    if not ref:
        unpinned.append(ident)
        continue
    usage[ref].append((ident, policy, age_days(xr["metadata"]["creationTimestamp"])))

by_comp = defaultdict(list)
for revname, members in usage.items():
    comp, num, age = info.get(revname, ("<unknown>", 0, 0))
    by_comp[comp].append((num, revname, age, members))

total = sum(len(m) for m in usage.values()) + len(unpinned)
behind = []

for comp, entries in sorted(by_comp.items()):
    print(f"\nComposition: {comp}")
    print(f"  {'REVISION':<9}{'AGE':<8}{'XRs':<6}STATUS")
    for num, revname, age, members in sorted(entries):
        gap = latest[comp] - num
        if gap == 0:
            status = "(latest)"
        else:
            status = f"← {gap} behind" + ("  ⚠️" if gap > 1 else "")
        print(f"  {num:<9}{str(age)+'d':<8}{len(members):<6}{status}")
        if gap > 1:
            for ident, policy, xr_age in members:
                behind.append((ident, num, xr_age, policy))

print(f"\n  {total} XRs total.")
if unpinned:
    print(f"  {len(unpinned)} on Automatic (will follow the latest revision).")

if behind:
    print(f"\n  ⚠️  {len(behind)} XRs are more than one revision behind:")
    for ident, num, xr_age, policy in behind:
        print(f"        {ident:<36} (revision {num}, {policy}, {xr_age}d old)")
    print("\n  These stopped receiving fixes when they were pinned. Either move")
    print("  them forward or record why they must stay.")

stale = [b for b in behind if b[2] > stale_days]
if stale:
    print(f"\n  🚨 {len(stale)} have been behind for more than {stale_days} days.")
    raise SystemExit(1)
PY
