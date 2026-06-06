# Challenge 01 — Reference Solution

### 1. Three-tier inventory
See [`inventory.ini`](./inventory.ini).
```bash
ansible-inventory -i inventory.ini --graph
ansible-inventory -i inventory.ini --list | python3 -m json.tool | head -30
ansible web -i inventory.ini -m debug -a "var=http_port"   # 8080 only on web hosts
```

### 2. Targeting patterns
```bash
ansible db                  -i inventory.ini --list-hosts     # (a) db only
ansible 'all:!lb'           -i inventory.ini --list-hosts     # (b) all except lb
ansible 'web:&staging'      -i inventory.ini --list-hosts     # (c) intersection
ansible 'web*'              -i inventory.ini --list-hosts     # (d) name wildcard
```

### 3. One-shot audit
```bash
ansible all -i inventory.ini -m setup -a 'filter=ansible_os_family,ansible_memtotal_mb'
```

### 4. Idempotent multi-package install
```bash
ansible web -i inventory.ini -m apt -a "name=curl,git state=present update_cache=true" --become
# run again -> reports 'ok' (already installed), not 'changed':
ansible web -i inventory.ini -m apt -a "name=curl,git state=present" --become
```
> The `apt` module accepts a list (`name=curl,git`). Because it manages **desired state**,
> the second run finds both already present and reports `ok` — idempotence.

### 5. command vs shell
```bash
ansible web -m command -a "systemctl is-active ssh"          # works: no shell features
ansible web -m shell   -a "cat /etc/passwd | wc -l"          # needs shell for the pipe '|'
```
> `command` runs the program directly with no shell, so `|`, `>`, `*`, `&&` are **not**
> interpreted (safer, avoids injection). Use `shell` only when you genuinely need those
> shell features.
