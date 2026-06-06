# Module 00 — Setup & First Contact

**Goal:** install Ansible on a control node, prepare managed hosts, write your first
inventory, and confirm connectivity. ⏱️ ~1 h.

---

## 1. The model (recap)

- **Control node** — where Ansible runs (your Mac or a Linux box). Needs Python 3.
- **Managed nodes** — the servers you automate. They need only **sshd + Python 3** (no
  Ansible installed there).
- Ansible connects over **SSH** (using your keys), ships modules, runs them, and reports.

## 2. Install Ansible (control node)

**macOS:**
```bash
brew install ansible           # or: pipx install ansible
ansible --version
```
**Linux (control node):**
```bash
sudo apt update && sudo apt install -y ansible          # Debian/Ubuntu
# or: python3 -m pip install --user ansible
sudo dnf install -y ansible-core                          # RHEL/Fedora
```

## 3. Prepare managed hosts

Easiest: two Ubuntu VMs with **Multipass** (on a Mac):
```bash
brew install --cask multipass
multipass launch --name web01 22.04
multipass launch --name web02 22.04
multipass list                 # note their IPs
```
> Any SSH-reachable Linux works: cloud VMs, a home server, or Docker/Podman containers.

### SSH key access (Ansible authenticates as you)
From your control node:
```bash
ssh-keygen -t ed25519 -C ansible      # if you don't already have a key
# install your public key on each host (set a temp password first if needed):
ssh-copy-id ubuntu@<web01-ip>
ssh-copy-id ubuntu@<web02-ip>
ssh ubuntu@<web01-ip> 'echo ok'        # confirm passwordless login
```
> Multipass tip: `multipass exec web01 -- bash -c 'echo "<your-pubkey>" >> ~/.ssh/authorized_keys'`
> avoids needing a password.

## 4. Write your first inventory

`inventory.ini` ([code/inventory.ini](./code/inventory.ini)):
```ini
[web]
web01 ansible_host=192.168.64.11
web02 ansible_host=192.168.64.12

[web:vars]
ansible_user=ubuntu
```
Replace the IPs with yours (`multipass list`). Inspect it:
```bash
ansible-inventory -i inventory.ini --graph
```

## 5. A project config (optional but nice)

`ansible.cfg` ([code/ansible.cfg](./code/ansible.cfg)) sets defaults so you can drop the
`-i` flag and avoid host-key prompts in the lab:
```ini
[defaults]
inventory = ./inventory.ini
remote_user = ubuntu
host_key_checking = False
```

## 6. First contact

```bash
cd ansible-course/00-setup/code
ansible all -m ping                          # uses inventory.ini via ansible.cfg
ansible web -a "uptime"                       # an ad-hoc command on the web group
ansible all -m setup -a 'filter=ansible_distribution*'   # gather a fact
```
✅ Expected: each host returns `SUCCESS => {"ping": "pong"}`, then uptime, then its
distribution. **You're now managing servers with Ansible.**

## 7. Verify

Run the full [../VERIFY.md](../VERIFY.md).

---

## Troubleshooting
- **`UNREACHABLE ... Permission denied`** → SSH key not installed / wrong `ansible_user`.
  Test plain `ssh ubuntu@host` first.
- **`/usr/bin/python3: not found`** → install Python on the managed host
  (`apt install -y python3`); modern Ubuntu has it by default.
- **Host key prompt blocks runs** → set `host_key_checking = False` in `ansible.cfg`
  (lab only) or pre-accept keys.

---

**Next →** [Module 01: Inventory & Ad-Hoc Commands](../01-inventory-adhoc/)
