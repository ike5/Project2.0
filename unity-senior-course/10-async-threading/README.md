# Module 10: Async, Awaitable, UniTask, Threading

This module covers the asynchronous programming model in Unity 6: the new `Awaitable` type, the relationship with `System.Threading.Tasks.Task`, the coroutine system, the C# job system, and the PlayerLoop. The senior patterns are not academic — they are the difference between a game that ships and a game that freezes on the first async exception.

## 1. The four async primitives in Unity

There are four ways to express "do this later" in Unity 6. Each has tradeoffs.

| Type | Allocation | Cancel | PlayerLoop integration | Use for |
|------|-----------|--------|------------------------|---------|
| `Coroutine` (IEnumerator) | small box | manual | implicit (yield returns) | legacy code, MonoBehaviour-coupled flows |
| `async Task` | high (state machine) | via CTS | manual (TaskScheduler) | interop with C# libraries, server code |
| `async UniTask` (UniTask package) | zero-alloc | built-in | first-class | hot-path gameplay code |
| `Awaitable` (Unity 6 native) | zero-alloc | built-in | first-class | Unity-native, no third-party dep |

**Senior default in Unity 6: use `Awaitable`.** It is the native type, the PlayerLoop integration is built-in, the cancellation is built-in, and the allocation profile is zero-alloc. The only reason to use UniTask in 2026 is if you have an existing UniTask codebase. The only reason to use Task is interop with C# libraries that require it (HttpClient, gRPC, etc.).

## 2. Coroutines: when they still make sense

Coroutines are fine for legacy code and for MonoBehaviour-coupled state machines. They run on the main thread, integrated with the PlayerLoop's CoroutineUpdate stage. They have a few real advantages over async:

- Trivial cancellation: `StopCoroutine(handle)`. With async you need a CancellationToken.
- They serialize MonoBehaviour state with the coroutine tick.
- They are easier to read for designers.

Disadvantages:
- One return type: `IEnumerator`. You cannot `return` a value.
- Nested coroutines are awkward (yield on an IEnumerator).
- No first-class exception handling.
- They do not run if the MonoBehaviour is disabled.

Pattern: use coroutines for simple fire-and-forget sequences on a MonoBehaviour (camera shake, fade-in). Use Awaitable for anything that crosses a frame, awaits a `Task`, or composes with cancellation.

## 3. async Task: the interop layer

`System.Threading.Tasks.Task` is fine when you are calling into C# libraries. Unity's main-thread rule still applies: a `Task` returned by an async method that was *not* awaited will run on whatever thread the continuation scheduled on. Unity does not install a custom TaskScheduler. If you call `await Task.Run(...)` on the main thread, the continuation resumes on a thread pool thread by default. You must `await` it and then explicitly switch back.

```csharp
async Awaitable<Texture2D> LoadTextureAsync(string path)
{
    // runs on thread pool
    var bytes = await Task.Run(() => File.ReadAllBytes(path));

    // back on main thread automatically with Awaitable
    var tex = new Texture2D(2, 2);
    tex.LoadImage(bytes);
    return tex;
}
```

Awaitable captures the UnitySynchronizationContext and resumes on the main thread by default. Task does not.

## 4. UniTask: the third-party gold standard

UniTask predates Awaitable. It is a third-party package (`com.cysharp.unitask`) that provides a value-type `UniTask` with zero allocations, PlayerLoop integration, cancellation, and a rich set of helpers. It is the de facto standard for async gameplay code in Unity 2020-2024.

In Unity 6, Awaitable covers the core use cases and the UniTask team has shifted toward being a thin compatibility layer on top of `ValueTask`. New code in 2026 should use `Awaitable`. Existing UniTask codebases can keep using UniTask — the API is similar.

## 5. Awaitable: the Unity 6 native type

`UnityEngine.Awaitable` is a struct, not a class. It is zero-alloc. The compiler generates a state machine for `async Awaitable` methods the same way it does for `async Task`, but the state machine is more efficient.

```csharp
async Awaitable FadeOutAsync(CanvasGroup group, float duration)
{
    var t = 0f;
    while (t < duration)
    {
        t += Time.deltaTime;
        group.alpha = 1f - t / duration;
        await Awaitable.NextFrameAsync();
    }
    group.alpha = 0f;
}
```

`Awaitable` cannot be `await`ed outside an async method or a coroutine — it is a one-shot, not a `Task`. There is no `Awaitable.RunSynchronously` (use `GetAwaiter().GetResult()` carefully — it can deadlock on the main thread).

The pattern for fire-and-forget with cancellation:

```csharp
public async Awaitable RunAsync(CancellationToken ct)
{
    try
    {
        await LongOperation(ct);
    }
    catch (OperationCanceledException) { }
}
```

## 6. Cancellation: everywhere, always

Senior rule: every async method that can be cancelled takes a `CancellationToken`. Every long-running async method uses the token to abort.

