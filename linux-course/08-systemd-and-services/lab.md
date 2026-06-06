# Lab 08 — systemd in Practice

**You'll:** manage a real service, read the journal, switch targets, and create your own
unit. ⏱️ ~55 min. In your VM.

---

## Part A — Manage an existing service (ssh)
```bash
systemctl status ssh
systemctl is-enabled ssh; systemctl is-active ssh
sudo systemctl restart ssh
journalctl -u ssh -n 20 --no-pager      # last 20 log lines for ssh
systemctl list-units --type=service --state=running | head
systemctl --failed                       # hopefully none
```

## Part B — enable vs start
```bash
sudo apt install -y cron 2>/dev/null
sudo systemctl disable --now cron        # stop now AND don't start at boot
systemctl is-active cron; systemctl is-enabled cron     # inactive; disabled
sudo systemctl enable --now cron         # start now AND at boot
systemctl is-active cron; systemctl is-enabled cron     # active; enabled
```
✅ Internalize: **enable** = at boot, **start** = now, **`--now`** = both.

## Part C — Read the journal
```bash
journalctl -b | tail                     # this boot
journalctl -p err -b --no-pager | head   # errors this boot
journalctl --since "5 min ago" --no-pager | tail
journalctl -u ssh -f                      # follow (open another shell, ssh in, watch). Ctrl+C
```

## Part D — Create your own service
```bash
sudo cp code/hello.sh /usr/local/bin/hello.sh    # (copy from this module's code/)
sudo chmod +x /usr/local/bin/hello.sh
sudo cp code/hello.service /etc/systemd/system/hello.service
sudo systemctl daemon-reload             # always after adding/editing unit files
sudo systemctl enable --now hello
systemctl status hello
journalctl -u hello -f                    # watch the heartbeat every 5s. Ctrl+C
```
✅ Your service runs, logs to the journal, and is set to start at boot.

## Part E — Prove auto-restart
```bash
# Find and kill the script; Restart=on-failure should bring it back:
PID=$(systemctl show -p MainPID --value hello)
sudo kill -9 "$PID"
sleep 3
systemctl status hello | grep -E 'Active|Main PID'    # running again, new PID
```
✅ systemd restarted it (per `Restart=on-failure`). That's why services beat `nohup`.

## Part F — Targets
```bash
systemctl get-default                     # graphical or multi-user
# (Don't permanently change a server you rely on graphically; just inspect.)
systemctl list-units --type=target
```

## Cleanup
```bash
sudo systemctl disable --now hello
sudo rm /etc/systemd/system/hello.service /usr/local/bin/hello.sh
sudo systemctl daemon-reload
```

## What you learned
- `systemctl` start/stop/restart/enable/`--now`; enable vs start; `daemon-reload`.
- `journalctl` by unit/boot/priority/time; following logs.
- Authoring a `.service` unit with `ExecStart`/`Restart`/`User`/`WantedBy`.
- Auto-restart — why services are the right way to run long-lived programs.

➡️ **[challenge.md](./challenge.md)** then [Module 09](../09-storage-filesystems/).
