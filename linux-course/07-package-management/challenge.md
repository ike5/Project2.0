# Challenge 07 — Packaging

Solutions in [`solutions/`](./solutions/). Give both the Debian and RHEL commands.

## Tasks
1. **Trace a binary.** Determine which installed package provides `/usr/bin/dig` (or
   another tool of your choice), on both families.

2. **List a package's files & config.** Show all files installed by the `openssh-server`
   package, and isolate just the ones under `/etc`. (Debian: `dpkg -L`; RHEL: `rpm -ql` /
   `rpm -qc`.)

3. **update vs upgrade.** Explain the difference between `apt update` and `apt upgrade`,
   and why running `apt install` right after a fresh boot might fail without `apt update`.

4. **Clean removal.** You installed `nginx` and edited `/etc/nginx/nginx.conf`. What's the
   difference between `apt remove nginx` and `apt purge nginx` regarding that config file?

5. **Repos.** Add the EPEL repository on a RHEL-family box (command), and add a PPA on
   Ubuntu (command). Why might you avoid third-party repos on production servers?

6. **Stretch:** Outline (commands) how you'd install a CLI tool from a release tarball,
   and why a package-manager install is preferable when one exists.

## Success criteria
- [ ] Correct "which package owns this file" on both families.
- [ ] Package file list + the `/etc` subset.
- [ ] Clear `update` vs `upgrade` explanation.
- [ ] `remove` vs `purge` config behavior explained.
- [ ] EPEL + PPA commands, plus a third-party-repo caution.
