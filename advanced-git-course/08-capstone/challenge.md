# Challenge 08 — Extend the Capstone

Solutions in [`solutions/`](./solutions/). Try first.

Build on the capstone by adding realistic team workflow scenarios.

## Tasks

1. **Multi-developer simulation.** Clone the platform repo into `alice/` and
   `bob/`. Alice updates auth-service, Bob updates worker-service. Both push.
   Simulate pulling both updates into a third clone and resolving any conflicts.

2. **Submodule update cascade.** Add a `shared-lib` submodule to the platform
   repo that's referenced by both `api-gateway` and `auth-service`. Demonstrate
   that updating `shared-lib` in the parent requires updating the pointer in both
   services.

3. **Release automation script.** Write a `release.sh` script that:
   - Takes a version number as argument
   - Creates annotated tags on all services and the platform
   - Pushes all tags
   - Prints a summary of what was released

4. **Recovery scenario.** In a fresh clone of the platform, accidentally run
   `git reset --hard HEAD~5`. Use reflog to recover. Then use `git -C` to verify
   all submodules are still intact.

## Success criteria

- [ ] Two clones push changes that merge cleanly into a third
- [ ] shared-lib update cascades to both dependent services
- [ ] release.sh creates and pushes tags for all repos
- [ ] Recovery from hard reset uses reflog successfully
- [ ] All verification commands pass

---

Congratulations on completing Advanced Git! You now have the skills to handle
submodules, force operations, multi-repo orchestration, and release workflows
in real production projects.
