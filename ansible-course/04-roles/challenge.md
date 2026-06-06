# Challenge 04 — Roles

Solutions in [`solutions/`](./solutions/). Try first.

## Tasks
1. **A `firewall` role.** Create a role that installs `ufw`, sets default-deny incoming,
   and allows a configurable list of ports (default `[22, 80]`) from a role default.
   Make the allowed ports overridable via `group_vars`. Add it to `site.yml`.

2. **Role variables done right.** In your `webserver` role, decide which values belong in
   `defaults/` (user-tunable: `http_port`, `web_root`, `site_title`) vs `vars/` (internal:
   e.g. the nginx config path). Justify the split.

3. **Conditional role.** Add a `monitoring` role (it can just install `htop` + a debug
   message) and include it only when `enable_monitoring | default(false)` is true. Show
   running with and without it via `-e enable_monitoring=true`.

4. **Dependencies.** Make `webserver` depend on `firewall` via `meta/main.yml` so the
   firewall is configured before nginx. Verify the order in the run output.

5. **Galaxy pinning.** Write a `requirements.yml` that pins `community.general` to a
   specific version and a community role, and the one command to install them. Why pin
   versions?

## Success criteria
- [ ] A working `firewall` role with overridable ports.
- [ ] A sensible `defaults` vs `vars` split with justification.
- [ ] `monitoring` role runs only when enabled.
- [ ] `webserver` depends on `firewall`; order confirmed in output.
- [ ] A pinned `requirements.yml` + install command, with a reason for pinning.
