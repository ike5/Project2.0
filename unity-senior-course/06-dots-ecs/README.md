# 05 — DOTS / ECS in Practice

DOTS (Data-Oriented Technology Stack) is Unity's bet on the future of
game development. It is **not** a silver bullet, and it is **not** a
replacement for everything in your game. This module teaches you when to
use it, when not to, and how to use it correctly when you do.

The mental model is the hard part. Once you have it, the code is
strictly less of it than the MonoBehaviour equivalent.

---

## 1. Why DOTS exists

The MonoBehaviour model has a fundamental cost that no amount of
pooling or `Update` discipline fully fixes:

- **GameObjects are pointer-chased.** Reading a `transform.position`
  follows a pointer to the `Transform` component, then to the
  internal native data. Cache misses dominate at scale.
- **Iteration is indirection-heavy.** `foreach (var e in enemies)`
  walks a list of `MonoBehaviour` references, each with its own
  per-frame allocation pattern and vtable.
- **Parallelism is awkward.** Each `MonoBehaviour` runs on the main
  thread by default; you can write jobs, but you have to copy data
  into `NativeArray`s first.

DOTS/ECS inverts the model:

- **Data is contiguous.** A `Translation` component for 100,000
  entities is 100,000 `float3`s in a tight array, not 100,000
  pointers to 100,000 `Vector3` fields.
- **Logic is data-parallel.** A system iterates chunks of 16 KB at a
  time, Burst-vectorized, on N worker threads.
- **The hot loop is just data.** A `MoveSystem` reads positions, writes
  positions, and the only thing the engine does is dispatch that
  loop to a job.

The 10,000-enemy problem becomes the 1,000,000-particle problem becomes
the "let me just do 60 FPS in 8 ms" problem.

---

## 2. The Entities package — what you install

**Window → Package Manager → search "Entities" → Install.**

`Entities` brings:

- The EntityManager + World.
- ComponentData (struct IComponentData).
- SystemBase / ISystem.
- Baking (the path from authoring GameObjects to runtime entities).
- Hybrid components (use MonoBehaviour + ECS in the same scene).
- Netcode for Entities (module 8).

It transitively brings **Burst**, **Collections**, **Mathematics**,
**Jobs** — all of which you should already have from module 4.

---

## 3. The three concepts: Entity, Component, System

```
Entity:  an ID (an int). Nothing more.
Component:  data attached to an entity. A struct. No logic.
System:  code that runs over entities matching a query.
```

That's it. A "red car" is:

```csharp
public struct Car : IComponentData { public float Speed; }
public struct RedTag : IComponentData {}

entityManager.AddComponent<Car>(e);
entityManager.AddComponent<RedTag>(e);
```

The car has no methods. It has data. **A system** runs the logic:

```csharp
public partial struct DriveSystem : ISystem
{
    public void OnUpdate(ref SystemState state)
    {
        float dt = SystemAPI.Time.DeltaTime;
        foreach (var (car, transform) in
                 SystemAPI.Query<RefRW<Car>, RefRW<LocalTransform>>())
        {
            transform.ValueRW.Position +=
                new float3(0f, 0f, car.ValueRO.Speed * dt);
        }
    }
}
```

The query selects every entity that has both `Car` and
`LocalTransform`. The system runs on the main thread; for parallel,
see below.

---

## 4. Authoring vs baking: the GameObject-to-Entity bridge

You don't usually create entities in code; you **author** a scene
with MonoBehaviours and **bake** it into entities at build time. This
is the "hybrid" path that keeps the editor familiar.

```csharp
// Authoring side (in the Editor)
public class CarAuthoring : MonoBehaviour
{
    public float Speed = 5f;

    class Baker : Baker<CarAuthoring>
    {
        public override void Bake(CarAuthoring authoring)
        {
            var entity = GetEntity(TransformUsageFlags.Dynamic);
            AddComponent(entity, new Car { Speed = authoring.Speed });
        }
    }
}

// Runtime side
public struct Car : IComponentData { public float Speed; }
```

