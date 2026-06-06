# Ansible Cheatsheet

## CLI
```bash
ansible --version
ansible all -m ping -i inventory.ini        # connectivity test (ping module)
ansible all -m setup                          # dump all facts about hosts
ansible web -a "uptime"                       # ad-hoc shell-ish command (command module)
ansible web -m apt -a "name=nginx state=present" --become   # ad-hoc with become

ansible-playbook site.yml -i inventory.ini    # run a playbook
ansible-playbook site.yml --check --diff      # dry run + show changes
ansible-playbook site.yml --tags nginx        # only tasks tagged 'nginx'
ansible-playbook site.yml --limit web01       # only this host
ansible-playbook site.yml -e "version=2.0"    # extra var (highest precedence)
ansible-playbook site.yml -v                  # verbose (-vvv for more)

ansible-inventory -i inventory.ini --graph    # show groups/hosts
ansible-inventory -i inventory.ini --list     # full inventory as JSON
ansible-doc apt                               # module documentation
ansible-doc -l | head                         # list modules
```

## Inventory (INI)
```ini
[web]
web01 ansible_host=192.168.50.11
web02 ansible_host=192.168.50.12

[db]
db01 ansible_host=192.168.50.21

[prod:children]      # a group of groups
web
db

[web:vars]
http_port=80
```

## Inventory (YAML)
```yaml
all:
  children:
    web:
      hosts:
        web01: { ansible_host: 192.168.50.11 }
        web02: { ansible_host: 192.168.50.12 }
      vars:
        http_port: 80
    db:
      hosts:
        db01: { ansible_host: 192.168.50.21 }
```

## Playbook skeleton
```yaml
- name: Configure web servers
  hosts: web
  become: true                     # use sudo
  vars:
    package: nginx
  tasks:
    - name: Install the web server
      ansible.builtin.apt:
        name: "{{ package }}"
        state: present
        update_cache: true
      notify: Restart web

    - name: Deploy the site config
      ansible.builtin.template:
        src: site.conf.j2
        dest: /etc/nginx/sites-available/site
      notify: Restart web

  handlers:
    - name: Restart web
      ansible.builtin.service:
        name: nginx
        state: restarted
```

## Common modules (FQCN = fully qualified)
| Task | Module |
|------|--------|
| Install package | `ansible.builtin.apt` / `ansible.builtin.dnf` / `ansible.builtin.package` |
| Manage service | `ansible.builtin.service` / `ansible.builtin.systemd` |
| Copy a file | `ansible.builtin.copy` |
| Render a template | `ansible.builtin.template` |
| Ensure a line | `ansible.builtin.lineinfile` |
| Edit blocks | `ansible.builtin.blockinfile` |
| Create user/group | `ansible.builtin.user` / `ansible.builtin.group` |
| Files/dirs/perms | `ansible.builtin.file` |
| Run a command | `ansible.builtin.command` (no shell) / `ansible.builtin.shell` |
| Get a URL | `ansible.builtin.get_url` |
| Git checkout | `ansible.builtin.git` |
| Unarchive | `ansible.builtin.unarchive` |
| cron job | `ansible.builtin.cron` |

> Prefer purpose-built modules over `command`/`shell` — they're **idempotent** and report
> changes. Use `command`/`shell` only when no module fits (and add `changed_when`/
> `creates` to control idempotence).

## Task features
```yaml
- name: Conditional + loop + register
  ansible.builtin.apt:
    name: "{{ item }}"
    state: present
  loop: [nginx, curl, ufw]
  when: ansible_os_family == "Debian"
  register: pkg_result
  tags: [packages]

- name: Use a registered result
  ansible.builtin.debug:
    msg: "changed={{ pkg_result.changed }}"
```

## Privilege escalation (become)
```yaml
become: true                 # per play or per task
become_user: postgres        # become a specific user
# CLI: --become / --become-user / --ask-become-pass (-K)
```

## ansible.cfg (project defaults)
```ini
[defaults]
inventory = ./inventory.ini
remote_user = ubuntu
host_key_checking = False
roles_path = ./roles
[privilege_escalation]
become = True
```
