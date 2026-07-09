# Lab 14: Build a Senior-Grade Architecture

**Time**: 90 minutes
**Goal**: Build a small game system that uses five senior patterns: object pooling, state machine, ScriptableObject architecture, command pattern, and async save/load. Each pattern is a real implementation, not a toy.

## Setup (5 min)

1. New Unity 6 project.
2. Create a scene `TowerDefense` with a plane, a few cube "towers," and a spawner.
3. Create folder structure:
   - `Assets/Scripts/Config/`
   - `Assets/Scripts/Combat/`
   - `Assets/Scripts/Input/`
   - `Assets/Scripts/Save/`
   - `Assets/Scripts/State/`

## Part A: ScriptableObject config (15 min)

`Assets/Scripts/Config/EnemyConfig.cs`:
```csharp
using UnityEngine;

[CreateAssetMenu(menuName = "Game/EnemyConfig", fileName = "EnemyConfig")]
public class EnemyConfig : ScriptableObject
{
    public string enemyName = "Goblin";
    public int maxHealth = 100;
    public float moveSpeed = 2f;
    public int damage = 10;
    public int goldReward = 5;
}
```

`Assets/Scripts/Config/TowerConfig.cs`:
```csharp
using UnityEngine;

[CreateAssetMenu(menuName = "Game/TowerConfig", fileName = "TowerConfig")]
public class TowerConfig : ScriptableObject
{
    public string towerName = "Arrow Tower";
    public float range = 5f;
    public float fireRate = 1f;
    public int damage = 15;
    public GameObject projectilePrefab;
}
```

Create two assets: `Assets/Configs/Goblin.asset` and `Assets/Configs/ArrowTower.asset`. Set the values.

## Part B: Object pool for projectiles (15 min)

`Assets/Scripts/Combat/Projectile.cs`:
```csharp
using UnityEngine;

public class Projectile : MonoBehaviour
{
    public Vector3 velocity;
    public int damage;
    public float maxLifetime = 5f;
    float _lifetime;

    void OnEnable()
    {
        _lifetime = 0;
    }

    void Update()
    {
        transform.position += velocity * Time.deltaTime;
        _lifetime += Time.deltaTime;
        if (_lifetime > maxLifetime) gameObject.SetActive(false);
    }

    void OnDisable()
    {
        velocity = Vector3.zero;
        damage = 0;
    }
}
```

`Assets/Scripts/Combat/ProjectilePool.cs`:
```csharp
using System.Collections.Generic;
using UnityEngine;

public class ProjectilePool
{
    readonly Stack<Projectile> _pool = new();
    readonly Projectile _prefab;
    readonly Transform _parent;

    public ProjectilePool(Projectile prefab, Transform parent, int preallocate = 20)
    {
        _prefab = prefab;
        _parent = parent;
        for (int i = 0; i < preallocate; i++)
        {
            var p = Object.Instantiate(_prefab, parent);
            p.gameObject.SetActive(false);
            _pool.Push(p);
        }
    }

    public Projectile Fire(Vector3 position, Quaternion rotation, Vector3 velocity, int damage)
    {
        var p = _pool.Count > 0 ? _pool.Pop() : Object.Instantiate(_prefab, _parent);
        p.transform.SetPositionAndRotation(position, rotation);
        p.velocity = velocity;
        p.damage = damage;
        p.gameObject.SetActive(true);
        return p;
    }

    public void Return(Projectile p) => p.gameObject.SetActive(false);
}
```

The pool pre-allocates 20 projectiles. The `OnEnable`/`OnDisable` reset state so pooled projectiles don't carry stale data.

## Part C: State machine for enemy AI (20 min)

`Assets/Scripts/State/IState.cs`:
```csharp
public interface IState
{
    void Enter();
    void Update();
    void Exit();
}

public class StateMachine
{
    public IState Current { get; private set; }

    public void ChangeState(IState next)
    {
        Current?.Exit();
        Current = next;
        Current.Enter();
    }

    public void Update() => Current?.Update();
}
```

