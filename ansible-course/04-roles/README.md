# Module 04 — Roles & Reuse

**Goal:** package your automation into reusable **roles** — the standard way to organize
Ansible — and pull in community roles/collections from Galaxy. ⏱️ ~3 h · 🎯 Prereq: 00–03.

---

## 1. Why roles

As playbooks grow, a single file becomes unwieldy. A **role** is a standardized directory
of tasks, handlers, templates, files, defaults, and variables that you can drop into any
playbook and share. Roles make automation **modular, reusable, and testable**.

## 2. Role directory structure

```
roles/
  webserver/
    tasks/main.yml        # the tasks (entry point)
    handlers/main.yml     # handlers
    templates/            # Jinja2 .j2 files (template: src is relative to here)
    files/                # static files (copy: src is relative to here)
    defaults/main.yml     # default variables (LOWEST precedence — easy to override)
    vars/main.yml         # role variables (higher precedence than defaults)
    meta/main.yml         # metadata + role dependencies
    handlers/  templates/  files/  ...
```
Create the skeleton with:
```bash
ansible-galaxy role init roles/webserver
```

## 3. Using a role

```yaml
# site.yml
- name: Web tier
  hosts: web
  become: true
  roles:
    - webserver
```
Or with variables / conditionally:
```yaml
  roles:
    - role: webserver
      vars:
        http_port: 8080
```
You can also include roles dynamically in `tasks:` with `include_role` / `import_role`.

## 4. defaults vs vars (precedence)

- **`defaults/main.yml`** — sensible defaults; **lowest** precedence, so users override
  them easily in `group_vars`, play `vars`, or `-e`. Put most tunables here.
- **`vars/main.yml`** — role-internal values you don't expect users to change; higher
  precedence.

```yaml
# roles/webserver/defaults/main.yml
http_port: 80
web_root: /srv/www/site
enable_gzip: true
```

## 5. tasks/main.yml (the body)

```yaml
# roles/webserver/tasks/main.yml
- name: Install nginx
  ansible.builtin.apt: { name: nginx, state: present, update_cache: true }

- name: Deploy site config
  ansible.builtin.template:
    src: site.conf.j2                 # resolves to roles/webserver/templates/site.conf.j2
    dest: /etc/nginx/sites-available/site
  notify: Reload nginx

- name: nginx running
  ansible.builtin.service: { name: nginx, state: started, enabled: true }
```
Paths in `template:`/`copy:` are **relative to the role's** `templates/`/`files/` — no
need to spell out the path.

## 6. meta & dependencies

```yaml
# roles/webserver/meta/main.yml
dependencies:
  - role: common          # runs 'common' before this role
galaxy_info:
  author: you
  description: An nginx web server role
```

## 7. Ansible Galaxy (community roles & collections)

```bash
# Roles:
ansible-galaxy role install geerlingguy.nginx
ansible-galaxy role list
# Collections (modules/plugins):
ansible-galaxy collection install community.general ansible.posix
```
Pin dependencies in `requirements.yml`:
```yaml
roles:
  - name: geerlingguy.nginx
    version: "3.1.4"
collections:
  - name: community.general
```
```bash
ansible-galaxy install -r requirements.yml
```
> Vet third-party roles before using them in production (read the tasks). Well-known
> authors (e.g. geerlingguy) are widely used and reviewed.

## 8. A multi-role playbook

```yaml
- name: Full stack
  hosts: web
  become: true
  roles:
    - common         # base hardening/packages
    - webserver      # nginx + site
    - { role: monitoring, when: enable_monitoring | default(false) }
```

---

## Do the lab
Refactor the Module 03 playbook into a `webserver` role, add a `common` base role, and use
both from a site playbook. 👉 **[lab.md](./lab.md)**

Then: 👉 **[challenge.md](./challenge.md)**

## Code
A complete role under [`code/roles/webserver/`](./code/roles/) plus
[`code/site.yml`](./code/site.yml) and [`code/inventory.ini`](./code/inventory.ini).

## Key terms
role · `tasks`/`handlers`/`templates`/`files`/`defaults`/`vars`/`meta` ·
`ansible-galaxy role init` · `defaults` vs `vars` precedence · role path resolution ·
`roles:` vs `import_role`/`include_role` · `meta` dependencies · Galaxy roles/collections ·
`requirements.yml`

**Next →** [Module 05: Vault, Testing & Best Practices](../05-vault-best-practices/)
