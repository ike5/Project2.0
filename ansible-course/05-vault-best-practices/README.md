# Module 05 — Vault, Testing & Best Practices

**Goal:** handle secrets safely with **Ansible Vault**, check quality with `--check` and
**ansible-lint**, and structure a project the professional way. ⏱️ ~2.5 h · 🎯 Prereq: 00–04.

---

## 1. Secrets do not belong in plaintext

Database passwords, API keys, TLS keys — never commit them in cleartext. **Ansible
Vault** encrypts files or individual variables at rest; Ansible decrypts them at run time
with a password.

```bash
ansible-vault create secrets.yml        # create a new encrypted file (opens editor)
ansible-vault edit secrets.yml          # edit it
ansible-vault view secrets.yml          # view without editing
ansible-vault encrypt vars/prod.yml     # encrypt an existing file
ansible-vault decrypt vars/prod.yml     # decrypt (careful!)
ansible-vault rekey secrets.yml         # change the vault password
```
A vaulted file looks like:
```
$ANSIBLE_VAULT;1.1;AES256
38396166383...   (ciphertext)
```

### Encrypt a single variable (inline)
```bash
ansible-vault encrypt_string 's3cr3t' --name 'db_password'
# paste the output into a vars file:
db_password: !vault |
  $ANSIBLE_VAULT;1.1;AES256
  6133...
```

### Run playbooks that use vaulted data
```bash
ansible-playbook site.yml --ask-vault-pass               # prompt for the password
ansible-playbook site.yml --vault-password-file ~/.vault_pass   # read from a file (chmod 600!)
```
Store secrets in `group_vars/<group>/vault.yml` (encrypted) alongside a plain `vars.yml`,
and reference the vaulted vars from the plain ones — a common, tidy pattern.

## 2. Best-practice project layout

```
project/
├── ansible.cfg
├── inventory/
│   ├── prod.ini
│   └── staging.ini
├── group_vars/
│   ├── all/        vars.yml  vault.yml      # plain + encrypted, auto-merged
│   └── web/        vars.yml  vault.yml
├── host_vars/
├── roles/
│   ├── common/
│   └── webserver/
├── requirements.yml
└── site.yml
```
- Separate **inventories** per environment (`prod`, `staging`).
- `group_vars/<group>/` as a **directory** lets you split plain `vars.yml` and encrypted
  `vault.yml`.
- Keep playbooks thin; put logic in **roles**.

## 3. Quality: check mode, lint, idempotence

```bash
ansible-playbook site.yml --syntax-check        # YAML/structure valid
ansible-playbook site.yml --check --diff        # dry run + show changes
ansible-lint                                     # style + correctness (install via pip/pipx)
ansible-lint site.yml roles/
```
**Idempotence test:** run the playbook twice; the second run must be `changed=0`. If a
task is `changed` every time, it's not idempotent (often a `command`/`shell` missing
`creates:`/`changed_when:`).

> **Molecule** (advanced) automates role testing: spin up a container, converge the role,
> assert idempotence, and tear down — great for CI. Beyond this course's scope, but know
> it exists.

## 4. Writing robust tasks

```yaml
- name: Run a one-off only when needed
  ansible.builtin.command: /opt/app/migrate.sh
  args:
    creates: /var/lib/app/migrated         # idempotence guard
  changed_when: false                       # or define when it counts as changed
  register: migrate
  failed_when: migrate.rc not in [0, 2]     # custom failure logic

- name: Validate before applying (handlers can validate too)
  ansible.builtin.template:
    src: nginx.conf.j2
    dest: /etc/nginx/nginx.conf
    validate: "nginx -t -c %s"               # only writes if the config is valid
```
Other good habits: always `name:` tasks; prefer modules over `shell`; use FQCN
(`ansible.builtin.apt`); keep secrets in Vault; tag for selective runs; pin Galaxy deps.

## 5. The professional workflow

```
edit roles/playbooks  →  ansible-lint  →  --syntax-check  →  --check --diff (staging)
   →  apply to staging  →  run twice (idempotent?)  →  apply to prod
```
Everything lives in **git**; changes are PR-reviewed; secrets are vaulted; CI runs lint +
a check.

---

## Do the lab
Vault a secret, wire it into a template, and run quality checks. 👉 **[lab.md](./lab.md)**

Then: 👉 **[challenge.md](./challenge.md)**

## Code
[`code/site.yml`](./code/site.yml), [`code/group_vars/`](./code/group_vars/) (plain +
vault placeholder), [`code/templates/app.env.j2`](./code/templates/app.env.j2).

## Key terms
Ansible Vault (`create`/`edit`/`view`/`encrypt`/`rekey`/`encrypt_string`) ·
`--ask-vault-pass`/`--vault-password-file` · `group_vars/<g>/vault.yml` · project layout ·
inventories per env · `--syntax-check`/`--check`/`ansible-lint` · idempotence test ·
`creates`/`changed_when`/`failed_when`/`validate` · Molecule

**Next →** [Module 06: Capstone — Multi-Host Deploy](../06-capstone/)
