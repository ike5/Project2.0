# 04 — Native Containers, Jobs, and Burst

The Jobs system and Burst compiler are Unity's answer to the question
"how do I use 8 CPU cores without writing 8 versions of the same code?"
This module is the practical introduction; module 5 builds on it for
DOTS/ECS.

The payoff is real: a jobified + Burst-compiled loop is **5–20× faster
than the equivalent MonoBehaviour Update** on a typical mobile device.
The cost is that you learn a new mental model: **no managed objects on
worker threads, no shared state, no race conditions**.

---

## 1. The three primitives

| Primitive | What | When |
|-----------|------|------|
| **Native containers** (`NativeArray<T>`, `NativeList<T>`, etc.) | Stack-or-heap-allocated buffers outside the GC | Per-job scratch, persistent data |
| **Jobs** (`IJob`, `IJobParallelFor`, `IJobEntity`) | Units of work that run on worker threads | Hot loops you want parallelized |
| **Burst** | A compiler that turns IL into highly optimized native code | Anything in a hot path; jobs, math, ECS |

You can use jobs without Burst (you'll see this in tutorials). Don't.
Burst is what makes the system worthwhile.

---

## 2. Why jobs exist: the main thread bottleneck

The main thread does:

- Script `Update`/`FixedUpdate`/`LateUpdate` calls.
- GameObject lifecycle (Awake, OnEnable, OnDisable, OnDestroy).
- Physics queries.
- Animation updates.
- Drawing command generation.

A 60 FPS target is **16.67 ms total per frame**. If your 5,000 enemies'
`Update` takes 12 ms, you have 4.67 ms left for **everything else**,
and your draw calls won't fit.

A job lets you say "run this 5,000-iteration loop on 4 worker threads,
each handling 1,250 enemies", and the main thread gets back its 9 ms.

---

## 3. `NativeArray<T>` — the foundation

```csharp
using Unity.Collections;

NativeArray<float> _data = new NativeArray<float>(
    length: 1000,
    allocator: Allocator.Persistent);

// Use it like a managed array
_data[0] = 3.14f;
float x = _data[0];

// Iteration is allocation-free
for (int i = 0; i < _data.Length; i++)
{
    _data[i] *= 2f;
}

// ALWAYS dispose
_data.Dispose();
```

**Lifetime rules**:

- `Allocator.Persistent`: lives until you `Dispose()`. Long-lived.
- `Allocator.TempJob`: lives ~4 frames, auto-freed after that. **Use
  this for jobs.** Cheaper than Persistent.
- `Allocator.Temp`: lives 1 frame, can't be passed to a job. For
  in-method scratch.

**AsSpan() for stack access**:

```csharp
Span<float> view = _data.AsSpan();
view.Sort();   // no allocation
```

---

## 4. The `IJob`: a single unit of work

```csharp
using Unity.Burst;
using Unity.Collections;
using Unity.Jobs;
using Unity.Mathematics;

[BurstCompile]
struct DoubleAllJob : IJob
{
    public NativeArray<float> Values;

    public void Execute()
    {
        for (int i = 0; i < Values.Length; i++)
        {
            Values[i] *= 2f;
        }
    }
}

public class JobSystemExample : MonoBehaviour
{
    NativeArray<float> _values;
    JobHandle _handle;

    void Start()
    {
        _values = new NativeArray<float>(10000, Allocator.Persistent);
        for (int i = 0; i < _values.Length; i++) _values[i] = i;
    }

    void Update()
    {
        var job = new DoubleAllJob { Values = _values };
        _handle = job.Schedule();
        _handle.Complete();  // wait for the job; usually you wait in LateUpdate
    }

    void OnDestroy()
    {
        _handle.Complete();
        if (_values.IsCreated) _values.Dispose();
    }
}
```

**Notes**:

- The job is a `struct`, not a class. Zero allocation.
- `[BurstCompile]` is what makes it fast. With it, this loop is
  ~10× faster than the equivalent MonoBehaviour `Update`.
- `_handle.Complete()` blocks the main thread. Better practice:
  schedule the job in `Update`, complete in `LateUpdate`, so the
  work overlaps with rendering.

---

## 5. `IJobParallelFor`: parallel over an index range

```csharp
[BurstCompile]
struct ScaleJob : IJobParallelFor
{
    public NativeArray<float3> Positions;
    public float Delta;
    public float Speed;

    public void Execute(int index)
    {
        Positions[index] += new float3(0f, math.sin(Delta + index * 0.1f) * Speed, 0f);
    }
}

public class ParallelExample : MonoBehaviour
{
    [SerializeField] int _count = 10000;
    NativeArray<float3> _positions;
    JobHandle _handle;

    void Start()
    {
        _positions = new NativeArray<float3>(_count, Allocator.Persistent);
    }

    void Update()
    {
        var job = new ScaleJob
        {
            Positions = _positions,
            Delta = Time.time,
            Speed = 0.01f
        };
        _handle = job.Schedule(_positions.Length, 64); // batch of 64
    }

    void LateUpdate()
    {
        _handle.Complete();
    }

    void OnDestroy()
    {
        _handle.Complete();
        if (_positions.IsCreated) _positions.Dispose();
    }
}
```

**Batch size** (the second argument to `Schedule`) matters:

- Too small (1): per-batch overhead dominates.
- Too large (10,000): you lose parallelism — one core gets all the work.
- Senior default: **32–128** for typical math jobs.

The job system auto-balances across cores.

---

## 6. Safety system: the friend that yells at you

The job system has a **safety system** that checks for:

- Two jobs writing to the same `NativeArray` simultaneously.
- A job writing to a `NativeArray` while the main thread reads it.
- A job being scheduled that uses a `NativeArray` already disposed.

When you see a job-safety error in the console, **read it**. The
error is precise: it tells you which job, which container, and which
thread. Don't disable the safety system to "make it work" — that
turns the safety system into a "ship a crash to QA" system.

To **temporarily** allow a specific unsafe pattern, use
`[NativeDisableContainerSafetyRestriction]` — but only on fields you
control, and only after a careful read.

---

## 7. Burst: what it does, and what it doesn't

Burst is a **compiler** that:

- Translates IL to **LLVM IR**, then to **native code** (x64, ARM64,
  WASM, etc.).
- Auto-vectorizes SIMD ops (SSE, AVX, NEON).
- Aggressively inlines and unrolls.
- **Strips** managed allocations (the Burst code path cannot allocate).

What Burst **does not** do:

- Run C# dynamic features (no `dynamic`, no reflection in compiled
  code).
