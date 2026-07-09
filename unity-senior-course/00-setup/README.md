# 00 — Setup & Senior Architecture Map

The single most expensive mistake in Unity is starting with the **wrong
project template** and discovering it six months in. This module takes ~30
minutes. Skip the rest of the course and you can recover; skip this and the
course itself becomes a rewrite.

---

## 1. The architecture map (read this first)

A Unity "senior" project is composed of decisions in roughly this order. Get
the top ones wrong and the bottom ones don't matter.

```
┌──────────────────────────────────────────────────────────────┐
│ 1. Project structure                                        │
│    MonoBehaviour-only   vs   DOTS (ECS)   vs   hybrid        │
│ 2. Render pipeline                                         │
│    Built-in (legacy)    vs   URP          vs   HDRP          │
│ 3. Asset pipeline                                           │
│    Resources            vs   AssetBundles vs   Addressables  │
│ 4. Scripting backend                                        │
│    Mono                 vs   IL2CPP                         │
│ 5. Build target                                             │
│    PC, Mobile, Console, WebGL                               │
│ 6. C# language version                                      │
│    C# 9                vs   C# 10         vs   C# 11/12     │
└──────────────────────────────────────────────────────────────┘
```

The defaults you'll get by clicking "New Project → 3D (URP)" in Unity Hub
are reasonable for 2026:

- **URP** as the render pipeline (correct for ~80% of projects).
- **MonoBehaviour** (no DOTS).
- **C# 9** as the language version. Bump in `Project Settings → Player
  → Other Settings → Configuration → Api Compatibility Level` and
  `csc.rsp` for C# 11+ features.
- **Resources only for Editor** (we'll migrate to Addressables in module 7).

We will **not** keep the defaults for: language version (we want modern C#),
asset pipeline (we want Addressables), and the DOTS modules are opt-in.

> **The wrong choice is rarely fatal, but it compounds.** Picking DOTS for
> a casual mobile game is fine but slow to develop. Picking MonoBehaviour
> for a strategy game with 10,000 units is fine but you'll fight the GC
> forever. Pick deliberately.

---

## 2. The tools you must install (this week)

| Tool                     | Why                                       | Where |
|--------------------------|-------------------------------------------|-------|
| **Unity 6.x** (LTS)      | The target.                              | hub.unity.com |
| **Memory Profiler**     | The "where is my RAM going" tool.        | Package Manager → "Memory Profiler" |
| **Profiler**            | Built in. Use it.                        | Window → Analysis → Profiler |
| **Frame Debugger**      | Render-call-by-render-call inspection.   | Window → Analysis → Frame Debugger |
| **RenderDoc**           | GPU draw-call inspection.                | renderdoc.org |
| **Entities** (DOTS)     | Modules 4–5 need it.                     | Package Manager → "Entities" |
| **Netcode for GameObjects** | Module 8.                            | Package Manager → "Netcode for GameObjects" |
| **Burst**                | Comes with Entities.                    | (transitive) |
| **Collections**          | Native containers. Comes with Entities.  | (transitive) |
| **Mathematics**          | `Unity.Mathematics` types. Same.         | (transitive) |
| **Addressables**        | Module 7.                                | Package Manager → "Addressables" |
| **Rider** or **VS Code + C# Dev Kit** | Editor for C#.               | jetbrains.com/rider, code.visualstudio.com |
| **Test Framework**      | For module 13 patterns tests.            | Package Manager → "Test Framework" |
| **ParrelSync**          | Optional: test multiplayer without 2 editors. | github.com/VeriorPies/ParrelSync |

Don't install them all right now — install the ones the current module
calls for, and add as we go.

---

## 3. Project setup (one-time)

1. Open **Unity Hub → New Project**.
2. Choose **3D (URP)**. Name it `UnitySeniorLab`. Put it in
   `~/UnityProjects/`.
3. Open the project.
4. Open **Edit → Project Settings → Player**:
   - **Company Name**: your real name or company.
   - **Product Name**: `UnitySeniorLab`.
   - **Api Compatibility Level**: `.NET Standard 2.1` (broadest
     compatibility) or `.NET Framework` (more APIs, larger build). Most
     modern projects pick `.NET Standard 2.1` for IL2CPP-friendly builds.
   - **Scripting Backend**: `IL2CPP` (we'll switch to Mono in module 10
     to compare; default is platform-dependent).
5. **Edit → Project Settings → Editor**:
   - **Enter Play Mode Settings** → enable both
     `Reload Domain` *disabled* and `Reload Scene` *disabled*. This
     makes Play Mode entry ~5× faster. We'll discuss the trade-off.
6. **Edit → Project Settings → Quality**:
   - Disable **V Sync Count** on at least the `Ultra` tier if you have a
     120/144 Hz monitor and want uncapped frame time for profiling.
7. **Window → Package Manager** → install the packages above as the
   modules need them.
8. Create the folder structure:

```
Assets/
  Scenes/
  Scripts/
  Materials/
  Shaders/
  Prefabs/
  Settings/         ← URP renderer assets, etc.
  Editor/           ← editor-only scripts
  Tests/            ← EditMode + PlayMode tests
