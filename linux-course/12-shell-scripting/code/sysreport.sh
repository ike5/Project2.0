#!/usr/bin/env bash
#
# sysreport.sh — a small, robust system report.
# Demonstrates: safety preamble, args, functions, conditionals, loops, exit codes.
#
# Usage: sysreport.sh [-v] [service ...]
#   -v          verbose
#   service ... optional systemd services to check (default: ssh cron)
#
set -euo pipefail

verbose=false
# --- parse options ---
while getopts ":vh" opt; do
  case "$opt" in
    v) verbose=true ;;
    h) echo "usage: $0 [-v] [service ...]"; exit 0 ;;
    *) echo "unknown option" >&2; exit 1 ;;
  esac
done
shift $(( OPTIND - 1 ))

# Remaining args are services to check; default if none given.
services=("$@")
if [[ ${#services[@]} -eq 0 ]]; then
  services=(ssh cron)
fi

log()  { echo "[$(date +%T)] $*"; }
vlog() { $verbose && log "$*" || true; }

section() { printf '\n== %s ==\n' "$1"; }

# --- report ---
section "Host"
echo "hostname : $(hostname)"
echo "kernel   : $(uname -r)"
echo "uptime   : $(uptime -p 2>/dev/null || uptime)"

section "Resources"
echo "load     : $(cut -d' ' -f1-3 /proc/loadavg)"
echo "memory   : $(free -h | awk '/^Mem:/ {print $3 " used / " $2 " total"}')"
# Disk: warn if any filesystem is over 80% full.
echo "disk     :"
df -hP | awk 'NR>1 {gsub(/%/,"",$5); flag=($5+0>80)?" <-- HIGH":""; printf "  %-22s %s%s\n", $6, $5"%", flag}'

section "Services"
for svc in "${services[@]}"; do
  if systemctl is-active --quiet "$svc"; then
    echo "  $svc: active"
  else
    echo "  $svc: NOT active"
  fi
  vlog "checked $svc"
done

section "Recent auth failures"
# Count failed sudo/ssh attempts if the log is readable.
if [[ -r /var/log/auth.log ]]; then
  fails=$(grep -c -i 'authentication failure\|failed password' /var/log/auth.log || true)
  echo "  auth failures in auth.log: ${fails:-0}"
else
  echo "  (auth.log not readable; run with sudo for this section)"
fi

log "report complete"
