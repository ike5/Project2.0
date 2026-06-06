# Module 06 — Processes & Job Control

**Goal:** see what's running, control it, send signals, and manage priorities and
background jobs. ⏱️ ~2 h · 🎯 Prereq: 00–05.

---

## 1. What a process is

A **process** is a running program, identified by a **PID**. Processes form a tree: each
has a **parent** (PPID); **PID 1** is `systemd` (the ancestor of all). Each process has an
owner, a state, memory, and open files.

## 2. Listing processes

```bash
ps aux                 # every process (BSD style): USER PID %CPU %MEM ... COMMAND
ps -ef                 # every process (System V style): UID PID PPID ... CMD
ps -ef --forest        # as a tree (see parent/child)
ps aux | grep sshd     # filter (or better: pgrep)
pgrep -a sshd          # PIDs + command lines matching 'sshd'
pstree -p              # the whole tree with PIDs
```
Useful columns: **STAT** (R running, S sleeping, D uninterruptible, Z zombie, T stopped),
**TTY**, **TIME**, **%CPU/%MEM**.

## 3. Live monitoring

```bash
top                    # live; press: M (sort mem), P (cpu), k (kill), q (quit)
htop                   # friendlier (sudo apt install -y htop): F6 sort, F9 kill, arrows
uptime                 # load averages (1/5/15 min)
free -h                # memory usage
vmstat 1               # system stats each second
```
**Load average** ≈ average number of processes wanting CPU. On an N-CPU box, ~N is "fully
busy"; well above N means saturation.

## 4. Signals & killing

A **signal** is an async message to a process:
```bash
kill 1234              # send SIGTERM (15): polite "please stop, clean up"
kill -9 1234           # SIGKILL (9): force-kill, no cleanup (last resort)
kill -HUP 1234         # SIGHUP (1): often "reload config"
kill -l                # list all signals
pkill -f "python app"  # kill by command-line pattern
killall nginx          # kill by exact process name
```
Order of escalation: **TERM → wait → KILL**. Prefer `systemctl stop` for services
(Module 08).

## 5. Job control (foreground/background)

```bash
sleep 300 &            # run in the background; prints [1] <PID>
jobs                   # list this shell's jobs
fg %1                  # bring job 1 to the foreground
Ctrl+Z                 # suspend the foreground job (stopped)
bg %1                  # resume it in the background
kill %1                # kill job 1
nohup long_task &      # keep running after you log out (ignores SIGHUP)
disown -h %1           # detach a job from the shell
```
For persistent sessions across disconnects, use **tmux** or **screen**.

## 6. Priorities (nice / renice)

Niceness ranges **-20 (highest priority)** to **19 (lowest)**; default 0. Only root can
raise priority (negative).
```bash
nice -n 10 some_batch_job        # start with lower priority
renice -n 5 -p 1234              # change a running process
ps -o pid,ni,cmd -p 1234         # see its niceness
```

## 7. /proc — the process filesystem

Each process appears under `/proc/<PID>`:
```bash
cat /proc/1/comm           # name of PID 1 (systemd)
ls -l /proc/$$/fd          # open file descriptors of THIS shell ($$ = its PID)
cat /proc/cpuinfo /proc/meminfo | head
```

---

## Do the lab
Start background jobs, inspect the tree, send signals, and adjust priority.
👉 **[lab.md](./lab.md)**

Then: 👉 **[challenge.md](./challenge.md)**

## Key terms
process/PID/PPID · `ps aux`/`ps -ef`/`pstree`/`pgrep` · `top`/`htop` · load average ·
signal (TERM/KILL/HUP) · `kill`/`pkill`/`killall` · job control (`&`/`fg`/`bg`/`jobs`/
`Ctrl+Z`) · `nohup` · `nice`/`renice` · `/proc`

**Next →** [Module 07: Package Management](../07-package-management/)
