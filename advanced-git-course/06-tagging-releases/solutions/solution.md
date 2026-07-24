# Challenge 06 — Reference Solution

## Task 1: Semantic versioning sequence

```bash
mkdir ~/git-advanced-course/challenge06 && cd ~/git-advanced-course/challenge06
git init versioned-project && cd versioned-project

echo "initial" > app.py && git add app.py && git commit -m "v1.0: initial"
git tag -a 1.0 -m "Release 1.0: initial stable release"

echo "feature A" >> app.py && git add app.py && git commit -m "v1.1: add feature A"
git tag -a 1.1 -m "Release 1.1: added feature A"

echo "bugfix" >> app.py && git add app.py && git commit -m "v1.1.1: fix critical bug"
git tag -a 1.1.1 -m "Release 1.1.1: critical bugfix"

echo "feature B" >> app.py && git add app.py && git commit -m "v1.2: add feature B"
git tag -a 1.2 -m "Release 1.2: added feature B"

echo "BREAKING: new API" > app.py && git add app.py && git commit -m "v2.0: breaking change"
git tag -a 2.0 -m "Release 2.0: breaking API change"

echo "hotfix" >> app.py && git add app.py && git commit -m "v2.0.1: hotfix"
git tag -a 2.0.1 -m "Release 2.0.1: hotfix for v2.0"

git tag -n1
```

Expected:
```
1.0         Release 1.0: initial stable release
1.1         Release 1.1: added feature A
1.1.1       Release 1.1.1: critical bugfix
1.2         Release 1.2: added feature B
2.0         Release 2.0: breaking API change
2.0.1       Release 2.0.1: hotfix for v2.0
```

## Task 2: Tag a submodule project

```bash
cd ~/git-advanced-course/challenge06
git init --bare sublib.git
git clone sublib.git sublib-work
cd sublib-work
echo "library code" > lib.py && git add lib.py && git commit -m "initial" && git push origin main
cd ..

git init parent-with-sub && cd parent-with-sub
git submodule add ../sublib.git libs/sublib
git commit -m "add submodule"

# Tag both
git tag -a 1.0 -m "Parent v1.0"
git -C libs/sublib tag -a 1.0.0 -m "Sublib v1.0.0"

# Create bare remote and push
cd ..
git init --bare parent-remote.git
git clone parent-remote.git parent-push
cd parent-push
git remote add source ../parent-with-sub
git fetch source
git push source main
git push source --tags
cd ..

# Verify tags
git -C parent-remote.git tag -l
git -C sublib.git tag -l
```

## Task 3: Check out old release

```bash
cd ~/git-advanced-course/challenge06/versioned-project
git checkout -b hotfix-1.1.x 1.1.1
echo "security patch" >> app.py
git add app.py && git commit -m "security patch"
git tag -a 1.1.2 -m "Release 1.1.2: security patch"
git log --oneline --decorate
```

Expected:
```
a1b2c3d (HEAD -> hotfix-1.1.x, tag: 1.1.2) security patch
c1d2e3f (tag: 1.1.1) v1.1.1: fix critical bug
...
```

## Task 4: Delete and recover

```bash
cd ~/git-advanced-course/challenge06/versioned-project
git tag -d 2.0
git tag -l | grep 2.0
# Expected: only 2.0.1 (2.0 is gone)

git reflog | head -10
# Find the commit hash before tag creation

git tag -a 2.0 HEAD@{1} -m "Release 2.0: breaking API change (recovered)"
git tag -l | grep 2.0
# Expected: both 2.0 and 2.0.1
```

---

## Cleanup

```bash
rm -rf ~/git-advanced-course/challenge06
```