- Allow managed object access (no `List<T>`, no `string`).
- Replace all of Unity's APIs. It only Burst-compiles the parts of
  your code (and Unity's APIs marked `[BurstCompatible]`).

The result on a 5,000-entity simulation is **5–20× speedup** on
mobile, often more on the high-end. CPU goes from "I can't ship this"
to "I have budget left over".

### Burst-compatible types

- All blittable value types: `int`, `float`, `Vector3`, `Quaternion`,
  `float3`, `int3`, `bool`, enums, your own `struct`s if all their
  fields are blittable.
- All Unity.Collections native containers: `NativeArray<T>`,
  `NativeList<T>`, `NativeHashMap<K,V>`, etc.
- **`string`**: NO. Strings are managed.
- **`T[]` (managed array)**: NO. Use `NativeArray<T>`.
- **Reference types (`class`)**: NO. They live on the GC heap.

**The `Unity.Mathematics` types are 1:1 with shader/HLSL types** and
are the senior default for any math in jobs.

---

## 8. The senior dependency: `IJobFor` and `IJobEntity`

For ECS (module 5), `IJobEntity` is the right primitive. For raw job
work, `IJobFor` (Unity 2022.2+) is a modern, simpler parallel-for
without the batch-size indirection:

```csharp
[BurstCompile]
struct MoveJob : IJobFor
{
    [ReadOnly] public NativeArray<float3> Targets;
    public NativeArray<float3> Positions;
    public float DeltaTime;

    public void Execute(int index)
    {
        Positions[index] = math.lerp(Positions[index], Targets[index], DeltaTime);
    }
}
```

`IJobFor` is preferred when you don't need the `int` index in the
inner loop (you can pass it through the iteration variable instead).

---

## 9. Common pitfalls

### 9.1 Calling `Schedule` from a job

`IJob.Schedule()` must be called from the main thread. It **can** be
called from another job, but only with the `Schedule` overload that
takes a `JobHandle` dependency. Get this wrong and the editor will
freeze or assert.

### 9.2 Forgetting `Complete()`

If you don't `Complete()` a `JobHandle` before the next time you
schedule a job that uses the same `NativeArray`, the safety system
will yell at you. If you don't `Complete()` before disposing the
container, the safety system will yell harder.

### 9.3 Leaking `NativeArray`

The leak detector only fires for `Allocator.Persistent` and only on
exit. `Allocator.TempJob` leaks don't show in the leak detector.
**Use `Allocator.Persistent` for any long-lived data** so the leak
detector can find your mistake.

### 9.4 Reading `Time.time` inside a job

`Time.time` is a managed property and not Burst-compatible. Pass it
in as a `float`:

```csharp
[BurstCompile]
struct Job : IJob
{
    public float Time;
    public void Execute() { /* use Time */ }
}

// Caller
new Job { Time = Time.time }.Schedule();
```

Same for `Time.deltaTime`, `Random.value`, etc. Pass them in.

### 9.5 Trying to log from a job

`Debug.Log` is not Burst-compatible. Either guard it with
`#if UNITY_EDITOR`, or use `Unity.Logging` (Unity 6+).

---

## 10. The profiler view

When you run a job, the Profiler (Window → Analysis → Profiler)
shows it under **CPU Usage → Job → Worker N > YourJob**. The row
will say **"AOT (Burst)"** in green if Burst is active, or **"IL"**
in red if it's running as managed IL. The IL version is much slower
and probably means your `[BurstCompile]` attribute is missing or
Burst failed to compile (check the Burst inspector in Window →
Jobs → Burst).

---

## Summary

- `NativeArray<T>` is your foundation; dispose it.
- `IJob` is single, `IJobParallelFor`/`IJobFor` is parallel.
- `[BurstCompile]` is mandatory for hot code.
- The job safety system is your friend; read its errors.
- Burst doesn't allow `string`, `T[]`, or `class`. Use `float3`,
  `NativeArray<T>`, struct.
- Pass `Time.time` and other main-thread state into the job as
  primitives.
- Profile with the Burst inspector and the Profiler; verify the
  job is "AOT (Burst)".
