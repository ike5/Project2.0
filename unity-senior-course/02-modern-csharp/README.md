# 01 — Modern C# in Unity

You already know C# (or can read it). This module is **not** a C# tutorial.
It's about which modern C# features work in Unity, which don't yet, and
how to use the ones that do without breaking the engine.

The single most common "senior" mistake: writing `IEnumerator` coroutines
because Unity "supports" them — when `Span<T>`, `Awaitable`, and source
generators do it cheaper, faster, and with better lifetime semantics.

---

## 1. The Unity C# version matrix (and why it matters)

Unity embeds a C# compiler. The version is **not** the same as Visual
Studio's. As of Unity 6 (mid-2026):

| Unity Version | C# version | Roslyn | Notes |
|---------------|------------|--------|-------|
| 2022.3 LTS    | C# 9       | 4.0    | LTS |
| Unity 6 (6000.0.x) | C# 9   | 4.6    | Default. C# 10/11/12 need `csc.rsp` |

**What's in C# 9** (default in Unity 6, what you'll use most):
- File-scoped namespaces: `namespace Foo;`
- Target-typed `new`: `List<int> xs = new();`
- Records (reference): `public record Player(string Name);`
- Init-only setters: `public int X { get; init; }`
- Pattern matching enhancements: relational patterns, `and`/`or`/`not`
- Top-level statements (in editor scripts only)
- `with` expressions on records

**What's in C# 10** (opt-in via `csc.rsp`):
- File-scoped namespaces (already in 9)
- `record struct` (very useful in Unity for value-type records)
- Global usings
- Improved lambdas (`Attribute` on lambdas, natural types)

**What's in C# 11/12** (opt-in):
- Raw string literals: `"""..."""`
- `required` members
- Primary constructors on classes
- `List<T>` patterns

**The C# 12+ caveat**: most Unity packages are compiled against C# 9
APIs. Going to C# 12 means some packages will fail to compile against
your code. Stay on C# 9 by default; opt into C# 10/11 only in
non-shared code if you really need it.

### Setting it

`Assets/csc.rsp`:
```
-langversion:9.0
-define:UNITY_6000_0_OR_NEWER
```

Restart the editor after editing.

---

## 2. The `Span<T>` and `ReadOnlySpan<T>` game

`Span<T>` is a **stack-allocated view over contiguous memory** that does
not allocate. It's the most important type in modern .NET and almost
free in Unity. Where it shines in Unity:

- **Parsing strings** without `string.Substring` (which allocates).
- **Working with `NativeArray<T>`** and `byte[]` interchangeably.
- **Implementing custom binary readers/writers** for save files.
- **Reducing `Vector3[]` → `ReadOnlySpan<Vector3>`** for read-only
  parameter passing.

### The constraint you must remember

`Span<T>` is a `ref struct`. That means:

- It **cannot** be a field of a class.
- It **cannot** be in an `async` method (across `await`).
- It **cannot** cross an `await` or `yield return`.
- It **can** be a method parameter, local, or `ref struct` field.

### Idiomatic Unity usage

```csharp
using System;
using UnityEngine;

public static class StringParsing
{
    // Parses "x,y,z" without allocating a string.
    public static bool TryParseVec3(ReadOnlySpan<char> input, out Vector3 result)
    {
        result = default;
        int idx1 = input.IndexOf(',');
        if (idx1 < 0) return false;

        var rest = input[(idx1 + 1)..];
        int idx2 = rest.IndexOf(',');
        if (idx2 < 0) return false;

        if (!float.TryParse(input[..idx1], out float x)) return false;
        if (!float.TryParse(rest[..idx2], out float y)) return false;
        if (!float.TryParse(rest[(idx2 + 1)..], out float z)) return false;

        result = new Vector3(x, y, z);
        return true;
    }
}
```

Compare to the naive version, which **allocates three substrings and
a new Vector3 string**:

```csharp
var parts = "1,2,3".Split(',');          // allocates string[]
var v = new Vector3(
    float.Parse(parts[0]),
    float.Parse(parts[1]),
    float.Parse(parts[2]));              // boxes if 'parts' is IEnumerable
```

### Spans over `NativeArray<T>`

