# Module 14 — Security & Hardening

**Goal:** apply layered, practical hardening — accounts, sudo, SSH, firewall, fail2ban,
updates, and mandatory access control (SELinux/AppArmor). ⏱️ ~2.5 h · 🎯 Prereq: 00–13.

---

## 1. The hardening mindset

Security is **layers** (defense in depth) and **least privilege** (grant the minimum
needed). No single control is enough; you stack them. The big wins on a Linux server:

```
1. Keep it patched          5. Restrict sudo
2. SSH key-only + no root    6. Audit accounts & setuid
3. Firewall (deny by default)7. MAC (SELinux/AppArmor) enforcing
4. fail2ban on auth          8. Minimal installed software
```

## 2. Updates (the highest-value control)

```bash
sudo apt update && sudo apt upgrade -y          # Debian/Ubuntu
sudo dnf upgrade -y                              # RHEL/Fedora
# Automatic security updates:
sudo apt install -y unattended-upgrades && sudo dpkg-reconfigure unattended-upgrades
#   RHEL: sudo dnf install -y dnf-automatic && enable the timer
```
Unpatched software is the most common breach vector — automate this.

## 3. Account & sudo hygiene

```bash
# Find accounts with empty passwords (should be none):
sudo awk -F: '($2==""){print $1}' /etc/shadow
# Find UID 0 accounts (should be ONLY root):
awk -F: '($3==0){print $1}' /etc/passwd
# Lock unused accounts:
sudo usermod -L olduser;  sudo usermod -s /usr/sbin/nologin olduser
# Scope sudo tightly (drop-ins in /etc/sudoers.d, validated by visudo):
sudo visudo -f /etc/sudoers.d/deploy   # 'deploy ALL=(ALL) NOPASSWD: /usr/bin/systemctl restart nginx'
```

## 4. SSH hardening (recap from Module 13)

In `/etc/ssh/sshd_config`: `PermitRootLogin no`, `PasswordAuthentication no` (keys only),
`AllowUsers <list>`. Validate with `sudo sshd -t`, then reload. **Test in a second
session.**

## 5. Firewall: default-deny

```bash
# ufw (Ubuntu)
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp                 # then only what you need
sudo ufw allow 80,443/tcp
sudo ufw enable
# firewalld (RHEL) defaults to a deny-ish zone; add only needed services/ports.
```
Expose the **minimum** ports. Check what's listening (`ss -tulpn`) and close the rest.

## 6. fail2ban (block brute force)

```bash
sudo apt install -y fail2ban
sudo tee /etc/fail2ban/jail.local >/dev/null <<'EOF'
[sshd]
enabled = true
maxretry = 5
bantime = 1h
findtime = 10m
EOF
sudo systemctl restart fail2ban
sudo fail2ban-client status sshd      # see banned IPs
```
It watches auth logs and firewalls off IPs after repeated failures.

## 7. Audit setuid & permissions

```bash
sudo find / -perm -4000 -type f 2>/dev/null     # setuid binaries — review each
sudo find / -perm -2 -type f -not -path '/proc/*' 2>/dev/null | head  # world-writable files
ls -l /etc/passwd /etc/shadow                    # shadow should be 640/600, root-owned
```

## 8. Mandatory Access Control (MAC)

Beyond user/group permissions, **SELinux** (RHEL) and **AppArmor** (Ubuntu) confine what
a program can do even if it's compromised.
```bash
# RHEL — SELinux
getenforce                       # Enforcing / Permissive / Disabled
sudo setenforce 1                # enforce (temporary)
sudo ausearch -m avc -ts recent  # recent denials;  audit2allow to craft policy
ls -Z /var/www                   # security contexts;  restorecon -Rv to fix
# Ubuntu — AppArmor
sudo aa-status                   # profiles loaded/enforcing
sudo aa-enforce /etc/apparmor.d/usr.sbin.nginx
```
Keep MAC **enforcing** in production; troubleshoot denials rather than disabling it.

## 9. Quick wins checklist

- [ ] Patched + auto security updates on.
- [ ] SSH: keys only, no root, limited users.
- [ ] Firewall default-deny; only needed ports open.
- [ ] fail2ban on sshd.
- [ ] No empty passwords; only root is UID 0; unused accounts locked.
- [ ] sudo scoped via `/etc/sudoers.d`.
- [ ] setuid binaries reviewed.
- [ ] SELinux/AppArmor enforcing.

---

## Do the lab
Harden a fresh server step by step using the checklist. 👉 **[lab.md](./lab.md)**

Then: 👉 **[challenge.md](./challenge.md)**

## Key terms
defense in depth · least privilege · unattended-upgrades · UID-0 audit · `usermod -L` ·
sudoers drop-ins · default-deny firewall · fail2ban · setuid audit · world-writable ·
SELinux (`getenforce`/contexts) · AppArmor (`aa-status`)

**Next →** [Module 15: Containers & Virtualization](../15-containers-virtualization/)
