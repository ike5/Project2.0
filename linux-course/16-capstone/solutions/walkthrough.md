# Capstone — Reference Walkthrough

A reference implementation. Try to build it from the brief first; use this to check
yourself or unblock. Run on the `capstone` VM.

## 1. User + SSH
```bash
sudo useradd -m -s /bin/bash deploy
sudo install -d -m 700 -o deploy -g deploy /home/deploy/.ssh
# from your Mac: ssh-copy-id deploy@<ip>   (or paste your pubkey into authorized_keys)
sudo visudo -f /etc/sudoers.d/deploy   # deploy ALL=(root) NOPASSWD: /usr/bin/systemctl restart nginx, /usr/bin/systemctl reload nginx
# harden sshd (KEEP A SESSION OPEN):
sudo sed -i 's/^#\?PermitRootLogin.*/PermitRootLogin no/;s/^#\?PasswordAuthentication.*/PasswordAuthentication no/' /etc/ssh/sshd_config
echo 'AllowUsers deploy ubuntu' | sudo tee -a /etc/ssh/sshd_config
sudo sshd -t && sudo systemctl reload ssh
```

## 2. Storage at /srv/www (loop-backed)
```bash
sudo mkdir -p /srv/disks /srv/www
sudo fallocate -l 1G /srv/disks/www.img
sudo losetup -fP /srv/disks/www.img; LOOP=$(losetup -j /srv/disks/www.img | cut -d: -f1)
sudo parted -s "$LOOP" mklabel gpt; sudo parted -s -a opt "$LOOP" mkpart primary ext4 0% 100%
sudo partprobe "$LOOP"; sudo mkfs.ext4 -q "${LOOP}p1"
UUID=$(sudo blkid -s UUID -o value "${LOOP}p1")
echo "UUID=$UUID /srv/www ext4 defaults,nofail 0 2" | sudo tee -a /etc/fstab
sudo mount -a; findmnt /srv/www
```
> Loop devices don't persist across reboot without re-`losetup`; for a real disk this
> fstab line is all you need. (For the lab, that's fine — or use a real attached disk.)

## 3. Web content + permissions (setgid)
```bash
sudo apt install -y nginx
sudo install -d -o deploy -g www-data -m 2750 /srv/www/site     # 2 = setgid
echo "<h1>Capstone server</h1>" | sudo -u deploy tee /srv/www/site/index.html
ls -ld /srv/www/site                                            # drwxr-s--- deploy www-data
# point nginx at it:
sudo tee /etc/nginx/sites-available/site >/dev/null <<'EOF'
server {
    listen 80 default_server;
    root /srv/www/site;
    index index.html;
}
EOF
sudo ln -sf /etc/nginx/sites-available/site /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl enable --now nginx
curl -I localhost                                               # 200 OK
```

## 4. Firewall
```bash
sudo ufw default deny incoming; sudo ufw default allow outgoing
sudo ufw allow 80,443/tcp
sudo ufw allow from 10.0.0.0/8 to any port 22 proto tcp        # scope to your admin net
sudo ufw enable; sudo ufw status verbose
```

## 5. Backup timer + health check
```bash
# backup.sh from Module 11/12:
sudo install -m 0755 ../11-scheduling-logging-backups/code/backup.sh /usr/local/bin/site-backup.sh
sudo tee /etc/systemd/system/site-backup.service >/dev/null <<'EOF'
[Unit]
Description=Backup the site
[Service]
Type=oneshot
ExecStart=/usr/local/bin/site-backup.sh /srv/www/site /var/backups/site
EOF
sudo tee /etc/systemd/system/site-backup.timer >/dev/null <<'EOF'
[Unit]
Description=Daily site backup
[Timer]
OnCalendar=*-*-* 02:00:00
Persistent=true
[Install]
WantedBy=timers.target
EOF
sudo systemctl daemon-reload && sudo systemctl enable --now site-backup.timer

# health check (cron every 5 min, logs via logger):
sudo tee /usr/local/bin/healthcheck.sh >/dev/null <<'EOF'
#!/usr/bin/env bash
set -uo pipefail
if systemctl is-active --quiet nginx && curl -fsS -o /dev/null http://localhost; then
  logger -t healthcheck "OK nginx+http"
else
  logger -t healthcheck "FAIL nginx or http"
fi
EOF
sudo chmod +x /usr/local/bin/healthcheck.sh
( sudo crontab -l 2>/dev/null; echo '*/5 * * * * /usr/local/bin/healthcheck.sh' ) | sudo crontab -
```

## 6. Hardening
```bash
sudo apt install -y fail2ban unattended-upgrades
printf '[sshd]\nenabled=true\nmaxretry=4\nbantime=1h\n' | sudo tee /etc/fail2ban/jail.local
sudo systemctl restart fail2ban
sudo install -m 0755 ../14-security-hardening/solutions/audit.sh /usr/local/bin/audit.sh
sudo /usr/local/bin/audit.sh
```

## 7. Verify (the acceptance test)
Run the **Acceptance test** block from the [capstone README](../README.md). All green =
done. Then score the rubric.

> Notice how many discrete files, services, and commands this took. In the Ansible course,
> the *entire* build becomes one declarative, re-runnable playbook — that's the payoff.
