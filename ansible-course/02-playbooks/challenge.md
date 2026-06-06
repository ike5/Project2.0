# Challenge 02 — Build a Playbook

Solutions in [`solutions/`](./solutions/). Try first. Keep it idempotent.

## Tasks
1. **Baseline play.** Write `baseline.yml` that, on `all` hosts: ensures `htop`, `curl`,
   and `vim` are installed; creates a `deploy` user with a bash shell; sets the timezone
   to UTC (`community.general.timezone` or `timedatectl` via command with `changed_when`);
   and ensures `ufw` is installed. Run it twice and confirm the second run is `changed=0`.

2. **Handler discipline.** Add a task that writes `/etc/motd` from inline content, and a
   handler "Log motd change" that runs only when the motd changes (use `notify` + a
   `debug`/`command` handler). Prove the handler fires only on change.

3. **command idempotence.** Add a task using `ansible.builtin.command` that creates a file
   `/srv/initialized` only if it doesn't exist, using `creates:` so it's idempotent.
   Explain why `creates:` matters.

4. **Check mode safety.** Run your playbook with `--check --diff` and explain what each of
   the `ok`/`changed` markers means in check mode (vs a real run).

5. **Stretch:** Add `--limit` and `--tags` usage notes: tag the package tasks `packages`
   and run only those.

## Success criteria
- [ ] `baseline.yml` is idempotent (`changed=0` on re-run).
- [ ] A handler that fires only when the motd changes.
- [ ] An idempotent `command` task via `creates:`.
- [ ] Correct interpretation of check-mode output.
