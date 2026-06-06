# Challenge 03 — Templating & Vars

Solutions in [`solutions/`](./solutions/). Try first.

## Tasks
1. **Per-environment config.** Add `group_vars/all.yml` (defaults) and override in
   `group_vars/web.yml`. Demonstrate the precedence: set `worker_processes: 1` in `all`
   and `worker_processes: 4` in `web`, and prove `web` hosts get 4 (and a host in no other
   group gets 1).

2. **Fact-driven branch.** Write a task that installs the correct web package and uses the
   correct service name across distros: nginx on Debian-family, nginx on RedHat-family,
   skipping unknown families — using `when: ansible_os_family == ...`.

3. **A real template.** Create `motd.j2` that prints the hostname, distro+version, IP,
   CPU count, and memory (all from facts), plus a `{{ site_title }}` line. Deploy it to
   `/etc/motd` with the `template` module and verify by SSHing in.

4. **Loop with dicts.** Use a `loop` to create three users from a list of
   `{ name, groups }` dictionaries, and a second loop to add several `ufw` allow rules
   from a list of ports.

5. **Stretch:** In a template, iterate `groups['web']` and print each host's
   `hostvars[host].ansible_default_ipv4.address` — a backend list a load balancer would
   use. (You'll reuse this in the capstone.)

## Success criteria
- [ ] Precedence demonstrated (`web` overrides `all`).
- [ ] Distro-aware install/service via facts.
- [ ] A fact-rich `motd.j2` deployed and visible on login.
- [ ] Dict-loop user creation + a ports loop.
- [ ] (Stretch) A template listing peer IPs from `groups`/`hostvars`.
