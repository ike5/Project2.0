# Challenge 07 — Reference Solution

### 1. Trace a binary
```bash
# Debian/Ubuntu
dpkg -S "$(which dig)"          # dnsutils: /usr/bin/dig
# RHEL/Fedora
rpm -qf "$(which dig)"          # bind-utils-...
```

### 2. Files & config of openssh-server
```bash
# Debian
dpkg -L openssh-server                 # all files
dpkg -L openssh-server | grep '^/etc'  # just config
# RHEL
rpm -ql openssh-server
rpm -qc openssh-server                 # config files specifically
```

### 3. update vs upgrade
> - **`apt update`** refreshes the *package index* (the list of available packages and
>   versions from the repos). It installs nothing.
> - **`apt upgrade`** actually downloads and installs newer versions of installed packages.
>
> After a fresh boot/image, your local index may be stale or empty, so `apt install foo`
> can fail with "Unable to locate package" or fetch errors until you `apt update` first.
> (`dnf` refreshes its metadata automatically, so this is a Debian-family gotcha.)

### 4. remove vs purge
> - **`apt remove nginx`** deletes the package's program files but **keeps configuration
>   files** (like your edited `/etc/nginx/nginx.conf`) so a reinstall preserves settings.
> - **`apt purge nginx`** removes the package **and** its config files.
>
> Use `remove` to keep your config; `purge` for a clean slate. (`dnf remove` removes
> package-owned configs but typically leaves files you modified as `.rpmsave`.)

### 5. Repos
```bash
# RHEL family — EPEL (Extra Packages for Enterprise Linux)
sudo dnf install -y epel-release
# Ubuntu — a PPA
sudo add-apt-repository ppa:owner/name && sudo apt update
```
> **Caution:** third-party repos can override system packages, ship unvetted updates, or
> go stale/unmaintained — risking stability and security on production servers. Prefer
> official repos; pin/limit third-party repos and audit what they provide.

### 6. Stretch — from a tarball
```bash
curl -LO https://example.com/tool-1.4.tar.gz
tar -xzf tool-1.4.tar.gz && cd tool-1.4
./configure && make && sudo make install     # or: copy a prebuilt binary into /usr/local/bin
```
> A package-manager install is preferable because it's **tracked** (you can list/verify/
> remove it), **updated** with the rest of the system (including security fixes), and
> **dependency-managed**. Source/tarball installs are invisible to the package DB and you
> must maintain them by hand.
