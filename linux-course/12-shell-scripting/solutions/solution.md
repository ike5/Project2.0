# Challenge 12 — Reference Solution

Runnable scripts in this folder: [`backup-rotate.sh`](./backup-rotate.sh),
[`wait-for.sh`](./wait-for.sh), [`ensure-user.sh`](./ensure-user.sh). Task 2 below.

### 2. logsummary.sh
```bash
#!/usr/bin/env bash
set -euo pipefail
log="${1:?usage: $0 <access-log>}"
[[ -r "$log" ]] || { echo "error: cannot read '$log'" >&2; exit 1; }

total=$(wc -l < "$log")
errors=$(awk '$9 ~ /^[45]/' "$log" | wc -l)
echo "total requests : $total"
echo "errors (4xx/5xx): $errors"
echo "top 3 IPs:"
awk '{print $1}' "$log" | sort | uniq -c | sort -rn | head -3
```

### 5. Quality pass (shellcheck)
```bash
sudo apt install -y shellcheck
shellcheck *.sh
```
Common fixes shellcheck flags:
- **SC2086** unquoted variable → quote it: `"$var"`.
- **SC2046** unquoted command substitution → quote it.
- **SC2164** `cd` without `|| exit` → `cd "$dir" || exit 1`.

### Idempotence (task 4) — the key idea
`ensure-user.sh` checks state **before** acting (`getent group`, `id`) and only changes
what's missing. Running it twice produces no errors and no second change — the same
principle Ansible is built on (you'll see this again in the **Ansible course**).

### Notes
- All scripts begin with `set -euo pipefail` and validate required arguments with
  `${1:?usage...}` so they fail fast with a helpful message.
- `wait-for.sh` mirrors what real deployment/CI scripts do before talking to a service.
