# 01 — The `Assets/` Folder: A Senior's Map of Unity's File Layout

> **Read this before writing a single line of code.** A senior Unity
> project lives or dies by what's in `Assets/` and where. New Unity
> developers put files "somewhere" and wonder why the build is 800 MB,
> why their shader isn't compiling, why their test doesn't run, or why
> their prefab changes got overwritten by a teammate. All of that is a
> file-layout problem.

This module walks every important folder, what's allowed there, what's
not, and the senior pattern for each.

---

## 0. The mental model

When you import a project, the `Assets/` folder is the **only** folder
the editor reads as a Unity project. The Unity editor scans it
recursively, builds a database of every file's type, metadata, and
GUIDs, and presents them in the Project window.

Everything outside `Assets/` is invisible to the editor unless you
explicitly tell it to look. This is why `Library/`, `Temp/`, `Logs/`
are not part of "your project"; Unity regenerates them from `Assets/`
and `ProjectSettings/`.

```
MyProject/
├── Assets/              ← YOUR STUFF. The editor scans this recursively.
├── ProjectSettings/     ← Editor config. Don't edit by hand.
├── Packages/            ← Package manifest. You edit manifest.json.
├── Library/             ← GENERATED. Do not commit. Do not edit.
├── Temp/                ← GENERATED. Do not commit.
├── Logs/                ← GENERATED. Editor logs.
├── UserSettings/        ← Per-user editor settings. Do not commit.
└── obj/                 ← Build intermediates. Do not commit.
```

**The senior rule**: only `Assets/`, `ProjectSettings/`, and
`Packages/manifest.json` are source-controlled. Everything else is
regenerable. If you commit `Library/`, you've made a mistake.

---

## 1. The standard folder layout

The Unity manual does not enforce a folder layout, but the community
has converged on one. The senior version:

```
Assets/
├── Scenes/              ← .unity files. One per "level" / "screen".
├── Scripts/             ← Runtime C# code (MonoBehaviour, etc.)
├── Editor/              ← Editor-only C# code (in an Editor folder).
├── Materials/           ← .mat files (material assets).
├── Shaders/             ← .shader, .shadergraph, .hlsl.
├── Textures/            ← Imported images (.png, .jpg, .psd, .tga).
├── Meshes/              ← Imported 3D models (.fbx, .obj, .blend).
├── Animations/          ← .anim clips, .controller (Animator Controllers).
├── Audio/               ← Imported audio (.wav, .ogg, .mp3).
├── Prefabs/             ← Reusable GameObject templates.
├── UI/                  ← UGUI/UI Toolkit assets (fonts, sprites, layouts).
├── ScriptableObjects/   ← Data assets (config, items, dialogue).
├── Plugins/             ← Third-party DLLs and native plugins.
├── Resources/           ← (Avoid in production. Used for legacy loading.)
├── StreamingAssets/     ← Files copied verbatim to the build (e.g. video).
├── AddressableAssetsData/ ← Addressables catalog (after install).
├── Tests/               ← Test Framework tests (EditMode + PlayMode).
├── Settings/            ← URP/HDRP renderer assets, input actions, etc.
└── ThirdParty/          ← Code or assets you vendored but don't own.
```

You don't need every folder on day one. Start with `Scenes/`,
`Scripts/`, `Materials/`, `Prefabs/`, `Settings/`, and add as the
project demands.

The senior rule: **no files at the root of `Assets/`.** A
`Player.prefab` at the root is fine for a tutorial; in production,
it goes in `Prefabs/Player/`.

---

## 2. The thing you must understand: the asset database

Every file under `Assets/` is an **asset** with:

- A **GUID** (a stable, 32-character hex string Unity uses internally
  to reference it from other assets).
- An **import settings** object (the inspector for a `.png` is the
  TextureImporter).
