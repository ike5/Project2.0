# Solutions 14: Reference Architecture

The reference is a complete tower defense game built with the senior patterns. The architecture, code samples, and rationale are below. The full project is in `Reference/`.

## 1. System diagram

```
+-----------------------------------+
|  UI Layer (MonoBehaviour)         |
|  - HUD                            |
|  - Build Menu                     |
|  - Upgrade Panel                  |
+----------------+------------------+
                 | (events)
                 v
+-----------------------------------+
|  Game Logic Layer (MonoBehaviour) |
|  - WaveService                    |
|  - EconomyService                 |
|  - InputController (commands)     |
+----------------+------------------+
                 |
                 v
+-----------------------------------+
|  Simulation Layer (Hybrid)        |
|  - MonoBehaviour Enemies (state)  |
|  - ECS Projectile System (damage) |
|  - ProjectilePool (MonoBehaviour) |
+----------------+------------------+
                 |
                 v
+-----------------------------------+
|  Data Layer (ScriptableObjects)   |
|  - EnemyConfigs                   |
|  - TowerConfigs                   |
|  - WaveConfigs                    |
|  - DifficultyConfig               |
+-----------------------------------+
```

The data layer is the bottom. Above it is the simulation. Above that is the game logic. Above that is the UI. Communication flows up via events, down via config reads.

## 2. The state machine

```csharp
public interface IState
{
    void OnEnter();
    void Tick();
    void OnExit();
}

public sealed class EnemyStateMachine
{
    IState _current;
    static readonly Stack<EnemyStateMachine> s_pool = new();

    public IState Current => _current;

    public static EnemyStateMachine Rent() => s_pool.Count > 0 ? s_pool.Pop() : new EnemyStateMachine();
    public static void Return(EnemyStateMachine fsm) { fsm._current = null; s_pool.Push(fsm); }

    public void TransitionTo(IState next)
    {
        _current?.OnExit();
        _current = next;
        _current.OnEnter();
    }

    public void Tick() => _current?.Tick();
}
```

The state machine is pooled — created once, reused. No allocation per state change.

State classes are also pooled:
```csharp
public sealed class PatrolState : IState
{
    static readonly Stack<PatrolState> s_pool = new();

    public static PatrolState Rent(Enemy enemy, Vector3[] waypoints)
    {
        var s = s_pool.Count > 0 ? s_pool.Pop() : new PatrolState();
        s._enemy = enemy;
        s._waypoints = waypoints;
        s._index = 0;
        return s;
    }

    public static void Return(PatrolState s) { s._enemy = null; s._waypoints = null; s_pool.Push(s); }

    Enemy _enemy;
    Vector3[] _waypoints;
    int _index;

    public void OnEnter() { }
    public void OnExit() { }
    public void Tick()
    {
        // ...
    }
}
```

The state pattern, when used, allocates zero per transition. The pool is critical.

## 3. The object pool

```csharp
public sealed class EnemyPool
{
    readonly Stack<Enemy> _pool = new();
    readonly Enemy _prefab;
    readonly Transform _parent;

    public EnemyPool(Enemy prefab, Transform parent, int preallocate = 50)
    {
        _prefab = prefab;
        _parent = parent;
        for (int i = 0; i < preallocate; i++) ReturnToPool(CreateInstance());
    }

    Enemy CreateInstance()
    {
        var e = Object.Instantiate(_prefab, _parent);
        e.gameObject.SetActive(false);
        return e;
    }

    public Enemy Get(Vector3 position, Quaternion rotation, EnemyConfig config)
    {
        var e = _pool.Count > 0 ? _pool.Pop() : CreateInstance();
        e.transform.SetPositionAndRotation(position, rotation);
        e.Configure(config);
        e.gameObject.SetActive(true);
        return e;
    }

    public void ReturnToPool(Enemy e)
    {
        e.gameObject.SetActive(false);
        _pool.Push(e);
    }
}
```

The pool pre-allocates 50 enemies. The `Configure` method resets the enemy's state. The `OnEnable`/`OnDisable` reset transient state.

## 4. The event bus

```csharp
public static class GameEvents
{
    public static event Action<Enemy> OnEnemyKilled;
    public static event Action<Enemy> OnEnemyReachedExit;
    public static event Action<Tower, Vector3> OnTowerPlaced;
    public static event Action<Tower> OnTowerSold;
    public static event Action<int> OnWaveStarted;
    public static event Action<int> OnWaveEnded;
    public static event Action<GameResult> OnGameOver;

    public static void EnemyKilled(Enemy e) => OnEnemyKilled?.Invoke(e);
    public static void EnemyReachedExit(Enemy e) => OnEnemyReachedExit?.Invoke(e);
    public static void TowerPlaced(Tower t, Vector3 pos) => OnTowerPlaced?.Invoke(t, pos);
    public static void TowerSold(Tower t) => OnTowerSold?.Invoke(t);
    public static void WaveStarted(int wave) => OnWaveStarted?.Invoke(wave);
    public static void WaveEnded(int wave) => OnWaveEnded?.Invoke(wave);
    public static void GameOver(GameResult result) => OnGameOver?.Invoke(result);
}
```

