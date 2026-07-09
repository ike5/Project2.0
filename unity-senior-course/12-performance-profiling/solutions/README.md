# Solutions 12: Profile Report Reference

The reference profile report is in `Reference/REPORT.md`. The summary is below. The full report includes the profile captures, the Memory Profiler snapshots, and the fix diffs.

## 1. Executive summary

We took a 45 fps RPG scene, profiled on a Pixel 4a, and identified five bottlenecks. We fixed them in two days of work. The result: 60 fps on the Pixel 4a, 80+ fps on flagships, 0 GC alloc per frame, no memory leak.

| Metric | Before | After | Delta |
|--------|--------|-------|-------|
| Median frame time | 22.0 ms | 15.8 ms | -28% |
| p95 frame time | 31.0 ms | 18.0 ms | -42% |
| p99 frame time | 48.0 ms | 22.0 ms | -54% |
| GC alloc per frame | 4.2 KB | 0.0 KB | -100% |
| GC events per minute | 12 | 0 | -100% |
| Peak memory | 1.8 GB | 1.1 GB | -39% |
| Draw calls | 1800 | 850 | -53% |
| Setpass calls | 420 | 180 | -57% |

## 2. The five bottlenecks

### Bottleneck 1: O(n^2) NPC distance check (8 ms/frame)

**Where**: `NPCDirector.Update()`. Every frame, for every NPC, find the closest player. The implementation was a double loop over 50 NPCs and 8 players = 400 distance checks per frame. That should be cheap. But the call was being made in `OnTriggerStay` callbacks, of which there were 50 * 8 = 400 per frame, each doing the same distance check. Plus the implementation was using `Vector3.Distance` (sqrt) instead of `sqrMagnitude`. Plus it was inside a `foreach` over a `List<NPC>` that was being modified by another system.

**Fix**:
1. Cache the closest player per NPC in a dictionary, recompute every 0.5 seconds instead of every frame.
2. Use `sqrMagnitude` instead of `Vector3.Distance`.
3. Move the iteration out of the trigger callbacks and into a single pass.
4. Use a `NativeArray` with a Burst-compiled job to do the closest-player check across all NPCs in parallel.

**Result**: 8 ms -> 1.2 ms. Saved 6.8 ms.

### Bottleneck 2: UI rebuild every frame (4.5 ms/frame)

**Where**: `QuestUI.Update()`. The quest UI was rebuilding the entire quest log every frame to show the current objective progress. With 20 quests and 5 objectives each, that's 100 text components updated per frame, each triggering a layout rebuild.

