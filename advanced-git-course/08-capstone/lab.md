# Lab 08 — Build the Capstone

**You'll:** create a complete multi-service platform project using every concept
from this course. Follow each part in order. ⏱️ ~80 min.

## Part A — Project setup and config

```bash
cd ~/git-advanced-course
mkdir capstone && cd capstone

# Configure the project
git init platform
cd platform

# Apply advanced config
git config core.protectNTFS false
git config core.protectNTFS true  # re-enable after setup
git config pull.rebase true
git config push.default simple
git config submodule.recurse true
git config init.defaultBranch main
```

Verify config:

```bash
git config --list --show-origin | grep -E "(pull.rebase|push.default|submodule.recurse)"
```

Expected:
```
file:.git/config       pull.rebase=true
file:.git/config       push.default=simple
file:.git/config       submodule.recurse=true
```

✅ Check: all three settings are active.

## Part B — Create the service repos

```bash
cd ~/git-advanced-course/capstone

# Create bare repos for each service
for svc in api-gateway auth-service worker-service; do
    git init --bare ${svc}.git
done

# Populate api-gateway
git clone api-gateway.git api-gateway-work
cd api-gateway-work
cat > main.py << 'EOF'
"""API Gateway - routes requests to services"""
def route(request):
    if request.path.startswith("/auth"):
        return forward_to("auth-service", request)
    elif request.path.startswith("/jobs"):
        return forward_to("worker-service", request)
    return {"status": 404}
EOF
cat > requirements.txt << 'EOF'
flask>=3.0
requests>=2.31
EOF
git add . && git commit -m "v1.0: initial API gateway" && git push origin main
cd ..

# Populate auth-service
git clone auth-service.git auth-service-work
cd auth-service-work
cat > main.py << 'EOF'
"""Auth Service - handles authentication"""
def authenticate(token):
    return validate_token(token)
def validate_token(token):
    return {"valid": True, "user": "demo"}
EOF
git add . && git commit -m "v1.0: initial auth service" && git push origin main
cd ..

# Populate worker-service
git clone worker-service.git worker-service-work
cd worker-service-work
cat > main.py << 'EOF'
"""Worker Service - processes background jobs"""
def process_job(job):
    return {"status": "completed", "job": job}
def queue_job(job_type, payload):
    return {"queued": True, "type": job_type}
EOF
git add . && git commit -m "v1.0: initial worker service" && git push origin main
cd ..
```

✅ Check: all three services have content.

## Part C — Add submodules with merge strategy

```bash
cd ~/git-advanced-course/capstone/platform
git submodule add ../api-gateway.git services/api-gateway
git submodule add ../auth-service.git services/auth-service
git submodule add ../worker-service.git services/worker-service
```

Configure merge strategy:

```bash
cat > .gitmodules << 'EOF'
[submodule "services/api-gateway"]
    path = services/api-gateway
    url = ../api-gateway.git
    branch = main
    update = merge
[submodule "services/auth-service"]
    path = services/auth-service
    url = ../auth-service.git
    branch = main
    update = merge
[submodule "services/worker-service"]
    path = services/worker-service
    url = ../worker-service.git
    branch = main
    update = merge
EOF

git add .
git commit -m "platform: add three services as submodules with merge strategy"
```

Verify:

```bash
git submodule status
cat .gitmodules
```

Expected: all three submodules listed, `.gitmodules` has `update = merge`.

✅ Check: submodules added with merge strategy.

## Part D — Set up shared hooks

```bash
cd ~/git-advanced-course/capstone/platform
mkdir .githooks

cat > .githooks/pre-commit << 'HOOK'
#!/bin/sh
echo "[pre-commit] Running quality checks..."
ERRORS=0

# Check for debug statements
if git diff --cached --name-only | xargs grep -l "print(" 2>/dev/null; then
    echo "[pre-commit] WARNING: Found print() statements"
fi

# Check for TODO comments
if git diff --cached --name-only | xargs grep -l "TODO\|FIXME" 2>/dev/null; then
    echo "[pre-commit] WARNING: Found TODO/FIXME comments"
fi

exit $ERRORS
HOOK
chmod +x .githooks/pre-commit

git config core.hooksPath .githooks
```

Apply to submodules:

```bash
git submodule foreach 'git config core.hooksPath ../../.githooks'
```

Test:

```bash
echo 'print("debug")' > test.py
git add test.py
git commit -m "test hook"
rm test.py
git reset HEAD~1
```

