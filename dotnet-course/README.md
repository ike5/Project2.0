# .NET: From C# to App Support & Unity 🎮🛠️

A hands-on, local-first course that takes an **experienced programmer who's new to
C#** all the way to (1) confidently **supporting and operating real .NET
applications** and (2) **building Unity games** — entirely on your Mac, for free.

> **Who this is for:** You already know how to program in *some* language. You want
> practical .NET skills for an **application-support** role, and you want to **make
> Unity games**. This course fast-tracks the C# language, then goes deep on the
> real-world support stack and a substantial Unity track.

---

## Why this course is shaped this way

```
                ┌──────────────────────────────┐
                │  Phase 0: C# & .NET core      │   ← the shared foundation
                │  (fast-tracked for you)       │
                └───────────────┬──────────────┘
                                │
            ┌───────────────────┴───────────────────┐
            ▼                                         ▼
┌───────────────────────────┐         ┌───────────────────────────┐
│ Phase 1: Supporting apps   │         │ Phase 2: Unity games       │
│ ASP.NET Core, EF Core,     │         │ Editor, scripting, 2D/3D,  │
│ logging, debugging, deploy │         │ physics, UI, audio, build  │
└───────────────────────────┘         └───────────────────────────┘
```

**C# is the trunk; support and Unity are two branches.** Both rely on the same
language and runtime, so we nail that first — quickly, because you already code.

---

## What makes it effective

- **Learn by doing.** Every module = short concepts + a guided lab (real `dotnet`
  projects or Unity scenes) + an unguided challenge + reference solutions.
- **Support realism.** You'll read stack traces, wire up structured logging, fix a
  **deliberately broken app**, and deploy — the actual day-to-day of app support.
- **Unity as applied C#.** You'll see exactly how Unity's C# differs from vanilla
  .NET (the frame loop, `MonoBehaviour`, coroutines vs `async`).
- **Two capstones.** A supported, tested, deployed Web API; and a finished, playable game.

---

## Prerequisites

- A Mac (Apple Silicon or Intel), ~10 GB free for the SDK + Unity later.
- Experience programming in **any** language (variables, loops, functions, OOP).
- Comfort in a terminal. We use the **.NET CLI** plus **VS Code** (or **Rider**).
- **No prior C#/.NET knowledge needed.**

Versions used throughout: **.NET 8 (LTS)**, **C# 12**, **Unity 6 (LTS)**.

---

## The learning path

Work the modules **in order** — each builds on the last.

### Phase 0 — Foundations (C# & .NET)
| # | Module | You'll learn to… | Est. |
|---|--------|------------------|------|
| 00 | [Setup & Orientation](./00-setup/) | Install the SDK + editor; build & run your first app | 45 min |
| 01 | [C# Fast-Track I](./01-csharp-fast-track-1/) | The type system, nullability, control flow | 1.5 h |
| 02 | [C# Fast-Track II (OOP)](./02-csharp-fast-track-2-oop/) | Classes, records, interfaces, polymorphism | 1.5 h |
| 03 | [C# Essentials](./03-csharp-essentials/) | Generics, LINQ, delegates/events, exceptions | 2 h |
| 04 | [.NET Runtime & Project Model](./04-dotnet-runtime-and-projects/) | CLR/GC, NuGet, projects, async/await | 2 h |

### Phase 1 — Supporting Applications
| # | Module | You'll learn to… | Est. |
|---|--------|------------------|------|
| 05 | [Debugging & Testing](./05-debugging-and-testing/) | Use the debugger, read stack traces, write xUnit tests | 2 h |
| 06 | [Logging, Config & Diagnostics](./06-logging-config-diagnostics/) | Structured logging, configuration, secrets | 2 h |
| 07 | [Web APIs with ASP.NET Core](./07-web-apis-aspnet-core/) | Build APIs with DI, middleware, routing | 2.5 h |
| 08 | [Data Access with EF Core](./08-data-access-ef-core/) | Model data, migrations, CRUD against a DB | 2.5 h |
| 09 | [Operate & Support (Capstone A)](./09-operate-and-support/) | Deploy, health-check, and diagnose a broken app | 3 h |

### Phase 2 — Unity
| # | Module | You'll learn to… | Est. |
|---|--------|------------------|------|
| 10 | [Unity Setup & Editor](./10-unity-setup-and-editor/) | Install Unity; navigate the editor; GameObjects | 1.5 h |
| 11 | [Scripting in Unity](./11-unity-scripting/) | MonoBehaviour lifecycle, input, prefabs | 2.5 h |
| 12 | [Build a 2D Game](./12-unity-2d-game/) | Sprites, Physics2D, a complete small 2D game | 3 h |
| 13 | [3D, Physics, UI & Audio](./13-unity-3d-ui-audio/) | 3D, rigidbodies, Canvas UI, sound | 3 h |
| 14 | [Build & Ship (Capstone B)](./14-build-and-ship/) | Export a playable desktop game | 2.5 h |

**Total: a realistic ~35 hours of focused, hands-on work.** Go at your own pace.

---

## How each module is structured

```
NN-topic/
├── README.md      ← Concepts in plain language. Read first.
├── lab.md         ← Step-by-step guided lab with expected output. Do second.
├── code/          ← Starter code the lab uses (when applicable).
├── challenge.md   ← An unguided task to prove you understood it. Do third.
└── solutions/     ← Reference answers — peek only after trying.
```

---

## Reference material (keep these open)

- **[cheatsheets/dotnet-cli.md](./cheatsheets/dotnet-cli.md)** — the `dotnet` commands you'll use daily
- **[cheatsheets/csharp-syntax.md](./cheatsheets/csharp-syntax.md)** — C# quick reference for an experienced dev
- **[cheatsheets/linq.md](./cheatsheets/linq.md)** — the LINQ operators worth knowing
- **[cheatsheets/debugging.md](./cheatsheets/debugging.md)** — reading stack traces & common exceptions
- **[GLOSSARY.md](./GLOSSARY.md)** — every term in plain English
- **[VERIFY.md](./VERIFY.md)** — end-to-end smoke test of your setup

## Shared sample projects

- **[apps/console-playground/](./apps/console-playground/)** — used across the fundamentals modules.
- **[apps/TaskApi/](./apps/TaskApi/)** — the Web API you grow across the support modules.
- **[unity-scripts/](./unity-scripts/)** — reference C# scripts for the Unity modules.

---

## Quick start

```bash
cd dotnet-course/00-setup
cat README.md            # install the SDK + editor, then:
./scripts/verify-setup.sh
cd ../01-csharp-fast-track-1 && cat README.md
```

Ready? **→ [Start with Module 00: Setup & Orientation](./00-setup/)**
