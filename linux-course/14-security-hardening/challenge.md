# Challenge 14 — Lock It Down

Solutions in [`solutions/`](./solutions/). Try first.

## Tasks
1. **Audit script.** Write `audit.sh` that reports: any UID-0 account besides root, any
   account with an empty password field, all setuid binaries, and any world-writable file
   under `/etc`. It should print a clear PASS/WARN per check.

2. **Scoped sudo.** Grant a `ci` user the ability to run **only** `systemctl restart
   myapp` (and nothing else) without a password, safely. Show the `visudo` drop-in and how
   you'd verify it with `sudo -l -U ci`.

3. **Minimal firewall.** A box runs a web app (80/443) and SSH (22) from a management
   subnet `10.10.0.0/24` only. Write the `ufw` rules implementing default-deny + exactly
   those allowances.

4. **fail2ban tuning.** Explain `maxretry`, `findtime`, and `bantime`, and set a policy
   that bans an IP for 24h after 3 failures within 5 minutes.

5. **Why MAC? (short answer).** Standard file permissions already restrict access — what
   additional protection do SELinux/AppArmor provide that `chmod`/users cannot? Give a
   concrete example (e.g. a compromised web server process).

## Success criteria
- [ ] `audit.sh` runs all four checks with PASS/WARN output.
- [ ] A correct, minimal sudoers drop-in for `ci`, verified with `sudo -l`.
- [ ] Default-deny + 80/443 anywhere + 22 from the management subnet.
- [ ] Correct fail2ban knob explanations + the 3/5m/24h policy.
- [ ] A sound explanation of MAC's value over DAC.
