# Lab 09 — Disks, Filesystems & fstab

**You'll:** create a filesystem, mount it, persist it, and try LVM + swap — using
**loop devices** so you need no real spare disk. ⏱️ ~60 min. In your VM (uses `sudo`).

> A **loop device** turns a regular file into a block device — perfect for safe practice.

---

## Part A — See your storage
```bash
lsblk -f
df -h
sudo fdisk -l 2>/dev/null | head -20
```

## Part B — Make a "disk" from a file
```bash
sudo mkdir -p /srv/disks
sudo fallocate -l 1G /srv/disks/disk1.img
sudo losetup -fP /srv/disks/disk1.img      # attach as a loop device
LOOP=$(losetup -j /srv/disks/disk1.img | cut -d: -f1)
echo "loop device is $LOOP"
lsblk "$LOOP"
```
✅ `$LOOP` (e.g. `/dev/loop8`) now behaves like a 1 GB disk.

## Part C — Partition, format, mount
```bash
sudo parted -s "$LOOP" mklabel gpt
sudo parted -s -a opt "$LOOP" mkpart primary ext4 0% 100%
sudo partprobe "$LOOP"; sleep 1
PART="${LOOP}p1"
sudo mkfs.ext4 -q "$PART"
sudo blkid "$PART"                          # note the UUID + TYPE=ext4

sudo mkdir -p /mnt/data
sudo mount "$PART" /mnt/data
df -h /mnt/data
echo "hello storage" | sudo tee /mnt/data/test.txt
```
✅ A real ext4 filesystem, mounted, holding a file.

## Part D — Persist in fstab (carefully)
```bash
UUID=$(sudo blkid -s UUID -o value "$PART")
echo "UUID=$UUID /mnt/data ext4 defaults,nofail 0 2" | sudo tee -a /etc/fstab
sudo umount /mnt/data
sudo mount -a                               # TEST the fstab entry without rebooting
df -h /mnt/data                             # mounted again, via fstab
```
✅ `mount -a` succeeded → the fstab line is valid. (`nofail` = don't block boot if the
disk is missing — wise for non-critical mounts.)

## Part E — LVM
```bash
# Make a second loop "disk":
sudo fallocate -l 1G /srv/disks/disk2.img
sudo losetup -fP /srv/disks/disk2.img
LOOP2=$(losetup -j /srv/disks/disk2.img | cut -d: -f1)

sudo umount /mnt/data 2>/dev/null
sudo pvcreate "$PART" "$LOOP2"              # (use whole loop2 as a PV)
sudo vgcreate labvg "$PART" "$LOOP2"
sudo vgdisplay labvg | grep 'VG Size'
sudo lvcreate -L 1200M -n lab labvg         # spans both PVs
sudo mkfs.ext4 -q /dev/labvg/lab
sudo mount /dev/labvg/lab /mnt/data
df -h /mnt/data                             # ~1.2G from two 1G disks combined
# Grow it live:
sudo lvextend -L +300M /dev/labvg/lab
sudo resize2fs /dev/labvg/lab
df -h /mnt/data                             # bigger, no unmount needed
```
✅ LVM pooled two disks and grew a volume online — the whole point of LVM.

## Part F — Swap
```bash
free -h
sudo fallocate -l 512M /swapfile && sudo chmod 600 /swapfile
sudo mkswap /swapfile && sudo swapon /swapfile
swapon --show; free -h
sudo swapoff /swapfile && sudo rm /swapfile
```

## Cleanup
```bash
sudo umount /mnt/data
sudo lvremove -y /dev/labvg/lab; sudo vgremove -y labvg; sudo pvremove -y "$PART" "$LOOP2"
# remove the fstab line you added, then:
sudo sed -i "\|/mnt/data|d" /etc/fstab
sudo losetup -d "$LOOP" "$LOOP2"
sudo rm -rf /srv/disks; sudo rmdir /mnt/data
```

## What you learned
- Loop devices for safe disk practice; `parted`/`mkfs`/`mount`.
- Persistent mounts via `/etc/fstab` with **UUIDs** + `nofail`, tested with `mount -a`.
- LVM (PV→VG→LV) and **online growth** with `lvextend` + `resize2fs`.
- Adding/removing swap.

➡️ **[challenge.md](./challenge.md)** then [Module 10](../10-networking/).
