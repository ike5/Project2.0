# Glossary

Plain-English definitions of the terms in this course.

## Shell & system

- **Kernel** — the core of the OS that talks to hardware and manages processes, memory,
  and devices. "Linux" technically *is* the kernel.
- **Distribution (distro)** — the kernel + tools + package manager bundled together
  (Ubuntu, Debian, Fedora, RHEL, …).
- **Shell** — the program that reads your commands and runs them. Default is usually
  **bash**; **zsh** and others exist.
- **Terminal / TTY** — the text interface where the shell runs.
- **Prompt** — the text the shell shows when waiting for input (often ending in `$` for a
  normal user, `#` for root).
- **Command / argument / option (flag)** — `ls -l /etc`: `ls` is the command, `-l` an
  option, `/etc` an argument.
- **PATH** — the list of directories the shell searches for commands.
- **Environment variable** — a named value available to programs (e.g. `HOME`, `PATH`).
- **Standard streams** — **stdin** (input, fd 0), **stdout** (output, fd 1), **stderr**
  (errors, fd 2).
- **Pipe (`|`)** — sends one command's stdout into the next command's stdin.
- **Redirection** — `>` (stdout to file), `>>` (append), `<` (file to stdin),
  `2>` (stderr).
- **Glob / wildcard** — shell pattern matching for filenames (`*`, `?`, `[...]`).
- **Exit status** — a command's result code: `0` = success, non-zero = failure (`$?`).

## Filesystem

- **FHS (Filesystem Hierarchy Standard)** — the conventional layout (`/etc`, `/var`,
  `/usr`, `/home`, …).
- **Root directory (`/`)** — the top of the single unified file tree.
- **Path** — absolute (from `/`) or relative (from the current directory).
- **Inode** — the on-disk structure holding a file's metadata (owner, perms, size,
  pointers to data) — *not* the filename.
- **Hard link** — another name for the same inode/data. **Symbolic (soft) link** — a
  pointer to a path (like a shortcut).
- **Mount** — attaching a filesystem (on a device) into the tree at a directory
  (mount point).

## Users & permissions

- **root** — the all-powerful superuser (UID 0).
- **UID / GID** — numeric user / group IDs.
- **`/etc/passwd`, `/etc/shadow`, `/etc/group`** — account, password-hash, and group databases.
- **Permissions** — read/write/execute (`rwx`) for **owner / group / other**.
- **`chmod` / `chown`** — change permission bits / ownership.
- **`umask`** — bits removed from default permissions on new files.
- **setuid / setgid / sticky bit** — special permission bits (run-as-owner / run-as-group
  or inherit-group / restrict-deletion).
- **sudo** — run a command as another user (usually root) per a policy in `/etc/sudoers`.

## Processes

- **Process** — a running program instance, identified by a **PID**.
- **Parent/child / PPID** — processes form a tree; `init`/`systemd` (PID 1) is the root.
- **Signal** — an async notification to a process (`SIGTERM` 15 = polite stop,
  `SIGKILL` 9 = force, `SIGHUP` 1 = reload).
- **Foreground / background / job** — shell job control (`&`, `fg`, `bg`, `jobs`).
- **Daemon** — a long-running background service (often named `*d`, e.g. `sshd`).
- **niceness** — scheduling priority hint (`nice`/`renice`).

## Packages

- **Package** — a bundled, installable piece of software + metadata.
- **Package manager** — installs/updates/removes packages and resolves dependencies:
  **apt/dpkg** (Debian/Ubuntu), **dnf/rpm** (RHEL/Fedora).
- **Repository (repo)** — a server of packages the manager pulls from.
- **Dependency** — a package another package needs.

## Boot & services

- **BIOS/UEFI → bootloader (GRUB) → kernel → init** — the boot chain.
- **init system** — PID 1 that starts everything; modern Linux uses **systemd**.
- **systemd unit** — a managed object: `.service`, `.timer`, `.mount`, `.target`, …
- **`systemctl`** — control units (start/stop/enable/status).
- **target** — a systemd grouping of units (roughly replaces SysV "runlevels").
- **journald / `journalctl`** — systemd's binary logging system and its query tool.

## Storage

- **Block device** — a disk or partition (`/dev/sda`, `/dev/nvme0n1`).
- **Partition** — a slice of a disk (MBR or GPT partition table).
- **Filesystem** — structure for storing files on a device (ext4, xfs, btrfs).
- **`/etc/fstab`** — the table of filesystems to mount at boot.
- **LVM** — Logical Volume Manager: flexible volumes on top of physical disks (PV → VG → LV).
- **Swap** — disk space used as overflow for RAM.

## Networking

- **IP address / subnet / CIDR** — host address + network size (`192.168.1.10/24`).
- **Gateway / route** — where to send packets not on the local network.
- **DNS** — name → IP resolution (`/etc/resolv.conf`, `/etc/hosts`).
- **Port / socket** — a numbered endpoint on a host; a socket is an active connection.
- **`ip` / `ss`** — modern tools for addresses/routes / sockets (replacing `ifconfig`/`netstat`).
- **Firewall** — packet filtering: **ufw** (Ubuntu front-end), **firewalld** (RHEL),
  **nftables/iptables** (underneath).

## Scheduling, logging, security

- **cron / crontab** — time-based job scheduler. **systemd timer** — the modern alternative.
- **`rsync`** — efficient file sync/backup tool.
- **logrotate** — rotates/compresses/expires log files.
- **SSH** — secure remote shell; **key-based auth** uses a keypair instead of passwords.
- **SELinux / AppArmor** — mandatory access control (extra security layers).
- **fail2ban** — bans IPs after repeated failed logins.

## Containers (the "and more")

- **Namespace / cgroup** — kernel features that isolate (namespace) and limit (cgroup)
  processes — the basis of containers.
- **Container** — an isolated process tree with its own filesystem view; **Docker** /
  **Podman** run them.
