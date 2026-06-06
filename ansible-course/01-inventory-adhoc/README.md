# Module 01 — Inventory & Ad-Hoc Commands

**Goal:** organize your hosts into groups and run one-off tasks across them with ad-hoc
commands — the fastest way to *do* something with Ansible. ⏱️ ~1.5 h · 🎯 Prereq: 00.

---

## 1. Inventory: who Ansible manages

The **inventory** lists hosts and groups. INI or YAML; both express the same thing.

**INI:**
```ini
[web]
web01 ansible_host=10.0.0.11
web02 ansible_host=10.0.0.12

[db]
db01 ansible_host=10.0.0.21

[prod:children]        # a group made of other groups
web
db

[web:vars]             # variables for everyone in [web]
http_port=80
```
**YAML:**
```yaml
all:
  children:
    web:
      hosts:
        web01: { ansible_host: 10.0.0.11 }
        web02: { ansible_host: 10.0.0.12 }
      vars: { http_port: 80 }
    db:
      hosts:
        db01: { ansible_host: 10.0.0.21 }
```
Built-in groups: **`all`** (every host) and **`ungrouped`**. Inspect with:
```bash
ansible-inventory -i inventory.ini --graph
ansible-inventory -i inventory.ini --list           # full JSON (vars resolved)
```

## 2. Host patterns (targeting)

```bash
ansible all -m ping
ansible web -m ping                 # a group
ansible web01 -m ping               # one host
ansible 'web:db' -m ping            # union of groups
ansible 'web:!web02' -m ping        # web EXCEPT web02
ansible 'web:&prod' -m ping         # intersection
ansible 'web*' -m ping              # wildcard
```

## 3. Ad-hoc commands

An **ad-hoc command** runs a single **module** without a playbook — great for quick
checks and one-time changes.
```bash
ansible <pattern> -m <module> -a "<args>" [--become]
```
Examples:
```bash
ansible all -m ping                                   # connectivity
ansible web -m command -a "uptime"                    # run a command (no shell features)
ansible web -m shell -a "ps aux | grep nginx"         # shell (pipes/globs work)
ansible web -m setup                                   # gather all facts
ansible web -m apt -a "name=htop state=present" --become      # install (needs root)
ansible web -m service -a "name=nginx state=started" --become # start a service
ansible web -m copy -a "src=./f dest=/tmp/f" --become         # push a file
ansible web -m file -a "path=/tmp/d state=directory mode=0755" --become
ansible web -m user -a "name=deploy state=present" --become
```
> `command` vs `shell`: `command` does **not** use a shell (no `|`, `>`, `*`) — safer.
> Use `shell` only when you need shell features.

## 4. `--become` (privilege escalation)

Most system changes need root. Add `--become` (sudo) to ad-hoc commands, or `become:
true` in playbooks. `-K` (`--ask-become-pass`) prompts for the sudo password if needed.

## 5. Why modules beat raw commands

Modules are **idempotent** and report **changed vs ok**:
```bash
ansible web -m apt -a "name=htop state=present" --become   # first run: changed
ansible web -m apt -a "name=htop state=present" --become   # again: ok (already present)
```
A raw `command: apt install htop` would run every time and always report "changed". Ansible
modules describe **desired state**, not steps.

## 6. Useful diagnostics

```bash
ansible all -m ping -o                # one line per host (terse)
ansible all -m setup -a 'filter=ansible_mem*'   # only memory facts
ansible web --list-hosts              # which hosts a pattern matches
ansible-doc apt                       # what a module accepts
```

---

## Do the lab
Build a grouped inventory and drive your hosts with ad-hoc commands (install, copy,
service, facts). 👉 **[lab.md](./lab.md)**

Then: 👉 **[challenge.md](./challenge.md)**

## Code
[`code/inventory.ini`](./code/inventory.ini), [`code/inventory.yml`](./code/inventory.yml).

## Key terms
inventory (INI/YAML) · group/`children`/`all`/`ungrouped` · group vars · host pattern
(`:`/`!`/`&`/`*`) · ad-hoc command · module · `command` vs `shell` · `--become`/`-K` ·
idempotence (changed vs ok) · `ansible-inventory`/`ansible-doc`

**Next →** [Module 02: Playbooks, Tasks & Idempotence](../02-playbooks/)
