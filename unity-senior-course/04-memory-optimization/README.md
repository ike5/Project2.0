# 03 — Memory Optimization with the Memory Profiler

Module 2 gave you the mental model. This module teaches you the **tool**.
The Memory Profiler is the single most important package in a senior
Unity developer's toolbox. The day you can read a snapshot is the day
you stop guessing about memory.

---

## 1. Install the Memory Profiler

**Window → Package Manager → search "Memory Profiler" → Install.**

The package is free, by Unity, and stable. Restart the editor.

Now you have **Window → Analysis → Memory Profiler** (separate from
**Window → Analysis → Profiler**).

---

## 2. Take your first snapshot

A **snapshot** is a frozen view of all memory in the player: managed
heap, native heap, every texture, every mesh, every audio clip, every
GameObject's components.

1. **Enter Play Mode** in your project.
2. Open the Memory Profiler window.
3. Click **Capture**.
4. Wait. The first capture takes 5–30 seconds; subsequent ones are
   faster.
5. The snapshot appears in the window's list. **Double-click** to open
   it.

You'll see a multi-tab view:

- **Summary**: high-level numbers (Managed, Native, Total).
- **Memory Map**: a tree of memory usage by category.
- **All Of Memory**: a flat list of every allocation, filterable.
- **Objects**: every Unity object (GameObjects, components, assets).
- **References**: who-owns-what graph.

---

## 3. The first thing to look at: Summary

The Summary tab has these numbers, in this order of importance:

| Number | What it means | Senior target (mid-range mobile) |
|--------|---------------|----------------------------------|
| **Total** | RSS-equivalent | < 1.5 GB |
| **Managed** | The GC heap | < 50 MB |
| **Native** | Unity's own + your native arrays | < 1.4 GB |
| **Native → Textures** | Texture memory | < 800 MB |
| **Native → Mesh** | Mesh memory | < 100 MB |
| **Native → Audio** | Audio memory | < 50 MB |
| **GC used** | Currently-alive managed objects | < 30 MB |

**Managed size is the easiest to fix; texture size is the easiest to
bloat.** Most shipped games have too much of both.

---

## 4. The second thing: Memory Map

The Memory Map is a tree, and the first three levels look like this:

```
Total
  Unity
    Textures
    Meshes
    Materials
    Shaders
    Audio
    Animation
    Asset Bundles
    ...
  Managed
    MemorySection
      ...
  System
    ...
```

Click on **Textures** and the right pane shows every texture in the
game, with its size. Sort by size. The top three textures are usually
the entire problem.

### Common "I have a memory problem" findings

| Finding | Cause | Fix |
|---------|-------|-----|
| One texture is 100 MB+ | Not compressed; or uncompressed ASTC/BC7 | Enable Crunch, ASTC, or BC7 compression; check `Max Size` |
| 200+ tiny textures | Every UI element has its own atlas | Combine atlases; use a single sprite atlas |
| Many "Duplicate" textures | Same texture loaded twice (e.g. Resources + AssetBundle) | Audit loading paths; use Addressables (module 7) |
| Texture is non-power-of-two | Some platforms mipmap-fail | Resize to POT in source |
| Mesh is 30 MB+ | Uncompressed, full LOD0 always loaded | Enable mesh compression; use LODs |

---

## 5. The third thing: the diff between two snapshots

This is the killer feature. Take snapshot A, run the game for 5
seconds, take snapshot B. Open A, then B, and look at the **Diff**:

- **New Managed Allocations**: which classes were created and
  survived? **This is the GC pressure list.**
- **New Native Allocations**: which native arrays, textures, or
  meshes are new?
- **Deleted Objects**: which ones went away? (Empty if the player
  was just running gameplay, which is what you want.)

The senior workflow:

1. Open a scene.
2. Snapshot A.
3. Run the worst case (5 minutes of gameplay, all systems active).
4. Snapshot B.
5. Diff.

**If anything grew, you have a leak or a churn bug. Find it.**

---

## 6. The four memory anti-patterns, and how the Profiler finds them

### 6.1 Per-frame allocations in `Update`

