# Challenge 02 — Reference Solution

## Task 1: Lost commit recovery

```bash
mkdir /tmp/challenge02-t1 && cd /tmp/challenge02-t1
git init

# Create 5 commits
for i in 1 2 3 4 5; do echo "commit $i" > "file$i.txt" && git add "file$i.txt" && git commit -m "commit $i"; done
git log --oneline
# Expected: 5 commits

# Accidentally reset hard
git reset --hard HEAD~3
git log --oneline
# Expected: only 2 commits remain

# Reflog before recovery
git reflog
# Expected: shows the hash of "commit 5" as HEAD@{1}

# Recover
git reset --hard HEAD@{1}
git log --oneline
# Expected: all 5 commits restored

rm -rf /tmp/challenge02-t1
```

## Task 2: Interactive rebase cleanup

```bash
mkdir /tmp/challenge02-t2 && cd /tmp/challenge02-t2
git init && echo "init" > base.txt && git add base.txt && git commit -m "initial"

git checkout -b feature
echo "login" > login.txt && git add login.txt && git commit -m "feat: add login"
echo "temp" > temp.txt && git add temp.txt && git commit -m "WIP: temp fix"
echo "signup" > signup.txt && git add signup.txt && git commit -m "feat: add signup"
echo "typo" > typo.txt && git add typo.txt && git commit -m "typo fix"

git log --oneline
# Expected: 4 commits on feature

# Interactive rebase — mark "WIP" and "typo" as squash
GIT_SEQUENCE_EDITOR="sed -i 's/^pick \(.*WIP.*\)/squash \1/; s/^pick \(.*typo.*\)/squash \1/'" git rebase -i HEAD~4

git log --oneline
# Expected: 2 clean feature commits

rm -rf /tmp/challenge02-t2
```

## Task 3: Cherry-pick a fix

```bash
mkdir /tmp/challenge02-t3 && cd /tmp/challenge02-t3
git init && echo "v1" > app.txt && git add app.txt && git commit -m "v1"

git checkout -b release-v1
echo "release v1" > release.txt && git add release.txt && git commit -m "release v1"

git checkout main
echo "bugfix: null check" >> app.txt && git add app.txt && git commit -m "fix: null pointer"

# Get the bugfix commit hash
FIX_HASH=$(git rev-parse HEAD)

# Cherry-pick onto release
git checkout release-v1
git cherry-pick $FIX_HASH
git log --oneline
# Expected: the fix commit appears on release-v1

grep "bugfix" app.txt
# Expected: the fix line is present

rm -rf /tmp/challenge02-t3
```

## Task 4: Force checkout

```bash
mkdir /tmp/challenge02-t4 && cd /tmp/challenge02-t4
git init && echo "v1" > file.txt && git add file.txt && git commit -m "v1"

git checkout -b feature-experiment
echo "experiment" > experiment.txt
echo "dirty" > file.txt
git add experiment.txt  # staged: experiment.txt, modified: file.txt (unstaged)

git checkout -f main
git status
# Expected: nothing to commit, working tree clean

ls
# Expected: only file.txt (with "v1" content)

rm -rf /tmp/challenge02-t4
```
