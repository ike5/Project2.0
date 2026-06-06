# Challenge 03 — Text-Fu

Use [`code/access.log`](./code/access.log) and system files. Solutions in
[`solutions/`](./solutions/). Try first.

## Tasks
1. **Error rate.** From `access.log`, compute how many requests were errors (status 4xx
   or 5xx) and the **percentage** of all requests. (Hint: `awk` with two counters and an
   `END` block.)

2. **Unique paths.** List each distinct requested path (field 7) with a count, sorted by
   most-requested.

3. **Login shells.** From `/etc/passwd`, print only the usernames whose login shell is
   `/bin/bash` (or `bash`), one per line.

4. **Config diff.** Produce the active (non-comment, non-blank) lines of
   `/etc/ssh/sshd_config`, then count how many there are.

5. **One pipeline.** In a single pipeline, find the top 3 source IPs that caused **error**
   responses (4xx/5xx) in the log.

6. **Stretch:** Redirect a command's stdout to one file and stderr to a different file in
   the same invocation, and explain the order-sensitivity of `> file 2>&1` vs `2>&1 > file`.

## Success criteria
- [ ] Error count and percentage computed in one `awk`.
- [ ] Per-path counts, sorted.
- [ ] Bash users extracted from `/etc/passwd`.
- [ ] Active sshd_config lines + their count.
- [ ] Top-3 error IPs in one pipeline.
