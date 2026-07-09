# Senior Unity Cheatsheets

Quick-reference cards for the senior Unity developer. Print these,
keep them next to your second monitor, glance at them when in doubt.

---

## 1. The four numbers

For any Unity game in production, you should be able to answer these
in under a minute:

| Number | Tool | Senior target (mid-range mobile) |
|--------|------|----------------------------------|
| Total RSS | Memory Profiler Summary | < 1.5 GB |
| Managed heap | Memory Profiler Summary | < 50 MB |
| GC.Alloc per frame | Profiler → Memory | 0 (ideally) |
| Texture pool | Memory Profiler → Textures | < 800 MB |
| Frame time (worst case) | Profiler → CPU | < 16.67 ms (60 FPS) |

## 2. The senior's per-frame budget (60 FPS)

| Cost | Mobile | PC |
|------|--------|----|
| Scripts | < 4 ms | < 6 ms |
| Rendering setup | < 2 ms | < 3 ms |
| SetPass | < 1 ms | < 1 ms |
| GPU | < 8 ms | < 6 ms |
| Slack | ~1.5 ms | ~0.5 ms |

## 3. The five allocation rules

1. **No `new` for reference types in `Update`.**
2. **No `string` concatenation in `Update`.**
3. **No `Find`/`GetComponent`/`Resources.Load` in `Update`.**
4. **No `async void` MonoBehaviour methods.**
5. **No `foreach` over `IEnumerable<T>` in `Update`.**

## 4. The five "before merge" checks

For every PR that touches a hot system:

- [ ] Profiler shows 0 GC.Alloc in the system.
- [ ] Memory Profiler diff is clean.
- [ ] No `Resources.Load` in runtime code.
- [ ] All `NativeArray<T>` are `Dispose`d.
- [ ] Frame time on target device is within budget.

## 5. The texture import cheat sheet

| Texture type | Compression | Max size | Mipmaps |
|--------------|-------------|----------|---------|
| Diffuse (Albedo) | BC7 (PC) / ASTC 6×6 (mobile) | 2048 (PC), 1024 (mobile) | ☑ |
| Normal map | BC5 (PC) / ASTC 5×5 (mobile) | 1024 (PC), 512 (mobile) | ☑ |
| Roughness / Metal / AO | BC7 / ASTC 6×6 | 1024 (PC), 512 (mobile) | ☑ |
| UI | RGBA32 (no mipmaps) | source size | ☐ |
| Mask | BC4 (PC) / ASTC 4×4 (mobile) | 512 | ☑ |

## 6. The platform scripting backend

| Backend | Use for | JIT? |
|---------|---------|------|
| Mono | Editor iteration, dev builds | Yes |
| IL2CPP | iOS, console, release | No (AOT) |

Always ship IL2CPP for iOS; it's the only option.

## 7. The native container lifetime

| Allocator | Lifetime | Use for |
|-----------|----------|---------|
| `Temp` | 1 frame | in-method scratch |
| `TempJob` | 4 frames | job scratch |
| `Persistent` | until you `Dispose()` | long-lived data |

Always `Dispose()` Persistent containers in `OnDestroy`. The leak
detector only fires for Persistent.

## 8. The threading rules

- **Main thread**: touches almost all Unity APIs. `MonoBehaviour.Update`,
  `Awake`, coroutines, Awaitable, the render thread.
- **Job threads**: IJob, IJobParallelFor, IJobFor, IJobEntity, Burst.
- **Thread pool**: `Task.Run`, UniTask `Taskpool` mode. **Don't touch
  Unity APIs from here.**
- **Async/await**: in Unity 6, `Awaitable` resumes on the main thread
  by default. `Task` does not.

## 9. The SRP Batcher rules

- All URP/Lit materials are SRP-Batcher compatible by default.
- Custom shaders must use `CBUFFER_START(UnityPerMaterial)`.
- Per-instance variation goes through `MaterialPropertyBlock`, not
  `material.color = ...`.
- The `material` getter creates a new instance. Use `sharedMaterial`
  for read-only.

## 10. The Addressables lifecycle

```
LoadAssetAsync   →  ref count = N
                  →  asset is loaded

Release          →  ref count = N-1
                  →  if N-1 == 0, asset is unloaded
```

**Track your handles. Release in pairs.** Forgetting to release
is the senior Addressables bug.

## 11. The Assembly Definition defaults

- **One root asmdef** in `Assets/Scripts/` for all runtime code.
- **One `Editor` asmdef per feature folder** for editor tools.
- **One `Test` asmdef per test context** (EditMode, PlayMode).
- **`Test Assemblies: ☑`** in the test asmdefs.

## 12. The naming prefixes (community convention)

| Prefix | Means |
|--------|-------|
| `M_` | Material |
| `S_` | Shader |
| `T_` | Texture |
| `A_` | Animation clip |
| `AC_` | Animator Controller |
| `SFX_` | Sound effect |
| `MUS_` | Music |

## 13. The folder layout

```
Assets/
├── Scenes/        # .unity
├── Scripts/       # runtime C#
├── Editor/        # editor-only C# (case-sensitive)
├── Materials/     # .mat
├── Shaders/       # .shader, .shadergraph, .hlsl
├── Textures/      # imported images
├── Meshes/        # imported models
├── Animations/    # .anim, .controller
├── Audio/         # imported audio
├── Prefabs/       # reusable GameObject templates
├── UI/            # UGUI / UI Toolkit
├── ScriptableObjects/  # data assets
├── Plugins/       # third-party DLLs
├── StreamingAssets/    # verbatim copies
├── Tests/         # EditMode + PlayMode
├── Settings/      # URP renderer assets, input actions
└── AddressableAssetsData/  # Addressables catalog
```

## 14. The .gitignore essentials

```
/Library/          # generated
/Temp/             # generated
/Logs/             # generated
/UserSettings/     # per-user
/Build/            # build output
/obj/              # build intermediates
/MemoryCaptures/   # Memory Profiler snapshots
*.csproj           # generated
*.sln              # generated
.vs/               # VS
.idea/             # Rider
.DS_Store          # macOS
```

## 15. The senior's profiler-first reflex

When something is slow:

1. Open Profiler.
2. Find the biggest bar.
3. Click into it.
4. Read the call stack.
5. Fix the line.
6. Re-profile.

Speculation in performance is wrong 50% of the time.
Profiling is wrong 5% of the time. The senior bets on profiling.
