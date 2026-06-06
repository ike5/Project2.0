# Capstone — Reference Walkthrough

The complete project is in [`../code/`](../code/). Try to build it from the brief first;
use this to check yourself.

## Layout
```
code/
├── ansible.cfg            # inventory + roles_path
├── inventory.ini          # [web] app01 app02 ; [lb] proxy01
├── group_vars/all.yml     # app_port, lb_port, app_name
├── site.yml               # 2 plays: app tier, lb tier
└── roles/
    ├── common/            # base packages + default-deny ufw (all hosts)
    ├── app/               # nginx on app_port + identifying homepage (web group)
    └── loadbalancer/      # nginx reverse proxy; upstream from groups['web'] (lb group)
```

## The key idea: a fact-driven load balancer
`roles/loadbalancer/templates/lb.conf.j2` builds its upstream list from the inventory:
```jinja
upstream app_backends {
{% for host in groups['web'] %}
    server {{ hostvars[host].ansible_default_ipv4.address }}:{{ app_port }};
{% endfor %}
}
```
- `groups['web']` — the app hosts from the inventory.
- `hostvars[host].ansible_default_ipv4.address` — each app host's IP (a **fact**).

So the proxy config is **derived from the inventory + facts**. Add `app03` to `[web]`,
re-run, and the upstream regenerates automatically — zero manual edits. This is the payoff
of variables + facts + templates + roles together.

## Run & verify
```bash
cd ../code
ansible-galaxy collection install community.general
ansible-playbook site.yml --check --diff
ansible-playbook site.yml

# Round-robin check:
for i in $(seq 6); do curl -s http://<proxy01-ip>/ | grep -o 'backend <strong>[^<]*'; done

# Idempotence:
ansible-playbook site.yml        # changed=0
```

## Why this mirrors the by-hand build
Everything here — install nginx, configure sites, open firewall ports, enable services,
generate config from peers — is exactly what you'd otherwise SSH in and do **by hand on
each box**. Ansible captures it once, applies it consistently to N hosts, and re-runs
safely. That's the whole point: **infrastructure as code**.

## Common pitfalls
- **`community.general.ufw` not found** → `ansible-galaxy collection install community.general`.
- **LB shows only one backend** → facts weren't gathered for the `web` hosts in this run;
  ensure both plays run (or set `gather_facts: true`), or run `site.yml` whole so
  `hostvars` is populated for the `web` group.
- **Not idempotent** → check for `shell`/`command` tasks lacking `creates:`/`changed_when:`.
