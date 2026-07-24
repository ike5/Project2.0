# Module 04 — Submodule Fundamentals

**Goal:** understand what submodules are, how to add them, update them, and
clone repos that use them — including `--init` and `--recursive`. ⏱️ ~75 min · 🎯 Prereq: Modules 00–03.

---

## What is a submodule?

A **submodule** is a Git repository embedded inside another Git repository. The
parent repo doesn't store the submodule's files — it stores a **commit hash**
that points to the exact state of the submodule it expects.

```
parent-repo/
├── .gitmodules          ← defines submodule paths and URLs
├── src/
│   └── ...
└── libs/
    └── our-cool-submodule/   ← this is a separate repo (submodule)
        ├── .git             ← actually a file pointing to parent's .git/modules/
        └── ...
```

The key insight: the parent repo tracks a **specific commit** of the submodule,
not its branch. When you run `git submodule update`, it checks out that exact
commit.

## The .gitmodules file

When you add a submodule, Git creates or updates `.gitmodules` in the parent
repo root:

```ini
[submodule "our-cool-submodule/here"]
    path = libs/our-cool-submodule
    url = https://github.com/user/our-cool-submodule.git
    branch = main
```

This file is committed and tracked — everyone who clones the parent repo can
see which submodules it uses.

## Adding a submodule

```bash
git submodule add <url> <path>
```

Example:

```bash
git submodule add https://github.com/octocat/Hello-World.git libs/hello-world
```

This does three things:
1. Clones the repository into `libs/hello-world`
2. Adds it to `.gitmodules`
3. Stages both `.gitmodules` and the submodule path

Check the result:

```bash
cat .gitmodules
git status
```

## Cloning a repo with submodules

When someone clones a repo that has submodules, the submodule directories are
empty by default:

```bash
git clone https://github.com/user/parent-repo.git
ls libs/our-cool-submodule/
# empty
```

You need to initialize and update:

```bash
git submodule update --init --recursive
```

Breaking this down:
- `update` — checkout the recorded commit for each submodule
- `init` — initialize submodules that haven't been set up yet
- `--recursive` — do the same for nested submodules (submodules within submodules)

## The one-step clone

```bash
git clone --recurse-submodules https://github.com/user/parent-repo.git
```

This clones and initializes all submodules in one step. Use this whenever the
repo has submodules.

## Checking submodule status

```bash
git submodule status
```

Output:
```
 a1b2c3d libs/hello-world       (expected commit)
```

The prefix tells you the state:
- (space) — submodule is at the expected commit
- `-` — submodule is not initialized
- `+` — submodule has a different commit than expected
- `U` — submodule has merge conflicts

With `--recursive`:
```bash
git submodule status --recursive
```

## Updating submodules

After pulling parent repo changes, submodule pointers may have moved:

```bash
git pull origin main
git submodule update --init --recursive
```

This checks out the new expected commit in each submodule.

## The recursive clone pattern

In multi-service projects, you often see:

```bash
git -C challenge-service submodule update --init --recursive
git -C md_agent_service checkout main
```

The `-C` flag tells Git to run in a different directory. This is how you
orchestrate multiple repos from a script.

## Key terms

- **Submodule** — a Git repo embedded inside another repo
- **.gitmodules** — config file defining submodule paths and URLs
- **submodule add** — register and clone a new submodule
- **submodule update** — checkout the expected commit
- **--init** — initialize uninitialized submodules
- **--recursive** — process nested submodules too
- **submodule status** — show state of all submodules
- **git -C** — run Git in a specified directory

---

**Next →** [Lab 04](./lab.md) — create a parent repo with submodules and manage them.
