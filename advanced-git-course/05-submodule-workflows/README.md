# Module 05 — Submodule Workflows & Hooks

**Goal:** orchestrate multiple submodules with `foreach`, set up shared hooks,
configure merge strategies, and manage `.git/modules/` — the patterns real
teams use daily. ⏱️ ~60 min · 🎯 Prereq: Modules 00–04.

---

## The foreach pattern

When you have multiple submodules, updating them one by one is tedious.
`git submodule foreach` runs a command in every submodule:

```bash
git submodule foreach 'git status'
```

Expected:
```
Entering 'libs/library-a'
On branch main
nothing to commit, working tree clean

Entering 'libs/library-b'
On branch main
nothing to commit, working tree clean
```

### Update all submodules to main

The command you'll use most often:

```bash
git submodule foreach --recursive '
  git checkout main &&
  git pull origin main
'
```

Breaking this down:
- `foreach` — iterate over all submodules
- `--recursive` — also run in nested submodules
- `git checkout main` — switch to main in each submodule
- `git pull origin main` — pull the latest from remote

This is the pattern from the real-world projects you've seen. It keeps all
submodules in sync with their remotes.

### Useful foreach commands

```bash
# Clean all submodules
git submodule foreach 'git clean -fd'

# Show all submodules on the same branch
git submodule foreach 'git branch --show-current'

# Run tests in each submodule
git submodule foreach 'make test'

# Show the latest commit in each submodule
git submodule foreach 'git log --oneline -1'
```

## Submodule hooks

Git hooks inside submodules work like any other repo. But there's a subtlety:
when you clone a parent repo, the submodule hooks might not be executable.

The `.git/modules/[submodule-name]/hooks/` directory stores the actual hook
scripts for each submodule. When you see:

```
.git/modules/our-cool-submodule/here/hooks
```

That's the hook storage for a submodule at path `our-cool-submodule/here`.

### Setting up shared hooks for submodules

Since hooks in `.git/hooks/` aren't tracked, use `core.hooksPath`:

```bash
# In each submodule:
cd libs/library-a
git config core.hooksPath ../../.githooks
```

This points submodule hooks to the parent repo's shared hooks directory.

### Pre-push validation

A common pattern: run tests before pushing from any submodule:

```bash
cat > .githooks/pre-push << 'EOF'
#!/bin/sh
echo "Running tests before push..."
make test
if [ $? -ne 0 ]; then
    echo "Tests failed. Push aborted."
    exit 1
fi
EOF
chmod +x .githooks/pre-push
```

## The update = merge strategy

By default, `git submodule update` checks out the exact commit the parent
records. This can discard local changes in the submodule. The merge strategy
preserves them:

In `.gitmodules`:
```ini
[submodule "libs/library-a"]
    path = libs/library-a
    url = https://github.com/user/library-a.git
    update = merge
```

With `update = merge`, running `git submodule update` merges the tracked commit
into the submodule's current state instead of doing a hard checkout.

This is useful when:
- Developers make local experimental changes in submodules
- You want to pull upstream changes without losing local work

## The full submodule update workflow

Here's the complete pattern for updating all submodules:

```bash
# Step 1: Pull parent repo changes
git pull origin main

# Step 2: Update submodules to parent's expected commits
git submodule update --init --recursive

# Step 3: Optionally update to latest remote
git submodule foreach --recursive '
  git checkout main &&
  git pull origin main
'

# Step 4: Commit the updated submodule pointers
git add libs/
git commit -m "update submodule pointers"
git push origin main
```

## The docker compose integration

In projects with Docker, submodules often contain service code. The pattern:

```bash
# Initialize submodules first
git submodule update --init --recursive

# Then build and run
docker compose up --build
```

The `--build` flag forces Docker to rebuild images, picking up any submodule
changes. Without it, Docker uses cached layers and might miss submodule updates.

## Multi-repo orchestration with git -C

The `-C` flag lets you run Git commands in different directories:

```bash
# Update challenge-service submodule
git -C challenge-service submodule update --init --recursive

# Checkout main in md_agent_service
git -C md_agent_service checkout main

# Combine in a script
for service in challenge-service md-agent-service; do
    git -C "$service" checkout main
    git -C "$service" pull origin main
    git -C "$service" submodule update --init --recursive
done
```

## Key terms

- **submodule foreach** — run a command in every submodule
- **--recursive foreach** — also run in nested submodules
- **.git/modules/** — internal storage for submodule data
- **update = merge** — merge strategy instead of checkout
- **core.hooksPath** — shared hooks directory
- **git -C** — run Git in a different directory
- **docker compose up --build** — rebuild with latest submodule code

---

**Next →** [Lab 05](./lab.md) — orchestrate submodules and hooks in practice.
