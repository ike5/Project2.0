# Challenge 14 — Reference Solution

### 1. Audit script
See [`audit.sh`](./audit.sh). Run `sudo ./audit.sh` (sudo needed for `/etc/shadow` and a
complete setuid scan).

### 2. Scoped sudo
```bash
sudo visudo -f /etc/sudoers.d/ci
# file content:
ci ALL=(root) NOPASSWD: /usr/bin/systemctl restart myapp
```
Verify:
```bash
sudo -l -U ci
#   User ci may run the following commands:
#     (root) NOPASSWD: /usr/bin/systemctl restart myapp
sudo -u ci sudo -n systemctl restart myapp     # allowed
sudo -u ci sudo -n systemctl stop myapp        # DENIED (not in the policy)
```
> Specify the **full binary path** and exact arguments; a bare `systemctl` would let `ci`
> control any unit. Always edit via `visudo` (it validates syntax before saving).

### 3. Minimal firewall
```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 80,443/tcp                                   # web from anywhere
sudo ufw allow from 10.10.0.0/24 to any port 22 proto tcp   # SSH only from mgmt subnet
sudo ufw enable
sudo ufw status verbose
```

### 4. fail2ban tuning
> - **`maxretry`** — number of failures that triggers a ban.
> - **`findtime`** — the window in which those failures must occur.
> - **`bantime`** — how long the IP stays banned.
```ini
[sshd]
enabled  = true
maxretry = 3
findtime = 5m
bantime  = 24h
```
(3 failures within 5 minutes → banned for 24 hours.)

### 5. Why MAC over DAC
> Standard permissions (**DAC** — discretionary access control) decide access by **user/
> group ownership**, and **root bypasses them entirely**. **MAC** (SELinux/AppArmor)
> confines a *process* to only the resources its **policy/profile** allows, regardless of
> the user it runs as.
> **Example:** nginx runs as `www-data` and is compromised via a bug. With DAC alone, the
> attacker can read anything `www-data` can. With **SELinux/AppArmor enforcing**, the
> nginx process is confined to its expected files/ports/syscalls — so it **can't** read
> `/etc/shadow`, open a reverse shell, or write outside its document root, even though the
> exploit succeeded. MAC contains the blast radius.
