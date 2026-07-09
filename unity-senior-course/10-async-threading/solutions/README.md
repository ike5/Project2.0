# Solutions 10: Asset Pipeline Reference Implementation

The reference implementation is in `Assets/Scripts/AssetPipeline/`. The key design decisions and tradeoffs are below.

## 1. Service lifetime and cancellation

The reference uses a `CancellationTokenSource` per service, with optional linking to an external token (e.g. a `MonoBehaviour.destroyCancellationToken`).

```csharp
public sealed class AssetPipeline : IDisposable
{
    readonly CancellationTokenSource _internalCts = new();
    readonly CancellationTokenSource _externalCts;
    readonly CancellationTokenSource _linkedCts;
    bool _disposed;

    public AssetPipeline(CancellationToken externalToken = default)
    {
        _externalCts = CancellationTokenSource.CreateLinkedTokenSource(externalToken);
        _linkedCts = CancellationTokenSource.CreateLinkedTokenSource(
            _internalCts.Token, _externalCts.Token);
    }

    public CancellationToken Token => _linkedCts.Token;

    public void Dispose()
    {
        if (_disposed) return;
        _disposed = true;
        _internalCts.Cancel();
        _linkedCts.Dispose();
        _externalCts.Dispose();
        _internalCts.Dispose();
    }
}
```

The double-linked CTS pattern lets the service cancel itself independently (`_internalCts`) or be cancelled by an owner (`_externalCts`). The merged token (`_linkedCts`) is what async methods await on.

Common bug: the reference used to call `Cancel()` on `_linkedCts` directly during dispose. That works for cancellation, but `_linkedCts` is not reusable after cancellation. Now it disposes the linked CTS and a fresh one would need to be created if the service is reset. In the reference, services are not reset — they are created fresh.

## 2. In-flight deduplication

```csharp
readonly Dictionary<string, Awaitable<UnityEngine.Object>> _inFlight = new();

public async Awaitable<T> LoadAsync<T>(string key, CancellationToken ct = default) where T : UnityEngine.Object
{
    ThrowIfDisposed();
    ct.ThrowIfCancellationRequested();

    if (_cache.TryGetValue(key, out var cached) && cached is T t)
    {
        Touch(key);
        _metrics.CacheHits++;
        return t;
    }

    if (_inFlight.TryGetValue(key, out var pending))
    {
        var result = await pending;
        return result as T;
    }

    _metrics.CacheMisses++;
    var loadOp = Addressables.LoadAssetAsync<UnityEngine.Object>(key);
    var awaitable = ToAwaitableAsync(loadOp, ct);
    _inFlight[key] = awaitable;

    try
    {
        var result = await awaitable;
        if (result is T typedResult)
        {
            _cache[key] = result;
            Touch(key);
            _metrics.LoadCount++;
            return typedResult;
        }
        throw new InvalidCastException($"asset {key} is not {typeof(T).Name}");
    }
    finally
    {
        _inFlight.Remove(key);
    }
}

static async Awaitable<UnityEngine.Object> ToAwaitableAsync(AsyncOperationHandle handle, CancellationToken ct)
{
    while (!handle.IsDone)
    {
        ct.ThrowIfCancellationRequested();
        await Awaitable.NextFrameAsync(ct);
    }
    if (handle.Status != AsyncOperationStatus.Succeeded)
        throw new Exception($"Addressables load failed: {handle.OperationException}");
    return handle.Result;
}
```

The `ToAwaitableAsync` helper bridges from the Addressables callback model to Awaitable. Addressables 2.x also exposes `handle.Task`, but the manual loop gives you cancellation in the middle of a multi-frame load.

The cast `result as T` is a place where the reference used to throw a `NullReferenceException` because `T` was a value type. The fix is the explicit `result is T typedResult` check.

## 3. LRU cache with eviction

```csharp
readonly LinkedList<string> _lru = new();
readonly Dictionary<string, LinkedListNode<string>> _nodeLookup = new();
readonly Dictionary<string, UnityEngine.Object> _cache = new();
const int MaxEntries = 256;

void Touch(string key)
{
    if (_nodeLookup.TryGetValue(key, out var node))
    {
        _lru.Remove(node);
        _lru.AddFirst(node);
        return;
    }
    var newNode = _lru.AddFirst(key);
    _nodeLookup[key] = newNode;
    if (_lru.Count > MaxEntries) EvictOldest();
}

void EvictOldest()
{
    var node = _lru.Last;
    if (node == null) return;
    _lru.RemoveLast();
    _nodeLookup.Remove(node.Value);
    if (_cache.TryGetValue(node.Value, out var asset))
    {
        Addressables.Release(asset);
        _cache.Remove(node.Value);
    }
}
```

LRU correctness: the `Touch` method is called on every access, and eviction happens at the tail. The reference does not lock around the LRU. All access is on the main thread (the only thread that touches `_cache`). If the LRU is ever accessed from a worker thread, add a lock.

