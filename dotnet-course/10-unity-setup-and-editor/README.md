# Module 10 — Unity Setup & Editor

**Goal:** install Unity, learn the editor, and understand how Unity uses your C#
skills. You're now applying the language to game development. ⏱️ ~1.5 h ·
🎯 Prereq: Phase 0 (C# fundamentals). The support phase isn't required for Unity, but
the C# from Modules 01–04 absolutely is.

> Versions: **Unity 6 LTS** (the "Unity 6000" line) via **Unity Hub**.

---

## 1. Install Unity (Mac)

1. Download **Unity Hub** from <https://unity.com/download> (or `brew install --cask unity-hub`).
2. In Unity Hub → **Installs → Install Editor** → choose the latest **Unity 6 LTS**.
   - In modules/options, you can include **macOS Build Support** (default) and add
     others later. Apple Silicon Macs use the Silicon editor.
3. Sign in with a free Unity account / personal license when prompted.

Unity Hub manages multiple editor versions and your projects — keep using it to open
projects so the right editor version is used.

## 2. Create your first project

Unity Hub → **Projects → New project** → template **2D (Built-In Render Pipeline)** or
**Universal 2D** → name it `MiniGame` → Create. (We start 2D in Module 12; 3D in 13.)

When it opens you'll see the editor.

## 3. The editor, oriented

```
┌──────────────┬───────────────────────────┬───────────────┐
│  Hierarchy   │        Scene / Game        │  Inspector    │
│ (objects in  │  (edit view / play view)   │ (selected     │
│  the scene)  │                            │  object's     │
│              │                            │  components)  │
├──────────────┴───────────────────────────┴───────────────┤
│  Project (assets on disk)   |   Console (logs/errors)     │
└───────────────────────────────────────────────────────────┘
```
- **Hierarchy** — every **GameObject** in the current **Scene**.
- **Scene view** — the editable 3D/2D world; **Game view** — what the player sees.
- **Inspector** — the **Components** on the selected GameObject (and their fields).
- **Project** — your assets (scripts, sprites, prefabs) as files on disk.
- **Console** — `Debug.Log` output, warnings, and errors. **Live here.**
- **Play/Pause/Step** buttons — enter **Play mode** to run the game in the editor.
  ⚠️ Changes made *during* Play mode are reverted when you stop — a classic gotcha.

## 4. GameObjects & Components (composition, not inheritance)

A **GameObject** is an empty container that *does nothing by itself*. You attach
**Components** to give it behavior/data:
- Every GameObject has a **Transform** (position/rotation/scale).
- Add a **Sprite Renderer** to draw a 2D image, a **Rigidbody2D** for physics, a
  **Collider2D** for collisions, and **your scripts** for custom logic.

This is **composition over inheritance** — the same principle from Module 02, made
visual. You build behavior by combining components.

## 5. How Unity uses C#/.NET

- Your scripts are **C#** — the language you already learned. Unity compiles them and
  loads them into the running game.
- Unity runs C# on its own runtime: **Mono** in the editor / many builds, or **IL2CPP**
  (C# → C++ → native) for performance/aot platforms. Either way, *you write C#*.
- The big differences from a console/web app (covered next module): there's **no
  `Main`**; the engine drives your code through a **frame loop** and lifecycle methods
  on classes derived from **`MonoBehaviour`**.

## 6. Scripts & the Console

A minimal Unity script:
```csharp
using UnityEngine;

public class Hello : MonoBehaviour
{
    void Start() => Debug.Log("Hello from Unity!");   // runs once when play begins
}
```
Attach it to a GameObject, press **Play**, and watch the **Console**.

---

## Do the lab
Create the project, add objects, attach your first script, and run it. 👉 **[lab.md](./lab.md)**

Then: 👉 **[challenge.md](./challenge.md)**

## Reference scripts
[`unity-scripts/`](../unity-scripts/) — the scripts you'll use across the Unity modules.

## Key terms
Unity Hub · editor (Hierarchy/Scene/Game/Inspector/Project/Console) · Play mode ·
GameObject · Component · Transform · Scene · `MonoBehaviour` · `Debug.Log` · Mono/IL2CPP

**Next →** [Module 11: Scripting in Unity](../11-unity-scripting/)
