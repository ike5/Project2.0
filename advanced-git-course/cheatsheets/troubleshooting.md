# Troubleshooting — Decision Tree

## "I can't checkout because of untracked/modified files"

```
Do you need the changes?
├── Yes → git stash → git checkout <branch> → git stash pop
└── No  → git checkout -f <branch>   (discards everything)
```

## "Non-fast-forward error on push"

```
Did you rebase or amend?
├── Yes → git push --force-with-lease   (safer than --force)
└── No  → git pull origin <branch> → git push
```

## "Submodule is dirty / won't update"

```
Check status: git submodule status
├── Shows '-' → not initialized → git submodule update --init --recursive
├── Shows '+' → commit mismatch → cd <submodule> && git checkout <expected>
├── Shows 'U' → merge conflict  → cd <submodule> && git merge --abort
└── Shows ' ' → clean, all good
```

## "Submodule foreach not reaching nested submodules"

```
Did you use --recursive?
├── No  → git submodule foreach --recursive '...'
└── Yes → check .gitmodules for correct paths
```

## "Detached HEAD warning"

```
Did you mean to be here?
├── No  → git checkout <branch>  (reattach to a branch)
└── Yes → proceed, or create a branch: git checkout -b temp-branch
```

## "Tag already exists on remote"

```
Do you want to overwrite?
├── Yes → git tag -d <tag> && git tag -a <tag> -m "new msg" && git push -f origin <tag>
└── No  → use a different tag name: git tag -a <tag>-v2 -m "..."
```

## "Merge conflict in submodule"

```bash
cd <submodule-path>
git log --oneline -5          # check what commits are involved
git merge --abort             # cancel the merge
git checkout main             # get back to a clean state
cd ..
git submodule update --init   # re-sync to parent's expected commit
```

## "git -C not finding the repo"

```
Is the path correct?
├── Check: ls -la <path>/.git
├── Is it a submodule? → may need --recurse-submodules
└── Use absolute path: git -C /full/path/to/repo status
```

## "Hook not running"

```
Is the hook executable?
├── Check: ls -la .git/hooks/<hook-name>
├── Not executable? → chmod +x .git/hooks/<hook-name>
└── Using hooks.path? → check shared hooks directory exists
```

## "Docker compose build failing in submodule project"

```
Are submodules initialized?
├── No  → git submodule update --init --recursive
├── Yes → check .gitmodules URLs are correct
└── Check: docker compose up --build --no-cache
```
