# Challenge 05 — Jobify a Real System

You have a MonoBehaviour system that does float-based animation on
1,000 game objects. It works, but it's slow on mobile (8 ms per
frame). Your job: jobify it and verify the speedup.

**Time**: 2 hours.

---

## The starting system

```csharp
using UnityEngine;

public class WaveMover : MonoBehaviour
{
    [SerializeField] Transform[] _items;
    [SerializeField] float _amplitude = 1f;
    [SerializeField] float _frequency = 1f;

    void Start()
    {
        if (_items == null || _items.Length == 0)
        {
            // Auto-populate: find all children
            _items = GetComponentsInChildren<Transform>();
        }
    }

    void Update()
    {
        float t = Time.time;
        for (int i = 0; i < _items.Length; i++)
        {
            var pos = _items[i].position;
            pos.y = Mathf.Sin(t * _frequency + i * 0.1f) * _amplitude;
            _items[i].position = pos;
        }
    }
}
```

**The cost**: 1,000 `transform.position` reads and writes per
frame. Each is a managed↔native interop call. On mobile, this is
~8 ms.

**The senior fix**: copy positions to a `NativeArray<float3>`,
run a Burst job, copy back.

## Requirements

1. Copy positions to a `NativeArray<float3>` once (in `Awake`
   or when the array changes).
2. Run a Burst-compiled `IJobParallelFor` every frame to compute
   the new positions.
3. Copy the result back to the transforms.
4. The transforms should move the same way.
5. Profile before and after. Confirm the speedup.

## Stretch

- Use `IJobFor` with `ScheduleParallel` instead of
  `IJobParallelFor`. Compare.
- Use `TransformAccessArray` + `ITransformJob` to write back
  directly, no copy.
- Bake the items into ECS entities and use `IJobEntity`. (Module
  6.)

## Verification

In the Profiler, time the `Update` block:

- **Before**: ~8 ms on mobile.
- **After**: ~0.3 ms (the job) + ~0.5 ms (the copy) = ~0.8 ms.

The "copy" itself is significant. The senior pattern: avoid it
entirely with `TransformAccessArray` or DOTS.

```csharp
// ITransformJob is the senior way to do this without a copy.
[BurstCompile]
public struct WaveTransformJob : ITransformParallelJob
{
    public NativeArray<float> Times;
    public float Frequency;
    public float Amplitude;

    public void Execute(int index, TransformAccess transform)
    {
        var pos = transform.position;
        pos.y = math.sin(Times[index] * Frequency + index * 0.1f) * Amplitude;
        transform.position = pos;
    }
}
```

Driver:

```csharp
TransformAccessArray _transforms;

void Start()
{
    _transforms = new TransformAccessArray(_items.Length);
    foreach (var t in _items) _transforms.Add(t);
}

void Update()
{
    var job = new WaveTransformJob { /* ... */ };
    job.ScheduleReadOnly(_transforms, 64);
}

void OnDestroy()
{
    if (_transforms.isCreated) _transforms.Dispose();
}
```

`ITransformParallelJob` writes back to the transforms inside
the job, no copy required. **This is the senior default for
transform-heavy updates.**

## What we're testing

- You can take a MonoBehaviour hot path and convert it to a job.
- You can verify the speedup in the Profiler.
- You can use `TransformAccessArray` to avoid managed↔native
  copies.
- You understand the trade-offs: simpler code (managed) vs
  faster code (job).

The senior dev who can't do this is the senior dev whose game
runs at 25 FPS on the target device.
