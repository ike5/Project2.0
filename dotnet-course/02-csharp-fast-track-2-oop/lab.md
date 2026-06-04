# Lab 02 — Model a Small Domain

**You'll:** build accounts with encapsulation, use a record for a value, and an
interface for pluggable behavior. ⏱️ ~40 min.

---

## Part A — Project
```bash
mkdir -p ~/dev/ft2 && cd ~/dev/ft2
dotnet new console -n Ft2 && cd Ft2
```

## Part B — An encapsulated class
Put this above the top-level statements won't work; instead add a new file
`Account.cs` (types can live in their own files):
```csharp
// Account.cs
namespace Ft2;

public class Account(string owner)
{
    public string Owner { get; } = owner;
    public decimal Balance { get; private set; }

    public void Deposit(decimal amount)
    {
        if (amount <= 0) throw new ArgumentOutOfRangeException(nameof(amount));
        Balance += amount;
    }

    public bool TryWithdraw(decimal amount)
    {
        if (amount <= 0 || amount > Balance) return false;
        Balance -= amount;
        return true;
    }
}
```
In `Program.cs`:
```csharp
using Ft2;
var acct = new Account("Ada");
acct.Deposit(100);
Console.WriteLine($"{acct.Owner} balance: {acct.Balance:C}");
Console.WriteLine(acct.TryWithdraw(40) ? "withdrew 40" : "declined");
Console.WriteLine(acct.TryWithdraw(1000) ? "withdrew 1000" : "declined (insufficient)");
// acct.Balance = 5;   // <- try this: COMPILE ERROR (private set). Good!
```
✅ Run it. Uncomment the `Balance =` line to *see* encapsulation enforced by the compiler.

## Part C — A record value
```csharp
// add to Program.cs
var m1 = new Money("USD", 9.99m);
var m2 = m1 with { Amount = 19.99m };
Console.WriteLine($"{m1} vs {m2}, equal={m1 == m2}");

public record Money(string Currency, decimal Amount);
```
✅ Note the free `ToString()` (`Money { Currency = USD, Amount = 9.99 }`) and value
equality (`equal=False`).

## Part D — An interface + polymorphism
```csharp
public interface INotifier { void Notify(string message); }

public class ConsoleNotifier : INotifier
{
    public void Notify(string message) => Console.WriteLine($"[console] {message}");
}
public class PrefixNotifier(string prefix) : INotifier
{
    public void Notify(string message) => Console.WriteLine($"[{prefix}] {message}");
}
```
```csharp
// drive them polymorphically:
INotifier[] notifiers = [new ConsoleNotifier(), new PrefixNotifier("AUDIT")];
foreach (var n in notifiers) n.Notify("account opened");
```
✅ Both implement `INotifier`; the loop doesn't care which concrete type it has —
that's polymorphism, and it's exactly what DI will exploit in Module 07.

## Part E — Read the reference demo
```bash
cd <repo>/dotnet-course/apps/console-playground
dotnet run -- 2        # OopDemo: Shape hierarchy, records, IGreeter
```

## What you learned
- Properties + `private set` enforce invariants at compile time.
- Records model immutable values with equality and `with`-copies.
- Interfaces let you swap implementations behind a contract.

➡️ **[challenge.md](./challenge.md)** then [Module 03](../03-csharp-essentials/).
