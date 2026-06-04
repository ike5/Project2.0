# Challenge 08 — Reference Solution

### 1. Related entity (one-to-many)
```csharp
public class Tag
{
    public int Id { get; set; }
    public string Name { get; set; } = "";
    public int TaskItemId { get; set; }          // FK
    public TaskItem? TaskItem { get; set; }       // nav back
}

public class TaskItem
{
    public int Id { get; set; }
    public string Title { get; set; } = "";
    public bool IsDone { get; set; }
    public List<Tag> Tags { get; set; } = new();  // nav: one task -> many tags
}

// DbContext:
public DbSet<Tag> Tags => Set<Tag>();
```
```bash
dotnet ef migrations add AddTags
dotnet ef database update
```
Return tasks with tags:
```csharp
tasks.MapGet("/", async (TaskDbContext db) =>
    Results.Ok(await db.Tasks.Include(t => t.Tags).OrderBy(t => t.Id).ToListAsync()));
```

### 2. Server-side filtering
```csharp
tasks.MapGet("/", async (TaskDbContext db, bool? done, string? search) =>
{
    IQueryable<TaskItem> q = db.Tasks;                       // still a query (not executed)
    if (done is not null)   q = q.Where(t => t.IsDone == done);
    if (!string.IsNullOrWhiteSpace(search))
        q = q.Where(t => t.Title.Contains(search));          // -> SQL LIKE
    return Results.Ok(await q.OrderBy(t => t.Id).ToListAsync()); // executes HERE
});
```
> Because the `Where`s are applied to `IQueryable` **before** `ToListAsync`, EF folds
> them into the SQL `WHERE`. The logged query shows the filter — no full-table load.

### 3. Translation trap
```csharp
// THROWS: EF can't translate a custom method to SQL
var bad = await db.Tasks.Where(t => Normalize(t.Title) == "x").ToListAsync();
static string Normalize(string s) => s.Trim().ToLowerInvariant();

// FIX A: rewrite with translatable operators
var okA = await db.Tasks.Where(t => t.Title.Trim().ToLower() == "x").ToListAsync();
// FIX B: materialize first, then filter in memory (only when the set is small)
var all = await db.Tasks.ToListAsync();
var okB = all.Where(t => Normalize(t.Title) == "x").ToList();
```
> EF Core converts the expression tree to SQL; it doesn't know your C# method, so it
> can't translate it. Use SQL-translatable operations, or pull data first (carefully).

### 4. Migration discipline
> Applied migrations are an **ordered, immutable history** recorded in the
> `__EFMigrationsHistory` table and possibly already run on other databases. Editing
> an applied migration would make environments diverge. To rename a column, add a
> **new** migration (`dotnet ef migrations add RenameX`). `dotnet ef migrations
> remove` deletes the **last** migration — safe only if it has **not** been applied
> (`database update`) anywhere; otherwise revert with `database update <previous>` first.
