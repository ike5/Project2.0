# Module 05 — Users, Groups & Permissions

**Goal:** manage accounts and control who can do what — the heart of Linux security and a
heavily-tested exam area. ⏱️ ~2.5 h · 🎯 Prereq: 00–04.

> Deep reference: [cheatsheets/permissions.md](../cheatsheets/permissions.md).

---

## 1. Users, groups, and the databases

Every user has a **UID**; every group a **GID**. Three text files define them:
```bash
/etc/passwd   # user:x:UID:GID:comment:home:shell   (world-readable; x = password in shadow)
/etc/shadow   # user:hashed_password:...             (root-only; the actual hashes)
/etc/group    # group:x:GID:member1,member2
```
```bash
id sam                     # uid, gid, group memberships
getent passwd sam          # sam's passwd entry
cat /etc/passwd | column -t -s:   # readable view
```
- **root** is UID 0 (all-powerful). **System/service** accounts are typically UID < 1000
  with a `nologin` shell. **Human** users are UID ≥ 1000.

## 2. Managing users

```bash
sudo adduser sam              # Debian: interactive, creates home + group (friendly)
sudo useradd -m -s /bin/bash sam   # portable: -m home, -s shell
sudo passwd sam              # set/lock password
sudo usermod -aG sudo sam    # ADD to a group (-a is vital; without it you REPLACE groups)
sudo usermod -L sam          # lock account;  -U unlock
sudo deluser sam             # remove (Debian);  userdel -r sam removes home too
sudo chage -l sam            # password aging info
```
> ⚠️ `usermod -G grp sam` (no `-a`) **replaces** all supplementary groups. Always
> `usermod -aG`.

## 3. Groups

```bash
sudo groupadd devs
sudo usermod -aG devs sam
groups sam                  # which groups sam is in
newgrp devs                 # switch primary group for this session
```
- **Primary group** (in `/etc/passwd`) — owns files the user creates by default.
- **Supplementary groups** (in `/etc/group`) — extra memberships (e.g. `sudo`, `docker`).

## 4. Permissions: the rwx model

Each file has permissions for **owner / group / other**, each with **read (4)**,
**write (2)**, **execute (1)**:
```
-rwxr-x---  owner=rwx(7)  group=r-x(5)  other=---(0)   =>  750
```
```bash
chmod 640 file        # rw-r----- : owner rw, group r, other none
chmod u+x,g-w file    # symbolic: add owner-exec, remove group-write
chmod -R u+rwX dir/   # recursive; X = exec only on dirs/already-exec files
chown sam:devs file   # set owner and group
chgrp devs file       # group only
```
**Directories are special:** `x` = traverse/enter, `r` = list names, `w` = add/remove
entries. You need `x` on every parent directory to reach a file.

## 5. umask — defaults for new files

New files start at `666` and dirs at `777`, minus the **umask**:
```bash
umask              # e.g. 0022 -> files 644, dirs 755
umask 027          # stricter: group r-x, other nothing
```

## 6. Special bits (exam favorites)

| Bit | Set with | Effect |
|-----|----------|--------|
| **setuid** (4000) | `chmod u+s` | executable runs as its **owner** (e.g. `passwd` runs as root) |
| **setgid** (2000) | `chmod g+s` | exec runs as its **group**; on a **dir**, new files inherit the dir's group |
| **sticky** (1000) | `chmod +t` | on a dir, only a file's **owner** can delete it (e.g. `/tmp`) |

```bash
ls -l /usr/bin/passwd     # -rwsr-xr-x  (the 's' = setuid root)
ls -ld /tmp               # drwxrwxrwt  (the 't' = sticky)
find / -perm -4000 -type f 2>/dev/null   # audit all setuid binaries
```

## 7. sudo & becoming root

```bash
sudo cmd            # run one command as root (per /etc/sudoers policy)
sudo -i             # interactive root shell
sudo -u sam cmd     # run as another user
sudo visudo         # SAFELY edit sudoers (validates syntax before saving)
```
Grant sudo by group membership (Ubuntu: `sudo` group; RHEL: `wheel`) or a drop-in:
```bash
echo 'sam ALL=(ALL) NOPASSWD: /usr/bin/systemctl restart nginx' | sudo tee /etc/sudoers.d/sam
```
> **RHEL family:** add admins to **`wheel`** instead of `sudo`.

---

## Do the lab
Create users and groups, set up a shared directory with setgid, and master `chmod`/
`chown`. 👉 **[lab.md](./lab.md)**

Then: 👉 **[challenge.md](./challenge.md)**

## Key terms
UID/GID · `/etc/passwd`/`shadow`/`group` · `useradd`/`usermod -aG`/`passwd` · primary vs
supplementary group · rwx (owner/group/other) · octal vs symbolic · `chmod`/`chown`/
`chgrp` · `umask` · setuid/setgid/sticky · `sudo`/`visudo`/`wheel`

**Next →** [Module 06: Processes & Job Control](../06-processes/)
