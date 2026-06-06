# Lab 02 — Your First Playbook

**You'll:** write and run a playbook that installs and configures nginx, see idempotence
and handlers, and use check mode. ⏱️ ~60 min. Control node → `web` hosts.

> Files are in this module's `code/`. Adjust IPs in `inventory.ini`.

---

## Part A — Read the playbook
```bash
cd ansible-course/02-playbooks/code
cat site.yml
```
Trace the structure: one **play** (`hosts: web`, `become: true`), several **tasks**
(install → web root → homepage → config → enable site → service), and a **handler**
(`Reload nginx`) that two tasks `notify`.

## Part B — Syntax-check & dry run
```bash
ansible-playbook -i inventory.ini site.yml --syntax-check     # YAML/structure valid?
ansible-playbook -i inventory.ini site.yml --check --diff      # what WOULD change (no changes made)
```
✅ `--check --diff` previews every change (new files, configs) without touching the hosts.

## Part C — Run it
```bash
ansible-playbook -i inventory.ini site.yml
```
✅ Watch the run: tasks report **changed** (first time), the handler **Reload nginx** runs
because configs changed, and the **PLAY RECAP** shows `changed=N`.

Verify the result:
```bash
ansible web -i inventory.ini -a "curl -s -o /dev/null -w '%{http_code}\n' localhost" --become
# or from your control node, hit a host's IP:
curl -s http://<web01-ip> | grep -i ansible
```
✅ Each host serves your page (HTTP 200).

## Part D — Prove idempotence
```bash
ansible-playbook -i inventory.ini site.yml
```
✅ Expected: **every task `ok`, `changed=0`**, and the handler does **not** run (nothing
changed). The same playbook is safe to run any number of times.

## Part E — Make a change and watch the handler
Edit the page and re-run:
```bash
sed -i 's/🎉/✅ updated/' files/index.html
ansible-playbook -i inventory.ini site.yml
```
✅ Only the "Deploy the homepage" task reports `changed`; because it doesn't notify the
handler (only config tasks do), nginx isn't reloaded — copying HTML doesn't need a reload.
Now change the nginx config block in `site.yml` (e.g. add `server_tokens off;`) and re-run
→ the config task is `changed` and the **handler reloads nginx**.

## Part F — Targeted runs
```bash
ansible-playbook -i inventory.ini site.yml --limit web01
ansible-playbook -i inventory.ini site.yml --start-at-task "Configure the nginx site"
```

## Cleanup (optional)
```bash
ansible web -i inventory.ini -m apt -a "name=nginx state=absent purge=true" --become
ansible web -i inventory.ini -m file -a "path=/srv/www state=absent" --become
```

## What you learned
- Playbook structure: plays, tasks, `become`, handlers.
- `--syntax-check` and `--check --diff` for safe previews.
- **Idempotence** in the PLAY RECAP (changed → ok on re-run).
- Handlers firing only on change (and only once).

➡️ **[challenge.md](./challenge.md)** then [Module 03](../03-variables-facts-templates/).
