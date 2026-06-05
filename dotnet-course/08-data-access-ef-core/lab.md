# Lab 08 — Persist TaskApi with EF Core

**You'll:** add EF Core + SQLite to the API, create/apply a migration, do CRUD through
the API, and evolve the schema with a second migration. ⏱️ ~55 min.

> Start from your Module 07 lab project, or a copy of the reference app. These steps
> mirror what the reference `apps/TaskApi` does.

---

## Part A — Add EF Core packages
```bash
cd ~/dev/taskapi-lab/TaskApi      # your Module 07 project
dotnet add package Microsoft.EntityFrameworkCore.Sqlite --version 8.0.7
dotnet add package Microsoft.EntityFrameworkCore.Design --version 8.0.7
dotnet tool install --global dotnet-ef    # if not already
```

## Part B — Entity + DbContext
Add `Data.cs`:
```csharp
using Microsoft.EntityFrameworkCore;
namespace TaskApi;

public class TaskItem
{
    public int Id { get; set; }
    public string Title { get; set; } = "";
    public bool IsDone { get; set; }
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;
}

public class TaskDbContext(DbContextOptions<TaskDbContext> options) : DbContext(options)
{
    public DbSet<TaskItem> Tasks => Set<TaskItem>();
}
```
Register it in `Program.cs` (replace the in-memory singleton):
```csharp
builder.Services.AddDbContext<TaskDbContext>(o => o.UseSqlite("Data Source=tasks.db"));
```

## Part C — First migration
```bash
dotnet ef migrations add InitialCreate
dotnet ef database update
ls Migrations/           # *_InitialCreate.cs + a ModelSnapshot
ls tasks.db              # the SQLite file now exists
```
✅ A `Migrations/` folder appeared and `tasks.db` was created with a `Tasks` table.

## Part D — CRUD through EF in the endpoints
Update your endpoints to use the DbContext (injected **Scoped**):
```csharp
var tasks = app.MapGroup("/api/tasks");

tasks.MapGet("/", async (TaskDbContext db) =>
    Results.Ok(await db.Tasks.OrderBy(t => t.Id).ToListAsync()));

tasks.MapGet("/{id:int}", async (int id, TaskDbContext db) =>
    await db.Tasks.FindAsync(id) is { } t ? Results.Ok(t) : Results.NotFound());

tasks.MapPost("/", async (TaskItem input, TaskDbContext db) =>
{
    if (string.IsNullOrWhiteSpace(input.Title))
        return Results.BadRequest(new { error = "Title is required" });
    var item = new TaskItem { Title = input.Title.Trim() };
    db.Tasks.Add(item);
    await db.SaveChangesAsync();
    return Results.Created($"/api/tasks/{item.Id}", item);
});

tasks.MapPost("/{id:int}/complete", async (int id, TaskDbContext db) =>
{
    var t = await db.Tasks.FindAsync(id);
    if (t is null) return Results.NotFound();
    t.IsDone = true;
    await db.SaveChangesAsync();
    return Results.NoContent();
});
```
Run and exercise:
```bash
dotnet run
curl -s -X POST http://localhost:5080/api/tasks -H 'Content-Type: application/json' -d '{"title":"persisted!"}' ; echo
curl -s http://localhost:5080/api/tasks ; echo
```
Now **stop the app and start it again**, then:
```bash
curl -s http://localhost:5080/api/tasks ; echo     # your task is STILL THERE
```
✅ Unlike the in-memory version, data survives a restart — it's in `tasks.db`.

## Part E — Evolve the schema (second migration)
Add a property to `TaskItem`:
```csharp
public string Priority { get; set; } = "Normal";
```
```bash
dotnet ef migrations add AddPriority
dotnet ef database update
dotnet ef migrations list           # InitialCreate, AddPriority
```
✅ EF generated an `ALTER TABLE` migration; existing rows get the default. Inspect the
generated `Migrations/*_AddPriority.cs` to see the `AddColumn` call.

## Part F — Inspect the SQL (optional)
Set Serilog/EF logging to see the SQL EF runs, or add:
```csharp
o.UseSqlite("Data Source=tasks.db").LogTo(Console.WriteLine, LogLevel.Information);
```
Run a GET and watch the `SELECT ... FROM "Tasks"` statement scroll by.

## What you learned
- Entities + `DbContext` map C# to tables; registered **Scoped**.
- Migrations version your schema (`add` → `database update`); never edit applied ones.
- CRUD via `DbSet` + `SaveChangesAsync`; data persists across restarts.
- LINQ becomes SQL — keep queries translatable and filtered server-side.

➡️ **[challenge.md](./challenge.md)** then [Module 09](../09-operate-and-support/).
