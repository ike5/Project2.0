# Challenge 01 — Reference Solution

### 1. Self-serve help
- Sort by modification time: **`-t`**. Append `/` to dirs (type indicators): **`-F`**.
- Newest-first listing of `/etc` with type indicators:
  ```bash
  ls -ltF /etc          # -l long, -t time-sorted (newest first), -F indicators
  ```
  (Found via `man ls` → `/sort` or `/modification`, and `/-F`.)

### 2. PATH detective
```bash
which python3            # the one that runs (first in PATH)
type -a python3          # every python3 in PATH, in order
type ll                  # 'll is aliased to ...' (alias), or builtin/file
```

### 3. Quoting puzzle
```bash
x="a b"
echo $x        # a b        (two words, but spaces collapse to one on display)
echo "$x"      # a b        (preserved as one argument)
echo '$x'      # $x         (literal)
touch "$x"; ls # ONE file named 'a b'
```
> Unquoted `$x` is split into two arguments (`a`, `b`); quoted, it stays one. Always quote
> variables that may contain spaces.

### 4. Conditional chain
```bash
mkdir -p /tmp/proj/logs && echo ready || echo failed
```

### 5. History recall
```bash
!man        # re-run the last command beginning with 'man'
ls -l !$    # reuse the previous command's last argument
```
