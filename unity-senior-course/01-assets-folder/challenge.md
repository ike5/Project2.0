# Challenge 01 — Senior Project Skeleton, Extended

You've built the skeleton; now stress it.

This is the "before merge" check. Get it right and you've earned
the right to call your project structure senior. Get it wrong and
you'll spend the next year paying for it.

---

## Part A — A second feature, isolated

Add a `Combat` feature with this layout:

```
Scripts/
  Combat/
    Combat.asmdef          ← its own assembly, references MyGame.Runtime
    Health.cs              ← move from Player
    IDamageable.cs
    DamageDealer.cs
    DamageOnHit.cs
```

You should now have **two feature asmdefs** (`MyGame.Player` and
`MyGame.Combat`), and the existing tests should still pass.

**Why this is the senior test**: a feature should be **portable**.
You should be able to copy the `Combat/` folder into another Unity
project and have it work, assuming that project has the right
runtime asmdef. If it doesn't compile, you have hard dependencies
hidden somewhere.

## Part B — A ScriptableObject config

Create `Scripts/Player/PlayerConfig.cs`:

```csharp
using UnityEngine;

namespace MyGame.Player
{
    [CreateAssetMenu(fileName = "PlayerConfig", menuName = "MyGame/Player Config")]
    public class PlayerConfig : ScriptableObject
    {
        [SerializeField] int _maxHealth = 100;
        [SerializeField] float _moveSpeed = 5f;
        [SerializeField] float _sprintMultiplier = 1.5f;

        public int MaxHealth => _maxHealth;
        public float MoveSpeed => _moveSpeed;
        public float SprintMultiplier => _sprintMultiplier;
    }
}
```

In the project, **right-click → Create → MyGame → Player Config**,
name it `DefaultPlayerConfig.asset`. Reference it from `Health.cs`
so `Max` is no longer hard-coded.

**The senior test**: change `DefaultPlayerConfig.asset`'s max
health in the inspector. Re-run EditMode tests. They should still
pass — your test should construct a `PlayerConfig` and inject it,
not rely on the asset.

## Part C — A runtime editor warning

Create `Editor/Build/HealthValidator.cs` that, when you save a scene
in the editor, scans all `Health` components in the scene and warns
in the console if any have `Max <= 0` or `Current > Max`.

```csharp
#if UNITY_EDITOR
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using MyGame.Player;

public static class HealthValidator
{
    [InitializeOnLoadMethod]
    static void Init()
    {
        EditorSceneManager.sceneSaved += OnSceneSaved;
    }

    static void OnSceneSaved(UnityEngine.SceneManagement.Scene scene)
    {
        var healths = Object.FindObjectsByType<Health>(FindObjectsSortMode.None);
        foreach (var h in healths)
        {
            if (h.Max <= 0)
                Debug.LogWarning($"[Health] {h.name} has Max <= 0", h);
        }
    }
}
#endif
```

**Stretch**: use `HierarchyProperty` or `StageUtility` to find
objects in prefab stage too, not just the open scene.

## Part D — A test for the warning

You can't easily test `Debug.LogWarning` itself, but you can
extract the validation logic into a pure function:

```csharp
public static class HealthValidator
{
    public static IEnumerable<string> FindProblems(IEnumerable<Health> healths)
    {
        foreach (var h in healths)
        {
            if (h.Max <= 0) yield return $"{h.name}: Max <= 0";
            if (h.Current > h.Max) yield return $"{h.name}: Current > Max";
            if (h.Current < 0) yield return $"{h.name}: Current < 0";
        }
    }
}
```

And the editor script calls `Debug.LogWarning` for each problem.
Now you can test `FindProblems` in EditMode.

**The senior insight**: the rule "logic in testable units,
side-effects at the edges" applies to editor code too. Most editor
code is untested, which is why the editor is usually the buggiest
part of a Unity project.

## Part E — A scene-loading utility

Create `Scripts/Scenes/SceneLoader.cs` that exposes:

```csharp
public static class SceneLoader
{
    public static async Awaitable LoadAsync(string sceneName, LoadSceneMode mode = LoadSceneMode.Single)
    {
        var op = SceneManager.LoadSceneAsync(sceneName, mode);
        op.allowSceneActivation = true;
        while (!op.isDone) await Awaitable.NextFrameAsync();
    }
}
```

Use it from your PlayMode test instead of the inline scene load.
This is the senior pattern: a thin abstraction over engine APIs
that you can swap out (e.g. for Addressables later) without
rewriting every call site.

## Stretch — a build report

Create `Editor/Build/BuildReportLogger.cs` that, after a build,
writes a CSV summary of total assets by type to
`Build/reports/asset-summary.csv`. The point of this exercise is
to learn `BuildReport` and the asset database, both of which
are senior tools.

---

## What we're testing

- **Folder structure discipline.** You can move code without
  breaking things.
- **Asmdef isolation.** Each feature is a unit.
- **Configuration via ScriptableObject**, not hard-coded values.
- **Editor code is testable** when you push the side-effects to
  the edges.
- **Engine APIs are wrapped**, not called inline.

If you can do this challenge in 90 minutes, you have the senior
discipline. If it takes 4 hours, you learned something the easy
way would have hidden.

---

## Submit / verify

```bash
# Tree of the new structure
tree -L 3 Assets/

# All tests still pass
unity-run-tests EditMode
unity-run-tests PlayMode
```

Where `unity-run-tests` is your own CLI alias for:

```bash
"$UNITY" -batchmode -projectPath "$PWD" -runTests -testPlatform EditMode -logFile -
```

(Find your Unity binary path with: Hub → Installs → ⋯ → Show in
Finder.)
