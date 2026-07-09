# Lab 05 — Native Containers, Jobs, Burst

A series of small experiments to make the jobs/Burst mental model
concrete.

**Time**: 90 minutes.

**Prerequisite**: `Entities` package installed (brings Burst, Jobs,
Collections, Mathematics transitively).

---

## Step 1 — Your first `IJob`

Create `Assets/Scripts/Jobs/SumJob.cs`:

```csharp
using Unity.Burst;
using Unity.Collections;
using Unity.Jobs;
using Unity.Mathematics;

[BurstCompile]
public struct SumJob : IJob
{
    [ReadOnly] public NativeArray<float> Values;
    public NativeArray<float> Result;  // one element

    public void Execute()
    {
        float sum = 0f;
        for (int i = 0; i < Values.Length; i++) sum += Values[i];
        Result[0] = sum;
    }
}
```

A driver `MonoBehaviour`:

```csharp
using Unity.Collections;
using Unity.Jobs;
using UnityEngine;

public class JobDriver : MonoBehaviour
{
    NativeArray<float> _values;
    NativeArray<float> _result;

    void Start()
    {
        const int n = 100_000;
        _values = new NativeArray<float>(n, Allocator.Persistent);
        _result = new NativeArray<float>(1, Allocator.Persistent);
        for (int i = 0; i < n; i++) _values[i] = i;
    }

    void Update()
    {
        var job = new SumJob { Values = _values, Result = _result };
        JobHandle handle = job.Schedule();
        handle.Complete();
        Debug.Log($"Sum = {_result[0]}");
    }

    void OnDestroy()
    {
        if (_values.IsCreated) _values.Dispose();
        if (_result.IsCreated) _result.Dispose();
    }
}
```

Run. Open **Window → Jobs → Burst → Inspector**. Confirm the job
is **AOT (Burst)**.

## Step 2 — `IJobParallelFor`

```csharp
[BurstCompile]
public struct ScaleJob : IJobParallelFor
{
    public NativeArray<float> Values;
    public float Factor;

    public void Execute(int index)
    {
        Values[index] *= Factor;
    }
}
```

In the driver:

```csharp
void Update()
{
    var job = new ScaleJob { Values = _values, Factor = 1.01f };
    JobHandle handle = job.Schedule(_values.Length, 64);
    handle.Complete();
}
```

Open the Profiler. **CPU Usage → Job → Worker N > ScaleJob**. You
should see work distributed across multiple worker threads.

## Step 3 — `Unity.Mathematics` types

```csharp
[BurstCompile]
public struct VectorOpJob : IJobParallelFor
{
    public NativeArray<float3> Positions;
    public float DeltaTime;
    public float Time;

    public void Execute(int index)
    {
        var p = Positions[index];
        p.y += math.sin(Time + index * 0.01f) * DeltaTime;
        Positions[index] = p;
    }
}
```

`float3` is 1:1 with `Vector3` but more Burst-friendly. The
Burst inspector will show the `math.sin` call vectorized.

## Step 4 — `IJobFor` (the modern parallel-for)

```csharp
[BurstCompile]
public struct AddJob : IJobFor
{
    [ReadOnly] public NativeArray<float> A;
    [ReadOnly] public NativeArray<float> B;
    public NativeArray<float> Result;

    public void Execute(int index)
    {
        Result[index] = A[index] + B[index];
    }
}
```

Driver:

```csharp
NativeArray<float> _a, _b, _result;

void Start()
{
    _a = new NativeArray<float>(1000, Allocator.Persistent);
    _b = new NativeArray<float>(1000, Allocator.Persistent);
    _result = new NativeArray<float>(1000, Allocator.Persistent);
    for (int i = 0; i < 1000; i++) { _a[i] = i; _b[i] = i * 2; }
}

void Update()
{
    new AddJob { A = _a, B = _b, Result = _result }
        .ScheduleParallel(_result.Length, 32);
}

void LateUpdate() { /* complete via Singleton */ }

void OnDestroy()
{
    if (_a.IsCreated) _a.Dispose();
    if (_b.IsCreated) _b.Dispose();
    if (_result.IsCreated) _result.Dispose();
}
```

