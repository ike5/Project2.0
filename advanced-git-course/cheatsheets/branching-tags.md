# Branching, Tags & Force Operations — Quick Reference

## Branch operations

```bash
git branch                        # list local branches
git branch -a                     # list all (local + remote)
git branch -d <branch>            # delete (safe — only if merged)
git branch -D <branch>            # delete (force — even if unmerged)
git branch -m <old> <new>         # rename a branch
git branch --show-current         # print current branch name
```

## Force checkout

```bash
git checkout -f main              # switch to main, discard all local changes
git checkout -B my-branch <ref>   # create/reset branch at ref
git switch -c <branch>            # create + switch (modern syntax)
```

## Reset (three modes)

```bash
git reset --soft HEAD~1           # undo commit, keep staged changes
git reset --mixed HEAD~1          # undo commit, unstage changes (default)
git reset --hard HEAD~1           # undo commit, discard everything
```

## Reflog (safety net)

```bash
git reflog                        # show all HEAD movements
git checkout abc123               # recover a "lost" commit
git reset --hard HEAD@{2}         # reset to a reflog entry
```

## Rebase

```bash
git rebase main                   # replay current branch on top of main
git rebase -i HEAD~5              # interactive rebase (squash, edit, reorder)
git rebase --abort                # cancel a conflicted rebase
git rebase --continue             # after resolving conflicts
```

## Cherry-pick

```bash
git cherry-pick abc123            # apply a single commit
git cherry-pick abc123..def456    # apply a range
git cherry-pick --no-commit abc   # apply without committing
```

## Tagging

```bash
git tag v1.0                      # lightweight tag
git tag -a v1.0 -m "Release 1.0" # annotated tag
git tag                           # list tags
git tag -d v1.0                   # delete local tag
git push origin v1.0              # push a single tag
git push --tags                   # push all tags
git push origin :refs/tags/v1.0   # delete remote tag
```

## Stash

```bash
git stash                         # stash changes
git stash list                    # list stashes
git stash pop                     # apply + remove latest stash
git stash apply stash@{2}         # apply a specific stash
git stash drop                    # remove latest stash
```
