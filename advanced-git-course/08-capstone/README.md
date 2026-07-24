# Module 08 — Capstone: Multi-Service Project

**Goal:** synthesize every concept from this course into a complete, realistic
multi-service project with submodules, tags, hooks, Docker integration, and
release workflow. ⏱️ ~90 min · 🎯 Prereq: Modules 00–07.

---

## The scenario

You're the tech lead on a platform team. Your company has three services:

- **api-gateway** — the public-facing API
- **auth-service** — handles authentication
- **worker-service** — processes background jobs

Each service is its own Git repository. The parent platform repo uses submodules
to reference all three. You need to:

1. Set up the entire project structure with proper Git config
2. Add all services as submodules with the merge strategy
3. Set up shared hooks for code quality
4. Create a release workflow with tags
5. Handle a hotfix scenario across multiple services
6. Build and verify with Docker Compose integration

## What you'll demonstrate

| Concept | Where it appears |
|---------|-----------------|
| `core.protectNTFS` | Module 01 config |
| `pull.rebase true` | Module 01 config |
| `checkout -f` | Module 02 force operations |
| `reset --hard` and reflog | Module 02 recovery |
| `git pull origin main` | Module 03 remote ops |
| `git submodule add` | Module 04 submodules |
| `git submodule update --init --recursive` | Module 04 submodules |
| `.gitmodules` with `update = merge` | Module 05 workflows |
| `git submodule foreach --recursive` | Module 05 batch operations |
| Shared hooks via `core.hooksPath` | Module 05 hooks |
| `git tag -a 2.0.32` | Module 06 tagging |
| `git -C` multi-repo orchestration | Module 07 integration |
| `docker compose up --build` | Module 07 integration |
| Worktrees | Module 07 parallel work |
| Stash | Module 07 temporary storage |

## Key terms

Everything from prior modules, applied together:
- Submodule lifecycle (add, update, foreach)
- Config hierarchy (system → global → local)
- Force operations and recovery
- Tag-based releases
- Multi-repo orchestration
- Shared hooks

---

**Next →** [Lab 08](./lab.md) — build the complete capstone project.
