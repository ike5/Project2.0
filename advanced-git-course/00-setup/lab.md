# Lab 00 — Verify and Configure

**You'll:** confirm your Git version, set identity, create a test repo, and verify
that all advanced features are available. ⏱️ ~15 min.

## Part A — Version and identity

Run:

```bash
git --version
```

Expected:
```
git version 2.x.0 or higher
```

Run:

```bash
git config --global user.name
git config --global user.email
```

Expected: both return values. If empty, set them:

```bash
git config --global user.name "Your Name"
git config --global user.email "you@example.com"
```

Verify:

```bash
git config --global user.name
```

Expected:
```
Your Name
```

✅ Check: both `user.name` and `user.email` return non-empty values.

## Part B — Create a test repo

```bash
mkdir -p ~/git-advanced-course/lab00 && cd ~/git-advanced-course/lab00
git init
```

Expected:
```
Initialized empty Git repository in /Users/you/git-advanced-course/lab00/.git/
```

```bash
echo "hello advanced git" > README.md
git add README.md
git commit -m "initial commit"
```

Expected:
```
[main (root-commit) a1b2c3d] initial commit
 1 file changed, 1 insertion(+)
 create mode 100644 README.md
```

✅ Check: `git log --oneline` shows your commit.

## Part C — Inspect config

```bash
git config --local --list
```

Expected: shows repo-specific settings (at minimum the `core.repositoryformatversion`,
`core.filemode`, etc.).

```bash
git config --list --show-origin | grep user
```

Expected: shows your `user.name` and `user.email` with origin `~/.gitconfig`.

✅ Check: config output includes your identity from the global config.

## Part D — Verify submodule support

```bash
cd ~/git-advanced-course/lab00
git submodule --help 2>&1 | head -5
```

Expected: the submodule help text appears (not "unknown command").

✅ Check: submodule help text is displayed.

## Part E — Clean up

```bash
rm -rf ~/git-advanced-course/lab00
```

✅ Check: the directory no longer exists.

---

**Next →** [Challenge 00](./challenge.md)
