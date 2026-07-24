# VERIFY.md — Environment Smoke Test

Run these steps in order to confirm your environment is ready for the
Advanced Git course. Each step shows the command and the expected output.

---

## Step 1: Git version

```bash
git --version
```

Expected:
```
git version 2.x.0 or higher
```

Git 2.40+ is recommended for modern submodule and config features. If your
version is older, update with your system's package manager.

---

## Step 2: Global config identity

```bash
git config --global user.name
git config --global user.email
```

Expected: both should return your name and email. If either returns empty:
```bash
git config --global user.name "Your Name"
git config --global user.email "you@example.com"
```

---

## Step 3: Create a temporary test repo

```bash
mkdir /tmp/git-verify && cd /tmp/git-verify && git init
```

Expected:
```
Initialized empty Git repository in /tmp/git-verify/.git/
```

---

## Step 4: Basic commit round-trip

```bash
echo "verify" > test.txt && git add test.txt && git commit -m "test"
git log --oneline
```

Expected:
```
a1b2c3d test
```

---

## Step 5: Clean up

```bash
rm -rf /tmp/git-verify
```

Expected: no output (directory removed).

---

## Step 6: Verify submodule tools (for Modules 04–05)

```bash
git submodule --version
```

Expected:
```
git submodule version
```

Or simply no error. Git includes submodule support by default.

---

## Step 7: Verify Docker (for Module 07 and capstone)

```bash
docker --version
docker compose version
```

Expected:
```
Docker version 24.x.x or higher
Docker Compose version v2.x.x or higher
```

If Docker is not installed, skip the Docker-specific labs. Every module
has non-Docker alternatives in the challenge tasks.

---

## Step 8: Verify SSH or HTTPS access to GitHub

```bash
ssh -T git@github.com
```

Expected:
```
Hi username! You've successfully authenticated...
```

If SSH fails, try HTTPS:
```bash
git ls-remote https://github.com/octocat/Hello-World.git
```

Expected: a list of refs (branches and tags).

---

## All checks passed

You're ready to start Module 00.
