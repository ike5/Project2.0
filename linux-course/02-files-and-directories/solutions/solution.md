# Challenge 02 — Reference Solution

### 1. One-command tree
```bash
mkdir -p site/{html,css,js}
touch site/html/index.html site/css/style.css site/js/app.js
```

### 2. Link behavior
```bash
echo hi > data.txt
ln data.txt h.txt          # hard link (same inode)
ln -s data.txt s.txt       # symlink (points at the NAME 'data.txt')
mv data.txt data2.txt
cat h.txt                  # works — hard link shares the inode/data
cat s.txt                  # FAILS — 'No such file' (target name gone)
ls -li h.txt s.txt         # h.txt has the data's inode; s.txt -> data.txt (broken)
```
> The hard link points at the **inode** (the data), so renaming the original doesn't
> matter. The symlink points at the **path** `data.txt`, which no longer exists.

### 3. Big or old logs
```bash
# size > 1M:
sudo find /var/log -name '*.log' -size +1M
# OR not modified in 7 days, in one grouped expression:
sudo find /var/log -name '*.log' \( -size +1M -o -mtime +7 \)
```
(`\( ... \)` groups; `-o` is OR. Quote/escape the parentheses for the shell.)

### 4. Safe cleanup
```bash
find ~ -name '*.tmp'            # SHOW first — verify the list is what you expect
find ~ -name '*.tmp' -delete    # then delete
```
> Running the show version first catches mistakes (wrong path, unexpected matches) before
> anything is irreversibly deleted.

### 5. Stretch
> If `$DIR` is unset/empty, `rm -rf "$DIR/"` becomes `rm -rf "/"` — it tries to delete the
> whole filesystem. **Habits that prevent it:** set `set -u` in scripts (error on unset
> vars), default with `${DIR:?must be set}`, and never put a trailing `/` after an
> unvalidated variable. Always `ls` the target first.
