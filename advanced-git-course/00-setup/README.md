# Module 00 — Setup & Orientation

**Goal:** verify your Git installation, configure your identity, and orient yourself
in the advanced topics we'll cover. ⏱️ ~20 min · 🎯 Prereq: Git basics (commit/push/pull/branch/checkout).

---

## What you need

Before diving into advanced Git, we need a solid foundation. This module ensures
your environment is ready and your config is correct.

## Git version check

Git evolves fast. Submodule improvements, config options, and safety features
land in newer versions. You need **Git 2.40+** for this course.

```bash
git --version
```

Expected:
```
git version 2.4x.0 or higher
```

If your version is older than 2.30, update before proceeding. On macOS use
`brew upgrade git`. On Ubuntu/Debian use `sudo apt update && sudo apt install git`.

## Identity configuration

Every commit you make is stamped with a name and email. These must be set
before you can commit.

```bash
git config --global user.name
git config --global user.email
```

Expected: both return your name and email. If either is empty:

```bash
git config --global user.name "Your Name"
git config --global user.email "you@example.com"
```

These settings live in `~/.gitconfig` and apply to every repository on your
machine. You can override them per-repository with `git config --local`.

## Creating a working directory

We'll create a dedicated workspace for this course. All labs run from here.

```bash
mkdir -p ~/git-advanced-course
cd ~/git-advanced-course
pwd
```

Expected:
```
/Users/you/git-advanced-course
```

or on Linux:
```
/home/you/git-advanced-course
```

## Verifying Git features

Let's confirm the features we'll use are available:

```bash
git config --global --list | head -20
```

Expected: a list of your current config settings.

```bash
git submodule --help > /dev/null 2>&1 && echo "submodule: OK" || echo "submodule: MISSING"
```

Expected:
```
submodule: OK
```

## What we'll cover

Here's the road ahead:

| Module | Topic | Key skills |
|--------|-------|------------|
| 01 | Advanced Git Config | `core.protectNTFS`, `pull.rebase`, hooks paths, per-repo settings |
| 02 | Branching & Force Operations | `checkout -f`, reset modes, reflog, rebase |
| 03 | Remote Operations | `pull origin main`, fetch, upstream tracking, push strategies |
| 04 | Submodule Fundamentals | `submodule add`, `update --init --recursive`, `.gitmodules` |
| 05 | Submodule Workflows | `foreach --recursive`, hooks, merge strategy, multi-repo orchestration |
| 06 | Tagging & Releases | `git tag`, semantic versioning, tag-based releases |
| 07 | Advanced Integration | `git -C`, Docker Compose integration, worktrees, cherry-pick |
| 08 | Capstone | Multi-service project combining everything |

## Key terms

- **Git config** — key-value settings controlling Git behavior
- **Global config** — settings that apply to all your repositories
- **Local config** — settings that apply to one repository only
- **Identity** — your `user.name` and `user.email` stamped on every commit

---

**Next →** Module 01: [Advanced Git Config](../01-git-config-advanced/README.md)
