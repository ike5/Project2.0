# Challenge 04 — Submodule Mastery

Solutions in [`solutions/`](./solutions/). Try first.

Work through each task using only Git commands — no copy-paste from the lab.

## Tasks

1. **Three-submodule project.** Create a parent repo with three submodules:
   `libs/auth`, `libs/database`, `libs/cache`. Each should be a separate bare
   repo with at least one file. Add all three to the parent, commit, and verify
   with `git submodule status`.

2. **Fresh clone simulation.** Clone the parent repo into a new directory WITHOUT
   `--recurse-submodules`. Verify submodules are empty. Initialize them with
   `git submodule update --init`. Verify files appear.

3. **Status interpretation.** Modify a file inside one submodule (without
   committing). Run `git submodule status` in the parent. What does the `+`
   prefix mean? Now commit the change inside the submodule. Check status again.
   What changed?

4. **Recursive operations.** Add a submodule INSIDE one of the existing submodules
   (nested submodule). Commit in the parent. Clone fresh and run
   `git submodule update --init --recursive`. Verify the nested submodule is also
   initialized.

5. **The -C pattern.** Write a single command that initializes all submodules
   inside a cloned copy using `git -C` instead of `cd`.

## Success criteria

- [ ] Three submodules exist with correct paths
- [ ] Fresh clone without --recurse-submodules has empty submodule dirs
- [ ] `submodule update --init` populates the files
- [ ] Status shows `+` when submodule commit diverges
- [ ] Nested submodule initializes with --recursive
- [ ] `git -C <path> submodule update --init --recursive` works

---

**Next →** Module 05: [Submodule Workflows & Hooks](../05-submodule-workflows/README.md)
