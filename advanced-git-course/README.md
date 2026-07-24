# Advanced Git — Master the Details

> Git is simple until it isn't. This course takes you from "I know the basics" to
> "I can handle submodules, force operations, complex configs, and real-world
> release workflows."

## Who this is for

Developers who:
- Use Git daily but feel shaky on submodules, force checkouts, or config internals
- Work on multi-service projects that use submodules or monorepo patterns
- Need to manage releases, tags, and cross-repository dependencies
- Have been copy-pasting `git submodule` commands without understanding them

**Starting point:** You should be comfortable with `git init`, `git add`, `git commit`,
`git push`, `git pull`, `git branch`, and `git checkout`. If those feel automatic,
this course is for you.

## Why this course

Most Git tutorials stop at basic commands. Real projects require:
- Submodules (and the `foreach` loops that keep them in sync)
- Advanced config (`core.protectNTFS`, pull strategies, hooks)
- Force operations (`checkout -f`, rebasing with care)
- Tagging workflows for actual releases
- Multi-repository orchestration (`git -C`, submodule update flags)

This course teaches what you actually need when your project grows beyond a
single repo with a single branch.

## Learning arc

```
00-setup ──► 01-git-config-advanced ──► 02-branching-force ──► 03-remote-operations
                                                              │
            ┌─────────────────────────────────────────────────┘
            ▼
04-submodule-fundamentals ──► 05-submodule-workflows ──► 06-tagging-releases
                                                        │
            ┌───────────────────────────────────────────┘
            ▼
07-advanced-integration ──► 08-capstone
```

## Prerequisites

| Requirement | Why |
|-------------|-----|
| Git 2.40+ installed | Modern submodule and config features |
| Command-line comfort | Every lab runs in a terminal |
| Basic Git workflow knowledge | Modules assume you can commit/push/pull |
| A GitHub account | For creating test remotes in labs |

## Learning path

| # | Module | Estimated time |
|---|--------|----------------|
| 00 | Setup & Orientation | 20 min |
| 01 | Advanced Git Config | 45 min |
| 02 | Branching & Force Operations | 60 min |
| 03 | Remote Operations & Pull Strategies | 45 min |
| 04 | Submodule Fundamentals | 75 min |
| 05 | Submodule Workflows & Hooks | 60 min |
| 06 | Tagging & Release Management | 45 min |
| 07 | Advanced Topics & Integration | 60 min |
| 08 | Capstone: Multi-Service Project | 90 min |
| **Total** | | **~8.5 hours** |

## Module structure

Every module follows the same four-file pattern:

```
NN-topic/
  README.md       ← Concepts in plain language. Read first.
  lab.md          ← Step-by-step guided lab with expected output. Do second.
  challenge.md    ← An unguided task to prove you understood. Do third.
  solutions/      ← Reference answers — peek only after you've tried.
```

## Reference material

- [`GLOSSARY.md`](./GLOSSARY.md) — plain-English definitions of every term
- [`VERIFY.md`](./VERIFY.md) — environment smoke test
- [`cheatsheets/`](./cheatsheets/) — quick-reference cards

## Philosophy

- **Learn by doing.** Every concept is exercised in a lab with real repos you create.
- **Deliberate failure.** You'll force-checkout over dirty work, break submodules,
  and fix what you broke.
- **Production patterns.** Submodule workflows, tag-based releases, multi-repo
  orchestration — the stuff senior devs deal with daily.
- **Local-first.** Everything runs on your laptop with free tools. No cloud required
  (though you'll push to GitHub in some labs).
