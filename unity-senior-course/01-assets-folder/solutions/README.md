# Solutions 01 — Senior Project Skeleton

Reference implementations for the lab and challenge.

The shape of these is the senior way to write the code; if your
solution has the same shape, you've earned the right to call it
senior. If your code is shorter, more efficient, or more readable
than this, that's fine — share it.

---

## Lab — Reference layout

```
Assets/
├── Editor/
│   └── (later modules add editor scripts)
├── Materials/
│   └── M_Ground.mat
├── Prefabs/
│   └── TestCube.prefab
├── Scenes/
│   └── Main.unity
├── Scripts/
│   ├── MyGame.Runtime.asmdef
│   └── Player/
│       └── Health.cs
├── Settings/
│   ├── URP-Balanced.asset
│   ├── URP-Performance.asset
│   └── URP-Performant.asset
├── Shaders/
│   └── (empty for now)
└── Tests/
    ├── EditMode/
    │   ├── MyGame.Tests.EditMode.asmdef
    │   └── HealthTests.cs
    └── PlayMode/
        ├── MyGame.Tests.PlayMode.asmdef
        └── CubeSpawnTests.cs
```

### `Assets/Scripts/MyGame.Runtime.asmdef`

```json
{
    "name": "MyGame.Runtime",
    "rootNamespace": "MyGame",
    "references": [],
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

### `Assets/Tests/EditMode/MyGame.Tests.EditMode.asmdef`

```json
{
    "name": "MyGame.Tests.EditMode",
    "references": [
        "MyGame.Runtime"
    ],
    "includePlatforms": ["Editor"],
    "excludePlatforms": [],
    "allowUnsafeCode": false,
    "overrideReferences": true,
    "precompiledReferences": [
        "nunit.framework.dll"
    ],
    "autoReferenced": false,
    "defineConstraints": [],
    "versionDefines": [],
    "noEngineReferences": false,
    "optionalUnityReferences": ["TestAssemblies"]
}
```

In Unity 6 the `"optionalUnityReferences"` field is now controlled
by a checkbox in the asmdef inspector; the JSON may omit it. The
inspector-controlled equivalent is **Test Assemblies: ☑** in the
asmdef.

### `Assets/Scripts/Player/Health.cs`

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

    /// <summary>
    /// Tracks hit points. Event-driven; no Update.
    /// </summary>
    [DisallowMultipleComponent]
    public class Health : MonoBehaviour
    {
        [SerializeField] HealthData _data = new() { Max = 100, Current = 100 };

        public int Max => _data.Max;
        public int Current => Mathf.Max(0, _data.Current);
        public bool IsDead => Current == 0;

        public event Action<int> Damaged;
        public event Action Healed;
        public event Action Died;

        public void TakeDamage(int amount)
        {
            if (amount <= 0 || IsDead) return;
            int before = _data.Current;
            int after = Mathf.Max(0, before - amount);
            int delta = before - after;
            _data.Current = after;
            Damaged?.Invoke(delta);
            if (IsDead) Died?.Invoke();
        }

        public void Heal(int amount)
        {
            if (amount <= 0 || IsDead) return;
            int before = _data.Current;
            int after = Mathf.Min(_data.Max, before + amount);
            _data.Current = after;
            Healed?.Invoke(after - before);
        }
    }
}
```

### `Assets/Tests/EditMode/HealthTests.cs`

