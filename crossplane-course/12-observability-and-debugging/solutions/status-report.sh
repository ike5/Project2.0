#!/usr/bin/env bash
# Challenge 12 Task 5 — the "what is broken right now" view.
#
# For every XR: readiness, HOW LONG it has been in that state, which composed
# resource is blocking it, and the raw cloud error. No built-in command gives
# you this, and it is the first thing a platform on-call wants.
#
# Usage: ./status-report.sh [xr-kind]     (omit the kind for all composites)
set -uo pipefail

KIND="${1:-composite}"

kubectl get "${KIND}" -A -o json > /tmp/xr-status.json 2>/dev/null || {
  echo "❌ could not list ${KIND}" >&2; exit 1; }
kubectl get managed -o json > /tmp/mr-status.json 2>/dev/null || echo '{"items":[]}' > /tmp/mr-status.json

python3 - <<'PY'
import json
from datetime import datetime, timezone

now = datetime.now(timezone.utc)


def parse(ts):
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))


def hhmmss(delta):
    total = int(delta.total_seconds())
    if total >= 86400:
        return f"{total // 86400}d{(total % 86400) // 3600}h"
    return f"{total // 3600:02d}:{(total % 3600) // 60:02d}:{total % 60:02d}"


def condition(obj, ctype):
    for c in (obj.get("status", {}) or {}).get("conditions", []) or []:
        if c.get("type") == ctype:
            return c
    return {}


xrs = json.load(open("/tmp/xr-status.json"))["items"]
mrs = json.load(open("/tmp/mr-status.json"))["items"]

# Index managed resources by the XR that owns them (via owner references).
owned = {}
for mr in mrs:
    for ref in mr["metadata"].get("ownerReferences", []) or []:
        owned.setdefault(ref.get("uid"), []).append(mr)

rows = []
for xr in xrs:
    meta = xr["metadata"]
    ident = f"{meta.get('namespace', '-')}/{meta['name']}"
    ready = condition(xr, "Ready")
    status = ready.get("status", "?")

    # Duration in the CURRENT state -- the column that distinguishes a healthy
    # creation from a stuck resource. Readiness alone cannot.
    since = ready.get("lastTransitionTime") or meta["creationTimestamp"]
    duration = now - parse(since)

    blocked_by, error = "-", "-"
    if status != "True":
        # Find the first child that is not healthy: that is what to go and look at.
        for mr in owned.get(meta.get("uid"), []):
            mr_ready = condition(mr, "Ready")
            mr_synced = condition(mr, "Synced")
            if mr_ready.get("status") != "True" or mr_synced.get("status") != "True":
                blocked_by = f"{mr['kind']}/{mr['metadata']['name']}"
                msg = mr_synced.get("message") or mr_ready.get("message") or ""
                if msg:
                    error = msg.replace("\n", " ")[:60]
                break
        else:
            error = (ready.get("message") or ready.get("reason") or "-")[:60]

    rows.append((duration, ident, status, hhmmss(duration), blocked_by, error))

# Worst first: longest time in a non-ready state at the top.
rows.sort(key=lambda r: (r[2] == "True", -r[0].total_seconds()))

print(f"{'XR':<34}{'READY':<7}{'FOR':<11}{'BLOCKED BY':<30}ERROR")
print("-" * 130)
for _, ident, status, dur, blocked, err in rows:
    print(f"{ident:<34}{status:<7}{dur:<11}{blocked:<30}{err}")

stuck = [r for r in rows if r[2] != "True" and r[0].total_seconds() > 3600]
if stuck:
    print()
    print(f"⚠️  {len(stuck)} XR(s) have been not-Ready for over an hour.")
    print("   That is past every normal provisioning time -- these are stuck,")
    print("   not slow. Start with the BLOCKED BY resource.")
PY