`Assets/Scripts/Combat/EnemyStates.cs`:
```csharp
using UnityEngine;

public class PatrolState : IState
{
    readonly Enemy _enemy;
    readonly Vector3[] _waypoints;
    int _index;

    public PatrolState(Enemy enemy, Vector3[] waypoints)
    {
        _enemy = enemy;
        _waypoints = waypoints;
    }

    public void Enter() { /* start walking */ }
    public void Update()
    {
        var target = _waypoints[_index];
        _enemy.transform.position = Vector3.MoveTowards(_enemy.transform.position, target, _enemy.config.moveSpeed * Time.deltaTime);
        if (Vector3.Distance(_enemy.transform.position, target) < 0.1f)
            _index = (_index + 1) % _waypoints.Length;
    }
    public void Exit() { }
}

public class ChaseState : IState
{
    readonly Enemy _enemy;
    Transform _target;

    public ChaseState(Enemy enemy, Transform target)
    {
        _enemy = enemy;
        _target = target;
    }

    public void Enter() { }
    public void Update()
    {
        _enemy.transform.position = Vector3.MoveTowards(_enemy.transform.position, _target.position, _enemy.config.moveSpeed * 1.5f * Time.deltaTime);
    }
    public void Exit() { }
}

public class AttackState : IState
{
    readonly Enemy _enemy;
    float _cooldown;

    public AttackState(Enemy enemy) { _enemy = enemy; }

    public void Enter() { _cooldown = 0; }
    public void Update()
    {
        _cooldown -= Time.deltaTime;
        if (_cooldown <= 0)
        {
            _enemy.targetTower.TakeDamage(_enemy.config.damage);
            _cooldown = 1f;
        }
    }
    public void Exit() { }
}
```

`Assets/Scripts/Combat/Enemy.cs`:
```csharp
using UnityEngine;

[RequireComponent(typeof(Health))]
public class Enemy : MonoBehaviour
{
    public EnemyConfig config;
    public Health health;
    public Tower targetTower;

    StateMachine _fsm;
    PatrolState _patrol;
    ChaseState _chase;
    AttackState _attack;

    void Awake()
    {
        health = GetComponent<Health>();
    }

    public void Init(Vector3[] waypoints, Tower target)
    {
        targetTower = target;
        _patrol = new PatrolState(this, waypoints);
        _chase = new ChaseState(this, target.transform);
        _attack = new AttackState(this);
        _fsm = new StateMachine();
        _fsm.ChangeState(_patrol);
    }

    void Update()
    {
        if (targetTower == null) return;
        var dist = Vector3.Distance(transform.position, targetTower.transform.position);
        if (dist < 2f) _fsm.ChangeState(_attack);
        else if (dist < 5f) _fsm.ChangeState(_chase);
        else _fsm.ChangeState(_patrol);
        _fsm.Update();
    }
}
```

The state machine has three states. Transitions are based on distance to the tower. Each state is its own class with `Enter`/`Update`/`Exit`.

## Part D: Command pattern for tower placement (15 min)

`Assets/Scripts/Input/PlaceTowerCommand.cs`:
```csharp
using UnityEngine;

public class PlaceTowerCommand
{
    readonly Tower _tower;
    readonly Vector3 _position;
    readonly TowerConfig _config;
    Vector3 _previousPosition;
    bool _wasPlaced;

    public PlaceTowerCommand(Tower tower, Vector3 position, TowerConfig config)
    {
        _tower = tower;
        _position = position;
        _config = config;
    }

    public void Execute()
    {
        _previousPosition = _tower.transform.position;
        _tower.transform.position = _position;
        _tower.config = _config;
        _tower.gameObject.SetActive(true);
        _wasPlaced = true;
    }

    public void Undo()
    {
        if (!_wasPlaced) return;
        _tower.transform.position = _previousPosition;
        _tower.gameObject.SetActive(false);
    }
}
```

