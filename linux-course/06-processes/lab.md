# Lab 06 — Inspect & Control Processes

**You'll:** view the process tree, run background jobs, send signals, and renice.
⏱️ ~45 min. In your VM.

---

## Part A — Look around
```bash
ps aux | head
ps -ef --forest | head -30        # see the tree from systemd (PID 1) down
pstree -p | head
echo "my shell PID is $$"
uptime; free -h
```
✅ Note PID 1 is `systemd`, and your shell descends from it.

## Part B — Background jobs
```bash
sleep 600 &                       # [1] 12345
sleep 800 &                       # [2] 12346
jobs                              # two running jobs
fg %1                             # bring job 1 forward...
Ctrl+Z                            #   ...then suspend it ([1]+ Stopped)
jobs                              # job 1 is Stopped
bg %1                             # resume in background
jobs                              # both running again
```

## Part C — Find and signal
```bash
pgrep -a sleep                    # PIDs + command lines of our sleeps
kill %2                           # polite stop of job 2 (SIGTERM)
jobs                              # job 2 terminated
PID=$(pgrep -f 'sleep 600' | head -1)
kill -TERM "$PID"                 # terminate by PID
pgrep -a sleep || echo "all sleeps gone"
```
✅ `SIGTERM` cleanly ends them. Try `kill -9` only when TERM doesn't work.

## Part D — A process that ignores TERM
```bash
# Start something that traps SIGTERM to show why -9 exists:
( trap '' TERM; echo "stubborn PID $$ running"; sleep 300 ) &
STUB=$!
kill -TERM "$STUB"; sleep 1
kill -0 "$STUB" 2>/dev/null && echo "still alive (ignored TERM)"
kill -9 "$STUB"                   # force kill
kill -0 "$STUB" 2>/dev/null || echo "now dead (SIGKILL)"
```
✅ `SIGTERM` can be caught/ignored; `SIGKILL` (-9) cannot — but it skips cleanup.

## Part E — Priorities
```bash
nice -n 15 sleep 300 &            # start low-priority
NP=$!
ps -o pid,ni,cmd -p "$NP"         # NI = 15
sudo renice -n 5 -p "$NP"         # change it
ps -o pid,ni,cmd -p "$NP"         # NI = 5
kill "$NP"
```

## Part F — Live monitor + /proc
```bash
top        # press M then P to re-sort; press q to quit
ls -l /proc/$$/fd          # this shell's open files (0,1,2 = stdin/out/err)
cat /proc/loadavg          # raw load averages
cat /proc/$$/status | head # status of your shell process
```

## Part G — Survive logout
```bash
nohup bash -c 'for i in $(seq 5); do echo "tick $i"; sleep 1; done' > ~/ticks.log 2>&1 &
# (it keeps running even if you disconnect)
sleep 6; cat ~/ticks.log
```

## What you learned
- Read `ps`/`pstree`/`top`; interpret load average and memory.
- Job control: `&`, `jobs`, `fg`/`bg`, `Ctrl+Z`.
- Signals: TERM vs KILL vs HUP; `kill`/`pkill`/`pgrep`.
- `nice`/`renice`; `/proc/<pid>`; `nohup` for logout-proof jobs.

➡️ **[challenge.md](./challenge.md)** then [Module 07](../07-package-management/).