```csharp
using NUnit.Framework;
using UnityEngine;
using MyGame.Player;

public class HealthTests
{
    Health MakeHealth()
    {
        var go = new GameObject("TestHealth");
        return go.AddComponent<Health>();
    }

    [Test]
    public void TakeDamage_ReducesCurrent()
    {
        var h = MakeHealth();
        try
        {
            h.TakeDamage(30);
            Assert.AreEqual(70, h.Current);
        }
        finally { Object.DestroyImmediate(h.gameObject); }
    }

    [Test]
    public void TakeDamage_NeverBelowZero()
    {
        var h = MakeHealth();
        try
        {
            h.TakeDamage(9999);
            Assert.AreEqual(0, h.Current);
            Assert.IsTrue(h.IsDead);
        }
        finally { Object.DestroyImmediate(h.gameObject); }
    }

    [Test]
    public void TakeDamage_NegativeAmount_Ignored()
    {
        var h = MakeHealth();
        try
        {
            h.TakeDamage(-10);
            Assert.AreEqual(100, h.Current);
        }
        finally { Object.DestroyImmediate(h.gameObject); }
    }

    [Test]
    public void Died_FiresOnce_WhenCrossingZero()
    {
        var h = MakeHealth();
        try
        {
            int diedCount = 0;
            h.Died += () => diedCount++;

            h.TakeDamage(50);
            Assert.AreEqual(0, diedCount);

            h.TakeDamage(60);
            Assert.AreEqual(1, diedCount);

            h.TakeDamage(10);
            Assert.AreEqual(1, diedCount, "Died should not re-fire");
        }
        finally { Object.DestroyImmediate(h.gameObject); }
    }

    [Test]
    public void Heal_CapsAtMax()
    {
        var h = MakeHealth();
        try
        {
            h.TakeDamage(50);
            h.Heal(999);
            Assert.AreEqual(100, h.Current);
        }
        finally { Object.DestroyImmediate(h.gameObject); }
    }

    [Test]
    public void Damaged_ReportsActualDelta()
    {
        var h = MakeHealth();
        try
        {
            int lastDelta = 0;
            h.Damaged += d => lastDelta = d;
            h.TakeDamage(50);
            Assert.AreEqual(50, lastDelta);
            h.TakeDamage(9999);
            Assert.AreEqual(50, lastDelta, "Second damage capped at 50, delta should be 50");
        }
        finally { Object.DestroyImmediate(h.gameObject); }
    }
}
```