```csharp
async Awaitable LoadSceneAsync(string sceneName, CancellationToken ct)
{
    var op = SceneManager.LoadSceneAsync(sceneName);
    while (!op.isDone)
    {
        if (ct.IsCancellationRequested) yield break; // or throw
        await Awaitable.NextFrameAsync(ct);
    }
}
```

Cancellation tokens come from:
- `destroyCancellationToken` on MonoBehaviour (auto-cancels on destroy).
- `Application.exitCancellationToken` (fires on app exit).
- A long-lived token stored on a service.
- A linked token combining multiple sources.

```csharp
async Awaitable RunPlayerLoopAsync(CancellationToken ct)
{
    while (!ct.IsCancellationRequested)
    {
        Update();
        await Awaitable.NextFrameAsync(ct);
    }
}
```

Never `async void` in Unity 6. `async void` methods have no task to await on, exceptions are routed to the SynchronizationContext, and the method cannot be cancelled. The only legitimate use is event handlers (button click) where the C# event pattern requires `void`. Even there, prefer a wrapper:

```csharp
void OnButtonClick() => _ = OnButtonClickAsync();
async Awaitable OnButtonClickAsync() { /* ... */ }
```

The `_ =` discard signals "I know this is fire-and-forget" to the reader.

## 7. PlayerLoop integration

Unity's main loop is a list of subsystems (PreUpdate, Update, PostUpdate, PreLateUpdate, LateUpdate, PostLateUpdate, etc.). When you `await Awaitable.NextFrameAsync()`, Awaitable schedules a continuation on the Update stage. You can target any stage:

```csharp
await Awaitable.NextFrameAsync();             // next Update
await Awaitable.EndOfFrameAsync();            // after rendering, before next frame
await Awaitable.FixedUpdateAsync();           // next FixedUpdate
await Awaitable.WaitForSecondsAsync(0.5f);    // delay, drift-free
```

`WaitForSecondsAsync` and `EndOfFrameAsync` are the replacements for `WaitForSeconds` and `WaitForEndOfFrame`. They have the same semantics but with cancellation and zero allocation.

You can insert a custom subsystem into the PlayerLoop via `PlayerLoopSystem`:

```csharp
var loop = PlayerLoop.GetCurrentPlayerLoop();
var mySystem = new PlayerLoopSystem
{
    type = typeof(MyUpdateSystem),
    updateDelegate = MyUpdateSystem.Update
};
loop.subSystemList[0].subSystemList.Add(mySystem);
PlayerLoop.SetPlayerLoop(loop);
```

This is how you write systems that tick at a specific point in the frame, decoupled from MonoBehaviour Update.

## 8. SynchronizationContext in Unity

Unity's main thread installs a `UnitySynchronizationContext`. Continuations scheduled on the main thread (via `await` from Awaitable) resume on the main thread. This is automatic. You do not need to write `await UnityMainThreadDispatcher.RunOnMainThread(...)` — that pattern is from before Awaitable.

If you are calling into `Task` code, the continuation does not automatically resume on the main thread. You must `ConfigureAwait(true)` and ensure the SynchronizationContext is captured. Or you switch back manually:

```csharp
await Task.Run(...).ConfigureAwait(true); // capture main thread
```

In Unity 6, prefer Awaitable. The Task pattern is a workaround.

## 9. The job system: when async isn't enough

The C# job system (`Unity.Jobs`) runs on worker threads with Burst-compiled code. Use it for:
- Heavy data processing (mesh generation, audio DSP, pathfinding).
- Anything that can be expressed as `IJob`, `IJobParallelFor`, `IJobEntity` (DOTS).
- Work that you want off the main thread for a known duration.

Jobs do not await. You schedule them, the worker threads run them, you call `handle.Complete()` later (which blocks the main thread until the job finishes — do not call this in Update if the job is long; use a job system fence pattern).

The hybrid pattern: spawn a long job, check `handle.IsCompleted` in Update each frame, run the next pipeline stage when done. This keeps the main thread free.

```csharp
JobHandle SchedulePipeline(NativeArray<float> data)
{
    var job = new ProcessJob { data = data };
    return job.Schedule(data.Length, 64);
}
```

Module 6 covered Burst. The job system + Burst is the right tool for compute-bound work. Async is the right tool for I/O-bound work.

## 10. The thread pool

`Task.Run` and `ThreadPool.QueueUserWorkItem` schedule on the .NET thread pool. The pool grows up to a CPU count and shrinks lazily. It is fine for I/O (file reads, HTTP), bad for per-frame work.

The senior rule: the main thread owns the simulation. The thread pool owns I/O. The job system owns compute. Crossing the boundary is fine if you do it deliberately (and Awaitable + the job system handle the resume for you).

Common bug: calling `Task.Run` from a hot per-frame Update to "offload" a small piece of work. The cost of scheduling a task dwarfs the work. The main thread is faster for short tasks.

## 11. The main thread rule

The main thread is the only thread that can touch:
- UnityEngine APIs (Transform, GameObject, Component, etc.).
- The scene graph.
- The PlayerLoop.

Cross-thread access throws or corrupts. The exception is `UnityEngine.Volume` and a few other thread-safe APIs. The full list is in the Unity docs.

