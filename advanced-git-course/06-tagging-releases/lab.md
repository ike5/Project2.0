# Lab 06 — Tag and Release a Project

**You'll:** create a repo, make several commits, tag them with semantic
versions, examine tags, delete and recover them, and simulate a release
workflow. ⏱️ ~35 min.

## Part A — Create a project with history

```bash
cd ~/git-advanced-course
mkdir lab06 && cd lab06
git init project
cd project

echo "v1 features" > app.py
git add app.py
git commit -m "v1.0: initial release"
```

Expected:
```
[main a1b2c3d] v1.0: initial release
```

```bash
echo "logging added" >> app.py
git add app.py
git commit -m "v1.1: add logging"

echo "bugfix applied" >> app.py
git add app.py
git commit -m "v1.1.1: fix critical bug"

echo "major refactor" > app.py
git add app.py
git commit -m "v2.0: major refactor"
```

✅ Check: `git log --oneline` shows 4 commits.

## Part B — Create annotated tags

```bash
cd ~/git-advanced-course/lab06/project

# Tag the first commit as v1.0
git tag -a v1.0 a1b2c34 -m "Release 1.0: initial release"

# Tag the second commit as v1.1
git tag -a v1.1 $(git rev-parse HEAD~2) -m "Release 1.1: added logging"

# Tag the third commit as v1.1.1
git tag -a v1.1.1 $(git rev-parse HEAD~1) -m "Release 1.1.1: critical bugfix"

# Tag the current commit as v2.0
git tag -a v2.0 -m "Release 2.0: major refactor"
```

✅ Check: `git tag` shows all four tags.

## Part C — List and inspect tags

```bash
git tag
```

Expected:
```
v1.0
v1.1
v1.1.1
v2.0
```

```bash
git tag -n1
```

Expected:
```
v1.0        Release 1.0: initial release
v1.1        Release 1.1: added logging
v1.1.1      Release 1.1.1: critical bugfix
v2.0        Release 2.0: major refactor
```

```bash
git show v1.1.1
```

Expected: shows the tag object with message, then the commit diff.

✅ Check: tags show correct messages and point to the right commits.

## Part D — Filter tags

```bash
git tag -l "v1.*"
```

Expected:
```
v1.0
v1.1
v1.1.1
```

```bash
git tag -l "v1.1*"
```

Expected:
```
v1.1
v1.1.1
```

✅ Check: glob filtering works correctly.

## Part E — Tag a specific commit by hash

```bash
cd ~/git-advanced-course/lab06/project
FIRST_COMMIT=$(git rev-list --max-parents=0 HEAD)
git tag -a v0.1 $FIRST_COMMIT -m "v0.1: pre-release"
git tag -l
```

Expected: `v0.1` appears in the list.

✅ Check: you can tag any commit regardless of HEAD position.

## Part F — Check out a tag (detached HEAD)

```bash
git checkout v1.1.1
git log --oneline -1
```

Expected:
```
c1d2e3f v1.1.1: critical bugfix
```

```bash
git status
```

Expected:
```
HEAD detached at v1.1.1
```

Return to main:

```bash
git checkout main
```

✅ Check: you can visit any tagged commit without affecting branches.

## Part G — Delete and recover a tag

```bash
git tag -d v0.1
git tag -l
```

Expected: `v0.1` is gone.

Recover using reflog:

```bash
git reflog | grep tag
```

Find the tag creation entry, then:

```bash
git tag -a v0.1 $(git rev-parse HEAD@{1}) -m "v0.1: pre-release (recovered)"
git tag -l
```

Expected: `v0.1` is back.

✅ Check: deleted tags can be recovered from reflog.

## Part H — Simulate a release workflow

```bash
cd ~/git-advanced-course/lab06/project
echo "release notes" > CHANGELOG.md
git add CHANGELOG.md
git commit -m "update CHANGELOG for v2.0.1"

git tag -a 2.0.1 -m "Release 2.0.1: changelog update"

# Simulate push (to our local bare remote would work, here we just verify)
git log --oneline --decorate
```

Expected: the latest commit shows `tag: 2.0.1`.

✅ Check: the tag appears in the decorated log.

## Part I — Clean up

```bash
rm -rf ~/git-advanced-course/lab06
```

✅ Check: the directory no longer exists.

---

**Next →** [Challenge 06](./challenge.md)