- A **`.meta` file** next to it, holding the GUID and import settings.
  **Always commit `.meta` files.** Two engineers with different GUIDs
  for the same logical file is the #1 cause of "the scene broke after
  pull".

This is also why Unity's diff/merge is famously bad in version
control: scenes and prefabs are YAML, references are GUIDs, and a
GUID change is invisible to a text diff. (Module 12 covers the
senior Git workflow with Unity.)

---

## 3. `Assets/Scenes/` — your levels

A scene is a serialized hierarchy of GameObjects + components + their
serialized field values. Stored as `.unity`, which is **YAML**.

**The senior rules**:

- **One scene per gameplay "place"**: `MainMenu.unity`, `Level1.unity`,
  `Level2.unity`, `GameOver.unity`.
- **Use additive loading for levels** with `SceneManager.LoadSceneAsync`
  with `LoadSceneMode.Additive`. The first scene is "boot"; everything
  else loads on top.
- **Don't put your player in the level scene**. Put the player in a
  `_Persistent` scene that's loaded additively and never unloaded.
- **No game logic in scene components**. The scene is **data**; logic
  lives in scripts. A scene with a 5,000-line `MonoBehaviour` is the
  "we can't refactor" anti-pattern.

Build settings (`File → Build Settings → Scenes In Build`) determines
which scenes ship and in what order. The first one is the boot scene.

**The senior scene budget**:

| Scene | Approx object count | Approx serialized size |
|-------|---------------------|------------------------|
| Boot  | < 20                | < 50 KB                |
| UI    | < 200               | < 1 MB                 |
| Level | < 5,000             | < 10 MB                |
| Open world chunk | < 50,000   | < 50 MB                |

A scene larger than 50 MB is a code smell. The fix: split it, use
streaming, or use DOTS subscenes.

---

## 4. `Assets/Scripts/` — runtime C#

**The senior rules**:

- **One type per file**, named after the type. `Player.cs` contains
  `public class Player`. Two types per file works; ten does not.
- **Folder by feature, not by type**:
  ```
  Scripts/
    Player/
      Player.cs
      PlayerMovement.cs
      PlayerInput.cs
      PlayerHealth.cs
    Enemies/
      Enemy.cs
      EnemySpawner.cs
    Combat/
      DamageDealer.cs
      Health.cs
      IDamageable.cs
  ```
  Folder by type (`Scripts/Controllers/`, `Scripts/Models/`) is the
  textbook answer. It does not scale; folder by feature does.
- **Asmdef for any folder with > 5 scripts**. Assembly definitions
  speed up compile time and let you control what sees what.
  See §11 below.
- **No third-party code in `Scripts/`**. Use `Plugins/` or
  `ThirdParty/`.

**The script that doesn't get written**:
The most senior thing you can do is **not write a script**. If a
behaviour can be expressed as a ScriptableObject, a prefab, or a
single tweak of an existing component, prefer that. The default
Unity 2D/3D components are far more capable than they look.

---

## 5. `Assets/Editor/` — editor-only C#

A script in any folder named `Editor` (at any depth) is **stripped
from the build**. This is the cleanest way to write inspector
customizations, build scripts, asset processors, and editor tools.

```
Assets/Scripts/Player/Editor/
  PlayerEditor.cs           ← this is editor-only
  PlayerStatsWindow.cs
```

**The senior rules**:

- The `Editor` folder name is **case-sensitive on macOS/Linux**.
  `editor/` won't work; it must be `Editor/`.
- Editor code **cannot** be referenced from runtime code. The
  reverse (editor code referencing runtime) is fine.
- Put **all** editor tools in `Editor/` or under an `Editor/`
  folder. Build-time errors from "I accidentally used
  `UnityEditor.AssetDatabase` in runtime" are the classic
  ship-blocker.
- A common pattern: `Assets/Editor/Build/` for build scripts,
  `Assets/Editor/Tools/` for in-editor utilities, and one
  `Editor/` per feature folder for inspector customizations.

