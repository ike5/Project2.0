# Module 09 — Storage & Filesystems

**Goal:** partition disks, create and mount filesystems, make mounts persistent, and use
LVM and swap. ⏱️ ~3 h · 🎯 Prereq: 00–08.

> 🧪 You'll attach a **spare virtual disk** so you can partition safely:
> `multipass stop lab` then (or simply create a fresh disk file and attach via your
> hypervisor). The lab shows a loop-device alternative that needs no extra disk.

---

## 1. Block devices

Disks and partitions are **block devices** under `/dev`:
```bash
lsblk                      # tree of disks/partitions + mountpoints + sizes
lsblk -f                   # + filesystem type and UUID
sudo fdisk -l              # detailed partition tables
ls -l /dev/sd* /dev/vd* /dev/nvme* 2>/dev/null
```
Naming: `/dev/sda` (first SATA/SCSI disk), `sda1` (its first partition); `/dev/vda`
(virtio, common in VMs); `/dev/nvme0n1` / `nvme0n1p1` (NVMe).

## 2. Partitioning

A disk holds a **partition table** (**MBR**, max 2 TB / 4 primary; or **GPT**, modern,
huge, many partitions).
```bash
sudo fdisk /dev/sdb        # interactive: n new, p print, d delete, t type, w write
sudo parted /dev/sdb       # scriptable; good for GPT
sudo parted /dev/sdb mklabel gpt
sudo parted -a opt /dev/sdb mkpart primary ext4 0% 100%
```

## 3. Filesystems

A partition needs a **filesystem** before it stores files. Common: **ext4** (default),
**xfs** (RHEL default), **btrfs**, **vfat** (EFI/USB).
```bash
sudo mkfs.ext4 /dev/sdb1          # make an ext4 filesystem
sudo mkfs.xfs  /dev/sdb1          # or xfs
sudo blkid /dev/sdb1             # show its UUID + type
sudo e2label /dev/sdb1 data      # set a label (ext);  xfs_admin -L for xfs
```

## 4. Mounting

```bash
sudo mkdir /mnt/data
sudo mount /dev/sdb1 /mnt/data    # attach the filesystem at a mountpoint
df -h /mnt/data                   # space usage
mount | grep sdb1                 # mount options in effect
sudo umount /mnt/data             # detach
```

## 5. Persistent mounts: /etc/fstab

Mounts done with `mount` vanish on reboot. **`/etc/fstab`** makes them permanent:
```
# device              mountpoint   type   options          dump  pass
UUID=xxxx-xxxx        /mnt/data    ext4   defaults         0     2
```
```bash
echo "UUID=$(sudo blkid -s UUID -o value /dev/sdb1) /mnt/data ext4 defaults 0 2" | sudo tee -a /etc/fstab
sudo mount -a                     # mount everything in fstab (tests your entry!)
```
> ⚠️ Use **UUIDs** (stable), not `/dev/sdb1` (can change). A bad `fstab` can block boot —
> always `sudo mount -a` to test before rebooting.

## 6. Disk usage

```bash
df -h                 # free space per filesystem
df -i                 # inode usage (you can run out of inodes!)
du -sh /var/* 2>/dev/null | sort -h    # what's using space
ncdu /var             # interactive disk usage (great)
```

## 7. LVM (flexible volumes)

**LVM** lets you resize/combine storage without repartitioning. Layers:
**PV** (physical volume) → **VG** (volume group) → **LV** (logical volume).
```bash
sudo pvcreate /dev/sdb1 /dev/sdc1         # mark disks as PVs
sudo vgcreate datavg /dev/sdb1 /dev/sdc1  # pool them into a VG
sudo lvcreate -L 5G -n datalv datavg      # carve a 5G LV
sudo mkfs.ext4 /dev/datavg/datalv
sudo lvextend -L +2G /dev/datavg/datalv && sudo resize2fs /dev/datavg/datalv  # grow live
```

## 8. Swap

```bash
free -h                           # see swap
sudo fallocate -l 1G /swapfile && sudo chmod 600 /swapfile
sudo mkswap /swapfile && sudo swapon /swapfile
swapon --show
# persist: add to fstab:  /swapfile none swap sw 0 0
```

## 9. Checking filesystems

```bash
sudo umount /dev/sdb1
sudo fsck /dev/sdb1               # check & repair (unmounted!)  -- xfs uses xfs_repair
```

---

## Do the lab
Partition a spare disk (or a loop file), make a filesystem, mount it, persist it in fstab,
and try LVM + swap. 👉 **[lab.md](./lab.md)**

Then: 👉 **[challenge.md](./challenge.md)**

## Key terms
block device · `lsblk`/`blkid`/`fdisk`/`parted` · MBR vs GPT · filesystem (ext4/xfs) ·
`mkfs`/`mount`/`umount` · `/etc/fstab` + UUID · `df`/`du`/inodes · LVM (PV/VG/LV/
`lvextend`/`resize2fs`) · swap · `fsck`

**Next →** [Module 10: Networking](../10-networking/)
