# Lab 05 — Vault & Quality

**You'll:** encrypt a secret with Vault, use it in a template, and run quality checks.
⏱️ ~50 min. Run from `code/`.

---

## Part A — Create an encrypted vault file
```bash
cd ansible-course/05-vault-best-practices/code
cp group_vars/all/vault.yml.example group_vars/all/vault.yml
ansible-vault encrypt group_vars/all/vault.yml      # set a vault password (remember it!)
head -1 group_vars/all/vault.yml                     # $ANSIBLE_VAULT;1.1;AES256
```
✅ `vault.yml` is now ciphertext. `vars.yml` (plain) references `vault_db_password` from it.

## Part B — View/edit safely
```bash
ansible-vault view group_vars/all/vault.yml          # prompts for the password, shows plaintext
ansible-vault edit group_vars/all/vault.yml          # opens decrypted in your editor, re-encrypts on save
```
✅ You never have plaintext on disk; Vault decrypts only in memory.

## Part C — Run a playbook that uses the secret
```bash
ansible-playbook site.yml --ask-vault-pass           # enter the vault password
ansible web -i inventory.ini -a "cat /etc/myapp.env" --become   # the rendered env file (mode 0640)
```
✅ The template pulled `db_password` (→ `vault_db_password`) and wrote `/etc/myapp.env`
with `0640` perms. The debug task printed only the **length**, never the secret.

> To avoid typing the password each run, put it in a file and `chmod 600`:
> ```bash
> echo 'yourvaultpass' > ~/.vault_pass && chmod 600 ~/.vault_pass
> ansible-playbook site.yml --vault-password-file ~/.vault_pass
> ```

## Part D — Encrypt a single variable (inline)
```bash
ansible-vault encrypt_string 'another-secret' --name 'api_key'
# paste the !vault block into a vars file to keep most of the file readable
```

## Part E — Quality checks
```bash
ansible-playbook site.yml --syntax-check
ansible-playbook site.yml --check --diff --ask-vault-pass    # dry run (note: check + vault)
# Lint (install once): pipx install ansible-lint   OR  pip install --user ansible-lint
ansible-lint site.yml 2>/dev/null || echo "(install ansible-lint to run this)"
```

## Part F — Idempotence test
```bash
ansible-playbook site.yml --ask-vault-pass           # run 1
ansible-playbook site.yml --ask-vault-pass           # run 2 -> changed=0 (idempotent)
```
✅ The template only rewrites if content changes; a second run is `changed=0`.

## Cleanup
```bash
ansible web -i inventory.ini -m file -a "path=/etc/myapp.env state=absent" --become
```

## What you learned
- Encrypt secrets with `ansible-vault` (file and inline `encrypt_string`).
- Reference vaulted vars from plain `group_vars`; run with `--ask-vault-pass`/file.
- `--syntax-check`, `--check --diff`, `ansible-lint`, and the idempotence test.
- Restrict secret-bearing files (`mode: 0640`) and never print secrets.

➡️ **[challenge.md](./challenge.md)** then the [Capstone](../06-capstone/).
