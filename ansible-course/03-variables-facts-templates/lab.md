# Lab 03 — Variables, Facts & Templates

**You'll:** drive a templated nginx config from `group_vars` and facts, with loops and a
custom homepage. ⏱️ ~55 min. Control node → `web` hosts.

> The `code/` folder has `group_vars/web.yml`, `templates/*.j2`, and `site.yml`. Run from
> `code/` so `group_vars/` auto-loads.

---

## Part A — See variables resolve
```bash
cd ansible-course/03-variables-facts-templates/code
ansible web -i inventory.ini -m debug -a "var=http_port"      # 8080 (from group_vars/web.yml)
ansible web -i inventory.ini -m debug -a "var=web_root"
ansible web -i inventory.ini -e "http_port=9999" -m debug -a "var=http_port"   # -e overrides -> 9999
```
✅ `group_vars/web.yml` supplies values; `-e` wins (precedence).

## Part B — Explore facts
```bash
ansible web01 -i inventory.ini -m setup -a 'filter=ansible_distribution*'
ansible web01 -i inventory.ini -m setup -a 'filter=ansible_default_ipv4'
ansible web01 -i inventory.ini -m setup -a 'filter=ansible_memtotal_mb'
```

## Part C — Run the templated playbook
```bash
ansible-playbook -i inventory.ini site.yml --check --diff      # preview the rendered files
ansible-playbook -i inventory.ini site.yml
```
✅ The `template` tasks render `site.conf.j2` and `index.html.j2` **per host** (each gets
its own hostname/IP/distro substituted). Confirm:
```bash
curl -s http://<web01-ip> | grep -E 'Served by|port'
ansible web -i inventory.ini -a "head -3 /etc/nginx/sites-available/site" --become
```
Each host's page shows **its own** hostname/distro — same template, different facts.

## Part D — Change a variable, re-render
```bash
sed -i 's/Templated by Ansible/My Cool Site/' group_vars/web.yml
ansible-playbook -i inventory.ini site.yml
curl -s http://<web01-ip> | grep '<h1>'        # new title
```
✅ Changing the variable re-rendered the template (the template task reports `changed`).

## Part E — Per-host override with host_vars
```bash
mkdir -p host_vars
echo "http_port: 8888" > host_vars/web01.yml
ansible-playbook -i inventory.ini site.yml --limit web01
ansible web01 -i inventory.ini -a "grep listen /etc/nginx/sites-available/site" --become   # 8888
ansible web02 -i inventory.ini -a "grep listen /etc/nginx/sites-available/site" --become   # 8080
```
✅ `host_vars/web01.yml` overrode the group value **only for web01** (precedence again).

## Part F — Loops & conditionals (quick)
```bash
ansible web -i inventory.ini -m debug -a "msg={{ groups['web'] }}"    # the group as a list
ansible-playbook -i inventory.ini site.yml --tags packages           # only the looped install
```

## What you learned
- Variable sources and **precedence** (`group_vars` < `host_vars` < `-e`).
- Facts (`ansible_*`) and using them in templates/conditionals.
- The `template` module rendering per-host config + a homepage with Jinja2.
- `loop`, tags, and per-host overrides.

➡️ **[challenge.md](./challenge.md)** then [Module 04](../04-roles/).