You drag `CarAuthoring` onto a cube in the scene. At build time (or in
the editor, on save), Unity generates the entity.

**Why this matters**:

- Designers can edit scenes the way they always have.
- You don't ship the authoring code; it's Editor-only.
- The baking pipeline is fully customizable; you can use
  `BlobAssetReference<T>` for large static data (terrain, nav meshes,
  dialogue trees).

---

## 5. The senior decision tree: when to use DOTS

```
Do you have 1000+ of the same "thing" updated every frame?
  → Yes, and the update is heavy: DOTS is the right answer.
  → No, and the update is heavy: pool + jobs, no DOTS.

Do you need to share 1000+ instances of a complex authoring tree?
  → No: DOTS, with a single authoring prefab.
  → Yes: stay MonoBehaviour.

Is your team new to ECS, with a deadline in <6 months?
  → Stay MonoBehaviour. The ECS learning curve is real.

Do you need a 10,000-unit RTS, a city sim, a particle system,
a tower-defense with thousands of enemies, a procedural world?
  → DOTS.
```

**DOTS is not "the future of all Unity code".** It's the right tool
for data-parallel, cache-friendly, large-N problems. For 50-enemy
RPG combat, MonoBehaviour + jobs is faster to develop and fast enough.

---

## 6. The senior implementation pattern: jobs in systems

```csharp
public partial struct DriveSystem : ISystem
{
    [BurstCompile]
    public void OnUpdate(ref SystemState state)
    {
        float dt = SystemAPI.Time.DeltaTime;
        new MoveJob { DeltaTime = dt }.ScheduleParallel();
    }
}

[BurstCompile]
public partial struct MoveJob : IJobEntity
{
    public float DeltaTime;

    public void Execute(ref LocalTransform transform, in Car car)
    {
        transform.Position += new float3(0f, 0f, car.Speed * DeltaTime);
    }
}
```

`IJobEntity` is the senior way:

- Auto-generates the query from the `Execute` signature.
- `ref` for read-write components, `in` for read-only.
- `ScheduleParallel` runs across all worker threads.

**No `foreach` boilerplate. No native array plumbing.** That's why
DOTS is a productivity win for the right problem.

---

## 7. The chunk model (and why it matters)

ECS stores components in **chunks**: 16 KB blocks, each containing
entities with identical component layouts. A query for `Translation`
iterates the chunks that contain `Translation` data, jumping 16 KB at
a time. That's the cache friendliness the data-oriented pattern is
about.

**The senior rules**:

- **Keep components small and tight.** A 256-byte component is a
  problem; a 16-byte component is fine.
- **Avoid `Entity` fields in components you query often.** `Entity`
  is a 12-byte ID, but following it requires an indirection. Use
  `NativeArray<Entity>` if you need references; or just store the
  data you need.
- **Don't put managed types in components.** A `string` field on
  `IComponentData` works (with caveats) but the cost is real. Use
  `BlobAssetReference<T>` for read-only data, `FixedString64Bytes`
  for short strings.
- **Use `IEnableableComponent`** for "tags you can toggle" instead
  of add/remove. Add/remove changes the chunk layout and is slow.
- **System update groups matter.** Use
  `[UpdateInGroup(typeof(SimulationSystemGroup))]`,
  `[UpdateAfter(typeof(...))]`, `[UpdateBefore(typeof(...))]` to
  control the order.

---

## 8. Singleton components and settings

```csharp
public struct GameSettings : IComponentData
{
    public float GlobalSpeed;
    public int MaxEnemies;
}

// Set once at startup
var settings = SystemAPI.ManagedAPI.GetSingleton<GameSettings>();
// or in code:
state.EntityManager.AddComponentData(state.SystemHandle, new GameSettings { ... });
```

Singletons are the senior way to pass per-world state to systems
without globals.

---

## 9. The Hybrid path: ECS in a MonoBehaviour game

You don't have to commit to all-DOTS. The common senior pattern:

