# Challenge 03 — Multi-User Remote Scenario

Solutions in [`solutions/`](./solutions/). Try first.

Simulate a realistic team workflow with multiple contributors.

## Tasks

1. **Three-user simulation.** Create a bare repo as a remote. Clone it into
   `alice/`, `bob/`, and `charlie/`. Each person pushes a different file. Pull
   to get all three files into each clone.

2. **Conflict resolution.** Alice and Bob both edit the same file (`shared.txt`)
   in different ways and push. The second person to push gets a non-fast-forward
   error. Pull, resolve the merge conflict (keep both changes), and push.

3. **Force with lease protection.** After the conflict is resolved, Charlie tries
   to force-push an old version of `main` using `--force-with-lease`. Explain why
   this might fail and what the failure means.

4. **Upstream tracking.** In one of the clones, create a new branch `feature-x`,
   push it with `-u`, then verify the upstream is set correctly using
   `git branch -vv`.

## Success criteria

- [ ] All three clones have all three files after pulling
- [ ] Merge conflict is resolved with both changes preserved
- [ ] `--force-with-lease` correctly prevents overwriting unseen work
- [ ] `git branch -vv` shows upstream tracking for `feature-x`

---

**Next →** Module 04: [Submodule Fundamentals](../04-submodule-fundamentals/README.md)
