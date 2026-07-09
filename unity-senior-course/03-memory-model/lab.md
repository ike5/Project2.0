# Lab 03 — The Memory Model, in Code

A 90-minute lab to make the three memory regions concrete. You will
allocate in each region, observe the allocation, and confirm the
behavior matches the model from the module.

---

## Part A — Managed heap allocations

Create `Assets/Scripts/MemoryLab/ManagedAllocLab.cs`:

```csharp
using System;
using UnityEngine;
using Unity.Profiling;

namespace MyGame.MemoryLab
{
    public class ManagedAllocLab : MonoBehaviour
    {
        ProfilerRecorder _gcAllocRecorder;
        int _frameCount;

        void OnEnable()
        {
            _gcAllocRecorder = ProfilerRecorder.StartNew(
                ProfilerCategory.Memory, "GC.Alloc.Count");
        }

        void OnDisable() => _gcAllocRecorder.Dispose();

        void Update()
        {
            _frameCount++;

            // Intentionally allocate every frame
            var tempArray = new int[100];
            var tempList = new System.Collections.Generic.List<int>(50);
            var tempString = $"frame {_frameCount}";
            var boxed = (object)42;

            // (the temps die at end of scope but the GC saw them)
            long allocCount = _gcAllocRecorder.LastValue;
            if (_frameCount % 60 == 0)
            {
                Debug.Log($"Frame {_frameCount}: GC.Alloc.Count = {allocCount}");
            }
        }
    }
}
```

Attach to a GameObject. Run Play. Open Profiler (Window →
Analysis → Profiler) and switch to the **Memory** module. The
"GC.Alloc.Count" line will show tens of allocations per frame.

**Expected**: ~5+ allocations per frame from this script alone. Each
`new` is one.

## Part B — Boxing

Add:

```csharp
void BoxedMethod(object o) { /* ... */ }

void Update()
{
    int x = 42;
    BoxedMethod(x);                  // ← boxes `x` to pass as `object`
    string s = "value: " + x;        // ← box in string.Concat(object, object)
    System.Collections.ArrayList list = new();  // ← ALLOCATES ArrayList
    list.Add(x);                     // ← boxes
}
```

Each of these is an allocation. The `ArrayList` adds 4 per frame
(its internal array, plus a box per `Add`).

**Verify**: Profiler shows ~5 extra allocations per frame from this
method.

## Part C — Native heap

Create `Assets/Scripts/MemoryLab/NativeAllocLab.cs`:

```csharp
using Unity.Collections;
using UnityEngine;

namespace MyGame.MemoryLab
{
    public class NativeAllocLab : MonoBehaviour
    {
        NativeArray<int> _persistent;
        NativeArray<int> _tempJob;
        JobHandle _handle;

        void Start()
        {
            _persistent = new NativeArray<int>(1024, Allocator.Persistent);

            // Take an early snapshot
            UnityEngine.Profiling.Memory.Experimental.MemoryProfiler.TakeSnapshot(
                "/tmp/before.png",
                OnSnapshotComplete,
                null);
        }

        void OnSnapshotComplete(string path, bool success)
        {
            Debug.Log($"Snapshot: {path}, success: {success}");
        }

        void Update()
        {
            // Allocates a TempJob NativeArray every frame
            _tempJob = new NativeArray<int>(64, Allocator.TempJob);
            // ...do some work...
            _tempJob.Dispose();
        }

        void OnDestroy()
        {
            if (_persistent.IsCreated) _persistent.Dispose();
        }
    }
}
```

**Verify**: Memory Profiler → Snapshot. Look at **Native → Unity
Collections → NativeArray**. The persistent array survives; the
temp job array is gone (it was disposed).

**Add an intentional leak**: comment out the `OnDestroy` Dispose
and re-snapshot. The persistent array is reported as a leak at
exit.

## Part D — The stack

```csharp
using System;
using UnityEngine;

public class StackLab : MonoBehaviour
{
    void Update()
    {
        Span<int> stackOnly = stackalloc int[100];
        for (int i = 0; i < stackOnly.Length; i++) stackOnly[i] = i;
        // (the span dies with the method; no GC, no native alloc)
    }
}
```

This allocates **zero bytes** in the managed heap and **zero bytes**
in the native heap. The 400 bytes live on the stack for the
duration of the method.

**Verify**: Memory Profiler diff shows no change for this method.

## Part E — Boxing via interface

```csharp
using System;
using System.Collections.Generic;
using UnityEngine;

public class BoxingViaInterface : MonoBehaviour
{
    interface IDoSomething { int Do(); }
    struct Counter : IDoSomething
    {
        public int N;
        public int Do() => N;
    }

    readonly List<IDoSomething> _items = new();
    int _frameCount;

    void Start()
    {
        for (int i = 0; i < 1000; i++) _items.Add(new Counter { N = i });
        // ← every Add here BOXES the struct (List<T> is unboxed for
        // ref types, but the interface is implemented as a box).
    }

    void Update()
    {
        // Iterate; no allocation in iteration.
        int sum = 0;
        foreach (var item in _items) sum += item.Do();
    }
}
```

The `Start` shows 1000 boxes. The `Update` is clean.

**The senior fix**: make the list concrete.

```csharp
readonly List<Counter> _items = new();
```

Now `Add` is **zero-alloc**.

## What to look for in the Profiler

For each section above, you should see:

- **Part A**: 3-5 GC.Alloc per frame.
- **Part B**: 5+ extra GC.Alloc per frame.
- **Part C**: A NativeArray in the snapshot; a leak warning at
  exit if you comment out Dispose.
- **Part D**: Nothing. The stack doesn't appear in the Memory
  Profiler at all (by design).
- **Part E**: A spike of 1000 allocations on the first frame
  (from `Start`), then zero per frame after.

---

## Stretch goals

- Replace `new int[100]` in Part A with a pre-allocated field.
  Verify the Profiler shows 0 allocations.
- Replace `ArrayList` with `List<int>`. Verify the box
  disappears.
- Use `[BurstCompile]` on a job that takes the `NativeArray`
  from Part C and runs a tight loop. Confirm it's "AOT (Burst)"
  in the Jobs profiler.