### `Assets/Tests/PlayMode/CubeSpawnTests.cs`

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
        var op = SceneManager.LoadSceneAsync("Main", LoadSceneMode.Additive);
        while (!op.isDone) yield return null;

        var scene = SceneManager.GetSceneByName("Main");
        int cubeCount = 0;
        foreach (var root in scene.GetRootGameObjects())
        {
            cubeCount += root.GetComponentsInChildren<MeshFilter>(true).Length;
        }
        Assert.GreaterOrEqual(cubeCount, 1);
    }
}
```

---

## Challenge — Reference solutions

### Part A — `MyGame.Combat` asmdef

`Assets/Scripts/Combat/Combat.asmdef`:

```json
{
    "name": "MyGame.Combat",
    "rootNamespace": "MyGame.Combat",
    "references": [
        "MyGame.Runtime",
        "MyGame.Player"
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

Note: `MyGame.Combat` references `MyGame.Player` because it needs
`Health` and `IDamageable`. To make `Combat` truly portable, you
would move `Health` and `IDamageable` to a third assembly
(`MyGame.Shared`) and have both `Player` and `Combat` reference it.
The senior trade-off: more assemblies = more compile units = faster
build, but more indirection.

### Part B — `PlayerConfig`

```csharp
using UnityEngine;

namespace MyGame.Player
{
    [CreateAssetMenu(fileName = "PlayerConfig", menuName = "MyGame/Player Config")]
    public class PlayerConfig : ScriptableObject
    {
        [SerializeField, Min(1)] int _maxHealth = 100;
        [SerializeField, Min(0)] float _moveSpeed = 5f;
        [SerializeField, Min(1)] float _sprintMultiplier = 1.5f;

        public int MaxHealth => _maxHealth;
        public float MoveSpeed => _moveSpeed;
        public float SprintMultiplier => _sprintMultiplier;
    }
}
```

`Health.cs` updated to use the config:

```csharp
public class Health : MonoBehaviour
{
    [SerializeField] HealthData _data = new() { Max = 100, Current = 100 };
    [SerializeField] PlayerConfig _config;

    public int Max => _config != null ? _config.MaxHealth : _data.Max;
    // ...
}
```

Tests still pass because the test creates a `Health` without a
config; `Max` falls back to the serialized value. The test for
the config-injected path:

```csharp
[Test]
public void Health_UsesConfigMax()
{
    var config = ScriptableObject.CreateInstance<PlayerConfig>();
    // Use reflection or a TestOnly setter; in senior code, add a
    // public method to set the config in tests, or expose a
    // constructor. The cleanest way is dependency injection.
    var go = new GameObject("Test");
    var h = go.AddComponent<Health>();
    // Inject via SerializeField reflection
    var field = typeof(Health).GetField("_config",
        System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Instance);
    field.SetValue(h, config);
    Assert.AreEqual(100, h.Max);
    Object.DestroyImmediate(go);
    Object.DestroyImmediate(config);
}
```

In production, you would not use reflection to set the config;
you'd inject via a constructor or a `Configure` method. The
reflection-based test is the cost of using Unity's SerializeField
with no test-friendly API.

### Part C — `HealthValidator`

`Assets/Editor/Validation/HealthValidator.cs`:

```csharp
#if UNITY_EDITOR
using System.Collections.Generic;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using MyGame.Player;

public static class HealthValidator
{
    public static IEnumerable<string> FindProblems(IEnumerable<Health> healths)
    {
        foreach (var h in healths)
        {
            if (h == null) continue;
            if (h.Max <= 0)
                yield return $"{h.name}: Max <= 0 ({h.Max})";
            if (h.Current > h.Max)
                yield return $"{h.name}: Current > Max ({h.Current} > {h.Max})";
            if (h.Current < 0)
                yield return $"{h.name}: Current < 0 ({h.Current})";
        }
    }

    [InitializeOnLoadMethod]
    static void Init()
    {
        EditorSceneManager.sceneSaved += OnSceneSaved;
    }

    static void OnSceneSaved(UnityEngine.SceneManagement.Scene scene)
    {
        var healths = Object.FindObjectsByType<Health>(FindObjectsSortMode.None);
        foreach (var problem in FindProblems(healths))
        {
            Debug.LogWarning($"[HealthValidator] {problem}");
        }
    }
}
#endif
```

### Part D — Test for the validator

```csharp
using NUnit.Framework;
using UnityEngine;
using MyGame.Player;

public class HealthValidatorTests
{
    [Test]
    public void NoHealths_NoProblems()
    {
        var problems = new List<string>(HealthValidator.FindProblems(new Health[0]));
        Assert.AreEqual(0, problems.Count);
    }

    [Test]
    public void HealthWithMaxZero_IsReported()
    {
        var go = new GameObject("Test");
        var h = go.AddComponent<Health>();
        // Force Max to 0 via reflection (test-only path)
        var dataField = typeof(Health).GetField("_data",
            System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Instance);
        var data = (HealthData)dataField.GetValue(h);
        data.Max = 0;
        dataField.SetValue(h, data);

        var problems = new List<string>(HealthValidator.FindProblems(new[] { h }));
        Assert.AreEqual(1, problems.Count);
        Assert.IsTrue(problems[0].Contains("Max <= 0"));

        Object.DestroyImmediate(go);
    }
}
```

### Part E — `SceneLoader`

```csharp
using System.Threading;
using UnityEngine;
using UnityEngine.SceneManagement;

namespace MyGame.Scenes
{
    public static class SceneLoader
    {
        public static async Awaitable LoadAsync(
            string sceneName,
            LoadSceneMode mode = LoadSceneMode.Single,
            CancellationToken cancellationToken = default)
        {
            var op = SceneManager.LoadSceneAsync(sceneName, mode);
            op.allowSceneActivation = true;
            while (!op.isDone)
            {
                if (cancellationToken.IsCancellationRequested) return;
                await Awaitable.NextFrameAsync(cancellationToken);
            }
        }
    }
}
```

Note: `Awaitable.NextFrameAsync` was added in Unity 2023; if your
project is on 2022 LTS, use `await Task.Yield()` or a coroutine
bridge. The senior pattern is the same: a thin async wrapper that
all callers go through.

---

## Common pitfalls in this module

- **`.meta` files missing on commit.** Two developers have different
  GUIDs for the same file; the scene/prefab references break.
  Verify with `git status` showing `.meta` files.
- **Editor folder in the wrong case.** `editor/` doesn't strip from
  build; only `Editor/` does. macOS is case-insensitive on default
  HFS+/APFS, so it compiles locally, then fails on Linux CI.
- **Asmdefs in subfolders that don't reference the parent.** A
  script in `Scripts/Player/Sub/` without its own asmdef becomes
  part of the closest parent asmdef. Use the asmdef inspector's
  "Show Assembly Definition References" tool to verify.
- **`Resources/` in the project from a tutorial.** Remove; it
  causes shipping content to load on startup with no opt-out.
- **Scenes not in Build Settings.** A scene that isn't in Build
  Settings doesn't ship. The build silently doesn't include it;
  the test that loads it by name fails.
- **Material at the root of `Assets/`.** Move to `Materials/`. The
  filter is easier to maintain.
