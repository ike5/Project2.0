# 02 — Memory Model: Managed, Native, Unsafe, GC

Every Unity performance problem you'll diagnose is, in the end, a memory
problem. The GC paused, the texture pool ran out, the native array leaked,
the asset is loaded twice. This module is the mental model you need to
reason about all of those.

If you take one thing from this course: **the managed heap is the most
expensive memory in your game**, and most of your job is keeping it cold.

---

## 1. Three memory regions

A running Unity player has at least three distinct memory regions. They
behave differently and the rules are not symmetric.

```
┌─────────────────────────────────────────────────────────┐
│ 1. Managed Heap                                         │
│    Where C# `class` instances live. Garbage-collected.  │
│    Allocations are slow, GC pauses are catastrophic.    │
├─────────────────────────────────────────────────────────┤
│ 2. Native Heap (Unmanaged)                              │
│    Unity's own allocations: textures, meshes, audio,    │
│    jobs, native collections, IL2CPP runtime.            │
│    Allocated/freed manually. No GC. You must dispose.    │
├─────────────────────────────────────────────────────────┤
│ 3. Stack                                                 │
│    Per-thread, ~1 MB default. Allocation is free.       │
│    Span<T>, ref struct, value-type locals, parameters.  │
└─────────────────────────────────────────────────────────┘
```

There are also GPU-visible resources (textures in VRAM, vertex buffers),
which are a fourth region. We cover those in module 6.

---

## 2. The managed heap: how Mono/IL2CPP GC works

Unity's managed runtime is **Mono** (or **IL2CPP** + Boehm). It uses a
**non-generational, non-compacting, stop-the-world** GC. This is the
single most important fact about Unity performance.

What that means:

- **Stop-the-world**: when the GC runs, the main thread (and any thread
  doing managed allocation) pauses. On mobile: a 5–20 ms pause looks
  like a frame stutter.
- **Non-generational**: every collection inspects **all** live objects,
  not just the recent ones. So a 10 MB managed heap with 1 MB of churn
  is more expensive than a 2 MB heap with 1 MB of churn, in
  collection time.
- **Non-compacting**: the GC never moves objects, so the heap
  fragments. Long-running sessions slowly accumulate holes.

### Generations (Mono)

Mono's GC has generations 0, 1, 2. **Gen 0** is the cheapest, and
survivors are promoted. Most per-frame churn dies in Gen 0 (cheap).
The expensive collection is **Gen 2**, which is the whole heap.

```
Allocation → Gen 0 → survives → Gen 1 → survives → Gen 2 → expensive!
```

So a single per-frame `new SomeClass()` that survives one collection
is cheap. A `new SomeClass()` that holds a long-lived reference
becomes a Gen-2 resident — and Gen 2 collections are what you feel
on mobile.

### What allocates?

**Every** of these allocates from the managed heap:

1. `new` for any reference type (class).
2. **Boxing** of a value type (e.g. `object x = 5;` or passing a
   value type to a method that takes `object`).
3. **Array creation**: `new T[N]`.
4. **String concatenation**: `$"x={x}"` allocates the resulting string.
5. **Closures capturing variables**: `() => x + 1` allocates a closure
   class.
6. **Iterators**: `yield return` builds a state machine class.
7. **Params arrays**: `void Foo(params int[] xs)` allocates the
   array. Prefer `ReadOnlySpan<int>`.
8. **LINQ**: `IEnumerable<T>` operations allocate; rarely used in
   hot paths for a reason.
9. **Reflection**: `Type.GetType`, `MethodInfo.Invoke` allocate.

**The single biggest source of "GC hitches" in shipped games is
#1 and #2**, plus #4 in UI code.

---

## 3. Stack vs heap — what lives where

| Type | Lives in | Allocated by | Lifetime |
|------|----------|--------------|----------|
| `int`, `float`, `bool` | Stack (when local) | Compiler emits `mov` | Method scope |
| `Vector3`, `Quaternion` | Stack (when local) | Compiler emits `mov` | Method scope |
| `record struct` (most cases) | Stack (when local) | Compiler emits `mov` | Method scope |
| `class` (any) | Managed heap | GC | Until unreachable |
| `string` | Managed heap | GC | Until unreachable |
| `T[]` (managed array) | Managed heap | GC | Until unreachable |
| `NativeArray<T>` | Native heap | You (or `[DeallocateOnJobCompletion]`) | Until you `Dispose()` |
| `Span<T>` | **Stack only** | Compiler | Method scope |
| `unsafe` pointers | Whatever you point at | `stackalloc` or `Marshal.AllocHGlobal` | Method scope or manual |

