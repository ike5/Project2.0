# Module 06 — Tagging & Release Management

**Goal:** create, manage, and use tags for real release workflows — from
lightweight pointers to annotated releases with semantic versioning. ⏱️ ~45 min · 🎯 Prereq: Modules 00–05.

---

## What is a tag?

A **tag** is a named pointer to a specific commit. Unlike branches, tags don't
move. Once you tag `v1.0`, that name always points to the same commit.

Tags are how you mark releases, versions, and milestones in your project's
history.

## Lightweight vs annotated tags

### Lightweight tag

A simple pointer — no metadata beyond the name:

```bash
git tag v1.0
```

This creates a tag `v1.0` pointing at the current commit. No message, no author,
no date.

### Annotated tag

A full Git object with metadata:

```bash
git tag -a v1.0 -m "Release 1.0: initial stable release"
```

Annotated tags include:
- Tagger name and email
- Date
- Tag message
- Optional GPG signature

**Always use annotated tags for releases.** They're the proper way to mark
versions. Lightweight tags are fine for temporary markers.

## Semantic versioning

The standard version numbering scheme:

```
MAJOR.MINOR.PATCH
```

- **MAJOR** — breaking changes (2.0.0 breaks backward compatibility with 1.x)
- **MINOR** — new features, backward compatible (1.2.0 adds features to 1.1.x)
- **PATCH** — bug fixes, backward compatible (1.1.2 fixes bugs in 1.1.1)

Example from the real world: `git tag 2.0.32`

```bash
git tag -a 2.0.32 -m "Release 2.0.32: submodule fixes and config improvements"
```

## Listing tags

```bash
git tag                    # list all tags
git tag -l "v1.*"          # filter with glob pattern
git tag -n1                # show first line of tag message
```

Expected:
```
v1.0        Release 1.0: initial stable release
v1.1        Release 1.1: added logging
v2.0        Release 2.0: major refactor
```

## Viewing a tag

```bash
git show v1.0
```

Shows the tag object (for annotated tags) and the commit it points to.

## Tagging a specific commit

You don't have to be on the commit to tag it:

```bash
git tag -a v1.0 abc1234 -m "Release 1.0"
```

This tags commit `abc1234` regardless of where HEAD is.

## Pushing tags

**Tags don't push automatically.** This surprises many people. You must push
them explicitly:

```bash
git push origin v1.0           # push one tag
git push origin --tags         # push all tags
```

## Deleting tags

```bash
git tag -d v1.0                      # delete locally
git push origin :refs/tags/v1.0      # delete remotely
```

The remote delete syntax looks odd — it pushes "nothing" to the tag ref,
effectively deleting it.

## Checking out a tag

```bash
git checkout v1.0
```

This puts you in **detached HEAD** state — you're at the tagged commit, not on
any branch. To make changes, create a branch:

```bash
git checkout -b hotfix-v1 v1.0
```

## Tag-based release workflow

A typical release process:

```bash
# 1. Make sure you're on main and up to date
git checkout main
git pull origin main

# 2. Create annotated tag
git tag -a 2.0.32 -m "Release 2.0.32: ..."

# 3. Push the tag
git push origin 2.0.32

# 4. Optionally create a GitHub release from the tag
# (or use CI/CD to automate this)
```

## Tagging in submodule projects

When your project uses submodules, you often want to tag the parent and
submodules at the same time:

```bash
# Tag the parent
git tag -a v2.0 -m "Release 2.0 with updated submodules"

# Tag each submodule
git -C services/service-a tag -a v1.3 -m "service-a v1.3"
git -C services/service-b tag -a v1.1 -m "service-b v1.1"

# Push everything
git push origin v2.0
git -C services/service-a push origin v1.3
git -C services/service-b push origin v1.1
```

## Key terms

- **Lightweight tag** — simple pointer to a commit
- **Annotated tag** — tag with metadata (author, date, message)
- **Semantic versioning** — MAJOR.MINOR.PATCH numbering
- **Tag push** — tags must be pushed explicitly
- **Detached HEAD** — checking out a tag or commit (not a branch)
- **refs/tags/** — the ref namespace for tags

---

**Next →** [Lab 06](./lab.md) — create, tag, and release a project.
