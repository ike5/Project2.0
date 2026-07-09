# Module 12: CPU/GPU Profiling in Depth

This module is about the practice of profiling, not the tools. The tools are Profiler, Memory Profiler, Profile Analyzer, Frame Debugger, and RenderDoc. The practice is: pick the right tool, ask the right question, fix the right thing, verify the fix. By the end you will be the person on the team that people bring their "the game is slow" problems to.

## 1. The senior's profiling workflow

A senior profiles every day, not just when something is slow. The workflow:

1. **Establish a baseline**: build the game, profile on the target device, record the metrics. Frame time, draw calls, GC alloc, setpass calls, memory peak.
2. **Diff against baseline**: every change, run the same scene, same actions, compare. A change that adds 2 ms without explanation is a regression.
3. **Profile the worst case**: longest scene, most particles, full inventory, all UI open. Not the empty scene.
4. **Profile on the lowest-spec target device**: not the dev machine. The dev machine is the most powerful hardware the game will ever see.
5. **Capture, don't guesstimate**: if you can't see it in the Profiler, you don't know if it's slow.

The default mistake: profiling on a PC that runs the game at 200 fps and concluding "performance is fine." It is not fine. The lowest-spec device runs at 22 fps. Profile that.

## 2. The Profiler window

The Profiler window (Window > Analysis > Profiler) has modules:
- **CPU Usage**: per-frame timeline of all code that ran. The default view.
- **GPU Usage**: per-frame timeline of GPU work.
- **Memory**: GC allocation, managed heap growth, native memory.
- **Audio**: per-frame audio thread time.
- **Physics**: per-frame physics time.
- **Network**: per-frame NGO traffic (module 9).
- **Rendering**: per-frame rendering work, batches, setpass calls.
- **UI**: per-frame UI rebuild, layout, raycast cost.
- **Loading**: per-frame asset loading, scene load, GC.

In Unity 6 the Profiler is async by default — it does not block the main thread to capture. The cost of profiling is low. You can leave it on.

The Profiler connects to a remote device via `Profiler.enabled = true` and the player connects back. Or use the Android/iOS profiler: build a "Development Build" with "Autoconnect Profiler" checked, attach the device, see frames live.

## 3. The CPU Usage module in depth

The CPU module shows a timeline of the main thread, the render thread, worker threads, and job threads. Each colored bar is a sample.

- **Hierarchy view**: aggregated by call tree. `Player.Update` -> `PlayerMotor.Update` -> `Physics.Raycast`. The deepest call is the bottom of the bar.
- **Raw hierarchy**: no aggregation, just the raw samples. Use for one-off frames.
- **Timeline**: horizontal axis is time, vertical axis is thread. Use for parallelism analysis.

Reading the CPU module:
1. Find the longest bar. That is your bottleneck.
2. Click into it. The call tree shows what was running.
3. The total time of the bar is the total time of that frame on that thread.
4. Frame time = max(main thread, render thread). If the main thread is 8 ms and the render thread is 12 ms, the frame is 12 ms.

The Profiler shows GC.Alloc as yellow icons in the bar. Yellow icon = allocation. If you have a 5 KB allocation per frame in a tight loop, that is 300 KB/min, 18 MB/hour. The GC will eventually trigger, the GC will pause the main thread, the game will hitch.

## 4. ProfilerRecorder API

The Profiler window is for human inspection. The ProfilerRecorder API is for runtime metrics. It is the right tool for production telemetry.

```csharp
using Unity.Profiling;

public static class Profiling
{
    public static readonly ProfilerRecorder MainThreadTimeRecorder =
        ProfilerRecorder.StartNew(ProfilerCategory.Internal, "Main Thread", 60);

    public static readonly ProfilerRecorder GcAllocRecorder =
        ProfilerRecorder.StartNew(ProfilerCategory.Memory, "GC.Alloc", 60);

    public static readonly ProfilerRecorder DrawCallsRecorder =
        ProfilerRecorder.StartNew(ProfilerCategory.Render, "Draw Calls Count", 60);

    public static double LastFrameTimeMs => MainThreadTimeRecorder.LastValue / 1e6;
    public static long LastGcAllocBytes => GcAllocRecorder.LastValue;
    public static long LastDrawCalls => DrawCallsRecorder.LastValue;
}
```

Use it in your telemetry service:
```csharp
void Update()
{
    if (Time.frameCount % 60 == 0) // every 60 frames
    {
        Telemetry.Send("frame_time_ms", Profiling.LastFrameTimeMs);
        Telemetry.Send("gc_alloc_bytes", Profiling.LastGcAllocBytes);
        Telemetry.Send("draw_calls", Profiling.LastDrawCalls);
    }
}
```

The data is the same as the Profiler window, but you ship it to your backend, you graph it, you alert on regressions.

