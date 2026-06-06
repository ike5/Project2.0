# Challenge 13 — Remote Mastery

Solutions in [`solutions/`](./solutions/). Try first (use your two VMs).

## Tasks
1. **Dedicated deploy key.** Generate a *separate* ed25519 key just for a `deploy` user,
   create that user on `web`, install the key, and add a `Host deploy-web` block in
   `~/.ssh/config` that uses it. Confirm `ssh deploy-web` works passwordless.

2. **Run a remote audit.** Without logging in interactively, run a single `ssh` command
   that prints `web`'s hostname, uptime, and free disk on `/` — all in one invocation.

3. **Jump host.** Assume `web` can only be reached *through* a bastion you can SSH to.
   Write the `ssh` command (and the `~/.ssh/config` `ProxyJump` block) to reach `web` via
   the bastion in one step.

4. **Lockout-proof hardening.** List the exact order of steps to disable password auth on
   a remote server **without risk** of locking yourself out, including the command that
   validates the config before restarting `sshd`.

5. **Permissions gotcha.** A user set up `~/.ssh/authorized_keys` but key auth still fails
   and the log says "Authentication refused: bad ownership or modes." What are the correct
   permissions for `~/.ssh` and `authorized_keys`, and the commands to fix them?

## Success criteria
- [ ] Separate deploy key + config alias works passwordless.
- [ ] One-shot remote audit command.
- [ ] Correct `ProxyJump`/`-J` usage.
- [ ] A safe, ordered hardening procedure including `sshd -t`.
- [ ] `chmod 700 ~/.ssh` + `chmod 600 authorized_keys` (and correct ownership).
