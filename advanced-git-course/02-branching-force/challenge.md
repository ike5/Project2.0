# Challenge 02 — Recovery Scenarios

Solutions in [`solutions/`](./solutions/). Try first.

Work through each scenario. Every problem has a solution using the tools from
this module.

## Tasks

1. **Lost commit recovery.** Create a repo with 5 commits on `main`. Accidentally
   run `git reset --hard HEAD~3`. Use the reflog to recover all 5 commits. Show
   the reflog output before and after recovery.

2. **Interactive rebase cleanup.** Create a branch with 4 commits: "feat: add
   login", "WIP: temp fix", "feat: add signup", "typo fix". Use interactive rebase
   to squash the "WIP" and "typo" commits into the feature commits, resulting in
   2 clean commits. Show the before and after `git log --oneline`.

3. **Cherry-pick a fix.** You have two branches: `release-v1` and `main`. A bugfix
   is committed on `main` but `release-v1` needs it too. Cherry-pick the fix onto
   `release-v1` without merging the branches. Verify the fix is there.

4. **Force checkout scenario.** You're on `feature-experiment` with a mix of staged
   and unstaged changes. You need to switch to `main` immediately and you don't
   care about the changes. Do it in one command. Verify the working tree is clean.

## Success criteria

- [ ] All 5 commits recovered using reflog
- [ ] Interactive rebase produces exactly 2 clean commits
- [ ] Bugfix appears on `release-v1` with the same diff as on `main`
- [ ] Force checkout switches to `main` with a clean working tree
- [ ] You can explain what `--soft`, `--mixed`, and `--hard` do

---

**Next →** Module 03: [Remote Operations & Pull Strategies](../03-remote-operations/README.md)
