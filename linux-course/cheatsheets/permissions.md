# Permissions Cheatsheet

## Reading `ls -l`
```
-rwxr-x---  1 alice devs  4096 Jun  1 10:00 script.sh
│└┬┘└┬┘└┬┘    │     │
│ │  │  └ other: ---   (no access)
│ │  └─── group: r-x   (read, execute)
│ └────── owner: rwx   (read, write, execute)
└──────── type: - file, d dir, l symlink, c/b device, s socket, p pipe
```
Three triplets: **owner**, **group**, **other**. Each is `r` (4), `w` (2), `x` (1).

## Octal ↔ symbolic
| Octal | Bits | Meaning |
|------:|------|---------|
| 7 | rwx | read+write+execute |
| 6 | rw- | read+write |
| 5 | r-x | read+execute |
| 4 | r-- | read |
| 0 | --- | none |

```bash
chmod 750 file        # owner rwx, group r-x, other ---
chmod 644 file        # owner rw-, group r--, other r--
chmod u+x file        # add execute for owner
chmod go-w file       # remove write for group & other
chmod -R u+rwX dir    # recursive; capital X = execute only on dirs/already-exec files
```

## Ownership
```bash
chown alice file            # change owner
chown alice:devs file       # owner and group
chgrp devs file             # group only
chown -R alice:alice dir/   # recursive
```

## Directory permissions (the tricky part)
- `r` on a dir = list names. `x` = enter/traverse (use the dir). `w` = create/delete
  entries **in** it.
- You usually need **`x`** to do anything inside a directory, even if you have `r`.
- To read a file you need `r` on the file **and** `x` on every parent directory.

## umask (defaults for new files)
- Default permissions: files start from `666`, dirs from `777`, then **umask is subtracted**.
- `umask 022` → new files `644`, new dirs `755` (common default).
```bash
umask           # show (e.g. 0022)
umask 027       # stricter: group r-x, other none
```

## Special bits
| Bit | Octal | On a file | On a directory |
|-----|------:|-----------|----------------|
| setuid | 4000 | run as the file's **owner** | (no effect) |
| setgid | 2000 | run as the file's **group** | new files inherit the dir's **group** |
| sticky | 1000 | (no effect) | only the **owner** of a file can delete it (e.g. `/tmp`) |

```bash
chmod u+s binary       # setuid   -> shows 's' in owner execute slot
chmod g+s shared_dir   # setgid   -> group inheritance
chmod +t /shared       # sticky   -> shows 't' in other execute slot
chmod 4755 binary      # octal form (leading 4 = setuid)
ls -l                  # rwsr-xr-x = setuid;  rwxr-sr-x = setgid;  drwxrwxrwt = sticky
```

## Find by permission / ownership
```bash
find / -perm -4000 -type f 2>/dev/null   # all setuid binaries (audit!)
find /home -user alice
find . -perm 777                          # world-writable (often a bug)
```

## ACLs (finer-grained, beyond owner/group/other)
```bash
getfacl file
setfacl -m u:bob:rw file      # give bob read+write without changing group
setfacl -x u:bob file         # remove
```
