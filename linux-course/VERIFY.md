# End-to-End Verification

Confirm your lab environment works. You need a **Linux machine to practice on** — a VM on
your Mac is ideal so you can break things safely.

## 1. You have a Linux box
On macOS, the quickest path is **Multipass** (Module 00 covers install):
```bash
multipass launch --name lab 22.04        # an Ubuntu 22.04 LTS VM
multipass shell lab                       # drop into it
```
✅ You're now at a shell prompt *inside Linux* (`ubuntu@lab:~$`).

## 2. The basics respond
Inside the VM:
```bash
uname -a              # Linux ... x86_64/aarch64
whoami; id            # ubuntu; uid=1000(ubuntu) ...
cat /etc/os-release   # PRETTY_NAME="Ubuntu 22.04..."
ls -la /              # the root filesystem
sudo -v               # confirms you can use sudo
```
✅ Each prints sensible output and `sudo` works without error.

## 3. Package manager works
```bash
sudo apt update
sudo apt install -y tree htop
tree --version; htop --version
```
✅ Packages install and run.

## 4. systemd is present
```bash
systemctl is-system-running        # 'running' or 'degraded' (both fine for labs)
systemctl status ssh               # a unit's status
journalctl -n 5                    # last 5 log lines
```
✅ `systemctl`/`journalctl` respond.

## 5. A second box (for the later modules)
Some modules (SSH, and the separate Ansible course) want **two** machines:
```bash
multipass launch --name web 22.04
multipass list                      # both 'lab' and 'web' Running, with IPs
```
✅ Two VMs listed. You can `multipass shell web` into the second.

## Cleanup between sessions
```bash
multipass stop lab web      # free RAM
multipass start lab         # resume later
multipass delete lab; multipass purge   # remove for good
```

---

🎉 **All green?** You're ready. Start with [Module 01: The Shell & Command Line](./01-shell-command-line/)
(or [Module 00](./00-setup/) for the full setup walkthrough).

> **No Multipass / different OS?** Any Ubuntu (or RHEL-family) machine works: a cloud VM,
> VirtualBox/UTM, WSL2 on Windows, or a spare PC. The course commands are the same; only
> the *getting-a-VM* step differs.
