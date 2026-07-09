# Lab 04 — Memory Optimization with the Memory Profiler

The Memory Profiler is the senior's primary tool. This lab is hands-
on with it.

**Time**: 90 minutes.

**Prerequisite**: Memory Profiler package installed (module 0).

---

## Step 1 — The empty project

1. Open `UnitySeniorLab`.
2. Add a scene with 100 cubes (use a `for` loop in a MonoBehaviour
   `Start`, or duplicate them in the editor).
3. Add a script that:
   - Updates each cube's position every frame
     (sin-wave on Y axis).
   - Logs every 60 frames.
4. Run Play. Open the Memory Profiler.

## Step 2 — First snapshot

Take a snapshot. Don't move. Note the Summary:

- **Total**: a few hundred MB (mostly editor overhead).
- **Managed**: should be < 30 MB.
- **Native → Textures**: probably small in this scene.

Now **click on Memory Map → Unity → Textures**. Sort by size.
The largest texture is likely the default skybox or the URP
fallback. This is normal in a fresh scene; the data is what
matters in a real game.

## Step 3 — Diff snapshots

Take snapshot A. Run Play for 60 frames. Take snapshot B. Diff:

- Look at **Managed Allocations**. Are there short-lived arrays
  or strings?
- Look at **Native Allocations**. Any growing entries?

If your `Update` is clean, the diff should be near-zero in steady
state.

## Step 4 — Add a leak

Add this to one of the cubes:

```csharp
readonly List<Vector3> _positions = new();

void Update()
{
    _positions.Add(transform.position);
    // never trimmed
}
```

Run Play for 5 seconds. Snapshot. Compare to the snapshot from
step 2. **The list has grown to ~300 entries** (~4.8 KB of
managed heap).

The Memory Profiler shows the new entries under **Managed →
List<Vector3>** in the **Objects** tab.

## Step 5 — Fix the leak (and verify)

Cap the list:

```csharp
const int MaxHistory = 60;
readonly Queue<Vector3> _positions = new(MaxHistory);

void Update()
{
    if (_positions.Count >= MaxHistory) _positions.Dequeue();
    _positions.Enqueue(transform.position);
}
```

Re-snapshot. Diff. The list is now bounded. **This is the
senior pattern: any collection that grows has a bound.**

## Step 6 — Add a native leak

Replace the cube's material assignment in `Start`:

```csharp
NativeArray<float> _native;

void Start()
{
    _native = new NativeArray<float>(1024, Allocator.Persistent);
}
```

Note: no `OnDestroy` Dispose.

Run, exit Play. The console will show:

```
A Native Collection has not been disposed...
```

Add the fix:

```csharp
void OnDestroy()
{
    if (_native.IsCreated) _native.Dispose();
}
```

Re-run, exit. No warning.

## Step 7 — Texture pool audit

Import a few large textures into `Assets/Textures/`:

- 2048×2048 PNG (no compression, default settings).
- 4096×4096 PNG.
- 1024×1024 PNG with mipmaps.

For each, check the import inspector:

- **Texture Type**: Default.
- **Format**: Automatic (no compression).
- **Max Size**: 2048 / 4096 / 1024.

The Memory Profiler won't show these unless they're used in a
material. Drag each into a material on a quad. Re-snapshot.

**The findings**:

- The 2048×2048 uncompressed RGBA texture is **16 MB** in the
  texture pool.
- The 4096×4096 uncompressed RGBA texture is **64 MB**.
- The 1024×1024 with mipmaps is **5.5 MB** (mipmaps add ~33%).

**Apply the fix**: change import settings:

- **Format**: ASTC 6×6 (mobile) or BC7 (PC).
- **Max Size**: 1024 (mobile) / 2048 (PC).
- **Mipmaps**: ☑ for textures sampled at varying distances.

Re-snapshot. Texture pool drops by 80%.

## Step 8 — Write a memory regression test

Add an EditMode test that creates a known-sized NativeArray, runs
a frame, disposes, and checks the leak detector doesn't fire:

```csharp
using NUnit.Framework;
using Unity.Collections;
using UnityEngine.TestTools;

public class NativeLeakTests
{
    [Test]
    public void NativeArray_LeakDetectorFindsLeak()
    {
        // Don't dispose
        var arr = new NativeArray<int>(100, Allocator.Persistent);
        LogAssert.Expect(LogType.Warning, new System.Text.RegularExpressions.Regex(".*not been disposed.*"));
        // Force a domain reload or end of test to trigger the leak detector
    }

    [Test]
    public void NativeArray_NoLeakWhenDisposed()
    {
        var arr = new NativeArray<int>(100, Allocator.Persistent);
        arr.Dispose();
        // No warning expected
    }
}
```

## Step 9 — Document your findings

Write a `MemoryLab/Notes.md` with:

- The four key numbers from your snapshots: RSS, managed heap,
  texture pool, GC.Alloc per frame.
- The top 3 texture pool entries and their sizes.
- The top 3 changes you'd make to reduce memory.
- Re-snapshot numbers after the changes.

This is the senior's weekly review for a real game. **Do it
every week, on the lowest-spec target device, with the worst
content loaded.**

---

## Stretch goals

- Use `UnityEngine.Profiling.Memory.Experimental.MemoryProfiler.TakeSnapshot`
  to capture snapshots from a build (not the editor). The Memory
  Profiler can open `.snap` files.
- Capture a snapshot at a frame where you know there's a hitch.
  Find the new managed allocations; those are the GC.
- Use `RenderDoc` (a separate tool) to capture a frame and look
  at the textures bound. Find the ones you don't need.

---

## What you should now understand

- The Memory Profiler is a snapshot tool, not a real-time monitor.
- The Summary tab gives the high-level numbers.
- The Memory Map shows the tree of allocations.
- **The diff between two snapshots is the killer feature**.
- Native leaks show up as warnings on exit (Persistent only).
- Texture import settings dominate the texture pool.
- A growing collection is a leak; cap it.
