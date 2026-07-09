# Lab 12: Profile and Fix a Real Game

**Time**: 90 minutes
**Goal**: Take a deliberately-slow scene, profile it with the Profiler and Memory Profiler, identify three bottlenecks, fix them, and verify the frame time dropped.

## Setup (5 min)

1. New Unity 6 project.
2. Install `com.unity.memoryprofiler` and `com.unity.profileanalyzer`.
3. Create a scene `ProfilerTest` with a plane, a directional light, and a camera.
4. Add 1000 cubes in a 10x10x10 grid using a script.

## Part A: Build a deliberately-slow scene (20 min)

`ProfilerHarness.cs`:
```csharp
using System.Collections.Generic;
using System.Text;
using UnityEngine;

public class ProfilerHarness : MonoBehaviour
{
    public GameObject unitPrefab;
    public int unitCount = 1000;

    readonly List<GameObject> _units = new();
    readonly StringBuilder _sb = new();
    int _frameCount;

    void Start()
    {
        for (int i = 0; i < unitCount; i++)
        {
            var go = Instantiate(unitPrefab, Random.insideUnitSphere * 50, Quaternion.identity);
            _units.Add(go);
        }
    }

    void Update()
    {
        _frameCount++;

        // Bug 1: GC alloc every frame
        var positions = new Vector3[unitCount];
        for (int i = 0; i < unitCount; i++)
            positions[i] = _units[i].transform.position;

        // Bug 2: O(n^2) loop
        for (int i = 0; i < _units.Count; i++)
        {
            for (int j = 0; j < _units.Count; j++)
            {
                if (i == j) continue;
                var dir = _units[i].transform.position - _units[j].transform.position;
                if (dir.sqrMagnitude < 1f) /* collision */ ;
            }
        }

        // Bug 3: String allocation in hot path
        if (_frameCount % 60 == 0)
            _sb.Append($"Frame {_frameCount} units {_units.Count}").ToString();
    }
}
```

Each unit has a MeshRenderer, MeshFilter, BoxCollider, Rigidbody. 1000 of them. The O(n^2) loop is the main cost. The Vector3[] alloc is GC pressure. The StringBuilder.ToString() is per-frame alloc.

## Part B: Profile (15 min)

1. Open the Profiler (Window > Analysis > Profiler).
2. Enter Play mode. Let the scene run for 10 seconds.
3. Look at the CPU module. The main thread bar should be 30-50 ms (1.5-3 fps on a mid-tier mobile).
4. Click into the main thread bar. Find `ProfilerHarness.Update`. Click into it. Find the O(n^2) loop.
5. Look at the GC.Alloc markers (yellow icons). Each frame should show a 16 KB allocation (the Vector3[] array).
6. Open the Memory Profiler. Take a snapshot after 30 seconds. Look at the managed heap. The StringBuilder and the array of positions should be visible.

Record the numbers:
- Frame time: ___
- GC alloc per frame: ___
- Number of GC events per minute: ___
- Managed heap size: ___

## Part C: Fix the three bugs (30 min)

### Fix 1: Eliminate the per-frame allocation

Cache the positions array:
```csharp
Vector3[] _positions;

void Start()
{
    _positions = new Vector3[unitCount];
    for (int i = 0; i < unitCount; i++) /* ... */
}

void Update()
{
    for (int i = 0; i < unitCount; i++)
        _positions[i] = _units[i].transform.position;
}
```

The allocation is gone. The GC.Alloc marker disappears.

### Fix 2: Spatial hash for the O(n^2) loop

For 1000 units with a 1m collision radius, the O(n^2) is 1,000,000 distance checks per frame. Use a spatial hash:

```csharp
Dictionary<long, List<int>> _grid = new();
const float CellSize = 1f;

long CellKey(Vector3 p) => ((long)Mathf.FloorToInt(p.x / CellSize) << 32) | (uint)Mathf.FloorToInt(p.z / CellSize);

void Update()
{
    _grid.Clear();
    for (int i = 0; i < _units.Count; i++)
    {
        var key = CellKey(_units[i].transform.position);
        if (!_grid.TryGetValue(key, out var list))
        {
            list = new List<int>();
            _grid[key] = list;
        }
        list.Add(i);
    }

    // Check only neighbors in the same cell
    foreach (var kv in _grid)
    {
        if (kv.Value.Count < 2) continue;
        for (int i = 0; i < kv.Value.Count; i++)
            for (int j = i + 1; j < kv.Value.Count; j++)
                /* distance check */ ;
    }
}
```

