# Lab 01 — Inventory & Ad-Hoc

**You'll:** build a grouped inventory and drive hosts with ad-hoc commands. ⏱️ ~45 min.
Run on your control node; targets are your managed hosts.

> Adjust the IPs in `code/inventory.ini` to match `multipass list`.

---

## Part A — Inspect the inventory
```bash
cd ansible-course/01-inventory-adhoc/code
ansible-inventory -i inventory.ini --graph
ansible-inventory -i inventory.yml  --graph     # same result, YAML form
ansible web -i inventory.ini --list-hosts        # which hosts are in 'web'
ansible 'prod:!proxy01' -i inventory.ini --list-hosts
```
✅ You see `web`, `lb`, and `prod` (children web+lb), and can target subsets with patterns.

## Part B — Connectivity & facts
```bash
ansible all -i inventory.ini -m ping
ansible all -i inventory.ini -m ping -o          # one line per host
ansible web -i inventory.ini -m setup -a 'filter=ansible_distribution*'
ansible web -i inventory.ini -m setup -a 'filter=ansible_default_ipv4'
```
✅ All hosts return `pong`; you can introspect OS and IP facts.

## Part C — Ad-hoc commands (read-only)
```bash
ansible web -i inventory.ini -a "uptime"                 # command module (default)
ansible web -i inventory.ini -m command -a "df -h /"
ansible web -i inventory.ini -m shell -a "ps aux | grep -c sshd"   # shell needed for the pipe
```

## Part D — Ad-hoc changes (with --become)
```bash
# Install a package (idempotent):
ansible web -i inventory.ini -m apt -a "name=htop state=present update_cache=true" --become
# Run it again — note 'ok' instead of 'changed':
ansible web -i inventory.ini -m apt -a "name=htop state=present" --become
# Push a file:
echo "managed by ansible" > motd.txt
ansible web -i inventory.ini -m copy -a "src=motd.txt dest=/etc/motd" --become
ansible web -i inventory.ini -a "cat /etc/motd"
# Ensure a directory + a service:
ansible web -i inventory.ini -m file -a "path=/srv/app state=directory mode=0755" --become
ansible web -i inventory.ini -m service -a "name=ssh state=started enabled=true" --become
```
✅ **Watch the colors/words:** first install = `CHANGED`; the second = `ok`. That's
idempotence — the same command is safe to repeat.

## Part E — Targeting practice
```bash
ansible 'web:&prod' -i inventory.ini -m ping     # intersection
ansible 'all:!web02'  -i inventory.ini --list-hosts
ansible 'web*'       -i inventory.ini --list-hosts
```

## Cleanup
```bash
ansible web -i inventory.ini -m apt -a "name=htop state=absent" --become
ansible web -i inventory.ini -m file -a "path=/srv/app state=absent" --become
rm -f motd.txt
```

## What you learned
- Build/inspect inventories (INI & YAML); groups, children, `all`/`ungrouped`.
- Host patterns (`:`, `!`, `&`, `*`) to target subsets.
- Ad-hoc commands with modules (`ping`/`command`/`shell`/`apt`/`copy`/`file`/`service`).
- `--become` for root; **idempotence** (changed vs ok) firsthand.

➡️ **[challenge.md](./challenge.md)** then [Module 02](../02-playbooks/).
