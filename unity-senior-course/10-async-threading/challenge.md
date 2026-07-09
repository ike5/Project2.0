# Challenge 10: Production-Grade Async System for Asset Pipeline

**Time**: 3 hours
**Goal**: Build an asset loading service that scales to a real game: preloading, streaming, cancellation, hot-reload, and tight integration with the PlayerLoop. The deliverable is production code, not a demo.

## Scope

An `AssetPipeline` service that:
1. Loads Addressable assets by key with retry, exponential backoff, and timeout.
2. Caches loaded assets in an LRU cache.
3. Preloads assets in batches during loading screens.
4. Streams assets in/out as the player moves through the world (zone-based).
5. Caches in-flight loads so two requests for the same key share one Addressables call.
6. Cancels everything on app exit, scene unload, or service dispose.
7. Reports metrics: load count, cache hits, average load time, failure count.

## Architecture

```
AssetPipeline (singleton service)
  ├── LoadAsync<T>(key) -> cached in-flight + LRU
  ├── PreloadBatchAsync(keys) -> group of LoadAsync
  ├── StreamIn(zone) -> load all keys in zone
  ├── StreamOut(zone) -> release all keys in zone
  ├── PreloadWithBudgetAsync(keys, ms) -> time-bounded preload
  └── Dispose() -> cancel all
```

Use `Awaitable` (Unity 6) for all async methods. `CancellationToken` on every public method. `destroyCancellationToken` for MonoBehaviour-owned services.

## Implementation requirements

### 1. In-flight deduplication

If two callers ask for the same key, share one Addressables handle:

```csharp
readonly Dictionary<string, Task<Texture2D>> _inFlight = new();

public async Awaitable<Texture2D> LoadAsync(string key, CancellationToken ct = default)
{
    if (_cache.TryGetValue(key, out var cached)) return cached;
    if (_inFlight.TryGetValue(key, out var task)) return await task; // share

    var t = Addressables.LoadAssetAsync<Texture2D>(key).Task;
    _inFlight[key] = t;
    try
    {
        var result = await t.WaitAsync(TimeSpan.FromSeconds(10), ct);
        _cache[key] = result;
        return result;
    }
    finally
    {
        _inFlight.Remove(key);
    }
}
```

### 2. LRU cache

Bounded cache. Evict least-recently-used. LRU thread-safety: all access from main thread, so no lock needed.

```csharp
readonly LinkedList<string> _lru = new();
readonly Dictionary<string, LinkedListNode<string>> _nodes = new();
const int MaxEntries = 256;

void Touch(string key)
{
    if (_nodes.TryGetValue(key, out var node))
    {
        _lru.Remove(node);
        _lru.AddFirst(node);
    }
    else
    {
        var n = _lru.AddFirst(key);
        _nodes[key] = n;
    }
    if (_lru.Count > MaxEntries) EvictOldest();
}

void EvictOldest()
{
    var oldest = _lru.Last;
    if (oldest == null) return;
    _lru.RemoveLast();
    _nodes.Remove(oldest.Value);
    // release from Addressables
    if (_cache.TryGetValue(oldest.Value, out var handle))
    {
        Addressables.Release(handle);
        _cache.Remove(oldest.Value);
    }
}
```

### 3. Retry with exponential backoff

```csharp
public async Awaitable<T> LoadWithRetryAsync<T>(string key, int maxAttempts = 3, CancellationToken ct = default)
{
    var delay = 100;
    for (int attempt = 1; attempt <= maxAttempts; attempt++)
    {
        try
        {
            return await LoadAsync<T>(key, ct);
        }
        catch (Exception ex) when (attempt < maxAttempts)
        {
            Debug.LogWarning($"load {key} attempt {attempt} failed: {ex.Message}");
            await Awaitable.WaitForSecondsAsync(delay / 1000f, ct);
            delay = Math.Min(delay * 2, 5000);
        }
    }
    return await LoadAsync<T>(key, ct); // last attempt
}
```

### 4. Time-bounded preload

The loading screen gives you N milliseconds. Load as many assets as fit, defer the rest to background.

```csharp
public async Awaitable<int> PreloadWithBudgetAsync(IEnumerable<string> keys, int budgetMs, CancellationToken ct = default)
{
    var sw = Stopwatch.StartNew();
    int loaded = 0;
    foreach (var key in keys)
    {
        if (sw.ElapsedMilliseconds > budgetMs) break;
        await LoadAsync<UnityEngine.Object>(key, ct);
        loaded++;
    }
    return loaded;
}
```

### 5. Zone-based streaming

```csharp
public sealed class AssetZone
{
    public string Name;
    public string[] Keys;
}

readonly Dictionary<string, AssetZone> _zones = new();

public async Awaitable StreamInAsync(string zone, CancellationToken ct = default)
{
    if (!_zones.TryGetValue(zone, out var z)) return;
    foreach (var key in z.Keys) await LoadAsync<UnityEngine.Object>(key, ct);
}

public void StreamOut(string zone)
{
    if (!_zones.TryGetValue(zone, out var z)) return;
    foreach (var key in z.Keys) Release(key);
}
```

