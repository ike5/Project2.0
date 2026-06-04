# Glossary

Plain-English definitions of the terms in this course. Skim now; return whenever a
word trips you up.

## .NET platform & runtime

- **.NET** — The platform: a runtime + base class libraries + tooling for running C#
  (and F#/VB) apps cross-platform. "**.NET 8**" is a specific version (LTS).
- **CLR (Common Language Runtime)** — The virtual machine that runs .NET code:
  manages memory, threads, and execution. Analogous to the JVM.
- **IL (Intermediate Language)** — The bytecode C# compiles to. The CLR's **JIT**
  (Just-In-Time compiler) turns IL into native machine code at runtime.
- **Garbage Collector (GC)** — Automatically frees memory you're no longer using. You
  rarely free memory manually in C#.
- **Assembly** — A compiled unit of .NET code: a `.dll` (library) or `.exe`
  (executable). Your project builds into an assembly.
- **BCL (Base Class Library)** — The standard library (`System.*`): collections,
  IO, networking, LINQ, etc.
- **NuGet** — The package manager for .NET. Packages are pulled into a project via
  its `.csproj`.
- **SDK vs Runtime** — The **SDK** builds apps (compiler + CLI + templates); the
  **Runtime** only runs them. Developers install the SDK.

## Project & tooling

- **`dotnet` CLI** — The command-line tool: `dotnet new/build/run/test/publish`.
- **Project (`.csproj`)** — An XML file describing one buildable unit: its target
  framework, dependencies, and settings.
- **Solution (`.sln`)** — A container grouping multiple projects (e.g. an API + its
  test project).
- **Target Framework Moniker (TFM)** — e.g. `net8.0`; which framework a project builds for.
- **Build / Restore / Publish** — *Restore* downloads NuGet deps; *Build* compiles to
  IL; *Publish* produces a deployable folder.

## C# language

- **Value type vs reference type** — **Value types** (`int`, `bool`, `struct`,
  `enum`) hold their data directly and are copied on assignment. **Reference types**
  (`class`, `string`, arrays) hold a *reference* to data on the heap.
- **Nullable reference types (NRT)** — A compiler feature: `string?` may be null,
  `string` shouldn't be. Warnings help you avoid `NullReferenceException`.
- **Property** — A class member that looks like a field but runs get/set logic:
  `public string Name { get; set; }`.
- **Record** — A concise reference (or value) type for immutable data with built-in
  equality: `record Person(string Name);`.
- **Interface** — A contract of members a type promises to implement (`IDisposable`).
- **Generic** — A type/method parameterized by type: `List<T>`, `Dictionary<K,V>`.
- **Delegate** — A type-safe function pointer; underpins lambdas and events.
- **Lambda** — An inline anonymous function: `x => x * 2`.
- **Event** — A publisher/subscriber notification mechanism built on delegates.
- **LINQ (Language-Integrated Query)** — Query operators over collections:
  `items.Where(...).Select(...)`.
- **Pattern matching** — `switch`/`is` expressions that match shape and extract data.
- **`async` / `await`** — Syntax for non-blocking asynchronous code; an `async`
  method returns a **`Task`**.
- **`Task`** — Represents an in-progress or completed asynchronous operation.
- **`IDisposable` / `using`** — Pattern for deterministically releasing resources
  (files, connections): `using var f = File.OpenRead(...);`.
- **Extension method** — A static method that *looks* like an instance method on an
  existing type (most LINQ operators are these).

## ASP.NET Core (web)

- **ASP.NET Core** — The web framework for building APIs and web apps on .NET.
- **Middleware** — Components forming a pipeline each HTTP request passes through
  (auth, logging, routing, …).
- **Dependency Injection (DI)** — The built-in pattern where the framework *provides*
  a class its dependencies rather than the class creating them. Registered in the
  service container; consumed via constructor parameters.
- **Minimal API vs Controllers** — Two styles of defining endpoints: terse
  `app.MapGet(...)` lambdas, or class-based `[ApiController]` controllers.
- **Model binding** — Mapping request data (route, query, body) onto C# parameters/objects.
- **`IConfiguration` / Options** — The system that reads settings from
  `appsettings.json`, env vars, and secrets into typed objects.
- **`ILogger`** — The logging abstraction; **structured logging** records data fields,
  not just text. **Serilog** is a popular implementation.
- **Health check** — An endpoint (`/health`) reporting whether the app/deps are OK.

## Entity Framework Core (data)

- **EF Core** — The Object-Relational Mapper (ORM): map C# classes to DB tables and
  query with LINQ instead of raw SQL.
- **`DbContext`** — Your session with the database; exposes `DbSet<T>` per table.
- **Entity** — A C# class mapped to a table row.
- **Migration** — A versioned, code-generated description of a schema change you apply
  to the database.
- **LINQ-to-Entities** — LINQ that EF Core translates into SQL.

## Unity (games)

- **Unity** — A game engine; you write gameplay in C#. Uses its own runtime (Mono or
  **IL2CPP**), not the standard .NET host.
- **GameObject** — The basic entity in a scene; does nothing on its own.
- **Component** — A piece of behavior/data attached to a GameObject (Transform,
  Rigidbody, your scripts). GameObjects are composed of components.
- **`MonoBehaviour`** — The base class for your scripts; gives lifecycle hooks.
- **Lifecycle methods** — `Awake`, `Start`, `Update` (per frame), `FixedUpdate` (per
  physics step), `OnCollisionEnter`, etc. — called by the engine, not by you.
- **Scene** — A level/screen containing GameObjects.
- **Prefab** — A reusable, saved GameObject template you instantiate at runtime.
- **ScriptableObject** — A data container asset (configs, item definitions) decoupled
  from scenes.
- **Coroutine** — Unity's way to spread work across frames (`yield return`), used
  instead of `async` for most timing in gameplay.
- **Inspector** — The editor panel where you tweak a component's serialized fields.
- **`[SerializeField]`** — Exposes a private field to the Inspector for tuning.
- **Rigidbody / Collider** — Physics body and its collision shape.
- **Player loop** — Unity's per-frame update cycle that drives your `Update` methods.
