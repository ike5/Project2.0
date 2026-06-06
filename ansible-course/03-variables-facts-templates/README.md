# Module 03 — Variables, Facts & Templates

**Goal:** parameterize your automation — variables, host/group vars, auto-discovered
facts, and **Jinja2 templates** — plus loops and conditionals. ⏱️ ~3 h · 🎯 Prereq: 00–02.

> Templating reference: [cheatsheets/jinja2.md](../cheatsheets/jinja2.md).

---

## 1. Variables: many places to set them

```yaml
# In a play
- hosts: web
  vars:
    http_port: 8080
  vars_files:
    - vars/web.yml
  tasks:
    - debug: { msg: "port is {{ http_port }}" }
```
Other sources: inventory (`[web:vars]`), **`group_vars/<group>.yml`**,
**`host_vars/<host>.yml`** (auto-loaded by name), role defaults/vars, `register`, and the
CLI `-e`.

### Precedence (simplified, low → high)
role `defaults/` < inventory vars < `group_vars/` < `host_vars/` < play `vars` <
`register`ed < **`-e` extra vars** (always wins).
> Rule of thumb: put sane **defaults** low (role defaults), override per environment in
> `group_vars`/`host_vars`, and use `-e` for one-off overrides.

### group_vars / host_vars layout
```
inventory.ini
group_vars/
  all.yml          # applies to every host
  web.yml          # applies to the 'web' group
host_vars/
  web01.yml        # applies to web01 only
```

## 2. Facts (auto-discovered host data)

At the start of a play, Ansible **gathers facts** about each host — OS, IPs, CPUs,
memory, disks — available as variables:
```bash
ansible web -m setup                                  # see them all
ansible web -m setup -a 'filter=ansible_distribution*'
```
```yaml
- debug:
    msg: "{{ ansible_distribution }} {{ ansible_distribution_version }} on {{ ansible_default_ipv4.address }}"
```
Use facts to write portable automation:
```yaml
- name: Install the web server (any distro)
  ansible.builtin.package:
    name: "{{ 'nginx' }}"
    state: present
  when: ansible_os_family in ['Debian', 'RedHat']
```
Special vars: `inventory_hostname`, `ansible_hostname`, `groups`, `hostvars`,
`group_names`.

## 3. Jinja2 templates

The **`template`** module renders a `.j2` file (with `{{ }}` and `{% %}`) onto a host —
the right way to manage config files:
```jinja
# templates/site.conf.j2
server {
    listen {{ http_port | default(80) }} default_server;
    server_name {{ server_name | default(ansible_hostname) }};
    root {{ web_root }};
{% if enable_gzip | default(true) %}
    gzip on;
{% endif %}
}
```
```yaml
- name: Deploy nginx site config
  ansible.builtin.template:
    src: site.conf.j2
    dest: /etc/nginx/sites-available/site
  notify: Reload nginx
```
Templates can reference **other hosts** via `groups[...]` and `hostvars[...]` — e.g. a
load balancer that lists its backends (you'll do this in the capstone).

## 4. Loops

```yaml
- name: Install several packages
  ansible.builtin.apt:
    name: "{{ item }}"
    state: present
  loop:
    - nginx
    - curl
    - ufw

- name: Create several users
  ansible.builtin.user:
    name: "{{ item.name }}"
    groups: "{{ item.groups }}"
  loop:
    - { name: alice, groups: sudo }
    - { name: bob,   groups: devs }
```

## 5. Conditionals & registering results

```yaml
- name: Check if a file exists
  ansible.builtin.stat:
    path: /etc/app.conf
  register: appconf

- name: Create it if missing
  ansible.builtin.copy:
    dest: /etc/app.conf
    content: "defaults\n"
  when: not appconf.stat.exists
```

## 6. Tags

Label tasks to run subsets:
```yaml
- name: Install packages
  ansible.builtin.apt: { name: nginx, state: present }
  tags: [packages]
```
```bash
ansible-playbook site.yml --tags packages
ansible-playbook site.yml --skip-tags packages
```

---

## Do the lab
Drive a templated nginx config from variables/facts, add `group_vars`, and use loops +
conditionals. 👉 **[lab.md](./lab.md)**

Then: 👉 **[challenge.md](./challenge.md)**

## Code
[`code/site.yml`](./code/site.yml), [`code/templates/site.conf.j2`](./code/templates/site.conf.j2),
[`code/group_vars/web.yml`](./code/group_vars/web.yml), [`code/inventory.ini`](./code/inventory.ini).

## Key terms
variable sources & **precedence** · `group_vars`/`host_vars` · facts/`setup`/
`ansible_*` · `inventory_hostname`/`groups`/`hostvars` · Jinja2 `template` module · filters
(`default`, `join`) · `loop` · `when:` · `register`/`stat` · tags

**Next →** [Module 04: Roles & Reuse](../04-roles/)
