# Lab 02 — Modern C# in Unity

A series of small experiments to make modern C# features concrete in
Unity. Each is a 5-minute task; together they take about an hour.

**Starter**: `UnitySeniorLab` with `Assets/csc.rsp` containing
`-langversion:9.0`.

---

## 1. `Span<char>` over a string

Goal: parse `"x,y,z"` into a `Vector3` with **zero allocations**.

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
        var rest = input[(first + 1)..];
        int second = rest.IndexOf(',');
        if (second < 0) return false;
        if (!float.TryParse(input[..first], out float x)) return false;
        if (!float.TryParse(rest[..second], out float y)) return false;
        if (!float.TryParse(rest[(second + 1)..], out float z)) return false;
        result = new Vector3(x, y, z);
        return true;
    }
}
```

Verify the implementation:

```csharp
// In a MonoBehaviour, or in a tests file:
Assert.IsTrue(Vec3Parser.TryParse("1,2,3".AsSpan(), out var v));
Assert.AreEqual(new Vector3(1, 2, 3), v);
```

**Stretch**: extend to `"x,y,z,w"` for quaternions, or to a
`Vector3[]` parser for `"1,2,3;4,5,6;..."`.

---

## 2. `record struct` for an event

Goal: a `DamageEvent` that's a value type, no allocations, Burst-friendly.

```csharp
using System;
using UnityEngine;

public readonly record struct DamageEvent(
    int SourceId,
    int TargetId,
    float Amount,
    Vector3 HitPoint)
{
    public bool IsFatal => Amount <= 0;
}
```

In a MonoBehaviour:

```csharp
readonly System.Collections.Generic.Queue<DamageEvent> _events = new();

void ApplyDamage(DamageEvent e)
{
    // ... apply ...
    _events.Enqueue(e);
}
```

**Verify**: in the Memory Profiler, after firing 10,000 events, the
managed heap delta should be near zero (the `Queue<T>` may grow its
internal array once, then stop). Compare to a `record class`
version, which allocates 10,000 records.

---

## 3. Pattern matching switch expression

Goal: replace a state-machine `if/else` chain with a `switch`
expression.

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

**Verify**: write EditMode tests covering all states.

---

## 4. `init` and `required`

Goal: a `GameConfig` you can construct once, immutably.

```csharp
public class GameConfig
{
    public string ServerUrl { get; init; }
    public int Port { get; init; }
    public int MaxPlayers { get; init; } = 16;
}

// Use
var cfg = new GameConfig
{
    ServerUrl = "wss://game.example.com",
    Port = 7777
};

// cfg.Port = 9999; // ← compile error
```

**Stretch**: with C# 11 enabled in `csc.rsp`, try `required`:

```
-langversion:11.0
```

```csharp
public class GameConfig
{
    public required string ServerUrl { get; init; }
    public required int Port { get; init; }
}

// var cfg = new GameConfig { Port = 7777 };  // ← compile error: ServerUrl is required
```

---

## 5. Span over a `NativeArray<T>`

Goal: zero-alloc iteration over a `NativeArray<float3>`.

```csharp
using System;
using Unity.Collections;
using Unity.Mathematics;
using UnityEngine;

public class SpanTest : MonoBehaviour
{
    NativeArray<float3> _data;

    void Start()
    {
        _data = new NativeArray<float3>(1000, Allocator.Persistent);
        for (int i = 0; i < _data.Length; i++) _data[i] = new float3(i, 0, 0);
    }

    void Update()
    {
        ReadOnlySpan<float3> view = _data.AsReadOnlySpan();
        float3 sum = float3.zero;
        foreach (ref readonly var v in view) sum += v;
        // use sum
    }

    void OnDestroy()
    {
        if (_data.IsCreated) _data.Dispose();
    }
}
```

Verify in the Memory Profiler: after 60 seconds, the managed heap
should not have grown from this script.

---

## 6. Bonus: see your code Burst-vectorize

Take the loop from above and wrap it in a job:

```csharp
[BurstCompile]
struct SumJob : IJob
{
    [ReadOnly] public NativeArray<float3> Data;
    public NativeArray<float3> Result;   // one element

    public void Execute()
    {
        float3 sum = float3.zero;
        for (int i = 0; i < Data.Length; i++) sum += Data[i];
        Result[0] = sum;
    }
}
```

Profile with **Window → Jobs → Burst → Open Inspector** to confirm
the job is **AOT (Burst)** and the loop is **vectorized**.

---

## What you should now understand

- `Span<T>` keeps string/binary work on the stack.
- `record struct` is the right value-type DTO in Unity.
- Pattern matching is shorter and more provable than `if/else`.
- `init` and `required` enforce immutability at compile time.
- `NativeArray<T>.AsSpan()` gives stack access to native memory.
