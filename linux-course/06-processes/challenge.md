# Challenge 06 — Process Control

Solutions in [`solutions/`](./solutions/). Try first.

## Tasks
1. **Find the hog.** Show the single command that lists the top 5 processes by **memory**
   usage, and another for top 5 by **CPU** (using `ps` + `sort`, not just `top`).

2. **Graceful then forceful.** Start a background `sleep 1000`. Try to stop it with
   `SIGTERM`; verify it's gone. Then describe (one sentence) when you'd need `SIGKILL`
   instead and what you lose by using it.

3. **Kill by pattern, safely.** You have several `python worker.py` processes. Write the
   command to kill *only* those (not other python processes), and the command you'd run
   **first** to preview exactly which PIDs would be affected.

4. **Priorities.** Launch a CPU-bound job at the **lowest** priority, confirm its
   niceness, then (as root) raise its priority to `-5`. Why can't a normal user set a
   negative nice value?

5. **Zombies & orphans (short answer).** What is a **zombie** process, what is an
   **orphan**, and which process "adopts" orphans?

## Success criteria
- [ ] Correct `ps ... | sort` one-liners for top mem/cpu.
- [ ] Demonstrated TERM stop and can explain when KILL is needed.
- [ ] `pgrep -f`/`pkill -f 'python worker.py'` with a preview step.
- [ ] Low-priority launch + root renice to -5, with the privilege explanation.
- [ ] Correct zombie/orphan/reaper (PID 1) explanation.
