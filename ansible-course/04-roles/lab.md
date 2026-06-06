# Lab 04 — Refactor into Roles

**You'll:** turn the Module 03 playbook into reusable roles and run a clean,
role-composed site playbook. ⏱️ ~60 min. Run from `code/` (its `ansible.cfg` sets
`roles_path`).

---

## Part A — Tour the role layout
```bash
cd ansible-course/04-roles/code
find roles -type f
```
✅ Two roles: `common` (base packages + motd) and `webserver` (nginx + templated site).
Note `webserver/defaults/main.yml` (overridable vars), `tasks/main.yml` (body),
`templates/` (Jinja2), `handlers/main.yml`, and `meta/main.yml` (depends on `common`).

## Part B — Scaffold a role yourself
```bash
ansible-galaxy role init roles/scratch
tree roles/scratch 2>/dev/null || find roles/scratch
rm -rf roles/scratch          # just seeing the skeleton
```
✅ `ansible-galaxy role init` generates the standard directory structure for you.

## Part C — Run the role-based site playbook
```bash
ansible-playbook site.yml --check --diff       # uses inventory.ini + roles_path from ansible.cfg
ansible-playbook site.yml
```
✅ The play is just `roles: [common, webserver]` — all logic lives in the roles. Because
`webserver/meta` depends on `common`, ordering is handled even if you forget it. Verify:
```bash
curl -s http://<web01-ip> | grep '<h1>'        # "Built from roles" (overridden in site.yml)
ansible web -a "head -2 /etc/motd" --become     # common role's motd
```

## Part D — Override defaults cleanly
The role defaults `http_port: 80`. Override per group without touching the role:
```bash
mkdir -p group_vars
echo "http_port: 8080" > group_vars/web.yml
ansible-playbook site.yml
ansible web -a "grep listen /etc/nginx/sites-available/site" --become   # 8080
```
✅ `group_vars` beats role `defaults` — you reconfigure without editing the role. That's
the point of `defaults/`.

## Part E — Idempotence holds
```bash
ansible-playbook site.yml          # second run -> changed=0
```

## Part F — Galaxy (collections/roles)
```bash
cat requirements.yml
ansible-galaxy install -r requirements.yml      # installs community.general, ansible.posix
ansible-galaxy collection list | head
# (optional) a community role:
# ansible-galaxy role install geerlingguy.nginx && ansible-galaxy role list
```

## What you learned
- The role directory structure and `ansible-galaxy role init`.
- Composing a site from roles (`roles: [...]`), with `meta` dependencies.
- `defaults/` vs `vars/` and overriding defaults via `group_vars`.
- Installing community roles/collections from Galaxy via `requirements.yml`.

➡️ **[challenge.md](./challenge.md)** then [Module 05](../05-vault-best-practices/).
