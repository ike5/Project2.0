# Module 03 — C# Essentials

**Goal:** the workhorse features you'll use in every real codebase — collections,
generics, **LINQ**, delegates/lambdas/**events**, exceptions, and `IDisposable`.
⏱️ ~2 h · 🎯 Prereq: 00–02.

---

## 1. Collections

```csharp
List<T>                 // dynamic array; the default
Dictionary<TKey,TValue> // hash map
HashSet<T>              // unique set
Queue<T> / Stack<T>     // FIFO / LIFO
T[]                     // fixed-size array
IEnumerable<T>          // the read-only "sequence" abstraction most APIs accept
IReadOnlyList<T>        // expose without allowing mutation
```
Prefer the **interface** (`IEnumerable<T>`, `IReadOnlyList<T>`) in public signatures;
use concrete types internally.

```csharp
var nums = new List<int> { 1, 2, 3 };
var byId = new Dictionary<int,string> { [1] = "a" };
if (byId.TryGetValue(1, out var name)) { }   // safe lookup (no KeyNotFoundException)
```

## 2. Generics

Write code once that works for many types, with compile-time safety:
```csharp
public class Cache<TKey, TValue> where TKey : notnull
{
    private readonly Dictionary<TKey, TValue> _store = new();
    public void Set(TKey key, TValue value) => _store[key] = value;
    public bool TryGet(TKey key, out TValue? value) => _store.TryGetValue(key, out value);
}

T Max<T>(T a, T b) where T : IComparable<T> => a.CompareTo(b) >= 0 ? a : b;
```
**Constraints** (`where T : ...`) let you call members on `T`: `class`, `struct`,
`new()`, an interface, or a base class.

## 3. LINQ (the big one)

Declarative queries over any `IEnumerable<T>`:
```csharp
var report = orders
    .Where(o => o.Total > 100)
    .GroupBy(o => o.CustomerId)
    .Select(g => new { CustomerId = g.Key, Count = g.Count(), Sum = g.Sum(o => o.Total) })
    .OrderByDescending(r => r.Sum)
    .ToList();
```
Key ideas:
- **Deferred execution** — operators build a query; it runs when enumerated
  (`ToList`, `foreach`, `Count`, `First`...). Re-enumerating re-runs it.
- **`FirstOrDefault` vs `First`** — prefer the `*OrDefault` forms unless you *know*
  there's an element.
- The same LINQ you learn here drives **EF Core** queries against the database (Module 08).

See **[cheatsheets/linq.md](../cheatsheets/linq.md)** for the full operator list.

## 4. Delegates, lambdas, events

```csharp
Func<int,int,int> add = (a, b) => a + b;     // returns a value
Action<string> log = Console.WriteLine;       // returns void
Predicate<int> even = n => n % 2 == 0;

// Events: a class publishes; others subscribe.
public class Button
{
    public event EventHandler? Clicked;       // declare
    public void Press() => Clicked?.Invoke(this, EventArgs.Empty);  // raise (null-safe)
}
// elsewhere:
var b = new Button();
b.Clicked += (sender, e) => Console.WriteLine("clicked!");   // subscribe
b.Press();
```
Lambdas + delegates are everywhere (LINQ, callbacks, DI factories). **Events** model
publish/subscribe — and you'll meet the same idea in Unity (`UnityEvent`, C# events).

## 5. Exceptions

```csharp
try
{
    DoWork();
}
catch (IOException ex) when (ex.Message.Contains("disk"))   // exception filter
{
    logger.LogWarning(ex, "disk issue");
}
catch (Exception ex)
{
    logger.LogError(ex, "unexpected");
    throw;                       // re-throw preserving the original stack trace
}
finally
{
    Cleanup();                   // always runs
}
```
- Throw specific types (`ArgumentException`, `InvalidOperationException`).
- `throw;` (not `throw ex;`) preserves the stack trace — crucial for support.
- Don't catch what you can't handle; let it bubble to where it's logged.

## 6. Deterministic cleanup: `IDisposable` / `using`

```csharp
using var file = File.OpenText("data.txt");   // Dispose() called at end of scope
var line = file.ReadLine();
```
Anything holding an OS/native resource (files, sockets, DB connections) implements
`IDisposable`; `using` guarantees release even on exceptions.

---

## Do the lab
Build a small in-memory "orders" analysis with LINQ, a generic cache, and an event;
read the playground's `LinqDemo`. 👉 **[lab.md](./lab.md)**

Then: 👉 **[challenge.md](./challenge.md)**

## Key terms
`List`/`Dictionary`/`HashSet` · `IEnumerable<T>` · generics & constraints · LINQ ·
deferred execution · `Func`/`Action`/`Predicate` · event · exception filter · `throw;` ·
`IDisposable`/`using`

**Next →** [Module 04: .NET Runtime & Project Model](../04-dotnet-runtime-and-projects/)
