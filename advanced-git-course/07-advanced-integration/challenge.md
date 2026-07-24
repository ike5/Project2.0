# Challenge 07 — Integration Mastery

Solutions in [`solutions/`](./solutions/). Try first.

Combine the advanced tools from this module in realistic scenarios.

## Tasks

1. **Multi-repo status dashboard.** Create 4 service repos and a parent with all
   them as submodules. Write a single script that uses `git -C` to show:
   - Current branch of each submodule
   - Last commit message of each submodule
   - Whether each submodule is clean or dirty

2. **Docker Compose build pipeline.** Using the parent from Task 1, write a
   `build.sh` script that:
   - Updates all submodules with `git submodule update --init --recursive`
   - Simulates building a Docker image for each service (echo "Building...")
   - Runs a simulated `docker compose up --build -d`
   - Checks status with `docker compose ps`

3. **Worktree hotfix workflow.** Using the parent from Task 1:
   - Create a hotfix worktree from the latest tag
   - Make a fix in the hotfix worktree
   - Tag the fix
   - Clean up the worktree

4. **Stash and recover.** Make changes in 2 different submodules, stash them
   separately with descriptive names, then pop them back in order.

## Success criteria

- [ ] Dashboard script shows branch, last commit, and clean/dirty status for 4 submodules
- [ ] Build pipeline script runs submodule update, build, and status check
- [ ] Hotfix worktree created, fixed, tagged, and removed
- [ ] Changes stashed and recovered from multiple submodules

---

**Next →** Module 08: [Capstone: Multi-Service Project](../08-capstone/README.md)
