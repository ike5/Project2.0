# Challenge 03 — Find the Hidden Allocation

The senior's morning routine: open the Profiler, look for the
biggest red bar, find the allocation, fix it. This challenge gives
you a deliberately leaky system. Find every leak.

**Time**: 60 minutes.

---

## The system

```csharp
using System.Collections.Generic;
using System.Text;
using UnityEngine;

namespace MyGame.Game
{
    public class GameManager : MonoBehaviour
    {
        public static GameManager Instance { get; private set; }

        readonly List<GameObject> _enemies = new();
        readonly List<GameObject> _projectiles = new();
        readonly Dictionary<int, string> _entityNames = new();
        readonly StringBuilder _sb = new();

        int _frameCount;
        int _enemiesKilled;

        void Awake() => Instance = this;

        void Update()
        {
            _frameCount++;

            // Logging
            Debug.Log($"Frame {_frameCount}: {CountActive(_enemies)} enemies, " +
                      $"{CountActive(_projectiles)} projectiles, " +
                      $"{_enemiesKilled} killed");

            // Spawning
            if (_frameCount % 60 == 0)
            {
                SpawnEnemy();
            }

            // Cleanup dead
            for (int i = 0; i < _enemies.Count; i++)
            {
                if (_enemies[i] == null) _enemies.RemoveAt(i--);
            }

            // Build a path string for AI
            var path = BuildPath();
        }

        int CountActive(List<GameObject> list)
        {
            int n = 0;
            foreach (var go in list) if (go != null) n++;
            return n;
        }

        void SpawnEnemy()
        {
            var prefab = Resources.Load<GameObject>("Enemy");   // ← look at this
            if (prefab == null) return;
            var go = Instantiate(prefab);
            go.name = $"Enemy {_enemies.Count}";
            _enemies.Add(go);
        }

        string BuildPath()
        {
            _sb.Clear();
            _sb.Append("Path: ");
            foreach (var e in _enemies)
            {
                if (e == null) continue;
                _sb.Append(e.name).Append(";");
            }
            return _sb.ToString();
        }

        public void RecordKill(GameObject go)
        {
            _enemies.Remove(go);
            _enemiesKilled++;
        }
    }
}
```

**The claim**: this has 0 allocations per frame after the first.

**The truth**: at least 6.

---

## Your job

1. Open Memory Profiler. Snapshot A. Play for 5 seconds. Snapshot B.
2. Diff. List every allocation. For each, name:
   - The line of code that caused it.
   - Whether it's a managed or native allocation.
   - Whether it's per-frame or one-shot.
3. Fix each one. Re-snapshot, re-diff. Confirm the diff is empty.

---

## What the senior finds (don't peek)

- **`$"..."` interpolation in `Update`**: two strings per frame
  (the format result and the concatenation).
- **`Resources.Load<GameObject>("Enemy")` in `SpawnEnemy`**: a
  sync asset load every 60 frames. Even if cached, the call
  itself is expensive.
- **`Instantiate(prefab)`**: that's the point, but the
  `go.name = $"Enemy {_enemies.Count}"` allocates a string every
  spawn.
- **`BuildPath()` → `_sb.ToString()`**: allocates a string every
  frame (used or not).
- **`_enemies.RemoveAt(i--)`** in a tight loop: O(n²) and may
  allocate when the list's internal array resizes.
- **`_enemiesKilled` is a managed `int` field, fine** — but
  incrementing it in `RecordKill` doesn't allocate. Sanity check.
- **`Instance` singleton**: the `Awake` assignment is fine; just
  confirm it's not null in `Update`.

There are likely more. The point: **count them all**.

---

## The senior fix (sketch)

```csharp
// Cached format - log every 60 frames
int _lastLogFrame;

void Update()
{
    if (_frameCount - _lastLogFrame >= 60)
    {
        _lastLogFrame = _frameCount;
        // Pre-format or just count
        Debug.Log($"F:{_frameCount} E:{_enemies.Count} P:{_projectiles.Count}");
    }

    // Addressables for spawning, not Resources.Load
    if (_frameCount % 60 == 0) SpawnEnemy();
}

async void SpawnEnemy()   // ok in lifecycle hooks
{
    var handle = Addressables.LoadAssetAsync<GameObject>("Enemy");
    await handle;
    if (handle.Status == AsyncOperationStatus.Succeeded)
    {
        var go = Instantiate(handle.Result);
        // ... use a counter, not string interp
        go.name = "Enemy_" + _enemies.Count.ToString(CultureInfo.InvariantCulture);
    }
}
```

---

## Submit

A `MemoryLab/Notes.md` with:

- The diff between Snapshot A and B (managed section).
- A line-by-line fix for each allocation.
- A re-snapshot showing the diff is empty (or near-empty).

---

## What we're testing

- The Memory Profiler diff is the senior's first tool. Can you
  read it?
- Can you trace a managed allocation back to a line of code?
- Can you fix the system so the diff is empty?
- Do you understand why Resources.Load is wrong in production
  code?

The senior dev who can't do this can't ship a Unity game. It's
that basic.
