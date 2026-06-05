# Module 02 — C# Fast-Track II (OOP)

**Goal:** model with C#'s object features — classes, records, interfaces,
polymorphism — the way real .NET codebases do. ⏱️ ~1.5 h · 🎯 Prereq: 00–01.

---

## 1. Classes & properties

```csharp
public class Account
{
    public string Owner { get; init; }        // settable only at construction
    public decimal Balance { get; private set; } // read anywhere, write only inside
    private readonly List<string> _log = new(); // private field convention: _camelCase

    public Account(string owner) => Owner = owner;   // primary-style constructor body

    public void Deposit(decimal amount)
    {
        if (amount <= 0) throw new ArgumentOutOfRangeException(nameof(amount));
        Balance += amount;
        _log.Add($"+{amount}");
    }

    public IReadOnlyList<string> History => _log;   // expression-bodied property
}
```
**Properties** are the idiomatic replacement for public fields — `{ get; set; }`,
`{ get; init; }` (set once), or with custom logic. Auto-properties generate the
backing field for you.

**Primary constructors (C# 12)** let you declare ctor params on the type:
```csharp
public class Repository(IDbConnection db)   // db is usable throughout the class
{
    public void Save() => db.Execute(/* ... */);
}
```

## 2. Records — data with value semantics

```csharp
public record Customer(string Name, string Email);   // positional record

var c1 = new Customer("Ada", "ada@x.com");
var c2 = c1 with { Email = "ada@y.com" };   // copy with a change (non-destructive)
bool same = c1 == c2;                        // VALUE equality, not reference
```
Records give you immutability, value-based equality, and a readable `ToString()` for
free — ideal for DTOs, configuration, and domain values. Use **records** for data,
**classes** for things with identity/behavior/mutable state.

`record struct` gives a value-type record.

## 3. Interfaces — contracts

```csharp
public interface INotifier
{
    Task SendAsync(string to, string message);
}

public class EmailNotifier : INotifier
{
    public Task SendAsync(string to, string message) => /* ... */ Task.CompletedTask;
}
```
Program against interfaces, not concrete types — it's the backbone of testability and
**dependency injection** (Module 07). Common BCL interfaces: `IEnumerable<T>`,
`IDisposable`, `IComparable<T>`, `IEquatable<T>`.

## 4. Inheritance & polymorphism

```csharp
public abstract class Shape
{
    public abstract double Area();              // must override
    public virtual string Describe() => $"area={Area():0.00}";  // may override
}
public class Circle(double r) : Shape
{
    public override double Area() => Math.PI * r * r;
}
```
- `abstract` — no body, subclass must implement.
- `virtual` — has a body, subclass *may* `override`.
- `sealed` — prevents further overriding/inheritance.
- Prefer **composition + interfaces** over deep inheritance hierarchies.

## 5. Enums & namespaces

```csharp
public enum Priority { Low, Normal, High }      // backed by int (0,1,2)
Priority p = Priority.High;
if (Enum.TryParse<Priority>("Low", out var parsed)) { }

namespace TaskApi.Domain;                        // file-scoped namespace
```

## 6. Static, constants, and object init

```csharp
public static class MathHelpers { public const double Tau = 6.283; }
var c = new Customer { Name = "Ada", Email = "a@x.com" };   // object initializer
```

---

## Do the lab
Model a tiny domain (accounts + notifications) using records, an interface, and
polymorphism; read the playground's `OopDemo`. 👉 **[lab.md](./lab.md)**

Then: 👉 **[challenge.md](./challenge.md)**

## Key terms
class · property (`get`/`init`/`private set`) · primary constructor · record ·
`with` · interface · `abstract`/`virtual`/`override`/`sealed` · enum · file-scoped namespace

**Next →** [Module 03: C# Essentials](../03-csharp-essentials/)
