# Lab 10 — Your First Unity Scene

**You'll:** create a project, place objects, attach a script, and run it. ⏱️ ~40 min.

> This lab is **editor-driven** — you click in Unity, not just type. Steps reference
> Unity 6 LTS menus; minor wording may differ by version.

---

## Part A — Create the project
1. Open **Unity Hub → Projects → New project**.
2. Template: **Universal 2D** (or **2D (Built-In Render Pipeline)**). Name it
   `MiniGame`. Create. Wait for it to open.
3. Notice the panels: **Hierarchy**, **Scene/Game**, **Inspector**, **Project**, **Console**.

## Part B — Add GameObjects
1. In the **Hierarchy**, right-click → **2D Object → Sprites → Square**. A white square
   appears in the Scene. Rename it `Player` (slow double-click or `F2`).
2. Select `Player`. In the **Inspector**, see its **Transform** and **Sprite Renderer**
   components. Change the Sprite Renderer **Color** to something bright.
3. With `Player` selected, use the **Move tool** (`W`) to drag it; watch Transform
   values update. Set Position to `(0, 0, 0)` to center it.

## Part C — Save the scene
`Cmd+S` → save as `Assets/Scenes/Main.unity` (Unity may prompt the first time). The
scene is now an asset in the **Project** panel.

## Part D — Attach your first script
1. In **Project**, create `Assets/Scripts/` (right-click → Create → Folder).
2. Right-click `Scripts` → **Create → MonoBehaviour Script** (or **C# Script**), name
   it `HelloUnity`. (Name must match the class name — Unity enforces this.)
3. Open it (double-click; opens VS Code/Rider). Replace its contents with
   [`unity-scripts/HelloUnity.cs`](../unity-scripts/HelloUnity.cs). Save.
4. Back in Unity, select `Player` → **Add Component** (Inspector) → type `HelloUnity` →
   add it. You'll see the `Greeting` field exposed (from `[SerializeField]`).
5. Edit the **Greeting** value in the Inspector to your own text.

## Part E — Play
1. Press the **Play** ▶ button.
2. Open the **Console** (Window → General → Console, or the tab) — you'll see your
   greeting log line.
3. With the **Game** view focused, press **Space** — a "Space pressed at time…" line
   appears each press.
4. Press **Play** again to **stop**.

✅ You created a scene, composed a GameObject from components, attached a C# script,
exposed a field to the Inspector, and ran it — the entire Unity inner loop.

## Part F — Notice the lifecycle
- The greeting logged **once** (`Start`).
- The Space message logs **on demand inside `Update`** (called every frame).
You'll go deep on this lifecycle next module.

> ⚠️ Gotcha you just relied on: changes during **Play mode are temporary**. Tune values
> in Play to experiment, then re-apply them while **stopped** to keep them.

## What you learned
- Create/open Unity projects via the Hub; navigate the editor panels.
- GameObjects are composed of Components (Transform, Sprite Renderer, your script).
- `[SerializeField]` exposes fields to the Inspector; the Console shows `Debug.Log`.
- `Start` runs once; `Update` runs every frame.

➡️ **[challenge.md](./challenge.md)** then [Module 11](../11-unity-scripting/).
