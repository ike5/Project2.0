# Lab 11 — Schedule, Log & Back Up

**You'll:** run jobs via cron and a systemd timer, write to syslog, rotate a log, and
back up with tar + rsync. ⏱️ ~50 min. In your VM.

---

## Part A — A cron job
```bash
mkdir -p ~/cronlab
crontab -e
# add this line (writes the date every minute), save & quit:
#   * * * * * date >> $HOME/cronlab/tick.log 2>&1
crontab -l                       # confirm it's there
sleep 65; cat ~/cronlab/tick.log # one or two timestamps appear
# remove it:
crontab -r
```
✅ cron ran your command on schedule and appended output.

## Part B — The backup script
```bash
install -m 0755 code/backup.sh /usr/local/bin/backup.sh   # from this module's code/
mkdir -p ~/data && echo "important" > ~/data/file.txt
/usr/local/bin/backup.sh ~/data ~/backups
ls -lh ~/backups                 # backup-<timestamp>.tgz
journalctl -t backup -n 3 --no-pager   # the logger line we wrote
tar -tzf ~/backups/backup-*.tgz | head # inspect contents
```
✅ A timestamped archive, a syslog entry (via `logger -t backup`), and retention built in.

## Part C — A systemd timer
```bash
sudo cp code/report.service /etc/systemd/system/report.service
sudo cp code/report.timer   /etc/systemd/system/report.timer
sudo systemctl daemon-reload
sudo systemctl enable --now report.timer
systemctl list-timers report.timer --no-pager     # NEXT/LAST run times
# trigger once immediately to see output:
sudo systemctl start report.service
journalctl -u report.service -n 3 --no-pager       # the report line
```
✅ The timer schedules the service; output goes to the journal (better than cron's email).

## Part D — Logging
```bash
logger "hello from the lab"
journalctl -n 5 --no-pager | grep hello            # it's in the journal
grep hello /var/log/syslog | tail                  # and the text log
sudo tail -n 5 /var/log/auth.log                   # auth events (sudo/ssh)
```

## Part E — Rotate a log
```bash
sudo mkdir -p /var/log/myapp
for i in $(seq 1 100); do echo "line $i"; done | sudo tee /var/log/myapp/app.log >/dev/null
sudo tee /etc/logrotate.d/myapp >/dev/null <<'EOF'
/var/log/myapp/*.log {
    daily
    rotate 3
    compress
    missingok
    notifempty
}
EOF
sudo logrotate -f /etc/logrotate.d/myapp           # force it
ls /var/log/myapp/                                  # app.log + app.log.1.gz
```
✅ logrotate rotated and compressed the log per your policy.

## Part F — rsync backup (with a safe dry run)
```bash
mkdir -p ~/mirror
rsync -avhn --delete ~/data/ ~/mirror/             # DRY RUN first (-n): preview
rsync -avh  --delete ~/data/ ~/mirror/             # do it
echo "new" > ~/data/another.txt
rsync -avh ~/data/ ~/mirror/                        # only the new file transfers (incremental)
ls ~/mirror
```
✅ `rsync` mirrored efficiently; the dry run let you preview before `--delete`.

## Cleanup
```bash
sudo systemctl disable --now report.timer
sudo rm /etc/systemd/system/report.{service,timer} /etc/logrotate.d/myapp /usr/local/bin/backup.sh
sudo rm -rf /var/log/myapp; rm -rf ~/cronlab ~/data ~/backups ~/mirror
sudo systemctl daemon-reload
```

## What you learned
- cron (per-user) and systemd timers (`OnCalendar`/`OnUnitActiveSec`, journald logging).
- `logger`, journald vs `/var/log`, and logrotate policies.
- tar snapshots and `rsync` incremental/mirroring backups (with dry-run safety).

➡️ **[challenge.md](./challenge.md)** then [Module 12](../12-shell-scripting/).
