# Module 14: Senior Patterns Catalog

This module is the catalog of patterns that senior Unity developers use every day. None of them are language features or engine tricks — they are conventions that emerge from shipping games. By the end you will recognize these patterns in production codebases and know when to apply them.

## 1. Object pooling

Object pooling reuses GameObjects instead of instantiating and destroying them. It eliminates `Instantiate` and `Destroy` cost, eliminates the GC.Alloc that `Destroy` triggers when the object is in a managed list, and reduces the memory fragmentation from frequent allocations.

The pattern:
```csharp
public class ObjectPool<T> where T : Component
{
    readonly Stack<T> _pool = new();
    readonly T _prefab;
    readonly Transform _parent;

    public ObjectPool(T prefab, Transform parent = null, int preallocate = 0)
    {
        _prefab = prefab;
        _parent = parent;
        for (int i = 0; i < preallocate; i++) Return(CreateInstance());
    }

    T CreateInstance()
    {
        var instance = Object.Instantiate(_prefab, _parent);
        instance.gameObject.SetActive(false);
        return instance;
    }

    public T Get(Vector3 position, Quaternion rotation)
    {
        var instance = _pool.Count > 0 ? _pool.Pop() : CreateInstance();
        instance.transform.SetPositionAndRotation(position, rotation);
        instance.gameObject.SetActive(true);
        return instance;
    }

    public void Return(T instance)
    {
        instance.gameObject.SetActive(false);
        _pool.Push(instance);
    }
}
```

Use it for: projectiles, particles, enemies, UI elements that come and go frequently. Don't use it for static objects, scene props, or anything instantiated once at startup.

Unity 6 has a built-in `UnityEngine.Pool.ObjectPool<T>` for plain C# objects, and `UnityEngine.Pool.GenericPool` is an older interface. The custom pattern above is for `Component` types and gives more control.

The senior rule: pool the things that are instantiated per-frame or per-action. Don't pool everything. The pool itself has overhead (the Stack, the lookup, the disable/enable calls). For something instantiated once at scene start, pooling is more code with no benefit.

## 2. State machines

A state machine models an entity that has discrete states and transitions between them. Three patterns:

### 2.1 Switch-based FSM

```csharp
public class Enemy
{
    enum State { Idle, Patrol, Chase, Attack }
    State _state;

    void Update()
    {
        switch (_state)
        {
            case State.Idle: UpdateIdle(); break;
            case State.Patrol: UpdatePatrol(); break;
            case State.Chase: UpdateChase(); break;
            case State.Attack: UpdateAttack(); break;
        }
    }

    void TransitionTo(State newState)
    {
        // exit current, enter new
        _state = newState;
    }
}
```

Pros: trivial to write, easy to read, no allocation. Cons: scales poorly, all states in one class, transitions are implicit.

### 2.2 State pattern

```csharp
public interface IState
{
    void Enter();
    void Update();
    void Exit();
}

public class StateMachine
{
    IState _current;
    public void ChangeState(IState next)
    {
        _current?.Exit();
        _current = next;
        _current.Enter();
    }
    public void Update() => _current?.Update();
}
```

Each state is a class implementing `IState`. Transitions are explicit (`ChangeState`).

Pros: scales, each state is its own class, testable in isolation. Cons: allocation per state change (if not pooled), more files.

### 2.3 Unity StateMachineBehaviour

```csharp
public class AttackState : StateMachineBehaviour
{
    public float damage = 10;

    override public void OnStateEnter(Animator animator, AnimatorStateInfo stateInfo, int layerIndex)
    {
        // enter
    }

    override public void OnStateUpdate(Animator animator, AnimatorStateInfo stateInfo, int layerIndex)
    {
        // update
    }
}
```

Attached to an Animator Controller state. The Animator drives the transitions.

Pros: integrated with the Animator, designer-editable. Cons: coupled to Animator, hard to use without animation.

Senior pattern: the state pattern for AI and complex logic, switch-based FSM for trivial cases, StateMachineBehaviour when the state is also an animation state. Don't mix.