### 6. Metrics

```csharp
public struct AssetMetrics
{
    public int CacheHits;
    public int CacheMisses;
    public int LoadCount;
    public int FailureCount;
    public double AverageLoadMs;
}
```

Increment counters at each touch point. Expose a `GetMetrics()` method for telemetry.

### 7. Cancellation

- `Dispose()` cancels the service's internal CTS. All in-flight loads throw `OperationCanceledException` at the next `await`.
- `Application.exitCancellationToken` cancels on app exit.
- `destroyCancellationToken` cancels when the MonoBehaviour owner is destroyed.

```csharp
public sealed class AssetPipeline : IDisposable
{
    readonly CancellationTokenSource _internalCts = new();
    CancellationTokenSource _linkedCts;

    public AssetPipeline(CancellationToken externalToken = default)
    {
        if (externalToken != default)
            _linkedCts = CancellationTokenSource.CreateLinkedTokenSource(externalToken, _internalCts.Token);
    }

    public CancellationToken Token => (_linkedCts ?? _internalCts).Token;

    public void Dispose()
    {
        _internalCts.Cancel();
        _internalCts.Dispose();
        _linkedCts?.Dispose();
    }
}
```

## PlayerLoop integration

Register a custom subsystem in the PlayerLoop that ticks the pipeline's "auto-release" logic — assets not touched in N seconds get evicted. This runs every frame, decoupled from any MonoBehaviour.

## Out of scope

- A real Addressables build setup. Use a stub `IAssetProvider` interface and an in-memory implementation that simulates `WaitForSecondsAsync(0.1f)`.
- Multi-threaded asset loading. Keep the service on the main thread.
- Persistent cache (PlayerPrefs / disk). The LRU is in-memory only.

## Deliverables

1. `AssetPipeline.cs`, the service.
2. `AssetMetrics.cs`, the metrics struct and reporting.
3. `PlayerLoopTickSystem.cs`, the custom PlayerLoop subsystem.
4. A test scene `AssetPipelineTest` that exercises:
   - 100 loads of the same key (deduplication).
   - 1000 loads of unique keys (LRU eviction).
   - Preload with 50 ms budget (only some load).
   - Disposal mid-load (cancellation, no leaked handles).
5. A short note on async lifetime ownership in `NOTES.md`.

## Acceptance criteria

| Criterion | Pass |
|-----------|------|
| In-flight deduplication works | required |
| LRU evicts at capacity | required |
| Retry succeeds on second attempt | required |
| Budget preload stops at the time limit | required |
| StreamIn/StreamOut manages zone assets | required |
| Disposal cancels in-flight loads | required |
| Metrics report correct counts | required |
| PlayerLoop subsystem ticks every frame | required |
| All async methods accept CancellationToken | required |
| Zero `async void` methods | required |

## Grading rubric

- **Async lifetime correctness (30%)**: cancellation is wired everywhere, no leaks.
- **LRU + dedup (25%)**: behavior is right under stress.
- **Retry + budget (20%)**: edge cases handled.
- **PlayerLoop integration (15%)**: subsystem registered, runs, deregistered cleanly.
- **Code quality (10%)**: SOLID-ish, no globals, metrics threaded through.

## Senior notes

Cancellation is not optional. A real game has hundreds of assets in flight at any moment. If you leak one, you leak the whole game. The `try/finally` in `LoadAsync` is the most important five lines in this challenge. Miss them and your service holds a reference to a destroyed scene's assets.

`async void` is the silent killer. Every button click, every UnityEvent, every event handler: if you wrote `async void`, fix it. The exception that escapes is logged to the console with no stack trace because the SynchronizationContext is dead by the time the exception fires. You'll spend a day debugging a feature that "sometimes throws NullReferenceException" before you realize it's the `async void` event handler you wrote three weeks ago.

Do not call `Addressables.LoadAssetAsync` more than once for the same key. Even if your cache hit rate is 99%, the 1% miss is enough to double your load time in stress tests. The in-flight dedup table is the safety net.

Do not use `Task.Run` to "offload" Addressables loads. Addressables already does its work off the main thread internally. Your `Task.Run` is double-bookkeeping with worse cache locality.

Do not store the `AsyncOperationHandle` in a way that survives a domain reload without re-warming. After a script reload in the editor, the handles are invalid. Re-resolve them in `OnAfterDeserialize` or accept that the cache is empty after a reload.

The PlayerLoop subsystem you register must unregister on dispose. Otherwise the static delegate holds a reference and your service leaks. The pattern: store the registered `PlayerLoopSystem` as a field, unregister in `Dispose`.

The metrics are not a debug tool. They are a production feature. Wire them to your telemetry (Firebase, Unity Cloud Diagnostics, or your own backend). When your load time regresses by 10 ms, you need to know which asset caused it.

Ship it.
