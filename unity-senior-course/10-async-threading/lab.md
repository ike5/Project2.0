# Lab 10: Async Lifetimes and PlayerLoop Integration

**Time**: 75 minutes
**Goal**: Build a service that loads assets asynchronously with proper cancellation, integrates a custom subsystem into the PlayerLoop, and demonstrates the difference between a leaky async lifetime and a clean one.

## Setup (5 min)

1. New Unity 6 project.
2. Create a `Bootstrap` scene with one GameObject `Services`.
3. Create a script `AssetService.cs`, a script `PlayerLoopService.cs`, and a UI canvas with a button and a progress slider.

## Part A: Asset service with cancellation (20 min)

`AssetService.cs`:
```csharp
using System;
using System.Threading;
using UnityEngine;
using UnityEngine.ResourceManagement.AsyncOperations;
using UnityEngine.AddressableAssets;
using UnityEngine.ResourceManagement.ResourceProviders;
using System.Collections.Generic;
using Cysharp.Threading.Tasks;

public sealed class AssetService : IDisposable
{
    readonly Dictionary<string, AsyncOperationHandle> _cache = new();
    readonly CancellationTokenSource _cts = new();
    public CancellationToken Token => _cts.Token;

    public async Awaitable<Texture2D> LoadTextureAsync(string key)
    {
        if (_cache.TryGetValue(key, out var cached))
            return cached.Convert<Texture2D>();

        var op = Addressables.LoadAssetAsync<Texture2D>(key);
        _cache[key] = op;
        await op.Task; // Addressables handles are Task-based
        if (_cts.IsCancellationRequested) throw new OperationCanceledException();
        return op.Result;
    }

    public void Dispose()
    {
        _cts.Cancel();
        _cts.Dispose();
        foreach (var kv in _cache) Addressables.Release(kv.Value);
        _cache.Clear();
    }
}
```

Note: `Addressables.LoadAssetAsync` returns a Task in Unity 6 (Addressables 2.x). Awaiting it from an `async Awaitable` method captures the SynchronizationContext and resumes on the main thread.

Wire the service into the scene:

```csharp
public class Services : MonoBehaviour
{
    public AssetService Assets { get; private set; }

    void Awake()
    {
        Assets = new AssetService();
    }

    void OnDestroy() => Assets.Dispose();
}
```

The `OnDestroy` triggers `Assets.Dispose()`, which cancels the CTS, which cancels any in-flight load. The next continuation sees `IsCancellationRequested == true` and bails.

## Part B: Custom PlayerLoop subsystem (20 min)

The PlayerLoop is the central scheduling list. Insert a custom subsystem that ticks every frame at a specific stage.

`PlayerLoopService.cs`:
```csharp
using System;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.LowLevel;
using UnityEngine.PlayerLoop;

public sealed class PlayerLoopService
{
    public static event Action OnTick;

    static PlayerLoopSystem _registered;

    public static void Register()
    {
        if (_registered.type != null) return;
        _registered = new PlayerLoopSystem
        {
            type = typeof(PlayerLoopService),
            updateDelegate = Tick
        };

        var loop = PlayerLoop.GetCurrentPlayerLoop();
        // Insert after PreUpdate
        var preUpdate = FindSystem(loop, typeof(PreUpdate));
        var list = new List<PlayerLoopSystem>(preUpdate.subSystemList ?? Array.Empty<PlayerLoopSystem>())
        {
            _registered
        };
        preUpdate.subSystemList = list.ToArray();
        PlayerLoop.SetPlayerLoop(loop);
    }

    public static void Unregister()
    {
        var loop = PlayerLoop.GetCurrentPlayerLoop();
        var preUpdate = FindSystem(loop, typeof(PreUpdate));
        if (preUpdate.subSystemList == null) return;
        var list = new List<PlayerLoopSystem>(preUpdate.subSystemList);
        list.RemoveAll(s => s.type == typeof(PlayerLoopService));
        preUpdate.subSystemList = list.ToArray();
        PlayerLoop.SetPlayerLoop(loop);
        _registered = default;
    }

    static void Tick() => OnTick?.Invoke();

    static PlayerLoopSystem FindSystem(PlayerLoopSystem root, Type type)
    {
        if (root.type == type) return root;
        if (root.subSystemList == null) return default;
        foreach (var s in root.subSystemList)
        {
            var found = FindSystem(s, type);
            if (found.type != null) return found;
        }
        return default;
    }
}
```

Subscribers:

```csharp
public class TickSubscriber : MonoBehaviour
{
    void OnEnable() => PlayerLoopService.OnTick += OnTick;
    void OnDisable() => PlayerLoopService.OnTick -= OnTick;
    void OnTick() => Debug.Log($"tick at {Time.frameCount}");
}
```

Register from a bootstrap MonoBehaviour:

```csharp
void Awake() => PlayerLoopService.Register();
void OnDestroy() => PlayerLoopService.Unregister();
```