`Assets/Scripts/Input/InputController.cs`:
```csharp
using System.Collections.Generic;
using UnityEngine;

public class InputController : MonoBehaviour
{
    public Tower towerPrefab;
    public TowerConfig defaultTowerConfig;
    readonly Stack<PlaceTowerCommand> _history = new();

    void Update()
    {
        if (Input.GetMouseButtonDown(0))
        {
            var pos = Camera.main.ScreenToWorldPoint(Input.mousePosition);
            pos.z = 0;
            var cmd = new PlaceTowerCommand(towerPrefab, pos, defaultTowerConfig);
            cmd.Execute();
            _history.Push(cmd);
        }
        if (Input.GetKeyDown(KeyCode.Z) && _history.Count > 0)
        {
            _history.Pop().Undo();
        }
    }
}
```

Click to place. Press Z to undo. The command pattern captures the placement, the Undo restores the previous state.

## Part E: Async save (15 min)

`Assets/Scripts/Save/SaveData.cs`:
```csharp
using System;
using System.Collections.Generic;

[Serializable]
public class SaveData
{
    public int version = 1;
    public int gold = 100;
    public List<string> placedTowerIds = new();
    public List<Vector3> placedTowerPositions = new();
}
```

`Assets/Scripts/Save/SaveSystem.cs`:
```csharp
using System;
using System.IO;
using System.Threading;
using UnityEngine;

public static class SaveSystem
{
    const int CurrentVersion = 1;
    static string SavePath => Path.Combine(Application.persistentDataPath, "save.dat");

    public static async Awaitable SaveAsync(SaveData data, CancellationToken ct = default)
    {
        var json = await Task.Run(() => JsonUtility.ToJson(data, prettyPrint: false), ct);
        var tmpPath = SavePath + ".tmp";
        await Task.Run(() => File.WriteAllText(tmpPath, json), ct);
        await Task.Run(() =>
        {
            if (File.Exists(SavePath)) File.Delete(SavePath);
            File.Move(tmpPath, SavePath);
        }, ct);
    }

    public static async Awaitable<SaveData> LoadAsync(CancellationToken ct = default)
    {
        if (!File.Exists(SavePath)) return null;
        var json = await Task.Run(() => File.ReadAllText(SavePath), ct);
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

The save runs entirely off the main thread. The atomic write prevents corruption.

Wire it up: on `F5`, save. On `F9`, load.

## Verification

1. The game has a few enemies patrolling, then chasing a tower, then attacking it. State transitions are visible in the console.
2. Projectiles fire from a tower. The pool pre-allocates 20. After firing 30, the pool size stays at 20. No new Instantiate.
3. Click to place a tower. Press Z to undo. The tower disappears. Click to place it again. The Undo/Redo works.
4. Press F5. The save file appears in `persistentDataPath`. Press F9. The data loads.
5. Open the Profiler. Look at `ProjectilePool.Fire`. The function is O(1). The Instantiate is not called after the first 20.

## Common pitfalls

- **Pool without state reset**: the projectile keeps its old velocity after being returned and re-fired. Use `OnEnable`/`OnDisable` to reset.
- **State machine without `Exit`**: switching from `Chase` to `Attack` doesn't exit `Chase`. The next state has stale data.
- **Command with no Undo support**: you placed a tower and want to undo, but the Undo method throws. Implement Undo for every command.
- **Save on main thread**: the file IO blocks the game. Use `Task.Run`.
- **Save without atomic write**: the save file is half-written on a crash. Use `tmp + rename`.
- **Save without version**: you ship v2, the old save crashes on load. Add a version field.
- **DI for trivial cases**: you have 3 services and a LifetimeScope. The overhead is more than the benefit. Use plain constructor injection.

## What we're testing

- Can you implement a pool that resets state and pre-allocates?
- Can you implement a state machine with explicit Enter/Update/Exit?
- Can you build a command pattern with Execute/Undo?
- Can you save/load with async + atomic write + version?
- Can you wire ScriptableObject configs into MonoBehaviours?

## Stretch goals

- Add a DI container (VContainer) for the services.
- Add a SO event for "enemy killed" and have a UI element respond.
- Add a save game menu that lists the last 5 saves with timestamps.
- Add a config-driven difficulty: easy/normal/hard configs that change enemy stats.
