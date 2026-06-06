# Challenge 05 — Reference Solution

### 1. Per-environment secrets
```
inventory/
  staging.ini       # [web] hosts...
  prod.ini
group_vars/
  all/
    vars.yml        # db_password: "{{ vault_db_password }}"
    vault.yml       # encrypted; vault_db_password: <staging value>
```
Use separate var dirs per env, or separate vault files and pass with `-e @`:
```bash
ansible-playbook -i inventory/staging.ini site.yml --ask-vault-pass
ansible-playbook -i inventory/prod.ini    site.yml --ask-vault-pass
```
> A clean pattern: `inventory/staging/group_vars/all/vault.yml` and
> `inventory/prod/group_vars/all/vault.yml` — each environment carries its own encrypted
> secrets, selected by which inventory you run.

### 2. Inline-encrypt a key
```bash
ansible-vault encrypt_string 'sk-live-abc123' --name 'api_key'
```
Paste into `group_vars/all/vars.yml`:
```yaml
app_env: production
api_key: !vault |
  $ANSIBLE_VAULT;1.1;AES256
  6532...
```
> The file stays human-readable except the one encrypted value — nice for diffs/reviews.

### 3. Idempotence fixes
```yaml
# (a) never reports changed (it's a log append; not a state change):
- ansible.builtin.shell: "echo $(date) >> /var/log/deploy.log"
  changed_when: false

# (b) run exactly once, then never again:
- ansible.builtin.shell: "echo $(date) > /var/log/deploy.stamp"
  args:
    creates: /var/log/deploy.stamp
```

### 4. Lint findings & fixes
> - **Missing `name:` on a task** → add a descriptive `name:` (readability + logs).
> - **Using `shell`/`command` where a module exists** → use `ansible.builtin.copy`/
>   `lineinfile`/`apt` etc. for idempotence.
> - **Not using FQCN** (`apt:` vs `ansible.builtin.apt:`) → use fully-qualified module
>   names to avoid ambiguity across collections.
> (Others: trailing whitespace, `become` at the wrong scope, unquoted octal `mode`.)

### 5. Safe rollout sequence
```bash
ansible-playbook site.yml --syntax-check
ansible-lint site.yml roles/
ansible-playbook -i inventory/staging.ini site.yml --check --diff --ask-vault-pass
ansible-playbook -i inventory/staging.ini site.yml --ask-vault-pass
ansible-playbook -i inventory/staging.ini site.yml --ask-vault-pass   # run twice -> changed=0
ansible-playbook -i inventory/prod.ini    site.yml --check --diff --ask-vault-pass
ansible-playbook -i inventory/prod.ini    site.yml --ask-vault-pass
```
