# Submodule Commands — Quick Reference

## Add a submodule

```bash
git submodule add <url> <path>
# Example:
git submodule add https://github.com/user/lib.git libs/lib
```

## Clone a repo with submodules (one step)

```bash
git clone --recurse-submodules <url>
```

## Initialize + update all submodules

```bash
git submodule update --init --recursive
```

## Update submodules to latest remote commits

```bash
git submodule update --remote --merge
# or
git submodule update --remote --rebase
```

## Run a command in every submodule

```bash
git submodule foreach 'git checkout main && git pull origin main'
git submodule foreach --recursive 'git status'
```

## Check submodule status

```bash
git submodule status
git submodule status --recursive
```

## Remove a submodule

```bash
git submodule deinit -f <path>
git rm -f <path>
rm -rf .git/modules/<path>
git add .gitmodules
```

## Useful .gitmodules options

```ini
[submodule "lib"]
    path = libs/lib
    url = https://github.com/user/lib.git
    branch = main
    update = merge        # merge instead of checkout
    shallow = true        # shallow clone for large submodules
```

## Orchestrate multiple repos

```bash
git -C challenge-service submodule update --init --recursive
git -C md_agent_service checkout main
```