**The whole point of `Span<T>` is to keep work on the stack.**

---

## 4. Boxing: the silent GC killer

Boxing happens when a value type is treated as a reference type:

```csharp
int x = 5;
object o = x;                          // ← box
string s = "value: " + x;              // ← box (string.Concat(object, object))
ArrayList list = new(); list.Add(x);  // ← box (ArrayList stores object)
IComparable<int> c = x;                // ← box (interface)
Console.WriteLine(x);                  // ← box
```

Each box is a **24+ byte managed allocation** plus a Gen-0 collection
candidate. In a tight loop, boxing 1000 times per frame is a real hitch.

**Avoid**:

```csharp
// WRONG
public string Describe(object o) => o.ToString();

// RIGHT
public string Describe<T>(T o) => o?.ToString();
```

In Unity, **the worst offenders** are:

- `String.Format`, `string.Concat` with mixed types → box.
- `Dictionary<K, V>` keys used in `Equals` chains that hit `object`.
- `enum` used in `IDictionary`, `Hashtable`, `ArrayList`.
- Logging frameworks that format with `params object[]`.

**The fix**: prefer `StringBuilder`, `Span<char>`, `ZString` (a
zero-alloc string package), or `Debug.Log` with explicit types.

---

## 5. The native heap: where Unity does its real work

Most of the **bytes** in a running game are in the native heap, not the
managed heap. A typical mobile game's breakdown:

```
Textures             ~40%
Meshes               ~10%
Audio                ~10%
Shader variants      ~5%
Managed code (IL2CPP) ~5%
Managed heap         ~5%
Everything else      ~25%
```

The native heap is:

- **Not garbage-collected.** Allocations return `IntPtr`s; you free
  them or they leak.
- **Allocated via `Unity.Collections.LowLevel.Unsafe.UnsafeUtility`**,
  `NativeArray<T>`, `Mesh.GetNativeIndexBufferPtr`, `Texture2D.GetNativeTexturePtr`.
- **Subject to platform-specific fragmentation**. iOS has a tighter
  budget than PC. WebGL has the tightest.

### Native container lifetime (CRITICAL)

```csharp
using Unity.Collections;

public class MySystem : MonoBehaviour
{
    NativeArray<float> _data;

    void Start()
    {
        _data = new NativeArray<float>(1000, Allocator.Persistent);
    }

    void OnDestroy()
    {
        if (_data.IsCreated) _data.Dispose();   // ← MUST DO THIS
    }
}
```

**The leak is the bug.** Forgetting `Dispose()` on a `NativeArray` (or
a `NativeList`, `NativeHashMap`) is the most common native bug in
Unity. The leak detector (`Allocator.Persistent` only) tells you about
it on exit; the leak is real.

### The four `Allocator` kinds

