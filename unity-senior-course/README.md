# Unity Senior: Production-Grade Game Development 🎮⚡

A hands-on, **senior-level** Unity course for **experienced programmers new to
Unity** (or Unity developers leveling up from mid to senior). Where most Unity
tutorials stop at "it works", this course starts at "it ships, scales, and
survives six months of content updates."

> **Who this is for:** You already know how to program. You can write C# (or
> translate from Java/Kotlin/C++/Swift easily). You want to build a Unity game
> the way a **senior Unity developer at a real studio** would: managing memory
> budgets, profiling the GPU, scaling rendering, shipping to console, and
> reasoning about DOTS vs MonoBehaviour.

---

## Why this course exists

The gap between "made a tutorial game" and "shipped a game" is enormous.
Senior Unity work lives in:

- **Memory budgets.** Consoles and mobile have hard RAM caps; a single bad
  texture import setting can sink a build.
- **CPU/GPU profiling.** Knowing how to read the Profiler, the Frame Debugger,
  and RenderDoc separates people who ship at 60 FPS from people who don't.
- **Data-oriented design.** DOTS, ECS, Burst, Jobs — Unity's answer to the
  problems every engine hits at scale.
- **The asset pipeline.** Addressables, build size, content updates, IL2CPP,
  managed vs native code.
- **Async, threading, and the main thread.** What is and isn't safe in Unity is
  famously subtle. `async`/`await` changed the rules again in Unity 2023+.

This course covers **all of that**, in order, with hands-on labs.

---

## Course shape

```
00  Setup & senior architecture map
01  The Assets/ folder: Scenes, Scripts, Materials, Shaders, Prefabs,
    Settings, Editor, Tests
02  Modern C# in Unity (Span<T>, source generators, modern syntax)
03  Memory model: managed heap, native, unsafe, GC
04  Memory optimization with the Memory Profiler
05  Native containers, Jobs, and Burst
06  DOTS / Entities (ECS) in practice
07  Rendering: URP, HDRP, SRP Batcher, GPU instancing
08  Asset pipeline & Addressables
09  Multiplayer: Netcode for GameObjects & Entities
10  Async, Awaitable, UniTask, threading rules
11  Platform targets: iOS, Android, console, IL2CPP
12  CPU/GPU profiling & frame budgets
13  Build pipeline & CI/CD
14  Senior patterns: pooling, decoupling, save systems
15  Capstone: ship a small production-grade game
```

Each module = short theory + a **guided lab** + an **unguided challenge** +
**reference solutions**. Code lives under `unity-scripts/` and is pasted into
Unity as the lab directs; we never commit `.csproj`, `Library/`, or `Temp/`.

---

## What you should already know

- **Confident in at least one language.** C# preferred; Java/Kotlin/C++/Swift all fine.
- **Basic data structures & Big-O.** GC pressure, boxing, cache locality all matter here.
- **A Mac or PC** that can run the Unity Hub. Unity 2022 LTS or 6.x is the
  target. DOTS/Entities modules use Entities 1.x.

You do **not** need:

- Prior Unity experience. Module 0 installs and orients you.
- Prior game-dev experience. We'll explain engine vocabulary as it comes up.
- A GPU monster. Most labs run on integrated graphics; profiling sections
  mention what to look for on real hardware.

---

## How to use this course

1. **Read the module README top-to-bottom** — it's a working notebook, not a
   reference manual. Read once for context.
2. **Do the lab.** Open Unity, paste the starter, follow the steps. The
   Memory Profiler and Burst sections really do require running the project.
3. **Try the challenge** before reading the solution.
4. **Skim the solutions** even if you solved it — they're written to show the
   *idiomatic senior way*, which may differ from your correct-but-naive
   solution.
5. **Run `VERIFY.md` checks** at the end of each module. If a check fails,
   re-read the relevant section.

See `GLOSSARY.md` for engine jargon, and `VERIFY.md` for the cross-module
verification commands.

---

## Ground rules (the senior way)

These are the rules we hold to throughout the course. They're boring, but
they're why production codebases don't rot.

1. **No allocations in `Update`.** If you `new` something per frame, the GC will
   hitch you in a meeting with a publisher. The Profiler will catch it; you
   will fix it before merge.
2. **No `Find`/`GetComponent` in hot paths.** Cache references in `Awake`.
3. **No `Resources.Load` at runtime** (in production code). Use Addressables.
4. **No `async void` MonoBehaviour methods.** Use Awaitable, UniTask, or
   coroutines — and be precise about lifetimes.
5. **Every system has a budget.** Frame time, draw calls, batched meshes,
   texture pool, audio voices. State the budget; hit it; measure it.
6. **Profile first, optimize second.** Speculation in this domain is
   embarrassingly expensive.

---

## Tools you'll need

- **Unity Hub + Unity 6.x** (or 2022 LTS). Use the **same version** as the
   course so labs behave as written.
- **Visual Studio** (Mac: **Rider** or **VS Code** with the C# Dev Kit).
- **RenderDoc** (free) for GPU inspection.
- **Memory Profiler** package (free, installed in Module 0).
- **Entities** package (free, installed in Module 5).
- A target device if you're doing the platform module (iOS: a spare iPhone or
  TestFlight; Android: any modern device).

---

## What's deliberately out of scope

- **Art, animation, shader authoring** beyond a working understanding. There
  are entire courses on URP/HDRP shader graphs.
- **Sound design.** FMOD, Wwise, and Unity audio are a course of their own.
- **Marketing, store pages, LiveOps.** Important, but not engineering.
- **The C# language itself.** We assume you can already read C#; Module 02
  is about *Unity-specific* modern C# (Span, ref struct, source generators,
  records).

If a module is light on the topic you wanted, that's the shape of the course.
Depth is preferred over breadth at this level.

---

## Reading order

Do the modules in order. The Memory Profiler module assumes you finished the
memory model module. DOTS assumes Jobs/Burst. Capstone assumes everything.

If you've used Unity before but never touched DOTS, do 05 → 06 in that order.
If you've used DOTS but never profiled memory, do 03 → 04 first.

**Module 01 is the one to not skip** even if you "know Unity." It documents
the senior folder convention (`Assets/Scenes/`, `Assets/Scripts/`,
`Assets/Materials/`, etc.), the assembly-definition discipline, the
`M_`/`S_`/`T_` naming prefixes, and the meta-file/gitignore rules that
production codebases live or die by.
