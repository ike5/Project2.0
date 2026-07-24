# Challenge 01 — Configure a Real Project

Solutions in [`solutions/`](./solutions/). Try first.

Apply what you learned about advanced config to set up a realistic project
environment.

## Tasks

1. **Create a project repo.** Initialize a Git repo in `~/git-advanced-course/challenge01`.
   Set the local `user.name` to "Project Lead" and local `user.email` to
   "lead@project.dev". Verify these override your global settings.

2. **Configure pull behavior.** Set `pull.rebase` to `true` locally. Set
   `push.default` to `simple` globally. Verify both are active.

3. **Create a shared hooks directory.** Create `.githooks/` in your repo. Write a
   `commit-msg` hook that rejects commits shorter than 10 characters. Set
   `core.hooksPath` to `.githooks`. Test it by trying to commit with a short
   message (it should fail), then a long message (it should succeed).

4. **Configure submodule auto-recurse.** Set `submodule.recurse` to `true`
   globally. Explain in one sentence what this setting does.

5. **Document your config.** Run `git config --list --show-origin` and note
   which settings came from system, global, and local config.

## Success criteria

- [ ] Local `user.name` = "Project Lead" and overrides global
- [ ] `pull.rebase` = `true` (local)
- [ ] `push.default` = `simple` (global)
- [ ] Commit-msg hook rejects short messages
- [ ] `submodule.recurse` = `true` (global)
- [ ] You can identify the origin of each config setting

---

**Next →** Module 02: [Branching & Force Operations](../02-branching-force/README.md)
