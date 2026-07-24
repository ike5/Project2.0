# Challenge 08 — Reference Solution

## Task 1: Multi-developer simulation

```bash
cd ~/git-advanced-course
mkdir challenge08 && cd challenge08

# Clone from capstone (or recreate)
# Assuming platform repo exists from capstone, or create fresh:
# ... (setup omitted for brevity — same structure as capstone)

# Alice clones and updates auth
git clone platform alice
cd alice
git submodule update --init --recursive
echo "def rate_limit(requests, limit=100): return len(requests) <= limit" >> services/auth-service/main.py
git add services/auth-service
git commit -m "feat: add rate limiting to auth"
git push origin main
cd ..

# Bob clones and updates worker
git clone platform bob
cd bob
git submodule update --init --recursive
echo "def retry(job, max_attempts=3): return attempt(job, max_attempts)" >> services/worker-service/main.py
git add services/worker-service
git commit -m "feat: add retry logic to worker"
git push origin main
cd ..

# Third person pulls both
git clone platform integration
cd integration
git submodule update --init --recursive
git pull origin main  # gets Alice's change
cd services/worker-service
git pull origin main  # gets Bob's change
cd ../..

git submodule foreach 'git log --oneline -1'
```

## Task 2: shared-lib cascade

```bash
cd ~/git-advanced-course/challenge08

git init --bare shared-lib.git
git clone shared-lib.git shared-lib-work
cd shared-lib-work
echo "def common(): return 'shared'" > common.py
git add common.py && git commit -m "v1.0: shared library" && git push origin main
cd ..

# Add shared-lib to platform
cd platform
git submodule add ../shared-lib.git libs/shared-lib
git commit -m "add shared-lib"

# api-gateway and auth-service reference it
cd services/api-gateway
git submodule add ../../shared-lib.git libs/shared-lib
git commit -m "add shared-lib dependency"
git push origin main
cd ../../

cd services/auth-service
git submodule add ../../shared-lib.git libs/shared-lib
git commit -m "add shared-lib dependency"
git push origin main
cd ../../

# Update shared-lib in parent
git -C libs/shared-lib pull origin main
git add libs/shared-lib
git commit -m "update shared-lib pointer"
```

## Task 3: Release automation

```bash
cd ~/git-advanced-course/challenge08/platform

cat > release.sh << 'EOF'
#!/bin/bash
set -euo pipefail

VERSION=$1
if [ -z "$VERSION" ]; then
    echo "Usage: ./release.sh <version>"
    exit 1
fi

echo "=== Releasing v${VERSION} ==="

# Tag platform
git tag -a "$VERSION" -m "Release $VERSION"
echo "Tagged platform: $VERSION"

# Tag each service
for service in services/*; do
    name=$(basename $service)
    git -C "$service" tag -a "$VERSION" -m "$name $VERSION"
    echo "Tagged $name: $VERSION"
done

# Push all tags
git push origin "$VERSION"
for service in services/*; do
    git -C "$service" push origin "$VERSION"
done

echo ""
echo "=== Release Summary ==="
echo "Platform:  $VERSION"
for service in services/*; do
    name=$(basename $service)
    echo "$name: $VERSION"
done
echo "=== Done ==="
EOF
chmod +x release.sh

./release.sh 2.1.0
```

## Task 4: Recovery scenario

```bash
cd ~/git-advanced-course/challenge08
git clone platform recovery-test
cd recovery-test
git submodule update --init --recursive

# Accidentally reset hard
git reset --hard HEAD~5

# Recover with reflog
git reflog
# Find the hash before the reset
git reset --hard HEAD@{1}

# Verify submodules
git submodule status
git submodule foreach 'git log --oneline -1'
```

---

## Cleanup

```bash
rm -rf ~/git-advanced-course/challenge08
rm -rf ~/git-advanced-course
```
