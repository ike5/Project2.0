# Module 11 — Scheduling, Logging & Backups

**Goal:** automate recurring work (cron, systemd timers, at), manage logs (rsyslog,
journald, logrotate), and take reliable backups with `tar`/`rsync`. ⏱️ ~2 h ·
🎯 Prereq: 00–10.

---

## 1. cron — time-based jobs

Each user has a **crontab**; the system has `/etc/crontab` and `/etc/cron.d/`.
```bash
crontab -e        # edit YOUR crontab
crontab -l        # list
sudo crontab -e   # root's crontab
```
The five time fields + command:
```
# ┌── minute (0-59)
# │ ┌── hour (0-23)
# │ │ ┌── day of month (1-31)
# │ │ │ ┌── month (1-12)
# │ │ │ │ ┌── day of week (0-7, 0/7=Sun)
# * * * * *  command
0 2 * * *      /usr/local/bin/backup.sh        # daily at 02:00
*/15 * * * *   /usr/local/bin/check.sh          # every 15 minutes
0 9 * * 1-5    cmd                               # 09:00 on weekdays
@reboot        /usr/local/bin/startup.sh         # at boot
```
Convenience: `@daily @hourly @weekly @reboot`. Drop scripts in `/etc/cron.daily/` etc.
for run-parts. **anacron** runs missed jobs on machines that aren't always on.

## 2. systemd timers (the modern alternative)

A **`.timer`** activates a matching **`.service`**. More flexible than cron (logging via
journald, dependencies, randomized delays, "catch up" with `Persistent=`).
```ini
# /etc/systemd/system/backup.timer
[Unit]
Description=Daily backup
[Timer]
OnCalendar=*-*-* 02:00:00      # daily at 02:00
Persistent=true                 # run if the machine was off at the scheduled time
[Install]
WantedBy=timers.target
```
```bash
sudo systemctl enable --now backup.timer
systemctl list-timers           # next run times
```

## 3. at — one-off jobs

```bash
echo 'systemctl restart nginx' | at 03:00      # once, at 3am
at now + 1 hour                                  # interactive
atq; atrm <id>                                   # list / remove
```

## 4. Logging

Two systems coexist:
- **journald** (binary, queried with `journalctl` — Module 08).
- **rsyslog** (text files in `/var/log/`):
  - Debian: `/var/log/syslog`, `/var/log/auth.log`
  - RHEL: `/var/log/messages`, `/var/log/secure`
  - service-specific: `/var/log/nginx/`, `/var/log/apt/`, …
```bash
sudo tail -f /var/log/syslog
logger "hello from the CLI"        # write a message into syslog
grep -i 'fail' /var/log/auth.log   # failed logins
```

## 5. logrotate — keep logs from eating the disk

```bash
cat /etc/logrotate.conf
ls /etc/logrotate.d/               # per-app rotation policies
```
A policy (`/etc/logrotate.d/myapp`):
```
/var/log/myapp/*.log {
    daily
    rotate 14            # keep 14 days
    compress
    missingok
    notifempty
    create 0640 root adm
}
```
```bash
sudo logrotate -f /etc/logrotate.d/myapp    # force a rotation to test
```

## 6. Backups with tar & rsync

```bash
# tar archive (snapshot)
tar -czf /backup/etc-$(date +%F).tgz /etc           # create gzip archive
tar -tzf /backup/etc-2024-06-01.tgz | head          # list contents
tar -xzf archive.tgz -C /restore                     # extract somewhere

# rsync (incremental, efficient mirroring — trailing slash matters!)
rsync -avh /home/ /backup/home/                      # copy contents of /home into /backup/home
rsync -avh --delete /home/ /backup/home/             # mirror (remove extras in dest)
rsync -avz -e ssh /home/ user@host:/backup/home/     # over SSH to another machine
rsync -avhn --delete /home/ /backup/home/            # -n = DRY RUN (preview!)
```
> `src/` (trailing slash) copies the **contents**; `src` (no slash) copies the **directory**.
> Always dry-run (`-n`) a `--delete` first.

---

## Do the lab
Schedule a job with cron and a systemd timer, write to syslog, rotate a log, and back up
with tar + rsync. 👉 **[lab.md](./lab.md)**

Then: 👉 **[challenge.md](./challenge.md)**

## Code
[`code/backup.sh`](./code/backup.sh), [`code/report.timer`](./code/report.timer),
[`code/report.service`](./code/report.service).

## Key terms
crontab (5 fields/`@daily`/`@reboot`) · anacron · systemd `.timer`/`OnCalendar`/
`Persistent` · `at`/`atq` · journald vs rsyslog · `/var/log/*` · `logger` · logrotate ·
`tar -czf`/`-xzf`/`-tzf` · `rsync -avh`/`--delete`/`-n`/trailing-slash

**Next →** [Module 12: Shell Scripting](../12-shell-scripting/)
