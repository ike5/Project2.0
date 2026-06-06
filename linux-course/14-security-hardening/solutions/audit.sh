#!/usr/bin/env bash
# Challenge 14, task 1: a small security audit. Run with sudo for the shadow/setuid checks.
set -uo pipefail

pass() { printf "  [PASS] %s\n" "$1"; }
warn() { printf "  [WARN] %s\n" "$1"; }

echo "== UID 0 accounts (only root expected) =="
extra_root=$(awk -F: '($3==0)&&($1!="root"){print $1}' /etc/passwd)
[[ -z "$extra_root" ]] && pass "only root is UID 0" || warn "extra UID-0 accounts: $extra_root"

echo "== Empty passwords =="
if [[ -r /etc/shadow ]]; then
  empties=$(awk -F: '($2==""){print $1}' /etc/shadow)
  [[ -z "$empties" ]] && pass "no empty-password accounts" || warn "empty passwords: $empties"
else
  warn "cannot read /etc/shadow (run with sudo)"
fi

echo "== setuid binaries =="
count=$(find / -perm -4000 -type f 2>/dev/null | wc -l)
echo "  found $count setuid binaries (review them):"
find / -perm -4000 -type f 2>/dev/null | sed 's/^/    /'

echo "== world-writable files under /etc =="
ww=$(find /etc -perm -2 -type f 2>/dev/null)
[[ -z "$ww" ]] && pass "no world-writable files in /etc" || warn "world-writable: $ww"

echo "audit complete"
