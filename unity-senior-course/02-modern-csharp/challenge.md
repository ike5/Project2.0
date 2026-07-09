# Challenge 02 — Allocation Audit

The senior's first habit: never trust a piece of code to be
allocation-free; measure it. This challenge is a structured
allocation audit of a small system.

**Time**: 60–90 minutes.

---

## The starting system

Create `Assets/Scripts/Gameplay/Inventory.cs`:

```csharp
using System.Collections.Generic;
using System.Text;
using UnityEngine;

namespace MyGame.Gameplay
{
    public class Inventory : MonoBehaviour
    {
        readonly List<string> _items = new();
        readonly StringBuilder _sb = new();

        public void Add(string item) => _items.Add(item);

        public string Describe()
        {
            _sb.Clear();
            _sb.Append("Inventory (");
            _sb.Append(_items.Count);
            _sb.Append("): ");
            for (int i = 0; i < _items.Count; i++)
            {
                if (i > 0) _sb.Append(", ");
                _sb.Append(_items[i]);
            }
            return _sb.ToString();
        }

        void Update()
        {
            if (Input.GetKeyDown(KeyCode.Space))
            {
                Debug.Log(Describe());
            }
        }
    }
}
```

**Claim 1**: this allocates at most one string per space-bar press
(the `ToString()`).

**Your job**: prove or disprove it. Then fix it.

---

## Part A — Measure

Use the **Memory Profiler**:

1. Open the project. Add an `Inventory` to a GameObject.
2. Open Memory Profiler. Snapshot.
3. Press space 100 times. Snapshot again.
4. Diff.

**Expected finding**: a few new `string` allocations from the log
call. Note them.

**Stretch**: use `Profiler.GetTotalAllocatedMemoryLong()` and
`GC.GetTotalMemory(false)` and log them around the operation:

```csharp
long before = GC.GetTotalMemory(true);
Describe();
long after = GC.GetTotalMemory(false);
Debug.Log($"Describe() allocated {after - before} bytes");
```

Note: `GC.GetTotalMemory(true)` forces a full collection, which
itself allocates; you want `false` for the "after".

## Part B — Use `ZString` or `Span<char>`

Replace `_sb.ToString()` with a zero-alloc `string.Create` or
`ZString.Concat`:

```csharp
// Using ZString (NuGet: Cysharp/NetStandard.ZString)
Debug.Log(ZString.Concat("Inventory (", _items.Count, "): ",
    string.Join(", ", _items)));
```

Or, with `string.Create`:

```csharp
public string Describe()
{
    return string.Create(DescribeLength(), this, (span, inv) =>
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
            pos += span[pos..].TryWrite(inv._items[i]);
        }
    });
}

int DescribeLength() { /* compute exact length */ }
```

**Verify**: the post-fix diff is empty. The audit passes.

## Part C — Catch one more allocation

The `Input.GetKeyDown` check is fine, but on the path there's a
`Debug.Log` that takes a `params object[]`. Each `Log` call
allocates a `object[]`. With the fix above, you're passing a
single `string` (no params), so no array. Verify.

If you ever log a format string, you're boxing. Use a single
`Debug.Log(message)` with the message pre-formatted.

## Part D — The senior wrap-up

For each `Update` in your game, the test is:

```text
Does Update allocate?     → if yes, fix it.
Does Update box?          → if yes, fix it.
Does Update call Find?    → if yes, fix it.
Does Update call Resources.Load?  → if yes, fix it.
Does Update use string interpolation?  → if yes, gate it.
```

Write a one-page note describing how you would find these in a
mature codebase. The Memory Profiler diff is the senior's best
friend; the Profiler is the runtime's best friend.

---

## What we're testing

- You can read the Memory Profiler diff and name the offending
  allocations.
- You can replace an allocation with a `Span<char>` or
  `string.Create` based zero-alloc version.
- You can describe, in your own words, the senior Update checklist.

---

## Verify

```bash
# Allocations in a frame, before and after fix
# Use Profiler → Memory Module → "GC Allocated In Frame"
# Before: ~120 bytes
# After: 0 bytes
```

If your numbers don't match, you missed an allocation. Common
candidates:

- The `params object[]` from `Debug.Log` overloads.
- The `List<T>.Add` resizing path.
- The closure capture from a lambda.
- The `ToString()` from an `enum`.

Find them all.
