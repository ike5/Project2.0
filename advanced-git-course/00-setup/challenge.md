# Challenge 00 — Verify Your Full Environment

Solutions in [`solutions/`](./solutions/). Try first.

Complete each task and confirm it works before moving on.

## Tasks

1. **Create and destroy a test repo.** Create a temporary Git repo, make a commit,
   verify the commit exists, then delete the repo. Do this entirely from the command
   line.

2. **Set and verify local config.** In a new test repo, set `user.name` and
   `user.email` locally (not globally). Verify these local values take precedence
   over your global config by running `git config --list --show-origin | grep user`.

3. **Check your Git version for submodule support.** Run `git submodule -h` and
   confirm it shows the `init`, `update`, `foreach`, and `add` subcommands. List
   them.

4. **Verify your working directory.** Create the directory `~/git-advanced-course/`
   if it doesn't exist. This will be your workspace for the rest of the course.

## Success criteria

- [ ] You can create a repo, commit, and delete it in under 30 seconds
- [ ] Local config overrides global config for a specific repo
- [ ] `git submodule -h` lists `init`, `update`, `foreach`, `add`
- [ ] `~/git-advanced-course/` exists

---

**Next →** Module 01: [Advanced Git Config](../01-git-config-advanced/README.md)
