# Lab 05 — Orchestrate Submodules and Hooks

**You'll:** use `foreach` to manage multiple submodules, set up shared hooks,
configure the merge strategy, and simulate a Docker-like workflow. ⏱️ ~50 min.

## Part A — Create a parent with two submodules

```bash
cd ~/git-advanced-course
mkdir lab05 && cd lab05

# Create bare repos
git init --bare service-a.git
git init --bare service-b.git

# Populate service-a
git clone service-a.git work-a
cd work-a
echo "def hello(): return 'A'" > app.py
git add app.py && git commit -m "service A v1" && git push origin main
cd ..

# Populate service-b
git clone service-b.git work-b
cd work-b
echo "def world(): return 'B'" > app.py
git add app.py && git commit -m "service B v1" && git push origin main
cd ..

# Create parent
git init parent && cd parent
git submodule add ../service-a.git services/service-a
git submodule add ../service-b.git services/service-b
git commit -m "add services"
```

Expected:
```
[main a1b2c3d] add services
 3 files changed, 8 insertions(+)
```

✅ Check: `git submodule status` shows both submodules.

## Part B — foreach: check status of all submodules

```bash
cd ~/git-advanced-course/lab05/parent
git submodule foreach 'git log --oneline -1'
```

Expected:
```
Entering 'services/service-a'
a1b2c3d service A v1

Entering 'services/service-b'
b2c3d4e service B v1
```

✅ Check: both services show their latest commit.

## Part C — foreach --recursive: update all to main

```bash
cd ~/git-advanced-course/lab05/parent
git submodule foreach --recursive '
  git checkout main &&
  git branch --show-current
'
```

Expected:
```
Entering 'services/service-a'
main

Entering 'services/service-b'
main
```

✅ Check: both are on `main`.

## Part D — Set up shared hooks

```bash
cd ~/git-advanced-course/lab05/parent
mkdir .githooks
cat > .githooks/pre-commit << 'EOF'
#!/bin/sh
echo "[pre-commit] Checking for debug statements..."
if git diff --cached --name-only | xargs grep -l "DEBUG\|TODO\|FIXME" 2>/dev/null; then
    echo "[pre-commit] WARNING: Found debug/TODO/FIXME statements"
fi
exit 0
EOF
chmod +x .githooks/pre-commit
git config core.hooksPath .githooks
```

Test the hook:

```bash
echo "TODO: fix this" > todo.txt
git add todo.txt
git commit -m "add todo file"
```

Expected: you see `[pre-commit] WARNING: Found debug/TODO/FIXME statements`
before the commit output.

✅ Check: the hook runs and reports the warning.

## Part E — Configure update = merge

```bash
cd ~/git-advanced-course/lab05/parent
cat >> .gitmodules << 'EOF'

[submodule "services/service-a"]
    update = merge
EOF
cat .gitmodules
```

Expected: the `update = merge` line appears under service-a.

✅ Check: `.gitmodules` contains the merge strategy.

## Part F — Simulate multi-repo orchestration

```bash
cd ~/git-advanced-course/lab05/parent
for service in services/service-a services/service-b; do
    echo "--- $service ---"
    git -C "$service" checkout main
    git -C "$service" log --oneline -1
done
```

Expected:
```
--- services/service-a ---
Switched to branch 'main'
a1b2c3d service A v1
--- services/service-b ---
Switched to branch 'main'
b2c3d4e service B v1
```

✅ Check: the loop runs Git commands in each submodule directory.

## Part G — Simulate docker compose up --build

```bash
cd ~/git-advanced-course/lab05/parent

# Simulate the build script
echo "Building services from submodules..."
git submodule update --init --recursive
git submodule foreach 'echo "Building in $(pwd)... done"'

echo "docker compose up --build (simulated)"
echo "Services would start here"
```

Expected: all submodules are updated and the "build" completes.

✅ Check: the workflow runs without errors.

## Part H — Inspect .git/modules/

```bash
ls -la ~/git-advanced-course/lab05/parent/.git/modules/
```

Expected:
```
service-a/
service-b/
```

```bash
ls ~/git-advanced-course/lab05/parent/.git/modules/service-a/
```

Expected: includes `hooks/`, `objects/`, `refs/` — this is the submodule's Git
data stored inside the parent's `.git`.

✅ Check: each submodule has its own directory under `.git/modules/`.

## Part I — Clean up

```bash
rm -rf ~/git-advanced-course/lab05
```

✅ Check: the directory no longer exists.

---

**Next →** [Challenge 05](./challenge.md)
