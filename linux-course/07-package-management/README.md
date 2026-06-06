# Module 07 — Package Management

**Goal:** install, update, query, and remove software the right way — on both the
Debian/Ubuntu (`apt`) and RHEL/Fedora (`dnf`) families. ⏱️ ~2 h · 🎯 Prereq: 00–06.

> Cross-reference: [cheatsheets/distro-differences.md](../cheatsheets/distro-differences.md).

---

## 1. Why a package manager

Software comes as **packages**: an archive of files + metadata + dependency info. The
**package manager** installs them, resolves **dependencies**, tracks what's installed, and
updates/removes cleanly — far better than copying files by hand. Packages come from
**repositories** (repos) the manager trusts.

Two layers per family:
- **Low-level** (`dpkg`, `rpm`) — operate on a single package file; *don't* resolve deps.
- **High-level** (`apt`, `dnf`) — talk to repos, resolve deps, and call the low-level tool.

## 2. Debian/Ubuntu: apt & dpkg

```bash
sudo apt update                 # refresh the package index (do this first)
sudo apt upgrade                # upgrade installed packages
sudo apt install nginx          # install (+ dependencies)
sudo apt remove nginx           # remove (keep config files)
sudo apt purge nginx            # remove + config files
sudo apt autoremove             # remove now-unused dependencies
apt search keyword              # find packages
apt show nginx                  # details (version, deps, description)
apt list --installed            # what's installed
```
Low-level `dpkg` (single `.deb`, queries):
```bash
sudo dpkg -i pkg.deb            # install a local file (then `apt install -f` for deps)
dpkg -l                         # list installed
dpkg -L nginx                   # files a package installed
dpkg -S /usr/sbin/nginx         # which package owns a file
```

## 3. RHEL/Fedora: dnf & rpm

```bash
sudo dnf install nginx          # install (index refresh is automatic)
sudo dnf upgrade                # update everything
sudo dnf remove nginx           # remove
dnf search keyword              # find
dnf info nginx                  # details
dnf list installed              # installed
dnf history                     # transaction history (and `dnf history undo N`)
```
Low-level `rpm`:
```bash
sudo rpm -i pkg.rpm             # install a local file (no dep resolution)
rpm -qa                         # list installed
rpm -ql nginx                   # files in a package
rpm -qf /usr/sbin/nginx         # which package owns a file
```

## 4. Repositories

- Debian: `/etc/apt/sources.list` and `/etc/apt/sources.list.d/*.list`; keys under
  `/etc/apt/keyrings`. Add a PPA: `sudo add-apt-repository ppa:foo/bar`.
- RHEL: `/etc/yum.repos.d/*.repo`; enable extras like **EPEL**:
  `sudo dnf install epel-release`.

After changing repos: `apt update` (Debian) — dnf refreshes automatically.

## 5. Other ways software arrives

- **Snap** (`snap install`) / **Flatpak** (`flatpak install`) — self-contained, sandboxed
  app bundles (cross-distro).
- **Language managers** — `pip` (Python), `npm` (Node), `cargo` (Rust) — for libraries/CLI
  tools within an ecosystem.
- **Tarballs / from source** — download, extract, build:
  ```bash
  tar -xzf app-1.2.tar.gz && cd app-1.2
  ./configure && make && sudo make install     # classic build
  ```
  Use the package manager when you can — source installs aren't tracked/updated for you.

## 6. Keeping a system current

```bash
sudo apt update && sudo apt upgrade -y          # Debian/Ubuntu
sudo dnf upgrade -y                              # RHEL/Fedora
# Security-only / unattended upgrades exist (unattended-upgrades / dnf-automatic).
```

---

## Do the lab
Install/query/remove packages, find which package owns a file, and inspect repos.
👉 **[lab.md](./lab.md)**

Then: 👉 **[challenge.md](./challenge.md)**

## Key terms
package · dependency · repository · high-level (`apt`/`dnf`) vs low-level (`dpkg`/`rpm`) ·
`update` vs `upgrade` · `install`/`remove`/`purge`/`autoremove` · `-S`/`-qf` (owns file) ·
`-L`/`-ql` (files in pkg) · PPA/EPEL · snap/flatpak · build from source

**Next →** [Module 08: Boot, systemd & Services](../08-systemd-and-services/)
