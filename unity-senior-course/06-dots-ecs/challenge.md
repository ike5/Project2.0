# Challenge 06 — Ship a 50,000-Entity Simulation

The senior developer gets asked "can we have 50,000 enemies on
screen?". The right answer is "yes, with DOTS". This challenge is
the full path.

**Time**: 3-4 hours.

---

## Requirements

- 50,000 entities in a single subscene.
- Each entity has a `LocalTransform`, a `Velocity`, a
  `HealthData`, and a `RenderMeshArrayIndex`.
- A `MovementSystem` updates positions every frame using
  `IJobEntity` + `ScheduleParallel`.
- A `DamageSystem` reduces health over time.
- A `CullSystem` removes entities with `Health <= 0` (or use
  `IEnableableComponent`).
- Frame time < 8 ms on a desktop CPU.
- Memory per entity < 100 bytes.

## Approach

1. **Components**: as above, all `IComponentData` structs.
2. **Authoring**: a single `EnemyAuthoring` with a `Baker` that
   adds the components and tags the entity as
   `TransformUsageFlags.Dynamic`.
3. **Spawner**: a subscene with one entity containing
   `Spawner { Count = 50_000 }`. A `SpawnerSystem` creates the
   entities in `OnUpdate`, then removes the `Spawner` component
   so it doesn't re-run.
4. **MovementSystem**: a `partial struct : ISystem` with a
   `BurstCompile` `OnUpdate` that schedules an `IJobEntity`.
5. **CullSystem**: a system that iterates entities with
   `Health <= 0` and `DestroyEntity`s them. **Or**, better,
   use `IEnableableComponent` and disable them.
6. **Rendering**: use Entities Graphics or
   `Graphics.RenderMeshIndirect` for instanced rendering.

## The senior discipline

- **Don't put `Entity` references in hot components.** They
  incur indirection.
- **Don't put managed types in components.** Strings → `FixedString`,
  arrays → `BlobAssetReference` or `DynamicBuffer`.
- **Use `IEnableableComponent` for tag toggling.** Add/remove
  changes the chunk layout and is slow.
- **Use `EntityCommandBuffer.ParallelWriter` for structural
  changes inside jobs.** This is the senior pattern for
  "spawn entities from inside a job".

## Verification

```bash
# In Editor
# - Subscene: 50,000 entities
# - Profiler: ECS Systems > SimulationSystemGroup > MovementSystem
#   - Should show "AOT (Burst)"
#   - Should run in < 1 ms
# - Memory Profiler: EntityManager chunks
#   - ~80 bytes per entity = 4 MB total
# - Run Play for 60 seconds, no leaks, no growth
```

If your numbers don't match:

- Check that the system has `[BurstCompile]` on both the struct
  and `OnUpdate`.
- Check that you used `ScheduleParallel`, not `Schedule`.
- Check the chunk layout in the Memory Profiler: if a single
  entity is > 100 bytes, you have a `Entity` reference or a
  large value type somewhere.

## Stretch goals

- **Add a `NavMeshAgent`-equivalent**: each entity moves toward
  a target. Use a `Target` component with a `float3 Position`.
- **Spatial hash grid**: a system bins entities into a 32×32
  grid for fast neighbor queries. The senior way to do
  collision-detection at scale.
- **Multithreaded spawning**: a `IJobChunk` that creates
  entities in parallel using `EntityCommandBuffer.ParallelWriter`.

## What we're testing

- DOTS is the right tool for 50,000-of-anything.
- The senior pattern is components + systems + jobs + Burst.
- The Profiler is how you verify.
- The Memory Profiler chunk view tells you if your data is
  well-laid-out.

The senior dev who can't do this can't ship a strategy game.