```csharp
void Update()
{
    var hits = Physics.RaycastAll(transform.position, transform.forward, 10f);
    // RaycastAll allocates a new RaycastHit[] every frame. 1000 fps = 60,000
    // arrays/sec. GC loves you.
    foreach (var hit in hits) ProcessHit(hit);
}
```

**Fix**: use the `RaycastNonAlloc` overload that fills a pre-allocated
array:

```csharp
readonly RaycastHit[] _hitBuf = new RaycastHit[16];

void Update()
{
    int n = Physics.RaycastNonAlloc(transform.position, transform.forward, _hitBuf, 10f);
    for (int i = 0; i < n; i++) ProcessHit(_hitBuf[i]);
}
```

In the Memory Profiler's diff, the pre-fix version shows thousands of
short-lived `RaycastHit[]`. The post-fix version is clean.

### 6.2 String concatenation in `Update`

```csharp
void Update()
{
    Debug.Log($"Player at {transform.position} health {health}");  // 2 boxes + 1 string per frame
}
```

**Fix**: gate the log:

```csharp
int _logCounter;
void Update()
{
    if ((++_logCounter & 0x3F) == 0)  // every 64 frames
    {
        Debug.Log($"Player at {transform.position} health {health}");
    }
}
```

Or use a `ZString` / `Unity.Logging` zero-alloc formatter. Or just
remove the log.

### 6.3 Coroutines that allocate on `yield`

```csharp
IEnumerator Spin()
{
    while (true)
    {
        yield return new WaitForSeconds(0.5f);   // ← allocates a WFSC every iteration
    }
}
```

**Fix**: cache the wait:

```csharp
readonly WaitForSeconds _wait = new(0.5f);
IEnumerator Spin()
{
    while (true) yield return _wait;
}
```

### 6.4 `foreach` over `List<T>`

`List<T>.GetEnumerator()` returns a struct enumerator, so most
`foreach` over a `List<T>` does **not** allocate. But `foreach` over
`IEnumerable<T>` (e.g. `Where`, `Select`) **does** allocate. The
pattern:

```csharp
// WRONG: allocates an enumerator object
foreach (var x in list.Where(p => p.IsActive)) { ... }

// RIGHT: use a for loop
for (int i = 0; i < list.Count; i++)
{
    if (list[i].IsActive) { ... }
}
```

---

## 7. The Memory Profiler checklist for a senior review

For every system in the game:

- [ ] The system has a `ProfilerMarker` for `Update`.
- [ ] `Update` does no `new` of any reference type.
- [ ] `Update` does no string concatenation in non-debug builds.
- [ ] `Update` does no `GetComponent`, `Find`, or `FindObjectOfType`.
- [ ] All `NativeArray<T>` / `NativeList<T>` / `NativeHashMap<T>` are
      `Dispose`d in `OnDestroy`.
- [ ] The system has a "stress" test that runs 10× its expected
      load. Run it. Diff. Repeat.

---

## 8. Practical session: the 10-minute memory audit

1. Open `UnitySeniorLab`. Add a cube, a script with `Update` that
   does `new Vector3[10]`, and run Play.
2. Open Memory Profiler.
3. Capture → wait 5 s → Capture.
4. Diff. Find the `Vector3[]` arrays.
5. Fix the code to use a pre-allocated array.
6. Re-run, re-diff. Verify the diff is clean.

This is the workflow. The numbers go down; the user-visible hitching
goes with them.

---

## 9. The "good enough" rule

**Don't optimize memory you don't have a budget for.** Profile your
target device, find the actual cost, fix that. Speculation in memory
is the same as speculation in CPU: it's wrong half the time.

The Memory Profiler exists to **end the speculation**.

---

## Summary

- Install the Memory Profiler package. Use it weekly.
- The Summary tab is your first read.
- The Memory Map is your second read. Top three textures, top three
  meshes.
- **The diff between two snapshots is the killer feature.** It shows
  leaks and churn directly.
- Per-frame allocations: `RaycastAll` → `RaycastNonAlloc`, `new
  WaitForSeconds` → cached, `foreach` over `IEnumerable<T>` → for
  loop.
- The senior checklist: marker, no `new`, no `Find` in `Update`,
  `Dispose`d natives, stress test.
- Profile your target device. Don't speculate.
