# Module 02 — Branching & Force Operations

**Goal:** master force checkout, the three reset modes, reflog recovery, and
rebase — the operations that separate Git power users from everyone else. ⏱️ ~60 min · 🎯 Prereq: Modules 00–01.

---

## Force checkout: `git checkout -f`

You're on `feature-x`. You've made changes — some staged, some not. You need
to switch to `main` immediately. You don't care about those changes.

```bash
git checkout -f main
```

This does three things:
1. Moves HEAD to `main`
2. Replaces the entire working tree with `main`'s snapshot
3. **Discards all staged and unstaged changes** — no warning, no recovery

The `-f` flag means "force." Without it, Git refuses to switch if you have
uncommitted changes:

```bash
git checkout main
# error: Your local changes to the following files would be overwritten by checkout
```

**When to use force checkout:**
- You're on a throwaway branch and want to start over
- You've been experimenting and want a clean slate
- CI/CD pipelines need a known state

**When NOT to use force checkout:**
- When you might want those changes back
- When you're not sure what you'll lose

## The three reset modes

`git reset` moves HEAD (and optionally the staging area and working tree) to
a different commit. The mode determines how far it reaches:

```
                  HEAD     staging     working tree
                  ────     ───────     ────────────
  --soft            ✓          
  --mixed (default) ✓          ✓
  --hard            ✓          ✓           ✓
```

### `git reset --soft HEAD~1`

Moves HEAD back one commit. The commit's changes remain staged (in the index).
Use this when you want to amend the last commit or combine commits.

```bash
git log --oneline
# a1b2c3d third commit
# e4f5g6h second commit
# i7j8k9l first commit

git reset --soft HEAD~1
git log --oneline
# e4f5g6h second commit
# i7j8k9l first commit

git status
# Changes to be committed: (the changes from "third commit" are still staged)
```

### `git reset --mixed HEAD~1` (default)

Moves HEAD back one commit AND unstages the changes. The changes remain in
the working tree as modified files.

```bash
git reset HEAD~1
git log --oneline
# i7j8k9l first commit

git status
# Changes not staged for commit: (the changes are there, just unstaged)
```

### `git reset --hard HEAD~1`

The nuclear option. Moves HEAD, unstages everything, AND deletes the changes
from the working tree. **This is destructive.**

```bash
git reset --hard HEAD~1
git log --oneline
# i7j8k9l first commit

git status
# nothing to commit, working tree clean
```

## Reflog: your safety net

Even after a `--hard` reset, the commits aren't truly gone. Git keeps a log
of every HEAD movement called the **reflog**:

```bash
git reflog
```

Output:
```
a1b2c3d HEAD@{0}: reset: moving to HEAD~1
b2c3d4e HEAD@{1}: commit: third commit
e4f5g6h HEAD@{2}: commit: second commit
```

To recover:

```bash
git reset --hard b2c3d4e
```

The reflog is local (not pushed) and entries expire after 90 days by default.
Within that window, you can recover from almost any mistake.

## Rebase: clean history

Rebase takes "your commits" and replays them on top of a different base:

```bash
git checkout feature-x
git rebase main
```

Before:
```
main:     A---B---C
feature-x:     D---E
```

After:
```
main:     A---B---C
feature-x:             D'---E'
```

D' and E' are new commits with the same changes but different hashes (because
their parent changed).

### Interactive rebase

```bash
git rebase -i HEAD~5
```

Opens an editor where you can:
- **pick** — keep the commit as-is
- **squash** — merge it into the previous commit
- **reword** — change the commit message
- **edit** — pause to modify the commit
- **drop** — remove the commit entirely

### When rebase goes wrong

```bash
git rebase --abort      # cancel the rebase, go back to before it started
git rebase --continue   # after resolving conflicts, continue replaying
```

## Cherry-pick: apply a single commit

```bash
git cherry-pick abc123
```

Creates a new commit with the same changes as `abc123` on your current branch.
Useful for:
- Backporting a bugfix from `main` to an older release branch
- Grabbing one specific change without merging a whole branch

```bash
git cherry-pick abc123..def456    # apply a range
git cherry-pick --no-commit abc   # stage changes without committing
```

## Key terms

- **Force checkout** — `checkout -f` switches branches and discards all changes
- **Soft reset** — moves HEAD, keeps changes staged
- **Mixed reset** — moves HEAD, unstages changes (default)
- **Hard reset** — moves HEAD, discards everything
- **Reflog** — log of HEAD movements; safety net for recovery
- **Rebase** — replays commits on a new base for linear history
- **Cherry-pick** — applies a specific commit to the current branch

---

**Next →** [Lab 02](./lab.md) — break things on purpose and recover.
