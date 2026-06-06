# End-to-End Verification

Confirm your Ansible control node can reach and manage your hosts.

## 1. Ansible is installed (control node)
```bash
ansible --version            # ansible-core 2.16+, with a Python 3 interpreter
ansible-playbook --version
```
✅ Versions print. (Install steps are in [Module 00](./00-setup/).)

## 2. An inventory exists
```bash
cd ansible-course/00-setup/code
ansible-inventory -i inventory.ini --graph
```
✅ Expected: your groups and hosts, e.g.
```
@all:
  |--@web:
  |  |--web01
  |--@ungrouped:
```

## 3. Connectivity: the ping module
```bash
ansible all -i inventory.ini -m ping
```
✅ Expected: each host returns
```
web01 | SUCCESS => { "changed": false, "ping": "pong" }
```
> `ping` here is Ansible's module (SSH + Python check), **not** ICMP ping. If it fails,
> see the SSH/Python notes in [Module 00](./00-setup/).

## 4. Gather a fact
```bash
ansible all -i inventory.ini -m setup -a 'filter=ansible_distribution*'
```
✅ Returns each host's OS distribution and version — Ansible can introspect the hosts.

## 5. Run a trivial playbook (dry run, then real)
```bash
cd ../../01-inventory-adhoc/code 2>/dev/null || cd ../00-setup/code
ansible-playbook -i inventory.ini ../../02-playbooks/code/site.yml --check --diff
ansible-playbook -i inventory.ini ../../02-playbooks/code/site.yml
```
✅ `--check` shows what *would* change; the real run applies it. Re-running it reports
**all `ok`, 0 changed** — that's **idempotence**, the heartbeat of Ansible.

---

🎉 **All green?** Your control node manages your hosts. Begin with
[Module 01](./01-inventory-adhoc/).

> **No hosts yet?** Module 00 shows how to create two Ubuntu VMs with Multipass (or use
> cloud servers / containers) and wire up SSH key access.