Eviction calls `Addressables.Release`. This decrements the refcount. The asset is destroyed when the refcount hits zero. If the asset is also referenced by an in-flight load, the refcount stays at 1 until that load completes.

## 4. Retry with exponential backoff

```csharp
public async Awaitable<T> LoadWithRetryAsync<T>(
    string key, int maxAttempts = 3, int initialDelayMs = 100,
    CancellationToken ct = default) where T : UnityEngine.Object
{
    int delay = initialDelayMs;
    Exception lastEx = null;
    for (int attempt = 1; attempt <= maxAttempts; attempt++)
    {
        try
        {
            return await LoadAsync<T>(key, ct);
        }
        catch (OperationCanceledException) { throw; }
        catch (Exception ex)
        {
            lastEx = ex;
            if (attempt == maxAttempts) break;
            Debug.LogWarning($"[AssetPipeline] load {key} attempt {attempt}/{maxAttempts} failed: {ex.Message}");
            try { await Awaitable.WaitForSecondsAsync(delay / 1000f, ct); }
            catch (OperationCanceledException) { throw; }
            delay = Math.Min(delay * 2, 5000);
        }
    }
    _metrics.FailureCount++;
    throw new AssetLoadException($"load {key} failed after {maxAttempts} attempts", lastEx);
}
```

`OperationCanceledException` is rethrown immediately — it is not a load failure, it is a cancellation. The catch-and-rethrow prevents the retry from eating a cancellation.

The maximum delay cap of 5 seconds prevents runaway backoff. The reference uses 100, 200, 400, 800, 1600, 3200, 5000, 5000, ... for an exponential curve that flattens.

## 5. Time-bounded preload

```csharp
public async Awaitable<PreloadResult> PreloadWithBudgetAsync(
    IEnumerable<string> keys, int budgetMs, CancellationToken ct = default)
{
    ThrowIfDisposed();
    var sw = Stopwatch.StartNew();
    var loaded = new List<string>();
    var deferred = new List<string>();

    foreach (var key in keys)
    {
        ct.ThrowIfCancellationRequested();
        if (sw.ElapsedMilliseconds > budgetMs)
        {
            deferred.Add(key);
            continue;
        }
        try
        {
            await LoadAsync<UnityEngine.Object>(key, ct);
            loaded.Add(key);
        }
        catch (OperationCanceledException) { throw; }
        catch (Exception ex)
        {
            Debug.LogWarning($"[AssetPipeline] preload {key} failed: {ex.Message}");
            deferred.Add(key);
        }
    }
    return new PreloadResult(loaded, deferred, sw.ElapsedMilliseconds);
}

public readonly record struct PreloadResult(IReadOnlyList<string> Loaded, IReadOnlyList<string> Deferred, long ElapsedMs);
```

The reference returns a `PreloadResult` instead of just a count. The caller can show "loaded 47 of 53 in 50 ms" to the player. The deferred list is a hint for what to load next time.

## 6. Zone-based streaming

```csharp
public sealed class AssetZone
{
    public string Name { get; init; }
    public IReadOnlyList<string> Keys { get; init; }
    public int Priority { get; init; }
}

readonly Dictionary<string, AssetZone> _zones = new();
readonly HashSet<string> _streamedInZones = new();

public async Awaitable StreamInZoneAsync(string zoneName, CancellationToken ct = default)
{
    if (!_zones.TryGetValue(zoneName, out var zone))
        throw new ArgumentException($"unknown zone {zoneName}");
    if (_streamedInZones.Contains(zoneName)) return;
    foreach (var key in zone.Keys)
    {
        ct.ThrowIfCancellationRequested();
        await LoadAsync<UnityEngine.Object>(key, ct);
    }
    _streamedInZones.Add(zoneName);
}

public void StreamOutZone(string zoneName)
{
    if (!_zones.TryGetValue(zoneName, out var zone)) return;
    foreach (var key in zone.Keys) Release(key);
    _streamedInZones.Remove(zoneName);
}

public void Release(string key)
{
    if (!_cache.TryGetValue(key, out var asset)) return;
    Addressables.Release(asset);
    _cache.Remove(key);
    if (_nodeLookup.TryGetValue(key, out var node))
    {
        _lru.Remove(node);
        _nodeLookup.Remove(key);
    }
}
```

The reference uses a hashset of "streamed in" zones to make `StreamIn` idempotent. Calling it twice for the same zone is a no-op.

## 7. Metrics

```csharp
public sealed class AssetMetrics
{
    int _cacheHits, _cacheMisses, _loadCount, _failureCount;
    double _totalLoadMs;
    readonly object _lock = new();

    public void RecordHit() { lock (_lock) _cacheHits++; }
    public void RecordMiss() { lock (_lock) _cacheMisses++; }
    public void RecordLoad(double ms) { lock (_lock) { _loadCount++; _totalLoadMs += ms; } }
    public void RecordFailure() { lock (_lock) _failureCount++; }

    public Snapshot GetSnapshot()
    {
        lock (_lock)
        {
            return new Snapshot(
                _cacheHits, _cacheMisses, _loadCount, _failureCount,
                _loadCount > 0 ? _totalLoadMs / _loadCount : 0);
        }
    }

    public readonly record struct Snapshot(
        int CacheHits, int CacheMisses, int LoadCount, int FailureCount, double AverageLoadMs);
}
```

