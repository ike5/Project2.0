# Challenge 04 — Reference Solution

## Task 1: Three-submodule project

```bash
cd ~/git-advanced-course
mkdir challenge04 && cd challenge04

# Create bare repos
git init --bare auth.git && git init --bare database.git && git init --bare cache.git

# Populate each
for lib in auth database cache; do
    git clone ${lib}.git ${lib}-work
    cd ${lib}-work
    echo "${lib} module" > ${lib}.py
    git add ${lib}.py && git commit -m "initial: ${lib}" && git push origin main
    cd ..
done

# Create parent
git init parent && cd parent
git submodule add ../auth.git libs/auth
git submodule add ../database.git libs/database
git submodule add ../cache.git libs/cache
git commit -m "add three submodules"
git submodule status
```

Expected: three submodules listed with no prefix (clean).

## Task 2: Fresh clone simulation

```bash
cd ~/git-advanced-course/challenge04
git clone parent fresh
ls fresh/libs/auth/
# Expected: empty

git -C fresh submodule update --init
ls fresh/libs/auth/
# Expected: auth.py present
```

## Task 3: Status interpretation

```bash
cd ~/git-advanced-course/challenge04/fresh
echo "modified" >> libs/auth/auth.py
git -C .. submodule status
# Expected: +hash libs/auth (dirty) — the + means commit diverged

cd libs/auth && git add auth.py && git commit -m "modify auth"
cd ../..
git -C .. submodule status
# Expected: +hash libs/auth (ahead 1) — still diverged from parent's expectation
```

The `+` prefix means the submodule's current commit differs from what the
parent recorded. After committing inside the submodule, it's "ahead" but still
not matching the parent's expected hash (which hasn't been updated yet).

## Task 4: Nested submodule

```bash
cd ~/git-advanced-course/challenge04/fresh
git -C libs/auth init --bare ../nested-dep.git
git -C libs/auth submodule add ../../nested-dep.git libs/nested-dep
git -C libs/auth commit -m "add nested submodule"
git -C libs/auth push origin main

cd ../..
git add libs/auth
git commit -m "auth has nested submodule"

# Fresh clone test
cd ~/git-advanced-course/challenge04
git clone parent nested-test
git -C nested-test submodule update --init --recursive
ls nested-test/libs/auth/libs/nested-dep/
```

Expected: the nested submodule directory is populated.

## Task 5: The -C pattern

```bash
git -C ~/git-advanced-course/challenge04/nested-test submodule update --init --recursive
```

Expected: all submodules (including nested) are initialized.

---

## Cleanup

```bash
rm -rf ~/git-advanced-course/challenge04
```
