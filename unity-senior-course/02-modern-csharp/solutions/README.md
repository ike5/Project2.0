# Solutions 02 — Modern C#

Reference implementations for the modern C# lab and challenge.

---

## Lab

### 1. `Vec3Parser`

```csharp
using System;
using UnityEngine;

public static class Vec3Parser
{
    public static bool TryParse(ReadOnlySpan<char> input, out Vector3 result)
    {
        result = default;
        int first = input.IndexOf(',');
        if (first < 0) return false;

        ReadOnlySpan<char> rest = input[(first + 1)..];
        int second = rest.IndexOf(',');
        if (second < 0) return false;

        if (!float.TryParse(input[..first], out float x)) return false;
        if (!float.TryParse(rest[..second], out float y)) return false;
        if (!float.TryParse(rest[(second + 1)..], out float z)) return false;

        result = new Vector3(x, y, z);
        return true;
    }

    public static bool TryParse(string input, out Vector3 result) =>
        TryParse(input.AsSpan(), out result);
}
```

Tests:

```csharp
[Test]
public void Vec3Parser_ParsesValid()
{
    Assert.IsTrue(Vec3Parser.TryParse("1,2,3".AsSpan(), out var v));
    Assert.AreEqual(new Vector3(1, 2, 3), v);
}

[Test]
public void Vec3Parser_RejectsInvalid()
{
    Assert.IsFalse(Vec3Parser.TryParse("1,2".AsSpan(), out _));
    Assert.IsFalse(Vec3Parser.TryParse("a,b,c".AsSpan(), out _));
}
```

### 2. `DamageEvent`

```csharp
using System.Collections.Generic;
using UnityEngine;

public readonly record struct DamageEvent(
    int SourceId,
    int TargetId,
    float Amount,
    Vector3 HitPoint)
{
    public bool IsFatal => Amount <= 0;
}

public class DamageLog : MonoBehaviour
{
    readonly Queue<DamageEvent> _events = new(64);

    public void Record(in DamageEvent e) => _events.Enqueue(e);

    public int Count => _events.Count;
}
```

### 3. Status display

```csharp
public enum GameState { Loading, Playing, Paused, GameOver }

public readonly record struct GameStatus(
    GameState State,
    float Progress = 0f,
    int Score = 0);

public static class StatusDisplay
{
    public static string Describe(GameStatus s) => s switch
    {
        { State: GameState.Loading, Progress: var p } => $"loading {p:P0}",
        { State: GameState.Playing } => "playing",
        { State: GameState.Paused } => "paused",
        { State: GameState.GameOver, Score: var f } => $"game over: {f}",
        _ => "unknown"
    };
}
```

### 4. `GameConfig`

```csharp
public class GameConfig
{
    public string ServerUrl { get; init; }
    public int Port { get; init; }
    public int MaxPlayers { get; init; } = 16;
}
```

With C# 11 (`csc.rsp`: `-langversion:11.0`):

```csharp
public class GameConfig
{
    public required string ServerUrl { get; init; }
    public required int Port { get; init; }
    public int MaxPlayers { get; init; } = 16;
}
```

### 5. Span over `NativeArray<T>`

The key insight: `_data.AsReadOnlySpan()` gives a `ReadOnlySpan<T>`
that wraps the native memory. No allocation. Iteration is
stack-only.

---

## Challenge — Allocation Audit

### Measurement

```csharp
using System;
using UnityEngine;
using Unity.Profiling;

public class AllocationProbe : MonoBehaviour
{
    ProfilerRecorder _gcAllocRecorder;
    ProfilerRecorder _totalAllocRecorder;

    void OnEnable()
    {
        _gcAllocRecorder = ProfilerRecorder.StartNew(
            ProfilerCategory.Memory, "GC.Alloc");
        _totalAllocRecorder = ProfilerRecorder.StartNew(
            ProfilerCategory.Memory, "Total Reserved Memory");
    }

    void OnDisable()
    {
        _gcAllocRecorder.Dispose();
        _totalAllocRecorder.Dispose();
    }

    void Update()
    {
        long gc = _gcAllocRecorder.LastValue;
        long total = _totalAllocRecorder.LastValue;
        if (gc > 0) Debug.Log($"GC.Alloc this frame: {gc} bytes, total reserved: {total}");
    }
}
```

