# Lab 07 — Manage Packages

**You'll:** install, query, trace, and remove packages on Ubuntu (with RHEL equivalents
noted). ⏱️ ~45 min. In your VM.

---

## Part A — Refresh & explore
```bash
sudo apt update                 # refresh the index FIRST
apt list --upgradable | head    # what could be upgraded
apt search '^ncdu$'             # find a specific package
apt show htop                   # details before installing
```
> **RHEL:** `dnf check-update`, `dnf search ncdu`, `dnf info htop`.

## Part B — Install & use
```bash
sudo apt install -y tree htop ncdu
tree --version; htop --version; ncdu --version
which tree htop ncdu            # where they landed
```
✅ Three tools installed with dependencies resolved automatically.

## Part C — Query: what owns what
```bash
# Which package owns the 'tree' binary?
dpkg -S "$(which tree)"         # tree: /usr/bin/tree
# What files did 'htop' install?
dpkg -L htop | head
# Is a package installed?
dpkg -l | grep -E '\s(tree|htop)\s'
```
> **RHEL:** `rpm -qf $(which tree)`, `rpm -ql htop`, `rpm -qa | grep htop`.

## Part D — Install a local .deb (low-level)
```bash
# Download a package file without installing, then install it manually:
cd /tmp
apt download ncdu              # fetches ncdu_*.deb here (no root needed)
ls *.deb
sudo dpkg -i ncdu_*.deb        # low-level install
sudo apt install -f            # fix any missing deps (no-op if none)
```
✅ You installed from a file with `dpkg`, then let `apt` satisfy dependencies — exactly
the pattern for third-party `.deb`s.

## Part E — Inspect repositories
```bash
cat /etc/apt/sources.list | grep -v '^#' | grep -v '^$'
ls /etc/apt/sources.list.d/
ls /etc/apt/keyrings/ 2>/dev/null
```
> **RHEL:** `ls /etc/yum.repos.d/`, `cat /etc/yum.repos.d/*.repo`.

## Part F — Remove cleanly
```bash
sudo apt remove -y ncdu         # remove the binary (keeps configs)
sudo apt purge -y tree          # remove + configs
sudo apt autoremove -y          # drop now-orphaned dependencies
dpkg -l | grep -E '\s(tree|ncdu)\s' || echo "removed"
```

## Part G — See the history / a security update view
```bash
# Debian keeps logs:
grep -i "install " /var/log/dpkg.log | tail
# Simulate an upgrade without doing it:
apt upgrade --dry-run | head
```
> **RHEL:** `dnf history`, `dnf history undo <ID>` to roll back a transaction.

## What you learned
- `apt update` vs `upgrade`; `install`/`remove`/`purge`/`autoremove`.
- Query packages: which owns a file (`dpkg -S`), what's in a package (`dpkg -L`).
- Low-level install with `dpkg -i` + `apt install -f`.
- Where repos live; the RHEL `dnf`/`rpm` equivalents throughout.

➡️ **[challenge.md](./challenge.md)** then [Module 08](../08-systemd-and-services/).
