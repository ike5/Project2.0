# Glossary — Advanced Git

Plain-English definitions for every domain-specific term in this course,
organized by topic.

---

## Git Config

| Term | Definition |
|------|------------|
| **Git config** | A key-value settings file that controls how Git behaves. Settings can live at system, global, or local (repository) level. |
| **core.protectNTFS** | A Git setting (default `true`) that prevents file paths with characters that are invalid on NTFS (Windows filesystem). Set to `false` when you need to force operations on Windows. |
| **core.autocrlf** | Controls how Git handles line endings. `true` converts CRLF on checkout; `input` converts on commit only. |
| **core.ignorecase** | Tells Git whether the filesystem is case-insensitive (macOS/Windows) or case-sensitive (Linux). |
| **pull.rebase** | A config setting that makes `git pull` default to `git pull --rebase` instead of creating merge commits. |
| **push.default** | Controls what `git push` pushes when no refspec is given. `simple` (default) pushes the current branch to a matching remote branch. |
| **user.name / user.email** | Identity settings — who Git says authored each commit. |

---

## Branching & Force Operations

| Term | Definition |
|------|------------|
| **Force checkout** | `git checkout -f` or `git checkout -B` — switches branches and discards all local changes (staged and unstaged) without warning. |
| **Hard reset** | `git reset --hard` — moves HEAD and the working tree, discarding all changes. Destructive. |
| **Soft reset** | `git reset --soft` — moves HEAD but leaves the staging area and working tree untouched. |
| **Mixed reset** | `git reset --mixed` (default) — moves HEAD and unstages changes, but keeps them in the working tree. |
| **Detach HEAD** | Checking out a commit (not a branch) — you're no longer on any branch. Changes here are easily lost. |
| **Reflog** | Git's safety net — a log of every HEAD movement. Used to recover "lost" commits after resets or force operations. |

---

## Remote Operations

| Term | Definition |
|------|------------|
| **Remote** | A named connection to another repository (usually on GitHub/GitLab). The default remote is named `origin`. |
| **Fetch** | Downloads commits and refs from a remote but doesn't merge them into your working tree. |
| **Pull** | `git pull` = `git fetch` + `git merge` (or `git rebase` if `pull.rebase = true`). |
| **Upstream** | The branch on the remote that your local branch tracks. `origin/main` is the upstream of `main`. |
| **Fast-forward** | When you pull and your local branch has no new commits, Git can simply move the pointer forward — no merge commit needed. |
| **Non-fast-forward** | When your local branch has diverged from the remote. Requires a merge or rebase to reconcile. |

---

## Submodules

| Term | Definition |
|------|------------|
| **Submodule** | A Git repository embedded inside another Git repository. The parent repo tracks a specific commit of the submodule, not its branches. |
| **.gitmodules** | A file in the parent repo root that defines which submodules exist and where they live (path + URL). |
| **submodule add** | Clones a repository and registers it as a submodule in `.gitmodules` and the index. |
| **submodule update** | Checks out the exact commit the parent repo expects. `--init` initializes submodules that haven't been set up yet. `--recursive` does the same for nested submodules. |
| **submodule foreach** | Runs a shell command inside every submodule. Use `--recursive` to also run it in nested submodules. |
| **Submodule tracking** | The parent repo stores a commit hash for each submodule. `git submodule update` checks out that exact commit. |
| **Submodule branch tracking** | An alternative where `.gitmodules` specifies `branch = main`, so `git submodule update --remote` fetches the latest from that branch. |
| **Submodule merge strategy** | `.gitmodules` can set `update = merge` so that `git submodule update` merges the tracked commit instead of checking it out (preserving local changes). |
| **.git/modules/** | Internal directory where Git stores submodule data. The submodule's `.git` is actually a file pointing here. |

---

## Tagging & Releases

| Term | Definition |
|------|------------|
| **Lightweight tag** | A simple pointer to a commit — like a branch that doesn't move. `git tag v1.0`. |
| **Annotated tag** | A tag object with a message, author, date, and optional GPG signature. `git tag -a v1.0 -m "Release 1.0"`. |
| **Tag ref** | A reference like `refs/tags/v1.0` that points to a tag object or commit. |
| **Semantic versioning** | A version numbering convention: `MAJOR.MINOR.PATCH` (e.g., `2.0.32`). |
| **Tag push** | Tags don't push automatically. You must `git push origin <tag>` or `git push --tags` to share them. |
| **Delete tag** | `git tag -d v1.0` deletes locally; `git push origin :refs/tags/v1.0` deletes remotely. |

---

## Hooks & Automation

| Term | Definition |
|------|------------|
| **Git hook** | A script that runs automatically at specific Git events (commit, push, merge, etc.). Lives in `.git/hooks/`. |
| **pre-commit hook** | Runs before a commit is created. Used for linting, formatting, and checks. |
| **pre-push hook** | Runs before `git push` executes. Used for running tests or validation. |
| **commit-msg hook** | Runs after you write a commit message. Used for enforcing message format (e.g., conventional commits). |
| **hooks.path** | Git config that lets you store hooks in a shared directory instead of `.git/hooks/`. |

---

## Integration & Advanced

| Term | Definition |
|------|------------|
| **git -C** | A flag that tells Git to run commands in a different directory. `git -C path/to/repo status` runs `git status` in that repo. |
| **Worktree** | A working directory linked to a repo. `git worktree add` lets you check out multiple branches simultaneously in separate directories. |
| **Cherry-pick** | Applying a specific commit from one branch onto another. `git cherry-pick abc123`. |
| **Bisect** | Binary search through commit history to find which commit introduced a bug. `git bisect start`, `git bisect good`, `git bisect bad`. |
| **Stash** | Temporarily shelves uncommitted changes so you can switch branches. `git stash`, `git stash pop`. |
| **Sparse checkout** | Checking out only part of a repository's tree. Useful for very large monorepos. |
