# Challenge 03 — Reference Solution

### 1. Error rate
```bash
awk '{total++} $9 ~ /^[45]/ {err++} END{printf "%d/%d errors (%.1f%%)\n", err, total, 100*err/total}' access.log
# -> 6/15 errors (40.0%)
```

### 2. Unique paths by count
```bash
awk '{print $7}' access.log | sort | uniq -c | sort -rn
# /index.html (4), /style.css (2), /app.js (2), /api/login (2), /api/data (2), ...
```

### 3. Bash login shells
```bash
awk -F: '$7 ~ /bash$/ {print $1}' /etc/passwd
# or: grep -E '/bin/bash$' /etc/passwd | cut -d: -f1
```

### 4. Active sshd_config lines + count
```bash
grep -vE '^\s*(#|$)' /etc/ssh/sshd_config            # the active lines
grep -vcE '^\s*(#|$)' /etc/ssh/sshd_config           # just the count
```

### 5. Top-3 error source IPs (one pipeline)
```bash
awk '$9 ~ /^[45]/ {print $1}' access.log | sort | uniq -c | sort -rn | head -3
#   3 10.0.0.9
#   2 10.0.0.5
#   1 10.0.0.7
```

### 6. Stretch — split streams & order
```bash
cmd > out.txt 2> err.txt          # stdout to out.txt, stderr to err.txt
```
> **Order matters** because `2>&1` means "make fd 2 point wherever fd 1 points *right
> now*."
> - `cmd > file 2>&1` → fd1 set to `file`, then fd2 copied to fd1 → **both** go to `file`.
> - `cmd 2>&1 > file` → fd2 copied to fd1 (the terminal) first, *then* fd1 changed to
>   `file` → stderr still goes to the **terminal**, stdout to `file`.