## 3. ScriptableObject architecture

ScriptableObjects (SOs) are data containers that live in the project, not in the scene. They are the foundation of data-driven design.

### 3.1 Config-driven gameplay

```csharp
[CreateAssetMenu(menuName = "Game/EnemyConfig")]
public class EnemyConfig : ScriptableObject
{
    public float moveSpeed = 3f;
    public int health = 100;
    public int damage = 10;
    public float attackRange = 2f;
}

public class Enemy : MonoBehaviour
{
    [SerializeField] EnemyConfig config;

    void Start()
    {
        _health = config.health;
    }

    void Update()
    {
        transform.position += Vector3.forward * config.moveSpeed * Time.deltaTime;
    }
}
```

The enemy has a config reference. The config is a ScriptableObject asset in the project. Designers can tweak `moveSpeed` without touching code or the scene.

### 3.2 SO events

```csharp
[CreateAssetMenu(menuName = "Game/Event")]
public class GameEvent : ScriptableObject
{
    readonly List<IGameEventListener> _listeners = new();

    public void Raise()
    {
        for (int i = _listeners.Count - 1; i >= 0; i--)
            _listeners[i].OnEventRaised();
    }

    public void Register(IGameEventListener listener) => _listeners.Add(listener);
    public void Unregister(IGameEventListener listener) => _listeners.Remove(listener);
}

public interface IGameEventListener { void OnEventRaised(); }
```

The event is an asset. Listeners register. The asset's `Raise()` is called from anywhere. This is the SO-based event bus.

Pros: no static singletons, no FindObjectOfType, designer-friendly (drag the asset in the inspector). Cons: not great for high-frequency events, no built-in ordering.

### 3.3 Data-driven design

The senior pattern: the entire game is data + code. The code is generic (read config, run logic). The data is in SOs. Designers tune the game by editing SOs, not code.

## 4. Save systems

Three approaches: binary, JSON, encrypted.

### 4.1 JSON

```csharp
[Serializable]
public class SaveData
{
    public int version;
    public PlayerState player;
    public List<QuestState> quests;
}

public static void Save(SaveData data)
{
    var json = JsonUtility.ToJson(data, prettyPrint: true);
    File.WriteAllText(SavePath, json);
}
```

Pros: human-readable, easy to debug, AOT-friendly (no reflection). Cons: larger file size, easier to cheat.

`JsonUtility` is the senior default. Newtonsoft.Json is more powerful but uses reflection and breaks with stripping (module 11).

### 4.2 Binary

```csharp
public static void Save<T>(T data)
{
    using var stream = File.Create(SavePath);
    var formatter = new BinaryFormatter();
    formatter.Serialize(stream, data);
}
```

Pros: smaller, faster. Cons: not human-readable, harder to migrate, BinaryFormatter is deprecated in modern .NET (use `System.Text.Json` or a custom binary serializer).

### 4.3 Encrypted

```csharp
public static void Save<T>(T data, byte[] key)
{
    var json = JsonUtility.ToJson(data);
    var encrypted = AesEncrypt(json, key);
    File.WriteAllBytes(SavePath, encrypted);
}
```

Pros: protected from casual cheaters. Cons: not actually secure (the key is in the binary), adds complexity.

The senior pattern: JSON for most games, encrypted JSON for competitive multiplayer, binary for very large saves. Always include a version field. Always write atomically (write to `.tmp`, rename).

## 5. Event bus

An event bus is a global publish/subscribe system. Three patterns in Unity:

### 5.1 C# event

```csharp
public static class EventBus
{
    public static event Action<DamageEvent> OnDamage;
    public static void Publish(DamageEvent e) => OnDamage?.Invoke(e);
}
```

Pros: simple, type-safe, fast. Cons: static, hard to test, no ordering, no per-bus isolation.

### 5.2 UnityEvent

Inspector-bound, designer-friendly, slower than C# events.

```csharp
[SerializeField] UnityEvent<DamageEvent> onDamage;
public void TakeDamage(int amount)
{
    onDamage.Invoke(new DamageEvent(amount));
}
```

