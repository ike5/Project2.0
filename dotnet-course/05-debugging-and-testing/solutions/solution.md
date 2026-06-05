# Challenge 05 — Reference Solution

### 1. Trace reading
- **(a)** `System.FormatException`.
- **(b)** `Importer.cs:line 57` (`ParseRow`) — the first frame in *your* code.
- **(c)** A CSV column contained a non-numeric value (`'N/A'`) and `int.Parse`
  threw. **Fix:** use `int.TryParse` and handle/skip the bad row.

### 2. Theory test + implementation
```csharp
public static class Fb
{
    public static string Fizzbuzz(int n) => (n % 3, n % 5) switch
    {
        (0, 0) => "FizzBuzz",
        (0, _) => "Fizz",
        (_, 0) => "Buzz",
        _ => n.ToString(),
    };
}

public class FizzbuzzTests
{
    [Theory]
    [InlineData(3, "Fizz")]
    [InlineData(5, "Buzz")]
    [InlineData(15, "FizzBuzz")]
    [InlineData(7, "7")]
    public void Cases(int n, string expected) => Assert.Equal(expected, Fb.Fizzbuzz(n));
}
```

### 3. Exception test
```csharp
[Fact]
public void Remove_missing_throws()
{
    var inv = new Inventory();
    Assert.Throws<KeyNotFoundException>(() => inv.Remove("ghost"));
}
// implementation:
public void Remove(string name)
{
    var item = _items.FirstOrDefault(i => i.Name == name)
        ?? throw new KeyNotFoundException(name);
    _items.Remove(item);
}
```

### 4. Async test (EF InMemory)
```csharp
[Fact]
public async Task Create_then_GetAll_has_one_trimmed()
{
    var db = new TaskDbContext(new DbContextOptionsBuilder<TaskDbContext>()
        .UseInMemoryDatabase(Guid.NewGuid().ToString()).Options);
    var svc = new TaskService(db, NullLogger<TaskService>.Instance);

    await svc.CreateAsync(new CreateTaskDto("  trim me  "));
    var all = await svc.GetAllAsync();

    Assert.Single(all);
    Assert.Equal("trim me", all[0].Title);
}
```
