# Lab 05 — Accounts & Permissions

**You'll:** create users/groups, build a shared setgid directory, and drive `chmod`/
`chown`. ⏱️ ~55 min. In your VM (uses `sudo`).

---

## Part A — Inspect the databases
```bash
id                                  # you
getent passwd | awk -F: '$3>=1000 {print $1, $3}'   # human users
getent passwd | awk -F: '$3<1000 {print $1}' | head # system accounts
sudo getent shadow ubuntu           # the (hashed) password entry — root-only file
```

## Part B — Create users and a group
```bash
sudo useradd -m -s /bin/bash alice
sudo useradd -m -s /bin/bash bob
sudo passwd alice                   # set a password (type one twice)
sudo groupadd devs
sudo usermod -aG devs alice
sudo usermod -aG devs bob
id alice; id bob                    # both in 'devs'
```
✅ Two users, both members of `devs` (note `-aG` *adds* without wiping other groups).

## Part C — Permissions hands-on
```bash
cd /tmp
echo "secret" > report.txt
ls -l report.txt                    # default perms (per umask)
chmod 640 report.txt                # rw-r-----
ls -l report.txt
sudo chown alice:devs report.txt    # owner alice, group devs
ls -l report.txt
# Test access AS bob (in devs, so group-read applies):
sudo -u bob cat report.txt          # works (group r)
sudo -u bob sh -c 'echo x >> /tmp/report.txt'   # FAILS (group has no w)
```
✅ Group members can read (group `r`) but not write (no group `w`). Permissions enforced.

## Part D — A shared team directory (setgid)
```bash
sudo mkdir /srv/team
sudo chown root:devs /srv/team
sudo chmod 2775 /srv/team           # 2 = setgid; rwxrwsr-x
ls -ld /srv/team                    # note the 's' in the group field
# Files created here inherit the 'devs' group automatically:
sudo -u alice touch /srv/team/from-alice
sudo -u bob   touch /srv/team/from-bob
ls -l /srv/team                     # both files are group 'devs' (setgid inheritance)
```
✅ **setgid on a directory** makes all new files belong to `devs`, so the team can
collaborate without fixing groups by hand.

## Part E — Sticky bit (like /tmp)
```bash
ls -ld /tmp                         # drwxrwxrwt  — the 't'
sudo chmod +t /srv/team
ls -ld /srv/team                    # now rwxrwsr-t
# With sticky set, bob can't delete alice's file even though the dir is group-writable:
sudo -u bob rm /srv/team/from-alice # Operation not permitted
```

## Part F — umask
```bash
umask                               # current (e.g. 0022)
touch a; ls -l a                    # 644
umask 027; touch b; ls -l b         # 640 (group r, other none)
umask 022                           # restore
```

## Part G — sudo policy
```bash
# Give alice passwordless restart of a service, safely:
echo 'alice ALL=(ALL) NOPASSWD: /usr/bin/systemctl restart ssh' | sudo tee /etc/sudoers.d/alice
sudo visudo -c                      # validate sudoers syntax
sudo -u alice sudo -n systemctl is-active ssh   # alice's limited sudo
```

## Cleanup
```bash
sudo deluser --remove-home alice; sudo deluser --remove-home bob
sudo groupdel devs; sudo rm -rf /srv/team /tmp/report.txt /tmp/a /tmp/b /etc/sudoers.d/alice
```

## What you learned
- Account/group management with `useradd`/`usermod -aG`/`passwd`.
- octal & symbolic `chmod`, `chown`/`chgrp`, and how group perms gate access.
- **setgid** dirs for team collaboration; **sticky** to protect shared dirs; `umask`.
- Scoped `sudo` via `/etc/sudoers.d` + `visudo -c`.

➡️ **[challenge.md](./challenge.md)** then [Module 06](../06-processes/).