Pros: no code needed for listeners, designer can wire it. Cons: not type-safe, slow, can't unsubscribe in code reliably.

### 5.3 SO-based

See section 3.2. SOs as event assets. Decouples publishers and listeners at the asset level.

The senior pattern: C# event for high-frequency in-code events, SO-based for designer-editable events, UnityEvent for one-off UI bindings. Don't use UnityEvent for anything that fires more than once per second.

## 6. Dependency injection (VContainer, Zenject)

DI containers manage the lifetime and dependencies of services. Two popular choices in Unity:

### 6.1 VContainer

```csharp
public class GameLifetimeScope : LifetimeScope
{
    public override void Configure(IContainerBuilder builder)
    {
        builder.Register<PlayerService>(Lifetime.Singleton);
        builder.Register<EnemySpawner>(Lifetime.Transient);
        builder.RegisterEntryPoint<GameBootstrap>();
    }
}
```

VContainer is fast, source-generator-based, and works with IL2CPP. It's the senior default for new projects.

### 6.2 Zenject (Extenject)

Older, more featureful, reflection-based. Slower than VContainer. Still widely used in legacy projects.

The senior pattern: use a DI container for services that need to be testable and have complex dependencies. Don't use a DI container for every MonoBehaviour. Most MonoBehaviours should be self-contained.

## 7. Service locator (anti-pattern)

```csharp
public static class Services
{
    public static T Get<T>() where T : class => /* find T */;
}
```

The "global registry" pattern. Looks like DI, isn't. The service is pulled by global state, which makes testing hard and creates hidden dependencies.

The senior rule: avoid service locators. Use DI. If you must use a service locator (for legacy code), make it explicit and minimal.

## 8. Command pattern for input

The command pattern wraps input as a data object, decoupled from the actor that processes it.

```csharp
public interface ICommand { void Execute(); void Undo(); }

public class MoveCommand : ICommand
{
    readonly Transform _target;
    readonly Vector3 _delta;
    Vector3 _previous;

    public MoveCommand(Transform target, Vector3 delta)
    {
        _target = target;
        _delta = delta;
    }

    public void Execute()
    {
        _previous = _target.position;
        _target.position += _delta;
    }

    public void Undo() => _target.position = _previous;
}

public class InputController
{
    readonly Stack<ICommand> _history = new();

    public void Move(Vector3 delta)
    {
        var cmd = new MoveCommand(_player, delta);
        cmd.Execute();
        _history.Push(cmd);
    }

    public void Undo()
    {
        if (_history.Count == 0) return;
        _history.Pop().Undo();
    }
}
```

Use it for: undo/redo, replay, networked input, AI that records its decisions.

## 9. Undo/redo

Built on the command pattern. The history stack holds executed commands. Undo pops and reverses. Redo re-executes.

```csharp
public class UndoRedoStack
{
    readonly Stack<ICommand> _undo = new();
    readonly Stack<ICommand> _redo = new();

    public void Execute(ICommand cmd)
    {
        cmd.Execute();
        _undo.Push(cmd);
        _redo.Clear();
    }

    public void Undo()
    {
        if (_undo.Count == 0) return;
        var cmd = _undo.Pop();
        cmd.Undo();
        _redo.Push(cmd);
    }

    public void Redo()
    {
        if (_redo.Count == 0) return;
        var cmd = _redo.Pop();
        cmd.Execute();
        _undo.Push(cmd);
    }
}
```

Use it for: editor tools, build modes, anything with user-driven changes. The pattern is the same regardless of the domain.

## 10. ECS for the hot path, MonoBehaviour for everything else (hybrid)

Unity's DOTS/ECS is fast for compute-heavy work. MonoBehaviour is fast for everything else. The senior pattern: ECS for the simulation (hundreds of units, physics, particles), MonoBehaviour for the rest (UI, scripts, one-off logic).

