# Lab 01 — Build a Senior Project Skeleton

In this lab you will turn the empty Unity project from module 00 into
a real senior project skeleton, with the folder structure, asmdefs,
and conventions you can build a game on top of.

**Time**: 30–45 minutes.

**Starter**: your `UnitySeniorLab` project from module 00.

---

## Goals

By the end of this lab you will have:

- The full senior folder layout under `Assets/`.
- A runtime asmdef in `Assets/Scripts/`.
- A test asmdef in `Assets/Tests/EditMode/` and one in
  `Assets/Tests/PlayMode/`.
- A `M_Ground` material using URP/Lit.
- A `TestCube` prefab using the material.
- A `Main.unity` scene with the prefab in it.
- A `Health.cs` MonoBehaviour on the cube.
- An `EditMode` test that verifies `Health` math without entering
  Play Mode.
- A `PlayMode` test that verifies the cube starts alive.
- All committed to git with a `.gitignore` that excludes generated
  folders.

---

## Step 1 — Folder structure

In the Project window, right-click → Create → Folder. Create:

```
Assets/
  Scenes/
  Scripts/
    Player/
  Materials/
  Shaders/
  Prefabs/
  Settings/
  Editor/
  Tests/
    EditMode/
    PlayMode/
```

You can drag existing scripts into `Scripts/Player/`. Do not put
anything at the root of `Assets/`.

## Step 2 — Runtime asmdef

Right-click `Assets/Scripts/` → **Create → Assembly Definition**. Name
it `MyGame.Runtime`. The auto-generated `.asmdef` is fine; we don't
need any references yet.

Open the `.asmdef` and confirm:

- `"name": "MyGame.Runtime"`
- `"rootNamespace": "MyGame"`
- `"autoReferenced": true`

Why we want this: scripts in folders with an asmdef compile into a
named assembly, not `Assembly-CSharp`. We can later restrict what
this assembly sees, and incremental compiles are faster.

## Step 3 — Test asmdefs

In `Assets/Tests/EditMode/`, right-click → Create → Assembly
Definition. Name it `MyGame.Tests.EditMode`.

In the asmdef inspector:

- ☑ **Test Assemblies** (this enables NUnit and the test runner)
- Reference: `MyGame.Runtime`
- Platforms: **Editor only** (set `includePlatforms: ["Editor"]`)

Repeat for `Assets/Tests/PlayMode/` with the same settings except
no `includePlatforms` restriction.

The test runner needs to know which assembly is "the test assembly";
the checkbox is what does it.

## Step 4 — The `Health` MonoBehaviour

Create `Assets/Scripts/Player/Health.cs`:

```csharp
using System;
using UnityEngine;

namespace MyGame.Player
{
    [Serializable]
    public struct HealthData
    {
        public int Max;
        public int Current;
    }

    public class Health : MonoBehaviour
    {
        [SerializeField] HealthData _data = new() { Max = 100, Current = 100 };

        public int Max => _data.Max;
        public int Current => Mathf.Max(0, _data.Current);
        public bool IsDead => Current == 0;

        public event Action<int> Damaged;
        public event Action Died;

        public void TakeDamage(int amount)
        {
            if (amount <= 0 || IsDead) return;
            int newCurrent = Mathf.Max(0, _data.Current - amount);
            int delta = _data.Current - newCurrent;
            _data.Current = newCurrent;
            Damaged?.Invoke(delta);
            if (IsDead) Died?.Invoke();
        }

        public void Heal(int amount)
        {
            if (amount <= 0 || IsDead) return;
            _data.Current = Mathf.Min(_data.Max, _data.Current + amount);
        }
    }
}
```

Notes:

- The data is a `[Serializable] struct` so it shows in the
  inspector.
- `Max` and `Current` clamp to `[0, Max]`. No negative health.
- Events for `Damaged` and `Died`. Decouples UI from this script.
- No `Update` — the script is event-driven.

## Step 5 — An EditMode test for `Health`

Create `Assets/Tests/EditMode/HealthTests.cs`:

```csharp
using NUnit.Framework;
using MyGame.Player;

public class HealthTests
{
    [Test]
    public void TakeDamage_ReducesCurrent()
    {
        var go = new GameObject("Test");
        var h = go.AddComponent<Health>();
        h.TakeDamage(30);
        Assert.AreEqual(70, h.Current);
        Object.DestroyImmediate(go);
    }

    [Test]
    public void TakeDamage_NeverBelowZero()
    {
        var go = new GameObject("Test");
        var h = go.AddComponent<Health>();
        h.TakeDamage(9999);
        Assert.AreEqual(0, h.Current);
        Assert.IsTrue(h.IsDead);
        Object.DestroyImmediate(go);
    }

    [Test]
    public void Died_FiresOnce()
    {
        var go = new GameObject("Test");
        var h = go.AddComponent<Health>();
        int diedCount = 0;
        h.Died += () => diedCount++;
        h.TakeDamage(50);
        h.TakeDamage(60);    // already dead, should not re-fire
        Assert.AreEqual(1, diedCount);
        Object.DestroyImmediate(go);
    }
}
```

