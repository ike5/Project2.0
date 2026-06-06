# Challenge 08 — systemd Mastery

Solutions in [`solutions/`](./solutions/). Try first.

## Tasks
1. **A web one-liner service.** Write a unit `pyweb.service` that serves the current
   directory over HTTP on port 8000 using `python3 -m http.server 8000`, running as
   `nobody`, restarting on failure. Enable it and confirm with `curl localhost:8000`.

2. **Ordering & deps.** Make `pyweb` start only **after** the network is up, and explain
   the difference between `After=` and `Requires=`.

3. **Find boot offenders.** Show the command to list which services took the longest to
   start at boot (hint: `systemd-analyze`). What does `systemd-analyze blame` tell you?

4. **Override, don't edit.** You want to change a packaged unit's `Restart=` without
   editing the vendor file. Use `systemctl edit <unit>` to create a drop-in override and
   explain where it's stored and why this is preferred.

5. **Logs investigation.** A service keeps crashing. Write the `journalctl` command to see
   only *its* errors since the last boot, following live.

## Success criteria
- [ ] `pyweb.service` serves HTTP and survives a kill (restarts).
- [ ] `After=network-online.target` (with the right Wants) set; After vs Requires explained.
- [ ] `systemd-analyze blame` / `critical-chain` used correctly.
- [ ] A drop-in override created via `systemctl edit`, stored under
      `/etc/systemd/system/<unit>.d/override.conf`.
- [ ] Correct `journalctl -u <unit> -b -p err -f`.
