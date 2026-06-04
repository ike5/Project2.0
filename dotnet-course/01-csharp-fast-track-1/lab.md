# Lab 01 — Types & Nullability Hands-On

**You'll:** spin up a console project and make value-vs-reference and nullability
concrete. ⏱️ ~35 min.

---

## Part A — A fresh project
```bash
mkdir -p ~/dev/ft1 && cd ~/dev/ft1
dotnet new console -n Ft1 && cd Ft1
```
Open `Program.cs` in your editor. Replace its contents as you work through the parts
below, running `dotnet run` after each.

## Part B — Value vs reference (prove the copy semantics)
```csharp
int x = 5;
int y = x;          // copy
y = 99;
Console.WriteLine($"x={x}, y={y}");   // x=5, y=99

var a = new List<int> { 1, 2, 3 };
var b = a;          // same reference
b.Add(4);
Console.WriteLine($"a.Count={a.Count}");   // 4  (b IS a)

// structs are value types — copied:
var p1 = (X: 1, Y: 2);   // value tuple (a struct)
var p2 = p1;
p2.X = 100;
Console.WriteLine($"p1.X={p1.X}");   // 1 (unaffected)
```
✅ Run it. Confirm the printed values match the comments. If `a.Count` surprised you,
re-read §1 of the README — this is the most common real-world C# confusion.

## Part C — Nullability
First, make sure NRT is on. Open `Ft1.csproj` — `dotnet new console` already includes
`<Nullable>enable</Nullable>`. Now:
```csharp
string? maybe = args.Length > 0 ? args[0] : null;

// This line should produce a COMPILER WARNING (dereference of possibly null):
// Console.WriteLine(maybe.Length);

// Safe versions:
Console.WriteLine(maybe?.Length ?? -1);     // -1 when null
maybe ??= "fallback";
Console.WriteLine($"value is now '{maybe}'");
```
Run with and without an argument:
```bash
dotnet run            # maybe is null -> prints -1, then 'fallback'
dotnet run -- hello   # maybe='hello' -> prints 5, then 'hello'
```
✅ Uncomment the warning line and run `dotnet build` — observe the **CS8602** warning.
That warning is the compiler stopping a `NullReferenceException` before it happens.

## Part D — Safe parsing & switch expressions
```csharp
foreach (var token in new[] { "7", "42", "oops" })
{
    string result = int.TryParse(token, out int n)
        ? n switch { < 10 => $"{n} is small", < 100 => $"{n} is medium", _ => "big" }
        : $"'{token}' is not a number";
    Console.WriteLine(result);
}
```
✅ Expected:
```
7 is small
42 is medium
'oops' is not a number
```

## Part E — Read the reference demo
```bash
cd <repo>/dotnet-course/apps/console-playground
dotnet run -- 1        # runs TypesDemo
```
Open `Demos/TypesDemo.cs` and match each line to what you just practiced.

## What you learned
- Value types copy; reference types share — this drives a lot of behavior.
- NRT converts null bugs into compile-time warnings; `?.`, `??`, `??=`, `!` handle nulls.
- `TryParse` + switch expressions = clean, exception-free branching.

➡️ **[challenge.md](./challenge.md)** then [Module 02](../02-csharp-fast-track-2-oop/).
