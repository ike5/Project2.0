# Challenge 00 — Reference Solution

## Task 1: Create and destroy a test repo

```bash
mkdir /tmp/test-repo && cd /tmp/test-repo
git init
echo "test" > file.txt
git add file.txt
git commit -m "test commit"
git log --oneline
cd /
rm -rf /tmp/test-repo
```

Expected: a commit appears in `git log`, then the directory is removed.

## Task 2: Local config override

```bash
mkdir /tmp/config-repo && cd /tmp/config-repo
git init
git config user.name "Local User"
git config user.email "local@example.com"
git config --list --show-origin | grep user
cd /
rm -rf /tmp/config-repo
```

Expected: the `--show-origin` output shows `local` for user.name and user.email,
overriding the global `~/.gitconfig` values.

## Task 3: Submodule subcommands

```bash
git submodule -h 2>&1 | grep -E "^\s+(init|update|foreach|add)"
```

Expected: all four subcommands appear in the output.

## Task 4: Working directory

```bash
mkdir -p ~/git-advanced-course
ls -d ~/git-advanced-course
```

Expected: the directory exists.