**The assembly-definition pair**:

```
Assets/Scripts/Player/
  Runtime.asmdef                 ← runtime assembly
  Editor/
    Editor.asmdef                ← editor assembly; references Runtime
    PlayerEditor.cs
```

The `Editor.asmdef` has `"includePlatforms": ["Editor"]` and
references the runtime asmdef by name or GUID.

---

## 6. `Assets/Materials/` — material assets

A material is the "instance" of a shader. The `.mat` file is YAML,
referencing a shader (by GUID) and serializing its properties.

**The senior rules**:

- **One material per visual concept**. `M_Player`, `M_Enemy`,
  `M_Ground`, `M_Wall`. The "M_" prefix is a community convention
  that says "this is a material, not a shader".
- **Don't create materials at runtime** unless you must. They leak
  into the build size and are hard to manage. Use `MaterialPropertyBlock`
  to vary one property on a shared material.
- **Material variants** (URP) let you inherit from a base material
  and override one or two properties. Senior pattern for "same look,
  different tint".
- **Materials in the build** are listed in the Build Report. A
  1,000-material project has 1,000 shader variant combinations;
  many will be unused. Use the `Shader Variant Collection` to
  limit.

**The MaterialPropertyBlock rule** (the senior default for tinting
or varying one or two properties on a shared material):

```csharp
// BAD: creates a new material per renderer. Memory leak.
foreach (var r in renderers) r.material.color = Color.red;

// GOOD: shares the material, varies the color via GPU-side data.
var mpb = new MaterialPropertyBlock();
mpb.SetColor("_BaseColor", Color.red);
foreach (var r in renderers) r.SetPropertyBlock(mpb);
```

The `material` getter **creates a new instance**. The `sharedMaterial`
getter is shared. Use `sharedMaterial` for read-only; use
`MaterialPropertyBlock` for variation.

---

## 7. `Assets/Shaders/` — shader code

Three flavors of shader files you'll see:

- `.shader` — hand-written, HLSL-flavored, the legacy/built-in
  approach. Still used for highly optimized custom work.
- `.shadergraph` — Unity's node-based editor, generates a `.shader`
  under the hood. The default for artists and most URP/HDRP work.
- `.hlsl` — pure HLSL include files; `.shadergraph` blocks compile
  down to these.
- `.compute` — compute shaders (for DOTS, GPU-side work).
- `.cginc`, `.hlsl` — include files (for shared functions).

**The senior rules**:

- **Shader Graph first** for visual work. It's faster to author,
  easier to maintain, and produces comparable results.
- **Hand-written `.shader` only for**: GPU-instanced variants,
  compute shaders, custom render passes, or shipping a tight
  optimization the artist can't get from a graph.
- **A shader that doesn't compile is a blocker**. Always check the
  console; a red shader error means **all materials using it are
  rendered as the pink "missing shader" placeholder**. This is
  the single most common visual bug in student Unity projects.
- **Multi_compile directives explode build size**. Each
  `multi_compile` doubles the variant count. Limit them.
- **Use `Shader.Find` only at startup, never in `Update`**. The
  shader lookup is expensive. Cache by direct reference in the
  inspector.

---

## 8. `Assets/Prefabs/` — the heart of the editor

A prefab is a **serialized GameObject template**. It's the Unity
answer to "I want to spawn this exact thing at runtime" and "I want
to make a change in one place and have it apply to 5,000 instances".

**The senior rules**:

- **Anything that appears more than once in a scene is a prefab.**
  An enemy, a tree, a UI panel, a bullet — all prefabs.
- **Prefab Variants** (Unity 2018.3+) are how you do "this enemy
  but with 1.5× health". They inherit from a base prefab.
- **Nested prefabs** are the senior way to compose: a `Player` prefab
  contains a `HealthBar` prefab. Editing the HealthBar once updates
  every player.