The reference uses a lock around metric updates. The metrics are not on the main-thread hot path (only on load), so a simple lock is fine. If you need zero-contention, use `Interlocked.Increment` for the counters and a separate accumulator for the average.

## 8. PlayerLoop subsystem

```csharp
public sealed class AssetPipelineTickSystem
{
    public static event Action OnTick;
    static PlayerLoopSystem _registered;

    [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.SubsystemRegistration)]
    static void AutoRegister()
    {
        // Auto-register on play. Production code may toggle this.
        Register();
    }

    public static void Register()
    {
        if (_registered.type != null) return;
        _registered = new PlayerLoopSystem
        {
            type = typeof(AssetPipelineTickSystem),
            updateDelegate = () => OnTick?.Invoke()
        };
        var loop = PlayerLoop.GetCurrentPlayerLoop();
        var earlyUpdate = FindSubsystem(loop, typeof(EarlyUpdate));
        var subsystems = new List<PlayerLoopSystem>(earlyUpdate.subSystemList ?? Array.Empty<PlayerLoopSystem>());
        subsystems.Add(_registered);
        earlyUpdate.subSystemList = subsystems.ToArray();
        PlayerLoop.SetPlayerLoop(loop);
    }

    public static void Unregister()
    {
        var loop = PlayerLoop.GetCurrentPlayerLoop();
        var earlyUpdate = FindSubsystem(loop, typeof(EarlyUpdate));
        if (earlyUpdate.subSystemList == null) return;
        var subsystems = new List<PlayerLoopSystem>(earlyUpdate.subSystemList);
        subsystems.RemoveAll(s => s.type == typeof(AssetPipelineTickSystem));
        earlyUpdate.subSystemList = subsystems.ToArray();
        PlayerLoop.SetPlayerLoop(loop);
        _registered = default;
    }

    static PlayerLoopSystem FindSubsystem(PlayerLoopSystem root, Type type)
    {
        if (root.type == type) return root;
        if (root.subSystemList == null) return default;
        foreach (var s in root.subSystemList)
        {
            var f = FindSubsystem(s, type);
            if (f.type != null) return f;
        }
        return default;
    }
}
```

The reference uses `[RuntimeInitializeOnLoadMethod]` to auto-register on play. In production, you might gate this behind a feature flag or only register when the AssetPipeline is in use.

## 9. Profiler integration

```csharp
static readonly ProfilerMarker s_loadMarker = new("AssetPipeline.Load");
static readonly ProfilerMarker s_evictMarker = new("AssetPipeline.Evict");

public async Awaitable<T> LoadAsync<T>(string key, CancellationToken ct = default) where T : UnityEngine.Object
{
    using (s_loadMarker.Auto())
    {
        // ...
    }
}
```

The marker shows up in the Profiler window under CPU Usage as `AssetPipeline.Load`. The Auto scope measures the time from when the method enters to when it returns (or throws). This includes the time spent awaiting continuations, which is the interesting number for async code.

## 10. Common bugs in the reference

- **Double-free of CTS**: `Dispose` used to dispose `_internalCts` and then `_linkedCts`, but `_linkedCts` holds a reference to `_internalCts.Token`. Disposing both in the wrong order throws. The fix is to dispose the linked CTS first, then the internal.
- **In-flight table not cleaned up on cancellation**: if the load is cancelled, the `_inFlight` entry stays. The `finally` block handles it. The reference had a bug where the `finally` only ran on the awaiter's continuation, and a cancellation that interrupted before the first await left the entry in. Fix: register the cleanup in the same scope as the add.
- **Cache hit returning a destroyed asset**: if a Unity scene unloads and the asset was a scene object, the cached reference is to a destroyed object. The `is T` check returns false, and the loader falls through to a fresh load. The fix is to check `asset == null` (Unity's overloaded equality, which checks for destroyed).
- **LRU eviction releasing an in-flight asset**: the in-flight table has the only reference. Eviction decrements the refcount, but the asset is still alive because the in-flight load holds it. The fix is to skip eviction for keys present in `_inFlight`.

## 11. What the reference does not solve

- Distributed cache: if your backend has multiple Unity instances serving the same content, you need a distributed LRU. The reference is per-process.
- Persistent cache: the LRU is in-memory. On process restart, it's empty. The reference would benefit from a disk-backed layer using `Addressables.DownloadDependenciesAsync`.
- Thread safety: the reference assumes single-threaded access from the main thread. The lock in `AssetMetrics` is for the snapshot only.
- Bundle resolution: the reference assumes Addressables keys are valid and resolvable. In production, you need bundle fallback for failed downloads.
