# Challenge 10 — Notes

1. **Two objects, one script.** Each GameObject gets its **own instance** of the
   `HelloUnity` component, with its own field values. A script class is a *template*;
   every GameObject you attach it to runs an independent copy — just like creating
   multiple objects from a class in plain C#.

2. **Assets on disk.** The script lives at `Assets/Scripts/HelloUnity.cs`; the scene at
   `Assets/Scenes/Main.unity`. **Do not commit `Library/`** — it's a regenerated cache
   Unity rebuilds from `Assets/` + `ProjectSettings/`. Commit `Assets/`,
   `ProjectSettings/`, and `Packages/`; ignore `Library/`, `Temp/`, `Logs/`,
   `obj/`, and `Build(s)/`. (Unity provides a standard `.gitignore`.)

3. **Per-frame logging.** `Update` runs 60+ times/second, so logging there floods the
   Console, hurts performance, and buries the messages you actually care about. Log on
   events/state changes, not every frame.

4. **Non-uniform scale.** Set **Transform → Scale → X = 2** (leave Y = 1). Scale is
   per-axis, so X widens without changing height.
