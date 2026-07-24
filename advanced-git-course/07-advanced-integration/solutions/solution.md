# Challenge 07 — Reference Solution

## Task 1: Multi-repo status dashboard

```bash
cd ~/git-advanced-course
mkdir challenge07 && cd challenge07

# Create 4 service repos
for svc in auth api worker scheduler; do
    git init --bare ${svc}.git
    git clone ${svc}.git ${svc}-work
    cd ${svc}-work
    echo "${svc} code" > main.py
    git add main.py && git commit -m "initial: ${svc}" && git push origin main
    cd ..
done

# Create parent
git init parent && cd parent
git submodule add ../auth.git services/auth
git submodule add ../api.git services/api
git submodule add ../worker.git services/worker
git submodule add ../scheduler.git services/scheduler
git commit -m "add four services"

# Dashboard script
cat > dashboard.sh << 'EOF'
#!/bin/bash
echo "=== Service Status Dashboard ==="
printf "%-20s %-10s %-30s %s\n" "SERVICE" "BRANCH" "LAST COMMIT" "STATUS"
echo "------------------------------------------------------------"
for service in services/*; do
    name=$(basename $service)
    branch=$(git -C "$service" branch --show-current)
    last_commit=$(git -C "$service" log --oneline -1 --format="%s")
    dirty=$(git -C "$service" status --porcelain)
    if [ -z "$dirty" ]; then
        status="clean"
    else
        status="DIRTY"
    fi
    printf "%-20s %-10s %-30s %s\n" "$name" "$branch" "$last_commit" "$status"
done
EOF
chmod +x dashboard.sh

./dashboard.sh
```

Expected:
```
=== Service Status Dashboard ===
SERVICE              BRANCH     LAST COMMIT                    STATUS
------------------------------------------------------------
auth                 main       initial: auth                  clean
api                  main       initial: api                   clean
worker               main       initial: worker                clean
scheduler            main       initial: scheduler             clean
```

## Task 2: Docker Compose build pipeline

```bash
cd ~/git-advanced-course/challenge07/parent

cat > build.sh << 'EOF'
#!/bin/bash
set -euo pipefail

echo "=== Docker Compose Build Pipeline ==="

echo "[1/3] Updating submodules..."
git submodule update --init --recursive

echo "[2/3] Building services..."
for service in services/*; do
    name=$(basename $service)
    echo "  Building $name..."
    echo "    COPY $service/*.py /app/"
    echo "    RUN pip install -r requirements.txt"
done

echo "[3/3] Starting services..."
echo "  docker compose up --build -d"
echo "  STATUS:"
echo "    auth       Up 2 minutes"
echo "    api        Up 2 minutes"
echo "    worker     Up 2 minutes"
echo "    scheduler  Up 2 minutes"
EOF
chmod +x build.sh

./build.sh
```

## Task 3: Worktree hotfix workflow

```bash
cd ~/git-advanced-course/challenge07/parent

# Create a tag first
git tag -a 1.0 -m "Release 1.0"

# Create hotfix worktree
git worktree add ../hotfix-1.0.1 -b hotfix-v1.0.1 1.0

cd ../hotfix-1.0.1
echo "security fix" >> services/auth/main.py
git add services/auth
git commit -m "fix: security vulnerability in auth"
git tag -a 1.0.1 -m "Release 1.0.1: security fix"
git log --oneline --decorate
cd ..

# Clean up
git worktree remove ../hotfix-1.0.1
git worktree list
```

## Task 4: Stash and recover

```bash
cd ~/git-advanced-course/challenge07/parent

# Make changes in auth
echo "auth experiment" >> services/auth/main.py

# Make changes in api
echo "api experiment" >> services/api/main.py

# Stash separately
git -C services/auth stash push -m "auth: experimental changes"
git -C services/api stash push -m "api: experimental changes"

# Verify clean
git submodule foreach 'git status --short'

# Recover
git -C services/auth stash pop
git -C services/api stash pop

# Verify
grep "experiment" services/auth/main.py
grep "experiment" services/api/main.py
```

---

## Cleanup

```bash
rm -rf ~/git-advanced-course/challenge07
```
