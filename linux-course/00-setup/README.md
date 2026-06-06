# Module 00 — Setup & Orientation

**Goal:** get a real Linux machine you can practice (and break) on, and get oriented in
the shell. ⏱️ ~45 min.

---

## 1. Why a VM?

Linux administration means changing real system state — users, services, disks,
firewalls. You want a **disposable** machine so mistakes cost nothing. On a Mac, the
fastest route is **Multipass** (lightweight Ubuntu VMs). You'll often want **two** VMs
later (for SSH and the Ansible course).

> Alternatives that work identically: a cloud VM (AWS/DigitalOcean), VirtualBox/UTM,
> WSL2 (Windows), or a spare machine. Pick what you have — the rest of the course is the
> same.

## 2. Install Multipass (macOS)

```bash
brew install --cask multipass
multipass version
```

## 3. Launch your lab VM

```bash
multipass launch --name lab 22.04        # Ubuntu 22.04 LTS (use 24.04 if you prefer)
multipass list                            # see it Running with an IP
multipass shell lab                       # enter it
```
You're now inside Linux as user `ubuntu` with passwordless `sudo`. To leave, type
`exit` (the VM keeps running).

> Give the VM more resources if needed:
> `multipass launch --name lab --cpus 2 --memory 2G --disk 10G 22.04`.

## 4. Orient yourself

Inside the VM:
```bash
whoami                 # ubuntu
id                     # your uid + group memberships
hostname               # the machine name
uname -a               # kernel + architecture
cat /etc/os-release    # which distro/version
pwd                    # where am I (/home/ubuntu)
ls -la                 # what's here (including dotfiles)
```

### The prompt
```
ubuntu@lab:~$
└┬───┘ └┬┘ │└ $ = normal user   (# = root)
 user   host └ ~ = current dir (home)
```

### The two families
This course uses **Ubuntu** (Debian family: `apt`). Every module has **RHEL-family**
call-outs (`dnf`/`firewalld`/SELinux) so you're ready for either — see
[cheatsheets/distro-differences.md](../cheatsheets/distro-differences.md).

## 5. Get comfortable getting help

You'll never memorize everything — you'll look it up:
```bash
man ls            # full manual (q to quit, / to search, n next match)
ls --help         # quick usage summary
apropos user      # find man pages about "user"
type cd           # what kind of thing is this command?
```

## 6. A safety habit

Before destructive commands, **look first**:
```bash
ls some/path           # before rm -rf some/path
cp file file.bak       # before editing an important file
sudo cmd --dry-run     # if the tool supports it
```
The VM makes mistakes cheap — but build the habit now.

## 7. Verify

Run the full [../VERIFY.md](../VERIFY.md) smoke test. When it's green, continue.

---

## Troubleshooting
- **`multipass launch` is slow the first time** — it downloads the image; later launches
  are fast.
- **Can't `multipass shell`** — `multipass start lab` first; check `multipass list`.
- **On Apple Silicon** — Multipass uses the ARM image automatically; everything in the
  course works on both architectures.

---

**Next →** [Module 01: The Shell & Command Line](../01-shell-command-line/)