The fix: pre-format the description outside `Update`, cache it,
and only re-compute when the inventory changes:

```csharp
public class Inventory : MonoBehaviour
{
    readonly List<string> _items = new(16);
    string _cached;
    bool _dirty = true;

    public void Add(string item)
    {
        _items.Add(item);
        _dirty = true;
    }

    public string Describe()
    {
        if (!_dirty) return _cached;

        var sb = new System.Text.StringBuilder(128);
        sb.Append("Inventory (").Append(_items.Count).Append("): ");
        for (int i = 0; i < _items.Count; i++)
        {
            if (i > 0) sb.Append(", ");
            sb.Append(_items[i]);
        }
        _cached = sb.ToString();
        _dirty = false;
        return _cached;
    }

    void Update()
    {
        if (Input.GetKeyDown(KeyCode.Space))
        {
            // Single string arg, no params object[] allocation.
            Debug.Log(Describe());
        }
    }
}
```

The senior refinement: keep an `IList<string>` reference, never
return `List<T>` directly (callers could mutate it). And if the
inventory can have hundreds of items, switch to `Span<char>` +
`string.Create` to avoid the `ToString()` allocation.

### ZString version

`ZString.Concat` (Cysharp's package) is the gold standard:

```csharp
using Cysharp.Text;

public string Describe()
{
    using var sb = ZString.CreateStringBuilder();
    sb.Append("Inventory (");
    sb.Append(_items.Count);
    sb.Append("): ");
    for (int i = 0; i < _items.Count; i++)
    {
        if (i > 0) sb.Append(", ");
        sb.Append(_items[i]);
    }
    return sb.ToString();
}
```

The `using var sb` returns the builder to a pool; the `ToString()`
allocates the result string. For frequent calls, return a
`ZString` directly and let the caller convert.

### Pure `Span<char>` version

```csharp
public string Describe()
{
    // Compute exact length
    int length = "Inventory (".Length + 3 /* ): */ +
                 CountDigits(_items.Count) +
                 _items.Sum(s => s.Length + 2) - 2 /* last separator */;
    if (_items.Count == 0) length = "Inventory (0): ".Length;

    return string.Create(length, this, (span, inv) =>
    {
        int pos = 0;
        "Inventory (".AsSpan().CopyTo(span[pos..]);
        pos += 12;
        pos += span[pos..].TryWrite(inv._items.Count);
        "): ".AsSpan().CopyTo(span[pos..]);
        pos += 3;
        for (int i = 0; i < inv._items.Count; i++)
        {
            if (i > 0) { ", ".AsSpan().CopyTo(span[pos..]); pos += 2; }
            var s = inv._items[i].AsSpan();
            s.CopyTo(span[pos..]);
            pos += s.Length;
        }
    });
}

static int CountDigits(int n) =>
    n < 10 ? 1 : n < 100 ? 2 : n < 1000 ? 3 : 4;
```

`string.Create` allocates exactly one string, of the exact length,
with no intermediate buffers. The senior default for
performance-critical string composition.

---

## Common pitfalls

- **Forgetting `init` and using `set`**. The `init` keyword prevents
  the property from being modified after construction; `set` allows
  it.
- **Boxing a `record struct`**. The compiler doesn't box in most
  contexts; it will if you pass it as `object` or use a non-generic
  collection. Stay generic.
- **Spans that escape**. A `Span<T>` local in a method that
  `await`s is a compile error. Refactor to do the work before the
  await.
- **`ZString` package not installed**. It's a third-party NuGet.
  Either install via NuGetForUnity or use `string.Create`.
- **Pre-formatting the description and not invalidating the cache**
  when items are added. Result: stale UI.

---

## The senior takeaway

> A senior Unity dev treats `Update` as a **hot, allocation-free,
> GC-free, side-effect-bounded** function. The senior reflex is
> "would the Memory Profiler diff catch this?".