This pattern lets you decouple systems from MonoBehaviour Update. The PlayerLoop system runs once per frame in PreUpdate. Module 14 uses this for the event bus.

## Part C: Async lifetime leak demo (15 min)

Demonstrate the leak: an async method that does not check a cancellation token, and a service that holds onto the in-flight call.

`LeakyService.cs`:
```csharp
public class LeakyService : MonoBehaviour
{
    async void Start() // BAD: async void, no cancellation
    {
        await Awaitable.WaitForSecondsAsync(10f);
        Debug.Log("finished");
    }
}
```

This compiles, runs, and is a ticking time bomb. If the GameObject is destroyed at second 3, the async method keeps running on the main thread, holding a reference to `this`. After 7 more seconds, the method tries to log — the GameObject is gone, the log runs anyway, but any Transform access would throw.

Fix:

```csharp
public class CleanService : MonoBehaviour
{
    async Awaitable Start()
    {
        try
        {
            await Awaitable.WaitForSecondsAsync(10f, destroyCancellationToken);
            Debug.Log("finished");
        }
        catch (OperationCanceledException) { /* expected on destroy */ }
    }
}
```

`destroyCancellationToken` is the cancellation token tied to the MonoBehaviour's destroy event. Awaiting with this token throws `OperationCanceledException` on destroy. The `try/catch` handles it.

`async void` -> `async Awaitable` + discard:

```csharp
void OnSomeEvent() => _ = OnSomeEventAsync();
async Awaitable OnSomeEventAsync() { /* ... */ }
```

## Part D: Async iterator pattern (10 min)

Build an async iterator over frames:

```csharp
public static async Awaitable RunForFramesAsync(int count, Action<int> onFrame, CancellationToken ct = default)
{
    for (int i = 0; i < count; i++)
    {
        onFrame(i);
        await Awaitable.NextFrameAsync(ct);
    }
}

// usage
async Awaitable Start()
{
    await RunForFramesAsync(60, i => transform.Rotate(0, 1, 0), destroyCancellationToken);
}
```

This is a senior pattern: small async helpers that compose. They are testable, cancellable, and don't allocate.

## Part E: Profiler markers (10 min)

Wrap async methods with `ProfilerMarker.Auto()` to make them visible in the profiler:

```csharp
static readonly ProfilerMarker s_loadMarker = new("AssetService.Load");

public async Awaitable<Texture2D> LoadTextureAsync(string key)
{
    using (s_loadMarker.Auto())
    {
        // ...
    }
}
```

In the Profiler window, you will see the `AssetService.Load` marker, including the time spent in continuations.

## Verification

1. Run the AssetService. Click the button. The progress slider fills, the texture loads, the button text updates. Total time: 2-3 seconds (simulate with `WaitForSecondsAsync(0.5f)` chained 5 times if no Addressables).
2. Click the button, then close the scene mid-load. Check the console: no `MissingReferenceException`. The `OperationCanceledException` was caught.
3. Open the Profiler. Enable the CPU Usage profiler. Find `AssetService.Load` markers. Confirm the time is in the milliseconds.
4. Check the custom PlayerLoop subsystem: in the Profiler, find the `PlayerLoopService.Tick` markers. They run once per frame.

## Common pitfalls

- `async void` event handlers that throw — the exception is logged to the console but not propagated. Convert to `async Awaitable` and discard.
- Awaiting `Addressables.Task` from outside a `using` block — the handle is leaked. Always release.
- `WaitForSecondsAsync` in an `Update` loop — wait, no, that doesn't make sense. But: don't call `WaitForSecondsAsync(0)` to yield — use `NextFrameAsync`.
- Subscribing to `OnTick` and forgetting to unsubscribe. The subscriber MonoBehaviour is held alive by the static event. Always subscribe in OnEnable, unsubscribe in OnDisable.
- Multiple registrations of the same PlayerLoop subsystem. The `Register` method checks `_registered.type != null` to prevent duplicates.
- Using `ConfigureAwait(false)` in a `async Awaitable` method — Awaitable is main-thread by default; the ConfigureAwait pattern is for Task.

## What we're testing

- Can you build an async service that cancels cleanly on dispose?
- Do you understand `destroyCancellationToken` and when to use it?
- Can you register a custom PlayerLoop subsystem?
- Can you wrap async methods in `ProfilerMarker` for visibility?
- Do you know the difference between Awaitable, Task, and UniTask in Unity 6?

## Stretch goals

- Add a custom Job System integration: schedule a Burst job in `PlayerLoopService.Tick` and complete it later in the same tick.
- Add a custom SynchronizationContext that pipes to a UI thread for the editor (the editor runs UnityEngine calls on a different thread than the play mode).
- Implement an `AsyncLazy<T>` with cancellation, similar to `Lazy<T>` but with Awaitable.
