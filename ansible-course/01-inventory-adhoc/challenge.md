# Challenge 01 — Inventory & Ad-Hoc

Solutions in [`solutions/`](./solutions/). Try first.

## Tasks
1. **Three-tier inventory.** Write an inventory with groups `web` (2 hosts), `db` (1
   host), and `lb` (1 host), plus a parent group `staging` containing all three. Set
   `ansible_user=ubuntu` for everyone and `http_port=8080` only for `web`. Prove the
   structure with `ansible-inventory --graph` and `--list`.

2. **Targeting.** Write the host patterns to address: (a) only db hosts, (b) everything
   except the load balancer, (c) hosts in both `web` and `staging`, (d) all web hosts whose
   name starts with `web`.

3. **One-shot audit.** With a single ad-hoc command, gather the OS family and total memory
   of every host (hint: `setup` with a `filter`).

4. **Idempotent install.** Use an ad-hoc command to ensure `curl` and `git` are present on
   `web` in one invocation (a module that accepts a list), and show how you'd confirm the
   second run reports `ok`, not `changed`.

5. **command vs shell.** Give one task that works with `command` and one that *requires*
   `shell`, and explain why.

## Success criteria
- [ ] Correct multi-group inventory with scoped vars, verified via `ansible-inventory`.
- [ ] All four host patterns correct.
- [ ] One command returns OS family + memory per host.
- [ ] A single idempotent multi-package install; you can explain changed→ok.
- [ ] A correct `command`-vs-`shell` example with rationale.
