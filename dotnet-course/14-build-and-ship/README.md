# Module 14 — Build & Ship (Capstone B)

**Goal:** turn your project into a real, runnable application — build/export for
desktop, learn build settings and basic optimization, organize the project, and ship a
finished small game. ⏱️ ~2.5 h · 🎯 Prereq: 10–13.

---

## 1. Building a player (export)

A Unity **build** ("player") is a standalone app — no editor needed to run it.

1. **File → Build Settings** (or **Build Profiles** in Unity 6).
2. Ensure your scenes are in **Scenes In Build**, in order (index 0 loads first).
3. Pick the platform: **Windows, Mac, Linux** → target **macOS**.
4. **Build** → choose an output folder → Unity produces a `.app` (macOS).
5. Run the `.app` like any Mac application.

> **Build vs Build And Run** — the latter builds then launches immediately.
> First macOS build can take a few minutes (it compiles your C# via the player
> pipeline; IL2CPP builds take longer than Mono).

## 2. Build settings that matter

- **Scenes In Build** — only listed scenes ship; index 0 is the entry scene.
- **Player Settings** — product name, company, icon, resolution/windowed vs fullscreen.
- **Development Build** — includes debugging/profiler support; **uncheck** for releases.
- **Scripting Backend** — **Mono** (faster builds) vs **IL2CPP** (AOT, better perf,
  required for some platforms). Desktop can use either.

## 3. Basic optimization & hygiene

You don't need to micro-optimize a small game, but build good habits:
- **Avoid per-frame allocations** in `Update` (don't `new` collections each frame; the
  GC pauses cause stutter). Cache references in `Awake`.
- **Cache `GetComponent`** results instead of calling every frame.
- Use the **Profiler** (Window → Analysis → Profiler) to find frame spikes.
- Keep textures/audio reasonably sized; use prefabs to avoid duplicated setup.
- **Don't log every frame** — Console logging is surprisingly expensive.

## 4. Project organization

Keep assets tidy so the project scales:
```
Assets/
├── Scenes/         Main.unity, Win.unity, Menu.unity
├── Scripts/        gameplay, managers, UI
├── Prefabs/        Coin, Pickup, Player, ...
├── Materials/
├── Audio/
└── Settings/       ScriptableObject assets (GameSettings, ...)
```
Use a **Unity `.gitignore`** (ignore `Library/`, `Temp/`, `Logs/`, `Obj/`, `Build/`);
commit `Assets/`, `Packages/`, `ProjectSettings/`. (The course's top-level
[`.gitignore`](../.gitignore) already covers these.)

## 5. Capstone B — your deliverable

Ship a **finished, playable game** (extend the 2D coin-collector *or* the 3D
roll-a-ball):
- ✅ A **menu → gameplay → win** flow across scenes.
- ✅ **Win and lose** conditions with a score/HUD.
- ✅ **Audio** (at least SFX), and basic polish (a couple of the challenge extras).
- ✅ Tidy project structure + a committed `.gitignore`.
- ✅ A **macOS build** (`.app`) that runs outside the editor.

Self-assessment **rubric**: [`solutions/RUBRIC.md`](./solutions/RUBRIC.md).

## Do the lab
Build, run the `.app`, and finish your game. 👉 **[lab.md](./lab.md)** ·
then 👉 **[challenge.md](./challenge.md)**

---

## Where to go next (beyond this course)

- **Deeper Unity:** the new **Input System**, animation/Animator, tilemaps, particle
  systems, the **Asset Store**, and 2D/3D art pipelines.
- **Performance:** the Profiler, object **pooling** (reuse instead of Instantiate/
  Destroy), addressables.
- **Multiplayer:** Netcode for GameObjects.
- **Other platforms:** iOS/Android/WebGL/consoles (each adds build-support modules).
- **Back to .NET:** your app-support skills + C# are exactly the foundation studios and
  tools teams want; Unity tooling/editor scripting is C#, too.

## Key terms
build/player · Build Settings/Profiles · Scenes In Build · Player Settings ·
Development Build · Mono vs IL2CPP · Profiler · allocation/GC stutter · `.app` ·
project organization · Unity `.gitignore`
