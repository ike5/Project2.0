# Challenge 05 — Submodule Workflow Mastery

Solutions in [`solutions/`](./solutions/). Try first.

Apply submodule workflows to a realistic multi-service project.

## Tasks

1. **Three-service orchestration.** Create a parent repo with three submodules
   (`services/api`, `services/worker`, `services/scheduler`). Write a shell loop
   that uses `git -C` to checkout `main` and pull the latest in each. Show the
   output.

2. **foreach batch update.** Using `git submodule foreach --recursive`, run
   `git log --oneline -1` in every submodule. Then write a foreach command that
   creates a `BUILD.md` file in each submodule with the current branch name and
   commit hash.

3. **Shared pre-push hook.** Create a `.githooks/pre-push` script in the parent
   repo that runs `git submodule status --recursive` and fails if any submodule
   shows a `+` or `-` prefix (meaning it's not at the expected commit). Configure
   `core.hooksPath` in each submodule to point to the parent's `.githooks/`.
   Test by modifying a submodule without committing.

4. **The update = merge pattern.** In `.gitmodules`, set `update = merge` for all
   submodules. Explain in one sentence why you'd use this over the default.

## Success criteria

- [ ] Three submodules created and orchestrated with `git -C`
- [ ] `foreach` runs commands across all submodules
- [ ] Pre-push hook detects dirty submodules and blocks push
- [ ] `update = merge` is set for all submodules
- [ ] You can explain the merge strategy vs default

---

**Next →** Module 06: [Tagging & Release Management](../06-tagging-releases/README.md)
