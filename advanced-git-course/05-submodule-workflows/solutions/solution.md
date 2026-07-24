# Challenge 05 — Reference Solution

## Task 1: Three-service orchestration

```bash
cd ~/git-advanced-course
mkdir challenge05 && cd challenge05

# Create bare repos
for svc in api worker scheduler; do
    git init --bare ${svc}.git
    git clone ${svc}.git ${svc}-work
    cd ${svc}-work
    echo "${svc} service" > main.py
    git add main.py && git commit -m "initial: ${svc}" && git push origin main
    cd ..
done

# Create parent
git init parent && cd parent
git submodule add ../api.git services/api
git submodule add ../worker.git services/worker
git submodule add ../scheduler.git services/scheduler
git commit -m "add three services"

# Orchestrate with git -C
for service in services/api services/worker services/scheduler; do
    echo "--- $service ---"
    git -C "$service" checkout main
    git -C "$service" pull origin main
done
```

Expected: all three services checked out and pulled.

## Task 2: foreach batch update

```bash
cd ~/git-advanced-course/challenge05/parent

# List latest commits
git submodule foreach --recursive 'echo "$(pwd): $(git log --oneline -1)"'

# Create BUILD.md in each
git submodule foreach --recursive '
    BRANCH=$(git branch --show-current)
    HASH=$(git rev-parse --short HEAD)
    echo "# BUILD INFO" > BUILD.md
    echo "Branch: $BRANCH" >> BUILD.md
    echo "Commit: $HASH" >> BUILD.md
'

# Verify
git submodule foreach 'cat BUILD.md'
```

## Task 3: Shared pre-push hook

```bash
cd ~/git-advanced-course/challenge05/parent

mkdir .githooks
cat > .githooks/pre-push << 'HOOK'
#!/bin/sh
echo "[pre-push] Checking submodule status..."
DIRTY=$(git submodule status --recursive | grep -E "^[+-]" | head -5)
if [ -n "$DIRTY" ]; then
    echo "[pre-push] ERROR: Submodules are not at expected commits:"
    echo "$DIRTY"
    echo "[pre-push] Run: git submodule update --init --recursive"
    exit 1
fi
echo "[pre-push] All submodules clean."
exit 0
HOOK
chmod +x .githooks/pre-push

# Configure hooks path in each submodule
for sub in services/api services/worker services/scheduler; do
    git -C "$sub" config core.hooksPath ../../.githooks
done

# Test: modify without committing (should show dirty)
cd services/api
echo "dirty" >> main.py
cd ../..

# Try to push from submodule (hook should catch it)
git -C services/api add main.py
# Note: pre-push hook runs on push, not commit
# To test the hook logic directly:
git submodule status --recursive | grep -E "^[+-]"
```

## Task 4: update = merge

```bash
cd ~/git-advanced-course/challenge05/parent

# Set merge strategy for all
cat > .gitmodules << 'EOF'
[submodule "services/api"]
    path = services/api
    url = ../api.git
    update = merge
[submodule "services/worker"]
    path = services/worker
    url = ../worker.git
    update = merge
[submodule "services/scheduler"]
    path = services/scheduler
    url = ../scheduler.git
    update = merge
EOF

git add .gitmodules
git commit -m "set update = merge for all submodules"
```

Explanation: "The merge strategy preserves local changes in submodules when
updating, instead of doing a hard checkout that discards them — useful when
developers experiment locally before pushing upstream."

---

## Cleanup

```bash
rm -rf ~/git-advanced-course/challenge05
```