Expected: hook runs and shows warning.

✅ Check: shared hooks work in parent and all submodules.

## Part E — Create initial release

```bash
cd ~/git-advanced-course/capstone/platform
git add .
git commit -m "platform: complete initial setup"

# Create release tags
git tag -a 2.0.0 -m "Release 2.0.0: platform with three services"
git -C services/api-gateway tag -a 1.0.0 -m "api-gateway v1.0.0"
git -C services/auth-service tag -a 1.0.0 -m "auth-service v1.0.0"
git -C services/worker-service tag -a 1.0.0 -m "worker-service v1.0.0"
```

Verify:

```bash
git tag -n1
git submodule foreach 'git tag -n1'
```

✅ Check: all tags are in place.

## Part F — Simulate development and updates

```bash
cd ~/git-advanced-course/capstone/platform

# Simulate someone updating api-gateway
cd services/api-gateway
echo "def health_check(): return {'status': 'ok'}" >> main.py
git add main.py && git commit -m "feat: add health check endpoint" && git push origin main
cd ../../

# Pull the update using foreach
git submodule foreach --recursive '
  git checkout main &&
  git pull origin main
'
```

Check the updated status:

```bash
git submodule status
```

Expected: `api-gateway` shows `+` (diverged from parent's recorded commit).

Update the parent's pointer:

```bash
git add services/
git commit -m "platform: update api-gateway to include health check"
```

✅ Check: submodule pointer is updated.

## Part G — Hotfix scenario

```bash
cd ~/git-advanced-course/capstone/platform

# Create a worktree for the hotfix
git worktree add ../hotfix-2.0.1 -b hotfix-v2.0.1 2.0.0

cd ../hotfix-2.0.1

# Fix in auth-service
echo "def sanitize(input): return input.strip()" >> services/auth-service/main.py
git add services/auth-service
git commit -m "fix: sanitize auth inputs"

# Tag the hotfix
git tag -a 2.0.1 -m "Release 2.0.1: security fix in auth"
git -C services/auth-service tag -a 1.0.1 -m "auth-service v1.0.1: security fix"

# Push
git push origin hotfix-v2.0.1
git push origin 2.0.1
git -C services/auth-service push origin 1.0.1
```

Clean up worktree:

```bash
cd ~/git-advanced-course/capstone/platform
git worktree remove ../hotfix-2.0.1
```

✅ Check: hotfix applied, tagged, and worktree removed.

## Part H — Simulate Docker Compose build

```bash
cd ~/git-advanced-course/capstone/platform

cat > docker-compose.yml << 'EOF'
version: '3.8'
services:
  api-gateway:
    build: ./services/api-gateway
    ports:
      - "8000:8000"
  auth-service:
    build: ./services/auth-service
    ports:
      - "8001:8001"
  worker-service:
    build: ./services/worker-service
    ports:
      - "8002:8002"
EOF

# Simulate the build workflow
echo "=== Docker Compose Build Workflow ==="
echo "Step 1: git submodule update --init --recursive"
git submodule update --init --recursive

echo "Step 2: docker compose up --build"
echo "  Building api-gateway..."
echo "  Building auth-service..."
echo "  Building worker-service..."

echo "Step 3: docker compose ps"
echo "  NAME                STATUS          PORTS"
echo "  api-gateway         Up 2 min        0.0.0.0:8000->8000/tcp"
echo "  auth-service        Up 2 min        0.0.0.0:8001->8001/tcp"
echo "  worker-service      Up 2 min        0.0.0.0:8002->8002/tcp"
```

✅ Check: Docker workflow completes.

## Part I — Final verification

```bash
cd ~/git-advanced-course/capstone/platform

echo "=== Platform Summary ==="
echo ""
echo "Submodules:"
git submodule status
echo ""
echo "Tags:"
git tag -n1
echo ""
echo "Config:"
git config pull.rebase
git config push.default
git config submodule.recurse
git config core.hooksPath
echo ""
echo "Last 5 commits:"
git log --oneline -5
```

✅ Check: all components are properly configured.

## Part J — Clean up

```bash
rm -rf ~/git-advanced-course/capstone
```

✅ Check: the directory no longer exists.

---

**You've completed the Advanced Git course!** You can now handle submodules,
force operations, multi-repo orchestration, tagging, hooks, and Docker
integration with confidence.