```csharp
// ECS for combat simulation
public struct Unit : IComponentData
{
    public float Health;
    public float Speed;
}

public partial class CombatSystem : SystemBase
{
    protected override void OnUpdate()
    {
        var dt = SystemAPI.Time.DeltaTime;
        foreach (var (transform, unit) in SystemAPI.Query<RefRW<LocalTransform>, RefRO<Unit>>())
        {
            transform.ValueRW.Position += new float3(0, 0, unit.ValueRO.Speed * dt);
        }
    }
}

// MonoBehaviour for UI
public class HealthBar : MonoBehaviour
{
    [SerializeField] EntityManager entityManager;
    [SerializeField] Entity unitEntity;
    [SerializeField] Image fillImage;

    void Update()
    {
        var health = entityManager.GetComponentData<Unit>(unitEntity).Health;
        fillImage.fillAmount = health / 100f;
    }
}
```

ECS is the hot path. The UI is MonoBehaviour reading from the ECS world. The boundary is well-defined.

## 11. Save/load with async

Use `Awaitable` (module 10) for save/load that doesn't block the main thread:

```csharp
public async Awaitable SaveAsync(SaveData data, CancellationToken ct = default)
{
    var json = await Task.Run(() => JsonUtility.ToJson(data), ct);
    var tmpPath = Path.Combine(Application.persistentDataPath, "save.tmp");
    var path = Path.Combine(Application.persistentDataPath, "save.dat");
    await Task.Run(() => File.WriteAllText(tmpPath, json), ct);
    await Task.Run(() =>
    {
        if (File.Exists(path)) File.Delete(path);
        File.Move(tmpPath, path);
    }, ct);
}
```

The serialize and write run on a worker thread. The main thread is free.

## 12. Hot reload with the Hot Reload package

The Hot Reload package (`com.singularitygroup.hotreload`) recompiles your C# code in the running player. You can change a method body, save, and the running game picks up the change without restart.

Pros: 10x faster iteration on gameplay code. Cons: limited to method body changes (no new fields, no new methods in some cases), state is reset for changed classes.

The senior pattern: use Hot Reload for iteration. Don't rely on it for production fixes. Some changes require a full restart. The package is a development tool.

## 13. The senior rules

1. Pool the things that are instantiated frequently. Don't pool everything.
2. Use the state pattern for complex AI, switch-based FSM for trivial cases.
3. ScriptableObjects for data, MonoBehaviours for logic.
4. JSON for saves. Atomic write. Versioned format.
5. C# events for high-frequency, SO events for designer-editable, UnityEvent for UI.
6. VContainer for DI. Avoid service locators.
7. Command pattern for input and undo/redo.
8. ECS for the hot path, MonoBehaviour for the rest.
9. Async save/load to avoid main-thread hitches.
10. Hot reload for iteration. Not for production.

## 14. Common pitfalls

- **Pooling without `OnDisable`/`OnEnable` reset**: a pooled object retains state from the last use. The next user sees stale data. Reset all state in `OnEnable` and `OnDisable`.
- **SO events without `OnDisable` unregister**: the listener stays subscribed after the GameObject is destroyed. NullReferenceException on next raise.
- **JSON save without version field**: you ship v2 of the save format, the old saves crash. Always version, always handle the version mismatch.
- **Async save blocking the main thread**: `File.WriteAllText` on the main thread. The disk IO blocks the main thread for the duration. Use `Task.Run`.
- **Service locator hidden everywhere**: the code is unmaintainable, untestable. Refactor to DI.
- **State pattern with no exit transition**: the previous state's `Exit()` is never called. State leaks.
- **ECS for UI**: ECS is for compute. UI is for MonoBehaviour. Don't force UI into ECS.
- **Hot reload in production**: the package is dev-only. Don't ship with it.
- **DI container for trivial cases**: 3 services don't need a container. Use plain constructor injection or a factory.

## What to read next

- Module 9: NGO uses the command pattern for input.
- Module 10: async save/load is the Awaitable pattern.
- Module 11: stripping breaks JSON deserialization; use JsonUtility.
- Module 13: build automation runs unit tests against the patterns.
