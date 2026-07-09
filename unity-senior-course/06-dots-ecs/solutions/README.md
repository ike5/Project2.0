# Solutions 06 — 50,000 Entities

---

## Components

```csharp
using Unity.Entities;
using Unity.Mathematics;

namespace MyGame.ECS
{
    public struct Velocity : IComponentData
    {
        public float3 Linear;
    }

    public struct HealthData : IComponentData
    {
        public int Current;
        public int Max;
    }

    public struct RenderMeshArrayIndex : IComponentData
    {
        public int Value;
    }
}
```

## Authoring

```csharp
using Unity.Entities;
using UnityEngine;

namespace MyGame.ECS.Authoring
{
    public class EnemyAuthoring : MonoBehaviour
    {
        [SerializeField] int maxHealth = 100;

        class Baker : Baker<EnemyAuthoring>
        {
            public override void Bake(EnemyAuthoring a)
            {
                var e = GetEntity(TransformUsageFlags.Dynamic);
                AddComponent(e, new HealthData
                {
                    Max = a.maxHealth,
                    Current = a.maxHealth
                });
                AddComponent(e, new Velocity { Linear = float3.zero });
            }
        }
    }
}
```

## Spawner

```csharp
public struct Spawner : IComponentData
{
    public int Count;
    public float3 Origin;
    public float Spread;
}

public partial struct SpawnerSystem : ISystem
{
    public void OnCreate(ref SystemState state)
    {
        state.RequireForUpdate<Spawner>();
    }

    public void OnUpdate(ref SystemState state)
    {
        var spawner = SystemAPI.GetSingleton<Spawner>();
        var em = state.EntityManager;

        var archetype = em.CreateArchetype(
            typeof(LocalTransform),
            typeof(Velocity),
            typeof(HealthData),
            typeof(RenderMeshArrayIndex));

        using var entities = em.CreateEntity(archetype, spawner.Count, Allocator.Temp);
        for (int i = 0; i < spawner.Count; i++)
        {
            var e = entities[i];
            em.SetComponentData(e, LocalTransform.FromPosition(
                spawner.Origin +
                new float3(
                    (i % 256) * spawner.Spread,
                    0,
                    (i / 256) * spawner.Spread)));
            em.SetComponentData(e, new Velocity
            {
                Linear = new float3(
                    math.sin(i * 0.01f),
                    0,
                    math.cos(i * 0.01f)) * 0.5f
            });
            em.SetComponentData(e, new HealthData
            {
                Max = 100,
                Current = 100
            });
            em.SetComponentData(e, new RenderMeshArrayIndex
            {
                Value = i % 4
            });
        }

        // Done spawning
        em.DestroyEntity(SystemAPI.GetSingletonEntity<Spawner>());
    }
}
```

`em.CreateEntity(archetype, count, allocator)` is a **batch
allocation** that creates `count` entities at once. Massively
faster than `CreateEntity()` in a loop.

## Movement system

```csharp
[BurstCompile]
public partial struct MovementSystem : ISystem
{
    [BurstCompile]
    public void OnUpdate(ref SystemState state)
    {
        new MoveJob
        {
            DeltaTime = SystemAPI.Time.DeltaTime
        }.ScheduleParallel();
    }
}

[BurstCompile]
public partial struct MoveJob : IJobEntity
{
    public float DeltaTime;

    public void Execute(ref LocalTransform transform, in Velocity velocity)
    {
        transform.Position += velocity.Linear * DeltaTime;
    }
}
```

## Cull system (IEnableableComponent pattern)

```csharp
public struct Dead : IComponentData, IEnableableComponent {}

[BurstCompile]
public partial struct CullSystem : ISystem
{
    [BurstCompile]
    public void OnUpdate(ref SystemState state)
    {
        new MarkDeadJob().ScheduleParallel();
        state.EntityManager.DestroyEntity(
            state.GetEntityQuery(typeof(Dead)));
    }
}

[BurstCompile]
public partial struct MarkDeadJob : IJobEntity
{
    public void Execute(ref HealthData health, EnabledRefRW<Dead> dead)
    {
        if (health.Current <= 0) dead.ValueRW = true;
    }
}
```

`EnabledRefRW<T>` lets you toggle an `IEnableableComponent` from
a job. The `Dead` tag stays on the entity, but is "disabled";
the chunk layout doesn't change.

## Profiler verification

Open the Profiler. The expected output:

```
CPU Usage:
  Systems:
    SimulationSystemGroup:
      SpawnerSystem (only on first frame)
      MovementSystem
        Worker N: MoveJob (AOT Burst, 0.4 ms)
      CullSystem
        Worker N: MarkDeadJob (AOT Burst, 0.1 ms)

Memory:
  Native > EntityManager:
    50,000 entities
    4 chunks per archetype component
    ~4 MB total
```

## Performance notes

On a desktop CPU (Ryzen 5 or M1):

- 50,000 entities with `MoveJob` + Burst: **0.4-0.8 ms**.
- Same job without Burst: **5-10 ms**.
- Same logic in MonoBehaviour: **40+ ms** (would not hit 60
  FPS).

The senior rule: **DOTS is the right answer at 10,000+
identical simple things**. Below that, MonoBehaviour with jobs
is fine.

## Common pitfalls

- **Forgetting `[BurstCompile]` on `ISystem.OnUpdate`**. The
  attribute on the struct alone is not enough.
- **Using `Entity` references in hot components**. Store the
  data you need, not a pointer to it.
- **Allocating managed types in jobs**. The Burst compiler
  rejects this; if you see "managed allocation", you're doing
  something wrong.
- **Forgetting `state.Dependency` chaining**. If two systems
  write to the same component, set the second's dependency to
  the first's handle, or use `[UpdateAfter]`.
- **Not using `EntityCommandBuffer.ParallelWriter` for
  structural changes in jobs**. Direct `EntityManager` calls
  from a job are slow and unsafe; the ECB is the senior
  pattern.
