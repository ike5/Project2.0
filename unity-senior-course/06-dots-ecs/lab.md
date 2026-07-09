# Lab 06 — DOTS in 90 Minutes

A hands-on introduction to Entities, components, systems, and baking.
By the end you will have a 10,000-entity wave simulation running
with ECS, jobs, and Burst.

**Time**: 90 minutes.

**Prerequisite**: `Entities` package installed (module 5 setup).

---

## Step 1 — The components

Create `Assets/Scripts/ECS/Components.cs`:

```csharp
using Unity.Entities;
using Unity.Mathematics;

namespace MyGame.ECS
{
    public struct WaveData : IComponentData
    {
        public float Amplitude;
        public float Frequency;
        public float3 Origin;
    }

    public struct WaveSpeed : IComponentData
    {
        public float Value;
    }
}
```

## Step 2 — The authoring component

Create `Assets/Scripts/ECS/Authoring/WaveAuthoring.cs`:

```csharp
using Unity.Entities;
using UnityEngine;

namespace MyGame.ECS.Authoring
{
    public class WaveAuthoring : MonoBehaviour
    {
        [SerializeField] float amplitude = 1f;
        [SerializeField] float frequency = 1f;
        [SerializeField] float speed = 1f;

        class Baker : Baker<WaveAuthoring>
        {
            public override void Bake(WaveAuthoring a)
            {
                var entity = GetEntity(TransformUsageFlags.Dynamic);
                AddComponent(entity, new WaveData
                {
                    Amplitude = a.amplitude,
                    Frequency = a.frequency,
                    Origin = a.transform.position
                });
                AddComponent(entity, new WaveSpeed { Value = a.speed });
            }
        }
    }
}
```

## Step 3 — The system

Create `Assets/Scripts/ECS/Systems/WaveSystem.cs`:

```csharp
using Unity.Burst;
using Unity.Entities;
using Unity.Mathematics;
using Unity.Transforms;

namespace MyGame.ECS
{
    [BurstCompile]
    [UpdateInGroup(typeof(SimulationSystemGroup))]
    public partial struct WaveSystem : ISystem
    {
        [BurstCompile]
        public void OnCreate(ref SystemState state)
        {
            state.RequireForUpdate<WaveData>();
        }

        [BurstCompile]
        public void OnUpdate(ref SystemState state)
        {
            float t = (float)SystemAPI.Time.ElapsedTime;

            foreach (var (transform, data, speed) in
                     SystemAPI.Query<RefRW<LocalTransform>,
                                     RefRO<WaveData>,
                                     RefRO<WaveSpeed>>())
            {
                var pos = transform.ValueRO.Position;
                pos.y = data.ValueRO.Origin.y +
                        math.sin(t * data.ValueRO.Frequency +
                                 pos.x * 0.1f) * data.ValueRO.Amplitude;
                pos.z += speed.ValueRO.Value * SystemAPI.Time.DeltaTime;
                transform.ValueRW.Position = pos;
            }
        }
    }
}
```

## Step 4 — Spawn 10,000 entities at startup

Create `Assets/Scripts/ECS/Systems/SpawnerSystem.cs`:

```csharp
using Unity.Burst;
using Unity.Collections;
using Unity.Entities;
using Unity.Mathematics;
using Unity.Transforms;

namespace MyGame.ECS
{
    [BurstCompile]
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

            for (int i = 0; i < spawner.Count; i++)
            {
                var e = em.CreateEntity();
                em.AddComponentData(e, LocalTransform.FromPosition(
                    new float3(
                        (i % 100) * 0.5f,
                        0,
                        (i / 100) * 0.5f)));
                em.AddComponentData(e, new WaveData
                {
                    Amplitude = 1f,
                    Frequency = 1f + (i % 10) * 0.1f,
                    Origin = float3.zero
                });
                em.AddComponentData(e, new WaveSpeed { Value = 0.5f });
                em.AddComponentData(e, new RenderMeshArrayIndex { Value = i % 4 });
            }

            // Disable the spawner so we don't spawn again
            em.RemoveComponent<Spawner>(state.SystemHandle);
        }
    }

    public struct Spawner : IComponentData
    {
        public int Count;
    }
}
```

## Step 5 — A subscene

In the editor:

1. **GameObject → New Sub Scene → Empty Scene**. Save as
   `WaveSubScene.unity` in `Assets/Scenes/`.
2. In the subscene, add a GameObject with a `WaveAuthoring`.
3. In the **Baker** output, you should see one entity being
   baked.
4. Add a "Spawner" entity in the scene with a
   `SpawnerAuthoring` MonoBehaviour.

```csharp
public class SpawnerAuthoring : MonoBehaviour
{
    [SerializeField] int count = 10000;
    class Baker : Baker<SpawnerAuthoring>
    {
        public override void Bake(SpawnerAuthoring a)
        {
            var e = GetEntity(TransformUsageFlags.None);
            AddComponent(e, new Spawner { Count = a.count });
        }
    }
}
```

5. Open the subscene. The **Entities Hierarchy** window
   (Window → Entities → Hierarchy) shows the entities.

## Step 6 — Render the entities

For 10,000 entities, use **Graphics.RenderMeshIndirect** (or
**Graphics.DrawMeshInstanced**). A simple approach: tag each
entity with a `RenderMeshArrayIndex` and have a system update
the matrix array per frame.

```csharp
public struct RenderMeshArrayIndex : IComponentData
{
    public int Value;
}
```

For an actual visual, use a hybrid: bake each entity with a
`MaterialMeshInfo` (a built-in Entities package concept) and
the URP will render them automatically with `EntitiesGraphics`.

```csharp
public class RenderAuthoring : MonoBehaviour
{
    [SerializeField] Mesh mesh;
    [SerializeField] Material material;
    class Baker : Baker<RenderAuthoring>
    {
        public override void Bake(RenderAuthoring a)
        {
            var e = GetEntity(TransformUsageFlags.Dynamic);
            AddComponent(e, new MaterialMeshInfo
            {
                Mesh = a.mesh,
                Material = a.material
            });
        }
    }
}
```

(Entities Graphics 1.x has a more elaborate setup. The senior
default is to use the **Hybrid Renderer** with the **URP
Entities** package.)

## Step 7 — Profile

1. Run Play. Open Profiler.
2. **CPU Usage → ECS Systems > SimulationSystemGroup > WaveSystem**.
   Look for the `AOT (Burst)` marker.
3. **Memory → Native → EntityManager**. 10,000 entities, ~80 bytes
   per entity, ~800 KB total.
4. **Time.deltaTime** is the budget. With 10,000 entities, the
   system should run in < 1 ms on a desktop CPU.

## Stretch goals

- Add a `LocalTransform` query for `RefRO<LocalTransform>` only
  to your system and use `ScheduleParallel`. Measure the
  improvement.
- Use `IJobEntity` instead of `SystemAPI.Query`. Compare the
  code.
- Add an `IEnableableComponent` for "frozen" entities that the
  system skips. Toggle it from a manager.
- Replace the simple sine with a 2D wave equation (multiple
  neighbors). Stress-test the system at 100,000 entities.

---

## What you should now understand

- ECS = Entity (id) + Component (data) + System (logic).
- Author with `MonoBehaviour` + `Baker`. Build entities at
  build time.
- `[BurstCompile]` on systems and jobs is mandatory.
- `SystemAPI.Query<RefRW<T>, RefRO<U>>` is the senior
  synchronous pattern.
- `IJobEntity` is the senior parallel pattern.
- Profiler shows ECS work under `Systems > SimulationSystemGroup`.
- Memory is ~80 bytes per entity for a simple shape.
