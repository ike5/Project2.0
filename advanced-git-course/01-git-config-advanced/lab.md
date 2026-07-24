# Lab 01 — Configure, Break, and Fix

**You'll:** set advanced config, create a repo with a "bad" filename, toggle
`core.protectNTFS`, configure pull behavior, and share hooks via config. ⏱️ ~40 min.

## Part A — Inspect your current config

```bash
cd ~/git-advanced-course
mkdir lab01 && cd lab01
git init
```

Expected:
```
Initialized empty Git repository in /Users/you/git-advanced-course/lab01/.git/
```

```bash
git config --list --show-origin
```

Expected: a long list showing system, global, and local settings. Notice that
each entry has a `file:` prefix indicating its origin.

✅ Check: you see settings from `/etc/gitconfig`, `~/.gitconfig`, and
`.git/config`.

## Part B — Set and verify pull.rebase

```bash
git config --global pull.rebase
```

Expected: either empty (not set) or `true`/`false`.

```bash
git config --global pull.rebase true
git config --global pull.rebase
```

Expected:
```
true
```

✅ Check: `git config --global pull.rebase` returns `true`.

## Part C — Set init.defaultBranch

```bash
git config --global init.defaultBranch main
git config --global init.defaultBranch
```

Expected:
```
main
```

✅ Check: new repos will use `main` as the default branch.

## Part D — Create a repo with a "dangerous" filename

We'll create a file that would fail on NTFS. This simulates cross-platform
issues:

```bash
cd ~/git-advanced-course/lab01
echo "cross-platform file" > "file:name.txt"
git add "file:name.txt"
git commit -m "add file with colon in name"
```

Expected:
```
[main a1b2c3d] add file with colon in name
 1 file changed, 1 insertion(+)
 create mode 100644 file:name.txt
```

If your system rejects the colon in the filename, that's expected on some
filesystems. Skip to Part E.

✅ Check: `git log --oneline` shows the commit.

## Part E — Toggle core.protectNTFS

```bash
git config core.protectNTFS
```

Expected: on macOS/Linux this may be empty (default is irrelevant). On Windows
it would show `true`.

```bash
git config core.protectNTFS false
git config core.protectNTFS
```

Expected:
```
false
```

Now re-enable it:

```bash
git config core.protectNTFS true
git config core.protectNTFS
```

Expected:
```
true
```

✅ Check: you successfully toggled the setting off and back on.

## Part F — Set a shared hooks path

```bash
cd ~/git-advanced-course/lab01
mkdir .githooks
cat > .githooks/pre-commit << 'EOF'
#!/bin/sh
echo "pre-commit hook running..."
exit 0
EOF
chmod +x .githooks/pre-commit
git config core.hooksPath .githooks
git config core.hooksPath
```

Expected:
```
.githooks
```

Now test the hook:

```bash
echo "test" > hook-test.txt
git add hook-test.txt
git commit -m "test hook"
```

Expected: you should see `pre-commit hook running...` before the commit output.

✅ Check: the hook message appears.

## Part G — Set submodule.recurse

```bash
git config --global submodule.recurse true
git config --global submodule.recurse
```

Expected:
```
true
```

✅ Check: `git pull` will now auto-update submodules.

## Part H — Set push.default

```bash
git config --global push.default simple
git config --global push.default
```

Expected:
```
simple
```

✅ Check: `git push` without arguments pushes only the current branch.

## Part I — Clean up

```bash
rm -rf ~/git-advanced-course/lab01
```

✅ Check: the directory no longer exists.

---

**Next →** [Challenge 01](./challenge.md)
