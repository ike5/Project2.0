# Challenge 11 — Reference Solution

### 1. Cron expressions
```
30 18 * * 1-5     # (a) weekdays 6:30 PM
*/5 * * * *       # (b) every 5 minutes
0  0  1 * *       # (c) 1st of the month, midnight
15 3  * * 0       # (d) Sundays 03:15  (0 or 7 = Sunday)
```

### 2. cron vs timer
> **Timer advantages:** (1) output/errors are captured in the **journal** automatically
> (cron emails or silently drops output); (2) **`Persistent=true`** runs missed jobs after
> downtime, plus dependencies/ordering and `RandomizedDelaySec`. **Cron advantage:**
> simpler and ubiquitous — a one-line `crontab -e` with no unit files, available even
> without systemd.

### 3. Daily backup timer
`/etc/systemd/system/backup.service`:
```ini
[Unit]
Description=Daily data backup
[Service]
Type=oneshot
ExecStart=/usr/local/bin/backup.sh /home/ubuntu/data /home/ubuntu/backups
```
`/etc/systemd/system/backup.timer`:
```ini
[Unit]
Description=Run backup daily at 02:00
[Timer]
OnCalendar=*-*-* 02:00:00
Persistent=true            # catch up if the box was off at 02:00
[Install]
WantedBy=timers.target
```
```bash
sudo systemctl daemon-reload && sudo systemctl enable --now backup.timer
systemctl list-timers backup.timer
```

### 4. rsync trailing slash + mirror
> - `rsync -a /src /dst` → copies the **directory** → result is `/dst/src/...`.
> - `rsync -a /src/ /dst` → copies the **contents** of `/src` → result is `/dst/...`.
```bash
rsync -avhn --delete /src/ /dst/      # PREVIEW the mirror (dry run)
rsync -avh  --delete /src/ /dst/      # mirror: also removes from /dst anything gone from /src
```

### 5. Retention pipeline
```bash
ls -1t "$DEST"/backup-*.tgz | tail -n +8 | xargs -r rm -f
```
- `ls -1t` — list backups, **one per line**, **newest first**.
- `tail -n +8` — output **from line 8 onward** (i.e. skip the 7 newest → everything older).
- `xargs -r rm -f` — pass those filenames as arguments to `rm -f`. **`-r`** (`--no-run-if-
  empty`) means: if there are 7 or fewer backups (empty input), **don't run `rm` at all**,
  avoiding `rm` with no arguments.
