# Module 07 — Advanced Topics & Integration

**Goal:** master `git -C` for multi-repo orchestration, Docker Compose integration
with submodules, worktrees, bisect, and stash — the tools that tie everything
together. ⏱️ ~60 min · 🎯 Prereq: Modules 00–06.

---

## The `-C` flag: Git in other directories

`git -C <path> <command>` runs Git in the specified directory. This is how you
orchestrate multiple repos from a single script:

```bash
# Update submodules in different services
git -C challenge-service submodule update --init --recursive
git -C md_agent_service checkout main
git -C md_agent_service pull origin main
```

### Batch operations

```bash
for service in services/*; do
    echo "=== $service ==="
    git -C "$service" status --short
done
```

### Combining with other commands

```bash
# Check if all submodules are clean
git submodule foreach 'git status --porcelain' | grep -v "^$"
# If output is empty, all submodules are clean

# Using -C instead
for sub in $(git submodule status | awk '{print $2}'); do
    git -C "$sub" status --porcelain
done
```

## Docker Compose integration

When your project uses submodules for services, the workflow is:

```bash
# 1. Ensure submodules are initialized
git submodule update --init --recursive

# 2. Build and run
docker compose up --build
```

The `--build` flag forces Docker to rebuild images from the latest code in each
submodule. Without it, Docker uses cached layers.

### The build script pattern

```bash
#!/bin/bash
set -euo pipefail

echo "Updating submodules..."
git submodule update --init --recursive

echo "Building services..."
docker compose up --build -d

echo "Checking status..."
docker compose ps
```

### Submodule-aware Dockerfiles

If your Dockerfile copies code from a submodule:

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY services/api/ ./api/
COPY shared-libs/ ./libs/
RUN pip install -r api/requirements.txt
CMD ["python", "api/main.py"]
```

The `COPY` only works if the submodule is initialized. That's why
`git submodule update --init --recursive` must come before `docker compose up`.

## Worktrees: multiple branches at once

Worktrees let you check out multiple branches in separate directories:

```bash
git worktree add ../feature-branch feature-x
git worktree add ../hotfix-branch hotfix-v1
```

Now you have:
```
project/          ← main branch
../feature-branch/ ← feature-x branch
../hotfix-branch/  ← hotfix-v1 branch
```

Work on any branch without stashing or switching. List worktrees:

```bash
git worktree list
```

Remove when done:

```bash
git worktree remove ../feature-branch
```

## Bisect: find the bug commit

Binary search through history to find which commit introduced a bug:

```bash
git bisect start
git bisect bad              # current commit is broken
git bisect good v1.0        # v1.0 was known to work
```

Git checks out a middle commit. You test it:

```bash
# Run your test
make test
# If it passes:
git bisect good
# If it fails:
git bisect bad
```

After several iterations, Git identifies the exact commit that introduced the
bug. Clean up:

```bash
git bisect reset
```

## Stash: temporary shelves

Save uncommitted changes without committing:

```bash
git stash                          # stash all changes
git stash push -m "WIP: experiment" # stash with a message
git stash list                     # list all stashes
git stash pop                      # apply + remove latest
git stash apply stash@{2}          # apply a specific stash
git stash drop stash@{0}           # remove a specific stash
```

## The full integration pattern

Here's how all these tools combine in a real project:

```bash
# Start a hotfix from an old release
git worktree add ../hotfix v2.0.1
cd ../hotfix

# Fix the bug
echo "fixed" > app.py
git add app.py && git commit -m "fix: critical security issue"

# Tag the fix
git tag -a 2.0.2 -m "Release 2.0.2: security fix"

# Update all submodules
git submodule foreach --recursive '
  git checkout main &&
  git pull origin main
'

# Build and test
git submodule update --init --recursive
docker compose up --build -d
docker compose exec api pytest

# Push everything
git push origin 2.0.2
git push origin hotfix
git submodule foreach 'git push origin main'

# Clean up worktree
cd ~/project
git worktree remove ../hotfix
```

## Key terms

- **git -C** — run Git in a different directory
- **Docker Compose** — multi-container Docker application runner
- **--build** — force Docker to rebuild images
- **Worktree** — multiple working directories for one repo
- **Bisect** — binary search through commit history
- **Stash** — temporarily shelve uncommitted changes

---

**Next →** [Lab 07](./lab.md) — practice multi-repo orchestration and Docker integration.
