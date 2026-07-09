# Solutions 03 — Memory Model

---

## Part A — Managed

The naive `Update` allocates:

1. `new int[100]` — managed array
2. `new List<int>(50)` — managed list + internal array
3. `$"frame {_frameCount}"` — format string + result string (also
   boxes `_frameCount`)
4. `(object)42` — boxes the int

**Total**: 4+ managed allocations per frame.

## Part B — Boxing

The `BoxedMethod(x)` boxes `x` (a value type passed as `object`).
The string concatenation boxes `_frameCount` for `string.Concat`. The
`ArrayList` constructor allocates the list and an internal
`object[]`; the `Add(x)` boxes the int.

**Total**: 4+ extra allocations from Part B alone.

## Part C — Native

The persistent `NativeArray<int>(1024, Allocator.Persistent)`
allocates **4096 bytes** in the native heap. The Memory Profiler
shows it under **Native → Unity Collections**.

The TempJob array is allocated and disposed every frame, so it
doesn't show in steady state.

**The leak**: comment out the `OnDestroy` Dispose. The leak
detector will print at exit:

```
A Native Collection has not been disposed, ...
```

The senior discipline: every `NativeArray<T>`, `NativeList<T>`,
`NativeHashMap<K,V>` has a `Dispose()`. **Use `Allocator.Persistent`
for any long-lived native so the leak detector finds your mistake.**

## Part D — Stack

`stackalloc int[100]` is 400 bytes on the stack. Stack memory is
**not** tracked by the Memory Profiler (it's freed by the function
return). This is the cheapest memory you can use.

## Part E — Boxing via interface

`List<IDoSomething>.Add(new Counter { ... })` boxes the `Counter`
struct. The Profiler shows ~1000 box allocations on the first
frame (one per `Add`).

**The fix**: `List<Counter>`. Now `Add` is a memcpy, no box.

---

## The senior rules, condensed

1. **Stack > Native > Managed** in preference for hot data.
2. **Profile, don't speculate**. The Memory Profiler is the truth.
3. **A leak is a bug**. Native containers must be disposed.
4. **An allocation in `Update` is a bug**. Use the Profiler diff to
   find it; refactor to remove it.
5. **Boxing is a hidden allocation**. Stay generic.

---

## Sample Profiler diff interpretation

A typical diff output (from the Module 03 lab, Part A) shows:

```
Frame 0 → Frame 300:
  Managed:
    +1,200 byte[]    (from int[100] each frame * 300 frames)
    +1,500 List<int>  (one per frame)
    +45,000 string    (from $"frame {i}")
    +1,200 boxed Int32
  Native: ~unchanged
```

After the fix (cached fields, no interpolation in Update):

```
Frame 0 → Frame 300:
  Managed: 0 new
  Native: 0 new
```

The "0 new" line is the senior's gold.
