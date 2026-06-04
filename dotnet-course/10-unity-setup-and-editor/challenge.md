# Challenge 10 — Explore the Editor

No reference code — these are editor/observation tasks. Notes in
[`solutions/`](./solutions/).

## Tasks
1. **Two objects, one script.** Add a second square `Enemy`, attach `HelloUnity` to it
   too, and give each a different `Greeting` in the Inspector. Confirm both log their
   own greeting on Play. What does this tell you about components and instances?

2. **Find the asset.** In the **Project** panel, locate the `.cs` file and the
   `Main.unity` scene on disk. Then in Finder, open the project folder — note the
   `Assets/`, `Library/`, and `ProjectSettings/` folders. Which one should you **not**
   commit to git, and why? (Hint: it's regenerated.)

3. **Console discipline.** Make `HelloUnity` log every frame (move the log out of the
   `if`), press Play, and watch the Console flood. Revert it. Why is logging every
   frame a bad habit?

4. **Inspector tweaking.** Without editing code, change the `Player`'s scale to make it
   twice as wide but the same height. Which Transform field did you use?

## Success criteria
- [ ] Two GameObjects share one script class but have independent field values.
- [ ] You can point to the script + scene assets and identify `Library/` as
      git-ignored (regenerated cache).
- [ ] You understand why per-frame logging is harmful (perf + noise).
- [ ] You scaled non-uniformly via the Transform Scale X.
