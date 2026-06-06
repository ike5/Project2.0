# Challenge 09 — Reference Solution

### 1. Mount by label
```bash
sudo mkfs.ext4 -q -L backup /dev/loopXp1     # label at format time
# or set later: sudo e2label /dev/loopXp1 backup
sudo mkdir -p /mnt/backup
echo "LABEL=backup /mnt/backup ext4 defaults,nofail 0 2" | sudo tee -a /etc/fstab
sudo mount -a
findmnt /mnt/backup                           # confirm
```

### 2. The fstab rescue
- **(a)** `/etc/fstab` is read **at boot**. A bad entry can drop the boot into an
  emergency shell (or hang waiting for a device), because the boot tries to mount it and
  fails.
- **(b)** Add **`nofail`** (and optionally `x-systemd.device-timeout=5`) so a
  missing/failed mount is logged but **doesn't block boot**.
- **(c)** Recovery: boot into the **rescue/emergency target** (or append `init=/bin/bash`
  / use the GRUB recovery entry), remount root read-write
  (`mount -o remount,rw /`), fix `/etc/fstab`, reboot. Or mount the disk from a live ISO/
  another VM and edit fstab there. **Always `sudo mount -a` after editing** to catch
  errors before rebooting.

### 3. Grow online
```bash
sudo pvcreate /dev/loopZ
sudo vgextend labvg /dev/loopZ
sudo lvextend -L 1.5G /dev/labvg/lab        # or -L +512M
sudo resize2fs /dev/labvg/lab                # ext4 grows online (xfs: xfs_growfs /mnt/...)
df -h /mnt/data
```

### 4. Out of inodes
> Every file needs an **inode**; a filesystem has a fixed number created at format time.
> Many tiny files can **exhaust inodes** while bytes remain free, so `df -h` shows space
> but `touch`/`create` fails with "No space left on device." Diagnose with:
> ```bash
> df -i        # IUse% near 100% = out of inodes
> ```
> Fix by deleting small files (e.g. mail spools, caches) or reformatting with more inodes.

### 5. Stretch — ext4 vs xfs
> - **ext4** — the long-standing Debian/Ubuntu default; mature, can be **grown and
>   shrunk**, great general-purpose choice.
> - **xfs** — the **RHEL default**; excellent for large files and parallel I/O, can be
>   **grown but not shrunk**. Pick xfs for big-data/throughput, ext4 for flexibility.