| Allocator | Lifetime | When to use |
|-----------|----------|-------------|
| `Invalid` | n/a | never |
| `None`    | n/a | only for views (don't allocate) |
| `Temp`    | **1 frame max** | per-frame jobs, scratch space |
| `TempJob` | **4 frames max** | job scratch space; auto-freed if job completes |
| `Persistent` | Until you `Dispose()` | long-lived data |

`Temp` and `TempJob` are the senior default for transient data.

---

## 6. The `unsafe` escape hatch

Sometimes you need to talk to native memory directly. Unity supports
`unsafe` C# code.

```csharp
unsafe void ZeroBuffer(byte* ptr, int length)
{
    for (int i = 0; i < length; i++) ptr[i] = 0;
}
```

To enable:

1. **Edit → Project Settings → Player → Other Settings →
   Allow 'unsafe' Code** ☑.

`unsafe` is the right tool when:

- You need to **interop with native plugins** (DLLs that expose C
  APIs).
- You need to **build a `Span<T>` over native memory** for fast
  iteration.
- You're writing a **custom allocator**.

It is **not** the right tool for "make my game faster". Profile first
(module 11).

---

## 7. A worked example: the same code, three ways

```csharp
// Naive: lots of allocations, GC pressure
public class Naive
{
    public List<Vector3> Positions { get; } = new();

    public Vector3 GetCenter()
    {
        float sumX = 0, sumY = 0, sumZ = 0;
        foreach (var p in Positions)   // List<T>.Enumerator is a struct, no alloc
        {
            sumX += p.x;               // Vector3 is a struct, no alloc
            sumY += p.y;
            sumZ += p.z;
        }
        int n = Positions.Count;        // n=0 edge case not handled
        return new Vector3(sumX / n, sumY / n, sumZ / n);
    }
}

// Senior: still allocates the List, but the operation is clean
public class Senior
{
    readonly List<Vector3> _positions = new(64);   // pre-sized capacity

    public void AddPosition(Vector3 p) => _positions.Add(p);

    public Vector3 GetCenter()
    {
        if (_positions.Count == 0) return Vector3.zero;

        var span = CollectionsMarshal.AsSpan(_positions);  // Span over the list
        double sumX = 0, sumY = 0, sumZ = 0;
        foreach (ref readonly var p in span)               // no enumerator
        {
            sumX += p.x;
            sumY += p.y;
            sumZ += p.z;
        }
        int n = _positions.Count;
        return new Vector3((float)(sumX / n), (float)(sumY / n), (float)(sumZ / n));
    }
}

// Hardcore: NativeArray, no GC ever
public class Hardcore
{
    NativeArray<Vector3> _positions;
    int _count;

    public Hardcore(int capacity)
    {
        _positions = new NativeArray<Vector3>(capacity, Allocator.Persistent);
    }

    public void AddPosition(Vector3 p)
    {
        if (_count == _positions.Length) Grow();
        _positions[_count++] = p;
    }

    void Grow()
    {
        var bigger = new NativeArray<Vector3>(_positions.Length * 2, Allocator.Persistent);
        NativeArray<Vector3>.Copy(_positions, bigger, _count);
        _positions.Dispose();
        _positions = bigger;
    }

    public Vector3 GetCenter()
    {
        if (_count == 0) return Vector3.zero;
        double sx = 0, sy = 0, sz = 0;
        for (int i = 0; i < _count; i++)
        {
            var p = _positions[i];
            sx += p.x; sy += p.y; sz += p.z;
        }
        int n = _count;
        return new Vector3((float)(sx / n), (float)(sy / n), (float)(sz / n));
    }

    public void Dispose() { if (_positions.IsCreated) _positions.Dispose(); }
}
```

When to use which:

- **Naive**: tools, debug code, one-off scripts.
- **Senior**: gameplay code with light hot paths.
- **Hardcore**: simulation code (10,000+ entities per frame), tight
  loops, anything DOTS-adjacent.

---

## 8. The four numbers you should always know

For any Unity game in production, the senior lead should be able to
answer these in under a minute:

1. **Total resident set size (RSS)** on the lowest-spec target device.
2. **Managed heap size** in steady state (after 10 minutes of play).
3. **GC.Alloc per frame** at peak gameplay.
4. **Texture pool size** in steady state.

If you don't know these, you're flying blind.

---

## 9. The single most useful `using` you'll add this year

```csharp
using Unity.Profiling;
```

The `Profiler` API is the standard way to instrument your code. The
memory profiler (next module) uses these markers to attribute cost.

```csharp
using Unity.Profiling;

static readonly ProfilerMarker s_MyMarker = new("MySystem.Update");

void Update()
{
    using (s_MyMarker.Auto())
    {
        // ... work ...
    }
}
```

These markers show up in the Profiler timeline and let you attribute
milliseconds to your code, not just to Unity subsystems.

---

## Summary

- Three memory regions: managed, native, stack. Different rules.
- Mono's GC is stop-the-world, non-compacting, non-generational. It
  hitches on mobile.
- Boxing is the silent GC killer. Avoid `object`-typed parameters in
  hot paths.
- Native allocations need manual `Dispose()`. The leak is the bug.
- Stack allocation is free. `Span<T>` keeps work on the stack.
- `unsafe` is for interop and custom allocators, not "making code
  faster".
- Know your four numbers: RSS, managed heap, alloc/frame, texture pool.
