# Lab 14 — Harden a Server

**You'll:** work the hardening checklist on your `web` VM (or `lab`). ⏱️ ~55 min.
Keep an SSH session open while changing SSH/firewall settings.

---

## Part A — Patch
```bash
sudo apt update && sudo apt -y upgrade
# Turn on automatic security updates:
sudo apt install -y unattended-upgrades
sudo systemctl status unattended-upgrades --no-pager | head
```

## Part B — Audit accounts
```bash
awk -F: '($3==0){print $1}' /etc/passwd          # ONLY 'root' should print
sudo awk -F: '($2==""){print $1}' /etc/shadow    # empty passwords (should be none)
awk -F: '$3>=1000 && $3<65534 {print $1, $7}' /etc/passwd   # human users + shells
# Create then lock a stale account to see the effect:
sudo useradd -m olduser
sudo usermod -L -s /usr/sbin/nologin olduser
sudo grep '^olduser' /etc/shadow | cut -c1-20    # '!' prefix = locked
```

## Part C — Firewall: default-deny
```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp                 # keep SSH!
sudo ufw --force enable
sudo ufw status verbose
sudo ss -tulpn                        # cross-check what's actually listening
```
✅ Only SSH is allowed in; everything else is denied by default.

## Part D — fail2ban
```bash
sudo apt install -y fail2ban
sudo tee /etc/fail2ban/jail.local >/dev/null <<'EOF'
[sshd]
enabled = true
maxretry = 4
bantime = 30m
findtime = 10m
EOF
sudo systemctl restart fail2ban
sudo fail2ban-client status            # lists active jails
sudo fail2ban-client status sshd       # ban counters
```

## Part E — SSH hardening (with a safety session)
```bash
# (Assumes key auth is set up from Module 13. Keep THIS session open.)
sudo sed -i 's/^#\?PermitRootLogin.*/PermitRootLogin no/' /etc/ssh/sshd_config
sudo sed -i 's/^#\?PasswordAuthentication.*/PasswordAuthentication no/' /etc/ssh/sshd_config
sudo sshd -t && sudo systemctl reload ssh        # validate, then reload (keeps sessions)
# In a SECOND terminal: ssh web 'echo still-works'   BEFORE closing this one.
```

## Part F — Audit setuid & permissions
```bash
sudo find / -perm -4000 -type f 2>/dev/null      # review the list (passwd, sudo, etc.)
ls -l /etc/shadow                                 # should be root:shadow, 640 (or 600)
sudo find /home -perm -2 -type f 2>/dev/null      # world-writable files under /home (bad)
```

## Part G — AppArmor (Ubuntu MAC)
```bash
sudo aa-status | head                             # profiles loaded/enforcing
# (RHEL equivalent: getenforce; sestatus; ls -Z)
```

## Cleanup
```bash
sudo deluser --remove-home olduser
sudo ufw --force reset
sudo systemctl stop fail2ban
```

## What you learned
- Patching + auto-updates; auditing UID-0/empty-password/stale accounts.
- Default-deny firewalling and verifying with `ss`.
- fail2ban against brute force; safe SSH hardening.
- setuid/world-writable audits; checking AppArmor/SELinux status.

➡️ **[challenge.md](./challenge.md)** then [Module 15](../15-containers-virtualization/).