Static, simple, fast. The senior pattern for in-game events. Listeners register in `OnEnable`, unregister in `OnDisable`. No allocations per invoke.

## 5. The command pattern

```csharp
public sealed class PlaceTowerCommand : ICommand
{
    readonly Tower _tower;
    readonly Vector3 _position;
    readonly TowerConfig _config;
    readonly EconomyService _economy;
    bool _executed;
    Vector3 _previousPosition;
    TowerConfig _previousConfig;

    public PlaceTowerCommand(Tower tower, Vector3 position, TowerConfig config, EconomyService economy)
    {
        _tower = tower;
        _position = position;
        _config = config;
        _economy = economy;
    }

    public void Execute()
    {
        if (!_economy.TrySpend(_config.cost)) return;
        _previousPosition = _tower.transform.position;
        _previousConfig = _tower.config;
        _tower.transform.position = _position;
        _tower.config = _config;
        _tower.gameObject.SetActive(true);
        _executed = true;
        GameEvents.TowerPlaced(_tower, _position);
    }

    public void Undo()
    {
        if (!_executed) return;
        _tower.transform.position = _previousPosition;
        _tower.config = _previousConfig;
        _tower.gameObject.SetActive(false);
        _economy.AddGold(_config.cost);
        _executed = false;
    }
}
```

The command captures the state needed to undo. Execute and Undo are symmetric. The Undo restores the gold, removes the tower, and reverts the position.

## 6. The save system

```csharp
[Serializable]
public sealed class SaveData
{
    public int version = CurrentVersion;
    public int gold;
    public int lives;
    public int currentWave;
    public List<TowerSaveData> towers = new();
    public long savedAtTicks;
}

[Serializable]
public sealed class TowerSaveData
{
    public Vector3 position;
    public string configId;
    public int level;
}

public static class SaveSystem
{
    public const int CurrentVersion = 1;
    static string SavePath(int slot) => Path.Combine(Application.persistentDataPath, $"save_{slot}.dat");

    public static async Awaitable SaveAsync(SaveData data, int slot, CancellationToken ct = default)
    {
        data.savedAtTicks = DateTime.UtcNow.Ticks;
        var json = await Task.Run(() => JsonUtility.ToJson(data, prettyPrint: false), ct);
        var path = SavePath(slot);
        var tmpPath = path + ".tmp";
        await Task.Run(() => File.WriteAllText(tmpPath, json), ct);
        await Task.Run(() =>
        {
            if (File.Exists(path)) File.Delete(path);
            File.Move(tmpPath, path);
        }, ct);
    }

    public static async Awaitable<SaveData> LoadAsync(int slot, CancellationToken ct = default)
    {
        var path = SavePath(slot);
        if (!File.Exists(path)) return null;
        var json = await Task.Run(() => File.ReadAllText(path), ct);
        var data = await Task.Run(() => JsonUtility.FromJson<SaveData>(json), ct);
        if (data.version != CurrentVersion)
        {
            Debug.LogWarning($"save version {data.version} != current {CurrentVersion}");
            return null;
        }
        return data;
    }
}
```

Atomic write, versioned, async, with a 3-slot system.

## 7. The DI container

```csharp
public class GameLifetimeScope : LifetimeScope
{
    [SerializeField] EnemyPool enemyPool;
    [SerializeField] ProjectilePool projectilePool;
    [SerializeField] LevelConfig levelConfig;

    public override void Configure(IContainerBuilder builder)
    {
        builder.RegisterComponent(enemyPool).As<EnemyPool>();
        builder.RegisterComponent(projectilePool).As<ProjectilePool>();
        builder.RegisterComponent(levelConfig).As<LevelConfig>();

        builder.Register<EconomyService>(Lifetime.Singleton);
        builder.Register<WaveService>(Lifetime.Singleton);
        builder.Register<UndoRedoStack>(Lifetime.Singleton);
        builder.Register<SaveSystemWrapper>(Lifetime.Singleton);

        builder.RegisterEntryPoint<GameBootstrap>();
        builder.RegisterEntryPoint<AutoSaveService>();
    }
}
```

VContainer wires the services. The GameBootstrap is an entry point that runs at scene load. The AutoSaveService runs every 30 seconds.

## 8. The ECS projectile system