For 1000 units with 1m cells, most cells have 0-2 units. The inner loop becomes O(n), not O(n^2).

### Fix 3: Remove the StringBuilder.ToString() allocation

```csharp
if (_frameCount % 60 == 0)
    Debug.Log(_sb.Append($"Frame {_frameCount}").ToString());
```

`Append(string)` and `ToString()` both allocate. Use `Debug.Log` directly with a formatted string and let the GC handle it once per second, not per frame. Or pre-allocate the format:

```csharp
if (_frameCount % 60 == 0)
    Debug.Log($"Frame {_frameCount} units {_units.Count}");
```

The string interpolation allocates once per second, not once per frame.

## Part D: Profile again and verify (15 min)

1. Re-run the scene. Profile.
2. Record the new numbers:
   - Frame time: ___
   - GC alloc per frame: ___
   - GC events per minute: ___
3. Compare to the baseline. The frame time should drop by 80%+. The GC.Alloc markers should be gone or near-zero.

The senior practice: write down the numbers before and after. The "feels faster" is not a metric. The numbers are.

## Part E: Memory Profiler diff (10 min)

1. Take a snapshot of the original (buggy) version. Save as `before.snap`.
2. Apply the fixes. Take a snapshot of the fixed version. Save as `after.snap`.
3. Open the Memory Profiler. Load both. Compare.
4. The "Managed Objects" view should show the Vector3[] is no longer allocating. The total managed heap should be smaller.

## Verification

1. Frame time dropped from > 30 ms to < 6 ms (5x improvement).
2. GC.Alloc per frame dropped from > 16 KB to < 1 KB.
3. The Memory Profiler shows no growth in managed heap over time.
4. The O(n^2) loop is replaced with a spatial hash, the inner loop is O(1) per cell.
5. The StringBuilder.ToString() is no longer allocating per frame.

## Common pitfalls

- **The Profiler overhead makes the numbers look worse than reality**: the Profiler adds 1-2 ms of overhead. Don't optimize the Profiler overhead, optimize the game.
- **Deep profile in the editor distorts the numbers**: deep profile is 5-10x slower. Use a development build for absolute numbers.
- **GC.Alloc on first call**: the first frame of a scene allocates a lot (initial allocations). Don't panic about frame 0's 200 KB alloc. Look at frame 100, 1000, 10000.
- **Optimizing a 0.1 ms function**: the spatial hash optimization saved 25 ms. The StringBuilder fix saved 0.05 ms. Don't waste time on the small wins when there's a big win to grab.
- **Ignoring the render thread**: if main thread is 5 ms but render thread is 20 ms, the frame is 20 ms. The main thread is not the bottleneck. Profile the render thread too.
- **Single-frame optimization**: optimizing for one frame's screenshot doesn't optimize the game. Use the Profile Analyzer to see the distribution.

## What we're testing

- Can you read the Profiler window and find the bottleneck?
- Can you identify GC.Alloc hot spots from the Profiler markers?
- Can you write a spatial hash to replace an O(n^2) loop?
- Can you capture and diff Memory Profiler snapshots?
- Do you understand the difference between main thread time, render thread time, and GPU time?

## Stretch goals

- Profile the same scene on an Android device. Compare frame times. The mobile GPU is much weaker; the bottleneck shifts.
- Add a `ProfilerMarker` around the spatial hash. Verify it shows up in the Profiler as `ProfilerHarness.SpatialHash`.
- Use `ProfilerRecorder` to read the frame time at runtime and display it on a debug overlay. Log to a CSV file when running a soak test.
- Run the scene for 10 minutes. Watch the managed heap in the Profiler. If it grows linearly, you have a leak. Find it.
