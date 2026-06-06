# Lab 02 — Files, Links & Find

**You'll:** build a tree, manage files, create both link types, glob, and find. ⏱️ ~45 min.
Work in your `lab` VM.

---

## Part A — Explore the FHS
```bash
ls /                       # the top level
ls -l /bin                 # often a symlink -> usr/bin
ls /etc | head             # config files
cat /etc/os-release        # a real config file
file /etc/hostname /bin/ls /dev/null    # text vs binary vs device
```

## Part B — Build a workspace
```bash
cd ~
mkdir -p project/{src,docs,logs}    # brace expansion: 3 dirs at once
touch project/src/main.c project/docs/readme.md
touch project/logs/app.{1,2,3}.log
tree project        # (sudo apt install -y tree)  — see the structure
```
✅ Expected: `project/` with `src`, `docs`, `logs` and the files you created.

## Part C — Copy, move, rename
```bash
cd ~/project
cp docs/readme.md docs/readme.bak      # copy
cp -r src src-backup                    # recursive copy
mv docs/readme.bak docs/README.old      # rename
mv src-backup archive                   # rename a dir
ls -R                                    # recursive listing
```

## Part D — Links
```bash
cd ~/project
ln -s /etc/os-release docs/os-link      # symbolic link
ls -l docs/os-link                       # shows '-> /etc/os-release'
cat docs/os-link                         # reads the target

echo "data" > logs/real.txt
ln logs/real.txt logs/hard.txt           # hard link (same inode)
ls -li logs/real.txt logs/hard.txt       # SAME inode number, link count 2
echo "more" >> logs/hard.txt
cat logs/real.txt                        # shows 'more' too (same data!)
rm logs/real.txt
cat logs/hard.txt                        # still works (data survives)
```
✅ Hard links share one inode (deleting one name keeps the data); a symlink is just a
pointer (breaks if the target moves).

## Part E — Globbing
```bash
cd ~/project/logs
ls *.log                  # all logs
ls app.?.log              # single-char wildcard
ls app.[12].log           # app.1.log app.2.log
ls /etc/*/                # only directories under /etc
echo file{a,b,c}.txt      # brace expansion (preview without creating)
```

## Part F — Find
```bash
find ~/project -type f                       # all files
find ~/project -name '*.log'                 # by pattern
find ~/project -type d                       # directories
find / -name 'hosts' 2>/dev/null             # suppress permission errors
find ~/project -name '*.bak' -o -name '*.old'  # OR
# Find and act:
find ~/project/logs -name '*.log' -exec ls -lh {} \;
```

## Part G — Clean up safely
```bash
ls ~/project           # LOOK before removing
rm -rf ~/project       # remove the workspace (it's just lab data)
```

## What you learned
- The FHS and how to inspect files (`stat`, `file`).
- `mkdir -p`, brace expansion, `cp -r`/`mv`/`rm -rf`.
- Hard vs symbolic links (inodes vs pointers).
- Globbing and `find` (by name/type/size/time, with `-exec`).

➡️ **[challenge.md](./challenge.md)** then [Module 03](../03-text-processing/).