- **MonoBehaviour** for the 30-or-so "complex" things (UI, dialogue,
  inventory).
- **ECS** for the thousands of "simple" things (enemies, bullets,
  particles, environment props).

The "bridge" is:

- `IComponentData` on a `MonoBehaviour` (works in ECS).
- `GameObject` references via `EntityManager.GetComponentObject<>`.
- A "spawn entity from prefab" routine in a `MonoBehaviour` that
  creates entities, then deactivates the GameObject.

```csharp
public class EnemySpawner : MonoBehaviour
{
    public GameObject EnemyPrefab;

    void Start()
    {
        var world = World.DefaultGameObjectInjectionWorld;
        var em = world.EntityManager;

        for (int i = 0; i < 1000; i++)
        {
            var go = Instantiate(EnemyPrefab);
            go.SetActive(false);
            // ... bridge code to attach an entity to the GameObject
            // (Entities 1.x has helpers for this) ...
        }
    }
}
```

For the "10,000 enemies" cap, this hybrid is the most common
production pattern.

---

## 10. Things DOTS does not solve (yet, mid-2026)

- **UI Toolkit / UGUI** is still MonoBehaviour. ECS UI is being
  worked on but not production-ready.
- **Animation** (Mecanim / Animator) is MonoBehaviour-friendly. There
  are DOTS animation packages, but adoption is mixed.
- **Audio** is MonoBehaviour. ECS has an experimental audio system.
- **Visual scripting** is MonoBehaviour. (Bolt → Unity Visual
  Scripting.)

If your game is 60% UI, 30% animation, 10% gameplay, **DOTS is the
wrong tool for 90% of it.** Use DOTS for the 10% that's "10,000
enemies" and leave the rest alone.

---

## 11. Common pitfalls

### 11.1 Managed types in components

```csharp
// WRONG: a managed string lives in the GC heap
public struct Bad : IComponentData { public string Name; }

// RIGHT: fixed-size string for short names
public struct Good : IComponentData { public FixedString64Bytes Name; }

// RIGHT: blob asset for large data
public struct BigData : IComponentData { public BlobAssetReference<MyData> Data; }
```

### 11.2 System with no Burst

```csharp
public partial struct SlowSystem : ISystem
{
    public void OnUpdate(ref SystemState state)   // no [BurstCompile]
    {
        // runs as IL, much slower
    }
}
```

Always `[BurstCompile]` system `OnUpdate` and job `Execute` methods.

### 11.3 Forgetting `Dependency`

`SystemBase` and `ISystem` have a `Dependency` property. If your
system writes to a `NativeArray` outside of a job, **set
`state.Dependency = handle;`** to chain it. Forgetting this leads
to races that the safety system will catch in editor but not in
release.

### 11.4 Edit-time baking at runtime

Baking at runtime is slow. **Bake at build time** (the default) and
just instantiate entities from a baked subscene.

---

## 12. The verification path

```bash
# Burst is active in the system
Jobs > Worker Threads > YourSystem > "AOT (Burst)"

# Profiler shows the work in the right group
CPU Usage > Systems > SimulationSystemGroup > YourSystem

# Memory Profiler: entity chunk overhead
Memory > Native > EntityManager > chunks
```

The senior weekly review: count your entity count, count your
components per entity, count the bytes per entity. A well-designed
ECS world is **< 64 bytes per entity**. A poorly designed one is
**> 512 bytes per entity** and you have 100,000 of them.

---

## Summary

- DOTS is for **thousands of the same simple thing**, not "all
  Unity code".
- The model: Entity (id), Component (data), System (logic).
- Author with MonoBehaviours, bake to entities at build time.
- `[BurstCompile]` is mandatory.
- Use `IJobEntity` with `ScheduleParallel` for the senior pattern.
- Keep components small. Avoid `Entity` references in hot components.
- Use `IEnableableComponent` for tag toggling.
- Hybrid (MonoBehaviour + ECS) is the common production pattern.
