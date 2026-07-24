# Lab 07 — Multi-Repo Orchestration & Docker

**You'll:** use `git -C` to manage multiple repos, simulate a Docker Compose
workflow, practice worktrees, bisect, and stash. ⏱️ ~50 min.

## Part A — Multi-repo orchestration with git -C

```bash
cd ~/git-advanced-course
mkdir lab07 && cd lab07

# Create three "service" repos
for svc in api worker scheduler; do
    git init --bare ${svc}.git
    git clone ${svc}.git ${svc}-work
    cd ${svc}-work
    echo "def run(): return '${svc}'" > main.py
    git add main.py && git commit -m "initial: ${svc}" && git push origin main
    cd ..
done
```

Create a parent that references them:

```bash
git init parent && cd parent
git submodule add ../api.git services/api
git submodule add ../worker.git services/worker
git submodule add ../scheduler.git services/scheduler
git commit -m "add services"
```

Now orchestrate with `git -C`:

```bash
echo "=== Status of all services ==="
for service in services/*; do
    echo "--- $service ---"
    git -C "$service" log --oneline -1
done
```

Expected:
```
=== Status of all services ===
--- services/api ---
a1b2c3d initial: api
--- services/worker ---
b2c3d4e initial: worker
--- services/scheduler ---
c3d4e5f initial: scheduler
```

✅ Check: the loop successfully runs Git commands in each service directory.

## Part B — Batch update with git -C

```bash
cd ~/git-advanced-course/lab07/parent
for service in services/*; do
    echo "Updating $service..."
    git -C "$service" checkout main
    git -C "$service" status --short
done
```

Expected:
```
Updating services/api...
Updating services/worker...
Updating services/scheduler...
```

(No output from `status --short` means clean working trees.)

✅ Check: all services are on `main` and clean.

## Part C — Simulate Docker Compose workflow

```bash
cd ~/git-advanced-course/lab07/parent

# Simulate the build script
cat > build.sh << 'EOF'
#!/bin/bash
set -euo pipefail

echo "Step 1: Updating submodules..."
git submodule update --init --recursive

echo "Step 2: Building services..."
for service in services/*; do
    echo "  Building $service..."
    echo "  COPY $(ls $service/*.py 2>/dev/null || echo 'no files') into container"
done

echo "Step 3: docker compose up --build (simulated)"
echo "  Services would start here"
EOF
chmod +x build.sh

./build.sh
```

Expected:
```
Step 1: Updating submodules...
Step 2: Building services...
  Building services/api...
  COPY services/api/main.py into container
  Building services/worker...
  COPY services/worker/main.py into container
  Building services/scheduler...
  COPY services/scheduler/main.py into container
Step 3: docker compose up --build (simulated)
  Services would start here
```

✅ Check: the build script runs without errors.

## Part D — Worktrees

```bash
cd ~/git-advanced-course/lab07/parent

# Create a hotfix branch in a worktree
git worktree add ../parent-hotfix -b hotfix-v1 main

# Verify
git worktree list
```

Expected:
```
/Users/you/git-advanced-course/lab07/parent          abc1234 [main]
/Users/you/git-advanced-course/lab07/parent-hotfix   abc1234 [hotfix-v1]
```

```bash
# Work in the hotfix worktree
cd ../parent-hotfix
echo "hotfix" > hotfix.txt
git add hotfix.txt && git commit -m "hotfix: security patch"
git log --oneline
```

Expected:
```
def5678 hotfix: security patch
abc1234 add services
```

```bash
# Check main is unaffected
cd ../parent
git log --oneline
```

Expected: main doesn't have the hotfix commit.

✅ Check: worktrees allow parallel work on different branches.

## Part E — Stash

```bash
cd ~/git-advanced-course/lab07/parent

echo "experiment" > experiment.txt
echo "dirty work" >> services/api/main.py

git stash push -m "WIP: experimental changes"
git status
```

Expected:
```
On branch main
nothing to commit, working tree clean
```

```bash
git stash list
```

Expected:
```
stash@{0}: On main: WIP: experimental changes
```

```bash
git stash pop
git status
```

Expected: changes are back.

✅ Check: stash saves and restores uncommitted changes.

## Part F — Bisect

```bash
cd ~/git-advanced-course/lab07/parent

# Create a history where one commit "breaks" things
git checkout -b bisect-demo
for i in 1 2 3 4 5 6 7 8; do
    echo "value=$i" > data.txt
    if [ $i -eq 5 ]; then
        echo "BUG" >> data.txt
    fi
    git add data.txt && git commit -m "commit $i"
done

# Find the bug
git bisect start
git bisect bad HEAD
git bisect good $(git rev-list --max-parents=0 HEAD)

# At each step, check if BUG is in data.txt
# In real life you'd run tests; here we just grep
if grep -q "BUG" data.txt; then
    git bisect bad
else
    git bisect good
fi
# Repeat until bisect identifies the commit

git bisect reset
git checkout main
```

Expected: Git identifies commit 5 as the one that introduced the bug.

✅ Check: bisect narrows down to the exact breaking commit.

## Part G — Clean up

```bash
cd ~/git-advanced-course/lab07
git worktree remove parent-hotfix 2>/dev/null || true
rm -rf lab07
```

✅ Check: the directory no longer exists.

---

**Next →** [Challenge 07](./challenge.md)