`IJobFor` doesn't have a batch size argument at scheduling; you
can use `.ScheduleParallel(arrayLength, innerLoopBatchCount)`
or the `IJobForExtensions.ScheduleParallel` overload.

## Step 5 — `NativeList<T>` and `NativeHashMap<K,V>`

```csharp
[BurstCompile]
public struct HashMapJob : IJob
{
    public NativeHashMap<int, float> Map;

    public void Execute()
    {
        for (int i = 0; i < 1000; i++)
        {
            Map.TryAdd(i, math.sqrt(i));
        }
    }
}
```

Driver:

```csharp
NativeHashMap<int, float> _map;

void Start()
{
    _map = new NativeHashMap<int, float>(1000, Allocator.Persistent);
    new HashMapJob { Map = _map }.Schedule().Complete();
}

void OnDestroy()
{
    if (_map.IsCreated) _map.Dispose();
}
```

`NativeHashMap` is a Burst-friendly hash map. Use it in jobs
where you'd use `Dictionary<K,V>` in regular C#.

## Step 6 — The safety system

Add a deliberate violation:

```csharp
void Update()
{
    var job = new ScaleJob { Values = _values, Factor = 1.01f };
    JobHandle handle = job.Schedule(_values.Length, 64);
    // Don't complete; try to use the result from the main thread
    Debug.Log(_values[0]);  // ← safety system fires
}
```

You'll see:

```
InvalidOperationException: The previously scheduled job ...
writes to the NativeArray ...
You must call JobHandle.Complete() ...
```

Read the message, fix the code, move on. **The safety system is
your friend.**

## Step 7 — Profiling the job

In the Profiler, the job shows under **CPU Usage → Job → Worker
N > YourJob**. The **Compile time** column says:

- `AOT (Burst)` — good, Burst is active.
- `IL` — bad, Burst is not active. Check the attribute and
  the Burst inspector.

**Cycle through `JobHandle.Complete()` in `LateUpdate`** instead
of `Update`. The job overlaps with the main thread's other work.

```csharp
JobHandle _handle;

void Update()
{
    var job = new ScaleJob { Values = _values, Factor = 1.01f };
    _handle = job.Schedule(_values.Length, 64);
}

void LateUpdate()
{
    _handle.Complete();
}
```

## Step 8 — Performance comparison

Compare three implementations:

1. `MonoBehaviour.Update` with a for loop.
2. `IJob` with Burst.
3. `IJobParallelFor` with Burst.

Time each with `Stopwatch` or `ProfilerMarker`:

```csharp
using Unity.Profiling;
using System.Diagnostics;

static readonly ProfilerMarker s_Marker = new("MyLoop");

void TimeLoop()
{
    using (s_Marker.Auto())
    {
        for (int i = 0; i < _values.Length; i++) _values[i] *= 1.01f;
    }
}
```

On a desktop CPU, the job+parallel+Burst version should be **5-20×
faster** than the MonoBehaviour `Update`.

## Stretch goals

- Use `IJobEntity` (in DOTS, module 6) to do the same work over
  ECS entities.
- Use a `NativeStream` to pass per-entity data between two jobs
  in a single frame.
- Use `[ReadOnly]` on `NativeArray` fields that the job doesn't
  write to. The safety system will allow more parallelism.

---

## What you should now understand

- `IJob`, `IJobParallelFor`, `IJobFor` are the three core job
  types.
- `[BurstCompile]` is mandatory for hot code.
- The safety system catches mistakes early; read its errors.
- `Allocator.Persistent` for long-lived data; `TempJob` for
  per-frame.
- `Unity.Mathematics` types are Burst-friendly and
  shader-compatible.
- Profiler: **AOT (Burst)** is what you want to see.