```

9. Save the scene as `Assets/Scenes/Main.unity` and add it to
   **Build Settings**.

---

## 4. The senior shortcut: the csc.rsp file

Modern C# features (file-scoped namespaces, `record`s, `init` setters, raw
string literals, etc.) need a C# language version. Unity 6 ships with
C# 9 by default. To bump to C# 9 with file-scoped namespaces and target-typed
`new`, create:

`Assets/csc.rsp`:

```
-langversion:9.0
-define:UNITY_2022_3_OR_NEWER
```

> **Note:** Don't go above C# 9 unless you know your target Unity
> supports it. Module 1 lists the language feature matrix.

---

## 5. Enter Play Mode Settings — the hidden 5× speedup

Default Unity re-runs **Domain Reload** (re-runs every `static` field
initializer) and **Scene Reload** every time you press Play. For a
50-script project, this is 4–8 seconds wasted. Toggle it off:

**Edit → Project Settings → Editor → Enter Play Mode Settings:**
- ☑ Enter Play Mode Options
- ☐ Reload Domain
- ☐ Reload Scene

**The catch**: any `static` field with state won't reset between Play
sessions. You must add `[RuntimeInitializeOnLoadMethod]` to reset
state, or move state to a `ScriptableObject` "session" asset. We'll
set this up in module 2.

---

## 6. The version matrix you actually care about (mid-2026)

| Unity | Default C# | Burst | Entities | URP  | Notes |
|-------|------------|-------|----------|------|-------|
| 2022.3 LTS | 9 | 1.8 | 1.0 | 14 | Long-term support until ~2025 |
| Unity 6 (6000.0.x) | 9 | 1.8 | 1.3 | 17 | **The target for this course** |
| Unity 6.1 (6000.1.x) | 9 | 1.8 | 1.3 | 17 |  |

We'll target **Unity 6 (6000.0.23f1 or newer)**, with notes where
2022.3 LTS differs.

---

## 7. The 30-minute sanity check

After this module, you should be able to:

- [ ] Open `UnitySeniorLab` in Unity Hub and have it boot in < 30 s.
- [ ] Open `Window → Analysis → Profiler` and see a live graph.
- [ ] Open `Window → Analysis → Frame Debugger`.
- [ ] Press Play. Exit. Press Play again. Note the speedup.
- [ ] Create a C# script, attach it to a GameObject, run a `Debug.Log`.
- [ ] `git init` (if you haven't) and add a `.gitignore` that excludes
      `Library/`, `Temp/`, `Logs/`, `obj/`, `Build/`.

A starter `.gitignore` for Unity 6:

```gitignore
# Unity-generated
/[Ll]ibrary/
/[Tt]emp/
/[Oo]bj/
/[Bb]uild/
/[Bb]uilds/
/[Ll]ogs/
/[Uu]ser[Ss]ettings/
/MemoryCaptures/

# Visual Studio / Rider
*.csproj
*.sln
*.suo
*.user
*.userprefs
*.pidb
*.booproj
*.svd
.vs/
.idea/

# OS
.DS_Store
Thumbs.db
```

---

## Common pitfalls

- **Picking the wrong template.** If you clicked "3D" (built-in), you
  have a deprecated render pipeline. Delete and start over; don't try
  to migrate after the fact.
- **Picking HDRP for a mobile game.** HDRP is PC/console only.
- **Putting code in `Assets/Plugins/`** without understanding it. That
  folder has special meaning; reserved for third-party DLLs.
- **Touching `Library/`, `Temp/`, `Logs/`**. These are regenerated.
  Never commit them. Never edit them.

---

## Verification

```bash
ls ~/UnityProjects/UnitySeniorLab/Packages/manifest.json
cat ~/UnityProjects/UnitySeniorLab/ProjectSettings/ProjectVersion.txt
# expect: 6000.0.23f1 (or whatever 6.x you installed)
```
