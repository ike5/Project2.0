# Challenge 05 — Secrets & Quality

Solutions in [`solutions/`](./solutions/). Try first.

## Tasks
1. **Per-environment secrets.** Restructure into `inventory/staging.ini` and
   `inventory/prod.ini` with `group_vars/all/vars.yml` + `group_vars/all/vault.yml`
   (encrypted). Give staging and prod **different** `vault_db_password` values and show how
   you'd run each environment.

2. **Inline-encrypt a key.** Use `ansible-vault encrypt_string` to add an `api_key`
   variable into an otherwise-plaintext vars file, so the file stays readable except for
   the secret. Reference it in a template.

3. **Idempotence fix.** Here's a non-idempotent task — make it idempotent two different
   ways:
   ```yaml
   - ansible.builtin.shell: "echo $(date) >> /var/log/deploy.log"
   ```
   (a) so it never reports `changed`, (b) so it runs exactly once.

4. **Lint cleanup.** Name three things `ansible-lint` commonly flags and the fix for each
   (e.g. missing `name:`, using `shell` where a module exists, not using FQCN).

5. **Safe rollout.** Write the exact command sequence for a safe production change:
   syntax-check → lint → check-diff on staging → apply staging → verify idempotence →
   apply prod.

## Success criteria
- [ ] Two inventories + per-env vaulted passwords; correct run commands.
- [ ] An inline-vaulted `api_key` in a mostly-plaintext file.
- [ ] Two idempotence fixes for the shell task.
- [ ] Three lint findings + fixes.
- [ ] A correct, ordered safe-rollout command sequence.
