# Challenge 09 — Storage Scenarios

Solutions in [`solutions/`](./solutions/). Try first (use loop devices as in the lab).

## Tasks
1. **Mount by label.** Format a loop partition, give it the filesystem label `backup`,
   and write an `/etc/fstab` entry that mounts it **by LABEL** (not UUID) at `/mnt/backup`.
   Test with `mount -a`.

2. **The fstab rescue.** You add a bad fstab line (typo'd UUID) and `mount -a` fails. (a)
   Why is this dangerous for the *next boot*? (b) What option makes a missing/failed mount
   non-fatal at boot? (c) How would you recover if the box won't boot due to fstab?

3. **Grow a filesystem.** Starting from a 1G LV mounted and in use, add a new PV, extend
   the VG, then grow the LV and its ext4 filesystem to ~1.5G **without unmounting**. Show
   the commands.

4. **Out of inodes.** Explain how a filesystem can report plenty of free space (`df -h`)
   yet refuse to create files. Which command reveals the real cause?

5. **Stretch:** Compare ext4 vs xfs in one or two sentences each (and note which is the
   RHEL default and whether each can be shrunk).

## Success criteria
- [ ] Label-based fstab mount works via `mount -a`.
- [ ] You can explain boot risk, the `nofail` option, and recovery (rescue/`init=/bin/bash`
      or editing fstab from a live env).
- [ ] Online LV + filesystem growth commands correct.
- [ ] `df -i` identified as the inode check.
