# Module 16 — Capstone: Build & Harden a Server

**Goal:** prove your mastery by standing up a small, real, **hardened** web server
**entirely by hand** — pulling together users, permissions, storage, services,
networking, scheduling, scripting, SSH, and security. ⏱️ ~3+ h · 🎯 Prereq: 00–15.

> This is the "do it manually" milestone. In the separate **[Ansible course](../../ansible-course/)**
> you'll codify this exact build as a playbook — and *that's* when automation clicks.

---

## The brief

On a fresh VM (`multipass launch --name capstone 22.04`), deliver a server that:

1. **Users & access**
   - A `deploy` user with a sudo policy limited to managing the web service.
   - SSH **key-only**, root login disabled, only `deploy` (and your admin user) allowed.

2. **Web service**
   - **nginx** installed and serving a site from `/srv/www/site` (your own `index.html`).
   - Running via systemd, enabled at boot.

3. **Storage**
   - The site content lives on a **separate filesystem** (a loop device is fine) mounted
     at `/srv/www` via `/etc/fstab` (by UUID, with `nofail`).

4. **Permissions**
   - `/srv/www/site` owned `deploy:www-data`, group-readable, **setgid** so new files
     inherit the group. No world-write anywhere.

5. **Networking & firewall**
   - Default-deny firewall; allow **80/443** from anywhere and **22** from your admin
     network only.

6. **Automation (by hand, with cron/timers + scripts)**
   - A **backup script** (from Module 12) that archives `/srv/www/site` daily via a
     **systemd timer**, keeping the 7 most recent backups, logging to the journal.
   - A **health-check script** that verifies nginx is active and the site returns HTTP 200,
     logging via `logger`.

7. **Hardening**
   - fail2ban on sshd; automatic security updates enabled.
   - Pass your own `audit.sh` (Module 14) with no WARNs you can't justify.

8. **Observability**
   - You can show the service status, recent logs (`journalctl -u nginx`), the timer's next
     run, listening ports (`ss -tulpn`), and disk/mount layout (`lsblk`, `df -h`).

---

## Suggested order

1. Provision the VM; create `deploy`; set up SSH keys; harden sshd (keep a session open!).
2. Create the loop-backed filesystem, mount at `/srv/www` via fstab, set permissions/setgid.
3. Install nginx; point it at `/srv/www/site`; add your `index.html`; enable at boot.
4. Firewall: default-deny, allow 80/443 + scoped 22.
5. Add the backup script + systemd timer; add the health-check script (timer or cron).
6. fail2ban + unattended-upgrades.
7. Run `audit.sh`; fix findings.

## Acceptance test (prove it works)

```bash
# From your Mac / admin host:
curl -I http://<capstone-ip>            # 200 OK from nginx
ssh deploy@<capstone-ip> 'echo ok'      # key login works; password login refused

# On the server:
systemctl is-active nginx               # active
systemctl is-enabled nginx              # enabled
findmnt /srv/www                        # mounted via fstab
ls -ld /srv/www/site                    # setgid (rwxr-s---), owner deploy:www-data
sudo ufw status verbose                 # default-deny; 80/443 + scoped 22
systemctl list-timers | grep backup     # next backup run scheduled
journalctl -t healthcheck -n 3          # health-check log lines
sudo fail2ban-client status sshd        # jail active
sudo ./audit.sh                         # no unexplained WARNs
```

---

## Mastery rubric (self-assess)

| Capability | Needs work | Solid | Mastery |
|------------|-----------|-------|---------|
| **Shell/text** | copies commands | fluent pipelines | builds tools; reasons about quoting/streams |
| **Files/perms** | sets perms | correct owner/group/setgid | explains traversal, special bits, audits |
| **Services** | starts nginx | systemd unit + enable | custom units, restarts, journal triage |
| **Storage** | mounts a disk | fstab by UUID + nofail | LVM/online-grow; recovers a bad fstab |
| **Networking** | opens ports | default-deny + scoped rules | layered triage; DNS/routing reasoning |
| **Scheduling** | a cron line | timer + retention | robust backup/health scripts |
| **SSH/security** | password login | key-only, hardened | least-privilege sudo, fail2ban, MAC-aware |
| **Scripting** | one-liners | `set -euo pipefail` tools | idempotent, validated, shellcheck-clean |

**You've reached the goal when** you can take a bare VM and turn it into a secure,
observable, self-maintaining service from memory — and explain every decision.

## What's next
- **Automate it:** the separate **[Ansible course](../../ansible-course/)** turns this
  entire by-hand build into a reusable, idempotent playbook.
- **Scale it:** the **[Kubernetes course](../../kubernetes-course/)** orchestrates the
  containerized version.

This is the final module. 🎓 Run the acceptance test, score the rubric, and you've
completed the Linux course.
