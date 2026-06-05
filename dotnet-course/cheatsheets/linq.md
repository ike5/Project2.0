# LINQ Cheatsheet

LINQ gives you SQL-like queries over any `IEnumerable<T>` (lists, arrays, EF Core
tables). Two syntaxes — **method** (used 95% of the time) and **query**:

```csharp
// method syntax (preferred)
var names = people.Where(p => p.Age >= 18).Select(p => p.Name).ToList();

// query syntax (equivalent)
var names2 = (from p in people where p.Age >= 18 select p.Name).ToList();
```

> Most operators are **deferred**: nothing runs until you enumerate (`foreach`,
> `ToList`, `Count`, `First`, …). With EF Core, that's when SQL is sent.

## Filtering & projection
```csharp
xs.Where(x => x > 0)                 // filter
xs.Select(x => x * 2)               // transform
xs.SelectMany(x => x.Children)      // flatten nested sequences
xs.OfType<Cat>()                    // filter by type
xs.Distinct()                       // unique
xs.DistinctBy(x => x.Key)           // unique by key (.NET 6+)
```

## Ordering
```csharp
xs.OrderBy(x => x.Name)
  .ThenByDescending(x => x.Age)
xs.OrderByDescending(x => x.Score)
xs.Reverse()
```

## Aggregation
```csharp
xs.Count();   xs.Count(x => x.IsActive)
xs.Sum(x => x.Total);   xs.Average(x => x.Score)
xs.Min();  xs.Max();  xs.MaxBy(x => x.Score)   // MaxBy/MinBy return the element
xs.Aggregate((acc, x) => acc + x)
```

## Element access (careful with empties!)
```csharp
xs.First();              // throws if empty
xs.FirstOrDefault();     // null/default if empty  ← prefer when unsure
xs.Single();             // exactly one, else throws
xs.SingleOrDefault();
xs.Last();  xs.LastOrDefault();
xs.ElementAtOrDefault(3);
```

## Quantifiers & set ops
```csharp
xs.Any();   xs.Any(x => x > 0)
xs.All(x => x.IsValid)
xs.Contains(item)
xs.Union(ys);  xs.Intersect(ys);  xs.Except(ys)
```

## Partitioning
```csharp
xs.Take(5);   xs.Skip(5)
xs.TakeWhile(x => x < 10);  xs.SkipWhile(...)
xs.Chunk(100)               // batches of 100 (.NET 6+)
```

## Grouping & joining
```csharp
xs.GroupBy(x => x.Category)            // -> IEnumerable<IGrouping<K, T>>
  .Select(g => new { g.Key, Count = g.Count() });

orders.Join(customers,
    o => o.CustomerId, c => c.Id,
    (o, c) => new { o.Id, c.Name });

xs.ToDictionary(x => x.Id, x => x.Name);
xs.ToLookup(x => x.Category);
```

## Materializing (ends deferral)
```csharp
xs.ToList();  xs.ToArray();  xs.ToHashSet();  xs.ToDictionary(...)
```

---
**Gotcha:** re-enumerating a deferred query re-runs it. If you need the results
multiple times, materialize once with `.ToList()`.
**EF Core:** keep queries server-side — call `.ToList()`/`.ToListAsync()` *after*
your `Where/Select`, not before, or you'll pull the whole table into memory.
