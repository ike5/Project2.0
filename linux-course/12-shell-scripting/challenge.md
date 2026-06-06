# Challenge 12 — Build a Tool

Solutions in [`solutions/`](./solutions/). Try first. Start every script with
`set -euo pipefail`.

## Tasks
1. **`backup-rotate.sh`.** Write a script that takes `<source-dir> <dest-dir> [keep]`,
   creates a timestamped `.tgz` of the source in the dest, and keeps only the newest
   `keep` (default 5) archives. Validate that the source exists and is a directory;
   print a usage message otherwise.

2. **`logsummary.sh`.** Given a web log file as `$1`, print: total requests, count of
   errors (status 4xx/5xx), and the top 3 IPs — using your Module 03 pipelines inside the
   script. Exit non-zero if the file doesn't exist.

3. **`wait-for.sh`.** Write `wait-for.sh <host> <port> [timeout]` that loops until the
   TCP port is reachable (`nc -z`) or the timeout (default 30s) elapses, printing progress
   and exiting 0 on success, 1 on timeout. (This is exactly what real deploy scripts do.)

4. **Idempotent setup.** Write `ensure-user.sh <username>` that creates the user **only
   if it doesn't already exist** (check `id`), adds them to a `devs` group (creating the
   group if needed), and is safe to run repeatedly with no errors or changes the second
   time.

5. **Quality pass.** Install `shellcheck` (`sudo apt install -y shellcheck`) and run it on
   all your scripts; fix at least the warnings about unquoted variables.

## Success criteria
- [ ] `backup-rotate.sh` validates input, archives, and rotates to `keep`.
- [ ] `logsummary.sh` reports totals/errors/top-IPs and handles a missing file.
- [ ] `wait-for.sh` polls a port with a timeout and correct exit codes.
- [ ] `ensure-user.sh` is **idempotent** (no error/change on re-run).
- [ ] `shellcheck` passes (or only intentional warnings remain).
