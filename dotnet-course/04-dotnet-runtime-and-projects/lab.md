# Lab 04 — Solutions, Packages & Async

**You'll:** build a multi-project solution, add a NuGet package, and *measure* async
concurrency. ⏱️ ~45 min.

---

## Part A — A multi-project solution
```bash
mkdir -p ~/dev/ft4 && cd ~/dev/ft4
dotnet new sln -n Ft4
dotnet new classlib -n Ft4.Core
dotnet new console  -n Ft4.App
dotnet sln add Ft4.Core/Ft4.Core.csproj Ft4.App/Ft4.App.csproj
dotnet add Ft4.App/Ft4.App.csproj reference Ft4.Core/Ft4.Core.csproj
```
In `Ft4.Core/Class1.cs`:
```csharp
namespace Ft4.Core;
public static class Calc { public static int Add(int a, int b) => a + b; }
```
In `Ft4.App/Program.cs`:
```csharp
using Ft4.Core;
Console.WriteLine($"2 + 3 = {Calc.Add(2, 3)}");
```
```bash
dotnet run --project Ft4.App     # 2 + 3 = 5
```
✅ The app consumes the library via a **project reference**, all tracked by the solution.

## Part B — Add a NuGet package
```bash
dotnet add Ft4.App/Ft4.App.csproj package Humanizer --version 2.14.1
```
Use it:
```csharp
using Ft4.Core;
using Humanizer;
Console.WriteLine($"2 + 3 = {Calc.Add(2, 3)}");
Console.WriteLine(TimeSpan.FromMinutes(90).Humanize());   // "1 hour"
Console.WriteLine("DotNetIsGreat".Humanize());            // "Dot net is great"
```
```bash
dotnet run --project Ft4.App
dotnet list Ft4.App/Ft4.App.csproj package    # see Humanizer listed
```
✅ A third-party package, restored and used. Open `Ft4.App.csproj` and find the
`<PackageReference Include="Humanizer" Version="2.14.1" />`.

## Part C — Measure async concurrency
Replace `Program.cs`:
```csharp
using System.Diagnostics;

async Task<int> WorkAsync(string name, int ms)
{
    await Task.Delay(ms);
    Console.WriteLine($"  {name} done ({ms}ms)");
    return ms;
}

// Sequential: ~300ms total
var sw = Stopwatch.StartNew();
await WorkAsync("seq-a", 150);
await WorkAsync("seq-b", 150);
Console.WriteLine($"sequential: {sw.ElapsedMilliseconds}ms");

// Concurrent: ~150ms total
sw.Restart();
var a = WorkAsync("conc-a", 150);
var b = WorkAsync("conc-b", 150);
await Task.WhenAll(a, b);
Console.WriteLine($"concurrent: {sw.ElapsedMilliseconds}ms");
```
```bash
dotnet run --project Ft4.App
```
✅ Sequential ≈ 300ms; concurrent ≈ 150ms. Starting both tasks *before* awaiting is
what overlaps them — the core async insight.

## Part D — Reference demo
```bash
cd <repo>/dotnet-course/apps/console-playground
dotnet run -- 4        # AsyncDemo: WhenAll vs sequential
```

## What you learned
- Solutions group projects; project references wire them together.
- NuGet packages add capability via `PackageReference` (pin versions).
- async overlaps I/O when you start tasks before awaiting (`Task.WhenAll`).

➡️ **[challenge.md](./challenge.md)** then [Module 05](../05-debugging-and-testing/).