- **Prefab overrides** (red text in the inspector) are the most
  common bug. "I changed the health on this one enemy and now my
  5,000 enemies are different". Fix: **Apply Overrides** back to
  the prefab, or **Revert** to clear the override.
- **Don't edit prefab instances during Play Mode without "Open
  Prefab"**. Edits to instances in Play Mode are lost when you
  exit Play Mode. (This is the most common "I lost my work" bug
  in Unity.)
- **Addressable prefabs** for runtime spawning. Drag the prefab
  into the inspector of a "spawner" MonoBehaviour with its
  address as the value. (Module 8.)

**The senior folder convention**:
```
Prefabs/
  Player/
    Player.prefab
    PlayerBullet.prefab
  Enemies/
    EnemyGrunt.prefab
    EnemyBoss.prefab
  Environment/
    Tree_Oak.prefab
    Tree_Pine.prefab
  UI/
    HUDPanel.prefab
    MenuButton.prefab
```

Match the scene folder structure one level up. Easy to find, easy
to grep.

---

## 9. `Assets/Settings/` — the configuration folder

This is where URP/HDRP renderer assets, input action assets, layer
definitions, and tag definitions live.

**What's typically in `Settings/`**:

- `URP-Performance.asset` — the URP renderer asset for the high
  tier.
- `URP-Balanced.asset` — the URP renderer asset for the mid tier.
- `URP-Performant.asset` — mobile low.
- `URP-PostProcessing.asset` — global post-process volume profile.
- `InputSystem.inputactions` — the Input System asset (replaces
  the legacy Input Manager).
- `TagManager.asset` — tags and layers (referenced from
  `ProjectSettings/TagManager.asset`; some projects keep a copy
  here for clarity).

**The senior rules**:

- **Don't put scripts in `Settings/`**. It's config-only.
- **URP assets are referenced from Project Settings → Quality**, one
  per quality level. They live in `Settings/` for version control.
- **Don't edit the URP assets in code at runtime**. Read them; cache
  references at startup.

---

## 10. `Assets/Tests/` — your test suites

Unity Test Framework has two contexts:

- **EditMode tests**: fast, run in the editor without Play Mode.
  For pure logic: data parsing, save systems, math, etc.
- **PlayMode tests**: enter Play Mode in a test scene. For systems
  that need an actual Unity tick: physics, audio, rendering.

**The senior folder structure**:

```
Assets/Tests/
  EditMode/
    EditMode.asmdef
    Combat/
      DamageCalculatorTests.cs
      HealthTests.cs
    SaveSystem/
      SaveLoadTests.cs
  PlayMode/
    PlayMode.asmdef
    Player/
      PlayerMovementTests.cs
```

Each subfolder needs an `.asmdef` (assembly definition) with
`"testAssemblies": true` and the right platform config. The test
runner uses these to find tests.

**The senior rules**:

- **Test the math, the state machines, the data layer**. Don't test
  MonoBehaviour `Update` directly.
- **A failing test is a feature**, not a problem. Tests that never
  fail aren't tests.
- **Use `[UnityTest]` with `IEnumerator` for PlayMode tests** that
  need to wait for a frame or two.

```csharp
using NUnit.Framework;
using UnityEngine.TestTools;
using System.Collections;

public class PlayerHealthTests
{
    [Test]
    public void Health_NeverGoesNegative()
    {
        var h = new Health(100);
        h.TakeDamage(150);
        Assert.AreEqual(0, h.Current);
    }

    [UnityTest]
    public IEnumerator Player_DiesAfterHealthZero() => UniTask.ToCoroutine(async () =>
    {
        var p = new GameObject().AddComponent<Player>();
        p.Health.TakeDamage(999);
        await UniTask.Yield();
        Assert.IsTrue(p.IsDead);
    });
}
```

---

## 11. The hidden gotcha: assembly definitions (`*.asmdef`)

By default, **all scripts in `Assets/` are in one giant assembly called
`Assembly-CSharp`**. This means:

- Recompiling one script recompiles all of them.
- Every script can see every other script, even "internal" ones.
- You can't have a "Player" namespace and another "Player" namespace
  in different folders.

An **assembly definition** (`.asmdef`) breaks this:

```json
// Assets/Scripts/Player/Runtime.asmdef
{
    "name": "MyGame.Player.Runtime",
    "rootNamespace": "MyGame.Player",
    "references": [
        "Unity.Mathematics",
        "Unity.Collections"
    ],
    "includePlatforms": [],
    "excludePlatforms": [],
    "allowUnsafeCode": false,
    "overrideReferences": false,
    "precompiledReferences": [],
    "autoReferenced": true,
    "defineConstraints": [],
    "versionDefines": [],
    "noEngineReferences": false
}
```

When you put an `.asmdef` in a folder, all scripts in that folder
(and subfolders without their own `.asmdef`) belong to **that
assembly**. The folder becomes its own compile unit.

**The senior default**:

- **One root-level `.asmdef` covering `Assets/Scripts/`** so the
  whole game code is one named assembly (not `Assembly-CSharp`).
- **One `.asmdef` per feature folder** if the project has 50+ scripts
  and compile time is killing you.
- **A separate `Editor.asmdef` for each Editor folder** that
  references the runtime asmdef.

This is the #1 way to **reduce edit-and-test cycle time** in a
non-trivial Unity project.

---

## 12. The "where does this go?" decision tree

| I want to add…                  | Folder                 | Filename convention |
|---------------------------------|------------------------|---------------------|
| A MonoBehaviour                 | `Scripts/<Feature>/`   | `PascalCase.cs`, type = filename |
| An editor tool                  | `Editor/<Feature>/`    | same                |
| A ScriptableObject type         | `Scripts/<Feature>/`   | the type            |
| A material                      | `Materials/`           | `M_UseCase.mat`     |
| A shader                        | `Shaders/`             | `S_UseCase.shader`  |
| A shader graph                  | `Shaders/Graphs/`      | `S_UseCase.shadergraph` |
| A texture                       | `Textures/<Feature>/`  | `T_UseCase.png`     |
| A 3D model                      | `Meshes/<Feature>/`    | the asset's name    |
| An animation clip               | `Animations/`          | `A_Action.anim`     |
| An Animator Controller          | `Animations/Controllers/` | `AC_UseCase.controller` |
| An audio clip                   | `Audio/<Feature>/`     | `SFX_UseCase.wav` or `MUS_UseCase.ogg` |
| A prefab                        | `Prefabs/<Feature>/`   | the GameObject name |
| A UI sprite atlas               | `UI/`                  | `Atlas_Name.png`    |
| A ScriptableObject data asset   | `ScriptableObjects/`   | type-based name     |
| A third-party plugin            | `Plugins/` or `ThirdParty/` | leave as-is   |
| A scene                         | `Scenes/`              | `Level_X.unity`     |
| A test                          | `Tests/EditMode/` or `Tests/PlayMode/` | `<Type>Tests.cs` |
| A build script                  | `Editor/Build/`        | `BuildScript.cs`    |

The naming prefixes (`M_`, `S_`, `T_`, `A_`, `AC_`, `SFX_`, `MUS_`,
`PFB_`) are conventions. They make the Project window filterable.
Adopt them on day one of a project; retrofitting is painful.

---

## 13. Special folders you should know

### `Assets/Resources/`

Anything in `Resources/` ships in the build regardless of use.
Loadable at runtime via `Resources.Load`. **The senior default is
to not use this for shipping code.**

The valid uses:

- Tiny assets that must always be available (a config ScriptableObject,
  the loading screen).
- Editor-only utilities.

For shipping content, use **Addressables** (module 8).

### `Assets/StreamingAssets/`

Files copied **verbatim** to the build. Used for things Unity can't
import: video files, custom data files, the Addressables catalog.