Pattern: any thread-pool callback must marshal back to the main thread before touching UnityEngine. With Awaitable, this is automatic. With Task, you must explicitly do it.

## 12. Awaitable.NextFrameAsync timing

`Awaitable.NextFrameAsync()` resumes at the start of the next Update. If you call it inside Update, the continuation runs at the start of the *following* Update, not the same one. This is one frame of latency. It is not a bug; it is the contract.

For finer timing, use `Awaitable.EndOfFrameAsync()` (resumes after rendering), or schedule into a custom PlayerLoop subsystem.

## 13. Awaitable in UnityEvents

UnityEvent (the inspector-bound event) does not support `async Awaitable` directly. If you bind a button to a method, the method must be `void` (or with a return type the inspector understands). The pattern:

```csharp
[SerializeField] Button button;

void Awake() => button.onClick.AddListener(OnButtonClick);

void OnButtonClick()
{
    _ = OnButtonClickAsync();
}

async Awaitable OnButtonClickAsync()
{
    await Awaitable.WaitForSecondsAsync(0.2f);
    DoStuff();
}
```

## 14. Async lifetimes

The senior pattern is **lifetime ownership**. Every async operation has an owner; the owner is responsible for cancellation when its lifetime ends.

For MonoBehaviour:

```csharp
async Awaitable RunAsync()
{
    try
    {
        await Awaitable.NextFrameAsync(destroyCancellationToken);
        // ...
    }
    catch (OperationCanceledException) { /* expected on destroy */ }
}
```

`destroyCancellationToken` is the cancellation token that fires when the MonoBehaviour is destroyed. Use it for any async method owned by a MonoBehaviour.

For services:

```csharp
public class AssetService
{
    readonly CancellationTokenSource _cts = new();
    public CancellationToken Token => _cts.Token;

    public void Dispose() => _cts.Cancel();

    public async Awaitable LoadAsync() { /* ... */ }
}
```

Dispose cancels everything. Subscribers to the token check `ct.IsCancellationRequested` and bail.

## 15. Awaitable vs Task performance

`Awaitable` is a struct, no allocation. `Task` allocates a Task object per async method invocation. In a hot path called 60 times per second, Task allocates 60 objects per second, ~6 KB of GC pressure per minute. Awaitable allocates zero.

```csharp
async Task DoStuffTask() { await Task.Yield(); }
async Awaitable DoStuffAwaitable() { await Awaitable.NextFrameAsync(); }
```

In a benchmark, Awaitable is ~10x faster to allocate and slightly faster to resume, because it integrates directly with the PlayerLoop instead of going through the SynchronizationContext.

## 16. UniTask patterns that map to Awaitable

If you have UniTask code, the Awaitable equivalents:

| UniTask | Awaitable |
|---------|-----------|
| `UniTask.NextFrame()` | `Awaitable.NextFrameAsync()` |
| `UniTask.Delay(ms)` | `Awaitable.WaitForSecondsAsync(s)` |
| `UniTask.Yield()` | `Awaitable.NextFrameAsync()` |
| `UniTask.WaitForEndOfFrame()` | `Awaitable.EndOfFrameAsync()` |
| `UniTask.SwitchToMainThread()` | (no-op, Awaitable is main-thread by default) |
| `UniTaskCompletionSource<T>` | `AwaitableCompletionSource<T>` (Unity 6.1+) |

## 17. The senior rules

1. Default to `Awaitable` in Unity 6. Use Task for interop only.
2. Every async method takes a `CancellationToken`. Always.
3. Never `async void` (except in event handlers, with a discard assignment wrapper).
4. Use `destroyCancellationToken` on MonoBehaviours. Cancel on destroy.
5. Main thread owns the scene. Thread pool owns I/O. Job system owns compute. Pick the right tool.
6. Never call `GetAwaiter().GetResult()` on the main thread. Deadlock risk.
7. Profiler-marker your async continuations. Add a `ProfilerMarker` around long async methods to see their cost.
8. Cancellation tokens are not optional. They are the difference between a clean shutdown and a hung process on app exit.

## 18. Common pitfalls

- `async void OnEnable() { ... }`: exceptions in the body crash the app silently. Use `async Awaitable OnEnable()` and discard the result.
- `await someTask` with no ConfigureAwait inside a Unity callback: continuation runs on thread pool, touches Transform, throws.
- Forgetting to dispose a CancellationTokenSource. The token lives forever, the registered callbacks hold references.
- `Task.Run` for "offloading" a 10-microsecond task: the schedule cost is more than the work.
- `WaitForSeconds` in a coroutine for UI animations: works, but `Awaitable.WaitForSecondsAsync` with cancellation is better.
- Awaiting `Awaitable.NextFrameAsync()` in a coroutine: does not work. Coroutines can only yield specific types.

## What to read next

- Module 11: IL2CPP strips async state machines, debug symbols are required to read stack traces.
- Module 12: profile async continuation cost with the Profiler.
- Module 14: command pattern uses async lifetimes for undo/redo.
- Module 9: NGO host startup with Awaitable.
