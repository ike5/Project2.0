# Module 02 — Files & Directories

**Goal:** navigate the filesystem, manage files confidently, and understand links and
globbing. ⏱️ ~2 h · 🎯 Prereq: 00–01.

---

## 1. One tree, no drive letters

Linux has a single tree rooted at **`/`**. Everything — disks, devices, even processes —
appears somewhere in it. Key locations (the **FHS**):

| Path | Holds |
|------|-------|
| `/` | the root of everything |
| `/home/<user>` | user home directories (`~`) |
| `/root` | root's home |
| `/etc` | system configuration (text files) |
| `/var` | variable data: `/var/log`, `/var/www`, spools |
| `/usr` | installed software (`/usr/bin`, `/usr/lib`, `/usr/share`) |
| `/bin`, `/sbin` | essential binaries (usually symlinks into `/usr`) |
| `/tmp` | temporary files (world-writable, wiped on reboot) |
| `/opt` | optional/third-party software |
| `/dev` | device files (`/dev/sda`, `/dev/null`) |
| `/proc`, `/sys` | virtual: kernel/process info |
| `/mnt`, `/media` | mount points for extra/removable filesystems |
| `/boot` | kernel + bootloader |

## 2. Paths: absolute vs relative

```bash
cd /etc/ssh          # absolute (from /)
cd ../..             # relative: up two levels
cd ~          # home          cd -   # previous dir          cd     # home
pwd                  # where am I
.   = current dir      ..  = parent      ~  = home      ~sam = sam's home
```

## 3. Listing & inspecting

```bash
ls -lah              # long, all (dotfiles), human sizes
ls -lt   / ls -lS    # by time / by size
stat file            # inode, perms, timestamps, size
file thing           # what *is* this (text? ELF binary? data?)
du -sh dir/          # total size of a dir
```
**Dotfiles** (names starting with `.`) are hidden by default; `-a` shows them.

## 4. Creating, copying, moving, deleting

```bash
mkdir -p a/b/c               # create nested dirs
touch file                   # create empty / update timestamp
cp src dst;  cp -r dir1 dir2 # copy (recursive for dirs)
cp -a dir1 dir2              # archive copy (preserve perms/links/times)
mv old new                   # move OR rename (same op)
rm file;  rm -r dir;  rm -rf dir   # remove (force-recursive = dangerous)
rmdir emptydir               # only removes empty dirs
```
> ⚠️ `rm -rf` has no undo and no trash. **Look before you delete** (`ls` the target).
> Never run `rm -rf /` or `rm -rf "$VAR/"` when `$VAR` might be empty.

## 5. Links (a classic exam topic)

```bash
ln -s /etc/hosts mylink      # SYMBOLIC link: a pointer to a path
ln /etc/hosts hardlink       # HARD link: another name for the same inode
ls -l                        # symlink shows '-> target'; hardlink shows link count
```
- **Hard link** — two names → one inode/data. Deleting one keeps the data until the last
  name is gone. Can't span filesystems or link directories.
- **Symbolic (soft) link** — a tiny file holding a path. Can cross filesystems and point
  to dirs, but **breaks** if the target moves/disappears.

## 6. Wildcards (globbing) — the shell expands these

```bash
*           # any chars (not leading dot)      ls *.conf
?           # exactly one char                 ls file?.txt
[abc]       # one of a, b, c                    ls [ab]*.log
[a-z] [0-9] # ranges
{a,b,c}     # brace expansion (not a wildcard)  touch file{1,2,3}.txt
ls /etc/*/  # only directories under /etc
```
The **shell** expands globs before the command runs — `rm *.tmp` is `rm` receiving each
matching name.

## 7. Finding files

```bash
find /etc -name '*.conf'             # by name (quote the pattern!)
find . -type f -size +10M            # files over 10 MB
find /var/log -mtime -1              # modified in the last day
find . -type d -empty                # empty directories
find . -name '*.bak' -delete         # find and act (careful)
find . -name '*.log' -exec gzip {} \;# run a command per match
locate sshd_config                   # fast, from an index (sudo updatedb to refresh)
```

---

## Do the lab
Build a directory tree, copy/move/link files, glob, and find. 👉 **[lab.md](./lab.md)**

Then: 👉 **[challenge.md](./challenge.md)**

## Key terms
FHS · `/` tree · absolute/relative path · `.`/`..`/`~` · dotfile · `stat`/`file` ·
`cp -a`/`mv`/`rm -rf` · hard vs symbolic link · inode · glob (`*`,`?`,`[]`,`{}`) ·
`find`/`locate`

**Next →** [Module 03: Text Processing & Pipelines](../03-text-processing/)