**Why EditMode, not PlayMode**: the logic is pure; no Unity frame
loop is needed. EditMode tests are 10–100× faster.

Open **Window → General → Test Runner → EditMode tab**. Click
**Run All**. All three should pass.

## Step 6 — A material, a prefab, a scene

1. **Create a material** in `Assets/Materials/`. Name it `M_Ground`.
   Set its shader to **Universal Render Pipeline/Lit**. Set the
   Base Color to a muted green.
2. **Create a 3D Cube** in the scene (GameObject → 3D Object → Cube).
3. Drag the `M_Ground` material onto the cube. The cube is now
   green-lit.
4. **Drag the cube from the Hierarchy into `Assets/Prefabs/`** to
   create a prefab. Name it `TestCube`. Delete the cube from the
   scene.
5. Drag `TestCube` from `Assets/Prefabs/` into the scene twice.
6. Save the scene as `Assets/Scenes/Main.unity`.
7. **Add the scene to Build Settings** (File → Build Settings →
   Add Open Scenes).

## Step 7 — A PlayMode test for the prefab

Create `Assets/Tests/PlayMode/CubeSpawnTests.cs`:

```csharp
using System.Collections;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;

public class CubeSpawnTests
{
    [UnityTest]
    public IEnumerator MainScene_HasAtLeastOneCube()
    {
        // Load the scene additively
        var op = SceneManager.LoadSceneAsync("Main", LoadSceneMode.Additive);
        while (!op.isDone) yield return null;

        var scene = SceneManager.GetSceneByName("Main");
        var roots = scene.GetRootGameObjects();

        int cubeCount = 0;
        foreach (var r in roots)
        {
            cubeCount += r.GetComponentsInChildren<MeshFilter>().Length;
        }

        Assert.GreaterOrEqual(cubeCount, 1, "Expected at least one cube in Main");
    }
}
```

Open the Test Runner → **PlayMode tab** → **Run All**. The test
loads the scene additively and counts meshes.

## Step 8 — The `.gitignore`

If you haven't, initialize git and add a `.gitignore`:

```bash
cd ~/UnityProjects/UnitySeniorLab
git init
```

Create `.gitignore` at the project root with the contents from
module 00 (`Library/`, `Temp/`, `Logs/`, `UserSettings/`, etc.).

First commit:

```bash
git add -A
git commit -m "Initial senior skeleton: folder layout, asmdefs, Health + tests"
```

## Step 9 — Verify

```bash
# Folder structure
ls Assets/
# expect: Scenes/ Scripts/ Materials/ Shaders/ Prefabs/ Settings/ Editor/ Tests/

# Asmdefs
ls Assets/Scripts/*.asmdef
ls Assets/Tests/EditMode/*.asmdef
ls Assets/Tests/PlayMode/*.asmdef

# No garbage at Assets/ root
ls Assets/ | grep -E "\.cs$|\.png$|\.mat$"
# expect: empty output

# Tests compile and pass via CLI (if Unity is in PATH):
"$UNITY" -batchmode -projectPath "$PWD" -runTests -testPlatform EditMode -logFile /tmp/unity-tests.log
grep -E "Tests passed|Tests failed" /tmp/unity-tests.log
# expect: 0 failed
```

---

## Stretch goals

- Add a `DamageDealer.cs` MonoBehaviour that takes a damage value
  and fires `TakeDamage` on collision. Use a layer mask to only
  affect certain objects.
- Add an editor script in `Assets/Editor/Build/` that, on save,
  prints the count of `Health` components in the open scene. This
  is the skeleton of a build report.
- Add a ScriptableObject `PlayerConfig.cs` in `Assets/Scripts/Player/`
  with max-health, sprint-speed, etc. Create a concrete
  `DefaultPlayerConfig.asset` and reference it from the prefab.

---

## What you should now understand

- Why the senior folder layout exists and what goes where.
- How asmdefs work and why they're worth the day-one setup.
- The difference between EditMode and PlayMode tests.
- Why the `material` getter leaks and you should use
  `MaterialPropertyBlock` for variation.
- Why prefab variants and nested prefabs are the senior way to
  compose.
- Why `.meta` files matter and must be committed.