## 5. Custom ProfilerMarker

Add markers to your own code:

```csharp
using Unity.Profiling;

public class CombatSystem
{
    static readonly ProfilerMarker s_updateMarker = new("Combat.Update");
    static readonly ProfilerMarker s_damageCalcMarker = new("Combat.DamageCalc");
    static readonly ProfilerRecorder s_damageCalcRecorder = ProfilerRecorder.StartNew(
        new ProfilerCategory("Combat"), "Combat.DamageCalc", 60);

    public void Update()
    {
        using (s_updateMarker.Auto())
        {
            UpdateUnits();
            using (s_damageCalcMarker.Auto())
            {
                CalculateDamage();
            }
        }
    }
}
```

`using (s_updateMarker.Auto())` automatically times the scope. The marker shows up in the Profiler as `Combat.Update`. The `ProfilerRecorder` lets you read the runtime value without opening the Profiler.

Best practice: one marker per major system, plus markers for hot inner loops. Don't marker every line — the Profiler view becomes noise.

## 6. Frame Debugger

The Frame Debugger (Window > Analysis > Frame Debugger) shows every draw call for the selected frame. Click a draw call, the Game view highlights the geometry. Use it to:

- Find an unexpected draw call ("why is this UI mesh rendered 5 times?").
- Verify shader passes ("did this material switch to the right variant?").
- Debug overdraw ("is this object rendered behind another object?").

The Frame Debugger is the only way to see what the GPU is actually being asked to do. Read the draw call list top-to-bottom. The first calls are usually shadow maps, then opaque geometry, then transparent, then UI.

## 7. RenderDoc integration

RenderDoc is the senior's GPU debugger. It captures a single frame and lets you inspect every draw call, every shader input, every render target. Use it for:

- Shader debugging (why is this not rendering as expected?).
- Render target inspection (what's in the depth buffer at this point?).
- Pipeline state (what blend mode, what depth function, what stencil).

Unity's RenderDoc integration: in Editor, go to the menu, "Capture > RenderDoc." RenderDoc must be installed. The capture button in the Unity Editor's Game view launches RenderDoc with the current frame.

The senior use case: a shader is producing visual artifacts. You can't fix what you can't see. RenderDoc shows you exactly what the GPU received. From there, you fix the shader.

## 8. GPU Usage profiler

The GPU Usage profiler module (Unity 6) shows per-frame GPU work. It runs on the device with a "Development Build" and is non-trivial to capture on every device. For most platforms, RenderDoc or platform-specific tools (Xcode's GPU capture, Android GPU Inspector) are more reliable.

The GPU module shows:
- Render thread time.
- GPU time per draw call (limited support).
- Pipeline state changes.
- Async compute usage.

The senior rule: GPU bottleneck is rare in well-designed games. If your game is slow, it's usually the main thread or the CPU-side render submission. Check the CPU module first. Only go to GPU profiling if the CPU module says the main thread is fast but the frame is still slow.

## 9. Memory Profiler in depth

The Memory Profiler package (`com.unity.memoryprofiler`) is the senior's tool for native memory. It captures a memory snapshot, then you inspect:
- Managed heap objects (size, count, references).
- Native objects (textures, meshes, render textures).
- Asset references (which GameObject references this asset).
- Fragmentation (the gaps between allocations).

A snapshot is a file. Capture on the target device, transfer the file, open in the Memory Profiler window. The package supports snapshot diffing — capture before and after a scene load, diff shows what was added.

```csharp
using UnityEngine.Profiling.Memory.Experimental;

public class MemoryCapture
{
    public static void Capture(string label)
    {
        MemoryProfiler.TakeSnapshot($"{label}.snap", (path, success) =>
        {
            Debug.Log($"snapshot {label}: {path} success={success}");
        });
    }
}
```

Common memory bugs the Memory Profiler finds:
- **Texture duplication**: a texture loaded twice with different references. The Memory Profiler shows two identical 4 MB textures.
- **Asset leaks**: a scene unload didn't release an Addressables bundle. The Memory Profiler shows the bundle is still in memory.
- **Managed heap growth**: objects accumulated without being released. The Memory Profiler shows 200,000 instances of `Waypoint`.
- **Fragmentation**: the native heap is 80 MB but only 30 MB is in use. The Memory Profiler shows the gaps.

## 10. Profile Analyzer

The Profile Analyzer package (`com.unity.profileanalyzer`) is for frame-time analysis across many frames. It loads a Profiler capture and shows:
- Distribution of frame times (median, p95, p99).
- Frame time trends over time.
- Per-system breakdown averaged across frames.
- Comparison of two captures (before/after a change).

The senior use case: a teammate says "I made the AI 2x faster." You run the game for 60 seconds before, 60 seconds after, load both in Profile Analyzer, see the AI bar is 50% shorter, confirm. The frame time distribution shifted from 18 ms median to 14 ms median.

## 11. Single-frame capture vs deep profile

The Profiler has two modes:
- **Live capture**: the Profiler records every frame. The overhead is low (a few percent) but the data is sampled.
- **Deep profile**: every function call is captured, no sampling. The overhead is high (5-10x) but the data is exact.

Use deep profile for finding the exact call stack of a bug. Use live capture for the long-running metrics. Switch between them with the Profiler window's "Deep Profile" toggle.

Deep profile is for short captures (5-10 seconds). Beyond that, the game slows to a crawl and the data is no longer representative.

## 12. Allocation call stacks

The Memory module's "Allocation Call Stacks" view shows where GC.Alloc happened. Enable in the Memory module's "Detailed" mode. The call stack shows the line of code that allocated.

Senior use case: a 2 KB allocation per frame from `string.Format` in the AI system. Find the line. Fix it: use a `StringBuilder` cached on the AI system, or pre-format the string. The allocation goes away.

## 13. Frame time budgets per platform

Frame time budget is the senior's mental model for "is this fast enough?"

| Platform | Target fps | Frame budget |
|----------|-----------|--------------|
| iOS flagships | 60 | 16.6 ms |
| iOS low-end (iPhone 8) | 30 | 33.3 ms |
| Android flagships | 60 | 16.6 ms |
| Android low-end (Pixel 4a) | 30 | 33.3 ms |
| PS5 / Xbox Series X | 60 | 16.6 ms |
| Xbox Series S | 60 | 16.6 ms (or 30 fps mode) |
| Switch | 30 | 33.3 ms |
| Steam Deck | 30-60 | 16.6-33.3 ms |

The budget is the total frame time. Main thread + render thread + GPU must all fit. If main thread is 10 ms, render is 8 ms, GPU is 12 ms, the frame is 12 ms (max), not 30 ms (sum). They run in parallel.

## 14. Target hardware specs

Reference devices for profiling:

- **iPhone SE (2020)**: A13, 3 GB RAM. The lowest iOS you can buy. Targets this for iOS low-end.
- **Pixel 4a**: Snapdragon 730G, 6 GB RAM. The lowest Android worth supporting.
- **PS5**: Zen 2 8-core, RDNA 2 GPU, 16 GB GDDR6. The flagship console.
- **Xbox Series S**: Zen 8-core, RDNA 2 4 TFLOPS, 10 GB GDDR6. The lowest current-gen console. Profile on this.
- **Steam Deck**: Zen 2 4-core, RDNA 2 1.6 TFLOPS, 16 GB LPDDR5. The lowest PC target.

The senior rule: the lowest-spec device is the design target. Don't design on the highest-spec and try to scale down. Design on the lowest and scale up. It's much easier to "make it look better" than to "make it run faster."

## 15. Common pitfalls

- **Profiling on the dev machine**: dev machines are 10x faster than the target. The bottlenecks you find are different from the ones the player sees. Profile on the device.
- **Profiling empty scenes**: empty scenes show 4 ms. Real scenes show 16 ms. Profile the worst case.
- **Profiling in the editor with deep profile**: deep profile in the editor is 5-10x slower than the player build. The numbers don't match. Use a development build.
- **GC.Alloc in Update**: any allocation in Update is a leak. The GC will trigger. The pause will hitch. Find them all.
- **Assuming the Profiler is accurate**: the Profiler adds overhead. The numbers are relative, not absolute. Use the same Profiler settings before/after to compare.
- **Not checking async**: Awaitable continuations may run on a different thread or at a different point in the frame. The Profiler shows them where they resume, not where they were scheduled.
- **Trusting synthetic benchmarks**: a "100,000 unit stress test" that runs at 60 fps doesn't tell you the real game runs at 60 fps. The synthetic test has no UI, no physics, no networking. Real games are not stress tests.

## 16. The profiling checklist

Before any release:

1. **Frame time**: median < budget, p95 < 1.5x budget, p99 < 2x budget.
2. **GC alloc per frame**: < 1 KB.
3. **Draw calls**: < 2000 (mobile) / < 5000 (PC/console).
4. **Setpass calls**: < 250 (mobile) / < 500 (PC/console).
5. **Memory peak**: < 80% of platform budget.
6. **Load time**: < 5 seconds to first scene.
7. **Streaming hitches**: no > 50 ms hitch during gameplay.
8. **Network round-trip**: < 100 ms p95 to server.

If any of these are red, fix before release.

## What to read next

- Module 13: CI build pipeline that runs the profiling suite on every commit.
- Module 9: NGO bandwidth profiling.
- Module 11: device-specific build configuration.
- Module 14: object pooling to eliminate GC alloc.
