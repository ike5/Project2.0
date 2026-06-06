# Debian vs RHEL Family Cheatsheet

The exams (and the real world) cover both families. Labs use **Ubuntu**; here's the
RHEL/Fedora equivalent for everything that differs.

## Families at a glance
| | Debian family | RHEL family |
|---|---------------|-------------|
| Examples | Debian, Ubuntu, Mint | RHEL, Rocky, Alma, Fedora, CentOS Stream |
| Package format | `.deb` | `.rpm` |
| Low-level tool | `dpkg` | `rpm` |
| High-level tool | `apt` | `dnf` (older: `yum`) |
| Firewall front-end | `ufw` | `firewalld` |
| Network config | `netplan` / NetworkManager | NetworkManager (`nmcli`) |
| Default MAC | AppArmor | SELinux |
| "admin" group | `sudo` | `wheel` |

## Packages
```bash
# Update metadata / upgrade
apt update && apt upgrade            # dnf upgrade        (dnf refreshes automatically)
# Install / remove
apt install nginx                    # dnf install nginx
apt remove nginx                     # dnf remove nginx
apt purge nginx                      # dnf remove nginx   (configs handled differently)
# Search / info
apt search word; apt show pkg        # dnf search word; dnf info pkg
# What package owns a file?
dpkg -S /bin/ls                      # rpm -qf /bin/ls
# List files in a package
dpkg -L coreutils                    # rpm -ql coreutils
# Installed list
dpkg -l                              # rpm -qa
# Install a local file
dpkg -i pkg.deb; apt install -f      # dnf install ./pkg.rpm  (or rpm -i)
```

## Services & firewall
```bash
# systemd is the same on both:
systemctl enable --now nginx

# Firewall (allow HTTP):
sudo ufw allow 80/tcp                          # Debian/Ubuntu
sudo firewall-cmd --add-service=http --permanent && sudo firewall-cmd --reload   # RHEL
```

## Network (show/set an address)
```bash
ip a                                  # same on both
# Persistent config:
#   Ubuntu: edit /etc/netplan/*.yaml then `sudo netplan apply`
#   RHEL:   nmcli con mod ... ;  nmcli con up ...
nmcli device status                   # NetworkManager (both, if installed)
```

## Users (small differences)
```bash
adduser sam        # Debian: interactive, friendly wrapper
useradd -m sam     # portable/low-level (both); -m makes home dir
usermod -aG sudo sam     # Debian admin group
usermod -aG wheel sam    # RHEL admin group
```

## Logs
```bash
journalctl -u nginx           # systemd journal (both)
# Text logs:
#   Debian: /var/log/syslog, /var/log/auth.log
#   RHEL:   /var/log/messages, /var/log/secure
```

## SELinux (RHEL) vs AppArmor (Ubuntu)
```bash
# RHEL — SELinux
getenforce; sudo setenforce 0          # Permissive (temporary)
sestatus; ls -Z; restorecon -Rv /path
# Ubuntu — AppArmor
sudo aa-status; sudo aa-complain /etc/apparmor.d/usr.sbin.nginx
```

> Rule of thumb: **systemd, the shell, files, permissions, and most coreutils are
> identical** across families. Differences cluster around **packaging, firewall, network
> config, and MAC (SELinux/AppArmor)**.