```csharp
using System;
using Unity.Collections;

public static class NativeExtensions
{
    // Span<T> is a stack-only view; NativeArray<T>.AsSpan() is allocation-free.
    public static void FillZeros<T>(this NativeArray<T> array) where T : unmanaged
    {
        array.AsSpan().Clear();
    }
}
```

---

## 3. Records in Unity — when, why, when not

Records are value-equality-by-default types. Great for **data transfer
objects** (DTOs), **save data**, **network messages**.

```csharp
public record struct DamageEvent(
    Entity Attacker,
    Entity Target,
    float Amount,
    Vector3 HitPoint);
```

**Use `record struct`** in Unity (rather than `record class`):

- **No allocation**: stack-allocated by default, no GC pressure.
- **No null**: not nullable, fewer defensive checks.
- **POD semantics**: works with Burst (covered in module 4).
- **with` expressions** work, but copy the struct.

**Don't use `record class`** for per-frame data. Each `with` allocates.

---

## 4. Source generators — the future, already here

A source generator is C# compile-time code that runs during your build
and **adds code to your assembly**. Unity 6 uses them heavily:

- `[BurstCompile]` (module 4) generates Burst entry points.
- `[CreateProperty]` (Unity 6+ experimental) generates property change
  notifications.
- `INotifyPropertyChanged` sources are common in MVVM.
- `Unity.Properties` (since 6) uses them for serialization.

You can write your own. A simple example:

```csharp
[Generator(LanguageNames.CSharp)]
public class HelloWorldGenerator : ISourceGenerator
{
    public void Initialize(GeneratorInitializationContext ctx) { }
    public void Execute(GeneratorExecutionContext ctx)
    {
        ctx.AddSource("GeneratedHello.g.cs", "public static class GeneratedHello { public static string Hi() => \"hi\"; }");
    }
}
```

For this course, you'll **consume** source generators more than write
them. The most useful one you'll use daily is `Unity.Mathematics` +
Burst's auto-vectorization (module 4).

---

## 5. Pattern matching: the senior default

```csharp
// Senior way
if (obj is Player { IsDead: false, Health: > 0 } p)
{
    p.Heal(10);
}

// Avoid
var p = obj as Player;
if (p != null && !p.IsDead && p.Health > 0)
{
    p.Heal(10);
}
```

The first is one expression, no temporary, no `as` cast, no null
check. The compiler proves exhaustiveness in `switch` expressions,
which is why C# engineers prefer them for state machines.

```csharp
public string Describe(GameState s) => s switch
{
    Loading { Progress: var p } => $"loading {p:P0}",
    Playing => "playing",
    Paused => "paused",
    GameOver { FinalScore: var f } => $"game over: {f}",
    _ => "unknown"
};
```

---

## 6. The `init` and `required` keywords

For data you want to construct once and then make immutable:

```csharp
public class GameConfig
{
    public string ServerUrl { get; init; }
    public int Port { get; init; }
    public int MaxPlayers { get; init; } = 16;
}

// In use
var cfg = new GameConfig
{
    ServerUrl = "wss://game.example.com",
    Port = 7777
};

// cfg.Port = 9999; // ← compile error
```

`required` (C# 11) forces the caller to set:

```csharp
public class GameConfig
{
    public required string ServerUrl { get; init; }
    public required int Port { get; init; }
}
```

---

## 7. The thing senior Unity devs avoid

**`async void`**. It crashes your scene if it throws, can't be awaited,
hides errors. In Unity, **always**:

```csharp
// WRONG
async void OnButtonClick() { await LoadAsync(); }  // exceptions disappear

// RIGHT
async Awaitable OnButtonClick()  // Unity 2023+
{
    try { await LoadAsync(); }
    catch (Exception e) { Debug.LogException(e); }
}
```

Module 9 goes deep on `Awaitable` and UniTask.

---

## Summary

- C# 9 by default; opt into C# 10/11/12 only for isolated code.
- `Span<T>` / `ReadOnlySpan<T>` for zero-alloc string/binary work.
- `record struct` for value-type DTOs that Burst can use.
- Source generators are everywhere; you consume them more than write them.
- Pattern matching is the senior default.
- `init`/`required` for immutable config.
- **Never** `async void`.
