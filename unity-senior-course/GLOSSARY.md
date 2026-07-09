# Glossary

Senior Unity work is full of jargon that means something specific. Pin these
down before the modules lean on them.

## Engine & editor

- **Asset** — Anything stored in the `Assets/` folder. Imported into a form
  the engine can use.
- **Prefab** — A serialized GameObject template. The "class instance" of
  the editor.
- **Scene** — A serialized hierarchy of GameObjects + components. The "level"
  in casual speech.
- **Component** — A `MonoBehaviour` (or built-in like `Transform`) attached
  to a GameObject. Unity's "composition over inheritance" answer.
- **GameObject** — A bag of components. Almost never subclassed.
- **Project Settings** — The editor's "config file", in 27+ sub-tabs.
- **Package** — A NuGet-style dependency, declared in `Packages/manifest.json`.
  Unity ships "package manager" packages like URP, Entities, Profiler.
- **ScriptableObject** — A serializable data asset, not a behaviour. The
  "data-only prefab".
- **YAML** — Unity's serialization format for scenes, prefabs, and most
  assets. Hand-edited often; merge-conflict-prone.

## Runtime model

- **MonoBehaviour** — The base class for behaviour components. Has lifecycle
  hooks (`Awake`, `OnEnable`, `Start`, `Update`, `FixedUpdate`, `LateUpdate`,
  `OnDisable`, `OnDestroy`).
- **Update loop** — The order Unity ticks components each frame.
  `FixedUpdate` → physics → `Update` → coroutines → `LateUpdate` → render.
- **Time.deltaTime** — Seconds since last frame, for frame-rate-independent
  motion.
- **Time.unscaledDeltaTime** — As above, ignoring `Time.timeScale`. Use for
  UI animation; *not* for gameplay.
- **Main thread** — The single thread that touches most Unity APIs. Touch
  almost anything from a worker thread → crash, undefined behaviour, or
  silent corruption.
- **Domain Reload** — Recompiling C# while in Play mode. Disable in
  Project Settings → Editor → "Enter Play Mode Settings" for fast iteration.

## Rendering

- **SRP (Scriptable Render Pipeline)** — Unity's modern, code-driven rendering.
  The two flavors are URP and HDRP.
- **URP (Universal Render Pipeline)** — The default, mobile-to-high-end-PC
  pipeline. The right answer most of the time.
- **HDRP (High Definition Render Pipeline)** — PC/console only. Heavy on
  lighting features.
- **SRP Batcher** — A batching path that *combines* many small draw calls
  into a few large ones, by binding uniform buffers per material. The reason
  materials and shader properties matter for CPU.
- **GPU Instancing** — Drawing N copies of the same mesh in one draw call
  with per-instance data. Good for grass, bullets, particles.
- **Draw call** — A single `DrawMesh*` issued to the GPU. CPU-side cost.
  Reduce them; do not chase zero.
- **SetPass** — A shader-pass binding change. Often the real CPU bottleneck.
- **Overdraw** — The same pixel being shaded multiple times. Look at the
  Rendering Debugger.
- **LOD (Level of Detail)** — Swap a high-poly mesh for a low-poly one at
  distance. The single biggest frame-time knob in 3D games.
- **Mipmap** — Pre-shrunk texture versions. Trade memory for sampling speed
  and fewer aliasing artifacts.
- **Texture pool** — The runtime memory set aside for textures. The
  dominant line item on most Unity games.

## Data-oriented

- **DOTS (Data-Oriented Technology Stack)** — Unity's data-oriented answer
  to the "10,000 enemies" problem. Composed of Entities, Jobs, Burst, and
  Mathematics.
- **ECS (Entity Component System)** — The DOTS architecture: data on
  components, logic in systems, no GameObjects.
- **Job** — A unit of work you can run on a worker thread. Comes with
  safety system; don't disable it.
- **Burst** — A compiler that turns IL into highly optimized native code.
  Mandatory for hot DOTS code.
- **IJob** — A single unit. **IJobParallelFor** — N units in parallel.
  **IJobEntity** — A job that runs per matching entity.
- **NativeArray / NativeList / NativeHashMap** — Native (unmanaged) memory
  containers. You own disposal.
- **Chunk** — A 16 KB block of components in ECS. The unit of cache
  locality. The reason you avoid `Entity` references.
- **World** — A complete ECS simulation. You can run more than one.

## Memory

- **Managed heap** — Where C# `class` instances live. Garbage-collected.
  Allocations here are slow and trigger GC.
- **GC (garbage collector)** — Mono's Boehm-style collector. Pauses the
  main thread during collections; on mobile, those pauses are visible
  hitches.
- **Gen 0 / 1 / 2** — Generations. Gen 0 is the most-recently-allocated and
  cheapest to collect. Surviving promotes. Most per-frame allocations die
  in Gen 0, so most Gen 0 collections are cheap. The bad ones are Gen 2.
- **Allocation** — `new` for reference types, boxing a value type, some
  array operations, string concatenation.
- **Boxing** — Wrapping a value type in a reference (e.g. `object x = 5;`
  or `string.Concat(5)`). It allocates. Avoid in hot paths.
- **Native memory** — Memory outside the managed heap, allocated via Unity
  collections or `UnsafeUtility.Malloc`. No GC; you dispose.
- **Profiler** — The runtime tool, in Editor. Shows CPU, GPU, memory,
  rendering, audio.
- **Memory Profiler** — A separate package, captures a snapshot of
  managed + native heap. Use this for "where is my RAM going".

## Build & ship

- **IL2CPP** — The AOT C++ compiler. Required for iOS, console. Slower to
  build, no JIT, easier to reverse-engineer.
- **Mono** — The older scripting backend. JIT-compiled, but you can't ship
  to iOS with it.
- **Addressables** — The asset loading system. Asynchronous, content-update
  friendly, label-driven.
- **Build size** — The APK/IPA/EXE size, dominated by textures and code
  stripping. The two things you control most are texture import settings
  and managed code stripping.
- **Managed code stripping** — Removing unused managed code from the
  build. Aggressive stripping can break reflection-based code. **The
  number one cause of "works in editor, crashes on device"**.
- **Build report** — A post-build JSON. Read it.
- **Player Settings** — The ScriptingBackend, Api Compatibility Level,
  etc. Per-platform.

## Multiplayer

- **Server / Host / Client** — Netcode topologies. Server has authority;
  host is a server that also plays.
- **RPC** — Remote Procedure Call. The "call this on the other side" primitive.
- **NetworkVariable** — A replicated piece of state, server-write/client-read
  by default.
- **NetworkBehaviour** — Like `MonoBehaviour`, but on the network. Most of
  the rules of MonoBehaviour apply plus networking.
- **NGO (Netcode for GameObjects)** — Unity's higher-level netcode, built
  on `UnityTransport`.
- **NFE (Netcode for Entities)** — The DOTS-native netcode. Predicates
  replication on component values, scales better.

## Misc

- **Awaitable** — Unity 2023+'s `async` for engine code. Replaces
  coroutines for most use cases.
- **UniTask** — A popular community package. Allocation-free `Task`
  replacement, the gold standard until Awaitable stabilized.
- **Span<T> / ReadOnlySpan<T>** — A stack-allocated view over contiguous
  memory. No allocations, no copying.
- **Source generator** — A C# compile-time code generator. Unity 6 uses
  them extensively (`[BurstCompile]`, `[CreateProperty]`, etc.).
- **PlayMode test / EditMode test** — Unity Test Framework's two test
  contexts.