**Fix**:
1. Only update the text when the value changes.
2. Cache the text component references; don't look them up by name.
3. Use a dirty flag instead of a per-frame check.
4. Move the UI to UIToolkit (which doesn't rebuild on text change, it invalidates only the changed elements).

**Result**: 4.5 ms -> 0.3 ms. Saved 4.2 ms.

### Bottleneck 3: Instantiate/Destroy for projectiles (3 ms/frame)

**Where**: `CombatSystem.Update()`. Every time a player fired, a projectile was instantiated with `Object.Instantiate`. Every time it hit, it was destroyed with `Object.Destroy`. The Instantiate allocates and the Destroy triggers a GC.Alloc if the object is in a managed list.

**Fix**:
1. Implement a projectile pool (see module 14).
2. Pre-allocate 200 projectiles at scene load.
3. Get/return from the pool instead of Instantiate/Destroy.

**Result**: 3 ms -> 0.2 ms. Saved 2.8 ms. GC alloc per frame dropped from 4.2 KB to 0.5 KB.

### Bottleneck 4: Physics per-frame on 200 rigidbodies (2.5 ms/frame)

**Where**: `Physics.Simulate`. 200 rigidbodies with colliders, simulated every frame at 50 Hz. Most of them were static (didn't move). The cost was the broadphase, not the actual simulation.

**Fix**:
1. Mark non-moving interactables as kinematic.
2. Use a custom broadphase (grid) for the moving ones.
3. Reduce the simulation frequency for the slow-moving ones (1 Hz instead of 50 Hz).

**Result**: 2.5 ms -> 0.8 ms. Saved 1.7 ms.

### Bottleneck 5: Save system blocking main thread (1.5 ms/frame every 30s)

**Where**: `SaveSystem.Save()`. Every 30 seconds, the save system serialized the game state to JSON and wrote to disk. The serialization took 1.5 ms, the disk write took 8 ms (sync), causing a 10 ms hitch every 30 seconds.

**Fix**:
1. Move the save to async with `Awaitable`.
2. Use a worker thread for the JSON serialization.
3. Use async file IO for the disk write.
4. Throttle: don't save more than once every 5 seconds.

**Result**: 10 ms hitch -> 0 ms hitch. The save runs in the background.

## 3. Total savings

- Total frame time saved: 15.5 ms (22.0 -> 6.5 ms in raw work).
- The frame budget for 60 fps is 16.6 ms. We went from 22 ms (over budget) to 6.5 ms (well under budget), giving us headroom for future features.
- GC alloc: 4.2 KB/frame -> 0.0 KB/frame. Zero GC events in 10 minutes of testing.

## 4. Verification

- **Sustained test**: 10 minutes of gameplay with 8 players, 200 projectiles, 50 NPCs, 20 quests. Frame time stayed at 15-16 ms. No growth.
- **Memory test**: 30-minute soak. Memory peaked at 1.1 GB and stayed flat.
- **Network test**: 8 players in combat, 60 Hz tick rate, 80 ms RTT simulated. Frame time stayed at 16 ms.
- **Cold start**: first frame after scene load: 45 ms. After warm-up: 15 ms. The cold start is dominated by shader compilation; we use async shader compilation to hide it.

## 5. The fixes in code

### Bottleneck 1: NPC distance check with Burst

```csharp
[BurstCompile]
struct FindClosestPlayerJob : IJobParallelFor
{
    [ReadOnly] public NativeArray<float3> NpcPositions;
    [ReadOnly] public NativeArray<float3> PlayerPositions;
    [WriteOnly] public NativeArray<int> ClosestPlayer;

    public void Execute(int index)
    {
        var npcPos = NpcPositions[index];
        var closest = 0;
        var closestDistSq = float.MaxValue;
        for (int i = 0; i < PlayerPositions.Length; i++)
        {
            var distSq = math.distancesq(npcPos, PlayerPositions[i]);
            if (distSq < closestDistSq)
            {
                closestDistSq = distSq;
                closest = i;
            }
        }
        ClosestPlayer[index] = closest;
    }
}
```

The job runs across all NPCs in parallel. The main thread reads the result every 0.5 seconds.

### Bottleneck 2: UI dirty flag

```csharp
public class QuestObjectiveView : MonoBehaviour
{
    [SerializeField] TMP_Text label;
    int _lastValue = int.MinValue;
    int _lastMax = int.MinValue;

    public void Bind(QuestObjective objective)
    {
        objective.OnProgressChanged += Refresh;
        Refresh(objective);
    }

    void OnDestroy()
    {
        // unbind
    }

    void Refresh(QuestObjective obj)
    {
        if (obj.Current == _lastValue && obj.Max == _lastMax) return;
        _lastValue = obj.Current;
        _lastMax = obj.Max;
        label.SetText($"{_lastValue}/{_lastMax}");
    }
}
```

The check skips the SetText call if nothing changed. TMP_Text's SetText is much faster than assigning to `text` (no string allocation).

### Bottleneck 3: Projectile pool

```csharp
public class ProjectilePool
{
    readonly Stack<Projectile> _pool = new();

    public Projectile Get(Vector3 position, Quaternion rotation)
    {
        var p = _pool.Count > 0 ? _pool.Pop() : Object.Instantiate(_prefab);
        p.transform.SetPositionAndRotation(position, rotation);
        p.gameObject.SetActive(true);
        return p;
    }

    public void Return(Projectile p)
    {
        p.gameObject.SetActive(false);
        _pool.Push(p);
    }
}
```

The pool eliminates Instantiate/Destroy and the associated GC.Alloc.

### Bottleneck 4: Physics optimization

```csharp
public class StaticMarker : MonoBehaviour
{
    void Awake()
    {
        var rb = GetComponent<Rigidbody>();
        if (rb != null) rb.isKinematic = true;
    }
}
```

Mark non-moving rigidbodies as kinematic in `Awake`. Unity's PhysX skips kinematic bodies in the broadphase. 150 of the 200 rigidbodies became kinematic, the broadphase cost dropped by 75%.

### Bottleneck 5: Async save

```csharp
public async Awaitable SaveAsync(GameState state, CancellationToken ct = default)
{
    // serialize on background thread
    var json = await Task.Run(() => JsonUtility.ToJson(state), ct);
    // write to disk on background thread
    var path = Path.Combine(Application.persistentDataPath, "save.dat");
    var tmpPath = path + ".tmp";
    await Task.Run(() => File.WriteAllText(tmpPath, json), ct);
    await Task.Run(() =>
    {
        if (File.Exists(path)) File.Delete(path);
        File.Move(tmpPath, path);
    }, ct);
}
```

The save runs entirely off the main thread. The main thread never blocks on disk.

## 6. Profiler markers added

```csharp
public class ProfilingMarkers
{
    public static readonly ProfilerMarker NpcUpdate = new("NPC.Update");
    public static readonly ProfilerMarker UiRefresh = new("UI.Refresh");
    public static readonly ProfilerMarker Pool = new("Pool.Get");
    public static readonly ProfilerMarker Physics = new("Physics.Simulate");
    public static readonly ProfilerMarker Save = new("Save.Async");
}
```

These markers show up in the Profiler timeline and let us see at a glance which system is slow.

## 7. Profile Analyzer comparison

The reference's Profile Analyzer captures are saved in `Reference/ProfileData/`. The "before" capture has 22 ms median frame time, the "after" has 15.8 ms. The p99 dropped from 48 ms to 22 ms. The distribution is tighter (fewer spikes) because we eliminated the save hitch.

## 8. The report

The full `REPORT.md` is a 20-page document. It includes:
- The baseline profile.
- The five bottlenecks with code, profile screenshots, and fix descriptions.
- The post-fix profile.
- The verification methodology.
- The lessons learned.
- The recommendations for the next phase.

A senior-level report is data-driven, not narrative. Every claim has a number. Every number has a source (the Profiler capture). Every fix has a verification.

## 9. Common mistakes in the reference

- **Optimizing a non-bottleneck**: the team spent 2 hours on a particle effect optimization that saved 0.2 ms. The biggest bottleneck was the O(n^2) loop, which they fixed in 30 minutes. Lesson: profile first, fix the top 5, ignore the rest.
- **Trusting the editor Profiler**: the editor showed 8 ms frame time, the device showed 22 ms. Lesson: always profile on the target device.
- **Ignoring the variance**: a 60 fps target with a 48 ms p99 is not 60 fps. It's 60 fps with a hitch every 30 seconds. Lesson: use p95/p99, not just median.
- **Single-frame optimization**: a teammate made a 5 ms optimization on a specific frame, but the average was unchanged. The optimization only helped the worst case. Lesson: optimize the distribution, not the peak.
- **Premature pooling**: pooling every GameObject in the scene. The pool overhead (linked list, dictionary) was more than the Instantiate cost for small objects. Lesson: pool only the hot path, leave the rest alone.
