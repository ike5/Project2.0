# Challenge 05 — Reference Solution

### 1. Octal ↔ symbolic
- (a) `rwxr-x---` = **750** (7=rwx, 5=r-x, 0=---).
- (b) `0644` = `rw-r--r--`.
- (c) Take `0664` and remove all "other" access → `chmod o= file` (or `chmod 660 file`).

### 2. Why can't they read it?
`bob` **cannot** read `secret.txt`. Even though the file is world-readable
(`-rw-r--r--`), the parent directory `/srv/data` is `drwx------` (owner-only). To reach a
file you need **`x` (traverse)** on *every* parent directory; bob has no access to
`/srv/data`, so he can't even get to the file.
**Minimal fix:** give traverse on the directory, e.g.
```bash
sudo chmod o+x /srv/data      # others can traverse (but still can't LIST without r)
```
(With `o+x` bob can `cat /srv/data/secret.txt` if he knows the name; add `o+r` on the dir
only if he also needs to *list* it.)

### 3. Dropbox → sticky bit
The **sticky bit** (`+t`) on a world-writable dir lets anyone create files but stops users
from deleting/renaming files they don't own:
```bash
sudo mkdir /srv/incoming
sudo chmod 1777 /srv/incoming     # like /tmp
```

### 4. Shared project dir
```bash
sudo groupadd eng                 # if needed
sudo mkdir /srv/project
sudo chown root:eng /srv/project
sudo chmod 2770 /srv/project      # 2=setgid (group inheritance), rwx for owner+group, --- other
```
> `2770`: setgid makes new files group `eng`; `770` gives full access to owner+group and
> nothing to others.

### 5. Audit setuid
```bash
find / -perm -4000 -type f 2>/dev/null
```
> **Why it matters:** a **setuid root** binary runs with root privileges regardless of who
> launches it. If such a binary has a bug (buffer overflow, command injection), an
> unprivileged user can exploit it to gain root. Minimizing and auditing setuid-root
> binaries is a core hardening task.
