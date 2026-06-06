# Challenge 02 — Reference Solution

Full playbook: [`baseline.yml`](./baseline.yml).

### 1. Idempotent baseline
```bash
ansible-playbook -i ../code/inventory.ini baseline.yml
ansible-playbook -i ../code/inventory.ini baseline.yml      # 2nd run -> changed=0
```
Each module (`apt`, `user`, `timezone`, `copy`) is state-based, so the second run finds
everything already correct.

### 2. Handler discipline
The `Write the message of the day` task `notify:`s **Log motd change**. The handler runs
**only** when that task reports `changed` (i.e. the motd content actually changed) and
**once** at the play's end. Change the `content:` and re-run to see it fire; run again
unchanged and it stays silent.

### 3. command idempotence with `creates:`
```yaml
- ansible.builtin.command: touch /srv/initialized
  args:
    creates: /srv/initialized
```
> `command`/`shell` are **not** idempotent by default — they'd run every time and always
> report `changed`. `creates: <path>` tells Ansible to **skip** the task if that path
> already exists, making it idempotent. (`removes:` is the inverse.) Without it, you'd
> re-run side effects and lose accurate change reporting.

### 4. Check mode meaning
```bash
ansible-playbook -i ../code/inventory.ini baseline.yml --check --diff
```
> In `--check`, Ansible **simulates**: `changed` means "this *would* change on a real
> run," `ok` means "already in the desired state." No changes are made. (Some tasks can't
> fully predict in check mode and may warn.) On a real run, `changed` means it *did*
> change.

### 5. Tags
```bash
ansible-playbook -i ../code/inventory.ini baseline.yml --tags packages    # only tagged tasks
ansible-playbook -i ../code/inventory.ini baseline.yml --skip-tags packages
ansible-playbook -i ../code/inventory.ini baseline.yml --limit web01      # only this host
```
