# Challenge 01 — Reference Solution

## Task 1: Project repo with local identity

```bash
mkdir ~/git-advanced-course/challenge01 && cd ~/git-advanced-course/challenge01
git init
git config user.name "Project Lead"
git config user.email "lead@project.dev"

# Verify
git config --list --show-origin | grep user
```

Expected: local config shows "Project Lead" and "lead@project.dev" with origin `.git/config`,
while global settings still show your personal identity.

## Task 2: Pull rebase and push default

```bash
git config pull.rebase true
git config --global push.default simple

# Verify
git config pull.rebase
git config --global push.default
```

Expected: both return the values we set.

## Task 3: Commit-msg hook

```bash
mkdir .githooks
cat > .githooks/commit-msg << 'EOF'
#!/bin/sh
msg=$(cat "$1")
if [ ${#msg} -lt 10 ]; then
    echo "ERROR: Commit message must be at least 10 characters."
    echo "Your message: '$msg' (${#msg} characters)"
    exit 1
fi
EOF
chmod +x .githooks/commit-msg
git config core.hooksPath .githooks

# Test: short message (should fail)
echo "test" > file.txt
git add file.txt
git commit -m "short" 2>&1 | head -5
# Expected: ERROR: Commit message must be at least 10 characters.

# Test: long message (should succeed)
git commit -m "this is a valid commit message" --allow-empty 2>&1 | head -5
# Expected: commit succeeds
```

## Task 4: Submodule auto-recurse

```bash
git config --global submodule.recurse true
git config --global submodule.recurse
```

Explanation: "This setting makes `git pull` and `git fetch` automatically
recurse into submodules, so you never forget to update them after pulling."

## Task 5: Config documentation

```bash
git config --list --show-origin
```

Example output with origins:
```
file:/etc/gitconfig    core.repositoryformatversion=0
file:/etc/gitconfig    core.filemode=true
file:~/.gitconfig      user.name=Your Name
file:~/.gitconfig      user.email=you@example.com
file:~/.gitconfig      pull.rebase=true
file:~/.gitconfig      push.default=simple
file:~/.gitconfig      submodule.recurse=true
file:.git/config       core.repositoryformatversion=0
file:.git/config       core.hooksPath=.githooks
file:.git/config       user.name=Project Lead
file:.git/config       user.email=lead@project.dev
file:.git/config       pull.rebase=true
```

---

## Cleanup

```bash
rm -rf ~/git-advanced-course/challenge01
```
