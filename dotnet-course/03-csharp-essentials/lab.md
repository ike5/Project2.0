# Lab 03 — LINQ, Generics & Events

**You'll:** analyze data with LINQ, write a generic cache, and wire an event.
⏱️ ~45 min.

```bash
mkdir -p ~/dev/ft3 && cd ~/dev/ft3
dotnet new console -n Ft3 && cd Ft3
```

## Part A — LINQ analysis
In `Program.cs`:
```csharp
record Order(int Id, string Customer, decimal Total);

var orders = new List<Order>
{
    new(1, "Ada", 120), new(2, "Ada", 80), new(3, "Grace", 200),
    new(4, "Linus", 50), new(5, "Grace", 90),
};

// total spend per customer, highest first:
var byCustomer = orders
    .GroupBy(o => o.Customer)
    .Select(g => new { Customer = g.Key, Spend = g.Sum(o => o.Total), Count = g.Count() })
    .OrderByDescending(x => x.Spend)
    .ToList();

foreach (var row in byCustomer)
    Console.WriteLine($"{row.Customer}: {row.Spend:C} over {row.Count} orders");

Console.WriteLine($"big orders (>100): {orders.Count(o => o.Total > 100)}");
Console.WriteLine($"top order: {orders.MaxBy(o => o.Total)!.Id}");
```
✅ Expected (order of the grouped rows by spend):
```
Grace: $290.00 over 2 orders
Ada: $200.00 over 2 orders
Linus: $50.00 over 1 orders
big orders (>100): 2
top order: 3
```

### Prove deferred execution
```csharp
var query = orders.Where(o => { Console.WriteLine($"  testing {o.Id}"); return o.Total > 100; });
Console.WriteLine("query built (nothing ran yet)");
var list = query.ToList();      // NOW the predicate runs
Console.WriteLine($"matched {list.Count}");
```
✅ "query built" prints *before* any "testing N" lines — that's deferral.

## Part B — A generic cache
Add `Cache.cs`:
```csharp
namespace Ft3;
public class Cache<TKey, TValue> where TKey : notnull
{
    private readonly Dictionary<TKey, TValue> _store = new();
    public TValue GetOrAdd(TKey key, Func<TKey, TValue> factory)
    {
        if (_store.TryGetValue(key, out var existing)) return existing;
        var created = factory(key);
        _store[key] = created;
        return created;
    }
}
```
```csharp
using Ft3;
var cache = new Cache<int, string>();
string Make(int n) { Console.WriteLine($"  computing {n}"); return $"value-{n}"; }
Console.WriteLine(cache.GetOrAdd(1, Make));   // computes
Console.WriteLine(cache.GetOrAdd(1, Make));   // cached — no "computing" line
```
✅ The second call prints no "computing" line — generics + a delegate factory.

## Part C — An event
Add `Stock.cs`:
```csharp
namespace Ft3;
public class Stock(string symbol)
{
    public string Symbol { get; } = symbol;
    public decimal Price { get; private set; }
    public event EventHandler<decimal>? PriceChanged;
    public void SetPrice(decimal price)
    {
        Price = price;
        PriceChanged?.Invoke(this, price);
    }
}
```
```csharp
using Ft3;
var stock = new Stock("ACME");
stock.PriceChanged += (s, price) => Console.WriteLine($"  alert: {((Stock)s!).Symbol} -> {price:C}");
stock.SetPrice(10m);
stock.SetPrice(12.5m);
```
✅ Each `SetPrice` fires the subscriber.

## Part D — Reference demo
```bash
cd <repo>/dotnet-course/apps/console-playground
dotnet run -- 3
```

## What you learned
- LINQ pipelines (filter/group/aggregate/order) + deferred execution.
- Generic types with constraints and delegate factories.
- Events as in-process publish/subscribe.

➡️ **[challenge.md](./challenge.md)** then [Module 04](../04-dotnet-runtime-and-projects/).
