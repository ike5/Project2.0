# Challenge 06 — Release Workflow

Solutions in [`solutions/`](./solutions/). Try first.

Apply tagging and release management to a realistic scenario.

## Tasks

1. **Semantic versioning sequence.** Create a project with 6 commits representing
   a realistic development history: v1.0 (initial), v1.1 (feature), v1.1.1 (bugfix),
   v1.2 (feature), v2.0 (breaking change), v2.0.1 (hotfix). Tag each with an
   annotated tag. List all tags with messages.

2. **Tag a submodule project.** Create a parent repo with one submodule. Tag the
   parent at v1.0 and the submodule at v1.0.0. Push both tags to a bare remote.
   Verify the tags exist on both remotes.

3. **Check out old release.** Using the project from Task 1, check out v1.1.1
   (the bugfix release). Create a branch `hotfix-1.1.x` from that tag. Add a
   commit to the hotfix branch. Tag it v1.1.2. Show the branch history.

4. **Delete and recover.** Delete the v2.0 tag. Verify it's gone. Recover it
   using the reflog. Verify it's back with the correct commit.

## Success criteria

- [ ] Six annotated tags with semantic versions
- [ ] Parent and submodule both tagged at v1.0/v1.0.0
- [ ] Hotfix branch created from old tag
- [ ] v2.0 deleted and recovered via reflog
- [ ] All tags have descriptive messages

---

**Next →** Module 07: [Advanced Topics & Integration](../07-advanced-integration/README.md)
