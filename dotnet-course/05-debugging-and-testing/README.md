# Module 05 — Debugging & Testing

**Goal:** the two core skills of application support — drive a debugger to find root
cause fast, and write tests that pin behavior and prevent regressions.
⏱️ ~2 h · 🎯 Prereq: Phase 0 (00–04).

---

## 1. Reading a stack trace (the support reflex)

When an app throws, the **stack trace** tells you almost everything. Read it
top-down: exception **type + message**, then the **first frame in your code**.

```
System.InvalidOperationException: Sequence contains no elements
   at System.Linq.Enumerable.First[T](IEnumerable`1 source)
   at TaskApi.Services.TaskService.GetAsync(Int32 id) in .../TaskService.cs:line 21
   at ...
```
Here `First()` was called on an empty sequence — line 21 is where to look. See the
full guide: **[cheatsheets/debugging.md](../cheatsheets/debugging.md)**.

> The **innermost** exception (`---> InnerException`) is usually the real cause.
> `throw;` (not `throw ex;`) preserves the original trace — never lose it.

## 2. The debugger (VS Code C# Dev Kit / Rider)

- **Breakpoint** (`F9` / gutter click) — pause execution at a line.
- **Step**: `F10` over · `F11` into · `Shift+F11` out · `F5` continue.
- **Locals / Watch** — inspect and pin variable values.
- **Call Stack** — how you got here; click frames to navigate.
- **Conditional breakpoint** — break only when `id == 7`.
- **Exception breakpoint** — break the instant an exception is *thrown*, even if it's
  later caught and swallowed. This finds "invisible" bugs.

The C# Dev Kit generates `launch.json` so `F5` debugs your app; attach to a running
process with "Attach to .NET Process".

## 3. Testing with xUnit

Tests are your safety net for supporting code you didn't write: characterize current
behavior, then change with confidence.

```csharp
public class CalculatorTests
{
    [Fact]                                   // a single test
    public void Add_returns_sum()
    {
        var result = Calculator.Add(2, 3);
        Assert.Equal(5, result);             // Arrange / Act / Assert
    }

    [Theory]                                 // data-driven
    [InlineData(0, 0, 0)]
    [InlineData(2, 3, 5)]
    [InlineData(-1, 1, 0)]
    public void Add_various(int a, int b, int expected)
        => Assert.Equal(expected, Calculator.Add(a, b));
}
```
Common assertions: `Assert.Equal`, `True/False`, `Null/NotNull`, `Throws<T>` /
`ThrowsAsync<T>`, `Contains`, `Collection`.

```bash
dotnet test                                  # run all tests
dotnet test --filter "FullyQualifiedName~TaskService"
```

## 4. The support workflow: reproduce → test → fix

The professional way to fix a reported bug:
1. **Reproduce** it (same inputs/config — often from logs).
2. Write a **failing test** that captures the bug.
3. **Fix** the code until the test (and all others) pass.
4. The test now **prevents the regression** forever.

You'll do exactly this in the lab and again in Module 09's "broken app" exercise.

## 5. Test doubles & isolation

To test a unit without its real dependencies (DB, HTTP), you swap in a **fake/mock**.
The `TaskApi.Tests` project uses **EF Core's InMemory provider** as a lightweight
fake database so `TaskService` is tested in isolation, fast and deterministically.

---

## Do the lab
Debug a buggy method with breakpoints, then reproduce-test-fix it; run the TaskApi
test suite and add a test. 👉 **[lab.md](./lab.md)**

Then: 👉 **[challenge.md](./challenge.md)**

## Key terms
stack trace · inner exception · breakpoint · step over/into/out · watch · call stack ·
conditional/exception breakpoint · xUnit · `[Fact]`/`[Theory]` · Arrange/Act/Assert ·
`Assert.ThrowsAsync` · test double · EF InMemory

**Next →** [Module 06: Logging, Configuration & Diagnostics](../06-logging-config-diagnostics/)