```csharp
var path = Path.Combine(Application.streamingAssetsPath, "data.bin");
var data = File.ReadAllBytes(path);   // mobile: use UnityWebRequest
```

On mobile, `Application.streamingAssetsPath` is inside a jar/apk
and can't be read with `File.ReadAllBytes`. Use `UnityWebRequest`
or load via Addressables instead. **Module 11 covers this.**

### `Assets/Plugins/`

Third-party DLLs and native plugins. Has special meaning:

- DLLs here are auto-referenced from all assemblies.
- Native plugins (`.so`, `.dll`, `.dylib`) get platform-specific
  handling.

Don't put your own code here.

### `Assets/Editor/`

Already covered. The case-sensitive folder that strips code from the
build.

---

## 14. What you should never put in `Assets/`

- **Generated files from your build process** (e.g. intermediate
  JSON). Put them in `StreamingAssets/` if the player needs them.
- **Large binary assets you don't actually use** (old PSDs, source
  files, large git LFS dumps). These ship in the build or bloat
  the source repo.
- **Personal scratch files** ("test.cs" with `Debug.Log("hello")`).
  Either commit to test or remove.

---

## 15. The senior workflow: a fresh project

1. `git init`. Add the Unity `.gitignore`.
2. Open Unity Hub. New 3D URP project. Save.
3. Create the folder structure (`Scenes/`, `Scripts/`, etc.).
4. **Create an asmdef at `Assets/Scripts/`** for the runtime.
5. **Save the first scene as `Assets/Scenes/Main.unity`**. Add to
   Build Settings.
6. **Save a URP asset as `Assets/Settings/URP-Performance.asset`**.
   Add a URP asset per quality level.
7. **Create a `Test/` folder with two asmdefs** (EditMode +
   PlayMode).
8. **Install the packages you'll need** (Entities, Addressables,
   Memory Profiler, Profiling Core).
9. **Commit** `Assets/`, `ProjectSettings/`, `Packages/manifest.json`.
   Add `.gitignore` rules. First commit.

That's a senior project skeleton. Build the game on top of it.

---

## 16. Verification

```bash
# Layout sanity
ls ~/UnityProjects/UnitySeniorLab/Assets/
# expect: Scenes/  Scripts/  Materials/  Shaders/  Prefabs/  Settings/  Editor/  Tests/

# No garbage at the root
ls ~/UnityProjects/UnitySeniorLab/Assets/ | head
# expect: only folders, no .cs/.png/.mat files at the root

# Asmdef present
ls ~/UnityProjects/UnitySeniorLab/Assets/Scripts/*.asmdef

# No Resources/ (yet)
test ! -d ~/UnityProjects/UnitySeniorLab/Assets/Resources && echo "OK: no Resources"

# .meta files tracked
ls -la ~/UnityProjects/UnitySeniorLab/Assets/Scenes/ | grep meta
# expect: every asset has a sibling .meta
```

---

## Summary

- `Assets/` is the only folder Unity reads. Everything else is
  generated.
- Use the senior folder convention: `Scenes/`, `Scripts/`,
  `Materials/`, `Shaders/`, `Prefabs/`, `Settings/`, `Editor/`,
  `Tests/`. Add more as needed.
- **One type per file**, folder by feature, **always commit `.meta`
  files**.
- `Editor/` strips code from the build. The case-sensitive `Editor`
  folder, not `editor/`.
- Materials, shaders, textures, models each have their folder.
- **Asmdefs reduce compile time and enforce architecture**. Use them
  on day one.
- **Prefabs are the heart of the editor**. Edit them in prefab mode,
  not in scene view, to avoid the "I lost my Play Mode change" bug.
- **No `Resources/` in production**. Use Addressables (module 8).
- **Always commit `Assets/`, `ProjectSettings/`,
  `Packages/manifest.json`**. Never `Library/`, `Temp/`, `Logs/`.
