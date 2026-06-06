# Challenge 03 — Reference Solution

### 1. Per-environment precedence
`group_vars/all.yml`:
```yaml
worker_processes: 1
```
`group_vars/web.yml`:
```yaml
worker_processes: 4
```
```bash
ansible web        -m debug -a "var=worker_processes"   # 4 (web overrides all)
ansible ungrouped  -m debug -a "var=worker_processes"   # 1 (only all applies)
```
> More specific group (`web`) beats `all`; `host_vars` would beat both; `-e` beats everything.

### 2. Fact-driven branch
```yaml
- name: Install web server (Debian family)
  ansible.builtin.apt: { name: nginx, state: present, update_cache: true }
  when: ansible_os_family == "Debian"

- name: Install web server (RedHat family)
  ansible.builtin.dnf: { name: nginx, state: present }
  when: ansible_os_family == "RedHat"

- name: Start nginx (both)
  ansible.builtin.service: { name: nginx, state: started, enabled: true }
  when: ansible_os_family in ["Debian", "RedHat"]
```

### 3. motd.j2
```jinja
{{ site_title | default('Managed Host') }}
========================================
host : {{ ansible_hostname }}
os   : {{ ansible_distribution }} {{ ansible_distribution_version }}
ip   : {{ ansible_default_ipv4.address | default('n/a') }}
cpus : {{ ansible_processor_vcpus }}
mem  : {{ ansible_memtotal_mb }} MB
```
```yaml
- ansible.builtin.template:
    src: motd.j2
    dest: /etc/motd
    mode: "0644"
```

### 4. Loops
```yaml
- name: Create users
  ansible.builtin.user:
    name: "{{ item.name }}"
    groups: "{{ item.groups }}"
    append: true
  loop:
    - { name: alice, groups: sudo }
    - { name: bob,   groups: adm }
    - { name: carol, groups: users }

- name: Allow firewall ports
  community.general.ufw:
    rule: allow
    port: "{{ item }}"
    proto: tcp
  loop: [22, 80, 443]
```

### 5. Stretch — peer IPs from a template
```jinja
upstream backends {
{% for host in groups['web'] %}
    server {{ hostvars[host].ansible_default_ipv4.address }}:{{ hostvars[host].http_port | default(80) }};
{% endfor %}
}
```
> `groups['web']` is the list of hosts in the group; `hostvars[host]` exposes another
> host's facts/vars. This renders a backend list — exactly what a load-balancer config
> needs (capstone).