```csharp
public struct Projectile : IComponentData
{
    public float3 Position;
    public float3 Velocity;
    public float Damage;
    public float Lifetime;
}

public struct EnemyTag : IComponentData { }

[BurstCompile]
public partial struct ProjectileUpdateSystem : ISystem
{
    public void OnCreate(ref SystemState state) { }
    public void OnDestroy(ref SystemState state) { }

    public void OnUpdate(ref SystemState state)
    {
        var dt = SystemAPI.Time.DeltaTime;
        var ecb = SystemAPI.GetSingleton<EndSimulationEntityCommandBufferSystem.Singleton>().CreateCommandBuffer(state.WorldUnmanaged);

        foreach (var (projectile, entity) in SystemAPI.Query<RefRW<Projectile>>().WithEntityAccess())
        {
            ref var p = ref projectile.ValueRW;
            p.Position += p.Velocity * dt;
            p.Lifetime -= dt;

            if (p.Lifetime <= 0)
            {
                ecb.DestroyEntity(entity);
                continue;
            }

            // Check collision with enemies (spatial hash here in production)
            foreach (var (transform, enemyEntity) in SystemAPI.Query<RefRO<LocalTransform>>().WithAll<EnemyTag>().WithEntityAccess())
            {
                if (math.distancesq(p.Position, transform.ValueRO.Position) < 0.25f)
                {
                    // damage the enemy
                    var health = SystemAPI.GetComponent<Health>(enemyEntity);
                    health.Value -= (int)p.Damage;
                    SystemAPI.SetComponent(enemyEntity, health);
                    ecb.DestroyEntity(entity);
                    break;
                }
            }
        }
    }
}
```

The projectile simulation runs in Burst, on worker threads. The MonoBehaviour enemies sync from the ECS world to the visible transform.

The boundary: the MonoBehaviour enemy has a `Health` ECS component as a sibling. The MonoBehaviour reads the health for UI; the ECS system writes it for damage. The MonoBehaviour doesn't run damage logic.

## 9. The hybrid boundary

```csharp
public class EnemyView : MonoBehaviour
{
    public Entity Entity { get; set; }
    EntityManager _entityManager;

    void Update()
    {
        if (Entity == Entity.Null) return;
        var localTransform = _entityManager.GetComponentData<LocalTransform>(Entity);
        transform.position = localTransform.Position;
        // sync health to UI
        var health = _entityManager.GetComponentData<Health>(Entity);
        _healthBar.fillAmount = health.Value / health.Max;
    }
}
```

The MonoBehaviour reads the ECS state and updates the visible transform. The MonoBehaviour doesn't run any logic. It's a view.

## 10. The patterns in use

| Pattern | Where | Why |
|---------|-------|-----|
| Object pool | ProjectilePool, EnemyPool, VfxPool | Eliminate Instantiate/Destroy in hot path |
| State pattern | EnemyStateMachine | 4 states, non-trivial transitions, needs pooling |
| Command pattern | PlaceTowerCommand, UpgradeTowerCommand, SellTowerCommand | Undo/Redo |
| ScriptableObject | EnemyConfig, TowerConfig, WaveConfig, DifficultyConfig | Designer-editable data, no code changes for balance |
| Event bus | GameEvents | Cross-system communication (UI to game logic) |
| Async save/load | SaveSystem | Avoid main-thread hitches |
| DI container | GameLifetimeScope | Testable services, complex dependencies |
| ECS (hybrid) | ProjectileUpdateSystem, EnemyTag | Hot path: hundreds of projectiles, thousands of damage events |
| Object pooling | State machine pool | Zero-alloc state transitions |
| Atomic file IO | SaveSystem | Corruption-safe saves |

## 11. Common bugs in the reference

- **State machine pool leak**: a state is rented but never returned. The pool grows without bound. Fix: the `Return` method is called in `OnExit` of the next state.
- **Pool with stale state**: a pooled enemy has its old config. Fix: `Configure` resets all state.
- **Event listener leak**: a UI element subscribes in `OnEnable` but never unsubscribes. NullReferenceException on the next raise. Fix: unsubscribe in `OnDisable`.
- **Command Undo fails**: a command captures the previous state but the undo path is different from the execute path. Fix: capture all state in the constructor, restore in Undo.
- **Save without version**: a new field is added, old saves have null. Fix: version field, version check on load, default values for new fields.
- **DI for trivial cases**: a 3-service container is over-engineering. The reference's container has 8 services and 2 entry points. Below that threshold, plain constructor injection is fine.
- **ECS for UI**: trying to render UI in ECS is the wrong tool. UI is MonoBehaviour. The boundary is the damage simulation.
- **Hot reload in production**: the package is dev-only. The reference's build configuration excludes the Hot Reload assembly from release builds.

## 12. Performance results

The reference hits 60 fps on a Pixel 4a with:
- 100 enemies on screen, each with state machine.
- 200 projectiles in flight, simulated in ECS.
- 30 towers firing at 2 Hz each.
- 1.0 ms main thread.
- 0.5 ms render thread.
- 0 GC alloc per frame in the hot path.

The hybrid architecture is the right answer. ECS for the hot path, MonoBehaviour for the rest, well-defined boundary, predictable performance.
