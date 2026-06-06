# Challenge 04 — Reference Solution

### 1. firewall role
`roles/firewall/defaults/main.yml`:
```yaml
firewall_allowed_ports:
  - 22
  - 80
```
`roles/firewall/tasks/main.yml`:
```yaml
- name: Install ufw
  ansible.builtin.apt: { name: ufw, state: present, update_cache: true }

- name: Default deny incoming
  community.general.ufw: { direction: incoming, policy: deny }

- name: Allow configured ports
  community.general.ufw:
    rule: allow
    port: "{{ item }}"
    proto: tcp
  loop: "{{ firewall_allowed_ports }}"

- name: Enable ufw
  community.general.ufw: { state: enabled }
```
Override per group:
```yaml
# group_vars/web.yml
firewall_allowed_ports: [22, 80, 443]
```

### 2. defaults vs vars
> Put **user-tunable** values in `defaults/main.yml` (`http_port`, `web_root`,
> `site_title`) so consumers can override them in `group_vars`/`-e` (defaults are lowest
> precedence). Put **internal constants** the user shouldn't change in `vars/main.yml`
> (e.g. `nginx_site_path: /etc/nginx/sites-available/site`) — `vars` has higher precedence,
> signaling "implementation detail."

### 3. Conditional monitoring role
`site.yml`:
```yaml
  roles:
    - common
    - firewall
    - webserver
    - role: monitoring
      when: enable_monitoring | default(false)
```
```bash
ansible-playbook site.yml                          # monitoring skipped
ansible-playbook site.yml -e enable_monitoring=true # monitoring runs
```

### 4. Dependency ordering
`roles/webserver/meta/main.yml`:
```yaml
dependencies:
  - role: firewall
```
> Now `firewall` runs before `webserver` automatically. In the output you'll see the
> firewall tasks complete before the nginx tasks, regardless of `site.yml` ordering.

### 5. Pinned requirements.yml
```yaml
collections:
  - name: community.general
    version: "8.6.0"
roles:
  - name: geerlingguy.nginx
    version: "3.1.4"
```
```bash
ansible-galaxy install -r requirements.yml
```
> **Pin versions** so builds are reproducible and a new upstream release can't silently
> change behavior or break your playbooks. Upgrade deliberately by bumping the pin and
> testing.
