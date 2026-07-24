# Module 03 — Remote Operations & Pull Strategies

**Goal:** master `git pull`, `git fetch`, upstream tracking, and push strategies
so you can work with remotes confidently — including the `git pull origin main`
workflow. ⏱️ ~45 min · 🎯 Prereq: Modules 00–02.

---

## The remote model

A **remote** is a named connection to another repository. The default remote is
`origin`. When you clone a repo, Git creates `origin` automatically:

```bash
git remote -v
```

Expected:
```
origin  git@github.com:user/repo.git (fetch)
origin  git@github.com:user/repo.git (push)
```

## Fetch vs Pull

**Fetch** downloads commits from the remote but doesn't change your working tree:

```bash
git fetch origin
```

After fetching, `origin/main` is updated but your local `main` is unchanged.
You can inspect what changed:

```bash
git log main..origin/main --oneline    # commits on remote not yet local
git log origin/main..main --oneline    # commits on local not yet on remote
```

**Pull** is fetch + merge (or rebase):

```bash
git pull origin main
```

This is equivalent to:
```bash
git fetch origin
git merge origin/main
```

If `pull.rebase = true` (set in Module 01), it's equivalent to:
```bash
git fetch origin
git rebase origin/main
```

## `git pull origin main` in practice

This is the most common pull pattern. It means:
- **origin** — the remote to fetch from
- **main** — the branch to merge into your current branch

```bash
git checkout main
git pull origin main
```

Expected: if your local `main` is behind `origin/main`, Git fast-forwards:
```
Updating a1b2c3d..f4g5h6i
Fast-forward
 3 files changed, 45 insertions(+), 12 deletions(-)
```

If your local `main` has diverged, Git creates a merge commit (or rebases,
depending on `pull.rebase`).

## Non-fast-forward: what happens when history diverges

When you try to `git pull` and your local branch has commits the remote
doesn't have:

```
local:     A---B---C---D
remote:    A---B---E---F
```

This is a **non-fast-forward** situation. Git can't simply move the pointer
forward. It must reconcile the diverged history.

With merge (default):
```
local:     A---B---C---D---M   (M is a merge commit)
                  \       /
remote:    A---B---E---F
```

With rebase (`pull.rebase = true`):
```
local:     A---B---E'---F'---C'---D'
remote:    A---B---E---F
```

## Push strategies

### Simple push (default)

```bash
git push origin main
```

Pushes your local `main` to `origin/main`. Fails if the remote has commits you
don't have.

### Force push (dangerous)

```bash
git push --force origin main
```

Overwrites the remote branch with your local version. **Destructive** to anyone
else working on that branch.

### Force push with lease (safer)

```bash
git push --force-with-lease origin main
```

Fails if someone else pushed since your last fetch. This prevents you from
accidentally overwriting a teammate's work.

## Upstream tracking

When you create a branch, you can set its upstream:

```bash
git checkout -b feature
git push -u origin feature
```

The `-u` flag sets `origin/feature` as the upstream. Now simple commands work:

```bash
git push          # pushes to origin/feature
git pull          # pulls from origin/feature
git status        # shows "Your branch is up to date with 'origin/feature'"
```

Check upstreams:

```bash
git branch -vv
```

Expected:
```
* feature  a1b2c3d [origin/feature: ahead 2] latest work
  main     e4f5g6h [origin/main] initial
```

## Key terms

- **Remote** — named connection to another repository (default: `origin`)
- **Fetch** — download commits without changing working tree
- **Pull** — fetch + merge (or rebase)
- **Fast-forward** — remote is ahead of local, pointer can move forward
- **Non-fast-forward** — local and remote have diverged, needs merge/rebase
- **Upstream** — the remote branch your local branch tracks
- **Force push** — overwrites remote branch (dangerous)
- **Force with lease** — force push that fails if remote changed since last fetch

---

**Next →** [Lab 03](./lab.md) — simulate a multi-user remote workflow.
