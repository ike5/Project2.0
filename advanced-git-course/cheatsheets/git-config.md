# Git Config — Quick Reference

## Config levels (highest precedence wins)

```bash
git config --system   <key> <value>   # /etc/gitconfig — system-wide
git config --global   <key> <value>   # ~/.gitconfig — per-user
git config --local    <key> <value>   # .git/config — per-repo (default)
```

## Read config

```bash
git config --list                    # all effective values
git config --list --show-origin      # values + where they're defined
git config <key>                     # single value
```

## Essential settings

```bash
git config --global user.name "Your Name"
git config --global user.email "you@example.com"
git config --global pull.rebase true
git config --global init.defaultBranch main
git config --global core.autocrlf input   # macOS/Linux
git config --global core.autocrlf true    # Windows
```

## Advanced / situational

```bash
git config core.protectNTFS false    # force checkout on Windows edge cases
git config core.ignorecase true      # case-insensitive filesystems
git config push.default simple       # push current branch only
git config core.hooksPath .githooks  # shared hooks directory
git config submodule.recurse true    # auto-recurse submodules on pull
```

## Unset / edit

```bash
git config --global --unset <key>
git config --global --edit          # open in $EDITOR
```
