# Module 02 — Playbooks, Tasks & Idempotence

**Goal:** write **playbooks** — reusable YAML that describes desired state — with tasks,
handlers, and idempotence, and verify them safely with check mode. ⏱️ ~3 h · 🎯 Prereq: 00–01.

---

## 1. From ad-hoc to playbook

Ad-hoc commands are one-offs. A **playbook** captures a whole configuration as a
reviewable, repeatable YAML file. A playbook has one or more **plays**; each play maps a
**host pattern** to a list of **tasks**.

```yaml
- name: Configure web servers          # a PLAY
  hosts: web
  become: true                         # run tasks as root (sudo)
  tasks:
    - name: Install nginx              # a TASK (a module + args + name)
      ansible.builtin.apt:
        name: nginx
        state: present
        update_cache: true

    - name: Ensure nginx is running and enabled
      ansible.builtin.service:
        name: nginx
        state: started
        enabled: true
```
Run it:
```bash
ansible-playbook -i inventory.ini site.yml
```

## 2. YAML, briefly

- Indentation (2 spaces) defines structure; **no tabs**.
- `key: value` mappings; `- item` lists.
- Strings usually don't need quotes; quote when they contain `:` or `{{ }}`.
- `name:` every play and task — it's your readable log.

## 3. Idempotence (the core idea)

Each module aims to reach a **desired state**, changing things only when needed and
reporting:
- **ok** — already in the desired state (no change).
- **changed** — the module made a change.
- **failed** — something went wrong.

Run a playbook twice: the first run shows `changed`, the second shows **all `ok`,
0 changed**. That's how you know it's safe to run repeatedly — the heart of Ansible.

```
PLAY RECAP
web01 : ok=4  changed=2  unreachable=0  failed=0     <- first run
web01 : ok=4  changed=0  unreachable=0  failed=0     <- second run (idempotent!)
```

## 4. Handlers (run on change, once)

A **handler** is a task that runs only when **notified** — and only **once**, at the end
of the play. Perfect for "restart the service if its config changed":
```yaml
  tasks:
    - name: Deploy nginx config
      ansible.builtin.template:
        src: site.conf.j2
        dest: /etc/nginx/sites-available/site
      notify: Reload nginx          # fires the handler IF this task changed something

  handlers:
    - name: Reload nginx
      ansible.builtin.service:
        name: nginx
        state: reloaded
```
If the template didn't change, the handler doesn't run — no needless restart.

## 5. Check mode & diff (dry runs)

```bash
ansible-playbook site.yml --check          # report what WOULD change; change nothing
ansible-playbook site.yml --check --diff   # + show the line-level differences
ansible-playbook site.yml --diff           # apply, and show what changed
```
Always `--check --diff` a risky playbook first.

## 6. Common modules you'll use constantly

| Goal | Module |
|------|--------|
| Packages | `ansible.builtin.apt` / `dnf` / `package` (auto-detects) |
| Services | `ansible.builtin.service` / `systemd` |
| Files/dirs/perms | `ansible.builtin.file` |
| Copy a file | `ansible.builtin.copy` |
| Render a template | `ansible.builtin.template` |
| Ensure a line | `ansible.builtin.lineinfile` |
| Users/groups | `ansible.builtin.user` / `group` |
| Run a command | `ansible.builtin.command` (idempotent with `creates:`) |

> Use real modules over `command`/`shell` so you keep idempotence and change-reporting.
> When you must use `command`, add `creates:`/`removes:` or `changed_when:` to control it.

## 7. Controlling execution

```bash
ansible-playbook site.yml --limit web01     # one host
ansible-playbook site.yml --start-at-task "Deploy nginx config"
ansible-playbook site.yml --step            # confirm each task
ansible-playbook site.yml -v                # verbose (-vvv to debug)
```

---

## Do the lab
Write and run a playbook that installs and configures nginx, with a handler and check
mode. 👉 **[lab.md](./lab.md)**

Then: 👉 **[challenge.md](./challenge.md)**

## Code
[`code/site.yml`](./code/site.yml) (nginx play), [`code/inventory.ini`](./code/inventory.ini),
[`code/files/index.html`](./code/files/index.html).

## Key terms
playbook/play/task · YAML · module · idempotence (ok/changed/failed) · PLAY RECAP ·
handler/`notify` · `--check`/`--diff` · `become` · `ansible.builtin.*` modules ·
`--limit`/`--start-at-task`/`--step`

**Next →** [Module 03: Variables, Facts & Templates](../03-variables-facts-templates/)
