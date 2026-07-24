# Module 01 — Advanced Git Config

**Goal:** master Git's configuration system so you can control behavior at the
system, global, and local level — including the settings that trip up real projects. ⏱️ ~45 min · 🎯 Prereq: Module 00.

---

## Config levels: precedence matters

Git reads config from three levels. When the same key is set at multiple levels,
the most specific wins:

```
system (/etc/gitconfig)  ←  lowest precedence
  ▼
global (~/.gitconfig)     ←  middle
  ▼
local (.git/config)       ←  highest precedence
```

Check all effective values with:

```bash
git config --list --show-origin
```

This shows every setting and where it came from — invaluable for debugging.

## core.protectNTFS

On Windows, NTFS forbids certain characters in filenames (e.g., `:`, `*`, `?`,
`"`, `<`, `>`, `|`). Git's `core.protectNTFS` (default `true`) prevents you from
checking out commits that would create files with these characters.

**When you need to disable it:**

You're working cross-platform. A teammate on Linux committed a file with a
Windows-invalid character. On Windows, `git checkout` fails:

```
error: path contains invalid characters: file:name.txt
```

The fix:

```bash
git config core.protectNTFS false
git checkout -f main
git config core.protectNTFS true
```

Notice the pattern: disable → do the dangerous operation → re-enable. You don't
want to leave `protectNTFS` off permanently.

**On macOS/Linux**, this setting is irrelevant (those filesystems allow more
characters). But you'll encounter it in cross-platform teams.

## pull.rebase

When you `git pull`, Git can either:
- **Merge** (default): creates a merge commit every time you pull. Clutters history.
- **Rebase**: replays your local commits on top of the remote. Clean history.

Set it globally:

```bash
git config --global pull.rebase true
```

Now `git pull` behaves like `git pull --rebase`. If you need a one-time merge
pull, use `git pull --no-rebase`.

## init.defaultBranch

New repos used to default to `master`. Modern Git defaults to `main`. Set it:

```bash
git config --global init.defaultBranch main
```

## core.hooksPath

By default, Git looks for hooks in `.git/hooks/`. This doesn't survive clones
(since `.git/hooks/` is not tracked). Set a shared hooks directory:

```bash
git config core.hooksPath .githooks
```

Now Git runs hooks from `.githooks/` instead — a tracked directory your whole
team shares.

## submodule.recurse

Tired of running `git submodule update` after every `git pull`? Enable auto-recurse:

```bash
git config --global submodule.recurse true
```

Now `git pull` also updates all submodules automatically.

## push.default

Controls what happens when you run `git push` with no arguments:

| Value | Behavior |
|-------|----------|
| `nothing` | Refuse — you must specify what to push |
| `current` | Push the current branch to a branch with the same name on the remote |
| `upstream` | Push to the upstream branch |
| `simple` (default) | Like `upstream`, but refuses if the remote branch name differs |
| `matching` | Push all local branches that have matching remote branches |

```bash
git config --global push.default simple
```

## Per-repository config

Some settings should only apply to one repo. Use `--local` (or omit the level):

```bash
cd my-project
git config core.ignorecase true
git config --local user.name "Work Name"
git config --local user.email "work@company.com"
```

These live in `.git/config` and don't affect other repos.

## The config editing workflow

Open the config file directly:

```bash
git config --global --edit    # opens ~/.gitconfig in $EDITOR
git config --local --edit     # opens .git/config in $EDITOR
```

This is sometimes faster than running individual `git config` commands.

## Key terms

- **core.protectNTFS** — safety setting preventing invalid NTFS filenames
- **pull.rebase** — makes `git pull` rebase instead of merge
- **core.hooksPath** — redirects hook lookup to a custom directory
- **submodule.recurse** — auto-updates submodules on pull/fetch
- **push.default** — controls what `git push` pushes without arguments
- **init.defaultBranch** — the branch name for new repositories

---

**Next →** [Lab 01](./lab.md) — configure, break, and fix a real repo.
