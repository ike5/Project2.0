# Challenge 06 — Reference Solution

### 1. Top consumers
```bash
ps aux --sort=-%mem | head -6          # header + top 5 by memory
ps aux --sort=-%cpu | head -6          # by CPU
# Portable alternative:
ps -eo pid,comm,%mem --sort=-%mem | head -6
```

### 2. Graceful then forceful
```bash
sleep 1000 &
PID=$!
kill -TERM "$PID"          # polite stop
kill -0 "$PID" 2>/dev/null || echo "stopped"
```
> Use **`SIGKILL` (-9)** only when a process ignores/can't handle `SIGTERM` (hung, or
> traps TERM). The cost: the process is killed instantly with **no chance to flush
> buffers, save state, or release locks/temp files** — risking data loss or stale locks.

### 3. Kill by pattern, safely
```bash
pgrep -af 'python worker\.py'      # PREVIEW: exactly which PIDs + cmdlines match
pkill -f 'python worker\.py'       # then kill only those
```
> `-f` matches the full command line, so `worker.py` pythons are targeted without hitting
> unrelated python processes. Always preview with `pgrep -af` first.

### 4. Priorities
```bash
nice -n 19 sh -c 'while :; do :; done' &     # lowest priority CPU loop
PID=$!
ps -o pid,ni,cmd -p "$PID"                     # NI = 19
sudo renice -n -5 -p "$PID"                    # root can raise priority
ps -o pid,ni,cmd -p "$PID"                     # NI = -5
kill "$PID"
```
> Normal users may only **lower** priority (increase niceness). Allowing arbitrary users
> to set negative nice would let them starve everyone else's processes of CPU — so
> raising priority requires root.

### 5. Zombies & orphans
- **Zombie** (`Z`): a process that has **exited** but whose parent hasn't yet read its
  exit status (`wait()`), so its entry lingers in the process table. It uses no resources
  but the slot; fixed when the parent reaps it (or the parent dies).
- **Orphan**: a process whose **parent died** while it's still running.
- Orphans are **adopted by PID 1** (`systemd`/`init`), which reaps them when they exit —
  preventing permanent zombies.
